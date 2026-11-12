#!/usr/bin/env python3
"""Merge the hand-written tag files into the derived name bank.

WHY THE TAGS LIVE IN A SEPARATE FILE. The bank itself is derived - rebuilt from
engine/namegen.py and engine/tools.py on every build, so a name added to the
site reaches the engine automatically. Tags cannot live in a derived file or
the next build erases them. So:

    engine/*.py        the names            (site source, authoritative)
    mcp/tags/*.tsv     the judgements       (hand-written, authoritative)
    mcp/data/*.json    the join of the two  (derived, never edited)

The tag files are keyed BY NAME rather than by row number on purpose. A row
number would silently point at a different name the moment the bank grows;
a name either matches or fails the build loudly.

Format, one row per name, tab-separated:

    Knot Working<TAB>hp<TAB>c<TAB>optional note

Run: python3 mcp/apply_tags.py        (reports coverage; build_bank.py calls it)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from taxonomy import MECHANISMS, LEVELS, check  # noqa: E402

TAGS = HERE / "tags"


def load_tags():
    """Read every tags/*.tsv. Returns (by_name, problems)."""
    by_name, problems, seen_in = {}, [], {}
    for f in sorted(TAGS.glob("*.tsv")):
        for lineno, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.rstrip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                problems.append("%s:%d needs name<TAB>mechanism<TAB>level, got %r"
                                % (f.name, lineno, line))
                continue
            name, mech, level = parts[0].strip(), parts[1].strip(), parts[2].strip()
            why = parts[3].strip() if len(parts) > 3 else None
            bad = check(mech, level)
            if bad:
                problems.append("%s:%d %s: %s" % (f.name, lineno, name, bad))
                continue
            key = name.lower()
            if key in by_name:
                problems.append("%s:%d %r is tagged twice (also %s)"
                                % (f.name, lineno, name, seen_in[key]))
                continue
            seen_in[key] = "%s:%d" % (f.name, lineno)
            by_name[key] = {"humor_mechanism": MECHANISMS[mech],
                            "mechanism_code": mech,
                            "humor_level": LEVELS[level],
                            "level_code": level,
                            "tag_note": why}
    return by_name, problems


def apply(names):
    """Tag a list of bank rows in place. Returns (stats, problems)."""
    by_name, problems = load_tags()
    bank_keys = {n["name"].lower() for n in names}

    # A tag for a name that is no longer in the bank means the site's name list
    # changed and the tag file was not followed up. Loud, not silent.
    for key in sorted(set(by_name) - bank_keys):
        problems.append("tagged name %r is not in the bank any more - the site "
                        "source changed; remove or re-point the tag" % key)

    tagged = 0
    for n in names:
        t = by_name.get(n["name"].lower())
        if t:
            n.update({k: v for k, v in t.items() if k != "tag_note"})
            if t["tag_note"]:
                n["tag_note"] = t["tag_note"]
            tagged += 1
    stats = {"tagged": tagged, "total": len(names),
             "untagged": len(names) - tagged}
    return stats, problems


def main():
    import json
    bank_f = HERE / "data" / "name_bank.json"
    bank = json.loads(bank_f.read_text())
    stats, problems = apply(bank["names"])
    for p in problems:
        print("PROBLEM: %s" % p)
    print("tagged %d of %d  (%d still untagged)"
          % (stats["tagged"], stats["total"], stats["untagged"]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
