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

for (const f of fails) console.log("FAIL: " + f);
if (fails.length) {
  console.log("\n" + fails.length + " engine test(s) failed");
  process.exit(1);
}
console.log("engine tests pass");
