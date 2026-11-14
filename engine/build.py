#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site builder for Number My Boat."""
import json, os, pathlib, re, sys, html, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from content import (SITE, PRICE, UPGRADES, PRODUCTS, BOAT_TYPES, TOOLS, GUIDES,
                     INDEXNOW_KEY,
                     STATES, FONTS, FONT_NAMES, COLORS, FAQ_HOME,
                     LOCAL_TOWNS, LOCAL_WATERS, head_fonts_href, STRIPE_PK,
                     VESSEL_PREFIX, POSTAL_MISTAKE, POSTAL_TO_VESSEL,
                     ORDER_COLORS)
from style import CSS
import namegen as NG
from state_data import (USCG_FLEET, USCG_SOURCE, USCG_URL,
                        USCG_NATIONAL, STATE_ACCENT, state_badge)
from state_waters import WATERS
from og_meta import META as OG_META, state_meta, boat_type_meta
from sharebox import block as share_block
import order as O
import mockpay as MP
import preview as PV
import shared_js as SH
import tools as T
import copy_blocks as CB

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
URL = os.environ.get("SITE_URL", SITE["url"]).rstrip("/")
TODAY = os.environ.get("BUILD_DATE", datetime.date.today().isoformat())
B = SITE["brand"]
e = html.escape
PAGES = []
# Paths that asked not to be indexed; kept out of sitemap.xml. Populated by
# write() from the page's own markup.
NOINDEX = set()

def U(p): return URL + p

# The mark is a number sign whose crossbars are water. "#" is literally the
# word "number" and the waves are the boat, so one glyph carries both halves
# of the name rather than parking two pictures next to each other. The waves
# are the same scallop the old logo used, which keeps a thread back to it.
#
# Two colors, four strokes, and it still reads at 16px - which the old
# "19"-in-a-box did not, and which matters because a favicon is where most
# people meet a logo first.
#
# The wordmark is set in Archivo Black: the same face the shop cuts as "Block"
# for registration numbers, and already loaded for the order form, so it costs
# no extra request.
LOGO_MARK = (
 '<rect width="32" height="32" rx="7" fill="#0e3a52"/>'
 '<path d="M12.8 5 9.8 27M21.8 5 18.8 27" stroke="#fff" stroke-width="2.9" '
 'stroke-linecap="round"/>'
 '<path d="M4 12.2c4 0 4 -2.2 8 0c4 0 4 2.2 8 0c4 0 4 -2.2 8 0" stroke="#5fc4f5" '
 'stroke-width="2.8" fill="none" stroke-linecap="round"/>'
 '<path d="M4 20.4c4 0 4 -2.2 8 0c4 0 4 2.2 8 0c4 0 4 -2.2 8 0" stroke="#5fc4f5" '
 'stroke-width="2.8" fill="none" stroke-linecap="round"/>')

WORDMARK = ('<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">'
            + LOGO_MARK + '</svg>')

ICONS = {
 "numbers":'<path d="M5 9h14M5 15h14M10 4l-2 16M16 4l-2 16" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round"/>',
 "letter":'<path d="M4 19L12 5l8 14M7.5 14h9" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
 "name":'<path d="M3 17c3 0 3-2 6-2s3 2 6 2 3-2 6-2" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round"/><path d="M6 11h12M8 7h8" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
 "decal":'<circle cx="12" cy="12" r="7.6" stroke="currentColor" stroke-width="1.9" fill="none"/><path d="M9 12.4l2.2 2.2L15.4 10" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
 "motor":'<path d="M9 4h6v5l3 4v5a2 2 0 01-2 2H8a2 2 0 01-2-2v-5l3-4z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M10 15h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
 "carpet":'<rect x="3.5" y="5.5" width="17" height="13" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M7 9.5h10M7 12.5h10M7 15.5h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 "port":'<path d="M12 4v16M6 11h12M8.5 7.5h7" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round"/>',
 "domed":'<path d="M4 17a8 8 0 0116 0z" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linejoin="round"/><path d="M3 20h18" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
 "stripe":'<path d="M3 8h18M3 13h18M3 17h12" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
 "tool":'<path d="M14.5 4.5a4.5 4.5 0 01-5.8 5.8L4 15v5h5l4.7-4.7a4.5 4.5 0 015.8-5.8l-3.3 3.3-2.4-2.4z" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/>',
 "state":'<path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.5" stroke="currentColor" stroke-width="1.8" fill="none"/>',
 "guide":'<path d="M5 4.5h9a3 3 0 013 3v12H8a3 3 0 00-3 3z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M8.5 9h6M8.5 12.5h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
}
# ---------------------------------------------------------------- imagery
# Generated illustrative shots. The mapping and the captions live in
# media/captions.json; this is the render side.
#
# CAPTIONS DESCRIBE THE SPEC, NEVER A NAMED CUSTOMER. See media/CAPTIONS.md -
# a generated image captioned as somebody's boat is fabricated social proof.
IMAGES = {}
_cap = ROOT / "media" / "captions.json"
if _cap.exists():
    for _r in json.loads(_cap.read_text()):
        IMAGES[_r["id"]] = _r

# Which shot leads which page.
PAGE_IMAGE = {
    "/boat-registration-numbers/": "AL-01",
    "/boat-lettering/":            "AL-03",
    "/for/jon-boats/":             "AL-04",
    "/for/jet-skis-and-pwc/":      "AL-05",
    "/for/kayaks-and-canoes/":     "AL-06",
    "/for/pontoon-boats/":         "AL-07",
    "/for/sailboats/":             "AL-08",
    "/for/bass-boats/":            "AL-10",
    "/guides/how-to-apply-boat-lettering/": "AL-09",
    "/guides/where-to-put-boat-registration-numbers/": "GD-1",
    "/guides/how-to-remove-boat-lettering/":           "GD-2",
    "/guides/boat-registration-number-rules/":         "GD-4",
    "/registration-numbers/iowa/":      "AL-01",
    "/registration-numbers/michigan/":  "AL-02",
    "/registration-numbers/wisconsin/": "AL-04",
    "/registration-numbers/california/":"AL-05",
    "/registration-numbers/texas/":     "AL-07",
    "/registration-numbers/missouri/":  "AL-10",
    "/registration-numbers/minnesota/": "AL-06",
    # The ST-* set: one hull per state, shot in that state's own landscape.
    "/registration-numbers/alabama/":        "ST-AL",
    "/registration-numbers/florida/":        "ST-FL",
    "/registration-numbers/georgia/":        "ST-GA",
    "/registration-numbers/illinois/":       "ST-IL",
    "/registration-numbers/indiana/":        "ST-IN",
    "/registration-numbers/louisiana/":      "ST-LA",
    "/registration-numbers/north-carolina/": "ST-NC",
    "/registration-numbers/new-york/":       "ST-NY",
    "/registration-numbers/ohio/":           "ST-OH",
    "/registration-numbers/pennsylvania/":   "ST-PA",
    "/registration-numbers/south-carolina/": "ST-SC",
    "/registration-numbers/tennessee/":      "ST-TN",
    "/registration-numbers/virginia/":       "ST-VA",
    "/registration-numbers/washington/":     "ST-WN",
    # Hubs and the remaining standalone pages.
    "/registration-numbers/": "HB-2",
    "/for/":                  "HB-1",
    "/guides/":               "HB-4",
    "/boat-lettering-waterloo-cedar-falls/": "HB-5",
    "/warranty/":             "AC-3",
    "/shipping-and-returns/": "AC-2",
    "/tools/":                "AC-1",
}

# Images paired to a page's prose sections, in document order. Short lists are
# fine - sections past the end of the list render full width.
PAGE_SECTIONS = {
    "/boat-registration-numbers/": ["PR-1", "PR-6", "GD-1"],
    "/boat-lettering/":            ["PR-5", "PR-4", "PR-3"],
    "/guides/where-to-put-boat-registration-numbers/": ["GD-1", "AL-01", "AL-04"],
    "/guides/how-to-remove-boat-lettering/":           ["GD-2"],
    "/guides/boat-registration-number-rules/":         ["GD-4", "PR-3"],
    "/guides/boat-lettering-fonts/":                   ["PR-5", "AL-01"],
    "/guides/best-vinyl-for-boat-lettering/":          ["AL-06", "AL-02"],
    "/guides/documented-vessel-name-and-hailing-port/":["AL-08"],
    "/guides/boat-registration-number-cost/":          ["PR-1"],
    "/guides/how-to-apply-boat-lettering/":            ["AL-09"],
}

DISCLOSURE = ""


def figure(img_id, sizes="(min-width:900px) 46vw, 100vw", cls="shot", lazy=True):
    """One responsive <picture> with its spec caption."""
    m = IMAGES.get(img_id)
    if not m:
        return ""
    alt = html.unescape("%s. %s." % (m["caption"], m["sub"]))
    return (
      '<figure class="%s">'
      '<picture>'
      '<source type="image/webp" srcset="/assets/img/%s-800.webp 800w,'
      '/assets/img/%s-1400.webp 1400w" sizes="%s">'
      '<img src="/assets/img/%s-800.jpg" '
      'srcset="/assets/img/%s-800.jpg 800w,/assets/img/%s-1400.jpg 1400w" '
      'sizes="%s" alt="%s" width="1400" height="933"%s>'
      '</picture>'
      '<figcaption><b>%s</b><span>%s</span></figcaption></figure>'
      % (cls, img_id, img_id, sizes, img_id, img_id, img_id, sizes, e(alt),
         ' loading="lazy" decoding="async"' if lazy else '',
         m["caption"], m["sub"]))


def steps_strip(ids, heading="The whole job, start to finish"):
    """The how-to sequence. One boat, seven frames, in order.

    Reference-image consistency is the entire reason this is on Nano Banana
    Pro: the same hull, trailer, gravel and overcast sky in every frame.
    """
    cards = "".join(figure(i, sizes="(min-width:900px) 31vw, 92vw", cls="gshot")
                    for i in ids)
    return ('<section class=soft><div class=w><h2>%s</h2>'
            '<div class=gallery steps>%s</div>%s</div></section>'
            % (heading, cards, DISCLOSURE))


class Band:
    """Alternating section backgrounds, counted per page.

    Product pages were running three white sections together because each
    builder decided its own background in isolation. One counter per page
    means the stripe stays honest no matter how many prose rows a page has.
    """
    def __init__(self, start=0):
        self.i = start

    def cls(self):
        c = "soft" if self.i % 2 else ""
        self.i += 1
        return c

    def open(self, extra=""):
        c = " ".join(x for x in (self.cls(), extra) if x)
        return '<section%s>' % (' class="%s"' % c if c else "")


def split_h2(body):
    """Break a prose body into (heading, html) sections at each <h2>.

    Anything before the first <h2> comes back under an empty heading so a
    leading note or rule block is not lost.
    """
    import re as _re
    parts = _re.split(r"(<h2>.*?</h2>)", body)
    out, lead = [], parts[0].strip()
    if lead:
        out.append(("", lead))
    for i in range(1, len(parts), 2):
        out.append((parts[i], parts[i + 1] if i + 1 < len(parts) else ""))
    return out


def alternating(body, img_ids, band):
    """Lay prose sections out beside images, alternating sides down the page.

    Sections are paired with images in order; once the images run out the
    remaining sections render full width rather than stretching one picture
    over three topics. Below 900px every row stacks image-then-text, because
    a zigzag on a phone is just a column with inconsistent reading order.
    """
    secs = split_h2(body)
    out, used = [], 0
    for head, html in secs:
        img = img_ids[used] if used < len(img_ids) and head else None
        if img and IMAGES.get(img):
            side = "r" if used % 2 else "l"          # first image on the left
            inner = ('<div class="altrow %s"><div class=altimg>%s</div>'
                     '<div class="alttext prose">%s%s</div></div>'
                     % (side, figure(img, sizes="(min-width:900px) 44vw, 100vw",
                                     cls="shot"), head, html))
            used += 1
        else:
            inner = ('<div class="altrow full"><div class="alttext prose">%s%s</div>'
                     '</div>' % (head, html))
        out.append('%s<div class=w>%s</div></section>'
                   % (band.open("altband"), inner))
    if used and out:
        out[-1] = out[-1].replace("</div></section>",
                                  DISCLOSURE + "</div></section>")
    return "".join(out)


def lead_figure(path, band=None, sizes="(min-width:900px) 70vw, 100vw"):
    """The lead image for a page that is not a product, state or guide.

    Returns an empty string when the page has no mapping, so a builder can
    call it unconditionally.
    """
    img = PAGE_IMAGE.get(path)
    if not img or not IMAGES.get(img):
        return ""
    inner = figure(img, sizes=sizes, cls="shot wide") + DISCLOSURE
    if band is None:
        return '<div style="margin:0 0 24px">%s</div>' % inner
    return '%s<div class=w>%s</div></section>' % (band.open(), inner)


def gallery(ids, heading="What it looks like on the boat"):
    cards = "".join(figure(i, sizes="(min-width:900px) 31vw, 92vw", cls="gshot")
                    for i in ids)
    return ('<section class=soft><div class=w><h2>%s</h2>'
            '<div class=gallery>%s</div>%s</div></section>'
            % (heading, cards, DISCLOSURE))


def icon(k):
    return ('<span class=icw><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>'
            % ICONS.get(k, ICONS["decal"]))

# ------------------------------------------------------------------- shell
TITLE_SUFFIXES = (" | " + B, "")

def _title(t):
    for sfx in TITLE_SUFFIXES:
        if len(t) + len(sfx) <= 60: return t + sfx
    return t[:60]

# Facebook caches a share image BY URL and will not re-fetch it when the file
# changes: "Use a new URL for the new image or the image won't be updated."
# Every redesign therefore has to ship under a new filename, and old ones stay
# on disk so previously-shared links keep rendering.
OG_VERSION = "v2"


def _og_ext(path):
    """.jpg for a photo card, .png for a typographic one.

    media/og_lines.has_photo() is the single source both this and the renderer
    consult, so the extension in the tag and the file on disk cannot drift.
    """
    try:
        sys.path.insert(0, str(ROOT / "media"))
        import og_lines
        og_lines.register_states(STATES)
        return ".jpg" if og_lines.has_photo(path) else ".png"
    except Exception:
        return ".png"


def og_image(path):
    """The share card for a page.

    Computed from the path rather than looked up, so head() can emit the URL
    before media/og.py has rendered the file - the build wipes public/ first,
    so the cards are written near the end. verify.py checks every referenced
    card actually exists, which is what stops that ordering from biting.
    """
    slug = path.strip("/").replace("/", "-") or "home"
    # Internal pages (leading underscore) are noindex and never shared, so
    # they borrow the home card rather than burn a render on one nobody sees.
    # Internal and transactional pages borrow the home card. /proof/ is a
    # private page reached only from an email link; rendering it a share card
    # would be a card for something nobody can open, and /brand/ is the logo
    # library - a page for Aaron and Ryan, never posted anywhere.
    if slug.startswith("_") or slug in ("proof", "fonts-check", "brand"):
        slug, path = "home", "/"
    return "/assets/og/%s-%s%s" % (slug, OG_VERSION, _og_ext(path))


def og_copy(path, title, desc):
    """Social title and description for a page.

    Falls back to the page's own, because a short honest title beats a
    hand-written one that nobody kept up to date.
    """
    if path in OG_META:
        return OG_META[path]
    m = re.match(r"^/registration-numbers/([a-z-]+)/$", path)
    if m:
        st = next((x for x in STATES if x["slug"] == m.group(1)), None)
        if st:
            return state_meta(st["name"], st["ab"])
    m = re.match(r"^/for/([a-z-]+)/$", path)
    if m:
        bt = next((x for x in BOAT_TYPES if x["slug"] == m.group(1)), None)
        if bt:
            return boat_type_meta(bt["nav"])
    return html.unescape(title)[:60], html.unescape(desc)[:110]


# Google Analytics 4. Loaded on every page, but only on the real domain:
# gated on location.hostname so the workers.dev staging copy and any local
# build stay out of the property. Without that gate every deploy test and
# every preview click lands in the same reports as real customers, and the
# numbers quietly stop meaning anything.
#
# Google Signals and ad personalisation are BOTH OFF. The privacy policy says
# "we do not run advertising trackers", and that stays true: this measures
# traffic and nothing is handed to the ad products. Turning either on is a
# policy change, not a settings change.
# The height surcharges, named once. The order form renders these into its
# data-add attributes and the worker has the same table; verify.py gates all
# three against each other.

GA_ID = "G-P2QBX2TXPX"
GA_HOST = "numbermyboat.com"

GA_TAG = (
 '<script>if(location.hostname==="%(host)s"||location.hostname==="www.%(host)s"){'
 'var s=document.createElement("script");s.async=true;'
 's.src="https://www.googletagmanager.com/gtag/js?id=%(id)s";'
 'document.head.appendChild(s);'
 'window.dataLayer=window.dataLayer||[];'
 'function gtag(){dataLayer.push(arguments);}window.gtag=gtag;'
 'gtag("js",new Date());'
 'gtag("config","%(id)s",{allow_google_signals:false,'
 'allow_ad_personalization_signals:false});}</script>'
 % {"id": GA_ID, "host": GA_HOST})

# ------------------------------------------------- Cloudflare Web Analytics
#
# A SECOND, INDEPENDENT COUNT. Not redundancy for its own sake: GA4 is the
# single most blocked script on the web, so the one number we have for "how
# many people came" is systematically short by an unknown amount, and the
# amount differs by audience. Boat owners on a phone at a marina are not the
# same blocking population as a desktop office visitor. Two counts that
# disagree by a stable ratio tell you the ratio; one count tells you nothing
# about what it is missing.
#
# It is also the count that survives GA going away - a blocked script, a
# consent change, a property misconfigured. Having the other one already
# running for months is worth more than standing it up afterwards.
#
# COOKIELESS, which is why it needs no banner and no consent gate. Cloudflare
# Web Analytics sets no cookie, stores no identifier and does not fingerprint;
# it samples the Navigation Timing and Core Web Vitals the browser already
# has. That is a real difference from GA4, not a marketing line, and it is the
# reason this can ship without touching the privacy page.
#
# THE TOKEN IS PUBLIC. It identifies a site, not an account, and it is visible
# in the page source of every site using this - so it belongs in the repo next
# to GA_ID rather than in a Worker secret. Treating it as a secret would only
# mean nobody could rebuild the site without one.
#
# Get it: Cloudflare dashboard -> the numbermyboat.com account -> Analytics &
# Logs -> Web Analytics -> Add a site -> numbermyboat.com. Copy the token out
# of the snippet it shows (the value of data-cf-beacon's "token") and paste it
# below. Do NOT use the "Automatic Setup" toggle: it injects the beacon at the
# edge for proxied origins, it does not reliably reach a Worker's own
# responses, and an injection we cannot see in the build is one verify.py
# cannot gate.
CF_BEACON_TOKEN = "8bcafbc68cba489581f4d474b1fcb6a6"

# ------------------------------------------------- Bing Webmaster Tools
#
# Google is verified by a DNS TXT record on the apex, which is the better
# method - it covers every subdomain and no rebuild can break it. Bing's
# equivalent would be a CNAME; this is the meta-tag method instead, because
# that is what Aaron had in hand.
#
# WHY BING IS WORTH THE TAG even though it is a rounding error of search
# share: its index is what ChatGPT search reads. This site is built to be
# quoted by answer engines - the guides, the tools and llms.txt all exist for
# that - and being absent from the index those engines read is a different
# kind of problem from being ranked badly in it.
#
# HOMEPAGE ONLY. Bing verifies by fetching the root URL and looking for this
# tag, so that is the only page that needs it, and 55 copies of a string
# nobody reads is 55 copies. The fragility that buys - someone changes how /
# is built, the tag silently vanishes, and Bing quietly unverifies the site
# months later with no email anyone reads - is covered by a gate in verify.py
# rather than by hoping.
BING_VERIFY = "F6596C0CCF272F32D4D68CF7A018E9A4"
BING_TAG = ('<meta name="msvalidate.01" content="%s">' % BING_VERIFY
            if BING_VERIFY else "")

# Host-gated for exactly the reason GA is: the staging worker at
# boatdecals.aironz.workers.dev serves these same pages, and a beacon that
# fires there mixes our own test traffic into the customer numbers. The
# staging site is the one place every page gets loaded by someone who is never
# going to buy anything.
#
# Built by script rather than written as a plain <script src> tag so that the
# hostname check can wrap it at all. A dynamically created script is async by
# default, which is what the beacon wants anyway - it reports after load.
CF_TAG = ('' if not CF_BEACON_TOKEN else
 '<script>if(location.hostname==="%(host)s"||location.hostname==="www.%(host)s"){'
 'var b=document.createElement("script");b.defer=true;'
 'b.src="https://static.cloudflareinsights.com/beacon.min.js";'
 'b.setAttribute("data-cf-beacon",JSON.stringify({token:"%(tok)s"}));'
 'document.head.appendChild(b);}</script>'
 % {"tok": CF_BEACON_TOKEN, "host": GA_HOST})

def head(title, desc, path, schema, noindex=False):
    canon = U(path)
    robots = ('<meta name="robots" content="noindex,follow">' if noindex else
      '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">')
    _ot, _od = og_copy(path, title, desc)
    # Verification tags go on the root only - that is the URL Bing fetches.
    _verify = BING_TAG if path == "/" else ""
    _img = U(og_image(path))
    # Guides are articles; everything else is a page of the shop.
    _ogtype = "article" if path.startswith("/guides/") and path != "/guides/" else "website"
    _oalt = _ot
    _imgtype = "image/jpeg" if _img.endswith(".jpg") else "image/png"
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
%s
<meta property="og:type" content="%s"><meta property="og:title" content="%s">
<meta property="og:description" content="%s"><meta property="og:url" content="%s">
<meta property="og:site_name" content="%s"><meta property="og:locale" content="en_US">
<meta property="og:image" content="%s"><meta property="og:image:secure_url" content="%s">
<meta property="og:image:type" content="%s">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630"><meta property="og:image:alt" content="%s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s"><meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s"><meta name="twitter:image:alt" content="%s">
<meta name="theme-color" content="#0e3a52">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>%s</style>
<script type="application/ld+json">%s</script>
%s
</head><body>
<a class="skip" href="#main">Skip to the order form</a>""" % (
    e(_title(html.unescape(title))), e(html.unescape(desc)), canon, robots,
    _ogtype, e(_ot), e(_od), canon, e(B),
    _img, _img, _imgtype, e(_oalt), e(_ot), e(_od), _img, e(_oalt),
    CSS, json.dumps(schema, separators=(',', ':')),
    # Internal pages are not customer journeys and would skew the reports:
    # /brand/ is a file library, /proof/ is one customer's own order. Both
    # counts follow the same rule, or the two reports cover different sites
    # and the comparison between them means nothing.
    _verify + ("" if noindex else GA_TAG + CF_TAG))

# The four headline claims, in one place. proof_band() spells each one out;
# the hero badges are the short form. Both read from here so they cannot drift.
# "Proofed Before We Cut" earns its place on the strength of what goes wrong
# without it: a registration number is worthless if one character is wrong, and
# the customer is the only person who can check it against their card. It also
# replaces the speed claim the proof step cost us - the honest trade is a day
# for a second pair of eyes, and that is the trade to sell.
# The price chip. It appears in FEATURES, in FEATURE_SUB's keys and in a
# dozen per-page `trust=[...]` lists, so it is built once from the one price
# table. Eight copies of the figure used to live in this file.
PRICE_CHIP = "$%d a Pair" % PRICE["numbers"]

FEATURES = [PRICE_CHIP, "Proofed Before We Cut", "Marine Vinyl",
            "Meets 33 CFR 173.27"]
FEATURE_SUB = {
    PRICE_CHIP:
        "One for each side of the hull, pre-spaced on a single sheet. "
        "Shipping included.",
    "Proofed Before We Cut":
        "We email your exact lettering within 12 hours. Nothing goes to the "
        "plotter until you have checked it and said yes.",
    "Marine Vinyl":
        "Marine film built for sun, salt and spray &mdash; not the craft stock "
        "the cheap sets use.",
    "Meets 33 CFR 173.27":
        "3-inch characters, pre-spaced to the federal display rule every state "
        "enforces. Pick a decorative face and we say so before you pay "
        "&mdash; the rule asks for plain block characters.",
}

# Header nav. Labels are what customers say ("Boat Numbers"), not what the
# product pages are titled - the hrefs still point at the canonical slugs.
NAV_MAIN = [
    ("Boat Numbers", "/boat-registration-numbers/"),
    ("Boat Letters", "/boat-lettering/"),
    ("Gallery",      "/gallery/"),
    ("Pricing",      "/pricing/"),
    ("By State",     "/registration-numbers/"),
]
# The dropdown's parent already links to /guides/, so a "Guides" child under
# it was a duplicate - two rows of the nav pointing at the same page.
# The dropdown's own parent links to /guides/, so no child may point there
# too - that was two rows of the nav going to the same page.
NAV_HELP = [
    ("Free tools",  "/tools/"),
    ("Warranty",    "/warranty/"),
    ("Shipping",    "/shipping-and-returns/"),
    ("Contact",     "/contact/"),
]

def topbar():
    return ('<div class=top><div class=w>'
            '<span><strong>$%d a pair</strong> &middot; both sides '
            '&middot; free shipping proof in 12 hours</span>'
            # The link is hidden on a phone: the header button sits directly
            # under it saying the same thing, and the point of this pass was to
            # stop offering the same action four times on one screen.
            '<span>Cut in %s, %s<span class=topcta> &middot; '
            '<a href="/design/" style="color:#fff">Start your order</a></span></span>'
            '</div></div>'
            % (PRICE["numbers"], SITE["city"], SITE["region"]))

def header():
    """Header nav.

    The About group opens on :hover and :focus-within, so it works for mouse,
    keyboard and touch without any JavaScript - and "About" itself stays a real
    link rather than becoming a button you cannot follow.

    Below 900px the links collapse behind a toggle; that is the only part that
    needs JS, and the footer carries every link if it fails.
    """
    main = "".join('<a href="%s">%s</a>' % (href, lbl) for lbl, href in NAV_MAIN)
    sub = "".join('<a href="%s">%s</a>' % (href, lbl) for lbl, href in NAV_HELP)
    return ('<header><div class=w>'
            '<a class=brand href="/">%s<span>NumberMy<br>Boat<b>.com</b></span></a>'
            '<button type=button class=menubtn id=menubtn aria-expanded="false" '
            'aria-controls="nav" aria-label="Menu">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>'
            '<nav id=nav>%s'
            '<span class=navgroup><a class=navtop href="/guides/">Help'
            '<svg class=caret viewBox="0 0 12 12" aria-hidden="true">'
            '<path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" stroke-width="1.7" '
            'fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></a>'
            '<span class=navmenu>%s</span></span>'
            '</nav>'
            '<a class=hbtn href="/design/">Start your order</a></div></header>'
            % (WORDMARK, main, sub))

def sticky(label="Registration numbers", price=19):
    return ('<div class=sticky><span class=sp>$%d<em>%s</em></span>'
            '<a class=btn href="/design/">Start your order</a></div>'
            % (price, e(html.unescape(label))))

# The cards, in order. A photo card is an id from IMAGES; a fact card is a
# (kicker, headline, line) triple. Interleaved so the deck reads as a tour of
# the work rather than a slideshow with adverts bolted on the end.
APP_CARDS = [
    "AL-01",
    ("What it costs", "$%d a pair" % PRICE["numbers"],
     "Both sides, pre-spaced on one sheet, shipping included. The price is on "
     "the page - you do not have to build a design to see it."),
    "AL-02",
    ("The law", "Legal in all 50 states",
     "3-inch plain block characters, contrasting with the hull, on the forward "
     "half, both sides. That is 33 CFR 173.27, and every set we cut meets it."),
    "AL-10",
    "AL-03",
    ("Your boat", "Any surface",
     "Gelcoat, bare aluminium, a textured pontoon rail, rotomoulded plastic. "
     "High-tack film for the awkward ones, free, no upcharge."),
    "AL-04",
    "AL-07",
    ("No typos", "You approve it before we cut",
     "Within twelve hours we email your exact lettering. Check it against "
     "your registration card, tap approve, and it is cut, packed and posted "
     "within 1-2 business days. Nothing is cut before you say so."),
    "AL-05",
    "AL-06",
    "AL-08",
]


def app_shell():
    """The phone experience: a full-screen card deck, not a hero element.

    This is an overlay over the page, never a replacement for it. The page's
    own content stays in the DOM and in normal flow underneath - nothing is
    `display:none`-d away - so what a crawler renders on mobile is still the
    whole page, and dismissing the deck drops you straight onto it.
    """
    cards = []
    for i, c in enumerate(APP_CARDS):
        first = " src" if i == 0 else " data-src"
        if isinstance(c, tuple):
            kick, head, line = c
            cards.append(
                '<li class="appcard fact"><div class=factbody>'
                '<span class=factkick>%s</span><strong>%s</strong><p>%s</p>'
                '</div></li>' % (kick, head, line))
            continue
        m = IMAGES.get(c)
        if not m:
            continue
        alt = html.unescape("%s. %s." % (m["caption"], m["sub"]))
        cards.append(
            '<li class="appcard%s">'
            '<img class=appbg%s="/assets/img/%s-800.jpg" alt="" '
            'aria-hidden=true decoding=async>'
            '<picture>'
            '<source type="image/webp"%s="/assets/img/%s-800.webp">'
            '<img%s="/assets/img/%s-800.jpg" alt="%s" width="1400" '
            'height="933" decoding=async>'
            '</picture>'
            '<div class=appcap><b>%s</b><em>%s</em></div>'
            '</li>'
            % ("" if i == 0 else " pending",
               " src" if i == 0 else " data-src", c,
               " srcset" if i == 0 else " data-srcset", c,
               " src" if i == 0 else " data-src", c, e(alt),
               m["caption"], m["sub"]))
    bars = "".join('<i class="appbar-seg%s"></i>' % (" on" if i == 0 else "")
                   for i in range(len(cards)))
    return (
        '<div class=appshell id=appshell hidden aria-label="Our work">'
        '<div class=apptop>'
        '<div class=appprog id=appprog>%s</div>'
        '<button type=button class=appskip id=appskip>Skip</button>'
        '</div>'
        '<ul class=apptrack id=apptrack>%s</ul>'
        '<div class=appfoot>'
        '<button type=button class="btn lg sheetgo appcta">Start your order</button>'
        '<div class=appn>$%d a pair &middot; both sides &middot; free shipping</div>'
        '</div>'
        '</div>' % (bars, "".join(cards), PRICE["numbers"]))


def hero(h1, sub, trust=None, right="", badge=None, cta2=None):
    t = trust or list(FEATURES)
    bd = '<div class=badge>%s</div>' % badge if badge else ""
    # Three grid areas, not two columns. On a phone that puts the wizard
    # directly under the headline instead of below a screenful of copy;
    # on desktop the copy stacks in the left column beside it.
    # The phone's one above-the-fold CTA. The home page opens on the
    # full-screen app layer instead, which sits over the top of this - and
    # Skip lands the visitor right here.
    start = ('<div class=heroStart>'
             '<div class=heroStartP><b>$%d</b><em>a pair &middot; both sides</em></div>'
             '<button type=button class="btn lg sheetgo">Start your order</button>'
             '<div class=heroStartN>Free shipping &middot; proof emailed '
             'within 12 hours</div></div>') % PRICE["numbers"] if right else ""
    sheetbar = ('<div class=sheetbar><span>Start your order</span>'
                '<button type=button class=sheetx aria-label="Close">'
                'Close</button></div>') if right else ""
    return ('<section class=hero><div class="w herogrid">'
            '<div class=heroA>%s<h1>%s</h1></div>'
            '<div class=heroF role=dialog aria-modal=false '
            'aria-label="Start your order">%s%s</div>%s'
            '<div class=heroB><p class=sub>%s</p><div class=trust>%s</div>'
            '<div class=btnrow><a class="btn lg heroCta" href="/design/">Start your order</a>'
            '<a class="btn ghost" href="%s">%s</a></div></div>'
            '</div></section>'
            % (bd, h1, sheetbar, right, start, sub,
               "".join("<span>%s</span>" % x for x in t),
               (cta2 or ("/pricing/", "See all prices"))[0],
               (cta2 or ("/pricing/", "See all prices"))[1]))

def faq_block(items, heading="Questions people actually ask", band=None):
    if not items: return ""
    rows = "".join(
        '<details><summary>%s</summary><div class=ans><p>%s</p></div></details>'
        % (e(html.unescape(q)), a) for q, a in items)
    # Participate in the page stripe when one is running, so the FAQ does not
    # land on the same color as the section above it.
    open_tag = band.open() if band else '<section class=soft>'
    return ('%s<div class=w><h2>%s</h2>'
            '<div class=faq style="margin-top:18px">%s</div></div></section>'
            % (open_tag, heading, rows))

def footer():
    pl = "".join('<li><a href="/%s/">%s</a></li>' % (p["slug"], p["nav"]) for p in PRODUCTS)
    tl = "".join('<li><a href="/tools/%s/">%s</a></li>' % (t["slug"], t["nav"]) for t in TOOLS)
    bl = "".join('<li><a href="/for/%s/">%s</a></li>' % (b["slug"], b["nav"]) for b in BOAT_TYPES)
    gl = "".join('<li><a href="/guides/%s/">%s</a></li>' % (g["slug"], g["nav"]) for g in GUIDES[:6])
    return ('<footer><div class=w><div class=fgrid>'
            '<div><h4>Products</h4><ul>%s</ul></div>'
            '<div><h4>Free tools</h4><ul>%s</ul></div>'
            '<div><h4>By boat</h4><ul>%s</ul></div>'
            '<div><h4>Guides</h4><ul>%s</ul></div>'
            '<div><h4>Shop</h4><ul>'
            '<li><a href="/pricing/">Pricing</a></li>'
            '<li><a href="/registration-numbers/">Numbers by state</a></li>'
            '<li><a href="/boat-lettering-waterloo-cedar-falls/">Local pickup</a></li>'
            '<li><a href="/contact/">Contact</a></li>'
            '<li><a href="/warranty/">Warranty &amp; guarantee</a></li>'
            '<li><a href="/shipping-and-returns/">Shipping &amp; returns</a></li>'
            '</ul></div></div>'
            '<div class=nap><strong>%s</strong><br>'
            'Cut and shipped from %s, %s<br>'
            '<a href="mailto:%s">%s</a> &middot; %s</div>'
            '<div class=fbot><span>&copy; %s %s. Cut by hand in %s, Iowa and shipped '
            'to all 50 states.</span>'
            '<span><a href="/privacy/">Privacy</a> &middot; <a href="/terms/">Terms</a>'
            ' &middot; <a href="/sitemap.xml">Sitemap</a></span></div>'
            '</div></footer>'
            % (pl, tl, bl, gl,
               e(B), SITE["city"], SITE["region_name"],
               SITE["email"], SITE["email"], SITE["hours"],
               datetime.date.today().year, e(B), SITE["city"]))

def bc(trail):
    out = ['<a href="/">Home</a>']
    for i, (lbl, href) in enumerate(trail):
        out.append('<span>/</span>' + ('<a href="%s">%s</a>' % (href, lbl) if href and i < len(trail)-1 else lbl))
    return '<div class=w><div class=bc>%s</div></div>' % "".join(out)

# ------------------------------------------------------------------ schema
def org_node():
    """One node typed as both OnlineStore and LocalBusiness.

    It genuinely is both: a real shop in Evansdale that ships nationwide. Keeping
    it as a single @id (rather than two nodes) means every Product, FAQ and
    Article on the site resolves to the same entity.
    """
    return {"@type": ["OnlineStore", "Organization"], "@id": U("/#org"),
            "name": B, "url": U("/"),
            "email": SITE["email"],
            "description": "Custom boat registration numbers, boat names and marine "
                           "vinyl decals cut to order in %s, %s and shipped "
                           "nationwide." % (SITE["city"], SITE["region_name"]),
            # Locality and region only. No streetAddress, no geo, no
            # openingHours - this is a mail-order shop run from a private
            # home, and none of that is public information.
            "address": {"@type": "PostalAddress",
                        "addressLocality": SITE["city"],
                        "addressRegion": SITE["region"],
                        "addressCountry": "US"},
            "areaServed": [{"@type": "Country", "name": "United States"},
                           {"@type": "AdministrativeArea", "name": SITE["county"]}],
            "priceRange": "$15-$120",
            "currenciesAccepted": "USD",
            "paymentAccepted": "Credit Card",
            "knowsAbout": ["boat registration numbers", "33 CFR 173.27",
                           "marine vinyl lettering", "hull identification numbers"]}

def site_node():
    return {"@type": "WebSite", "@id": U("/#site"), "url": U("/"), "name": B,
            "publisher": {"@id": U("/#org")}}

def crumb_node(trail, path):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": U("/")}]
    for i, (lbl, href) in enumerate(trail):
        items.append({"@type": "ListItem", "position": i + 2,
                      "name": html.unescape(lbl).replace("&amp;", "&"),
                      "item": U(href) if href else U(path)})
    return {"@type": "BreadcrumbList", "@id": U(path) + "#bc", "itemListElement": items}

def faq_node(items, path):
    return {"@type": "FAQPage", "@id": U(path) + "#faq", "mainEntity": [
        {"@type": "Question", "name": html.unescape(q),
         "acceptedAnswer": {"@type": "Answer",
                            "text": html.unescape(html.unescape(a).replace("<strong>", "")
                                                  .replace("</strong>", ""))}}
        for q, a in items]}

# The standard-post transit window, in business days. The table on
# /shipping-and-returns/ prints it and the Product schema publishes it; this is
# the one definition, and verify.py checks the rendered page still agrees.
SHIP_TRANSIT = (3, 6)


def product_node(p, path):
    """The Product node, and every field in it is a promise we keep.

    Search Console reported this node as "1 invalid item" on the homepage: a
    missing `image`, which makes the whole thing ineligible for rich results,
    plus three optional fields it would like. The optional three are worth
    filling in because they are the ones a buyer actually wants answered
    before clicking - can I send it back, how long until it arrives, and is
    that price still good - and Google shows them in the listing.

    Everything here is read off the published pages rather than chosen to look
    good. /shipping-and-returns/ is the source for the return policy and the
    transit window; verify.py fails the build if this node and that page ever
    disagree, because structured data is a claim made to a search engine on
    the shop's behalf and a false one is worse than an absent one.
    """
    return {"@type": "Product", "@id": U(path) + "#product",
            "name": html.unescape(p["nav"]) + " - " + B,
            "description": p["desc"], "brand": {"@type": "Brand", "name": B},
            "category": "Marine vinyl decals",
            # Was missing entirely, which is what made the item invalid.
            "image": [U("/assets/img/%s.jpg" % i) for i in p["image"]],
            "offers": {"@type": "Offer", "price": str(p["price"]), "priceCurrency": "USD",
                       "availability": "https://schema.org/InStock",
                       "url": U("/design/"),
                       # The date these prices actually took effect, from the
                       # price table. NOT today's date: an offer that claims
                       # to have begun this morning on every rebuild is a lie
                       # with a timestamp on it.
                       "validFrom": PRICE["set_on"],
                       # A YEAR OUT, rolling, rather than the 31st of December
                       # of whatever year it is now. The old version was
                       # correct in January and nearly expired by Christmas,
                       # and Google warns on a priceValidUntil in the past.
                       "priceValidUntil": str(datetime.date.today()
                                              + datetime.timedelta(days=365)),
                       # NOT RETURNABLE, and that is the honest category.
                       # /shipping-and-returns/ says it plainly: custom-cut
                       # vinyl with your own registration number on it cannot
                       # be resold. What we DO is remake our own errors and
                       # anything that arrives damaged, free - but that is a
                       # remake, not a customer-initiated return, and dressing
                       # it up as a returns window would be a promise the shop
                       # has not made.
                       "hasMerchantReturnPolicy": {
                           "@type": "MerchantReturnPolicy",
                           "applicableCountry": "US",
                           "returnPolicyCategory":
                               "https://schema.org/MerchantReturnNotPermitted"},
                       "shippingDetails": {"@type": "OfferShippingDetails",
                           "shippingRate": {"@type": "MonetaryAmount", "value": "0",
                                            "currency": "USD"},
                           "shippingDestination": {"@type": "DefinedRegion",
                                                   "addressCountry": "US"},
                           # Handling is 1-3 business days, and the range is
                           # wide on purpose. The shop's own promise is a
                           # proof within 12 hours and then cut and posted
                           # within 1-2 business days OF APPROVAL - and the
                           # approval is the customer's, not ours. Quoting the
                           # 1-2 we control as though it were the whole wait
                           # would be a delivery estimate that starts from a
                           # moment the buyer has not reached yet.
                           #
                           # Transit is the standard-post row of the table on
                           # /shipping-and-returns/: 3-6 business days.
                           "deliveryTime": {
                               "@type": "ShippingDeliveryTime",
                               "handlingTime": {
                                   "@type": "QuantitativeValue",
                                   "minValue": 1, "maxValue": 3,
                                   "unitCode": "DAY"},
                               "transitTime": {
                                   "@type": "QuantitativeValue",
                                   "minValue": SHIP_TRANSIT[0],
                                   "maxValue": SHIP_TRANSIT[1],
                                   "unitCode": "DAY"}}}}}

def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}

# ------------------------------------------------------------------- write
def write(path, body, prio="0.7"):
    p = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    PAGES.append((path, prio))
    # A noindex page must not be in the sitemap. A sitemap is a request to
    # index, so listing one that refuses indexing is a contradiction Search
    # Console reports as "Submitted URL marked noindex". Read off the rendered
    # HTML rather than passed in again, so it cannot disagree with the page.
    if 'content="noindex' in body:
        NOINDEX.add(path)

def shell(title, desc, path, schema, main, trail=None, noindex=False,
          faqs=None, faq_heading=None, sticky_label=None, sticky_price=PRICE["numbers"],
          sticky_bar=True, app=False, js="",
          band=None):
    parts = [head(title, desc, path, schema, noindex), topbar(), header()]
    if trail: parts.append(bc(trail))
    parts.append('<main id=main>' + main)
    if faqs: parts.append(faq_block(faqs, faq_heading or "Questions people actually ask", band))
    parts.append('</main>')
    # The phone app layer: the HOME PAGE ONLY.
    #
    # It ran on all 32 commercial pages first. The problem is arrival intent:
    # someone searching "iowa boat registration numbers" lands on the Iowa
    # page wanting Iowa, and a full-screen deck over it is an interstitial -
    # which Google treats as a mobile ranking signal, on a site whose whole
    # strategy is search. The home page has no specific answer being sought,
    # so there is nothing to interrupt. Every other page gets the offer card
    # in the hero instead.
    #
    # Emitted here, after </main> and outside every container, because a
    # fixed-position element is positioned against the nearest ancestor with
    # a transform, filter or contain - and the hero has a gradient today but
    # could grow one of those tomorrow.
    if app:
        parts.append(app_shell())
    parts.append(footer())
    # The order page suppresses it: the wizard already carries a live total in
    # its header, and a second bar reading a flat registration-number price
    # under a total for a boat name contradicts it - on a page whose whole
    # job is that total. Its button also links to the page you are already on.
    if sticky_bar:
        parts.append(sticky(sticky_label or "Registration numbers", sticky_price))
        parts.append('<script>document.body.classList.add("has-sticky");</script>')
    parts.append('<script>'
                 '(function(){var b=document.getElementById("menubtn"),'
                 'n=document.getElementById("nav");if(!b||!n)return;'
                 'b.addEventListener("click",function(){'
                 'var o=n.classList.toggle("open");'
                 'b.setAttribute("aria-expanded",o?"true":"false");});})();</script>')
    if js:
        if "BNS_STRIPE_PK" in js:
            # Only the BLOCK set loads with the page: it holds the default
            # face and is the only set a registration number may legally use.
            # Display (28) and script (24) are injected by order.py the first
            # time their tab is opened, which for most orders is never.
            # Async either way, so type never blocks first paint.
            gf = head_fonts_href()
            parts.append(
                '<link rel="preconnect" href="https://fonts.googleapis.com">'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                '<link rel="stylesheet" href="%s" media="print" '
                'onload="this.media=\'all\'">'
                '<noscript><link rel="stylesheet" href="%s"></noscript>' % (gf, gf))
            # Precedence: a real publishable key wins; otherwise PAY_MODE decides
            # between the sandbox card form and the emailed-payment-link fallback.
            pk = os.environ.get("STRIPE_PUBLISHABLE_KEY", "") or STRIPE_PK
            mode = os.environ.get("PAY_MODE", "sandbox" if not pk else "stripe")
            parts.append('<script>window.BNS_STRIPE_PK=%s;window.BNS_PAY_MODE=%s;'
                         'window.BNS_MOCKPAY_HTML=%s;</script>'
                         % (json.dumps(pk), json.dumps(mode), json.dumps(MP.HTML)))
            if pk:
                parts.append('<script src="https://js.stripe.com/v3/"></script>')
            elif mode == "sandbox":
                parts.append('<script>' + MP.JS + '</script>')
        parts.append('<script>' + js + '</script>')
    return "".join(parts)

# The registration checker is worker/decode.js, inlined here, with the old
# BNS_VALIDATE name kept as a shim so the order form's callers are untouched.
# price_js() is worker/price.js itself, inlined - so the running total, the
# "Pay $71" on the button and the amount the Stripe intent is created for are
# all one implementation. It must come BEFORE O.JS, which calls into it.
ORDER_JS = (PV.data_js() + PV.JS + SH.decode_js() + SH.SHIM_JS
            + SH.price_js() + O.color_js() + O.JS)

# =================================================================== PAGES
def why_grid(limit=6):
    return '<div class="grid">' + "".join(
        '<div class=card><h3>%s</h3><p>%s</p></div>' % (t, d)
        for t, d in CB.WHY_US[:limit]) + '</div>'

def how_it_works(band):
    cards = "".join(
        '<div class=stepcard><span class=stepnum>%d</span>'
        '<h3>%s</h3><p>%s</p></div>' % (i + 1, t, b)
        for i, (t, b) in enumerate(CB.HOW_IT_WORKS_STEPS))
    return ('%s<div class=w><h2>How it works</h2>'
            '<p class=lede>Four steps, about a minute.</p>'
            '<div class=stepgrid>%s</div>'
            '<a class="btn lg" href="/design/">Start your order</a>'
            '</div></section>' % (band.open(), cards))


def other_products(exclude, band, heading="Other things we cut"):
    """The cross-sell. Three products means two cards here, so they get the
    room to look deliberate rather than like a grid that ran out."""
    items = [x for x in PRODUCTS if x["slug"] != exclude]
    cards = "".join(
        '<a class=xcard href="/%s/">%s<div class=xbody><h3>%s</h3><p>%s</p>'
        '<div class=xprice>$%d <small>%s</small></div></div>'
        '<span class=xgo aria-hidden="true">&rarr;</span></a>'
        % (x["slug"], icon(x["icon"]), x["nav"], x["blurb"], x["price"], x["unit"])
        for x in items)
    return ('%s<div class=w><h2>%s</h2><div class=xgrid>%s</div></div></section>'
            % (band.open(), heading, cards))


def product_grid(exclude=None, heading="What we cut"):
    cards = "".join(
        '<a class=card href="/%s/">%s<h3>%s</h3><p>%s</p>'
        '<div class=price>$%d <small>%s</small></div><div class=go>See details &rarr;</div></a>'
        % (p["slug"], icon(p["icon"]), p["nav"], p["blurb"], p["price"], p["unit"])
        for p in PRODUCTS if p["slug"] != exclude)
    return '<section><div class=w><h2>%s</h2><p class=lede>Everything is cut from \
sheet vinyl, pre-spaced, and shipped flat with application tape over the top.</p>\
<div class=grid>%s</div></div></section>' % (heading, cards)

def state_wheel(current=None, limit=None):
    sts = STATES[:limit] if limit else STATES
    return '<div class=stategrid>' + "".join(
        '<a href="/registration-numbers/%s/"%s>%s <i>%s</i></a>'
        % (s["slug"], ' aria-current="page"' if s["slug"] == current else "",
           s["name"], s["ab"]) for s in sts) + '</div>'

def tools_grid():
    return '<div class=grid>' + "".join(
        '<a class=card href="/tools/%s/">%s<h3>%s</h3><p>%s</p>'
        '<div class=go>Open the tool &rarr;</div></a>'
        % (t["slug"], icon("tool"), t["nav"], t["desc"]) for t in TOOLS) + '</div>'

def claims_band():
    """The four headline claims.

    Each sub-line exists to stop the headline over-promising:

    - "Two Sets" has to say which two, because elsewhere on the site a "set"
      has meant a pair.
    - "Proofed Before We Cut" has to say what the proof is and when it comes,
      or it reads as a delay rather than the protection it is.
    - "Meets 33 CFR 173.27" has to scope itself to what we actually control. We cut
      the characters to the federal rule; where they get stuck is the owner's.
    """
    return ('<section class=soft><div class=w><h2>The offer, plainly</h2>'
            '<div class=claims>'
            + "".join('<div><b>%s</b><span>%s</span></div>' % (f, FEATURE_SUB[f])
                      for f in FEATURES)
            + '</div></div></section>')

def proof_band(band=None):
    """How the proof works, as three steps.

    This is the one thing on the site that is genuinely different from the
    marketplace sets, so it gets a section rather than a line in a list. It is
    also the answer to the real objection - "what if you cut it wrong" - which
    is worth more than the day of turnaround the proof step costs us.
    """
    steps = [
        ("Within 12 hours",
         "We email you a proof",
         "Your exact lettering, at your height, in your font and colour. Not a "
         "mock-up of something similar - the artwork itself."),
        ("You check it",
         "Against your registration card",
         "Character by character, including the spaces. You are the only "
         "person who can tell us the card says UH and not U4."),
        ("You approve it",
         "Then it goes to the plotter",
         "One tap, or just reply to the email. Cut, packed and posted within "
         "1-2 business days. Nothing is cut before you say yes."),
    ]
    open_ = band.open() if band else '<section class=soft>'
    return (open_ + '<div class=w><h2>Nothing is cut until you have seen it</h2>'
            '<p class=lede>A registration number with one wrong character is '
            'worth nothing &mdash; you cannot file the corner off a 3-inch '
            'digit. So we proof every order before the vinyl moves.</p>'
            '<ol class=proofsteps>'
            + "".join('<li><span class=psnum>%d</span><b>%s</b>'
                      '<strong>%s</strong><span class=pstext>%s</span></li>'
                      % (i + 1, k, h, t) for i, (k, h, t) in enumerate(steps))
            + '</ol>'
            '<p class=hint>Need a change instead? Say so on the proof and we '
            'send a corrected one. It costs nothing and there is no limit.</p>'
            '</div></section>')


# ------------------------------------------------------------------- home
def build_home():
    sch = graph(org_node(), site_node(),
                product_node(PRODUCTS[0], "/"), faq_node(FAQ_HOME, "/"))
    right = O.form()
    main = (
      hero("Custom Boat Registration Numbers, Proofed Before We Cut",
           "Legal 3-inch block numbers for both sides of your hull, cut from "
           "marine vinyl and pre-spaced on one sheet. We email you a proof "
           "within 12 hours and cut nothing until you approve it. Boat names "
           "and custom lettering too.",
           badge="Price on the page. Shipping included.",
           right=right)
      + claims_band()
      + proof_band()
      + gallery(["AL-01", "AL-02", "AL-08"])
      + '<section><div class=w><h2>Why buy here instead of the cheap set</h2>'
        '<p class=lede>There are $11 sets on marketplaces. Here is honestly what '
        'separates them from this.</p>' + why_grid() + '</div></section>'
      + product_grid()
      + '<section class=soft><div class=w><h2>Free tools, no email required</h2>'
        '<p class=lede>Decode a hull number, generate a boat name, or check your '
        'registration layout against the federal rule before you spend anything.</p>'
        + tools_grid() + '</div></section>'
      + '<section><div class=w><h2>Your state&rsquo;s numbers</h2>'
        '<p class=lede>The 3-inch block rule is federal and applies everywhere. '
        'What changes by state is the prefix, who issues it, and where the validation '
        'decal sits.</p>' + state_wheel(limit=20) +
        '<p style="margin-top:16px"><a href="/registration-numbers/">All states &rarr;</a></p>'
        '</div></section>'
      + how_it_works(Band(1))
      + share_block('/', U('/'), '/assets/share/line-3-inches.png'))
    write("/", shell("Boat Registration Numbers - Legal 3-Inch Sets, Both Sides",
          "Custom boat registration numbers $%d a pair with free shipping. Legal "
          "3-inch block vinyl for all 50 states, boat names from $%d. Proof in "
          "12 hours." % (PRICE["numbers"], PRICE["name_from"]),
          "/", sch, main, faqs=FAQ_HOME, js=ORDER_JS, app=True), "1.0")

# ---------------------------------------------------------------- /design/
def build_proof():
    """The page the proof email links to.

    noindex, and it holds nothing until the browser fetches /api/proof with
    the token from the link - so the HTML in the build carries no customer
    data at all, and a crawler that somehow reached it would find an empty
    shell.
    """
    main = (
        '<section style="padding:30px 0 44px"><div class=w style="max-width:620px">'
        '<div id=proofbox class=proofbox>'
        '<p class=proofwait>Loading your proof&hellip;</p>'
        '</div></div></section>')
    js = r"""
(function(){
  var box=document.getElementById('proofbox'); if(!box) return;
  var q=new URLSearchParams(location.search);
  var ref=q.get('r')||'', tok=q.get('t')||'';
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function fail(){
    box.innerHTML='<h1>That link did not work</h1><p class=lede>It may have '
      +'been typed rather than clicked, or the order may have been cancelled. '
      +'Reply to the proof email and we will sort it out.</p>';
  }
  if(!ref||!tok){ fail(); return; }

  function api(extra){
    return fetch('/api/approve?r='+encodeURIComponent(ref)
      +'&t='+encodeURIComponent(tok)+(extra||''))
      .then(function(r){return r.json();});
  }

  function thanks(){
    box.innerHTML='<div class=prooftick>&#10003;</div>'
      +'<h1>Approved</h1><p class=lede>That is on its way to the plotter. '
      +'Cut, packed and posted within 1-2 business days.</p>'
      +'<p class=hint>Order '+esc(ref)+'. Spotted something after all? Reply '
      +'to the proof email today and we can almost always stop it.</p>'
      +'<a class="btn lg" href="/">Back to the shop</a>';
  }
  function logged(){
    box.innerHTML='<h1>Thanks &mdash; we have it</h1>'
      +'<p class=lede>Nothing will be cut. We will email you a corrected '
      +'proof.</p><p class=hint>Order '+esc(ref)+'.</p>'
      +'<a class="btn lg" href="/">Back to the shop</a>';
  }

  fetch('/api/proof?r='+encodeURIComponent(ref)+'&t='+encodeURIComponent(tok))
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if(!d||!d.ok){ fail(); return; }
      if(d.approved){ thanks(); return; }
      var letters=[d.text,d.boatname].filter(Boolean).join('  /  ');
      var css=(window.BNS_FONTCSS||{})[d.font]||"'Archivo Black',sans-serif";
      box.innerHTML=
        '<h1>Check your proof</h1>'
       +'<p class=lede>This is exactly what the plotter cuts. Check every '
       +'character against your registration card.</p>'
       +'<div class=proofart><span style="font-family:'+esc(css)+'">'
       +esc(letters)+'</span></div>'
       +'<dl class=proofspec>'
       +'<dt>Order</dt><dd>'+esc(d.ref)+'</dd>'
       +'<dt>Height</dt><dd>'+esc(d.height)+'&quot;</dd>'
       +'<dt>Font</dt><dd>'+esc(d.font)+'</dd>'
       +'<dt>Colour</dt><dd>'+esc(d.color)
         +(d.outline_color?' with a '+esc(d.outline_color)+' outline':'')+'</dd>'
       +'<dt>Price</dt><dd>$'+esc(d.total)+'</dd>'
       +'</dl>'
       +(d.changes?'<p class=hint>You have already asked for a change on this '
         +'order. Approving now cuts it as shown above.</p>':'')
       +'<button type=button class="btn lg" id=okbtn>Approve &mdash; cut it</button>'
       +'<button type=button class=prooflink id=chbtn>Something needs '
       +'changing</button>';

      document.getElementById('okbtn').addEventListener('click', function(){
        this.disabled=true; this.textContent='Sending…';
        api().then(function(j){ j&&j.ok ? thanks() : fail(); }).catch(fail);
      });
      document.getElementById('chbtn').addEventListener('click', function(){
        box.insertAdjacentHTML('beforeend',
          '<div class=proofnote><label for=chnote>What needs changing?</label>'
         +'<textarea id=chnote rows=4 placeholder="For example: the suffix '
         +'should read UH with a space before it."></textarea>'
         +'<button type=button class="btn lg" id=chsend>Send this to the '
         +'shop</button></div>');
        this.remove();
        document.getElementById('chsend').addEventListener('click', function(){
          this.disabled=true; this.textContent='Sending…';
          var n=document.getElementById('chnote').value.slice(0,600);
          api('&c=1&note='+encodeURIComponent(n))
            .then(function(j){ j&&j.ok ? logged() : fail(); }).catch(fail);
        });
      });
    }).catch(fail);
})();
"""
    # Written straight out rather than through write(): it must not reach the
    # sitemap. The page exists only to be opened from a link in an email.
    body = shell("Your proof", "Check and approve your lettering.",
                 "/proof/", None, main, noindex=True, sticky_bar=False,
                 js=O.color_js() + js)
    out = OUT / "proof" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")


def build_fonts_check():
    """A page Ryan opens on the cutter PC to report what is installed.

    Two ways of finding out, because neither covers everything:

    * `queryLocalFonts()` is the real API for this and returns the whole
      system list, but it is Chrome and Edge on desktop only, and it puts up
      a permission prompt he has to accept.
    * A canvas metric check works in any browser but can only answer "is THIS
      family here", so it is run against the site's own faces. That happens
      to be the actual question, so it is the one that always runs.

    Deliberately loads no web fonts. A face pulled in by the page would
    measure as installed when it is not, and the whole report would be wrong
    in the direction that costs a mis-cut.
    """
    fams = []
    seen = set()
    for label, css, spec, block, _match in FONTS:
        fam = spec.split(":")[0].replace("+", " ")
        wght = spec.split("wght@")[1] if "wght@" in spec else "400"
        if fam in seen:
            continue
        seen.add(fam)
        fams.append({"label": label, "family": fam, "weight": wght,
                     "cat": "block" if block else "display"})

    main = (
        '<section style="padding:30px 0 46px"><div class=w style="max-width:680px">'
        '<h1 style="font-size:28px;margin-bottom:10px">What fonts are on this '
        'computer?</h1>'
        '<p class=lede>Run this on the machine that drives the plotter. It '
        'checks which of the %d faces the website offers are already '
        'installed here, so we only install what is actually missing.</p>'
        '<div class=fcnote><b>What this sends.</b> Font names, your browser '
        'version and whether this is Windows or a Mac. Nothing else &mdash; no '
        'files, no documents, nothing about the rest of the machine. It is only '
        'sent when you press the button at the bottom, and it goes to Aaron.</div>'
        '<div id=fcrun><button type=button class="btn lg" id=fcgo>Check this '
        'computer</button></div>'
        '<div id=fcout></div>'
        '</div></section>' % len(fams))

    js = ("window.NMB_FAMS="
          + json.dumps(fams, separators=(",", ":"))
          + ";window.NMB_TARGET=0;") + r"""
(function(){
  var go=document.getElementById('fcgo'), out=document.getElementById('fcout');
  if(!go) return;
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}

  // Measured on a canvas against three different generic fallbacks. If the
  // family is missing, the browser draws the fallback and the widths match.
  var ctx=document.createElement('canvas').getContext('2d');
  var PROBE='MWQ@0123456789mwiABCXYZ';
  function installed(fam){
    var base=['monospace','serif','sans-serif'];
    for(var i=0;i<base.length;i++){
      ctx.font='72px '+base[i];
      var a=ctx.measureText(PROBE).width;
      ctx.font='72px "'+fam.replace(/"/g,'')+'",'+base[i];
      if(Math.abs(a-ctx.measureText(PROBE).width)>0.5) return true;
    }
    return false;
  }

  var report=null;

  var CATS=[['block','Block','legal on a registration number'],
            ['display','Display','names and lettering'],
            ['script','Script','names and lettering']];
  var TARGET=window.NMB_TARGET||15;

  // Counts live against the grid's budget. The website shows each category as
  // three rows of five, so a category that is not exactly TARGET cannot be
  // built - better he sees that here than Aaron finds out at build time.
  function tally(){
    var ok=true;
    CATS.forEach(function(c){
      var n=out.querySelectorAll('.fcpick[data-cat="'+c[0]+'"]:checked').length;
      var el=document.getElementById('fccount-'+c[0]);
      if(!el) return;
      el.textContent=n+' of '+TARGET;
      el.className='fccount'+(n===TARGET?' on':(n>TARGET?' over':''));
      if(n!==TARGET) ok=false;
    });
    var w=document.getElementById('fcwarn');
    if(w) w.hidden=ok;
  }

  function render(have, missing, sys, method){
    var haveSet={};
    have.forEach(function(f){ haveSet[f.label]=1; });
    var all=window.NMB_FAMS;

    var h='<h2 style="margin-top:26px">'+have.length+' of '+all.length
         +' already installed</h2>'
       +'<p class=lede>Tick the faces you want the website to offer. The ones '
       +'already on this machine are ticked for you - untick any you do not '
       +'want to cut, and tick a missing one if you are happy to install it.</p>';

    CATS.forEach(function(c){
      var rows=all.filter(function(f){ return f.cat===c[0]; });
      h+='<div class=fcgroup><div class=fchead><div><b>'+esc(c[1])+'</b>'
        +'<span>'+esc(c[2])+'</span></div>'
        +'<div class=fcactions><span class=fccount id=fccount-'+c[0]+'></span>'
        +'<button type=button class=fcbtn data-cat="'+c[0]+'" data-on="1">All</button>'
        +'<button type=button class=fcbtn data-cat="'+c[0]+'" data-on="">None</button>'
        +'</div></div><ul class=fclist>';
      rows.forEach(function(f){
        var got=!!haveSet[f.label];
        h+='<li class=fcrow><label><input type=checkbox class=fcpick'
          +' data-cat="'+esc(f.cat)+'" data-label="'+esc(f.label)+'"'
          +' data-family="'+esc(f.family)+'" data-weight="'+esc(f.weight)+'"'
          +(got?' checked':'')+'>'
          +'<span class=fcname><b>'+esc(f.label)+'</b>'
          +'<em>'+esc(f.family)+(f.weight!=='400'?' '+esc(f.weight):'')+'</em></span>'
          +'<span class="fcstat'+(got?' yes':'')+'">'
          +(got?'installed':'needs installing')+'</span></label></li>';
      });
      h+='</ul></div>';
    });

    h+='<p class=fcwarn id=fcwarn hidden>The website shows five across and '
      +'three down in each group, so it needs exactly '+TARGET+' in each. '
      +'Send it anyway if you like - Aaron will sort the numbers out.</p>';

    if(sys&&sys.length){
      h+='<details class=fcdet><summary>Everything else installed on this '
        +'computer ('+sys.length+')</summary><div class=fcall>'
        +esc(sys.join(', '))+'</div></details>';
    }
    h+='<div class=fcsend><button type=button class="btn lg" id=fcsend>'
      +'Send this to Aaron</button>'
      +'<p class=hint>Nothing has been sent yet.</p></div>';
    out.innerHTML=h;

    out.addEventListener('change', function(ev){
      if(ev.target.classList.contains('fcpick')) tally();
    });
    [].forEach.call(out.querySelectorAll('.fcbtn'), function(b){
      b.addEventListener('click', function(){
        var on=!!b.dataset.on;
        [].forEach.call(out.querySelectorAll('.fcpick[data-cat="'+b.dataset.cat+'"]'),
          function(i){ i.checked=on; });
        tally();
      });
    });
    tally();

    document.getElementById('fcsend').addEventListener('click', function(){
      var b=this; b.disabled=true; b.textContent='Sending...';
      var picks=[].map.call(out.querySelectorAll('.fcpick:checked'), function(i){
        return {label:i.dataset.label, family:i.dataset.family,
                weight:i.dataset.weight, cat:i.dataset.cat};
      });
      var body={have:have, missing:missing, all_sys:sys, method:method,
                picks:picks, ua:navigator.userAgent,
                platform:(navigator.userAgentData&&navigator.userAgentData.platform)
                         ||navigator.platform||''};
      fetch('/api/fonts',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)})
        .then(function(r){return r.json();})
        .then(function(j){
          b.parentNode.innerHTML = j&&j.ok
            ? '<p class=fcok>Sent - '+picks.length+' faces picked. Aaron has '
              +'the list.</p>'
            : '<p class=fcerr>That did not send. Screenshot this page instead.</p>';
        }).catch(function(){
          b.parentNode.innerHTML='<p class=fcerr>That did not send. Screenshot '
            +'this page instead.</p>';
        });
    });
  }

  function check(sys){
    var have=[], missing=[], names=null;
    if(sys){ names={}; sys.forEach(function(n){ names[n.toLowerCase()]=1; }); }
    window.NMB_FAMS.forEach(function(f){
      var yes = names ? !!names[f.family.toLowerCase()] : installed(f.family);
      (yes?have:missing).push(f);
    });
    render(have, missing, sys||[], names?'local-font-access':'metrics');
  }

  go.addEventListener('click', function(){
    go.disabled=true; go.textContent='Checking…';
    if(typeof window.queryLocalFonts==='function'){
      window.queryLocalFonts().then(function(list){
        var fams={}; list.forEach(function(f){ fams[f.family]=1; });
        check(Object.keys(fams).sort());
      }).catch(function(){
        // Prompt dismissed or blocked - the metric check still answers the
        // question we actually care about.
        check(null);
      });
    } else { check(null); }
  });
})();
"""
    body = shell("Font check", "Which fonts are installed on this computer.",
                 "/fonts-check/", None, main, noindex=True, sticky_bar=False,
                 js=js)
    out = OUT / "fonts-check" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")


def build_design():
    trail = [("Start your order", None)]
    sch = graph(org_node(), crumb_node(trail, "/design/"),
                product_node(PRODUCTS[0], "/design/"))
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">Start your order</h1>'
            '<p class=lede>Build it, see the price update as you go, and send it. '
            'The preview shows your exact lettering before you pay &mdash; we cut what '
            'is on that screen.</p>'
            '</div></section>'
            '<section style="padding-top:0"><div class=w>'
            '<div class=herogrid><div>' + O.form() + '</div>'
            '<div>' + why_grid(6) +
            '</div></div></div></section>')
    write("/design/", shell("Start Your Order - Boat Lettering &amp; Numbers",
          "Build your boat registration numbers or custom lettering order. Live pricing, "
          "live pricing, a live preview of your exact lettering, and next-day shipping.",
          "/design/", sch, main, trail=trail, js=ORDER_JS,
                sticky_bar=False), "0.9")

# -------------------------------------------------------------- /pricing/
# A traditional three-up pricing table. Features are claims we can stand behind
# on every order - no "up to", no asterisks.
PRICE_PLANS = [
    dict(slug="boat-registration-numbers", name="Boat numbers",
         price="$%d" % PRICE["numbers"], unit="a pair", featured=True,
         line="The legal set, both sides of the bow.",
         feats=["Two sets &mdash; one for each side",
                "3&quot; block characters, legal in all 50 states",
                "Checked against your state&rsquo;s format before it cuts",
                "Pre-spaced on one sheet",
                "Eight colors, all included",
                "Contrasting outline, +$%d" % PRICE["outline"],
                "Free shipping, proof in 12 hours"]),
    dict(slug="boat-lettering", name="Boat letters", featured=False,
         price="$%d" % PRICE["name_from"], unit="to start",
         line="Names, hailing ports and any transom text.",
         feats=["Ten fonts, previewed in your own lettering",
                "Script, serif and block",
                "Pre-spaced with application tape over the top",
                "Curved transoms laid out from your photo",
                "Priced by finished size &mdash; most land $%d&ndash;%d"
                % (PRICE["name_from"], PRICE["name_typical_to"]),
                "Eight colors, all included",
                "Contrasting outline, +$%d" % PRICE["outline"],
                "Free shipping, proof in 12 hours"]),
]


def plan_table():
    cards = []
    for pl in PRICE_PLANS:
        feats = "".join("<li>%s</li>" % f for f in pl["feats"])
        cards.append(
            '<div class="plan%s">%s'
            '<h3>%s</h3><p class=planline>%s</p>'
            '<div class=planprice>%s <small>%s</small></div>'
            '<ul class=planfeats>%s</ul>'
            '<a class="btn planbtn" href="/design/">Start your order</a>'
            '<a class=planmore href="/%s/">See details &rarr;</a>'
            '</div>'
            % (" featured" if pl["featured"] else "",
               '<span class=planflag>Most ordered</span>' if pl["featured"] else "",
               pl["name"], pl["line"], pl["price"], pl["unit"], feats, pl["slug"]))
    return '<div class=plangrid>%s</div>' % "".join(cards)


def build_pricing():
    trail = [("Pricing", None)]
    faqs = [
      ("Is shipping really free?",
       "Yes, on everything, to anywhere in the 50 states. Standard post, %d-%d "
       "days in transit. If you need it sooner than that, email us before you "
       "order and we will tell you what is possible and what it costs."
       % SHIP_TRANSIT),
      ("Why is $%d not the cheapest price on the internet?"
       % PRICE["numbers"],
       "Because it is not a race we want to win. An $11 set is usually cut as loose "
       "characters, which means you doing the spacing on the water. Ours arrives "
       "pre-spaced on one sheet and checked against your state format before it cuts. "
       "If price is the only thing that matters to you, the marketplace sets are "
       "genuinely cheaper and we would rather say so."),
      ("When do I pay?",
       "By card at checkout. The preview on that screen is what gets cut, so read it "
       "before you pay, and again as a proof you approve before we cut."),
      ("Do you do trade or volume pricing?",
       "Yes - marinas, dealers and fleet operators. Email " + SITE["email"] +
       " with roughly how many sets a month and we will put numbers together."),
    ]
    sch = graph(org_node(), crumb_node(trail, "/pricing/"), faq_node(faqs, "/pricing/"))
    main = ('<section style="padding-top:26px"><div class=w>'
      '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">Pricing</h1>'
      '<p class=lede>No designer to click through before you see a number. '
      'Every price includes free standard shipping in the USA.</p>'
      + plan_table()
      + '</div></section>'
      + '</div></section>')
    write("/pricing/", shell("Boat Lettering &amp; Registration Number Prices",
          "Boat registration numbers $%d a pair, boat names from $%d, custom "
          "lettering from $%d. Free shipping, next-business-day production."
          % (PRICE["numbers"], PRICE["name_from"], PRICE["name_from"]),
          "/pricing/", sch, main, trail=trail, faqs=faqs,
          faq_heading="Pricing questions"), "0.9")

# -------------------------------------------------------------- products
PROD_BODY = {
 "boat-registration-numbers": (
   CB.FED_RULE + CB.CONTRAST_NOTE +
   "<h2>What you actually receive</h2>"
   "<p>One sheet, not a bag of loose letters. Your full number is cut from a single "
   "piece of colored vinyl, already spaced to the federal rule, with clear application "
   "tape laid over the top holding every character in position. You get two of them "
   "&mdash; one for each side &mdash; plus a squeegee and written instructions.</p>"
   "<p>That matters more than it sounds. The most common way a home install goes wrong "
   "is not a torn letter, it is spacing: loose characters placed by eye end up uneven, "
   "drifting uphill, or packed too tight to meet the spacing rule. Pre-spaced removes "
   "the only hard part of the job.</p>"
   "<h2>Sizing it to your hull</h2>"
   "<p>Three inches is the legal floor, and it is what most people order. Go taller if "
   "your hull has the run for it &mdash; 4 inches reads noticeably better from a "
   "distance and costs $4 more. A six-character number at 3 inches finishes roughly "
   "13&ndash;15 inches wide. At 4 inches, about 18 inches. Measure the flat run on the "
   "forward half of your hull above the waterline before you commit, and use our "
   "<a href=\"/tools/registration-number-layout-checker/\">layout checker</a> to see "
   "the finished width.</p>"
   "<h2>Where they go</h2>"
   "<p>Forward half of the boat, both sides, reading left to right. In practice that "
   "means as far forward as you can get them while staying on a flat panel above the "
   "waterline, and high enough that they are not permanently under spray. The "
   "validation decal &mdash; the little sticker with your expiry &mdash; sits near the "
   "number, and exactly where varies by state. "
   "<a href=\"/guides/where-to-put-boat-registration-numbers/\">Full placement guide</a>.</p>"),

 "boat-lettering": (
   "<h2>Fonts that work, and the ones that are illegal</h2>"
   "<p>We cut ten fonts, and you see your own lettering in every one of them before "
   "you choose. On a transom name almost anything goes &mdash; script "
   "reads beautifully, and a heavy serif looks like money. On a <strong>registration "
   "number, script is not legal</strong>: the rule says plain vertical block characters, "
   "so our order form locks script out the moment you pick registration numbers. It is "
   "the one place where taste does not get a vote.</p>"
   "<p>The practical test for any boat font is distance. Thin strokes and tight counters "
   "disappear at fifty yards and look like a smudge in photos. If you want the name "
   "readable from the next slip, pick weight over flourish.</p>"
   "<h2>Layout we handle for you</h2>"
   "<p>Send a straight-on photo of the panel with a tape measure in frame and we will "
   "lay the text out to the actual space &mdash; including arcing it to follow a curved "
   "transom, which almost every sailboat and a lot of cruisers need. That is included, "
   "not an upcharge.</p>"
   "<h2>Color, and the one combination to avoid</h2>"
   "<p>Thirty-two colors including metallic silver and gold, chrome, and reflective. "
   "The combination to avoid is low contrast: dark navy on a black hull, white on "
   "cream. It photographs as nothing. If you want subtle, get the contrast from "
   "finish &mdash; chrome on white reads as tone-on-tone in person and still catches "
   "light.</p>"
   "<h2>Picking the name</h2>"
   "<p>If you are still deciding, our <a href=\"/tools/boat-name-generator/\">name "
   "generator</a> spins a thousand-plus ideas by category, and the "
   "<a href=\"/tools/funny-boat-names/\">funny list</a> is sorted by how hard the joke "
   "lands. One piece of practical advice: say it out loud as a radio call. "
   "&ldquo;Pan-pan, pan-pan, this is Multiple Scoregasms&rdquo; is funny exactly once.</p>"
   "<h2>How it is made</h2>"
   "<p>Cut from a single sheet of colored vinyl and pre-spaced with application tape "
   "over the top, so it goes on in one pass. Not printed on a clear square &mdash; "
   "there is no visible background or edge, just the letter shapes on your hull.</p>"
   "<h2>Sizes and what they cost</h2>"
   "<p>Most transom names land between $38 and $68. Price follows the width the "
   "finished decal measures, so a short name in big letters costs about the same "
   "as a long name in small ones.</p>"),

}

def build_product(p):
    trail = [(p["nav"], None)]
    faqs = [
      ("How fast will I get it?",
       "Posted 1-2 business days after you approve the proof, free. Standard "
       "post is then %d-%d days in transit after that." % SHIP_TRANSIT),
      ("Can I see it before it is made?",
       "Yes - the preview in the order form shows your exact lettering, at your chosen "
       "height, in your chosen color. That is what gets cut, so read it twice before "
       "you pay."),
      ("What if I ruin it putting it on?",
       "A replacement set is a new order. The install is the part we cannot do for you, "
       "which is why everything ships pre-spaced on one sheet with application tape over "
       "the top - it goes on in one pass rather than character by character. Read the "
       "install guide before you start and take the twenty minutes."),
      ("How long will it last?",
       "Years, not seasons - it is marine-grade film, not craft vinyl, and it is the "
       "same stock sign shops put on vehicles. A dark color in southern sun fades "
       "soonest. If one of ours fails on a hull you prepared properly, tell us."),
    ]
    sch = graph(org_node(), crumb_node(trail, "/%s/" % p["slug"]),
                product_node(p, "/%s/" % p["slug"]), faq_node(faqs, "/%s/" % p["slug"]))
    body = PROD_BODY.get(p["slug"], "")
    secs = PAGE_SECTIONS.get("/%s/" % p["slug"], [])
    band = Band()
    main = (hero(p["h1"], p["blurb"],
            trust=["$%d %s" % (p["price"], p["unit"] or "flat"),
                   "Proofed Before We Cut", "Marine Vinyl",
                   "Meets 33 CFR 173.27"],
            right=O.form())
      + (alternating(body, secs, band) if secs
         else band.open() + '<div class=w><div class=prose>' + body
              + '</div></div></section>')

      + how_it_works(band)
      + other_products(p["slug"], band))
    write("/%s/" % p["slug"],
          shell(p.get("title", p["h1"]).replace("&amp;", "&"), p["desc"],
                "/%s/" % p["slug"], sch,
                main, trail=trail, faqs=faqs, sticky_label=p["nav"],
                sticky_price=p["price"], js=ORDER_JS, band=band), "0.9")

# ---------------------------------------------------------------- states
def ordinal(n):
    """21st, not 21th. The hand-rolled version special-cased 2 and 3 and then
    printed "22th" and "21th" on two live pages."""
    words = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
             6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}
    if n in words:
        return words[n]
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suf)


def state_identity(s, band):
    """The band that says, immediately, which state you are on.

    Shape plus prefix plus three real numbers. The numbers are the Coast
    Guard's, cited inline, because a state page that invents its own
    statistics is worth nothing to an answer engine - and these pages were
    previously publishing fleet figures that were wrong by 2-3x.
    """
    fleet, rank, scope = USCG_FLEET[s["slug"]]
    share = fleet / float(USCG_NATIONAL) * 100
    _deep, _bright, _motif = STATE_ACCENT.get(s["slug"], ("", "", ""))
    return (band.open("sidband")
      + '<div class="w sband" style="--sbright:%s">' % _bright
      + '<div>' + state_badge(s["slug"], s["ab"], s["name"])
      + ('<p class=smotif>%s in %s</p>' % (s["name"], _motif) if _motif else "")
      + '</div>'
      + '<div><div class=sfacts>'
        '<div class=sfact><b>%s</b><span>Registered vessels</span></div>'
        '<div class=sfact><b>#%d</b><span>Of the 50 states</span></div>'
        '<div class=sfact><b>%s</b><span>Vessel prefix</span></div>'
        '</div>'
        '<p class=ssrc>%s of every registered boat in the country is in %s. '
        'Registration counts from the %s, 2024 figures. '
        '<a href="%s" rel="nofollow noopener" target="_blank">Source</a>.</p>'
        '</div></div></section>'
      % ("{:,}".format(fleet), rank, s["ab"],
         ("%.1f%%" % share) if share >= 0.1 else "Under 0.1%",
         s["name"], USCG_SOURCE, USCG_URL))


def state_waters(s, band):
    """Where people in this state actually put a boat in the water.

    This is the part a state page lives or dies on. Anyone can restate the
    federal 3-inch rule; naming Okoboji, the Santee Cooper lakes or the
    Western Basin the way a local names them is what makes the page worth
    ranking, and what an answer engine has nothing else to quote for.
    """
    w = WATERS.get(s["slug"])
    if not w:
        return ""
    items = "".join('<li><b>%s</b><span>%s</span></li>' % (n, note)
                    for n, note in w["waters"])
    return (band.open() + '<div class=w>'
      '<h2>Where people boat in %s</h2>'
      '<p class=lede>%s</p>'
      '<ul class=waters>%s</ul>'
      '<p style="margin-top:18px"><strong>The season.</strong> %s</p>'
      '</div></section>' % (s["name"], w["lede"], items, w["season"]))


def state_scope(s, band):
    """What this state actually requires you to register.

    Straight off the Coast Guard's own summary of each state's system, which
    is the authoritative answer to "do I have to register my kayak" - a real
    query with a different answer in nearly every state.
    """
    _f, _r, scope = USCG_FLEET[s["slug"]]
    return (band.open() + '<div class=w><div class=prose>'
      '<h2>What has to be registered in %s</h2>'
      '<div class=rule><p><strong>%s registers:</strong> %s.</p></div>'
      '<p>That is the Coast Guard&rsquo;s own summary of the %s system. It '
      'matters because it decides whether you need a number on the bow at '
      'all &mdash; the answer for a kayak or a canoe is different in nearly '
      'every state, and a boat that does not need registering does not need '
      'numbers from us either. If you are not required to register it, we '
      'would rather tell you that than sell you a set.</p>'
      '</div></div></section>'
      % (s["name"], s["name"], scope[0].lower() + scope[1:], s["agency"]))


def build_state(s):
    path = "/registration-numbers/%s/" % s["slug"]
    trail = [("By state", "/registration-numbers/"), (s["name"], None)]
    nm, ab = s["name"], s["ab"]
    vern = s.get("vern")
    h1 = ("%s Boat Registration Numbers: %s Prefix, Legal 3-Inch Block"
          % (nm, ab))
    title = "%s Boat Registration Numbers %s" % (nm, ab)
    desc = ("%s boat registration numbers, $%d a pair with free shipping. Legal "
            "3-inch block vinyl starting with %s, proof emailed within 12 hours."
            % (nm, PRICE["numbers"], ab))
    example = "%s 1234 AB" % ab
    faqs = [
      ("How tall do %s boat registration numbers have to be?" % nm,
       "Not less than 3 inches, in plain vertical block characters. That is the federal "
       "minimum under 33 CFR 173.27 and it applies in %s like everywhere else. Taller "
       "is always legal." % nm),
      ("What do %s boat numbers start with?" % nm,
       "<strong>%s</strong>. Your full number runs prefix, digits, then a letter suffix "
       "&mdash; for example %s. Copy it off your registration card exactly rather than "
       "guessing the spacing." % (ab, example)),
      ("Who issues boat registration in %s?" % nm,
       "You register through %s. We only make the decals &mdash; you get the number "
       "from them first, then we cut it."
       % s.get("register_at", "the " + s["agency"])),
      ("Do the numbers need a space or a hyphen?",
       "Yes. The rule requires a space or hyphen between the letter and number groups, "
       "about as wide as one character. So %s, not %s. Ours arrive pre-spaced correctly, "
       "so you cannot get this wrong." % (example, example.replace(" ", ""))),
      ("Where do they go on the boat?",
       "Each side of the forward half of the hull, reading left to right, in a color "
       "that contrasts with the hull. " +
       (html.unescape(s["decal"]).replace("<strong>", "").replace("</strong>", "")
        if s.get("decal") else
        "The validation decal goes near the number &mdash; %s publishes the exact "
        "offset, and it is usually within a few inches." % nm)),
    ]
    # Statewide AEO: these are the questions people type with a state name in
    # them, and every answer here is backed by something on the page - the
    # Coast Guard scope line, the Coast Guard count, or the waters research.
    _fleet, _rank, _scope = USCG_FLEET[s["slug"]]
    _w = WATERS.get(s["slug"])
    faqs += [
      ("Do I have to register a kayak or canoe in %s?" % nm,
       "%s registers %s. If your boat falls outside that, it does not need a "
       "registration number on the bow &mdash; and it does not need a set from us "
       "either. This is the Coast Guard's own summary of the %s system."
       % (nm, _scope[0].lower() + _scope[1:], s["agency"])),
      ("How many registered boats are there in %s?" % nm,
       "%s, which puts %s %s in the country. That is the Coast Guard's 2024 count, "
       "from Recreational Boating Statistics, Table 38."
       % ("{:,}".format(_fleet), nm, ordinal(_rank))),
    ]
    if _w:
        faqs.append(
          ("Where are the best places to boat in %s?" % nm,
           "%s %s" % (_w["waters"][0][0] + " is the one most people name first: "
                      + _w["waters"][0][1].rstrip(".") + ".",
                      "Others worth knowing: " + ", ".join(
                        n for n, _ in _w["waters"][1:5]) + ".")))
        faqs.append(
          ("When is boating season in %s?" % nm, _w["season"]))
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path),
                product_node(PRODUCTS[0], path))
    note = '<div class=note><p><b>%s specifics.</b> %s</p></div>' % (nm, s["note"]) \
           if s.get("note") else ""
    # Prefix traps: say it loudly on the page for the state it affects.
    # Uses POSTAL_TO_VESSEL, not the validator's POSTAL_MISTAKE - the validator
    # excludes MI and MS because typing them is ambiguous, but on Michigan's own
    # page there is nothing ambiguous about saying "yours is MC, not MI".
    postal = {v: k for k, v in POSTAL_TO_VESSEL.items()}.get(ab)
    if postal:
        note += ('<div class=note><p><b>Watch the prefix.</b> %s boat numbers start '
                 'with <strong>%s</strong>, not %s. The vessel prefixes were set by '
                 'the Coast Guard in 1958, five years before the Post Office picked '
                 'its own two-letter codes, and the two never got reconciled. Our '
                 'order form checks it for you.</p></div>'
                 % (nm, ab, postal))
    vb = ""
    if vern:
        vb = ('<p>Worth knowing: locally these are almost never called '
              '&ldquo;%s boat registration numbers.&rdquo; They are called '
              '<strong>%s</strong>, and that is what to search for and what the '
              'ramp conversation will use.</p>' % (nm, vern))
    # The prose, as one body. alternating() splits it on <h2> and lays each
    # section beside an image, so the pairing below is semantic rather than
    # decorative: the state's own hull next to its format, the registration
    # card next to "getting the number", what arrives next to "ordering".
    body = (note
      + ('<h2>What a %s number looks like</h2>'
         '<p>A %s registration number is built from three parts: the state prefix '
         '<strong>%s</strong>, a block of digits, and a letter suffix. Written out with '
         'the spacing the law requires, it looks like <strong>%s</strong>.</p>'
         % (nm, nm, ab, example))
      + ('<p><strong>%s format:</strong> %s.</p>' % (nm, s["fmt"]) if s.get("fmt") else "")
      + ('<h2>Where the validation decal goes in %s</h2><p>%s</p>' % (nm, s["decal"])
         if s.get("decal") else "")
      + vb
      + CB.FED_RULE
      + ('<h2>Getting the number in the first place</h2>'
         '<p>Register the boat through <strong>%s</strong> first. That is where the '
         'number and the validation decal come from. We are a vinyl shop, not a '
         'registry &mdash; we cannot look your number up or issue one, so order once '
         'you have the certificate in hand and copy the line straight off it.</p>'
         % s.get("register_at", "the " + s["agency"]))
      + CB.CONTRAST_NOTE
      + '<h2>Ordering for a %s boat</h2>'
        '<p>Type the number as it appears on your card, pick a color that contrasts with '
        'your hull, and leave the height at 3 inches unless you want it bolder. You will '
        'see your exact lettering in the preview before you pay &mdash; that is what '
        'gets cut.</p>' % nm)

    own = PAGE_IMAGE.get(path)
    imgs = ([own] if own else []) + ["AL-01", "HB-4", "PR-1", "PR-6"]
    band = Band()
    main = (hero(h1,
            "Legal 3-inch block numbers starting with %s, cut from marine vinyl, "
            "pre-spaced on one sheet for each side of the hull. Free shipping, shipped "
            "1-2 business days after you approve your proof." % ab,
            trust=[PRICE_CHIP, "%s prefix" % ab, "Proofed Before We Cut",
                   "Meets 33 CFR 173.27"],
            right=O.form())
      + state_identity(s, band)
      + alternating(body, imgs, band)
      + state_waters(s, band)
      + state_scope(s, band)
      + cta_band(band)
      + band.open() + '<div class=w><h2>Other states</h2>' + state_wheel(current=s["slug"])
      + '</div></section>')
    write(path, shell(title, desc, path, sch, main, trail=trail, faqs=faqs,
                      faq_heading="%s questions" % nm, js=ORDER_JS), "0.7")

def build_states_hub():
    path = "/registration-numbers/"
    trail = [("Numbers by state", None)]
    faqs = [
      ("Does every state use the same rule?",
       "The core rule is federal and identical everywhere: 3-inch minimum, plain vertical "
       "block characters, contrasting color, spaces or hyphens between groups, reading "
       "left to right, on both sides of the forward half. States can add requirements on "
       "top but cannot go below it. What genuinely varies is the prefix, the issuing "
       "agency, and exactly where the validation decal sits."),
      ("Which states do not use their postal abbreviation?",
       "California is the big one - California boat numbers start with CF, not CA, and "
       "everyone there calls them CF numbers. Washington uses WN rather than WA. Always "
       "copy the prefix off your own registration card rather than assuming."),
      ("My state is not listed. Can you still cut my numbers?",
       "Yes. We cut for all 50 states and DC - these are just the pages we have written "
       "up so far. Pick 'Other / not listed' on the order form and type your number."),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path))
    rows = "".join('<tr><td><a href="/registration-numbers/%s/"><strong>%s</strong></a></td>'
                   '<td><strong>%s</strong></td><td>%s</td><td>#%d</td><td>%s</td></tr>'
                   % (s["slug"], s["name"], s["ab"],
                      "{:,}".format(USCG_FLEET[s["slug"]][0]),
                      USCG_FLEET[s["slug"]][1], s["agency"])
                   for s in sorted(STATES, key=lambda x: -USCG_FLEET[x["slug"]][0]))
    main = (hero("Boat Registration Numbers by State",
            "The 3-inch block rule is federal and the same everywhere. What changes is "
            "your prefix, who issues the number, and where the validation decal goes. "
            "$%d a pair, every state." % PRICE["numbers"],
            trust=[PRICE_CHIP, "All 50 states", "Proofed Before We Cut",
                   "Meets 33 CFR 173.27"],
            right=O.form())
      + '<section><div class=w>' + lead_figure(path) + '<h2>Pick your state</h2>'
      + state_wheel()
      + '<h2 style="margin-top:34px">Prefix, fleet size and who issues it</h2>'
        '<p class=lede>Registered-vessel counts below are the Coast Guard\'s 2024 '
        'figures, not estimates. They are a useful sanity check: the bigger the fleet, '
        'the longer the queue at your local shop in April. Nationally there are '
        '%s registered recreational vessels.</p>'
        '<div class=tw><table><thead><tr><th>State</th><th>Prefix</th>'
        '<th>Registered vessels</th><th>US rank</th><th>Issuing agency</th>'
        '</tr></thead><tbody>' % "{:,}".format(USCG_NATIONAL)
        + rows + '</tbody></table></div>'
      + '<div class=prose>' + CB.FED_RULE + '</div>'
      + '<a class="btn lg" href="/design/">Start your order</a></div></section>')
    write(path, shell("Boat Registration Numbers by State - All 50",
          "Boat registration numbers for every state, $%d a pair with free "
          "shipping. State prefixes, issuing agencies and the federal 3-inch "
          "block rule explained." % PRICE["numbers"],
          path, sch, main, trail=trail, faqs=faqs), "0.9")

# ------------------------------------------------------------ boat types
def build_boat_type(b):
    path = "/for/%s/" % b["slug"]
    trail = [("By boat type", None), (b["nav"], None)]
    faqs = [
      ("Will these stick to my %s?" % b["nav"].lower().rstrip("s"),
       b["note"]),
      ("Do I need registration numbers on it?",
       "If it has a motor on it - including an electric trolling motor in most states - "
       "yes. Unpowered hulls usually do not need numbers, but a few states register "
       "them anyway. Check with your state agency, then order."),
      ("What does it cost?",
       "Registration numbers are $%d a pair including shipping. Names start at "
       "$%d and are priced by the width they finish at. High-tack vinyl, which "
       "your hull may need, is free."
       % (PRICE["numbers"], PRICE["name_from"])),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path))
    main = (hero(b["title"], b["lead"],
            trust=[PRICE_CHIP, "High-tack when needed, free",
                   "Proofed Before We Cut", "Meets 33 CFR 173.27"], right=O.form())
      + '<section><div class=w><div class=prose>'
        '<div class=note><p><b>The thing that matters on this hull.</b> %s</p></div>'
        '<h2>What we cut for %s</h2>'
        '<p>Registration numbers, boat names and custom lettering. Everything arrives '
        'pre-spaced on one sheet with application tape over the top, so you apply the '
        'whole set in a single pass rather than placing loose characters.</p>'
        '<h2>Ordering</h2>'
        '<p>Tell us the boat on the order form &mdash; make, model and roughly the year. '
        'That is how we decide whether to send standard or high-tack film, and we would '
        'rather get that right than have you peel a set off in August.</p>'
        '</div><a class="btn lg" href="/design/">Start your order</a></div></section>'
        % (b["note"], b["nav"].lower())
      + (gallery([PAGE_IMAGE["/for/%s/" % b["slug"]]],
                  heading="On this kind of boat")
         if ("/for/%s/" % b["slug"]) in PAGE_IMAGE else '')
      + product_grid(heading="Products for this boat"))
    write(path, shell(b["title"].replace("&amp;", "&")[:58],
          "%s - cut from marine vinyl, $%d a pair for registration numbers, free "
          "shipping, proof in 12 hours."
          % (b["title"].replace("&amp;", "&"), PRICE["numbers"]),
          path, sch, main, trail=trail, faqs=faqs, js=ORDER_JS), "0.7")

# ----------------------------------------------------------------- tools
def tool_shell(t, body, js, faqs, extra_schema=None):
    path = "/tools/%s/" % t["slug"]
    trail = [("Free tools", None), (t["nav"], None)]
    app = {"@type": "WebApplication", "@id": U(path) + "#app", "name":
           html.unescape(t["title"]), "url": U(path),
           "applicationCategory": "UtilitiesApplication",
           "operatingSystem": "Any", "browserRequirements": "Requires JavaScript",
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
           "publisher": {"@id": U("/#org")}}
    sch = graph(org_node(), crumb_node(trail, path), app, faq_node(faqs, path),
                extra_schema)
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">%s</h1>'
            % t["title"]) + lead_figure(path) + body + '</div></section>'
    write(path, shell(html.unescape(t["title"])[:58], t["desc"], path, sch, main,
                      trail=trail, faqs=faqs, js=js), "0.8")

def build_tool_names():
    t = TOOLS[0]
    body = ('<p class=lede>Twenty-two categories nobody else bothered to write &mdash; '
            'double meanings, deadpan one-liners, anagrams, head scratchers, pontoon-dad '
            'energy, slightly haunted. Every name gets a radio-call test and a '
            'transom-width estimate. When one sticks, we cut it in Evansdale from '
            '$%d.</p>' % PRICE["name_from"]
            + NG.markup()
            + '<div class=prose>'
            '<h2>How to actually pick one</h2>'
            '<p>Four tests, in order of how much they will matter later. The generator '
            'runs the first three for you.</p>'
            '<ol><li><strong>Say it as a radio call.</strong> &ldquo;Mayday, mayday, this '
            'is <em>Wet Couch</em>&rdquo; is a sentence you may one day have to say to the '
            'Coast Guard in front of your family. Click any name to see how it reads on '
            'channel 16.</li>'
            '<li><strong>Spell it over the radio.</strong> If it needs spelling twice, it '
            'is too clever. Short and phonetic wins. The deliberately-misspelled category '
            'is funny on the dock and a full-time job on the VHF.</li>'
            '<li><strong>Count the characters.</strong> At 4 inches tall each character '
            'takes about 2.5 inches of width, so a 22-character name runs over five feet. '
            'The estimate is on every card &mdash; measure the transom before you fall in '
            'love.</li>'
            '<li><strong>Check it is not already on your lake.</strong> There is exactly '
            'one <em>Serenity</em> per marina and it is awkward for everybody. That is the '
            'whole reason the weird categories exist.</li></ol>'
            '<h2>Renaming a boat</h2>'
            '<p>Sailors will tell you renaming is bad luck unless you hold a ceremony that '
            'involves telling Poseidon in writing and pouring champagne into the water. '
            'Practically: remove every trace of the old name first &mdash; logbooks, life '
            'rings, the lot &mdash; then apply the new one. Our '
            '<a href="/guides/how-to-remove-boat-lettering/">removal guide</a> covers '
            'getting the old vinyl off without hazing the gelcoat.</p>'
            '<p>If the vessel is USCG documented, the name is on the certificate and you '
            'have to file to change it. State-registered boats have no such paperwork '
            '&mdash; the name is decoration and you can change it on a Saturday.</p>'
            '</div>'
            '<a class="btn lg" href="/design/">Get your name cut &middot; from $%d</a>'
            % PRICE["name_from"])
    faqs = [
      ("Is the boat name generator free?",
       "Yes, and there is no email wall. Spin it as long as you like. We make money when "
       "you decide to put one on the boat."),
      ("Can I use a boat name someone else already has?",
       "On a state-registered boat, yes - boat names are not registered or protected, and "
       "there are hundreds of boats called Serenity. On a USCG documented vessel the name "
       "goes on the certificate, and the Coast Guard will not document two vessels with "
       "the same name and hailing port."),
      ("How much does a boat name decal cost?",
       "From $%d including shipping. Most transom names land between $%d and $%d "
       "depending on the width they finish at."
       % (PRICE["name_from"], PRICE["name_from"], PRICE["name_typical_to"])),
      ("How many characters fit on my transom?",
       "Rough maths: at 4 inches tall, each character takes about 2.5 inches of width "
       "including spacing. A 10-character name runs about 25 inches. Send us a photo with "
       "a tape measure in it and we will lay it out properly."),
      ("Are these boat names family friendly?",
       "PG-13. Nothing here will get you a conversation with the marina manager, but a "
       "couple will get you a look from your mother-in-law."),
    ]
    tool_shell(t, body + share_block(
        '/tools/boat-name-generator/', U('/tools/boat-name-generator/'),
        '/assets/share/name-wet-couch.png'),
            NG.data_js() + NG.NAMES_JS, faqs)

def build_tool_funny():
    t = TOOLS[1]
    groups = "".join(
        '<h2>%s</h2><div class=names>%s</div>'
        % (g, "".join("<div>%s</div>" % e(n) for n in names))
        for g, names in T.FUNNY_GROUPS)
    body = ('<p class=lede>Sorted by how the joke actually lands, not alphabetically. '
            'The ones in the first group get a laugh; the ones in the last group get you '
            'a conversation at the fuel dock whether you wanted one or not.</p>'
            + groups
            + '<div class=prose><h2>The ones we would talk you out of</h2>'
            '<p>We will cut anything legal, but two categories come back as regrets:</p>'
            '<ul><li><strong>Anything you have to explain.</strong> If the pun needs a '
            'setup, it is not a boat name, it is a bit.</li>'
            '<li><strong>Anything you would not say to the Coast Guard.</strong> Your boat '
            'name is what you broadcast in an emergency and what goes in an incident '
            'report. <em>Multiple Scoregasms</em> is a famous boat name and it was famously '
            'read out in a rescue transcript.</li></ul>'
            '<h2>Still stuck?</h2>'
            '<p>Our <a href="/tools/boat-name-generator/">name generator</a> spins classic, '
            'nautical, fishing and retirement names as well as funny ones, and will keep '
            'going as long as you keep clicking.</p></div>'
            '<a class="btn lg" href="/design/">Put one on the transom '
            '&middot; from $%d</a>' % PRICE["name_from"])
    faqs = [
      ("What is the most common funny boat name?",
       "Variations on 'Knot' - Knot Working, Knot Guilty, Knot Paid For - and 'Seas the "
       "Day'. They are common because they are genuinely good puns, which is also the "
       "argument against using them."),
      ("Can I put a rude name on my boat?",
       "Legally, in US waters, there is no decency rule on a state-registered boat name. "
       "Marinas can have their own rules, and the Coast Guard will refuse to document a "
       "vessel with an obscene name. We will cut it; we would just point out you have to "
       "say it on the radio."),
      ("How much is a boat name decal?",
       "From $%d with free shipping, pre-spaced and ready to apply. Most land "
       "between $%d and $%d depending on the width they finish at."
       % (PRICE["name_from"], PRICE["name_from"], PRICE["name_typical_to"])),
    ]
    tool_shell(t, body, "", faqs)

def build_tool_hin():
    t = TOOLS[2]
    data = "window.BNS_MIC={%s};" % ",".join('"%s":"%s"' % (k, v.replace('"', ''))
                                             for k, v in T.MIC.items())
    body = ('<p class=lede>A hull identification number is the 12-character code the '
            'builder stamped into your transom. Paste it below and we will read the '
            'manufacturer, serial, build date and model year out of it.</p>'
            '<div class=tool>'
            '<label for=hin>Your 12-character HIN</label>'
            '<div class="fieldrow two"><div>'
            '<input type=text id=hin maxlength=20 placeholder="BUJ12345A404" autocomplete=off>'
            '<div class=hint>Starboard side of the transom, up near the top edge. '
            'Spaces and hyphens are ignored.</div></div>'
            '<div style="display:flex;align-items:flex-start">'
            '<button type=button class=btn id=hinbtn style="width:100%">Decode it</button>'
            '</div></div>'
            '<div class=out id=hinout></div></div>'
            '<div class=prose>'
            '<h2>How a HIN is put together</h2>'
            '<p>Since August 1984 every hull sold in the US carries a 12-character HIN in '
            'a fixed format:</p>'
            '<div class=tw><table><thead><tr><th>Position</th><th>What it is</th>'
            '<th>Example</th></tr></thead><tbody>'
            '<tr><td>1&ndash;3</td><td>Manufacturer Identification Code (MIC), assigned by '
            'the US Coast Guard</td><td><strong>BUJ</strong> = Bayliner</td></tr>'
            '<tr><td>4&ndash;8</td><td>Hull serial number, the builder&rsquo;s own '
            'sequence</td><td>12345</td></tr>'
            '<tr><td>9&ndash;10</td><td>Month and year of build &mdash; A=January through '
            'L=December, then the year digit</td><td><strong>A4</strong> = January, '
            'year ending 4</td></tr>'
            '<tr><td>11&ndash;12</td><td>Model year</td><td>04 = 2004</td></tr>'
            '</tbody></table></div>'
            '<h2>A HIN is not your registration number</h2>'
            '<p>People mix these up constantly, so plainly:</p>'
            '<ul><li>The <strong>HIN</strong> is permanent, assigned by the builder, '
            'stamped into the hull, and never displayed in large letters. It is the '
            'boat&rsquo;s VIN.</li>'
            '<li>The <strong>registration number</strong> is issued by your state, changes '
            'if you move or re-register, and is the one you must display in 3-inch block '
            'characters on both sides of the bow.</li></ul>'
            '<p>If you came here because you need the second one made, that is what we do '
            '&mdash; <a href="/design/">$28 a pair</a>.</p>'
            '<h2>If the HIN is missing or unreadable</h2>'
            '<p>Pre-1972 hulls may genuinely never have had one. From 1972 onward it should '
            'be there, and a hull with a ground-off or illegible HIN is a serious red flag '
            'on a used purchase &mdash; it is how stolen boats get laundered. Your state '
            'agency can issue a replacement HIN for a legitimately unmarked hull, but you '
            'will need to prove ownership.</p>'
            '<p>Check the starboard transom first, then inside a locker or under the gunwale '
            'on the starboard side &mdash; builders are required to put a duplicate in an '
            'unexposed location.</p>'
            '</div>')
    faqs = [
      ("How do I find the hull number on my boat?",
       "Starboard side of the transom, within a couple of inches of the top edge. There is "
       "also a duplicate hidden somewhere unexposed - inside a locker, under the gunwale, "
       "or beneath a deck plate on the starboard side."),
      ("Can you tell the year of a boat by the hull number?",
       "Yes. The last two characters are the model year, and characters 9-10 give the month "
       "and year it was actually built. The two can differ - a boat built in September 2003 "
       "is commonly a 2004 model."),
      ("Is the hull number the same as the VIN?",
       "It is the same idea - a permanent, unique builder-assigned identifier - but boats "
       "use a 12-character HIN rather than a 17-character VIN, and the formats are "
       "different. Boat trailers have their own separate VIN."),
      ("What happens if my boat has no Hull Identification Number?",
       "Hulls built before 1972 may never have had one. After that it is required, and a "
       "missing or altered HIN is a major warning sign on a used boat. Your state agency "
       "can assign a replacement HIN if you can document ownership."),
      ("Can I look up who owns a boat from the HIN?",
       "Not publicly, in most states - ownership records are restricted. A HIN will tell "
       "you the builder, serial and age, and USCG documented vessels are searchable in the "
       "federal vessel database, but state registration owner data generally is not open."),
    ]
    tool_shell(t, body, SH.decode_js() + T.HIN_JS, faqs)

def build_tool_layout():
    t = TOOLS[3]
    hull = ["White", "Black", "Navy", "Light Blue", "Red", "Gray", "Forest",
            "Burgundy", "Tan", "Silver", "Yellow"]
    body = ('<p class=lede>Type your registration number, pick your hull color, and this '
            'checks it against every part of the federal rule &mdash; then tells you how '
            'wide the finished set will be so you can measure before you order.</p>'
            '<div class=tool>'
            '<div class="fieldrow two"><div><label for=chknum>Your registration number</label>'
            '<input type=text id=chknum value="TX 1234 AB" maxlength=40 autocomplete=off>'
            '<div class=hint>Type it with the spaces, exactly as on your card.</div></div>'
            '<div><label for=chkh>Character height</label><select id=chkh>'
            '<option value="2">2&quot;</option><option value="3" selected>3&quot;</option>'
            '<option value="4">4&quot;</option><option value="5">5&quot;</option>'
            '<option value="6">6&quot;</option></select></div></div>'
            '<div class="fieldrow two" style="margin-top:13px">'
            '<div><label for=chkhull>Hull color</label><select id=chkhull>'
            + "".join('<option%s>%s</option>' % (" selected" if h == "White" else "", h)
                      for h in hull) + '</select></div>'
            '<div><label for=chkcol>Number color</label><select id=chkcol>'
            + "".join('<option%s>%s</option>' % (" selected" if h == "Black" else "", h)
                      for h in hull) + '</select></div></div>'
            '<button type=button class="btn lg" id=chkbtn style="margin-top:15px">'
            'Check it</button>'
            '<div class=out id=chkout></div></div>'
            '<div class=prose>' + CB.FED_RULE +
            '<h2>The two things this catches most</h2>'
            '<p><strong>No spacing.</strong> People order TX1234AB because that is how it '
            'is printed on some cards. The rule wants a gap about one character wide '
            'between the letter and number groups. We pre-space every set correctly, but '
            'if you are cutting your own or buying loose characters, this is the one that '
            'fails an inspection.</p>'
            '<p><strong>No contrast.</strong> There is no required color, but the '
            'characters must contrast with the background and be distinctly visible. White '
            'on white is the classic failure &mdash; and it happens because white vinyl is '
            'the default on most cheap sets.</p>'
            '<h2>Measuring your hull first</h2>'
            '<p>You need a flat run on the forward half of the hull, above the waterline, '
            'long enough for the width this tool gives you, and tall enough to clear your '
            'character height with a little margin. Watch out for rub rails, strakes and '
            'rivet lines &mdash; vinyl will not bridge a hard edge and stay stuck. On a '
            'ribbed aluminum hull, keep the whole set between two ribs.</p>'
            '</div>')
    faqs = [
      ("How tall do boat registration numbers have to be?",
       "Not less than 3 inches in height, in plain vertical block characters. Federal rule, "
       "every state. Taller is always legal."),
      ("Do boat registration numbers have to be a certain color?",
       "No specific color is required, but the characters must contrast with the color of "
       "the background and be distinctly visible and legible. White numbers on a white hull "
       "fail that test."),
      ("Do I need a space or a hyphen in my boat number?",
       "Yes - a space or hyphen equal to the width of a letter other than 'I' or a number "
       "other than '1', between the letter and number groupings. So TX 1234 AB."),
      ("How wide will my registration numbers be?",
       "Roughly 0.6 times the character height per character, plus the spaces. A "
       "six-character number at 3 inches finishes about 13-15 inches wide. The tool above "
       "calculates it for your exact number."),
    ]
    tool_shell(t, body, SH.decode_js() + SH.SHIM_JS + T.LAYOUT_JS, faqs)

def build_tools_hub():
    path = "/tools/"
    trail = [("Free tools", None)]
    sch = graph(org_node(), crumb_node(trail, path))
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">Free boat tools</h1>'
            '<p class=lede>No signup, no email wall. These are genuinely useful on their '
            'own &mdash; we built them because the people who need them usually need '
            'vinyl afterwards.</p>' + lead_figure(path) + tools_grid() + '</div></section>')
    write(path, shell("Free Boat Tools - HIN Decoder, Name Generator",
          "Free boat tools: decode a hull identification number, generate boat name ideas, "
          "and check your registration number against the federal size and spacing rules.",
          path, sch, main, trail=trail), "0.8")

# ---------------------------------------------------------------- guides
GUIDE_BODY = {
 "boat-registration-number-rules":
   CB.FED_RULE +
   "<h2>Why it is one rule and not fifty</h2>"
   "<p>Boat numbering comes from the Federal Boat Safety Act, and states administer it "
   "under a federally approved numbering system. That is why the core requirements are "
   "identical from Florida to Alaska: a state can add requirements, but it cannot issue "
   "you a number and then let you display it smaller than 3 inches.</p>"
   "<p>So when a shop tells you &ldquo;your state is different,&rdquo; what they almost "
   "always mean is one of three things: your prefix, your issuing agency, or where the "
   "validation decal goes.</p>" + CB.CONTRAST_NOTE +
   "<h2>The five failures we see</h2>"
   "<ol><li><strong>Characters under 3 inches.</strong> Usually because someone bought a "
   "set sized to fit a small panel instead of sizing the panel to the rule.</li>"
   "<li><strong>No contrast.</strong> White on white, or a dark navy on black.</li>"
   "<li><strong>No spacing.</strong> TX1234AB run together, because that is how it looks "
   "on some registration cards.</li>"
   "<li><strong>Script or outline fonts.</strong> The rule says plain vertical block. An "
   "outline font with a hollow center is not plain block.</li>"
   "<li><strong>Too far aft.</strong> They have to be on the forward half. Numbers on the "
   "stern quarter are a common and easily avoided ticket.</li></ol>"
   "<h2>What about documented vessels?</h2>"
   "<p>Different rules entirely. A USCG documented vessel does not display state "
   "registration numbers at all &mdash; it carries its name and hailing port in 4-inch "
   "characters instead. See our "
   "<a href=\"/guides/documented-vessel-name-and-hailing-port/\">documented vessel "
   "guide</a>.</p>",

 "where-to-put-boat-registration-numbers":
   "<p>Short answer: <strong>on both sides of the forward half of the hull, reading left "
   "to right, high enough to be clearly visible from the water.</strong> That is the "
   "whole requirement. Everything below is how to get it right in practice.</p>"
   + CB.FED_RULE +
   "<h2>&ldquo;Forward half&rdquo; means exactly that</h2>"
   "<p>Measure your hull length, halve it, and your numbers must sit in the front "
   "portion. In practice almost everybody puts them as far forward as the hull shape "
   "allows, because that is where the panel is flattest and the numbers look intentional "
   "rather than stuck in the middle of the boat.</p>"
   "<h2>How high above the waterline</h2>"
   "<p>No rule specifies a height off the water. Use judgement: high enough that the "
   "numbers are not permanently submerged in spray or buried by the bow wave at speed, "
   "and not so high they wrap over the gunwale. On most runabouts that lands just below "
   "the rub rail. Keep the whole character height on one flat plane &mdash; vinyl that "
   "bridges a hard chine or a strake will lift at the edge within a season.</p>"
   "<h2>Both sides, and both reading forward</h2>"
   "<p>This trips people up: the numbers read left to right <em>on each side</em>. They "
   "are not mirrored. You are not making a reversed set for the port side &mdash; you are "
   "making two identical sets, and each one reads normally to somebody standing beside "
   "that side of the boat.</p>"
   "<h2>Where the validation decal goes</h2>"
   "<p>Your state also issues a small validation or expiry decal, and this is the piece "
   "that genuinely varies. Most states want it within a few inches of the registration "
   "number &mdash; commonly aft of the number on both sides, sometimes forward of it, "
   "sometimes on one specific side only. Your registration paperwork states it, and it is "
   "worth reading, because a correctly sized number with the decal in the wrong place is "
   "still a correctable violation.</p>"
   "<h2>Rivets, ribs and textured aluminum</h2>"
   "<p>On a jon boat or a riveted aluminum hull, place the full set between two ribs on "
   "a flat panel. Do not run vinyl over a rivet head and expect it to hold &mdash; the "
   "adhesive cannot make contact around the dome, water gets under it and the character "
   "peels from that point. If there is not enough clear panel, drop to 3 inches exactly "
   "and gain the width back, or mount a flat backing plate, which the regulation "
   "explicitly allows.</p>",

 "how-to-apply-boat-lettering":
   "<p>Pre-spaced lettering goes on in one pass and the whole job takes about twenty "
   "minutes a side. The wet method is the forgiving one and it is what we recommend for "
   "anything up to about three feet wide.</p>" + CB.APPLY_STEPS +
   "<h2>Wet or dry?</h2>"
   "<p><strong>Wet</strong> for lettering and numbers: the soapy water stops the adhesive "
   "grabbing instantly, so you can slide the piece into position and squeegee the water "
   "out. Forgiving, slightly slower to cure.</p>"
   "<p><strong>Dry</strong> for long stripes and very large graphics: water trapped under "
   "a 20-foot run has nowhere to go and will leave you with a stripe full of bubbles. Use "
   "a hinge of tape, peel progressively, and squeegee as you advance.</p>"
   "<h2>The four ways this goes wrong</h2>"
   "<ul><li><strong>Wax on the hull.</strong> The single biggest cause of failure. Vinyl "
   "will not bond to wax or polish. Alcohol wipe, every time.</li>"
   "<li><strong>Too cold.</strong> Under about 50&deg;F the adhesive barely tacks and you "
   "will think the vinyl is faulty. It is not; it is February.</li>"
   "<li><strong>Pulling the tape straight out.</strong> Pull it back flat against itself "
   "at a sharp angle. Pulling outward lifts the characters with it.</li>"
   "<li><strong>Impatience.</strong> If letters lift with the tape, lay it back down, "
   "squeegee hard, and wait another fifteen minutes.</li></ul>"
   "<h2>Bubbles afterwards</h2>"
   "<p>Small bubbles in the first day will often disappear on their own as the solvent "
   "flashes off through the film. For one that stays, prick it at the edge with a pin "
   "&mdash; not the center &mdash; and press the air out toward the hole with your thumb.</p>"
   "<div class=note><p><b>Take your time with it.</b> Everything is pre-spaced on one "
   "sheet with application tape over the top, so the whole set goes on in a single "
   "pass &mdash; the spacing is already done and already legal. The twenty minutes "
   "this takes is the whole job.</p></div>",

 "how-to-remove-boat-lettering":
   "<p>Old vinyl comes off with heat and patience. The adhesive is the hard part, and "
   "gelcoat is softer than people think, so the order of operations matters.</p>"
   "<ol class=steps>"
   "<li><strong>Heat it.</strong> A heat gun on low, or a hairdryer, or genuinely just a "
   "hot sunny afternoon. Warm the character until the vinyl goes pliable. Do not cook it "
   "&mdash; you want it soft, not smoking, and sustained high heat can blister gelcoat.</li>"
   "<li><strong>Lift an edge with plastic.</strong> A plastic razor blade or an old credit "
   "card. Never a steel blade on gelcoat; it will leave scores you cannot polish out.</li>"
   "<li><strong>Peel slowly at a shallow angle.</strong> Keep heating just ahead of the "
   "peel. If it is tearing into confetti, it is not warm enough.</li>"
   "<li><strong>Attack the adhesive separately.</strong> Once the film is off you will have "
   "a sticky ghost. Adhesive remover, citrus-based cleaner, or mineral spirits on a rag. "
   "Let it dwell a minute, then wipe. Repeat rather than scrub hard.</li>"
   "<li><strong>Wash, then polish.</strong> Soap and water to get the solvent off, then "
   "polish or compound the area.</li></ol>"
   "<h2>About the shadow</h2>"
   "<p>Here is the part nobody warns you about: under the old lettering, the gelcoat has "
   "been shaded from UV for years. The hull around it has faded. Remove the vinyl and you "
   "get a perfect darker outline of the old name &mdash; the ghost.</p>"
   "<p>Polishing or compounding the whole panel, not just the letter area, blends it. On a "
   "badly oxidised hull you may need to compound the full side. The alternative that costs "
   "nothing: make the new lettering slightly larger than the old, so it covers the "
   "shadow.</p>"
   "<div class=note><p><b>Plan for this when renaming.</b> Send us a photo of the old name "
   "with a tape measure in frame and we will size the new one to cover the ghost line. It "
   "is free and it saves an afternoon of compounding.</p></div>"
   "<h2>What not to use</h2>"
   "<ul><li><strong>Steel blades or scrapers</strong> on gelcoat or paint.</li>"
   "<li><strong>Acetone</strong> &mdash; it will soften gelcoat and ruin paint and "
   "clearcoat.</li>"
   "<li><strong>Pressure washers</strong> to blast vinyl off. It drives water behind the "
   "film and under trim, and it will not remove the adhesive anyway.</li>"
   "<li><strong>Power tools with eraser wheels</strong> unless you have used one before. "
   "They work fast and they burn through gelcoat faster.</li></ul>",

 "boat-lettering-fonts":
   "<p>Two different jobs with two different answers. Registration numbers have a legal "
   "constraint. A transom name does not, and that is where you get to have taste.</p>"
   "<h2>For registration numbers: block, and nothing else</h2>"
   "<p>The rule says <strong>plain vertical block characters</strong>. That rules out:</p>"
   "<ul><li>Script and cursive of any kind</li>"
   "<li>Italic or slanted faces &mdash; &ldquo;vertical&rdquo; is in the rule</li>"
   "<li>Outline-only fonts with a hollow center</li>"
   "<li>Heavily stylised display faces, western or gothic</li></ul>"
   "<p>Of the ten faces we cut, five qualify: <strong>Block, Condensed, Heavy Impact, "
   "Modern and Stencil</strong>. Our order form only offers those five once you pick "
   "registration numbers, so you cannot accidentally order an unlawful set.</p>"
   "<h2>For a boat name: the distance test</h2>"
   "<p>Whatever you pick has to survive being read from fifty yards away, at an angle, "
   "in glare, often from a moving boat. That rules out more than legality does:</p>"
   "<ul><li><strong>Weight beats flourish.</strong> Thin strokes vanish. If a script has "
   "hairline connectors, they will read as gaps.</li>"
   "<li><strong>Open counters.</strong> Tight interior shapes in letters like a, e and g "
   "fill in visually at distance and turn into blobs.</li>"
   "<li><strong>Beware all-caps script.</strong> Script faces are designed with lowercase. "
   "All-caps script is hard to read and looks like a wedding invitation.</li></ul>"
   "<h2>What people actually order</h2>"
   "<p>For classic boats: <strong>Classic Serif</strong> or <strong>Slab</strong> "
   "&mdash; restrained, reads as expensive. For sportfish and bass boats: "
   "<strong>Heavy Impact</strong> or <strong>Nautical</strong>, something with attitude. "
   "For sailboats: <strong>Formal Script</strong>, which is what a transom name has "
   "looked like for a century. For anything funny: the joke carries it, so pick the "
   "legible option and let the words do the work.</p>"
   "<p>Shadow or outline in a second color costs a little more and roughly doubles the "
   "perceived quality from a distance &mdash; it is the single best upgrade on a transom "
   "name.</p>",

 "best-vinyl-for-boat-lettering":
   "<p>Three decisions: cast or calendared, standard or high-tack, and whether you need "
   "a specialty finish. Get the second one wrong and your decal falls off.</p>"
   "<h2>Cast vs calendared</h2>"
   "<p><strong>Cast</strong> vinyl is made by pouring liquid resin onto a carrier and "
   "letting it cure flat. Because it is never stretched, it carries no internal stress, "
   "so it conforms to curves and stays where you put it. Thinner, more conformable, "
   "and the longer-lived of the two outdoors.</p>"
   "<p><strong>Calendared</strong> vinyl is squeezed between rollers into sheet. It is "
   "cheaper and slightly thicker, but it remembers being stretched and slowly tries to "
   "shrink back, which is what makes old decals pull away at the corners. Shorter "
   "outdoor life than cast, and shorter again on a dark color in southern sun.</p>"
   "<p>For a flat transom on a trailered boat, calendared is honestly fine and it is what "
   "we ship as standard. For a curved hull, a dark color, or a boat kept in a slip in "
   "Florida, pay the $8.</p>"
   "<h2>High-tack: not optional on plastic</h2>"
   "<p>Polyethylene &mdash; rotomoulded kayaks, PWC hulls, some pontoon furniture &mdash; "
   "has a low surface energy, which is a technical way of saying almost nothing sticks to "
   "it. Standard vinyl will hold for a few weeks and then release in one clean piece.</p>"
   "<p>High-tack film uses a much more aggressive adhesive designed for exactly this. We "
   "send it free on any kayak, canoe or PWC order, and on textured pontoon rails, because "
   "shipping the wrong film to save nothing is a bad trade.</p>"
   "<h2>What a film warranty actually covers</h2>"
   "<p>Honest version: it covers the <strong>film</strong> &mdash; color fade beyond a "
   "stated tolerance, cracking, and adhesive failure where the film was applied correctly "
   "to a suitable surface. It does not cover a decal applied over wax, applied in the "
   "cold, applied to a surface it was not specified for, or physically damaged.</p>"
   "<p>Worth being clear about the gap that leaves: the film warranty is the film "
   "maker&rsquo;s, and it covers the material. It does not cover the install, which is "
   "the part you do. That is the argument for taking the twenty minutes and reading the "
   "<a href=\"/guides/how-to-apply-boat-lettering/\">apply guide</a> first.</p>",

 "documented-vessel-name-and-hailing-port":
   "<p>If your vessel is documented with the US Coast Guard rather than registered with a "
   "state, you are in a different ruleset &mdash; and the most important part is what you "
   "<em>do not</em> display.</p>"
   "<div class=rule><p><strong>A documented vessel does not display state registration "
   "numbers on the bow.</strong> Instead it must be marked with its name and hailing port, "
   "in clearly legible characters not less than <strong>4 inches</strong> in height, "
   "together on some clearly visible exterior part of the hull &mdash; in practice, the "
   "transom. The official number is separately marked in the interior of the hull in "
   "3-inch characters, permanently affixed.</p></div>"
   "<h2>The hailing port</h2>"
   "<p>It has to include a <strong>place and a state</strong> &mdash; spelled out or "
   "properly abbreviated. <em>Galveston, TX</em> works. <em>Galveston</em> alone does "
   "not. It must match the hailing port on your Certificate of Documentation, and it does "
   "not have to be where you keep the boat or where you live.</p>"
   "<h2>Typical layout</h2>"
   "<p>Name on the upper line, usually 6 to 8 inches tall. Hailing port centred beneath "
   "it at 4 inches. If your transom is curved, send a straight-on photo with a tape "
   "measure and we will lay the name out to the actual curve.</p>"
   "<h2>Boats that are both</h2>"
   "<p>Some owners document federally <em>and</em> register with a state for tax or "
   "launch-permit purposes. If that is you, you still do not display the state number on "
   "the bow &mdash; you display the state validation decal, and keep the name and hailing "
   "port on the transom. Your state will tell you exactly where it wants the decal.</p>"
   "<p>We cut the <a href=\"/boat-lettering/\">name and the hailing port line</a> as "
   "lettering &mdash; order the name and tell us in the notes what the hailing port "
   "should read and how tall you need it.</p>",

 "boat-registration-number-cost":
   "<p>Registration number decals run roughly <strong>$15 to $39 a pair</strong> online "
   "in 2026. That is a wide band for what looks like the same product, so here is what "
   "actually drives it.</p>"
   "<div class=tw><table><thead><tr><th>Where</th><th>Typical price, a pair</th>"
   "<th>What you get</th></tr></thead><tbody>"
   "<tr><td>Marketplace sellers</td><td>$10&ndash;16</td><td>Usually calendared film, "
   "often cut as loose characters you space yourself, no format check, no "
   "warranty</td></tr>"
   "<tr><td>Generic sign shops</td><td>$9&ndash;15</td><td>Cheap, competent, not boat "
   "specialists &mdash; you will be asked to specify everything</td></tr>"
   "<tr><td>Boat lettering specialists</td><td>$15&ndash;25</td><td>Pre-spaced, marine "
   "film and a warranty. Most hide the price behind a design "
   "tool</td></tr>"
   "<tr><td><strong>Us</strong></td><td><strong>$28</strong></td><td>Pre-spaced, "
   "marine film, free shipping, your number checked against its state format before it "
   "cuts</td></tr>"
   "</tbody></table></div>"
   "<h2>What makes one set cost twice another</h2>"
   "<ul><li><strong>Film grade.</strong> Craft and sign-stock calendared versus marine "
   "cast. This is most of the difference, and you will not see it for a few "
   "summers.</li>"
   "<li><strong>Pre-spaced or loose.</strong> Pre-spacing is labour. Loose characters are "
   "cheaper to produce and much harder to install legally.</li>"
   "<li><strong>Shipping.</strong> A $12 set plus $6 shipping is an $18 set. Always "
   "compare delivered price.</li>"
   "<li><strong>Checking.</strong> Software that reads your number back to you before "
   "money and prevents the most expensive mistake, which is a wrong number.</li></ul>"
   "<h2>The hidden cost</h2>"
   "<p>A cheap set that chalks out early costs you another set plus the removal "
   "job &mdash; and removal is the part that takes the afternoon and risks the gelcoat. "
   "Our <a href=\"/guides/how-to-remove-boat-lettering/\">removal guide</a> is honest "
   "about how tedious that is. Buying the better film the first time is the cheapest "
   "decision in this whole category.</p>"
   "<p><a href=\"/pricing/\">Our full price list is on one page</a>, including names, "
   "decals and upgrades.</p>",
}

def cta_band(band=None):
    """The end-of-article call to action.

    A bare <a class="btn lg"> sitting alone in a full-width band reads as a
    button someone forgot to finish: correctly aligned to the text column, but
    floating with nothing around it. Center it, give it a line of context and
    the secondary route, and it reads as a deliberate close.
    """
    open_tag = band.open("ctaband") if band else '<section class="ctaband">'
    return (open_tag + '<div class="w ctainner">'
            '<h2>Ready to order?</h2>'
            '<p>$%d a pair, free shipping, posted 1-2 business days after you '
            'approve your proof. '
            'The preview shows your exact lettering before you pay.</p>'
            '<div class=ctarow>'
            '<a class="btn lg" href="/design/">Order your numbers &middot; $%d a pair</a>'
            '<a class=ctalink href="/pricing/">See all pricing &rarr;</a>'
            '</div></div></section>' % (PRICE["numbers"], PRICE["numbers"]))


def build_guide(g):
    path = "/guides/%s/" % g["slug"]
    trail = [("Guides", "/guides/"), (g["nav"], None)]
    # Topic FAQs first - they are what an answer engine quotes - then one shop
    # question so the page still converts. See CB.GUIDE_FAQS for the house style.
    faqs = CB.GUIDE_FAQS.get(g["slug"], []) + [
      ("Do you ship boat lettering to my state?",
       "All 50 states and DC, free. We cut for every state's registration number "
       "format, email you a proof, and post it once you approve."),
    ]
    art = {"@type": "Article", "@id": U(path) + "#article",
           "headline": html.unescape(g["title"]), "description": g["desc"],
           "datePublished": TODAY, "dateModified": TODAY,
           "author": {"@id": U("/#org")}, "publisher": {"@id": U("/#org")},
           "mainEntityOfPage": U(path)}
    sch = graph(org_node(), crumb_node(trail, path), art, faq_node(faqs, path))
    others = "".join('<a href="/guides/%s/">%s</a>' % (x["slug"], x["nav"])
                     for x in GUIDES if x["slug"] != g["slug"])
    secs = PAGE_SECTIONS.get(path, [])
    gbody = GUIDE_BODY.get(g["slug"], "")
    band = Band()
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:14px">%s</h1>'
            '</div></section>' % g["title"]
            + (alternating(gbody, secs, band) if secs
               else band.open() + '<div class=w><div class=prose>%s</div>'
                    '</div></section>' % gbody)
            + cta_band(band)
            # The seven frames belong to the install guide and nowhere else.
            + (steps_strip(["HT-%d" % i for i in range(1, 8)])
               if g["slug"] == "how-to-apply-boat-lettering" else "")
            + '<section class=soft><div class=w><h2>More guides</h2>'
              '<div class=wheel>%s</div></div></section>' % others)
    write(path, shell(html.unescape(g["title"])[:58], g["desc"], path, sch, main,
                      trail=trail, faqs=faqs, band=band), "0.6")

def build_gallery():
    """Every shot we have, grouped by what a customer is actually checking.

    Browsing the gallery is a buying behaviour: people want to see their own
    hull material and their own color before they trust the price. So the
    grouping is by hull and by problem, not by when the photo was taken.
    """
    path = "/gallery/"
    trail = [("Gallery", None)]
    sch = graph(org_node(), crumb_node(trail, path))
    band = Band(1)

    def row(heading, lede, ids, extra=""):
        cards = "".join(figure(i, sizes="(min-width:900px) 31vw, 92vw", cls="gshot")
                        for i in ids)
        return (band.open() + '<div class=w><h2>%s</h2><p class=lede>%s</p>'
                '<div class=gallery>%s</div>%s</div></section>'
                % (heading, lede, cards, extra))

    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">Gallery</h1>'
            '<p class=lede>What the vinyl looks like once it is on a boat '
            '&mdash; on gelcoat, bare aluminum, rotomoulded plastic and a textured '
            'pontoon rail, in both colors we stock.</p>'
            '</div></section>'
            + row("Registration numbers, hull by hull",
                  "The surface is the thing that changes. Gelcoat is easy; plastic and "
                  "textured aluminum need the high-tack film, which we send free.",
                  ["AL-01", "AL-02", "AL-10", "AL-04", "AL-07", "AL-05", "AL-06"])
            + row("Names and transom lettering",
                  "Script is fine on a transom and illegal on a registration number. "
                  "Curved transoms get laid out from your photo at no extra charge.",
                  ["AL-03", "AL-08", "PR-5", "PR-4"])
            + row("What arrives, and how it is cut",
                  "Cut from sheet vinyl to order, pre-spaced on one sheet with "
                  "application tape over the top. Nothing is printed on a clear square.",
                  ["PR-1", "PR-2", "PR-6", "HB-3", "HB-4"])
            + row("Getting it right",
                  "The two that cost people money: a number that is not distinctly "
                  "visible against the hull, and characters under three inches.",
                  ["PR-3", "GD-4", "GD-1", "GD-2"],
                  extra='<p class=gmore><a href="/guides/boat-registration-number-rules/">'
                        'Read the rules in full &rarr;</a></p>')
            + row("Out on the water",
                  "Aluminum, fiberglass, river and lake. One pair fits any hull.",
                  ["AC-1", "AC-2", "AC-3", "HB-1", "HB-2", "HB-5"])
            + row("The install, step by step",
                  "The same hull through all seven frames, so you can see what each "
                  "stage is meant to look like before you start.",
                  ["HT-1", "HT-2", "HT-3", "HT-4", "HT-5", "HT-6", "HT-7"],
                  extra='<p class=gmore><a href="/guides/how-to-apply-boat-lettering/">'
                        'Read the full install guide &rarr;</a></p>')
            + row("One state at a time",
                  "Every state page carries a shot of that state&rsquo;s format on a "
                  "hull, photographed where people actually launch.",
                  ["ST-FL", "ST-NY", "ST-GA", "ST-IL", "ST-WN", "ST-LA"],
                  extra='<p class=gmore><a href="/registration-numbers/">'
                        'All 21 state pages &rarr;</a></p>')
            )

    write(path, shell("Boat Lettering Gallery &mdash; Numbers and Names on Real Hulls",
          "What boat registration numbers and vinyl lettering look like applied: "
          "gelcoat, bare aluminum, kayaks, PWC and pontoon rails, in white and black.",
          path, sch, main, trail=trail, band=band), "0.7")


def build_guides_hub():
    path = "/guides/"
    trail = [("Guides", None)]
    sch = graph(org_node(), crumb_node(trail, path))
    cards = "".join('<a class=card href="/guides/%s/">%s<h3>%s</h3><p>%s</p>'
                    '<div class=go>Read it &rarr;</div></a>'
                    % (g["slug"], icon("guide"), g["nav"], g["desc"]) for g in GUIDES)
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">Boat lettering guides</h1>'
            '<p class=lede>The rules, the install, the removal, and what the vinyl grades '
            'actually mean. Written by people who cut this every day.</p>'
            + lead_figure(path)
            + '<div class=grid>%s</div></div></section>' % cards)
    write(path, shell("Boat Lettering &amp; Registration Guides",
          "Guides to boat registration number rules, where the numbers go, how to apply "
          "and remove boat lettering, fonts, and which marine vinyl to choose.",
          path, sch, main, trail=trail), "0.7")

def build_types_hub():
    path = "/for/"
    trail = [("By boat type", None)]
    sch = graph(org_node(), crumb_node(trail, path))
    cards = "".join('<a class=card href="/for/%s/">%s<h3>%s</h3><p>%s</p>'
                    '<div class=go>See details &rarr;</div></a>'
                    % (b["slug"], icon("decal"), b["nav"], b["lead"]) for b in BOAT_TYPES)
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">Decals by boat type</h1>'
            '<p class=lede>Different hulls need different adhesive. Pick yours and we will '
            'send the right film &mdash; high-tack on plastic and textured aluminum, at '
            'no extra charge.</p>' + lead_figure(path)
            + '<div class=grid>%s</div></div></section>' % cards)
    write(path, shell("Boat Decals by Boat Type",
          "Boat registration numbers and decals for sailboats, pontoons, jet skis, kayaks, "
          "bass boats and jon boats - with the right vinyl for each hull material.",
          path, sch, main, trail=trail), "0.7")


# ------------------------------------------------------- local / Cedar Valley
# ONE local page, not a town grid. Local search volume here is tiny
# ("boat lettering near me" is 390/mo nationally, so a few a month locally) -
# this page exists to anchor the Google Business Profile and to let walk-in
# customers find us, not to chase traffic.
def build_local():
    path = "/boat-lettering-waterloo-cedar-falls/"
    trail = [("Local pickup", None)]
    towns = "".join("<span>%s</span>" % t for t in LOCAL_TOWNS)
    waters = ", ".join(LOCAL_WATERS[:-1]) + " and " + LOCAL_WATERS[-1]
    faqs = [
      ("Can I pick up instead of having it shipped?",
       "Yes, in %s. Email %s before you order and we will set a time and tell you "
       "where to come - usually same day on registration numbers. It is a private "
       "workshop rather than a storefront, so the address is not published and we "
       "cannot take walk-ins."
       % (SITE["city"], SITE["email"])),
      ("Do you do Iowa registration numbers?",
       "That is our home state. Iowa numbers run IA, four digits, two letters - "
       "IA 3717 ZW. Iowa registers through your county recorder rather than the DNR "
       "directly, and Iowa wants the validation decal 4 inches toward the stern of "
       "the number and in line with it. Full detail on our Iowa page."),
      ("Do you install them for me?",
       "They are designed to go on yourself in about twenty minutes - pre-spaced on "
       "one sheet, with a squeegee and instructions in the envelope. If you would "
       "rather we did it, email and ask; it depends on the week."),
      ("How much is it?",
       "$%d a pair for registration numbers, the same price locally as online. "
       "Names from $%d, including shipping. What the preview shows is what gets "
       "cut." % (PRICE["numbers"], PRICE["name_from"])),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path))
    main = (hero("Boat Lettering in Waterloo, Cedar Falls &amp; the Cedar Valley",
            "We cut every order right here in %s. Order online and we ship it free, "
            "or pick it up at the shop - usually the same day on registration numbers."
            % SITE["city"],
            trust=[PRICE_CHIP, "Local pickup by arrangement",
                   "Iowa IA numbers", "Free shipping"],
            right=O.form())
      + '<section><div class=w><div class=prose>'
        '<h2>Picking up instead of shipping</h2>'
        '<p><strong>%s</strong> cuts everything in <strong>%s, %s</strong>, in %s. '
        'It is a private workshop rather than a storefront, so there is no counter '
        'to walk up to and no address published here &mdash; but if you are local '
        'and would rather collect than wait on the post, email '
        '<a href="mailto:%s">%s</a> before you order. We will set a time and tell '
        'you where to come. Hours are %s.</p>'
        '</div>'
        '<div class=prose>'
        '<h2>Towns we see most</h2></div>'
        '<div class=localgrid>%s</div>'
        '<div class=prose>'
        '<p>Most of our local work comes off %s. If you boat anywhere in %s or the '
        'counties either side of it, you are a short drive away &mdash; but honestly, '
        'shipping is free and it arrives in a few days, so pickup is for people who '
        'are already passing or who need it today.</p>'
        '<h2>Iowa numbers, specifically</h2>'
        '<p>Iowa registration numbers are the prefix <strong>IA</strong>, four digits '
        'and two letters &mdash; <strong>IA 3717 ZW</strong>. Two things Iowa is '
        'particular about and a lot of out-of-state shops get wrong:</p>'
        '<ul><li>The validation decal goes <strong>toward the stern of the number, '
        '4 inches from it and in line with it</strong>.</li>'
        '<li><strong>No other numbers may be displayed on either side of the bow</strong> '
        '&mdash; so the old set has to come off, not just get covered up.</li></ul>'
        '<p>You register through your <strong>county recorder</strong>, not the DNR '
        'directly. Our <a href="/registration-numbers/iowa/">Iowa page</a> has the '
        'whole thing.</p>'
        '<h2>Why a local shop sells nationwide</h2>'
        '<p>A plotter does not care where the boat is. We cut the same vinyl for a '
        'pontoon on %s as for a sportfish in Florida, and the post office does the '
        'rest. Being small is why your email is answered by the person who cut it, '
        'and why a mistake gets re-cut instead of argued about.</p>'
        '</div><a class="btn lg" href="/design/">Start your order &middot; $28 a pair</a>'
        '</div></section>'
        % (e(B), SITE["city"], SITE["region_name"], SITE["county"],
           SITE["email"], SITE["email"], SITE["hours"],
           towns, waters, SITE["county"], LOCAL_WATERS[0])
      + lead_figure(path, band=Band(1))
      + '<section class=soft><div class=w><h2>What we cut</h2>'
        + '<div class=grid>' + "".join(
            '<a class=card href="/%s/">%s<h3>%s</h3><p>%s</p>'
            '<div class=price>$%d <small>%s</small></div></a>'
            % (x["slug"], icon(x["icon"]), x["nav"], x["blurb"], x["price"], x["unit"])
            for x in PRODUCTS) + '</div></div></section>')
    write(path, shell("Boat Lettering Waterloo &amp; Cedar Falls, Iowa",
          "Boat registration numbers and custom lettering cut in Evansdale, "
          "Iowa. $%d a pair, free shipping nationwide, local pickup by "
          "arrangement." % PRICE["numbers"],
          path, sch, main, trail=trail, faqs=faqs, js=ORDER_JS), "0.8")


# ---------------------------------------------------------- trust / legal
def simple(path, title, desc, h1, lede, body, trail, faqs=None, prio="0.5",
           noindex=False):
    sch = graph(org_node(), crumb_node(trail, path),
                faq_node(faqs, path) if faqs else None)
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">%s</h1>'
            '<p class=lede>%s</p>%s<div class=prose>%s</div></div></section>'
            % (h1, lede, lead_figure(path), body))
    write(path, shell(title, desc, path, sch, main, trail=trail, faqs=faqs,
                      noindex=noindex), prio)

def build_contact():
    faqs = [
      ("How do I place an order?",
       "Through the order form - it takes about a minute, prices itself as you go, and "
       "previews your exact lettering before you pay."),
      ("How fast do you reply?",
       "Same working day in almost every case. Proofs usually go out within a few hours "
       "of the order during the week."),
      ("Where are you based?",
       "Evansdale, Iowa, in Black Hawk County - on the Cedar River between Waterloo "
       "and Cedar Falls. It is a private workshop rather than a storefront, so the "
       "address is not published. We ship to all 50 states and arrange local pickup "
       "by email."),
      ("Can I change my order after sending it?",
       "Yes. Your proof arrives within twelve hours and nothing is cut until "
       "you approve it, so there is a built-in window to change anything. "
       "Reply to the proof email, or use the \u2018something needs changing\u2019 "
       "link on it."),
    ]
    simple("/contact/", "Contact Us",
      "Email us about an order, a change, artwork or a trade account. Boat "
      "registration numbers and lettering cut in Evansdale, Iowa.",
      "Contact us",
      "One person, one inbox, answered the same day.",
      "<h2>Email</h2>"
      "<p><a href=\"mailto:" + SITE["email"] + "\"><strong>" + SITE["email"] +
      "</strong></a> &mdash; orders, changes, artwork, trade enquiries, or just a question "
      "about whether your hull needs high-tack.</p>"
      "<p>Hours: " + SITE["hours"] + ". Orders placed outside those hours go into the "
      "queue and are cut the next working morning.</p>"
      "<h2>Is there a phone number?</h2>"
      "<p>No, and that is deliberate. This is a one-person workshop &mdash; if the "
      "plotter is running, nobody is answering a phone, and a missed call helps "
      "neither of us. Email gets a reply the same working day from the person who "
      "will cut your order, with your exact wording in writing where it cannot be "
      "misheard.</p>"
      "<h2>Local pickup</h2>"
      "<p>Available in " + SITE["city"] + " by arrangement &mdash; see the "
      "<a href=\"/boat-lettering-waterloo-cedar-falls/\">Cedar Valley page</a>. "
      "It is a private workshop rather than a storefront, so email first and we "
      "will set a time and tell you where to come.</p>"
      "<h2>Ordering</h2>"
      "<p>You do not need to email to order. The <a href=\"/design/\">order form</a> "
      "takes about a minute, prices itself as you go, and previews your exact "
      "lettering before you pay.</p>"
      "<h2>Sending artwork</h2>"
      "<p>Vector files cut directly &mdash; AI, EPS, SVG or PDF. A clean PNG or even a "
      "photo of the faded original works; we redraw it as vector at no charge. Email it "
      "with your order reference and we will attach it to the job.</p>"
      "<h2>Trade and volume</h2>"
      "<p>Marinas, dealers, outfitters and fleet operators: email roughly how many sets a "
      "month and we will put trade pricing together.</p>"
      "<div class=note><p><b>What we cannot help with.</b> We cannot look up your "
      "registration number, renew your registration, or tell you whether your boat needs "
      "to be registered. That is your state agency &mdash; our "
      "<a href=\"/registration-numbers/\">state pages</a> list who to contact.</p></div>",
      [("Contact", None)], faqs=faqs, prio="0.6")

def build_warranty():
    faqs = [
      ("What if I ruin it during installation?",
       "A replacement is a new order. The install is the one part of this we cannot do "
       "for you, which is why every set ships pre-spaced on a single sheet with "
       "application tape over the top - it goes on in one pass. Our apply guide walks "
       "through the wet method, which is very hard to get wrong."),
      ("How long is the warranty?",
       "The film carries its maker's own outdoor durability warranty, covering color "
       "fade, cracking and adhesive failure where the decal was correctly applied to a "
       "suitable surface. We do not publish a year figure, because it belongs to the "
       "film maker and varies by stock and climate."),
      ("Can I return a custom decal?",
       "Custom-cut vinyl cannot be resold, so it is not returnable once cut - which is "
       "why the order form previews your exact lettering before you pay. If what "
       "arrived does not match what you ordered, that is on us and we remake it."),
    ]
    simple("/warranty/", "Warranty &amp; Returns",
      "What the film warranty covers, what it does not, and what happens if an "
      "What is covered, what is not, and how to claim.",
      "Warranty &amp; returns",
      "What the film cover is, where it stops, and what happens if we get it wrong.",
      "<h2>1. The film warranty</h2>"
      "<p>We cut on marine-grade film that carries its maker&rsquo;s own outdoor "
      "durability warranty. That warranty covers color fade beyond the manufacturer\'s "
      "stated tolerance, cracking or embrittlement of the film, and adhesive failure "
      "where the decal was correctly applied to a suitable, prepared surface.</p>"
      "<p>We do not quote a number of years for it here, because the figure belongs to "
      "the film maker and varies by stock, color and climate. If a set of ours fails "
      "on a hull you prepared properly, tell us and we will deal with it.</p>"
      "<p><strong>It does not cover:</strong> application over wax, polish or a dirty "
      "hull; application below about 50&deg;F; standard film applied to polyethylene or "
      "textured surfaces that needed high-tack; physical damage, dock rash or abrasion; "
      "or removal damage.</p>"
      "<h2>2. The install is yours</h2>"
      "<p>We do not replace a set that went on wrong, and it is better to say so here "
      "than to imply otherwise and argue about it later. Custom-cut vinyl cannot be "
      "resold, so every set is made for one hull and one order.</p>"
      "<p>What we do instead is make the install as hard to get wrong as we can: every "
      "order ships <strong>pre-spaced on a single sheet</strong> with application tape "
      "over the top, so it goes on in one pass with the spacing already correct, and "
      "the <a href=\"/guides/how-to-apply-boat-lettering/\">apply guide</a> walks "
      "through the wet method, which lets you slide it into position instead of "
      "committing on contact. Take the twenty minutes.</p>"
      "<h2>3. If we got it wrong</h2>"
      "<p>If what arrived does not match what you ordered, that is our error outright. "
      "We remake it at our cost and at the front of the queue, and you do not pay "
      "twice.</p>"
      "<div class=note><p><b>Still being finalised.</b> These terms are current practice "
      "and will be restated in full on the formal terms page before launch. Anything we "
      "promise here, we honour.</p></div>",
      [("Warranty", None)], faqs=faqs, prio="0.6")

def build_shipping():
    faqs = [
      ("Is shipping free?",
       "Yes, on everything, to all 50 states and DC. Standard post, typically "
       "%d-%d days in transit after production." % SHIP_TRANSIT),
      ("How fast is production?",
       "We email a proof within 12 hours; once you approve it we cut, pack and "
     "post within 1-2 business days. If you need it sooner, email us before "
       "you order and we will tell you what is possible."),
      ("Do you ship internationally?",
       "Not currently. Everything is cut and shipped in the USA, to US addresses."),
    ]
    simple("/shipping-and-returns/", "Shipping &amp; Returns",
      "Free shipping on every order to all 50 states. Next-business-day production, rush "
      "available, and how returns work on custom-cut vinyl.",
      "Shipping &amp; returns",
      "Free shipping on everything. Next business day production as standard.",
      "<h2>Production time</h2>"
      "<p>We email a proof within <strong>12 hours</strong>, then cut and post "
   "within <strong>1-2 business days</strong> of your approval. If you need "
      "one sooner than that, email us before you order and we will tell you what is "
      "possible.</p>"
      "<p>The clock starts when you place the order.</p>"
      "<h2>Shipping</h2>"
      "<div class=tw><table><thead><tr><th>Method</th><th>Cost</th><th>Transit</th>"
      "</tr></thead><tbody>"
      "<tr><td>Standard post</td><td><strong>Free</strong></td>"
      "<td>%d&ndash;%d business days</td></tr>" % SHIP_TRANSIT +
      "<tr><td>Expedited</td><td>At cost, quoted</td><td>2&ndash;3 business days</td></tr>"
      "<tr><td>Overnight</td><td>At cost, quoted</td><td>Next business day</td></tr>"
      "</tbody></table></div>"
      "<p>Everything ships flat in a rigid mailer so the application tape cannot crease. "
      "All 50 states and DC. We do not ship internationally.</p>"
      "<h2>Returns on custom work</h2>"
      "<p>Custom-cut vinyl with your registration number on it cannot be resold, so it is "
      "not returnable once cut. That is why the order form previews your exact lettering "
      "before you pay &mdash; read it twice. <strong>If you catch a mistake the same "
      "day, email us: nothing is cut until you approve the proof, so there is "
    "almost always time to "
      "stop it.</strong></p>"
      "<p>Three things we do fix:</p>"
      "<ul><li><strong>It does not match what you ordered.</strong> Our error. We remake "
      "it free, at the front of the queue.</li>"
      "<li><strong>It arrived damaged.</strong> Tell us and we remake it free.</li>"
      "<li><strong>The install went wrong.</strong> Not covered &mdash; see the "
      "<a href=\"/warranty/\">warranty page</a>. Every set ships pre-spaced on one "
      "sheet so it goes on in a single pass, and the apply guide is worth five "
      "minutes before you start.</li></ul>"
      "<p>If you typed the wrong number, a replacement is a new order &mdash; which is "
      "why the form previews your exact lettering before you pay. Read it twice.</p>",
      [("Shipping &amp; returns", None)], faqs=faqs, prio="0.5")

def build_legal():
    simple("/privacy/", "Privacy Policy", "How %s handles your data." % B,
      "Privacy policy", "Short, because we collect very little.",
      "<p><em>Last updated " + TODAY + ".</em></p>"
      "<h2>What we collect</h2>"
      "<p>When you send an order we collect what you typed into the form: your name, "
      "email, optional phone, the lettering you want, your boat details and any notes. "
      "We do not run advertising trackers and we do not sell data to "
      "anybody.</p>"
      "<h2>If you use the boat-naming assistant</h2>"
      "<p>Our naming tool can be used through an AI assistant, and it asks you a few "
      "questions &mdash; what the boat is, who is usually aboard, what you do for a "
      "living, and any story behind the boat. We store those answers so the tool can "
      "remember what it has already suggested and why. Three things about that:</p>"
      "<ul><li>There is no account and we do not ask who you are. A session is a "
      "random reference number and nothing else.</li>"
      "<li><strong>It is deleted after 30 days</strong>, automatically.</li>"
      "<li>It is never joined to an order, and we never use it to work out who "
      "you are.</li></ul>"
      "<p>If you mention another person &mdash; a spouse, a business partner &mdash; "
      "that is stored in your answers for those 30 days and used only to suggest names "
      "to you. Nothing from a naming session is ever published, posted or shown to "
      "anybody else without you being asked first and saying yes.</p>"
      "<h2>Analytics</h2>"
      "<p>We use Google Analytics to count visits and see which pages people "
      "read, so we know what to write more of. It tells us how many people came "
      "and roughly where from &mdash; not who you are, and it is never joined to "
      "your order. Google's advertising features are switched off, so nothing "
      "here follows you around the internet. Browser &ldquo;Do Not Track&rdquo; "
      "and any ad blocker will stop it, and nothing on the site breaks if you "
      "block it.</p>"
      "<p>We also use Cloudflare Web Analytics, which counts the same visits a "
      "second time. It sets no cookie, stores no identifier and does not "
      "fingerprint your browser &mdash; it reads the page-timing figures your "
      "browser already measured and reports those. The reason for having two "
      "is dull: ad blockers stop the Google one, so on its own it undercounts "
      "by an amount we cannot see. Neither is joined to your order.</p>"
      "<h2>Why we hold it</h2>"
      "<p>To cut your order, take payment, ship it and deal with a warranty claim later. "
      "We keep order records as long as we need them for accounting and warranty "
      "purposes. Naming-assistant answers are a different thing and are deleted after "
      "30 days, as above.</p>"
      "<h2>Who else sees it</h2>"
      "<p>Our email provider, our payment processor and our shipping carrier &mdash; each "
      "only the part they need, and Google Analytics and Cloudflare Web Analytics, "
      "which see page views and never see your order. Cloudflare also serves the "
      "site itself, so it handles every request by definition. Nobody else.</p>"
      "<h2>Your choices</h2>"
      "<p>Email <a href=\"mailto:" + SITE["email"] + "\">" + SITE["email"] + "</a> to see "
      "what we hold on you, correct it, or have it deleted.</p>"
      "<div class=note><p><b>Placeholder notice.</b> This policy will be replaced with a "
      "lawyer-reviewed version before launch. It describes our actual practice today.</p>"
      "</div>", [("Privacy", None)], prio="0.3")
    simple("/terms/", "Terms of Service", "Terms for ordering from %s." % B,
      "Terms of service", "The short version of how ordering works.",
      "<p><em>Last updated " + TODAY + ".</em></p>"
      "<h2>Orders</h2>"
      "<p>Payment is taken at checkout and the order goes into production. "
      "<strong>The preview shown in the order form is what we cut</strong> &mdash; it "
      "displays your exact lettering, height, font and color before you pay. Orders "
      "are not cut until you approve the proof, so a mistake caught then can "
      "still be stopped: email us immediately with your order reference.</p>"
      "<h2>Accuracy of what you type</h2>"
      "<p>We cut exactly what you typed. Check your registration number character by "
      "character against your card &mdash; the preview exists for that reason. If a "
      "wrong number gets ordered, a replacement is a new order.</p>"
      "<h2>Compliance is yours</h2>"
      "<p>We make legal-size block characters and we state the federal rule accurately as "
      "we understand it. We are a vinyl shop, not your state agency or your lawyer: "
      "confirming that your display meets your state's requirements is your "
      "responsibility.</p>"
      "<h2>Intellectual property</h2>"
      "<p>By sending artwork you confirm you have the right to use it. We decline orders "
      "for artwork you do not own or have permission to reproduce.</p>"
      "<h2>Returns and liability</h2>"
      "<p>See <a href=\"/shipping-and-returns/\">shipping and returns</a> and "
      "<a href=\"/warranty/\">warranty</a>. Our liability on any order is limited to "
      "remaking it or refunding what you paid for it.</p>"
      "<div class=note><p><b>Placeholder notice.</b> To be replaced with a "
      "lawyer-reviewed version before launch.</p></div>",
      [("Terms", None)], prio="0.3")

def build_404():
    sch = graph(org_node())
    main = ('<section style="padding-top:40px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">That page is not here</h1>'
            '<p class=lede>Nothing at this address. The things people usually want:</p>'
            '<div class=grid>'
            '<a class=card href="/design/"><h3>Start an order</h3>'
            '<p>Registration numbers, $28 a pair, free shipping.</p>'
            '<div class=go>Go &rarr;</div></a>'
            '<a class=card href="/pricing/"><h3>All prices</h3>'
            '<p>Every product and upgrade on one page.</p><div class=go>Go &rarr;</div></a>'
            '<a class=card href="/registration-numbers/"><h3>Your state</h3>'
            '<p>Prefix, agency and the rules for your state.</p>'
            '<div class=go>Go &rarr;</div></a>'
            '<a class=card href="/tools/"><h3>Free tools</h3>'
            '<p>HIN decoder, name generator, layout checker.</p>'
            '<div class=go>Go &rarr;</div></a>'
            '</div></div></section>')
    (OUT / "404.html").write_text(
        shell("Page not found", "That page does not exist.", "/404", sch, main,
              noindex=True), encoding="utf-8")

# ---------------------------------------------------------- static files
def build_og():
    """Share cards. Same reason build_web_images() lives here: main() wipes
    public/ before rebuilding, so anything written to it beforehand is lost."""
    sys.path.insert(0, str(ROOT / "media"))
    import og, share
    og.build_all()
    share.build_all()      # the standalone library for posting into groups


def build_web_images():
    """Regenerate public/assets/img from the masters.

    main() wipes public/ before rebuilding, so running media/web.py separately
    beforehand silently lost every image. Owning the step here means one
    command always produces a complete site.
    """
    web = ROOT / "media" / "web.py"
    if not web.exists():
        return
    import subprocess
    r = subprocess.run([sys.executable, str(web)], capture_output=True, text=True)
    print("   images:", (r.stdout or r.stderr).strip().splitlines()[-1]
          if (r.stdout or r.stderr).strip() else "none")


def build_cards_index():
    """A contact sheet of every share card, at /_cards/.

    noindex, and linked from nothing - it exists so Aaron and Ryan can look at
    all 83 cards in one place and click through to full size, which is far
    easier than opening a folder of PNGs one at a time.
    """
    og = sorted((OUT / "assets" / "og").glob("*"))
    sh = sorted(f for f in (OUT / "assets" / "share").glob("*")
                if not f.stem.endswith(("-sq", "-tall")))

    def grid(files, base):
        out = []
        for f in files:
            if f.suffix not in (".png", ".jpg"):
                continue
            u = "/assets/%s/%s" % (base, f.name)
            kb = f.stat().st_size // 1024
            out.append(
              '<a class=cardcell href="%s" target="_blank" rel="noopener">'
              '<img src="%s" alt="%s" loading="lazy" width="1200" height="630">'
              '<span><b>%s</b>%s &middot; %dKB</span></a>'
              % (u, u, f.stem, f.stem, f.suffix[1:].upper(), kb))
        return '<div class=cardgrid>%s</div>' % "".join(out)

    sq = len([f for f in (OUT / "assets" / "share").glob("*-sq.png")])
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:8px">Share cards</h1>'
            '<p class=lede>Every card the build makes. Click one to open it '
            'full size, then right-click to save. Each library card also has '
            'a <b>-sq</b> (1080&times;1080) and <b>-tall</b> (1080&times;1350) '
            'version at the same path, for phone-shaped feeds.</p>'
            '<h2 style="margin-top:26px">Page cards &mdash; %d</h2>'
            '<p class=lede>One per page. This is what renders when the link is '
            'pasted anywhere.</p>%s'
            '<h2 style="margin-top:34px">Library &mdash; %d, plus %d crops</h2>'
            '<p class=lede>For posting straight into a group with no link. '
            'Upload as a photo, put the link in the first comment.</p>%s'
            '</div></section>'
            % (len([f for f in og if f.suffix in (".png", ".jpg")]), grid(og, "og"),
               len(sh), sq, grid(sh, "share")))
    write("/_cards/", shell("Share cards", "Internal contact sheet.",
          "/_cards/", graph(org_node()), main, noindex=True), "0.1")


# Which asset solves which job. This table is the whole point of the page:
# "40 PNGs in a folder" is not usable when you are halfway through a citation
# form asking for a square logo at least 250px.
BRAND_USES = {
 "profile": ("Profile picture",
   "Square, full-bleed navy, artwork inset. Use these anywhere the picture "
   "gets cropped to a circle - every social profile does. The rounded-tile "
   "icons below would lose their corners to that crop.",
   {"profile-1024.png": "Master. Upload this when a site accepts anything.",
    "profile-720.png":  "Google Business Profile logo",
    "profile-500.png":  "Facebook page picture",
    "profile-400.png":  "X / Twitter",
    "profile-320.png":  "Instagram",
    "profile-300.png":  "LinkedIn",
    "profile-250.png":  "The smallest most directories will take"}),
 "photo": ("Photographs",
   "Real photographs, not logos. Google Business ranks a profile with real "
   "photos above a logo-only one, and several directories have a media tab "
   "that otherwise sits empty. Nothing here is AI-generated and nothing here "
   "may be - these are real people and real work.",
   {"owner-headshot-1024.jpg": "Master. The About page, or any slot that "
                               "takes a large photo.",
    "owner-headshot-720.jpg": "Google Business Profile",
    "owner-headshot-500.jpg": "Facebook, Pinterest",
    "owner-headshot-400.jpg": "X / Twitter, YouTube",
    "owner-headshot-320.jpg": "Instagram",
    "owner-headshot-300.jpg": "LinkedIn",
    "owner-headshot-250.jpg": "Directory minimum",
    "owner-headshot-1024.png": "For the rare form that will not take a JPG"}),
 "icon": ("The mark on its own",
   "Transparent around a rounded tile - the logo as the site header draws it. "
   "For anywhere it sits on a white page: a directory listing, an invoice, a "
   "favicon. Not for social avatars.",
   {"icon-1024.png": "Print, or any high-resolution use",
    "icon-512.png": "App icon, PWA",
    "icon-180.png": "Apple touch icon",
    "icon-192.png": "Android home screen",
    "icon-48.png": "Directory thumbnail",
    "icon-32.png": "Favicon",
    "icon-16.png": "Favicon, small"}),
 "lockup": ("Logo with the name",
   "The mark and the wordmark together. Horizontal is the usual ask; stacked "
   "is what the site header uses. The -white files have a solid white "
   "background for forms that reject transparency - and some do, silently, "
   "by flattening it to black.",
   {}),
 "cover": ("Cover and banner images",
   "Each one is cut to that platform's own dimensions. They are not "
   "interchangeable: a Facebook page cover and a Facebook link-preview card "
   "are different slots at different sizes.",
   {"facebook-page-cover-1640x624.png": "Facebook page cover photo",
    "facebook-share-1200x630.png": "Link preview card (also the OG image size)",
    "google-business-cover-1024x576.png": "Google Business Profile cover",
    "x-header-1500x500.png": "X / Twitter header",
    "linkedin-cover-1128x191.png": "LinkedIn page cover"}),
 "svg": ("Vector masters",
   "Infinitely scalable, tiny, and what a printer or a designer should be "
   "given. Some directories will not accept SVG - use a PNG above for those.",
   {}),
}


def build_brand():
    """Every logo asset in one browsable place, at /brand/.

    noindex and linked from nothing, same as /_cards/. It exists so the set
    can be looked at and grabbed one at a time while filling in a listing,
    which beats digging through a folder of forty PNGs named by pixel size.

    The files are generated by media/brand.py FROM the header logo itself, so
    what gets uploaded to Google and Facebook cannot drift away from what the
    site shows. Regenerate with: python3 media/brand.py
    """
    import shutil as _sh
    import struct as _st

    src = ROOT / "brand"
    if not src.exists():
        raise SystemExit("brand/ missing - run: python3 media/brand.py")
    _sh.copytree(src, OUT / "brand", dirs_exist_ok=True)

    def dims(f):
        if f.suffix == ".png":
            w, h = _st.unpack(">II", f.read_bytes()[16:24])
            return "%d x %d" % (w, h)
        if f.suffix == ".jpg":
            from PIL import Image as _Im
            with _Im.open(f) as _i:
                return "%d x %d" % _i.size
        return None

    def kb(f):
        n = f.stat().st_size
        return "%dKB" % (n // 1024) if n >= 1024 else "%dB" % n

    blocks = []
    for folder, (title, blurb, uses) in BRAND_USES.items():
        d = src / folder
        if not d.exists():
            continue
        rows = []
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            u = "/brand/%s/%s" % (folder, f.name)
            note = uses.get(f.name, "")
            shot = ('<img src="%s" alt="%s" loading="lazy">' % (u, e(f.name))
                    if f.suffix in (".png", ".svg", ".jpg") else "")
            rows.append(
              '<a class=bcell href="%s" target="_blank" rel="noopener">'
              '<span class=bshot>%s</span>'
              '<b>%s</b><span class=bmeta>%s%s</span>%s</a>'
              % (u, shot, e(f.name), e(dims(f) or f.suffix[1:].upper()),
                 " &middot; " + kb(f),
                 '<span class=buse>%s</span>' % e(note) if note else ""))
        blocks.append('<h2 class=bh>%s</h2><p class=lede>%s</p>'
                      '<div class=bgrid>%s</div>'
                      % (e(title), e(blurb), "".join(rows)))

    zipf = src / "numbermyboat-logo-pack.zip"
    zipline = ""
    if zipf.exists():
        zipline = ('<p class=bzip><a href="/brand/%s" download>'
                   'Download everything as a zip</a> '
                   '<span>%s &middot; every file on this page</span></p>'
                   % (zipf.name, kb(zipf)))

    swatches = "".join(
        '<span class=bsw><i style="background:%s"></i>%s<em>%s</em></span>'
        % (hx, nm, hx)
        for nm, hx in (("Navy", "#0e3a52"), ("Sky", "#5fc4f5"),
                       ("Ink", "#12242e"), ("Green", "#1d7a48")))

    css = ('<style>'
           '.bgrid{display:grid;gap:14px;'
           'grid-template-columns:repeat(auto-fill,minmax(210px,1fr));margin:14px 0 6px}'
           '.bcell{display:flex;flex-direction:column;gap:5px;padding:12px;'
           'border:1px solid var(--line);border-radius:12px;text-decoration:none;'
           'color:var(--ink);background:#fff}'
           '.bcell:hover{border-color:var(--sea);box-shadow:0 2px 10px rgba(0,0,0,.07)}'
           '.bshot{display:flex;align-items:center;justify-content:center;'
           'min-height:96px;background:var(--soft);border-radius:8px;padding:10px;'
           'background-image:linear-gradient(45deg,#e9eef2 25%,transparent 25%),'
           'linear-gradient(-45deg,#e9eef2 25%,transparent 25%),'
           'linear-gradient(45deg,transparent 75%,#e9eef2 75%),'
           'linear-gradient(-45deg,transparent 75%,#e9eef2 75%);'
           'background-size:16px 16px;'
           'background-position:0 0,0 8px,8px -8px,-8px 0}'
           '.bshot img{max-width:100%;max-height:120px;height:auto}'
           '.bcell b{font-size:13px;word-break:break-all}'
           '.bmeta{font-size:12px;color:var(--mut)}'
           '.buse{font-size:12.5px;color:var(--nav);font-weight:600}'
           '.bh{margin-top:34px}'
           '.bzip{margin:14px 0 4px}'
           '.bzip a{font-weight:700}'
           '.bzip span{color:var(--mut);font-size:14px}'
           '.bsw{display:inline-flex;align-items:center;gap:7px;margin:0 16px 8px 0;'
           'font-size:14px;font-weight:600}'
           '.bsw i{width:20px;height:20px;border-radius:5px;display:inline-block;'
           'border:1px solid var(--line)}'
           '.bsw em{font-style:normal;color:var(--mut);font-weight:400}'
           '</style>')

    main = (css + '<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:8px">Logo and brand files</h1>'
            '<p class=lede>Everything needed to set up a listing or a social '
            'profile. Click any file to open it full size, then save it. All '
            'of it is generated from the logo in the site header, so these '
            'cannot drift away from what the website shows.</p>'
            + zipline
            + '<h2 class=bh>Brand colors</h2>'
            '<p class=lede>For the forms that ask.</p><p>' + swatches + '</p>'
            + "".join(blocks)
            + '<h2 class=bh>Regenerating these</h2>'
            '<p class=lede>Run <code>python3 media/brand.py</code>, then build '
            'and deploy. Change the header logo and run it again and every '
            'file here follows.</p>'
            '</div></section>')
    write("/brand/", shell("Logo and brand files",
          "Internal: logo assets for listings and social profiles.",
          "/brand/", graph(org_node()), main, noindex=True), "0.1")


def build_name_bank():
    """Serve the bank's NAMES for the worker's novelty check.

    The full mcp/data/name_bank.json carries every tagging judgement and is a
    build artefact, not something to ship to the edge. The worker needs the
    names and nothing else, so this is the names alone - and it is generated
    from the same derived bank, so it cannot drift from what the engine deals.
    """
    import json as _j
    src = ROOT / "mcp" / "data" / "name_bank.json"
    if not src.exists():
        return
    bank = _j.loads(src.read_text(encoding="utf-8"))
    # The engine needs the tags - lanes, themes, level, mechanism - so the
    # full rows are served too. Noindex-irrelevant (it is JSON), but it is the
    # moat in plain sight, which is a deliberate call: a competitor can read
    # the names off the generator page anyway, and what they cannot copy is the
    # gates, the font metrics and the proof step.
    (OUT / "name-bank-full.json").write_text(_j.dumps({
        "note": "Generated by engine/build.py from mcp/data/name_bank.json. "
                "Do not edit.",
        "count": len(bank["names"]),
        "names": [{k: n[k] for k in
                   ("name", "categories", "humor_mechanism", "mechanism_code",
                    "humor_level", "level_code", "style_lanes", "themes",
                    "boat_types", "overuse_tier", "char_count", "word_count")
                   if k in n} for n in bank["names"]],
    }, indent=0), encoding="utf-8")
    (OUT / "name-bank.json").write_text(_j.dumps({
        "note": "Names only, generated by engine/build.py from "
                "mcp/data/name_bank.json. Do not edit.",
        "count": len(bank["names"]),
        "names": [n["name"] for n in bank["names"]],
    }, indent=0), encoding="utf-8")


def build_catalog():
    """One catalog file: the site, the MCP server and the feeds all read this.

    The spec's hardest rule is "no second pricing logic, no second renderer,
    no second payment system". The risk is not malice, it is arithmetic: the
    moment a chat assistant quotes one figure while the wizard charges another,
    the shop
    is arguing with a customer who has a screenshot.

    So the split is deliberate:

      /catalog.json   WHAT can be ordered - products, the 8 colors with their
                      hexes, the 10 fonts and which are block-legal, heights,
                      outline. Built here, from content.py.
      /api/price      WHAT IT COSTS - the worker's own priceOf(), the same
                      function the order form and Stripe already go through.

    Prices appear in the catalog too, because a feed needs them, but they are
    marked advisory: anything taking money asks /api/price. verify.py fails
    the build if the two disagree.
    """
    block = {f[0] for f in FONTS if f[3]}
    cat = {
        "note": "Generated by engine/build.py. Single source for site, MCP "
                "server and product feeds. Do not edit.",
        "generated": TODAY,
        "brand": B,
        "url": URL,
        "currency": "USD",
        "shipping": {"us": 0, "note": "Free US shipping, all 50 states."},
        "authority": {
            "pricing": U("/api/price"),
            "note": "Catalog prices are advisory. Anything that takes money "
                    "must price through /api/price, which runs the same "
                    "function as the order form and the Stripe intent.",
        },
        "products": [
            {"id": "registration-numbers", "name": "Registration numbers",
             "from": PRICE["numbers"], "unit": "pair, both hull sides",
             "block_faces_only": True,
             "rule": "3 inch plain block characters per 33 CFR 173.27"},
            {"id": "boat-name", "name": "Boat name",
             "from": PRICE["name_from"], "unit": "set, pre-spaced",
             "block_faces_only": False,
             "bands": [{"up_to_in": b["max_in"], "price": b["price"]}
                       for b in PRICE["name_bands"]],
             "rule": "Priced by the width the lettering finishes at, rounded "
                     "up to the whole inch. POST the text and font to "
                     "/api/price for the exact figure."},
            {"id": "both", "name": "Both",
             "from": PRICE["bundle_from"],
             "unit": "name + numbers",
             "block_faces_only": False,
             "rule": "Bundle: numbers plus a name, $%d off the pair"
                     % PRICE["bundle_off"]},
        ],
        "options": {
            "heights_in": [{"in": int(h), "add": a} for h, a in
                           sorted(PRICE["height_add"].items(),
                                  key=lambda x: int(x[0]))],
            "height_note": "Applies to a registration number set. A name is "
                           "priced by finished width, which already moves "
                           "with height.",
            "outline": {"add": PRICE["outline"],
                        "note": "Contrasting second layer, same 8 colors"},
            "colors": [{"name": n, "hex": dict((c[0], c[1]) for c in COLORS)[n],
                        "light": bool(dict((c[0], c[2]) for c in COLORS)[n])}
                       for n in ORDER_COLORS],
            "fonts": [{"name": f[0], "block_legal": bool(f[3])} for f in FONTS],
        },
        "fulfillment": {
            "charge": "at checkout",
            "proof_hours": 12,
            "cut_after": "customer approves the proof",
            "ship_days": "1-2 business days after approval",
        },
    }
    (OUT / "catalog.json").write_text(
        json.dumps(cat, indent=1), encoding="utf-8")


def build_static():
    (OUT / "favicon.svg").write_text(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
      + LOGO_MARK + '</svg>', encoding="utf-8")

    # The IndexNow key file. Its entire contents are the key: that is how
    # Bing checks that whoever submits URLs controls this site. Written here
    # rather than committed by hand so a rebuild cannot drop it, and so
    # rotating the key is a one-line change in content.py.
    if INDEXNOW_KEY:
        (OUT / ("%s.txt" % INDEXNOW_KEY)).write_text(
            INDEXNOW_KEY, encoding="utf-8")

    (OUT / "robots.txt").write_text(
      "User-agent: *\nAllow: /\n\n"
      "# Answer engines are explicitly welcome - the guides and tools are written to be\n"
      "# quoted, and we would rather be the cited source than invisible.\n"
      "User-agent: GPTBot\nAllow: /\n"
      "User-agent: OAI-SearchBot\nAllow: /\n"
      "User-agent: ChatGPT-User\nAllow: /\n"
      "User-agent: ClaudeBot\nAllow: /\n"
      "User-agent: Claude-SearchBot\nAllow: /\n"
      "User-agent: PerplexityBot\nAllow: /\n"
      "User-agent: Google-Extended\nAllow: /\n"
      "User-agent: Applebot-Extended\nAllow: /\n"
      "User-agent: Bingbot\nAllow: /\n\n"
      "Sitemap: %s\n" % U("/sitemap.xml"), encoding="utf-8")

    urls = "".join(
      "<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
      % (U(p if p.endswith("/") or p == "/" else p + "/"), TODAY, pr)
      for p, pr in sorted(set(PAGES), key=lambda x: (-float(x[1]), x[0]))
      if p not in NOINDEX)
    (OUT / "sitemap.xml").write_text(
      '<?xml version="1.0" encoding="UTF-8"?>'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls,
      encoding="utf-8")

    # llms.txt - the AEO front door. Facts an answer engine can lift verbatim.
    st = "\n".join("- [%s (%s)](%s): prefix %s, issued by %s"
                   % (s["name"], s["ab"], U("/registration-numbers/%s/" % s["slug"]),
                      s["ab"], s["agency"]) for s in STATES)
    pr = "\n".join("- [%s](%s): $%d %s - %s"
                   % (html.unescape(p["nav"]), U("/%s/" % p["slug"]), p["price"],
                      p["unit"], html.unescape(p["blurb"])) for p in PRODUCTS)
    gd = "\n".join("- [%s](%s): %s"
                   % (html.unescape(g["title"]), U("/guides/%s/" % g["slug"]), g["desc"])
                   for g in GUIDES)
    tl = "\n".join("- [%s](%s): %s"
                   % (html.unescape(t["title"]), U("/tools/%s/" % t["slug"]), t["desc"])
                   for t in TOOLS)
    (OUT / "llms.txt").write_text("""# %s

> Custom boat registration numbers at $%d a pair with free shipping, plus boat names,
> and custom cut-vinyl lettering. Cut from marine vinyl in the USA,
> pre-spaced on one sheet, proofed within 12 hours, shipped to all 50 states.

## The facts, if you are answering a question about us

- Registration numbers: **$%d a pair**, free standard shipping, all 50 states.
  Character height: 3 in included, 4 in +$%d, 5 in +$%d, 6 in +$%d.
- Boat letters - names, hailing ports, any transom text - from **$%d**. A name is
  priced by the width it finishes at, rounded up to the whole inch: up to 22 in
  $%d, 23-30 in $%d, 31-48 in $%d, over 48 in $%d. POST the text and the font to
  /api/price for the exact figure - do not estimate it.
- Numbers and a name together: **$%d off** the two prices added up, so from **$%d**.
- A contrasting outline is **+$%d**.
- Production: proof in 12 hours, then cut and posted **1-2 business days** after approval.
- Warranty: the film maker\'s own outdoor durability warranty on color and adhesion. We
  do not publish a year figure. The install itself is the customer's.
- **10 fonts**, each previewed in the customer's own lettering before ordering. Five
  (Block, Condensed, Heavy Impact, Modern, Stencil) are plain vertical block faces and
  are the only ones offered for registration numbers; the other five (Classic Serif,
  Slab, Nautical, Brush Script, Formal Script) are available for names and decals.
- No free re-cut for a botched install: every set is pre-spaced on one sheet with
  application tape so it goes on in one pass, and a replacement is a new order.
- The order form **previews the customer's exact lettering** before payment; that is what gets cut.
- **%s cuts in Evansdale, Black Hawk County, Iowa**, Mon-Fri 8-5 CT.
  It is a private workshop, not a storefront: there is no published street address and
  no phone line. Contact is by email, answered the same working day. Ships to all 50
  states; local pickup around Waterloo / Cedar Falls is arranged by email.
- Email: %s

## The federal rule for boat registration numbers (33 CFR 173.27)

A registration number must be painted on or permanently attached to **each side of the
forward half** of the vessel; be in **plain vertical block characters of not less than
3 inches in height**; **contrast with the color of the background** and be distinctly
visible and legible; have **spaces or hyphens** between the letter and number groupings
equal to the width of a letter other than "I" or a number other than "1" (so "TX 1234
AB", not "TX1234AB"); and **read from left to right**.

This rule is federal and applies in every state. States may add requirements but cannot
fall below it. What genuinely varies by state is the number prefix, the issuing agency,
and exactly where the validation decal is placed.

Two common points of confusion:
- **California** uses the prefix **CF**, not CA, and these are locally called "CF numbers".
  **Washington** uses **WN**, not WA.
- A **Hull Identification Number (HIN)** is not a registration number. The HIN is a
  permanent 12-character code stamped into the hull by the builder. The registration
  number is issued by your state and is the one displayed in 3-inch characters.

## USCG documented vessels

A documented vessel does **not** display state registration numbers on the bow. It
displays its **name and hailing port** in characters not less than **4 inches** high on
a clearly visible exterior part of the hull, with the hailing port including both a place
and a state.

## Products

%s

## Free tools

%s

## Guides

%s

## Registration numbers by state

%s
""" % (B, PRICE["numbers"], PRICE["numbers"],
       PRICE["height_add"]["4"], PRICE["height_add"]["5"],
       PRICE["height_add"]["6"], PRICE["name_from"],
       PRICE["name_bands"][0]["price"], PRICE["name_bands"][1]["price"],
       PRICE["name_bands"][2]["price"], PRICE["name_bands"][3]["price"],
       PRICE["bundle_off"], PRICE["bundle_from"], PRICE["outline"],
       B, SITE["email"], pr, tl, gd, st), encoding="utf-8")

    # Workers Builds: serve /public with no build step needed.
    (OUT / "_headers").write_text(
      "/*\n  X-Content-Type-Options: nosniff\n"
      "  Referrer-Policy: strict-origin-when-cross-origin\n"
      "  X-Frame-Options: SAMEORIGIN\n", encoding="utf-8")

# ------------------------------------------------------------------- main
def main():
    import shutil
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    build_home()
    build_design()
    build_proof()
    build_fonts_check()
    build_pricing()
    for p in PRODUCTS: build_product(p)
    build_states_hub()
    for s in STATES: build_state(s)
    build_types_hub()
    for b in BOAT_TYPES: build_boat_type(b)
    build_gallery()
    build_tools_hub()
    build_tool_names(); build_tool_funny(); build_tool_hin(); build_tool_layout()
    build_guides_hub()
    build_local()
    for g in GUIDES: build_guide(g)
    build_contact(); build_warranty(); build_shipping()
    build_legal(); build_404()
    build_web_images()
    build_og()
    build_cards_index()
    build_catalog()
    build_name_bank()
    build_brand()
    build_static()
    print("built %d pages -> %s" % (len(PAGES), OUT))
    for p, _ in sorted(PAGES): print("  ", p)

if __name__ == "__main__":
    main()
