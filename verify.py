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
for _val, _base, _p, _f, _k, _label in _KINDS:
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
# which falls through to the $19 base: a "Both" order at 6" with an outline is
# $69 and would have been charged $19. Undercharging is silent, so it is
# gated rather than remembered.
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
                 "so a refund or dispute starts from a row saying only $19.00")
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
if fails:
    print("\nFAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
print("all gates pass")
