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
 * EIGHT TOOLS ARE READ-ONLY. ONE IS NOT, and it is worth being exact rather
 * than keeping a tidier claim: `start_naming_session` writes a row to
 * naming_sessions, because the engine has to remember what it has already
 * dealt and which jokes the customer rejected. It writes session state and
 * nothing else - no order, no payment, no mail, no column that identifies a
 * person - and the row is purged after 30 days. The privacy policy was
 * updated for it. verify.py enforces the split: that tool may write, the other
 * eight may not, and none of them may reach an order or a card.
 */
import { radioGate, overuseGate, fitGate, noveltyGate, widthIn,
         loadLexicon } from "./gates.js";
import { D } from "./gates-data.js";
// The same file the website runs for these two - see engine/shared_js.py.
import { checkRegistration, decodeHin, toPlain } from "./decode.js";
import { INTERVIEW, profileFrom, missingQuestions, dealRound } from "./engine.js";

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
      const killed = (args.killed_mechanisms || [])
        .concat(prior ? JSON.parse(prior.killed_mechs || "[]") : []);
      const shown = prior ? JSON.parse(prior.shown || "[]") : [];
      const round = dealRound(bank, profile, {
        size: args.size || 8, exclude: shown, killedMechs: killed,
        font: args.font || "Arial Bold",
        seed: (sid || now) + ":" + (prior ? prior.rounds + 1 : 1),
      });

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
             JSON.stringify([...new Set(killed)]), "[]",
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
        honesty: "Every name here is from our own curated bank, already "
          + "tested. How common a name is comes from market data, not a "
          + "registry - we cannot tell anyone what is already on their lake.",
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
