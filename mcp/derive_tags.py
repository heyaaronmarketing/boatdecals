#!/usr/bin/env python3
"""Derive style_lanes, themes, boat_types and overuse_tier for every name.

Called by build_bank.py, after the hand-written mechanism and level tags are
merged. See the long note in taxonomy.py for why these four are derived while
humor_mechanism was tagged by hand: the site's categories are its own lanes
("Pick a vibe"), and a keyword rule that reads "walleye" will still be right
for names nobody has written yet.

Hand-written exceptions go in mcp/tags/overrides.tsv:

    name<TAB>field<TAB>value[,value]<TAB>why

and are applied last. Every override is counted and reported, so if the rules
ever need dozens of them that is a signal the rules are wrong, not a thing to
quietly accumulate.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from taxonomy import (BOAT_TYPES, CATEGORY_LANES, LANES, THEMES)  # noqa: E402
import gates as G  # noqa: E402

OVERRIDES = HERE / "tags" / "overrides.tsv"

# Theme keywords. Matched on word boundaries against the lowercased name, so
# "Carp Diem" does not pick up "car".
THEME_WORDS = {
    "money": r"money|debt|loan|payment|mortgage|apr|credit|cash|broke|price|dollar|"
             r"paid|owe|bank|tax|refund|bonus|raise|fund|invoice|escrow|"
             r"alimony|interest|overdraft|budget|afford|expensive|cheap|"
             r"liquidat|asset|worth|inherit|repo|collateral|deductible|"
             r"severance|pension|wage|salary|fee|rent|bill",
    "fishing": r"fish|bass|walleye|crappie|carp|cod|trout|catfish|minnow|"
               r"lure|bait|hook|reel|rod|tackle|jig|bobber|stringer|limit|"
               r"skunked|trolling|angler|muskie|bluegill|sunfish|drag",
    "retirement": r"retire|pension|65|social security|golden year|medicare|"
                  r"clocked out|no alarm|gold watch|out to pasture|"
                  r"done working|last paycheck|senior",
    "drinking": r"beer|rum|booze|sober|drunk|koozie|coozie|cooler|happy hour|"
                r"last call|painkiller|liquid lunch|shipfaced|ship faced|"
                r"one more round|cocktail|stormy|aquaholic|aqua-holic|"
                r"legal limit|designated driver|pour decision",
    "marriage": r"wife|husband|marri|spouse|anniversar|honeymoon|ring|"
                r"yes dear|her idea|his idea|couples|prenup|vow|dear",
    "divorce": r"divorc|alimony|custody|settlement|decree|ex-|her half|"
               r"she got|single again|prenup|lawyer|court|separat|split",
    "work": r"office|boss|meeting|email|work|job|overtime|kpi|roi|synergy|"
            r"deliverable|stakeholder|offsite|pto|zoom|quitter|shift|"
            r"clock|employ|career|hr\b",
    "family": r"grandkid|grandma|grandpa|dad|mom|kid|son|daughter|cousin|"
              r"uncle|family|baby|child",
    "food": r"taco|pizza|nacho|cheese|brat|burrito|lasagna|casserole|snack|"
            r"soup|sandwich|jerky|corn|potato|salad|hotdish|gravy|sauce|"
            r"pickle|cookie|dough|breakfast|lunch|supper|marinara|mayonnaise|"
            r"ham\b|bologna|sushi|chop|tea|cream",
    "death": r"haunt|ghost|dead|death|grave|mortal|cursed|doom|undertow|"
             r"sunken|drown|coffin|reaper|ashes|memento|rip\b|rest in|"
             r"final|tetanus|scream|horror|monster|creature",
    "nature": r"heron|wren|kestrel|kingfisher|nightjar|juniper|cedar|oak|"
              r"alder|pine|tallgrass|bluestem|driftwood|wild rice|horizon|"
              r"sunset|first light|last light|north star|lodestar|moon|"
              r"luna|prairie|harbor|tide|windward|vesper",
    "speed": r"fast|rocket|zoom|speed|velocity|mph|quick|rush|hurry",
    "slow": r"slow|lazy|drift|nap|mild|idle|5 mph|chill|no wake|dawdl",
    "tech": r"ctrl|alt|exe|404|null|beta|patch|version|respawn|bug|server|"
            r"bluetooth|wifi|online|offline|bandwidth|loading|password|"
            r"error|reboot|pixel|resolution|quantum|hypothes|peer review|"
            r"open source|side quest|extra life|plot armor",
    "region": r"iowa|midwest|minnesota|wisconsin|sconnie|nort|ope|hotdish|"
              r"lutefisk|cheese head|hawkeye|don'tcha|supper club|"
              r"duck duck|pop not soda|bean walker|detasseler|gray duck",
    "laziness": r"nap|lazy|recliner|sit|couch|porch|do nothing|quit|"
                r"not working|no plan|snooze",
    "boat_ownership": r"boat|pontoon|hull|transom|slip|marina|dock|trailer|"
                      r"motor|prop|anchor|keel|deck|barge|vessel|yacht|"
                      r"toon\b|canoe|kayak|sail|mast|jib\b|oar\b|row|"
                      r"aft\b|stern|bow\b|port\b|starboard|helm|rudder|"
                      r"wake|bilge|cleat|fender|buoy|regatta|moor|berth|"
                      r"launch|float|draft|knot\b|rig\b|hailing",
    "weather": r"storm|wind chill|tornado|fog|calm|lake effect|ice out|"
               r"sun's out|weather|rain|frozen",
    "animals": r"goose|geese|duck|raccoon|possum|beaver|lizard|goblin|dog|"
               r"horse|bird|gull|heron|clown|turtle|snake|deer",
    "law": r"legal|cfr|citation|court|exhibit|terms|warrant|liab|"
           r"guilty|statute|regulat|permit|ordinance|subpoena|redacted|"
           r"petition|mediation|decree",
}

BOAT_WORDS = {
    "pontoon": r"pontoon|toon\b|party barge|barge|deck boat|floating patio|"
               r"floating deck|porch with a motor|lazy susan|dadmiral",
    "bass": r"bass\b|crappie|walleye|livewell|tournament|bass boat",
    "fishing_boat": r"fish|lure|bait|hook|reel|rod|tackle|jig|stringer|"
                    r"minnow|trolling|angler",
    "sail": r"sail|mast|jib|windward|keel|tack|boom|halyard|spinnaker|"
            r"evensong|lodestar|vesper",
    "kayak": r"kayak|canoe|paddle|oar\b|rowing|row-|rowboat",
    "jetski": r"jet ski|jetski|waverunner|sea-doo|seadoo|rocket",
    "cruiser": r"yacht|cruiser|cabin|galley|flybridge|liveaboard",
    "runabout": r"runabout|bowrider|ski boat|wakeboard|tow",
}

# Categories that pin a boat type regardless of wording: a name from the
# pontoon lane belongs on a pontoon even when it never says so.
CATEGORY_BOATS = {
    "pontoon": ["pontoon"],
    "fishing": ["fishing_boat", "bass"],
    "funny:Fishing, specifically": ["fishing_boat", "bass"],
    "classy": ["sail", "cruiser"],
}


# Every pattern is anchored at a word START. Without this the matching is
# substring matching, and substring matching on a 20-word list is a steady
# supply of wrong answers: "rent" inside "Current Affairs" tagged it as a money
# name, "fee" inside "Coffee", "bill" inside "Billboard". A trailing boundary
# is deliberately NOT added, so prefixes like "divorc" still reach "divorced"
# and "marri" still reaches "marriage".
_ANCHORED = {}


def _match(pattern, text):
    rx = _ANCHORED.get(pattern)
    if rx is None:
        rx = _ANCHORED[pattern] = re.compile(r"\b(?:" + pattern + ")")
    return rx.search(text) is not None


def load_overrides():
    """Hand-written exceptions. Returns (by_name, problems)."""
    out, problems = {}, []
    if not OVERRIDES.exists():
        return out, problems
    valid = {"style_lanes": set(LANES), "themes": set(THEMES),
             "boat_types": set(BOAT_TYPES), "overuse_tier": {"0", "1", "2"}}
    for lineno, raw in enumerate(
            OVERRIDES.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) < 3:
            problems.append("overrides.tsv:%d needs name<TAB>field<TAB>value"
                            % lineno)
            continue
        name, field, value = p[0].strip(), p[1].strip(), p[2].strip()
        if field not in valid:
            problems.append("overrides.tsv:%d unknown field %r (allowed: %s)"
                            % (lineno, field, " ".join(sorted(valid))))
            continue
        vals = [v.strip() for v in value.split(",") if v.strip()]
        bad = [v for v in vals if v not in valid[field]]
        if bad:
            problems.append("overrides.tsv:%d %s is not in the %s vocabulary"
                            % (lineno, bad, field))
            continue
        out.setdefault(name.lower(), {})[field] = (
            int(vals[0]) if field == "overuse_tier" else vals)
    return out, problems


def derive(names):
    """Fill the four derived fields in place. Returns (stats, problems)."""
    overrides, problems = load_overrides()
    seen_overrides = set()
    stats = {"overridden": 0, "no_theme": 0, "any_boat": 0}

    for n in names:
        low = n["name"].lower()
        cats = n["categories"]

        # --- lanes, from the category the site itself calls a vibe ---------
        lanes = []
        for c in cats:
            for l in CATEGORY_LANES.get(c, []):
                if l not in lanes:
                    lanes.append(l)
        # Mechanism refines it. A sincere name is in the sincere lane whatever
        # category it sits in, and a deadpan mechanism is a deadpan name even
        # inside the money or the horror lane.
        mech = n.get("mechanism_code")
        if mech == "sincere":
            lanes = ["sincere"]
        elif mech == "dp" and "deadpan" not in lanes:
            lanes.append("deadpan")
        elif mech in ("hp", "pm", "an") and "pun" not in lanes:
            lanes.append("pun")
        # Anything graded double entendre belongs in the dock lane, because
        # that is the lane a user picks when he is telling us who is aboard.
        if n.get("level_code") == "x" and "dock" not in lanes:
            lanes.append("dock")
        if not lanes:
            lanes = ["absurd"]
        n["style_lanes"] = lanes

        # --- themes -------------------------------------------------------
        themes = sorted(t for t, pat in THEME_WORDS.items() if _match(pat, low))
        # The category carries a theme the wording may not: every name in the
        # divorce lane is about divorce even when it only says "Amicable".
        for c, extra in (("payments", "money"), ("retirement", "retirement"),
                         ("divorce", "divorce"), ("couples", "marriage"),
                         ("fishing", "fishing"), ("food", "food"),
                         ("corporate", "work"), ("midwest", "region"),
                         ("horror", "death"), ("classy", "nature"),
                         ("nerd", "tech"), ("pontoon", "boat_ownership"),
                         ("funny:The money jokes", "money"),
                         ("funny:Honest about the drinking", "drinking"),
                         ("funny:Retirement bragging", "retirement"),
                         ("funny:Fishing, specifically", "fishing"),
                         ("funny:Marriage commentary (order at your own risk)",
                          "marriage")):
            if c in cats and extra not in themes:
                themes.append(extra)
        n["themes"] = sorted(themes)
        if not themes:
            stats["no_theme"] += 1

        # --- boat types ---------------------------------------------------
        boats = sorted(b for b, pat in BOAT_WORDS.items() if _match(pat, low))
        for c, extra in CATEGORY_BOATS.items():
            if c in cats:
                for e in extra:
                    if e not in boats:
                        boats.append(e)
        n["boat_types"] = sorted(boats)
        if not boats:
            stats["any_boat"] += 1

        # --- overuse tier, from the gate. One source. ---------------------
        n["overuse_tier"] = G.overuse_gate(n["name"])["tier"]

        # --- hand-written exceptions, last --------------------------------
        ov = overrides.get(low)
        if ov:
            seen_overrides.add(low)
            n.update(ov)
            stats["overridden"] += 1

    for key in sorted(set(overrides) - seen_overrides):
        problems.append("overrides.tsv names %r, which is not in the bank"
                        % key)
    return stats, problems
