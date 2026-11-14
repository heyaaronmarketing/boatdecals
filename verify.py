#!/usr/bin/env python3
"""Pre-deploy gate. Runs after every build - a silent build failure shipped a
stale public/ once, so this refuses to pass unless the output is genuinely fresh
and internally consistent."""
import html, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "public"
fails = []
# Things that are not wrong but that someone has to finish. A note never fails
# the build - it exists so a deliberately half-finished thing (a beacon with
# no token yet) says so on every run instead of being quietly forgotten.
notes = []

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
# "+" and "or more" are the two shapes that got past a first version:
# "holds color 7+ years" matched none of the patterns and shipped.
_YR_SPAN = _YR_N + r"(?:\s*(?:to|-|&ndash;|&mdash;)\s*\d+)?\+?"
_DUR = r"(?:warrant\w*|durabilit\w*|outdoor life|rated for|lasts?|adhesion|chalks)"
_MATERIAL = r"(?:film|vinyl|stock)"
# (pattern, may a person-noun excuse it)
_FILM_LIFE_PATTERNS = [
    (_YR_SPAN + r"[\s-]year\s+(?:\w+\s+){0,3}" + _MATERIAL, True),
    (_YR_SPAN + r"\s+years?\s+on\s+(?:\w+\s+){0,3}" + _MATERIAL, False),
    (_DUR + r"[^<.]{0,40}?" + _YR_SPAN + r"[\s-]*years?", False),
    (_YR_SPAN + r"[\s-]*years?[^<.]{0,40}?" + _DUR, False),
    (_MATERIAL + r"[^<.]{0,90}?(?:runs?|lasts?|holds?)[^<.]{0,40}?" + _YR_SPAN
     + r"[\s-]*years?", False),
]

broken, blocks, bad_json, titles, descs = set(), 0, 0, [], []
for f in OUT.rglob("*.html"):
    t = f.read_text()
    for h in re.findall(r'href="(/[^"#?]*)"', t):
        # a page, an API route, or a real file on disk (the share block links
        # straight at a downloadable card)
        if h.startswith("/api") or h in have: continue
        if (OUT / h.lstrip("/")).is_file(): continue
        broken.add(h)
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
# Step count asserted explicitly so a section cannot vanish unnoticed. Two of
# the eight only apply to some orders, so the markup always carries all eight
# and data-when decides which are shown. Payment is step 8 and stands alone:
# contact, address and a card form on one screen was the longest page in the
# funnel and the one with the most to get wrong.
_steps = len(re.findall(r'data-step="\d"', design))
if _steps != 8:
    fails.append("order wizard has %d steps, expected 8" % _steps)
_when = re.findall(r'data-step="(\d)" data-when="(\w*)"', design)
if dict(_when) != {"1": "", "2": "num", "3": "name", "4": "", "5": "", "6": "",
                   "7": "", "8": ""}:
    fails.append("wizard step conditions changed: %s" % _when)
# The number and name steps must be conditional, or a numbers-only order is
# asked for a boat name it does not have.
for _need in ('data-when="num"', 'data-when="name"'):
    if _need not in design:
        fails.append("wizard lost a conditional step: %s" % _need)
for need in ("data-step=\"1\"", "data-step=\"4\"", "id=payelement", "BNS_COL=",
             "id=prevsvg", "id=p_num", "name=kind"):
    if need not in design: fails.append("order wizard missing %s" % need)

# Prices are duplicated between the generator and the worker on purpose; they
# must not drift, because the worker's number is what gets charged.
import sys as _s; _s.path.insert(0, str(ROOT / "engine"))
from content import PRICE, UPGRADES
import importlib as _il0
_SHIP_TRANSIT = tuple(_il0.import_module("build").SHIP_TRANSIT)
wjs = (ROOT / "worker" / "index.js").read_text()
_pdj0 = (ROOT / "worker" / "price-data.js").read_text(encoding="utf-8")
for lbl, amt, _b, _f, _n in UPGRADES:
    # In the GENERATED price table now, not hand-kept in the worker.
    if '"%s": %d' % (lbl, amt) not in _pdj0:
        fails.append("worker price table UPGRADE_ADD missing/mismatched: "
                     "%s = %d" % (lbl, amt))
    # The client joins upgrades with " | "; a label containing the delimiter
    # would be split into fragments the worker cannot price, undercharging us.
    if "|" in lbl:
        fails.append("upgrade label contains the join delimiter: %s" % lbl)
if "upgrades:ups.join(' | ')" not in (ROOT / "engine" / "order.py").read_text():
    fails.append("client upgrade delimiter changed without updating the worker")
from content import PREFIX_STATE as _PS
import json
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

# ===================================================================== PRICE
# ONE TABLE, AND THE PROOF THAT IT IS ONE.
#
# What used to be here compared worker/index.js's own price list against
# engine/content.py's and failed on a difference. It worked. It also meant two
# copies of the price existed, which is why the bundle could be - and was -
# quoted at the registration-number base by a third copy in a third
# vocabulary.
#
# Now engine/content.py PRICE is the only table, worker/price-data.js is
# GENERATED from it, worker/price.js is the only pricing function, and the
# order form gets that same function inlined. These gates check that the
# generated file is current and that nothing has grown a second copy.
import subprocess as _sp          # noqa: E402

_pd = ROOT / "worker" / "price-data.js"
if not _pd.exists():
    fails.append("worker/price-data.js is gone - the worker has no price table")
else:
    _was = _pd.read_text(encoding="utf-8")
    try:
        _sp.run([sys.executable, str(ROOT / "mcp" / "build_price_js.py")],
                check=True, capture_output=True, cwd=str(ROOT))
        _now = _pd.read_text(encoding="utf-8")
        if _now != _was:
            _pd.write_text(_was, encoding="utf-8")
            fails.append("worker/price-data.js is STALE: regenerating it from "
                         "engine/content.py changes it. The site would "
                         "advertise one price and the card would charge "
                         "another. Run: python3 mcp/build_price_js.py")
    except Exception as _e:
        fails.append("could not regenerate worker/price-data.js: %s" % _e)

_pjs = (ROOT / "worker" / "price.js").read_text(encoding="utf-8")

# No price literal in the pricing function. Every figure must come through P.
_pjs_code = "\n".join(l for l in _pjs.splitlines()
                      if not l.strip().startswith(("//", "*", "/*")))
if re.search(r"\$\d\d", _pjs_code):
    fails.append("worker/price.js has a price literal in its code - every "
                 "figure must come from P, which is generated from "
                 "engine/content.py")

# The worker must not have grown its own table back.
for _dead in ("const BASE = {", "const HEIGHT_ADD = {", "const OUTLINE_ADD =",
              "const UPGRADE_ADD = {", "const KIND_ALIAS = {"):
    if _dead in wjs:
        fails.append("worker/index.js has %r again - the price table lives in "
                     "engine/content.py and reaches the worker through "
                     "worker/price-data.js" % _dead)
if 'from "./price.js"' not in wjs:
    fails.append("worker/index.js is not importing the pricing function")

# The order form must not do its own arithmetic. It used to read data-base and
# data-add off the DOM, which is a price list living in HTML attributes.
_ojs0 = (ROOT / "engine" / "order.py").read_text(encoding="utf-8")
if "dataset.base" in _ojs0:
    fails.append("the order form is reading a price off a DOM attribute "
                 "again - call window.NMB_PRICE.priceOf()")
if "window.NMB_PRICE.priceOf(" not in _ojs0:
    fails.append("the order form is no longer pricing through the shared "
                 "function - its total can drift from the card charge")

# The browser's copy IS the worker's file, not a copy of it.
from shared_js import price_js as _pjs_browser        # noqa: E402
_browser = _pjs_browser()
for _fn in ("function priceBreakdown(", "function nameBand(",
            "function widthIn("):
    if _fn not in _browser:
        fails.append("the inlined browser pricing module is missing %s - the "
                     "form would price differently from the card" % _fn)
for _lbl, _amt in (("numbers", PRICE["numbers"]),
                   ("name", PRICE["name_from"]),
                   ("bundle", PRICE["bundle_from"])):
    if '"%s": %d' % (_lbl, _amt) not in _browser:
        fails.append("the inlined browser price table does not carry the "
                     "published %s price (%d)" % (_lbl, _amt))

# The arithmetic the pages publish. The entry bundle is quoted as a flat
# figure in four places; if it stops being the sum of its parts the page is
# lying about the discount.
if PRICE["bundle_from"] != (PRICE["numbers"] + PRICE["name_from"]
                            - PRICE["bundle_off"]):
    fails.append("PRICE['bundle_from'] is not numbers + name_from - "
                 "bundle_off, so the advertised bundle saving is wrong")
if PRICE["name_bands"][0]["price"] != PRICE["name_from"]:
    fails.append("PRICE['name_from'] is not the smallest band's price, so "
                 '"from $%d" on the letters page is not a price anyone can '
                 "actually pay" % PRICE["name_from"])
_bmax = [b["max_in"] for b in PRICE["name_bands"]]
if _bmax[-1] is not None:
    fails.append("the last name band must be open-ended or a wide name has "
                 "no price at all")
if _bmax[:-1] != sorted(x for x in _bmax if x is not None):
    fails.append("the name bands are not in ascending width order - a name "
                 "would fall in the wrong one")

# The form's badge states the saving. It is read off the price table, so this
# catches the badge being hand-written back.
# ---- the claims gate's blind spot -----------------------------------------
# It scans public/**/*.html. catalog.json and llms.txt are read by assistants
# and quoted back to customers as fact, and neither was checked. Found the
# long way round: inlining the price table nearly published a film-life year
# figure, and the only reason the gate caught it was that the table landed
# inside an HTML page.
for _nonhtml in ("catalog.json", "llms.txt"):
    _f = OUT / _nonhtml
    if _f.exists():
        _t = _f.read_text(encoding="utf-8")
        for _pat, _person_ok in _FILM_LIFE_PATTERNS:
            for _m in re.finditer(r"(?i)\b" + _pat, _t):
                fails.append("film-life claim %r in %s - we do not publish a "
                             "year figure, and an assistant quotes this file "
                             "as fact" % (_m.group(0), _nonhtml))

# Generated from PRICE, so the figure is not in the source - check what the
# customer is actually shown.
if "Save $%d" % PRICE["bundle_off"] not in design:
    fails.append("the order form's bundle badge does not state the real "
                 "saving of $%d" % PRICE["bundle_off"])
for _lbl, _amt in (("Boat Numbers", "$%d" % PRICE["numbers"]),
                   ("Boat Name", "$%d+" % PRICE["name_from"]),
                   ("Both", "$%d+" % PRICE["bundle_from"])):
    if "<b>%s</b><i>%s</i>" % (_lbl, _amt) not in design:
        fails.append("the order form's %s card does not show %s"
                     % (_lbl, _amt))
# The browser's copy of the price table must be the whole table. It was once
# shipped with the upgrade prices emptied out, which left the running total
# and the card charge disagreeing for any order carrying an upgrade.
if '"UPGRADE_ADD": {}' in design:
    fails.append("the order form's price table has the upgrade prices "
                 "emptied out - the running total would leave them out while "
                 "the card charged for them")

# NO SUPERSEDED PRICE LITERAL, ANYWHERE.
#
# This is the gate that makes the next price change safe, and it is the reason
# the November change took an afternoon instead of a week: ninety-odd figures
# were spread through page copy, meta descriptions, OG card text, FAQ answers
# and share scripts, and nothing would have told anyone if one had been
# missed. A customer reading last month's figure on a state page and being
# charged this month's at the till is the single worst bug this shop can ship.
#
# Prose does not have to interpolate from PRICE - plenty of it cannot, sitting
# mid-way through fifty concatenated literals with their own percent signs -
# but no file may carry a figure we no longer charge.
_RETIRED = (19, 29, 44, 23, 27, 22, 79)
_SCAN = [("engine", "*.py"), ("media", "*.py"), ("media", "*.json"),
         ("worker", "*.js"), ("public", "*.html"), ("public", "*.txt"),
         ("public", "*.json")]
_live = {PRICE["numbers"], PRICE["name_from"], PRICE["bundle_from"],
         PRICE["outline"], PRICE["rush"], PRICE["kit"],
         PRICE["market_low"], PRICE["market_high"],
         PRICE["bundle_off"], PRICE["name_typical_to"]}
_live |= {b["price"] for b in PRICE["name_bands"]}
_live |= {PRICE["numbers"] + a for a in PRICE["height_add"].values()}
_live |= set(PRICE["height_add"].values())
_live |= {u[1] for u in UPGRADES}
_stale = [v for v in _RETIRED if v not in _live]
_hits = []
for _dirname, _glob in _SCAN:
    for _f in sorted((ROOT / _dirname).rglob(_glob)):
        if not _f.is_file():
            continue
        _t = _f.read_text(encoding="utf-8", errors="replace")
        for _v in _stale:
            for _mm in re.finditer(r"\$%d\b" % _v, _t):
                _hits.append((_f.relative_to(ROOT), _v,
                              _t[max(0, _mm.start() - 50):_mm.end() + 25]
                              .replace("\n", " ")))
if _hits:
    for _h in _hits[:8]:
        fails.append("superseded price $%d in %s: ...%s..."
                     % (_h[1], _h[0], _h[2].strip()))
    if len(_hits) > 8:
        fails.append("...and %d more superseded price literals" % (len(_hits) - 8))

# An unpaid order taken at the old price must be charged the old price. The
# pay link reprices from the row, which was harmless until the price moved.
if "Number(o.total) > 0" not in wjs:
    fails.append("/api/paylink is repricing an existing order at today's "
                 "price - an order taken before a price change would be sent "
                 "a pay link for a figure the customer never agreed to")

# The radio VALUE is a contract between the form, the worker and every row in
# D1; the LABEL beside it is free text. Catch a rename of the value that does
# not reach worker/index.js.
sys.path.insert(0, str(ROOT / "engine"))
from order import KINDS as _KINDS
# The card no longer carries a base price, so what has to hold is that the
# radio's value is a vocabulary the pricing function speaks. If it is not,
# every order of that kind is priced as the cheapest product.
for _val, _p, _f, _k, _label in _KINDS:
    if '"%s": "' % _val not in _pjs:
        fails.append("order kind %r is not a key in worker/price.js "
                     "KIND_ALIAS - it would be priced as the cheapest thing "
                     "we sell. The radio value is a contract; rename the "
                     "label instead" % _val)

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
from content import SITE as _SITE
_SUFFIXES = tuple(x for x in (" | " + _SITE["brand"],) if x)
for _f in OUT.rglob("index.html"):
    _m = re.search(r"<title>(.*?)</title>", _f.read_text())
    if not _m:
        continue
    _t = _m.group(1)
    if len(_t) in (58, 59, 60) and not _t.endswith(_SUFFIXES):
        fails.append("title truncated mid-word in %s: %r" % (_f, _t))
    if _t.count(_SITE["brand"]) > 1:
        fails.append("brand appears twice in the title of %s: %r"
                     % (_f.relative_to(OUT), _t))

# No personal information, anywhere. The shop runs out of a private home, so
# the street address, the landline and a rooftop coordinate are personal
# details rather than business ones - Aaron's call, 2026-10-30. Town and state
# stay. This gate exists because that kind of thing creeps back in one
# well-meaning edit at a time.
_PII = [
    (r"\b\(?319\)?[\s.-]?239[\s.-]?3793\b", "the old phone number"),
    (r"\btel:\+?1?319", "a tel: link"),
    (r"475\s+River\s+Forest", "the street address"),
    (r'"streetAddress"', "a streetAddress in schema"),
    (r"GeoCoordinates", "geo coordinates in schema"),
    (r'"LocalBusiness"', "a LocalBusiness entity (no public address to back it)"),
    (r"maps\.google|google\.com/maps", "a Google Maps link"),
    (r"\bfire chief\b", "the owner's other job"),
    (r"Ryan\s+Phillips", "the owner by name"),
]
for _f in OUT.rglob("*"):
    if _f.suffix not in (".html", ".xml", ".txt") or not _f.is_file():
        continue
    _t = _f.read_text(errors="ignore")
    for _pat, _what in _PII:
        if re.search(_pat, _t, re.I):
            fails.append("PII: %s in %s" % (_what, _f.relative_to(OUT)))

# The domain is numbermyboat.com. boatnumbershop.com was never registered and
# must not survive in a canonical, a schema @id, a sitemap entry or an email
# address - a stale canonical pointing at a domain nobody owns is the kind of
# thing that quietly de-indexes a site.
for _f in OUT.rglob("*"):
    if _f.suffix in (".html", ".xml", ".txt") and _f.is_file():
        if "boatnumbershop" in _f.read_text(errors="ignore"):
            fails.append("stale domain boatnumbershop.com in %s"
                         % _f.relative_to(OUT))

# The brand lives in SITE["brand"] and nowhere else. Four pages and llms.txt
# had it hardcoded, so renaming the shop left the site half-renamed until a
# manual sweep caught it. This fails the build if the old name survives.
for _f in OUT.rglob("*"):
    if _f.suffix in (".html", ".xml", ".txt") and _f.is_file():
        if "Boat Number Shop" in _f.read_text(errors="ignore"):
            fails.append("stale brand 'Boat Number Shop' in %s - read it from "
                         "SITE[\"brand\"]" % _f.relative_to(OUT))

# Two `function x()` declarations in the same scope do not error - the later
# one silently replaces the first. A second `function finish()` once replaced
# the order-submission `finish(extra)`, so payload() called the finish
# selector, which called payload(), and checkout died with a stack overflow
# that nothing on the page surfaced.
_order_js = (ROOT / "engine" / "order.py").read_text()
_decls = re.findall(r"\n\s*function\s+(\w+)\s*\(", _order_js)
for _name in sorted(set(_decls)):
    if _decls.count(_name) > 1:
        fails.append("order.py declares function %s() %d times - the later one "
                     "silently replaces the earlier" % (_name, _decls.count(_name)))

# The outline upcharge reaches the form, the card and the proof email from one
# place now, so there is nothing left to compare - but the proof email states
# the figure in words, and the pricing function has to keep reading BOTH the
# raw payload's `outline` and the sanitised order's `finish`.
from content import PRICE as _P
_pj = (ROOT / "worker" / "price.js").read_text(encoding="utf-8")
if 'd.finish === "outline" || d.outline' not in _pj:
    fails.append("worker/price.js must read BOTH d.finish and d.outline - it\n"
                 "                  is called with the raw payload AND with "
                 "the sanitised order")
_ojs = (ROOT / "engine" / "order.py").read_text()
if "window.NMB_PRICE.OUTLINE_ADD" not in _ojs:
    fails.append("the order form has its own outline price again instead of "
                 "reading it from the shared table")

# Share cards. og_image() derives the URL from the page path before the PNG
# has been rendered - the build wipes public/ first, so the cards are written
# last. That ordering is fine right up until a page path changes and the card
# silently 404s, which Facebook renders as a blank grey box. Check every
# reference resolves, and that nothing is a placeholder-sized file.
# A sitemap is a request to index. Listing a page that carries noindex is a
# contradiction Google reports as "Submitted URL marked noindex", and it was
# doing exactly that for /_cards/ and /brand/.
_sm = (OUT / "sitemap.xml").read_text()
for _f in OUT.rglob("index.html"):
    if 'content="noindex' not in _f.read_text():
        continue
    _rel = str(_f.relative_to(OUT).parent).replace("\\", "/")
    _url = "/" if _rel == "." else "/%s/" % _rel
    if "%s</loc>" % _url in _sm:
        fails.append("noindex page %s is listed in sitemap.xml" % _url)

# ---- brand assets -------------------------------------------------------
# The logo pack is what goes on Google Business, Facebook and every citation
# site. Two ways it rots: the files stop shipping, or the header logo changes
# and the listings quietly keep the old one for years. Both are checked.
_brand = OUT / "brand"
if not _brand.exists():
    fails.append("public/brand/ is missing - the logo pack did not ship. "
                 "Run: python3 media/brand.py")
else:
    for _need in ("profile/profile-720.png",   # Google Business
                  "profile/profile-500.png",   # Facebook
                  "profile/profile-250.png",   # the common directory minimum
                  "icon/icon-512.png", "icon/icon-32.png",
                  "lockup/lockup-horizontal-1200.png",
                  "lockup/lockup-horizontal-white-1200.png",
                  "cover/facebook-page-cover-1640x624.png",
                  "cover/google-business-cover-1024x576.png",
                  "svg/lockup-horizontal.svg",
                  "numbermyboat-logo-pack.zip"):
        if not (_brand / _need).exists():
            fails.append("brand asset missing: %s" % _need)

    # A PNG that is all one colour rendered as an empty box. rsvg-convert
    # exits 0 either way, so a silently blank logo would otherwise ship.
    import struct as _struct
    for _img in sorted(_brand.rglob("*.png")):
        _b = _img.read_bytes()
        if len(_b) < 24 or _b[:8] != b"\x89PNG\r\n\x1a\n":
            fails.append("brand file is not a PNG: %s" % _img.name)
            continue
        _w, _h = _struct.unpack(">II", _b[16:24])
        if _w < 16 or _h < 16:
            fails.append("brand PNG %s is %dx%d" % (_img.name, _w, _h))
        # An 8KB 1024px logo is a blank canvas; a real one is ~30KB+.
        if _w >= 512 and _img.stat().st_size < 4096:
            fails.append("brand PNG %s is %dpx but only %dB - probably blank"
                         % (_img.name, _w, _img.stat().st_size))

    # Photographs: every master in media/photos must reach the pack. The
    # listing slots that want a real photo are exactly the ones that look
    # worst empty, and a master that silently stops being published is not
    # something anyone would notice.
    _pm = ROOT / "media" / "photos"
    if _pm.exists():
        if not (_pm / "README.md").exists():
            fails.append("media/photos/README.md is gone - it carries the "
                         "rule that nothing in there may be AI-generated")
        for _src in sorted(_pm.glob("*.png")):
            for _sz in (1024, 720, 500, 400, 320, 300, 250):
                _want = _brand / "photo" / ("%s-%d.jpg" % (_src.stem, _sz))
                if not _want.exists():
                    fails.append("photo %s is in media/photos but %s was not "
                                 "generated - run media/brand.py"
                                 % (_src.name, _want.name))
                    break

    # The generated assets must come from the header's own mark. Comparing the
    # mark's path data against the SVG master catches a header redesign that
    # never made it into the logo pack.
    _bld = (ROOT / "engine" / "build.py").read_text()
    _mk = re.search(r'LOGO_MARK = \((.*?)\)\n\nWORDMARK', _bld, re.S)
    if not _mk:
        fails.append("could not read LOGO_MARK out of build.py")
    else:
        _paths = re.findall(r'd="([^"]+)"', _mk.group(1))
        _svg = (_brand / "svg" / "icon.svg").read_text()
        for _d in _paths:
            if _d not in _svg:
                fails.append("the header logo has changed but brand/ has not "
                             "been regenerated - listings would keep the old "
                             "logo. Run: python3 media/brand.py")
                break

# Every asset the gallery links to must exist, or the page offers downloads
# that 404 in the middle of filling in a listing.
_bp = OUT / "brand" / "index.html"
if _bp.exists():
    for _href in set(re.findall(r'href="(/brand/[^"]+)"', _bp.read_text())):
        if not (OUT / _href.lstrip("/")).exists():
            fails.append("brand page links to a missing file: %s" % _href)
    if 'content="noindex' not in _bp.read_text():
        fails.append("the brand page is indexable - it is an internal library")

_og_pages = 0
for _f in OUT.rglob("index.html"):
    _m = re.search(r'og:image" content="[^"]*?(/assets/og/[^"]+)"', _f.read_text())
    if not _m:
        fails.append("no og:image on %s" % _f.relative_to(OUT)); continue
    _og_pages += 1
    _card = OUT / _m.group(1).lstrip("/")
    if not _card.exists():
        fails.append("og:image 404 on %s -> %s"
                     % (_f.relative_to(OUT), _m.group(1)))
    elif _card.stat().st_size < 6000:
        fails.append("og card suspiciously small (%d bytes): %s"
                     % (_card.stat().st_size, _m.group(1)))
# Every card carries the lockup. Checking the PNG pixels is not practical,
# so this asserts the renderer still composes one - the failure mode is a
# refactor that drops the mark and ships 83 unbranded cards nobody notices,
# because they all still look fine.
_og_py = (ROOT / "media" / "og.py").read_text()
if "lock = (mark(" not in _og_py or "NUMBERMYBOAT.COM" not in _og_py:
    fails.append("media/og.py no longer composes the mark + URL lockup")

if _og_pages < 50:
    fails.append("only %d pages carry an og:image" % _og_pages)

# No two nav rows may point at the same page. "Help" and "Guides" both went
# to /guides/ for a fortnight and nothing complained.
_nav = re.search(r"<nav id=nav>(.*?)</nav>", (OUT / "index.html").read_text(), re.S)
if _nav:
    _hrefs = re.findall(r'href="([^"]+)"', _nav.group(1))
    _dupe = {h for h in _hrefs if _hrefs.count(h) > 1}
    if _dupe:
        fails.append("duplicate nav links: %s" % sorted(_dupe))

# Social tags, to the spec in the share plan. A card that renders wrong on
# Facebook fails silently - there is no error anywhere, it just looks cheap in
# a feed - so every one of these is checked rather than trusted.
_REQ_OG = ["og:type", "og:site_name", "og:locale", "og:url", "og:title",
           "og:description", "og:image", "og:image:secure_url",
           "og:image:type", "og:image:width", "og:image:height",
           "og:image:alt"]
_REQ_TW = ["twitter:card", "twitter:title", "twitter:description",
           "twitter:image", "twitter:image:alt"]
for _f in OUT.rglob("index.html"):
    _h = _f.read_text()
    _rel = _f.relative_to(OUT)
    for _t in _REQ_OG:
        if 'property="%s"' % _t not in _h:
            fails.append("missing %s on %s" % (_t, _rel))
    for _t in _REQ_TW:
        if 'name="%s"' % _t not in _h:
            fails.append("missing %s on %s" % (_t, _rel))
    # exactly one image, absolute, and matching the canonical host
    _imgs = re.findall(r'property="og:image" content="([^"]+)"', _h)
    if len(_imgs) != 1:
        fails.append("%d og:image tags on %s (Facebook takes the first)"
                     % (len(_imgs), _rel))
    for _u in _imgs:
        if not _u.startswith("https://"):
            fails.append("relative og:image on %s: %s" % (_rel, _u))
        if "workers.dev" in _u:
            fails.append("staging URL in og:image on %s" % _rel)
    _ou = re.search(r'property="og:url" content="([^"]+)"', _h)
    _cn = re.search(r'rel="canonical" href="([^"]+)"', _h)
    if _ou and _cn and _ou.group(1) != _cn.group(1):
        fails.append("og:url != canonical on %s" % _rel)
    # Facebook shows ~60 chars of title on a phone and hides most descriptions
    _ot = re.search(r'property="og:title" content="([^"]+)"', _h)
    if _ot and len(html.unescape(_ot.group(1))) > 60:
        fails.append("og:title over 60 chars on %s (%d)"
                     % (_rel, len(html.unescape(_ot.group(1)))))
    _od = re.search(r'property="og:description" content="([^"]+)"', _h)
    if _od and len(html.unescape(_od.group(1))) > 110:
        fails.append("og:description over 110 chars on %s (%d)"
                     % (_rel, len(html.unescape(_od.group(1)))))

# Every card must be exactly 1200x630 - Facebook crops anything else, and a
# PNG header is cheap to read.
def _dims(path):
    """Width/height from a PNG or JPEG header, without a decoder."""
    b = path.read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] != 0xFF:
                i += 1; continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                return (int.from_bytes(b[i + 7:i + 9], "big"),
                        int.from_bytes(b[i + 5:i + 7], "big"))
            i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    return None


for _d in ("og", "share"):
    for _c in sorted((OUT / "assets" / _d).glob("*")):
        if _c.suffix not in (".png", ".jpg"):
            continue
        _wh = _dims(_c)
        if _wh is None:
            fails.append("unreadable share card: %s" % _c.name); continue
        if _d == "og" and _wh != (1200, 630):
            fails.append("og card %s is %dx%d, not 1200x630"
                         % (_c.name, _wh[0], _wh[1]))
        if _c.stat().st_size > 600_000:
            fails.append("share card over 600KB (%dKB): %s"
                         % (_c.stat().st_size // 1024, _c.name))

# og:image:type must match the file it points at
for _f in OUT.rglob("index.html"):
    _h = _f.read_text()
    _i = re.search(r'property="og:image" content="([^"]+)"', _h)
    _t = re.search(r'property="og:image:type" content="([^"]+)"', _h)
    if _i and _t:
        _want = "image/jpeg" if _i.group(1).endswith(".jpg") else "image/png"
        if _t.group(1) != _want:
            fails.append("og:image:type %s but image is %s on %s"
                         % (_t.group(1), _i.group(1)[-4:], _f.relative_to(OUT)))

sys.path.insert(0, str(ROOT / "engine"))
from sharebox import posts_for as _posts
from content import STATES as _ST2
_DISCLOSE = re.compile(r"brother|family|my shop|we cut|disclosure", re.I)
for _ctx, _args in (("site-wide", {}), ("state", {"state": _ST2[0]})):
    for _label, _text in _posts("/", **_args):
        if not _DISCLOSE.search(_text):
            fails.append("share post %r (%s) has no disclosure - an "
                         "undisclosed promo post gets the account banned"
                         % (_label, _ctx))
        if len(_text) > 300:
            fails.append("share post %r is %d chars, over the 300 limit"
                         % (_label, len(_text)))
        if "link in comment" not in _text.lower():
            fails.append("share post %r does not say link in comments" % _label)

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
# The phone deck is built by build.py and only exists on pages with a hero, so
# its ids are absent from /design/. Scan a hero page too rather than exempting
# them: a typo in a deck id still has to fail, it just has to be looked for
# where the deck actually is.
_homepage = (OUT / "index.html").read_text()
markup_ids |= set(_re.findall(r'id="([A-Za-z0-9_]+)"', _homepage))
markup_ids |= set(_re.findall(r"id=([A-Za-z0-9_]+)", _homepage))
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

# ---- the font picker ----------------------------------------------------
# FONTS went from 4-tuples to 5-tuples (label, css, spec, block_legal,
# category) and two call sites unpacked four names. Python raised, build.py
# died, and the stale page in public/ still looked fine - so nothing noticed
# until a page was diffed by hand. Unpack every entry here instead.
import importlib, sys as _sys
_sys.path.insert(0, "engine")
_C = importlib.import_module("content")
_shape = [f for f in _C.FONTS if len(f) != 5]
if _shape:
    fails.append("%d FONTS entries are not 5-tuples (first: %r) - a build-time "
                 "unpack will raise and ship a stale page"
                 % (len(_shape), _shape[0][0]))
else:
    # Nothing is preselected on the font step: a default there is a choice
    # nobody made, and it is the one field the whole order is cut from.
    if ' checked' in design.split("class=fontgrid")[-1].split("</div>")[0]:
        fails.append("a font chip ships preselected - the customer must pick "
                     "one, not inherit whichever face happens to be first")
    if "'Pick a font to carry on.'" not in design:
        fails.append("the font step no longer blocks on an empty choice, so "
                     "an order could be cut in a font nobody picked")
    # Ryan cuts these ten. The grid is five across, so ten is two clean rows
    # and the five block-legal ones are exactly the first row.
    if len(_C.FONTS) % _C.FONT_COLS:
        fails.append("%d faces does not divide into rows of %d, so the grid "
                     "ends on a ragged row"
                     % (len(_C.FONTS), _C.FONT_COLS))
    _legal = [f for f in _C.FONTS if f[3]]
    if not _legal:
        fails.append("no face is marked as plainly meeting 33 CFR 173.27, so "
                     "every registration number would carry the warning")
    # Every face is orderable on every product now, so nothing is hidden. What
    # has to survive is the WARNING: the site advertises "Meets 33 CFR
    # 173.27", and that claim cannot quietly stop being true for an order.
    if "may not satisfy 33 CFR" not in design:
        fails.append("the order form no longer warns when a decorative face "
                     "is picked for a registration number, while the site "
                     "still advertises meeting the rule")
    if "classList.remove('off')" not in design:
        fails.append("the font grid is hiding faces again - the shop decided "
                     "every face is orderable on every product")
    _pf = (ROOT / "worker" / "proof.js").read_text()
    # Matched on the CALL SITE, not the definition. Checking for
    # "riskNote(o)" passes against "function riskNote(o)" while the call has
    # been deleted - the fourth time a gate in this file has been written as a
    # substring that its own declaration satisfies.
    if "letteringBlock(o) + riskNote(o)" not in _pf or "PLAIN_BLOCK" not in _pf:
        fails.append("the proof no longer carries the font warning, so the "
                     "customer approves a non-compliant cut without being "
                     "told on the document they are approving")
    if "o.font_risk" not in (ROOT / "worker" / "index.js").read_text():
        fails.append("the shop email no longer flags a non-block face on a "
                     "registration number")
    # Every one of these is an OPEN stand-in for a licensed Microsoft face.
    # Serving the originals would need a webfont licence we do not have, and
    # a visitor without them installed would silently see something else -
    # so the picker, the proof and the plotter would disagree.
    for _f in _C.FONTS:
        if not _f[4]:
            fails.append("font %r has no note on how close its open stand-in "
                         "is - that judgement is the whole reason the "
                         "substitution is defensible" % _f[0])
    _lbls = [f[0] for f in _C.FONTS]
    if len(set(_lbls)) != len(_lbls):
        fails.append("two fonts share a label - `font` is submitted by label, "
                     "so the order would be ambiguous")
    if not _legal:
        fails.append("no block-legal face left - a registration number could "
                     "not be ordered at all")

# worker/index.js keeps its own copy of the block-legal faces, because it
# cannot import Python. If a legal face is missing there the worker rewrites
# the order to BLOCK_FONTS[0] and tells Ryan the customer asked for something
# illegal - so the wrong font gets cut and the email blames the customer.
import re as _re, json as _json
_m = _re.search(r"const BLOCK_FONTS = \[(.*?)\];",
                pathlib.Path("worker/index.js").read_text(), _re.S)
if not _m:
    fails.append("worker/index.js has no BLOCK_FONTS list")
elif not _shape:
    _wk = set(_json.loads("[" + _re.sub(r",(\s*\])", r"\1", _m.group(1)) + "]"))
    _py = {f[0] for f in _C.FONTS if f[3]}
    if _wk != _py:
        fails.append("BLOCK_FONTS in worker/index.js has drifted from "
                     "content.py: missing %s, extra %s"
                     % (sorted(_py - _wk) or "none", sorted(_wk - _py) or "none"))

# ---- the on-the-boat preview -------------------------------------------
# The plate table is what makes "shown to scale" true. Each plate declares how
# many inches of real hull its WIDTH spans, and the browser derives character
# height from that - so a plate whose image is missing, or whose calibration
# drifted from the crop it was measured against, puts the customer's lettering
# at a scale the photograph does not support. That is a claim, not a layout
# glitch, which is why it fails the build.
_plates = _json.loads((ROOT / "engine" / "plates.json").read_text())
if len(_plates) < 4:
    fails.append("engine/plates.json has %d plates - the preview needs a light "
                 "and a dark one for both the side and transom views, or some "
                 "colour/product combination silently has no plate at all"
                 % len(_plates))
_seen = set()
for _pl in _plates:
    _seen.add((_pl["view"], bool(_pl["dark"])))
    for _w in (800, 1400):
        _f = ROOT / "public" / "assets" / "img" / ("%s-%d.webp" % (_pl["id"], _w))
        if not _f.exists():
            fails.append("plate %s has no %dpx asset - the preview would show "
                         "an empty frame" % (_pl["id"], _w))
    if not isinstance(_pl.get("inches"), (int, float)) or _pl["inches"] <= 0:
        fails.append("plate %s has no usable `inches` calibration, so "
                     "character height cannot be derived from it" % _pl["id"])
    if not _pl.get("nominal"):
        fails.append("plate %s has no `nominal` - the preview prints it as the "
                     "stated scale, and scaling lettering onto a hull without "
                     "saying what hull is an unstated claim about boat size"
                     % _pl["id"])
    if _pl.get("align") not in ("left", "center"):
        fails.append("plate %s has align=%r" % (_pl["id"], _pl.get("align")))
for _want in (("side", False), ("side", True),
              ("transom", False), ("transom", True)):
    if _want not in _seen:
        fails.append("no %s plate for a %s hull - %s vinyl on that view would "
                     "fall back to a hull it cannot be seen against, which is "
                     "the opposite of what 33 CFR 173.27 asks for"
                     % (_want[0], "dark" if _want[1] else "light",
                        "light" if _want[1] else "dark"))
# The stated scale has to actually reach the screen.
if "shown to scale on a " not in design:
    fails.append("the preview no longer prints the hull it is scaled against")
if "About <b>" not in design:
    fails.append("the finished-size note is gone from the preview")
# Derived, never asserted: the width comes from whatever glyphs are on screen,
# so it is an estimate and has to read as one.
if "About <b>'+long+'&quot; long" not in design.replace("' + '", "'+'"):
    fails.append("the finished size is no longer hedged with \"About\" - it is "
                 "derived from font metrics and is not an exact promise")
# Both views must exist: the boat view at honest scale puts a 3" character at
# about 16px, which is right for context and wrong for proofreading a
# registration number - and a typo there makes the decal worthless.
for _id in ("boatview", "viewboat", "viewflat", "platespan", "plateimg"):
    if 'id=' + _id not in design:
        fails.append("the preview lost #%s - the boat/flat view toggle is "
                     "broken" % _id)

# The lettering on the hull plate must not be filtered or blended into its
# own composited layer on a phone. Both filter() and mix-blend-mode promote it,
# and a phone rasterises that layer coarser than its device pixels - at a ~12px
# cap height that is the difference between crisp vinyl and mush. This shipped
# blurry once.
if "span.style.filter" in design:
    fails.append("the hull preview is filtering the lettering again - filter() "
                 "promotes it to a composited layer and a phone renders that "
                 "layer soft, which is exactly how the text went blurry")
if "@media(max-width:760px){#platespan.ink{mix-blend-mode:normal}" not in design:
    fails.append("the hull preview no longer drops mix-blend-mode on phones - "
                 "the blend costs the lettering its sharpness at phone sizes, "
                 "and a flat overlay that is sharp beats a blended one that "
                 "is not")

# The phone order sheet. Four CTAs for one action was the problem; the fix is
# that they all open the same wizard full screen rather than each being its own
# entry point. If any piece of that goes missing the page quietly returns to
# offering a cramped inline form plus three links to a different page.
_heroes = [q for q in pages if "class=heroF" in q.read_text()]
if not _heroes:
    fails.append("no page carries a hero wizard any more")
for _h in _heroes:
    _d = _h.read_text()
    for _need, _why in (
            ("<div class=sheetbar>",
             "the sheet has no title bar, so there is no way to close it"),
            ("class=sheetx ", "the sheet has no close control")):
        if _need not in _d:
            fails.append("%s: %s" % (_h.relative_to(OUT), _why))
if "classList.add('sheeton')" not in design:
    fails.append("the order sheet never opens - the phone CTAs would fall back "
                 "to navigating to /design/ and the cramped inline form")
if "body.sheeton{overflow:hidden}" not in design:
    fails.append("the page behind the order sheet still scrolls")
if "mq.addEventListener" not in design and "addListener(onBreak)" not in design:
    fails.append("nothing watches the sheet's breakpoint - rotating to "
                 "landscape past it would leave the body scroll-locked with "
                 "every sheet style gone")
if "body.sheeton .sticky" not in design:
    fails.append("the sticky CTA still floats over the open order sheet, "
                 "offering the thing that is already open")

# ---- Stripe ------------------------------------------------------------
# The server reprices every order from its fields and ignores whatever amount
# the browser sends. That is correct - and it is why the browser has to send
# the ORDER. Posting only {amount} left the server pricing an empty object,
# which falls through to the cheapest product: a "Both" order at 6 inches with
# a large name and an outline is well over a hundred dollars and would have
# been charged the price of a three-inch pair. Undercharging is silent, so it
# is gated rather than remembered.
if "body:JSON.stringify({order:payload()})" not in design.replace(" ", ""):
    fails.append("the checkout call no longer sends the order, so the server "
                 "prices an empty object and every order above the base rate "
                 "is undercharged")
if "repriceIntent()" not in design:
    fails.append("nothing reprices the payment intent. A customer can reach "
                 "checkout, go back, add an outline and return - the card "
                 "would be charged the old amount")
_wj = (ROOT / "worker" / "index.js").read_text()
if "Idempotency-Key" not in _wj:
    fails.append("the payment intent call lost its idempotency key - a "
                 "double-tap on a flaky connection makes two holds on the "
                 "customer's card")
if "metadata[ref]" not in _wj:
    fails.append("payments no longer carry the order reference into Stripe, "
                 "so a refund or dispute starts from a row saying only an "
                 "amount")
# priceOf is the only authority. A posted total must never reach it.
if "priceOf(d.quoted" in _wj or "amount: d.amount" in _wj:
    fails.append("a browser-supplied amount is reaching the Stripe call")
# The card field has to say when the money moves. The shop charges at
# checkout, so the page may not still imply payment waits for the proof.
if "You are charged now" not in design:
    fails.append("the card field no longer says when the customer is charged")
if "nothing is charged for artwork you have not seen" in design:
    fails.append("the checkout still promises not to charge before the proof, "
                 "which stopped being true when payment moved to checkout")

# A configured publishable key must actually reach the page. If it goes
# missing the card field cannot mount and checkout degrades to "payment
# unavailable" - no error, no log line, just orders quietly not being paid.
if _C.STRIPE_PK:
    if _C.STRIPE_PK not in design:
        fails.append("STRIPE_PK is configured but is not in the built order "
                     "page, so the card field cannot mount and checkout "
                     "silently falls back to taking no payment")
    if "js.stripe.com/v3" not in design:
        fails.append("Stripe.js is not loaded on the order page")
    if not _C.STRIPE_PK.startswith("pk_"):
        fails.append("STRIPE_PK does not look like a publishable key. A "
                     "SECRET key here would be published in the page source")
    if _C.STRIPE_PK.startswith("sk_") or "sk_live" in design or "sk_test" in design:
        fails.append("a Stripe SECRET key is in the built output")

# An order with no address cannot be posted. The form collected a name and an
# email and nothing else until 2026-11-11, which left a real approved order
# unshippable - so the address is required at checkout and gated here.
for _f in ("f_a1", "f_city", "f_state", "f_zip"):
    if "id=" + _f not in design:
        fails.append("the shipping field %s is gone from checkout - an order "
                     "without an address cannot be posted" % _f)
if "to post it to you" not in design:
    fails.append("checkout no longer blocks on a missing address")

# The shipping state must be a POSTAL code. STATES[*]["ab"] holds the vessel
# registration prefix - California is CF there, Michigan MC, Washington WN,
# Wisconsin WS - and the dropdown was built from that list by mistake, so
# every parcel carried a state the post office does not recognise.
_bad_ab = [a for a in ("CF", "MC", "WN", "WS")
           if ('<option value="%s">' % a) in design]
if _bad_ab:
    fails.append("the shipping state dropdown is offering vessel registration "
                 "prefixes %s instead of postal codes - those belong on a hull, "
                 "not a parcel" % _bad_ab)
for _ab in ("CA", "MI", "WA", "WI", "AZ", "WY"):
    if ('<option value="%s">' % _ab) not in design:
        fails.append("the shipping state dropdown has no %s - we promise free "
                     "shipping to all 50 states" % _ab)
_nstates = design.count('<option value="') - design.count('<option value="">')
if _nstates < 51:
    fails.append("only %d shipping states offered, expected 51 incl. DC"
                 % _nstates)

# The card form no longer asks for a country or a ZIP, because the step
# before it already took a validated address. Stripe then REQUIRES the
# address at confirm time: with the suppression but without the billing
# details, EVERY payment fails. The two must never drift apart.
_supp = "billingDetails:{address:'never'}" in design
_give = "payment_method_data:{billing_details:" in design
if _supp != _give:
    fails.append("the card form suppresses the billing address (%s) but "
                 "supplies it at confirm time (%s) - mismatched, so every "
                 "payment would fail" % (_supp, _give))
if _supp and "country:'US'" not in design:
    fails.append("billing address is supplied without a country, which Stripe "
                 "rejects")

# Card only. automatic_payment_methods puts every method enabled on the
# account - Klarna, Cash App, Amazon Pay, Bank - in a tab row above a decal
# that costs less than lunch for two.
_wj3 = (ROOT / "worker" / "index.js").read_text()
if '"automatic_payment_methods[allow_redirects]": "never"' not in _wj3:
    fails.append("the PaymentIntent allows redirect payment methods again, so "
                 "the checkout grows a tab row of Klarna / Cash App / Amazon "
                 "Pay above a decal")
# Stripe removed this parameter outright: sending it 400s the intent and
# degrades every checkout on the site. It cost one live deploy to learn.
if '"payment_method_types' in _wj3:   # the quoted KEY, not a mention in prose
    fails.append("payment_method_types is back - Stripe no longer supports it "
                 "and REJECTS the PaymentIntent, degrading card payment "
                 "site-wide")
_wj2 = (ROOT / "worker" / "index.js").read_text()
if "ship_line1: str(d.ship_line1" not in _wj2:
    fails.append("the worker is not storing the shipping address")
if '"shipping[address][line1]"' not in _wj2:
    fails.append("the address is no longer sent to Stripe, so a dispute "
                 "cannot show where the parcel went")
if '["Ship to"' not in _wj2:
    fails.append("the shop email no longer prints a shipping label")

# Pay-by-link orders have no address on the form at all - Stripe collects it at
# checkout and the ONLY way it reaches us is the payment_intent.succeeded
# webhook. Without these three the address lives in the Stripe dashboard and
# nowhere else, which is how the first real order came to be unshippable.
if '"shipping_address_collection[allowed_countries][0]"' not in _wj2:
    fails.append("the pay-by-link session no longer asks for an address, so a "
                 "link-paid order arrives with nowhere to post it")
_hook0 = (ROOT / "worker" / "stripehook.js").read_text()
# The CALL with its argument - "shippingOf" alone is satisfied by the
# function's own declaration, which is the mistake that let five earlier gates
# pass against code that never ran.
if "const ship = shippingOf(obj);" not in _hook0:
    fails.append("the webhook is ignoring the address Stripe collected - a "
                 "link-paid order would store no address")
if "SET ship_line1" not in _hook0:
    fails.append("the webhook reads the collected address but never writes it")
if "COALESCE(ship_line1,'')=''" not in _hook0:
    fails.append("the webhook would overwrite a validated checkout address "
                 "with whatever was later typed into Stripe")

# ---- the catalog --------------------------------------------------------
# /catalog.json is what the MCP server, the product feeds and any assistant
# read. If it drifts from the worker's own pricing, a chat assistant quotes
# one number while the wizard charges another, and the shop is arguing with a
# customer holding a screenshot. So the catalog is checked against the
# worker's tables, not merely against itself.
_cat_f = OUT / "catalog.json"
if not _cat_f.exists():
    fails.append("catalog.json was not built - the MCP server and the feeds "
                 "have no catalog to read")
else:
    _cat = json.loads(_cat_f.read_text())
    # Checked against the table the WORKER will actually charge from -
    # worker/price-data.js, as committed - not against content.py, which both
    # are generated from. Comparing a generated file to its own source proves
    # only that the generator ran; comparing the published catalog to the
    # committed runtime table catches the case that actually bites, which is a
    # catalog rebuilt from a new price while the worker still ships the old
    # table.
    _pdj = (ROOT / "worker" / "price-data.js").read_text(encoding="utf-8")
    _pdata = json.loads(_pdj[_pdj.index("{"):_pdj.rindex(";")])

    for _p in _cat["products"]:
        _want = _pdata["FROM"][{"registration-numbers": "numbers",
                                "boat-name": "name", "both": "bundle"}[_p["id"]]]
        if _want != _p["from"]:
            fails.append("catalog says %s starts at $%s but the worker's price "
                         "table says $%s" % (_p["id"], _p["from"], _want))

    for _h in _cat["options"]["heights_in"]:
        _got = _pdata["HEIGHT_ADD"].get(str(_h["in"]))
        if _got != _h["add"]:
            fails.append('catalog says %s" adds $%s, the worker adds $%s'
                         % (_h["in"], _h["add"], _got))

    if _pdata["OUTLINE_ADD"] != _cat["options"]["outline"]["add"]:
        fails.append("catalog outline price disagrees with the worker")

    # The bands the catalog publishes are what a model will quote from, so
    # they have to be the bands the card charges.
    _cat_bands = [(b["up_to_in"], b["price"])
                  for b in next(x for x in _cat["products"]
                                if x["id"] == "boat-name")["bands"]]
    _run_bands = [(b["max_in"], b["price"]) for b in _pdata["NAME_BANDS"]]
    if _cat_bands != _run_bands:
        fails.append("catalog publishes the name bands %r and the worker "
                     "charges %r - an assistant would quote a price the card "
                     "does not take" % (_cat_bands, _run_bands))

    # The catalog must describe the SAME options the order form offers, or an
    # assistant offers a color or a font the customer cannot actually buy.
    for _c in _cat["options"]["colors"]:
        if 'value="%s"' % _c["name"] not in design and _c["name"] not in design:
            fails.append("catalog offers the color %s but the order form does "
                         "not" % _c["name"])
    from content import FONTS as _FONTS
    if len(_cat["options"]["fonts"]) != len(_FONTS):
        fails.append("catalog lists %d fonts, the site has %d"
                     % (len(_cat["options"]["fonts"]), len(_FONTS)))
    # Registration numbers are block-only by law; the catalog has to say which
    # faces qualify or the assistant will offer Snap ITC for a reg number.
    _blk = [f["name"] for f in _cat["options"]["fonts"] if f["block_legal"]]
    _site_blk = [f[0] for f in _FONTS if f[3]]
    if sorted(_blk) != sorted(_site_blk):
        fails.append("catalog block-legal fonts %s != site %s"
                     % (sorted(_blk), sorted(_site_blk)))

    if _cat["shipping"]["us"] != 0:
        fails.append("catalog no longer says US shipping is free")
    if _cat["fulfillment"]["proof_hours"] != 12:
        fails.append("catalog proof window is not 12 hours")

# The pricing authority must exist, or the catalog points callers at a 404.
if '/api/price' not in (ROOT / "worker" / "index.js").read_text():
    fails.append("/api/price is gone - the catalog names it as the pricing "
                 "authority and the MCP server prices through it")

# ---- the naming engine's bank -------------------------------------------
# Derived from the site's own two name sources. If the extractor silently
# produces a short bank, the engine starts dealing thin rounds and nobody
# notices until sessions stop converting.
_bank_f = ROOT / "mcp" / "data" / "name_bank.json"
if _bank_f.exists():
    _bank = json.loads(_bank_f.read_text())
    if _bank["name_count"] < 1000:
        fails.append("name bank has only %d names - the extractor is losing "
                     "the bank" % _bank["name_count"])
    _dupes = len(_bank["names"]) - len({n["name"].lower() for n in _bank["names"]})
    if _dupes:
        fails.append("name bank has %d duplicate names" % _dupes)
    for _n in _bank["names"][:50]:
        if not _n["categories"]:
            fails.append("bank name %r has no category" % _n["name"])
            break

    # Spec test 21: 100% of names carry a humor_mechanism. This is not
    # paperwork. The riff brief is built by asking "which mechanisms has this
    # lane kept?", so an untagged name is invisible to the ledger but still
    # dealable - it would win rounds and teach the engine nothing. And a name
    # with no humor_level can be dealt to a man naming the boat his
    # grandchildren ride in, which is the one mistake that costs a sale and a
    # reputation at the same time.
    import importlib.util as _ilu
    _tx_spec = _ilu.spec_from_file_location("nmb_tax", ROOT / "mcp" / "taxonomy.py")
    _tx = _ilu.module_from_spec(_tx_spec)
    _tx_spec.loader.exec_module(_tx)

    _no_mech = [n["name"] for n in _bank["names"] if not n.get("humor_mechanism")]
    if _no_mech:
        fails.append("%d bank names carry no humor_mechanism (e.g. %s) - the "
                     "engine must not deal an untagged name"
                     % (len(_no_mech), ", ".join(repr(x) for x in _no_mech[:4])))
    _no_lvl = [n["name"] for n in _bank["names"] if not n.get("humor_level")]
    if _no_lvl:
        fails.append("%d bank names carry no humor_level (e.g. %s) - without it "
                     "the engine cannot keep a dock joke off a family boat"
                     % (len(_no_lvl), ", ".join(repr(x) for x in _no_lvl[:4])))

    _mech_names = set(_tx.MECHANISMS.values())
    _lvl_names = set(_tx.LEVELS.values())
    _bad = sorted({n["humor_mechanism"] for n in _bank["names"]
                   if n.get("humor_mechanism")} - _mech_names)
    if _bad:
        fails.append("bank uses mechanisms outside the taxonomy: %s" % _bad)
    _bad = sorted({n["humor_level"] for n in _bank["names"]
                   if n.get("humor_level")} - _lvl_names)
    if _bad:
        fails.append("bank uses humor levels outside the taxonomy: %s" % _bad)

    # The §4b taxonomy is a library of ten mechanisms. If a build leaves most of
    # them with no examples, the riff brief has nothing to show and the engine
    # degrades to one joke told ten ways - which is what a base model already
    # does for free.
    _used = {n["humor_mechanism"] for n in _bank["names"] if n.get("humor_mechanism")}
    _unused = sorted(set(_tx.HUMOR_MECHANISMS.values()) - _used)
    if len(_unused) > 2:
        fails.append("%d of the 10 humor mechanisms have no example in the bank "
                     "(%s) - the riff brief cannot teach a mechanism it cannot "
                     "show" % (len(_unused), ", ".join(_unused)))

    # The level grades have to be a real distribution. If every name grades
    # clean, the gate is decorative and the next crude name sails through it.
    from collections import Counter as _TagCounter
    _lvls = _TagCounter(n.get("humor_level") for n in _bank["names"])
    if _lvls.get("dock", 0) < 20:
        fails.append("only %d names are graded dock - the humor_level pass was "
                     "not really done" % _lvls.get("dock", 0))

    # ---- the MCP server --------------------------------------------------
    # Structural, not behavioural - the behaviour is exercised against a real
    # worker. What is gated here is the things that must never slip:
    _mcpf = ROOT / "worker" / "mcp.js"
    if not _mcpf.exists():
        fails.append("worker/mcp.js is gone - there is no MCP server")
    else:
        _mcp = _mcpf.read_text()
        _wi0 = (ROOT / "worker" / "index.js").read_text()
        if "handleMcp" not in _wi0:
            fails.append("the MCP server is not mounted on the worker")
        # Every tool must declare itself read-only. The server takes no money
        # and writes nothing; the moment a tool does, it needs its own review
        # and this gate should be the thing that forces it.
        # One tool writes session state (start_naming_session). Every other
        # tool must declare readOnlyHint:true. The exception is named here so
        # that adding a second writer is a deliberate edit to this gate rather
        # than something that slips in.
        _WRITERS = {"start_naming_session", "vote_on_names",
                    "submit_riff_candidates"}
        _declared = re.findall(r'name: "(\w+)",\s*\n\s*title:', _mcp)
        _ro = len(re.findall(r"readOnlyHint: true", _mcp))
        _rw = len(re.findall(r"readOnlyHint: false", _mcp))
        if _declared and len(_declared) != _ro + _rw:
            fails.append("%d MCP tools declared but only %d carry a "
                         "readOnlyHint - every tool needs one, both "
                         "directories read it"
                         % (len(_declared), _ro + _rw))
        if _rw != len(_WRITERS):
            fails.append("%d MCP tools declare readOnlyHint:false but only %s "
                         "may write. A new writer needs a deliberate change "
                         "here and a look at the privacy policy."
                         % (_rw, sorted(_WRITERS)))
        # Against the DECLARED tool names, not a substring of the file. The
        # first version used `_w not in _mcp` and renaming the tool to
        # submit_riffs passed clean, because the old name still appeared in
        # another tool's description. A gate that reads prose is not a gate.
        for _w in _WRITERS:
            if _w not in _declared:
                fails.append("%s is listed as a permitted writer but no tool "
                             "declares that name - it was renamed or removed "
                             "and the allowlist was not" % _w)
        # The validator must be CALLED, not merely present. Removing the one
        # line in dispatch() that calls it leaves every unit test for
        # validate() passing and the server wide open again - which is how
        # check_registration_layout came to answer verdict "ok" to a call it
        # had not read. Unit tests cover the function; only a gate covers the
        # wiring.
        if "validate(t.inputSchema" not in _mcp:
            fails.append("worker/mcp.js no longer validates tool arguments "
                         "against inputSchema in dispatch() - a call with a "
                         "misnamed parameter would be answered rather than "
                         "rejected")
        if "export function validate" not in _mcp:
            fails.append("the MCP argument validator is gone")
        # Every schema has to be enforceable: a tool that declares no
        # required fields and no additionalProperties:false cannot be
        # validated into anything.
        for _blk in re.finditer(r'name: "(\w+)",\n\s*title:', _mcp):
            _nm = _blk.group(1)
            _seg = _mcp[_blk.start():_blk.start() + 7000]
            _i, _j = _seg.find("inputSchema"), _seg.find("async run")
            if _i < 0 or _j < _i:
                continue
            _sch = _seg[_i:_j]
            if "additionalProperties: false" not in _sch:
                fails.append("%s's inputSchema does not set "
                             "additionalProperties:false, so a hallucinated "
                             "parameter would be silently ignored" % _nm)
        # "+/-undefined%" reached a customer through this template.
        if "error_pct}%" in _mcp and "error_pct != null" not in _mcp:
            fails.append("the MCP server prints the accuracy figure without "
                         "checking it exists - fitGate's no-name path has no "
                         "error_pct and this printed '+/-undefined%'")
        # The first thing every client reads is `initialize`, and it said
        # "Every tool here is read-only" for as long as three of them wrote.
        if "Every tool here is read-only" in _mcp or \
                "All tools are read-only" in _mcp:
            fails.append("the MCP server still tells every client that every "
                         "tool is read-only, and three of them write")
        if "destructiveHint: false" not in _mcp:
            fails.append("MCP tools are missing destructiveHint - OpenAI and "
                         "Anthropic both read the annotations")
        # It must price through the one function, never its own arithmetic.
        if "ctx.priceBreakdown(" not in _mcp:
            fails.append("the MCP server is no longer pricing through the "
                         "shared function - it has grown its own copy of the "
                         "price")
        # AND IT MUST SPEAK THE SAME VOCABULARY. This gate used to check
        # only that the pricing function was CALLED, which it always was -
        # while the slugs the tool passed it ("numbers", "name", "both")
        # matched nothing in the table, fell through a default, and quoted the
        # registration-number base for a name and for the bundle, silently,
        # on every quote at three inches. Calling the one pricing function
        # with a vocabulary it does not speak is exactly as wrong as keeping a
        # second copy of the price, and it fails more quietly. So: every value
        # in the tool's own enum must resolve through KIND_ALIAS.
        _m_enum = re.search(
            r'kind: \{ type: "string",\s*\n?\s*enum: \[([^\]]*)\]', _mcp)
        _pricejs = (ROOT / "worker" / "price.js").read_text(encoding="utf-8")
        _alias = re.search(r"export const KIND_ALIAS = \{(.*?)\n\};",
                           _pricejs, re.S)
        if not _m_enum:
            fails.append("price_order's kind enum could not be read - this "
                         "gate is the only thing checking that the MCP "
                         "server and the price table agree on product names")
        elif not _alias:
            fails.append("KIND_ALIAS is gone from worker/price.js - the "
                         "vocabulary and the price live together on purpose")
        else:
            _al = dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', _alias.group(1)))
            _canon = {"numbers", "name", "both"}
            for _k in re.findall(r'"([^"]+)"', _m_enum.group(1)):
                if _al.get(_k) not in _canon:
                    fails.append("price_order offers kind=%r, which KIND_ALIAS "
                                 "does not resolve to a real product - it "
                                 "would be quoted as the cheapest thing we "
                                 "sell" % _k)
            for _k, _v in _al.items():
                if _v not in _canon:
                    fails.append("KIND_ALIAS maps %r to %r, which is not one "
                                 "of numbers/name/both" % (_k, _v))
            # catalog.json advertises a third set of names. A model reads them
            # from get_products and then prices what it read.
            try:
                _cat = json.loads((OUT / "catalog.json").read_text())
                for _pr in _cat.get("products", []):
                    _pid = _pr.get("id")
                    if _pid and _al.get(_pid) not in _canon:
                        fails.append("get_products advertises the product id "
                                     "%r and price_order cannot price it - a "
                                     "model reading the catalog and pricing "
                                     "what it read gets the wrong number"
                                     % _pid)
                # The height upcharges the catalog publishes must be the ones
                # the tool will charge.
                _ch = {str(h["in"]): h["add"]
                       for h in _cat.get("options", {}).get("heights_in", [])}
                if _ch != {k: v for k, v in PRICE["height_add"].items()}:
                    fails.append("catalog.json publishes height upcharges %r "
                                 "and the price table says %r"
                                 % (_ch, PRICE["height_add"]))
            except Exception:
                pass
            # A boat name is priced by the width it finishes at, so the tool
            # cannot answer without the lettering and the face. If the SCHEMA
            # stops asking for them, every name quote becomes the smallest
            # band - the undercharge bug with a new coat of paint.
            #
            # Scoped to price_order's inputSchema, and that scoping is the
            # whole gate. The first version searched the file for "boatname:"
            # and passed with the schema field deleted, because the handler
            # and the echoed `priced` block both still mention it. A gate that
            # cannot fail is worse than no gate: it reads as coverage.
            _po = re.search(r'name: "price_order".*?async run\(', _mcp, re.S)
            if not _po:
                fails.append("price_order's tool definition could not be read")
            else:
                _schema = re.search(r"inputSchema: \{(.*)$", _po.group(0), re.S)
                _schema = _schema.group(1) if _schema else ""
                for _need in ("boatname:", "font:"):
                    if _need not in _schema:
                        fails.append(
                            "price_order's inputSchema no longer accepts %s - "
                            "a boat name is priced by the width it finishes "
                            "at, so without it every name is quoted in the "
                            "cheapest band" % _need.rstrip(":"))
                # And it must actually PASS them through, or asking for them
                # is theatre.
                _run = _mcp[_mcp.index('name: "price_order"'):]
                _run = _run[_run.index("async run("):]
                _run = _run[:_run.index("\n  },")]
                for _need in ("boatname: args.boatname", "font: args.font"):
                    if _need not in _run:
                        fails.append("price_order reads %s from the caller and "
                                     "does not pass it to the pricing "
                                     "function" % _need.split(":")[0])

        # The strict path exists because the lenient one hid the bug above.
        if "ctx.priceBreakdown(" in _mcp and ", true)" not in _mcp:
            fails.append("the MCP server is pricing leniently again - an "
                         "unknown product would be quoted as the cheapest "
                         "thing we sell instead of erroring")
        # Scan CODE, not prose. This file explains at length why price_order
        # exists separately from /api/checkout and what a Stripe PaymentIntent
        # costs us - and the first version of this gate failed the build on
        # its own comment. Strip the comment lines first.
        _mcp_nc = "\n".join(
            l for l in _mcp.splitlines()
            if not l.strip().startswith(("//", "*", "/*")))
        _mcp_code = _mcp_nc.lower()
        # The session writer needs DB.prepare, so a flat ban no longer works.
        # Instead: the only table the MCP server may name is naming_sessions.
        for _tbl in re.findall(
                r"(?:INSERT INTO|DELETE FROM|FROM|UPDATE|JOIN)\s+([a-z_]+)",
                _mcp_nc):
            if _tbl not in ("naming_sessions",):
                fails.append("worker/mcp.js reads or writes the %r table - "
                             "the only table this server may touch is "
                             "naming_sessions" % _tbl)
        if "naming_sessions" in _mcp_code and "30 days" not in _mcp:
            fails.append("the MCP server stores naming sessions but no longer "
                         "states the 30-day retention it promises in the "
                         "privacy policy")
        for _bad in ("/api/checkout", "resend.com", "stripe"):
            if _bad in _mcp_code:
                fails.append("worker/mcp.js references %r - this server is "
                             "read-only and must not take money, write rows "
                             "or send mail" % _bad)
        # The honesty limit has to reach the model, not just the code.
        if "not a registry" not in _mcp:
            fails.append("the MCP server no longer tells the model that the "
                         "overuse data is market data and not a registry")
        # mcpInfo() names a privacy page and a support page, and a
        # directory reviewer will click both. Worker code is not scanned by
        # the broken-link pass that covers the built pages, so it gets its
        # own check.
        for _u in re.findall(r'"https://numbermyboat\.com(/[a-z0-9/-]*)"',
                             _mcp):
            _t = (OUT / _u.strip("/") / "index.html") if _u.strip("/") \
                else (OUT / "index.html")
            if _u not in ("/mcp",) and not _t.exists():
                fails.append("the MCP server points callers and reviewers at "
                             "%s and that page is not built" % _u)
        if "33 CFR 173.27" not in _mcp:
            fails.append("the MCP server no longer states the 3-inch block "
                         "character rule for registration numbers")
    _wi = (ROOT / "worker" / "index.js").read_text()
    if "naming_sessions" in _mcp and "DELETE FROM naming_sessions" not in _wi:
        fails.append("naming sessions are stored but nothing purges them - a "
                     "retention promise nothing enforces is not a promise")
    _pp = (OUT / "privacy" / "index.html")
    if _pp.exists():
        _pt = _pp.read_text()
        if "naming_sessions" in _mcp and "30 days" not in _pt:
            fails.append("the privacy policy does not mention the naming "
                         "assistant's 30-day retention, and the site now "
                         "stores interview answers")
        if "That is it." in _pt:
            fails.append("the privacy policy still says order data is all we "
                         "collect - the naming assistant stores interview "
                         "answers too")
    if not (OUT / "name-bank-full.json").exists():
        fails.append("public/name-bank-full.json was not built - the ranker "
                     "has no tagged bank to read")
    if not (OUT / "name-bank.json").exists():
        fails.append("public/name-bank.json was not built - the MCP novelty "
                     "check has no bank to compare against")

    # ---- the performance ledger -----------------------------------------
    # The ledger is the only table on this site that LEARNS, and the only
    # naming table that outlives the 30-day session purge. Both of those are
    # fine for exactly one reason - it holds nothing personal - so that is
    # what is gated here, along with the decay that makes "proven" mean
    # something this month rather than last year.
    _sch = (ROOT / "schema.sql").read_text()
    _eng_src = (ROOT / "worker" / "engine.js").read_text()
    if "CREATE TABLE IF NOT EXISTS ledger" in _sch:
        _led = _sch.split("CREATE TABLE IF NOT EXISTS ledger")[1].split(");")[0]
        for _col in ("session", "answers", "story", "email", "profile",
                     "order", "ip", "ua"):
            if _col in _led.lower():
                fails.append("the ledger table has a %r column - this is the "
                             "one naming table that outlives the 30-day "
                             "purge and it may hold nothing but (lane, "
                             "mechanism, counters)" % _col)
        if "nothing personal" not in _sch.lower():
            fails.append("schema.sql no longer records WHY the ledger is "
                         "allowed to outlive the session purge")
        # A careless retention sweep that took the ledger with it would
        # silently delete the learning loop and nothing would ever say so.
        if "DELETE FROM ledger" in _wi:
            fails.append("something deletes from the ledger - the counters "
                         "are aggregate and are meant to survive the session "
                         "purge; decay is a halving, not a delete")
        # Riff text must never reach it. mcp.js cannot name the table at all
        # (the allowlist above), so the remaining risk is engine.js filing a
        # riff as a name row.
        if 'it.source !== "riff"' not in _eng_src:
            fails.append("engine.js no longer keeps riff text out of the "
                         "ledger - a riff is built out of somebody's wife, "
                         "dog or hometown and the ledger is permanent")
        if "w_exposures / 2" not in _wi:
            fails.append("nothing halves the ledger's window - without the "
                         "decay a mechanism that stopped landing in October "
                         "still reads as proven in December")
        if "w_exposures / 2" in _wi and "getUTCHours() === 0" not in _wi:
            fails.append("the monthly review is not guarded on the hour, and "
                         "it runs on an HOURLY cron - it would halve the "
                         "window twenty-four times in a day")
        if "/api/mech-review" in _wi:
            _blk = _wi.split('"/api/mech-review"')[1][:400]
            if "PROOF_RUN_KEY" not in _blk:
                fails.append("/api/mech-review is not behind the owner key")
    # The brief is a set of claims made to a model, which writes them into a
    # rationale a customer reads. Two of those claims must stay honest.
    if "COLD" not in _eng_src:
        fails.append("the riff brief no longer declares a cold ledger - it "
                     "would present exemplars as evidence when nothing has "
                     "ever been kept")
    if "no keep data" not in _eng_src:
        fails.append("the riff brief no longer says how its exemplars were "
                     "chosen - claiming they are the highest keep-rate names "
                     "before anything has been kept is a lie the host model "
                     "will repeat")
    for _need, _why in (
            ("noveltyGate(name, bankNames)",
             "riffs are no longer novelty-checked, so a model can hand back "
             "one of our own 1,089 names as its own invention"),
            ("Math.floor(size / 3)",
             "the riff cap is gone - riffs are at most a third of a round"),
            ("nExplore >= exploreCap",
             "the exploration cap is gone - an unproven mechanism may take "
             "at most one slot in a round")):
        if _need not in _eng_src:
            fails.append(_why)

    # ---- the naming engine -----------------------------------------------
    # Tested in JavaScript because it only ever runs on the worker - no Python
    # twin, so nothing to keep in step. The ceiling case is the one that
    # matters: a name dealt to a man naming the boat his grandchildren ride in.
    _eng = ROOT / "mcp" / "test_engine.mjs"
    if not _eng.exists():
        fails.append("mcp/test_engine.mjs is missing - the ranker is untested")
    else:
        _p = subprocess.run(["node", str(_eng)], capture_output=True,
                            text=True, cwd=str(ROOT))
        if _p.returncode:
            for _l in (_p.stdout or "").splitlines():
                if _l.startswith("FAIL:"):
                    fails.append("engine: %s" % _l[6:])
            if not any(f.startswith("engine:") for f in fails):
                fails.append("the engine tests would not run: %s"
                             % (_p.stderr or "")[-300:])

    # ---- the Pay button and the card ------------------------------------
    # The order form's running total is worker/price.js itself, inlined into
    # the page by engine/shared_js.price_js(). In principle the two cannot
    # disagree. In practice the INLINER is four text transforms applied to
    # code that takes money - regex-stripping imports and `export`, slicing
    # the font metrics out of a generated file, lifting widthIn() out by brace
    # matching, and emptying one key. Any of those could silently drop a
    # clause, and the result would be a form quoting a price the card does not
    # charge.
    #
    # So both are run over every combination of product, height, name, face,
    # outline and upgrade set and compared. 5,600-odd cases, about a second.
    _tpb = ROOT / "mcp" / "test_price_browser.mjs"
    if not _tpb.exists():
        fails.append("mcp/test_price_browser.mjs is missing - nothing proves "
                     "the form's total matches the card charge")
    else:
        import tempfile as _tf
        with _tf.NamedTemporaryFile("w", suffix=".js", delete=False,
                                    encoding="utf-8") as _bf:
            _bf.write(_pjs_browser())
            _bundle = _bf.name
        try:
            _p2 = subprocess.run(["node", str(_tpb), _bundle],
                                 capture_output=True, text=True, cwd=str(ROOT))
            if _p2.returncode:
                _lines = [l for l in (_p2.stdout or "").splitlines()
                          if l.strip()]
                if _lines:
                    for _l in _lines[:6]:
                        fails.append("price: %s" % _l)
                else:
                    fails.append("the form/card price comparison would not "
                                 "run: %s" % (_p2.stderr or "")[-300:])
        finally:
            pathlib.Path(_bundle).unlink(missing_ok=True)

    # ---- one implementation of the decoders ------------------------------
    # worker/decode.js is run by the MCP server AND inlined into the order
    # form and both tool pages. That is only true as long as the inlined copy
    # is regenerated from the source, so it is checked rather than trusted.
    _dj = ROOT / "worker" / "decode.js"
    _dd = ROOT / "worker" / "decode-data.js"
    if not _dj.exists() or not _dd.exists():
        fails.append("worker/decode.js or decode-data.js is missing - the "
                     "registration checker and HIN decoder have no source")
    else:
        import subprocess as _sp2
        _b = _dd.read_bytes()
        _sp2.run([sys.executable, str(ROOT / "mcp" / "build_decode_js.py")],
                 capture_output=True)
        if _dd.read_bytes() != _b:
            fails.append("worker/decode-data.js was stale - it is generated "
                         "from engine/content.py and engine/tools.py and had "
                         "drifted. Regenerated; commit it.")
        _sh_spec = _ilu.spec_from_file_location(
            "nmb_sh", ROOT / "engine" / "shared_js.py")
        _sh = _ilu.module_from_spec(_sh_spec)
        _sh_spec.loader.exec_module(_sh)
        _want = _sh.decode_js()
        for _pg in ("design/index.html",
                    "tools/registration-number-layout-checker/index.html",
                    "tools/hull-number-decoder/index.html"):
            _f = OUT / _pg
            if not _f.exists():
                fails.append("%s is missing" % _pg)
                continue
            _t = _f.read_text(encoding="utf-8")
            if "window.NMB_DECODE=" not in _t:
                fails.append("%s does not carry the shared decoder - it has "
                             "its own copy of the logic again" % _pg)
            # A couple of distinctive lines, to catch an inlined copy that was
            # hand-patched instead of regenerated.
            for _probe in ("function checkRegistration(raw)",
                           "function decodeHin(raw)"):
                if _probe not in _t:
                    fails.append("%s is missing %r from the shared decoder"
                                 % (_pg, _probe))
        # A second copy must not reappear. engine/validate.py held the old
        # registration logic and was deleted when the shared module took over;
        # these probes catch either decoder being reimplemented anywhere in
        # the engine, which is how this drifts back apart.
        for _ef in sorted((ROOT / "engine").glob("*.py")):
            if _ef.name == "shared_js.py":
                continue
            _et = _ef.read_text(encoding="utf-8")
            if "BNS_POSTAL_MISTAKE" in _et or "window.BNS_VALIDATE = (func" in _et:
                fails.append("engine/%s has its own registration logic - "
                             "worker/decode.js is the implementation and "
                             "engine/shared_js.py ships it to the browser"
                             % _ef.name)
            if "MIC[mic]" in _et:
                fails.append("engine/%s is decoding HINs again - that logic "
                             "belongs to worker/decode.js only" % _ef.name)

    # ---- the deterministic gates ----------------------------------------
    # mcp/test_gates.py pins the radio, overuse and novelty gates. It runs
    # HERE rather than as a separate command because every one of its cases is
    # a decision that was got wrong once already, and a gate that only runs
    # when somebody remembers to run it is not a gate.
    _tg_spec = _ilu.spec_from_file_location("nmb_tg", ROOT / "mcp" / "test_gates.py")
    try:
        _tg = _ilu.module_from_spec(_tg_spec)
        _tg_spec.loader.exec_module(_tg)
        for _f in _tg.run():
            fails.append("gates: %s" % _f)
    except Exception as _e:
        fails.append("the gate tests could not run at all: %s: %s"
                     % (type(_e).__name__, _e))

    # ---- python vs worker ------------------------------------------------
    # The MCP server runs on the Worker, so the gates exist in JavaScript too.
    # Two implementations of the moat is exactly what the one-implementation
    # rule exists to prevent, so they are compared over every bank name on
    # every field. If node is missing this reports that rather than passing.
    _eq_spec = _ilu.spec_from_file_location(
        "nmb_eq", ROOT / "mcp" / "test_equivalence.py")
    try:
        _eq = _ilu.module_from_spec(_eq_spec)
        _eq_spec.loader.exec_module(_eq)
        for _f in _eq.run()[:6]:
            fails.append("gates: %s" % _f)
    except Exception as _e:
        fails.append("the python/worker gate comparison could not run: %s: %s"
                     % (type(_e).__name__, _e))

    # The emitted tables must be current. gates-data.js is derived from
    # gates.py; a stale copy means the worker is running yesterday's rules.
    _gd = ROOT / "worker" / "gates-data.js"
    if not _gd.exists():
        fails.append("worker/gates-data.js is missing - rebuild it with "
                     "python3 mcp/build_gates_js.py")
    else:
        import subprocess as _sp
        _before = _gd.read_bytes()
        _sp.run([sys.executable, str(ROOT / "mcp" / "build_gates_js.py")],
                capture_output=True)
        if _gd.read_bytes() != _before:
            fails.append("worker/gates-data.js was stale - it is generated "
                         "from mcp/gates.py and had drifted. It has been "
                         "regenerated; commit it.")

    # Sincere names are not a joke mechanism. If one is ever handed to the riff
    # brief as a mechanism to write in, the engine starts producing earnest
    # one-word nature names in a deadpan round.
    if "sincere (not a joke)" in _tx.HUMOR_MECHANISMS.values():
        fails.append("sincere leaked into HUMOR_MECHANISMS - it must never be "
                     "offered to the riff brief as a mechanism")

# ---- IndexNow ------------------------------------------------------------
# Two halves, and a submission is rejected unless both are true: the key, and
# a file at /<key>.txt whose entire contents are that key. The file is what
# proves to Bing that whoever is submitting URLs controls this site, so if it
# goes missing every submission silently 403s - and nothing else on the site
# looks any different, which is why this is gated rather than noticed.
from content import INDEXNOW_KEY as _INK                      # noqa: E402
if _INK:
    if not re.fullmatch(r"[0-9a-f]{8,128}", _INK):
        fails.append("INDEXNOW_KEY is %r - Bing wants 8 to 128 hex characters"
                     % _INK[:16])
    _kf = OUT / ("%s.txt" % _INK)
    if not _kf.is_file():
        fails.append("the IndexNow key file %s.txt was not built - every "
                     "submission would be rejected and nothing on the site "
                     "would look wrong" % _INK)
    elif _kf.read_text().strip() != _INK:
        fails.append("the IndexNow key file does not contain the key")
    # A rotated key must not leave the old file behind: two valid key files is
    # a second credential nobody is tracking.
    _strays = [f.name for f in OUT.glob("*.txt")
               if re.fullmatch(r"[0-9a-f]{8,128}\.txt", f.name)
               and f.name != "%s.txt" % _INK]
    if _strays:
        fails.append("stale IndexNow key file(s) still published: %s"
                     % ", ".join(_strays))
    if not (ROOT / "mcp" / "indexnow.py").is_file():
        fails.append("the IndexNow key is configured but mcp/indexnow.py is "
                     "gone - nothing submits anything")

# ---- the Product node, as Search Console reads it ------------------------
# Structured data is a claim made to a search engine on the shop's behalf.
# Google reported this node as "1 invalid item" for a missing image, which
# costs the whole rich result; these gates are the ones that would have caught
# it, plus the ones that keep the rest of the node true.
#
# The expensive failure is not an absent field - Search Console emails about
# those. It is a field that is PRESENT and WRONG: a delivery window the shop
# does not meet, or a returns policy it has not offered. Nobody emails about
# those, and the first person to find out is a customer quoting it back.
import datetime as _dt                                        # noqa: E402

_prod_nodes = []
for _f in OUT.rglob("index.html"):
    _t = _f.read_text()
    for _blk in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', _t, re.S):
        try:
            _g = json.loads(_blk)
        except Exception:
            continue
        # A block may be a graph, a bare node, a list of nodes, or - on the
        # pages that embed a placeholder - literally null. The first version
        # of this assumed a dict and died on the first page that was not one.
        _cands = _g if isinstance(_g, list) else [_g]
        for _c in _cands:
            if not isinstance(_c, dict):
                continue
            for _node in (_c.get("@graph") or [_c]):
                if isinstance(_node, dict) and _node.get("@type") == "Product":
                    _prod_nodes.append((_f.relative_to(OUT), _node))

if not _prod_nodes:
    fails.append("no Product schema anywhere - the shop has stopped "
                 "describing what it sells to search engines")

_seen_img = set()
for _page, _n in _prod_nodes:
    _o = _n.get("offers") or {}

    # THE CRITICAL ONE. Missing image = the whole item is invalid and the page
    # is ineligible for rich results.
    _imgs = _n.get("image") or []
    if isinstance(_imgs, str):
        _imgs = [_imgs]
    if not _imgs:
        fails.append("the Product node on %s has no image - Search Console "
                     "reports the whole item as invalid and the page gets no "
                     "rich result" % _page)
    for _u in _imgs:
        if not _u.startswith("https://"):
            fails.append("Product image %r on %s is not an absolute https URL"
                         % (_u, _page))
            continue
        # A merchant listing image must be the PRODUCT. The OG cards have a
        # headline and a price badge burned across them, which is exactly what
        # that image may not be - and they are the easiest wrong thing to
        # reach for, since og_image() is right there.
        if "/assets/og/" in _u:
            fails.append("the Product node on %s uses a share card as its "
                         "image - those have marketing text burned into them"
                         % _page)
        _rel = _u.split("numbermyboat.com/", 1)[-1]
        _disk = OUT / _rel
        if not _disk.is_file():
            fails.append("Product image %s on %s does not exist on disk - "
                         "Google cannot fetch it and the item stays invalid"
                         % (_rel, _page))
        elif _rel not in _seen_img:
            _seen_img.add(_rel)
            # Google wants at least 696px on the long edge.
            try:
                _dim = subprocess.run(
                    ["sips", "-g", "pixelWidth", str(_disk)],
                    capture_output=True, text=True)
                _w = int(re.search(r"pixelWidth:\s*(\d+)", _dim.stdout).group(1))
                if _w < 696:
                    fails.append("Product image %s is %dpx wide; Google wants "
                                 "at least 696" % (_rel, _w))
            except Exception:
                pass          # sips is a convenience, not a dependency

    # The price in the schema is the price on the card.
    if _o.get("price") != str(PRICE["numbers"]) and \
            _o.get("price") != str(PRICE["name_from"]):
        fails.append("the Product node on %s offers $%s, which is neither of "
                     "the published starting prices ($%d, $%d)"
                     % (_page, _o.get("price"), PRICE["numbers"],
                        PRICE["name_from"]))

    # validFrom must be real and in the past. Emitting today's date on every
    # rebuild would be an offer that claims to have begun this morning.
    _vf = _o.get("validFrom")
    if _vf != PRICE["set_on"]:
        fails.append("the Product node on %s says the price has been valid "
                     "from %r and the price table says %r"
                     % (_page, _vf, PRICE["set_on"]))
    else:
        try:
            if _dt.date.fromisoformat(_vf) > _dt.date.today():
                fails.append("validFrom %s is in the future - the offer "
                             "claims not to have started yet" % _vf)
        except ValueError:
            fails.append("validFrom %r is not a date" % _vf)

    # priceValidUntil in the past makes Google drop the offer.
    _pvu = _o.get("priceValidUntil")
    try:
        _days = (_dt.date.fromisoformat(_pvu) - _dt.date.today()).days
        if _days < 90:
            fails.append("priceValidUntil on %s is %d days away - Google "
                         "treats a near or past date as a stale price and "
                         "drops the offer. It should roll forward on build."
                         % (_page, _days))
    except (ValueError, TypeError):
        fails.append("priceValidUntil %r on %s is not a date" % (_pvu, _page))

    # The return policy has to be the one the site publishes.
    _rp = (_o.get("hasMerchantReturnPolicy") or {}).get("returnPolicyCategory")
    if not _rp:
        fails.append("the Product node on %s has no return policy - Search "
                     "Console asks for one and buyers ask for it first"
                     % _page)
    elif _rp != "https://schema.org/MerchantReturnNotPermitted":
        fails.append("the Product node on %s claims the return policy %r. "
                     "/shipping-and-returns/ says custom-cut vinyl is not "
                     "returnable; promising a window the shop does not offer "
                     "is worse than promising nothing" % (_page, _rp))

    # Delivery time, against the page that prints it.
    _dtm = (_o.get("shippingDetails") or {}).get("deliveryTime") or {}
    _tt = _dtm.get("transitTime") or {}
    _ht = _dtm.get("handlingTime") or {}
    if not _tt or not _ht:
        fails.append("the Product node on %s has no delivery time - the "
                     "listing cannot say when it arrives" % _page)
    else:
        if (_tt.get("minValue"), _tt.get("maxValue")) != _SHIP_TRANSIT:
            fails.append("the Product node on %s publishes a transit window "
                         "of %s-%s days and build.SHIP_TRANSIT says %s-%s"
                         % (_page, _tt.get("minValue"), _tt.get("maxValue"),
                            _SHIP_TRANSIT[0], _SHIP_TRANSIT[1]))
        # Handling must cover the proof AND the customer's approval, not just
        # the 1-2 days of production we control.
        if (_ht.get("maxValue") or 0) < 2:
            fails.append("the Product node on %s promises handling in under "
                         "two days. The shop's own promise is a proof within "
                         "12 hours and then 1-2 business days FROM APPROVAL, "
                         "and the approval is the customer's" % _page)

# The schema's transit window against the page a customer actually reads.
_ship = (OUT / "shipping-and-returns" / "index.html").read_text()
# ANCHORED TO THE STANDARD-POST ROW, and that anchoring is the whole gate.
#
# The first version searched the whole page for "N-M business days". A break
# test moved the window to 1-2 and the gate stayed silent, because the page
# also says production takes "1-2 business days" - a different promise about a
# different stage - and the substring matched that instead. A gate that can
# match the wrong sentence is not checking anything.
#
# Compared against what a READER sees, too: the table writes the range with
# &ndash;, so matching the raw markup for a dash finds nothing.
_ship_txt = html.unescape(_ship).replace("\u2013", "-").replace("\u2014", "-")
_row = re.search(r"Standard post.{0,120}?business days", _ship_txt, re.S)
if not _row:
    fails.append("the shipping table has no Standard post row - that row is "
                 "where the transit window the Product schema publishes is "
                 "shown to the customer")
elif "%d-%d business days" % _SHIP_TRANSIT not in _row.group(0):
    fails.append("the shipping table's Standard post row says %r and the "
                 "Product schema publishes %d-%d business days - the listing "
                 "would promise a delivery window the page does not"
                 % (_row.group(0)[-28:].strip(), _SHIP_TRANSIT[0],
                    _SHIP_TRANSIT[1]))
# And the returns claim the schema makes.
if "not returnable" not in _ship_txt:
    fails.append("the shipping page no longer says custom work is not "
                 "returnable, but the Product schema tells Google returns are "
                 "not permitted - one of the two is now wrong")

# ---- analytics ----------------------------------------------------------
# GA4 on every public page and on no internal one. A tag that silently stops
# being emitted looks exactly like a traffic collapse in the reports, and a
# tag on /brand/ or /proof/ quietly pollutes them instead.
_GA = "G-P2QBX2TXPX"
_ga_pub = _ga_int = 0
for _f in OUT.rglob("index.html"):
    _t = _f.read_text()
    _has = _GA in _t
    if 'content="noindex' in _t:
        if _has:
            fails.append("GA4 is on the internal page %s"
                         % _f.relative_to(OUT))
        _ga_int += 1
    else:
        if not _has:
            fails.append("GA4 is missing from %s" % _f.relative_to(OUT))
        _ga_pub += 1
        if _t.count(_GA) != 2:   # the script src and the config call
            fails.append("GA4 appears %d times on %s - a double tag counts "
                         "every pageview twice"
                         % (_t.count(_GA), _f.relative_to(OUT)))
if _ga_pub < 50:
    fails.append("only %d public pages carry GA4" % _ga_pub)

_home = (OUT / "index.html").read_text()
# Staging and local builds must stay out of the property, or deploy testing
# lands in the same reports as real customers.
if 'location.hostname==="numbermyboat.com"' not in _home:
    fails.append("the GA4 tag is no longer gated to the live hostname - "
                 "workers.dev and local traffic would pollute the property")
# The privacy policy promises no advertising trackers. These two switches are
# what keep that true; turning either on is a policy change.
for _flag in ("allow_google_signals:false",
              "allow_ad_personalization_signals:false"):
    if _flag not in _home:
        fails.append("GA4 %s is gone - the privacy policy says we run no "
                     "advertising trackers" % _flag)
if "async=true" not in _home and "async = true" not in _home:
    fails.append("the GA4 script is no longer async and would block rendering")

# ---- Cloudflare Web Analytics -------------------------------------------
# The second, independent count. Cookieless, so it needs no consent gate - but
# it is still a third party receiving page views, so the privacy policy has to
# say so, and it must follow GA4's rules exactly or the two reports cover
# different sites and comparing them means nothing.
import importlib as _il                                   # noqa: E402
_bld = _il.import_module("build")
_CFT = getattr(_bld, "CF_BEACON_TOKEN", None)
if _CFT is None:
    fails.append("CF_BEACON_TOKEN is gone from build.py - Cloudflare Web "
                 "Analytics was wired up deliberately")
elif not _CFT:
    # Not an error. The plumbing ships with no token until someone pastes one
    # in from the dashboard; what must NOT happen is a half-wired beacon going
    # out and firing with an invalid token.
    notes.append("Cloudflare Web Analytics is wired but has no token yet - "
                 "no beacon is emitted. Paste the site token into "
                 "CF_BEACON_TOKEN in engine/build.py.")
    for _f in OUT.rglob("index.html"):
        if "cloudflareinsights" in _f.read_text():
            fails.append("a Cloudflare beacon is on %s with no token set - it "
                         "would fire against nothing"
                         % _f.relative_to(OUT))
else:
    if not re.fullmatch(r"[0-9a-f]{32}", _CFT):
        fails.append("CF_BEACON_TOKEN is %r, which is not a 32-character hex "
                     "site token - the beacon would report to nothing"
                     % _CFT[:12])
    _cf_pub = 0
    for _f in OUT.rglob("index.html"):
        _t = _f.read_text()
        _has = "cloudflareinsights" in _t
        if 'content="noindex' in _t:
            if _has:
                fails.append("the Cloudflare beacon is on the internal page "
                             "%s" % _f.relative_to(OUT))
        else:
            if not _has:
                fails.append("the Cloudflare beacon is missing from %s - the "
                             "two counts no longer cover the same site"
                             % _f.relative_to(OUT))
            else:
                _cf_pub += 1
            if _t.count("cloudflareinsights") > 1:
                fails.append("the Cloudflare beacon appears twice on %s"
                             % _f.relative_to(OUT))
    if _cf_pub and _cf_pub != _ga_pub:
        fails.append("the Cloudflare beacon is on %d public pages and GA4 is "
                     "on %d - the two counts cover different sites, so any "
                     "comparison between them is meaningless"
                     % (_cf_pub, _ga_pub))
    # Same hostname gate as GA4, for the same reason: the staging worker
    # serves these same pages and nobody there is going to buy anything.
    _home_cf = (OUT / "index.html").read_text()
    _i = _home_cf.find("cloudflareinsights")
    if _i > 0:
        _window = _home_cf[max(0, _i - 400):_i]
        if 'location.hostname==="numbermyboat.com"' not in _window:
            fails.append("the Cloudflare beacon is not gated to the live "
                         "hostname - staging and local traffic would land in "
                         "the same report as real customers")
    if "Cloudflare Web Analytics" not in (OUT / "privacy" / "index.html").read_text():
        fails.append("the site runs Cloudflare Web Analytics but the privacy "
                     "policy does not mention it")

# ---- Bing Webmaster Tools ------------------------------------------------
# Verification by meta tag, on the root only, because the root is the URL Bing
# fetches to check. The failure this gates against is silent and slow: the tag
# stops being emitted, nobody notices, and months later Bing unverifies the
# site - which also takes away the index that ChatGPT search reads.
_bing = getattr(_bld, "BING_VERIFY", None)
if _bing:
    if not re.fullmatch(r"[0-9A-F]{32}", _bing):
        fails.append("BING_VERIFY is not a 32-character hex token: %r"
                     % _bing[:12])
    _hp = (OUT / "index.html").read_text()
    _tag = '<meta name="msvalidate.01" content="%s">' % _bing
    if _tag not in _hp:
        fails.append("the Bing verification tag is missing from the homepage "
                     "- Bing will unverify the site and we lose the index "
                     "ChatGPT search reads")
    elif _hp.index(_tag) > _hp.index("</head>"):
        fails.append("the Bing verification tag is outside <head>, where no "
                     "crawler looks for it")
    if _hp.count("msvalidate.01") > 1:
        fails.append("the Bing verification tag appears more than once on the "
                     "homepage")
    _elsewhere = [_f.relative_to(OUT) for _f in OUT.rglob("index.html")
                  if _f != OUT / "index.html" and "msvalidate" in _f.read_text()]
    if _elsewhere:
        fails.append("the Bing verification tag has spread to %d other "
                     "page(s), starting with %s - only the root needs it"
                     % (len(_elsewhere), _elsewhere[0]))

# The policy has to describe what the site actually does.
_priv = (OUT / "privacy" / "index.html").read_text()
if "Google Analytics" not in _priv:
    fails.append("the site runs Google Analytics but the privacy policy does "
                 "not mention it")
if "Nobody else" in _priv and "Google Analytics and Cloudflare Web Analytics" not in _priv:
    fails.append('the privacy policy still claims "Nobody else" sees data '
                 "while two analytics providers are running")

# ---- where orders go ----------------------------------------------------
# ORDER_TO used to be a Worker secret, which meant the answer to "where do
# order emails go?" could not be read from the repo at all - and a wrong
# value would be invisible until someone noticed orders had stopped arriving.
# It is an ordinary address, not a credential, so it lives in config now.
# Parsed as plain JSON. Stripping // comments first looked tidier and ate the
# "https://" inside every URL in the file.
_wr = json.loads((ROOT / "wrangler.jsonc").read_text())
_vars = _wr.get("vars", {})
if _vars.get("ORDER_TO") != "orders@numbermyboat.com":
    fails.append("ORDER_TO is %r - order emails would go somewhere else, or "
                 "nowhere" % _vars.get("ORDER_TO"))
if _vars.get("ORDER_BCC") != "hello@aaron.chat":
    fails.append("ORDER_BCC is %r - Aaron would stop being copied on orders"
                 % _vars.get("ORDER_BCC"))
_wj4 = (ROOT / "worker" / "index.js").read_text()
if "bcc: [env.ORDER_BCC]" not in _wj4:
    fails.append("the order email no longer carries a BCC")
# A BCC that is not blind defeats the point: the shop's copy would show a
# second recipient and replies could land on the wrong one.
if re.search(r'to:\s*\[env\.ORDER_TO,\s*env\.ORDER_BCC', _wj4):
    fails.append("ORDER_BCC was moved into the To line - it must stay blind")

# ---- the Stripe webhook -------------------------------------------------
# Without a verified signature this is a public endpoint that marks any order
# paid for anyone who can spell the reference. The signature is the entire
# security model, so each part of it is checked here.
_hook = (ROOT / "worker" / "stripehook.js").read_text()
if "STRIPE_WEBHOOK_SECRET" not in _hook or "crypto.subtle" not in _hook:
    fails.append("the Stripe webhook no longer verifies a signature - it "
                 "would mark any order paid for anyone who posts to it")
if "await request.text()" not in _hook:
    fails.append("the webhook is not reading the RAW body. Stripe signs the "
                 "exact bytes it sent; a re-serialised copy never matches")
# The CALL, not the declaration - "sameBytes" alone is satisfied by the
# function's own signature, which is how four earlier gates in this file
# passed while the thing they guarded had been removed.
if "return sameBytes(await hmacHex(" not in _hook:
    fails.append("signature comparison is no longer constant-time, so a "
                 "signature can be guessed a byte at a time")
if "age > 300" not in _hook:
    fails.append("the webhook lost its timestamp check, so a captured request "
                 "can be replayed forever")
# A Charge does not inherit the PaymentIntent's metadata, so a refund or
# dispute arrives with no ref and has to be matched through the intent id.
# Without this they are silently dropped and the order still reads paid.
if "obj.payment_intent" not in _hook:
    fails.append("refunds and disputes are not matched by payment intent id. "
                 "A Charge does not carry our metadata, so they would arrive "
                 "with no reference and be silently ignored")
if "COALESCE(paid,0)=0" not in _hook:
    fails.append("the paid update is no longer idempotent. Stripe retries, "
                 "and a retry must not do anything a second time")
if 'url.pathname === "/api/stripe-webhook"' not in (ROOT / "worker" / "index.js").read_text():
    fails.append("the webhook route is not mounted")

# ---- server-side glyph outlining ----------------------------------------
# The faces the shop cuts with are licensed Microsoft and Monotype fonts. A
# desktop licence covers installing them and making artwork; it does not cover
# serving the font file to visitors, which is what @font-face does. So the
# font files live in R2 and the worker returns OUTLINES of the characters a
# customer typed. Three things have to stay true for that to hold.
_ol = (ROOT / "worker" / "outline.js").read_text()
if "env.FONTS" not in _ol:
    fails.append("the outliner no longer reads fonts from the private bucket")
_wrangler = json.loads((ROOT / "wrangler.jsonc").read_text())
if not [b for b in _wrangler.get("r2_buckets", [])
        if b.get("binding") == "FONTS"]:
    fails.append("the FONTS bucket binding is gone, so the worker has no "
                 "fonts to outline from")
# The bucket must never be served to the browser. A public route to it would
# be distributing the font software, which is the whole thing this avoids.
for _b in _wrangler.get("r2_buckets", []):
    if _b.get("preview_bucket_name") or _b.get("public"):
        fails.append("the font bucket looks publicly exposed - outlining only "
                     "works as a licence answer while the files stay private")
# Matched on the CALL, not the definition: an earlier version of this gate
# checked for "capHeight(f, upm)" and passed happily against the function
# signature while the call site had been replaced with the OS/2 lookup.
if "const cap = capHeight(f, upm);" not in _ol \
        or 'charToGlyph("H")' not in _ol:
    fails.append("cap height is no longer measured off the capital H. Rye "
                 "declares sCapHeight 363 against a 2048 em when its real H "
                 "is 1550 - trusting the table cuts that face four times "
                 "oversize on a decal whose job is being exactly 3 inches")
if "ALLOWED" not in _ol:
    fails.append("the outliner no longer restricts input characters - a glyph "
                 "that silently drops between preview and cut is the failure "
                 "the proof exists to catch")

# ---- the font inventory page --------------------------------------------
# /fonts-check/ reports which of the site's faces are installed on the shop
# PC. It must load NO web fonts: a face pulled in by the page measures as
# installed when it is not, and the report would be wrong in the direction
# that costs a mis-cut.
_fc = (OUT / "fonts-check" / "index.html")
if not _fc.exists():
    fails.append("the font-check page is gone")
else:
    _fcd = _fc.read_text()
    if "fonts.googleapis.com/css" in _fcd:
        fails.append("/fonts-check/ is loading web fonts, so every face it "
                     "loads reports as installed whether it is or not")
    if 'content="noindex' not in _fcd:
        fails.append("/fonts-check/ is indexable - it is a private tool, not "
                     "a page for search")
    if "What this sends" not in _fcd:
        fails.append("/fonts-check/ no longer tells the reader what it "
                     "collects before they press the button")
    if "queryLocalFonts" not in _fcd or "measureText" not in _fcd:
        fails.append("/fonts-check/ lost one of its two detection paths - the "
                     "API is Chrome-only and the metric check is the fallback")
if "fonts-check" in (OUT / "sitemap.xml").read_text():
    fails.append("/fonts-check/ is in the sitemap")

# ---- the proof promise --------------------------------------------------
# The site promises a proof within twelve hours and says nothing is cut until
# it is approved. Two things make that true, and both have to stay true:
# worker/proof.js has to send it, and no page may still claim the old
# cut-it-the-next-day turnaround that the proof step replaced.
for _q in pages:
    _qd = _q.read_text()
    if "next business day" in _qd:
        fails.append("%s: still promises the old next-business-day turnaround. "
                     "Orders now wait on an approved proof, so that is a "
                     "delivery date we do not meet" % _q.relative_to(OUT))
    if "no proof to approve" in _qd:
        fails.append("%s: still sells 'no proof to approve first' as a "
                     "feature, which is now the opposite of what happens"
                     % _q.relative_to(OUT))
_proof = (ROOT / "worker" / "proof.js").read_text()
if "PROOF_AFTER = 11 * HOURS" not in _proof:
    fails.append("the proof send window is no longer inside the twelve hours "
                 "the site promises")
if _proof.count("NUDGES = [") != 1 or "24 * HOURS, 72 * HOURS, 144 * HOURS" not in _proof:
    fails.append("the proof reminder schedule changed - the site says we "
                 "chase it, and three reminders is what that means")
if "approved_at IS NULL" not in _proof:
    fails.append("the proof cycle no longer excludes approved orders - it "
                 "would email people who already approved")
if "test_mode = 0" not in _proof:
    fails.append("the proof cycle no longer excludes sandbox orders - a test "
                 "order would email a real person asking them to approve it")
# The customer hears from us the moment they order. Without this they get
# nothing until the proof eleven hours later, having just been told on screen
# that an email was on its way - which is exactly how the first real order sat
# unanswered for a working day.
_wjs = (ROOT / "worker" / "index.js").read_text()
if "sendOrderConfirmation" not in _wjs or "sendOrderConfirmation" not in _proof:
    fails.append("orders no longer send the customer a confirmation - the "
                 "screen promises one and the proof is 11 hours away")
if "secure payment link" in design:
    fails.append("the checkout still promises to email a secure payment link. "
                 "Nothing sends one, so that is a promise the site cannot keep")
# Checked on the home page: /design/ has no trust chips of its own.
if "Proofed Before We Cut" not in _homepage:
    fails.append("the proof is no longer one of the headline claims")
if "proofsteps" not in _homepage:
    fails.append("the home page lost the section explaining how the proof "
                 "works - it is the one thing here the marketplace sets do "
                 "not do, so it earns more than a line in a list")
if "env.PROOF_RUN_KEY" not in _wjs:
    fails.append("the manual proof-run endpoint lost its key check - that is "
                 "a button anybody can press to email our customers")

# ---- the phone app layer and the one-CTA rule ---------------------------
# A phone gets ONE way to start an order: the button under the card deck. The
# notification bar, the header button and the sticky drawer are hidden.
#
# Each hide needs an extra selector in front of it, because the base rules for
# .sticky and body.has-sticky sit LATER in style.py and win at equal
# specificity. That has now silently broken a hide twice - once for .heroCta
# and once for .sticky - so it is checked rather than remembered.
for _sel in ("body .top{display:none}", "body .hbtn{display:none}",
             "body .sticky{display:none}",
             "html body.has-sticky{padding-bottom:0}"):
    if _sel not in design:
        fails.append("the phone chrome rule %r is gone or has lost the extra "
                     "selector that makes it outrank the base rule later in "
                     "the sheet - the hide would silently do nothing" % _sel)
if ".appfoot .appcta{display:block" not in design:
    fails.append("the app layer's button lost the `.appfoot` in front of it, "
                 "so .btn{display:inline-block} later in the sheet wins and "
                 "the button stops being full width")

# The app layer must be an OVERLAY, never a replacement for the page. The
# page's own content stays in the DOM and in normal flow underneath, so mobile
# -first indexing still renders the whole page and Skip lands you on it.
_app = [q for q in pages if "id=appshell" in q.read_text()]
if not _app:
    fails.append("no page carries the phone app layer")
for _h in _app:
    _d = _h.read_text()
    if "<main id=main>" not in _d:
        fails.append("%s: the page's own <main> is gone - the app layer is an "
                     "overlay over the page, not a replacement for it"
                     % _h.relative_to(OUT))
    _sh = _d.split("id=appshell")[-1].split("</div></div>")[0]
    _cards = len(_re.findall(r'<li class="appcard', _d))
    _segs = len(_re.findall(r'class="appbar-seg', _d))
    if _cards < 8:
        fails.append("%s: the app layer is down to %d cards - it is the whole "
                     "phone experience" % (_h.relative_to(OUT), _cards))
    if _cards != _segs:
        fails.append("%s: %d app cards but %d progress segments - the bar "
                     "cannot reach every card"
                     % (_h.relative_to(OUT), _cards, _segs))
    _track = _d.split("class=apptrack")[-1].split("</ul>")[0]
    _imgs = _re.findall(r"<img\b[^>]*>", _track)
    _eager = [t for t in _imgs if " src=" in t]
    # Exactly the first card ships a real src. loading=lazy is NOT an
    # acceptable substitute: in a horizontal scroller Chrome treats the whole
    # inline axis as near-viewport and fetches every card anyway. That was
    # measured, not assumed - all of them came down on load.
    if len(_eager) != 2:
        fails.append("%s: %d app images carry a real src, expected 2 (the "
                     "first card's photo and its backdrop) - the rest must "
                     "wait, or the whole deck downloads before a swipe"
                     % (_h.relative_to(OUT), len(_eager)))
    if "loading=lazy" in _track:
        fails.append("%s: the app deck is on loading=lazy, which a horizontal "
                     "scroller ignores" % _h.relative_to(OUT))
    if 'style="background-image' in _track:
        fails.append("%s: an app card is using a CSS background-image - those "
                     "ignore lazy loading entirely"
                     % _h.relative_to(OUT))
    # Ships hidden: with JS off nobody may be handed a full-screen layer with
    # no way out.
    if "<div class=appshell id=appshell hidden" not in _d:
        fails.append("%s: the app layer no longer ships with the `hidden` "
                     "attribute - with JavaScript off it would cover the page "
                     "with no way to dismiss it" % _h.relative_to(OUT))

# THE HOME PAGE ONLY. Anywhere else is an interstitial over content somebody
# searched for: a visitor arriving on the Iowa page wants Iowa, and Google
# treats an intrusive mobile interstitial as a ranking signal - on a site whose
# whole strategy is search. The home page has no specific answer being sought.
if len(_app) != 1 or str(_app[0].relative_to(OUT)) != "index.html":
    fails.append("the phone app layer is on %d pages (%s) - it belongs on the "
                 "home page and nowhere else, or it is a full-screen "
                 "interstitial over content the visitor searched for"
                 % (len(_app), ", ".join(str(q.relative_to(OUT)) for q in _app[:4])))

# Every other page needs its own above-the-fold CTA on a phone, because the
# chrome that used to carry one - notification bar, header button, sticky
# drawer - is hidden there. Without this a state page has no way to order
# until you scroll into the in-content bands.
for _q in pages:
    _qd = _q.read_text()
    if "class=heroF" in _qd and "<div class=heroStart>" not in _qd:
        fails.append("%s: has the wizard but no phone offer card - on a phone "
                     "the header button, notification bar and sticky drawer "
                     "are all hidden, so this page would have no order CTA "
                     "above the fold" % _q.relative_to(OUT))
if ".heroStart .btn{display:block" not in design:
    fails.append("the offer card's button lost the `.heroStart` in front of "
                 "it, so .btn{display:inline-block} later in the sheet wins "
                 "and the button stops being full width")

if "classList.add('appon')" not in design:
    fails.append("the app layer never opens")
if "body.appon{overflow:hidden}" not in design:
    fails.append("the page behind the app layer still scrolls")
if "sessionStorage.setItem('bnsAppSeen'" not in design:
    fails.append("the app layer no longer remembers being dismissed - it "
                 "would reappear on every page of the visit")
_app_src = order_js.split("the phone app layer")[-1].split("the phone order sheet")[0]
if "requestAnimationFrame(" in _app_src:
    fails.append("the app layer's progress bar is behind requestAnimationFrame "
                 "- it freezes permanently if a scroll lands while hidden")
if "markSeg(i)" not in _app_src:
    fails.append("the app scroll handler no longer moves the progress bar")
if ".offsetLeft" in _app_src:
    fails.append("the app layer is measuring with offsetLeft, which is "
                 "relative to the nearest positioned ancestor rather than the "
                 "track - the progress bar would never move")

# The order page must not carry the site-wide sticky CTA. It prints a flat
# registration-number price and links to /design/ - so on /design/ it sits
# under a live total that may read three times as much and points at the page
# you are already on.
if "class=sticky" in design:
    fails.append("the sticky CTA bar is back on the order page - its flat "
                 "price contradicts the wizard's live total, on the one page "
                 "whose job is that total")
elif 'classList.add("has-sticky")' in design:
    # Only reachable with the bar itself gone, so this is the narrower case:
    # no bar, but the body still padded for one.
    fails.append("the order page still reserves footer space for a sticky bar "
                 "it no longer renders")
# Only an increase animates. Flashing the total while it DROPS reads as a
# penalty for deselecting something, which is the opposite of the intent.
if "p>lastTot" not in design.replace(" ", ""):
    fails.append("the total's bump animation lost its direction guard - it "
                 "would flash on price decreases too")
if "lastTot=null" not in design.replace(" ", ""):
    fails.append("lastTot no longer starts null, so merely arriving on the "
                 "page animates the total as though the price went up")

# The order JS is concatenated preview + validate + color_js + order_js, so
# anything in the preview half that caches a window.BNS_* global at IIFE scope
# caches {} - color_js() has not run yet. It fails silently: no error, the
# lookup just always misses. Any such global must be read at call time.
for _hit in _re.finditer(r"var \w+\s*=\s*window\.(BNS_\w+)\s*\|\|", design):
    _g, _cache = _hit.group(1), _hit.start()
    _assign = design.find("window.%s={" % _g)
    if _assign == -1:
        fails.append("the order JS caches window.%s, which is never assigned" % _g)
    elif _cache < _assign:
        fails.append("window.%s is cached at offset %d but not assigned until "
                     "offset %d - the cached copy is always empty; read it at "
                     "call time instead" % (_g, _cache, _assign))

# Only the block sheet is in the head; the other two are injected on first tab
# open. If a category's tab loses its href those faces silently render in
# Helvetica, which is exactly the bug the glyph-outlining work was about.
if "grid-template-columns:repeat(%d,1fr)" % _C.FONT_COLS not in design:
    fails.append("the font grid is no longer %d columns wide, so %d faces "
                 "stops being two clean rows"
                 % (_C.FONT_COLS, len(_C.FONTS)))
# The head must carry the block set plus one specimen face per other tab -
# nothing more. Counting families beats grepping for a function name: it keeps
# holding when the helper is renamed, and it is the number that actually costs
# the customer bandwidth.
_head = _re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis'
                   r'\.com/css2\?[^"]+)"', design)
if not _head:
    fails.append("the order page head has no font stylesheet")
elif not _shape:
    _want = len(_C.FONTS)
    _got = len(_re.findall(r"family=", _head.group(1)))
    if _got != _want:
        fails.append("the head font stylesheet carries %d families, expected %d "
                     "(block set + one tab specimen per other category). Loading "
                     "all %d is ~670KB for a step most orders pick one face from"
                     % (_got, _want, len(_C.FONTS)))

print("%d pages | %d JSON-LD blocks (%d invalid) | %d broken links"
      % (len(pages), blocks, bad_json, len(broken)))
if notes:
    print("\nTO FINISH:"); [print("  -", n) for n in notes]
if fails:
    print("\nFAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
print("all gates pass")
