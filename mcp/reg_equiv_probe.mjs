/**
 * Compares worker/decode.js against the validator currently running in the
 * browser (engine/validate.py's BNS_VALIDATE), over every prefix and shape.
 *
 * Why: BNS_VALIDATE is on the live order form. Before the site is switched to
 * the shared module, the two have to be proven to agree - otherwise the swap
 * is a change to the checkout path made on hope.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as D from "../worker/decode.js";
import { T } from "../worker/decode-data.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const py = fs.readFileSync(path.join(HERE, "..", "engine", "validate.py"), "utf8");

// Pull the JS out of the Python string and run it with the globals it expects.
const m = py.match(/^JS = r"""([\s\S]*?)"""/m);
if (!m) throw new Error("could not find the JS block in engine/validate.py");
globalThis.window = {
  BNS_PREFIX_STATE: T.PREFIX_STATE,
  BNS_NOLETTERS: T.NO_LETTERS,
  BNS_POSTAL_MISTAKE: Object.fromEntries(
    Object.entries(T.POSTAL_MISTAKE).map(([k, v]) => [k, [v.state, v.prefix]])),
};
new Function(m[1])();
const OLD = globalThis.window.BNS_VALIDATE;

// Normalise for comparison: the old side emits HTML and em-dashes, the new one
// emits **bold** and hyphens. Compare the SENTENCE, not the typography.
const norm = (s) => String(s || "")
  .replace(/<\/?strong>/g, "").replace(/\*\*/g, "")
  .replace(/&mdash;/g, "-").replace(/&ldquo;|&rdquo;/g, '"')
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&")
  .replace(/\s+/g, " ").trim();
const lvl = (s) => String(s || "").replace(/^v/, "");

const cases = [];
for (const p of Object.keys(T.PREFIX_STATE)) {
  cases.push(`${p} 1234 AB`, `${p}1234AB`, `${p} 12 ABC`, `${p}1234A`,
             `${p} 123`, `${p}99999ZZZZ`, `${p}`, `${p} ABCD`);
}
for (const p of Object.keys(T.POSTAL_MISTAKE)) {
  cases.push(`${p} 1234 AB`, `${p}1234AB`, `${p} XY`);
}
cases.push("", "  ", "A", "AB", "XX999", "ZZ 1234 AB", "CF1234IO",
           "cf 1234 io", "IA-3717-ZW", "ME12ABC", "ME 1234 A", "ME 123 AB",
           "IA 3717 ZW ", "9999", "IA3717ZW");

const diffs = [];
for (const c of cases) {
  const a = OLD.check(c), b = D.checkRegistration(c);
  const pa = { level: lvl(a.level), fixed: a.fixed ?? null,
               state: a.state ?? null, msg: norm(a.msg) };
  const pb = { level: b.level, fixed: b.fixed ?? null,
               state: b.state ?? null, msg: norm(b.msg) };
  // The old side only reports `state` on a clean pass; the new one always
  // knows it. That is an improvement, not a disagreement, so only compare
  // state when the old side offered one.
  if (!pa.state) pb.state = null;
  for (const k of ["level", "fixed", "state", "msg"]) {
    if (pa[k] !== pb[k]) {
      diffs.push({ input: c, field: k, old: pa[k], now: pb[k] });
    }
  }
}
console.log(JSON.stringify({ tested: cases.length, diffs }, null, 1));
