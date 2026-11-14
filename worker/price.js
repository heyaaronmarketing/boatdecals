/**
 * THE PRICE. One function, one table, every surface.
 *
 * Read by, and only by, this list - if you are adding a sixth caller, add it
 * here rather than doing the arithmetic again:
 *
 *   worker/index.js   /api/order, /api/checkout, /api/price, /api/paylink
 *   worker/mcp.js     price_order, and the price_note on get_products
 *   engine/order.py   the order form's running total, via
 *                     engine/shared_js.price_js() which inlines THIS FILE
 *                     into the browser - so the figure on the button and the
 *                     figure on the card are produced by the same code, not
 *                     by two implementations that agree today
 *
 * The numbers come from worker/price-data.js, which is GENERATED from
 * engine/content.py by mcp/build_price_js.py. There is no price literal in
 * this file and there must never be one.
 */
import { P } from "./price-data.js";
import { widthIn } from "./gates.js";

/**
 * Four vocabularies for three products, resolved in one place.
 *
 * A REAL BUG this map exists to make impossible. The price table used to be
 * keyed by the labels the website's own form posts, and the MCP server's
 * price_order took "numbers"/"name"/"both" and passed them straight in -
 * matching nothing and falling through to a default of the cheapest product.
 * An assistant quoted the registration-number price for a boat name and for
 * the bundle, silently, for every quote at three inches. catalog.json
 * advertises a THIRD set of names, the product ids, so a model that read the
 * catalog and then priced what it read was guaranteed to miss.
 *
 * The lesson is not "add a map". It is that calling the one pricing function
 * with a vocabulary it does not speak is exactly as wrong as keeping a second
 * copy of the price, and it fails more quietly.
 */
export const KIND_ALIAS = {
  // what the order form posts
  "Registration numbers": "numbers",
  "Boat name": "name",
  "Both": "both",
  // MCP price_order
  "numbers": "numbers",
  "name": "name",
  "both": "both",
  // catalog.json ids / get_products
  "registration-numbers": "numbers",
  "boat-name": "name",
  // Older cached pages. "Numbers + name" was the bundle's label before it was
  // shortened to "Both", and "Something else" was a fourth card offering
  // custom lettering. Both can still arrive from a page sitting in a browser
  // tab or a CDN, and a cached page is a real customer, so they still price.
  // "Something else" prices as a name, because that is what it was - custom
  // cut lettering - and the old flat figure for it is now below the cheapest
  // thing the shop sells.
  "Numbers + name": "both",
  "Something else": "name",
};

export const KIND_NAMES = Object.keys(KIND_ALIAS);

/**
 * Which band a name falls in, from the width it actually finishes at.
 *
 * Banded on the finished width rounded UP to the whole inch. That is not a
 * rounding convenience, it is what makes the published table continuous: the
 * page says small is "up to 22 inches" and medium is "23-30", so a name
 * finishing at 22.4" has to be medium or the page is wrong. The epsilon keeps
 * a name that measures 22.0000001" because of float arithmetic in the small
 * band, where a tape measure would put it.
 */
export function nameBand(name, font, heightIn) {
  const h = Number(heightIn) || 3;
  const [w] = widthIn(String(name), font, h);
  const billed = Math.ceil(w - 1e-6);
  for (const b of P.NAME_BANDS) {
    if (b.max_in === null || billed <= b.max_in) {
      return { key: b.key, price: b.price, label: b.label,
               width_in: Math.round(w * 10) / 10, billed_in: billed };
    }
  }
  // Unreachable: the last band has max_in null. Here so a hand-edited table
  // with no open-ended band fails loudly instead of returning undefined.
  throw new Error("price-data.js has no open-ended name band");
}

/** The default face, for the lenient path only. */
function fallbackFont() {
  try { widthIn("A", "Arial Bold", 3); return "Arial Bold"; } catch { return null; }
}

/**
 * What the components cost, itemised. priceOf() is the sum of this; the
 * itemisation exists so /api/price and the MCP quote can SHOW the customer
 * why a name is $53 rather than asserting it.
 *
 * `strict` throws on anything it cannot price properly - an unknown product,
 * a name with no text, a font it has no metrics for - instead of quietly
 * charging the cheapest thing we sell. The order path stays lenient on
 * purpose: this repo's standing judgement is that losing a real order over a
 * stale cached page is worse than quietly correcting it, and the order row
 * carries a `mismatch` flag for exactly that case. A quote is different.
 * Nothing is lost by erroring on a quote, and a wrong number told to a
 * customer by an assistant is worse than no number at all - so /api/price and
 * the MCP server ask for strict.
 */
export function priceBreakdown(d, strict = false) {
  const raw = d.kind == null ? "" : String(d.kind);
  const kind = KIND_ALIAS[raw] || KIND_ALIAS[raw.trim()];
  if (!kind) {
    if (strict) {
      throw new Error(`no price for ${JSON.stringify(raw)} - the products are `
        + `numbers, name, both`);
    }
    return priceBreakdown({ ...d, kind: "numbers" }, false);
  }

  const lines = [];
  const notes = [];
  const height = String(d.height || "3");

  if (kind === "numbers" || kind === "both") {
    const add = P.HEIGHT_ADD[height];
    if (add === undefined) {
      if (strict) {
        throw new Error(`no price for a ${JSON.stringify(height)} inch `
          + `character - the heights are `
          + Object.keys(P.HEIGHT_ADD).sort().join(", "));
      }
      notes.push(`height ${height} is not offered; priced at `
        + `${Object.keys(P.HEIGHT_ADD).sort()[0]} inch`);
    }
    lines.push({ what: `Registration numbers, ${height} in`,
                 amount: P.NUMBERS + (add || 0) });
  }

  let band = null;
  if (kind === "name" || kind === "both") {
    // `boatname` is the lettering. `name` on an order row is the CUSTOMER's
    // name, which is why this does not read d.name - pricing a boat by the
    // length of its owner's name is a bug worth naming in a comment.
    const text = String(d.boatname || d.lettering || d.name_text || "").trim();
    const font = String(d.font || "").trim();
    if (!text) {
      if (strict) {
        throw new Error("a boat name is priced by the width it finishes at, "
          + "so quoting one needs the text: pass `boatname`");
      }
      band = { key: P.NAME_BANDS[0].key, price: P.NAME_BANDS[0].price,
               label: P.NAME_BANDS[0].label, width_in: null, billed_in: null };
      notes.push("no lettering supplied; priced in the smallest band");
    } else {
      try {
        band = nameBand(text, font, height);
      } catch (e) {
        if (strict) throw e;
        const fb = fallbackFont();
        if (fb) {
          band = nameBand(text, fb, height);
          notes.push(`no metrics for ${JSON.stringify(font)}; measured in ${fb}`);
        } else {
          band = { key: P.NAME_BANDS[0].key, price: P.NAME_BANDS[0].price,
                   label: P.NAME_BANDS[0].label, width_in: null, billed_in: null };
          notes.push("could not measure the lettering; smallest band");
        }
      }
    }
    lines.push({ what: band.width_in == null
                   ? `Boat name, ${band.label}`
                   : `Boat name, ${band.width_in} in finished (${band.label})`,
                 amount: band.price });
  }

  if (kind === "both") {
    lines.push({ what: "Numbers + name together", amount: -P.BUNDLE_OFF });
  }

  if (d.finish === "outline" || d.outline) {
    lines.push({ what: "Contrasting outline", amount: P.OUTLINE_ADD });
  }

  // Pipe-delimited: an upgrade label may legitimately contain a comma, and
  // splitting on "," silently dropped those line items (and undercharged).
  const up = String(d.upgrades || "");
  const ups = (up.includes("|") ? up.split("|") : up.split(","))
    .map((s) => s.trim()).filter(Boolean);
  for (const u of ups) {
    const add = P.UPGRADE_ADD[u];
    if (add === undefined) {
      if (strict) {
        throw new Error(`no price for the upgrade ${JSON.stringify(u)}`);
      }
      notes.push(`unknown upgrade ${JSON.stringify(u)}; not charged`);
      continue;
    }
    lines.push({ what: u, amount: add });
  }

  const sum = lines.reduce((t, l) => t + l.amount, 0);
  const amount = Math.min(P.MAX, Math.max(P.MIN, Math.round(sum)));
  return { amount, kind, height, lines, band, notes,
           clamped: amount !== Math.round(sum) };
}

export function priceOf(d, strict = false) {
  return priceBreakdown(d, strict).amount;
}

/** Published "from" figures, for copy that needs one without a second copy. */
export const FROM = P.FROM;

/** For the proof email's "Outline" row, which states the upcharge in words. */
export const OUTLINE_ADD = P.OUTLINE_ADD;
