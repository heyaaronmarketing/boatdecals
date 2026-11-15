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
 *
 * AUTO-APPROVAL AFTER FIVE BUSINESS DAYS (Aaron's call, 2026-11-15).
 *
 * What it does and does not do is the whole thing. It does NOT cut anything
 * and it does NOT take any money, because in this shop the payment link
 * follows approval - it marks the proof accepted so the order can be
 * invoiced, and the customer still has to pay before a single inch of vinyl
 * is cut. Paying is a second, explicit consent. That is what makes a
 * five-day rule defensible here when it would not be in a shop that charged
 * the card up front.
 *
 * It is disclosed three times before it can fire - a checkbox at checkout,
 * the order confirmation, and every reminder names the date - and it is
 * refused outright when the order is anything other than routine:
 *
 *   - the customer unticked it at checkout
 *   - a change was requested
 *   - the validator flagged the registration number (a human looks at those)
 *   - the row predates number_flag, so we cannot tell whether it was flagged
 *   - fewer than three reminders have gone out
 *   - RESEND CANNOT CONFIRM THE PROOF WAS DELIVERED
 *
 * That last one carries the most weight and is the reason this is sound
 * rather than merely permitted. Silence is not consent if the email went to
 * spam, so the deadline runs off DELIVERY, not off sending. While ORDER_FROM
 * is an unverified sending domain this will mostly decline to fire, which is
 * the correct behaviour and not a bug to work around.
 */

const HOURS = 3600e3;
// Twelve hours is the promise, so send at eleven: a cron that fires on the
// hour would otherwise land the "within 12 hours" email at 12h59m.
const PROOF_AFTER = 11 * HOURS;
// Retimed so the last reminder lands the day BEFORE the auto-approval
// deadline instead of four days after it. Cumulative from the previous send:
// day 1, day 3, day 4. The old [24, 72, 144] put the final warning on day 10,
// which would have been a last chance offered after the chance had gone.
//
// The ceiling is not arbitrary, and it is not what I first wrote. Five
// business days is 5 CALENDAR days at its shortest - a proof delivered on a
// Sunday falls due that Friday - so the three reminders have to finish inside
// 120 hours, not the 144 I assumed from the Saturday case. 24+48+24 = 96h,
// which leaves a day of daylight in the worst case and three in the usual
// one. mcp/test_autoapprove.mjs walks all seven starting weekdays and the
// verifier checks the sum against the floor.
const NUDGES = [24 * HOURS, 48 * HOURS, 24 * HOURS];
const MAX_NUDGES = NUDGES.length;

// Five BUSINESS days. A proof delivered on Thursday evening has not been
// ignored for five days by Tuesday morning, and a calendar week would quietly
// charge the customer two of their weekends.
const AUTO_APPROVE_DAYS = 5;

/** The instant `days` business days after `fromIso`. Saturday and Sunday do
 *  not count. Returns Infinity for an unparseable date, so a bad timestamp
 *  can never read as "the deadline has passed". */
export function businessDeadline(fromIso, days) {
  const t = Date.parse(fromIso || "");
  if (!Number.isFinite(t)) return Infinity;
  const d = new Date(t);
  let left = days;
  while (left > 0) {
    d.setUTCDate(d.getUTCDate() + 1);
    const wd = d.getUTCDay();
    if (wd !== 0 && wd !== 6) left--;
  }
  return d.getTime();
}

const DATE_FMT = { weekday: "long", month: "long", day: "numeric" };
const niceDate = (ms) => Number.isFinite(ms)
  ? new Date(ms).toLocaleDateString("en-US", DATE_FMT) : "";

/**
 * Did Resend actually DELIVER this message?
 *
 * Pulled rather than webhooked on purpose: it needs no new secret, no new
 * endpoint and no signature verification, and it is read at the one moment
 * the answer matters. `r.ok` from the send only means Resend accepted it for
 * delivery, which is a different claim entirely.
 */
async function wasDelivered(env, msgId) {
  if (!env.RESEND_API_KEY || !msgId) return false;
  try {
    const r = await fetch(
      "https://api.resend.com/emails/" + encodeURIComponent(msgId),
      { headers: { Authorization: `Bearer ${env.RESEND_API_KEY}` } });
    if (!r.ok) return false;
    const j = await r.json();
    return (j && j.last_event) === "delivered";
  } catch { return false; }
}

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

// The five faces that plainly satisfy 33 CFR 173.27. Kept in step with
// content.py by the same drift gate that guards worker/index.js.
const PLAIN_BLOCK = ["Arial Bold", "Arial Black", "Impact",
  "OCR A Extended", "MS Gothic"];

function riskNote(o) {
  if (o.kind === "Boat name" || PLAIN_BLOCK.includes(o.font)) return "";
  return `<p style="background:#fdf4e6;border:1px solid #f0dcbb;border-radius:9px;` +
    `padding:12px 14px;font-size:14px;color:#7a5417;margin:0 0 18px">` +
    `<b>About this font.</b> ${esc(o.font)} is not a plain block face. ` +
    `33 CFR 173.27 asks for plain vertical block characters on a ` +
    `registration number, so an officer may read this as non-compliant. ` +
    `We will cut exactly what you approve.</p>`;
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

/**
 * The deadline sentence. ONE copy, used by the proof, every reminder and the
 * confirmation, because three descriptions of the same rule is how a policy
 * ends up meaning three things. Returns "" for an order that can never
 * auto-approve, so those emails keep the old open-ended promise and stay
 * true for the customer reading them.
 */
function deadlineLine(o, when) {
  if (o.auto_cut_optout) {
    return `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">You ` +
      `asked us to wait for your word, so nothing happens until you ` +
      `approve &mdash; however long that takes.</p>`;
  }
  if (!when) return "";
  return `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">` +
    `<b>If we do not hear from you by ${esc(when)}</b> we will treat this ` +
    `proof as approved and send your payment link. Nothing is cut until that ` +
    `link is paid, so you get a second look either way &mdash; and you can ` +
    `reply at any time to change it or stop it.</p>`;
}

function proofEmail(env, o) {
  const url = proofUrl(env, o);
  return {
    subject: `Your proof for order ${o.ref} - approve to start cutting`,
    html: shell(
      `<h2 style="font-size:21px;margin:0 0 6px">Here is your proof</h2>` +
      `<p style="margin:0 0 18px;color:#44606f">Check every character against ` +
      `your registration card. This is exactly what the plotter cuts.</p>` +
      letteringBlock(o) + riskNote(o) +
      `<table style="border-collapse:collapse;margin:0 0 22px">${specRows(o)}</table>` +
      `<p style="margin:0 0 18px">${button(url, "Approve this proof")}</p>` +
      `<p style="margin:0 0 6px;color:#44606f">Something not right? ` +
      `<a href="${url}&c=1" style="color:#1b6382">Tell us what to change</a> ` +
      `&mdash; or just reply to this email.</p>` +
      `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">Once you ` +
      `approve, it is cut, packed and posted within 1-2 business days. ` +
      `Nothing is cut before then.</p>` +
      deadlineLine(o, niceDate(businessDeadline(o.proof_sent_at
        || new Date().toISOString(), AUTO_APPROVE_DAYS)))),
  };
}

function nudgeEmail(env, o, n) {
  const url = proofUrl(env, o);
  const lead = [
    `Your proof is still waiting`,
    `Still waiting on your approval`,
    `Last reminder about order ${o.ref}`,
  ][n] || `Your proof is still waiting`;
  // Both of these used to promise the opposite of what now happens - "the
  // order stays open" and "nothing is cut until you approve it". A reminder
  // that contradicts the policy it is reminding you about is worse than no
  // reminder, so the deadline line replaces them and the LAST one says the
  // date plainly rather than softly.
  const when = niceDate(businessDeadline(o.proof_sent_at, AUTO_APPROVE_DAYS));
  const tail = o.auto_cut_optout || !when
    ? deadlineLine(o, when)
    : (n >= 2
      ? `<p style="font-size:13.5px;color:#5b7383;margin:16px 0 0">This is ` +
        `the last reminder we will send. <b>On ${esc(when)} we will treat ` +
        `this proof as approved</b> and email you the payment link &mdash; ` +
        `nothing is cut until that is paid. Reply now if anything is wrong.` +
        `</p>`
      : deadlineLine(o, when));
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
  if (!r.ok) return false;
  // The message id, not just true: the auto-approval deadline runs off
  // whether THIS email was delivered, and that cannot be asked later without
  // its id. Still truthy, so every `if (!ok)` caller is unchanged.
  try {
    const j = await r.json();
    return (j && j.id) || true;
  } catch { return true; }
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
      `UPDATE orders SET proof_token=?, proof_sent_at=?, status=?,
                         proof_msg_id=? WHERE id=?`
    ).bind(t, iso, "proof-sent", typeof ok === "string" ? ok : null, o.id).run();
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

  const auto = await autoApproveSweep(env, now);
  return { sent, nudged, auto };
}

/**
 * Treat a delivered, un-answered, routine proof as approved after five
 * business days.
 *
 * Reminder: this cuts nothing and charges nothing. It moves the order to
 * "cleared to invoice" so the payment link can go out, and the customer pays
 * before any vinyl moves - which is the second consent that makes the whole
 * arrangement honest rather than merely disclosed.
 *
 * Every exclusion below is in the SQL rather than in JavaScript after the
 * fact, so a row that must not be touched is never even a candidate:
 *
 *   auto_cut_optout     the customer unticked the box at checkout
 *   changes_at          a change is in flight; a human owns it
 *   number_flag <> ''   the validator flagged the registration number
 *   number_flag NULL    row predates the column - we cannot tell, so no
 *   proof_nudges < 3    fewer than three reminders have gone out
 *   status test*        ours, not a customer's
 *
 * `COALESCE(number_flag,'?')` is the fail-safe that matters: the four orders
 * already sitting in the queue have no flag recorded, so they will never be
 * swept by this. Ryan handles those by hand, which is right - they were
 * placed under the old promise.
 */
export async function autoApproveSweep(env, nowMs) {
  if (!env.DB) return { approved: 0, skipped: "no db" };
  if (String(env.PROOF_AUTO_APPROVE || "on").toLowerCase() === "off") {
    return { approved: 0, skipped: "switched off" };
  }
  const now = nowMs == null ? Date.now() : nowMs;
  const iso = new Date(now).toISOString();

  const cand = await env.DB.prepare(
    `SELECT * FROM orders
      WHERE proof_sent_at IS NOT NULL
        AND approved_at IS NULL
        AND auto_approved_at IS NULL
        AND changes_at IS NULL
        AND COALESCE(test_mode,0) = 0
        AND COALESCE(status,'') NOT IN ('test','test-archived')
        AND COALESCE(auto_cut_optout,0) = 0
        AND COALESCE(number_flag,'?') = ''
        AND COALESCE(proof_nudges,0) >= ?
        AND email IS NOT NULL AND email <> ''
      ORDER BY id LIMIT 20`).bind(MAX_NUDGES).all();

  let approved = 0, waiting = 0, undelivered = 0;
  for (const o of (cand.results || [])) {
    if (now < businessDeadline(o.proof_sent_at, AUTO_APPROVE_DAYS)) {
      waiting++;
      continue;
    }
    // The load-bearing check. Silence after an email that never arrived is
    // not silence, so this is asked LAST and refuses rather than assumes.
    if (!await wasDelivered(env, o.proof_msg_id)) {
      undelivered++;
      continue;
    }
    await env.DB.prepare(
      `UPDATE orders SET approved_at=?, auto_approved_at=?, status=?
        WHERE id=? AND approved_at IS NULL`
    ).bind(iso, iso, "auto-approved", o.id).run();
    approved++;

    await send(env, o.email, {
      subject: `Order ${o.ref} is going ahead - payment link enclosed next`,
      html: shell(
        `<h2 style="font-size:21px;margin:0 0 6px">We are treating your ` +
        `proof as approved</h2>` +
        `<p style="margin:0 0 18px;color:#44606f">We sent your proof and ` +
        `three reminders and have not heard back, so as promised we are ` +
        `moving your order forward. Your payment link follows from us ` +
        `shortly.</p>` +
        letteringBlock(o) +
        `<table style="border-collapse:collapse;margin:0 0 20px">` +
        `${specRows(o)}</table>` +
        `<p style="background:#fdf4e6;border:1px solid #f0dcbb;` +
        `border-radius:9px;padding:12px 14px;margin:0 0 16px">` +
        `<b>Nothing has been cut.</b> This is exactly what we will cut once ` +
        `the payment link is paid, so you still have a last look. If any ` +
        `character is wrong, <b>reply to this email now</b> and do not pay ` +
        `the link &mdash; we will fix it first.</p>` +
        `<p style="font-size:13.5px;color:#5b7383;margin:0">Changed your ` +
        `mind entirely? Reply and we will cancel it. You have not been ` +
        `charged.</p>`),
    });

    if (env.ORDER_TO) {
      await send(env, env.ORDER_TO, {
        subject: `AUTO-APPROVED (no reply) - ${o.ref} - ${lettering(o)}`,
        html: shell(
          `<h2>${esc(o.ref)} auto-approved after 5 business days</h2>` +
          `<p style="background:#fff7e6;border-left:4px solid #d08700;` +
          `padding:10px 13px"><b>The customer never replied.</b> Send the ` +
          `payment link. <b>Do not cut this until it is paid</b> &mdash; ` +
          `unlike a normal approval, nobody has confirmed these characters, ` +
          `so the payment is the only confirmation you will get.</p>` +
          letteringBlock(o) +
          `<table style="border-collapse:collapse">${specRows(o)}</table>` +
          `<p>${esc(o.name || "")} &lt;${esc(o.email)}&gt;</p>` +
          `<p style="font-size:13px;color:#5b7383">Proof delivered ` +
          `${esc(o.proof_sent_at || "")}, three reminders sent, no reply.</p>`),
      }, o.email);
    }
  }
  return { approved, waiting, undelivered };
}

/**
 * Sent the moment the order lands.
 *
 * Without this the customer gets nothing at all until the proof eleven hours
 * later, having just been told on screen that an email was on its way. That
 * gap is how the first real order sat unanswered: the shop was notified, the
 * customer was not, and the screen had promised otherwise.
 */
export async function sendOrderConfirmation(env, o) {
  if (!o || !o.email) return false;
  return send(env, o.email, {
    subject: `Order ${o.ref} received - your proof is on its way`,
    html: shell(
      `<h2 style="font-size:21px;margin:0 0 6px">We have your order</h2>` +
      `<p style="margin:0 0 18px;color:#44606f">Nothing is cut yet. Within ` +
      `<strong>12 hours</strong> we will email you a proof of your exact ` +
      `lettering to check and approve.</p>` +
      letteringBlock(o) +
      `<table style="border-collapse:collapse;margin:0 0 20px">${specRows(o)}</table>` +
      `<p style="font-size:13.5px;color:#5b7383;margin:0">Order ` +
      `<strong>${esc(o.ref)}</strong>. Spotted a mistake already? Reply to ` +
      `this email and we will fix it before the proof goes out.</p>` +
      (o.auto_cut_optout
        ? `<p style="font-size:13.5px;color:#5b7383;margin:14px 0 0">You ` +
          `asked us to wait for your word, so this order sits until you ` +
          `approve it &mdash; however long that takes.</p>`
        : `<p style="font-size:13.5px;color:#5b7383;margin:14px 0 0">So an ` +
          `order never gets stuck: if we have not heard from you five ` +
          `business days after the proof is delivered, we will treat it as ` +
          `approved and send your payment link. <b>Nothing is cut until that ` +
          `link is paid</b>, and a reply stops the clock at any point.</p>`)),
  }, env.ORDER_TO);
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
          `<p style="background:#fff7e6;border-left:4px solid #d08700;` +
          `padding:10px 13px"><b>Send the payment link now.</b> Nothing in ` +
          `the site does this - the customer was told the link follows ` +
          `approval. Then cut, pack and post within 1-2 business days.</p>` +
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
