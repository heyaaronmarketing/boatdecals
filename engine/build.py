#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site builder for Boat Number Shop."""
import json, os, pathlib, sys, html, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from content import (SITE, PRICE, UPGRADES, PRODUCTS, BOAT_TYPES, TOOLS, GUIDES,
                     STATES, FONTS, FONT_NAMES, COLORS, FAQ_HOME,
                     LOCAL_TOWNS, LOCAL_WATERS, google_fonts_href)
from style import CSS
import order as O
import mockpay as MP
import preview as PV
import tools as T
import copy_blocks as CB

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
URL = os.environ.get("SITE_URL", SITE["url"]).rstrip("/")
TODAY = os.environ.get("BUILD_DATE", datetime.date.today().isoformat())
B = SITE["brand"]
PH, PT = SITE["phone_display"], SITE["phone_tel"]
e = html.escape
PAGES = []

def U(p): return URL + p

WORDMARK = ('<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">'
 '<rect width="32" height="32" rx="7" fill="#0e3a52"/>'
 '<path d="M4 22c2.4 0 2.4-2.3 4.8-2.3S11.2 22 13.6 22s2.4-2.3 4.8-2.3S20.8 22 23.2 22s2.4-2.3 4.8-2.3" '
 'stroke="#5fc4f5" stroke-width="2.1" fill="none" stroke-linecap="round"/>'
 '<path d="M4 27c2.4 0 2.4-2.3 4.8-2.3S11.2 27 13.6 27s2.4-2.3 4.8-2.3S20.8 27 23.2 27s2.4-2.3 4.8-2.3" '
 'stroke="#2f8fc4" stroke-width="2.1" fill="none" stroke-linecap="round"/>'
 '<text x="16" y="15.5" font-family="Arial Black,Arial" font-size="12" font-weight="900" '
 'fill="#5fc4f5" text-anchor="middle">19</text></svg>')

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
def icon(k):
    return ('<span class=icw><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>'
            % ICONS.get(k, ICONS["decal"]))

# ------------------------------------------------------------------- shell
def _title(t):
    for sfx in (" | " + B, " | Boat Numbers", ""):
        if len(t) + len(sfx) <= 60: return t + sfx
    return t[:60]

def head(title, desc, path, schema, noindex=False):
    canon = U(path)
    robots = ('<meta name="robots" content="noindex,follow">' if noindex else
      '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">')
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
%s
<meta property="og:type" content="website"><meta property="og:title" content="%s">
<meta property="og:description" content="%s"><meta property="og:url" content="%s">
<meta property="og:site_name" content="%s"><meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0e3a52">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>%s</style>
<script type="application/ld+json">%s</script>
</head><body>
<a class="skip" href="#main">Skip to the order form</a>""" % (
    e(_title(html.unescape(title))), e(html.unescape(desc)), canon, robots,
    e(html.unescape(title)), e(html.unescape(desc)), canon, e(B),
    CSS, json.dumps(schema, separators=(',', ':')))

# Header nav. Labels are what customers say ("Boat Numbers"), not what the
# product pages are titled - the hrefs still point at the canonical slugs.
NAV_MAIN = [
    ("Boat Numbers", "/boat-registration-numbers/"),
    ("Boat Letters", "/boat-lettering/"),
    ("Boat Names",   "/boat-name-decals/"),
    ("Pricing",      "/pricing/"),
    ("By State",     "/registration-numbers/"),
]
NAV_ABOUT = [
    ("Guides",     "/guides/"),
    ("Guarantee",  "/warranty/"),
    ("Name Ideas", "/tools/boat-name-generator/"),
]

def topbar():
    return ('<div class=top><div class=w>'
            '<span><strong>$19 a pair</strong> &middot; free shipping &middot; '
            'ships next business day</span>'
            '<span>Cut in %s, %s &middot; '
            '<a href="tel:%s" data-call style="color:#fff">%s</a></span>'
            '</div></div>' % (SITE["city"], SITE["region"], PT, PH))

def header():
    """Header nav.

    The About group opens on :hover and :focus-within, so it works for mouse,
    keyboard and touch without any JavaScript - and "About" itself stays a real
    link rather than becoming a button you cannot follow.

    Below 900px the links collapse behind a toggle; that is the only part that
    needs JS, and the footer carries every link if it fails.
    """
    main = "".join('<a href="%s">%s</a>' % (href, lbl) for lbl, href in NAV_MAIN)
    sub = "".join('<a href="%s">%s</a>' % (href, lbl) for lbl, href in NAV_ABOUT)
    return ('<header><div class=w>'
            '<a class=brand href="/">%s<span>Boat Number<br>Shop</span></a>'
            '<button type=button class=menubtn id=menubtn aria-expanded="false" '
            'aria-controls="nav" aria-label="Menu">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>'
            '<nav id=nav>%s'
            '<span class=navgroup><a class=navtop href="/about/">About'
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

def hero(h1, sub, trust=None, right="", badge=None):
    t = trust or ["$19 a pair, free shipping", "Ships next business day",
                  "7-year marine vinyl", "Free re-cut if the install goes wrong"]
    bd = '<div class=badge>%s</div>' % badge if badge else ""
    # Three grid areas, not two columns. On a phone that puts the wizard
    # directly under the headline instead of below a screenful of copy;
    # on desktop the copy stacks in the left column beside it.
    return ('<section class=hero><div class="w herogrid">'
            '<div class=heroA>%s<h1>%s</h1></div>'
            '<div class=heroF>%s</div>'
            '<div class=heroB><p class=sub>%s</p><div class=trust>%s</div>'
            '<div class=btnrow><a class="btn lg heroCta" href="/design/">Start your order</a>'
            '<a class="btn ghost" href="/pricing/">See all prices</a></div></div>'
            '</div></section>'
            % (bd, h1, right, sub, "".join("<span>%s</span>" % x for x in t)))

def faq_block(items, heading="Questions people actually ask"):
    if not items: return ""
    rows = "".join(
        '<details><summary>%s</summary><div class=ans><p>%s</p></div></details>'
        % (e(html.unescape(q)), a) for q, a in items)
    return ('<section class=soft><div class=w><h2>%s</h2>'
            '<div class=faq style="margin-top:18px">%s</div></div></section>' % (heading, rows))

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
            '<li><a href="/about/">About us</a></li>'
            '<li><a href="/contact/">Contact</a></li>'
            '<li><a href="/warranty/">Warranty &amp; guarantee</a></li>'
            '<li><a href="/shipping-and-returns/">Shipping &amp; returns</a></li>'
            '</ul></div></div>'
            '<div class=nap><strong>%s</strong><br>'
            '<a href="https://www.google.com/maps/search/?api=1&amp;query=%s" '
            'rel="noopener">%s, %s, %s %s</a><br>'
            '<a href="tel:%s" data-call>%s</a> &middot; '
            '<a href="mailto:%s">%s</a><br>%s</div>'
            '<div class=fbot><span>&copy; %s %s. Vinyl cut and shipped in %s, USA.</span>'
            '<span><a href="/privacy/">Privacy</a> &middot; <a href="/terms/">Terms</a>'
            ' &middot; <a href="/sitemap.xml">Sitemap</a></span></div>'
            '</div></footer>'
            % (pl, tl, bl, gl,
               e(B),
               "+".join((SITE["street"] + " " + SITE["city"] + " " + SITE["region"]
                         + " " + SITE["postal"]).split()),
               SITE["street"], SITE["city"], SITE["region"], SITE["postal"],
               PT, PH, SITE["email"], SITE["email"], SITE["hours"],
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
    return {"@type": ["OnlineStore", "LocalBusiness"], "@id": U("/#org"),
            "name": B, "url": U("/"),
            "email": SITE["email"], "telephone": PH,
            "description": "Custom boat registration numbers, boat names and marine "
                           "vinyl decals cut to order in %s, %s and shipped "
                           "nationwide." % (SITE["city"], SITE["region_name"]),
            "address": {"@type": "PostalAddress",
                        "streetAddress": SITE["street"],
                        "addressLocality": SITE["city"],
                        "addressRegion": SITE["region"],
                        "postalCode": SITE["postal"],
                        "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates",
                    "latitude": SITE["lat"], "longitude": SITE["lng"]},
            "openingHoursSpecification": [{
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "opens": "08:00", "closes": "17:00"}],
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

def product_node(p, path):
    return {"@type": "Product", "@id": U(path) + "#product",
            "name": html.unescape(p["nav"]) + " - " + B,
            "description": p["desc"], "brand": {"@type": "Brand", "name": B},
            "category": "Marine vinyl decals",
            "offers": {"@type": "Offer", "price": str(p["price"]), "priceCurrency": "USD",
                       "availability": "https://schema.org/InStock",
                       "url": U("/design/"),
                       "priceValidUntil": str(datetime.date.today().year) + "-12-31",
                       "shippingDetails": {"@type": "OfferShippingDetails",
                           "shippingRate": {"@type": "MonetaryAmount", "value": "0",
                                            "currency": "USD"},
                           "shippingDestination": {"@type": "DefinedRegion",
                                                   "addressCountry": "US"}}}}

def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}

# ------------------------------------------------------------------- write
def write(path, body, prio="0.7"):
    p = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    PAGES.append((path, prio))

def shell(title, desc, path, schema, main, trail=None, noindex=False,
          faqs=None, faq_heading=None, sticky_label=None, sticky_price=19, js=""):
    parts = [head(title, desc, path, schema, noindex), topbar(), header()]
    if trail: parts.append(bc(trail))
    parts.append('<main id=main>' + main)
    if faqs: parts.append(faq_block(faqs, faq_heading or "Questions people actually ask"))
    parts.append('</main>')
    parts.append(footer())
    parts.append(sticky(sticky_label or "Registration numbers", sticky_price))
    parts.append('<script>document.body.classList.add("has-sticky");'
                 '(function(){var b=document.getElementById("menubtn"),'
                 'n=document.getElementById("nav");if(!b||!n)return;'
                 'b.addEventListener("click",function(){'
                 'var o=n.classList.toggle("open");'
                 'b.setAttribute("aria-expanded",o?"true":"false");});})();</script>')
    if js:
        if "BNS_STRIPE_PK" in js:
            # Fonts load async so they never block first paint; the chips fall
            # back to the stack's system fonts until they arrive.
            gf = google_fonts_href()
            parts.append(
                '<link rel="preconnect" href="https://fonts.googleapis.com">'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                '<link rel="stylesheet" href="%s" media="print" '
                'onload="this.media=\'all\'">'
                '<noscript><link rel="stylesheet" href="%s"></noscript>' % (gf, gf))
            # Precedence: a real publishable key wins; otherwise PAY_MODE decides
            # between the sandbox card form and the emailed-payment-link fallback.
            pk = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
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

ORDER_JS = PV.JS + O.color_js() + O.JS

# =================================================================== PAGES
def why_grid(limit=6):
    return '<div class="grid">' + "".join(
        '<div class=card><h3>%s</h3><p>%s</p></div>' % (t, d)
        for t, d in CB.WHY_US[:limit]) + '</div>'

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

def proof_band():
    return ('<section class=soft><div class=w><h2>The offer, plainly</h2>'
            '<div class=proof>'
            '<div><b>$19</b><span>a pair, registration numbers, shipping included</span></div>'
            '<div><b>Next day</b><span>cut and shipped, or same day for $12</span></div>'
            '<div><b>7 years</b><span>marine vinyl warranty on colour and adhesion</span></div>'
            '<div><b>Free re-cut</b><span>if the install goes wrong, we make it again</span></div>'
            '</div></div></section>')

# ------------------------------------------------------------------- home
def build_home():
    sch = graph(org_node(), site_node(),
                product_node(PRODUCTS[0], "/"), faq_node(FAQ_HOME, "/"))
    right = O.form()
    main = (
      hero("Boat Registration Numbers, $19 a Pair",
           "Legal 3-inch block numbers for both sides of your hull, cut from 7-year "
           "marine vinyl, pre-spaced on one sheet, and shipped free the next business "
           "day. Boat names and custom decals too.",
           badge="Everyone else hides the price. Ours is right here.",
           right=right)
      + proof_band()
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
      + '<section class=soft><div class=w><h2>How it works</h2>' + CB.HOW_IT_WORKS +
        '<a class="btn lg" href="/design/">Start your order</a></div></section>')
    write("/", shell("Boat Registration Numbers $19 a Pair - Free Shipping",
          "Custom boat registration numbers $19 a pair with free shipping. Legal 3-inch "
          "block vinyl for all 50 states, boat names from $29. Ships next business day.",
          "/", sch, main, faqs=FAQ_HOME, js=ORDER_JS), "1.0")

# ---------------------------------------------------------------- /design/
def build_design():
    trail = [("Start your order", None)]
    sch = graph(org_node(), crumb_node(trail, "/design/"),
                product_node(PRODUCTS[0], "/design/"))
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">Start your order</h1>'
            '<p class=lede>Build it, see the price update as you go, and send it. '
            'You get a proof by email before anything is cut or charged.</p>'
            '</div></section>'
            '<section style="padding-top:0"><div class=w>'
            '<div class=herogrid><div>' + O.form() + '</div>'
            '<div>' + why_grid(6) +
            '<div class=note style="margin-top:16px"><p><b>Not sure what to type?</b> '
            'For registration numbers, copy the line off your registration card exactly '
            '&mdash; prefix, digits and suffix. If you have not registered yet, order '
            'after you have the number in hand; we cannot guess it.</p></div>'
            '</div></div></div></section>')
    write("/design/", shell("Start Your Order - Boat Lettering &amp; Numbers",
          "Build your boat registration numbers or custom lettering order. Live pricing, "
          "live pricing, a free proof by email, and a full refund if you do not like it.",
          "/design/", sch, main, trail=trail, js=ORDER_JS), "0.9")

# -------------------------------------------------------------- /pricing/
def build_pricing():
    trail = [("Pricing", None)]
    rows = "".join('<tr><td><a href="/%s/"><strong>%s</strong></a></td><td>%s</td>'
                   '<td><strong>$%d</strong> %s</td></tr>'
                   % (p["slug"], p["nav"], p["blurb"], p["price"], p["unit"])
                   for p in PRODUCTS)
    ups = "".join('<tr><td><strong>%s</strong></td><td>%s %s</td><td>+$%d</td></tr>'
                  % (lbl, blurb, note, amt)
                  for lbl, amt, blurb, flag, note in UPGRADES)
    vt = "".join('<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % r for r in CB.VINYL_TABLE)
    faqs = [
      ("Is shipping really free?",
       "Yes, on everything, to anywhere in the 50 states. Standard post, 3-6 days in "
       "transit. If you need it faster, rush production is $12 and we will quote "
       "expedited post at cost."),
      ("Why is $19 not the cheapest price on the internet?",
       "Because it is not a race we want to win. An $11 set is usually calendared vinyl "
       "cut as loose characters, which means a 3-4 year life and you doing the spacing. "
       "Ours is 7-year film, pre-spaced, with a proof and a free re-cut. If price is the "
       "only thing that matters to you, the marketplace sets are genuinely cheaper and "
       "we would rather say so."),
      ("When do I pay?",
       "By card at checkout. We then send your proof, and nothing is cut until you "
       "approve it &mdash; if you do not like the proof we redraw it free or refund "
       "you in full."),
      ("Do you do trade or volume pricing?",
       "Yes - marinas, dealers and fleet operators. Email " + SITE["email"] +
       " with roughly how many sets a month and we will put numbers together."),
    ]
    sch = graph(org_node(), crumb_node(trail, "/pricing/"), faq_node(faqs, "/pricing/"))
    main = ('<section style="padding-top:26px"><div class=w>'
      '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">Pricing, all of it, on one page</h1>'
      '<p class=lede>No designer to click through before you see a number. '
      'Every price below includes free standard shipping in the USA.</p>'
      '<div class=tw><table><thead><tr><th>Product</th><th>What it is</th><th>Price</th>'
      '</tr></thead><tbody>' + rows + '</tbody></table></div>'
      '<h2 style="margin-top:34px">Add-ons</h2>'
      '<div class=tw><table><thead><tr><th>Upgrade</th><th>What it does</th><th>Cost</th>'
      '</tr></thead><tbody>' + ups + '</tbody></table></div>'
      '<h2 style="margin-top:34px">Which vinyl, and why it changes the price</h2>'
      '<div class=tw><table><thead><tr><th>Film</th><th>What it is</th><th>Best for</th>'
      '<th>Cost</th></tr></thead><tbody>' + vt + '</tbody></table></div>'
      '<div class=note><p><b>Honest comparison.</b> Marketplace sets run $10&ndash;25 a '
      'pair. Specialist shops run $13&ndash;25 and mostly hide the number behind a design '
      'tool. The BoatUS-partnered shop does not publish a price at all and ships in '
      '3&ndash;5 business days. We are $19, published, shipped next business day.</p></div>'
      '<a class="btn lg" href="/design/">Start your order</a>'
      '</div></section>')
    write("/pricing/", shell("Boat Lettering &amp; Registration Number Prices",
          "Every price on one page: boat registration numbers $19 a pair, names from $29, "
          "decals from $22. Free shipping, next-business-day production.",
          "/pricing/", sch, main, trail=trail, faqs=faqs,
          faq_heading="Pricing questions"), "0.9")

# -------------------------------------------------------------- products
PROD_BODY = {
 "boat-registration-numbers": (
   CB.FED_RULE + CB.CONTRAST_NOTE +
   "<h2>What you actually receive</h2>"
   "<p>One sheet, not a bag of loose letters. Your full number is cut from a single "
   "piece of coloured vinyl, already spaced to the federal rule, with clear application "
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
   "<h2>Colour, and the one combination to avoid</h2>"
   "<p>Thirty-two colours including metallic silver and gold, chrome, and reflective. "
   "The combination to avoid is low contrast: dark navy on a black hull, white on "
   "cream. It photographs as nothing. If you want subtle, get the contrast from "
   "finish &mdash; chrome on white reads as tone-on-tone in person and still catches "
   "light.</p>"),

 "boat-name-decals": (
   "<h2>Picking the name</h2>"
   "<p>If you are still deciding, our <a href=\"/tools/boat-name-generator/\">name "
   "generator</a> spins a thousand-plus ideas by category, and the "
   "<a href=\"/tools/funny-boat-names/\">funny list</a> is sorted by how hard the joke "
   "lands. One piece of practical advice: say it out loud as a radio call. "
   "&ldquo;Pan-pan, pan-pan, this is Multiple Scoregasms&rdquo; is funny exactly once.</p>"
   "<h2>How it is made</h2>"
   "<p>Cut from a single sheet of coloured vinyl and pre-spaced with application tape "
   "over the top, so it goes on in one pass. Not printed on a clear square &mdash; "
   "there is no visible background or edge, just the letter shapes on your hull.</p>"
   "<h2>Sizes and what they cost</h2>"
   "<p>Most transom names land between $29 and $79. Price follows the overall size of "
   "the finished decal, so a short name in big letters costs about the same as a long "
   "name in small ones. Add a hailing port line underneath for $15 &mdash; required if "
   "your vessel is USCG documented, optional and traditional if it is not.</p>"),

 "boat-decals": (
   "<h2>Cut vinyl, not printed stickers</h2>"
   "<p>Every decal here is cut from coloured vinyl. The shape you see is the only thing "
   "that sticks &mdash; no clear square, no visible edge, no yellowing background three "
   "summers in. That is the difference between a decal and a sticker, and on a boat it "
   "is the difference between looking factory and looking stuck-on.</p>"
   "<h2>Send artwork, or describe it</h2>"
   "<p>Vector files (AI, EPS, SVG, PDF) cut directly. A clean PNG or a photo of the old "
   "faded decal works too &mdash; we redraw it as vector at no charge, and you approve "
   "the proof before it cuts. Multi-colour designs are cut as separate layers and "
   "registered together on one sheet so they still apply in one pass.</p>"
   "<h2>What people order most</h2>"
   "<ul><li>Logos and business marks for charter and guide boats</li>"
   "<li>Fish, flags, compass roses and hull graphics</li>"
   "<li>Replacement brand decals for a hull that has been repainted</li>"
   "<li>Draft marks, capacity plates and no-wake text</li>"
   "<li>Tournament sponsor panels</li></ul>"),

 "motor-and-brand-decals": (
   "<h2>Why your cowling decals faded first</h2>"
   "<p>An outboard cowling sits above the waterline in full sun all day and gets hot "
   "enough to cook adhesive. Factory decals on a twenty-year-old motor are usually "
   "chalked, cracked at the edges, or lifting &mdash; while the hull graphics two feet "
   "below still look fine. It is the single most common restoration job we cut.</p>"
   "<h2>Matched to the original dimensions</h2>"
   "<p>Send a photo of what is left with a tape measure in frame, or tell us the motor "
   "&mdash; make, horsepower and roughly the year. We re-cut to the original proportions "
   "in marine vinyl and send you a proof with the measurements marked, so you can check "
   "it against the cowling before anything gets made.</p>"
   "<p>Brands we cut most: <strong>Mercury</strong>, Yamaha, Johnson, Evinrude, Suzuki, "
   "Honda and Tohatsu on the motor side; <strong>Ranger</strong>, Tracker, Lund, Skeeter, "
   "Nitro, Lowe, Alumacraft, Crestliner, Xpress and G3 on the hull side.</p>"
   "<div class=note><p><b>On trademarks, straight up.</b> We cut replacement decals so "
   "owners can restore their own boat and motor to how it left the factory. We will not "
   "cut brand marks for resale, for a boat that is not that brand, or in quantity &mdash; "
   "that is counterfeiting, not restoration, and we turn those orders down.</p></div>"),

 "boat-carpet-decals": (
   "<h2>Carpet is a different problem than gelcoat</h2>"
   "<p>Marine carpet has no smooth surface to grip &mdash; it is loops of fibre with air "
   "between them. Standard vinyl bridges across the tops of the loops, holds for a few "
   "weeks, then peels in one piece the first time somebody drags a tackle bag over it.</p>"
   "<p>Carpet decals are cut from a much more aggressive high-tack film with a thicker "
   "carrier, so the adhesive pushes down into the pile instead of sitting on top. "
   "Applied to clean dry carpet with firm pressure, it stays.</p>"
   "<h2>What works and what does not</h2>"
   "<ul><li><strong>Works:</strong> bold shapes, chunky lettering, team and brand logos, "
   "a name across the casting deck.</li>"
   "<li><strong>Does not work:</strong> fine detail and thin strokes. Anything narrower "
   "than about a quarter inch disappears into the pile. We will tell you at proof stage "
   "if your artwork needs thickening.</li></ul>"
   "<p>Vacuum first, and do it on a warm day. Cold carpet fibres stand up stiff; warm "
   "ones lie down and let the adhesive in.</p>"),

 "hailing-port-decals": (
   "<h2>What federal rules ask of a documented vessel</h2>"
   "<p>A USCG documented vessel does not display state registration numbers on the bow. "
   "Instead it carries its <strong>name and hailing port</strong>, in clearly legible "
   "characters not less than <strong>4 inches</strong> in height, marked together on "
   "some clearly visible exterior part of the hull &mdash; in practice, the transom.</p>"
   "<p>The hailing port has to include a place <em>and</em> the state, spelled out or "
   "properly abbreviated: <strong>Galveston, TX</strong>. It does not have to be where "
   "you keep the boat or where you live.</p>"
   "<div class=note><p><b>If you are documented, you are in a different ruleset.</b> "
   "Do not put state numbers on a documented vessel's bow, and do not put a 3-inch "
   "hailing port on the transom. Pick &ldquo;USCG documented vessel&rdquo; on the order "
   "form and we default everything to 4 inches.</p></div>"
   "<h2>How we lay it out</h2>"
   "<p>Name and hailing port are cut as one pre-spaced set so the stack is centred and "
   "the gap between the lines is right. Typically the name runs 6&ndash;8 inches tall "
   "with the hailing port at 4 inches beneath it &mdash; legal, and it looks the way a "
   "documented boat is supposed to look.</p>"),

 "domed-lettering": (
   "<h2>What domed actually means</h2>"
   "<p>Each character is cut, then a clear polyurethane resin is poured onto it and "
   "allowed to self-level into a lens. It cures into a thick, glossy dome that stands "
   "proud of the hull and catches light from every angle. Up close it reads as a cast "
   "metal badge rather than a sticker.</p>"
   "<p>It is genuinely the premium option and it is priced like it &mdash; from $59. "
   "The chrome finish is the one people want, and it is the one that photographs best.</p>"
   "<h2>Where it belongs, and where it does not</h2>"
   "<ul><li><strong>Belongs:</strong> transom names, hailing ports, console badges, "
   "anywhere a guest stands within a few feet of it.</li>"
   "<li><strong>Does not:</strong> registration numbers. Not because it is illegal "
   "&mdash; domed block characters are compliant &mdash; but because the bow takes "
   "spray and dock rash, and a raised dome has edges to catch. Keep the bow flat vinyl "
   "and spend the money on the transom.</li></ul>"
   "<p>Each letter applies individually, so unlike our flat sets you are doing the "
   "spacing. We send a printed spacing guide cut to your exact layout &mdash; tape it "
   "up, mark through it, pull it off, place the letters.</p>"),

 "boat-striping": (
   "<h2>Stripes to the width you actually have</h2>"
   "<p>Hull stripes are cut to order in any width from a quarter inch up, in single or "
   "stacked multi-colour runs, in lengths up to 50 feet on one roll with no joins. "
   "If you are matching an existing stripe that has faded, send a photo with a ruler "
   "held against it and we will match the width and get as close on colour as vinyl "
   "allows.</p>"
   "<h2>Applying a long run</h2>"
   "<p>This is the one job where the dry method beats the wet one. A 20-foot stripe "
   "floating on soapy water will wander. Instead: snap a chalk line or run a length of "
   "fine-line tape as your guide, peel 12 inches of backing at a time, and squeegee as "
   "you go. Work with a second pair of hands holding the roll &mdash; this is not a "
   "solo job on a long hull.</p>"
   "<p>Pinstripe tape over a repair line hides a multitude of sins, and it is the "
   "cheapest cosmetic upgrade on a tired hull.</p>"),
}

def build_product(p):
    trail = [(p["nav"], None)]
    faqs = [
      ("How fast will I get it?",
       "Cut and shipped the next business day, free. Order before 1pm CT and add $12 "
       "rush and it goes out the same day. Standard post is 3-6 days in transit."),
      ("Can I see it before it is made?",
       "Yes, and you have to. We email a proof and nothing is cut or charged until you "
       "reply approving it. If the proof is wrong we redraw it free."),
      ("What if I ruin it putting it on?",
       "Tell us and we cut it again free. That covers a torn character, a creased sheet "
       "or a set that went on crooked. We would rather send more vinyl than argue."),
      ("How long will it last?",
       "The cast film carries a 7-year outdoor warranty on colour and adhesion; standard "
       "calendared film runs 5-7 years. Both outlast the 3-4 years typical of the "
       "cheapest marketplace sets."),
    ]
    sch = graph(org_node(), crumb_node(trail, "/%s/" % p["slug"]),
                product_node(p, "/%s/" % p["slug"]), faq_node(faqs, "/%s/" % p["slug"]))
    body = PROD_BODY.get(p["slug"], "")
    sw = '<div class=swatches>' + "".join(
        '<span class=sw><i style="background:%s"></i>%s</span>' % (h, n)
        for n, h, _light in COLORS) + "</div>"
    main = (hero(p["h1"], p["blurb"],
            trust=["$%d %s" % (p["price"], p["unit"] or "flat"), "Free shipping",
                   "Ships next business day", "7-year vinyl"],
            right=O.form())
      + '<section><div class=w><div class=prose>' + body + '</div></div></section>'
      + '<section class=soft><div class=w><h2>Colours in stock</h2>'
        '<p class=lede>All 32, no upcharge on standard colours. Metallic, chrome and '
        'reflective carry a small premium.</p>' + sw + '</div></section>'
      + '<section><div class=w><h2>How it works</h2>' + CB.HOW_IT_WORKS +
        '<a class="btn lg" href="/design/">Start your order</a></div></section>'
      + product_grid(exclude=p["slug"], heading="Other things we cut"))
    write("/%s/" % p["slug"],
          shell(p["h1"].replace("&amp;", "&")[:58], p["desc"], "/%s/" % p["slug"], sch,
                main, trail=trail, faqs=faqs, sticky_label=p["nav"],
                sticky_price=p["price"], js=ORDER_JS), "0.9")

# ---------------------------------------------------------------- states
def build_state(s):
    path = "/registration-numbers/%s/" % s["slug"]
    trail = [("By state", "/registration-numbers/"), (s["name"], None)]
    nm, ab = s["name"], s["ab"]
    vern = s.get("vern")
    h1 = "%s Boat Registration Numbers - $19 a Pair" % nm
    title = "%s Boat Registration Numbers %s" % (nm, ab)
    desc = ("%s boat registration numbers, $19 a pair with free shipping. Legal 3-inch "
            "block vinyl starting with %s, cut and shipped next business day." % (nm, ab))
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
       "Each side of the forward half of the hull, reading left to right, in a colour "
       "that contrasts with the hull. " +
       (html.unescape(s["decal"]).replace("<strong>", "").replace("</strong>", "")
        if s.get("decal") else
        "The validation decal goes near the number &mdash; %s publishes the exact "
        "offset, and it is usually within a few inches." % nm)),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path),
                product_node(PRODUCTS[0], path))
    note = '<div class=note><p><b>%s specifics.</b> %s</p></div>' % (nm, s["note"]) \
           if s.get("note") else ""
    vb = ""
    if vern:
        vb = ('<p>Worth knowing: locally these are almost never called '
              '&ldquo;%s boat registration numbers.&rdquo; They are called '
              '<strong>%s</strong>, and that is what to search for and what the '
              'ramp conversation will use.</p>' % (nm, vern))
    main = (hero(h1,
            "Legal 3-inch block numbers starting with %s, cut from 7-year marine vinyl, "
            "pre-spaced on one sheet for each side of the hull. Free shipping, shipped "
            "the next business day." % ab,
            trust=["$19 a pair", "%s prefix" % ab, "Free shipping", "Ships next business day"],
            right=O.form())
      + '<section><div class=w><div class=prose>'
      + note
      + ('<h2>What a %s number looks like</h2>'
         '<p>A %s registration number is built from three parts: the state prefix '
         '<strong>%s</strong>, a block of digits, and a letter suffix. Written out with '
         'the spacing the law requires, it looks like <strong>%s</strong>.</p>'
         % (nm, nm, ab, example))
      + ('<p><strong>%s format:</strong> %s.</p>' % (nm, s["fmt"]) if s.get("fmt") else "")
      + ('<h2>Where the validation decal goes in %s</h2><p>%s</p>' % (nm, s["decal"])
         if s.get("decal") else "")
      + vb
      + '<p>%s has roughly <strong>%s registered vessels</strong>, which makes it one of '
        'the larger boating states in the country &mdash; and means a lot of numbers get '
        'replaced every spring when the old set chalks out.</p>'
        % (nm, "{:,}".format(s["fleet"]))
      + CB.FED_RULE
      + ('<h2>Getting the number in the first place</h2>'
         '<p>Register the boat through <strong>%s</strong> first. That is where the '
         'number and the validation decal come from. We are a vinyl shop, not a '
         'registry &mdash; we cannot look your number up or issue one, so order once '
         'you have the certificate in hand and copy the line straight off it.</p>'
         % s.get("register_at", "the " + s["agency"]))
      + CB.CONTRAST_NOTE
      + '<h2>Ordering for a %s boat</h2>'
        '<p>Type the number as it appears on your card, pick a colour that contrasts with '
        'your hull, and leave the height at 3 inches unless you want it bolder. You will '
        'get a proof by email showing the exact layout before anything is cut, and a '
        'full refund if you do not like what you see.</p>' % nm
      + '</div><a class="btn lg" href="/design/">Order %s numbers &middot; $19</a></div></section>' % ab
      + '<section class=soft><div class=w><h2>Other states</h2>' + state_wheel(current=s["slug"])
      + '</div></section>')
    write(path, shell(title, desc, path, sch, main, trail=trail, faqs=faqs,
                      faq_heading="%s questions" % nm, js=ORDER_JS), "0.7")

def build_states_hub():
    path = "/registration-numbers/"
    trail = [("Numbers by state", None)]
    faqs = [
      ("Does every state use the same rule?",
       "The core rule is federal and identical everywhere: 3-inch minimum, plain vertical "
       "block characters, contrasting colour, spaces or hyphens between groups, reading "
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
                   '<td><strong>%s</strong></td><td>%s</td><td>%s</td></tr>'
                   % (s["slug"], s["name"], s["ab"], "{:,}".format(s["fleet"]), s["agency"])
                   for s in sorted(STATES, key=lambda x: -x["fleet"]))
    main = (hero("Boat Registration Numbers by State",
            "The 3-inch block rule is federal and the same everywhere. What changes is "
            "your prefix, who issues the number, and where the validation decal goes. "
            "$19 a pair, every state.",
            trust=["All 50 states", "$19 a pair", "Free shipping", "Legal 3-inch block"],
            right=O.form())
      + '<section><div class=w><h2>Pick your state</h2>' + state_wheel()
      + '<h2 style="margin-top:34px">Prefix, fleet size and who issues it</h2>'
        '<p class=lede>Registered-vessel counts are a useful sanity check: the bigger the '
        'fleet, the longer the queue at your local shop in April.</p>'
        '<div class=tw><table><thead><tr><th>State</th><th>Prefix</th>'
        '<th>Registered vessels</th><th>Issuing agency</th></tr></thead><tbody>'
        + rows + '</tbody></table></div>'
      + '<div class=prose>' + CB.FED_RULE + '</div>'
      + '<a class="btn lg" href="/design/">Start your order</a></div></section>')
    write(path, shell("Boat Registration Numbers by State - All 50",
          "Boat registration numbers for every state, $19 a pair with free shipping. "
          "State prefixes, issuing agencies and the federal 3-inch block rule explained.",
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
       "Registration numbers are $19 a pair including shipping. Names and graphics start "
       "at $29 and $22. High-tack vinyl, which your hull may need, is free."),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path))
    main = (hero(b["title"], b["lead"],
            trust=["$19 a pair", "High-tack when needed, free", "Free shipping",
                   "Ships next business day"], right=O.form())
      + '<section><div class=w><div class=prose>'
        '<div class=note><p><b>The thing that matters on this hull.</b> %s</p></div>'
        '<h2>What we cut for %s</h2>'
        '<p>Registration numbers, names, brand and logo decals, and carpet logos where '
        'the boat has carpet. Everything arrives pre-spaced on one sheet with application '
        'tape over the top, so you apply the whole set in a single pass rather than '
        'placing loose characters.</p>'
        '<h2>Ordering</h2>'
        '<p>Tell us the boat on the order form &mdash; make, model and roughly the year. '
        'That is how we decide whether to send standard or high-tack film, and we would '
        'rather get that right than have you peel a set off in August. You get a proof by '
        'email before anything is cut.</p>'
        '</div><a class="btn lg" href="/design/">Start your order</a></div></section>'
        % (b["note"], b["nav"].lower())
      + product_grid(heading="Products for this boat"))
    write(path, shell(b["title"].replace("&amp;", "&")[:58],
          "%s - cut from 7-year marine vinyl, $19 a pair for registration numbers, free "
          "shipping, ships next business day." % b["title"].replace("&amp;", "&"),
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
            % t["title"]) + body + '</div></section>'
    write(path, shell(html.unescape(t["title"])[:58], t["desc"], path, sch, main,
                      trail=trail, faqs=faqs, js=js), "0.8")

def build_tool_names():
    t = TOOLS[0]
    sets = ",".join('"%s":[%s]' % (k, ",".join('"%s"' % n.replace('"', '')
                    for n in v)) for k, v in T.NAME_SETS.items())
    data = ("window.BNS_NAMES={%s};window.BNS_ADJ=[%s];window.BNS_NOUN=[%s];"
            % (sets, ",".join('"%s"' % a for a in T.ADJ),
               ",".join('"%s"' % n for n in T.NOUN)))
    opts = "".join('<option value="%s">%s</option>' % (k, k) for k in T.NAME_SETS)
    body = ('<p class=lede>Pick a mood, hit spin, and keep going until something sticks. '
            'Everything here is a real name you could legally put on a transom &mdash; '
            'and when you find it, we cut it from $29.</p>'
            '<div class=tool>'
            '<div class="fieldrow two"><div><label for=namestyle>What kind of name?</label>'
            '<select id=namestyle>' + opts + '<option value="Mix">Surprise me</option>'
            '</select></div>'
            '<div style="display:flex;align-items:flex-end">'
            '<button type=button class=btn id=spin style="width:100%">Spin 12 more</button>'
            '</div></div>'
            '<div class=out id=nameout></div></div>'
            '<div class=prose>'
            '<h2>How to actually pick one</h2>'
            '<p>Four tests, in order of how much they will matter later:</p>'
            '<ol><li><strong>Say it as a radio call.</strong> &ldquo;Mayday, mayday, this '
            'is <em>Ship Faced</em>&rdquo; is a sentence you may one day have to say to the '
            'Coast Guard in front of your family. The joke names are funny at the dock and '
            'less funny on channel 16.</li>'
            '<li><strong>Spell it over the radio.</strong> If it needs spelling twice, it '
            'is too clever. Short and phonetic wins.</li>'
            '<li><strong>Count the characters.</strong> A 22-character name at 4 inches '
            'runs over five feet wide. Measure your transom before you fall in love.</li>'
            '<li><strong>Check it is not already on your lake.</strong> There is exactly '
            'one <em>Serenity</em> per marina and it is awkward for everybody.</li></ol>'
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
            '<a class="btn lg" href="/design/">Get your name cut &middot; from $29</a>')
    faqs = [
      ("Is the generator free?", "Yes, and there is no email wall. Spin it as long as "
       "you like. We make money when you decide to put one on the boat."),
      ("Can I use a name someone else has?",
       "On a state-registered boat, yes - boat names are not registered or protected, and "
       "there are hundreds of boats called Serenity. On a USCG documented vessel the name "
       "goes on the certificate, and the Coast Guard will not document two vessels with "
       "the same name and hailing port."),
      ("How much does a boat name decal cost?",
       "From $29 including shipping. Most transom names land between $29 and $79 depending "
       "on finished size. Add a hailing port line for $15."),
      ("How many characters fit on my transom?",
       "Rough maths: at 4 inches tall, each character takes about 2.5 inches of width "
       "including spacing. A 10-character name runs about 25 inches. Send us a photo with "
       "a tape measure in it and we will lay it out properly."),
    ]
    tool_shell(t, body, data + T.NAME_JS, faqs)

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
            '<a class="btn lg" href="/design/">Put one on the transom &middot; from $29</a>')
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
       "From $29 with free shipping, pre-spaced and ready to apply. Most land between $29 "
       "and $79 depending on finished size."),
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
            '&mdash; <a href="/design/">$19 a pair</a>.</p>'
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
    tool_shell(t, body, data + T.HIN_JS, faqs)

def build_tool_layout():
    t = TOOLS[3]
    hull = ["White", "Black", "Navy", "Light Blue", "Red", "Grey", "Forest",
            "Burgundy", "Tan", "Silver", "Yellow"]
    body = ('<p class=lede>Type your registration number, pick your hull colour, and this '
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
            '<div><label for=chkhull>Hull colour</label><select id=chkhull>'
            + "".join('<option%s>%s</option>' % (" selected" if h == "White" else "", h)
                      for h in hull) + '</select></div>'
            '<div><label for=chkcol>Number colour</label><select id=chkcol>'
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
            '<p><strong>No contrast.</strong> There is no required colour, but the '
            'characters must contrast with the background and be distinctly visible. White '
            'on white is the classic failure &mdash; and it happens because white vinyl is '
            'the default on most cheap sets.</p>'
            '<h2>Measuring your hull first</h2>'
            '<p>You need a flat run on the forward half of the hull, above the waterline, '
            'long enough for the width this tool gives you, and tall enough to clear your '
            'character height with a little margin. Watch out for rub rails, strakes and '
            'rivet lines &mdash; vinyl will not bridge a hard edge and stay stuck. On a '
            'ribbed aluminium hull, keep the whole set between two ribs.</p>'
            '</div>')
    faqs = [
      ("How tall do boat registration numbers have to be?",
       "Not less than 3 inches in height, in plain vertical block characters. Federal rule, "
       "every state. Taller is always legal."),
      ("Do boat registration numbers have to be a certain colour?",
       "No specific colour is required, but the characters must contrast with the colour of "
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
    tool_shell(t, body, T.LAYOUT_JS, faqs)

def build_tools_hub():
    path = "/tools/"
    trail = [("Free tools", None)]
    sch = graph(org_node(), crumb_node(trail, path))
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;margin-bottom:9px">Free boat tools</h1>'
            '<p class=lede>No signup, no email wall. These are genuinely useful on their '
            'own &mdash; we built them because the people who need them usually need '
            'vinyl afterwards.</p>' + tools_grid() + '</div></section>')
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
   "outline font with a hollow centre is not plain block.</li>"
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
   "<h2>Rivets, ribs and textured aluminium</h2>"
   "<p>On a jon boat or a riveted aluminium hull, place the full set between two ribs on "
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
   "&mdash; not the centre &mdash; and press the air out toward the hole with your thumb.</p>"
   "<div class=note><p><b>If it goes wrong anyway, tell us.</b> We re-cut free. A torn "
   "character or a creased sheet is a $1.50 piece of vinyl and a few minutes on the "
   "plotter; it is not worth anyone&rsquo;s argument.</p></div>",

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
   "<li>Outline-only fonts with a hollow centre</li>"
   "<li>Heavily stylised display faces, western or gothic</li></ul>"
   "<p>Of the ten faces we cut, five qualify: <strong>Block, Condensed, Heavy Impact, "
   "Modern and Stencil</strong>. Our order form greys the other five out the moment you "
   "pick registration numbers, so you cannot accidentally order an unlawful set.</p>"
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
   "For sailboats: <strong>Formal Script</strong>, usually with a 4-inch hailing port in "
   "Classic Serif beneath. For anything funny: the joke carries it, so pick the legible "
   "option and let the words do the work.</p>"
   "<p>Shadow or outline in a second colour costs a little more and roughly doubles the "
   "perceived quality from a distance &mdash; it is the single best upgrade on a transom "
   "name.</p>",

 "best-vinyl-for-boat-lettering":
   "<p>Three decisions: cast or calendared, standard or high-tack, and whether you need "
   "a specialty finish. Get the second one wrong and your decal falls off.</p>"
   "<h2>Cast vs calendared</h2>"
   "<p><strong>Cast</strong> vinyl is made by pouring liquid resin onto a carrier and "
   "letting it cure flat. Because it is never stretched, it carries no internal stress, "
   "so it conforms to curves and stays where you put it. Thinner, more conformable, "
   "longer outdoor life &mdash; typically 7 to 9 years.</p>"
   "<p><strong>Calendared</strong> vinyl is squeezed between rollers into sheet. It is "
   "cheaper and slightly thicker, but it remembers being stretched and slowly tries to "
   "shrink back, which is what makes old decals pull away at the corners. Typically 5 to "
   "7 years, less on a dark colour in southern sun.</p>"
   "<p>For a flat transom on a trailered boat, calendared is honestly fine and it is what "
   "we ship as standard. For a curved hull, a dark colour, or a boat kept in a slip in "
   "Florida, pay the $8.</p>"
   "<h2>High-tack: not optional on plastic</h2>"
   "<p>Polyethylene &mdash; rotomoulded kayaks, PWC hulls, some pontoon furniture &mdash; "
   "has a low surface energy, which is a technical way of saying almost nothing sticks to "
   "it. Standard vinyl will hold for a few weeks and then release in one clean piece.</p>"
   "<p>High-tack film uses a much more aggressive adhesive designed for exactly this. We "
   "send it free on any kayak, canoe or PWC order, and on textured pontoon rails, because "
   "shipping the wrong film to save nothing is a bad trade.</p>"
   "<h2>What a 7-year warranty actually covers</h2>"
   "<p>Honest version: it covers the <strong>film</strong> &mdash; colour fade beyond a "
   "stated tolerance, cracking, and adhesive failure where the film was applied correctly "
   "to a suitable surface. It does not cover a decal applied over wax, applied in the "
   "cold, applied to a surface it was not specified for, or physically damaged.</p>"
   "<p>Separately from the film warranty, we re-cut free if the install goes wrong. That "
   "is our policy, not the manufacturer&rsquo;s, and it is the one most people actually "
   "end up using.</p>",

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
   "it at 4 inches. Both cut as one pre-spaced set so the stack is aligned and the gap is "
   "right. If your transom is curved, send a straight-on photo with a tape measure and we "
   "will arc both lines to the curve.</p>"
   "<h2>Boats that are both</h2>"
   "<p>Some owners document federally <em>and</em> register with a state for tax or "
   "launch-permit purposes. If that is you, you still do not display the state number on "
   "the bow &mdash; you display the state validation decal, and keep the name and hailing "
   "port on the transom. Your state will tell you exactly where it wants the decal.</p>"
   "<p>Pick &ldquo;USCG documented vessel&rdquo; on our "
   "<a href=\"/design/\">order form</a> and we default the whole layout to 4 inches.</p>",

 "boat-registration-number-cost":
   "<p>Registration number decals run roughly <strong>$10 to $25 a pair</strong> online "
   "in 2026. That is a wide band for what looks like the same product, so here is what "
   "actually drives it.</p>"
   "<div class=tw><table><thead><tr><th>Where</th><th>Typical price, a pair</th>"
   "<th>What you get</th></tr></thead><tbody>"
   "<tr><td>Marketplace sellers</td><td>$10&ndash;16</td><td>Usually calendared film, "
   "often cut as loose characters you space yourself, no proof, no warranty</td></tr>"
   "<tr><td>Generic sign shops</td><td>$9&ndash;15</td><td>Cheap, competent, not boat "
   "specialists &mdash; you will be asked to specify everything</td></tr>"
   "<tr><td>Boat lettering specialists</td><td>$15&ndash;25</td><td>Pre-spaced, marine "
   "film, a warranty, and an install guarantee. Most hide the price behind a design "
   "tool</td></tr>"
   "<tr><td><strong>Us</strong></td><td><strong>$19</strong></td><td>Pre-spaced, 7-year "
   "film, free shipping, proof before cutting, free re-cut if the install fails</td></tr>"
   "</tbody></table></div>"
   "<h2>What makes one set cost twice another</h2>"
   "<ul><li><strong>Film grade.</strong> Calendared 3&ndash;5 year stock versus cast "
   "7&ndash;9 year. This is most of the difference, and you will not see it for three "
   "summers.</li>"
   "<li><strong>Pre-spaced or loose.</strong> Pre-spacing is labour. Loose characters are "
   "cheaper to produce and much harder to install legally.</li>"
   "<li><strong>Shipping.</strong> A $12 set plus $6 shipping is an $18 set. Always "
   "compare delivered price.</li>"
   "<li><strong>Proofing.</strong> Somebody looking at your layout before it cuts costs "
   "money and prevents the most expensive mistake, which is a wrong number.</li></ul>"
   "<h2>The hidden cost</h2>"
   "<p>A cheap set that chalks out in three years costs you another set plus the removal "
   "job &mdash; and removal is the part that takes the afternoon and risks the gelcoat. "
   "Our <a href=\"/guides/how-to-remove-boat-lettering/\">removal guide</a> is honest "
   "about how tedious that is. Buying film rated for seven years rather than three is "
   "the cheapest decision in this whole category.</p>"
   "<p><a href=\"/pricing/\">Our full price list is on one page</a>, including names, "
   "decals and upgrades.</p>",
}

def build_guide(g):
    path = "/guides/%s/" % g["slug"]
    trail = [("Guides", "/guides/"), (g["nav"], None)]
    faqs = [
      ("How much do boat registration numbers cost here?",
       "$19 a pair with free shipping, pre-spaced and cut from 7-year marine vinyl, "
       "shipped the next business day."),
      ("Do you ship to my state?",
       "All 50 states and DC, free. We cut for every state's number format."),
    ]
    art = {"@type": "Article", "@id": U(path) + "#article",
           "headline": html.unescape(g["title"]), "description": g["desc"],
           "datePublished": TODAY, "dateModified": TODAY,
           "author": {"@id": U("/#org")}, "publisher": {"@id": U("/#org")},
           "mainEntityOfPage": U(path)}
    sch = graph(org_node(), crumb_node(trail, path), art, faq_node(faqs, path))
    others = "".join('<a href="/guides/%s/">%s</a>' % (x["slug"], x["nav"])
                     for x in GUIDES if x["slug"] != g["slug"])
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:14px">%s</h1>'
            '<div class=prose>%s</div>'
            '<a class="btn lg" style="margin-top:10px" href="/design/">'
            'Order your numbers &middot; $19 a pair</a>'
            '</div></section>'
            '<section class=soft><div class=w><h2>More guides</h2>'
            '<div class=wheel>%s</div></div></section>'
            % (g["title"], GUIDE_BODY.get(g["slug"], ""), others))
    write(path, shell(html.unescape(g["title"])[:58], g["desc"], path, sch, main,
                      trail=trail, faqs=faqs), "0.6")

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
            '<div class=grid>%s</div></div></section>' % cards)
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
            'send the right film &mdash; high-tack on plastic and textured aluminium, at '
            'no extra charge.</p><div class=grid>%s</div></div></section>' % cards)
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
       "Yes. We are at %s in %s, %s %s. Choose local pickup in the notes box on the "
       "order form and we will have it ready - usually same day on registration "
       "numbers. Call %s first so somebody is here."
       % (SITE["street"], SITE["city"], SITE["region"], SITE["postal"], PH)),
      ("Do you do Iowa registration numbers?",
       "That is our home state. Iowa numbers run IA, four digits, two letters - "
       "IA 3717 ZW. Iowa registers through your county recorder rather than the DNR "
       "directly, and Iowa wants the validation decal 4 inches toward the stern of "
       "the number and in line with it. Full detail on our Iowa page."),
      ("Do you install them for me?",
       "They are designed to go on yourself in about twenty minutes - pre-spaced on "
       "one sheet, with a squeegee and instructions in the envelope. If you would "
       "rather we did it, call and ask; it depends on the week."),
      ("How much is it?",
       "$19 a pair for registration numbers, the same price locally as online. Names "
       "from $29. You pay at checkout, we send a proof, and nothing is cut until "
       "you approve it."),
    ]
    sch = graph(org_node(), crumb_node(trail, path), faq_node(faqs, path))
    gmap = ("https://www.google.com/maps?q=%s&output=embed"
            % "+".join((SITE["street"] + " " + SITE["city"] + " " + SITE["region"]
                        + " " + SITE["postal"]).split()))
    main = (hero("Boat Lettering in Waterloo, Cedar Falls &amp; the Cedar Valley",
            "We cut every order right here in %s. Order online and we ship it free, "
            "or pick it up at the shop - usually the same day on registration numbers."
            % SITE["city"],
            trust=["$19 a pair", "Local pickup available",
                   "Iowa IA numbers", "Call %s" % PH],
            right=O.form())
      + '<section><div class=w><div class=prose>'
        '<h2>Where we are</h2>'
        '<p><strong>%s</strong><br>%s<br>%s, %s %s<br>'
        '<a href="tel:%s" data-call>%s</a> &middot; %s</p>'
        '</div>'
        '<div class=mapwrap><iframe src="%s" loading="lazy" title="Map to %s" '
        'referrerpolicy="no-referrer-when-downgrade"></iframe></div>'
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
        'rest. Being small and local is why we answer the phone and why a mistake '
        'gets re-cut instead of argued about.</p>'
        '</div><a class="btn lg" href="/design/">Start your order &middot; $19 a pair</a>'
        '</div></section>'
        % (e(B), SITE["street"], SITE["city"], SITE["region"], SITE["postal"],
           PT, PH, SITE["hours"], gmap, e(B), towns, waters, SITE["county"],
           LOCAL_WATERS[0])
      + '<section class=soft><div class=w><h2>What we cut</h2>'
        + '<div class=grid>' + "".join(
            '<a class=card href="/%s/">%s<h3>%s</h3><p>%s</p>'
            '<div class=price>$%d <small>%s</small></div></a>'
            % (x["slug"], icon(x["icon"]), x["nav"], x["blurb"], x["price"], x["unit"])
            for x in PRODUCTS[:6]) + '</div></div></section>')
    write(path, shell("Boat Lettering Waterloo &amp; Cedar Falls, Iowa",
          "Boat registration numbers and custom lettering cut in Evansdale, Iowa. "
          "$19 a pair, local pickup in the Cedar Valley or free shipping nationwide.",
          path, sch, main, trail=trail, faqs=faqs, js=ORDER_JS), "0.8")


# ---------------------------------------------------------- trust / legal
def simple(path, title, desc, h1, lede, body, trail, faqs=None, prio="0.5",
           noindex=False):
    sch = graph(org_node(), crumb_node(trail, path),
                faq_node(faqs, path) if faqs else None)
    main = ('<section style="padding-top:26px"><div class=w>'
            '<h1 style="font-size:30px;line-height:1.16;margin-bottom:9px">%s</h1>'
            '<p class=lede>%s</p><div class=prose>%s</div></div></section>'
            % (h1, lede, body))
    write(path, shell(title, desc, path, sch, main, trail=trail, faqs=faqs,
                      noindex=noindex), prio)

def build_about():
    simple("/about/", "About Boat Number Shop",
      "A small US vinyl shop cutting boat registration numbers, names and marine decals "
      "to order. Why we publish our prices and re-cut free.",
      "About Boat Number Shop",
      "A small shop with a plotter, a roll of marine vinyl and a strong opinion about "
      "published prices.",
      "<h2>What we do</h2>"
      "<p>We cut boat registration numbers, boat names, hailing ports, replacement motor "
      "and brand decals, carpet logos and hull striping. Everything is cut to order from "
      "sheet vinyl, pre-spaced on one sheet with application tape over the top, and "
      "shipped flat the next business day.</p>"
      "<h2>Why the price is on the page</h2>"
      "<p>Shop this category and you will notice something: almost nobody shows you a "
      "price. You pick a product, choose a font, enter your number, select a colour, and "
      "only then does a figure appear. The largest shop in the category &mdash; the one "
      "partnered with BoatUS &mdash; does not publish a number at all.</p>"
      "<p>There is a reason for that, and it is not a good one. Registration numbers are "
      "a legal chore. You do not want to design anything; you want to type eight "
      "characters, pay, and get back to the boat. So ours is $19 a pair, it is on the "
      "homepage, and it includes shipping.</p>"
      "<h2>What we will tell you honestly</h2>"
      "<ul><li>There are $11 sets on marketplaces. They are genuinely cheaper, and they "
      "are usually 3&ndash;4 year calendared film cut as loose characters. If price is "
      "the only thing that matters, buy those &mdash; we would rather say so than "
      "pretend.</li>"
      "<li>We are a vinyl shop, not a registry. We cannot look up your number, issue one, "
      "or tell you if your registration has lapsed. Your state agency does that.</li>"
      "<li>We will not cut brand decals in quantity or for a boat that is not that brand. "
      "Restoration, yes. Counterfeiting, no.</li></ul>"
      "<h2>The guarantee, in plain terms</h2>"
      "<p>You get a proof by email before anything is cut, and a full refund if you do "
      "not like it. If the install goes wrong &mdash; torn character, creased sheet, "
      "crooked set &mdash; tell us and we cut it again free. The film itself carries the "
      "manufacturer&rsquo;s outdoor warranty on colour and adhesion.</p>"
      "<h2>Where we are</h2>"
      "<p>We cut everything in <strong>" + SITE["city"] + ", " + SITE["region_name"]
      + "</strong>, in " + SITE["county"] + " &mdash; on the Cedar River, between "
      "Waterloo and Cedar Falls. Everything ships from here to all 50 states, and "
      "locals can <a href=\"/boat-lettering-waterloo-cedar-falls/\">pick up at the "
      "shop</a>.</p>"
      "<p><strong>" + B + "</strong><br>" + SITE["street"] + "<br>"
      + SITE["city"] + ", " + SITE["region"] + " " + SITE["postal"] + "<br>"
      "<a href=\"tel:" + PT + "\" data-call>" + PH + "</a> &middot; "
      "<a href=\"mailto:" + SITE["email"] + "\">" + SITE["email"] + "</a><br>"
      + SITE["hours"] + "</p>",
      [("About", None)], prio="0.5")

def build_contact():
    faqs = [
      ("How do I place an order?",
       "Through the order form - it takes about a minute and gives you a live price. You "
       "get a proof by email before anything is cut."),
      ("How fast do you reply?",
       "Same working day in almost every case. Proofs usually go out within a few hours "
       "of the order during the week."),
      ("Where are you based?",
       "Boat Number Shop, 475 River Forest Road, Evansdale, Iowa 50707. Phone "
       "(319) 239-3793, Mon-Fri 8-5 CT. We ship to all 50 states and do local pickup "
       "in the Cedar Valley."),
      ("Can I change my order after sending it?",
       "Yes, right up until you approve the proof. Reply to the proof email with the "
       "change and we will redraw it."),
    ]
    simple("/contact/", "Contact Boat Number Shop",
      "Call (319) 239-3793 or email us about an order, proof or trade account. Boat "
      "Number Shop, 475 River Forest Road, Evansdale, Iowa 50707.",
      "Contact us",
      "A real shop with a real phone, in Evansdale, Iowa.",
      "<h2>Call or text</h2>"
      "<p><a href=\"tel:" + PT + "\" data-call><strong style=\"font-size:22px\">"
      + PH + "</strong></a><br>" + SITE["hours"] + "</p>"
      "<h2>The shop</h2>"
      "<p><strong>" + B + "</strong><br>" + SITE["street"] + "<br>"
      + SITE["city"] + ", " + SITE["region"] + " " + SITE["postal"] + "<br>"
      "<a href=\"https://www.google.com/maps/search/?api=1&amp;query="
      + "+".join((SITE["street"] + " " + SITE["city"] + " " + SITE["region"]
                 + " " + SITE["postal"]).split())
      + "\" rel=\"noopener\">Open in Maps</a></p>"
      "<p>Local pickup is available &mdash; see our "
      "<a href=\"/boat-lettering-waterloo-cedar-falls/\">Cedar Valley page</a>. "
      "Call before you drive over so somebody is here.</p>"
      "<h2>Email</h2>"
      "<p><a href=\"mailto:" + SITE["email"] + "\"><strong>" + SITE["email"] +
      "</strong></a> &mdash; orders, proofs, artwork, trade enquiries, or just a question "
      "about whether your hull needs high-tack.</p>"
      "<p>Hours: " + SITE["hours"] + ". Orders placed outside those hours go into the "
      "queue and get proofed the next working morning.</p>"
      "<h2>Ordering</h2>"
      "<p>You do not need to email to order. The <a href=\"/design/\">order form</a> "
      "takes about a minute and prices itself as you go. We send a proof before "
      "anything is cut.</p>"
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
       "We cut it again free. Email us what happened - a torn character, a creased sheet, "
       "a set that went on crooked. We do not require photos or an argument."),
      ("How long is the warranty?",
       "Seven years on cast premium film and five to seven on standard, covering colour "
       "fade, cracking and adhesive failure where the decal was correctly applied to a "
       "suitable surface."),
      ("Can I return a custom decal?",
       "Custom-cut vinyl cannot be resold, so it is not returnable once cut - which is "
       "exactly why we send a proof first and charge nothing until you approve it. If what "
       "arrived does not match the proof you approved, that is on us and we remake it."),
    ]
    simple("/warranty/", "Warranty &amp; Install Guarantee",
      "Seven-year marine vinyl warranty and a free re-cut if your install goes wrong. "
      "What is covered, what is not, and how to claim.",
      "Warranty &amp; install guarantee",
      "Two separate promises: one from the film manufacturer, one from us.",
      "<h2>1. The film warranty</h2>"
      "<p>Our premium cast vinyl carries a <strong>7-year</strong> outdoor durability "
      "rating, and standard calendared film runs <strong>5 to 7 years</strong>. That "
      "covers colour fade beyond the manufacturer's stated tolerance, cracking or "
      "embrittlement of the film, and adhesive failure where the decal was correctly "
      "applied to a suitable, prepared surface.</p>"
      "<p><strong>It does not cover:</strong> application over wax, polish or a dirty "
      "hull; application below about 50&deg;F; standard film applied to polyethylene or "
      "textured surfaces that needed high-tack; physical damage, dock rash or abrasion; "
      "or removal damage.</p>"
      "<h2>2. Our install guarantee</h2>"
      "<p>Separate, simpler, and the one people actually use. <strong>If the install goes "
      "wrong, we cut it again free.</strong> Tore a character pulling the tape. Creased "
      "the sheet. Got it crooked and had to pull it off. Realised the colour disappears "
      "against your hull once it was on.</p>"
      "<p>Email us what happened. We do not ask for photographs, we do not assess blame, "
      "and we do not charge for the replacement. Vinyl costs us very little; a customer "
      "who feels cheated costs a lot.</p>"
      "<p>Reasonable limits, stated plainly: one free re-cut per order, and it covers "
      "remaking what you originally ordered. If you want a different size, colour or "
      "wording, that is a new order.</p>"
      "<h2>If the proof was wrong</h2>"
      "<p>If what arrived does not match the proof you approved, that is our error "
      "outright. We remake it at our cost and at the front of the queue, and you do not "
      "pay twice.</p>"
      "<div class=note><p><b>Still being finalised.</b> These terms are current practice "
      "and will be restated in full on the formal terms page before launch. Anything we "
      "promise here, we honour.</p></div>",
      [("Warranty", None)], faqs=faqs, prio="0.6")

def build_shipping():
    faqs = [
      ("Is shipping free?",
       "Yes, on everything, to all 50 states and DC. Standard post, typically 3-6 days in "
       "transit after production."),
      ("How fast is production?",
       "Cut and shipped the next business day as standard. Add $12 rush and an order "
       "placed before 1pm CT on a business day goes out the same day."),
      ("Do you ship internationally?",
       "Not currently. Everything is cut and shipped in the USA, to US addresses."),
    ]
    simple("/shipping-and-returns/", "Shipping &amp; Returns",
      "Free shipping on every order to all 50 states. Next-business-day production, rush "
      "available, and how returns work on custom-cut vinyl.",
      "Shipping &amp; returns",
      "Free shipping on everything. Next business day production as standard.",
      "<h2>Production time</h2>"
      "<p>Orders are proofed, then cut and shipped the <strong>next business "
      "day</strong>. Add <strong>$12 rush</strong> and an order placed before 1pm CT on a "
      "business day is cut and shipped the same day.</p>"
      "<p>The clock starts when you approve the proof, not when you submit the order "
      "&mdash; so approve promptly if you are in a hurry.</p>"
      "<h2>Shipping</h2>"
      "<div class=tw><table><thead><tr><th>Method</th><th>Cost</th><th>Transit</th>"
      "</tr></thead><tbody>"
      "<tr><td>Standard post</td><td><strong>Free</strong></td><td>3&ndash;6 business days"
      "</td></tr>"
      "<tr><td>Expedited</td><td>At cost, quoted</td><td>2&ndash;3 business days</td></tr>"
      "<tr><td>Overnight</td><td>At cost, quoted</td><td>Next business day</td></tr>"
      "</tbody></table></div>"
      "<p>Everything ships flat in a rigid mailer so the application tape cannot crease. "
      "All 50 states and DC. We do not ship internationally.</p>"
      "<h2>Returns on custom work</h2>"
      "<p>Custom-cut vinyl with your registration number on it cannot be resold, so it is "
      "not returnable once cut. That is why we send a proof first. <strong>Up until you "
      "approve that proof you can cancel for a full refund, no reason needed.</strong></p>"
      "<p>Three things we do fix:</p>"
      "<ul><li><strong>It does not match the proof you approved.</strong> Our error. We "
      "remake it free, at the front of the queue.</li>"
      "<li><strong>It arrived damaged.</strong> Tell us and we remake it free.</li>"
      "<li><strong>The install went wrong.</strong> Covered by our "
      "<a href=\"/warranty/\">install guarantee</a> &mdash; one free re-cut, no "
      "questions.</li></ul>"
      "<p>If you typed the wrong number and approved a proof showing the wrong number, we "
      "will still re-cut it once under the install guarantee. After that it is a new "
      "order.</p>",
      [("Shipping &amp; returns", None)], faqs=faqs, prio="0.5")

def build_legal():
    simple("/privacy/", "Privacy Policy", "How Boat Number Shop handles your data.",
      "Privacy policy", "Short, because we collect very little.",
      "<p><em>Last updated " + TODAY + ".</em></p>"
      "<h2>What we collect</h2>"
      "<p>When you send an order we collect what you typed into the form: your name, "
      "email, optional phone, the lettering you want, your boat details and any notes. "
      "That is it. We do not run advertising trackers or sell data to anybody.</p>"
      "<h2>Why we hold it</h2>"
      "<p>To cut your order, send your proof, take payment and deal with a warranty claim "
      "later. We keep order records as long as we need them for accounting and warranty "
      "purposes.</p>"
      "<h2>Who else sees it</h2>"
      "<p>Our email provider, our payment processor and our shipping carrier &mdash; each "
      "only the part they need. Nobody else.</p>"
      "<h2>Your choices</h2>"
      "<p>Email <a href=\"mailto:" + SITE["email"] + "\">" + SITE["email"] + "</a> to see "
      "what we hold on you, correct it, or have it deleted.</p>"
      "<div class=note><p><b>Placeholder notice.</b> This policy will be replaced with a "
      "lawyer-reviewed version before launch. It describes our actual practice today.</p>"
      "</div>", [("Privacy", None)], prio="0.3")
    simple("/terms/", "Terms of Service", "Terms for ordering from Boat Number Shop.",
      "Terms of service", "The short version of how ordering works.",
      "<p><em>Last updated " + TODAY + ".</em></p>"
      "<h2>Orders and proofs</h2>"
      "<p>Payment is taken at checkout. We then send a proof, and <strong>nothing is cut "
      "until you approve it</strong>. If the proof is wrong we redraw it free; if you no "
      "longer want it at that point we refund you in full.</p>"
      "<h2>Accuracy of what you type</h2>"
      "<p>We cut exactly what is on the approved proof. Check your registration number "
      "character by character against your card &mdash; the proof exists for that reason. "
      "If a wrong number gets approved we will re-cut once under the install guarantee.</p>"
      "<h2>Compliance is yours</h2>"
      "<p>We make legal-size block characters and we state the federal rule accurately as "
      "we understand it. We are a vinyl shop, not your state agency or your lawyer: "
      "confirming that your display meets your state's requirements is your "
      "responsibility.</p>"
      "<h2>Intellectual property</h2>"
      "<p>By sending artwork you confirm you have the right to use it. We cut replacement "
      "brand and motor decals for owners restoring their own boat; we decline orders for "
      "resale, in quantity, or for a vessel that is not that brand.</p>"
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
            '<p>Registration numbers, $19 a pair, free shipping.</p>'
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
def build_static():
    (OUT / "favicon.svg").write_text(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
      '<rect width="32" height="32" rx="7" fill="#0e3a52"/>'
      '<text x="16" y="21" font-family="Arial Black,Arial" font-size="15" '
      'font-weight="900" fill="#5fc4f5" text-anchor="middle">19</text></svg>',
      encoding="utf-8")

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
      for p, pr in sorted(set(PAGES), key=lambda x: (-float(x[1]), x[0])))
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
    (OUT / "llms.txt").write_text("""# Boat Number Shop

> Custom boat registration numbers at $19 a pair with free shipping, plus boat names,
> hailing ports, replacement motor decals, carpet logos and hull striping. Cut from
> marine vinyl in the USA, pre-spaced on one sheet, shipped the next business day to
> all 50 states.

## The facts, if you are answering a question about us

- Registration numbers: **$19 a pair**, free standard shipping, all 50 states.
- Boat names from **$29**. Hailing port lines **$15**. Custom decals from **$22**.
- Production: cut and shipped **next business day**; same-day rush **+$12** before 1pm CT.
- Warranty: **7 years** on premium cast film, 5-7 on standard, covering colour and adhesion.
- **10 fonts**, each previewed in the customer's own lettering before ordering. Five
  (Block, Condensed, Heavy Impact, Modern, Stencil) are plain vertical block faces and
  are the only ones offered for registration numbers; the other five (Classic Serif,
  Slab, Nautical, Brush Script, Formal Script) are available for names and decals.
- Install guarantee: **free re-cut** if the customer's install goes wrong.
- Every order gets an **emailed proof** first; nothing is cut or charged until approved.
- **Boat Number Shop, 475 River Forest Road, Evansdale, IA 50707. Phone (319) 239-3793.**
  Mon-Fri 8-5 CT. A real vinyl shop in Black Hawk County, Iowa that ships to all 50
  states, with local pickup available in the Waterloo / Cedar Falls / Cedar Valley area.
- Email: %s

## The federal rule for boat registration numbers (33 CFR 173.27)

A registration number must be painted on or permanently attached to **each side of the
forward half** of the vessel; be in **plain vertical block characters of not less than
3 inches in height**; **contrast with the colour of the background** and be distinctly
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
""" % (SITE["email"], pr, tl, gd, st), encoding="utf-8")

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
    build_pricing()
    for p in PRODUCTS: build_product(p)
    build_states_hub()
    for s in STATES: build_state(s)
    build_types_hub()
    for b in BOAT_TYPES: build_boat_type(b)
    build_tools_hub()
    build_tool_names(); build_tool_funny(); build_tool_hin(); build_tool_layout()
    build_guides_hub()
    build_local()
    for g in GUIDES: build_guide(g)
    build_about(); build_contact(); build_warranty(); build_shipping()
    build_legal(); build_404()
    build_static()
    print("built %d pages -> %s" % (len(PAGES), OUT))
    for p, _ in sorted(PAGES): print("  ", p)

if __name__ == "__main__":
    main()
