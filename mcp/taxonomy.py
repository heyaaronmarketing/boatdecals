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


# ---------------------------------------------------------------------------
# The remaining three vocabularies. Spec §2.
# ---------------------------------------------------------------------------
#
# WHY THESE ARE DERIVED AND NOT HAND-TAGGED, WHEN MECHANISM WAS NOT.
#
# humor_mechanism had to be per-name because the site's categories are
# THEMATIC, not mechanical: the pontoon lane contains literal truths, puns and
# deadpan side by side, so no rule could read a mechanism off a category.
#
# style_lanes are the opposite. The generator page's own first step is headed
# "Pick a vibe", and the thing it asks you to pick is the category. The
# categories ARE the lanes, in the site's own words, chosen by the person who
# wrote them. Deriving the lane from the category is not a shortcut around the
# work - it is reading the answer off the place where the decision was already
# made, and it means a name added to namegen.py arrives with its lane already
# right instead of waiting for someone to remember to tag it.
#
# themes and boat_types are keyword-derived for the same reason: "Walleye
# Wednesday" is about fishing because it says walleye, and a rule that reads
# the word will keep being correct for names nobody has written yet.
#
# Hand-written exceptions live in mcp/tags/overrides.tsv, which is applied
# after the rules and reported so the count stays visible.

LANES = {
    "deadpan": "flat delivery, no wink",
    "pun": "wordplay, homophones, twists",
    "absurd": "non-sequitur, surreal",
    "sincere": "not a joke at all",
    "dock": "dock-party humor - beer, the ex, the boss",
    "dark": "mortality, horror, dread",
    "nerd": "in-jokes for a trade or a discipline",
    "pontoon_dad": "slow boat, full cooler, lawn-chair energy",
    "regional": "lands on a local and nobody else",
    "brag": "retired, paid off, made it",
    "ironic": "claims the opposite of the truth",
    "current": "slang that will date",
}

THEMES = {
    "money", "fishing", "retirement", "drinking", "marriage", "divorce",
    "work", "family", "food", "death", "nature", "speed", "slow", "tech",
    "region", "laziness", "boat_ownership", "weather", "animals", "law",
}

# Deliberately NOT a complete taxonomy of boats. These are the hulls where a
# name either fits or looks ridiculous: "Pontoon Of Doom" on a bass boat, or
# "Dock Rocket (0-5 MPH)" on a 40-foot cruiser. An empty list means the name
# suits any boat, which is the common case and the right default.
BOAT_TYPES = {
    "pontoon", "bass", "runabout", "cruiser", "sail", "kayak", "jetski",
    "fishing_boat",
}

# category -> lanes. Several categories legitimately carry two.
CATEGORY_LANES = {
    "scratch": ["absurd", "deadpan"],
    "wtf": ["absurd"],
    "double": ["pun"],
    "ironic": ["ironic"],
    "deadpan": ["deadpan"],
    "pontoon": ["pontoon_dad"],
    "existential": ["deadpan", "dark"],
    "classy": ["sincere"],
    "horror": ["dark"],
    "payments": ["ironic", "dock"],
    "retirement": ["brag"],
    "nerd": ["nerd"],
    "corporate": ["nerd"],
    "divorce": ["dock"],
    "couples": ["dock"],
    "midwest": ["regional"],
    "fishing": ["pun"],
    "genz": ["current"],
    "food": ["absurd"],
    "anagram": ["pun"],
    "misspelled": ["pun"],
    "funny:Puns that actually land": ["pun"],
    "funny:The money jokes": ["ironic", "dock"],
    "funny:Fishing, specifically": ["pun"],
    "funny:Retirement bragging": ["brag"],
    "funny:Marriage commentary (order at your own risk)": ["dock"],
    "funny:Honest about the drinking": ["dock"],
}
