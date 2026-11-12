#!/usr/bin/env python3
"""Build the naming engine's name bank from the site's own two name sources.

The bank is the moat. A base model can invent boat names for free, so a list
alone gives it no reason to call this app; what it cannot do is hand back
1,000 names curated to a house standard. That curation is the asset, and it
already exists in two places on the site:

  engine/namegen.py    the generator's 21 categories, as a JS object literal
  engine/tools.py      FUNNY_GROUPS, the funny-names page, 6 groups

Both are READ, never copied. A name added to either source reaches the engine
on the next build; a hand-maintained third list would drift from the site
within a month and nobody would notice which one was wrong.

Run:  python3 mcp/build_bank.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "engine"))

DATA = HERE / "data"


def js_bank():
    """The generator's categories, via the Node extractor (the source is JS)."""
    subprocess.run(["node", str(HERE / "extract_bank.mjs")],
                   check=True, capture_output=True, text=True)
    return json.loads((DATA / "_bank_js.json").read_text())


def funny_bank():
    """The funny-names page, which is Python data rather than JS."""
    import tools as T
    out = []
    for group, names in T.FUNNY_GROUPS:
        for n in names:
            out.append({"name": n.strip(), "group": group})
    return out


def main():
    js = js_bank()
    rows = {r["name"].lower(): r for r in js["names"]}
    for r in rows.values():
        r.setdefault("note", None)

    # Merge the funny list. An overlap is not a conflict - a name can be both a
    # generator pun and a curated funny-page entry - so the categories union
    # rather than one source winning.
    added = overlapped = 0
    for f in funny_bank():
        key = f["name"].lower()
        cat = "funny:" + f["group"]
        if key in rows:
            if cat not in rows[key]["categories"]:
                rows[key]["categories"].append(cat)
            overlapped += 1
        else:
            name = f["name"]
            rows[key] = {
                "name": name,
                "categories": [cat],
                "note": None,
                "char_count": len(name),
                "word_count": len(name.split()),
                "source": "bank",
            }
            added += 1

    names = sorted(rows.values(), key=lambda r: r["name"].lower())

    # Every name needs these before the engine may deal it. They are filled by
    # the tagging pass, NOT guessed at runtime - a runtime LLM guess is both a
    # per-session cost and a different answer every time.
    for r in names:
        r.setdefault("humor_mechanism", None)
        r.setdefault("humor_level", None)
        r.setdefault("boat_types", [])
        r.setdefault("style_lanes", [])
        r.setdefault("themes", [])
        r.setdefault("overuse_tier", None)

    # Join the hand-written judgements onto the derived names. This happens
    # HERE, inside the one command that writes the bank, so there is no window
    # in which a tagged bank exists on disk untagged - which would let the
    # engine start up and deal names with no mechanism.
    import apply_tags
    stats, problems = apply_tags.apply(names)

    # Then derive the four fields that follow from the hand tags and the
    # site's own categories. Done here, after the join, because the lane
    # derivation reads mechanism_code and level_code - a sincere name is in the
    # sincere lane whatever category it sits in.
    import derive_tags
    dstats, dproblems = derive_tags.derive(names)
    problems += dproblems

    bank = {
        "note": "DERIVED FILE - do not edit. Run: python3 mcp/build_bank.py",
        "sources": ["engine/namegen.py", "engine/tools.py:FUNNY_GROUPS"],
        "name_count": len(names),
        "categories": sorted({c for r in names for c in r["categories"]}),
        "untagged": sum(1 for r in names if not r["humor_mechanism"]),
        "lanes": sorted({l for r in names for l in r.get("style_lanes", [])}),
        "themes_used": sorted({t for r in names for t in r.get("themes", [])}),
        "mechanisms": sorted({r["humor_mechanism"] for r in names
                              if r.get("humor_mechanism")}),
        "names": names,
    }
    DATA.mkdir(exist_ok=True)
    (DATA / "name_bank.json").write_text(json.dumps(bank, indent=1))

    print("name bank: %d unique names, %d categories"
          % (len(names), len(bank["categories"])))
    print("   generator  %d" % len(js["names"]))
    print("   funny page %d new, %d already in the generator"
          % (added, overlapped))
    print("   untagged   %d  (humor_mechanism required before a name is dealt)"
          % bank["untagged"])
    pct = 100.0 * stats["tagged"] / max(stats["total"], 1)
    print("   tagged     %d  (%.1f%%)" % (stats["tagged"], pct))
    print("   derived    lanes + themes + boat types + overuse tier")
    print("              %d hand overrides, %d names with no theme, "
          "%d that suit any boat"
          % (dstats["overridden"], dstats["no_theme"], dstats["any_boat"]))
    for p_ in problems:
        print("   PROBLEM: %s" % p_)
    if problems:
        raise SystemExit("tag files have %d problem(s) - bank written, fix "
                         "them before building the engine" % len(problems))
    print("-> %s" % (DATA / "name_bank.json"))


if __name__ == "__main__":
    main()
