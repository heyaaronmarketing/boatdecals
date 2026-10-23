/**
 * Boat Number Shop worker.
 *
 * Serves the static build from ASSETS and handles /api/order.
 *
 * The browser computes a price for instant feedback; this file recomputes it
 * from scratch and that figure is the authority. Never trust a posted total.
 */

const BASE = {
  "Registration numbers": 19,
  "Boat name": 29,
  "Both": 44,
  // kept so older cached pages still price correctly
  "Numbers + name": 44,
  "Something else": 22,
};
const HEIGHT_ADD = { "3": 0, "4": 4, "5": 8, "6": 13 };
const UPGRADE_ADD = {
  "Premium 8-year cast vinyl": 8,
  "Spare set - a second pair at half price": 9,
  "Install kit - squeegee + solution + tape": 6,
  "Rush - cut and shipped today": 12,
  "Hailing port line": 15,
  "Reflective finish": 10,
};
const BASE_MIN = 19, BASE_MAX = 200;

// 33 CFR 173.27 requires plain vertical block characters on a registration
// number. The form only offers these five, but a stale cached page or a
// hand-built POST could still ask for a script face - and cutting one would
// be illegal. Coerce rather than reject: losing a real order over a cached
// page is worse than quietly correcting the font and flagging it on the
// proof the customer has to approve anyway.
const BLOCK_FONTS = ["Block", "Condensed", "Heavy Impact", "Modern", "Stencil"];

function priceOf(d) {
  let n = BASE[d.kind] ?? 19;
  n += HEIGHT_ADD[String(d.height || "3")] ?? 0;
  // Pipe-delimited: an upgrade label may legitimately contain a comma, and
  // splitting on "," silently dropped those line items (and undercharged).
  const raw = String(d.upgrades || "");
  const ups = (raw.includes("|") ? raw.split("|") : raw.split(","))
    .map(s => s.trim()).filter(Boolean);
  for (const u of ups) n += UPGRADE_ADD[u] ?? 0;
  return Math.min(BASE_MAX, Math.max(BASE_MIN, Math.round(n)));
}

const str = (v, max) => String(v == null ? "" : v).slice(0, max).trim();
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/;

/**
 * Defence in depth against a PAN ever reaching storage.
 *
 * The sandbox card form is built to send only {brand, last4}, but a future edit
 * there must not be able to quietly start leaking a full number. Any posted
 * value carrying a 13-19 digit run is rejected outright, and the whole request
 * is refused rather than silently scrubbed - a silent scrub would hide the
 * regression that caused it.
 */
const PAN = /(?:\d[ -]?){13,19}/;
function carriesCardNumber(d) {
  for (const [k, v] of Object.entries(d || {})) {
    if (typeof v !== "string" && typeof v !== "number") continue;
    // The lettering field is legitimately short; notes are free text. Neither
    // should ever contain a card-length digit run.
    if (k === "card_last4" || k === "quoted_total") continue;
    if (PAN.test(String(v))) return k;
  }
  return null;
}

function ref() {
  // Short, human-readable, says it on the phone without spelling.
  const a = "BNS";
  const n = Math.floor(Math.random() * 46656).toString(36).toUpperCase().padStart(3, "0");
  const d = new Date();
  return `${a}-${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}-${n}`;
}

async function handleOrder(request, env) {
  let d;
  try { d = await request.json(); }
  catch { return json({ error: "bad request" }, 400); }

  const leak = carriesCardNumber(d);
  if (leak) {
    console.error("refused: card-number-shaped value in field", leak);
    return json({ error: "card details must never be sent to this endpoint" }, 400);
  }

  const o = {
    ref: ref(),
    kind: str(d.kind, 40) || "Registration numbers",
    text: str(d.text, 60),
    boatname: str(d.boatname, 60),
    payment: str(d.payment, 40),
    paid: d.paid ? 1 : 0,
    test_mode: d.test_mode ? 1 : 0,
    // last4 and brand only - there is no field here for a full number by design.
    card_brand: str(d.card_brand, 20),
    card_last4: str(d.card_last4, 4).replace(/\D/g, ""),
    state: str(d.state, 40),
    height: str(d.height, 4) || "3",
    font: str(d.font, 50),
    color: str(d.color, 40),
    upgrades: str(d.upgrades, 300),
    name: str(d.name, 80),
    email: str(d.email, 120),
    phone: str(d.phone, 30),
    boat: str(d.boat, 80),
    notes: str(d.notes, 1200),
    page: str(d.page, 120),
    quoted: Number(d.quoted_total) || 0,
    ua: str(request.headers.get("user-agent"), 200),
    country: request.headers.get("cf-ipcountry") || "",
    ts: new Date().toISOString(),
  };

  // "Both" and "Boat name" carry the lettering in boatname, not text.
  if ((!o.text && !o.boatname) || !o.name || !EMAIL.test(o.email)) {
    return json({ error: "missing lettering, name or a valid email" }, 422);
  }
  // A confirmation POST re-uses the reference the first POST handed back, so the
  // two halves of a card order stay one row rather than two.
  const reuse = str(d.ref, 24);
  if (reuse) o.ref = reuse;
  if (o.kind === "Registration numbers" && o.font && !BLOCK_FONTS.includes(o.font)) {
    o.font_requested = o.font;
    o.font = BLOCK_FONTS[0];
  }
  o.total = priceOf(o);
  // A mismatch means the client is stale or tampered with. Log it, trust ours.
  o.mismatch = o.quoted && o.quoted !== o.total ? 1 : 0;

  if (env.DB) {
    try {
      if (reuse && o.paid) {
        await env.DB.prepare(
          `UPDATE orders SET paid=1, payment=?, status=? WHERE ref=?`
        ).bind(o.payment, o.test_mode ? "test" : "paid", o.ref).run();
      } else {
        await env.DB.prepare(
          `INSERT INTO orders (ref,kind,text,boatname,state,height,font,color,upgrades,
             name,email,phone,boat,notes,page,total,quoted,mismatch,paid,payment,
             ua,country,ts
           ,test_mode,card_brand,card_last4,status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
        ).bind(o.ref, o.kind, o.text, o.boatname, o.state, o.height, o.font, o.color,
               o.upgrades, o.name, o.email, o.phone, o.boat, o.notes, o.page, o.total,
               o.quoted, o.mismatch, o.paid, o.payment, o.ua, o.country, o.ts,
               o.test_mode, o.card_brand, o.card_last4,
               // `paid` stays the real-money flag, so SUM(total) WHERE paid=1 is
               // correct with no test-exclusion needed. Sandbox orders are never
               // paid=1; `status` is what makes them visible in the queue.
               o.test_mode ? "test" : (o.paid ? "paid" : "new")).run();
      }
    } catch (err) {
      console.error("d1 insert failed", err && err.message);
      // Keep going - an unsaved row is recoverable from the email, a lost
      // customer is not.
    }
  }

  // The confirmation POST would otherwise send a duplicate shop email.
  if (reuse && o.paid) return json({ ok: true, ref: o.ref, total: o.total, paid: 1 });

  if (env.RESEND_API_KEY && env.ORDER_TO) {
    const rows = [
      ["Reference", o.ref], ["Product", o.kind],
      ["Lettering", [o.text, o.boatname].filter(Boolean).join("  |  ")],
      ["State", o.state], ["Height", o.height + '"'],
      ["Font", o.font_requested
        ? `${o.font} - customer asked for ${o.font_requested}, which is not legal `
          + `on a registration number. Corrected automatically; confirm on the proof.`
        : o.font],
      ["Colour", o.color],
      ["Upgrades", o.upgrades || "none"],
      ["Price", "$" + o.total],
      ["Payment", o.test_mode
        ? `TEST MODE - no money taken (${o.card_brand || "card"} ending ${o.card_last4 || "----"})`
        : (o.paid ? `Paid (${o.card_brand} ending ${o.card_last4})` : "Payment link to send")],
      ["Customer", o.name], ["Email", o.email],
      ["Phone", o.phone || "-"], ["Boat", o.boat || "-"],
      ["Notes", o.notes || "-"], ["From page", o.page],
    ];
    const body =
      (o.test_mode
        ? `<p style="background:#fff7e6;border-left:4px solid #d08700;padding:10px 13px;
             font:14px system-ui;margin:0 0 14px"><strong>TEST ORDER.</strong> This came
             from the sandbox checkout. No payment was taken and no card was stored.
             Do not cut it.</p>`
        : "") +
      `<h2>${o.test_mode ? "[TEST] " : ""}New order ${o.ref} - $${o.total}</h2>` +
      (o.mismatch ? `<p style="color:#b0202f"><strong>Price mismatch:</strong> browser
        quoted $${o.quoted}, server says $${o.total}. Check before you invoice.</p>` : "") +
      `<table cellpadding="6" style="border-collapse:collapse;font:14px system-ui">` +
      rows.map(([k, v]) =>
        `<tr><td style="border-bottom:1px solid #ddd"><b>${esc(k)}</b></td>
             <td style="border-bottom:1px solid #ddd">${esc(v)}</td></tr>`).join("") +
      `</table>`;
    try {
      await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`,
                   "Content-Type": "application/json" },
        body: JSON.stringify({
          from: env.ORDER_FROM || "orders@boatnumbershop.com",
          to: [env.ORDER_TO], reply_to: o.email,
          subject: `${o.test_mode ? "[TEST] " : ""}Order ${o.ref} - ${o.kind} - $${o.total}`,
          html: body,
        }),
      });
    } catch (err) { console.error("resend failed", err && err.message); }
  }

  return json({ ok: true, ref: o.ref, total: o.total });
}

const esc = s => String(s).replace(/[&<>"]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const json = (o, status = 200) => new Response(JSON.stringify(o), {
  status, headers: { "content-type": "application/json; charset=utf-8",
                     "cache-control": "no-store" },
});

/**
 * Creates a Stripe PaymentIntent for the amount WE calculate, never the amount
 * the browser sends - the posted figure is only used to detect a stale page.
 */
async function handleCheckout(request, env) {
  if (!env.STRIPE_SECRET_KEY) return json({ error: "stripe not configured" }, 503);
  let d;
  try { d = await request.json(); } catch { return json({ error: "bad request" }, 400); }

  const amount = priceOf(d.order || d);
  const body = new URLSearchParams({
    amount: String(amount * 100),
    currency: "usd",
    "automatic_payment_methods[enabled]": "true",
    description: `Boat Number Shop - ${d.kind || "custom lettering"}`,
  });
  try {
    const r = await fetch("https://api.stripe.com/v1/payment_intents", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
                 "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const pi = await r.json();
    if (!r.ok) {
      console.error("stripe intent failed", pi && pi.error && pi.error.message);
      return json({ error: "payment setup failed" }, 502);
    }
    return json({ clientSecret: pi.client_secret, amount });
  } catch (err) {
    console.error("stripe unreachable", err && err.message);
    return json({ error: "payment setup failed" }, 502);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/order") {
      if (request.method !== "POST") return json({ error: "POST only" }, 405);
      return handleOrder(request, env);
    }
    if (url.pathname === "/api/checkout") {
      if (request.method !== "POST") return json({ error: "POST only" }, 405);
      return handleCheckout(request, env);
    }
    if (url.pathname === "/api/health") {
      return json({ ok: true, db: !!env.DB, email: !!env.RESEND_API_KEY,
                    stripe: !!env.STRIPE_SECRET_KEY,
                    pay_mode: env.STRIPE_SECRET_KEY ? "stripe" : "sandbox" });
    }

    const res = await env.ASSETS.fetch(request);
    // Static HTML is cheap to regenerate and we deploy often; keep it short so a
    // price change is not stuck in a CDN for a day.
    if (res.headers.get("content-type")?.includes("text/html")) {
      const h = new Headers(res.headers);
      h.set("cache-control", "public, max-age=0, s-maxage=300, must-revalidate");
      return new Response(res.body, { status: res.status, headers: h });
    }
    return res;
  },
};
