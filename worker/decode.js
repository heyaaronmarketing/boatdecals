/**
 * Registration-number checking and HIN decoding. ONE implementation.
 *
 * This file is run by the website (inlined into the two tool pages by
 * engine/build.py) and by the MCP server. Not two copies kept in step by a
 * test - the same source, in both places.
 *
 * That is worth the small build step. The alternative was what the gates had
 * to settle for: real logic in two languages with an equivalence harness
 * holding them together. Here both surfaces are JavaScript, so there is no
 * reason to accept the duplication at all.
 *
 * Every table comes from decode-data.js, generated from engine/content.py and
 * engine/tools.py.
 *
 * MESSAGE FORMAT. Messages carry **bold** markers rather than HTML. The page
 * renders them as <strong>, the MCP server hands the markdown to the model,
 * and there is one string either way. Returning HTML would have meant an
 * assistant reading "<strong>" aloud to a customer; returning plain text would
 * have meant losing the emphasis the page has always had.
 *
 * NOTHING HERE EVER BLOCKS AN ORDER. The prefix table is compiled from
 * secondary sources, states issue sequentially so old hulls carry retired
 * formats, and we only cover tier 1 of the rules. An order refused by an
 * incomplete validator is a lost sale; an order flagged for the proof is a
 * thirty-second check by someone who knows. That is what the proof step is for.
 */
import { T } from "./decode-data.js";

export const MONTHS = {
  A: "January", B: "February", C: "March", D: "April", E: "May", F: "June",
  G: "July", H: "August", I: "September", J: "October", K: "November",
  L: "December",
};

export function clean(v) {
  return String(v || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

/** **bold** -> <strong>, for the website. */
export function toHtml(s) {
  return String(s || "")
    .replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]))
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

/** **bold** -> bold, for anything that reads it aloud. */
export function toPlain(s) {
  return String(s || "").replace(/\*\*(.+?)\*\*/g, "$1");
}

/**
 * Check a registration number. Returns:
 *   level  'ok' | 'note' | 'warn'   (never 'blocked' - see above)
 *   msg    with **bold** markers, or null when there is nothing to say
 *   fixed  a correctly spaced version when one can be derived
 *   state  the state the prefix belongs to, when known
 */
export function checkRegistration(raw) {
  const compact = clean(raw);
  if (compact.length < 3) {
    return { level: "ok", msg: null, fixed: null, state: null,
             compact, prefix: null };
  }

  const prefix = compact.slice(0, 3).match(/^[A-Z]{2}/)
    ? compact.slice(0, 2) : compact.slice(0, 2);
  const rest = compact.slice(2);
  const state = T.PREFIX_STATE[prefix] || null;

  // 1. prefix. The common case by far is the postal code: a Michigan owner
  // types MI, which is in fact Mississippi's prefix.
  if (!state) {
    const oops = T.POSTAL_MISTAKE[prefix];
    if (oops) {
      const g = rest.match(/^(\d{1,4})([A-Z]{0,3})$/);
      const fixed = g
        ? `${oops.prefix} ${g[1]}${g[2] ? " " + g[2] : ""}`
        : `${oops.prefix} ${rest}`;
      return {
        level: "warn", fixed, state: oops.state, compact, prefix,
        msg: `**${oops.state}** boat numbers start with **${oops.prefix}**, `
          + `not ${prefix} - the vessel prefixes were set before the postal `
          + "codes. Check your card.",
      };
    }
    return {
      level: "warn", fixed: null, state: null, compact, prefix,
      msg: `**${prefix}** is not a vessel prefix we recognise. Check it `
        + "against your registration card - a few states differ from the "
        + "postal code.",
    };
  }

  // 2. shape
  const m = rest.match(/^(\d{1,4})([A-Z]{0,3})$/);
  if (!m) {
    return {
      level: "warn", fixed: null, state, compact, prefix,
      msg: `That does not read as **${prefix} <numbers> <letters>**. Copy it `
        + "off the card exactly - we cut what you type.",
    };
  }
  const digits = m[1], letters = m[2];

  const exc = T.FORMAT_EXCEPTIONS[prefix];
  if (exc) {
    const ok = exc.patterns.some((p) => new RegExp(p).test(rest));
    if (!ok) {
      return {
        level: "note", fixed: null, state, compact, prefix,
        msg: `${exc.note} We will cut it as typed - just worth a second look.`,
      };
    }
  } else if (letters.length > 2) {
    return {
      level: "note", fixed: null, state, compact, prefix,
      msg: "Most states end in one or two letters. We will cut it as typed, "
        + "but check the card.",
    };
  }

  // 3. characters a state will not issue
  const banned = T.NO_LETTERS[prefix];
  if (banned) {
    for (const ch of banned) {
      if (letters.includes(ch)) {
        return {
          level: "note", fixed: null, state, compact, prefix,
          msg: `${state} does not issue the letters **`
            + `${banned.split("").join(", ")}** in a number. Worth checking `
            + "that is not a 0 or a 1.",
        };
      }
    }
  }

  // 4. spacing - offer the corrected string rather than scolding
  const fixed = `${prefix} ${digits}${letters ? " " + letters : ""}`;
  const typedGroups = String(raw || "").trim().split(/[\s-]+/)
    .filter(Boolean).length;
  if (typedGroups < 2) {
    return {
      level: "note", fixed, state, compact, prefix,
      msg: `The rule wants a gap between the groups. We will cut it as `
        + `**${fixed}**.`,
    };
  }

  return { level: "ok", msg: null, fixed, state, compact, prefix };
}

/**
 * Decode a hull identification number.
 *
 * A HIN is exactly 12 characters, stamped into the starboard side of the
 * transom by the builder. Positions 1-3 are the manufacturer code, 4-8 the
 * serial, and 9-12 a date block whose meaning changed in August 1984.
 */
export function decodeHin(raw) {
  const v = clean(raw);
  const bad = (msg) => ({ ok: false, msg, hin: v });

  if (v.length < 12) {
    return bad("A hull identification number is exactly 12 characters. You "
      + `gave ${v.length}. Check the starboard side of the transom, up near `
      + "the top edge.");
  }
  if (v.length > 12) {
    return bad(`That is ${v.length} characters. A HIN is exactly 12 - no `
      + "more. Drop any trailing text.");
  }
  if (!/^[A-Z]{3}/.test(v)) {
    return bad("The first three characters should be letters - the "
      + `manufacturer code. Yours are "${v.slice(0, 3)}".`);
  }

  const mic = v.slice(0, 3), serial = v.slice(3, 8), d = v.slice(8, 12);
  const maker = T.MIC[mic] || null;

  const out = {
    ok: true, hin: v, mic, serial,
    manufacturer: maker,
    manufacturer_note: maker
      ? null
      : "Not in our table. It is a valid-looking code - search the USCG MIC "
        + "database for the builder.",
    date_code: d,
    format: null, built: null, model_year: null, notes: [],
  };

  const m1 = d.charAt(0), y1 = d.charAt(1), my = d.slice(2);
  if (MONTHS[m1] && /^\d$/.test(y1) && /^\d{2}$/.test(my)) {
    // Post-August-1984 format. The build year is a SINGLE digit, so its
    // decade has to be inferred from the model year - which is why a build
    // year can come out later than the model year on odd data, and why this
    // says "reads as" rather than stating it as fact.
    const century = parseInt(my, 10) > 40 ? "19" : "20";
    out.format = "post-1984";
    out.model_year = century + my;
    out.built = `${MONTHS[m1]} ${century}${my.charAt(0)}${y1}`;
    out.notes.push("Read as the current (post-August 1984) format: characters "
      + "9-10 are the build month and year, 11-12 are the model year. The "
      + "build year is a single digit, so its decade is inferred from the "
      + "model year.");
  } else if (/^\d{2}/.test(d)) {
    out.format = "pre-1984";
    out.notes.push(`Date code ${d} looks like the pre-1984 format, where the `
      + "last characters are the model year and month.");
  } else {
    out.format = "unknown";
    out.notes.push(`We could not read ${d} as a standard date block. `
      + "Straight-year formats were common before August 1984.");
  }

  out.notes.push("**A HIN is not your registration number.** The HIN is "
    + "stamped into the hull by the builder and never changes. Your "
    + "registration number is issued by your state and is the one you have to "
    + "display in 3-inch letters.");
  return out;
}
