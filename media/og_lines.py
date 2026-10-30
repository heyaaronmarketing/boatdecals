# -*- coding: utf-8 -*-
"""What each card says.

Rules that make these work in a Facebook group, learned from the format they
are stolen from:

  * Three words beat eight. The whole card is read at thumbnail size while
    somebody scrolls past it.
  * The pipe breaks the line, so the rhythm is written rather than wrapped.
  * Every card either TEACHES something surprising or IS a joke. A card that
    only announces a product gets scrolled. "Michigan is MC, not MI" gets
    screenshotted and argued about in the comments, which is the point.
  * Hulls rotate so a feed with three of our cards in it does not look like
    three copies of the same card.

`script=True` sets the line in Pacifico, i.e. as a boat NAME on a transom.
Those are the pure-fun cards and they double as a demo of the script face.
"""

# path -> dict(main, kicker, hull, script)
LINES = {
 "/": dict(main="EVERYONE ELSE|HIDES THE PRICE", kicker="ours is $19 a pair",
           hull="navy"),

 "/boat-registration-numbers/": dict(
     main="3 INCHES.|BOTH SIDES.|$19.", kicker="legal in all 50 states",
     hull="black"),
 "/boat-lettering/": dict(main="Nauti Buoy", script=True,
     kicker="we cut whatever you call her", hull="white"),

 "/design/": dict(main="TYPE IT.|SEE IT.|SEND IT.",
     kicker="no designer, no proof, no queue", hull="green"),
 "/pricing/": dict(main="THE PRICE IS|ON THE PAGE", kicker="$19 a pair, shipped",
     hull="navy"),
 "/gallery/": dict(main="WHAT $19|LOOKS LIKE|ON A HULL", kicker="gallery",
     hull="teal"),

 "/registration-numbers/": dict(main="YOUR PREFIX|ISN'T WHAT|YOU THINK",
     kicker="11 states get this wrong", hull="red"),

 # ---- guides: every one of these is a thing people get wrong ----
 "/guides/boat-registration-number-rules/": dict(
     main="PLAIN BLOCK.|3 INCHES.|NOTHING FANCY.", kicker="33 CFR 173.27",
     hull="black"),
 "/guides/where-to-put-boat-registration-numbers/": dict(
     main="FORWARD HALF.|BOTH SIDES.", kicker="every state, no exceptions",
     hull="navy"),
 "/guides/how-to-apply-boat-lettering/": dict(
     main="WET METHOD.|TWENTY MINUTES.", kicker="how to apply boat lettering",
     hull="teal"),
 "/guides/how-to-remove-boat-lettering/": dict(
     main="HEAT.|PATIENCE.|A PLASTIC BLADE.", kicker="never use steel",
     hull="red"),
 "/guides/boat-lettering-fonts/": dict(
     main="SCRIPT IS ILLEGAL|ON YOUR NUMBERS", kicker="fine on the transom",
     hull="white"),
 "/guides/best-vinyl-for-boat-lettering/": dict(
     main="NOTHING STICKS|TO A KAYAK", kicker="which is why high-tack exists",
     hull="green"),
 "/guides/documented-vessel-name-and-hailing-port/": dict(
     main="DOCUMENTED BOATS|DON'T GET|BOW NUMBERS", kicker="4-inch name instead",
     hull="navy"),
 "/guides/boat-registration-number-cost/": dict(
     main="AN $11 SET|IS AN $18 SET|WITH SHIPPING", kicker="ours includes it",
     hull="black"),
 "/guides/": dict(main="THE RULES,|IN PLAIN ENGLISH", kicker="boat lettering guides",
     hull="navy"),

 # ---- tools: the fun ones ----
 "/tools/boat-name-generator/": dict(main="Wet Couch", script=True,
     kicker="free boat name generator", hull="teal"),
 "/tools/funny-boat-names/": dict(main="Ship Faced", script=True,
     kicker="400 funny boat names", hull="red"),
 "/tools/hull-number-decoder/": dict(main="YOUR HIN KNOWS|WHEN SHE|WAS BUILT",
     kicker="free hull number decoder", hull="black"),
 "/tools/registration-number-layout-checker/": dict(
     main="IS YOUR NUMBER|ACTUALLY LEGAL?", kicker="free layout checker",
     hull="green"),
 "/tools/": dict(main="FREE TOOLS|FOR BOAT OWNERS", kicker="no email wall",
     hull="navy"),

 # ---- by boat type ----
 "/for/": dict(main="EVERY HULL|NEEDS A NUMBER", kicker="by boat type", hull="navy"),
 "/for/jon-boats/": dict(main="JON BOATS|NEED NUMBERS|TOO", kicker="bare aluminium, no problem",
     hull="green"),
 "/for/kayaks-and-canoes/": dict(main="YOUR KAYAK|MIGHT NEED|NUMBERS",
     kicker="depends on your state", hull="teal"),
 "/for/jet-skis-and-pwc/": dict(main="PWC HULLS|EAT CHEAP VINYL",
     kicker="high-tack, free on every PWC order", hull="red"),
 "/for/pontoon-boats/": dict(main="TEXTURED RAILS|NEED HIGH-TACK",
     kicker="we ship it by default", hull="navy"),
 "/for/sailboats/": dict(main="CURVED TRANSOM?|SEND A PHOTO.",
     kicker="we lay it out from your measurement", hull="white"),
 "/for/bass-boats/": dict(main="METALFLAKE IS|THE EASIEST|SURFACE THERE IS",
     kicker="bass boat numbers, $19", hull="black"),

 # ---- the rest ----
 "/warranty/": dict(main="WE SAY WHAT|ISN'T COVERED", kicker="warranty and returns",
     hull="navy"),
 "/shipping-and-returns/": dict(main="FREE SHIPPING.|ALL 50 STATES.",
     kicker="cut and posted next business day", hull="teal"),
 "/contact/": dict(main="ONE PERSON.|ONE INBOX.", kicker="answered the same day",
     hull="navy"),
 "/boat-lettering-waterloo-cedar-falls/": dict(
     main="CUT ON THE|CEDAR RIVER", kicker="Evansdale, Iowa", hull="green"),
 "/privacy/": dict(main="WE DON'T SELL|YOUR DATA", kicker="privacy policy", hull="navy"),
 "/terms/": dict(main="THE BORING BIT", kicker="terms of service", hull="navy"),
}

# State cards are generated, because the joke writes itself: 11 states have a
# vessel prefix that is NOT their postal code, and nearly everyone assumes
# otherwise. Those get the gotcha; the rest get the plain fact.
STATE_HULLS = ["navy", "black", "teal", "green", "red", "white"]


def state_card(i, name, ab, postal):
    hull = STATE_HULLS[i % len(STATE_HULLS)]
    if ab != postal:
        return dict(main="%s IS %s|NOT %s" % (name.upper(), ab, postal),
                    kicker="yes, really", hull=hull)
    return dict(main="%s BOATS|START WITH %s" % (name.upper(), ab),
                kicker="%s registration numbers, $19" % name, hull=hull)


# ------------------------------------------------------- photo cards
# Commercial pages get the product ON something. A text card says what we
# sell; a card with the vinyl on a hull shows it, which is the question a
# buyer actually has. Teaching pages keep the typographic card, because there
# the LINE is the thing being shared.
#
# path -> (photo id, headline, sub-line, badge top, badge bottom)
_PHOTOS = {
    "/": ("AL-01", "LEGAL BOAT|NUMBERS",
          "BOTH SIDES - PRE-SPACED - POSTED NEXT DAY", "$19", "A PAIR"),
    "/design/": ("AL-10", "DESIGN YOURS|IN A MINUTE",
                 "TYPE IT - SEE IT - SEND IT", "$19", "A PAIR"),
    "/boat-registration-numbers/": ("AL-02", "3-INCH BLOCK|BOTH SIDES",
                 "PRE-SPACED ON ONE SHEET", "$19", "A PAIR"),
    "/boat-lettering/": ("AL-03", "NAME IT|PROPERLY",
                 "TEN FONTS - PRE-SPACED - FREE SHIPPING", "$29", "TO START"),
    "/pricing/": ("PR-1", "THE PRICE IS|ON THE PAGE",
                 "SHIPPING INCLUDED, ALL 50 STATES", "$19", "A PAIR"),
    "/for/jon-boats/": ("AL-04", "JON BOAT|NUMBERS",
                 "BARE ALUMINUM, NO PROBLEM", "$19", "A PAIR"),
    "/for/jet-skis-and-pwc/": ("AL-05", "PWC|NUMBERS",
                 "HIGH-TACK FILM, FREE ON EVERY PWC ORDER", "$19", "A PAIR"),
    "/for/kayaks-and-canoes/": ("AL-06", "KAYAK|NUMBERS",
                 "HIGH-TACK, BECAUSE PLASTIC FIGHTS BACK", "$19", "A PAIR"),
    "/for/pontoon-boats/": ("AL-07", "PONTOON|NUMBERS",
                 "TEXTURED RAILS NEED HIGH-TACK", "$19", "A PAIR"),
    "/for/sailboats/": ("AL-08", "SAILBOAT|LETTERING",
                 "CURVED TRANSOMS LAID OUT FROM YOUR PHOTO", "$29", "TO START"),
    "/for/bass-boats/": ("AL-10", "BASS BOAT|NUMBERS",
                 "METALFLAKE IS THE EASY ONE", "$19", "A PAIR"),
}


import pathlib as _pathlib
import re as _re

_STATE_AB = {}          # filled by og.py once content.STATES is importable


_SHOTS = _pathlib.Path(__file__).resolve().parent / "shots"


def has_photo(path):
    """True when a page gets a photo card AND its master actually exists.

    Both the renderer and the page builder call this, so the file extension
    they each decide on cannot disagree - and a page whose photo was never
    shot (Texas has no ST-TX) quietly falls back to the typographic card.
    """
    spec = photo_spec(path)
    return bool(spec) and (_SHOTS / (spec[0] + ".jpg")).exists()


def photo_spec(path):
    """The photo card for a page, or None to use the typographic one."""
    if path in _PHOTOS:
        return _PHOTOS[path]
    m = _re.match(r"^/registration-numbers/([a-z-]+)/$", path)
    if m and m.group(1) in _STATE_AB:
        name, ab = _STATE_AB[m.group(1)]
        return ("ST-" + ab, "%s BOAT|NUMBERS" % name.upper(),
                "%s PREFIX - 3-INCH BLOCK - BOTH SIDES" % ab, "$19", "A PAIR")
    return None


def register_states(states):
    for st in states:
        _STATE_AB[st["slug"]] = (st["name"], st["ab"])
