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
| **0 — home** | **IA 340k** | Home state. Researched to the bottom: `IA 3717 ZW` format, registers via **county recorder** not the DNR, validation decal **4 inches toward the stern, in line with the number**, and no other numbers permitted on the bow. This is the depth template every other state page should eventually reach. |
| **1 — built** | FL 1.7M, MI 1.7M, NY 1.3M, CA 1.3M, SC 1.1M, WI 1.1M, MN 1.0M, TX 922k, PA 842k, NC 799k, GA 783k, VA 595k, OH 573k, IL 566k, MO 561k | Largest fleets, all measurable volume |
| **2 — built** | WA 560k, TN 476k, LA 446k, AL 419k, IN 523k | Good fleet, thinner volume |
| **3 — hold** | Remaining 30 + DC | Build only once Tier 1 indexes and ranks |

⚠️ **Do not bulk-generate the remaining 30.** That is the mistake the aaron.chat
town grid made. Each page must carry real distinct facts — prefix, agency, fleet,
vernacular — or it is a doorway page.

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

## 7. Offer, and why $19

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
| **Us** | **$19** | free | next business day | 7 yr |

Undercuts the branded anchor by 24%, clears the $10–14 marketplace floor enough to
stay credible and profitable, reads as "under twenty."

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
- [ ] Register **boatnumbershop.com**, add to Cloudflare, route the `boatdecals` Worker
- [ ] **Confirm pricing and COGS with your brother** — $19 and the whole ladder are my
      recommendation from market data, not his numbers
- [x] **Film-life figures pulled from the whole site** (2026-10-23, Aaron's call).
      No year number is published for our film or for the cheap sets; `verify.py`
      gates it. Restore only with a spec sheet for the film actually in the shop.
- [ ] Verify boatnumbershop.com in Resend, switch `ORDER_FROM` off `onboarding@resend.dev`
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
