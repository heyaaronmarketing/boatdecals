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
import { killCounts, retiredMechs } from "../worker/mcp.js";

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

for (const f of fails) console.log("FAIL: " + f);
if (fails.length) {
  console.log("\n" + fails.length + " engine test(s) failed");
  process.exit(1);
}
console.log("engine tests pass");
