/**
 * The case-study feed: numbermyboat.com measuring itself, in the shape
 * aaron.chat already consumes.
 *
 * WHAT THIS IS FOR. aaron.chat's /work pages are not written, they are fed.
 * Each site publishes /api/case-study.json, a registry on aaron.chat lists
 * the feed URLs, a prebuild step bakes them, and the report page renders
 * whatever is actually true that week. So the only honest way to appear
 * there is to publish real numbers and let the page say what they are -
 * which also means this endpoint must never round a zero up into a story.
 *
 * SCHEMA 1.1, matching the other feeds. The consumer is adaptive: it picks a
 * "win" from whatever is connected, and it reads `updated` and `last_error`
 * on each source to tell "we have no data" apart from "we never connected".
 * Those two fields are the most important thing in this file. A source that
 * fails silently and reports zero is worse than one that reports nothing,
 * because the report page will cheerfully draw a flat line through it.
 *
 * ONE TABLE FEWER THAN THE REFERENCE. aaron.chat logs AI crawls to its own
 * cs_bot_crawl; this site already has traffic_log, which was built for the
 * same question and has been through the privacy review (no IP, no visitor
 * id, user-agent for bots only). Adding a second crawl table would mean two
 * answers to "did ChatGPT read this page". The engine mapping happens at
 * read time instead.
 *
 * Data sources:
 *   cs_gsc_daily / cs_gsc_query  <- Search Console, weekly service-account pull
 *   cs_ai_monthly                <- Bing AI Performance CSV, uploaded by hand
 *   traffic_log                  <- this worker's own crawl + referral log
 *   cs_meta                      <- per-source updated / last_error, GA4 scalars
 *   orders                       <- what the shop actually sold
 */

import { pullDataForSeo, searchVisibilityBlock } from "./dataforseo.js";

export const CASE_STUDY_SCHEMA_VERSION = "1.1";

/**
 * Which answer engine a crawler belongs to. Deliberately the SAME labels as
 * aaron.chat's BOT_ENGINE map: the report page groups bars by these strings,
 * so "ChatGPT" here and "OpenAI" there would draw two bars for one engine.
 */
export const BOT_ENGINE = {
  "gptbot": "ChatGPT", "chatgpt-user": "ChatGPT", "oai-searchbot": "ChatGPT",
  "claudebot": "Claude", "claude-web": "Claude", "anthropic-ai": "Claude",
  "claude-searchbot": "Claude", "claude-user": "Claude",
  "perplexitybot": "Perplexity", "perplexity-user": "Perplexity",
  "google-extended": "Google (Gemini)", "googleother": "Google",
  "googlebot": "Google",
  "bingbot": "Bing / Copilot", "bingpreview": "Bing / Copilot",
  "applebot-extended": "Apple", "applebot": "Apple",
  "meta-externalagent": "Meta AI", "facebookbot": "Meta AI",
  "amazonbot": "Amazon", "cohere-ai": "Cohere", "ccbot": "Common Crawl",
  "bytespider": "ByteDance", "mistralai-user": "Mistral", "diffbot": "Diffbot",
  "duckduckbot": "DuckDuckGo", "yandexbot": "Yandex", "baiduspider": "Baidu",
  "slurp": "Yahoo",
};

export async function ensureCaseStudySchema(env) {
  await env.DB.batch([
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_gsc_daily (
      date TEXT PRIMARY KEY, clicks INTEGER NOT NULL DEFAULT 0,
      impressions INTEGER NOT NULL DEFAULT 0, position REAL NOT NULL DEFAULT 0
    )`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_gsc_query (
      query TEXT PRIMARY KEY, clicks INTEGER NOT NULL DEFAULT 0,
      impressions INTEGER NOT NULL DEFAULT 0, position REAL NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL
    )`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_ai_monthly (
      month TEXT PRIMARY KEY, citations INTEGER NOT NULL DEFAULT 0,
      crawls INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
    )`),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS cs_meta (
      k TEXT PRIMARY KEY, v TEXT NOT NULL
    )`),
  ]);
}

export async function getMeta(env, k) {
  const r = await env.DB.prepare("SELECT v FROM cs_meta WHERE k=?").bind(k).first();
  return (r && r.v) || null;
}
export async function setMeta(env, k, v) {
  await env.DB.prepare(
    "INSERT INTO cs_meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v"
  ).bind(k, String(v)).run();
}

/* ------------------------------------------------- RS256 service-account JWT */
const b64url = (buf) => {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const b64urlStr = (s) => b64url(new TextEncoder().encode(s));

function pemToPkcs8(pem) {
  const body = pem.replace(/-----BEGIN [^-]+-----/, "")
    .replace(/-----END [^-]+-----/, "").replace(/\s+/g, "");
  const bin = atob(body);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/**
 * A short-lived Google access token from a service-account key.
 *
 * The private key arrives as a PEM inside a JSON secret. Two things bite
 * here and both are worth naming: the newlines in that PEM must be real
 * newlines (a secret pasted with literal \\n characters imports as garbage
 * and fails with an opaque DataError), and the service account must be an
 * OWNER on the Search Console property - "Full" permission is not enough
 * for the API and fails as a 403 that reads like a bad key.
 */
export async function googleAccessToken(saJson, scope) {
  const sa = typeof saJson === "string" ? JSON.parse(saJson) : saJson;
  const tokenUri = sa.token_uri || "https://oauth2.googleapis.com/token";
  const now = Math.floor(Date.now() / 1000);
  const signingInput =
    `${b64urlStr(JSON.stringify({ alg: "RS256", typ: "JWT" }))}.`
    + `${b64urlStr(JSON.stringify({
      iss: sa.client_email, scope, aud: tokenUri, iat: now, exp: now + 3600 }))}`;
  const key = await crypto.subtle.importKey(
    "pkcs8", pemToPkcs8(String(sa.private_key).replace(/\\n/g, "\n")),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(signingInput));
  const res = await fetch(tokenUri, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${signingInput}.${b64url(sig)}` }),
  });
  if (!res.ok) {
    throw new Error(`google token ${res.status}: ${(await res.text()).slice(0, 180)}`);
  }
  const j = await res.json();
  if (!j.access_token) throw new Error("google token: no access_token returned");
  return j.access_token;
}

const iso = (d) => d.toISOString().slice(0, 10);

/* ------------------------------------------------------- Search Console pull */
async function gscQuery(token, property, body) {
  const url = "https://www.googleapis.com/webmasters/v3/sites/"
    + encodeURIComponent(property) + "/searchAnalytics/query";
  const res = await fetch(url, {
    method: "POST",
    headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`GSC query ${res.status}: ${(await res.text()).slice(0, 180)}`);
  }
  return (await res.json()).rows || [];
}

export async function pullGsc(env, saJson, property) {
  await ensureCaseStudySchema(env);
  const token = await googleAccessToken(
    saJson, "https://www.googleapis.com/auth/webmasters.readonly");
  const end = new Date(); end.setDate(end.getDate() - 1);
  const start = new Date(); start.setDate(start.getDate() - 480);
  const range = { startDate: iso(start), endDate: iso(end) };

  const dayRows = await gscQuery(token, property,
    { ...range, dimensions: ["date"], rowLimit: 500 });
  for (let i = 0; i < dayRows.length; i += 50) {
    await env.DB.batch(dayRows.slice(i, i + 50).map((r) => env.DB.prepare(
      `INSERT INTO cs_gsc_daily(date,clicks,impressions,position) VALUES(?,?,?,?)
       ON CONFLICT(date) DO UPDATE SET clicks=excluded.clicks,
         impressions=excluded.impressions, position=excluded.position`)
      .bind(r.keys[0], Math.round(r.clicks || 0),
            Math.round(r.impressions || 0), +(r.position || 0).toFixed(1))));
  }

  const qRows = await gscQuery(token, property,
    { ...range, dimensions: ["query"], rowLimit: 100 });
  if (qRows.length) {
    // Replaced wholesale, not merged: a query that stopped getting
    // impressions should leave the list, not sit there for ever at its best
    // ever position.
    await env.DB.prepare("DELETE FROM cs_gsc_query").run();
    const now = new Date().toISOString();
    for (let i = 0; i < qRows.length; i += 50) {
      await env.DB.batch(qRows.slice(i, i + 50).map((r) => env.DB.prepare(
        `INSERT INTO cs_gsc_query(query,clicks,impressions,position,updated_at)
         VALUES(?,?,?,?,?)`)
        .bind(String(r.keys[0]).slice(0, 200), Math.round(r.clicks || 0),
              Math.round(r.impressions || 0), +(r.position || 0).toFixed(1), now)));
    }
  }
  return { days: dayRows.length, queries: qRows.length };
}

/* ------------------------------------------------------------- GA4 Data API */
export async function pullGa4(env, saJson, propertyId) {
  const token = await googleAccessToken(
    saJson, "https://www.googleapis.com/auth/analytics.readonly");
  const res = await fetch(
    `https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`,
    { method: "POST",
      headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
      body: JSON.stringify({
        dateRanges: [{ startDate: "90daysAgo", endDate: "yesterday" }],
        metrics: [{ name: "sessions" }, { name: "totalUsers" },
                  { name: "screenPageViews" }],
      }) });
  if (!res.ok) {
    throw new Error(`GA4 ${res.status}: ${(await res.text()).slice(0, 180)}`);
  }
  const j = await res.json();
  const v = ((j.rows || [])[0] || {}).metricValues || [];
  const n = (i) => Number((v[i] || {}).value || 0);
  await setMeta(env, "ga4_sessions", n(0));
  await setMeta(env, "ga4_users", n(1));
  await setMeta(env, "ga4_pageviews", n(2));
  await setMeta(env, "ga4_updated", new Date().toISOString());
  return { sessions: n(0), users: n(1), pageviews: n(2) };
}

/* --------------------------------------------------- Bing Webmaster Tools */
export async function pullBing(env, apiKey, siteUrl) {
  const res = await fetch(
    `https://ssl.bing.com/webmaster/api.svc/json/GetRankAndTrafficStats`
    + `?siteUrl=${encodeURIComponent(siteUrl)}&apikey=${encodeURIComponent(apiKey)}`,
    { headers: { "content-type": "application/json" } });
  if (!res.ok) {
    throw new Error(`Bing ${res.status}: ${(await res.text()).slice(0, 180)}`);
  }
  const j = await res.json();
  const rows = (j && j.d) || [];
  const clicks = rows.reduce((a, r) => a + (r.Clicks || 0), 0);
  const impressions = rows.reduce((a, r) => a + (r.Impressions || 0), 0);
  await setMeta(env, "bing_clicks", clicks);
  await setMeta(env, "bing_impressions", impressions);
  await setMeta(env, "bing_updated", new Date().toISOString());
  return { clicks, impressions, days: rows.length };
}

/* ------------------------------------------------------------- the rollups */
const pct = (curr, prior) => (!prior ? null : Math.round(((curr - prior) / prior) * 100));

/**
 * Crawls per engine, out of traffic_log.
 *
 * traffic_log stores the matched user-agent token ("GPTBot"); the report page
 * groups by engine ("ChatGPT"), so the mapping happens here. Anything this
 * map does not know is counted under its own raw name rather than dropped -
 * a crawler nobody has named yet is exactly the thing worth seeing.
 */
async function botRollup(env) {
  let rows = [];
  try {
    rows = (await env.DB.prepare(
      "SELECT bot, COUNT(*) c FROM traffic_log WHERE bot IS NOT NULL GROUP BY bot"
    ).all()).results || [];
  } catch { return { bots: {}, total: 0 }; }
  const bots = {};
  let total = 0;
  for (const r of rows) {
    const engine = BOT_ENGINE[String(r.bot).toLowerCase()] || String(r.bot);
    bots[engine] = (bots[engine] || 0) + r.c;
    total += r.c;
  }
  return { bots, total };
}

async function referralRollup(env) {
  try {
    const rows = (await env.DB.prepare(
      `SELECT referer_host, COUNT(*) c FROM traffic_log
       WHERE referer_host IS NOT NULL GROUP BY referer_host ORDER BY c DESC`
    ).all()).results || [];
    return rows.map((r) => ({ host: r.referer_host, visits: r.c }));
  } catch { return []; }
}

/** Counts that describe the site itself, written by engine/build.py. */
async function siteStructure(env, origin) {
  try {
    const res = await env.ASSETS.fetch(new Request(origin + "/site-stats.json"));
    if (res.ok) return await res.json();
  } catch { /* fall through */ }
  return null;
}

const CLIENT = {
  name: "Number My Boat",
  industry: "Custom boat registration numbers and vinyl lettering",
  location: "Evansdale, Iowa",
  service_area_states: 50,
  website: "https://numbermyboat.com",
  launched: "2026-10-22",
};

const CAPABILITIES = [
  "Static site generated in Python onto a single Cloudflare Worker, with D1 for orders",
  "One pricing function shared by the order form, the Stripe intent and the MCP server - the figure on the button is the code that charges the card",
  "Model Context Protocol server at /mcp: 12 tools an assistant can use to quote, measure and name a boat",
  "llms.txt + llms-full.txt (311 FAQ Q&A) and an explicit 21-bot AI allowlist in robots.txt",
  "Product, FAQPage, BreadcrumbList and Article schema with a named author",
  "Server-side crawl logging: which answer engines actually read the site, which GA4 cannot see",
  "Registration numbers validated against every state's real format before they are cut",
  "Weekly third-party visibility sample: every keyword the domain ranks for in the top 100, and who links to it",
];

export async function buildCaseStudyFeed(env, origin) {
  await ensureCaseStudySchema(env);
  const nowIso = new Date().toISOString();

  const daily = (await env.DB.prepare(
    "SELECT date, clicks, impressions, position FROM cs_gsc_daily ORDER BY date"
  ).all()).results || [];
  const sum = (a) => a.reduce((t, r) => ({
    clicks: t.clicks + r.clicks, impressions: t.impressions + r.impressions }),
    { clicks: 0, impressions: 0 });
  const cutoff = (d) => { const x = new Date(); x.setDate(x.getDate() - d); return iso(x); };
  const allTime = sum(daily);
  const last90 = sum(daily.filter((r) => r.date >= cutoff(90)));
  const prior90 = sum(daily.filter((r) => r.date >= cutoff(180) && r.date < cutoff(90)));
  const avgPos = daily.length
    ? +(daily.reduce((t, r) => t + r.position, 0) / daily.length).toFixed(1) : 0;
  const queries = (await env.DB.prepare(
    `SELECT query, clicks, impressions, position FROM cs_gsc_query
     ORDER BY clicks DESC, impressions DESC LIMIT 25`).all()).results || [];

  // `updated` and `last_error` are the connected-versus-really-zero signal.
  // When nothing has ever been pulled, all_time is NULL rather than a set of
  // zeroes - a zero is a measurement and we have not made one.
  const google_search = daily.length ? {
    all_time: { clicks: allTime.clicks, impressions: allTime.impressions,
                avg_position: avgPos, days: daily.length,
                first_date: daily[0].date, last_date: daily[daily.length - 1].date },
    last_90d: last90,
    prior_90d: prior90,
    delta_90d: { clicks_pct: pct(last90.clicks, prior90.clicks),
                 impressions_pct: pct(last90.impressions, prior90.impressions) },
    daily,
    top_queries: queries,
    updated: await getMeta(env, "gsc_updated"),
    last_error: await getMeta(env, "gsc_last_error"),
  } : { all_time: null,
        updated: await getMeta(env, "gsc_updated"),
        last_error: await getMeta(env, "gsc_last_error") };

  const { bots, total: totalCrawls } = await botRollup(env);
  const monthly = (await env.DB.prepare(
    "SELECT month, citations, crawls FROM cs_ai_monthly ORDER BY month").all()).results || [];
  const ai_search = {
    all_time: {
      total_citations: monthly.reduce((a, m) => a + m.citations, 0),
      total_crawls: totalCrawls,
      bots,
    },
    monthly,
    referrals: await referralRollup(env),
    updated: await getMeta(env, "ai_updated"),
    last_error: await getMeta(env, "ai_last_error"),
    source: "Bing AI Performance Overview for citations; this worker's own "
      + "request log for crawls and referrals",
  };

  const ga4Updated = await getMeta(env, "ga4_updated");
  const analytics = ga4Updated ? {
    sessions_90d: Number(await getMeta(env, "ga4_sessions") || 0),
    users_90d: Number(await getMeta(env, "ga4_users") || 0),
    pageviews_90d: Number(await getMeta(env, "ga4_pageviews") || 0),
    updated: ga4Updated,
    source: "Google Analytics 4 (Data API)",
  } : null;

  // What the shop actually sold.
  //
  // "WHERE test_mode=0" was a filter that excluded nothing: the column exists
  // and no code has ever set it, so every row we submitted while BUILDING the
  // order form counted as a lead. Live, that published 17 of them to a
  // portfolio page. A filter that has never excluded anything cannot be
  // trusted to be excluding tests, so it is treated as untrustworthy until
  // something has actually used it - and then this reports normally with no
  // further change. Flagging is the fix; this is the guard until it exists.
  let orders = null, paid = null, orders30 = null, leadNote = null;
  try {
    const r = await env.DB.prepare(
      `SELECT COUNT(*) n, SUM(CASE WHEN paid=1 THEN 1 ELSE 0 END) p,
              SUM(CASE WHEN ts >= datetime('now','-30 days') THEN 1 ELSE 0 END) r30,
              SUM(COALESCE(test_mode,0)) flagged
       FROM orders WHERE COALESCE(test_mode,0)=0`).first();
    if (r && r.flagged === 0 && (r.n || 0) > 0) {
      leadNote = "Not published: the orders table has " + r.n + " rows and "
        + "none has ever been flagged test_mode, so these cannot be "
        + "distinguished from our own submissions while the order form was "
        + "being built. Reports normally once test rows are flagged.";
    } else if (r) {
      orders = r.n || 0;
      paid = r.p || 0;
      orders30 = r.r30 || 0;
    }
  } catch { /* table may not exist in a fresh database */ }

  const structure = await siteStructure(env, origin);
  const visibility = await searchVisibilityBlock(env, getMeta);

  return {
    schema_version: CASE_STUDY_SCHEMA_VERSION,
    last_updated: nowIso,
    data_as_of: (await getMeta(env, "data_as_of")) || nowIso,
    client: CLIENT,
    // The four figures the contract puts at the top. Every one of them is
    // null until something has actually measured it - a dash on a portfolio
    // page is honest, a zero is a claim.
    headline_stats: {
      total_pages: (structure && structure.pages) ?? null,
      ranked_keywords_top_100: visibility.current
        ? visibility.current.ranked_keywords_top_100 : null,
      unique_referring_domains: visibility.current
        ? visibility.current.unique_referring_domains : null,
      leads_all_time: orders,
      leads_last_30_days: orders30,
    },
    google_search,
    search_visibility: visibility,
    ai_search,
    analytics,
    leads: {
      total_submissions: orders,
      paid_orders: paid,
      note: leadNote,
      source: "Cloudflare D1 (orders table, test orders excluded)",
    },
    site_structure: structure,
    capabilities_shown: CAPABILITIES,
  };
}

/**
 * Pull every connected source, isolating their failures from each other.
 *
 * Per-source try/catch is the whole design. One expired key must not stop the
 * other three, and - more importantly - a source that fails must record WHY
 * in last_error rather than leaving yesterday's number sitting there looking
 * current. The report page reads last_error and says so.
 */
export async function refreshCaseStudy(env, force) {
  await ensureCaseStudySchema(env);
  const out = {};
  const last = await getMeta(env, "refresh_at");
  if (!force && last && Date.now() - Date.parse(last) < 60 * 60 * 1000) {
    return { skipped: "rate limited", last };
  }

  if (env.GSC_SERVICE_ACCOUNT_JSON) {
    try {
      const prop = env.GSC_SITE_URL || "sc-domain:numbermyboat.com";
      out.gsc = await pullGsc(env, env.GSC_SERVICE_ACCOUNT_JSON, prop);
      await setMeta(env, "gsc_updated", new Date().toISOString());
      await setMeta(env, "gsc_last_error", "");
    } catch (e) {
      out.gsc = { error: String(e.message || e) };
      await setMeta(env, "gsc_last_error", String(e.message || e).slice(0, 300));
    }
  }
  if (env.GSC_SERVICE_ACCOUNT_JSON && env.GA4_PROPERTY_ID) {
    try {
      out.ga4 = await pullGa4(env, env.GSC_SERVICE_ACCOUNT_JSON, env.GA4_PROPERTY_ID);
      await setMeta(env, "ga4_last_error", "");
    } catch (e) {
      out.ga4 = { error: String(e.message || e) };
      await setMeta(env, "ga4_last_error", String(e.message || e).slice(0, 300));
    }
  }
  if (env.BING_API_KEY) {
    try {
      out.bing = await pullBing(env, env.BING_API_KEY, "https://numbermyboat.com");
      await setMeta(env, "bing_last_error", "");
    } catch (e) {
      out.bing = { error: String(e.message || e) };
      await setMeta(env, "bing_last_error", String(e.message || e).slice(0, 300));
    }
  }
  if (env.DATAFORSEO_LOGIN && env.DATAFORSEO_PASSWORD) {
    try {
      out.dfs = await pullDataForSeo(env);
      await setMeta(env, "dfs_updated", new Date().toISOString());
      // The backlinks half can fail on its own without losing the rankings,
      // so its error is recorded here rather than thrown away.
      await setMeta(env, "dfs_last_error", out.dfs.backlinks_error || "");
    } catch (e) {
      out.dfs = { error: String(e.message || e) };
      await setMeta(env, "dfs_last_error", String(e.message || e).slice(0, 300));
    }
  }
  await setMeta(env, "refresh_at", new Date().toISOString());
  await setMeta(env, "data_as_of", new Date().toISOString());
  return out;
}
