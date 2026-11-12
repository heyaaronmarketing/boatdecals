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

for (const f of fails) console.log("FAIL: " + f);
if (fails.length) {
  console.log("\n" + fails.length + " engine test(s) failed");
  process.exit(1);
}
console.log("engine tests pass");
