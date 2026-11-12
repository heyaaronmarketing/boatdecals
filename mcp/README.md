# Number My Boat in AI chat — MCP server

Build against `AI-CHAT-COMMERCE-BUILD-SPEC.md` v3.4. This directory is the
MCP server and the naming engine. It lives **inside the site repo on purpose**:
the spec's hardest rule is one pricing source, one renderer, one order
pipeline, and the cheapest way to honor that is to make a second copy
impossible to create without failing the build.

## Step 0 — what exists and is reusable (audited 2026-11-12)

| Spec asks for | Where it already lives | Status |
|---|---|---|
| Pricing function | `worker/index.js` `priceOf()` | **Authority.** Now exposed read-only at `/api/price` |
| Catalog (products, colors, fonts) | `engine/content.py` | Built to `/catalog.json` |
| Preview renderer | `engine/preview.py`, `worker/outline.js` | Not yet wired to MCP |
| Order pipeline + Stripe | `worker/index.js` `/api/order`, `/api/checkout` | Reuse as-is |
| Name bank (1,000+) | `engine/namegen.py` (JS literal, 21 categories) | Extracted |
| Funny names | `engine/tools.py` `FUNNY_GROUPS` | Extracted |
| Layout checker state data | `engine/state_data.py`, `engine/validate.py` | Not yet wired |
| HIN decoder | `engine/tools.py` | Not yet wired |
| Policies (`get_policies`) | `/shipping-and-returns/`, `/warranty/`, `/terms/` | Not yet wired |

### Findings that change the spec

1. **The bank is 1,089 names, not 1,400.** The generator holds 1,005 across 21
   categories (spec said 22). The funny-names page holds **110**, not 400, and
   26 of those are already in the generator — so it contributes 84 new names.

2. **The funny-names page overstates itself.** Its `<title>` and meta
   description both say "400 funny boat names"; the page renders 110. That is
   a live page targeting ~8,100 searches/month. Either the copy comes down to
   110 or the list grows to 400 — Aaron's call, flagged not silently changed.

3. **Every locked fact in the spec matches the live site exactly** — all three
   base prices, the four height steps, outline at $12, all 8 colors including
   their hexes, all 10 fonts in the same order, free US shipping, the 12-hour
   proof rule. No reconciliation needed.

4. **Pricing had no read-only surface.** Quoting a price previously meant
   calling `/api/checkout`, which creates a Stripe PaymentIntent. An assistant
   quoting prices would have littered the Stripe account with abandoned
   intents. `/api/price` fixes that.

## What is built

- `extract_bank.mjs` — lifts the generator's JS object literal into data.
  Brace-balanced rather than regex-parsed, and it fails loudly rather than
  truncating the bank.
- `build_bank.py` — merges that with `FUNNY_GROUPS` into `data/name_bank.json`.
  **Derived, never hand-edited:** a name added to either site source reaches
  the engine on the next build.
- `/catalog.json` (from `engine/build.py`) — what can be ordered.
- `/api/price` (worker) — what it costs, through the same `priceOf()` the
  order form and the Stripe intent use. Proven equal to `/api/checkout` across
  three configurations.
- Gates in `verify.py`: catalog vs worker prices, heights, outline, color and
  font lists, block-legal set, free shipping, the 12-hour proof window, and
  bank size/duplicates. Each proven against a deliberate break.

## The tagging pass (mechanism + level) — DONE, 1,089 of 1,089

Spec §2 and §4b: offline data task, no runtime LLM guessing, no name enters the
bank untagged. Mechanism and level first because the deterministic gates need
only those two; `style_lanes`, `boat_types`, `themes` and `overuse_tier` remain.

    engine/*.py        the names            (site source, authoritative)
    mcp/tags/*.tsv     the judgements       (hand-written, authoritative)
    mcp/data/*.json    the join of the two  (derived, never edited)

Tags are keyed by name, not by row number, so a name that leaves the site fails
the build instead of silently re-pointing a judgement at its neighbour.

| mechanism | count |
|---|---|
| literal truth | 194 |
| misdirection | 184 |
| deadpan understatement | 143 |
| in-group in-joke | 129 |
| homophone pun | 124 |
| double meaning | 109 |
| title twist | 104 |
| sincere (not a joke) | 53 |
| anagram | 38 |
| portmanteau | 11 |
| backronym | **0** |

Levels: 913 clean, 168 dock, 8 double.

### Three decisions the taxonomy forced

1. **`sincere` is an eleventh value.** §4b's ten all describe how a joke works,
   and the `classy` lane is 50 names that are not jokes. Tagging Halcyon as
   deadpan understatement is not a cosmetic error: the riff brief reads
   mechanisms to decide what to write next, so it would learn that a deadpan
   lane liked Halcyon and start writing more. `sincere` is a real value but
   **not** a humor mechanism — `HUMOR_MECHANISMS` excludes it and a gate fails
   the build if it leaks in. Gate 21's "100% carry a mechanism" still holds.

2. **`profession in-joke` is broadened to in-group in-joke.** The bank has three
   such lanes, not one: corporate jargon, Midwest dialect (Ope, Hotdish, Pop Not
   Soda) and Gen Z slang. Same mechanism doing the same work — lands only on a
   member, invisible to everyone else — so one tag and one rule for the ranker:
   never deal `pj` until the interview proves membership. The §4b count stays
   at ten.

3. **`backronym` has no example in the entire bank.** The spec names a mechanism
   the house has never used. Either it is a gap worth 20 new names or it comes
   out of the taxonomy; it cannot be taught to the riff engine from exemplars
   that do not exist. Flagged, not decided.

### What the pass turned up

- **The radio gate's worst cases are already identified.** All 30 `misspelled`
  names are built to be heard right and spelled wrong — they *should* fail, and
  they are in the bank so the engine can demonstrate a failure rather than deal
  one. Separately, `Crappie Attitude` / `Crappie Day` / `Crappie Hour` say a
  word over VHF that sounds like another word entirely.
- **`horror` is the most title-twist-heavy lane**, which is a ranker risk: a tt
  name only lands on someone who knows the source, so a round full of them is a
  round that may land on nobody.
- **Every `divorce` name is graded dock**, including the gentle ones. The level
  field is the only thing keeping that lane away from a man naming the boat he
  takes his wife out on.
- **Ambiguous innuendo graded up, not down.** A gate that wrongly withholds a
  clean name costs one name; one that wrongly deals a crude name costs the
  customer his transom and the shop the job.
- `Vitamin Sea` and `Seas the Day` — the spec's named Tier-1 clichés — are both
  tagged and in the bank. The overuse gate, not the mechanism tag, excludes them.

## The deterministic gates — all four DONE

`mcp/gates.py`. Pure functions: no model, no network, no randomness. The same
name gets the same verdict every time, and every verdict can be read out to a
customer in one sentence. The engine's credibility rests on *testing* names,
and a test whose answer moves is not a test.

### The radio gate

The scenario is an owner on channel 16 saying his boat's name to somebody who
has never heard it and has to write it down. Three different things go wrong,
and they are not the same problem:

| verdict | what it means |
|---|---|
| `clear` | says clean and spells itself |
| `sayable` | a homophone — "say it twice the first time". **Most of this bank.** |
| `mouthful` | long. Fine on a transom, slow on a radio |
| `spell_it` | nonstandard spelling or a coinage: spelled out every single time |
| `fail` | **the rebus class only.** Not dealable. |

Spec test 11 pins the line and the suite asserts it: `Knot On Call` is fine,
the `Nauti-4-U` class fails. Over the whole bank: **813 clear, 128 sayable,
119 spell_it, 29 mouthful, 0 refused.**

Zero refused is the point, and it is a test. The bank is curated, so a gate
that rejects names the shop already sells is miscalibrated, not strict.

**Measured, not assumed.** Against the 30 names in the site's own `misspelled`
category: **29 of 30 caught.** The one miss is `Boat Goes Fast`, which is not
misspelled at all — the site files it there because the joke is the grammar.
Against the 53 `sincere` names: **0 false positives.** Across the rest of the
bank, 23 of 1,089 are flagged for a spell-out and every one is a genuine
coinage (Aquaholic, Delulu, Sofishticated, Dadmiral).

**Four wrong versions got there first**, each of which looked fine until it was
measured. All four are now test cases:

1. It failed `Unsinkable (Terms Apply)` on the grounds that you cannot say a
   bracket. You do not say the bracket — you say "Unsinkable, terms apply."
   What is actually lost is the deadpan, because nobody hears an asterisk. So
   it is not a radio failure at all; it is a separate `visual_only` fact worth
   telling a customer, and the spoken readback drops the punctuation.
2. It told customers that `Paid Off`, `Wave Goodbye` and `My Boat Has A Boat`
   needed spelling out letter by letter. `/usr/share/dict/words` is Webster's
   1913 and a **headword** list: "pay" but not "paid", "have" but not "has",
   "hear" but not "heard". 70 names were wrongly flagged.
3. It reported that "holic" and "rrito" are not words. The names are
   `Aqua-holic` and `Buoy-rrito`; it was splitting on the hyphen.
4. It passed only 12 of the 30 deliberately-misspelled names, because
   Webster's 1913 lists **`bote`, `nawt`, `gud`, `shure`, `thee`, `bois` and
   `da`** as real archaic words. That is the honest cost of a free dictionary
   with no frequency data, and an explicit `ARCHAIC_COLLISIONS` list handles it.

The respelling detector **generalises** rather than matching the bank: it is
built from the inverse of the substitutions people actually make (`k`→`c`,
`ph`→`f`, `y`→`i`, doubled final letter, `ote`→`oat`), applied up to twice,
each result checked against the lexicon. So it finds respellings nobody has
written yet, and it reports *what the listener will write*: say this and they
write "Boat".

### The lexicon

`mcp/data/lexicon.txt.gz`, 176,664 words, built by `build_lexicon.py` from
`/usr/share/dict/words` + `/usr/share/dict/propernames` + ~100 shop-specific
and modern additions. **Derived and committed**, the same as the name bank: a
deterministic gate must answer identically on this Mac, on a CI box and in the
worker, and that system file exists on exactly one of the three.

### The overuse gate

Tier 1 (29 names) is the one-in-every-marina class the spec names by example:
Serenity, Vitamin Sea, Seas the Day. Excluded from top picks, never silently
dropped, never shown without the note. Tier 2 (28) is common but not worn out.

**The honesty limit is enforced in code, not just documented.** We have no
registry and cannot see any particular marina, so `claims_are_honest()`
rejects "at your marina", "on your lake", "already taken" and four more, and a
test runs every tier note through it. "Common everywhere" is true. "Taken at
your marina" is a claim the first customer who checked would catch us on.

### The novelty gate

Bigram Dice coefficient against all 1,089 bank names, reporting the closest
match rather than a yes/no. A model handed this bank and told to be creative
returns a near-copy of something already in it, confidently, and it reads as
new until somebody searches. `Knot Workin` does not pass.

### The fit gate

The only one that cannot be done with text rules, because the answer is
physical: will this name, in this face, at this height, go on the flat run of
his hull?

`mcp/data/font_metrics.json` carries **per-character advance widths measured
out of all ten real TTFs** — the same files that cut the vinyl. Eight of the
ten live only in R2, so `build_font_metrics.py` pulls them from the worker's
own `/api/outline`, which loads the font and reports `advance`, `upm` and
`capRatio`. Pulled once, committed, never needed at gate time.

Summing advances cannot see kerning, so that error was **measured rather than
assumed**: worst case **1.43%** across all ten faces, and the gate reports
that number to the customer instead of hiding it. It is far smaller than the
error in his own tape measure, and saying so is what makes the figure
believable.

Verdicts: `fits` / `height_capped` / `too_wide` / `measured` (no transom
given) / `unknown_font`. An uncuttable character is **reported, never counted
as zero width** — treating it as zero is how a 20-inch name gets quoted at 14.

`registration_gate()` is separate because it is law, not taste: 33 CFR 173.27
wants plain block characters at least 3 inches tall, so a script face and a
2-inch height are both hard failures with the rule cited.

### What the fit gate found on the live site

The generator page was computing `chars × 2.5" + spaces × 1.5"` at a fixed 4
inches, **with no idea which face was selected**. It was not slightly off:

| name | page said | actually | |
|---|---|---|---|
| Wet Couch | 21.5" | **30.4"** | +41% |
| The Undertow | 29" | **39"** | +34% |
| Knot Working | 29" | **38.1"** | +31% |
| Walleye Wednesday | 42" | **56"** | +33% |

A customer was measuring his transom against a number up to nine inches
short. And the spread across faces is enormous — Walleye Wednesday runs 37" in
Impact and 65" in Snap ITC, which one formula cannot express.

**Also fixed, same page:** the "Uniqueness" line printed *"You will not meet
another one of these"* for anything outside two categories, and told everyone
else to *"check your marina first."* The first claim was being made about
names like Vitamin Sea; the second implies we can see his marina. Both are
exactly the honesty limit spec §4a names. The line now reads from the real
overuse tiers and says plainly that we have market data, not a registry.

The page now carries the measured metrics and the tier lists as emitted data
from the same authorities, and four gates fail the build if the copies drift —
including one that checks `width()` actually **calls** the table, because the
first version of that test only checked the table was present and a revert to
the character-count guess passed it cleanly.

## The ChatGPT submission

`/.well-known/openai-apps-challenge` is live in the worker, served from the
`OPENAI_APPS_TOKEN` **secret** rather than a committed file. The token is a
bearer proof of domain ownership, so it does not belong in a public git
history, and a secret can be set or rotated with one `wrangler secret put` and
no deploy — which matters while a submission is waiting on it. With no secret
set it 404s, which is the honest answer: we cannot prove anything yet.

## Next

1. **The MCP server skeleton** with the pure-port read tools — `get_products`,
   `configure_order`, `check_registration_layout`, `decode_hull_number`,
   `get_policies`. These need no naming engine: the catalog, `/api/price`, the
   gates, `engine/validate.py` and the HIN decoder in `engine/tools.py` are all
   built. This is what makes the server real and submittable.
2. The remaining bank tags — `style_lanes`, `boat_types`, `themes`,
   `overuse_tier` — which the ranker needs but the gates do not.
3. Design Studio widget, then the tournament.
3. The MCP server skeleton with the pure-port read tools:
   `get_products`, `configure_order`, `check_registration_layout`,
   `decode_hull_number`, `get_policies`. These need no naming engine and make
   the server real.
4. Design Studio widget, then the tournament.

## Commands

```
node mcp/extract_bank.mjs    # generator -> data/_bank_js.json
python3 mcp/build_bank.py    # + funny names + tags -> data/name_bank.json
python3 mcp/apply_tags.py    # tag coverage report on its own
python3 engine/build.py      # writes public/catalog.json
python3 verify.py            # gates, including catalog/worker drift
```
