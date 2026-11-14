/**
 * DataForSEO: the two numbers neither Search Console nor the server log can
 * give us.
 *
 * Search Console only knows the queries we ALREADY appear for, and it only
 * knows our own property. It cannot answer "how many keywords does this
 * domain rank for at all" (because a keyword we rank #74 for produces no
 * impressions worth reporting) and it knows nothing about who links to us.
 * Both of those are third-party measurements, and the case-study contract has
 * had two null slots waiting for them since it was written:
 * ranked_keywords_top_100 and unique_referring_domains.
 *
 * Deliberately NOT a keyword-research cron. STRATEGY.md reasons from search
 * volumes pulled on 2026-10-22, and a job that quietly rewrote those numbers
 * every Monday would change the premises of a document without anyone
 * deciding to. Research is a re-pull you run on purpose: mcp/dfs.py.
 *
 * Cost: two live calls, $0.012 + $0.024 = about $0.036 a week, so roughly
 * two dollars a year. Worth knowing the account is prepaid - if the balance
 * runs out these calls fail with a 402 and the feed says so in last_error
 * rather than silently reporting zero rankings.
 */

const DFS = "https://api.dataforseo.com/v3/";
const LOCATION_CODE = 2840;  // United States - the whole market, not a town.

function auth(env) {
  return "Basic " + btoa(`${env.DATAFORSEO_LOGIN}:${env.DATAFORSEO_PASSWORD}`);
}

async function dfs(env, endpoint, payload) {
  const res = await fetch(DFS + endpoint, {
    method: "POST",
    headers: { Authorization: auth(env), "Content-Type": "application/json" },
    body: JSON.stringify([payload]),
  });
  if (!res.ok) {
    throw new Error(`DataForSEO ${endpoint} HTTP ${res.status}: `
      + (await res.text()).slice(0, 180));
  }
  const j = await res.json();
  const task = (j.tasks || [])[0];
  if (!task) throw new Error(`DataForSEO ${endpoint}: no task in response`);
  // 20000 is "Ok." - anything else is a real failure and must not be read as
  // an empty result. A 40402 (insufficient funds) returning "0 keywords"
  // would be a lie we published on a portfolio page.
  if (task.status_code !== 20000) {
    throw new Error(`DataForSEO ${endpoint} ${task.status_code}: `
      + String(task.status_message).slice(0, 180));
  }
  return { result: (task.result || [])[0] || {}, cost: task.cost || 0 };
}

export async function ensureRankSchema(env) {
  await env.DB.batch([
    // One row per sample date, so the series is append-only and a second run
    // on the same day corrects that day instead of inventing a data point.
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_rank_snap (
      date TEXT PRIMARY KEY,
      ranked_top100 INTEGER NOT NULL DEFAULT 0,
      ranked_top10 INTEGER NOT NULL DEFAULT 0,
      ranked_top3 INTEGER NOT NULL DEFAULT 0,
      referring_domains INTEGER,
      backlinks INTEGER,
      domain_rank INTEGER
    )`),
    // The current picture, replaced each run. History lives in cs_rank_snap;
    // keeping every keyword at every position for ever would be a different
    // product.
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_rank_kw (
      keyword TEXT PRIMARY KEY,
      position INTEGER NOT NULL,
      volume INTEGER,
      url TEXT,
      updated_at TEXT NOT NULL
    )`),
  ]);
}

/**
 * Every keyword the domain ranks for in the top 100, plus who links to it.
 *
 * The two calls are separately try/caught by the caller through its own
 * per-source wrapper, but they share one function because they share one
 * meaning: "how visible is this domain to the rest of the web this week".
 */
export async function pullDataForSeo(env) {
  await ensureRankSchema(env);
  const today = new Date().toISOString().slice(0, 10);
  const host = (env.SITE_HOST || "numbermyboat.com");
  let cost = 0;

  const kw = await dfs(env, "dataforseo_labs/google/ranked_keywords/live", {
    target: host,
    location_code: LOCATION_CODE,
    language_code: "en",
    limit: 100,
    order_by: ["ranked_serp_element.serp_item.rank_group,asc"],
    filters: [["ranked_serp_element.serp_item.rank_group", "<=", 100]],
  });
  cost += kw.cost;
  const items = kw.result.items || [];

  // A ranking is a position, so rows missing one are not counted either way.
  const rows = [];
  for (const it of items) {
    const se = ((it.ranked_serp_element || {}).serp_item) || {};
    const pos = se.rank_group;
    if (!Number.isFinite(pos)) continue;
    const kd = it.keyword_data || {};
    rows.push({
      keyword: String(kd.keyword || "").slice(0, 200),
      position: pos,
      volume: ((kd.keyword_info || {}).search_volume) ?? null,
      url: String(se.url || "").slice(0, 300),
    });
  }
  const top100 = rows.length;
  const top10 = rows.filter((r) => r.position <= 10).length;
  const top3 = rows.filter((r) => r.position <= 3).length;

  // Backlinks is the second call and the more expensive one. If it fails we
  // still want the rankings, so its own failure is swallowed into nulls and
  // reported - a missing referring-domain count is not a reason to lose the
  // keyword count we already paid for.
  let bl = null, blErr = null;
  try {
    const b = await dfs(env, "backlinks/summary/live", {
      target: host, internal_list_limit: 1,
      backlinks_status_type: "live", include_subdomains: true,
    });
    cost += b.cost;
    bl = {
      referring_domains: b.result.referring_domains ?? null,
      backlinks: b.result.backlinks ?? null,
      domain_rank: b.result.rank ?? null,
    };
  } catch (e) {
    blErr = String((e && e.message) || e).slice(0, 200);
  }

  await env.DB.prepare(
    `INSERT INTO cs_rank_snap
       (date, ranked_top100, ranked_top10, ranked_top3,
        referring_domains, backlinks, domain_rank)
     VALUES (?1,?2,?3,?4,?5,?6,?7)
     ON CONFLICT(date) DO UPDATE SET
       ranked_top100=excluded.ranked_top100,
       ranked_top10=excluded.ranked_top10,
       ranked_top3=excluded.ranked_top3,
       referring_domains=COALESCE(excluded.referring_domains, cs_rank_snap.referring_domains),
       backlinks=COALESCE(excluded.backlinks, cs_rank_snap.backlinks),
       domain_rank=COALESCE(excluded.domain_rank, cs_rank_snap.domain_rank)`
  ).bind(today, top100, top10, top3,
         bl && bl.referring_domains, bl && bl.backlinks, bl && bl.domain_rank).run();

  // Replace the current keyword picture. DELETE then INSERT in one batch so a
  // reader never sees an empty table.
  const stmts = [env.DB.prepare("DELETE FROM cs_rank_kw")];
  for (const r of rows.slice(0, 100)) {
    stmts.push(env.DB.prepare(
      `INSERT INTO cs_rank_kw (keyword, position, volume, url, updated_at)
       VALUES (?1,?2,?3,?4,?5) ON CONFLICT(keyword) DO UPDATE SET
         position=excluded.position, volume=excluded.volume,
         url=excluded.url, updated_at=excluded.updated_at`)
      .bind(r.keyword, r.position, r.volume, r.url, today));
  }
  await env.DB.batch(stmts);

  return { top100, top10, top3, backlinks: bl, backlinks_error: blErr,
           cost: +cost.toFixed(4), keywords_stored: rows.length };
}

/**
 * The feed block. Null when nothing has ever been pulled, because a domain
 * with no measurement is not the same as a domain measured at zero - and for
 * a shop that launched three weeks ago, zero top-100 keywords is a real and
 * expected finding, not a broken integration.
 */
export async function searchVisibilityBlock(env, getMeta) {
  let snaps = [], kws = [];
  try {
    snaps = (await env.DB.prepare(
      `SELECT date, ranked_top100, ranked_top10, ranked_top3,
              referring_domains, backlinks, domain_rank
         FROM cs_rank_snap ORDER BY date`).all()).results || [];
    kws = (await env.DB.prepare(
      `SELECT keyword, position, volume, url FROM cs_rank_kw
        ORDER BY position ASC, volume DESC LIMIT 25`).all()).results || [];
  } catch { /* tables not created yet */ }

  const updated = await getMeta(env, "dfs_updated");
  const last_error = await getMeta(env, "dfs_last_error");
  if (!snaps.length) return { current: null, updated, last_error };

  const cur = snaps[snaps.length - 1];
  const first = snaps[0];
  return {
    current: {
      date: cur.date,
      ranked_keywords_top_100: cur.ranked_top100,
      ranked_keywords_top_10: cur.ranked_top10,
      ranked_keywords_top_3: cur.ranked_top3,
      unique_referring_domains: cur.referring_domains,
      backlinks: cur.backlinks,
      domain_rank: cur.domain_rank,
    },
    first_sample: { date: first.date, ranked_keywords_top_100: first.ranked_top100 },
    history: snaps,
    top_ranked_keywords: kws,
    updated,
    last_error,
    source: "DataForSEO Labs ranked_keywords and Backlinks summary, "
      + "United States, Google desktop + mobile, sampled weekly",
  };
}
