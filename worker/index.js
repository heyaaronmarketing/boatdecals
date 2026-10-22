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
  "Numbers + name": 44,
  "Something else": 22,
};
const HEIGHT_ADD = { "3": 0, "4": 4, "5": 8, "6": 13 };
const UPGRADE_ADD = {
  "Premium 8-year cast vinyl": 8,
  "Add your boat name": 29,
  "Hailing port line": 15,
  "Rush - cut and shipped same day": 12,
  "Reflective or metallic finish": 10,
  "Install kit - squeegee + solution": 6,
};

function priceOf(d) {
  let n = BASE[d.kind] ?? 19;
  n += HEIGHT_ADD[String(d.height || "3")] ?? 0;
  const ups = String(d.upgrades || "")
    .split(",").map(s => s.trim()).filter(Boolean);
  for (const u of ups) {
    // "Add your boat name" is already inside the base for the combined option.
    if (d.kind === "Numbers + name" && /boat name/i.test(u)) continue;
    n += UPGRADE_ADD[u] ?? 0;
  }
  return Math.round(n);
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

  if (!o.text || !o.name || !EMAIL.test(o.email)) {
    return json({ error: "missing lettering, name or a valid email" }, 422);
  }
  o.total = priceOf(o);
  // A mismatch means the client is stale or tampered with. Log it, trust ours.
  o.mismatch = o.quoted && o.quoted !== o.total ? 1 : 0;

  if (env.DB) {
    try {
      await env.DB.prepare(
        `INSERT INTO orders (ref,kind,text,state,height,font,color,upgrades,
           name,email,phone,boat,notes,page,total,quoted,mismatch,ua,country,ts)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
      ).bind(o.ref, o.kind, o.text, o.state, o.height, o.font, o.color, o.upgrades,
             o.name, o.email, o.phone, o.boat, o.notes, o.page, o.total, o.quoted,
             o.mismatch, o.ua, o.country, o.ts).run();
    } catch (err) {
      console.error("d1 insert failed", err && err.message);
      // Keep going - an unsaved row is recoverable from the email, a lost
      // customer is not.
    }
  }

  if (env.RESEND_API_KEY && env.ORDER_TO) {
    const rows = [
      ["Reference", o.ref], ["Product", o.kind], ["Lettering", o.text],
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/order") {
      if (request.method !== "POST") return json({ error: "POST only" }, 405);
      return handleOrder(request, env);
    }
    if (url.pathname === "/api/health") {
      return json({ ok: true, db: !!env.DB, email: !!env.RESEND_API_KEY });
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
