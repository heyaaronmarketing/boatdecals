#!/usr/bin/env python3
"""The fixed tag vocabularies. Spec §2 and §4b.

These are deliberately CLOSED sets. The point of tagging the bank is that the
engine can reason about *mechanisms* rather than names - "this lane responds to
deadpan, stop dealing it puns". That only works if a mechanism means the same
thing in every row, so a typo must be a build failure and not a 1,090th
mechanism with one member.
"""

# §4b, verbatim. The short code is what the tag files carry; a two-letter code
# keeps a 1,089-row hand-tagged file reviewable on one screen.
MECHANISMS = {
    "hp": "homophone pun",
    "pm": "portmanteau",
    "tt": "title twist",            # song, film, book, proverb
    "dp": "deadpan understatement",
    "dm": "double meaning",
    "ba": "backronym",
    # §4b calls this "profession in-joke". Broadened, not replaced: the bank
    # has three in-group lanes, not one - corporate jargon (profession),
    # Midwest dialect (region: Ope, Hotdish, Pop Not Soda) and Gen Z slang
    # (cohort: Delulu, No Cap, Rizz Boat). They are the same mechanism doing
    # the same work - the joke lands only on a member and is invisible to
    # everyone else - so they share a tag, and the ranker gets one rule rather
    # than three: never deal pj until the interview proves membership. Kept as
    # one value so the humor-mechanism count stays at the §4b ten.
    "pj": "in-group in-joke (profession, region, cohort)",
    "an": "personal-name/place anagram",
    "lt": "literal truth",
    "md": "misdirection",

    # SPEC EXTENSION, deliberate. §4b's ten values all describe how a JOKE
    # works, and the site's `classy` lane is 50 names that are not jokes -
    # Halcyon, Lodestar, Wild Rice, True North. There is no honest way to tag
    # Halcyon as deadpan understatement, and tagging it as one is not a
    # cosmetic error: the riff brief reads mechanisms to decide what to write
    # next, so a sincere name mislabelled "deadpan" teaches the engine that a
    # deadpan lane responded to Halcyon and it starts writing more Halcyons
    # into deadpan rounds.
    #
    # So sincere is a real value, not a null. Gate 21 ("100% of names carry a
    # humor_mechanism") still holds. But sincere is NOT a humor mechanism:
    # it must never be offered to the riff brief as a mechanism to write in,
    # and never counted in a lane's proven-mechanism ledger.
    "sincere": "sincere (not a joke)",
}

# The ten §4b mechanisms - everything in MECHANISMS except the extension. This
# is the set the riff brief and the mechanism ledger may use.
HUMOR_MECHANISMS = {k: v for k, v in MECHANISMS.items() if k != "sincere"}

# §2: humor_level (clean/dock/double). This is NOT "how funny" - it is who can
# be in earshot. It drives what the engine may deal to a man naming the boat he
# takes his grandkids on, which is most of them.
LEVELS = {
    "c": "clean",     # reads fine with the pastor aboard
    "d": "dock",      # dock-party humor: beer, debt, the ex-wife, the boss
    "x": "double",    # double entendre; funny until a six-year-old reads it
}

# Mechanisms whose whole joke is that the spelling is wrong. The radio gate
# penalises these, so they are flagged here rather than rediscovered: a name
# that has to be spelled out over VHF is a different product from a name that
# just has to be said.
SPELLING_BURDEN_CATEGORIES = {"misspelled"}


def check(mech, level):
    """Return a problem string, or None."""
    if mech not in MECHANISMS:
        return "unknown mechanism %r (allowed: %s)" % (
            mech, " ".join(sorted(MECHANISMS)))
    if level not in LEVELS:
        return "unknown humor_level %r (allowed: %s)" % (
            level, " ".join(sorted(LEVELS)))
    return None
