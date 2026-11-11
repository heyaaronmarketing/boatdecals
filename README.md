# Boat Number Shop — numbermyboat.com

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

## The font inventory check (`/fonts-check/`)

A private page the shop opens on the machine that drives the plotter. It
reports which of the site's 45 faces are already installed, so only the
missing ones get installed by hand.

**Two detection paths, because neither covers everything:**

- `queryLocalFonts()` is the real API for this and returns the whole system
  list — but it is Chrome and Edge on desktop only, and it raises a permission
  prompt that has to be accepted.
- A canvas metric check works in any browser but can only answer *"is this
  family here"*, so it runs against the site's own list. That happens to be
  the actual question, which is why it always runs and the API is the bonus.

**The page must load no web fonts.** A face pulled in by the page measures as
installed when it is not, and the report would then be wrong in the direction
that costs a mis-cut. Gated.

**What it collects is on the page before the button is pressed**: font names,
browser version, Windows-or-Mac. Nothing is sent until the second button, and
the page says where it goes. That disclosure is gated too — a tool that reads
something off someone's machine should say so in its own words, not in a
policy somewhere else.

`POST /api/fonts` stores names only; `GET /api/fonts?k=…` reads the last ten
reports back and 404s without the key. noindex and out of the sitemap.

## The proof cycle (`worker/proof.js`)

Every order is promised **a proof within twelve hours**, and **nothing is cut
until it is approved**. That promise is load-bearing copy on 19 pages, so the
machinery behind it is gated.

| | |
|---|---|
| Proof sent | 11 hours after the order |
| Reminders | +24h, +72h, +144h, then stop |
| Approval | `/api/approve?r=REF&t=TOKEN` |
| Proof page | `/proof/?r=REF&t=TOKEN` (noindex, not in the sitemap) |
| Schedule | Worker cron, hourly at `:17` |

**Eleven hours, not twelve.** A cron firing on the hour would otherwise land
the "within 12 hours" email at 12h59m, and the promise would be false for most
orders.

**There is no queue.** The schedule *is* the timestamps on the order row, so a
missed cron run catches up on the next one instead of dropping anybody, and the
same order cannot be picked twice because the send stamps the row in the same
request. Anything already approved, already asking for changes, or flagged
`test_mode` is excluded by the query — a sandbox order emailing a real person
to approve something is the failure that gate exists for.

**The token is random, not derived.** 16 bytes from `crypto.getRandomValues`,
compared in full and only after the row is found, so a wrong reference and a
wrong token give the same answer. `/api/proof` returns only what the proof has
to show — no email, no name — because the link travels through an inbox and a
forwarded one should not hand over the customer's details.

**The lettering is styled text in the email, not inline SVG.** Gmail strips
SVG, and a customer who cannot see the proof cannot approve it. If the web font
fails, the fallback still shows the right characters at the right size, which
is the part being checked; the proof page renders it properly.

`/api/proof-run?k=…` runs a cycle on demand, keyed on `PROOF_RUN_KEY` and 404
without it. It sends real email — unguarded, it is a button anybody can press
to mail the customer list.

### What is automated and what is claimed

The proof, the sending and the chasing are all automatic. The site only ever
claims that we *send* a proof and *wait* for approval, which is exactly true.
Nothing says a person drew it, because nobody did.

### The turnaround promise moved

This replaced "cut and shipped the next business day", which appeared in 35
places and was sold as a feature — one FAQ literally advertised **"no queue, no
proof to approve first"**. All of it now reads: proof in 12 hours, then cut,
packed and posted within 1-2 business days of approval. `verify.py` fails the
build if either the old claim or that old boast reappears on any page, because
a turnaround we no longer meet is a delivery date, not a slogan.

## The order wizard

Seven steps, one decision each, in a fixed-height shell (`min-height` on
`.wizbody`) so the panel never jumps. Two of the seven are conditional — there
is no "what is the number" step on a name-only order — so any given order sees
five or six. `cur` is the step's **stable `data-step` id, not its position**;
position is derived. Anti-fatigue rules, all load-bearing:

- step 1 **auto-advances on click** — no Continue press to start
- only the number and name steps require typing; the rest are pure clicking
- every step's Next button names the next one ("Next: pick a color"), so the
  customer always knows how much is left
- phone / boat / notes live behind a `<details>`; the card supplies the name
- the running total is visible from step 1, so price is never a late surprise

### The phone app layer

On a phone **the home page** opens as a full-screen card deck — a stories-style
progress bar, full-bleed cards you swipe or tap through, and one "Start your
order" pinned to the bottom. No site header, no notification bar, no sticky
drawer. The deck is the experience, not a hero element.

Thirteen cards: nine photographs of lettering already on a hull, interleaved
with four plain-language cards covering price, the law, surfaces and turnaround
(`APP_CARDS` in `build.py`). Interleaved rather than photos-then-adverts, so it
reads as a tour of the work.

#### It is an overlay, never a replacement

This is the part that matters, and it is gated three ways:

- The page's own content **stays in the DOM and in normal flow underneath**.
  Nothing is `display:none`-d away, so mobile-first indexing still renders the
  whole page.
- `<main id=main>` must still be present on every page that carries the layer.
- The element **ships with the `hidden` attribute** and JavaScript removes it.
  With JS off nobody is handed a full-screen layer they cannot dismiss.

It is shown **once per visit** (`sessionStorage`), because handing someone the
deck again on the second page, after they already chose to browse, is hostile.

#### The home page and nowhere else

`verify.py` fails the build if it appears on a second page.

It ran on all 32 commercial pages first, and the problem is **arrival intent**.
Somebody searching "iowa boat registration numbers" lands on the Iowa page
wanting Iowa, and a full-screen deck over it is an interstitial — which Google
treats as a mobile ranking signal, on a site whose whole strategy is search.
The home page has no specific answer being sought, so there is nothing to
interrupt.

**Every other page gets `.heroStart` instead** — a small offer card in the
wizard's grid slot, above the headline: the price, one button, one line of
terms. It is not optional. The chrome that used to carry a phone CTA — the
notification bar, the header button, the sticky drawer — is all hidden on a
phone, so without the card a state page would have no way to order until you
scrolled into the in-content bands. There is a gate for exactly that: any page
with the wizard must also carry the card.

On the home page the card sits underneath the app layer, so **Skip lands you
straight on it**.

#### The mechanics

- **CSS scroll-snap**, full-bleed cards. Native momentum and rubber-banding,
  and it still works with the JS doing nothing but the progress bar. Tapping
  the left or right 28% of the track moves a card, the way a stories UI does.
- **Each card carries the photo twice** — a blurred copy filling the card, and
  the sharp one at its own 3:2. These are landscape photographs and a phone
  card is tall and narrow; stretching one to fill crops it to a slab of hull
  with the lettering running off both edges.
- The order sheet sits at `z-index:300` **above** the layer's `200`, so the
  button opens the form over the deck and closing it returns you to the deck.

#### Getting the images to load only when wanted

This took three goes, and every wrong version *looked* fine:

- `loading=lazy` **does not work in a horizontal scroller.** Chrome treats the
  whole inline axis as near-viewport and fetched every card on load — measured
  at ~580KB before a single swipe.
- A **CSS `background-image` ignores lazy loading entirely**, so the first
  attempt at the blurred backdrop quietly doubled the problem. The backdrop is
  a real `<img>` for exactly that reason.
- So: the first card ships a real `src`, every other card carries `data-src`,
  and the scroll handler swaps in the neighbours as you go. Two requests on
  load instead of twenty-six.

Two more things, both gated:

- **The progress bar is updated straight from the scroll event, with no
  `requestAnimationFrame` in front of it.** rAF does not tick in a hidden tab,
  so a scroll that landed while backgrounded left a pending flag set and the
  bar froze for the rest of the session.
- Positions are measured off `getBoundingClientRect`, **not `offsetLeft`**:
  `offsetLeft` is relative to the nearest *positioned* ancestor rather than the
  track, so the first version computed centres in the wrong coordinate space
  and the bar never moved.

#### The specificity trap, three times

`.appbg` has to be written `.appcard img.appbg`, because the sharp-image rule
is `.appcard img` — a class plus a type selector, which outranks a bare class —
and it was handing the backdrop `height:auto` and `aspect-ratio:3/2`. The
backdrop sized itself to the sharp photo instead of filling the card.

That is the third time in this file that a later or higher-specificity rule has
quietly beaten a new one — `.heroCta`, then `.sticky`, then this. When a rule
here looks correct and does nothing, check what else matches the element before
changing the value.

#### And the chrome

### The phone order sheet

Every "Start your order" on the page — the deck button, the header, the sticky
bar on wider screens, any `a[href="/design/"]` — opens the wizard **full
screen** instead of navigating.

**It is promoted, not duplicated.** `body.sheeton` turns the existing `.heroF`
into a fixed, full-viewport panel; there is never a second copy of the form to
keep in step, and the customer's answers survive opening and closing it. Pages
with no hero wizard (`/pricing/`, the guides) have no `.heroF`, so their links
navigate as they always did, and `/design/` keeps its wizard inline because
there the form *is* the page.

Four things the sheet has to get right, each of which is gated:

- **the page behind must not scroll** (`body.sheeton{overflow:hidden}`)
- **the sticky bar must not float over it**, offering the thing already open
- **Back closes the sheet rather than leaving the page** — a `pushState` on
  open and a `popstate` listener. On a phone that is what the gesture means.
- **crossing the breakpoint closes it**, or rotating to landscape would leave
  the body scroll-locked and `.heroF` still `aria-modal` with every sheet
  style gone. This watches `matchMedia().change` rather than `resize`: the
  query flipping is the actual event, and it fires however it was crossed.

Opening also fires a `resize`, because the panel just went from a 343px column
to the full viewport and the boat preview sizes its lettering off the panel's
width.

**The total sits in a dark box with light type**, with "Free shipping" under the
figure — the one claim worth repeating at the moment someone is looking at a
price. **It animates on every increase** (`bumpTotal()`,
`@keyframes totbump`). Two guards: `lastTot` starts `null`, so arriving on the
page is not a "price went up" event, and the bump is gated on `p > lastTot` —
flashing the total while it *drops* would read as a penalty for deselecting
something. Every colour the flash uses lives in the keyframes rather than in
`.bump`, so the box returns to its resting state on its own and the class can
be left on the element; re-triggering is remove + reflow + add.

**The order page is the one page with no sticky CTA bar** (`sticky_bar=False`).
That bar prints a flat "$19 · Registration numbers" and links to `/design/`, so
on `/design/` it would sit under a live total reading $44 and point at the page
you are already on. Gated both ways: the bar must be absent, and the body must
not still be padded for one.

**A price looks like a price wherever it appears.** `.kindbox i` and
`.optcap i` share one pill — same 20px figure, same outline, same tint — so
step 1's "$19 / $29+ / $44+" and the height step's "included / +$4 / +$8 /
+$13" read as the same kind of thing. 20px is 1.5x where that pill started.

Each step shows the decision and its price, and nothing else. Step 1 used to
carry a caption under every option ("On the bow, both sides", "On the transom")
— but the thumbnail already shows where the lettering goes, so it was the icon
in words. The height step
used to carry a one-word pitch under every box ("legal minimum", "reads
better", "big transom") plus a two-line hint about the federal minimum; the
size and the price are the whole decision, so the captions went and the boxes
got bigger. Same for the colour step, which used to explain contrast law under
the swatches. The legal detail lives in the guides, which is where someone
actually reading about it will be.
- **there is no upsell step, and no notes field.** The add-ons on `/pricing/`
  are requested by replying to the proof email instead. The worker still prices every entry in
  `UPGRADE_ADD`, so a note-added upgrade costs exactly what a clicked one would
  have — don't delete that table just because nothing posts it any more.

`MAX` is derived from the rendered step count, and every conditional uses it
rather than a literal, so adding or removing a section renumbers everything.
`verify.py` asserts the count is 4 — a silently vanished section would otherwise
look like a working wizard.

### The preview (`engine/preview.py`)

Two views behind a toggle: **the lettering on a photograph of a hull** (the
default) and **just the letters** (one click away).

Both exist on purpose. At honest scale a 3" character on six feet of hull is
about 16px on screen — right for *"what will this look like on my boat"* and
wrong for *"is my registration number correct"*, and a typo there makes the
decal worthless. The flat view is where someone proofreads; the boat view is
where they judge it.

#### The plates (`media/plates.py`, `engine/plates.json`)

Four photographs — light and dark hull, side and transom — are the **only
images on the site with no lettering on them**. Every other hull shot was
generated with a registration number already applied, which is why none of them
could be reused: the customer's own text would double up on top. There is no
patching over the existing ones either; the hulls carry scuffs, water spots and
shading, so a flat patch reads as a smudge.

Two things a plate has to be:

- **Square-on.** PV-01's rub rail is level to within 6px across 1400, so the
  lettering plane is fronto-parallel and a plain rotate-and-translate is
  enough. No homography, nothing to peel off a curve. The dock-side bow shots
  in the `ST-*` set are three-quarter views and would not take an overlay.
- **Cropped tight.** This is the one that is easy to get wrong. On the full
  PV-01 frame the hull spans about 13 feet, so a 3" character renders 29px on
  the master and ~15px at the panel's real width — true to scale and
  illegible. Six feet of hull doubles it without touching the proportions.
  The crop also has to keep the bow in frame: cropped to flat topside alone the
  plate reads as a white wall rather than a boat.

`inches` — how much real hull the plate's **width** spans — is the one number
that makes "shown to scale" true. Character height is `inches / plate.inches`
of the plate width, so it holds at any panel size without a second calibration,
and the finished-size note is the rendered glyph width converted back through
the same ratio.

**The boats are not real, so no dimension here is measured.** Each is declared
from the hull geometry in frame (rub rail to waterline on the side plates,
corner to corner on the transoms) against normal dimensions for a boat that
size, and the preview prints the matching `nominal` — *"shown to scale on a
17 ft runabout"* — so the assumption is on screen rather than implied. Scaling
lettering onto a hull without saying what hull is an unstated claim about boat
size, which is why `verify.py` fails the build if `nominal` goes missing.

Captions stay the same as everywhere else: **by spec, never as a customer's
boat** (`media/CAPTIONS.md`).

#### Making it look applied rather than pasted

- Dark vinyl uses `mix-blend-mode: multiply`, so the hull's scuffs and shading
  read through the film the way they do on real gelcoat. Light vinyl is opaque,
  so it does not.
- `paint-order: stroke fill` on the outline, so the fill paints over the
  stroke and the outline sits outside the character — which is what a second
  layer of vinyl cut slightly larger actually does.

**Nothing may put the lettering in its own composited layer on a phone.** Both
`filter` and `mix-blend-mode` do, and a phone rasterises that layer at a
coarser scale than its device pixels — at the ~12px cap height a 3" character
renders at on a 375px screen, that is the difference between crisp vinyl and
mush. This shipped blurry once: a `blur(capPx * 0.012)` meant to soften the
vinyl's edges cost far more in sharpness than it bought in realism. The blur is
gone outright and the blend stops at the 760px breakpoint. **A flat overlay
that is sharp beats a blended one that is not**, and `verify.py` fails the
build if either comes back.

#### Which plate

The view follows the product: **registration numbers go on the bow** (side
view), **a name goes on the transom**. A "Both" order shows the side, because
the numbers are the half with a legal placement rule.

The hull is then picked to contrast with the film — white vinyl gets the dark
plate, black gets the light one. That is 33 CFR 173.27's contrast requirement
demonstrated rather than described, and it replaces what the flat panel's
night-flip was doing abstractly. **With an outline it is the outline colour
that decides**, because the outline is what touches the hull.

`verify.py` requires a plate for all four view/hull combinations: without one,
some colour and product combination silently falls back to a hull its vinyl
cannot be seen against.

#### Cap height, measured not assumed

Character height in the regulation means **cap height**, and a face's cap
height is a fraction of its em that varies per family. A name with ascenders
and descenders ("Sea Ya Later") has a bounding box taller than its capitals, so
sizing from the rendered box would make every script face read small.
`capRatio()` measures a lone "H" in the same family and caches it — but
**refuses to cache a ratio outside 0.4–1.2**, because a face that has not
downloaded yet measures against the fallback and that wrong number would stick
for the whole session.

#### The flat view

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

### Registration number validation (tier 1)

`engine/validate.py` emits the client validator; `worker/index.js: checkNumber`
mirrors it. Four checks, in the order a typo actually happens: prefix is a real
vessel prefix → shape is plausible → characters are issuable → groups are
separated.

⚠️ **It warns. It never blocks.** The prefix table is secondary-sourced, states
issue sequentially so old hulls carry retired formats, and this is only tier 1
of the rules. An order refused by an incomplete validator is a lost sale; an
order flagged for the proof is a thirty-second check by someone who knows.

#### The prefix table

`content.py: VESSEL_PREFIX` — set by the USCG in 1958, five years before the
Post Office picked its own codes, so **11 states disagree** with the postal
abbreviation. Two of them collide, which is the whole reason this is a table
and not a postal lookup:

| Prefix | Is actually |
|---|---|
| `MS` | **Massachusetts** (not Mississippi) |
| `MI` | **Mississippi** (not Michigan) |
| `MC` | **Michigan** |

`POSTAL_MISTAKE` holds the 9 postal codes that are *not* themselves valid
prefixes, so we can say exactly what the customer meant. **MI and MS are
deliberately excluded** — both are valid prefixes, so "did you mean" there
would be wrong as often as right.

`verify.py` fails the build if `PREFIX_STATE` drifts between `content.py` and
the worker.

#### Gotchas that already bit

- **Maine is an exception to the letter-count rule, so it must be checked
  *instead of* it**, not before. A valid `ME 12ABC` has three trailing letters
  and the generic rule flagged it.
- The validator's CSS classes are `vok`/`vnote`/`vwarn` — `ok` and `note` are
  already global classes and the message picked up the big amber callout box.
- State pages use `POSTAL_TO_VESSEL` (all 11), not `POSTAL_MISTAKE` (9). On
  Michigan's own page there's nothing ambiguous about "yours is MC, not MI".

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

**The ten faces Ryan cuts with**, defined once in `content.py: FONTS` as
`(label, css stack, Google spec, block_legal, match note)`.

| he asked for | the site serves | how close | legal on a number |
|---|---|---|---|
| Arial Bold | Arimo Bold | metric-compatible Arial | yes |
| Arial Black | Archivo Black | very close | yes |
| Impact | Anton | the standard open Impact | yes |
| OCR A Extended | Nova Mono | **loose** — OCR-ish mono, not OCR A | yes |
| MS Gothic | Noto Sans Mono | **loose** — plain mono sans | yes |
| Bodoni MT | Bodoni Moda | the same typeface | no |
| Rockwell Extra Bold | Alfa Slab One | heavier than Rockwell XB | no |
| Playbill | Rye | western slab, same spirit | no |
| Snap ITC | Bowlby One | fat round, less extreme | no |
| Stencil | Stardos Stencil | close | no |

#### Why not the fonts he actually named

All ten originals ship with Windows or Office under a licence that covers
**installing** them, not serving them as webfonts. And a visitor on a Mac or a
phone does not have them at all — a face the browser cannot load falls back
silently, so the customer would approve one thing and receive another. That is
the single failure the preview and the proof exist to prevent.

So the rule is: **the site renders what Ryan cuts.** He installs these ten
open faces, and the picker, the proof and the plotter agree. The two marked
*loose* are the ones to revisit — OCR A and MS Gothic have no close open
equivalent, and if the look matters they need a different choice.

#### The shape of the list

`FONT_COLS = 5`, ten faces, so the grid is two clean rows — and **the five
block-legal faces are deliberately the first five**, so a registration-numbers
order shows one tidy row with nothing hidden. `verify.py` fails the build if
the count stops dividing into rows of five, if the legal faces stop being
exactly the first row, or if any face loses its match note — that judgement is
the whole reason the substitution is defensible.

#### Every face is orderable, and five of them carry a warning

`block_legal` marks the five that plainly satisfy 33 CFR 173.27's "plain
vertical block characters". The other five are serif, stencilled or
decorative.

They used to be **hidden** on a registration-numbers order, and the worker
silently rewrote any that got through to Block — which meant cutting something
the customer never chose and never saw on their proof. The shop decided all
ten should be orderable on both products, so nothing is hidden and nothing is
rewritten.

**What replaced the filter is a warning, and it is gated in three places**,
because the site advertises *"Meets 33 CFR 173.27"* on every page and that
claim cannot quietly stop being true for an order:

- the order form says so when the face is picked, before payment
- the **proof** carries it, since that is the document being approved
- the shop email flags it, so Ryan knows before the plotter runs

The headline claim itself was reworded to match: it now says we flag a
decorative pick rather than implying every order meets the rule.

This is a real trade. Hiding them made every order compliant by construction;
warning makes every order *informed*. The second is the shop's call to make —
an officer's reading of "plain block" is a judgement, and Ryan deals with the
customers who find out.

**Nothing is preselected.** The step will not advance until a face is picked,
and a face that becomes illegal (picking a transom font then switching to
numbers) is cleared rather than silently swapped — picking for the customer is
how you cut a font nobody chose.

#### What the 45-face version needed and this does not

Three category tabs, per-category lazy stylesheet loading, and a 15-per-tab
budget all existed to make 45 faces survivable on a phone — 650KB of type if
loaded at once. Ten faces is about 90KB, so it all loads with the page and the
tabs are gone.

`worker/index.js` keeps its own `BLOCK_FONTS` copy and coerces a non-block font
to the first legal one on a registration-numbers order. It is the obvious thing
to forget — it has now gone stale twice, and `verify.py` fails the build if the
two lists drift in either direction. It caught this change too.

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
it, pointing numbermyboat.com at this worker would put a dead card field in
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

- `DB` → D1 `boatnumbershop` (`43724d47-…`), schema in `schema.sql`. The
  database keeps its original name on purpose — it is an existing CF resource
  and renaming it here would point the worker at a database that does not exist.
- `RESEND_API_KEY`, `ORDER_TO` → set ✅
- `ORDER_FROM` → currently `onboarding@resend.dev`. **Verify numbermyboat.com
  in Resend and switch this to `orders@numbermyboat.com` before launch.**

## Before launch

See the "Before this takes a real order" checklist in `STRATEGY.md`.

## No personal information on this site

The shop runs out of a private home, so **there is no street address, no phone
number and no coordinates anywhere** — site, schema, `llms.txt` or otherwise.
Town and state stay: "cut in Evansdale, Iowa" is a real differentiator and
gives nothing away. Contact is email only; local pickup is arranged by email
and the address is sent privately.

Two consequences worth knowing before you "helpfully" add a NAP block back:

* The schema is **`OnlineStore` + `Organization`, never `LocalBusiness`**. A
  LocalBusiness entity with no street address is a half-filled listing, and
  this site ships to all 50 states rather than wanting walk-ins.
* `SITE` no longer carries `street`, `postal`, `phone_display`, `phone_tel`,
  `lat` or `lng`. They were deleted rather than blanked, so a NAP block cannot
  be reassembled by reaching for a key that is still sitting there.

`verify.py` fails the build on the old phone number, the old street, a `tel:`
link, `streetAddress`, `GeoCoordinates`, a `LocalBusiness` entity, a Google
Maps link, or the owner's name.

## Writing background waiters: two traps

Both of these cost a day of a stuck process, so they are written down.

```bash
# WRONG - the shell's own command line contains "nano_banana", so pgrep
# matches itself and the loop never exits.
until ! pgrep -f nano_banana; do sleep 6; done

# RIGHT - exclude self, and match the actual interpreter invocation.
until ! pgrep -f "python3 .*nano_banana\.py" | grep -qv "^$$\b"; do sleep 6; done
```

And never gate a wait on a **count of files** that a later decision might
reduce:

```bash
# WRONG - waits for 6 hub images. One got deleted for being bad, so this
# waited forever.
until [ "$(ls media/shots | grep -c '^HB-')" -ge 6 ]; do sleep 12; done
```

Wait on the producing process exiting, not on an artefact count.

## Share cards

Two sets, both rendered at build time by `media/og.py` into 1200x630 PNGs —
the size Facebook crops to.

**`public/assets/og/`** — one card per page, wired into `og:image`. The URL is
derived from the page path by `build.og_image()`, and `verify.py` fails the
build if any page's card is missing or suspiciously small. A broken share card
renders on Facebook as a blank grey box, which is worse than no card.

**`public/assets/share/`** — a standalone library for posting straight into
boating groups. No link, no pitch: the domain is cut small into the bottom of
the card and that is the whole advert. A group that deletes link posts will
leave up a picture of a boat called *Payment 12 Of 240*.

Copy lives in `media/og_lines.py` (per page) and `media/share.py` (the
library). The funny names are read out of the generator's own bank in
`engine/namegen.py`, so the library and the tool cannot drift apart.

### Why the type is converted to paths

librsvg on macOS renders through CoreText, not fontconfig, so a font that
isn't installed system-wide falls back to Helvetica **silently** — the cards
would ship in the wrong face with nothing failing. `media/ogtype.py` turns the
glyphs into outlines with fontTools before rendering, so the PNG is identical
on any machine and nothing has to be installed. It is also what a plotter
does: it never sets type, it cuts a path.

Fonts live in `media/fonts/` (Archivo Black, Pacifico — both OFL).
