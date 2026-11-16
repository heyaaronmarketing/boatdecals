# Boat Number Shop — gap analysis & strategy

All volumes from live DataForSEO pulls (`keywords_data/google_ads/search_volume`,
location 2840) and SERPs from `serp/google/organic/live/advanced`, **2026-10-22**.
Re-pull before acting on anything here in six months.

---

## 1. The premise needed correcting

The brief was "compete with boatletteringtoyou.com and boatdecalslettering.com."
The SERP data says that framing is half wrong.

| Money term | Vol/mo | Who actually ranks top-10 |
|---|---|---|
| boat registration numbers | **5,400** | alphabetsigns (#2, #6), hardlineproducts (#3), signs.com (#5), vinyldisorder (#7), Amazon (#8), discoverboating (#9), wholesalemarine (#10) |
| boat decals | 3,600 | stevediossy, thecustomcaptain, stickeryou, boatus |
| boat lettering | 2,400 | **boatletteringtoyou #1 AND #2** |
| boat name decals | 1,600 | zoombuffalo, Amazon, eBay, lettering.com, boatdecals.com |

**boatletteringtoyou.com owns exactly one term — "boat lettering."** It is absent
from the biggest money term, from "boat decals," and from "boat name decals."
**boatdecalslettering.com did not appear in a single top-10 I pulled.**

The real competitive set is generic sign shops (alphabetsigns, signs.com,
vinyldisorder), marketplaces (Amazon, eBay, Etsy), and one sleeper:
**domednumbers.com**, which ranks #1 for "mercury boat decals" and #3 for "boat
hull numbers" — they found the OEM angle first.

### The index is astonishingly shallow

`se_results_count` across every term tested: **99–193 total results**. Ninety-nine
results for "florida boat registration numbers." Normal commercial niches run to
millions. This category is genuinely under-built — which is the whole opportunity.

---

## 2. Keyword gaps — what the original sitemap missed

Harvested via `keyword_suggestions` across five seeds. Five clusters were absent
from the first plan, and four are now built.

### GAP 1 — OEM / motor / brand replacement decals ✅ built
`/motor-and-brand-decals/`

| Keyword | Vol | CPC |
|---|---|---|
| mercury boat decals | 880 | $0.85 |
| yamaha boat motor decals | 480 | $0.75 |
| ranger boat decals | 480 | $0.71 |
| tracker boat decals | 480 | $0.48 |
| boat motor decals | 320 | $0.61 |
| lund / mastercraft / johnson / skeeter / bass boat decals | 210 ea | $0.45–1.46 |

**~3,000/mo at $0.45–1.46 CPC.** A tenth the click cost of the core terms, high
purchase intent (restoration), and neither named competitor targets it. This is a
whole second revenue line.

⚠️ Trademark discipline is non-negotiable: replacement decals for an owner
restoring their own boat, never for resale, quantity, or a non-matching hull. The
page states this publicly and that line stays in.

### GAP 2 — Boat carpet decals ✅ built
`/boat-carpet-decals/` — carpet decals 590 + bass boat carpet decals 390 ≈
**1,000/mo at ~$0.60 CPC.** Different product (high-tack film), near-zero
competition, natural attach to bass-boat buyers.

### GAP 3 — HIN / hull-number lookup ✅ built as a tool
`/tools/hull-number-decoder/`

| Keyword | Vol | CPC | Comp |
|---|---|---|---|
| boat hull numbers / hull id / hin numbers | 880 ×3 | $1.79–2.97 | LOW–MED |
| boat hull numbers lookup / search | 720 | $2.13 | LOW |
| boat serial numbers lookup | 590 | $2.72 | LOW |
| lookup boat registration numbers / search | 320 ×2 | $1.56 | LOW |
| boat vin numbers lookup / trailer vin | 260 ×2 | $1.59–2.76 | LOW |
| boat identification / id numbers | 210 ×2 | $2.02–2.22 | HIGH |

**~4,500/mo, almost all LOW competition.**

🚩 **These people are not buying decals.** They are decoding a hull number. Judge
this page on traffic, authority and AI citations — *not* conversion. The tool
exists because it is genuinely useful, it is highly linkable, and it lets us own
the "a HIN is not your registration number" distinction that AI engines keep
getting asked about.

### GAP 4 — the "funny boat names" monster ✅ built
`/tools/boat-name-generator/` + `/tools/funny-boat-names/`

| Keyword | Vol | CPC | Comp |
|---|---|---|---|
| funny boat names | **8,100** | $0.09 | **LOW** |
| boat name generator | 1,900 | $1.61 | **LOW** |
| boat name ideas | 880 | $0.15 | MED |

**~10,900/mo, LOW competition, pennies per click.** Bigger than any commercial
term on the board and far softer. Current top-10 is magazines and generic name
generators — *nobody who can actually cut the name owns it.* That is the single
largest organic opportunity here, and it feeds straight into boat name decals
(1,600 + 480/mo).

### GAP 5 — California vernacular 🔑
"california boat registration numbers" = **20/mo**.
"cf numbers on boat" + "cf boat numbers" + "boat cf numbers" = **630/mo**.

California uses the prefix **CF**, not CA, and locals call them CF numbers. A
templated 50-state build would have targeted the 20 and missed the 630.
Washington is **WN**, not WA. **Lesson: state pages need vernacular research, not
a template.** Both are handled in `content.py` via the `vern` / `note` fields.

### Also corrected
- "boat registration numbers" true head volume is **5,400**, not 4,400 — the
  "boat reg numbers" / "boat register numbers" variants cluster higher.
- "boat lettering to you" = **320/mo @ $4.10** — people search the incumbent by
  name. A comparison page is a legitimate future capture (not yet built).
- Placement questions: "where to place / where are / where on the boat are
  registration numbers placed" ≈ **700–900/mo at $0.00 CPC, LOW comp.** Pure AEO.

---

## 3. Geographic gaps

### The state SERPs are soft because sellers aren't competing

"florida boat registration numbers" top-10: **flhsmv.gov, boat-ed.com,
boatdecals.com, driveaboatusa, aceboater, sarasotataxcollector.gov, YouTube,
boatletteringtoyou (#10), mdctaxcollector.gov.**

**Only 2 of 10 are sellers.** Eight are government or boater-education sites that
answer the rules and then leave the visitor with nowhere to buy. A page that fully
answers the rules *and* sells the product has no real competition there.

This — not search volume — is why state pages are worth building. Volume is thin:
FL and MI top out at 140/mo, TX and GA at 110, and 31 of 80 state-term variants
returned **zero**. Treat state pages as an *authority and AEO* surface with a
transactional path, not a traffic play.

### Priority: fleet size × volume × SERP softness

20 states built, ordered by registered vessels:

| Tier | States | Why |
|---|---|---|
| **0 — home** | **IA 340k** | Home state. Researched to the bottom: `IA 3717 ZW` format, registers via **county recorder** not the DNR, validation decal **4 inches toward the stern, in line with the number**, and no other numbers permitted on the bow. This was the depth template every other state page had to reach — **all 21 reached it on 2026-11-16**. |
| **1 — built** | FL 1.7M, MI 1.7M, NY 1.3M, CA 1.3M, SC 1.1M, WI 1.1M, MN 1.0M, TX 922k, PA 842k, NC 799k, GA 783k, VA 595k, OH 573k, IL 566k, MO 561k | Largest fleets, all measurable volume |
| **2 — built** | WA 560k, TN 476k, LA 446k, AL 419k, IN 523k | Good fleet, thinner volume |
| **3 — hold** | Remaining 30 + DC | Build only once Tier 1 indexes and ranks |

⚠️ **Do not bulk-generate the remaining 30.** That is the mistake the aaron.chat
town grid made. Each page must carry real distinct facts — prefix, agency, fleet,
vernacular — or it is a doorway page.

### Depth before width — what 2026-11-16 added, and why it was not 29 new states

The roadmap's next step read "the remaining 29 states." This document's own
Tier 3 line says the opposite — **hold until Tier 1 indexes and ranks** — and
Tier 1 was published days ago. So the work went into depth instead, and found
that **20 of the 21 pages had no `fmt` and no `decal` at all.** Only Iowa, the
template, carried them. Twenty pages were asserting authority on a question
they did not answer.

All 21 now state, from the state's own page:

- the **number format** as that state writes it (18 of 21 — Florida, New York
  and Indiana publish no letter pattern, so those pages say nothing rather than
  invent one), and
- **exactly where the validation decal goes**, with the source linked and the
  date a human read it, rendered on the page so it ages in public.

That second one is the whole point. It is the most-asked question on a state
page, the competitor answers it nowhere, and **it is genuinely different in
every state** — which is the proof these are not templated doorway pages:

| State | Where the decal goes |
|---|---|
| Florida | **port (left) side only**, immediately before or after the number |
| Georgia | **before the prefix letters** — forward of the number |
| Texas | in line with, **3 inches toward the stern** |
| Missouri | **below** each MO number |
| New York | **18 inches from the bow**, measured off the bow, not the number |
| Minnesota | toward the stern within 4in, and **nothing else within 24 inches** |
| Michigan | 3in beyond the last letter, **on the same strake** |
| Indiana | **3 inches to the right** of the number |
| Ohio | **6 inches** toward the stern |
| Tennessee | left **or** right — and on a documented boat, **on the windows by the helm** |

Three findings worth keeping:

1. **Search summaries drift from the state's page.** A summary said Florida's
   decal sits "within 6 inches" of the number; FLHSMV's own page says *port
   side, immediately before or after*, with no inches at all. Everything here
   was read off the primary page for that reason.
2. **Alabama's figures come from a proposed rule.** ALEA's chapter 760-X-6 was
   certified as a *notice of intended action* on 20 July 2026, comment closing
   4 September; adoption is unconfirmed. The page says so in its own words.
3. **Two defects surfaced while writing it**, both shipped and both now gated:
   the Iowa hull (`AL-01`, captioned "validation decal aft") padded **all 21**
   state pages — harmless until each page stated its own rule, at which point
   it contradicted Georgia, Florida, Missouri and New York; and Missouri's
   prose sent readers to the **Highway Patrol** while the fee block named the
   **Department of Revenue**, which is the agency that actually registers the
   boat.

### Local geography — new, because your brother has a shop

This was impossible when the plan was rank-and-rent. It is live now:

- **`local_pack` appears on "boat lettering."** A GBP can rank.
- "boat lettering near me" **390/mo @ $2.52**, "boat decals near me" **260/mo @ $3.04**
- A real shop, a real address and a real person is **E-E-A-T the entire
  competitive set lacks** — alphabetsigns, signs.com and vinyldisorder are faceless.

✅ **Done 2026-10-22.** Real NAP is live site-wide:
**Boat Number Shop, 475 River Forest Road, Evansdale, IA 50707 · (319) 239-3793 ·
Mon–Fri 8–5 CT.**

- `LocalBusiness` + `OnlineStore` on one `@id`, with PostalAddress, GeoCoordinates
  (city-level — GBP's pin becomes authoritative once claimed), opening hours, and
  `areaServed` = US + Black Hawk County
- Tappable phone in the topbar, header, footer and on `/contact/`
- One local page: `/boat-lettering-waterloo-cedar-falls/` — **deliberately one page,
  not a town grid.** Local volume is a handful a month; this exists to anchor the GBP
  and serve walk-ins, not to chase traffic
- `/registration-numbers/iowa/` added as the home state, and it is the deepest state
  page on the site (see below)

⚠️ **NAP must match the GBP and every citation character-for-character.** It is
written once in `content.py: SITE` — change it there, never in a template.

⚠️ **This looks like a residential address.** Google Business Profile lets a
home-based business hide the street address and show a service area instead. Worth
deciding with your brother *before* claiming the GBP — it is awkward to change after.

**History of this decision, because it has moved twice.** The NAP went live
2026-10-22, came off the whole site 2026-10-30 (`07f415f`, Aaron's call: the shop
runs out of a private home, so the address and the landline were personal
information), and went back on 2026-11-15 (Aaron's call again, after the local-pack
and E-E-A-T upside was put against it). What came back is the **phone and the
address only**. Three things did *not* come back, and each is a separate decision:

| Still off the site | Why |
|---|---|
| Coordinates | No rooftop pin. Once the GBP is claimed Google's own pin is authoritative and a lat/lng here only competes with it. |
| Maps links and the embed | The address in text does the SEO work; an iframe is third-party JS on the contact page. |
| The About page, the owner's photo, his name in visible text | The name is approved for the `Article` author node only — Aaron's 2026-11-14 call, untouched by this. |

⚠️ The gate **flipped rather than disappeared**. It used to prove the phone and
street were absent; it now proves there is exactly **one spelling of each**, present
in the footer of every page and in the org node. The failure mode is no longer a
leak — it is a second spelling, which breaks a citation match and is invisible on
the page.

---

## 4. AI engine (AEO) gaps — the strongest signal in the whole analysis

**AI Overviews appeared on 7 of the 10 SERPs tested:** boat registration numbers,
boat name decals, boat hull numbers, cf numbers on boat, boat name generator,
where to place boat registration numbers, florida boat registration numbers.

This is an AEO-first category. Whoever writes the most precise, citable answer
gets quoted — and the incumbent is weak exactly where citation happens.

### The incumbent's state pages are shallow

I read boatletteringtoyou's Wisconsin page: ~900 words, and the *only* rule stated
is "3 inches, block lettering." No contrast rule. No spacing rule. No placement.
No validation decal. That is the gap, and it is wide.

**Our answer:** `copy_blocks.py: FED_RULE` carries all five requirements of
33 CFR 173.27 verbatim-verified, on every state page, every relevant product page,
the layout checker and `llms.txt`.

### Six "where can I buy" questions sit in PAA

Harvested live: *Where can I get boat decals made? · Where can I buy boat decals? ·
Who makes the best boat decals? · Where can I purchase custom decals? · Where can
I find waterproof decals for boats? · Where can I find Mercury outboard decals?*

These are the AEO money questions — a citation here is revenue, not traffic.
Answered directly in `FAQ_HOME` and `llms.txt`.

### Other PAA answered on-site
*Do boat registration numbers have to be a certain colour?* (the contrast rule the
incumbent omits) · *What kind of vinyl is best for boat decals?* · *What is the
difference between vinyl stickers and vinyl decals?* · *What is a hull number?* ·
*Can you tell the year of a boat by the hull number?* · *Is the hull number the
same as the VIN?* · *What does CF stand for on a boat?*

### The informational cluster, re-pulled 2026-11-15

Live DataForSEO, US, $0.09, raw response kept in `research/raw/`:

| keyword | volume | CPC |
|---|---|---|
| how much does it cost to register a boat | **320** | — |
| boat registration number placement | 170 | $0.60 |
| **boat registration number requirements** | **140** | **$1.74** |
| boat registration number size | 70 | $0.71 |
| how to display boat registration numbers | 30 | — |
| boat registration number spacing | 10 | $2.47 |
| boat registration number **rules** | *none* | — |
| boat registration **fees by state** / cost by state | *none* | — |
| 33 cfr 173.27 | *none* | — |

Two decisions came out of this.

**The rules guide was targeting the one phrasing nobody searches.** Its own entry
already declared `kw="boat registration number requirements"`; only the title said
"Rules". Retitled. The slug stays — a keyword in a URL is worth very little and a
redirect costs more than it buys.

**"How much does it cost to register a boat" (320) had no page.** It is a question
about what the *state* charges; `/guides/boat-registration-number-cost/` answers
what *our decals* cost. Different question. That gap is now
`/guides/how-much-does-it-cost-to-register-a-boat/`, and it is the one page here a
competitor cannot copy without doing the same reading — every figure on it is
rendered from `state_fees.py`, which took a day of reading .gov fee schedules.

⚠️ **Note what is NOT there.** Nobody searches "boat registration fees by state" or
"33 cfr 173.27", so neither is a page title. The regulation is a credibility
citation inside pages, not a target.

### Shipped for AEO
- `llms.txt` — the full federal rule, the CF/WN exceptions, the HIN-vs-registration
  distinction, and every price, written to be lifted verbatim
- `robots.txt` explicitly allows GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot,
  Google-Extended, Applebot-Extended
- FAQPage schema on 40+ pages; Product + Offer with real prices; WebApplication on
  tools; Article on guides; BreadcrumbList everywhere — 61 JSON-LD blocks, all valid

🚩 **Verify Cloudflare's AI-bot blocking is OFF** for this zone before launch.
It silently undoes all of the above. (This bit Deuces Wild Poker.)

---

## 5. SEO gaps

1. **Price transparency is the wedge.** boatletteringtoyou publishes *no* price —
   you must build a design first. boatdecalslettering shows one ($24.95). The
   whole `/pricing/` page exists for this.
2. **The incumbent is the slowest credible player** — 3–5 business days to ship,
   versus lettering.com at same-day-by-1:30pm. We commit to next business day.
3. **Warranty asymmetry** — lettering.com offers 7 years, the BoatUS partner 5.
   We match the 7.
4. **Nobody has the tools.** No competitor offers a HIN decoder, a name generator
   or a compliance checker. Three linkable assets in a category with a 99-result
   index.
5. **continuouswave.com ranks #2 for "cf numbers on boat"** with a plain state
   abbreviation reference table. An enthusiast forum outranks every seller on a
   reference table — a sharper version is easy future content.

---

## 6. Social media gaps — evidenced from the SERP, not vibes

**YouTube ranks in 5 of the 10 SERPs tested.** Actual ranking videos:
- "How to Apply Boat Registration Numbers Like a Pro" — ranks on *two* terms
- "How To Install Boat Lettering & Decals Using the Dry Method"
- "How to Apply Boat Decals and Registration Numbers [DIY]"
- "Mercury Outboard Decal Replacement"
- "The Top 5 Best Boat Lettering Decals in 2026"

**Facebook ranks 4 times** — group threads on placement, CF numbers, and name
generators. Those groups are an active, locatable demand pool.

### What this means for a shop owner who physically does the work

| Channel | Play | Why it works here |
|---|---|---|
| **YouTube** (priority) | Install and removal how-tos, shot on real jobs | Already ranks *in Google* for install terms. Our `/guides/how-to-apply-boat-lettering/` and removal guide are the scripts — shoot them verbatim and embed. |
| **TikTok / Reels / Shorts** | Weeding and application ASMR, name reveals, before/after on faded motor cowlings | Vinyl weeding is a proven satisfying-content format. Your brother has the plotter — this is content nobody else in the category can fake. |
| **Facebook groups** | Answer placement/CF questions where they're already being asked | 4 group threads rank in Google. Participate honestly; link only when asked. |
| **Pinterest** | "Funny boat names" and name-idea boards | Pure overlap with the 10,900/mo name cluster. Cheap, evergreen. |
| **Buffer** | Scheduling TikTok / LinkedIn / Pinterest | Already the house tool. |

**The single highest-leverage asset:** a genuinely good "How to apply boat
registration numbers" video. It ranks in Google *and* YouTube, answers the most
common PAA, and ends with the product in the viewer's hand.

---

## 7. Offer, and the price

Verified market (2026-10-22):

| Player | Reg numbers / pair | Ship | Turnaround | Warranty |
|---|---|---|---|---|
| Etsy / eBay | $10.50–25 | free | varies | none |
| squaresigns | from $7.50 | — | — | — |
| alphabetsigns | $9.45–12.95 | free | — | — |
| signs.com | from $10.57 | — | — | — |
| lettering.com | from $14.38 | free ground | **same-day by 1:30 ET** | **7 yr** |
| boatdecalslettering | **$24.95** | — | same-day | 5–7 yr |
| **boatletteringtoyou** (BoatUS partner) | **hidden** | free | 3–5 days | 5 yr |
| **Us** | **$28** | free | next business day | 7 yr |

**The table above is a market snapshot from 2026-10-22 and the price no longer
follows from it.** The launch price was set against this data; Aaron reset it
to $28 on 2026-11-13, which is above `boatdecalslettering`'s $24.95 and well
above the marketplace floor, so the original rationale — undercut the branded
anchor, read as "under twenty" — does not describe what we now sell.

That is not an argument against the price. It is a note that the *positioning*
has not been rewritten to match it, and the honest version of this section
needs Aaron's reasoning rather than a justification reverse-engineered from
the number. Until then: we are no longer the cheap option, and the pages lean
on pre-spacing, the state-format check, the 12-hour proof and free shipping,
which is what they already led with.

Names moved too, from a flat rate to four bands by the width the lettering
finishes at ($38 / $53 / $68 / $88), which is what /pricing/ had always said
it did.

**Margin, honestly:** vinyl ~$1.25 + tape ~$0.30 + mailer ~$1.25 + postage ~$4.50
+ processing ~$0.85 ≈ **$8–10 all-in → ~50% gross.** Thin on one pair, which is
why the upgrade ladder (premium film, name, hailing port, rush, reflective, kit)
matters more than the headline. **Have your brother confirm these COGS against his
actual material and postage costs before launch.**

---

## 8. Before this takes a real order

**Blocking**
- [ ] **Decide the GBP address posture** — street address public, or hidden with a
      service area? The address looks residential. Decide before claiming
- [ ] Register **numbermyboat.com**, add to Cloudflare, route the `boatdecals` Worker
- [ ] **Confirm pricing and COGS with your brother** — the ladder was my
      recommendation from market data; the 2026-11-13 figures ($28 base, name
      bands, $10 bundle) are Aaron's. Still unconfirmed against Ryan's actual
      material and time cost
- [x] **Film-life figures pulled from the whole site** (2026-10-23, Aaron's call).
      No year number is published for our film or for the cheap sets; `verify.py`
      gates it. Restore only with a spec sheet for the film actually in the shop.
- [ ] Verify numbermyboat.com in Resend, switch `ORDER_FROM` off `onboarding@resend.dev`
- [ ] Payment: the flow is proof-then-payment-link today. Decide Stripe Checkout vs
      manual invoice before volume

**High value, not blocking**
- [ ] **Claim the GBP** — `local_pack` is live on "boat lettering", NAP and schema are ready
- [ ] Local citations with the exact NAP string (chamber, BBB, Apple/Bing Maps, Nextdoor)
- [ ] GSC + Bing + IndexNow
- [ ] Shoot the install video — the highest-leverage asset on this list
- [ ] Real product photography (no stock, no AI-generated "customers")
- [ ] Turnstile on `/api/order`
- [ ] Tier 3 states — **only after Tier 1 ranks**

---

## Re-pull log

This file reasons from volumes pulled on a date. Each re-pull is appended here
rather than overwriting the numbers above, because the original figures are
what the pages were built on and that decision record matters. Raw responses
live in `research/raw/`, every paid call is costed in `research/api-log.md`,
and the client is `mcp/dfs.py` (run by hand, never on a cron).

### 2026-11-14 — money terms, `keywords_data/google_ads/search_volume/live`

| Term | 2026-10-22 | 2026-11-14 | CPC |
|---|---|---|---|
| boat registration numbers | 5,400 | **4,400** | $3.00 |
| boat decals | 3,600 | 3,600 | $3.54 |
| boat lettering | 2,400 | **1,900** | $5.27 |
| boat name decals | 1,600 | 1,600 | $3.46 |
| boat numbers | — | 1,300 | $3.14 |
| boat hull numbers | — | 880 | $2.56 |
| boat registration number stickers | — | 320 | $3.25 |
| custom boat lettering | — | 260 | $4.03 |
| boat name lettering | — | 260 | $3.50 |

Two terms fell about 20% and two did not move at all. **This is a season, not a
trend.** Google Ads reports a trailing twelve-month average, so a November pull
is weighted toward the end of the northern boating season; the terms that held
are the ones people search when a boat is already out of the water and the
paperwork is due. Nothing here changes what to build. Re-pull in March before
reading anything into the direction.

**One trap worth recording, because this niche is full of it.** "registration
numbers for boat" returns **4,400 — identical to "boat registration numbers."**
That is not a second market. Google reports close variants at the same volume,
and adding them would have invented 4,400 searches a month that do not exist.
Nothing in this file is a sum of a keyword list, and it must not become one.
