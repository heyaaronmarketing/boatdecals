/**
 * Stripe webhooks.
 *
 * The browser flow marks an order paid with a second POST after the card
 * clears. If the customer closes the tab, loses signal or the phone dies in
 * between, the money is taken and the order still reads paid=0 - a paid job
 * sitting in the queue looking unpaid, found only by cross-checking the
 * Stripe dashboard by hand.
 *
 * This closes that: Stripe tells us server to server, so the record does not
 * depend on the customer's browser surviving the round trip.
 *
 * SIGNATURE VERIFICATION IS THE WHOLE SECURITY MODEL. Without it this is a
 * public endpoint that marks any order paid for anybody who can spell the
 * reference. It is verified against the raw body - not a re-serialised copy,
 * because JSON.stringify will not reproduce Stripe's byte order and every
 * signature would fail.
 */

const enc = new TextEncoder();

/** Constant-time compare, so a wrong signature cannot be found a byte at a time. */
function sameBytes(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function hmacHex(secret, payload) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" },
    false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  return [...new Uint8Array(sig)]
    .map((b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Verifies Stripe's `t=...,v1=...` header against the raw body.
 *
 * The timestamp check is replay protection: a signature stays valid forever
 * otherwise, so a captured request could be replayed to re-mark an order.
 */
export async function verifyStripe(raw, header, secret, nowMs) {
  if (!header || !secret) return false;
  const parts = Object.fromEntries(
    header.split(",").map((p) => p.split("=").map((x) => x.trim())));
  const t = Number(parts.t);
  if (!t || !parts.v1) return false;
  const age = Math.abs((nowMs == null ? Date.now() : nowMs) / 1000 - t);
  if (age > 300) return false;
  return sameBytes(await hmacHex(secret, `${t}.${raw}`), parts.v1);
}

/**
 * The shipping address Stripe collected, flattened.
 *
 * A Checkout Session with shipping_address_collection saves the address onto
 * the PaymentIntent's `shipping`, so payment_intent.succeeded carries it. That
 * matters for the pay-by-link path: those orders predate the address fields on
 * the form, so the only copy of where to post the parcel is the one Stripe
 * just collected. Ignoring it leaves the address in the Stripe dashboard and
 * nowhere else - a paid order with a blank "Ship to" on Ryan's email.
 *
 * `shipping` is also absent on perfectly ordinary intents, because the site's
 * own checkout already holds the address. Hence null rather than empty
 * strings: the caller must not overwrite a good address with blanks.
 */
function shippingOf(obj) {
  // A PaymentIntent calls it `shipping`; a Checkout Session calls the same
  // thing `shipping_details`, and newer API versions nest it under
  // `collected_information`. Which event arrives depends on what is ticked in
  // the Stripe dashboard, which is not something this code can see - so it
  // reads all three rather than betting on one.
  const ci = obj && obj.collected_information;
  const s = (obj && (obj.shipping || obj.shipping_details))
    || (ci && ci.shipping_details);
  const a = s && s.address;
  if (!a || !a.line1) return null;
  const t = (v) => String(v == null ? "" : v).slice(0, 120);
  return {
    name: t(s.name), line1: t(a.line1), line2: t(a.line2),
    city: t(a.city), state: t(a.state), zip: t(a.postal_code),
  };
}

export async function handleStripeWebhook(request, env) {
  if (request.method !== "POST") return new Response("POST only", { status: 405 });
  if (!env.STRIPE_WEBHOOK_SECRET) {
    return new Response("not configured", { status: 503 });
  }
  const raw = await request.text();
  const ok = await verifyStripe(raw, request.headers.get("Stripe-Signature"),
                                env.STRIPE_WEBHOOK_SECRET);
  if (!ok) return new Response("bad signature", { status: 400 });

  let ev;
  try { ev = JSON.parse(raw); } catch { return new Response("bad json", { status: 400 }); }

  const obj = (ev.data && ev.data.object) || {};
  const intent = obj.id || "";

  // Always 200 for events we do not act on. A non-2xx makes Stripe retry for
  // days over something we were never going to do anything about.
  if (!env.DB) return json200({ ok: true, ignored: ev.type });

  // A PaymentIntent carries our metadata; a Charge does NOT. Stripe does not
  // copy metadata from the intent onto the charge it creates, so a refund or
  // dispute arrives with metadata.ref empty and has to be matched the other
  // way - through the intent id stored on the order when it was paid.
  let ref = (obj.metadata && obj.metadata.ref) || "";
  if (!ref && obj.payment_intent) {
    const row = await env.DB.prepare(
      `SELECT ref FROM orders WHERE payment = ? LIMIT 1`
    ).bind("stripe:" + String(obj.payment_intent)).first();
    if (row) ref = row.ref;
  }
  if (!ref) return json200({ ok: true, ignored: ev.type, reason: "no ref" });

  if (ev.type === "payment_intent.succeeded") {
    // Idempotent by construction: Stripe retries, and the same event must not
    // produce a second anything. WHERE paid=0 means a replay changes nothing.
    const r = await env.DB.prepare(
      `UPDATE orders SET paid=1, payment=?, status=?
        WHERE ref=? AND COALESCE(paid,0)=0`
    ).bind(intent ? `stripe:${intent}` : "stripe", "paid", ref).run();
    const changed = (r.meta && r.meta.changes) || 0;

    // Only when we have nothing. The site's own checkout collects a validated
    // address and must win over whatever was typed into Stripe afterwards.
    const ship = shippingOf(obj);
    if (ship) {
      await env.DB.prepare(
        `UPDATE orders SET ship_line1=?, ship_line2=?, ship_city=?,
                           ship_state=?, ship_zip=?
          WHERE ref=? AND COALESCE(ship_line1,'')=''`
      ).bind(ship.line1, ship.line2, ship.city, ship.state, ship.zip, ref).run();
    }

    if (changed && env.ORDER_TO && env.RESEND_API_KEY) {
      // Only when the browser never got back to us - the normal path already
      // told Ryan, and a second email on every order is noise he will learn
      // to ignore.
      await notify(env, ref, obj, ship);
    }
    return json200({ ok: true, ref, updated: changed });
  }

  // The other event that can carry the address. Harmless if the dashboard
  // never sends it; the guards below make a duplicate a no-op.
  if (ev.type === "checkout.session.completed") {
    const ship = shippingOf(obj);
    if (ship) {
      await env.DB.prepare(
        `UPDATE orders SET ship_line1=?, ship_line2=?, ship_city=?,
                           ship_state=?, ship_zip=?
          WHERE ref=? AND COALESCE(ship_line1,'')=''`
      ).bind(ship.line1, ship.line2, ship.city, ship.state, ship.zip, ref).run();
    }
    // Only a session that actually took the money. An expired or unpaid
    // session must never mark an order paid.
    if (obj.payment_status === "paid") {
      await env.DB.prepare(
        `UPDATE orders SET paid=1, payment=?, status=?
          WHERE ref=? AND COALESCE(paid,0)=0`
      ).bind(obj.payment_intent ? `stripe:${obj.payment_intent}` : "stripe",
             "paid", ref).run();
    }
    return json200({ ok: true, ref, address: !!ship });
  }

  if (ev.type === "charge.refunded" || ev.type === "charge.dispute.created") {
    await env.DB.prepare(
      `UPDATE orders SET status=? WHERE ref=?`
    ).bind(ev.type === "charge.refunded" ? "refunded" : "disputed", ref).run();
    return json200({ ok: true, ref, status: ev.type });
  }

  return json200({ ok: true, ignored: ev.type });
}

function json200(o) {
  return new Response(JSON.stringify(o),
    { headers: { "Content-Type": "application/json" } });
}

async function notify(env, ref, obj, ship) {
  const amount = ((obj.amount_received || obj.amount || 0) / 100).toFixed(2);
  try {
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`,
                 "Content-Type": "application/json" },
      body: JSON.stringify({
        from: env.ORDER_FROM || "orders@numbermyboat.com",
        to: [env.ORDER_TO],
        // Same copy Aaron gets on the order itself.
        ...(env.ORDER_BCC ? { bcc: [env.ORDER_BCC] } : {}),
        subject: `Payment confirmed by Stripe - ${ref} - $${amount}`,
        html: `<p><b>${ref}</b> is paid ($${amount}), confirmed by Stripe `
          + `rather than by the customer's browser.</p><p>That means they paid `
          + `and then lost the page before it could tell us - so the order was `
          + `sitting unpaid. It is marked paid now.</p>`
          // Printed here too: for a pay-by-link order this email is the first
          // place the address appears outside Stripe.
          + (ship
            ? `<p><b>Ship to</b><br>${esc(ship.name)}<br>${esc(ship.line1)}<br>`
              + (ship.line2 ? `${esc(ship.line2)}<br>` : "")
              + `${esc(ship.city)}, ${esc(ship.state)} ${esc(ship.zip)}</p>`
              + `<p>Collected by Stripe at checkout and saved onto the order.</p>`
            : `<p>No address came with this payment. If the order has none on `
              + `it either, it cannot be posted - look it up in Stripe before `
              + `cutting anything.</p>`),
      }),
    });
  } catch (err) { console.error("webhook notify failed", err && err.message); }
}

/** Addresses are customer-typed and this is HTML email. */
function esc(v) {
  return String(v == null ? "" : v)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
