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
| `engine/hull.py` | The boat preview SVG + its renderer. |
| `engine/mockpay.py` | Sandbox card form (see Payment modes). |
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

### The preview (`engine/hull.py`)

A hull in side profile, not a colour swatch — because a swatch cannot answer the
two questions people actually have: *will this read against my hull?* and *where
does it go?*

- Registration numbers render on the **forward half**, with the validation decal
  placed aft of them
- A boat name renders on the **transom**
- "Both" shows both, which is the clearest possible argument for the $44 bundle
- The hull **and the water** flip dark when the vinyl is light (`COLORS[2]`), so
  light vinyl is always shown on a dark hull. That is 33 CFR 173.27's contrast
  rule demonstrated rather than described.

Step 1's three options carry the same hull as a thumbnail, so the picture is the
explanation and the prose could go.

⚠️ **The steps are `<section>` elements.** The global `section{padding:42px 0}`
(56px at ≥900px) was silently adding **112px to every step** — `.step{padding:0}`
is load-bearing, don't remove it.

### Header nav

Labels are customer vocabulary ("Boat Numbers"), not page titles — the hrefs
still point at the canonical slugs. Edit `NAV_MAIN` / `NAV_ABOUT` in
`engine/build.py`; nothing else needs touching.

The About group opens on `:hover` **and** `:focus-within`, so mouse, keyboard
and touch all work with no JavaScript — and "About" stays a real link to
`/about/` rather than a button you cannot follow. The invisible `::after` strip
below it stops the menu closing as the pointer travels into the panel.

Below 900px the links collapse behind a toggle (the only part needing JS) and
the About group renders inline as a labelled section rather than a flyout. The
footer carries every link, so a JS failure leaves nothing unreachable.

The phone number is deliberately **not** in the header row — it's in the topbar,
the footer and on `/contact/`.

### Hero layout

`.herogrid` uses three named areas (`a` headline, `f` form, `b` supporting copy),
not two columns. On a phone that puts the wizard directly under the headline
instead of below a screenful of copy; on desktop the copy stacks in the left
column beside it, with `grid-template-rows:auto 1fr` so row 1 hugs the headline
rather than stretching.

## Payment modes

Resolved at build time, highest wins:

| Mode | When | Behaviour |
|---|---|---|
| `stripe` | `STRIPE_PUBLISHABLE_KEY` is set at build time | Real Stripe Payment Element |
| `sandbox` | **current default** | Fake card form, accepts any number, no network call |
| `link` | `PAY_MODE=link` | Collects the order, promises an emailed payment link |

### Sandbox mode (`engine/mockpay.py`)

Looks and behaves like Stripe's Payment Element — card formatting (4-4-4-4, and
4-6-5 for Amex), brand detection, `MM / YY` auto-slash, Stripe's own error
wording — and talks to nobody.

**The hard rule: a full card number never leaves the browser and is never
stored.** `collect()` validates shape only (deliberately *not* Luhn, so any test
number works) and returns `{brand, last4}`. The PAN and CVC go out of scope and
are never returned, logged, or posted.

Three layers enforce it, and `verify.py` gates all three:

1. `collect()` returns brand + last4 only
2. The worker's `carriesCardNumber()` **refuses the whole request** with a 400 if
   any posted field contains a 13–19 digit run — it rejects rather than silently
   scrubbing, because a silent scrub would hide the regression that caused it
3. There is no column for a full number in `schema.sql`

A permanent **TEST MODE** banner sits above the field, the shop email is subject
-prefixed `[TEST]` with a "do not cut it" warning, and rows land with
`test_mode=1, status='test', paid=0` — so `SUM(total) WHERE paid=1` is real
revenue with no test exclusion needed.

To go live, set both keys and rebuild (the publishable key is read at build time,
so a redeploy alone will not switch modes).

### Stripe

`/api/checkout` creates a PaymentIntent for the amount **the worker** calculates.
Set `STRIPE_SECRET_KEY` (worker secret) and `STRIPE_PUBLISHABLE_KEY` (build-time
env var, read by `build.py`) to switch it on:

```bash
echo "sk_live_..." | npx wrangler secret put STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_... python3 engine/build.py && npx wrangler deploy
```

Until both are set the site runs in `sandbox` mode (above). Setting
`PAY_MODE=link` instead skips the fake card field entirely and collects the order
against an emailed payment link.

## Bindings & secrets

- `DB` → D1 `boatnumbershop` (`43724d47-…`), schema in `schema.sql`
- `RESEND_API_KEY`, `ORDER_TO` → set ✅
- `ORDER_FROM` → currently `onboarding@resend.dev`. **Verify boatnumbershop.com
  in Resend and switch this to `orders@boatnumbershop.com` before launch.**

## Before launch

See the "Before this takes a real order" checklist in `STRATEGY.md`.
