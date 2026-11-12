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


def gates_charset():
    """Exactly what worker/outline.js will cut. The metrics table has to cover
    all of it or the fit gate silently drops characters."""
    return ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            "0123456789 .,'&!?@#:/()+-")


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

    # --- the fit gate ----------------------------------------------------
    met = gates.metrics()["fonts"]
    cat = json.loads((HERE.parent / "public" / "catalog.json").read_text())
    for f in cat["options"]["fonts"]:
        check(f["name"] in met,
              "no font metrics for %r - the fit gate cannot measure a face the "
              "shop sells, and it must not guess" % f["name"])
    for label, m in met.items():
        missing = [c for c in gates_charset() if c not in m["advance"]]
        check(not missing,
              "%s is missing advances for %s - a character counted as zero "
              "width is how a 20-inch name gets quoted at 14"
              % (label, " ".join(repr(c) for c in missing[:6])))

    # Font-blindness was the bug. These two faces must come out materially
    # different at the same cap height, or the metrics are not being read.
    narrow, _ = gates.width_in("Knot Working", "Impact", 4)
    wide, _ = gates.width_in("Knot Working", "Snap ITC", 4)
    check(wide > narrow * 1.3,
          "Impact and Snap ITC measure within 30%% of each other (%.1f vs "
          "%.1f) - the fit gate is not actually reading per-face metrics"
          % (narrow, wide))

    # The old browser formula under-read by 24-41%. Pin the real number so a
    # regression to a character-count guess fails here.
    w, _ = gates.width_in("Wet Couch", "Arial Bold", 4)
    check(29.5 < w < 31.5,
          '"Wet Couch" at 4" in Arial Bold should measure about 30.4" wide, '
          "got %.1f" % w)
    # Widths must scale linearly with cap height - it is the same outline.
    w3, _ = gates.width_in("Wet Couch", "Arial Bold", 3)
    check(abs(w3 * (4.0 / 3.0) - w) < 0.05,
          "width does not scale linearly with cap height: 3in=%.2f 4in=%.2f"
          % (w3, w))

    # An unsupported character is reported, never counted as zero.
    _, miss = gates.width_in("Wet\u2744Couch", "Arial Bold", 4)
    check(miss, "an uncuttable character must be reported by the fit gate")

    fg = gates.fit_gate("Knot Working", "Arial Bold", 96)
    check(fg["verdict"] == "fits", "a 38in name on a 96in run should fit, got "
                                   "%s" % fg["verdict"])
    fg = gates.fit_gate("Knot Working", "Arial Bold", 26)
    check(fg["verdict"] == "too_wide",
          "a 38in name at 4in on a 26in run must not report a fit, got %s"
          % fg["verdict"])
    check(fg["best_height"] is None, "too_wide must offer no height")
    # Spec test 11: too wide for the stated transom is excluded OR
    # height-capped, with the fit shown.
    fg = gates.fit_gate("Wet Couch", "Arial Bold", 34)
    check(fg["verdict"] == "height_capped",
          "spec test 11 wants a height cap with the fit shown, got %s"
          % fg["verdict"])
    check(fg["best_height"] and fg["best_height"] < 6,
          "a height cap must name the height that fits")
    check(any('"' in r for r in fg["reasons"]),
          "the height cap must show the customer the actual measurement")

    # --- registration numbers are law, not taste -------------------------
    check(not gates.registration_gate("IA 3717 ZW", "Snap ITC", 3)["legal"],
          "a script face must not be legal for registration numbers")
    check(not gates.registration_gate("IA 3717 ZW", "Arial Bold", 2)["legal"],
          'under 3" must not be legal for registration numbers')
    check(gates.registration_gate("IA 3717 ZW", "Arial Bold", 3)["legal"],
          '3" block characters must be legal')

    # --- the site must not re-invent either fact -------------------------
    # The spec's hardest rule is one implementation. The generator page carries
    # copies of the metrics and the overuse tiers for the browser; if they
    # drift from the authority, the free tool contradicts the paid engine.
    page = (HERE.parent / "public" / "tools" / "boat-name-generator"
            / "index.html")
    if not page.exists():
        check(False, "the boat-name-generator page is missing")
    else:
        html = page.read_text(encoding="utf-8")
        check("window.NMB_REF=" in html,
              "the generator page no longer carries the measured font metrics "
              "- it has gone back to guessing widths")
        # Carrying the table is not the same as USING it. The first version of
        # this test checked only that the table was present, so reverting
        # width() to a character count passed cleanly - the table sat there
        # unread. Check the call, and check the old guess is gone.
        check("widthFace(" in html and "window.NMB_REF, 4)" in html,
              "the page carries the measured metrics but width() no longer "
              "reads them - a table nobody calls is not a source of truth")
        for guess in ("length*2.5", "length * 2.5", "length*2.5 +"):
            check(guess not in html,
                  "the old character-count width formula (%r) is back on the "
                  "page; it under-read real widths by 24-41%%" % guess)
        import re as _re
        m = _re.search(r"window\.NMB_REF=\{cap:([0-9.]+),adv:\{(.*?)\}\};",
                       html)
        if not m:
            check(False, "could not read the emitted metrics off the page")
        else:
            ref = met["Arial Bold"]
            check(abs(float(m.group(1)) - ref["cap_ratio"]) < 1e-5,
                  "the page's cap ratio has drifted from font_metrics.json")
            got = dict(_re.findall(r'"((?:[^"\\]|\\.)*)":([0-9.]+)',
                                   m.group(2)))
            bad = [c for c in "ABCWabcw 0127"
                   if abs(float(got.get(c, -1))
                          - ref["advance"][c] / ref["upm"]) > 1e-4]
            check(not bad,
                  "the page's advance widths have drifted from "
                  "font_metrics.json for: %s" % bad)

        # The honesty limit, on the live page this time.
        for claim in ("check your marina first",
                      "you will not meet another one"):
            check(claim not in html.lower(),
                  "the generator page still says %r - we have market data, "
                  "not a registry, and must not imply we can see a "
                  "customer's marina" % claim)
        t1 = _re.search(r"window\.NMB_T1=(\[.*?\]);", html)
        if t1:
            check(set(json.loads(t1.group(1))) == set(gates.OVERUSE_T1),
                  "the page's tier-1 overuse list has drifted from gates.py")

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
