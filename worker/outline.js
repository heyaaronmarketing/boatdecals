/**
 * Glyph outlining.
 *
 * Turns "IA 3717 ZW" in a named face into SVG path data, server side, from
 * the real font file. The browser gets vector outlines of the characters the
 * customer typed - it never gets the font.
 *
 * WHY THIS EXISTS. The faces the shop cuts with are licensed Microsoft and
 * Monotype fonts. A desktop licence covers installing them and using them to
 * make artwork; it does not cover serving the font file to every visitor,
 * which is what @font-face does and what a separate webfont licence is sold
 * for. Outlining sidesteps that entirely: the output is artwork, the same as
 * any sign shop producing a cut file, and the font software stays here.
 *
 * It also fixes something a webfont never could. The preview and the proof
 * used to be CSS text, so what the customer approved was their own browser's
 * rendering. Now the preview, the proof and the plotter all come from one
 * file, so they cannot disagree.
 */
import opentype from "opentype.js";

// Parsed fonts, kept per isolate. Parsing a 400KB TTF on every keystroke
// would be absurd; the isolate holds these for its lifetime and R2 is read
// once per font per isolate.
const PARSED = new Map();

// Characters a plotter will actually be asked to cut. Anything outside this
// is refused rather than silently dropped, because a character that vanishes
// between the preview and the cut is the exact failure the proof prevents.
const ALLOWED = /^[A-Za-z0-9 .,'&!?@#:/()+-]{1,60}$/;

const KEY = (label) =>
  label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + ".ttf";

async function font(env, label) {
  const key = KEY(label);
  if (PARSED.has(key)) return PARSED.get(key);
  if (!env.FONTS) throw new Error("no FONTS bucket");
  const obj = await env.FONTS.get(key);
  if (!obj) throw new Error("no font " + key);
  const buf = await obj.arrayBuffer();
  const f = opentype.parse(buf);
  PARSED.set(key, f);
  return f;
}

/**
 * Cap height, MEASURED off the capital H rather than read from the font.
 *
 * Rye - which the shop calls Playbill - declares sCapHeight 363 against a
 * 2048 em. Its actual H tops out at 1550. Trusting the table would have made
 * a "3 inch" Playbill cut about four times oversize, on a decal whose whole
 * job is being exactly three inches. Every other face in the set agrees with
 * its own table; this one does not, and there is no way to know which is
 * which without looking.
 *
 * OS/2 is the fallback, and a flat 0.7 the fallback for that, each only used
 * when the step above produces nothing sane.
 */
function capHeight(f, upm) {
  const sane = (v) => (v > upm * 0.4 && v < upm * 1.2 ? v : null);
  try {
    const g = f.charToGlyph("H");
    if (g) {
      const bb = g.getPath(0, 0, upm).getBoundingBox();
      // Baseline at y=0 and y grows downward, so the cap top is -y1.
      const h = sane(Math.abs(bb.y1));
      if (h) return h;
    }
  } catch { /* fall through to the table */ }
  const os2 = f.tables && f.tables.os2;
  return sane(os2 && os2.sCapHeight) || Math.round(upm * 0.7);
}

/**
 * One line of text as a path, plus the metrics the caller needs to place it.
 *
 * Everything is reported in font units and as a ratio of the em, so the
 * browser can scale to whatever the panel is without this knowing or caring
 * what size it will be drawn at.
 *
 * capHeight comes from the font's own OS/2 table rather than a guess. The
 * registration rule measures CAP height specifically, and a face's cap height
 * is a fraction of its em that varies - which is why the old client-side
 * version had to measure a hidden "H" to find it.
 */
function outline(f, text) {
  const upm = f.unitsPerEm || 1000;
  const path = f.getPath(text, 0, 0, upm, { kerning: true });
  const d = path.toPathData(2);
  const bb = path.getBoundingBox();
  const cap = capHeight(f, upm);
  return {
    d,
    upm,
    capRatio: cap / upm,
    advance: f.getAdvanceWidth(text, upm, { kerning: true }),
    // y grows downward in the path because the baseline was placed at upm.
    box: Number.isFinite(bb.x1)
      ? { x1: bb.x1, y1: bb.y1, x2: bb.x2, y2: bb.y2 }
      : { x1: 0, y1: 0, x2: 0, y2: 0 },
  };
}

/**
 * GET /api/outline?t=TEXT&f=Label[,Label...]
 *
 * One call can ask for several faces, because the font picker shows the
 * customer's own lettering in every face at once - ten round trips per
 * keystroke would be ten times the latency for no reason.
 */
export async function handleOutline(request, env) {
  const url = new URL(request.url);
  const text = (url.searchParams.get("t") || "").slice(0, 60);
  const want = (url.searchParams.get("f") || "").split(",")
    .map((s) => s.trim()).filter(Boolean).slice(0, 12);
  if (!text.trim() || !want.length) return { ok: false, error: "need t and f" };
  if (!ALLOWED.test(text)) return { ok: false, error: "unsupported characters" };

  const out = {};
  for (const label of want) {
    try {
      out[label] = outline(await font(env, label), text);
    } catch (err) {
      // A missing face is reported, not silently skipped: the caller needs to
      // know it has nothing to draw rather than render an empty box.
      out[label] = { error: String((err && err.message) || err).slice(0, 80) };
    }
  }
  return { ok: true, text, fonts: out };
}
