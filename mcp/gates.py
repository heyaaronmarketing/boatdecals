#!/usr/bin/env python3
"""The deterministic gates. Spec §4a.

These are pure functions. No model, no network, no randomness: the same name
gets the same verdict every time, and every verdict can be explained to a
customer in a sentence. That is the whole point - the engine's credibility
rests on TESTING names, and a test whose answer moves is not a test.

What each gate is for:

  radio_gate    Can the Coast Guard write this down from hearing it once?
  overuse_gate  Is this the name on four other boats at every ramp?
  novelty_gate  Is this "new" riff just a bank name with a word moved?

The fit gate lives separately (it needs real font metrics, not text rules).

HONESTY LIMITS, enforced in code below:
  - The overuse tier is a heuristic from market data, NOT a registry. This
    module must never emit language claiming a name is taken on a particular
    lake or at a particular marina. There is a test for that.
  - The radio gate fails only what is genuinely unusable. Half this bank is
    built on homophones; "Knot Working" is a great name, and a gate that
    killed it would be a gate that killed the product.
"""
import functools
import gzip
import json
import math
import pathlib
import re
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
LEXICON_F = HERE / "data" / "lexicon.txt.gz"

_LEX = None


def lexicon():
    """The baked standard-English word list. See build_lexicon.py."""
    global _LEX
    if _LEX is None:
        if not LEXICON_F.exists():
            raise RuntimeError(
                "no %s - run python3 mcp/build_lexicon.py. The radio gate "
                "cannot tell a nonstandard spelling from a standard one "
                "without it, and guessing is worse than failing loudly."
                % LEXICON_F)
        with gzip.open(LEXICON_F, "rt", encoding="utf-8") as f:
            _LEX = set(f.read().split("\n"))
    return _LEX


# ---------------------------------------------------------------------------
# The radio gate
# ---------------------------------------------------------------------------
#
# The scenario this gate is actually about: the owner is on channel 16 saying
# the name of his boat to someone who has never heard it, who has to write it
# down. Three different things can go wrong, and they are not the same problem:
#
#   1. AMBIGUOUS - spelled normally, sounds like something else. "Knot Working"
#      is heard as "not working". Costs one clarification: "knot, like rope."
#      This is most of the bank and it is FINE. A pun is the product.
#
#   2. NONSTANDARD - sounds right, spelled wrong. "Bote", "Fysh", "Yaht". The
#      listener writes "Boat" and is now looking for the wrong boat. Costs a
#      full spell-out, every single time, forever.
#
#   3. UNUSABLE - letter-soup. Digits standing in for words ("Nauti-4-U"),
#      symbols, or so long nobody gets through it. There is no readback that
#      fixes this.
#
# Spec test 11 pins the line exactly: "Knot On Call" is fine, the "Nauti-4-U"
# class fails. So only 3 fails. 1 and 2 pass with a note, and the note is worth
# saying out loud - it is the kind of thing only someone who has actually used
# a VHF would tell you.

# Digits and letters doing duty as words. This is the single clearest signal of
# the unusable class, and it is why "Nauti-4-U" fails while "Nauti Buoy" does
# not - one is a rebus, the other is a pun.
# The rebus class, and ONLY the rebus class. A digit or single letter standing
# in for a WORD - "Nauti-4-U", "Sea-U-L8r", "B4 Sunrise". There is no way to
# say these so a listener writes them as spelled, and spelling them out does
# not help either, because "four" and "4" sound identical.
#
# Bare numerals are deliberately NOT here. "Draft 1", "Freedom 45", "Boat 2.0"
# and "Payment 12 Of 240" are all numbers doing a number's job, and the first
# version of this gate refused every one of them.
REBUS_TOKENS = {
    "u", "r", "b4", "l8", "l8r", "gr8", "4u", "2u", "cu", "ur", "2nite",
    "4ever", "ne1", "any1", "some1", "w8", "sk8", "xoxo",
}
# A digit wedged between letters, hyphenated or not: Nauti-4-U, M8, Sk8er.
_REBUS_SHAPE = re.compile(r"[A-Za-z]-?\d-?[A-Za-z]")

# Devices that work on the page and vanish when spoken. A parenthetical is the
# signature joke of this bank - "Unsinkable (Terms Apply)", "Paid In Full*",
# "Starboard Is Left*" - and the first version of this gate FAILED all of them
# on the grounds that you cannot say a bracket.
#
# You do not say the bracket. You say "Unsinkable, terms apply," and it is
# perfectly clear. What is lost is the deadpan: the asterisk is the punchline
# and nobody hears an asterisk. So this is not a radio failure at all, it is a
# separate fact worth telling a customer - that one only lands written down.
VISUAL_ONLY = set("()[]*%+/<>~^_=|{}")

# Words that sound exactly like another word. Hearing one of these, a listener
# writes the common spelling - which is the joke, and also the problem. Kept as
# an explicit table rather than derived, because this is about what a HUMAN
# mishears, and no phonetic algorithm knows that "buoy" is said "boy" in the
# United States and "boo-ee" in a dictionary.
HOMOPHONES = {
    "knot": "not", "reel": "real", "sea": "see", "seas": "seize",
    "buoy": "boy", "hull": "hell", "moor": "more", "aft": "after",
    "berth": "birth", "tide": "tied", "sole": "soul", "pier": "peer",
    "oar": "or", "bass": "base", "mast": "mass", "prop": "pop",
    "port": "poor", "sail": "sale", "keel": "kill", "helm": "hell",
    "stern": "stearn", "wake": "woke", "bow": "bough", "crappie": "crappy",
    "carp": "carpe", "cod": "god", "fin": "finn", "jib": "gib",
    "trim": "trem", "shore": "sure", "lure": "lore", "current": "currant",
    "nauti": "naughty", "ship": "shhh", "coastal": "postal",
    "fission": "fishin", "mussel": "muscle", "pour": "poor", "bote": "boat",
}

_WORD = re.compile(r"[A-Za-z0-9'\u2019-]+")
_OK_PUNCT = set(" '&,.!?-:")
_VOWELS = set("aeiouy")


def _tokens(name):
    """Words, with hyphenated compounds kept whole.

    Splitting on the hyphen turns Aqua-holic into "aqua" and "holic" and makes
    the gate report that "holic" is not a word. It is not; the name is not
    "holic" either. A hyphenated coinage is judged as the one word it reads as.
    """
    return [t.strip("-") for t in _WORD.findall(name) if t.strip("-")]


def _syllables(word):
    """Crude syllable count. Only used for 'is this a mouthful', where being
    one off does not change the verdict."""
    w = word.lower()
    n, prev = 0, False
    for ch in w:
        v = ch in _VOWELS
        if v and not prev:
            n += 1
        prev = v
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


# Webster's 1913 - which is what /usr/share/dict/words is - carries thousands
# of archaic and dialect entries. Several of them collide exactly with the
# respellings this bank is built on: `bote`, `nawt`, `gud`, `shure`, `thee`,
# `bois` and `da` are all REAL entries in that dictionary, which made the first
# version of this gate pass 12 of the 30 deliberately-misspelled names. Nobody
# writing a boat name in 2026 means the Middle English legal term "bote"; they
# mean "boat". So these tokens are forced back through the respelling rules.
#
# This list is the honest cost of using a free dictionary with no frequency
# data. Each entry is here because the modern reading is overwhelmingly more
# likely than the dictionary one, not because it was convenient for a test.
ARCHAIC_COLLISIONS = {
    "bote", "nawt", "gud", "shure", "thee", "bois", "da", "ye", "tha",
    "wot", "sez", "wuz", "kum", "ded", "red",  # 'red' as in "red the sail"
    "thar", "thet", "bin", "ter", "fer", "ar", "ser", "nite", "lite",
}

# Productive respelling rules. Each one is the INVERSE of a substitution people
# actually make when they respell a word on a transom, so applying it to a
# nonstandard token and finding a dictionary word proves what the listener will
# write down. This is why the gate generalises: it was not built by listing the
# bank's 30 misspelled names, it was built from the substitutions, and it finds
# respellings nobody has written yet.
RESPELL_RULES = [
    (r"(.)\1$", r"\1"),        # Ahoyy  -> Ahoy
    (r"^(.*)yy", r"\1y"),
    (r"k", "c"),                # Nautikal -> Nautical, Titanik -> Titanic
    (r"ph", "f"),               # Phloat -> Float
    (r"y", "i"),                # Lyfe -> Life, Fysh -> Fish
    (r"z$", "s"),               # Anchorz -> Anchors
    (r"z", "s"),
    (r"abel$", "able"),         # Unsinkabel -> Unsinkable
    (r"el$", "le"),
    (r"aw", "o"),               # Nawt -> Not
    (r"u", "oo"),               # Gud -> Good
    (r"ois$", "oys"),           # Bois -> Boys
    (r"ote$", "oat"),           # Bote -> Boat
    (r"ott$", "acht"),          # Yott -> Yacht
    (r"aht$", "acht"),          # Yaht -> Yacht
    (r"^sh", "s"),              # Shure -> Sure
    (r"ah$", "a"),              # Marinah -> Marina
    (r"ery$", "ury"),           # Luxery -> Luxury
    (r"ius", "iou"),            # Seriusly -> Seriously
    (r"ayter$", "ater"),        # Layter -> Later
    (r"n$", "ng"),              # Fishn -> Fishng -> (with another pass) ...
    (r"n$", "ing"),             # Fishn -> Fishing
    (r"ee", "e"),               # Thee -> The
    (r"^(.)$", r"\1"),
    (r"il$", "ittle"),          # Lil -> Little
    (r"eel", "eal"),            # (Reel is in HOMOPHONES; this catches others)
    (r"oa", "o"),
    (r"o", "oa"),
    (r"i", "ea"),
    (r"u", "ou"),
]


def _initialism(token):
    """Is this an initialism - APR, MPH, KPI, PTO, HOA?

    These are read letter by letter, which is a cost on the radio but a normal
    and expected one: nobody is confused by "A-P-R", they just have to hear
    three letters. Calling that a misspelling - which the first version did -
    puts KPI in the same bucket as "Fysh", and they are not the same problem.
    """
    t = (token or "").strip("'")
    if not (2 <= len(t) <= 5) or not t.isalpha():
        return False
    return t.isupper() and not _is_word(t.lower())


@functools.lru_cache(maxsize=40000)
def _is_word(t):
    """Is this a standard English word, allowing for inflection?

    Webster's 1913 lists almost no plurals - "boy" is in it, "boys" is not -
    so a bare set membership test calls half of written English nonstandard.
    Both the respelling search and the coinage check go through here, because
    the first version had them disagree: the coinage check forgave "boys" via
    its suffix rule while the respelling search could not reach it, so
    "Bois" -> "Boys" was silently missed.
    """
    lex = lexicon()
    if t in lex:
        return True
    # A doubled final letter is a respelling signature, not an inflection.
    # Without this, stripping the "y" off "Ahoyy" produces "ahoy" and the gate
    # declares a deliberate misspelling to be a standard word.
    if len(t) > 2 and t[-1] == t[-2]:
        return False
    for suf in ("s", "es", "ed", "ing", "er", "est", "ly", "y"):
        if t.endswith(suf) and len(t) > len(suf) + 2 and t[: -len(suf)] in lex:
            return True
    # doubled-consonant inflections: running -> run, bigger -> big
    for suf in ("ing", "ed", "er", "est"):
        if t.endswith(suf):
            stem = t[: -len(suf)]
            if len(stem) > 2 and stem[-1] == stem[-2] and stem[:-1] in lex:
                return True
    # dropped-e inflections: making -> make
    for suf in ("ing", "ed", "er", "est"):
        if t.endswith(suf) and len(t) > len(suf) + 2 and t[: -len(suf)] + "e" in lex:
            return True
    return False


@functools.lru_cache(maxsize=20000)
def _respelling(token):
    """The standard word this token is a respelling of, or None.

    Breadth-first over the rules, up to two substitutions, because real
    respellings stack: "Fast Bote" is one, "Sea Ya Layter" is two.
    """
    t = token.lower().strip("'\u2019").replace("-", "")
    # Gone Fishin', Bussin', Growin' - the dropped g is an elision everybody
    # reads correctly, not a respelling anybody has to spell out.
    if t.endswith("in") and _is_word(t + "g"):
        return None
    if len(t) < 3 or not t.isalpha():
        return None
    if _is_word(t) and t not in ARCHAIC_COLLISIONS:
        return None

    seen, frontier = {t}, [t]
    for _ in range(2):
        nxt = []
        for cur in frontier:
            for pat, repl in RESPELL_RULES:
                cand = re.sub(pat, repl, cur)
                if cand == cur or cand in seen or len(cand) < 3:
                    continue
                seen.add(cand)
                nxt.append(cand)
                if _is_word(cand) and cand not in ARCHAIC_COLLISIONS:
                    return cand
        frontier = nxt
    return None


@functools.lru_cache(maxsize=20000)
def _nonstandard(token):
    """(is_nonstandard, heard_as). heard_as is the word a listener will write.

    Two different failures land here. A RESPELLING has a known target, so the
    gate can say "they will write Boat" - which is the useful sentence. A
    COINAGE has none: Boatiful is not a misspelling of anything, it is a new
    word, and it still has to be spelled out every time.
    """
    bare = token.lower().strip("'\u2019")
    t = bare.replace("-", "")
    if len(t) < 3 or not t.isalpha():
        return False, None
    if _initialism(token):
        return False, None
    # A hyphenated compound of real words is spelled predictably: Co-Signed,
    # Low-Hanging, Try-Angle, Bankrupt-Sea. Judging the joined form instead
    # ("cosigned", "lowhanging", "tryangle") calls all four unspellable.
    # Parts under three letters are prefixes and are not held against it.
    if "-" in bare:
        _parts = [x for x in bare.split("-") if len(x) >= 3]
        if _parts and all(_is_word(x) for x in _parts):
            return False, None
    if t.endswith("in") and _is_word(t + "g"):
        return False, None

    heard = _respelling(t)
    if heard:
        return True, heard

    if _is_word(t):
        return False, None
    lex = lexicon()
    # A closed compound of two real words is spelled predictably: Lodestar,
    # Honeylocust, Tallgrass. Both halves must be substantial - a 3-letter
    # fragment matches almost anything in a 176,000-word list.
    for i in range(4, len(t) - 3):
        if t[:i] in lex and t[i:] in lex:
            return False, None
    return True, None


def _spoken(name):
    """The name as a person would say it on the radio.

    The readback is spoken aloud at the reveal (spec §5), so it has to be the
    words, not the typography. Brackets and asterisks are dropped rather than
    read: nobody says "Unsinkable open bracket terms apply close bracket."
    """
    s = re.sub(r"[*\u2020\u2021]", "", name or "")
    # The space before the bracket goes too, or the readback reads
    # "Unsinkable , Terms Apply" with a space in front of the comma.
    s = re.sub(r"\s*[\(\[\{]\s*", ", ", s)
    s = re.sub(r"[\)\]\}]", "", s)
    s = s.replace("&", " and ").replace("%", " percent")
    s = re.sub(r"\s+", " ", s).strip().strip(",").strip()
    # Trailing punctuation comes off, because the readback puts a full stop
    # after it. The bank has "Loading..." and "Pending" in it, and the reveal
    # was saying "Mayday, mayday, this is Loading....", with four dots, on the
    # one screen the whole session is building towards.
    return re.sub(r"[\u2026.,;:!?\-]+$", "", s).strip()


def radio_gate(name):
    """Can this be written down from hearing it once?

    Deliberately NOT memoised, although the scalar helpers below it are. This
    returns a mutable dict, and lru_cache would hand every caller the same
    object - one caller adding a field would silently change what every later
    caller sees. The helpers it leans on are cached instead, which is where the
    cost actually was: a full pass over the 1,089-name bank runs in 0.06s.

    Returns a dict:
      verdict   'clear' | 'sayable' | 'mouthful' | 'spell_it' | 'fail'
      dealable  False only for 'fail'
      readback  the line the assistant should actually SAY
      reasons   plain-language strings, safe to show a customer
      spell_out   True if the owner will have to spell it every time
      visual_only True if the joke needs to be seen, not heard
    """
    raw = (name or "").strip()
    if not raw:
        return {"verdict": "fail", "dealable": False, "readback": "",
                "reasons": ["No name given."], "spell_out": True,
                "visual_only": False, "score": 0}

    # Normalise accents for analysis but keep the original for the readback -
    # "Déjà Vu" is said the same as "Deja Vu" and should not be punished.
    flat = unicodedata.normalize("NFKD", raw)
    flat = "".join(c for c in flat if not unicodedata.combining(c))

    toks = _tokens(flat)
    letters = sum(len(t) for t in toks)
    words = len(toks)
    sylls = sum(_syllables(t) for t in toks)

    reasons, hard = [], []
    spell_out = False

    # --- unusable: the rebus class ---------------------------------------
    rebus = sorted({t for t in toks if t.lower() in REBUS_TOKENS})
    if rebus and words > 1:
        hard.append('"%s" stands in for a whole word. Said out loud there is '
                    "no way for anybody to know you spelled it that way, and "
                    "spelling it out does not help - the letter and the word "
                    "sound the same." % '", "'.join(rebus))
    if _REBUS_SHAPE.search(flat):
        hard.append("A digit wedged inside the words cannot be spoken as "
                    "written.")
    # Anything outside letters, digits, ordinary punctuation and the visual
    # devices above - an arrow, an emoji, a currency sign.
    exotic = {c for c in flat
              if not c.isalnum() and c not in _OK_PUNCT and c not in VISUAL_ONLY}
    if exotic:
        hard.append("%s cannot be said at all - it has to be described."
                    % " ".join(sorted(exotic)))

    if hard:
        return {"verdict": "fail", "dealable": False,
                "readback": "", "reasons": hard, "spell_out": True,
                "visual_only": False, "score": 0}

    # --- devices that only work written down -----------------------------
    visual = sorted({c for c in flat if c in VISUAL_ONLY})
    visual_only = bool(visual)
    if visual_only:
        reasons.append("The %s is the punchline and nobody hears punctuation. "
                       "This one lands on the transom, not on the radio."
                       % ("brackets" if "(" in visual else
                          "asterisk" if "*" in visual else
                          " ".join(visual)))

    # A digit inside a name is sayable but not spellable-from-hearing: say
    # "Q four Goals" and the listener has to ask whether that is a numeral.
    if any(c.isdigit() for c in flat):
        spell_out = True
        reasons.append("There is a number in it, so expect to confirm whether "
                       "it is a numeral or spelled out.")

    # --- nonstandard spelling --------------------------------------------
    odd, heard = [], []
    for t in toks:
        bad, as_ = _nonstandard(t)
        if bad:
            odd.append(t)
            if as_:
                heard.append((t, as_))
    if odd:
        spell_out = True
        if heard:
            reasons.append("Say this on the radio and they write down %s. "
                           "You will be spelling it out every time."
                           % ", ".join('"%s" instead of "%s"' % (a, t)
                                       for t, a in heard))
        else:
            reasons.append("%s %s not a word anybody can spell from hearing "
                           "it, so expect to spell this one out every time."
                           % (", ".join(odd),
                              "is" if len(odd) == 1 else "are"))

    inits = sorted({t for t in toks if _initialism(t)})
    if inits:
        reasons.append("%s get%s read out letter by letter - normal on a "
                       "radio, just slower." % (", ".join(inits),
                                                "s" if len(inits) == 1 else ""))

    # --- homophone ambiguity ---------------------------------------------
    homo = [t for t in toks if t.lower() in HOMOPHONES]
    if homo:
        pairs = ", ".join('"%s" (heard as "%s")'
                          % (t, HOMOPHONES[t.lower()]) for t in homo)
        reasons.append("Expect to say it twice the first time: %s. That is the "
                       "joke working, not a problem with the name." % pairs)

    # --- mouthful ---------------------------------------------------------
    if sylls >= 9 or words >= 5:
        reasons.append("It is a long one on the radio - %d syllables."
                       % sylls)

    # --- verdict ----------------------------------------------------------
    if spell_out:
        verdict = "spell_it"
    elif letters > 24 or words > 6 or sylls >= 12:
        verdict = "mouthful"
        reasons.append("At %d letters across %d words this is a long haul on "
                       "channel 16. Fine on a transom, slow on a radio."
                       % (letters, words))
    elif homo or sylls >= 9 or words >= 5:
        verdict = "sayable"
    else:
        verdict = "clear"
        reasons.append("Says clean and spells itself.")

    # 0-100, only for ranking. The verdict is what a human is shown.
    score = 100
    score -= 35 if spell_out else 0
    score -= 8 * len(homo)
    score -= max(0, sylls - 6) * 4
    score -= max(0, words - 3) * 5
    score = max(1, min(100, score))

    return {"verdict": verdict, "dealable": True,
            "readback": "Mayday, mayday, this is %s." % _spoken(raw),
            "reasons": reasons, "spell_out": spell_out,
            "visual_only": visual_only, "score": score}


# ---------------------------------------------------------------------------
# The overuse gate
# ---------------------------------------------------------------------------
#
# HONESTY LIMIT (spec §4a): this is a heuristic from market data. We do not
# have a registry, we cannot see any particular marina, and we must never say
# or imply otherwise. "Common everywhere" is true and useful. "Taken at your
# marina" is a claim we cannot support and would be caught out on by the first
# customer who looked.

# Tier 1 - the names you see at every ramp in America. The spec names Serenity,
# Vitamin Sea and Seas the Day by example; these are that class.
OVERUSE_T1 = {
    "serenity", "vitamin sea", "seas the day", "island time", "second wind",
    "aquaholic", "aqua-holic", "knot working", "carpe diem", "freedom",
    "serendipity", "escape", "pura vida", "therapy", "shenanigans",
    "liquid asset", "liquid assets", "namaste", "dream weaver", "wet dream",
    "nauti buoy", "miss behavin", "fishful thinking", "happy hour",
    "no worries", "sea ya", "last resort", "the office", "reel therapy",
}
# Tier 2 - common, but not a punchline yet.
OVERUSE_T2 = {
    "shore thing", "sole mates", "pier pressure", "knot a problem",
    "hull yeah", "ship faced", "shipfaced", "dock holiday", "reel deal",
    "anchor management", "berth control", "current sea", "sail la vie",
    "buoy oh buoy", "oh buoy", "gone coastal", "sofishticated", "codfather",
    "trolling", "hooked", "bite me", "tight lines", "fish on",
    "lake time", "forever friday", "the golden years", "boat payment",
}

_FORBIDDEN_CLAIMS = ("at your marina", "on your lake", "already taken",
                     "is taken", "registered to", "in your county")


def _norm(name):
    s = unicodedata.normalize("NFKD", (name or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def overuse_gate(name):
    """Returns tier 1, 2 or 0, and the note to show if the name is displayed.

    tier 1 is excluded from top picks unless the user asks for popular names;
    it is never silently dropped and never shown without the note.
    """
    n = _norm(name)
    if n in {_norm(x) for x in OVERUSE_T1}:
        return {"tier": 1, "top_pick_eligible": False,
                "note": "One in every marina. This is one of the most common "
                        "boat names in the country - a fine name, but you will "
                        "be answering to it alongside somebody else."}
    if n in {_norm(x) for x in OVERUSE_T2}:
        return {"tier": 2, "top_pick_eligible": True,
                "note": "Common, but not worn out."}
    return {"tier": 0, "top_pick_eligible": True, "note": None}


# ---------------------------------------------------------------------------
# The novelty gate
# ---------------------------------------------------------------------------

def _bigrams(s):
    s = _norm(s).replace(" ", "")
    return {s[i:i + 2] for i in range(len(s) - 1)} or {s}


def _dice(a, b):
    A, B = _bigrams(a), _bigrams(b)
    return 2 * len(A & B) / (len(A) + len(B)) if (A or B) else 0.0


def novelty_gate(candidate, bank_names, threshold=0.82):
    """Reject a 'new' riff that is really a bank name with a word moved.

    The riff lane exists to produce names the bank does not have. A model
    handed a bank of 1,089 names and asked to be creative will hand back a
    near-copy of one of them, confidently, and it reads as new until somebody
    searches the bank. So this compares against every bank name and reports
    the closest match rather than a yes/no.
    """
    n = _norm(candidate)
    if not n:
        return {"novel": False, "closest": None, "similarity": 1.0,
                "reason": "Empty candidate."}
    best, score = None, 0.0
    for b in bank_names:
        if _norm(b) == n:
            return {"novel": False, "closest": b, "similarity": 1.0,
                    "reason": "Already in the bank, word for word."}
        d = _dice(n, b)
        if d > score:
            best, score = b, d
    if score >= threshold:
        return {"novel": False, "closest": best, "similarity": round(score, 3),
                "reason": 'Too close to "%s" already in the bank.' % best}
    return {"novel": True, "closest": best, "similarity": round(score, 3),
            "reason": None}


def claims_are_honest(text):
    """Guard for the overuse language. Returns the offending phrase, or None."""
    t = (text or "").lower()
    for bad in _FORBIDDEN_CLAIMS:
        if bad in t:
            return bad
    return None


# ---------------------------------------------------------------------------
# The fit gate
# ---------------------------------------------------------------------------
#
# The only gate that cannot be done with text rules, because the answer is
# physical: will this name, in this face, at this height, actually go on the
# flat run of his hull?
#
# The site's browser estimate is `chars * 2.5" + spaces * 1.5"` at a fixed 4
# inches with no idea which face is selected. Playbill at 4 inches and Arial
# Bold at 4 inches are not the same width. This gate measures instead, from
# per-character advance widths pulled out of the ten real TTFs - the same files
# that cut the vinyl - and baked by build_font_metrics.py.
#
# Measured error of the model against whole strings: 1.43% worst case across
# all ten faces (kerning, which summing advances cannot see). That number is
# reported to the customer rather than hidden, because it is far smaller than
# the error in his own tape measure and saying so is what makes the figure
# believable.

METRICS_F = HERE / "data" / "font_metrics.json"
FIT_ERROR_PCT = 1.5          # measured; see build_font_metrics.py --check
HEIGHTS_IN = (3, 4, 5, 6)    # the four the site sells
# Leave the lettering some air. A name that is exactly as wide as the flat run
# is a name touching the rubrail at both ends, and it looks like a mistake even
# when it fits.
COMFORT = 0.90

_MET = None


def _r1(x):
    """Round to one decimal, HALF UP.

    Python's round() is half-to-EVEN: round(8.45, 1) is 8.4 while JavaScript's
    Math.round(8.45*10)/10 is 8.5. The equivalence test caught this on "Aloft"
    in Impact - 8.4 here, 8.5 in the worker - which would have shipped as the
    MCP server and the website quoting different widths for the same name in
    the same face. Both sides now round half up.
    """
    return math.floor(x * 10 + 0.5) / 10


def _inch(x):
    """Format inches the way JavaScript stringifies a number: 36, not 36.0.

    Same reason. Python's "%s" % 36.0 is "36.0" and JS gives "36", so the two
    implementations were emitting different sentences to customers.
    """
    return "%g" % _r1(x)


def metrics():
    global _MET
    if _MET is None:
        if not METRICS_F.exists():
            raise RuntimeError(
                "no %s - run python3 mcp/build_font_metrics.py. The fit gate "
                "will not fall back to a guess: a made-up width is how a "
                "customer ends up holding vinyl that does not fit his boat."
                % METRICS_F)
        _MET = json.loads(METRICS_F.read_text())
    return _MET


def width_in(name, font, height_in):
    """Width of this lettering, in inches, at that cap height.

    Returns (width, unsupported_characters). Unsupported characters are
    REPORTED rather than counted as zero width - treating them as zero is how
    a 20-inch name is quoted at 14 inches.
    """
    m = metrics()["fonts"].get(font)
    if not m:
        raise KeyError("no metrics for %r - the ten faces are %s"
                       % (font, ", ".join(sorted(metrics()["fonts"]))))
    total, missing = 0, []
    for ch in name:
        a = m["advance"].get(ch)
        if a is None:
            missing.append(ch)
        else:
            total += a
    # advance units -> em -> inches. cap_ratio converts a cap height, which is
    # what "3 inch letters" means and what the states legislate, into an em.
    em_in = height_in / m["cap_ratio"]
    return (total / m["upm"]) * em_in, sorted(set(missing))


def fit_gate(name, font="Arial Bold", transom_in=None, heights=HEIGHTS_IN):
    """Will it fit, and how tall can it go?

    transom_in is the flat run the owner says he has above the waterline. With
    no transom given this still answers the useful half - how wide it comes out
    at each height the shop sells.
    """
    name = (name or "").strip()
    if not name:
        return {"verdict": "fail", "reasons": ["No name given."]}
    try:
        widths, missing = {}, []
        for h in heights:
            w, miss = width_in(name, font, h)
            widths[h] = _r1(w)
            missing = miss
    except KeyError as e:
        return {"verdict": "unknown_font", "reasons": [str(e)]}

    out = {"font": font, "name": name,
           "widths_in": widths,
           "error_pct": FIT_ERROR_PCT,
           "unsupported": missing,
           "reasons": []}

    if missing:
        out["reasons"].append(
            "We cannot cut %s in this face, so the width below leaves it out. "
            "Ask before you order." % " ".join(repr(c) for c in missing))

    if transom_in is None:
        out["verdict"] = "measured"
        out["best_height"] = max(heights)
        out["reasons"].append(
            'At %d" tall it finishes about %s" wide, give or take %.1f%%. '
            "Measure the flat run above your waterline before you order."
            % (max(heights), _inch(widths[max(heights)]), FIT_ERROR_PCT))
        return out

    usable = transom_in * COMFORT
    fits = {h: widths[h] <= usable for h in heights}
    out["fits"] = fits
    out["transom_in"] = transom_in
    out["usable_in"] = _r1(usable)

    ok = [h for h in heights if fits[h]]
    if not ok:
        out["verdict"] = "too_wide"
        out["best_height"] = None
        out["reasons"].append(
            'This one does not fit. Even at %d" tall it runs about %s" wide '
            'and you have %s" of flat run to work with. Shorter name, or we '
            "split it over two lines."
            % (min(heights), _inch(widths[min(heights)]), _inch(transom_in)))
        return out

    best = max(ok)
    out["best_height"] = best
    if best == max(heights):
        out["verdict"] = "fits"
        out["reasons"].append(
            'Fits at every height we cut. At %d" tall it is about %s" wide on '
            'a %s" run.' % (best, _inch(widths[best]), _inch(transom_in)))
    else:
        out["verdict"] = "height_capped"
        out["reasons"].append(
            'Fits up to %d" tall - about %s" wide. At %d" it would run %s" '
            'and that is more than your %s" of flat run.'
            % (best, _inch(widths[best]), best + 1,
               _inch(widths[best + 1]), _inch(transom_in)))
    return out


# Registration numbers are not a style choice. 33 CFR 173.27 requires plain
# block characters at least 3 inches tall, which is why the catalog carries a
# block_legal flag per face and why this is a gate and not a suggestion.
def registration_gate(number, font, height_in):
    """Is this a legal registration-number set?"""
    reasons, ok = [], True
    if height_in < 3:
        ok = False
        reasons.append('Registration numbers have to be at least 3" tall - '
                       "that is federal, not a shop rule (33 CFR 173.27).")
    blk = {f["name"] for f in json.loads(
        (HERE.parent / "public" / "catalog.json").read_text()
    )["options"]["fonts"] if f["block_legal"]}
    if font not in blk:
        ok = False
        reasons.append("%s is not a plain block face, so it cannot be used for "
                       "registration numbers. The block faces are %s."
                       % (font, ", ".join(sorted(blk))))
    if ok:
        reasons.append('Plain block characters at %d" - legal.' % height_in)
    return {"legal": ok, "reasons": reasons}
