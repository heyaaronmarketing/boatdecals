#!/usr/bin/env python3
"""Pre-deploy gate. Runs after every build - a silent build failure shipped a
stale public/ once, so this refuses to pass unless the output is genuinely fresh
and internally consistent."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "public"
fails = []

r = subprocess.run([sys.executable, "-m", "py_compile"] +
                   [str(p) for p in (ROOT / "engine").glob("*.py")],
                   capture_output=True, text=True)
if r.returncode: fails.append("engine does not compile:\n" + r.stderr)

r = subprocess.run(["node", "--check", str(ROOT / "worker" / "index.js")],
                   capture_output=True, text=True)
if r.returncode: fails.append("worker/index.js does not parse:\n" + r.stderr)

pages = list(OUT.rglob("index.html"))
if len(pages) < 55: fails.append("only %d pages built" % len(pages))

have = {"/sitemap.xml", "/robots.txt", "/llms.txt", "/favicon.svg"}
for f in pages:
    p = "/" + str(f.parent.relative_to(OUT)).replace("\\", "/") + "/"
    have.add("/" if p == "/./" else p)

broken, blocks, bad_json, titles, descs = set(), 0, 0, [], []
for f in OUT.rglob("*.html"):
    t = f.read_text()
    for h in re.findall(r'href="(/[^"#?]*)"', t):
        if not h.startswith("/api") and h not in have: broken.add(h)
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        blocks += 1
        try: json.loads(m)
        except Exception: bad_json += 1; fails.append("invalid JSON-LD in %s" % f)
    if "&amp;amp;" in t or "&amp;mdash;" in t:
        fails.append("double-escaped entities in %s" % f)
    if f.name == "index.html":
        mt = re.search(r"<title>(.*?)</title>", t)
        md = re.search(r'name="description" content="(.*?)"', t)
        if mt: titles.append(mt.group(1))
        if md: descs.append(md.group(1))

if broken: fails.append("broken internal links: %s" % sorted(broken))
for label, vals in (("title", titles), ("description", descs)):
    dupes = {v for v in vals if vals.count(v) > 1}
    if dupes: fails.append("duplicate %s: %s" % (label, sorted(dupes)[:3]))

# The wizard is the only conversion path; if it loses a step, nothing converts.
design = (OUT / "design" / "index.html").read_text()
for need in ("data-step=\"1\"", "data-step=\"5\"", "id=payelement", "BNS_COL=",
             "id=prevstage", "name=kind"):
    if need not in design: fails.append("order wizard missing %s" % need)

# Prices are duplicated between the generator and the worker on purpose; they
# must not drift, because the worker's number is what gets charged.
import sys as _s; _s.path.insert(0, str(ROOT / "engine"))
from content import PRICE, UPGRADES
wjs = (ROOT / "worker" / "index.js").read_text()
for lbl, amt, _b, _f, _n in UPGRADES:
    if '"%s": %d' % (lbl, amt) not in wjs:
        fails.append("worker UPGRADE_ADD missing/mismatched: %s = %d" % (lbl, amt))
    # The client joins upgrades with " | "; a label containing the delimiter
    # would be split into fragments the worker cannot price, undercharging us.
    if "|" in lbl:
        fails.append("upgrade label contains the join delimiter: %s" % lbl)
if "upgrades:ups.join(' | ')" not in (ROOT / "engine" / "order.py").read_text():
    fails.append("client upgrade delimiter changed without updating the worker")
if '"Registration numbers": %d' % PRICE["numbers"] not in wjs:
    fails.append("worker BASE disagrees with content.PRICE")

print("%d pages | %d JSON-LD blocks (%d invalid) | %d broken links"
      % (len(pages), blocks, bad_json, len(broken)))
if fails:
    print("\nFAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
print("all gates pass")
