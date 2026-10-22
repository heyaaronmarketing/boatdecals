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

  const o = {
    ref: ref(),
    kind: str(d.kind, 40) || "Registration numbers",
    text: str(d.text, 60),
    boatname: str(d.boatname, 60),
    payment: str(d.payment, 40),
    paid: d.paid ? 1 : 0,
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
  o.total = priceOf(o);
  // A mismatch means the client is stale or tampered with. Log it, trust ours.
  o.mismatch = o.quoted && o.quoted !== o.total ? 1 : 0;

  if (env.DB) {
    try {
      if (reuse && o.paid) {
        await env.DB.prepare(
          `UPDATE orders SET paid=1, payment=?, status='paid' WHERE ref=?`
        ).bind(o.payment, o.ref).run();
      } else {
        await env.DB.prepare(
          `INSERT INTO orders (ref,kind,text,boatname,state,height,font,color,upgrades,
             name,email,phone,boat,notes,page,total,quoted,mismatch,paid,payment,
             ua,country,ts)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
        ).bind(o.ref, o.kind, o.text, o.boatname, o.state, o.height, o.font, o.color,
               o.upgrades, o.name, o.email, o.phone, o.boat, o.notes, o.page, o.total,
               o.quoted, o.mismatch, o.paid, o.payment, o.ua, o.country, o.ts).run();
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
      ["State", o.state], ["Height", o.height + '"'], ["Font", o.font],
      ["Colour", o.color], ["Upgrades", o.upgrades || "none"],
      ["Price", "$" + o.total], ["Customer", o.name], ["Email", o.email],
      ["Phone", o.phone || "-"], ["Boat", o.boat || "-"],
      ["Notes", o.notes || "-"], ["From page", o.page],
    ];
    const body =
      `<h2>New order ${o.ref} - $${o.total}</h2>` +
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
          subject: `Order ${o.ref} - ${o.kind} - $${o.total}`,
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
                    stripe: !!env.STRIPE_SECRET_KEY });
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
