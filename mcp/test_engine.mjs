/**
 * Tests for the naming engine. Run by verify.py.
 *
 * The engine has no Python twin and does not need one - it only ever runs on
 * the worker, so it is tested in the language it runs in rather than mirrored
 * and compared. The gates it leans on are the ones already held to the
 * equivalence harness.
 *
 * Each case below is something that would be invisible in a demo and
 * expensive in the post: the ceiling on who is aboard, an in-joke dealt to a
 * stranger, a round that is one joke eight times.
 */
import fs from "node:fs";
import zlib from "node:zlib";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as G from "../worker/gates.js";
import * as E from "../worker/engine.js";
// The MCP server, for the two pure helpers that read the session row.
import { killCounts, retiredMechs, validate } from "../worker/mcp.js";
import * as PR from "../worker/price.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
G._setLexicon(zlib.gunzipSync(
  fs.readFileSync(path.join(HERE, "data", "lexicon.txt.gz")))
  .toString().split("\n"));
const BANK = JSON.parse(fs.readFileSync(
  path.join(HERE, "data", "name_bank.json"), "utf8")).names;

const fails = [];
const check = (cond, msg) => { if (!cond) fails.push(msg); };
const deal = (answers, opts = {}) =>
  E.dealRound(BANK, E.profileFrom(answers), { seed: "test", ...opts });

// --- the ceiling. The most consequential rule in the engine. ---------------
{
  const r = deal({ boat: "pontoon", aboard: "my grandkids every weekend",
                   vibe: "deadpan" });
  const bad = r.names.filter((n) => n.level !== "clean");
  check(!bad.length,
    "grandkids are aboard and the engine dealt " + bad.length + " name(s) "
    + "that are not clean: " + bad.map((n) => n.name + " (" + n.level + ")"));
  check(r.names.length > 0, "a clean ceiling must still fill a round");
}
{
  // Nobody said who is aboard. Default must be CLEAN - defaulting the other
  // way puts the cost of the mistake on the customer, and it is his transom.
  const p = E.profileFrom({ boat: "pontoon" });
  check(p.ceiling === "clean",
    "with nobody named aboard the ceiling must default to clean, got "
    + p.ceiling);
  const r = deal({ boat: "pontoon" });
  check(!r.names.some((n) => n.level !== "clean"),
    "a round dealt with no answer about who is aboard contained a non-clean "
    + "name");
}
{
  // He asked for dock humor and said it is just his friends. Honour it.
  const r = deal({ boat: "bass boat", aboard: "just me and my buddies",
                   vibe: "dock humor" });
  check(r.names.some((n) => n.level !== "clean"),
    "a customer who asked for dock humor with only his friends aboard got "
    + "nothing but clean names - the ceiling is too tight to be useful");
}

// --- two bugs that reached production, now pinned -----------------------
{
  // "me and my brother" set the ceiling to DOCK, because /her\b/ matches
  // inside "brother". The live engine dealt Alimony, Yes Dear and Ask Her to
  // a man who had asked for nothing crude. "mother", "father", "other" and
  // "together" all did the same.
  for (const aboard of ["me and my brother", "my mother", "my father",
                        "the other half of the family", "all of us together"]) {
    const p = E.profileFrom({ boat: "pontoon", aboard });
    check(p.ceiling === "clean",
      `"${aboard}" produced ceiling ${p.ceiling} - a substring match on `
      + "her/she is setting the ceiling again");
  }
  // And the words that SHOULD set it still do.
  check(E.profileFrom({ boat: "pontoon", aboard: "my wife" }).ceiling === "dock",
    '"my wife" must still reach the dock ceiling');
  check(E.profileFrom({ boat: "pontoon",
                        aboard: "she comes along" }).ceiling === "dock",
    '"she comes along" must still reach the dock ceiling');
}
{
  // "deadpan, nothing crude" matched the dock lane on the word "crude", so
  // the engine dealt him crude names because he asked not to have them.
  const p = E.profileFrom({ boat: "pontoon", aboard: "buddies",
                            vibe: "deadpan, nothing crude" });
  check(p.ceiling === "clean",
    "a customer who said 'nothing crude' got ceiling " + p.ceiling);
  check(p.lanes.includes("deadpan") && !p.lanes.includes("dock"),
    "'deadpan, nothing crude' produced lanes " + p.lanes);
  const r = deal({ boat: "pontoon", aboard: "me and my brother",
                   vibe: "deadpan, nothing crude" });
  check(!r.names.some((n) => n.level !== "clean"),
    "'nothing crude' still produced non-clean names: "
    + r.names.filter((n) => n.level !== "clean").map((n) => n.name));
  check(!r.names.some((n) => n.lanes.includes("dock")),
    "'nothing crude' still produced dock-lane names");
}
{
  // A lane he asked us to leave out is an exclusion, not a nudge.
  const r = deal({ boat: "pontoon", aboard: "buddies",
                   vibe: "not puns, something absurd" });
  check(!r.names.some((n) => n.lanes.includes("pun")),
    "the customer said 'not puns' and got "
    + r.names.filter((n) => n.lanes.includes("pun")).map((n) => n.name));
  check(r.rejected.avoided_lane > 0,
    "an avoided lane set nothing aside");
  // Negation must not invert a plain request.
  check(E.profileFrom({ vibe: "something popular" }).wants_popular,
    "'something popular' must still ask for popular names");
  check(!E.profileFrom({ vibe: "nothing common" }).wants_popular,
    "'nothing common' must not be read as a request for common names");
}

// --- in-group jokes stay shut until the trade is known --------------------
{
  const r = deal({ boat: "runabout", aboard: "buddies", vibe: "nerd" });
  check(!r.names.some((n) => n.mechanism === "in-group in-joke (profession, "
    + "region, cohort)"),
    "an in-group in-joke was dealt before the interview established the "
    + "trade - it lands on nobody");
  const r2 = deal({ boat: "runabout", aboard: "buddies", vibe: "nerd",
                    work: "retired software engineer" });
  check(r2.eligible > r.eligible,
    "naming a trade did not unlock any names - the in_group gate is not "
    + "actually opening");
}

{
  // "Limit Out" is angler jargon. It came back described as "an in-joke for
  // I run a small HVAC company" - the pj mechanism covers a trade, a region
  // and a cohort, and the reveal assumed it was always the trade.
  const fishy = BANK.find((n) => n.mechanism_code === "pj"
    && (n.themes || []).includes("fishing"));
  if (fishy) {
    const hvac = E.profileFrom({ boat: "runabout", aboard: "buddies",
                                 work: "I run a small HVAC company" });
    const r = E.rationale(fishy, hvac, G.radioGate(fishy.name), null);
    check(!r.includes("HVAC"),
      `${fishy.name} is a fishing in-joke but was explained as an in-joke `
      + "for the customer's unrelated trade: " + r);
    // And with no boat to prove he fishes, it should not be dealt at all.
    check(E.inGroupEvidence(fishy, hvac) === null,
      `${fishy.name} was treated as an in-joke he is inside, on a runabout `
      + "with an HVAC job");
    const angler = E.profileFrom({ boat: "19 foot bass boat",
                                   aboard: "buddies" });
    check(E.inGroupEvidence(fishy, angler) !== null,
      `${fishy.name} should be unlocked by the boat being a bass boat`);
    const r2 = E.rationale(fishy, angler, G.radioGate(fishy.name), null);
    check(r2.includes("fishes"),
      "a fishing in-joke should name the group it is for: " + r2);
  }
  // A regional in-joke needs the port, not the job.
  const regional = BANK.find((n) => n.mechanism_code === "pj"
    && (n.style_lanes || []).includes("regional"));
  if (regional) {
    check(E.inGroupEvidence(regional,
      E.profileFrom({ boat: "pontoon", work: "dentist" })) === null,
      `${regional.name} is regional and was unlocked by a job`);
    check(E.inGroupEvidence(regional,
      E.profileFrom({ boat: "pontoon", port: "Clear Lake, Iowa" })) !== null,
      `${regional.name} should be unlocked by a hailing port`);
  }
}

// --- fit ------------------------------------------------------------------
{
  const small = deal({ boat: "kayak", aboard: "just me", transom: "14" });
  check(small.rejected.fit > 0,
    "a 14-inch transom excluded nothing - the fit gate is not being applied "
    + "in the ranker");
  for (const n of small.names) {
    check(n.fit.tallest_that_fits !== null,
      n.name + " was dealt for a 14-inch transom with no height that fits");
  }
}

// --- overuse --------------------------------------------------------------
{
  const r = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" });
  check(!r.names.some((n) => n.how_common === 1),
    "a tier-1 cliche was dealt as a top pick: "
    + r.names.filter((n) => n.how_common === 1).map((n) => n.name));
  check(r.rejected.tier1 > 0, "no tier-1 names were set aside at all");
  const pop = deal({ boat: "pontoon", aboard: "buddies",
                     vibe: "something popular and well known" });
  check(pop.rejected.tier1 === 0,
    "a customer who explicitly asked for popular names still had the common "
    + "ones withheld");
}

// --- a rejected joke does not come back in a different costume -----------
{
  const r = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" },
                  { killedMechs: ["hp"] });
  check(!r.names.some((n) => n.mechanism === "homophone pun"),
    "a mechanism the customer killed was dealt again");
  check(r.rejected.killed_mechanism > 0,
    "killing a mechanism set nothing aside");
}

// --- never an unfiltered list --------------------------------------------
{
  const r = deal({ boat: "pontoon", aboard: "buddies" }, { size: 8 });
  check(r.names.length <= 8, "a round returned more than it was asked for");
  check(r.names.length < r.considered,
    "the engine returned the whole bank - the spec's one hard rule is that it "
    + "never returns an unfiltered list");
  check(r.riff_slots <= Math.floor(8 / 3),
    "riff slots exceed a third of the round");
  check(r.eligible < r.considered,
    "nothing at all was filtered out of a round");
}

// --- diversity. A round of eight of the same joke reads as a thin bank. ---
{
  for (const vibe of ["pun", "deadpan", "dock humor", "absurd", "classy"]) {
    const r = deal({ boat: "pontoon", aboard: "just me and my buddies", vibe },
                    { size: 8 });
    const mechs = {};
    for (const n of r.names) mechs[n.mechanism] = (mechs[n.mechanism] || 0) + 1;
    const worst = Math.max(...Object.values(mechs));
    check(worst <= 3,
      `the ${vibe} round is ${worst} of the same mechanism out of `
      + `${r.names.length} - one joke told ${worst} times`);
  }
}
{
  // The alphabetical-bias bug: ties were broken by name, so rounds came out
  // "Actual In, Airman, Ails Sail, Alder & Oak, Alimony, Amicable, Ask Her".
  const r = deal({ boat: "runabout", aboard: "buddies", vibe: "pun" },
                  { size: 8 });
  const firsts = new Set(r.names.map((n) => n.name[0].toUpperCase()));
  check(firsts.size >= 4,
    "a round of 8 used only " + firsts.size + " distinct first letters ("
    + [...firsts] + ") - ties are being broken alphabetically again, which "
    + "reads as a list off the top of a file");
}

// --- reproducible from its seed ------------------------------------------
{
  const a = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" },
                  { seed: "same" });
  const b = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" },
                  { seed: "same" });
  check(JSON.stringify(a.names.map((n) => n.name))
        === JSON.stringify(b.names.map((n) => n.name)),
    "the same profile and seed produced two different rounds - a round must "
    + "be reproducible or a complaint about one cannot be investigated");
  const c = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" },
                  { seed: "other" });
  check(JSON.stringify(a.names.map((n) => n.name))
        !== JSON.stringify(c.names.map((n) => n.name)),
    "two different seeds produced an identical round - the seed does nothing");
}

// --- already-shown names do not repeat -----------------------------------
{
  const a = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" });
  const b = deal({ boat: "pontoon", aboard: "buddies", vibe: "pun" },
                  { exclude: a.names.map((n) => n.name), seed: "r2" });
  const overlap = b.names.filter(
    (n) => a.names.some((m) => m.name === n.name));
  check(!overlap.length,
    "round two repeated " + overlap.map((n) => n.name) + " from round one");
}

// --- the interview itself -------------------------------------------------
{
  check(E.INTERVIEW.length >= 5 && E.INTERVIEW.filter((q) => q.required)
    .length === 1,
    "the interview should ask several things and require exactly one");
  check(E.INTERVIEW.every((q) => q.why),
    "every interview question must record why it is asked - a question that "
    + "does not change the round should not be asked");
  const p = E.profileFrom({ transom: "about 60 inches or so" });
  check(p.transom_in === 60, "transom not parsed from plain words, got "
    + p.transom_in);
  check(E.profileFrom({ transom: "4" }).transom_in === null,
    "an implausible transom should be discarded rather than used");
}

// --- the tournament -------------------------------------------------------
{
  const pun = BANK.find((n) => n.mechanism_code === "hp");
  const pun2 = BANK.filter((n) => n.mechanism_code === "hp")[1];
  const dp = BANK.find((n) => n.mechanism_code === "dp");
  const dp2 = BANK.filter((n) => n.mechanism_code === "dp")[1];

  // One kill is a name he did not like.
  let st = E.applyVote({}, BANK, [], [pun.name]);
  check(!st.rejected_mechs.includes("hp"),
    "one kill rejected a whole mechanism - one kill is a name he did not "
    + "like, not a verdict on the joke");

  // Two kills with nothing kept is the joke itself not landing.
  st = E.applyVote(st, BANK, [], [pun2.name]);
  check(st.rejected_mechs.includes("hp"),
    "two kills of the same mechanism with no keeps did not reject it");

  // A keep protects it.
  let st2 = E.applyVote({}, BANK, [dp.name], [dp2.name]);
  st2 = E.applyVote(st2, BANK, [], [dp2.name]);
  check(!st2.rejected_mechs.includes("dp"),
    "a mechanism he has kept once was rejected on kills alone");

  // Proven needs two keeps and more keeps than kills.
  let st3 = E.applyVote({}, BANK, [dp.name], []);
  check(!st3.proven_mechs.includes("dp"), "one keep should not prove a mechanism");
  st3 = E.applyVote(st3, BANK, [dp2.name], []);
  check(st3.proven_mechs.includes("dp"), "two keeps should prove a mechanism");

  // Finalists.
  const three = BANK.slice(0, 3).map((n) => n.name);
  const st4 = E.applyVote({}, BANK, three, []);
  check(st4.finalists_ready, "three keeps should make the finalists ready");
  check(!E.applyVote({}, BANK, three.slice(0, 2), []).finalists_ready,
    "two keeps should not");
  // A name that is not in the bank must not be invented into the kept list.
  const st5 = E.applyVote({}, BANK, ["Definitely Not A Bank Name"], []);
  check(!st5.kept.length,
    "a vote for a name that is not in the bank was accepted");
  // Voting twice for the same name must not double-count it.
  let st6 = E.applyVote({}, BANK, [dp.name], []);
  st6 = E.applyVote(st6, BANK, [dp.name], []);
  check(st6.kept.length === 1, "the same keep was counted twice in kept[]");
}

// --- the reveal must not invent a single fact ----------------------------
{
  const n = BANK.find((x) => x.mechanism_code === "dp");
  // An empty profile. Every clause in the rationale is supposed to be either
  // a fixed phrase or a quotation of something the customer typed, so with
  // nothing typed there is nothing to quote.
  const bare = E.profileFrom({});
  const r = E.rationale(n, bare, G.radioGate(n.name), null);
  check(!/"/.test(r),
    "the rationale quoted something although the customer told us nothing: "
    + r);
  for (const invented of ["grandkid", "your boat", "weekend", "family",
                          "fishing", "retire", "wife"]) {
    check(!r.toLowerCase().includes(invented),
      `the rationale invented "${invented}" from an empty profile: ${r}`);
  }
  check(!/You asked for/.test(r),
    "the rationale claimed the customer asked for something when he said "
    + "nothing: " + r);
  check(r.length < 160 && r.endsWith("."),
    "the rationale should be one short line, got " + r.length + " chars: " + r);

  // And with real facts it must quote them rather than paraphrase.
  const full = E.profileFrom({ boat: "a 22 foot pontoon",
                               aboard: "my grandkids", vibe: "deadpan",
                               work: "retired electrician", port: "Clear Lake" });
  const pontoonDeadpan = BANK.find((x) => (x.style_lanes || []).includes("deadpan")
    && (x.boat_types || []).includes("pontoon"));
  if (pontoonDeadpan) {
    const r2 = E.rationale(pontoonDeadpan, full, G.radioGate(pontoonDeadpan.name), null);
    check(r2.includes("a 22 foot pontoon"),
      "the rationale did not quote the customer's own description of the "
      + "boat: " + r2);
  }
  const pj = BANK.find((x) => x.mechanism_code === "pj");
  const r3 = E.rationale(pj, full, G.radioGate(pj.name), null);
  check(r3.includes("retired electrician"),
    "an in-joke's rationale must quote the trade it is an in-joke for: " + r3);
}

{
  // The heading read "Three names for the a 22 foot pontoon".
  check(E.bareBoat("a 22 foot pontoon") === "22 foot pontoon",
    "a leading article is not being stripped: " + E.bareBoat("a 22 foot pontoon"));
  for (const [raw, want] of [["my bass boat", "bass boat"],
                             ["the pontoon", "pontoon"],
                             ["an old runabout", "old runabout"],
                             ["pontoon", "pontoon"],
                             ["", ""]]) {
    check(E.bareBoat(raw) === want,
      `bareBoat(${JSON.stringify(raw)}) gave ${JSON.stringify(E.bareBoat(raw))}`);
  }
}
{
  // All three finalists' reasons read identically, because every clause came
  // from the shared profile. The mechanism clause is what differs per name.
  const full = E.profileFrom({ boat: "a 22 foot pontoon",
                               aboard: "my grandkids", vibe: "deadpan" });
  const picks = BANK.filter((x) => (x.style_lanes || []).includes("deadpan")
    && x.humor_level === "clean");
  const seen = new Set();
  for (const n of picks.slice(0, 12)) {
    seen.add(E.rationale(n, full, G.radioGate(n.name), null));
  }
  check(seen.size >= 3,
    "twelve deadpan finalists produced only " + seen.size + " distinct "
    + "reasons - the reveal reads as generated");
}

// --- no two finalists may lean on the same fact --------------------------
{
  // FOUND LIVE. "Live Bait" and "Last Cast" are both literal-truth names,
  // both suit a bass boat, and neither carries a note - so the ladder landed
  // on the same rung twice and the reveal read:
  //
  //   Live Bait - ...the joke is that it is simply, boringly true.
  //   Last Cast - ...the joke is that it is simply, boringly true.
  //
  // Correct about each name in isolation, and useless as a reveal. The reveal
  // is the three names together, so distinctness is a property of the set.
  const prof = E.profileFrom({ boat: "a 19 foot bass boat",
                               aboard: "just me and my brother",
                               vibe: "puns, nothing crude",
                               transom: "44 inches" });
  // Same mechanism, no notes: the hard case, not a convenient one.
  const twins = BANK.filter(
    (n) => n.mechanism_code === "lt" && !n.note
           && (n.boat_types || []).includes("bass")).slice(0, 3);
  check(twins.length >= 2,
    "the fixture needs at least two note-less names sharing a mechanism");
  const used = new Set();
  const said = twins.map((n) => E.rationale(n, prof, G.radioGate(n.name),
    G.fitGate(n.name, "Arial Bold", 44), used));
  check(new Set(said).size === said.length,
    "two finalists sharing a mechanism came back with the same reason:\n   "
    + said.join("\n   "));
  // And without the shared set it must still be the old behaviour - this is
  // what proves the `used` argument is what is doing the work.
  const solo = twins.map((n) => E.rationale(n, prof, G.radioGate(n.name),
    G.fitGate(n.name, "Arial Bold", 44)));
  check(new Set(solo).size < solo.length,
    "the fixture no longer reproduces the bug, so it proves nothing");
  // Nothing invented: every clause still has to come from his own answers.
  for (const r of said) {
    check(!/grandkid|wife|retire|dog/i.test(r),
      "the reveal invented a fact he never gave us: " + r);
  }
}

// --- gate results in plain words -----------------------------------------
{
  const n = BANK.find((x) => x.name === "Knot Working")
    || BANK.find((x) => x.mechanism_code === "hp");
  const sum = E.gateSummary(G.radioGate(n.name),
    G.fitGate(n.name, "Arial Bold", 60), G.overuseGate(n.name));
  check(sum.length >= 2, "the gate summary should say at least two things");
  for (const line of sum) {
    check(!/verdict|tier|gate|null|undefined|_/.test(line),
      "the gate summary is leaking internal vocabulary at a customer: "
      + line);
  }
}


// --- the ledger and the riff brief (spec test 21) -------------------------
//
// Every case here is a claim the brief makes to the host model. A brief that
// says "these mechanisms are proven" when nothing is proven, or that offers
// back a mechanism the customer just killed, is worse than no brief: the host
// writes it into a rationale and the customer is told his own taste out loud,
// wrongly.
const DEADPAN = { boat: "a 22 foot pontoon", aboard: "my wife and I",
                  vibe: "deadpan", transom: "48 inches" };

/** Build ledger rows the way the table would hold them. */
const lrow = (kind, lane, key, exp, keeps, kills = 0) =>
  ({ kind, lane, key, exposures: exp, keeps, kills,
     w_exposures: exp, w_keeps: keeps, w_kills: kills });

{
  // Cold ledger: nothing is proven, and the brief must SAY so rather than
  // dress up the exemplars as evidence.
  const p = E.provenFor([], "deadpan");
  check(p.cold && !p.proven.length, "an empty ledger must be cold");
  const b = E.riffBrief(BANK, E.profileFrom(DEADPAN), {}, [], 2);
  check(/COLD/.test(b.ledger_status),
    "a cold ledger must be declared as cold in the brief, not implied");
  check(/no keep data/.test(b.exemplars_chosen_by),
    "with no keep data the brief must not claim its exemplars are the "
    + "highest keep-rate names: " + b.exemplars_chosen_by);
  // FOUND LIVE. A cold ledger still accrues an exposure for every name the
  // moment the first round is dealt, and the first version read "any name has
  // a row" as "we have keep data" - so within minutes of going live the brief
  // was telling the model its exemplars were the highest keep-rate names
  // while every rate in the table was zero.
  const exposedOnly = BANK.slice(0, 40).map(
    (n) => lrow("name", "any", n.name, 12, 0));
  const b2 = E.riffBrief(BANK, E.profileFrom(DEADPAN), {}, exposedOnly, 2);
  check(/no keep data/.test(b2.exemplars_chosen_by),
    "forty names with exposures and zero keeps were read as keep data: "
    + b2.exemplars_chosen_by);
  // FOUND LIVE. A cold ledger produced a brief with no exemplars at all,
  // because the fallback read the ledger's exploring list, which on a cold
  // ledger is empty. A brief with nothing in it is a model free-associating.
  check(b.exemplars.length >= 3,
    "a cold-ledger brief carried only " + b.exemplars.length + " exemplars - "
    + "there is nothing for the host to work from and it will invent");
  check(b.until_the_ledger_has_data
    && b.until_the_ledger_has_data.mechanisms.length >= 1,
    "an empty mechanisms_to_use list is not an instruction; the brief must "
    + "say what to do instead while the ledger is cold");
  check(b.exemplars.every((e) => b.until_the_ledger_has_data.mechanisms
    .includes(e.mechanism_code)),
    "the cold brief's exemplars do not demonstrate the mechanisms it told "
    + "the host to use");
}
{
  // Thirty exposures and not one keep is not "top half of a field of one".
  const p = E.provenFor([lrow("mech", "deadpan", "dp", 40, 0)], "deadpan");
  check(!p.proven.length,
    "a mechanism with forty exposures and zero keeps was called proven");
}
{
  // The threshold. Twenty-nine exposures is not enough; thirty is.
  check(!E.provenFor([lrow("mech", "deadpan", "dp", 29, 10)], "deadpan")
    .proven.length, "29 exposures cleared a 30-exposure threshold");
  check(E.provenFor([lrow("mech", "deadpan", "dp", 30, 10)], "deadpan")
    .proven.includes("dp"), "30 exposures did not clear the threshold");
}

// A warm deadpan lane: dp and lt are landing, hp and md are not.
const WARM = [
  lrow("mech", "deadpan", "dp", 120, 30),
  lrow("mech", "deadpan", "lt", 90, 20),
  lrow("mech", "deadpan", "hp", 100, 4),
  lrow("mech", "deadpan", "md", 60, 2),
  lrow("mech", "deadpan", "pm", 8, 3),      // not enough exposures yet
];
{
  const p = E.provenFor(WARM, "deadpan");
  check(p.proven.includes("dp") && p.proven.includes("lt"),
    "the two mechanisms with the best keep-rates were not proven: "
    + JSON.stringify(p.proven));
  check(!p.proven.includes("hp") && !p.proven.includes("md"),
    "a bottom-half keep-rate was called proven: " + JSON.stringify(p.proven));
  check(p.exploring.includes("pm"),
    "a mechanism under the exposure threshold must be exploration");
}
{
  // Spec test 21: only proven-for-lane mechanisms, and at least three
  // exemplars.
  const b = E.riffBrief(BANK, E.profileFrom(DEADPAN), {}, WARM, 2);
  const codes = b.mechanisms_to_use.map((m) => m.code);
  check(codes.length && codes.every((c) => ["dp", "lt"].includes(c)),
    "the brief offered an unproven mechanism in mechanisms_to_use: "
    + JSON.stringify(codes));
  check(b.exemplars.length >= 3,
    "the brief carried only " + b.exemplars.length + " exemplars; the spec "
    + "asks for at least three");
  check(b.exemplars.every((e) => ["dp", "lt"].includes(e.mechanism_code)),
    "an exemplar does not use a mechanism the brief told the host to use");
  check(b.one_slot_for_something_unproven
    && !["dp", "lt"].includes(b.one_slot_for_something_unproven.code),
    "the brief did not offer its single exploration slot");
  check(Object.keys(b.his_own_words).length >= 2
    && b.his_own_words.boat === DEADPAN.boat,
    "the brief must hand the host the customer's own words, verbatim");
  // His wife is aboard and he did not ask for anything crude: dock humor is
  // allowed, jokes at her expense are not, and the brief has to say which.
  // And the clean ceiling must say WHICH reason it is. The first version told
  // the model "children or his wife are aboard" even when nobody had said who
  // was aboard at all - a fact handed to a model that writes rationales.
  const nobody = E.riffBrief(BANK, E.profileFrom({ boat: "pontoon" }), {},
                             [], 2);
  check(nobody.ceiling === "clean" && /nobody has told us/
    .test(nobody.ceiling_means),
    "with nobody named aboard the brief must say so rather than invent a "
    + "family: " + nobody.ceiling_means);
  check(!/children|wife|grandkid/i.test(nobody.ceiling_means),
    "the brief invented a family nobody mentioned: " + nobody.ceiling_means);
  check(b.ceiling === "dock" && /expense/.test(b.ceiling_means),
    "a brief for a man with his wife aboard must spell out where the line "
    + "is, got: " + b.ceiling + " / " + b.ceiling_means);
}
{
  // Spec test 21: a mechanism killed in Round 1 is out of the Round 2 brief.
  const state = E.applyVote({}, BANK,
    [], BANK.filter((n) => n.mechanism_code === "dp").slice(0, 2)
          .map((n) => n.name));
  check(state.rejected_mechs.includes("dp"),
    "two kills of the same mechanism with no keeps did not retire it");
  const b = E.riffBrief(BANK, E.profileFrom(DEADPAN), state, WARM, 2);
  check(!b.mechanisms_to_use.some((m) => m.code === "dp"),
    "a mechanism the customer killed twice in Round 1 came back in the "
    + "Round 2 brief, which is the one thing a vote is supposed to prevent");
  check(b.do_not_use.mechanisms_he_killed.includes("dp"),
    "the brief must tell the host what he killed, not just omit it");
  check(!b.exemplars.some((e) => e.mechanism_code === "dp"),
    "the brief's exemplars are still demonstrating the killed mechanism");
}
{
  // Spec test 21: an unproven mechanism occupies at most one slot in a round.
  const prof = E.profileFrom(DEADPAN);
  const r = E.dealRound(BANK, prof,
    { seed: "explore", size: 8, proven: ["dp", "lt"] });
  const unproven = r.names.filter(
    (n) => !["dp", "lt"].includes(n.mechanism_code));
  check(unproven.length <= 1,
    "a round dealt " + unproven.length + " names on mechanisms the ledger "
    + "has not proven; the cap is one: "
    + unproven.map((n) => n.name + " (" + n.mechanism_code + ")").join(", "));
  check(r.names.length >= 4,
    "the exploration cap starved the round down to " + r.names.length);
  // And with a cold ledger the cap must NOT bind, or every round is one name.
  const cold = E.dealRound(BANK, prof, { seed: "explore", size: 8 });
  check(cold.names.length >= 6,
    "with nothing proven the exploration cap bound anyway and the round came "
    + "back with " + cold.names.length + " names");
  // FOUND LIVE. One proven mechanism cannot compose a round. He killed
  // deadpan, which left exactly one proven mechanism in his lane, and a round
  // of four came back as three literal-truth jokes and one riff - the same
  // joke three times, which is what the diversity caps exist to prevent.
  const one = E.dealRound(BANK, prof,
    { seed: "lonely", size: 4, proven: ["lt"], killedMechs: ["dp"] });
  // DOMINANCE, not distinctness. The first version of this check asked for
  // two distinct mechanisms and passed with the cap left in: three
  // literal-truth names plus one exploration slot is two distinct
  // mechanisms, and it is also the bug. What matters is that no single joke
  // takes three of the four.
  const tally = {};
  for (const n of one.names) {
    tally[n.mechanism_code] = (tally[n.mechanism_code] || 0) + 1;
  }
  const worst = Math.max(...Object.values(tally));
  check(one.names.length === 4 && worst <= 2,
    "with one proven mechanism a round of four came back as "
    + one.names.length + " names, " + worst + " of them the same joke: "
    + one.names.map((n) => n.name + " (" + n.mechanism_code + ")").join(", "));
}

// --- gating a riff --------------------------------------------------------
const DEPS = { radioGate: G.radioGate, overuseGate: G.overuseGate,
               fitGate: G.fitGate, noveltyGate: G.noveltyGate };
const BANKN = BANK.map((n) => n.name);
{
  const prof = E.profileFrom(DEADPAN);
  const g = E.gateRiff({ name: "Deere Diary", mechanism: "hp",
                         why: "he spent thirty years at the Deere plant" },
                       prof, BANKN, DEPS);
  check(g.ok, "a clean two-word riff was rejected: " + g.reason);
  check(g.row.source === "riff" && g.row.mechanism_code === "hp",
    "a gated riff must be tagged as a riff");
  check(g.row.humor_level === "unrated",
    "a riff must be recorded as unrated - nobody has read it, so calling it "
    + "clean is a claim we cannot make");
}
{
  // Spec test 21: a near-copy of a bank name is a copy, not creativity.
  const target = BANK.find((n) => n.name.split(" ").length === 2).name;
  const g = E.gateRiff({ name: target, mechanism: "dp" },
                       E.profileFrom(DEADPAN), BANKN, DEPS);
  check(!g.ok && /bank/i.test(g.reason || ""),
    "a word-for-word copy of the bank name \"" + target + "\" passed the "
    + "novelty gate");
  const near = E.gateRiff({ name: target + "s", mechanism: "dp" },
                          E.profileFrom(DEADPAN), BANKN, DEPS);
  check(!near.ok, "a near-copy of \"" + target + "\" passed the novelty gate");
}
{
  // The rebus class. Already dead in the radio gate; it must stay dead when
  // a model submits it rather than when the bank contains it.
  const g = E.gateRiff({ name: "Nauti-4-U", mechanism: "hp" },
                       E.profileFrom(DEADPAN), BANKN, DEPS);
  check(!g.ok, "\"Nauti-4-U\" was accepted as a riff");
}
{
  const prof = E.profileFrom({ boat: "pontoon", aboard: "my grandkids",
                               vibe: "deadpan" });
  // Overt crudeness, under a ceiling of grandchildren. "Ship Happens" would
  // have proved nothing here - it dies on the novelty gate, because it is
  // already in the bank as "Ships Happen" - so this is a name the crude
  // screen is the only thing standing in front of.
  const g = E.gateRiff({ name: "Nude Awakening", mechanism: "tt" }, prof,
                       BANKN, DEPS);
  check(!g.ok && /crude/.test(g.reason || ""),
    "a crude riff survived a clean ceiling: " + (g.reason || "accepted"));
  // And the same name is allowed when a man on his own asked for it. The
  // screen is a ceiling, not a taste.
  const ok = E.gateRiff({ name: "Nude Awakening", mechanism: "tt" },
    E.profileFrom({ boat: "bass boat", aboard: "just me",
                    vibe: "double entendre, dock humor" }), BANKN, DEPS);
  check(ok.ok, "the crude screen is refusing a man on his own who asked for "
    + "it, which makes it a taste rather than a ceiling: " + ok.reason);
}
{
  const prof = E.profileFrom(DEADPAN);
  check(!E.gateRiff({ name: "Lowkey Nauti", mechanism: "dp" }, prof, BANKN,
                    DEPS).ok, "meme-speak survived the riff gate");
  check(!E.gateRiff({ name: "Fine", mechanism: "zz" }, prof, BANKN, DEPS).ok,
    "a riff with an invented mechanism code was accepted");
  const long = E.gateRiff(
    { name: "The Boat That My Father In Law Sold Me Twice", mechanism: "lt" },
    prof, BANKN, DEPS);
  check(!long.ok, "a 44-character name was accepted for a 48-inch transom");
}
{
  // Riffs are at most a third of a round, and they have to actually get in.
  const prof = E.profileFrom(DEADPAN);
  const riffs = ["Deere Diary", "Second Shift", "Pension Plan", "Clocked Out",
                 "Line Speed", "Union Dues"].map((name) => {
    const g = E.gateRiff({ name, mechanism: "dp" }, prof, BANKN, DEPS);
    return g.ok ? g.row : null;
  }).filter(Boolean);
  check(riffs.length >= 4, "the riff fixtures do not survive their own "
    + "gates: only " + riffs.length + " of 6");
  const r = E.dealRound(BANK, prof, { seed: "riffs", size: 8, riffs });
  const got = r.names.filter((n) => n.source === "riff");
  check(got.length <= 2,
    "a round of eight dealt " + got.length + " riffs; the cap is a third");
  check(got.length >= 1,
    "six gated riffs built from his own words and not one reached a round of "
    + "eight - the bonus is not working");
  check(r.riff_slots === Math.floor(8 / 3) - got.length,
    "riff_slots must report what is LEFT so the host knows whether to invent "
    + "more");
  // A ROUND OF FOUR, which is what every round after the first actually is.
  // The round of eight above does not prove the cap on its own: the riffs all
  // share the category "riff", so the diversity cap holds them to two whether
  // the riff cap exists or not, and deleting the riff cap changed nothing.
  // Four is where the two caps disagree - a third of four is one - so this is
  // the case that fails if the cap is removed.
  const four = E.dealRound(BANK, prof, { seed: "riffs", size: 4, riffs });
  const g4 = four.names.filter((n) => n.source === "riff");
  check(g4.length <= 1,
    "a round of four dealt " + g4.length + " riffs; a third of four is one: "
    + g4.map((n) => n.name).join(", "));
  check(four.names.length === 4,
    "the riff cap starved a round of four down to " + four.names.length);
}

// --- the monthly review ---------------------------------------------------
{
  // Spec test 21: after simulated keeps and kills, one mechanism crosses the
  // threshold and one decays out, and both are visible in the review.
  const before = { deadpan: ["dp", "hp"] };
  const now = [
    lrow("mech", "deadpan", "dp", 120, 30),   // still landing
    lrow("mech", "deadpan", "hp", 120, 2),    // stopped landing
    lrow("mech", "deadpan", "lt", 60, 18),    // crossed
  ];
  const rev = E.monthlyReview(now, before);
  check(rev.crossed.includes("deadpan:lt"),
    "a mechanism that crossed the threshold is not in the review: "
    + JSON.stringify(rev.crossed));
  check(rev.decayed.includes("deadpan:hp"),
    "a mechanism whose keep-rate collapsed did not decay out: "
    + JSON.stringify(rev.decayed));
  check(rev.lanes.deadpan.rates.hp.keeps === 2
    && rev.lanes.deadpan.rates.dp.exposures === 120,
    "the review must show the real counts beside the verdict");
}
{
  // The decay itself. Halving the window is what makes an old win fade, so
  // check the arithmetic the review relies on rather than trusting it.
  const stale = [lrow("mech", "deadpan", "dp", 30, 12)];
  check(E.provenFor(stale, "deadpan").proven.includes("dp"),
    "a mechanism at the threshold should be proven before any decay");
  const halved = stale.map((r) => ({ ...r,
    w_exposures: Math.floor(r.w_exposures / 2),
    w_keeps: Math.floor(r.w_keeps / 2) }));
  check(!E.provenFor(halved, "deadpan").proven.includes("dp"),
    "one month of decay with no new exposures left a mechanism proven on "
    + "fifteen exposures - the window is not actually decaying");
}
{
  // Where evidence is filed. A session that asked for deadpan files under
  // deadpan AND under 'any', so a cold lane always has a fallback.
  const d = E.ledgerDeltas(E.profileFrom(DEADPAN),
    [{ name: "Halcyon", mechanism_code: "sincere" }], "keeps");
  const lanes = d.filter((x) => x.kind === "mech").map((x) => x.lane).sort();
  check(lanes.join(",") === "any,deadpan",
    "a deadpan session's evidence must file under its lane and 'any', got "
    + lanes.join(","));
  check(d.some((x) => x.kind === "name" && x.key === "Halcyon"),
    "bank names must accrue their own keep-rate - it is what picks exemplars");
}
{
  // The privacy line that makes the ledger allowed to outlive the session
  // purge: a riff's TEXT never reaches it.
  const d = E.ledgerDeltas(E.profileFrom(DEADPAN),
    [{ name: "Marjorie's Mistake", mechanism_code: "lt", source: "riff" }],
    "keeps");
  check(!d.some((x) => x.kind === "name"),
    "a riff's text was filed in the ledger, which outlives the 30-day purge "
    + "- riffs are built out of somebody's wife, dog or hometown");
  check(d.some((x) => x.kind === "mech" && x.key === "lt"),
    "a riff must still teach the ledger about its mechanism");
}

// --- the argument boundary ----------------------------------------------
{
  // FOUND LIVE, and the dangerous kind. dispatch() handed params.arguments
  // straight to the tool and never read the schema, so a call to
  // check_registration_layout with the parameter misnamed - `text` instead of
  // `number` - was accepted, read nothing, and came back verdict "ok",
  // height_is_legal true. A model would tell a customer their registration
  // layout is fine having checked nothing at all.
  const layout = {
    type: "object",
    properties: {
      number: { type: "string", maxLength: 24 },
      height_in: { type: "number" },
      transom_in: { type: "number" },
    },
    required: ["number"], additionalProperties: false,
  };
  check(validate(layout, { text: "IA 1234 AB", state: "IA" }),
    "the exact live call that slipped through is still accepted");
  check(/number is required/.test(validate(layout, {}) || ""),
    "a missing required parameter must say which one: "
    + validate(layout, {}));
  check(/no parameter "state"/.test(
    validate(layout, { number: "IA 1234 AB", state: "IA" }) || ""),
    "an unknown parameter must be named back, not ignored");
  check(!validate(layout, { number: "IA 1234 AB" }),
    "a valid call was rejected: " + validate(layout, { number: "IA 1" }));
  check(!validate(layout, { number: "IA 1", height_in: 3 }),
    "an optional number was rejected");
  check(validate(layout, { number: "IA 1", height_in: "3" }),
    "a string was accepted where the schema says number - the tool would "
    + "compare it arithmetically and get it wrong");
  // An empty string is not an answer to a required field. This is the real
  // shape of the live bug: args.number was undefined and the tool treated it
  // as "no number given" rather than as a broken call.
  check(validate(layout, { number: "" }),
    "an empty required string was accepted");
  check(validate(layout, { number: "x".repeat(30) }),
    "a 30-character registration number was accepted past maxLength 24");
}
{
  // The enum, which is what stands between a model and a wrong price now
  // that price_order is strict.
  const price = {
    type: "object",
    properties: {
      kind: { type: "string", enum: ["numbers", "name", "both"] },
      outline: { type: "boolean" },
    },
    required: ["kind"], additionalProperties: false,
  };
  check(/one of numbers, name, both/.test(
    validate(price, { kind: "name-plus-port" }) || ""),
    "an off-enum product was accepted: "
    + validate(price, { kind: "name-plus-port" }));
  check(validate(price, { kind: "name", outline: "yes" }),
    'outline: "yes" was accepted where the schema says boolean');
  check(!validate(price, { kind: "both", outline: true }), "a valid quote "
    + "was rejected");
}
{
  // Nested: the riff candidates array, where a model is most likely to
  // improvise a field name.
  const riffs = {
    type: "object",
    properties: {
      session_id: { type: "string", maxLength: 40 },
      candidates: {
        type: "array", maxItems: 12,
        items: {
          type: "object",
          properties: { name: { type: "string", maxLength: 40 },
                        mechanism: { type: "string" },
                        why: { type: "string", maxLength: 160 } },
          required: ["name", "mechanism"], additionalProperties: false,
        },
      },
    },
    required: ["session_id", "candidates"], additionalProperties: false,
  };
  check(!validate(riffs, { session_id: "abc",
    candidates: [{ name: "Deere Diary", mechanism: "hp" }] }),
    "a valid riff batch was rejected");
  check(/candidates\[0\]\.mechanism is required/.test(validate(riffs,
    { session_id: "abc", candidates: [{ name: "Deere Diary" }] }) || ""),
    "a riff with no mechanism must be named by index");
  check(/candidates\[1\] has no parameter "joke"/.test(validate(riffs,
    { session_id: "abc", candidates: [
      { name: "A", mechanism: "dp" },
      { name: "B", mechanism: "dp", joke: "a pun" }] }) || ""),
    "an improvised field inside the array was ignored");
  check(validate(riffs, { session_id: "abc",
    candidates: new Array(13).fill({ name: "A", mechanism: "dp" }) }),
    "thirteen candidates were accepted past maxItems 12");
  check(validate(riffs, { session_id: "abc", candidates: "Deere Diary" }),
    "a bare string was accepted where the schema says array");
}
{
  // The interview answers use additionalProperties AS A SCHEMA, not false -
  // the keys are the customer's own question ids. Both branches have to work.
  const start = {
    type: "object",
    properties: {
      answers: { type: "object",
                 additionalProperties: { type: "string", maxLength: 400 } },
    },
    additionalProperties: false,
  };
  check(!validate(start, { answers: { boat: "pontoon", port: "Clear Lake" } }),
    "a real interview was rejected");
  check(validate(start, { answers: { boat: "x".repeat(500) } }),
    "a 500-character answer was accepted past maxLength 400");
  check(validate(start, { answers: { boat: 22 } }),
    "a number was accepted where an interview answer must be text");
  check(!validate(start, {}), "an empty call to start the interview was "
    + "rejected - nothing in it is required");
}

// --- the card a man forwards to his wife ---------------------------------
{
  // FOUND LIVE. It said "Three names for the 22 foot pontoon" over a card
  // with two names on it: the heading hardcoded the word, while the reveal
  // happily reveals whatever has been kept.
  check(E.cardHeading(2, "a 22 foot pontoon")
    === "Two names for the 22 foot pontoon",
    "the card miscounted itself: " + E.cardHeading(2, "a 22 foot pontoon"));
  check(E.cardHeading(1, "my bass boat") === "One name for the bass boat",
    "got: " + E.cardHeading(1, "my bass boat"));
  check(E.cardHeading(3, null) === "Three names for the boat",
    "got: " + E.cardHeading(3, null));
}

// --- the killed_mechs column, which two tools wrote in two shapes ---------
{
  // start_naming_session wrote an ARRAY of codes; vote_on_names wrote an
  // OBJECT of counts, into the same column. Reading the object as an array
  // silently forgot every mechanism the customer had rejected, so a host that
  // called start_naming_session again - which is what it does when the
  // customer adds "oh, and it's a pontoon" - got the jokes he had just
  // killed, dealt back to him.
  check(JSON.stringify(killCounts('["hp","pm"]')) === '{"hp":2,"pm":2}',
    "an array of killed codes must read as two kills each");
  check(killCounts('{"dp":2,"hp":1}').dp === 2,
    "a counts object must read as itself");
  check(JSON.stringify(killCounts(null)) === "{}"
    && JSON.stringify(killCounts("not json")) === "{}",
    "a missing or corrupt column must read as no kills, not throw mid-round");
  check(retiredMechs({ dp: 2, hp: 1 }, {}).join() === "dp",
    "one kill is a name he did not like; two is the joke not landing");
  check(!retiredMechs({ dp: 2 }, { dp: 1 }).length,
    "a mechanism he also kept once must not be retired on kills alone");
}

// ===========================================================================
// THE PRICE.
//
// Separate from the naming engine on purpose: a wrong joke is embarrassing and
// a wrong price is a chargeback. Every figure below is one the site publishes
// in plain words on /pricing/, so a test failing here means a page is lying.
// ---------------------------------------------------------------------------
{
  const P = (d) => PR.priceOf(d, false);

  // The published height ladder, exactly as /pricing/ prints it.
  for (const [h, want] of [["3", 28], ["4", 36], ["5", 43], ["6", 48]]) {
    check(P({ kind: "numbers", height: h }) === want,
      `a ${h}" pair must be $${want}, got $${P({ kind: "numbers", height: h })}`);
  }

  // The four name bands, at the width each one is published for. Measured in
  // Arial Bold at 3 inches; the names are chosen for their width, not their
  // wit.
  const band = (txt) => PR.nameBand(txt, "Arial Bold", 3);
  for (const [txt, key] of [["Ox", "small"], ["Second Wind", "medium"]]) {
    check(band(txt).key === key,
      `"${txt}" finishes ${band(txt).width_in}" and should be the ${key} band, `
      + `got ${band(txt).key}`);
  }

  // THE BOUNDARY, which is the only part of banding anyone gets wrong.
  // Published as "up to 22 in" and "23-30 in", so 22.0 is small and anything
  // over it is medium. Rounding the width DOWN would have priced 22.1-22.9 as
  // "up to 22 inches", which is not what the page says.
  const fake = (w) => {
    for (const b of [{ max: 22, k: "small" }, { max: 30, k: "medium" },
                     { max: 48, k: "large" }, { max: null, k: "xl" }]) {
      if (b.max === null || Math.ceil(w - 1e-6) <= b.max) return b.k;
    }
  };
  check(fake(22) === "small", "a name finishing at exactly 22\" is small");
  check(fake(22.1) === "medium", "22.1\" is over the small band's published 22\"");
  check(fake(30) === "medium" && fake(30.1) === "large",
    "the medium band's published top is 30 inches");
  check(fake(48) === "large" && fake(49) === "xl",
    "over 48 inches is XL, and 48 itself is not");

  // The bundle. The site advertises a flat saving, so it must BE the saving.
  const n3 = P({ kind: "numbers", height: "3" });
  const nm = P({ kind: "name", height: "3", boatname: "Ox", font: "Arial Bold" });
  const both = P({ kind: "both", height: "3", boatname: "Ox", font: "Arial Bold" });
  check(both === n3 + nm - 10,
    `the bundle must be $10 off the two prices added up: $${n3} + $${nm} `
    + `- $10 = $${n3 + nm - 10}, got $${both}`);
  check(both === 56, `the published entry bundle is $56, got $${both}`);

  // The outline is a flat second layer, on either payload shape. It is called
  // with the raw browser post AND with the sanitised order row.
  check(P({ kind: "numbers", height: "3", outline: 1 }) === n3 + 12
        && P({ kind: "numbers", height: "3", finish: "outline" }) === n3 + 12,
    "the outline must add $12 whether it arrives as `outline` or `finish`");

  // EVERY VOCABULARY. This is the bug that shipped: the MCP server's slugs
  // matched nothing in the table and every quote fell through to the cheapest
  // product.
  check(P({ kind: "both", height: "3", boatname: "Ox", font: "Arial Bold" })
        === P({ kind: "Both", height: "3", boatname: "Ox", font: "Arial Bold" }),
    'the MCP slug "both" and the form label "Both" must price the same');
  check(P({ kind: "boat-name", height: "3", boatname: "Ox", font: "Arial Bold" })
        === nm,
    'the catalog id "boat-name" must price as a boat name');
  check(P({ kind: "Numbers + name", height: "3", boatname: "Ox",
            font: "Arial Bold" }) === both,
    "a cached page posting the retired bundle label must still price as the "
    + "bundle, not as the cheapest product");

  // STRICT REFUSES rather than guessing. A wrong number told to a customer by
  // an assistant is worse than no number.
  const throws = (d) => {
    try { PR.priceOf(d, true); return false; } catch { return true; }
  };
  check(throws({ kind: "a dinghy sticker" }),
    "a strict quote for a product we do not sell must throw, not fall "
    + "through to the cheapest thing in the shop");
  check(throws({ kind: "name", height: "3", font: "Arial Bold" }),
    "a strict quote for a name with no lettering must throw - the price "
    + "depends on the width it finishes at");
  check(throws({ kind: "name", height: "3", boatname: "Ox", font: "Papyrus" }),
    "a strict quote in a font we have no metrics for must throw rather than "
    + "measure it in some other face");
  check(throws({ kind: "numbers", height: "9" }),
    "a strict quote at a height we do not cut must throw");

  // LENIENT never throws and never undercharges below the floor. The order
  // path is lenient on purpose: losing a real order to a stale cached page is
  // worse than quietly correcting it, and the row carries a mismatch flag.
  for (const d of [{}, { kind: "" }, { kind: "numbers", height: "9" },
                   { kind: "name", boatname: "Ox", font: "Papyrus" },
                   { kind: "name" }]) {
    let v;
    try { v = PR.priceOf(d, false); } catch (e) { v = "threw: " + e.message; }
    check(typeof v === "number" && v >= 28,
      "the lenient path must always return at least the cheapest real price "
      + "for " + JSON.stringify(d) + ", got " + v);
  }

  // The itemisation is what the customer is SHOWN, so it has to add up to
  // what he is charged. A summary that disagrees with the Pay button is the
  // bug the form used to have.
  const b = PR.priceBreakdown({ kind: "both", height: "4", outline: 1,
    boatname: "Second Wind", font: "Impact",
    upgrades: "Rush - cut and shipped today" }, true);
  check(b.lines.reduce((t, l) => t + l.amount, 0) === b.amount,
    "the line items must sum to the total the card is charged");
  check(b.band && b.band.width_in > 0,
    "a priced name must report the width it was measured at, so the figure "
    + "can be checked against a tape measure rather than believed");
}

for (const f of fails) console.log("FAIL: " + f);
if (fails.length) {
  console.log("\n" + fails.length + " engine test(s) failed");
  process.exit(1);
}
console.log("engine tests pass");
