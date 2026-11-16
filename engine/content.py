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
    # REAL NAP, PUBLISHED - Aaron's call 2026-11-15, reversing his own
    # 2026-10-30 call that took it off the site. The reasoning for taking it
    # down (the shop runs out of a private home) has not changed; he has
    # decided the local-pack and E-E-A-T upside is worth it. A real shop, a
    # real address and a real phone is the one thing alphabetsigns, signs.com
    # and vinyldisorder cannot answer.
    #
    # Written ONCE, here. Never typed into a template, and never retyped into
    # a citation by hand from a page: NAP consistency character-for-character
    # is the whole game in local ranking, and the live risk is now a typo
    # rather than an omission. The gate pins all four of these strings.
    #
    # Still off the site, deliberately, and these are separate decisions:
    #   coordinates   no rooftop pin. Once the GBP is claimed Google's own
    #                 pin is authoritative and a lat/lng here is only a hint.
    #   Maps links    the address in text does the work; an iframe is
    #                 third-party JS on the contact page.
    #   the owner     name stays schema-only (Article author), his
    #                 photograph and the About page stay gone.
    "phone_display": "(319) 239-3793",
    "phone_tel": "+13192393793",
    "street": "475 River Forest Road",
    "city": "Evansdale",
    "region": "IA",
    "region_name": "Iowa",
    "postal": "50707",
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

# ------------------------------------------------------------------ author
# Who wrote the guides, for the Article schema.
#
# This is the first time Ryan's name appears anywhere on the public site -
# until now he existed only in code comments. Aaron's call, 2026-11-14.
#
# An author is an E-E-A-T signal and Google weights a real, attributable
# person over an organisation. The guides are worth attributing: they are
# written from what actually happens on the cutter, which is the thing a
# content farm cannot copy.
#
# NO STREET ADDRESS, NO PHONE, NO EMAIL on this node - a name and a job are
# business facts, the rest is personal information and the same 2026-10-30
# rule applies to it here as everywhere else on this site.
#
# Schema only: there is no visible byline on the guides. Worth knowing that
# Google has said it cross-checks schema authorship against what a reader can
# see, so this is a weaker signal than a byline would be. Aaron's call.
AUTHOR = {
    "name": "Ryan Phillips",
    "job": "Owner and cutter",
}

# When the guides were published. Read off git history (every guide page's
# first commit is 2026-10-22), NOT set to the build date.
#
# A REAL BUG this replaces: datePublished was TODAY, so every guide claimed to
# have been published on the morning of whatever day the site was last built.
# Rebuilt daily, that is eight pages insisting they are brand new for ever -
# which is a lie Google can check against its own crawl history, and it throws
# away the age the pages have actually earned.
GUIDES_PUBLISHED = "2026-10-22"

# ------------------------------------------------------------- AI crawlers
# Every answer engine that publishes a user-agent, named explicitly in
# robots.txt. The list is long on purpose; see the comment where it is
# written out in engine/build.py.
AI_CRAWLERS = [
    # OpenAI: training, live-fetch-on-behalf-of-a-user, and search index
    "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    # Anthropic. Claude-Web and anthropic-ai are retired names kept because
    # a stale crawler config somewhere may still send them.
    "ClaudeBot", "Claude-SearchBot", "Claude-Web", "anthropic-ai",
    # Perplexity: index, and fetch-for-this-answer
    "PerplexityBot", "Perplexity-User",
    # Google's AI surfaces are opt-out via these, NOT via Googlebot
    "Google-Extended", "GoogleOther",
    "Applebot-Extended",
    "meta-externalagent", "FacebookBot",
    "Amazonbot", "cohere-ai", "MistralAI-User", "Diffbot",
    # Common Crawl feeds a lot of training sets and some retrieval
    "CCBot",
    # ByteDance. Noisy, but it feeds Doubao's answers.
    "Bytespider",
    # Not an AI engine; here so the one explicit list covers search too.
    "Bingbot",
]

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
    # The title said "Rules" while this entry's own `kw` said "requirements".
    # Measured 2026-11-15: "boat registration number requirements" is 140/mo
    # at $1.74, and "boat registration number rules" returns NO measurable
    # volume at all. The slug stays as it is - a keyword in a URL is worth
    # very little, and a redirect costs more than it would buy.
    dict(slug="boat-registration-number-rules", nav="The requirements",
         title="Boat Registration Number Requirements, Plainly Stated",
         kw="boat registration number requirements", vol=140,
         desc="The federal rule for boat registration numbers - 3-inch block characters, contrasting color, correct spacing, forward half of each side - in plain English."),
    dict(slug="where-to-put-boat-registration-numbers", nav="Where they go",
         title="Where Do Boat Registration Numbers Go?",
         kw="where to place boat registration numbers", vol=430,
         desc="Boat registration numbers go on the forward half of both sides, reading left to right. Exactly how high, how far forward, and where the validation decal sits."),
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
         desc="Cast vs calendared vinyl for boats, when high-tack film is mandatory on bare aluminium and rotomoulded plastic, and what a film warranty actually covers."),
    dict(slug="documented-vessel-name-and-hailing-port", nav="Documented vessels",
         title="Documented Vessel Name &amp; Hailing Port Requirements",
         kw="documented vessel lettering", vol=10,
         desc="USCG documented vessels carry the name and hailing port in 4-inch characters, and do not display state registration numbers. Here is the layout."),
    dict(slug="boat-registration-number-cost", nav="What it costs",
         title="What Boat Registration Numbers Cost in 2026",
         kw="boat registration numbers cost", vol=30,
         desc="Boat registration number decals run $10-25 a pair online. What drives the price, what the cheap sets leave out, and what we charge."),
    # The biggest informational term in this cluster, measured 2026-11-15, and
    # nothing on the site answered it: the guide above is about what the
    # DECALS cost, while this question is about what the STATE charges. The
    # answer is `state_fees.py`, which is ours and verified, so this page is
    # the one piece of national content here that a competitor cannot copy
    # without doing the same reading.
    dict(slug="how-much-does-it-cost-to-register-a-boat", nav="State fees",
         title="How Much Does It Cost to Register a Boat?",
         kw="how much does it cost to register a boat", vol=320,
         desc="What each state charges to register a boat, taken from the state's own fee page, with the date we last checked it - plus what else lands on the bill."),
]

# ------------------------------------------------------------------ states
# fleet = registered vessels. vol = "{state} boat registration numbers".
# vern = local vernacular that outranks the generic phrasing.
# Every `fmt`, `decal` and `note` below was read off the page in `rules_src` on
# the date in RULES_VERIFIED - the state's own site, never a competitor and
# never a boater-education site that is not the state's own publication.
# Same hard rule as engine/state_fees.py: if a state does not put it in words,
# we say that instead of inferring the number. Florida, New York and Indiana
# therefore have no `fmt` - their own pages do not publish a letter pattern,
# and build.py simply omits that line rather than guessing one.
#
# `fmt`   the format line, as the state writes it
# `decal` where the validation decal goes - the single most-asked question on
#         these pages, and the one the ranking competitor answers nowhere
# rules_src / rules_src_name  the page it came from, rendered as a link under
#         the decal section. verify.py fails the build on a decal without one.
RULES_VERIFIED = "2026-11-16"

STATES = [
    dict(slug="iowa", name="Iowa", ab="IA", vol=20,
         agency="Iowa DNR", tier=1, home=True,
         register_at="your county recorder's office (Iowa registers boats through "
                     "the county, not directly through the DNR)",
         fmt="IA 3717 ZW &mdash; the IA prefix, four digits, then two letters",
         decal="Iowa is specific about this: the validation decal goes on each side "
               "<strong>toward the stern of the registration number, 4 inches from it "
               "and in line with it</strong>. Not above, not below, not touching.",
         rules_src="https://www.iowadnr.gov/things-do/boating/boating-registration",
         rules_src_name="Iowa DNR, Boat Registration and Titling",
         note="This is our home state &mdash; the shop is in Evansdale, in Black Hawk "
              "County. Iowa also says plainly that <strong>no other numbers may be "
              "displayed on either side of the bow</strong>, so strip any old set off "
              "before the new one goes on."),
    dict(slug="florida", name="Florida", ab="FL", vol=140,
         agency="Florida Department of Highway Safety and Motor Vehicles", tier=1,
         decal="Florida is the odd one out, and it catches people: the registration "
               "decal goes on the <strong>port (left) side only</strong>, immediately "
               "before or after the number &mdash; not one on each side. FLHSMV also "
               "requires that decals from expired registrations be removed.",
         rules_src="https://www.flhsmv.gov/motor-vehicles-tags-titles/vessels/numbering-and-decals/",
         rules_src_name="FLHSMV, Numbering and Decals",
         note="FLHSMV's numbering page gives the display rule &mdash; painted or "
              "permanently attached to both sides of the bow, block letters at least "
              "three inches high, reading left to right, contrasting, maintained in "
              "readable condition &mdash; but it does not publish a letter-and-digit "
              "pattern, so we do not print one. Copy the line off your card."),
    dict(slug="michigan", name="Michigan", ab="MC", vol=140,
         agency="Michigan Secretary of State", tier=1,
         fmt="MC 0000 AA &mdash; the MC prefix, four numerals, then two capital "
             "letters. Michigan's rule bars <strong>I, O and Q</strong> from the "
             "suffix because they read as numerals, and asks for spaces or hyphens "
             "<strong>as wide as the letter M</strong> between the groups",
         decal="Michigan writes this one to the inch. The validation decal is "
               "<strong>about 3 inches square</strong> and goes <strong>3 inches "
               "beyond the last letter of the number, on the same strake or level as "
               "the number</strong>, on each side of the forward half, as high above "
               "the water line as practical.",
         rules_src="https://ars.apps.lara.state.mi.us/AdminCode/DownloadAdminCodeFile?FileName=1190_2013-027NR_AdminCode.pdf",
         rules_src_name="Michigan DNR rule R 281.1203&ndash;1208, Numbering of Vessels and Motorboats"),
    dict(slug="new-york", name="New York", ab="NY", vol=20,
         agency="New York State DMV", tier=1,
         decal="New York measures from the bow rather than from the number. The DMV "
               "says to put the registration stickers <strong>18 inches from the bow "
               "on both sides of the boat</strong> &mdash; which it describes as about "
               "where they land when a boat also carries numbers on the hull. On a "
               "Coast Guard documented boat, which gets stickers and no number, they "
               "go where the numbers would normally be.",
         rules_src="https://dmv.ny.gov/registration/register-a-boat",
         rules_src_name="New York DMV, Register a Boat"),
    dict(slug="california", name="California", ab="CF", vol=630,
         agency="California DMV", tier=1, vern="CF numbers",
         fmt="CF 1234 AB or CF-1234-AB &mdash; the CF prefix, four digits, two "
             "letters, with the space or hyphen the same size as a letter other than "
             "I or a number other than 1. The DMV asks for plain vertical block "
             "characters <strong>more than</strong> three inches high",
         decal="The sticker goes on <strong>both sides, three inches from the "
               "number</strong>. The DMV describes it as the immediate left of the CF "
               "number on the starboard side and the immediate right on the port side "
               "&mdash; which is the stern side on each. Nothing else may sit near it "
               "except the CF number and, on fresh water, the Mussel Fee sticker.",
         rules_src="https://www.dmv.ca.gov/portal/vehicle-registration/new-registration/register-your-boat-vessel/",
         rules_src_name="California DMV, Register your boat/vessel",
         note="California is the one state that does not use its postal abbreviation. "
              "California boat numbers start with <strong>CF</strong>, and locals call them "
              "CF numbers - which is what people actually search for."),
    dict(slug="south-carolina", name="South Carolina", ab="SC", vol=30,
         agency="South Carolina Department of Natural Resources", tier=1,
         fmt="Block design not less than three inches high, in a color that clearly "
             "contrasts with the hull, with the letter groups separated from the "
             "numerals by hyphens or equivalent spaces, read left to right "
             "<strong>as it appears on the certificate of number</strong>",
         decal="South Carolina fixes both the side and the order: the year decals are "
               "attached to each side of the bow <strong>immediately following the "
               "number, within six inches</strong>.",
         rules_src="https://www.dnr.sc.gov/boating/Titling_and_Registration/docs/WatercraftOutboardMotorApplication.pdf",
         rules_src_name="SCDNR Watercraft/Outboard Motor Application, Display of Number and Decals"),
    dict(slug="wisconsin", name="Wisconsin", ab="WS", vol=70,
         agency="Wisconsin DNR", tier=1,
         fmt="At least 3-inch block letters, contrasting with the boat, read left to "
             "right, with the letters separated from the numbers by a space "
             "<strong>at least two inches wide</strong>",
         decal="Wisconsin requires the number and the expiration decals to be "
               "displayed on the side of the boat, and shows the decal beside the "
               "number in a diagram &mdash; but it does not state an offset in words, "
               "so we will not put inches in its mouth. What it does say in words is "
               "unusual and worth repeating: <strong>two-toned and camouflage numbers "
               "are not legal and should not be used</strong>. A number that "
               "disappears into a camo wrap fails even at the right height.",
         rules_src="https://dnr.wisconsin.gov/permits/registrations/boat/BeforeYouOperate.html",
         rules_src_name="Wisconsin DNR, What you should know before you operate your boat"),
    dict(slug="minnesota", name="Minnesota", ab="MN", vol=30,
         agency="Minnesota DNR", tier=1,
         fmt="At least 3 inches high, block character, with a <strong>3-inch "
             "space</strong> between the MN and the numbers and another between the "
             "numbers and the letters &mdash; the widest spacing rule of any state "
             "here",
         decal="Minnesota's clearance rule is the strictest we have found. The current "
               "decal is <strong>always placed closer to the stern, within 4 inches of "
               "the license number</strong>, and <strong>no other number, letter or "
               "design may appear within 24 inches</strong> of the number or the "
               "decal. A canoe, kayak, paddleboard, rowing shell, paddle boat, "
               "sailboard or sailboat with no motor needs <strong>only the "
               "decal</strong> &mdash; no 3-inch numbers at all.",
         rules_src="https://files.dnr.state.mn.us/rlp/regulations/boatwater/boatingguide.pdf",
         rules_src_name="Minnesota DNR 2026 Boating Guide"),
    dict(slug="texas", name="Texas", ab="TX", vol=110,
         agency="Texas Parks and Wildlife Department", tier=1,
         fmt="TX 0001 GG or TX-0001-GG &mdash; the numerals separated from the prefix "
             "and the suffix by hyphens or equivalent spaces, in block characters of "
             "good proportion not less than three inches in height",
         decal="Texas measures off the number and runs aft: the validation decal is "
               "affixed <strong>in line with, and three inches towards the rear of the "
               "boat from, the TX number</strong>. A Coast Guard documented vessel may "
               "display only the decal, on both sides of the bow.",
         rules_src="https://tpwd.texas.gov/regulations/outdoor-annual/boating/title-registration-id-requirements/placement-of-tx-number-and-decal-on-vessels",
         rules_src_name="TPWD Outdoor Annual, Placement of TX Number and Decal on Vessels"),
    dict(slug="pennsylvania", name="Pennsylvania", ab="PA", vol=10,
         agency="Pennsylvania Fish and Boat Commission", tier=1,
         fmt="Bold block letters and numbers at least 3 inches high, contrasting with "
             "the background, read left to right, separated by a dash or space "
             "<strong>equal to the width of any letter or number except I or 1</strong>",
         decal="Pennsylvania lets you choose the side of the number but pins the "
               "height: the validation decal goes <strong>within 6 inches of the "
               "number, before or following it, on the same level</strong>.",
         rules_src="https://www.pa.gov/agencies/fishandboat/boating/register-title-a-boat",
         rules_src_name="Pennsylvania Fish and Boat Commission, Register/Title a Boat",
         note="The Commission says it plainly: <strong>it does not supply the actual "
              "letters and numbers</strong>, and the owner is responsible for buying "
              "and displaying them. That is the job this shop exists to do."),
    dict(slug="north-carolina", name="North Carolina", ab="NC", vol=90,
         agency="NC Wildlife Resources Commission", tier=1,
         fmt="At least three-inch block lettering, <strong>any solid color</strong> "
             "so long as it contrasts with the bow, letters separated from the "
             "numerals by hyphens or equivalent spaces, read left to right as it "
             "appears on the registration card",
         decal="The decals go on the <strong>starboard and port side bow, within 6 "
               "inches of the number</strong>. NCWRC also publishes the application "
               "conditions most states leave out: remove the old validation decals "
               "first, and apply <strong>at a temperature above 40&nbsp;&deg;F</strong> "
               "to a surface that is clean, dry and free of dust, grease or wax.",
         rules_src="https://www.ncwildlife.gov/affix-vessel-numbers-decalpdf/download",
         rules_src_name="NCWRC, How to Affix Vessel Registration Numbers and the Decals (rev. 8/2023)"),
    dict(slug="georgia", name="Georgia", ab="GA", vol=110,
         agency="Georgia DNR Wildlife Resources Division", tier=1,
         fmt="GA 3717 ZW or GA-3717-ZW &mdash; a space or hyphen between the letters "
             "and the numbers, at least three-inch-high block letters in a color that "
             "contrasts with the background, read left to right on both sides of the bow",
         decal="Georgia runs the opposite way from Texas. The decals are displayed on "
               "each side of the bow <strong>before the prefix letters of the "
               "registration number</strong> &mdash; forward of it, not aft. And no "
               "other numbers may be displayed on either side of the bow.",
         rules_src="https://gadnrle.org/register-boat-pwc",
         rules_src_name="Georgia DNR Law Enforcement, Registering Your Boat or Personal Water Craft"),
    dict(slug="virginia", name="Virginia", ab="VA", vol=20,
         agency="Virginia Department of Wildlife Resources", tier=1,
         fmt="Displayed exactly as it appears on the registration, in block letters at "
             "least 3 inches high, contrasting in color with the hull, read left to "
             "right, with a space or hyphen separating <strong>both</strong> the VA and "
             "the letter suffix from the numerals",
         decal="The decal goes <strong>within 6 inches of the registration "
               "number</strong> on each side of the watercraft, and Virginia is firm "
               "about the rest: <strong>only the current decal may be visible, and "
               "expired decals must be removed</strong>.",
         rules_src="https://dwr.virginia.gov/boating/boaters-guide/watercraft-registration-and-titling-requirements/",
         rules_src_name="Virginia DWR, Watercraft Registration, Titling and Sales Tax Requirements",
         note="Virginia also says the number itself <strong>should never be "
              "removed</strong> from the boat unless DWR assigns a new one &mdash; the "
              "number stays with the hull even though the registration expires every "
              "three years. Renew the decal; leave the lettering alone."),
    dict(slug="ohio", name="Ohio", ab="OH", vol=50,
         agency="Ohio DNR Division of Parks and Watercraft", tier=1,
         fmt="OH, then four numbers, then two letters, with the four numbers in the "
             "middle separated from the letters at either end by a hyphen or "
             "equivalent space; block characters of good proportion, minimum 3 inches, "
             "in <strong>one</strong> color that contrasts with the boat",
         decal="Ohio's offset is six inches, not three: the decals go <strong>six "
               "inches from the numbers, toward the back of the boat</strong>, one on "
               "each side, and the two are identical. The colors rotate through four, "
               "so an expired decal reads from a distance.",
         rules_src="https://ohiodnr.gov/rules-and-regulations/rules-and-regulations-by-division/state-parks-and-watercraft/boating-rules/02-registration-decals-ohio-boat",
         rules_src_name="ODNR, Displaying Your Numbers &amp; Decals &mdash; Ohio Boats",
         note="Two Ohio quirks worth knowing before you order. The <strong>OH number "
              "stays with the boat for its lifetime in Ohio</strong> regardless of how "
              "many times it changes hands &mdash; so a used boat usually keeps the "
              "number already on the card. And the <strong>Alternative Registration "
              "for hand-powered vessels displays a single decal and no OH number at "
              "all</strong>, which means a kayak may need nothing cut."),
    dict(slug="illinois", name="Illinois", ab="IL", vol=30,
         agency="Illinois DNR", tier=1,
         fmt="IL 1234 AB &mdash; two capital letters, a space, four digits, a space, "
             "two capital letters, all on one line, in at least three-inch-high block "
             "letters whose color contrasts sharply with its background",
         decal="Illinois puts it in one line: the decals are placed on both sides of "
               "the bow <strong>after a space at the end of the number</strong>.",
         rules_src="https://dnr.illinois.gov/content/dam/soi/en/web/dnr/boating/documents/boatdigest.pdf",
         rules_src_name="Handbook of Illinois Boating Laws and Responsibilities (IDNR)"),
    dict(slug="missouri", name="Missouri", ab="MO", vol=70,
         agency="Missouri Department of Revenue", tier=1,
         fmt="MO 1234 AB &mdash; two alpha characters, four numerals, then two more, "
             "with the prefix and suffix <strong>separated from the numbers by 2-inch "
             "spaces</strong> (a hyphen may be used within that 2-inch space). Block "
             "characters of good proportion, not less than 3 inches, dark on a light "
             "hull and light on a dark one",
         decal="Missouri is the one state on this list that does not put the decal "
               "beside the number: the vessel decals are <strong>placed below each MO "
               "number</strong>. An outboard motor decal goes on a solid part of the "
               "metal housing instead, and stays valid until the motor changes hands.",
         rules_src="https://dor.mo.gov/motor-vehicle/watercraft/additional-information.html",
         rules_src_name="Missouri DOR, Boat/Vessel Titling and Registration",
         note="Registration is through the <strong>Department of Revenue</strong>, not "
              "the Highway Patrol &mdash; the Patrol is the water-patrol side. Pay DOR, "
              "then order the lettering."),
    dict(slug="washington", name="Washington", ab="WN", vol=40,
         agency="Washington State Department of Licensing", tier=2,
         fmt="BLOCK style, at least 3 inches high, contrasting with the background, "
             "always read left to right, with the segments separated by a hyphen or "
             "equivalent space. Washington's own example for a tender carries a fourth "
             "group: WN 1234 ZZ 1 or WN-1234-ZZ-1",
         decal="The decals are placed on both sides of the bow, <strong>aft of and "
               "directly in line with the registration number, within 6 inches</strong> "
               "of it.",
         rules_src="https://dol.wa.gov/vehicles-and-boats/boats/register-boat/boat-registration-and-hull-identification-numbers",
         rules_src_name="Washington DOL, Boat registration and hull identification numbers",
         note="Washington registration numbers begin with <strong>WN</strong>, not WA."),
    dict(slug="louisiana", name="Louisiana", ab="LA", vol=70,
         agency="Louisiana Department of Wildlife and Fisheries", tier=2,
         fmt="LA-4002-CS or LA 4002 GS &mdash; a hyphen or space equal to the width of "
             "a number (except 1) or a letter (except I) between the prefix, numerals "
             "and suffix. Plain block design, at least 3 inches high, clearly visible "
             "and legible, and <strong>placed vertically</strong>",
         decal="The decals received from LDWF are attached to each side of the "
               "vessel's bow <strong>within 6 inches of the number, before or after "
               "it</strong>.",
         rules_src="https://www.wlf.louisiana.gov/page/boat-title-and-registration-faqs",
         rules_src_name="LDWF, Boat Title and Registration FAQs",
         note="Louisiana is the only state here that says what to do about outlines, "
              "and it matters if you order a two-color set: <strong>&ldquo;Disregard "
              "border, outline, and shadowing when determining height and color "
              "contrast.&rdquo;</strong> The 3-inch minimum is measured on the letter "
              "itself, not on the outline around it &mdash; so order 3-inch "
              "<em>letters</em>, not a 3-inch outlined block."),
    dict(slug="alabama", name="Alabama", ab="AL", vol=70,
         agency="Alabama Law Enforcement Agency, Marine Patrol", tier=2,
         fmt="Block characters of good proportion, not less than <strong>76 "
             "millimeters (about 2.99 inches)</strong> in height &mdash; Alabama is "
             "the state that writes the minimum in millimeters &mdash; properly spaced "
             "so as to be easily readable, read left to right, in paint or decals that "
             "contrast with the background",
         decal="A current-year registration decal goes on each side of the vessel "
               "<strong>within six inches (152.4 mm) of the number, either at the "
               "beginning or the end</strong> of it. Alabama adds a condition most "
               "states only imply: the decal is not properly placed unless it is the "
               "<strong>only</strong> Alabama registration decal on the boat, so every "
               "previous year's has to come off.",
         rules_src="https://www.alea.gov/sites/default/files/Vessel%20Registration%20and%20Operation%20Requirements%202026.pdf",
         rules_src_name="ALEA, Vessel Registration and Operation Requirements, rule 760-X-6-.03",
         note="A caveat we would rather print than bury. These Alabama figures come "
              "from ALEA's own 2026 rulemaking for chapter 760-X-6, which it describes "
              "as importing and comprehensively updating the existing DCNR chapter "
              "220-6. The document we read is the <strong>notice of intended "
              "action</strong>, certified 20 July 2026, with comment closing 4 "
              "September 2026 &mdash; and we could not confirm from ALEA's site that "
              "the chapter has since been formally adopted. The millimetre figures are "
              "ALEA's stated rule; if you are measuring to the edge of six inches, ring "
              "Marine Patrol."),
    dict(slug="tennessee", name="Tennessee", ab="TN", vol=20,
         agency="Tennessee Wildlife Resources Agency", tier=2,
         fmt="TN 3717 ZW or TN-3717-ZW &mdash; letters separated from the numbers by a "
             "space or hyphen, in at least three-inch-high plain vertical BLOCK "
             "letters whose color contrasts with the background, read left to right "
             "on both sides of the bow",
         decal="Tennessee is the relaxed one: the decals <strong>may be placed to the "
               "left or right of the registration number</strong> on both sides of the "
               "bow. A Coast Guard documented vessel is handled completely differently "
               "&mdash; its validation decals go on <strong>both sides of the vessel "
               "on the windows closest to the main operator station</strong>, or, on a "
               "sailboat, both sides of the bottom of the main mast.",
         rules_src="https://www.tn.gov/content/dam/tn/twra/documents/boating/TWRA-TN-Boating-Handbook.pdf",
         rules_src_name="2025 Tennessee Boating Laws and Responsibilities (TWRA)"),
    dict(slug="mississippi", name="Mississippi", ab="MI", vol=70,
         agency="Mississippi Department of Wildlife, Fisheries and Parks", tier=3,
         fmt="MI, then up to four digits, then up to two letters &mdash; &ldquo;each "
             "part shall be separated by hyphens or equivalent spaces when placed on "
             "the boat.&rdquo; Block characters of good proportion, not less than 3 "
             "inches, read left to right, dark on a light hull and light on a dark one",
         decal="MDWFP puts it in one line: &ldquo;the decals should be displayed "
               "<strong>within six (6&Prime;) inches of the numbers</strong>.&rdquo; "
               "Each side of the forward half, in a position that gives clear "
               "legibility, and no other numbers on the bow.",
         rules_src="https://www.mdwfp.com/fishing-boating/boat-registration-renewal",
         rules_src_name="MDWFP, Boat Registration &amp; Renewal",
         note="This is the prefix that catches people more than any other. "
              "<strong>Mississippi boat numbers start with MI</strong> &mdash; and "
              "<strong>Michigan&rsquo;s start with MC</strong>. The two are swapped "
              "relative to the postal abbreviations everybody knows, because the "
              "Coast Guard set the vessel prefixes in 1958, five years before the "
              "Post Office picked its own codes. Our order form checks it for you."),
    dict(slug="maine", name="Maine", ab="ME", vol=50,
         agency="Maine Department of Inland Fisheries and Wildlife", tier=3,
         fmt="ME-123-A &mdash; the statute&rsquo;s own example. Three parts, with the "
             "ME separated from the numerals by a hyphen or a space <strong>equal to "
             "the width of a letter other than &ldquo;I&rdquo;</strong>, and the "
             "suffix separated the same way. Vertical block capital letters and "
             "Arabic numerals, not less than 3 inches, of good proportion, kept "
             "legible at all times",
         decal="Maine measures from the end of the number: the validation sticker is "
               "displayed <strong>approximately 3 inches behind the last letter of "
               "the identification number, and on a level with it</strong>, on both "
               "sides of the bow.",
         rules_src="https://legislature.maine.gov/statutes/12/title12sec13056.pdf",
         rules_src_name="Maine Revised Statutes Title 12 §13056",
         note="Two Maine-only things. The registration is priced off the "
              "<strong>engine</strong> rather than the boat, and it is cheaper if "
              "you operate only on tidal water. And the validation stickers are "
              "<strong>nontransferable</strong> &mdash; they do not go with a sold "
              "boat, so a used hull arrives needing its own."),
    dict(slug="arkansas", name="Arkansas", ab="AR", vol=30,
         agency="Arkansas Department of Finance and Administration", tier=3,
         fmt="AR 3717 ZW or AR-3717-ZW &mdash; and Arkansas also issues the three-"
             "digit form, AR 123 ABC. At least 3 inches high, bold BLOCK letters, "
             "contrasting with the background, read left to right on both sides, "
             "with the letters separated from the numbers by a space or hyphen",
         decal="The decals go on each side <strong>toward the stern of the "
               "registration number, three inches from it and in line with "
               "it</strong>. No other numbers on either side of the bow.",
         rules_src="https://www.dfa.arkansas.gov/office/motor-vehicle/motor-boat-registration/",
         rules_src_name="Arkansas DFA, Motor Boat Registration",
         note="You register an Arkansas boat through the <strong>Department of "
              "Finance and Administration</strong> &mdash; the car-tag office &mdash; "
              "not through Game and Fish. Game and Fish writes the boating handbook "
              "and works the water; DFA takes the money and issues the number."),
    dict(slug="massachusetts", name="Massachusetts", ab="MS", vol=20,
         agency="Massachusetts Environmental Police", tier=3,
         fmt="MS followed by no more than four numbers and two capital letters, with "
             "a <strong>two-inch space or hyphen</strong> separating the letters from "
             "the numbers. Block letters not less than three inches high, read left "
             "to right, contrasting with the hull, on each side of the forward half",
         decal="Massachusetts is the second port-side state. The decal is placed "
               "<strong>in line with and three inches to the stern of the number, on "
               "the port side of the boat</strong> &mdash; not one on each side.",
         rules_src="https://www.mass.gov/info-details/boat-registration-faqs",
         rules_src_name="Massachusetts Environmental Police, Boat Registration FAQs",
         note="Two things that are true almost nowhere else. "
              "<strong>Massachusetts numbers start with MS</strong>, which is "
              "Mississippi&rsquo;s postal code &mdash; and Mississippi&rsquo;s boats "
              "start with MI. And the Massachusetts number is issued "
              "<strong>to the owner, not to the vessel</strong>: it can move to a "
              "different boat you own, but it can never transfer to a new owner. If "
              "you are selling, the number comes off."),
    dict(slug="new-jersey", name="New Jersey", ab="NJ", vol=30,
         agency="New Jersey Motor Vehicle Commission", tier=3,
         fmt="NJ-1234-AA or NJ 9999 ZZ &mdash; the code&rsquo;s own examples. Three "
             "parts: NJ, not more than four Arabic numerals, not more than two "
             "letters, separated by a hyphen or an equivalent space. <strong>I, O and "
             "Q may not be used in the suffix</strong> because they read as numerals. "
             "Block characters of good proportion, not less than three inches, "
             "contrasting, on each side of the bow",
         decal="New Jersey states it flatly: <strong>the validation decal shall be "
               "placed on each side of the vessel, three inches aft of the "
               "registration number</strong>. Expired decals must not be visible &mdash; "
               "and when the vessel is sold, removing them is the "
               "<strong>seller&rsquo;s</strong> job.",
         rules_src="https://www.nj.gov/njsp/marine-services/pdf/Title_13_82_20220127.pdf",
         rules_src_name="New Jersey Administrative Code Title 13:82-8.2 and 8.3",
         note="The display rules above are the administrative code; the three-inch "
              "decal offset is stated in the State Police&rsquo;s own 2024 Boating "
              "Safety Manual, which is the publication an officer on Barnegat Bay is "
              "working from."),
    dict(slug="oregon", name="Oregon", ab="OR", vol=20,
         agency="Oregon State Marine Board", tier=3,
         fmt="Oregon publishes one spacing rule in words and the rest in a diagram. "
             "The rule it writes out is for the long numbers: <strong>if your OR "
             "number has three letters, group them next to each other</strong> "
             "(OAR 250-010-0040)",
         decal="Oregon shows the decal position in a placement diagram rather than "
               "describing it in words, so we will not put inches in its mouth. What "
               "the Marine Board does state in words is the penalty &mdash; failing "
               "to display the numbers and a current decal properly is a "
               "<strong>Class D violation, $110</strong> &mdash; and the rule for "
               "Coast Guard documented boats, which register in Oregon too and "
               "<strong>put the expiration stickers on the port and starboard sides "
               "at the stern</strong>.",
         rules_src="https://www.oregon.gov/osmb/title-registration/pages/or-numbers.aspx",
         rules_src_name="Oregon State Marine Board, OR Number Placement and Spacing",
         note="One Oregon rule catches people who leave a boat in the water: a boat "
              "must be currently registered <strong>whenever it is on the water, "
              "even when docked or moored</strong>. Not just under way."),
    dict(slug="nebraska", name="Nebraska", ab="NB", vol=20,
         agency="county treasurer, for Nebraska Game and Parks", tier=3,
         fmt="Nebraska writes the whole line out in order, and the sticker is part of "
             "it: <strong>validation sticker first, then NB, then a 2-inch space, "
             "then four digits, then a 2-inch space, then two or three capital block "
             "letters</strong>. Block figures at least 3 inches high, contrasting, "
             "and <strong>visible for 100 feet</strong> &mdash; Nebraska is the only "
             "state here that states the distance it has to read from",
         decal="Nebraska puts the validation sticker at the <strong>front of the "
               "number, before the NB</strong>, on each side of the forward half. "
               "Nothing but the registration letters, numbers and validation "
               "stickers may appear on either forward side.",
         rules_src="https://govdocs.nebraska.gov/epubs/G1000/H006-2026.pdf",
         rules_src_name="Nebraska Game and Parks 2026 Boating Guide",
         note="Two Nebraska-only things. <strong>Nebraska boat numbers start with "
              "NB, not NE</strong> &mdash; the Coast Guard set the vessel prefixes "
              "in 1958, before the Post Office picked its codes, and the two never "
              "got reconciled. And <strong>all registrations are "
              "nontransferable</strong>: a boat you just bought may be wearing a "
              "current sticker, and you still have 30 days to register it in your "
              "own name."),
    dict(slug="idaho", name="Idaho", ab="ID", vol=20,
         agency="Idaho Department of Parks and Recreation", tier=3,
         fmt="Plain vertical block characters not less than three inches high, "
             "contrasting with the background, read left to right, with spaces or "
             "hyphens <strong>equal to the width of a letter other than "
             "&ldquo;I&rdquo; or a number other than &ldquo;1&rdquo;</strong> "
             "between the groups, and set <strong>as high above the waterline as "
             "practicable without decreasing the visibility of the number</strong>",
         decal="Idaho sizes the sticker as well as placing it: approximately "
               "<strong>three inches square</strong>, displayed <strong>within six "
               "inches of and directly in line with the vessel number</strong>, on "
               "each side of the bow. Only the number and the validation stickers may "
               "appear there.",
         rules_src="https://legislature.idaho.gov/statutesrules/idstat/title67/t67ch70/sect67-7008/",
         rules_src_name="Idaho Code §67-7008",
         note="Idaho rotates the sticker colour by expiry year &mdash; "
              "<strong>green, red, blue, international orange</strong>, and round "
              "again &mdash; so an officer reads the year off the colour at a "
              "distance before ever reading the date."),
    dict(slug="utah", name="Utah", ab="UT", vol=20,
         agency="Utah Division of Motor Vehicles", tier=3,
         fmt="Plain vertical block characters not less than three inches in height, "
             "contrasting and distinctly legible, read left to right, with spaces or "
             "hyphens <strong>equal to the width of a letter</strong> between the "
             "letter and numeral groups, painted or permanently attached to each "
             "side of the forward half",
         decal="Utah is the two-decal state, and the order matters. The "
               "<strong>yearly registration decal goes three inches aft of the "
               "number</strong> on each side &mdash; and the <strong>month-of-"
               "expiration decal goes immediately aft of the yearly decal</strong>. "
               "Only current-year decals may be displayed. On a documented vessel "
               "the yearly decal goes on each side of the forward half instead.",
         rules_src="https://recreation.utah.gov/wp-content/uploads/Boating-Code-and-Rules-2022-Online.pdf",
         rules_src_name="Utah Code §73-18-7 and Utah Administrative Code R651-212",
         note="A boat carrying a valid U.S. Coast Guard marine document is "
              "<strong>exempt from the Utah number display requirement</strong> "
              "entirely &mdash; it still registers and still shows decals, but it "
              "does not carry UT numbers on the bow."),
    dict(slug="montana", name="Montana", ab="MT", vol=20,
         agency="county treasurer, for Montana Fish, Wildlife and Parks", tier=3,
         fmt="MT 234 ABC or MT-234-ABC &mdash; a space or hyphen separating the MT "
             "from the number and letter suffix. Vertical block letters at least 3 "
             "inches high, contrasting with the hull, read left to right, "
             "<strong>as high above the water line as practical and still "
             "visible</strong>, on each outboard side of the forward half",
         decal="Montana is unlike every other state on this site. "
               "<strong>Validation stickers are no longer required</strong>. You get "
               "<strong>one permanent white decal</strong>, and it goes on the "
               "<strong>left or port side only, three inches aft of and directly in "
               "line with the number</strong>. It stays valid until you sell the "
               "boat. No other numbers or letters may be displayed on the bow.",
         rules_src="https://fwp.mt.gov/binaries/content/assets/fwp/fish/regulations/2026-boating-laws-final-for-print.pdf",
         rules_src_name="2026 Montana Boating Laws (FWP)",
         note="Because the decal is permanent and the fee is one-time, a Montana "
              "boat&rsquo;s lettering is the part that ages, not the sticker. If "
              "your numbers have gone chalky or started lifting, replacing them is "
              "the whole job &mdash; there is no annual renewal to do it alongside."),
    dict(slug="colorado", name="Colorado", ab="CL", vol=10,
         agency="Colorado Parks and Wildlife", tier=3,
         fmt="Read left to right in block characters of good proportion, at least 3 "
             "inches tall <strong>not counting any border or trim</strong>, "
             "contrasting with the background, kept clearly visible and legible, "
             "painted or attached to each side of the bow on the forward half. If "
             "the boat has no such sides, a matching spot on both sides of the "
             "foredeck is acceptable",
         decal="Colorado runs forward, not aft: the yearly decals are placed "
               "<strong>to the left of the registration number on both sides of the "
               "boat</strong>. No other number may be carried on the bow &mdash; and "
               "if another state&rsquo;s number is still showing, it has to come off.",
         rules_src="https://cpw.state.co.us/register-boat",
         rules_src_name="Colorado Parks and Wildlife, Register a Boat",
         note="<strong>Colorado boat numbers start with CL, not CO.</strong> The "
              "Coast Guard set the vessel prefixes in 1958, five years before the "
              "Post Office picked its own two-letter codes, and the two were never "
              "reconciled. Also worth knowing: the 3-inch minimum is measured on the "
              "character itself, <em>not counting border or trim</em> &mdash; so an "
              "outlined set has to have 3-inch letters inside the outline."),
    dict(slug="maryland", name="Maryland", ab="MD", vol=10,
         agency="Maryland Department of Natural Resources", tier=3,
         fmt="Plain vertical block characters of good proportion, not less than 3 "
             "inches high, contrasting with the hull, read left to right, "
             "<strong>placed as high above the waterline as practical</strong>, with "
             "the letters separated from the numbers by hyphens or spaces &mdash; "
             "and the number must read exactly as it appears on the Vessel "
             "Registration Card",
         decal="Maryland sizes the decals and then pins them close: the set is "
               "<strong>two 3&Prime; &times; 3&Prime; decals, displayed within 3 "
               "inches of the vessel number</strong>. The same 3-inch rule applies "
               "to a dealer&rsquo;s round temporary decal.",
         rules_src="https://dnr.maryland.gov/Documents/BoatDealersManual.pdf",
         rules_src_name="Maryland DNR Boat Dealer Manual, Appendix D (rev. 3/2026)",
         note="Maryland charges one flat fee for every vessel regardless of length "
              "or horsepower, so unlike most states there is nothing to gain from "
              "where your boat falls in a length band."),
    dict(slug="kentucky", name="Kentucky", ab="KY", vol=10,
         agency="county clerk, for Kentucky Fish and Wildlife", tier=3,
         fmt="KY 1234 A &mdash; the statute&rsquo;s own example. Block letters of "
             "good proportion not less than three inches in height, read left to "
             "right, in a position giving <strong>maximum visibility</strong>, with "
             "spaces <strong>equal to the width of a letter other than "
             "&ldquo;I&rdquo; or a number other than &ldquo;1&rdquo;</strong> "
             "between the groups, dark on a light background or the reverse",
         decal="Kentucky gives both a distance and a direction: the registration "
               "decals go <strong>within six inches behind (aft) and in line with "
               "the registration number</strong>. Each year the old ones come off "
               "and the current ones go on.",
         rules_src="https://apps.legislature.ky.gov/law/statutes/statute.aspx?id=11055",
         rules_src_name="Kentucky Revised Statutes §235.110",
         note="Kentucky registrations all expire on the <strong>same date, 30 "
              "April</strong>, not on the anniversary of the day you registered. "
              "Register a boat in March and the renewal notice follows almost "
              "immediately."),
    dict(slug="kansas", name="Kansas", ab="KA", vol=30,
         agency="Kansas Department of Wildlife and Parks", tier=3,
         decal="Kansas writes the display rule in two places and we can only read "
               "one of them. The statute says the owner shall <strong>paint on or "
               "attach to each side of the bow the identification number</strong> so "
               "that it is <strong>clearly visible</strong>, &ldquo;in such manner "
               "as prescribed by rules and regulations of the secretary&rdquo; "
               "&mdash; and that detail lives in K.A.R. 115-30-1, which KDWP "
               "publishes on a site that refuses every request we make to it. So "
               "take the floor from the federal rule quoted above, which applies in "
               "Kansas as everywhere: 3-inch plain vertical block characters, "
               "contrasting, spaced, reading left to right, on the forward half.",
         rules_src="https://ksrevisor.gov/statutes/chapters/ch32/032_011_0011.html",
         rules_src_name="Kansas Statutes §32-1111",
         note="<strong>Kansas boat numbers start with KA, not KS.</strong> The Coast "
              "Guard set the vessel prefixes in 1958, five years before the Post "
              "Office picked its own two-letter codes. Kansas registrations run "
              "<strong>three years</strong>, and the statute sets a sharp penalty "
              "for letting one lapse: $20 for each 30 days late, up to $60."),
    dict(slug="new-hampshire", name="New Hampshire", ab="NH", vol=10,
         agency="New Hampshire Division of Motor Vehicles", tier=3,
         fmt="The statute is unusually short about it: numbers <strong>not less than "
             "3 inches in height, in block letters of contrasting color</strong>, "
             "displayed on each side of the forward half, <strong>clearly readable "
             "when the vessel is being operated</strong> and maintained in legible "
             "condition. New Hampshire does not specify the spacing, so the federal "
             "rule above governs it",
         decal="From 1 January 2025 a registered New Hampshire boat carries "
               "<strong>two decals on each side of the bow</strong>: the square "
               "registration decal, and a round reflective <strong>boat fee "
               "decal</strong> bought separately each year. No numbers other than "
               "the ones assigned to the vessel may be displayed on either side of "
               "the forward half.",
         rules_src="https://gc.nh.gov/rsa/html/XXII/270-E/270-E-mrg.htm",
         rules_src_name="New Hampshire RSA 270-E:8",
         note="An out-of-state motorboat on New Hampshire public water also needs a "
              "New Hampshire aquatic invasive species decal, and that one goes on "
              "the <strong>port side, within 3 inches of the valid registration "
              "decal</strong>."),
    dict(slug="delaware", name="Delaware", ab="DL", vol=10,
         agency="DNREC Division of Fish and Wildlife", tier=3,
         fmt="Plain vertical block characters of not less than 3 inches in height, "
             "contrasting with the background and distinctly visible and legible, "
             "read left to right, with spaces or hyphens <strong>equal to the width "
             "of a letter other than &ldquo;I&rdquo; or a number other than "
             "&ldquo;1&rdquo;</strong>, painted on or permanently attached to each "
             "side of the forward half",
         decal="Delaware sizes the sticker and then places it: validation stickers "
               "are <strong>approximately 3 inches square</strong> and must be "
               "<strong>displayed within 6 inches of the number</strong>. "
               "<strong>Expired validation decals shall be removed</strong> and only "
               "effective decals displayed. The expiry year is coded by colour "
               "&mdash; blue, international orange, green and red, in rotation.",
         rules_src="https://regulations.delaware.gov/register/january2026/final/29%20DE%20Reg%20617%2001-01-26",
         rules_src_name="Delaware DNREC regulation 3100 Boating, §3.8 and §3.15 (January 2026)",
         note="<strong>Delaware boat numbers start with DL, not DE</strong> &mdash; "
              "another 1958 Coast Guard prefix that never got reconciled with the "
              "postal code. If the hull shape would hide the number, Delaware "
              "expressly allows it on a <strong>backing plate</strong> attached to "
              "the forward half instead."),
    dict(slug="oklahoma", name="Oklahoma", ab="OK", vol=20,
         agency="Service Oklahoma", tier=3,
         decal="Service Oklahoma&rsquo;s current pages do not publish an offset for "
               "the registration decal, and we are not going to take one off an "
               "older guide and present it as the rule. What those pages do say: the "
               "current registration must be carried in the boat while it is in "
               "operation, and the separate <strong>carbon monoxide warning decal "
               "issued under Andy&rsquo;s Law must be placed inside the vessel in "
               "plain view</strong> &mdash; inside, not on the bow. For the number "
               "and decal placement, the federal rule quoted above is the floor "
               "that applies in Oklahoma as everywhere.",
         rules_src="https://oklahoma.gov/service/all-services/auto-vehicle/boats-motors.html",
         rules_src_name="Service Oklahoma, Boats &amp; Motors",
         note="Oklahoma is the value-priced state. It registers the <strong>boat and "
              "the motor separately</strong>, prices each on what it is worth rather "
              "than how long it is, depreciates the fee by 10% a year for nine "
              "years, and expires everything <strong>at the end of June</strong> "
              "whatever month you bought in."),
    dict(slug="indiana", name="Indiana", ab="IN", vol=10,
         agency="Indiana Bureau of Motor Vehicles", tier=2,
         decal="Indiana gives a direction as well as a distance: the decals go on the "
               "bow of each side of the watercraft, <strong>within three inches to the "
               "right of the registration number</strong>. If a registration number is "
               "not required to be displayed, they go on each side of the forward half "
               "of the bow <strong>above the water line</strong>.",
         rules_src="https://www.in.gov/bmv/registration-plates/boat-registration",
         rules_src_name="Indiana BMV, Watercraft Registration",
         note="The BMV page states where the number goes &mdash; painted on or "
              "attached to each side of the bow, legible and clearly visible &mdash; "
              "but does not publish a lettering pattern of its own, so we do not print "
              "one. The federal rule quoted above is what governs the height and "
              "spacing."),
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
