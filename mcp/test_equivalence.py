#!/usr/bin/env python3
"""Prove the Python gates and the Worker gates agree. Run by verify.py.

WHY THIS EXISTS. The MCP server has to be reachable over HTTPS by Claude's
directory and by ChatGPT, so it runs on the Cloudflare Worker - JavaScript.
The gates' validation corpus is 1,089 names in Python. Both halves are real
and neither can be deleted.

Every TABLE has one definition (mcp/gates.py, emitted to worker/gates-data.js
by build_gates_js.py). But the LOGIC exists twice, and two implementations of
the moat is precisely what the spec's one-implementation rule exists to stop:
an assistant telling a customer his name is clear on the radio while the site's
own tool calls it a mouthful is the exact failure.

So the two are compared over EVERY bank name on EVERY field - verdict,
dealable, readback, score, spell_out, visual_only, every reason string, every
width at every height, the overuse tier and its note. Not a spot check. If
they disagree anywhere, the build stops.

Run: python3 mcp/test_equivalence.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gates as G  # noqa: E402

BANK = json.loads((HERE / "data" / "name_bank.json").read_text())

# Names that are not in the bank but exercise the edges: the rebus class the
# spec names, the parenthetical devices, the irregular verbs that broke an
# earlier version, and the two Tier-1 cliches.
FIXTURES = [
    "Nauti-4-U", "Sea-U-L8r", "B4 Sunset", "Gr8 Escape", "Knot On Call",
    "Unsinkable (Terms Apply)", "Paid In Full*", "Starboard Is Left*",
    "Paid Off", "Wave Goodbye", "Vitamin Sea", "Seas the Day", "Serenity",
    "Pour Decisions", "Ahoyy", "Bote", "Fysh", "Halcyon", "KPI",
    "Déjà Vu (Again)", "Aqua-holic", "Bermuda Try-Angle", "Wet❄Couch",
    "Hull Integrity 74%", "Ctrl+Alt+Float", "", "   ",
]


def py_side(names):
    out = {}
    for n in names:
        r = G.radio_gate(n)
        o = G.overuse_gate(n)
        out[n] = {
            "radio": {k: r.get(k) for k in
                      ("verdict", "dealable", "readback", "spell_out",
                       "visual_only", "score", "reasons")},
            "overuse": {k: o[k] for k in
                        ("tier", "top_pick_eligible", "note")},
            "fit": G.fit_gate(n, "Arial Bold", 34),
            "fit_impact": G.fit_gate(n, "Impact", None),
        }
    return out


def js_side(names):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(names, f)
        path = f.name
    try:
        p = subprocess.run(["node", str(HERE / "js_gate_probe.mjs"), path],
                           capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError("the JS gates would not run: %s"
                               % (p.stderr or "")[-600:])
        return json.loads(p.stdout)
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def norm(v):
    """JS has one number type; Python distinguishes int from float. Compare
    numbers by value so 3 and 3.0 are not reported as a disagreement."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return round(float(v), 6)
    if isinstance(v, dict):
        return {str(k): norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


def run():
    names = [n["name"] for n in BANK["names"]] + FIXTURES
    try:
        js = js_side(names)
    except Exception as e:
        return ["could not run the JS gates, so the two implementations are "
                "unverified: %s" % e]

    fails = []
    for n in names:
        a, b = norm(py_side([n])[n]), norm(js.get(n))
        if b is None:
            fails.append("the JS gates returned nothing for %r" % n)
            continue
        for area in ("radio", "overuse", "fit", "fit_impact"):
            pa, pb = a.get(area), b.get(area)
            if pa == pb:
                continue
            keys = sorted(set(pa or {}) | set(pb or {}))
            for k in keys:
                if (pa or {}).get(k) != (pb or {}).get(k):
                    fails.append(
                        "%s disagree on %r [%s.%s]: python=%r js=%r"
                        % ("the two implementations", n, area, k,
                           (pa or {}).get(k), (pb or {}).get(k)))
            if len(fails) > 25:
                fails.append("... stopping after 25 disagreements")
                return fails
    return fails


def main():
    fails = run()
    for f in fails:
        print("FAIL: %s" % f)
    if fails:
        print("\n%d disagreement(s)" % len(fails))
        return 1
    print("python and worker gates agree on all %d bank names + %d fixtures"
          % (len(BANK["names"]), len(FIXTURES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
