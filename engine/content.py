# -*- coding: utf-8 -*-
"""Content model for Boat Number Shop.

Every number in VOL/CPC came from a live DataForSEO google_ads search_volume
pull on 2026-10-22 (location_code 2840). FLEET counts are registered-vessel
totals per state. Both are recorded so later edits can be argued with data
instead of taste.
"""

SITE = {
    "brand": "Boat Number Shop",
    "short": "Boat Number Shop",
    "url": "https://boatnumbershop.com",
    "domain": "boatnumbershop.com",
    "tagline": "Boat registration numbers, $19 a pair. Shipped next business day.",
    "email": "orders@boatnumbershop.com",
    "hours": "Mon-Fri 8-5 CT",
    # Real NAP, supplied 2026-10-22. Must match the Google Business Profile and
    # every citation character-for-character - NAP consistency is the whole game
    # in local pack ranking.
    "phone_display": "(319) 239-3793",
    "phone_tel": "+13192393793",
    "street": "475 River Forest Road",
    "city": "Evansdale",
    "region": "IA",
    "region_name": "Iowa",
    "postal": "50707",
    "county": "Black Hawk County",
    "metro": "the Cedar Valley",
    # City-centre coordinates (Evansdale, IA per Wikipedia). Deliberately
    # city-level, not a rooftop pin - once the GBP is claimed, Google's own
    # pin is authoritative and this is only a hint.
    "lat": 42.4583,
    "lng": -92.2608,
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
    "numbers": 19,
    "numbers_premium": 27,
    "name_from": 29,
    "hailing": 15,
    "domed_from": 59,
    "carpet_from": 24,
    "oem_from": 22,
    "striping_from": 32,
    "rush": 12,
    "kit": 6,
    "free_ship_over": 0,     # free shipping on everything
}

UPGRADES = [
    ("Premium 8-year cast vinyl", 8, "3M/Oracal cast instead of calendared. Worth it on a boat that lives outside."),
    ("Add your boat name", PRICE["name_from"], "Priced by size. Most transom names land $29-79."),
    ("Hailing port line", PRICE["hailing"], "Required under the name on USCG documented vessels."),
    ("Rush - cut and shipped same day", PRICE["rush"], "Order before 1pm CT on a business day."),
    ("Reflective or metallic finish", 10, "Shows up under a spotlight. Legal in every state."),
    ("Install kit - squeegee + solution", PRICE["kit"], "Makes the wet method foolproof."),
]

# ---------------------------------------------------------------- products
# vol/cpc = the primary keyword this page is built to win.
PRODUCTS = [
    dict(slug="boat-registration-numbers", nav="Registration numbers", short="Reg numbers",
         h1="Boat Registration Numbers - $19 a Pair, Shipped Next Day",
         kw="boat registration numbers", vol=5400, cpc=2.60, price=PRICE["numbers"],
         unit="a pair", icon="numbers",
         blurb="Legal 3-inch block numbers for both sides of the hull. Pre-spaced on one sheet so you apply them in a single pass.",
         desc="Custom boat registration numbers, $19 a pair with free shipping. Legal 3-inch block vinyl for all 50 states, cut and shipped the next business day."),
    dict(slug="boat-lettering", nav="Boat lettering", short="Lettering",
         h1="Custom Boat Lettering - Any Font, Any Color",
         kw="boat lettering", vol=2400, cpc=4.59, price=PRICE["name_from"],
         unit="to start", icon="letter",
         blurb="Names, home ports, hull stripes, transom text. You pick the font and the colour, we cut it and pre-space it.",
         desc="Custom vinyl boat lettering from $29. 40+ marine fonts, 32 colours, 7-year warranty, free shipping, next-business-day production."),
    dict(slug="boat-name-decals", nav="Boat names", short="Boat names",
         h1="Boat Name Decals - From $29, Pre-Spaced and Ready",
         kw="boat name decals", vol=1600, cpc=3.54, price=PRICE["name_from"],
         unit="to start", icon="name",
         blurb="One decal, pre-spaced, with application tape over the top. Peel the backing, squeegee it on, pull the tape.",
         desc="Custom boat name decals from $29. Pre-spaced vinyl lettering in 40+ fonts, 7-year marine vinyl, free shipping, ships next business day."),
    dict(slug="boat-decals", nav="Boat decals", short="Boat decals",
         h1="Custom Boat Decals - Cut Vinyl, Marine Grade",
         kw="boat decals", vol=3600, cpc=3.58, price=22, unit="to start", icon="decal",
         blurb="Logos, graphics, flags, fish, bubble-free cut vinyl. Send artwork or describe it and we will draw it.",
         desc="Custom boat decals cut from 7-year marine vinyl. Logos, graphics and lettering from $22 with free shipping and next-day production."),
    dict(slug="motor-and-brand-decals", nav="Motor decals", short="Motor decals",
         h1="Outboard Motor &amp; Boat Brand Decals - Replacements That Match",
         kw="mercury boat decals", vol=880, cpc=0.85, price=PRICE["oem_from"],
         unit="to start", icon="motor",
         blurb="Faded cowling decals and hull brand graphics, re-cut to the original dimensions. Mercury, Yamaha, Johnson, Evinrude, Ranger, Tracker, Lund, Skeeter and more.",
         desc="Replacement outboard motor and boat brand decals from $22. Mercury, Yamaha, Johnson, Ranger, Tracker, Lund and Skeeter re-cut in marine vinyl."),
    dict(slug="boat-carpet-decals", nav="Carpet decals", short="Carpet decals",
         h1="Boat Carpet Decals - Logos That Stick to Carpet",
         kw="boat carpet decals", vol=590, cpc=0.62, price=PRICE["carpet_from"],
         unit="to start", icon="carpet",
         blurb="High-tack vinyl made for marine carpet, not hull gelcoat. Bass boat logos, brand marks, custom text.",
         desc="Boat carpet decals from $24. High-tack vinyl built to hold on marine carpet - bass boat logos, brand marks and custom text."),
    dict(slug="hailing-port-decals", nav="Hailing port", short="Hailing port",
         h1="Hailing Port Decals - For Documented Vessels",
         kw="hailing port decals", vol=70, cpc=1.33, price=PRICE["hailing"],
         unit="", icon="port",
         blurb="Federal rules want the name and hailing port in 4-inch characters on a documented vessel. We cut both as one pre-spaced set.",
         desc="Hailing port decals for USCG documented vessels, $15. Legal 4-inch lettering cut and pre-spaced with the vessel name."),
    dict(slug="domed-lettering", nav="Domed &amp; chrome", short="Domed",
         h1="Domed &amp; Chrome Boat Lettering - 3D Finish",
         kw="domed boat lettering", vol=110, cpc=3.09, price=PRICE["domed_from"],
         unit="to start", icon="domed",
         blurb="Each letter poured with a clear polyurethane dome so it reads as 3D in sunlight. Chrome, gold and colour-matched.",
         desc="Domed and chrome boat lettering from $59. Individually poured 3D letters in chrome, gold and custom colours with a 7-year warranty."),
    dict(slug="boat-striping", nav="Striping", short="Striping",
         h1="Boat Striping &amp; Pinstripe Tape",
         kw="boat striping", vol=90, cpc=2.24, price=PRICE["striping_from"],
         unit="to start", icon="stripe",
         blurb="Hull stripes cut to the width, length and colour you need, in single or multi-colour runs.",
         desc="Custom boat striping and pinstripe tape from $32. Any width, length and colour, cut from 7-year marine vinyl."),
]

# -------------------------------------------------------------- boat types
BOAT_TYPES = [
    dict(slug="sailboats", nav="Sailboats", title="Sailboat Name Decals &amp; Lettering",
         kw="sailboat name decals", vol=1600, cpc=3.54,
         lead="Transom names, cove stripes and hailing ports for sail. Curved transoms need the layout drawn to the curve, so we send a proof first.",
         note="A sailboat transom is rarely flat. Send a straight-on photo with a tape measure in frame and we will lay the name out to the actual curve."),
    dict(slug="pontoon-boats", nav="Pontoon boats", title="Pontoon Boat Decals &amp; Lettering",
         kw="pontoon boat decals", vol=480, cpc=0.59,
         lead="Fence-panel graphics, deck names and registration numbers sized for aluminium rails.",
         note="Pontoon fencing is usually brushed or painted aluminium. We ship high-tack vinyl for it by default, because standard adhesive lifts off a textured rail."),
    dict(slug="jet-skis-and-pwc", nav="Jet skis &amp; PWC", title="Jet Ski &amp; PWC Registration Numbers and Graphics",
         kw="jet ski decals", vol=210, cpc=0.90,
         lead="PWC hulls are moulded plastic with tight compound curves and almost no flat panel.",
         note="Plastic PWC hulls need high-tack vinyl. Standard vinyl will release from polyethylene inside a season - we send high-tack on every PWC order at no charge."),
    dict(slug="kayaks-and-canoes", nav="Kayaks &amp; canoes", title="Kayak &amp; Canoe Decals and Registration Numbers",
         kw="kayak decals", vol=320, cpc=0.39,
         lead="Most states only require numbers on a kayak once you hang a motor on it - including a trolling motor.",
         note="Rotomoulded polyethylene is the hardest surface in boating to stick to. High-tack vinyl, a clean alcohol wipe and a warm day are all mandatory."),
    dict(slug="bass-boats", nav="Bass boats", title="Bass Boat Decals, Carpet Logos &amp; Numbers",
         kw="bass boat decals", vol=210, cpc=0.54,
         lead="Metalflake gelcoat, carpet logos and tournament sponsor panels.",
         note="Metalflake is glossy and very forgiving - the wet method works perfectly. Carpet logos are a different product entirely and need high-tack."),
    dict(slug="jon-boats", nav="Jon boats", title="Jon Boat Decals &amp; Registration Numbers",
         kw="jon boat decals", vol=140, cpc=0.58,
         lead="Bare or painted aluminium, usually riveted, usually textured.",
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
         desc="The federal rule for boat registration numbers - 3-inch block characters, contrasting colour, correct spacing, forward half of each side - in plain English."),
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
         desc="Cast vs calendared vinyl for boats, when high-tack is mandatory, and what a 7-year warranty actually covers."),
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
    dict(slug="iowa", name="Iowa", ab="IA", fleet=340000, vol=20,
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
    dict(slug="florida", name="Florida", ab="FL", fleet=1700000, vol=140,
         agency="Florida Department of Highway Safety and Motor Vehicles", tier=1),
    dict(slug="michigan", name="Michigan", ab="MI", fleet=1700000, vol=140,
         agency="Michigan Secretary of State", tier=1),
    dict(slug="new-york", name="New York", ab="NY", fleet=1300000, vol=20,
         agency="New York State DMV", tier=1),
    dict(slug="california", name="California", ab="CF", fleet=1300000, vol=630,
         agency="California DMV", tier=1, vern="CF numbers",
         note="California is the one state that does not use its postal abbreviation. "
              "California boat numbers start with <strong>CF</strong>, and locals call them "
              "CF numbers - which is what people actually search for."),
    dict(slug="south-carolina", name="South Carolina", ab="SC", fleet=1100000, vol=30,
         agency="South Carolina Department of Natural Resources", tier=1),
    dict(slug="wisconsin", name="Wisconsin", ab="WI", fleet=1100000, vol=70,
         agency="Wisconsin DNR", tier=1),
    dict(slug="minnesota", name="Minnesota", ab="MN", fleet=1000000, vol=30,
         agency="Minnesota DNR", tier=1),
    dict(slug="texas", name="Texas", ab="TX", fleet=922000, vol=110,
         agency="Texas Parks and Wildlife Department", tier=1),
    dict(slug="pennsylvania", name="Pennsylvania", ab="PA", fleet=842000, vol=10,
         agency="Pennsylvania Fish and Boat Commission", tier=1),
    dict(slug="north-carolina", name="North Carolina", ab="NC", fleet=799000, vol=90,
         agency="NC Wildlife Resources Commission", tier=1),
    dict(slug="georgia", name="Georgia", ab="GA", fleet=783000, vol=110,
         agency="Georgia DNR Wildlife Resources Division", tier=1),
    dict(slug="virginia", name="Virginia", ab="VA", fleet=595000, vol=20,
         agency="Virginia Department of Wildlife Resources", tier=1),
    dict(slug="ohio", name="Ohio", ab="OH", fleet=573000, vol=50,
         agency="Ohio DNR Division of Parks and Watercraft", tier=1),
    dict(slug="illinois", name="Illinois", ab="IL", fleet=566000, vol=30,
         agency="Illinois DNR", tier=1),
    dict(slug="missouri", name="Missouri", ab="MO", fleet=561000, vol=70,
         agency="Missouri State Highway Patrol", tier=1),
    dict(slug="washington", name="Washington", ab="WN", fleet=560000, vol=40,
         agency="Washington State Department of Licensing", tier=2,
         note="Washington registration numbers begin with <strong>WN</strong>, not WA."),
    dict(slug="louisiana", name="Louisiana", ab="LA", fleet=446000, vol=70,
         agency="Louisiana Department of Wildlife and Fisheries", tier=2),
    dict(slug="alabama", name="Alabama", ab="AL", fleet=419000, vol=70,
         agency="Alabama Law Enforcement Agency, Marine Patrol", tier=2),
    dict(slug="tennessee", name="Tennessee", ab="TN", fleet=476000, vol=20,
         agency="Tennessee Wildlife Resources Agency", tier=2),
    dict(slug="indiana", name="Indiana", ab="IN", fleet=523000, vol=10,
         agency="Indiana Bureau of Motor Vehicles", tier=2),
]

FONTS = ["Block (legal for numbers)", "Arial Black", "Helvetica Bold", "Impact",
         "Clarendon", "Copperplate", "Times Bold", "Optima", "Futura",
         "Brush Script", "Edwardian Script", "Lobster", "Great Vibes",
         "Old English", "Stencil", "Varsity Block", "Hobo", "Cooper Black"]

COLORS = [("White","#ffffff"),("Black","#111111"),("Navy","#12243f"),("Royal Blue","#1b4fa8"),
          ("Light Blue","#5fc4f5"),("Teal","#0d7f7f"),("Forest","#15512c"),("Lime","#7ac70c"),
          ("Yellow","#f5d000"),("Orange","#f07c00"),("Red","#c8102e"),("Burgundy","#6d1026"),
          ("Purple","#5b2a86"),("Pink","#e8669e"),("Brown","#5a3a22"),("Tan","#c9a979"),
          ("Grey","#8b949c"),("Silver Metallic","#c6ccd1"),("Gold Metallic","#c9a227"),
          ("Chrome","#dfe6ea"),("Reflective White","#f2f4f5"),("Reflective Red","#d02b3f")]

# PAA harvested live from Google on 2026-10-22. These are the questions the
# answer engines are already answering for someone else.
FAQ_HOME = [
    ("How much do boat registration numbers cost?",
     "Ours are $19 a pair with free shipping, cut and shipped the next business day. "
     "Online prices across the market run about $10 to $25 a pair. Cheap sets are usually "
     "calendared vinyl with a 3-4 year life, cut as loose characters you space yourself."),
    ("Do boat registration numbers have to be a certain colour?",
     "Not a specific colour - but federal rule 33 CFR 173.27 requires the characters to "
     "contrast with the background and be distinctly visible and legible. White numbers on "
     "a white hull fail. Dark hull, light numbers; light hull, dark numbers."),
    ("How tall do boat registration numbers have to be?",
     "Not less than 3 inches in height, in plain vertical block characters. That is the "
     "federal minimum and it applies in every state. Taller is always legal."),
    ("Where do the numbers go on the boat?",
     "On each side of the forward half of the vessel, reading left to right, so they are "
     "visible from the water. The validation decal placement varies by state - usually "
     "within a few inches of the number."),
    ("Where can I get boat decals made?",
     "Here. You pick the characters, font and colour, we cut them from marine vinyl, "
     "pre-space them on one sheet with application tape, and ship next business day."),
    ("What kind of vinyl is best for boat decals?",
     "Cast vinyl for anything that lives outside - it conforms to curves and holds colour "
     "7+ years. High-tack is mandatory on plastic: kayaks, PWC hulls and pontoon rails. "
     "Calendared vinyl is cheaper and shorter-lived."),
    ("What is the difference between vinyl stickers and vinyl decals?",
     "A sticker is printed on a vinyl square and you see the background. A decal is cut "
     "from coloured vinyl, so only the letter shape sticks to the hull and there is no "
     "visible edge or square. Everything we make is cut vinyl."),
    ("Can I apply these myself?",
     "Yes - they arrive as one pre-spaced sheet under application tape, so the spacing is "
     "already right. Clean the hull, tape the sheet in place, wet it, squeegee, peel the "
     "tape. If it goes wrong we re-cut it free."),
]
