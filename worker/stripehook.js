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
    if (changed && env.ORDER_TO && env.RESEND_API_KEY) {
      // Only when the browser never got back to us - the normal path already
      // told Ryan, and a second email on every order is noise he will learn
      // to ignore.
      await notify(env, ref, obj);
    }
    return json200({ ok: true, ref, updated: changed });
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

async function notify(env, ref, obj) {
  const amount = ((obj.amount_received || obj.amount || 0) / 100).toFixed(2);
  try {
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`,
                 "Content-Type": "application/json" },
      body: JSON.stringify({
        from: env.ORDER_FROM || "orders@numbermyboat.com",
        to: [env.ORDER_TO],
        subject: `Payment confirmed by Stripe - ${ref} - $${amount}`,
        html: `<p><b>${ref}</b> is paid ($${amount}), confirmed by Stripe `
          + `rather than by the customer's browser.</p><p>That means they paid `
          + `and then lost the page before it could tell us - so the order was `
          + `sitting unpaid. It is marked paid now. Nothing else to do.</p>`,
      }),
    });
  } catch (err) { console.error("webhook notify failed", err && err.message); }
}
