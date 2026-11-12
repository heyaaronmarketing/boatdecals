/**
 * The MCP server. One server, verb-led tool names, full annotations.
 *
 * Mounted on this worker on purpose: Claude's directory and ChatGPT both need
 * an HTTPS endpoint, and the pricing function, the order pipeline, the fonts
 * and the gates are already here. A separate service would have meant a second
 * copy of the price - which is the one thing the spec forbids outright.
 *
 * NOTHING HERE TAKES MONEY OR TOUCHES AN ORDER. Ordering stays on the site
 * behind the real checkout, so an assistant can quote, test and lay out a name
 * but cannot buy on someone's behalf. That is also why `price_order` exists
 * separately from the order endpoint: quoting a price used to mean calling
 * /api/checkout, which mints a Stripe PaymentIntent, and an assistant quoting
 * prices all day would have buried the account in abandoned intents.
 *
 * NINE TOOLS ARE READ-ONLY. THREE ARE NOT, and it is worth being exact rather
 * than keeping a tidier claim: `start_naming_session`, `vote_on_names` and
 * `submit_riff_candidates` write to naming_sessions, because the engine has to
 * remember what it has already dealt, which jokes the customer rejected, and
 * which riffs survived the gates. They write session state and nothing else -
 * no order, no payment, no mail, no column that identifies a person - and the
 * row is purged after 30 days. The privacy policy was updated for it.
 * verify.py enforces the split: those three may write, the other nine may
 * not, and none of them may reach an order or a card.
 *
 * The performance ledger those three feed is aggregate and lives outside this
 * file on purpose - (lane, mechanism, three integers), no session id, no text
 * a customer typed. The SQL for it is in worker/index.js so that the gate on
 * this file can keep saying the only table it names is naming_sessions.
 */
import { radioGate, overuseGate, fitGate, noveltyGate, widthIn,
         loadLexicon } from "./gates.js";
import { D } from "./gates-data.js";
// The same file the website runs for these two - see engine/shared_js.py.
import { checkRegistration, decodeHin, toPlain } from "./decode.js";
import { INTERVIEW, profileFrom, missingQuestions, dealRound, applyVote,
         rationale, gateSummary, bareBoat, ROUND_SIZE, FINALISTS,
         laneKeys, provenFor, ledgerDeltas, riffBrief,
         gateRiff, cardHeading } from "./engine.js";

const PROTOCOL = "2024-11-05";
const SERVER = { name: "numbermyboat", version: "0.1.0" };

/** Catalog, read once per isolate from the site's own built file. */
let CATALOG = null;
async function catalog(env) {
  if (CATALOG) return CATALOG;
  const r = await env.ASSETS.fetch("https://numbermyboat.com/catalog.json");
  if (!r.ok) throw new Error("catalog.json is not being served");
  CATALOG = await r.json();
  return CATALOG;
}

/**
 * Everything the ledger has to say about one session, in one place.
 *
 * Two questions get asked at the same three moments: which mechanisms are
 * proven for this customer's lane, and what should the brief show. Reading
 * them together means one query per tool call rather than three.
 */
async function ledgerFor(env, ctx, profile) {
  if (!ctx.ledgerRows) return { rows: [], proven: [] };
  let rows = [];
  try {
    rows = await ctx.ledgerRows(env, laneKeys(profile));
  } catch (e) {
    // A cold ledger and a broken ledger must both degrade to "we have no
    // evidence yet", never to a failed round. The customer is mid-sentence.
    console.log("ledger read failed", e && e.message);
    return { rows: [], proven: [] };
  }
  const lane = (profile.lanes || [])[0] || "any";
  return { rows, proven: provenFor(rows, lane).proven, lane };
}

/**
 * killed_mechs, in whichever shape the column is holding.
 *
 * A REAL BUG, found while wiring the brief in. start_naming_session wrote
 * this column as a JSON array of codes; vote_on_names wrote it as a JSON
 * object of counts. So calling start_naming_session again after a vote - which
 * is exactly what a host does when the customer adds "oh, and it's a
 * pontoon" - parsed an object, concat'd it into an array as a single object,
 * and silently forgot every mechanism he had rejected. He would have been
 * dealt the same jokes he had just killed, and nothing would have said so.
 *
 * Counts are the canonical shape, because the two-kills rule needs them. An
 * array is read as two kills each: a host passing killed_mechanisms is
 * relaying a customer saying "stop offering me these", which is at least as
 * strong a statement as killing two of them.
 */
export function killCounts(raw) {
  let v = {};
  try { v = raw ? JSON.parse(raw) : {}; } catch (e) { v = {}; }
  if (Array.isArray(v)) {
    return Object.fromEntries(v.filter((m) => typeof m === "string")
      .map((m) => [m, 2]));
  }
  return (v && typeof v === "object") ? v : {};
}

/** Which mechanisms are retired: killed twice, with nothing of theirs kept. */
export function retiredMechs(counts, keptMechs) {
  return Object.keys(counts).filter(
    (m) => (counts[m] || 0) >= 2 && !((keptMechs || {})[m] > 0));
}

/** Fire-and-forget accrual. A round must never fail because a counter did. */
function bump(env, ctx, deltas) {
  if (!ctx.ledgerBump || !deltas.length) return;
  ctx.ledgerBump(env, deltas).catch(
    (e) => console.log("ledger write failed", e && e.message));
}

const txt = (o) => ({
  content: [{ type: "text", text: JSON.stringify(o, null, 1) }],
});
const err = (msg) => ({
  content: [{ type: "text", text: msg }], isError: true,
});

// ---------------------------------------------------------------------------
// Tools. Descriptions are written in boater language, not catalog language,
// because a model picks a tool off its description and "transom" is the word
// the customer will have used.
// ---------------------------------------------------------------------------
const TOOLS = [
  {
    name: "get_products",
    title: "What we make and what it costs",
    description:
      "Boat registration numbers, boat names, or both as a set - with every "
      + "height, colour and lettering style we actually cut, and which styles "
      + "are legal for registration numbers. Start here before quoting "
      + "anything.",
    annotations: { title: "What we make and what it costs",
                   readOnlyHint: true, destructiveHint: false,
                   idempotentHint: true, openWorldHint: false },
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    async run(_args, env) {
      const c = await catalog(env);
      return txt({
        products: c.products, options: c.options, shipping: c.shipping,
        fulfillment: c.fulfillment,
        pricing_note: "Prices here are advisory. Call price_order for the "
          + "figure that will actually be charged.",
      });
    },
  },
  {
    name: "price_order",
    title: "Price a set exactly",
    description:
      "The real price for a specific set - product, lettering height, outline "
      + "or not, any extras. Runs the same pricing function the website's own "
      + "order form and the card charge use, so the number is what the "
      + "customer will pay. Use this rather than adding prices up yourself.",
    annotations: { title: "Price a set exactly", readOnlyHint: true,
                   destructiveHint: false, idempotentHint: true,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        kind: { type: "string", enum: ["numbers", "name", "both"],
                description: "numbers = registration numbers, name = boat "
                  + "name, both = the bundle" },
        height: { type: "string", enum: ["3", "4", "5", "6"],
                  description: "Lettering height in inches" },
        outline: { type: "boolean",
                   description: "Contrasting second layer behind the letters" },
      },
      required: ["kind"], additionalProperties: false,
    },
    async run(args, env, ctx) {
      const amount = ctx.priceOf({
        kind: args.kind, height: args.height || "3",
        outline: args.outline ? "yes" : "",
      });
      return txt({
        amount_usd: amount, shipping_usd: 0,
        priced: { kind: args.kind, height: args.height || "3",
                  outline: !!args.outline },
        note: "Free shipping to all 50 states. Nothing is charged until the "
          + "customer checks out on the website.",
      });
    },
  },
  {
    name: "test_boat_name",
    title: "Test a boat name before you commit it to vinyl",
    description:
      "Run a name through the four tests that matter: can the Coast Guard "
      + "write it down from hearing it once on the radio, how wide it "
      + "finishes in a given lettering style at each height we cut, whether "
      + "it is one of the names at every ramp in America, and whether a "
      + "'new' name is really one we already sell. Works on any name, not "
      + "just ours. Give the transom's flat run in inches if you know it.",
    annotations: { title: "Test a boat name", readOnlyHint: true,
                   destructiveHint: false, idempotentHint: true,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string", maxLength: 60,
                description: "The name as it would be cut" },
        font: { type: "string",
                description: "One of the ten lettering styles; defaults to "
                  + "Arial Bold" },
        transom_in: { type: "number",
                      description: "Inches of flat run above the waterline" },
      },
      required: ["name"], additionalProperties: false,
    },
    async run(args, env) {
      await loadLexicon(env);
      const name = String(args.name || "").slice(0, 60);
      const font = args.font || "Arial Bold";
      if (!D.FONTS[font]) {
        return err(`We do not cut ${font}. The styles are: `
          + Object.keys(D.FONTS).join(", "));
      }
      const radio = radioGate(name);
      const over = overuseGate(name);
      const fit = fitGate(name, font,
        Number.isFinite(args.transom_in) ? args.transom_in : null);
      return txt({
        name,
        radio: { verdict: radio.verdict, readback: radio.readback,
                 will_have_to_spell_it: radio.spell_out,
                 joke_needs_to_be_seen: radio.visual_only,
                 notes: radio.reasons },
        fit: { font, widths_in: fit.widths_in, verdict: fit.verdict,
               tallest_that_fits: fit.best_height,
               accuracy: `+/-${fit.error_pct}%`, notes: fit.reasons },
        how_common: { tier: over.tier, note: over.note,
                      honesty: "Market data, not a registry. We cannot tell "
                        + "you what is already on your lake or at your "
                        + "marina." },
        dealable: radio.dealable,
      });
    },
  },
  {
    name: "check_name_is_new",
    title: "Is this name already one of ours",
    description:
      "Checks a name against our own bank of curated names and reports the "
      + "closest match. Use it before claiming a name is original.",
    annotations: { title: "Is this name already one of ours",
                   readOnlyHint: true, destructiveHint: false,
                   idempotentHint: true, openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: { name: { type: "string", maxLength: 60 } },
      required: ["name"], additionalProperties: false,
    },
    async run(args, env, ctx) {
      const names = await ctx.bankNames(env);
      return txt(noveltyGate(String(args.name || "").slice(0, 60), names));
    },
  },
  {
    name: "check_registration_layout",
    title: "Check a registration number before we cut it",
    description:
      "Checks a state registration number the way we check it before cutting: "
      + "is the prefix a real vessel prefix (several states differ from the "
      + "postal code - California boats are CF, not CA), does it read as "
      + "prefix-numbers-letters, does the state actually issue those letters, "
      + "and is it spaced the way the rule wants. Also gives the finished "
      + "width at each legal height. It flags, it never refuses - every order "
      + "gets a human proof before anything is cut.",
    annotations: { title: "Check a registration number",
                   readOnlyHint: true, destructiveHint: false,
                   idempotentHint: true, openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        number: { type: "string", maxLength: 24,
                  description: "As printed on the registration card, "
                    + "e.g. IA 3717 ZW" },
        height_in: { type: "number",
                     description: "Lettering height in inches; 3 is the "
                       + "federal minimum" },
        transom_in: { type: "number",
                      description: "Inches of flat run on the forward hull" },
      },
      required: ["number"], additionalProperties: false,
    },
    async run(args) {
      const r = checkRegistration(String(args.number || "").slice(0, 24));
      const h = Number.isFinite(args.height_in) ? args.height_in : 3;
      // Registration numbers are block-only by law, so the width is quoted in
      // a block face rather than whichever face the customer liked.
      const fit = fitGate(r.fixed || r.compact || String(args.number || ""),
        "Arial Bold",
        Number.isFinite(args.transom_in) ? args.transom_in : null, [3, 4, 5, 6]);
      return txt({
        number: String(args.number || ""),
        reads_as: r.fixed,
        state: r.state,
        verdict: r.level,
        note: r.msg ? toPlain(r.msg) : "Reads as a normal state format.",
        legal_height: h >= 3
          ? `${h}" clears the 3" federal minimum.`
          : `${h}" is under the 3" federal minimum - 33 CFR 173.27 requires `
            + "at least 3 inches. Go up to 3\" or taller.",
        height_is_legal: h >= 3,
        block_characters: "We cut registration numbers in plain vertical "
          + "block only, so that requirement is handled.",
        width: { font: "Arial Bold", widths_in: fit.widths_in,
                 accuracy: `+/-${fit.error_pct}%`, notes: fit.reasons },
        honesty: "This flags problems, it never refuses an order. The prefix "
          + "table is compiled from secondary sources and states issue "
          + "sequentially, so older hulls carry retired formats. Every order "
          + "gets a human proof before anything is cut.",
      });
    },
  },
  {
    name: "decode_hull_number",
    title: "Decode a hull identification number",
    description:
      "Reads the 12-character HIN stamped into the starboard side of the "
      + "transom: who built the boat, its serial, when it was built and its "
      + "model year. Useful on a used boat. A HIN is not a registration "
      + "number - the HIN is the builder's and never changes, the "
      + "registration number is issued by the state and is the one that has "
      + "to be displayed.",
    annotations: { title: "Decode a hull identification number",
                   readOnlyHint: true, destructiveHint: false,
                   idempotentHint: true, openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        hin: { type: "string", maxLength: 24,
               description: "The 12-character hull identification number" },
      },
      required: ["hin"], additionalProperties: false,
    },
    async run(args) {
      const r = decodeHin(String(args.hin || "").slice(0, 24));
      if (!r.ok) return err(r.msg);
      return txt({
        hin: r.hin, manufacturer_code: r.mic,
        manufacturer: r.manufacturer,
        manufacturer_note: r.manufacturer_note,
        serial: r.serial, date_code: r.date_code, format: r.format,
        built: r.built, model_year: r.model_year,
        notes: r.notes.map(toPlain),
      });
    },
  },
  {
    name: "start_naming_session",
    title: "Name a boat properly - interview, then a gated round",
    description:
      "Runs the real naming process rather than listing names. Asks what the "
      + "boat is, who is usually aboard, what kind of name they want and how "
      + "much flat run they have, then deals a round of up to eight names "
      + "from a bank of 1,089 curated ones - every one already tested for the "
      + "radio, measured against their transom, and checked against the names "
      + "you see at every ramp. Pass the answers you have; it will say what "
      + "else it needs. Pass the session id back to get another round, and "
      + "killed_mechanisms to stop it offering the same kind of joke again.",
    annotations: { title: "Name a boat properly",
                   readOnlyHint: false,        // writes session state only
                   destructiveHint: false, idempotentHint: false,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string", maxLength: 40,
                      description: "Omit to start; pass it back to continue" },
        answers: {
          type: "object",
          description: "Interview answers in the customer's own words. Keys: "
            + "boat, aboard, vibe, transom, work, story, port. All optional "
            + "except boat.",
          additionalProperties: { type: "string", maxLength: 400 },
        },
        killed_mechanisms: {
          type: "array", items: { type: "string" },
          description: "Short codes of joke mechanisms the customer has "
            + "rejected - hp, pm, tt, dp, dm, ba, pj, an, lt, md",
        },
        font: { type: "string", description: "Defaults to Arial Bold" },
        size: { type: "number", description: "Names per round, 6-8" },
      },
      additionalProperties: false,
    },
    async run(args, env, ctx) {
      await loadLexicon(env);
      const now = new Date().toISOString();
      let prior = null;
      const sid = String(args.session_id || "").slice(0, 40);

      if (sid) {
        prior = await env.DB.prepare(
          "SELECT * FROM naming_sessions WHERE id = ?").bind(sid).first();
        if (!prior) {
          return err("That naming session has expired or never existed. "
            + "Sessions are kept for 30 days. Start a new one by leaving "
            + "session_id out.");
        }
      }

      const answers = { ...(prior ? JSON.parse(prior.answers || "{}") : {}),
                        ...(args.answers || {}) };
      // Bound what is stored. Nothing here needs an essay, and a long free
      // text field is the one place a customer might paste something we have
      // no business keeping.
      for (const k of Object.keys(answers)) {
        if (!INTERVIEW.some((q) => q.id === k)) { delete answers[k]; continue; }
        answers[k] = String(answers[k] || "").slice(0, 400);
      }

      const profile = profileFrom(answers);
      const missing = missingQuestions(profile, answers);

      if (!answers.boat) {
        return txt({
          session_id: null,
          next_questions: INTERVIEW.filter((q) => q.required || !answers[q.id])
            .map((q) => ({ id: q.id, ask: q.ask, why: q.why,
                           required: !!q.required })),
          note: "Ask what the boat is first - it decides which names fit. The "
            + "rest can come as they talk; nothing is dealt until we know who "
            + "is aboard, because that sets how blue a name may be.",
        });
      }

      const bank = await ctx.bankRows(env);
      const counts = killCounts(prior ? prior.killed_mechs : null);
      for (const m of (args.killed_mechanisms || [])) {
        counts[String(m).slice(0, 8)] = Math.max(2, counts[m] || 0);
      }
      const keptMechs = prior ? killCounts(prior.kept_mechs) : {};
      const killed = retiredMechs(counts, keptMechs);
      const shown = prior ? JSON.parse(prior.shown || "[]") : [];
      const riffs = prior ? JSON.parse(prior.riffs || "[]") : [];
      const led = await ledgerFor(env, ctx, profile);
      const round = dealRound(bank, profile, {
        size: args.size || 8, exclude: shown, killedMechs: killed,
        font: args.font || "Arial Bold", riffs, proven: led.proven,
        seed: (sid || now) + ":" + (prior ? prior.rounds + 1 : 1),
      });
      // Exposures. Every name dealt is evidence about its mechanism whether
      // or not the customer ever votes - a name shown and ignored is the
      // denominator the keep-rate needs.
      bump(env, ctx, ledgerDeltas(profile, round.names.map(
        (n) => ({ name: n.name, mechanism_code: n.mechanism_code,
                  source: n.source })), "exposures"));

      const id = sid || crypto.randomUUID().replace(/-/g, "").slice(0, 24);
      const nextShown = shown.concat(round.names.map((n) => n.name));
      await env.DB.prepare(
        `INSERT INTO naming_sessions
           (id, ts, updated, answers, profile, shown, killed_mechs, kept,
            rounds, harvest_optin)
         VALUES (?,?,?,?,?,?,?,?,?,0)
         ON CONFLICT(id) DO UPDATE SET
           updated=excluded.updated, answers=excluded.answers,
           profile=excluded.profile, shown=excluded.shown,
           killed_mechs=excluded.killed_mechs, rounds=excluded.rounds`
      ).bind(id, prior ? prior.ts : now, now, JSON.stringify(answers),
             JSON.stringify(profile), JSON.stringify(nextShown),
             JSON.stringify(counts), "[]",
             (prior ? prior.rounds : 0) + 1).run();

      return txt({
        session_id: id,
        round: (prior ? prior.rounds : 0) + 1,
        names: round.names,
        still_worth_asking: missing.map((q) => ({ id: q.id, ask: q.ask,
                                                  why: q.why })),
        // The engine says what it filtered and why. 1,089 in and 8 out is only
        // defensible if the other 1,081 can be accounted for.
        how_this_round_was_built: {
          names_in_bank: round.considered,
          passed_every_gate: round.eligible,
          dealt: round.names.length,
          set_aside: round.rejected,
          reading: "radio = unusable on a VHF; level = cruder than who is "
            + "aboard allows; in_joke = needs a trade we have not been told; "
            + "fit = will not go on the transom at any height; tier1 = one of "
            + "the names at every ramp in America",
        },
        riff_slots_available: round.riff_slots,
        // The brief. This is how the host model is made funny on purpose
        // rather than by luck: the mechanisms that have actually been landing
        // in his lane, real exemplars, the house register, and a banned list.
        riff_brief: round.riff_slots > 0
          ? riffBrief(bank, profile, { shown: nextShown,
              killed_mechs_count: counts, kept_mechs: keptMechs,
              rejected_mechs: killed }, led.rows, round.riff_slots)
          : null,
        honesty: "Every name here is from our own curated bank, already "
          + "tested. How common a name is comes from market data, not a "
          + "registry - we cannot tell anyone what is already on their lake.",
      });
    },
  },
  {
    name: "vote_on_names",
    title: "Keep the ones that landed, kill the ones that did not",
    description:
      "Records which names the customer liked and which he did not, then "
      + "deals the next round of four. Killing names does more than skip "
      + "them: kill two of the same kind of joke and the engine stops "
      + "offering that kind of joke altogether, which is the single most "
      + "useful thing a session learns. Once three names are kept, call "
      + "reveal_finalists.",
    annotations: { title: "Keep and kill", readOnlyHint: false,
                   destructiveHint: false, idempotentHint: false,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string", maxLength: 40 },
        kept: { type: "array", items: { type: "string", maxLength: 60 },
                description: "Names he liked, exactly as they were shown" },
        killed: { type: "array", items: { type: "string", maxLength: 60 },
                  description: "Names he rejected" },
      },
      required: ["session_id"], additionalProperties: false,
    },
    async run(args, env, ctx) {
      await loadLexicon(env);
      const sid = String(args.session_id || "").slice(0, 40);
      const prior = await env.DB.prepare(
        "SELECT * FROM naming_sessions WHERE id = ?").bind(sid).first();
      if (!prior) {
        return err("That naming session has expired or never existed. "
          + "Sessions are kept for 30 days.");
      }
      const bank = await ctx.bankRows(env);
      const profile = JSON.parse(prior.profile || "{}");

      const state = applyVote({
        kept: JSON.parse(prior.kept || "[]"),
        killed_names: JSON.parse(prior.killed_names || "[]"),
        kept_mechs: killCounts(prior.kept_mechs),
        killed_mechs_count: killCounts(prior.killed_mechs),
      }, bank, args.kept || [], args.killed || []);

      const shown = JSON.parse(prior.shown || "[]");
      const riffs = JSON.parse(prior.riffs || "[]");
      const rounds = (prior.rounds || 0) + 1;
      const now = new Date().toISOString();

      // Keeps and kills, filed against the mechanism, per lane. This is the
      // only place in the whole build where a human being's taste becomes
      // data, so it happens on the vote and nowhere else.
      const byN = new Map(bank.map((n) => [n.name.toLowerCase(), n]));
      const asRows = (list) => (list || []).map((x) => {
        const b = byN.get(String(x).toLowerCase());
        if (b) return { name: b.name, mechanism_code: b.mechanism_code };
        const r = riffs.find(
          (q) => q.name.toLowerCase() === String(x).toLowerCase());
        return r ? { name: r.name, mechanism_code: r.mechanism_code,
                     source: "riff" } : null;
      }).filter(Boolean);
      const led = await ledgerFor(env, ctx, profile);
      bump(env, ctx, [
        ...ledgerDeltas(profile, asRows(args.kept), "keeps"),
        ...ledgerDeltas(profile, asRows(args.killed), "kills"),
      ]);

      // Rounds of four from here. Eight is a shortlist; four is a decision.
      const round = state.finalists_ready ? null : dealRound(bank, profile, {
        size: ROUND_SIZE, exclude: shown,
        killedMechs: state.rejected_mechs, riffs, proven: led.proven,
        seed: sid + ":" + rounds,
      });
      if (round) {
        bump(env, ctx, ledgerDeltas(profile, round.names.map(
          (n) => ({ name: n.name, mechanism_code: n.mechanism_code,
                    source: n.source })), "exposures"));
      }
      const nextShown = round
        ? shown.concat(round.names.map((n) => n.name)) : shown;

      await env.DB.prepare(
        `UPDATE naming_sessions SET updated=?, shown=?, kept=?,
           killed_names=?, kept_mechs=?, killed_mechs=?, rounds=?
         WHERE id=?`
      ).bind(now, JSON.stringify(nextShown), JSON.stringify(state.kept),
             JSON.stringify(state.killed_names),
             JSON.stringify(state.kept_mechs),
             JSON.stringify(state.killed_mechs_count), rounds, sid).run();

      return txt({
        session_id: sid,
        kept_so_far: state.kept,
        killed_so_far: state.killed_names.length,
        finalists_ready: state.finalists_ready,
        next_round: round ? round.names : null,
        // Round 2's brief, with the mechanisms he has already killed taken
        // out of it. That subtraction is the whole point of the tournament:
        // the ledger knows what lands on strangers, he knows what lands on
        // him, and he wins.
        riff_brief: round && round.riff_slots > 0
          ? riffBrief(bank, profile, { ...state, shown: nextShown },
                      led.rows, round.riff_slots)
          : null,
        what_the_session_has_learned: {
          landing: state.proven_mechs,
          not_landing: state.rejected_mechs,
          reading: "Two kills of the same mechanism with nothing kept and we "
            + "stop offering it. One kill is a name he did not like; two is "
            + "the joke itself not working.",
        },
        next_step: state.finalists_ready
          ? `He has kept ${state.kept.length}. Call reveal_finalists.`
          : `Keep going - ${FINALISTS - state.kept.length} more to keep.`,
      });
    },
  },
  {
    name: "submit_riff_candidates",
    title: "Submit your own names for gating",
    description:
      "The only way a name you invented can enter a round. Send names built "
      + "from the customer's own material - his dog, his lake, his trade, the "
      + "story he told - following the riff_brief the round returned. Every "
      + "one is gated exactly like a bank name: the radio test, the width "
      + "against his transom, the overuse check, how crude it is against who "
      + "is aboard, and a novelty check against all 1,089 bank names so a "
      + "near-copy is rejected as a copy rather than passed off as "
      + "creativity. Survivors join the next round at no more than a third of "
      + "it; the rest are dropped. You do not choose the round - the ranker "
      + "does, from what survives.",
    annotations: { title: "Submit riffs for gating",
                   readOnlyHint: false,       // writes session state only
                   destructiveHint: false, idempotentHint: false,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string", maxLength: 40 },
        candidates: {
          type: "array", maxItems: 12,
          description: "Up to twelve. Send more than the slots available - "
            + "most of a good batch will fail a gate, and that is the "
            + "system working.",
          items: {
            type: "object",
            properties: {
              name: { type: "string", maxLength: 40,
                      description: "The name exactly as it would be cut" },
              mechanism: { type: "string",
                           description: "How the joke is built: hp homophone, "
                             + "pm portmanteau, tt title twist, dp deadpan, "
                             + "dm double meaning, ba backronym, pj in-joke, "
                             + "an anagram, lt literal truth, md "
                             + "misdirection, sincere no joke at all" },
              why: { type: "string", maxLength: 160,
                     description: "One line on what of his it is built from. "
                       + "Shown back to him at the reveal, so it must be "
                       + "true." },
            },
            required: ["name", "mechanism"], additionalProperties: false,
          },
        },
        font: { type: "string", description: "Defaults to Arial Bold" },
      },
      required: ["session_id", "candidates"], additionalProperties: false,
    },
    async run(args, env, ctx) {
      await loadLexicon(env);
      const sid = String(args.session_id || "").slice(0, 40);
      const prior = await env.DB.prepare(
        "SELECT * FROM naming_sessions WHERE id = ?").bind(sid).first();
      if (!prior) {
        return err("That naming session has expired or never existed. "
          + "Sessions are kept for 30 days.");
      }
      const profile = JSON.parse(prior.profile || "{}");
      const held = JSON.parse(prior.riffs || "[]");
      const shown = JSON.parse(prior.shown || "[]");
      const bankN = await ctx.bankNames(env);
      const seen = new Set([...held.map((r) => r.name.toLowerCase()),
                            ...shown.map((n) => String(n).toLowerCase())]);
      const deps = { radioGate, overuseGate, fitGate, noveltyGate };

      const kept = [], dropped = [];
      for (const cand of (args.candidates || []).slice(0, 12)) {
        const g = gateRiff(cand, profile, bankN, deps,
                           { font: args.font || "Arial Bold" });
        if (!g.ok) { dropped.push({ name: g.name, reason: g.reason }); continue; }
        if (seen.has(g.name.toLowerCase())) {
          dropped.push({ name: g.name, reason: "already submitted" });
          continue;
        }
        seen.add(g.name.toLowerCase());
        kept.push(g);
      }

      const riffs = held.concat(kept.map((g) => g.row));
      await env.DB.prepare(
        "UPDATE naming_sessions SET updated = ?, riffs = ? WHERE id = ?")
        .bind(new Date().toISOString(), JSON.stringify(riffs.slice(-24)), sid)
        .run();

      return txt({
        session_id: sid,
        survived: kept.map((g) => ({
          name: g.row.name,
          mechanism: g.row.humor_mechanism,
          radio: { verdict: g.radio.verdict, readback: g.radio.readback,
                   will_spell_it: g.radio.spell_out },
          fit: g.fit
            ? { verdict: g.fit.verdict, tallest_that_fits: g.fit.best_height }
            : { note: "No transom measurement in this session." },
          how_common: g.over.tier,
          distance_from_the_nearest_bank_name: g.novelty.similarity,
        })),
        dropped: dropped.length,
        // Per-name reasons, for the log and for the next batch - not for the
        // customer. A name shown with an apology is worse than a name never
        // shown, and this endpoint is how the host learns which walls it keeps
        // walking into.
        why_they_dropped: dropped,
        next_step: kept.length
          ? "Call vote_on_names to deal the next round - the survivors are in "
            + "the pool now and will be ranked against the bank like anything "
            + "else. Riffs are capped at a third of a round."
          : "Nothing survived. Read why_they_dropped, then send another batch "
            + "built on his own words rather than on our names.",
        honesty: "We gate what can be measured: the radio, the width, how "
          + "common it is, how crude the words are. A word list cannot catch "
          + "a double meaning - that is what a double meaning is - so the "
          + "ceiling in the brief is yours to honour, not ours to enforce.",
      });
    },
  },
  {
    name: "reveal_finalists",
    title: "The Final 3, with the reasons and the radio call",
    description:
      "The payoff. Takes the names he kept and presents the final three: why "
      + "each one survived, written from what he actually told us; the radio "
      + "readback to say out loud; what the gates found in plain words; the "
      + "width at the height we would cut; and a card he can send his family "
      + "to vote on. Also the link to order each one.",
    annotations: { title: "The Final 3", readOnlyHint: true,
                   destructiveHint: false, idempotentHint: true,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        session_id: { type: "string", maxLength: 40 },
        font: { type: "string", description: "Defaults to Arial Bold" },
      },
      required: ["session_id"], additionalProperties: false,
    },
    async run(args, env, ctx) {
      await loadLexicon(env);
      const sid = String(args.session_id || "").slice(0, 40);
      const prior = await env.DB.prepare(
        "SELECT * FROM naming_sessions WHERE id = ?").bind(sid).first();
      if (!prior) return err("That naming session has expired.");

      const profile = JSON.parse(prior.profile || "{}");
      const kept = JSON.parse(prior.kept || "[]");
      if (!kept.length) {
        return err("Nothing has been kept yet in this session. Deal a round "
          + "with start_naming_session and record the keeps with "
          + "vote_on_names first.");
      }
      const bank = await ctx.bankRows(env);
      // Riffs that survived the gates and then won a round are finalists like
      // any other name. Leaving them out of this map meant a customer could
      // keep three names, one of them built from his own dog, and get a Final
      // 2 with no explanation of where the third went.
      const riffs = JSON.parse(prior.riffs || "[]");
      const byName = new Map([...bank, ...riffs]
        .map((n) => [n.name.toLowerCase(), n]));
      const font = args.font || "Arial Bold";
      const site = env.SITE_URL || "https://numbermyboat.com";

      const finalists = [];
      for (const name of kept.slice(0, FINALISTS)) {
        const n = byName.get(name.toLowerCase());
        if (!n) continue;
        const radio = radioGate(n.name);
        const fit = fitGate(n.name, font,
          profile.transom_in != null ? profile.transom_in : null);
        const over = overuseGate(n.name);
        finalists.push({
          name: n.name,
          why_this_one: rationale(n, profile, radio, fit),
          say_it_on_the_radio: radio.readback,
          what_we_checked: gateSummary(radio, fit, over),
          width: { font, widths_in: fit.widths_in,
                   tallest_that_fits: fit.best_height,
                   accuracy: `+/-${fit.error_pct}%` },
          // Deep link into the real order form with the name already in it.
          // The buy path is here and in the studio, never in round one.
          order_it: `${site}/design/?name=${encodeURIComponent(n.name)}`
            + `&font=${encodeURIComponent(font)}`,
          see_it_rendered: `${site}/api/outline?t=`
            + `${encodeURIComponent(n.name)}&f=${encodeURIComponent(font)}`,
        });
      }

      return txt({
        session_id: sid,
        finalists,
        // The spec's Final 3 card: something he sends his wife, not a receipt.
        card_for_the_family: {
          heading: cardHeading(finalists.length, profile.boat_raw),
          names: finalists.map((f) => f.name),
          ask: "Which one? Reply with 1, 2 or 3.",
          footer: "Cut in Evansdale, Iowa. Free shipping, all 50 states.",
        },
        price_note: "A boat name set starts at $23 and a name plus "
          + "registration numbers is $44. Call price_order for the exact "
          + "figure once he picks a height.",
        honesty: "Every reason above is built from what he told us in the "
          + "interview. Where we had nothing to go on, it says how the joke "
          + "works instead of inventing a reason.",
      });
    },
  },
  {
    name: "get_policies",
    title: "Shipping, returns, proofs and the warranty",
    description:
      "What we promise and what we do not: the proof step before anything is "
      + "cut, how long shipping takes, what happens if it is wrong, and how "
      + "long the film lasts. Quote these rather than guessing.",
    annotations: { title: "Shipping, returns, proofs and the warranty",
                   readOnlyHint: true, destructiveHint: false,
                   idempotentHint: true, openWorldHint: false },
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    async run(_args, env) {
      const c = await catalog(env);
      return txt({
        proof: `Nothing is cut until the customer approves a proof. We send `
          + `it within ${c.fulfillment.proof_hours} hours.`,
        charge: "Charged at checkout, before the proof.",
        shipping: "Free to all 50 states. Ships 1-2 business days after the "
          + "proof is approved.",
        returns: "Wrong or defective, we recut it. Custom lettering that was "
          + "approved on the proof and cut correctly is not returnable - that "
          + "is what the proof step is for.",
        warranty: "Outdoor-grade cast vinyl, rated for marine use. We do not "
          + "publish a year figure because we have not run the test "
          + "ourselves.",
        registration_numbers: "Must be plain block characters at least 3 "
          + "inches tall - 33 CFR 173.27. We will not cut a script face for "
          + "registration numbers.",
        full_text: { shipping_and_returns: `${c.url}/shipping-and-returns/`,
                     warranty: `${c.url}/warranty/`,
                     terms: `${c.url}/terms/`,
                     privacy: `${c.url}/privacy/` },
      });
    },
  },
  {
    name: "measure_lettering",
    title: "How wide will this come out",
    description:
      "Width in inches for any text in any of the ten lettering styles at any "
      + "height, measured from the real font files we cut from - not "
      + "estimated from a character count. Use it to answer 'will this fit'.",
    annotations: { title: "How wide will this come out", readOnlyHint: true,
                   destructiveHint: false, idempotentHint: true,
                   openWorldHint: false },
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", maxLength: 60 },
        height_in: { type: "number", description: "Cap height in inches" },
        fonts: { type: "array", items: { type: "string" },
                 description: "Omit for every style we cut" },
      },
      required: ["text"], additionalProperties: false,
    },
    async run(args) {
      const text = String(args.text || "").slice(0, 60);
      if (!text.trim()) return err("Give me some text to measure.");
      const h = Number.isFinite(args.height_in) ? args.height_in : 4;
      if (h <= 0 || h > 24) return err("Height has to be between 0 and 24 inches.");
      const want = (args.fonts && args.fonts.length)
        ? args.fonts : Object.keys(D.FONTS);
      const out = {};
      for (const f of want) {
        if (!D.FONTS[f]) { out[f] = { error: "not a style we cut" }; continue; }
        const [w, missing] = widthIn(text, f, h);
        out[f] = { width_in: Math.round(w * 10) / 10,
                   ...(missing.length ? { cannot_cut: missing } : {}) };
      }
      return txt({
        text, height_in: h, widths: out, accuracy: `+/-${D.FIT_ERROR_PCT}%`,
        note: "Measured from the actual font files. Measure the flat run "
          + "above the waterline before ordering.",
      });
    },
  },
];

const BY_NAME = new Map(TOOLS.map((t) => [t.name, t]));

// ---------------------------------------------------------------------------
// JSON-RPC 2.0 over HTTP.
// ---------------------------------------------------------------------------
const rpcOk = (id, result) => ({ jsonrpc: "2.0", id, result });
const rpcErr = (id, code, message) => ({ jsonrpc: "2.0", id,
                                         error: { code, message } });

async function dispatch(msg, env, ctx) {
  const { id, method, params } = msg || {};
  switch (method) {
    case "initialize":
      return rpcOk(id, {
        protocolVersion: PROTOCOL,
        capabilities: { tools: { listChanged: false } },
        serverInfo: SERVER,
        instructions:
          "Number My Boat cuts boat registration numbers and boat-name "
          + "lettering in Evansdale, Iowa and ships to all 50 states free. "
          + "Every tool here is read-only: quote, test and measure freely, "
          + "but ordering happens on the website. Price through price_order "
          + "rather than adding figures up. Registration numbers are legally "
          + "required to be plain block characters at least 3 inches tall. "
          + "On how common a name is we have market data, not a registry - "
          + "never tell a customer a name is taken at their marina.",
      });
    case "notifications/initialized":
    case "initialized":
      return null;                       // notification: no reply
    case "ping":
      return rpcOk(id, {});
    case "tools/list":
      return rpcOk(id, {
        tools: TOOLS.map((t) => ({
          name: t.name, title: t.title, description: t.description,
          inputSchema: t.inputSchema, annotations: t.annotations,
        })),
      });
    case "tools/call": {
      const t = BY_NAME.get(params && params.name);
      if (!t) return rpcErr(id, -32602, `no tool named ${params && params.name}`);
      try {
        return rpcOk(id, await t.run((params && params.arguments) || {},
                                      env, ctx));
      } catch (e) {
        // Reported as a tool error, not a protocol error: the model can read
        // it, say something useful and try again.
        return rpcOk(id, err(`That did not work: ${String(e.message || e)}`));
      }
    }
    default:
      return rpcErr(id, -32601, `unsupported method ${method}`);
  }
}

export async function handleMcp(request, env, ctx) {
  const cors = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "content-type, mcp-protocol-version",
    "access-control-allow-methods": "POST, OPTIONS",
  };
  if (request.method === "OPTIONS") return new Response(null, { headers: cors });
  if (request.method === "GET") {
    // A plain GET is a person or a crawler, not a client. Say what this is.
    return new Response(JSON.stringify({
      server: SERVER, protocol: PROTOCOL,
      transport: "JSON-RPC 2.0 over HTTP POST",
      tools: TOOLS.map((t) => t.name),
      note: "All tools are read-only. POST a JSON-RPC request here.",
    }, null, 1), { headers: { "content-type": "application/json", ...cors } });
  }
  if (request.method !== "POST") {
    return new Response("POST only", { status: 405, headers: cors });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify(rpcErr(null, -32700, "bad JSON")),
      { status: 400, headers: { "content-type": "application/json", ...cors } });
  }

  // A batch is legal in JSON-RPC and clients do send them.
  const many = Array.isArray(body);
  const msgs = many ? body : [body];
  const out = [];
  for (const m of msgs) {
    const r = await dispatch(m, env, ctx);
    if (r) out.push(r);
  }
  const payload = many ? out : (out[0] ?? null);
  return new Response(payload === null ? "" : JSON.stringify(payload), {
    status: payload === null ? 202 : 200,
    headers: { "content-type": "application/json; charset=utf-8",
               "cache-control": "no-store", ...cors },
  });
}
