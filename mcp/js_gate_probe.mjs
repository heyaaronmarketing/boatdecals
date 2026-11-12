/**
 * Runs the worker's gates over a list of names and prints JSON.
 * Used only by mcp/test_equivalence.py - this is the JS half of the
 * cross-language comparison that keeps the two implementations honest.
 */
import fs from "node:fs";
import zlib from "node:zlib";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as G from "../worker/gates.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const words = zlib.gunzipSync(
  fs.readFileSync(path.join(HERE, "data", "lexicon.txt.gz"))).toString().split("\n");
G._setLexicon(words);

const names = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = {};
for (const n of names) {
  const r = G.radioGate(n);
  const o = G.overuseGate(n);
  out[n] = {
    radio: {
      verdict: r.verdict, dealable: r.dealable, readback: r.readback,
      spell_out: r.spell_out, visual_only: r.visual_only, score: r.score,
      reasons: r.reasons,
    },
    overuse: { tier: o.tier, top_pick_eligible: o.top_pick_eligible,
               note: o.note },
    fit: G.fitGate(n, "Arial Bold", 34),
    fit_impact: G.fitGate(n, "Impact", null),
  };
}
process.stdout.write(JSON.stringify(out));
