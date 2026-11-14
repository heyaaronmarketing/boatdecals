/**
 * Does the figure on the Pay button equal the figure on the card?
 *
 * worker/price.js is the one pricing function, and engine/shared_js.price_js()
 * ships that same file to the browser rather than a reimplementation of it. So
 * in principle this test cannot fail - which is the point, and is a better
 * outcome than a test.
 *
 * It exists anyway because the INLINER can fail. price_js() strips import
 * lines and the `export` keyword with regexes, slices the font metrics out of
 * worker/gates-data.js, lifts widthIn() out of worker/gates.js by brace
 * matching, and empties one key. Any of those is a text transform on code
 * that takes money. A transform that silently drops a clause would leave the
 * form quoting one price and the card charging another - the exact bug the
 * single implementation was meant to end.
 *
 * So: run both, over every combination of product, height, name, face,
 * outline and upgrade set, and compare. verify.py runs this; the browser
 * bundle is written to argv[2] by verify.py first, because only Python can
 * produce it.
 */
import fs from "node:fs";
import * as W from "../worker/price.js";

const bundlePath = process.argv[2];
if (!bundlePath) {
  console.log("usage: node mcp/test_price_browser.mjs <inlined-bundle.js>");
  process.exit(2);
}

// The bundle is an IIFE that hangs its exports on `window`. Give it one.
const window = {};
new Function("window", fs.readFileSync(bundlePath, "utf8"))(window);
const B = window.NMB_PRICE;
if (!B || typeof B.priceOf !== "function") {
  console.log("FAIL: the inlined bundle did not expose window.NMB_PRICE");
  process.exit(1);
}

// Names chosen to straddle every band boundary in every face, not to be
// funny: a two-letter one, a typical transom name, a long one, and one with a
// character the metrics tables have to carry (the apostrophe).
const NAMES = ["Ox", "Knot Working", "Second Wind", "Reel Therapy",
               "Mortality Barge", "Cap'n Crunch Time",
               "The Codicil Of Captain Absalom Finch"];
const FONTS = ["Arial Bold", "Arial Black", "Impact", "OCR A Extended",
               "MS Gothic", "Bodoni MT", "Rockwell Extra Bold", "Playbill",
               "Snap ITC", "Stencil"];
const KINDS = ["numbers", "name", "both", "Registration numbers", "Boat name",
               "Both", "boat-name", "registration-numbers",
               "Numbers + name", "Something else"];
const UPS = ["", "Rush - cut and shipped today",
             "Premium 8-year cast vinyl | Reflective finish"];

let n = 0;
const bad = [];
for (const kind of KINDS) {
  for (const height of ["3", "4", "5", "6"]) {
    for (const boatname of NAMES) {
      for (const font of FONTS) {
        for (const outline of [0, 1]) {
          for (const upgrades of UPS) {
            const d = { kind, height, boatname, font, outline, upgrades };
            n++;
            const a = W.priceOf(d, false);
            const b = B.priceOf(d, false);
            if (a !== b) bad.push([JSON.stringify(d), a, b]);
          }
        }
      }
    }
  }
}

// And the band itself, not only the total - a band that differed by a dollar
// would be invisible in a sum that happened to clamp.
for (const boatname of NAMES) {
  for (const font of FONTS) {
    for (const h of [3, 4, 5, 6]) {
      n++;
      const a = W.nameBand(boatname, font, h);
      const b = B.nameBand(boatname, font, h);
      if (a.key !== b.key || a.price !== b.price || a.billed_in !== b.billed_in) {
        bad.push([`nameBand(${JSON.stringify(boatname)}, ${font}, ${h})`,
                  JSON.stringify(a), JSON.stringify(b)]);
      }
    }
  }
}

if (bad.length) {
  for (const [d, a, b] of bad.slice(0, 6)) {
    console.log(`FAIL: ${d}\n  worker ${a}  browser ${b}`);
  }
  console.log(`\n${bad.length} of ${n} cases disagree: the order form would `
    + `quote a price the card does not charge`);
  process.exit(1);
}
console.log(`form and worker price identically on all ${n} cases`);
