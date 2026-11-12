#!/usr/bin/env python3
"""Tests for the deterministic gates. Run by verify.py, so a regression here
fails the site build.

These are not unit tests for their own sake. Each one pins a decision that was
got WRONG at least once while the gate was being written, and every one of
those wrong versions looked fine until it was measured:

  - the first version failed "Unsinkable (Terms Apply)" because you cannot say
    a bracket, which would have deleted a signature joke of this bank
  - the second told customers that "Paid Off" and "Wave Goodbye" needed
    spelling out letter by letter, because Webster's 1913 has no irregular
    verb forms
  - the third reported that "holic" is not a word, when the name is Aqua-holic
  - the fourth passed 12 of the 30 deliberately-misspelled names, because
    Webster's 1913 lists "bote", "nawt", "gud" and "shure" as real words

Run: python3 mcp/test_gates.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gates  # noqa: E402

BANK = json.loads((HERE / "data" / "name_bank.json").read_text())
NAMES = [n["name"] for n in BANK["names"]]


def run():
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    # --- spec test 11, verbatim ------------------------------------------
    # "a deliberately misspelled riff candidate (e.g. 'Knot On Call' is fine,
    #  'Nauti-4-U' class) fails the radio gate and is never dealt"
    check(gates.radio_gate("Knot On Call")["dealable"],
          "spec test 11: 'Knot On Call' must pass the radio gate and it does not")
    for soup in ("Nauti-4-U", "Sea-U-L8r", "B4 Sunset", "Gr8 Escape"):
        check(not gates.radio_gate(soup)["dealable"],
              "spec test 11: %r must fail the radio gate and it does not" % soup)

    # --- the bank is curated, so the gate must not refuse it -------------
    # A gate that rejects names the shop already sells on its own website is
    # not strict, it is miscalibrated.
    refused = [n for n in NAMES if not gates.radio_gate(n)["dealable"]]
    check(not refused,
          "the radio gate refuses %d names that are already on the site "
          "(%s) - a gate that rejects the curated bank is wrong, not strict"
          % (len(refused), ", ".join(refused[:5])))

    # --- recall on the deliberately-misspelled category -----------------
    # The site has a whole category of names built to be heard right and
    # spelled wrong. The gate exists to notice them. Measured, not assumed.
    mis = [n["name"] for n in BANK["names"] if "misspelled" in n["categories"]]
    missed = [n for n in mis if not gates.radio_gate(n)["spell_out"]]
    check(len(mis) - len(missed) >= 29,
          "radio gate catches only %d of %d deliberately-misspelled names "
          "(missed: %s)" % (len(mis) - len(missed), len(mis), missed))
    # 'Boat Goes Fast' is the one allowed miss and it is not actually
    # misspelled - the site files it under misspelled because the joke is the
    # grammar. If the miss list ever changes, that is a real regression.
    check(missed in ([], ["Boat Goes Fast"]),
          "the radio gate's misses changed: %s" % missed)

    # --- no false positives on the sincere lane -------------------------
    # Halcyon, Lodestar, Wild Rice. If the gate tells a man that Lodestar needs
    # spelling out, he stops believing the rest of the page.
    sincere = [n["name"] for n in BANK["names"]
               if (n.get("humor_mechanism") or "").startswith("sincere")]
    fp = [n for n in sincere if gates.radio_gate(n)["spell_out"]]
    check(not fp, "radio gate wrongly flags sincere names: %s" % fp)

    # The whole-bank false-positive rate. 23 of 1,089 at the time of writing,
    # every one a real coinage (Aquaholic, Delulu, Sofishticated). A jump here
    # means the lexicon or the respelling rules have drifted.
    flagged = [n["name"] for n in BANK["names"]
               if "misspelled" not in n["categories"]
               and gates.radio_gate(n["name"])["spell_out"]
               and any(gates._nonstandard(t)[0]
                       for t in gates._tokens(n["name"]))]
    check(len(flagged) <= 28,
          "radio gate now flags %d non-misspelled names as needing a "
          "spell-out (was 23). Something in the lexicon or the respelling "
          "rules regressed: %s" % (len(flagged), flagged))

    # --- the devices that only work written down ------------------------
    for vis in ("Unsinkable (Terms Apply)", "Paid In Full*",
                "Starboard Is Left*", "Mutual Decision*"):
        r = gates.radio_gate(vis)
        check(r["dealable"], "%r must stay dealable - the parenthetical IS "
                             "the joke" % vis)
        check(r.get("visual_only"),
              "%r must be flagged visual_only so the engine can say the joke "
              "needs to be seen" % vis)
    # And the readback must be the WORDS, not the typography.
    rb = gates.radio_gate("Unsinkable (Terms Apply)")["readback"]
    check("(" not in rb and "*" not in rb,
          "the spoken readback still contains punctuation: %r" % rb)

    # --- irregular verbs and modern words -------------------------------
    # Each of these was wrongly flagged by a real version of this gate.
    for ok in ("Paid Off", "Wave Goodbye", "My Boat Has A Boat",
               "Independence Day", "Last Paycheck", "Lasagna",
               "Wake Zone? Never Heard Of Her", "Human Floatie",
               "Co-Signed", "Low-Hanging Fruit", "Bermuda Try-Angle",
               "Gone Fishin' Forever", "Marlin Monroe", "KPI"):
        check(not gates.radio_gate(ok)["spell_out"],
              "%r is ordinary English and must not be flagged for a "
              "spell-out" % ok)

    # --- overuse ---------------------------------------------------------
    # The spec names these two as the Tier-1 class by example.
    for cliche in ("Vitamin Sea", "Seas the Day", "Serenity"):
        o = gates.overuse_gate(cliche)
        check(o["tier"] == 1, "%r must be tier 1, got %s" % (cliche, o["tier"]))
        check(not o["top_pick_eligible"],
              "%r must be excluded from top picks" % cliche)
        check(o["note"], "%r must carry the one-in-every-marina note" % cliche)
    check(gates.overuse_gate("Pontoon Of Doom")["tier"] == 0,
          "an ordinary bank name must not be graded as overused")

    # HONESTY LIMIT (spec §4a): the overuse tier is a heuristic from market
    # data, not a registry. We cannot see any particular marina and must never
    # say or imply that we can.
    for name in ("Vitamin Sea", "Seas the Day", "Shore Thing", "Trolling"):
        note = gates.overuse_gate(name)["note"] or ""
        bad = gates.claims_are_honest(note)
        check(not bad,
              "the overuse note for %r claims %r - we have no registry and "
              "cannot support that" % (name, bad))

    # --- novelty ---------------------------------------------------------
    check(not gates.novelty_gate("Knot Working", NAMES)["novel"],
          "a name already in the bank must not pass the novelty gate")
    check(not gates.novelty_gate("Knot Workin", NAMES)["novel"],
          "a one-letter variant of a bank name must not pass as novel")
    nv = gates.novelty_gate("Dockside Pecan Pie", NAMES)
    check(nv["novel"], "a genuinely new name must pass the novelty gate "
                       "(closest was %r at %s)" % (nv["closest"],
                                                   nv["similarity"]))

    # --- the lexicon is a committed artefact ----------------------------
    lex = HERE / "data" / "lexicon.txt.gz"
    check(lex.exists(), "mcp/data/lexicon.txt.gz is missing - the radio gate "
                        "cannot run. Rebuild with mcp/build_lexicon.py")
    if lex.exists():
        check(len(gates.lexicon()) > 150000,
              "the lexicon has only %d words - it was rebuilt from something "
              "smaller than web2" % len(gates.lexicon()))

    return fails


def main():
    fails = run()
    for f in fails:
        print("FAIL: %s" % f)
    if fails:
        print("\n%d gate test(s) failed" % len(fails))
        return 1
    print("gate tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
