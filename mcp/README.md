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

## Next

1. The deterministic gates (radio, fit, overuse, photo, dedupe) — pure
   functions, testable without a model, and the thing that makes this not a
   slot machine.
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
