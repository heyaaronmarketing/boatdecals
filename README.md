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

## Retired products

Motor/brand decals, carpet decals, hailing-port decals, domed & chrome lettering
and boat striping were removed on 2026-10-23. Four products remain.

Their URLs were live, so `worker/index.js: RETIRED` **301-redirects** each one to
the nearest surviving page rather than 404ing — a dead end loses the link equity
and the visitor. Don't delete those redirects.

The hailing-port **add-on** went with the product line. If the shop still wants to
sell a hailing-port line under a name, restore it in `content.py: UPGRADES` and in
the worker's `UPGRADE_ADD` together — `verify.py` fails if they disagree.

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

Four steps, one decision each, in a fixed-height shell (`min-height` on `.wizbody`)
so the panel never jumps. Anti-fatigue rules, all load-bearing:

- step 1 **auto-advances on click** — no Continue press to start
- only steps 2 and 5 require typing; 1, 3 and 4 are pure clicking
- phone / boat / notes live behind a `<details>`; the card supplies the name
- the running total is visible from step 1, so price is never a late surprise
- **there is no upsell step, and no notes field.** The add-ons on `/pricing/`
  are requested by replying to the proof email instead. The worker still prices every entry in
  `UPGRADE_ADD`, so a note-added upgrade costs exactly what a clicked one would
  have — don't delete that table just because nothing posts it any more.

`MAX` is derived from the rendered step count, and every conditional uses it
rather than a literal, so adding or removing a section renumbers everything.
`verify.py` asserts the count is 4 — a silently vanished section would otherwise
look like a working wizard.

### The preview (`engine/preview.py`)

Just the letters, as large as the box allows. The text is drawn into an SVG
whose **viewBox is recomputed from the rendered bounding box** on every change
(`fit()`), so the glyphs fill the panel edge to edge regardless of length or
font. "Both" stacks two lines and fits them together.

Step 2 carries no visible heading or sub-line — the step counter, the field
labels and the "Pick a font" legend say it all. The `<h2>` is still in the
markup as `.vh` (visually hidden) so screen readers keep the step structure.

⚠️ **If you remove an element, remove every `$('id')` that writes to it.**
Deleting step 2's sub-line while leaving its setter made `syncStep2()` throw a
TypeError on every render — and because the visible half of the function ran
first, the only symptom was that the scroll-into-view and autofocus after it
silently stopped working. `verify.py` now cross-checks every id the wizard's JS
writes against the ids present in the markup.

The panel is **fixed at 94px and the glyphs scale inside it** — 6" fills it,
3" renders at half. `fit()` inflates the viewBox rather than resizing the
element: a larger viewBox around the same glyphs renders them smaller. Measured
on short text: 1.00 / 1.35 / 1.65 / 2.00.

Shrink-wrapping alone always fills the panel in one dimension, which is why
every height used to render identically before. Text too wide for the panel
still shrinks to fit, so a long string at 6" lands below 2.00 — honest, because
it really will not fit where a short one does.

The panel height is a constant (`BASE_H`), never a CSS `min/max` pair: a
min/max let the box resize as the text grew, which made it jitter while typing.

### Visitor state detection

`/api/geo` returns `{region, code}` from Cloudflare's own `request.cf`, and the
wizard seeds the placeholder with it (`seedStatePrefix`). `PREFIX_OVERRIDE` in
the worker maps **CA → CF** and **WA → WN**, the two states that don't use their
postal abbreviation on the water.

It is a **placeholder only** — the customer types their real number off the
card regardless, so a wrong guess costs nothing. That is why there's no retry,
no fallback chain, and no attempt at better accuracy: failure quietly keeps the
Iowa default. It never overwrites typed text, and the result is cached in
`sessionStorage`.

Deliberately its own endpoint rather than injected into the HTML: pages are
edge-cached with `s-maxage`, and a region baked into a cached page would be
served to the wrong visitors.

The panel flips dark when the vinyl is light (`COLORS[2]`), so white, chrome and
gold are always shown against something they can be seen on. That is 33 CFR
173.27's contrast requirement, demonstrated rather than described.

Step 1's three options use line icons (`_KICON` in `engine/order.py`): a hash
for numbers, a letterform for names, two stacked plates for both.

### Fonts

Ten faces, defined once in `content.py: FONTS` as
`(label, css family, Google spec, block_legal)`.

**All ten are free Google Fonts on purpose.** A plotter cuts any TTF, so the shop
installs these and cuts *exactly* what the customer previewed. Substituting a
lookalike for the preview would make it a lie.

Each chip renders the customer's own lettering (first 7 characters) in that face,
so the choice is made on the thing itself rather than a font name. The stylesheet
loads async (`media="print"` → `onload`), so it never blocks first paint and the
chips fall back to the stack's system fonts until it lands.

`block_legal` marks the five faces satisfying 33 CFR 173.27's "plain vertical
block characters":

- **Registration numbers** — the other five are **removed from the grid**, so it
  shows one tidy row of five. No explanatory hint; an order that cannot legally
  be placed isn't worth describing.
- **"Both"** — all ten unlock, because the font applies to the *name*. The big
  preview then renders the **number line in Block regardless** (`numBlock` →
  `numFam` in `preview.py`), because showing script registration numbers we would
  never cut would make the preview a lie. The hint says so explicitly — it is the
  only font hint left, because it is the only case that isn't self-evident.

`worker/index.js` keeps its own `BLOCK_FONTS` copy and **coerces** a non-block
font to Block on a registration-numbers order. It coerces rather than rejects:
losing a real order to a stale cached page is worse than correcting the font and
flagging it in the shop email, on a proof the customer approves anyway.

### Colours

The order form offers **White and Black only** (`content.py: ORDER_COLORS`).
Between them they contrast with every hull colour there is, which is what
33 CFR 173.27 actually asks for, and both are always in stock.

The full `COLORS` list still drives the swatch display on product pages, which
now says white and black ship standard and the rest are quoted by email —
**don't let the order form and the product pages disagree again**: advertising
32 colours while shipping a two-colour picker is how refund requests start.

### Sizes

The chip holds the measurement alone; the caption and the price sit **outside
and below** it (`.optbox` + `.optcap`, both children of `.opt`).

⚠️ **The wizard renders inside `.hero{color:#fff}`.** Anything in the panel that
doesn't set its own colour inherits white and vanishes — `<legend>` did exactly
that and "Colour" / "Character height" were invisible for several deploys.
`.panel` now anchors `color:var(--ink)` and `verify.py` gates both that rule and
the explicit `legend` colour.

### The state field is gone

Step 2 no longer asks for it — the registration number already carries its state
prefix. `stateFromPrefix()` reads the first two characters against
`window.BNS_PREFIX` (so CF → California, WN → Washington) and posts it silently,
so the shop still gets the data without the customer filling a field.

⚠️ **The steps are `<section>` elements.** The global `section{padding:42px 0}`
(56px at ≥900px) was silently adding **112px to every step** — `.step{padding:0}`
is load-bearing, don't remove it.

### Hero buttons

The pair is normalised in one rule **inside `@media(min-width:900px)`**. Two
traps live here, both of which bit:

1. The primary carried `.btn.lg` (16.2px, 12px padding) while the ghost beside
   it was a plain `.btn` (17px, 15px) — the *secondary* button was bigger than
   the primary it defers to.
2. `.heroCta{display:none}` for mobile loses to `.btn{display:inline-block}`,
   which sits **later in the sheet at the same specificity**. It must be
   written `.hero .btnrow .heroCta`. An unscoped desktop normalisation rule
   out-specifies the mobile rules for the same reason.

Check both breakpoints after touching anything in here.

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

⚠️ **The TEST MODE banner was removed from the card field** at the owner's
request, so there is no longer anything on screen telling a visitor the field
takes no payment. `initPay()` therefore only mounts the sandbox on a
**preview host** — `*.workers.dev`, `*.pages.dev`, `localhost`, `127.0.0.1`.
On any real domain without Stripe keys it falls through to `degrade()` and the
emailed-payment-link flow instead. **Do not loosen that host check**: without
it, pointing boatnumbershop.com at this worker would put a dead card field in
front of real customers who would believe they had paid.

(A build-time guard on `SITE_URL` was tried first and removed — the canonical
URL is always the production domain, so it could not tell a preview deploy from
a live one. The host is the only honest signal.)

**There is no TEST MODE marker anywhere on screen** — not on the card field, not
on the confirmation. Both were removed by request. What remains is shop-side:
the email is subject-prefixed `[TEST]` with a "do not cut it" warning, and rows
land with `test_mode=1, status='test', paid=0` — so `SUM(total) WHERE paid=1` is
real revenue with no test exclusion needed.

That makes the host check the single point of failure, which is why `verify.py`
asserts it and why breaking it was tested before being trusted.

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
