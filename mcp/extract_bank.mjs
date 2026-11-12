/**
 * Lift the name bank out of the site's generator into structured data.
 *
 * WHY THIS IS AN EXTRACTOR AND NOT A COPY. The 1,400 names are the moat - the
 * part a base model cannot reproduce, because they are curated to a house
 * standard rather than generated. They currently live as a JavaScript object
 * literal inside engine/namegen.py, shipped to the browser. The naming engine
 * needs them server-side, tagged and queryable.
 *
 * Copying them into a second file would mean two banks that drift: a name
 * added to the site generator would silently never reach the engine. So this
 * reads the generator itself, every build, and the bank is derived - never
 * hand-maintained.
 *
 * The literal is JS, not JSON: unquoted keys, single quotes, trailing commas,
 * and two value shapes (a bare string, or {n, note} for names that carry an
 * explanation - the anagram set needs its "anagram of Captain" line or the
 * joke is invisible). Rather than write a fragile regex parser, this isolates
 * the object literal by brace-balancing and evaluates that one expression.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");
const SRC = path.join(ROOT, "engine", "namegen.py");

const text = fs.readFileSync(SRC, "utf8");

// Isolate `var N = { ... };` by balancing braces. Counting braces is safe here
// because the literal contains no braces inside its strings - checked below,
// and the check fails loudly rather than silently truncating the bank.
const start = text.indexOf("var N = {");
if (start < 0) throw new Error("could not find `var N = {` in namegen.py");
const open = text.indexOf("{", start);

let depth = 0, end = -1, inStr = null, prev = "";
for (let i = open; i < text.length; i++) {
  const ch = text[i];
  if (inStr) {
    if (ch === inStr && prev !== "\\") inStr = null;
  } else if (ch === '"' || ch === "'") {
    inStr = ch;
  } else if (ch === "{") {
    depth++;
  } else if (ch === "}") {
    depth--;
    if (depth === 0) { end = i + 1; break; }
  }
  prev = ch;
}
if (end < 0) throw new Error("unbalanced braces in the name bank literal");

const literal = text.slice(open, end);

// Evaluated, not JSON.parsed: it is JavaScript. The input is a file in this
// repo, not user data.
const N = new Function(`return (${literal});`)();

const rows = [];
const seen = new Map();
let dupes = 0;

for (const [category, list] of Object.entries(N)) {
  if (!Array.isArray(list)) continue;
  for (const item of list) {
    const name = typeof item === "string" ? item : item.n;
    const note = typeof item === "string" ? null : (item.note || null);
    if (!name || typeof name !== "string") continue;
    const key = name.toLowerCase().trim();
    if (seen.has(key)) {
      // A name can legitimately sit in two categories; keep the first and
      // record the second rather than dropping the fact on the floor.
      seen.get(key).categories.push(category);
      dupes++;
      continue;
    }
    const row = {
      name: name.trim(),
      categories: [category],
      note,
      char_count: name.trim().length,
      word_count: name.trim().split(/\s+/).length,
      source: "bank",
    };
    seen.set(key, row);
    rows.push(row);
  }
}

const byCat = {};
for (const r of rows) for (const c of r.categories) byCat[c] = (byCat[c] || 0) + 1;

const out = {
  generated_from: "engine/namegen.py",
  note: "Derived file. Do not edit by hand - run `node mcp/extract_bank.mjs`.",
  category_count: Object.keys(byCat).length,
  name_count: rows.length,
  names: rows,
};

const dest = path.join(HERE, "data");
fs.mkdirSync(dest, { recursive: true });
// Intermediate: build_bank.py merges this with the funny-names page.
fs.writeFileSync(path.join(dest, "_bank_js.json"), JSON.stringify(out, null, 1));

console.log(`bank: ${rows.length} unique names across ${out.category_count} categories`);
console.log(`      ${dupes} cross-category duplicates merged`);
console.log("");
const widest = Math.max(...Object.keys(byCat).map((c) => c.length));
for (const [c, n] of Object.entries(byCat).sort((a, b) => b[1] - a[1])) {
  console.log(`      ${c.padEnd(widest)}  ${String(n).padStart(4)}`);
}
const withNotes = rows.filter((r) => r.note).length;
console.log("");
console.log(`      ${withNotes} names carry an explanatory note`);
console.log(`      longest: ${Math.max(...rows.map((r) => r.char_count))} chars`);
