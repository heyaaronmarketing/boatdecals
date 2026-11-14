# -*- coding: utf-8 -*-
"""Content model for Number My Boat.

Every number in VOL/CPC came from a live DataForSEO google_ads search_volume
pull on 2026-10-22 (location_code 2840). FLEET counts are registered-vessel
totals per state. Both are recorded so later edits can be argued with data
instead of taste.
"""

SITE = {
    "brand": "Number My Boat",
    "short": "Number My Boat",
    "url": "https://numbermyboat.com",
    "domain": "numbermyboat.com",
    "tagline": None,   # set from PRICE below - SITE is defined first
    "email": "orders@numbermyboat.com",
    "hours": "Mon-Fri 8-5 CT",
    # NO PHONE, NO STREET ADDRESS, NO COORDINATES - Aaron's call 2026-10-30.
    # The shop runs out of a private home, so the address and the landline are
    # personal information, not business information. Town and state stay:
    # "cut in Evansdale, Iowa" is a real differentiator and gives away nothing.
    #
    # This is also why the schema is OnlineStore + Organization and NOT
    # LocalBusiness. A LocalBusiness entity without a street address is a
    # half-filled listing that Google treats as low quality, and the site does
    # not want walk-ins anyway - it ships to all 50 states.
    "city": "Evansdale",
    "region": "IA",
    "region_name": "Iowa",
    "county": "Black Hawk County",
    "metro": "the Cedar Valley",
}

# Towns inside a sensible drive of the shop. Used for ONE local page, not a
# town grid - local volume here is tiny and a grid would be a doorway farm.
LOCAL_TOWNS = ["Evansdale", "Waterloo", "Cedar Falls", "Waverly", "Independence",
               "La Porte City", "Hudson", "Denver", "Janesville", "Dunkerton",
               "Jesup", "Gilbertville", "Raymond", "Elk Run Heights"]

LOCAL_WATERS = ["the Cedar River", "George Wyth Lake", "Big Woods Lake",
                "Casey's Lake", "Meyers Lake", "the Wapsipinicon River",
                "Hickory Hills Lake", "Island Park"]

# ---------------------------------------------------------------- the offer
PRICE = {
    # ---------------------------------------------------------------------
    # THE ONE PLACE. Every price on the site, in the order form, in the
    # Stripe intent, in catalog.json, in the JSON-LD offers and in every MCP
    # quote resolves to a number in this dict.
    #
    # It is not a convention, it is enforced three ways:
    #   * worker/price-data.js is GENERATED from here by mcp/build_price_js.py
    #     and worker/price.js is the only pricing function - the order form
    #     gets the same module inlined, so the browser and the server cannot
    #     disagree;
    #   * verify.py regenerates price-data.js and fails the build on any diff;
    #   * verify.py fails the build if any superseded price literal
    #     survives anywhere in engine/, media/ or public/.
    #
    # Set 2026-11-13. The figures it replaced are in git, not in a comment
    # here - a comment naming the old price is the thing the gate below is
    # for, and an exception carved out for one is an exception.
    # ---------------------------------------------------------------------
    "numbers": 28,
    # Character height upcharge on a REGISTRATION NUMBER set. A name is not
    # priced by height - it is priced by the width it finishes at, which
    # already moves with height. Charging both would charge twice for one
    # thing.
    "height_add": {"3": 0, "4": 8, "5": 15, "6": 20},
    # A name is priced by the width it finishes at, because that is what it
    # costs us: vinyl area, plotter time and weeding all track width, and a
    # 9-character name at 3 inches is a different job from a 22-character one
    # at 6. The site has always SAID "priced by finished size" on /pricing/
    # while the form charged a flat rate plus a height step; this is the
    # first version where the two agree.
    #
    # Banded on the finished width rounded UP to the whole inch, so the
    # published table has no gap in it: a name that finishes at 22.0" is
    # small, 22.1" is medium. Rounding down would have left 22.1-22.9"
    # priced as "up to 22 inches", which is not what the page says.
    "name_bands": [
        {"key": "small",  "max_in": 22,   "price": 38, "label": "up to 22 in"},
        {"key": "medium", "max_in": 30,   "price": 53, "label": "23-30 in"},
        {"key": "large",  "max_in": 48,   "price": 68, "label": "31-48 in"},
        {"key": "xl",     "max_in": None, "price": 88, "label": "over 48 in"},
    ],
    # Shorthands for copy. Derived below so prose cannot drift from the bands.
    "name_from": 38,
    # The range quoted as "most land $38-68": small through large. XL exists
    # and is priced, but a transom name that finishes over four feet across
    # is not what "most" means, and quoting $88 as the top of a typical range
    # reads as a warning rather than a price.
    "name_typical_to": 68,
    # The bundle. A name AND a pair of numbers in one envelope: one proof,
    # one setup, one package, so $10 of it is work we only do once.
    "bundle_off": 10,
    # A contrasting outline is a SECOND layer of vinyl: cut separately,
    # weeded separately, and registered against the first by hand. Roughly
    # double the work, which is what the price reflects.
    "outline": 12,
    "rush": 12,
    "kit": 6,
    "free_ship_over": 0,     # free shipping on everything
    # What a pair costs elsewhere online, for the comparison on /pricing/ and
    # in the homepage FAQ. A claim about other people's prices, so it lives
    # here next to ours and gets changed deliberately, not in passing.
    "market_low": 15,
    "market_high": 39,
    # When the current prices took effect. Structured data publishes this as
    # the offer's validFrom, so it has to be a real date and not today's - an
    # offer that claims to have started this morning every time the site is
    # rebuilt is a lie that Google can see. Change it when the prices change.
    "set_on": "2026-11-13",
}

# ------------------------------------------------------------------ IndexNow
# Tells Bing (and Yandex) that a page changed, instead of waiting to be
# crawled. Worth having here specifically because Bing's index is what ChatGPT
# search reads, and this site is built to be quoted by answer engines - so the
# question that matters is not where we rank on Bing, it is how long after a
# change Bing knows. The November price change is the case in point: 55 pages
# changed price at once and nothing told anybody.
#
# NOT A SECRET, by design. The verification mechanism is that this same string
# is served from https://numbermyboat.com/<key>.txt - a public URL - so
# whoever can publish that file is taken to control the site. A Worker secret
# would hide it from the repo while still publishing it on the web, which is
# the worst of both.
#
# engine/build.py writes the key file as part of the normal build, so a
# rebuild cannot forget it and a rotated key leaves no stale file behind (the
# build wipes public/ first). verify.py fails the build if the file is missing
# or stops matching. Submit with: python3 mcp/indexnow.py
INDEXNOW_KEY = "26928a3ecc7144db8956fa776b142f7e"

# Derived, so no second copy of the arithmetic exists anywhere.
# Entry bundle: 3-inch numbers plus the smallest name band, less the bundle
# discount. 28 + 38 - 10 = 56.
PRICE["bundle_from"] = (PRICE["numbers"] + PRICE["name_from"]
                        - PRICE["bundle_off"])
assert PRICE["name_from"] == PRICE["name_bands"][0]["price"]
assert PRICE["name_typical_to"] == PRICE["name_bands"][-2]["price"]
assert PRICE["height_add"]["3"] == 0, "the published base price is the 3 inch one"

# SITE has to exist before PRICE (the states and the waters are read above it),
# so the one line of SITE that quotes a price is filled in here instead of
# carrying a second copy of the figure.
SITE["tagline"] = ("Boat registration numbers, $%d a pair. Proof in 12 hours."
                   % PRICE["numbers"])

UPGRADES = [
    # No year figure, in the label or the blurb. See the film-life gate in
    # verify.py: this site states the film maker's own warranty and does not
    # publish a durability figure of its own.
    ("Premium cast vinyl instead of calendared", 8,
     "Cast film rather than calendared - deeper color that resists chalking "
     "and shrink-back.",
     "Most popular", "Worth it if the boat lives outside or you picked a dark color."),
    ("Spare set - a second pair at half price", 9,
     "A whole second pair in the envelope for when one gets dock-rashed.",
     "Best value", "Cheaper now than reordering later, and shipping is already paid."),
    ("Install kit - squeegee + solution + tape", PRICE["kit"],
     "The felt squeegee and application fluid that make the wet method foolproof.",
     "", "A bare set ships with a basic squeegee. This is the proper kit."),
    ("Rush - cut and shipped today", PRICE["rush"],
     "Jumps the queue. Order before 1pm CT on a business day.",
     "", "Only worth it if you are launching this weekend."),
    ("Reflective finish", 10,
     "Glass-bead film that lights up under a spotlight at night.",
     "", "Legal in every state. Popular on working and patrol boats."),
]

# ---------------------------------------------------------------- products
# vol/cpc = the primary keyword this page is built to win.
PRODUCTS = [
    dict(slug="boat-registration-numbers", nav="Registration numbers", short="Reg numbers",
         h1="Boat Registration Numbers for Any Boat, Legal in All 50 States",
         title="Boat Registration Numbers for All 50 States",
         kw="boat registration numbers", vol=5400, cpc=2.60, price=PRICE["numbers"],
         unit="a pair", icon="numbers",
         # THE PRODUCT, photographed. Not the OG share card, which carries
         # marketing text across it - a price badge and a headline burned into
         # the image is the one thing a merchant listing image must not be.
         # Largest first: Google takes the first it can fetch.
         # AL-01 is "IA 3717 ZW, 3 inch black on a white hull" - the thing
         # being sold, on a hull, which is what the buyer is deciding about.
         image=["AL-01-1400", "AL-01-800"],
         blurb="Legal 3-inch block numbers for both sides of the hull. Pre-spaced on one sheet so you apply them in a single pass.",
         desc="Custom boat registration numbers, $%d a pair with free shipping. "
              "Legal 3-inch block vinyl for all 50 states. Proof emailed "
              "within 12 hours." % PRICE["numbers"]),
    dict(slug="boat-lettering", nav="Boat letters", short="Lettering",
         h1="Boat Letters &amp; Name Decals - Any Font, From $%d" % PRICE["name_from"],
         title="Boat Letters &amp; Name Decals, Any Font",
         kw="boat lettering", vol=2400, cpc=4.59, price=PRICE["name_from"],
         unit="to start", icon="letter",
         # AL-03, "transom name, 6 inch black script".
         image=["AL-03-1400", "AL-03-800"],
         blurb="Boat names, hailing ports and any other transom text. You pick the font and the color, we cut it, pre-space it and tape it.",
         desc="Boat name decals and custom vinyl lettering from $%d. 10 marine "
              "fonts previewed live, white or black, free shipping, next-day "
              "production." % PRICE["name_from"]),
]

# -------------------------------------------------------------- boat types
BOAT_TYPES = [
    dict(slug="sailboats", nav="Sailboats", title="Sailboat Name Decals &amp; Lettering",
         kw="sailboat name decals", vol=1600, cpc=3.54,
         lead="Transom names and lettering for sail. Curved transoms need the layout drawn to the curve, so send us a photo with a tape measure in it.",
         note="A sailboat transom is rarely flat. Send a straight-on photo with a tape measure in frame and we will lay the name out to the actual curve."),
    dict(slug="pontoon-boats", nav="Pontoon boats", title="Pontoon Boat Decals &amp; Lettering",
         kw="pontoon boat decals", vol=480, cpc=0.59,
         lead="Fence-panel graphics, deck names and registration numbers sized for aluminum rails.",
         note="Pontoon fencing is usually brushed or painted aluminum. We ship high-tack vinyl for it by default, because standard adhesive lifts off a textured rail."),
    dict(slug="jet-skis-and-pwc", nav="Jet skis &amp; PWC", title="Jet Ski &amp; PWC Registration Numbers and Graphics",
         kw="jet ski decals", vol=210, cpc=0.90,
         lead="PWC hulls are moulded plastic with tight compound curves and almost no flat panel.",
         note="Plastic PWC hulls need high-tack vinyl. Standard vinyl will release from polyethylene inside a season - we send high-tack on every PWC order at no charge."),
    dict(slug="kayaks-and-canoes", nav="Kayaks &amp; canoes", title="Kayak &amp; Canoe Decals and Registration Numbers",
         kw="kayak decals", vol=320, cpc=0.39,
         lead="Most states only require numbers on a kayak once you hang a motor on it - including a trolling motor.",
         note="Rotomoulded polyethylene is the hardest surface in boating to stick to. High-tack vinyl, a clean alcohol wipe and a warm day are all mandatory."),
    dict(slug="bass-boats", nav="Bass boats", title="Bass Boat Decals &amp; Registration Numbers",
         kw="bass boat decals", vol=210, cpc=0.54,
         lead="Metalflake gelcoat, boat names and tournament sponsor panels.",
         note="Metalflake is glossy and very forgiving - the wet method works perfectly, and vinyl holds on it better than on almost any other hull finish."),
    dict(slug="jon-boats", nav="Jon boats", title="Jon Boat Decals &amp; Registration Numbers",
         kw="jon boat decals", vol=140, cpc=0.58,
         lead="Bare or painted aluminum, usually riveted, usually textured.",
         note="Rivets and ribs break the adhesive line. Keep numbers on a flat panel between ribs, or step down to a smaller character height that still clears the 3-inch minimum."),
]

# ------------------------------------------------------------------- tools
TOOLS = [
    dict(slug="boat-name-generator", nav="Name generator",
         title="Boat Name Generator - 1,000+ Ideas, Instantly",
         kw="boat name generator", vol=1900, cpc=1.61,
         desc="Free boat name generator. Spin clever, classic and funny boat names, then see your pick rendered in real marine fonts before you order."),
    dict(slug="funny-boat-names", nav="Funny names",
         title="400 Funny Boat Names That Actually Land",
         kw="funny boat names", vol=8100, cpc=0.09,
         desc="400 funny boat names sorted by how they land - puns, retirement jokes, money jokes and the ones that get groans at the ramp."),
    dict(slug="hull-number-decoder", nav="HIN decoder",
         title="Free Boat HIN Decoder - Read Your Hull Number",
         kw="boat hull numbers", vol=880, cpc=2.97,
         desc="Free boat HIN decoder. Paste a 12-character hull identification number to read the manufacturer code, serial, model year and build date."),
    dict(slug="registration-number-layout-checker", nav="Layout checker",
         title="Boat Registration Number Size &amp; Spacing Checker",
         kw="boat registration number size", vol=70, cpc=1.08,
         desc="Check your boat registration number against the federal 3-inch, block-character, contrast and spacing rules before you order."),
]

# ------------------------------------------------------------------ guides
GUIDES = [
    dict(slug="boat-registration-number-rules", nav="The rules",
         title="Boat Registration Number Rules, Plainly Stated",
         kw="boat registration number requirements", vol=140,
         desc="The federal rule for boat registration numbers - 3-inch block characters, contrasting color, correct spacing, forward half of each side - in plain English."),
    dict(slug="where-to-put-boat-registration-numbers", nav="Where they go",
         title="Where Do Boat Registration Numbers Go?",
         kw="where to place boat registration numbers", vol=430,
         desc="Boat registration numbers go on the forward half of both sides, reading left to right. Here is exactly how high, how far forward, and where the validation decal sits."),
    dict(slug="how-to-apply-boat-lettering", nav="How to apply",
         title="How to Apply Boat Lettering (Wet and Dry Method)",
         kw="how to apply boat lettering", vol=60,
         desc="Step-by-step: how to apply pre-spaced boat lettering and registration numbers using the wet method, with the mistakes that ruin a set."),
    dict(slug="how-to-remove-boat-lettering", nav="How to remove",
         title="How to Remove Old Boat Lettering Without Wrecking Gelcoat",
         kw="remove boat lettering", vol=20,
         desc="Heat, a plastic razor and adhesive remover will lift old boat lettering. What not to use on gelcoat, and how to deal with the shadow left behind."),
    dict(slug="boat-lettering-fonts", nav="Fonts",
         title="Boat Lettering Fonts: What Works on Water",
         kw="boat lettering fonts", vol=110,
         desc="Which fonts read from fifty yards, which ones are legal for registration numbers, and why script fails on a registration number but wins on a transom."),
    dict(slug="best-vinyl-for-boat-lettering", nav="Vinyl types",
         title="Best Vinyl for Boat Lettering: Cast vs Calendared",
         kw="best vinyl for boat lettering", vol=10,
         desc="Cast vs calendared vinyl for boats, when high-tack is mandatory, and what a film warranty actually covers."),
    dict(slug="documented-vessel-name-and-hailing-port", nav="Documented vessels",
         title="Documented Vessel Name &amp; Hailing Port Requirements",
         kw="documented vessel lettering", vol=10,
         desc="USCG documented vessels carry the name and hailing port in 4-inch characters, and do not display state registration numbers. Here is the layout."),
    dict(slug="boat-registration-number-cost", nav="What it costs",
         title="What Boat Registration Numbers Cost in 2026",
         kw="boat registration numbers cost", vol=30,
         desc="Boat registration number decals run $10-25 a pair online. What drives the price, what the cheap sets leave out, and what we charge."),
]

# ------------------------------------------------------------------ states
# fleet = registered vessels. vol = "{state} boat registration numbers".
# vern = local vernacular that outranks the generic phrasing.
STATES = [
    dict(slug="iowa", name="Iowa", ab="IA", vol=20,
         agency="Iowa DNR", tier=1, home=True,
         register_at="your county recorder's office (Iowa registers boats through "
                     "the county, not directly through the DNR)",
         fmt="IA 3717 ZW &mdash; the IA prefix, four digits, then two letters",
         decal="Iowa is specific about this: the validation decal goes on each side "
               "<strong>toward the stern of the registration number, 4 inches from it "
               "and in line with it</strong>. Not above, not below, not touching.",
         note="This is our home state &mdash; the shop is in Evansdale, in Black Hawk "
              "County. Iowa also says plainly that <strong>no other numbers may be "
              "displayed on either side of the bow</strong>, so strip any old set off "
              "before the new one goes on."),
    dict(slug="florida", name="Florida", ab="FL", vol=140,
         agency="Florida Department of Highway Safety and Motor Vehicles", tier=1),
    dict(slug="michigan", name="Michigan", ab="MC", vol=140,
         agency="Michigan Secretary of State", tier=1),
    dict(slug="new-york", name="New York", ab="NY", vol=20,
         agency="New York State DMV", tier=1),
    dict(slug="california", name="California", ab="CF", vol=630,
         agency="California DMV", tier=1, vern="CF numbers",
         note="California is the one state that does not use its postal abbreviation. "
              "California boat numbers start with <strong>CF</strong>, and locals call them "
              "CF numbers - which is what people actually search for."),
    dict(slug="south-carolina", name="South Carolina", ab="SC", vol=30,
         agency="South Carolina Department of Natural Resources", tier=1),
    dict(slug="wisconsin", name="Wisconsin", ab="WS", vol=70,
         agency="Wisconsin DNR", tier=1),
    dict(slug="minnesota", name="Minnesota", ab="MN", vol=30,
         agency="Minnesota DNR", tier=1),
    dict(slug="texas", name="Texas", ab="TX", vol=110,
         agency="Texas Parks and Wildlife Department", tier=1),
    dict(slug="pennsylvania", name="Pennsylvania", ab="PA", vol=10,
         agency="Pennsylvania Fish and Boat Commission", tier=1),
    dict(slug="north-carolina", name="North Carolina", ab="NC", vol=90,
         agency="NC Wildlife Resources Commission", tier=1),
    dict(slug="georgia", name="Georgia", ab="GA", vol=110,
         agency="Georgia DNR Wildlife Resources Division", tier=1),
    dict(slug="virginia", name="Virginia", ab="VA", vol=20,
         agency="Virginia Department of Wildlife Resources", tier=1),
    dict(slug="ohio", name="Ohio", ab="OH", vol=50,
         agency="Ohio DNR Division of Parks and Watercraft", tier=1),
    dict(slug="illinois", name="Illinois", ab="IL", vol=30,
         agency="Illinois DNR", tier=1),
    dict(slug="missouri", name="Missouri", ab="MO", vol=70,
         agency="Missouri State Highway Patrol", tier=1),
    dict(slug="washington", name="Washington", ab="WN", vol=40,
         agency="Washington State Department of Licensing", tier=2,
         note="Washington registration numbers begin with <strong>WN</strong>, not WA."),
    dict(slug="louisiana", name="Louisiana", ab="LA", vol=70,
         agency="Louisiana Department of Wildlife and Fisheries", tier=2),
    dict(slug="alabama", name="Alabama", ab="AL", vol=70,
         agency="Alabama Law Enforcement Agency, Marine Patrol", tier=2),
    dict(slug="tennessee", name="Tennessee", ab="TN", vol=20,
         agency="Tennessee Wildlife Resources Agency", tier=2),
    dict(slug="indiana", name="Indiana", ab="IN", vol=10,
         agency="Indiana Bureau of Motor Vehicles", tier=2),
]

# Ten fonts, previewed in the customer's own lettering before they pick.
#
# All ten are free Google Fonts, chosen deliberately: a vinyl plotter cuts any
# TTF, so the shop can install these and cut EXACTLY what the customer saw.
# Substituting a lookalike would make the preview a lie.
#
# block=True marks the faces that satisfy 33 CFR 173.27's "plain vertical block
# characters" - only those are offered for registration numbers.
#   (label, css family, Google spec, block-legal)
# (label, CSS family, Google Fonts spec, legal on a number, category)
#
# Three categories, because that is how the product actually splits and how a
# sign shop's font chart is organised:
#
#   block    plain vertical block faces. The ONLY ones legal on a
#            registration number under 33 CFR 173.27, which is also why they
#            look alike - the rule prescribes the shape. Variety here is
#            width, weight and corner treatment, not personality.
#   display  anything with character: slabs, fat serifs, western, techno,
#            dimensional. Names and lettering only.
#   script   brush, casual, formal and handwritten. Names and lettering only.
#
# Loaded ONE CATEGORY AT A TIME (see order.py): a face costs about 9KB and 72
# of them at once is not a thing to do to a phone. Someone cutting a
# registration number only ever loads the block set.
FONTS = [
    # The ten faces Ryan cuts with, named as he names them.
    #
    # Every one is an OPEN equivalent, not the Microsoft original. That is not
    # a shortcut - the originals ship with Windows and Office under a licence
    # that covers installing them, not serving them as webfonts, and a visitor
    # on a Mac or a phone does not have them at all. A face the browser cannot
    # load falls back silently, so the customer would approve one thing and
    # receive another, which is the single failure the preview and the proof
    # exist to prevent.
    #
    # So the rule is: the site renders what Ryan cuts. He installs these ten,
    # and preview, proof and plotter agree.
    #
    # `block` marks the five that satisfy 33 CFR 173.27's "plain vertical
    # block characters". The other five are serif, stencilled or decorative -
    # fine on a transom, not on a registration number.
    #
    # (label, css stack, Google spec, block_legal, match quality)
    ("Arial Bold",          "'Arimo',Arial,Helvetica,sans-serif",
     "Arimo:wght@700",            True,  "metric-compatible Arial"),
    ("Arial Black",         "'Archivo Black','Arial Black',sans-serif",
     "Archivo+Black",             True,  "very close"),
    ("Impact",              "'Anton',Impact,sans-serif",
     "Anton",                     True,  "the standard open Impact"),
    ("OCR A Extended",      "'Nova Mono',monospace",
     "Nova+Mono",                 True,  "loose - OCR-ish mono, not OCR A"),
    ("MS Gothic",           "'Noto Sans Mono',monospace",
     "Noto+Sans+Mono",            True,  "loose - plain mono sans"),
    ("Bodoni MT",           "'Bodoni Moda',Didot,Georgia,serif",
     "Bodoni+Moda:opsz@6..96",    False, "the same typeface"),
    ("Rockwell Extra Bold", "'Alfa Slab One',Rockwell,Georgia,serif",
     "Alfa+Slab+One",             False, "heavier than Rockwell XB"),
    ("Playbill",            "'Rye',Playbill,Georgia,serif",
     "Rye",                       False, "western slab, same spirit"),
    ("Snap ITC",            "'Bowlby One','Snap ITC',sans-serif",
     "Bowlby+One",                False, "fat round, less extreme"),
    ("Stencil",             "'Stardos Stencil',Stencil,sans-serif",
     "Stardos+Stencil:wght@700",  False, "close"),
]

# Stripe's publishable key. Public by design - it ships in the page source of
# every Stripe-powered site and can only confirm payments the server already
# authorised. It lives here rather than in an environment variable because the
# page is built, not served: a rebuild without the variable set drops the key,
# the card field cannot mount, and checkout silently degrades to "payment
# unavailable" with nothing in any log. STRIPE_PUBLISHABLE_KEY still overrides
# it for a one-off build.
STRIPE_PK = "pk_live_51UZidJLNiNr0qE3jmG1msQVtgUZYUiVXyBy9jP3HiVsLkB4Ym20VMv4YYecXVJEe0P6yAFLTUNmMtxLMBh4uVEtb00WZgUVDKw"

FONT_NAMES = [f[0] for f in FONTS]

# Five across. Ten faces is two tidy rows, and the five block-legal ones are
# Five across. Ten faces is two tidy rows, and the five block-legal ones are
# exactly the first row - so a registration-numbers order shows one row with
# nothing hidden behind a tab.
FONT_COLS = 5


def google_fonts_href():
    """All ten faces in one stylesheet.

    About 90KB. The 45-face version had to split by category and load them
    lazily because 650KB of type on a phone was indefensible; ten is small
    enough to arrive with the page, so the picker never shows a fallback.

    display=swap keeps the text visible while they land.
    """
    fams = "&".join("family=" + f[2] for f in FONTS)
    return "https://fonts.googleapis.com/css2?%s&display=swap" % fams


def head_fonts_href():
    return google_fonts_href()


# ------------------------------------------------- vessel number prefixes
# The two-letter prefix a state issues on a registration number. Established
# by the USCG under the Federal Boating Act of 1958 - five years BEFORE the
# Post Office standardised its own two-letter codes, which is why 11 of them
# disagree with the postal abbreviation.
#
# Two of those collide, and they are the reason this table exists rather than
# a postal-code lookup:
#   MS = Massachusetts (not Mississippi)
#   MI = Mississippi   (not Michigan)
#   MC = Michigan
#
# Sources: Murray Yacht Sales; Wisconsin DNR boating handbook ("WS 1234 AB");
# Michigan SOS watercraft dealer manual ("MC"). Secondary, not an official
# machine-readable feed - which is exactly why the validator warns and never
# blocks an order.
VESSEL_PREFIX = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR",
    "California":"CF","Colorado":"CL","Connecticut":"CT","Delaware":"DL",
    "District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HA",
    "Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KA",
    "Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MS","Michigan":"MC","Minnesota":"MN","Mississippi":"MI",
    "Missouri":"MO","Montana":"MT","Nebraska":"NB","Nevada":"NV",
    "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
    "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
    "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WN","West Virginia":"WV","Wisconsin":"WS",
    "Wyoming":"WY",
    # Territories issue numbers too.
    "American Samoa":"AS","Guam":"GU","Northern Mariana Islands":"CM",
    "Puerto Rico":"PR","US Virgin Islands":"VI",
}
# prefix -> state. A bijection, so a valid prefix names exactly one issuer.
PREFIX_STATE = {v: k for k, v in VESSEL_PREFIX.items()}
# postal code -> vessel prefix, for the 11 that disagree. Used by geo seeding.
POSTAL_TO_VESSEL = {"CA":"CF","CO":"CL","DE":"DL","HI":"HA","KS":"KA",
                    "MA":"MS","MI":"MC","MS":"MI","NE":"NB","WA":"WN","WI":"WS"}

# Postal codes a customer might type that are NOT valid vessel prefixes, so we
# can say exactly what they meant. MI and MS are deliberately absent: both ARE
# valid prefixes (Mississippi, Massachusetts), so "did you mean" there would be
# wrong as often as right.
POSTAL_MISTAKE = {
    "CA": ("California", "CF"),
    "CO": ("Colorado", "CL"),
    "DE": ("Delaware", "DL"),
    "HI": ("Hawaii", "HA"),
    "KS": ("Kansas", "KA"),
    "MA": ("Massachusetts", "MS"),
    "NE": ("Nebraska", "NB"),
    "WA": ("Washington", "WN"),
    "WI": ("Wisconsin", "WS"),
}

# Maine is the documented format outlier: 2 digits + 3 letters, or 4 digits +
# 1 letter, instead of the usual up-to-4 digits + up-to-2 letters.
FORMAT_EXCEPTIONS = {
    "ME": {"note": "Maine numbers run ME 12ABC or ME 1234A rather than the "
                   "usual four-digits-two-letters.",
           "patterns": [r"^\d{2}[A-Z]{3}$", r"^\d{4}[A-Z]$"]},
}
# California never issues I, O or Q in a CF number.
NO_LETTERS = {"CF": "IOQ"}


# (name, hex, is_light) - is_light drives which hull color the preview sits on.
COLORS = [("White","#ffffff",1),("Black","#111111",0),("Navy","#12243f",0),
          ("Royal Blue","#1b4fa8",0),("Light Blue","#5fc4f5",1),("Teal","#0d7f7f",0),
          ("Forest","#15512c",0),("Lime","#7ac70c",1),("Yellow","#f5d000",1),
          ("Orange","#f07c00",1),("Red","#c8102e",0),("Burgundy","#6d1026",0),
          ("Purple","#5b2a86",0),("Pink","#e8669e",1),("Brown","#5a3a22",0),
          ("Tan","#c9a979",1),("Gray","#8b949c",1),("Silver Metallic","#c6ccd1",1),
          ("Gold Metallic","#c9a227",1),("Chrome","#dfe6ea",1),
          ("Reflective White","#f2f4f5",1),("Reflective Red","#d02b3f",0)]
# What the order form offers. Two colors cover the overwhelming majority of
# boat lettering, they are always in stock, and between them they satisfy the
# contrast rule against any hull. Everything else in COLORS is quoted by email.
ORDER_COLORS = ["White", "Black", "Red", "Navy", "Royal Blue", "Forest",
                "Yellow", "Silver Metallic"]

# PAA harvested live from Google on 2026-10-22. These are the questions the
# answer engines are already answering for someone else.
FAQ_HOME = [
    ("How much do boat registration numbers cost?",
     "Ours are $%d a pair with free shipping, proofed within 12 hours. "
     "Web prices for a pair run about $%d to $%d across the market. Cheap sets "
     "are usually calendared craft vinyl, cut as loose characters you space "
     "yourself." % (PRICE["numbers"], PRICE["market_low"], PRICE["market_high"])),
    ("Do boat registration numbers have to be a certain color?",
     "Not a specific color - but federal rule 33 CFR 173.27 requires the characters to "
     "contrast with the background and be distinctly visible and legible. White numbers on "
     "a white hull fail. Dark hull, light numbers; light hull, dark numbers."),
    ("How tall do boat registration numbers have to be?",
     "Not less than 3 inches in height, in plain vertical block characters. That is the "
     "federal minimum and it applies in every state. Taller is always legal."),
    ("Where do the numbers go on the boat?",
     "On each side of the forward half of the vessel, reading left to right, so they are "
     "visible from the water. The validation decal placement varies by state - usually "
     "within a few inches of the number."),
    ("Where can I get boat lettering made?",
     "Here. You pick the characters, font and color, we cut them from marine vinyl, "
     "pre-space them on one sheet with application tape, and email you a proof. "
     "We cut registration numbers, boat names and custom lettering - not printed "
     "graphics or logo artwork."),
    ("What kind of vinyl is best for boat lettering?",
     "Cast vinyl for anything that lives outside - it conforms to curves and holds color "
     "longer outdoors than calendared. High-tack is mandatory on plastic: kayaks, "
     "PWC hulls and pontoon rails. "
     "Calendared vinyl is cheaper and shorter-lived."),
    ("What is the difference between vinyl stickers and vinyl decals?",
     "A sticker is printed on a vinyl square and you see the background. A decal is cut "
     "from colored vinyl, so only the letter shape sticks to the hull and there is no "
     "visible edge or square. Everything we make is cut vinyl."),
    ("Can I apply these myself?",
     "Yes - they arrive as one pre-spaced sheet under application tape, so the spacing is "
     "already right. Clean the hull, tape the sheet in place, wet it, squeegee, peel the "
     "tape. The wet method lets you slide it straight before it grabs, so take the "
     "twenty minutes and it goes on in one pass."),
]

# Postal abbreviations for the SHIPPING address - deliberately separate from
# STATES[*]["ab"], which holds the VESSEL REGISTRATION prefix. They are not the
# same alphabet: California registers boats as CF, Michigan MC, Washington WN,
# Wisconsin WS. Those belong on a hull, never on a parcel, and the shipping
# dropdown was built from the wrong list until 2026-11-11.
#
# All 50 plus DC, because the page promises free shipping to all 50 states and
# a customer who cannot find their own state simply leaves.
SHIP_STATES = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"),
    ("DE", "Delaware"), ("DC", "District of Columbia"), ("FL", "Florida"),
    ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"), ("IL", "Illinois"),
    ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"), ("KY", "Kentucky"),
    ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"),
    ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"),
    ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"),
    ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
    ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"),
    ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"), ("SC", "South Carolina"), ("SD", "South Dakota"),
    ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
    ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"),
]
