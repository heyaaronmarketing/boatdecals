/**
 * Auto-approval: the arithmetic, and the SQL that decides who is eligible.
 *
 * Two halves, because they fail in different ways:
 *
 *  1. businessDeadline() - run against every starting weekday, including the
 *     Saturday case that verify.py's 144-hour floor depends on. If that floor
 *     is wrong the last reminder lands after the deadline it warns about.
 *
 *  2. The sweep's WHERE clause, executed by a real SQLite against seeded rows
 *     - one row per way an order can be ineligible. A stubbed database would
 *     only prove that my stub agrees with my expectations; the point is
 *     whether D1 agrees with the clause.
 *
 *   node mcp/test_autoapprove.mjs
 */
import { businessDeadline } from "../worker/proof.js";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

let fails = 0;
const ok = (cond, what) => {
  console.log(`  ${cond ? "pass" : "FAIL"}  ${what}`);
  if (!cond) fails++;
};

/* ---------------------------------------------- 1. the deadline arithmetic */
console.log("business-day arithmetic");
const DAY = 864e5;
// 2026-11-16 is a Monday. Walk a whole week of starting days.
const names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
               "Friday", "Saturday"];
let minSpan = Infinity, maxSpan = 0;
for (let i = 0; i < 7; i++) {
  const start = new Date(Date.UTC(2026, 10, 15 + i, 12, 0, 0));
  const got = businessDeadline(start.toISOString(), 5);
  const span = (got - start.getTime()) / DAY;
  const landed = new Date(got).getUTCDay();
  console.log(`    ${names[start.getUTCDay()].padEnd(10)}`
    + ` -> +${span} days, lands ${names[landed]}`);
  ok(landed !== 0 && landed !== 6, `a ${names[start.getUTCDay()]} proof`
    + ` does not fall due at a weekend`);
  minSpan = Math.min(minSpan, span);
  maxSpan = Math.max(maxSpan, span);
}
// This is the number the verifier's floor is built on.
// A Sunday proof falls due on the Friday: 5 calendar days, not the 6 I first
// assumed from the Saturday case. The verifier's reminder floor is built on
// this number, so it is asserted rather than remembered.
ok(minSpan === 5, `the SHORTEST five business days is 5 calendar days`
  + ` (got ${minSpan}) - the verifier's 120h reminder floor depends on it`);
ok(maxSpan === 7, `the longest is 7 calendar days (got ${maxSpan})`);
ok(businessDeadline("not a date", 5) === Infinity,
  "an unparseable timestamp returns Infinity, so it can never read as due");
ok(businessDeadline(null, 5) === Infinity, "so does a missing one");

/* ------------------------------------------------- 2. the eligibility SQL */
console.log("\neligibility, against a real SQLite");

// Lifted verbatim out of the sweep so the test cannot drift from it.
const src = await import("node:fs").then((fs) =>
  fs.readFileSync(new URL("../worker/proof.js", import.meta.url), "utf8"));
// Anchored INSIDE the sweep. Matching the first `SELECT * FROM orders` in the
// file picked up the proof-cycle's own query instead and tested the wrong
// clause entirely - it only surfaced because SQLite choked on the trailing
// JavaScript it dragged in with it.
const fn = src.slice(src.indexOf("export async function autoApproveSweep"));
const m = fn.match(/SELECT \* FROM orders\n([\s\S]*?)ORDER BY id LIMIT 20/);
if (!m) {
  console.log("  FAIL  could not find the sweep's query in proof.js");
  process.exit(1);
}
// The sweep interpolates ${PLAIN_FACE_SQL}; resolve it the same way it does,
// off the same array, so the test exercises the real clause.
const plain = src.match(/const PLAIN_BLOCK = \[([\s\S]*?)\];/)[1]
  .match(/"([^"]+)"/g).map((q) => q.slice(1, -1));
let where = m[1].replace("${PLAIN_FACE_SQL}",
  `(kind = 'Boat name' OR font IN (${plain.map((f) => `'${f}'`).join(",")}))`);
where = where.replace(/\?/g, "3");   // MAX_NUDGES
console.log("  query found, %d chars", where.length);

const YES = "ELIGIBLE";
const rows = [
  // ref,            optout, changes_at, number_flag,  nudges, status,  approved, auto
  [YES,                0, null, "''",      3, "'proof-sent'", null, null],
  ["opted-out",        1, null, "''",      3, "'proof-sent'", null, null],
  ["change-requested", 0, "'x'", "''",     3, "'proof-sent'", null, null],
  ["number-flagged",   0, null, "'CF not issuable'", 3, "'proof-sent'", null, null],
  ["flag-never-set",   0, null, "NULL",    3, "'proof-sent'", null, null],
  ["two-reminders",    0, null, "''",      2, "'proof-sent'", null, null],
  ["already-approved", 0, null, "''",      3, "'approved'", "'t'", null],
  ["already-swept",    0, null, "''",      3, "'auto-approved'", null, "'t'"],
  ["a-test-row",       0, null, "''",      3, "'test-archived'", null, null],
  // A decorative face on a REGISTRATION NUMBER - the order riskNote() warns
  // the customer about by name. A human has to say yes to those.
  ["decorative-regnum", 0, null, "''",     3, "'proof-sent'", null, null,
   "Registration numbers", "Great Vibes"],
  // The same face on a BOAT NAME is fine: 33 CFR has nothing to say about it.
  ["BOATNAME-OK",      0, null, "''",      3, "'proof-sent'", null, null,
   "Boat name", "Great Vibes"],
  // An unpaid row is an abandoned checkout, not a job waiting on approval.
  ["never-paid",       0, null, "''",      3, "'proof-sent'", null, null,
   "Registration numbers", "Arial Bold", 0],
];

const dir = mkdtempSync(join(tmpdir(), "nmb-aa-"));
const sql = join(dir, "t.sql");
writeFileSync(sql, `
CREATE TABLE orders (
  id INTEGER PRIMARY KEY, ref TEXT, email TEXT, ts TEXT, kind TEXT, font TEXT,
  paid INTEGER DEFAULT 1,
  proof_sent_at TEXT, approved_at TEXT, auto_approved_at TEXT,
  changes_at TEXT, test_mode INTEGER DEFAULT 0, status TEXT,
  auto_cut_optout INTEGER DEFAULT 0, number_flag TEXT, proof_nudges INTEGER);
${rows.map(([ref, out, ch, flag, n, st, ap, au, kind, font, paid], i) => `
INSERT INTO orders (id,ref,email,ts,kind,font,paid,proof_sent_at,approved_at,
  auto_approved_at,changes_at,test_mode,status,auto_cut_optout,number_flag,
  proof_nudges)
VALUES (${i + 1},'${ref}','a@b.c','2026-11-01',
  '${kind || "Registration numbers"}','${font || "Arial Bold"}',
  ${paid === 0 ? 0 : 1},'2026-11-01',
  ${ap || "NULL"},${au || "NULL"},${ch || "NULL"},0,${st},${out},${flag},${n});`
).join("")}
SELECT ref FROM orders
${where}ORDER BY id LIMIT 20;
`);

let out;
try {
  out = execFileSync("sqlite3", [":memory:"], {
    input: `.read ${sql}\n`, encoding: "utf8" });
} catch (e) {
  console.log("  SKIP  sqlite3 not available:", String(e.message).slice(0, 60));
  process.exit(fails ? 1 : 0);
}
const picked = out.trim().split("\n").filter(Boolean);
console.log("  selected:", JSON.stringify(picked));
const WANT = [YES, "BOATNAME-OK"];
ok(picked.length === WANT.length && WANT.every((r) => picked.includes(r)),
  `exactly the routine orders are eligible (wanted ${JSON.stringify(WANT)})`);
for (const [ref] of rows) {
  if (WANT.includes(ref)) continue;
  ok(!picked.includes(ref), `${ref} is excluded`);
}

console.log(fails ? `\n${fails} FAILED` : "\nall auto-approval checks pass");
process.exit(fails ? 1 : 0);
