/**
 * The proof cycle.
 *
 * Every order is promised a proof within twelve hours. This sends it, chases
 * it up to three times, and records the approval. Nothing is cut until
 * `approved_at` is set - that is the whole point of the cycle, and it is the
 * one thing the shop email now leads with.
 *
 * There is no queue. The schedule IS the timestamps on the order row, so a
 * missed cron run catches up on the next one instead of dropping anybody, and
 * the same order can never be picked up twice because the send stamps the row
 * inside the same request.
 *
 * WHAT IS AUTOMATED AND WHAT IS NOT. The proof image, the sending and the
 * chasing are automatic. The claim on the page is only ever that we send a
 * proof and wait for approval, which is exactly true. Nothing says a person
 * drew it, because nobody did.
 */

const HOURS = 3600e3;
// Twelve hours is the promise, so send at eleven: a cron that fires on the
// hour would otherwise land the "within 12 hours" email at 12h59m.
const PROOF_AFTER = 11 * HOURS;
const NUDGES = [24 * HOURS, 72 * HOURS, 144 * HOURS];
const MAX_NUDGES = NUDGES.length;

const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;")
  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** Unguessable, and not derived from anything in the row. */
function token() {
  const b = new Uint8Array(16);
  crypto.getRandomValues(b);
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

function lettering(o) {
  return [o.text, o.boatname].filter(Boolean).join("  /  ");
}

function proofUrl(env, o) {
  const base = env.SITE_URL || "https://numbermyboat.com";
  return `${base}/proof/?r=${encodeURIComponent(o.ref)}&t=${o.proof_token}`;
}

function specRows(o) {
  const rows = [
    ["Lettering", lettering(o)],
    ["Product", o.kind],
    ["Height", o.height + '"'],
    ["Font", o.font],
    ["Colour", o.outline_color
      ? `${o.color} with a ${o.outline_color} outline` : o.color],
    ["Price", "$" + o.total],
  ];
  return rows.map(([k, v]) =>
    `<tr><td style="padding:7px 14px 7px 0;color:#5b7383;font-size:14px">${esc(k)}</td>` +
    `<td style="padding:7px 0;font-size:15px;font-weight:700;color:#0e2430">${esc(v)}</td></tr>`
  ).join("");
}

/**
 * The lettering, drawn in the email itself.
 *
 * Deliberately a table and a web font rather than an inline SVG or a canvas:
 * Gmail strips SVG entirely, and a customer who cannot see the proof cannot
 * approve it. If the web font does not load the fallback still shows the
 * right characters at the right size, which is the part that has to be
 * checked. The proof page renders it properly.
 */
function letteringBlock(o) {
  return (
    `<div style="background:#eef3f6;border:1px solid #cfdde6;border-radius:10px;` +
    `padding:26px 18px;text-align:center;margin:0 0 20px">` +
    `<div style="font-family:'Arial Black',Arial,Helvetica,sans-serif;` +
    `font-weight:900;font-size:30px;letter-spacing:1px;color:#111;` +
    `word-break:break-word">${esc(lettering(o))}</div>` +
    `<div style="font-size:12px;color:#5b7383;margin-top:12px">` +
    `${esc(o.height)}" tall &middot; ${esc(o.font)} &middot; ${esc(o.color)}</div>` +
    `</div>`
  );
}

function button(href, label) {
  return `<a href="${href}" style="display:inline-block;background:#2f6f43;` +
    `color:#fff;font-weight:800;font-size:16px;text-decoration:none;` +
    `padding:14px 26px;border-radius:9px">${esc(label)}</a>`;
}

function shell(inner) {
  return `<div style="font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;` +
    `color:#0e2430;max-width:560px;margin:0 auto;padding:4px 2px">${inner}` +
    `<p style="font-size:12.5px;color:#5b7383;border-top:1px solid #dde7ed;` +
    `margin-top:26px;padding-top:14px">Number My Boat &middot; cut in ` +
    `Evansdale, Iowa. Reply to this email and it reaches us.</p></div>`;
}

function proofEmail(env, o) {
  const url = proofUrl(env, o);
  return {
    subject: `Your proof for order ${o.ref} - approve to start cutting`,
    html: shell(
      `<h2 style="font-size:21px;margin:0 0 6px">Here is your proof</h2>` +
      `<p style="margin:0 0 18px;color:#44606f">Check every character against ` +
      `your registration card. This is exactly what the plotter cuts.</p>` +
      letteringBlock(o) +
      `<table style="border-collapse:collapse;margin:0 0 22px">${specRows(o)}</table>` +
      `<p style="margin:0 0 18px">${button(url, "Approve this proof")}</p>` +
      `<p style="margin:0 0 6px;color:#44606f">Something not right? ` +
      `<a href="${url}&c=1" style="color:#1b6382">Tell us what to change</a> ` +
      `&mdash; or just reply to this email.</p>` +
      `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">Once you ` +
      `approve, it is cut, packed and posted within 1-2 business days. ` +
      `Nothing is cut before then.</p>`),
  };
}

function nudgeEmail(env, o, n) {
  const url = proofUrl(env, o);
  const lead = [
    `Your proof is still waiting`,
    `Still waiting on your approval`,
    `Last reminder about order ${o.ref}`,
  ][n] || `Your proof is still waiting`;
  const tail = n >= 2
    ? `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">This is the ` +
      `last reminder we will send. The order stays open - approve whenever ` +
      `you are ready and we will cut it then.</p>`
    : `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">Nothing is ` +
      `cut until you approve it, so the order is simply sitting here.</p>`;
  return {
    subject: `${lead} - ${o.ref}`,
    html: shell(
      `<h2 style="font-size:21px;margin:0 0 6px">${esc(lead)}</h2>` +
      `<p style="margin:0 0 18px;color:#44606f">One tap and it goes to the ` +
      `plotter. Check the characters first.</p>` +
      letteringBlock(o) +
      `<p style="margin:0 0 18px">${button(url, "Approve this proof")}</p>` +
      `<p style="margin:0 0 6px;color:#44606f">Need a change? ` +
      `<a href="${url}&c=1" style="color:#1b6382">Tell us</a> or reply here.</p>` +
      tail),
  };
}

async function send(env, to, mail, replyTo) {
  if (!env.RESEND_API_KEY) return false;
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`,
               "Content-Type": "application/json" },
    body: JSON.stringify({
      from: env.ORDER_FROM || "orders@numbermyboat.com",
      to: [to], reply_to: replyTo || env.ORDER_TO || undefined,
      subject: mail.subject, html: mail.html,
    }),
  });
  return r.ok;
}

/**
 * One pass of the cycle. Safe to run as often as you like: every candidate is
 * chosen by a timestamp and stamped the moment it is sent.
 */
export async function runProofCycle(env, nowMs) {
  if (!env.DB) return { sent: 0, nudged: 0, skipped: "no db" };
  const now = nowMs == null ? Date.now() : nowMs;
  const iso = new Date(now).toISOString();
  let sent = 0, nudged = 0;

  const due = await env.DB.prepare(
    `SELECT * FROM orders
      WHERE proof_sent_at IS NULL AND approved_at IS NULL
        AND test_mode = 0 AND email IS NOT NULL AND email <> ''
      ORDER BY id LIMIT 40`).all();

  for (const o of (due.results || [])) {
    if (now - Date.parse(o.ts) < PROOF_AFTER) continue;
    const t = o.proof_token || token();
    const ok = await send(env, o.email, proofEmail(env, { ...o, proof_token: t }));
    if (!ok) continue;
    await env.DB.prepare(
      `UPDATE orders SET proof_token=?, proof_sent_at=?, status=? WHERE id=?`
    ).bind(t, iso, "proof-sent", o.id).run();
    sent++;
  }

  const waiting = await env.DB.prepare(
    `SELECT * FROM orders
      WHERE proof_sent_at IS NOT NULL AND approved_at IS NULL
        AND changes_at IS NULL AND test_mode = 0
        AND COALESCE(proof_nudges,0) < ?
      ORDER BY id LIMIT 40`).bind(MAX_NUDGES).all();

  for (const o of (waiting.results || [])) {
    const n = o.proof_nudges || 0;
    const since = Date.parse(o.proof_nudged_at || o.proof_sent_at);
    if (now - since < NUDGES[n]) continue;
    const ok = await send(env, o.email, nudgeEmail(env, o, n));
    if (!ok) continue;
    await env.DB.prepare(
      `UPDATE orders SET proof_nudges=?, proof_nudged_at=? WHERE id=?`
    ).bind(n + 1, iso, o.id).run();
    nudged++;
  }

  return { sent, nudged };
}

/** GET /api/approve?r=REF&t=TOKEN[&c=1] - the link in the email. */
export async function handleApprove(request, env) {
  const url = new URL(request.url);
  const ref = url.searchParams.get("r") || "";
  const tok = url.searchParams.get("t") || "";
  const wantsChange = url.searchParams.get("c") === "1";
  const note = (url.searchParams.get("note") || "").slice(0, 600);
  if (!env.DB || !ref || !tok) return { ok: false, error: "bad link" };

  const o = await env.DB.prepare(
    `SELECT * FROM orders WHERE ref=? LIMIT 1`).bind(ref).first();
  // Compared in full, and only after the row is found, so a wrong token and a
  // wrong reference are the same answer either way.
  if (!o || !o.proof_token || o.proof_token !== tok) {
    return { ok: false, error: "bad link" };
  }

  const iso = new Date().toISOString();
  if (wantsChange) {
    await env.DB.prepare(
      `UPDATE orders SET changes_at=?, changes_note=?, status=? WHERE id=?`
    ).bind(iso, note, "changes-requested", o.id).run();
    if (env.ORDER_TO) {
      await send(env, env.ORDER_TO, {
        subject: `CHANGES REQUESTED - ${o.ref}`,
        html: shell(`<h2>${esc(o.ref)}: the customer wants a change</h2>` +
          `<p><b>${esc(o.name || "")}</b> &lt;${esc(o.email)}&gt;</p>` +
          `<p style="background:#fff7e6;border-left:4px solid #d08700;` +
          `padding:10px 13px">${esc(note || "(no note left)")}</p>` +
          `<table style="border-collapse:collapse">${specRows(o)}</table>` +
          `<p><b>Do not cut this.</b></p>`),
      }, o.email);
    }
    return { ok: true, state: "changes", ref: o.ref };
  }

  if (!o.approved_at) {
    await env.DB.prepare(
      `UPDATE orders SET approved_at=?, status=? WHERE id=?`
    ).bind(iso, "approved", o.id).run();
    if (env.ORDER_TO) {
      await send(env, env.ORDER_TO, {
        subject: `APPROVED - cut ${o.ref} - ${lettering(o)}`,
        html: shell(`<h2>${esc(o.ref)} is approved</h2>` +
          `<p>Cut, pack and post within 1-2 business days.</p>` +
          letteringBlock(o) +
          `<table style="border-collapse:collapse">${specRows(o)}</table>` +
          `<p>${esc(o.name || "")} &lt;${esc(o.email)}&gt;</p>`),
      }, o.email);
    }
    await send(env, o.email, {
      subject: `Approved - ${o.ref} goes to the plotter`,
      html: shell(`<h2 style="font-size:21px;margin:0 0 6px">Thanks - that is ` +
        `approved</h2><p style="margin:0 0 18px;color:#44606f">It is cut, ` +
        `packed and posted within 1-2 business days.</p>` +
        letteringBlock(o) +
        `<p style="font-size:13.5px;color:#5b7383">Spotted something after ` +
        `all? Reply today with ${esc(o.ref)} and we can almost always stop ` +
        `it before the plotter runs.</p>`),
    });
  }
  return { ok: true, state: "approved", ref: o.ref };
}

/** GET /api/proof?r=REF&t=TOKEN - what the proof page renders from. */
export async function handleProofData(request, env) {
  const url = new URL(request.url);
  const ref = url.searchParams.get("r") || "";
  const tok = url.searchParams.get("t") || "";
  if (!env.DB || !ref || !tok) return { ok: false };
  const o = await env.DB.prepare(
    `SELECT * FROM orders WHERE ref=? LIMIT 1`).bind(ref).first();
  if (!o || !o.proof_token || o.proof_token !== tok) return { ok: false };
  // Only what the proof has to show. No email, no name, no address: the link
  // is unguessable but it still travels through an inbox, and a forwarded
  // one should not hand over the customer's details.
  return {
    ok: true, ref: o.ref, kind: o.kind, text: o.text || "",
    boatname: o.boatname || "", height: o.height, font: o.font,
    color: o.color, outline_color: o.outline_color || "",
    total: o.total, state: o.state || "",
    approved: !!o.approved_at, changes: !!o.changes_at,
  };
}
