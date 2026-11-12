/**
 * The naming engine: the interview, and the ranker that deals a round.
 *
 * This is the part the gates were built for. Everything here is a pure
 * function of (bank, profile) - no model, no randomness beyond an explicit
 * seed, no network - so a round can be reproduced exactly from a session
 * profile, which is the only way a complaint about a round can ever be
 * investigated.
 *
 * THE RULE THAT SHAPES ALL OF IT. A base model can hand someone eight boat
 * names for free. What it cannot do is refuse to show them a name that will
 * not fit their transom, or that they will be spelling out on channel 16 for
 * the next decade, or that four boats at their ramp already carry. So this
 * file is mostly about what NOT to deal, and the spec's line is literal:
 * never return an unfiltered list.
 */
import { radioGate, overuseGate, fitGate } from "./gates.js";

// ---------------------------------------------------------------------------
// The interview
// ---------------------------------------------------------------------------
//
// Seven questions, and only the first is required. Every one of them exists
// because it changes what may be dealt - not to build a profile for its own
// sake. If an answer would not change the round, it is not asked.
export const INTERVIEW = [
  {
    id: "boat",
    required: true,
    ask: "What are we naming? A pontoon, a bass boat, a runabout, a sailboat, "
      + "a kayak - whatever it is in your words.",
    why: "Decides which names fit the boat. 'Dock Rocket (0-5 MPH)' is funny "
      + "on a pontoon and odd on a bass boat.",
  },
  {
    id: "aboard",
    ask: "Who is usually aboard? Grandkids, your wife, your fishing buddies, "
      + "just you?",
    why: "THE most important answer. It sets the ceiling on how blue a name "
      + "can be, and it is the difference between a joke that lands and one "
      + "he has to explain to a six-year-old.",
  },
  {
    id: "vibe",
    ask: "What kind of name do you actually want - deadpan, a pun, something "
      + "absurd, something straight and classy, or the kind they laugh at on "
      + "the dock?",
    why: "The lane. The bank is organised by this and the ranker weights it "
      + "heaviest.",
  },
  {
    id: "transom",
    ask: "Roughly how many inches of flat run do you have above the "
      + "waterline, where the lettering goes? A guess is fine.",
    why: "Excludes names that cannot physically fit, or caps the height. "
      + "Without it we can only tell you the width and let you measure.",
  },
  {
    id: "work",
    ask: "What do you do, or what did you do before you retired?",
    why: "Unlocks the in-joke lanes. A retired foreman gets the corporate "
      + "jokes; they are invisible to everyone else, so they are not dealt "
      + "until this is known.",
  },
  {
    id: "story",
    ask: "Anything behind the boat - how you came by it, what you use it for, "
      + "a story that comes up every time?",
    why: "Feeds the rationale at the reveal, which quotes the customer's own "
      + "words back. A name explained with his story is a name he keeps.",
  },
  {
    id: "port",
    ask: "What lake or port would go under the name, if any?",
    why: "Hailing port line, and it weights the regional lane - the Midwest "
      + "names only land on somebody from here.",
  },
];

// Words people actually use, mapped to the vocabularies. Matched on the raw
// answer, so the customer never has to pick from a list.
const BOAT_WORDS = {
  pontoon: /pontoon|toon|party barge|deck boat/i,
  bass: /bass ?boat|bass\b|tournament/i,
  fishing_boat: /fish|jon ?boat|aluminum|tiller|skiff|walleye|crappie/i,
  sail: /sail|sloop|catamaran|ketch|yawl/i,
  kayak: /kayak|canoe|paddle|row ?boat|dinghy/i,
  jetski: /jet ?ski|waverunner|sea.?doo|pwc/i,
  cruiser: /cruiser|yacht|cabin|liveaboard|trawler/i,
  runabout: /runabout|bowrider|ski ?boat|wakeboard|deck ?boat|speed ?boat/i,
};

const LANE_WORDS = {
  deadpan: /deadpan|dry|flat|understated|straight.?faced|subtle/i,
  pun: /pun|wordplay|play on words|clever|witty/i,
  absurd: /absurd|weird|random|strange|surreal|silly|nonsense|dumb/i,
  sincere: new RegExp("classy|classic|elegant|serious|straight|nice|"
    + "tasteful|pretty|traditional|no joke|not funny", "i"),
  dock: /dock|crude|raunchy|dirty|blue|filthy|rude|drinking|beer|bar/i,
  dark: /dark|horror|spooky|haunted|morbid|creepy|grim/i,
  nerd: /nerd|geek|science|engineer|tech|computer|physics|math/i,
  pontoon_dad: /dad|pontoon|lawn ?chair|cooler|slow|lazy|relax/i,
  regional: /midwest|iowa|minnesota|wisconsin|local|hometown/i,
  brag: /retire|brag|earned|made it|paid off|proud/i,
  ironic: /ironic|irony|sarcas|tongue.in.cheek|opposite/i,
  current: /gen.?z|slang|trendy|tiktok|modern|young/i,
};

// Who is aboard sets the ceiling. This is the single most consequential
// mapping in the file: get it wrong in the permissive direction and the engine
// offers a man naming his grandkids' boat something he has to apologise for.
const CEILING_WORDS = {
  // Children present: clean only, no exceptions.
  clean: new RegExp("\\b(?:grandkid|grand.?child|grandson|granddaughter|kid|"
    + "child|son|daughter|family|church|baby|niece|nephew|school)\\b", "i"),
  // Partner aboard: dock humor is fine, jokes at her expense are not.
  //
  // THE LEADING \b IS NOT DECORATION. Without it, /her\b/ matches inside
  // "brother" - so "me and my brother" set the ceiling to dock and the live
  // engine dealt Alimony, Yes Dear and Ask Her to a man who had just asked
  // for nothing crude. "mother", "father", "other" and "together" did the
  // same. A trailing boundary alone is worse than none, because it looks
  // careful.
  dock: /\b(?:wife|husband|girlfriend|boyfriend|partner|spouse|her|she)\b/i,
  // Just the owner or his friends.
  double: /\b(?:buddies|buddy|friends|boys|guys|alone|just me|myself|crew)\b/i,
};

// Every pattern in the tables above is anchored at a word start. The tables
// are written as plain alternations for readability; this wraps them once, so
// a future addition cannot forget.
function anchored(table) {
  const out = {};
  for (const [k, re] of Object.entries(table)) {
    out[k] = new RegExp("\\b(?:" + re.source + ")", re.flags.includes("i")
      ? "i" : "");
  }
  return out;
}
const BOATS_A = anchored(BOAT_WORDS);
const LANES_A = anchored(LANE_WORDS);

// Negation. "deadpan, nothing crude" matched the dock lane on the word
// "crude" and the live engine dealt him crude names BECAUSE he asked not to
// have them. A clause that starts with a negator says what to avoid, and
// avoiding crudeness also lowers the ceiling - it is a stronger statement
// than any guess from who is aboard.
const NEGATORS = new RegExp(
  "^\\s*(?:but\\s+)?(?:no|not|nothing|none|never|avoid|without|anything"
  + "\\s+but|rather\\s+not|don'?t|less|keep\\s+it\\s+away|skip|minus)\\b",
  "i");
const CRUDE_WORDS = /\b(?:crude|dirty|blue|raunchy|filthy|rude|vulgar|off.?colou?r|dock)\b/i;

function clauses(text) {
  return String(text || "").split(/[,;.]|\bbut\b|\band\b/i)
    .map((c) => c.trim()).filter(Boolean);
}

export function profileFrom(answers) {
  const a = Object.fromEntries(
    Object.entries(answers || {}).map(([k, v]) => [k, String(v || "").trim()]));

  const boat_types = Object.entries(BOATS_A)
    .filter(([, re]) => re.test(a.boat || "")).map(([k]) => k);

  // Read the vibe answer clause by clause so a negated clause subtracts
  // instead of adding.
  const wanted = new Set(), avoided = new Set();
  let refused_crude = false;
  for (const c of clauses(a.vibe)) {
    const neg = NEGATORS.test(c);
    for (const [k, re] of Object.entries(LANES_A)) {
      if (re.test(c)) (neg ? avoided : wanted).add(k);
    }
    if (neg && CRUDE_WORDS.test(c)) refused_crude = true;
  }
  for (const k of avoided) wanted.delete(k);
  const lanes = [...wanted];

  // Ceiling: default to CLEAN when nobody said. Defaulting the other way puts
  // the burden of the mistake on the customer, and he is the one whose transom
  // it is.
  let ceiling = "clean";
  const aboard = a.aboard || "";
  if (refused_crude) {
    // He said it in his own words. Nothing about who is aboard overrides a
    // customer telling us plainly what he does not want.
    ceiling = "clean";
  } else if (CEILING_WORDS.clean.test(aboard)) {
    ceiling = "clean";
  } else if (CEILING_WORDS.double.test(aboard)) {
    ceiling = "double";
  } else if (CEILING_WORDS.dock.test(aboard)) {
    ceiling = "dock";
  } else if (!refused_crude && wanted.has("dock")) {
    // He asked for it in the vibe answer even though he did not say who is
    // aboard. That is consent to dock humor, not to a double entendre.
    ceiling = "dock";
  }

  const tm = (a.transom || "").match(/(\d{1,3})(\.\d+)?/);
  const transom_in = tm ? parseFloat(tm[1] + (tm[2] || "")) : null;

  return {
    boat_raw: a.boat || null,
    boat_types,
    lanes,
    ceiling,
    transom_in: transom_in && transom_in >= 6 && transom_in <= 400
      ? transom_in : null,
    work: a.work || null,
    story: a.story || null,
    port: a.port || null,
    aboard_raw: aboard || null,
    // Only true if the customer asked for the common names by name.
    // Also clause-aware: "nothing common" is not a request for common names.
    wants_popular: clauses(a.vibe).some(
      (c) => !NEGATORS.test(c)
        && /\b(?:popular|common|classic|well.?known|most ?used)\b/i.test(c)),
    avoided_lanes: [...avoided],
    refused_crude,
    // The in-group lanes stay shut until the interview proves membership.
    in_group: !!(a.work || "").trim(),
    answered: Object.keys(a).filter((k) => a[k]),
  };
}

export function missingQuestions(profile, answers) {
  const have = new Set(Object.keys(answers || {}).filter(
    (k) => String((answers || {})[k] || "").trim()));
  return INTERVIEW.filter((q) => !have.has(q.id));
}

// ---------------------------------------------------------------------------
// The ranker
// ---------------------------------------------------------------------------

const LEVEL_RANK = { clean: 0, dock: 1, double: 2 };

// Lanes with a flavour strong enough that getting one you did not ask for is
// jarring rather than a bonus. "Mortality Barge" is clean, genuinely deadpan,
// and was the top pick for a man naming the boat his grandchildren ride in -
// because the deadpan hit scored and the dark lane cost nothing. A lane the
// customer did not ask for is now a penalty when the lane is this loud.
const STRONG_LANES = new Set(["dark", "dock", "current", "regional", "nerd",
                              "brag", "sincere", "absurd"]);

/**
 * Why a name is not being dealt. Returned rather than silently dropped,
 * because "we have 1,089 names and showed you 8" is only defensible if the
 * other 1,081 can be accounted for.
 */
// WHICH in-group? The pj mechanism deliberately covers three kinds of
// in-joke - a trade, a region, a cohort - and the first version of the reveal
// assumed it was always the customer's trade. So "Limit Out", which is angler
// jargon, came back described as "an in-joke for I run a small HVAC company".
// Wrong, and wrong in the way that tells a customer the whole thing is
// generated.
//
// This returns the evidence that the customer is IN the group, or null. It is
// used twice: to decide whether an in-joke may be dealt at all, and to name
// the group correctly when explaining it.
export function inGroupEvidence(n, profile) {
  const themes = n.themes || [];
  const lanes = n.style_lanes || [];
  if (themes.includes("fishing")) {
    const fishy = (profile.boat_types || []).some(
      (b) => b === "bass" || b === "fishing_boat");
    return fishy ? { group: "anybody who fishes", from: "boat" } : null;
  }
  if (themes.includes("region") || lanes.includes("regional")) {
    return profile.port
      ? { group: "people from around here", from: "port" } : null;
  }
  if (profile.work) {
    return { group: `"${profile.work}"`, from: "work" };
  }
  return null;
}

function excludeReason(n, profile, radio, fit) {
  if (!radio.dealable) {
    return "radio: " + (radio.reasons[0] || "unusable on a radio");
  }
  const lvl = LEVEL_RANK[n.humor_level] ?? 0;
  if (lvl > (LEVEL_RANK[profile.ceiling] ?? 0)) {
    return profile.ceiling === "clean"
      ? "not clean enough for who is aboard"
      : "cruder than the room allows";
  }
  // An in-group joke lands on nobody outside the group. Dealing one to a
  // stranger is not a risk, it is a wasted slot. Which group matters: a
  // fishing in-joke is unlocked by the boat, a regional one by the port, a
  // trade one by the job - not any of them by any of the others.
  if (n.mechanism_code === "pj" && !inGroupEvidence(n, profile)) {
    return "an in-joke for a group we have no sign he is in";
  }
  if (fit && fit.verdict === "too_wide") {
    return "will not fit the transom at any height we cut";
  }
  // An avoided lane is an exclusion, not a penalty. He did not say he was
  // lukewarm about puns, he said not puns.
  const avoided = (profile.avoided_lanes || [])
    .filter((l) => (n.style_lanes || []).includes(l));
  if (avoided.length) {
    return "the " + avoided[0] + " lane, which he asked us to leave out";
  }
  return null;
}

function scoreName(n, profile, radio, fit) {
  let s = 0;
  const lanes = n.style_lanes || [];

  // The lane is what the customer actually asked for, so it dominates.
  if (profile.lanes.length) {
    const hits = lanes.filter((l) => profile.lanes.includes(l)).length;
    s += hits * 40;
    if (!hits) s -= 25;
    const unasked = lanes.filter(
      (l) => STRONG_LANES.has(l) && !profile.lanes.includes(l)).length;
    s -= unasked * 22;
  }

  // Boat type: a match helps, a mismatch hurts, and an empty list is neutral
  // because most names suit any boat.
  const bt = n.boat_types || [];
  if (bt.length && profile.boat_types.length) {
    s += bt.some((b) => profile.boat_types.includes(b)) ? 25 : -30;
  }

  // Themes drawn out of the customer's own words.
  const text = [profile.work, profile.story, profile.aboard_raw, profile.port]
    .filter(Boolean).join(" ").toLowerCase();
  if (text) {
    for (const t of (n.themes || [])) {
      if (text.includes(t.replace(/_/g, " "))) s += 8;
    }
  }
  if (profile.port && (n.themes || []).includes("region")) s += 10;

  // The radio score is already 1-100 and already means what we want it to.
  s += radio.score * 0.25;
  if (radio.verdict === "clear") s += 10;
  if (radio.spell_out) s -= 15;

  // Fit: prefer a name that can be cut tall. Lettering that only works at
  // three inches is lettering nobody can read from another boat.
  if (fit && fit.best_height) s += (fit.best_height - 3) * 6;

  // Overuse. Tier 1 is handled as an exclusion from top picks below; this is
  // the nudge that keeps tier 2 out of the first slots.
  s -= (n.overuse_tier || 0) * 18;

  // A shorter name is easier to live with on a transom and on a radio.
  s -= Math.max(0, (n.char_count || 0) - 16) * 1.2;
  return s;
}

/** Deterministic shuffle, so a round is reproducible from its seed. */
function seeded(seed) {
  let x = 0;
  for (const c of String(seed)) x = (x * 31 + c.charCodeAt(0)) >>> 0;
  return () => {
    x ^= x << 13; x >>>= 0;
    x ^= x >> 17;
    x ^= x << 5; x >>>= 0;
    return x / 4294967296;
  };
}

/**
 * Deal a round.
 *
 * opts.size        how many names (6-8 per spec)
 * opts.exclude     names already shown or killed
 * opts.killedMechs mechanisms the customer has rejected this session
 * opts.seed        for reproducibility
 */
export function dealRound(bank, profile, opts = {}) {
  const size = Math.max(1, Math.min(8, opts.size || 8));
  const exclude = new Set((opts.exclude || []).map((s) => String(s).toLowerCase()));
  const killed = new Set(opts.killedMechs || []);
  const font = opts.font || "Arial Bold";

  const scored = [];
  const rejected = { radio: 0, level: 0, in_joke: 0, fit: 0, tier1: 0,
                     avoided_lane: 0, killed_mechanism: 0, already_seen: 0 };

  for (const n of bank) {
    if (exclude.has(n.name.toLowerCase())) { rejected.already_seen++; continue; }
    const radio = radioGate(n.name);
    const fit = profile.transom_in
      ? fitGate(n.name, font, profile.transom_in) : null;

    const why = excludeReason(n, profile, radio, fit);
    if (why) {
      if (why.startsWith("radio")) rejected.radio++;
      else if (why.includes("clean") || why.includes("cruder")) rejected.level++;
      else if (why.includes("in-joke")) rejected.in_joke++;
      else if (why.includes("leave out")) rejected.avoided_lane++;
      else rejected.fit++;
      continue;
    }
    // A mechanism the customer has already rejected does not come back in a
    // different costume. This is the single clearest signal a session gives.
    if (killed.has(n.mechanism_code)) { rejected.killed_mechanism++; continue; }
    // Tier-1 cliches are out of the picks unless he asked for popular names.
    if (n.overuse_tier === 1 && !profile.wants_popular) {
      rejected.tier1++; continue;
    }
    scored.push({ n, radio, fit, score: scoreName(n, profile, radio, fit) });
  }

  // Tie-break on a seeded hash of the name, NOT alphabetically. Sorting ties
  // by name produced rounds that read "Actual In, Airman, Ails Sail, Alder &
  // Oak, Alimony, Amicable, Ask Her" - which looks exactly like a canned list
  // read off the top of a file, because it is. Still deterministic for a given
  // seed, so a round can be reproduced from its session.
  const jitter = {};
  const jrnd = seeded(opts.seed || "round");
  for (const c of scored) jitter[c.n.name] = jrnd();
  scored.sort((a, b) => b.score - a.score
    || jitter[a.n.name] - jitter[b.n.name]);

  // Diversity. A round of eight homophone puns reads as one joke told eight
  // times, and the customer concludes the bank is thin. At most two per
  // mechanism and two per category, relaxed only if that cannot fill a round.
  const picked = [];
  const perMech = {}, perCat = {}, perTheme = {};
  for (const pass of [1, 2, 3]) {
    const mechCap = pass === 1 ? 2 : pass === 2 ? 3 : 99;
    const catCap = pass === 1 ? 2 : pass === 2 ? 3 : 99;
    // Theme matters as much as mechanism and category, and it was missing.
    // The dock lane spans divorce, money and marriage, which are three
    // separate categories - so a round came out as Alimony, Alimony Alley,
    // Exhibit B, Amicable, Ask Her: eight ways of saying "my ex". Tonally one
    // note, and not what a man with his buddies aboard asked for.
    const themeCap = pass === 1 ? 3 : pass === 2 ? 4 : 99;
    for (const c of scored) {
      if (picked.length >= size) break;
      if (picked.includes(c)) continue;
      const m = c.n.mechanism_code || "?";
      const cat = (c.n.categories || ["?"])[0];
      const themes = (c.n.themes || []);
      if ((perMech[m] || 0) >= mechCap) continue;
      if ((perCat[cat] || 0) >= catCap) continue;
      if (themes.some((t) => (perTheme[t] || 0) >= themeCap)) continue;
      perMech[m] = (perMech[m] || 0) + 1;
      perCat[cat] = (perCat[cat] || 0) + 1;
      for (const t of themes) perTheme[t] = (perTheme[t] || 0) + 1;
      picked.push(c);
    }
    if (picked.length >= size) break;
  }
  return {
    names: picked.map((c) => ({
      name: c.n.name,
      why_it_might_work: laneWords(c.n, profile),
      radio: { verdict: c.radio.verdict, readback: c.radio.readback,
               will_spell_it: c.radio.spell_out },
      fit: c.fit
        ? { verdict: c.fit.verdict, tallest_that_fits: c.fit.best_height,
            widths_in: c.fit.widths_in }
        : { widths_in: null,
            note: "Give us the flat run and we will tell you if it fits." },
      how_common: overuseGate(c.n.name).tier,
      lanes: c.n.style_lanes, mechanism: c.n.humor_mechanism,
      level: c.n.humor_level,
      source: "bank",
    })),
    // Accountability: 1,089 names in, eight out, and here is where the rest
    // went. Without this the engine is a black box asking to be trusted.
    considered: bank.length,
    eligible: scored.length,
    rejected,
    riff_slots: Math.floor(size / 3),   // spec: riffs are at most a third
    seed: String(opts.seed || "round"),
  };
}

function laneWords(n, profile) {
  const bits = [];
  const hit = (n.style_lanes || []).filter((l) => profile.lanes.includes(l));
  if (hit.length) bits.push(`${hit.join(" and ")} - what you asked for`);
  const bt = (n.boat_types || []).filter((b) => profile.boat_types.includes(b));
  if (bt.length) bits.push(`made for a ${bt[0].replace(/_/g, " ")}`);
  if (n.overuse_tier === 2) bits.push("common, but not worn out");
  if (!bits.length) bits.push(n.humor_mechanism);
  return bits.join("; ");
}


// ---------------------------------------------------------------------------
// The tournament
// ---------------------------------------------------------------------------
//
// Round 1 deals eight. After that it is rounds of four, because four is the
// most a person will actually compare rather than skim - and because a vote
// between four is a decision, where a vote between eight is a shortlist.
//
// What a vote is FOR is the mechanism, not the name. A customer who kills
// three homophone puns in a row has told us something far more useful than
// which three names he disliked, and the next round should stop offering puns
// rather than offer three different ones.
export const ROUND_ONE = 8;
export const ROUND_SIZE = 4;
export const FINALISTS = 3;

/**
 * Fold a vote into the session's running state.
 *
 * kept/killed are names. Returns the new state plus the mechanism ledger, and
 * a mechanism is only treated as rejected once it has been killed twice with
 * no keeps - one kill is a name someone did not like, two is a pattern.
 */
export function applyVote(state, bank, kept = [], killed = []) {
  const byName = new Map(bank.map((n) => [n.name.toLowerCase(), n]));
  const s = {
    kept: [...(state.kept || [])],
    killed_names: [...(state.killed_names || [])],
    kept_mechs: { ...(state.kept_mechs || {}) },
    killed_mechs_count: { ...(state.killed_mechs_count || {}) },
  };

  for (const name of kept) {
    const n = byName.get(String(name).toLowerCase());
    if (!n) continue;
    if (!s.kept.includes(n.name)) s.kept.push(n.name);
    const m = n.mechanism_code || "?";
    s.kept_mechs[m] = (s.kept_mechs[m] || 0) + 1;
  }
  for (const name of killed) {
    const n = byName.get(String(name).toLowerCase());
    if (!n) continue;
    if (!s.killed_names.includes(n.name)) s.killed_names.push(n.name);
    const m = n.mechanism_code || "?";
    s.killed_mechs_count[m] = (s.killed_mechs_count[m] || 0) + 1;
  }

  // Two kills and no keeps. One kill is a name he did not like; two with
  // nothing kept is him telling us the joke itself is not landing.
  const rejected = Object.entries(s.killed_mechs_count)
    .filter(([m, c]) => c >= 2 && !(s.kept_mechs[m] > 0))
    .map(([m]) => m);

  // Proven: kept at least twice and kept more than killed. This is what a
  // riff brief is allowed to write in.
  const proven = Object.entries(s.kept_mechs)
    .filter(([m, c]) => c >= 2 && c > (s.killed_mechs_count[m] || 0))
    .map(([m]) => m);

  return { ...s, rejected_mechs: rejected, proven_mechs: proven,
           finalists_ready: s.kept.length >= FINALISTS };
}

// ---------------------------------------------------------------------------
// The reveal
// ---------------------------------------------------------------------------
//
// THE ONE RULE HERE. The rationale is written from the session profile and
// nothing else. Every clause below is either a fixed phrase or a quotation of
// something the customer actually typed - there is no branch that invents a
// fact about his boat, his family or his job. A reveal that says "perfect for
// your weekends with the grandkids" to a man who never mentioned grandchildren
// is worse than no rationale at all, because it tells him the whole thing was
// generated.
// How each joke is built, in words a customer would use. The reveal needs
// this because the other clauses - the lane he asked for, who is aboard - are
// the same for all three finalists, so without it all three reasons read
// identically and the whole thing looks generated.
const MECHANISM_PHRASE = {
  hp: "it sounds like something else entirely",
  pm: "two words jammed into one",
  tt: "a line everybody knows, bent",
  dp: "it never raises its voice, which is the joke",
  dm: "it means two things at once, and both are true on a boat",
  ba: "the letters stand for something",
  pj: "an in-joke",
  an: "the letters rearrange into something else",
  lt: "the joke is that it is simply, boringly true",
  md: "it sends you one way and lands somewhere else",
  sincere: "no joke in it at all - it just reads well on a transom",
};

// "the a 22 foot pontoon" - a leading article has to come off before the
// heading puts one in front of it.
export function bareBoat(raw) {
  return String(raw || "").replace(/^\s*(?:a|an|the|my|our)\s+/i, "").trim();
}

// Boat types in the words a customer uses. "it is a bass name" reads wrong.
const BOAT_LABEL = {
  pontoon: "pontoon", bass: "bass boat", fishing_boat: "fishing boat",
  runabout: "runabout", cruiser: "cruiser", sail: "sailboat",
  kayak: "kayak or canoe", jetski: "jet ski",
};

export function rationale(n, profile, radio, fit) {
  // At most three clauses. The spec asks for a one-line rationale, and the
  // first version ran to five semicolons - "You asked for deadpan, and this
  // is that; it is a pontoon name and you told us X; it stays clean, which
  // matters with Y aboard; and it never raises its voice; it reads as a boat
  // ownership name." Nobody reads that as a reason. They read it as output.
  const bits = [];

  // 1. What he asked for.
  const lanes = (n.style_lanes || []).filter((l) => profile.lanes.includes(l));
  if (lanes.length) {
    bits.push(`You asked for ${lanes.join(" and ")}, and this is that`);
  }

  // 2. The most specific thing he told us that this name actually answers.
  //    One of these, in order of how particular it is to him.
  const bt = (n.boat_types || []).filter(
    (b) => profile.boat_types.includes(b));
  let saidInJoke = false;
  const grp = n.mechanism_code === "pj" ? inGroupEvidence(n, profile) : null;
  if (grp) {
    saidInJoke = true;
    bits.push(`it is an in-joke for ${grp.group}, so most people will not `
      + "get it - which is part of the point");
  } else if (profile.port && (n.themes || []).includes("region")) {
    bits.push(`it reads local, and you are out of ${profile.port}`);
  } else if (bt.length && profile.boat_raw) {
    bits.push(`it is a ${BOAT_LABEL[bt[0]] || bt[0]} name, and you told us `
      + `"${profile.boat_raw}"`);
  } else if (profile.ceiling === "clean" && profile.aboard_raw
             && CEILING_WORDS.clean.test(profile.aboard_raw)) {
    // Only when who is aboard is WHY it has to be clean. For a man whose
    // answer was "my buddies", "it stays clean" is not a selling point.
    bits.push(`it stays clean, which matters with "${profile.aboard_raw}" `
      + "aboard");
  }

  // 3. One fact true of this name and no other, in order of how specific it
  //    is. Every branch is read off the name's own row or its gate result -
  //    none of it is a guess about the customer.
  if (n.note) {
    bits.push(n.note.replace(/\.$/, "")
      .replace(/^([A-Z])/, (m) => m.toLowerCase()));
  } else if (radio && radio.spell_out) {
    bits.push("you will be spelling it out on the radio, which some people "
      + "like and some people hate");
  } else if (radio && radio.visual_only) {
    bits.push("the punctuation is the punchline, so it only really works "
      + "written down");
  } else if (radio && radio.verdict === "mouthful") {
    bits.push("it is a long one to say, and worth it");
  } else if (MECHANISM_PHRASE[n.mechanism_code] && !saidInJoke) {
    // Skipped when clause 2 already called it an in-joke, which produced
    // "it is an in-joke for X; an in-joke."
    bits.push(MECHANISM_PHRASE[n.mechanism_code]);
  } else if (fit && fit.best_height) {
    // A real per-name fact for the cases where the mechanism is shared by
    // everything else in the lane - three in-jokes in a nerd round otherwise
    // came back with word-for-word identical reasons.
    bits.push(`it will cut at ${fit.best_height}" tall on what you have`);
  } else if ((n.themes || []).length) {
    bits.push(`it reads as a ${(n.themes || [])[0].replace(/_/g, " ")} name`);
  }

  if (!bits.length) {
    // The honest floor: how the joke works, rather than an invented reason.
    bits.push(`It works by ${n.humor_mechanism}`);
  }
  return bits.slice(0, 3).join("; ") + ".";
}

/** Gate results in plain words, for the reveal. Spec section 6. */
export function gateSummary(radio, fit, over) {
  const out = [];
  out.push({
    clear: "Clear on the radio",
    sayable: "You will say it twice the first time, then never again",
    mouthful: "A long one on channel 16",
    spell_it: "You will be spelling this one out",
    fail: "Not usable on a radio",
  }[radio.verdict] || radio.verdict);

  if (fit && fit.best_height) {
    out.push(`Fits at ${fit.best_height}" tall`);
  } else if (fit && fit.widths_in) {
    out.push(`About ${fit.widths_in[4]}" wide at 4"`);
  }
  out.push(over.tier === 1 ? "One in every marina"
    : over.tier === 2 ? "Common, but not worn out"
    : "Not one we see often");
  if (radio.visual_only) out.push("The joke needs to be read, not heard");
  return out;
}
