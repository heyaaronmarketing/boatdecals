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
 * opts.riffs       gated riff rows from submit_riff_candidates
 * opts.proven      mechanisms proven for this lane, from the ledger
 * opts.seed        for reproducibility
 */
export function dealRound(bank, profile, opts = {}) {
  const size = Math.max(1, Math.min(8, opts.size || 8));
  const exclude = new Set((opts.exclude || []).map((s) => String(s).toLowerCase()));
  const killed = new Set(opts.killedMechs || []);
  const font = opts.font || "Arial Bold";
  const riffs = (opts.riffs || []).filter(
    (r) => r && r.name && !exclude.has(r.name.toLowerCase())
           && !killed.has(r.mechanism_code));
  // Riffs are at most a third of a round. The spec's cap, and it is the right
  // one: a riff is a name nobody has read before it was shown, built in one
  // pass from a stranger's words, and the rest of the round is 1,089 names
  // that were read by a human and then measured.
  const riffCap = Math.min(riffs.length, Math.floor(size / 3));
  // Exploration: at most ONE slot for a mechanism the ledger has not proven
  // for this lane - but only once the ledger has proven something, because a
  // cold ledger has proven nothing and capping the round at one name is not
  // caution, it is an empty round. This is a deliberate reading of the spec's
  // "unproven mechanisms are exploration, capped at one slot per round": the
  // cap binds when there is a proven set to fall back on.
  const proven = new Set(opts.proven || []);
  const exploreCap = proven.size ? 1 : Infinity;

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

  // Riffs compete in the same pool rather than being handed a slot. They get
  // a bonus because they are built out of his own words - the dog, the lake,
  // the job - and that is material no bank name can have. They do not get a
  // free pass: a weak riff still loses to a strong bank name, which is the
  // only thing that keeps the riff slots worth having.
  for (const r of riffs) {
    const radio = radioGate(r.name);
    const fit = profile.transom_in
      ? fitGate(r.name, font, profile.transom_in) : null;
    scored.push({ n: r, radio, fit, riff: true,
                  score: scoreName(r, profile, radio, fit) + 30 });
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
  let nRiffs = 0, nExplore = 0;
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
      // The two spec caps are hard and survive every relaxation pass below.
      // The diversity caps are mine and may relax to fill a round; these two
      // may not, which is the difference between a house rule and a rule.
      if (c.riff && nRiffs >= riffCap) continue;
      if (!proven.has(m) && nExplore >= exploreCap) continue;
      if ((perMech[m] || 0) >= mechCap) continue;
      if ((perCat[cat] || 0) >= catCap) continue;
      if (themes.some((t) => (perTheme[t] || 0) >= themeCap)) continue;
      if (c.riff) nRiffs++;
      if (!proven.has(m)) nExplore++;
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
      // The code as well as the English. The host needs it to pass
      // killed_mechanisms back, and the ledger needs it to file the vote.
      mechanism_code: c.n.mechanism_code,
      level: c.n.humor_level,
      source: c.riff ? "riff" : "bank",
    })),
    // Accountability: 1,089 names in, eight out, and here is where the rest
    // went. Without this the engine is a black box asking to be trusted.
    considered: bank.length,
    eligible: scored.length,
    rejected,
    // Spec: riffs are at most a third of a round. This is what is LEFT, so
    // the host knows how many to bother inventing.
    riff_slots: Math.max(0, Math.floor(size / 3) - nRiffs),
    riffs_dealt: nRiffs,
    exploration_slots_used: nExplore,
    exploration_cap: proven.size ? 1 : null,
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

/**
 * The card's heading, counting what is actually on the card.
 *
 * It said "Three names for the 22 foot pontoon" over a card with two names on
 * it, because the heading hardcoded the word while reveal_finalists happily
 * reveals whatever has been kept. The one thing a man forwards to his wife
 * should not miscount itself.
 */
export function cardHeading(count, boatRaw) {
  const word = ["No", "One name", "Two names", "Three names"][count]
    || count + " names";
  const head = count === 1 ? "One name" : word;
  const boat = bareBoat(boatRaw);
  return head + " for the " + (boat || "boat");
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


// ---------------------------------------------------------------------------
// The performance ledger
// ---------------------------------------------------------------------------
//
// What "proven" means, and why it is a table rather than an opinion.
//
// "Be funny" is not a prompt. The bank is 1,089 names that somebody judged
// funny once, in a room, in advance - which is a hypothesis, not evidence.
// The ledger is the evidence: every name and every mechanism accrues
// exposures, keeps and kills from real sessions, and a mechanism is only
// called proven for a lane once it has been seen enough times to mean
// something.
//
// DECAY IS WHY THERE ARE TWO SETS OF COUNTERS. A lifetime keep-rate barely
// moves: a mechanism that landed all year and stopped landing in October will
// still read as proven in December, which is exactly the failure the spec
// calls out. So the window counters are HALVED at every monthly review after
// the snapshot is taken - an exponential decay with a one-month half-life.
// Proven status is computed from the window; the lifetime counters are kept
// only so the review can show the all-time figure beside the current one.
//
// NOTHING IN THIS TABLE IS PERSONAL. A row is (lane, mechanism, three
// integers). It is never joined to a session, carries no id, no free text and
// no name a customer typed - which is the only reason it is allowed to
// outlive the 30-day session purge. Riff text in particular never reaches it:
// a riff feeds the mechanism's counters and its own words stay in the session
// row that gets deleted. See `ledgerDeltas`.
export const LEDGER = {
  // Spec defaults, owner-tunable. Thirty exposures is roughly four rounds.
  min_exposures: 30,
  // A mechanism with thirty exposures and not one keep is not "top half of a
  // field of one" - it is a mechanism nobody has ever liked. Without this
  // floor, a single eligible mechanism at a 0% keep-rate is its own median
  // and gets called proven.
  min_keep_rate: 0.01,
  half_life_reviews: 1,
};

/**
 * Which lanes a session's evidence is filed under.
 *
 * The question the ledger answers is "does this joke land on people who asked
 * for deadpan", so the key is the lane the CUSTOMER asked for, not the lane
 * the name happens to sit in. A session with no stated lane still has to go
 * somewhere, and "any" is also written on every session so there is always a
 * fallback for a cold lane.
 */
export function laneKeys(profile) {
  const ls = (profile && profile.lanes) || [];
  return [...new Set([...ls, "any"])];
}

/**
 * Proven-for-lane, from ledger rows.
 *
 * rows: [{ kind, lane, key, w_exposures, w_keeps, w_kills }]
 * Returns { proven, exploring, rates, cold } for one lane.
 */
export function provenFor(rows, lane, cfg = LEDGER) {
  const mine = (rows || []).filter(
    (r) => r.kind === "mech" && r.lane === lane);
  const rates = {};
  for (const r of mine) {
    const exp = r.w_exposures || 0;
    rates[r.key] = { exposures: exp, keeps: r.w_keeps || 0,
                     kills: r.w_kills || 0,
                     rate: exp ? (r.w_keeps || 0) / exp : 0 };
  }
  const eligible = Object.entries(rates)
    .filter(([, v]) => v.exposures >= cfg.min_exposures);
  if (!eligible.length) {
    return { proven: [], exploring: Object.keys(rates), rates, cold: true };
  }
  // Top half for the lane, by keep-rate. Half the field is proven by
  // construction, which is the point: proven is relative to what else we
  // have, not an absolute bar nobody clears.
  const sorted = eligible.map(([, v]) => v.rate).sort((a, b) => a - b);
  const mid = sorted.length % 2
    ? sorted[(sorted.length - 1) / 2]
    : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2;
  const proven = eligible
    .filter(([, v]) => v.rate >= mid && v.rate >= cfg.min_keep_rate)
    .map(([k]) => k);
  const exploring = Object.keys(rates).filter((k) => !proven.includes(k));
  return { proven, exploring, rates, cold: false, median_keep_rate: mid };
}

/**
 * The deltas a round or a vote owes the ledger.
 *
 * Returned rather than written here so the engine stays a pure function and
 * the only SQL in the naming engine lives in one place. `names` are the names
 * dealt or voted on; each needs its mechanism, which the caller has from the
 * bank row or the riff row.
 *
 * Riff names are counted under kind "mech" only. Their text is deliberately
 * not filed as a name row: a riff is built out of a customer's dog, his wife
 * or his hometown, and the ledger is the one table here that outlives the
 * 30-day purge.
 */
export function ledgerDeltas(profile, items, field) {
  const lanes = laneKeys(profile);
  const out = [];
  for (const it of items || []) {
    const mech = it.mechanism_code || "?";
    for (const lane of lanes) {
      out.push({ kind: "mech", lane, key: mech, field, n: 1 });
    }
    if (it.source !== "riff" && it.name) {
      out.push({ kind: "name", lane: "any", key: it.name, field, n: 1 });
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// The riff brief
// ---------------------------------------------------------------------------
//
// The host model never free-associates. It gets a brief: the customer's own
// raw material, the mechanisms that have actually been landing in his lane,
// real exemplars of those mechanisms, the house register, and a banned list.
// Then it invents inside those walls and submits through
// submit_riff_candidates, where everything is gated exactly like a bank name
// plus a novelty check.
//
// This is the whole reason the server makes zero LLM calls and is still
// expected to be funnier than a prompt: creativity happens in the host, taste
// is a table, and the gates are the floor.
export const HOUSE_STYLE = {
  register: "Deadpan. The name does not announce that it is a joke, and it "
    + "never explains itself. If it needs a wink it is not the name.",
  double_meanings: "Left unexplained. A double meaning the customer has to "
    + "catch is the one he repeats at the ramp; one that is spelled out is a "
    + "caption.",
  furniture: "Faux-official is the house furniture - 'It remains on file.', "
    + "'(Terms Apply)', 'Pending Review'. Use it dry, never twice in a "
    + "round.",
  length: "Short. Two or three words. It has to be said once on a radio and "
    + "read from another boat.",
  never: [
    "meme-speak, hashtags, emoji, leetspeak, anything with a number for a "
      + "word",
    "deliberate misspelling for the sake of it - the radio gate will kill it "
      + "and the customer will be spelling it out for a decade",
    "explaining the joke in the name",
    "a name built on a word the customer did not give us",
  ],
};

const MEME_SPEAK = [
  "rizz", "sigma", "based", "no cap", "slaps", "lowkey", "vibes only",
  "it's giving", "main character", "era", "unalive", "skibidi", "gyat",
  "fr fr", "ohio", "aura",
];

/** The customer's own raw material, in his words. Nothing inferred. */
export function hooks(profile) {
  const h = {};
  if (profile.boat_raw) h.boat = profile.boat_raw;
  if (profile.port) h.port = profile.port;
  if (profile.work) h.work = profile.work;
  if (profile.story) h.story = profile.story;
  if (profile.aboard_raw) h.aboard = profile.aboard_raw;
  return h;
}

/**
 * Exemplars: real instances of a mechanism, best first.
 *
 * Best means highest keep-rate once there is keep data, and until then the
 * cleanest instances we have - a short name that is clear on a radio and is
 * not one of the names at every ramp. The brief SAYS which of the two it is,
 * because a brief claiming "these are the highest keep-rate names" when
 * nothing has ever been kept is lying to the model, and the model will write
 * it into a rationale.
 */
export function exemplarsFor(bank, mechs, rows, want = 5) {
  const keeps = {};
  for (const r of (rows || [])) {
    if (r.kind === "name" && (r.w_exposures || 0) > 0) {
      keeps[r.key] = (r.w_keeps || 0) / r.w_exposures;
    }
  }
  // KEEP data, not EXPOSURE data. The first version asked whether any name
  // had a row, and live it answered yes within minutes - every name dealt
  // accrues an exposure - so the brief told the model its exemplars were
  // "the highest keep-rate names" while every rate in the table was zero.
  // Forty exposures and no keeps is not a ranking signal, it is a denominator.
  const haveKeepData = Object.values(keeps).some((v) => v > 0);
  const pool = bank.filter((n) => mechs.includes(n.mechanism_code));
  pool.sort((a, b) => {
    const d = (keeps[b.name] || 0) - (keeps[a.name] || 0);
    if (d) return d;
    return (a.overuse_tier || 0) - (b.overuse_tier || 0)
      || (a.char_count || 0) - (b.char_count || 0)
      || a.name.localeCompare(b.name);
  });
  const out = [];
  const per = {};
  for (const n of pool) {
    const m = n.mechanism_code;
    if ((per[m] || 0) >= 2 && out.length >= mechs.length) continue;
    per[m] = (per[m] || 0) + 1;
    out.push({ name: n.name, mechanism: n.humor_mechanism,
               mechanism_code: m,
               keep_rate: keeps[n.name] != null
                 ? Math.round(keeps[n.name] * 100) / 100 : null,
               note: n.note || null });
    if (out.length >= want) break;
  }
  return { exemplars: out,
           chosen_by: haveKeepData
             ? "keep-rate in real sessions"
             : "no keep data for these yet, so these are the cleanest "
               + "instances we have: clear on the radio, short, not one of "
               + "the names at every ramp" };
}

/**
 * Assemble the brief.
 *
 * state is the session's running tournament state (kept/killed mechanisms).
 * rows are the ledger rows. slots is how many riffs the next round can take.
 */
export function riffBrief(bank, profile, state, rows, slots) {
  const lane = (profile.lanes || [])[0] || "any";
  const p = provenFor(rows, lane);
  // A mechanism the customer killed is out of the brief entirely, even if it
  // is the best-performing mechanism we have. He has told us about his own
  // boat; the ledger is about everyone else's.
  const killed = new Set([...(state.rejected_mechs || []),
                          ...Object.keys(state.killed_mechs_count || {})
                            .filter((m) => (state.killed_mechs_count[m] || 0)
                              >= 2 && !(state.kept_mechs || {})[m])]);
  const usable = p.proven.filter((m) => !killed.has(m));
  // One slot, and only one, may try something the ledger has not proven.
  // Exploration is how the ledger ever learns a new mechanism; more than one
  // slot and the round stops being the best we have.
  const explore = p.exploring.filter((m) => !killed.has(m))[0] || null;

  // WHICH mechanisms the exemplars demonstrate. Proven ones when there are
  // any; otherwise the mechanisms that actually exist in his lane, read off
  // the bank. The first version fell back to the ledger's exploring list,
  // which on a genuinely cold ledger is empty - so a brand-new lane got a
  // brief with ZERO exemplars, which teaches the host nothing, which means it
  // free-associates, which is the one thing the brief exists to prevent.
  let demo = usable;
  if (!demo.length) {
    const inLane = {};
    for (const n of bank) {
      if (!(n.style_lanes || []).includes(lane) && lane !== "any") continue;
      if (killed.has(n.mechanism_code)) continue;
      inLane[n.mechanism_code] = (inLane[n.mechanism_code] || 0) + 1;
    }
    demo = Object.entries(inLane).sort((a, b) => b[1] - a[1])
      .slice(0, 3).map(([m]) => m);
  }
  const ex = exemplarsFor(bank, demo, rows);
  return {
    how_to_use: "Invent inside this brief and submit with "
      + "submit_riff_candidates. Everything you send is gated: radio, fit, "
      + "overuse, crudeness against who is aboard, and a novelty check "
      + "against all 1,089 bank names. Failures are dropped, not shown. You "
      + "do not choose the round - the ranker does, from what survives.",
    lane,
    slots_in_the_next_round: slots,
    his_own_words: hooks(profile),
    ceiling: profile.ceiling,
    // Why the ceiling is what it is, not just what it is. Clean is also the
    // DEFAULT when nobody said who is aboard, and a brief that tells the
    // model "children are aboard" when nobody mentioned any is handing it a
    // fact to write into a rationale.
    ceiling_means: profile.ceiling === "clean"
      ? (profile.refused_crude
          ? "Clean, because he asked for nothing crude in those words."
          : profile.aboard_raw
          ? `Clean, because of who is aboard: "${profile.aboard_raw}".`
          : "Clean, because nobody has told us who is usually aboard and "
            + "that is the way to be wrong.")
        + " No double meanings that only work if you are thinking of "
        + "something else."
      : profile.ceiling === "dock"
      ? "Dock humor is fine. Jokes at his partner's expense are not, whether "
        + "or not he named one."
      : "He is on his own or with his friends and asked for it. Still his "
        + "transom, and his family will read it eventually.",
    mechanisms_to_use: usable.map((m) => ({
      code: m, keep_rate: Math.round((p.rates[m].rate || 0) * 100) / 100,
      exposures: p.rates[m].exposures,
      status: "proven for this lane",
    })),
    one_slot_for_something_unproven: explore
      ? { code: explore, status: "exploration - at most one name in the "
            + "round may use it" }
      : p.cold ? { code: null, status: "the whole round is exploration while "
            + "the ledger is cold, so the cap does not bind yet" } : null,
    // On a cold ledger `mechanisms_to_use` is empty, and an empty list is not
    // an instruction. This says what to do instead, in the same breath.
    until_the_ledger_has_data: p.cold || !usable.length
      ? { mechanisms: demo,
          reading: "No evidence yet, so these are simply the mechanisms this "
            + "lane is built out of. Work from the exemplars and the house "
            + "style, not from a keep-rate that does not exist." }
      : null,
    ledger_status: p.cold
      ? "COLD. No mechanism has the " + LEDGER.min_exposures + " exposures "
        + "it takes to call it proven in this lane yet, so nothing below is "
        + "evidence - treat the exemplars as house style and nothing more."
      : "Proven means at least " + LEDGER.min_exposures + " exposures in "
        + "this lane and a keep-rate in the top half of the lane, measured "
        + "on a one-month half-life so a mechanism that stops landing falls "
        + "out.",
    exemplars: ex.exemplars,
    exemplars_chosen_by: ex.chosen_by,
    house_style: HOUSE_STYLE,
    do_not_use: {
      mechanisms_he_killed: [...killed],
      names_already_shown: (state.shown || []).length,
      meme_speak: MEME_SPEAK,
      and: "any Tier-1 name - the ones on a boat at every ramp. The overuse "
        + "gate will reject them anyway.",
    },
    novelty_rule: "A riff that is a near-copy of a bank name is a copy, not "
      + "creativity, and the novelty gate rejects it. Build on HIS words - "
      + "the dog, the job, the lake, the story - not on our names.",
  };
}

// ---------------------------------------------------------------------------
// Gating a riff
// ---------------------------------------------------------------------------
//
// A riff arrives as text from a model with no tags, so it gets the same gates
// a bank name got plus a novelty check, and it gets them here rather than in
// gates.py because riffs only ever exist on the worker - there is no second
// implementation to keep in step.
//
// WHAT THIS CANNOT DO, said plainly: a word list cannot catch a double
// meaning. That is what a double meaning is. So the crude screen below is a
// floor for the overt cases, and the real protection for a man with his
// grandchildren aboard is that the brief states the ceiling, riffs are capped
// at a third of a round, and every riff still has to beat bank names that
// were read by a human before they were banked.
const CRUDE_STEMS = new RegExp(
  "\\b(?:fuck\\w*|shit\\w*|piss\\w*|cunt\\w*|cock|dick\\w*|tits?|titty|"
  + "boob\\w*|arse|ass(?:hole|hat)|bitch\\w*|whore|slut|bastard|wank\\w*|"
  + "bang(?:ing|er)|horny|nude|naked|strip(?:per|ping)|sex\\w*|orgy|"
  + "erect\\w*|hooters|blow ?job|hump(?:ing|er)?|screw(?:ing)?|"
  + "seaman|semen|poop|turd|fart\\w*)\\b", "i");

const MEME_RX = new RegExp("\\b(?:" + MEME_SPEAK.map(
  (m) => m.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/ /g, "\\s+"))
  .join("|") + ")\\b", "i");

/**
 * Gate one riff candidate.
 *
 * Returns { ok: true, row } or { ok: false, reason }. The reason is for the
 * log and the owner, never for the customer: a name shown with an apology is
 * worse than a name never shown.
 */
export function gateRiff(cand, profile, bankNames, deps, opts = {}) {
  const { radioGate, overuseGate, fitGate, noveltyGate } = deps;
  const name = String((cand && cand.name) || "").trim().replace(/\s+/g, " ");
  const mech = String((cand && cand.mechanism) || "").trim().toLowerCase();

  if (!name) return { ok: false, name: "", reason: "empty" };
  if (name.length > 40) {
    return { ok: false, name, reason: "longer than anything we cut" };
  }
  if (!/^[\x20-\x7E\u00C0-\u024F]+$/.test(name)) {
    return { ok: false, name, reason: "characters the cutter has no path for" };
  }
  if (!MECHANISM_PHRASE[mech]) {
    return { ok: false, name,
             reason: `unknown mechanism "${mech}" - one of `
               + Object.keys(MECHANISM_PHRASE).join(", ") };
  }
  if (MEME_RX.test(name)) {
    return { ok: false, name, reason: "meme-speak, which the house style bans "
             + "and which dates a transom in eighteen months" };
  }
  if (profile.ceiling !== "double" && CRUDE_STEMS.test(name)) {
    return { ok: false, name,
             reason: "cruder than the room allows - " + profile.ceiling };
  }
  const radio = radioGate(name);
  if (!radio.dealable) {
    return { ok: false, name,
             reason: "radio: " + (radio.reasons[0] || "unusable on a radio") };
  }
  const over = overuseGate(name);
  if (over.tier === 1 && !profile.wants_popular) {
    return { ok: false, name, reason: "a name on a boat at every ramp" };
  }
  const nov = noveltyGate(name, bankNames);
  if (!nov.novel) {
    return { ok: false, name, reason: nov.reason };
  }
  const font = opts.font || "Arial Bold";
  const fit = profile.transom_in ? fitGate(name, font, profile.transom_in)
    : null;
  if (fit && fit.verdict === "too_wide") {
    return { ok: false, name,
             reason: "will not fit the transom at any height we cut" };
  }
  return {
    ok: true, name,
    row: {
      name, mechanism_code: mech, humor_mechanism: MECHANISM_PHRASE[mech],
      // A riff has no hand-tagged lane. It is his material in his lane, which
      // is the only honest thing to say about it.
      style_lanes: (profile.lanes || []).slice(),
      themes: [], boat_types: (profile.boat_types || []).slice(),
      // UNRATED, not "clean", and not the session's ceiling either. Both of
      // those are claims we cannot make: a model wrote this name one second
      // ago and nobody has read it. It was screened for overt crudeness
      // against the ceiling at submission - that is all, and the level says
      // so rather than borrowing a grade from a name a human graded.
      // LEVEL_RANK has no entry for it, so it ranks as 0 and passes the
      // ceiling check it already passed once at submission.
      humor_level: "unrated",
      overuse_tier: over.tier, char_count: name.length,
      categories: ["riff"], source: "riff",
      note: cand && cand.why ? String(cand.why).slice(0, 160) : null,
      novelty: nov.similarity,
    },
    radio, fit, over, novelty: nov,
  };
}

// ---------------------------------------------------------------------------
// The monthly review
// ---------------------------------------------------------------------------
//
// The ledger is only a learning loop if somebody looks at it, so the review
// is an output rather than a state of the database: what crossed the
// threshold this month, what decayed out, and what is still exploring. The
// diff is against the previous snapshot, which is why snapshots are stored.
export function monthlyReview(rows, prevByLane, cfg = LEDGER) {
  const lanes = [...new Set((rows || [])
    .filter((r) => r.kind === "mech").map((r) => r.lane))].sort();
  const out = { lanes: {}, crossed: [], decayed: [] };
  for (const lane of lanes) {
    const p = provenFor(rows, lane, cfg);
    const was = new Set((prevByLane || {})[lane] || []);
    const now = new Set(p.proven);
    const crossed = [...now].filter((m) => !was.has(m));
    const decayed = [...was].filter((m) => !now.has(m));
    out.lanes[lane] = {
      proven: [...now], exploring: p.exploring, cold: p.cold,
      crossed, decayed,
      median_keep_rate: p.median_keep_rate != null
        ? Math.round(p.median_keep_rate * 1000) / 1000 : null,
      rates: Object.fromEntries(Object.entries(p.rates).map(([k, v]) => [
        k, { exposures: v.exposures, keeps: v.keeps, kills: v.kills,
             keep_rate: Math.round(v.rate * 1000) / 1000 }])),
    };
    for (const m of crossed) out.crossed.push(lane + ":" + m);
    for (const m of decayed) out.decayed.push(lane + ":" + m);
  }
  return out;
}
