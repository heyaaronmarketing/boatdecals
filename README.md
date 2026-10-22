# Boat Number Shop — boatnumbershop.com

Custom boat registration numbers, names and marine vinyl decals. National
e-commerce, not a local lead-gen site: the conversion element is an **order
configurator**, not a tap-to-call.

**Live:** https://boatdecals.aironz.workers.dev (Worker `boatdecals`, CF account `681da9da…`)

## Build & deploy

```bash
python3 engine/build.py && python3 verify.py && npx wrangler deploy
```

**Never skip `verify.py`, and never pipe the build to /dev/null.** A syntax error in
`build.py` once failed the build silently and three deploys shipped a stale `public/`
before anyone noticed. `verify.py` gates: engine compiles, worker parses, page count,
broken links, JSON-LD validity, double-escaped entities, duplicate titles/descriptions,
the order wizard's required hooks, and **price parity between `content.py` and the
worker**.

`public/` is committed so Cloudflare Workers Builds can deploy without a Python
step. **Always rebuild before committing** — editing `public/` by hand gets
overwritten.

## Layout

| Path | What |
|---|---|
| `engine/content.py` | All page data: products, states, boat types, tools, guides, pricing. Search volumes recorded inline (DataForSEO, 2026-10-22). |
| `engine/build.py` | Static generator + all long-form body copy. |
| `engine/order.py` | The five-step order wizard + client price JS + Stripe mount. |
| `engine/tools.py` | Name generator, HIN decoder (96 MIC codes), layout checker. |
| `engine/copy_blocks.py` | Reusable prose. **The 33 CFR 173.27 block is verbatim-verified — do not loosely paraphrase it.** |
| `engine/style.py` | CSS. Palette/type carried over from Piney Woods Soft Wash. |
| `worker/index.js` | `/api/order` (D1 + Resend) and asset serving. |
| `STRATEGY.md` | Gap analysis: keyword, geographic, AEO, SEO and social. Read before adding pages. |

## Pricing is in two places and must stay in sync

`engine/content.py: PRICE/UPGRADES` (display + client JS) and
`worker/index.js: BASE/HEIGHT_ADD/UPGRADE_ADD` (the authority). The worker
recomputes every order and flags `mismatch=1` in D1 if the browser disagreed —
that's the tamper guard, so never make the worker trust `quoted_total`.
`verify.py` fails the build if the two tables disagree.

⚠️ **Upgrades are joined with `" | "`, not a comma.** Two labels contain commas
("a second pair at half price"), and comma-splitting silently dropped them
server-side — the customer was undercharged $9 and the line item vanished from
the shop email. `verify.py` now rejects any label containing the delimiter.

## The order wizard

Five steps, one decision each, in a fixed-height shell (`min-height` on `.wizbody`)
so the panel never jumps. Anti-fatigue rules, all load-bearing:

- step 1 **auto-advances on click** — no Continue press to start
- only steps 2 and 5 require typing; 1, 3 and 4 are pure clicking
- phone / boat / notes live behind a `<details>`; the card supplies the name
- the running total is visible from step 1, so price is never a late surprise

The preview flips its hull colour from the vinyl's lightness flag (`COLORS[2]`):
light vinyl renders on a dark hull, dark vinyl on a light one. That is both an
honest preview and the federal contrast rule taught visually.

## Stripe

`/api/checkout` creates a PaymentIntent for the amount **the worker** calculates.
Set `STRIPE_SECRET_KEY` (worker secret) and `STRIPE_PUBLISHABLE_KEY` (build-time
env var, read by `build.py`) to switch it on:

```bash
echo "sk_live_..." | npx wrangler secret put STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_... python3 engine/build.py && npx wrangler deploy
```

Until both are set the checkout step **degrades honestly** — it does not render a
fake card field. It collects the order and promises an emailed payment link.

## Bindings & secrets

- `DB` → D1 `boatnumbershop` (`43724d47-…`), schema in `schema.sql`
- `RESEND_API_KEY`, `ORDER_TO` → set ✅
- `ORDER_FROM` → currently `onboarding@resend.dev`. **Verify boatnumbershop.com
  in Resend and switch this to `orders@boatnumbershop.com` before launch.**

## Before launch

See the "Before this takes a real order" checklist in `STRATEGY.md`.
