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

_YR_N = (r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
         r"twelve|fifteen|twenty)")
_YR_SPAN = _YR_N + r"(?:\s*(?:to|-|&ndash;|&mdash;)\s*\d+)?"
_DUR = r"(?:warrant\w*|durabilit\w*|outdoor life|rated for|lasts?|adhesion|chalks)"
_MATERIAL = r"(?:film|vinyl|stock)"
# (pattern, may a person-noun excuse it)
_FILM_LIFE_PATTERNS = [
    (_YR_SPAN + r"[\s-]year\s+(?:\w+\s+){0,3}" + _MATERIAL, True),
    (_YR_SPAN + r"\s+years?\s+on\s+(?:\w+\s+){0,3}" + _MATERIAL, False),
    (_DUR + r"[^<.]{0,40}?" + _YR_SPAN + r"[\s-]*years?", False),
    (_YR_SPAN + r"[\s-]*years?[^<.]{0,40}?" + _DUR, False),
    (_MATERIAL + r"\s+(?:runs?|lasts?)[^<.]{0,20}?" + _YR_SPAN + r"[\s-]*years?", False),
]

broken, blocks, bad_json, titles, descs = set(), 0, 0, [], []
for f in OUT.rglob("*.html"):
    t = f.read_text()
    for h in re.findall(r'href="(/[^"#?]*)"', t):
        if not h.startswith("/api") and h not in have: broken.add(h)
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        blocks += 1
        try: json.loads(m)
        except Exception: bad_json += 1; fails.append("invalid JSON-LD in %s" % f)
    # Film-life figures were pulled from the whole site on Aaron's call, so a
    # year figure must never attach to the MATERIAL again. Proximity was the
    # wrong test in both directions: a wide window let "we cut" next door
    # suppress a real claim, and a narrow one flagged the About page's "fifteen
    # years of making vinyl stick". What separates them is what the years are
    # attached to - a warranty, a film, a rating (bad), or a verb and a person
    # (fine). Checked against a fixture of 9 real claims and 8 legitimate
    # sentences: 0 missed, 0 false positives.
    for pat, person_ok in _FILM_LIFE_PATTERNS:
        for m in re.finditer(r"(?i)\b" + pat, t):
            if person_ok and re.match(r"(?i)\s*(?:pro|veteran|owner|career)\b",
                                      t[m.end():m.end() + 14]):
                continue        # "a 15-year vinyl pro" is a person
            fails.append("film-life claim %r in %s - we do not publish a year "
                         "figure" % (" ".join(m.group(0).split())[:48], f))
    for dbl in set(re.findall(r"&amp;(#?\w{2,8});", t)):
        fails.append("double-escaped entity &amp;%s; in %s" % (dbl, f))
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
# Step count asserted explicitly so a section cannot vanish unnoticed.
_steps = len(re.findall(r'data-step="\d"', design))
if _steps != 4:
    fails.append("order wizard has %d steps, expected 4" % _steps)
for need in ("data-step=\"1\"", "data-step=\"4\"", "id=payelement", "BNS_COL=",
             "id=prevsvg", "id=p_num", "name=kind"):
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
from content import PREFIX_STATE as _PS
import re as _r
_m = _r.search(r'const PREFIX_STATE = \{(.*?)\};', wjs, _r.S)
if not _m:
    fails.append("worker lost its PREFIX_STATE table")
else:
    _worker = dict(_r.findall(r'(\w{2}):"([^"]+)"', _m.group(1)))
    if _worker != _PS:
        _d = set(_PS.items()) ^ set(_worker.items())
        fails.append("PREFIX_STATE drifted between content.py and the worker: %s"
                     % sorted(_d)[:6])

if '"Registration numbers": %d' % PRICE["numbers"] not in wjs:
    fails.append("worker BASE disagrees with content.PRICE")

# The radio VALUE is a contract between the form, the worker and every row in
# D1; the LABEL beside it is free text. Catch a rename of the value that does
# not reach worker/index.js.
sys.path.insert(0, str(ROOT / "engine"))
from order import KINDS as _KINDS
for _val, _base, _c, _p, _f, _k, _label in _KINDS:
    if '"%s": %d' % (_val, _base) not in wjs:
        fails.append("order kind %r (base %d) missing from worker BASE - the radio "
                     "value is a contract, rename the label instead" % (_val, _base))

# Published statistics must trace to the cited source. These pages shipped
# invented fleet figures for months (NY at 1.3M against an actual 428,445), so
# the numbers now live in one table and the gate proves every state page prints
# the value from it and nothing else.
from state_data import USCG_FLEET, USCG_NATIONAL
from state_waters import WATERS
from content import STATES as _ST
for _s in _ST:
    _page = OUT / "registration-numbers" / _s["slug"] / "index.html"
    if not _page.exists():
        fails.append("missing state page %s" % _s["slug"]); continue
    _h = _page.read_text()
    _n = "{:,}".format(USCG_FLEET[_s["slug"]][0])
    if _n not in _h:
        fails.append("%s does not print its USCG figure %s" % (_s["slug"], _n))
    if "uscgboating.org" not in _h:
        fails.append("%s cites no source for its statistics" % _s["slug"])
    if _s["slug"] not in WATERS:
        fails.append("%s has no boating-waters research" % _s["slug"])
    for _name, _note in WATERS.get(_s["slug"], {}).get("waters", []):
        if _name.split(" and ")[0].split(",")[0] not in _h:
            fails.append("%s: water %r never reaches the page" % (_s["slug"], _name))

# Every state accent must carry white text. The prefix letters sit on `deep`
# with a `deep` halo, so a palette edit that lightens one turns the badge into
# nothing. 4.5:1 is the WCAG AA threshold for large text with room to spare.
from state_data import STATE_ACCENT, contrast_on_white_text
for _slug, (_deep, _bright, _motif) in STATE_ACCENT.items():
    _c = contrast_on_white_text(_deep)
    if _c < 4.5:
        fails.append("state accent %s: white on %s is only %.2f:1, prefix "
                     "will not read" % (_slug, _deep, _c))
    if not _motif:
        fails.append("state accent %s has no motif label" % _slug)
for _s in _ST:
    if _s["slug"] not in STATE_ACCENT:
        fails.append("no accent palette for %s" % _s["slug"])

# A <title> that stops dead at the slice length with no brand suffix is a
# hard truncation, not a title. The product pages shipped "Boat Registration
# Numbers for Any Boat, Legal in All 50 St" because the H1 was being reused as
# the title and sliced at 58. An H1 and a title do different jobs; give a page
# its own title rather than cutting one to fit.
_SUFFIXES = (" | Boat Number Shop", " | Boat Numbers")
for _f in OUT.rglob("index.html"):
    _m = re.search(r"<title>(.*?)</title>", _f.read_text())
    if not _m:
        continue
    _t = _m.group(1)
    if len(_t) in (58, 59, 60) and not _t.endswith(_SUFFIXES):
        fails.append("title truncated mid-word in %s: %r" % (_f, _t))

# Sandbox checkout invariants. The card form must never hand a full number to
# the payload, and the worker must refuse one if a future edit ever does.
mp = (ROOT / "engine" / "mockpay.py").read_text()
if "return {brand: brandOf(d)[1] || 'Card', last4: d.slice(-4)}" not in mp:
    fails.append("mockpay collect() no longer returns brand+last4 only - "
                 "check it is not leaking a full card number")
for banned in ("pan:", "number:", "cvc:", "card_number"):
    if banned in mp.split("function collect()")[-1]:
        fails.append("mockpay collect() appears to return %r" % banned)
if "carriesCardNumber" not in wjs or "const PAN" not in wjs:
    fails.append("worker lost its card-number refusal guard")
# Every element id the wizard's JS writes to must exist in the markup. A
# removed element leaves a silent TypeError that kills everything after it in
# the same function - which is exactly how the step-2 scroll and autofocus
# broke without any visible symptom.
import re as _re
order_js = (ROOT / "engine" / "order.py").read_text()
js_ids = set(_re.findall(r"\$\('([A-Za-z0-9_]+)'\)", order_js))
markup_ids = set(_re.findall(r"id=([A-Za-z0-9_]+)", order_js))
markup_ids |= set(_re.findall(r'id="([A-Za-z0-9_]+)"', design))
missing = sorted(i for i in js_ids - markup_ids if i not in {"order"})
if missing:
    fails.append("order.py JS writes to ids with no element: %s" % missing)

# The wizard renders inside .hero{color:#fff}; anything in it that does not
# set its own colour inherits white and disappears.
if "color:var(--ink);box-shadow" not in design:
    fails.append("the order panel lost its explicit text colour - elements that "
                 "do not set their own will inherit the hero's white")
if "legend{" in design and "legend{font-size:12.8px;font-weight:700;margin-bottom:5px;color:var(--ink)}" not in design:
    fails.append("<legend> lost its explicit colour (renders white on white in the hero)")
# There is no TEST MODE marker on screen any more (removed by request), so the
# host check in initPay() is the ONLY thing stopping a dead card field from
# appearing in front of real customers on a real domain. Guard it hard.
if "window.BNS_PAY_MODE==='sandbox' && preview" not in design:
    fails.append("initPay() no longer gates the sandbox card form on a preview "
                 "host - on a real domain this would show a card field that "
                 "takes no payment")
if "workers\\.dev" not in design and "workers.dev" not in design:
    fails.append("the preview-host allowlist is gone from the order JS")

print("%d pages | %d JSON-LD blocks (%d invalid) | %d broken links"
      % (len(pages), blocks, bad_json, len(broken)))
if fails:
    print("\nFAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
print("all gates pass")
