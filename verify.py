#!/usr/bin/env python3
"""Pre-deploy gate. Runs after every build - a silent build failure shipped a
stale public/ once, so this refuses to pass unless the output is genuinely fresh
and internally consistent."""
import html, json, pathlib, re, subprocess, sys

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
# the seven only apply to some orders, so the markup always carries all seven
# and data-when decides which are shown.
_steps = len(re.findall(r'data-step="\d"', design))
if _steps != 7:
    fails.append("order wizard has %d steps, expected 7" % _steps)
_when = re.findall(r'data-step="(\d)" data-when="(\w*)"', design)
if dict(_when) != {"1": "", "2": "num", "3": "name", "4": "", "5": "", "6": "", "7": ""}:
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

# The outline is the only paid add-on in the form, so the browser and the
# worker must agree on what it costs. Three places have to say 12.
from content import PRICE as _P
if "const OUTLINE_ADD = %d;" % _P["outline"] not in wjs:
    fails.append("worker OUTLINE_ADD disagrees with content.PRICE['outline'] (%d)"
                 % _P["outline"])
if 'd.finish === "outline" || d.outline' not in wjs:
    fails.append("worker priceOf() must read BOTH d.finish and d.outline - it\n                  is called with the raw payload AND with the sanitised order")
_ojs = (ROOT / "engine" / "order.py").read_text()
if "var OUTLINE_ADD=%d;" % _P["outline"] not in _ojs:
    fails.append("order form OUTLINE_ADD disagrees with content.PRICE['outline']")

# Share cards. og_image() derives the URL from the page path before the PNG
# has been rendered - the build wipes public/ first, so the cards are written
# last. That ordering is fine right up until a page path changes and the card
# silently 404s, which Facebook renders as a blank grey box. Check every
# reference resolves, and that nothing is a placeholder-sized file.
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
_cats = {k for k, _l, _h in _C.FONT_CATEGORIES}
_shape = [f for f in _C.FONTS if len(f) != 5]
if _shape:
    # Report and stop here: every check below indexes f[4], so a shape failure
    # would crash verify.py instead of printing something a human can act on.
    fails.append("%d FONTS entries are not 5-tuples (first: %r) - a build-time "
                 "unpack will raise and ship a stale page"
                 % (len(_shape), _shape[0][0]))
else:
    for _f in _C.FONTS:
        if _f[4] not in _cats:
            fails.append("font %r has category %r, which is not in "
                         "FONT_CATEGORIES - its chip renders but no tab ever "
                         "shows it" % (_f[0], _f[4]))
    _lbls = [f[0] for f in _C.FONTS]
    if len(set(_lbls)) != len(_lbls):
        fails.append("two fonts share a label - `font` is submitted by label, "
                     "so the order would be ambiguous")
    if not [f for f in _C.FONTS if f[4] == "block" and f[3]]:
        fails.append("no block-legal face left in the block category - a "
                     "registration number could not be ordered at all")
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

# The order page must not carry the site-wide sticky CTA. It prints a flat
# "$19 Registration numbers" and links to /design/ - so on /design/ it sits
# under a live total that may read $44 and points at the page you are on.
if "class=sticky" in design:
    fails.append("the sticky CTA bar is back on the order page - its flat $19 "
                 "contradicts the wizard's live total, on the one page whose "
                 "job is that total")
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
for _key, _lbl, _h in _C.FONT_CATEGORIES:
    if 'data-cat="%s" data-href="https://fonts.googleapis.com' % _key not in design:
        fails.append("the %s tab has no data-href - its faces would never "
                     "load and would render in a fallback face" % _key)
if "loadedCats[cat]) return" not in design:
    fails.append("the font stylesheet loader lost its once-only guard - every "
                 "tab click would append another <link>")
# The head must carry the block set plus one specimen face per other tab -
# nothing more. Counting families beats grepping for a function name: it keeps
# holding when the helper is renamed, and it is the number that actually costs
# the customer bandwidth.
_head = _re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis'
                   r'\.com/css2\?[^"]+)"', design)
if not _head:
    fails.append("the order page head has no font stylesheet")
elif not _shape:
    _want = len([f for f in _C.FONTS if f[4] == "block"]) + len(_C.FONT_CATEGORIES) - 1
    _got = len(_re.findall(r"family=", _head.group(1)))
    if _got != _want:
        fails.append("the head font stylesheet carries %d families, expected %d "
                     "(block set + one tab specimen per other category). Loading "
                     "all %d is ~670KB for a step most orders pick one face from"
                     % (_got, _want, len(_C.FONTS)))

print("%d pages | %d JSON-LD blocks (%d invalid) | %d broken links"
      % (len(pages), blocks, bad_json, len(broken)))
if fails:
    print("\nFAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
print("all gates pass")
