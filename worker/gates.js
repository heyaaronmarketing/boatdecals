/**
 * The deterministic gates, worker side.
 *
 * Every TABLE this uses comes from gates-data.js, which is generated from
 * mcp/gates.py - there is one definition of the rebus tokens, the homophones,
 * the respelling rules, the overuse tiers and the font metrics.
 *
 * The LOGIC below is a second implementation of the ~150 lines in
 * mcp/gates.py, and that is the honest cost of the MCP server having to run on
 * a Worker while the validation corpus lives in Python. It is paid for by
 * mcp/test_equivalence.py, which runs both over all 1,089 bank names and fails
 * the build on any disagreement in any field. Do not change a rule here
 * without changing it there; the build will stop you, which is the point.
 */
import { D } from "./gates-data.js";

const OK_PUNCT = new Set(" '&,.!?-:".split(""));
const VISUAL = new Set(D.VISUAL_ONLY.split(""));
const REBUS = new Set(D.REBUS_TOKENS);
const ARCHAIC = new Set(D.ARCHAIC_COLLISIONS);
const REBUS_SHAPE = /[A-Za-z]-?\d-?[A-Za-z]/;
const WORD = /[A-Za-z0-9'’-]+/g;
const VOWELS = new Set("aeiouy".split(""));
const RULES = D.RESPELL_RULES.map(([src, flags, repl]) =>
  [new RegExp(src, flags), repl]);

// The lexicon is 176,664 words and lives in R2, not in the bundle. Loaded once
// per isolate and held in module scope - the same pattern the ten fonts use.
let LEX = null;

export async function loadLexicon(env) {
  if (LEX) return LEX;
  const obj = await env.FONTS.get("lexicon.txt.gz");
  if (!obj) {
    // Deliberately loud. A radio gate with no dictionary cannot tell a
    // nonstandard spelling from a standard one, and a gate that guesses is
    // worse than a gate that says it is unavailable.
    throw new Error("lexicon.txt.gz is not in R2 - the radio gate cannot run");
  }
  const text = await new Response(
    obj.body.pipeThrough(new DecompressionStream("gzip"))).text();
  LEX = new Set(text.split("\n"));
  return LEX;
}

/** Test-only: inject a lexicon without R2. */
export function _setLexicon(words) { LEX = new Set(words); }

function tokens(name) {
  return (String(name).match(WORD) || [])
    .map((t) => t.replace(/^-+|-+$/g, "")).filter(Boolean);
}

function syllables(word) {
  const w = word.toLowerCase();
  let n = 0, prev = false;
  for (const ch of w) {
    const v = VOWELS.has(ch);
    if (v && !prev) n++;
    prev = v;
  }
  if (w.endsWith("e") && n > 1) n--;
  return Math.max(n, 1);
}

function isWord(t) {
  if (LEX.has(t)) return true;
  // A doubled final letter is a respelling signature, not an inflection:
  // stripping the y off "Ahoyy" yields "ahoy" and would call it standard.
  if (t.length > 2 && t[t.length - 1] === t[t.length - 2]) return false;
  for (const suf of ["s", "es", "ed", "ing", "er", "est", "ly", "y"]) {
    if (t.endsWith(suf) && t.length > suf.length + 2
        && LEX.has(t.slice(0, -suf.length))) return true;
  }
  for (const suf of ["ing", "ed", "er", "est"]) {
    if (t.endsWith(suf)) {
      const stem = t.slice(0, -suf.length);
      if (stem.length > 2 && stem[stem.length - 1] === stem[stem.length - 2]
          && LEX.has(stem.slice(0, -1))) return true;
    }
  }
  for (const suf of ["ing", "ed", "er", "est"]) {
    if (t.endsWith(suf) && t.length > suf.length + 2
        && LEX.has(t.slice(0, -suf.length) + "e")) return true;
  }
  return false;
}

function initialism(token) {
  const t = String(token).replace(/^'+|'+$/g, "");
  if (t.length < 2 || t.length > 5 || !/^[A-Za-z]+$/.test(t)) return false;
  return t === t.toUpperCase() && !isWord(t.toLowerCase());
}

function respelling(token) {
  let t = token.toLowerCase().replace(/^['’]+|['’]+$/g, "")
    .replace(/-/g, "");
  if (t.endsWith("in") && isWord(t + "g")) return null;
  if (t.length < 3 || !/^[a-z]+$/.test(t)) return null;
  if (isWord(t) && !ARCHAIC.has(t)) return null;

  const seen = new Set([t]);
  let frontier = [t];
  for (let pass = 0; pass < 2; pass++) {
    const next = [];
    for (const cur of frontier) {
      for (const [re, repl] of RULES) {
        const cand = cur.replace(re, repl);
        if (cand === cur || seen.has(cand) || cand.length < 3) continue;
        seen.add(cand);
        next.push(cand);
        if (isWord(cand) && !ARCHAIC.has(cand)) return cand;
      }
    }
    frontier = next;
  }
  return null;
}

function nonstandard(token) {
  const bare = token.toLowerCase().replace(/^['’]+|['’]+$/g, "");
  const t = bare.replace(/-/g, "");
  if (t.length < 3 || !/^[a-z]+$/.test(t)) return [false, null];
  if (initialism(token)) return [false, null];
  if (bare.includes("-")) {
    const parts = bare.split("-").filter((x) => x.length >= 3);
    if (parts.length && parts.every(isWord)) return [false, null];
  }
  if (t.endsWith("in") && isWord(t + "g")) return [false, null];

  const heard = respelling(t);
  if (heard) return [true, heard];
  if (isWord(t)) return [false, null];
  for (let i = 4; i < t.length - 3; i++) {
    if (LEX.has(t.slice(0, i)) && LEX.has(t.slice(i))) return [false, null];
  }
  return [true, null];
}

function spoken(name) {
  let s = String(name || "").replace(/[*†‡]/g, "");
  s = s.replace(/[([{]/g, ", ").replace(/[)\]}]/g, "");
  s = s.replace(/&/g, " and ").replace(/%/g, " percent");
  return s.replace(/\s+/g, " ").trim().replace(/^,|,$/g, "").trim();
}

export function radioGate(name) {
  const raw = String(name || "").trim();
  const bail = (reasons) => ({
    verdict: "fail", dealable: false, readback: "", reasons,
    spell_out: true, visual_only: false, score: 0,
  });
  if (!raw) return bail(["No name given."]);

  // Strip combining marks for analysis, keep the original for the readback:
  // "Deja Vu" and "Déjà Vu" are said the same way.
  const flat = raw.normalize("NFKD").replace(/\p{M}/gu, "");
  const toks = tokens(flat);
  const letters = toks.reduce((a, t) => a + t.length, 0);
  const words = toks.length;
  const sylls = toks.reduce((a, t) => a + syllables(t), 0);

  const hard = [];
  const rebus = [...new Set(toks.filter((t) => REBUS.has(t.toLowerCase())))].sort();
  if (rebus.length && words > 1) {
    hard.push(`"${rebus.join('", "')}" stands in for a whole word. Said out `
      + "loud there is no way for anybody to know you spelled it that way, "
      + "and spelling it out does not help - the letter and the word sound "
      + "the same.");
  }
  if (REBUS_SHAPE.test(flat)) {
    hard.push("A digit wedged inside the words cannot be spoken as written.");
  }
  const exotic = [...new Set([...flat].filter(
    (c) => !/[A-Za-z0-9]/.test(c) && !OK_PUNCT.has(c) && !VISUAL.has(c)))].sort();
  if (exotic.length) {
    hard.push(`${exotic.join(" ")} cannot be said at all - it has to be `
      + "described.");
  }
  if (hard.length) return bail(hard);

  const reasons = [];
  let spellOut = false;

  const visual = [...new Set([...flat].filter((c) => VISUAL.has(c)))].sort();
  const visualOnly = visual.length > 0;
  if (visualOnly) {
    reasons.push(`The ${visual.includes("(") ? "brackets"
      : visual.includes("*") ? "asterisk" : visual.join(" ")} is the punchline `
      + "and nobody hears punctuation. This one lands on the transom, not on "
      + "the radio.");
  }
  if (/\d/.test(flat)) {
    spellOut = true;
    reasons.push("There is a number in it, so expect to confirm whether it is "
      + "a numeral or spelled out.");
  }

  const odd = [], heardAs = [];
  for (const t of toks) {
    const [bad, as_] = nonstandard(t);
    if (bad) { odd.push(t); if (as_) heardAs.push([t, as_]); }
  }
  if (odd.length) {
    spellOut = true;
    if (heardAs.length) {
      reasons.push("Say this on the radio and they write down "
        + heardAs.map(([t, a]) => `"${a}" instead of "${t}"`).join(", ")
        + ". You will be spelling it out every time.");
    } else {
      reasons.push(`${odd.join(", ")} ${odd.length === 1 ? "is" : "are"} not a `
        + "word anybody can spell from hearing it, so expect to spell this "
        + "one out every time.");
    }
  }

  const inits = [...new Set(toks.filter(initialism))].sort();
  if (inits.length) {
    reasons.push(`${inits.join(", ")} get${inits.length === 1 ? "s" : ""} read `
      + "out letter by letter - normal on a radio, just slower.");
  }

  const homo = toks.filter((t) => D.HOMOPHONES[t.toLowerCase()]);
  if (homo.length) {
    reasons.push("Expect to say it twice the first time: "
      + homo.map((t) => `"${t}" (heard as "${D.HOMOPHONES[t.toLowerCase()]}")`)
        .join(", ")
      + ". That is the joke working, not a problem with the name.");
  }
  if (sylls >= 9 || words >= 5) {
    reasons.push(`It is a long one on the radio - ${sylls} syllables.`);
  }

  let verdict;
  if (spellOut) {
    verdict = "spell_it";
  } else if (letters > 24 || words > 6 || sylls >= 12) {
    verdict = "mouthful";
    reasons.push(`At ${letters} letters across ${words} words this is a long `
      + "haul on channel 16. Fine on a transom, slow on a radio.");
  } else if (homo.length || sylls >= 9 || words >= 5) {
    verdict = "sayable";
  } else {
    verdict = "clear";
    reasons.push("Says clean and spells itself.");
  }

  let score = 100;
  if (spellOut) score -= 35;
  score -= 8 * homo.length;
  score -= Math.max(0, sylls - 6) * 4;
  score -= Math.max(0, words - 3) * 5;
  score = Math.max(1, Math.min(100, score));

  return {
    verdict, dealable: true,
    readback: `Mayday, mayday, this is ${spoken(raw)}.`,
    reasons, spell_out: spellOut, visual_only: visualOnly, score,
  };
}

function norm(name) {
  return String(name || "").toLowerCase().normalize("NFKD")
    .replace(/\p{M}/gu, "").replace(/[^a-z0-9 ]+/g, "")
    .replace(/\s+/g, " ").trim();
}

const T1 = new Set(D.OVERUSE_T1.map(norm));
const T2 = new Set(D.OVERUSE_T2.map(norm));

export function overuseGate(name) {
  const n = norm(name);
  if (T1.has(n)) {
    return {
      tier: 1, top_pick_eligible: false,
      note: "One in every marina. This is one of the most common boat names "
        + "in the country - a fine name, but you will be answering to it "
        + "alongside somebody else.",
    };
  }
  if (T2.has(n)) {
    return { tier: 2, top_pick_eligible: true, note: "Common, but not worn out." };
  }
  return { tier: 0, top_pick_eligible: true, note: null };
}

/** The honesty limit, enforced the same way on both sides. */
export function claimsAreHonest(text) {
  const t = String(text || "").toLowerCase();
  for (const bad of D.FORBIDDEN_CLAIMS) if (t.includes(bad)) return bad;
  return null;
}

function bigrams(s) {
  const t = norm(s).replace(/ /g, "");
  const out = new Set();
  for (let i = 0; i < t.length - 1; i++) out.add(t.slice(i, i + 2));
  return out.size ? out : new Set([t]);
}

export function noveltyGate(candidate, bankNames, threshold = 0.82) {
  const n = norm(candidate);
  if (!n) {
    return { novel: false, closest: null, similarity: 1.0,
             reason: "Empty candidate." };
  }
  const A = bigrams(n);
  let best = null, score = 0;
  for (const b of bankNames) {
    if (norm(b) === n) {
      return { novel: false, closest: b, similarity: 1.0,
               reason: "Already in the bank, word for word." };
    }
    const B = bigrams(b);
    let inter = 0;
    for (const g of A) if (B.has(g)) inter++;
    const d = (A.size + B.size) ? (2 * inter) / (A.size + B.size) : 0;
    if (d > score) { best = b; score = d; }
  }
  if (score >= threshold) {
    return { novel: false, closest: best, similarity: Math.round(score * 1000) / 1000,
             reason: `Too close to "${best}" already in the bank.` };
  }
  return { novel: true, closest: best,
           similarity: Math.round(score * 1000) / 1000, reason: null };
}

export function widthIn(name, font, heightIn) {
  const m = D.FONTS[font];
  if (!m) {
    throw new Error(`no metrics for ${font} - the ten faces are `
      + Object.keys(D.FONTS).sort().join(", "));
  }
  let total = 0;
  const missing = new Set();
  for (const ch of String(name)) {
    const a = m.advance[ch];
    if (a === undefined) missing.add(ch); else total += a;
  }
  const emIn = heightIn / m.cap_ratio;
  return [(total / m.upm) * emIn, [...missing].sort()];
}

export function fitGate(name, font = "Arial Bold", transomIn = null,
                        heights = D.HEIGHTS_IN) {
  const nm = String(name || "").trim();
  if (!nm) return { verdict: "fail", reasons: ["No name given."] };
  const widths = {};
  let missing = [];
  try {
    for (const h of heights) {
      const [w, miss] = widthIn(nm, font, h);
      widths[h] = Math.round(w * 10) / 10;
      missing = miss;
    }
  } catch (e) {
    return { verdict: "unknown_font", reasons: [String(e.message || e)] };
  }

  const out = { font, name: nm, widths_in: widths,
                error_pct: D.FIT_ERROR_PCT, unsupported: missing, reasons: [] };
  if (missing.length) {
    out.reasons.push("We cannot cut "
      + missing.map((c) => `'${c}'`).join(" ")
      + " in this face, so the width below leaves it out. Ask before you order.");
  }
  const hi = Math.max(...heights), lo = Math.min(...heights);
  if (transomIn === null || transomIn === undefined) {
    out.verdict = "measured";
    out.best_height = hi;
    out.reasons.push(`At ${hi}" tall it finishes about ${widths[hi]}" wide, `
      + `give or take ${D.FIT_ERROR_PCT.toFixed(1)}%. Measure the flat run `
      + "above your waterline before you order.");
    return out;
  }

  const usable = transomIn * D.COMFORT;
  const fits = {};
  for (const h of heights) fits[h] = widths[h] <= usable;
  out.fits = fits;
  out.transom_in = transomIn;
  out.usable_in = Math.round(usable * 10) / 10;

  const ok = heights.filter((h) => fits[h]);
  if (!ok.length) {
    out.verdict = "too_wide";
    out.best_height = null;
    out.reasons.push(`This one does not fit. Even at ${lo}" tall it runs about `
      + `${widths[lo]}" wide and you have ${transomIn}" of flat run to work `
      + "with. Shorter name, or we split it over two lines.");
    return out;
  }
  const best = Math.max(...ok);
  out.best_height = best;
  if (best === hi) {
    out.verdict = "fits";
    out.reasons.push(`Fits at every height we cut. At ${best}" tall it is `
      + `about ${widths[best]}" wide on a ${transomIn}" run.`);
  } else {
    out.verdict = "height_capped";
    out.reasons.push(`Fits up to ${best}" tall - about ${widths[best]}" wide. `
      + `At ${best + 1}" it would run ${widths[best + 1]}" and that is more `
      + `than your ${transomIn}" of flat run.`);
  }
  return out;
}
