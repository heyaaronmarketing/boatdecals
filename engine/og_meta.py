# -*- coding: utf-8 -*-
"""Per-page social copy.

Facebook shows roughly 60 characters of title on a phone and hides the
description on most cards, so the title and the IMAGE have to carry the whole
offer on their own. Descriptions are written to 110 so they survive where they
do appear.

Anything not listed here falls back to the page's own title and description,
trimmed by verify.py's length gate.
"""
import html as _html

# path -> (og:title <=60, og:description <=110)
META = {
 "/": ("Legal Boat Registration Numbers - $19 a Pair",
       "3\" block vinyl, pre-spaced to the federal rule. Free shipping, cut and "
       "proofed within 12 hours."),
 "/design/": ("Design Your Boat Numbers - $19, Posted Next Day",
       "Type your number, see it on screen, and we cut it from marine vinyl. "
       "No designer to click through first."),
 "/boat-registration-numbers/": ("3-Inch Block Boat Numbers, Pre-Spaced - $19",
       "Both sides of the bow on one sheet, wet-apply in minutes. Free "
       "shipping, cut in Iowa."),
 "/boat-lettering/": ("Boat Names & Custom Lettering - From $29",
       "Ten marine fonts previewed in your own lettering. Pre-spaced with "
       "application tape over the top."),
 "/pricing/": ("Boat Numbers $19 a Pair - Every Price on One Page",
       "Numbers $19, letters from $29. Shipping included, and the price is on "
       "the page before you build anything."),
 "/gallery/": ("What $19 Boat Lettering Looks Like on a Hull",
       "Gelcoat, bare aluminum, kayaks, PWC and pontoon rails - the same vinyl "
       "on every surface we cut for."),
 "/registration-numbers/": ("Boat Registration Numbers by State - All 50",
       "Your vessel prefix is not always your postal code. 11 states differ. "
       "Find yours, then order a pair."),
 "/tools/boat-name-generator/": ("Free Boat Name Generator - 1,000+ Real Ideas",
       "Twenty-two categories, a radio-call test and a transom preview in real "
       "marine fonts. No email wall."),
 "/tools/funny-boat-names/": ("400 Funny Boat Names That Actually Land",
       "Sorted by how hard the joke lands, with the ones that fail the radio "
       "test marked. Free, no email."),
 "/tools/registration-number-layout-checker/":
      ("Are Your Boat Numbers Legal? Free 30-Second Check",
       "Test height, block font, contrast and spacing against 33 CFR 173.27 "
       "before the lake patrol does."),
 "/tools/hull-number-decoder/": ("Free Boat HIN Decoder - Read Your Hull Number",
       "Find the builder, the model year and the month your hull was laid up, "
       "straight from the 12 characters."),
 "/tools/": ("Free Boat Tools - HIN Decoder, Name Generator",
       "Four tools for boat owners, no email wall on any of them."),
 "/guides/boat-registration-number-rules/":
      ("Boat Registration Number Rules: Size, Font, Spacing",
       "The five federal display rules in plain English, and the mistakes that "
       "actually get warnings."),
 "/guides/where-to-put-boat-registration-numbers/":
      ("Where Boat Registration Numbers Go on the Hull",
       "Forward half, both sides, reading left to right - plus where your "
       "state wants the validation decal."),
 "/guides/how-to-apply-boat-lettering/":
      ("How to Apply Boat Lettering: the Wet Method",
       "Twenty minutes, a squeegee and soapy water. The method that lets you "
       "slide it straight before it grabs."),
 "/guides/how-to-remove-boat-lettering/":
      ("How to Remove Old Boat Lettering Safely",
       "Heat, patience and a plastic blade - and why a steel one will cost you "
       "the gelcoat underneath."),
 "/guides/boat-lettering-fonts/": ("Boat Lettering Fonts: What's Legal, What Works",
       "Script is illegal on a registration number and perfect on a transom. "
       "Ten fonts, and where each belongs."),
 "/guides/best-vinyl-for-boat-lettering/": ("Best Vinyl for Boat Lettering: Cast vs Calendared",
       "What actually sticks to a kayak, why high-tack exists, and the one "
       "surface that defeats standard film."),
 "/guides/documented-vessel-name-and-hailing-port/":
      ("Documented Vessel Name and Hailing Port Rules",
       "Documented boats carry no bow numbers. 4-inch name and hailing port "
       "instead, and a 3-inch interior number."),
 "/guides/boat-registration-number-cost/": ("What Boat Registration Numbers Cost",
       "An $11 set plus shipping is an $18 set. What separates a cheap pair "
       "from one that goes on straight."),
 "/guides/": ("Boat Lettering and Registration Guides",
       "The rules, the install, the removal and the vinyl grades - written by "
       "the person who cuts it."),
 "/warranty/": ("Boat Decal Warranty and Returns",
       "What the film warranty covers, where it stops, and what happens if we "
       "get your order wrong."),
 "/shipping-and-returns/": ("Free Shipping on Boat Numbers, All 50 States",
       "Posted 1-2 business days after you approve, then 3-6 days in post. "
       "No minimum, no surcharge."),
 "/contact/": ("Contact Number My Boat",
       "One person, one inbox, answered the same working day by whoever cuts "
       "your order."),
 "/boat-lettering-waterloo-cedar-falls/":
      ("Boat Lettering in Waterloo and Cedar Falls, Iowa",
       "Cut in Evansdale on the Cedar River. Free shipping anywhere, or local "
       "pickup by arrangement."),
}

# "{State} Boat Registration Numbers - {PFX} Rules + $19" keeps the state and
# the prefix inside the ~60 characters a phone shows.
def state_meta(name, ab):
    title = "%s Boat Numbers - %s Prefix, $19 a Pair" % (name, ab)
    desc = ("Federal 3-inch block rule, %s decal placement, and a pre-spaced "
            "pair, proof in 12 hours." % name)
    return title[:60], desc[:110]


def boat_type_meta(nav):
    # Boat-type nav labels carry entities ("Jet Skis &amp; PWC"); head()
    # escapes again, so unescape here or the card reads "&amp;amp;".
    nav = _html.unescape(nav)
    title = "%s Registration Numbers - $19 a Pair" % nav
    desc = ("3-inch block vinyl sized for %s, pre-spaced on one sheet. Free "
            "shipping, proof in 12 hours." % nav.lower())
    return title[:60], desc[:110]
