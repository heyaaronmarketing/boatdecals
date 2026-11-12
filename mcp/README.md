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

## The MCP server

`worker/mcp.js`, mounted at **`/mcp`** on the site's own worker. JSON-RPC 2.0
over HTTP POST; a plain GET returns what the server is, for anyone who opens
the URL in a browser.

Eleven tools. **Nine are read-only; `start_naming_session` and `vote_on_names` write session state and nothing else.** Nothing on this server takes money, writes
a row or sends mail — ordering stays on the site behind the real checkout, so
an assistant can quote, test and lay out a name but cannot buy on someone's
behalf. `verify.py` fails the build if a tool loses its `readOnlyHint`, or if
the file so much as references `db.prepare` or Stripe in code.

| tool | what it does |
|---|---|
| `get_products` | the catalog: products, heights, 8 colours, 10 faces, which are block-legal |
| `price_order` | the real price, through the **same `priceOf()`** the order form and the card charge use |
| `test_boat_name` | radio + fit + overuse in one call, the flagship |
| `check_name_is_new` | novelty against all 1,089 curated names |
| `measure_lettering` | width in any face at any height, from the real font files |
| `check_registration_layout` | prefix, shape, unissued letters, spacing, legal height, finished width |
| `decode_hull_number` | builder, serial, build date, model year from a 12-character HIN |
| `start_naming_session` | the interview, then a gated ranked round (**the only tool that writes**) |
| `vote_on_names` | keeps and kills, mechanism learning, next round of four (**writes**) |
| `reveal_finalists` | the Final 3 with reasons, readback, gates and a family card |
| `get_policies` | proof window, shipping, returns, warranty, the 3-inch rule |

It lives on this worker rather than a service of its own precisely so the price
an assistant quotes comes from the same function as the charge. **Verified:**
four configurations priced identically through `/mcp`, through `/api/price`,
and against production — $19, $39, $44, $23.

The `initialize` response carries the honesty limits as instructions, so they
reach the model and not just the code: price through `price_order`,
registration numbers are legally 3-inch block characters, and *never tell a
customer a name is taken at their marina.*

### The architecture decision, stated plainly

The server has to be reachable over HTTPS by Claude's directory and by
ChatGPT, so it runs on the Worker — JavaScript. The gates' 1,089-name
validation corpus is Python. Both halves are real and neither can be deleted,
so the split is deliberate and narrow:

- **Data** has one definition, in `mcp/gates.py`, emitted to
  `worker/gates-data.js` by `build_gates_js.py`. The rebus tokens, homophones,
  respelling rules, archaic collisions, overuse tiers and font metrics cannot
  drift because there is only one of each. A stale emitted file fails the build.
- **Logic** exists twice, ~150 lines each. That is the real cost, and it is
  paid for by `mcp/test_equivalence.py`, which runs **both implementations over
  all 1,089 bank names plus 27 edge fixtures and compares every field** —
  verdict, dealable, readback, score, every reason string, every width at every
  height, the overuse tier and its note. Not a spot check.
- **The lexicon** is 509 KB gzipped and lives in R2, loaded once per isolate,
  the same proven pattern as the ten fonts.

Two real bugs came straight out of that comparison, neither of which any
amount of reading would have found:

1. **Python rounds half to even; JavaScript rounds half up.** `round(8.45, 1)`
   is `8.4` in Python and `8.5` in JS, so the site and the MCP server quoted
   different widths for "Aloft" in Impact. Both now round half up.
2. **`"%s" % 36.0` is `"36.0"`; JS gives `"36"`.** The two implementations
   were emitting different sentences to customers — *about 36.0" wide* versus
   *about 36" wide*.

### `check_registration_layout` and `decode_hull_number` — one implementation, no harness needed

These two did **not** need the equivalence treatment, because both surfaces are
JavaScript. `worker/decode.js` is the single implementation, and
`engine/shared_js.py` inlines that same file into the order form and both free
tool pages. Not two copies kept in step by a test — the same source in both
places.

Before this, the registration logic lived only as a JS string inside
`engine/validate.py` and the HIN logic only inside `engine/tools.py`, so putting
either on the worker would have created a second copy. Instead:

- `worker/decode.js` — the logic, pure, no DOM, no HTML
- `worker/decode-data.js` — 56 vessel prefixes, 9 postal confusions, Maine's
  format exception, California's unissued letters, 96 MIC codes; generated from
  `engine/content.py` and `engine/tools.py`
- `engine/validate.py` — **deleted.** It was the second copy.
- `engine/tools.py`'s `HIN_JS` — reduced to rendering: read the box, call the
  shared decoder, draw the table.

Messages carry `**bold**` markers rather than HTML, so the page renders
`<strong>` and the MCP server hands markdown to the model from one string.
Returning HTML would have had an assistant reading "`<strong>`" aloud to a
customer; returning plain text would have lost the emphasis the page has always
had.

**Proven before the switch, because the order form is the checkout path.**
`worker/decode.js` was compared against the validator it replaced across **490
inputs** — every vessel prefix in every shape, all nine postal-code
confusions, and the malformed cases. Identical on verdict, corrected spacing
and state. The only wording that changed was Maine's, where the old string was
a hardcoded duplicate of the note in `content.py` and the new one reads the
real thing.

The old `BNS_VALIDATE` name is kept as a thin shim over the shared module, so
the order form's callers were not touched at all. All three surfaces were then
exercised in a real browser.

`verify.py` gates it: the emitted tables must be current, each of the three
pages must carry the shared decoder, and either decoder reappearing anywhere
under `engine/` fails the build.

### Honesty limit, carried into the tool

`check_registration_layout` flags and never refuses. The prefix table is
compiled from secondary sources, states issue sequentially so older hulls carry
retired formats, and this covers tier 1 of the rules only. An order refused by
an incomplete validator is a lost sale; an order flagged for the proof is a
thirty-second check by someone who knows. The tool says so in its own output.

## The ChatGPT submission

`/.well-known/openai-apps-challenge` is live in the worker, served from the
`OPENAI_APPS_TOKEN` **secret** rather than a committed file. The token is a
bearer proof of domain ownership, so it does not belong in a public git
history, and a secret can be set or rotated with one `wrangler secret put` and
no deploy — which matters while a submission is waiting on it. With no secret
set it 404s, which is the honest answer: we cannot prove anything yet.

## The remaining four tags — derived, not hand-tagged

`style_lanes`, `themes`, `boat_types` and `overuse_tier`, in
`mcp/derive_tags.py`. The bank is now complete on all six fields.

**Why these four are derived when `humor_mechanism` was tagged by hand.** The
mechanism had to be per-name because the site's categories are *thematic*, not
mechanical — the pontoon lane holds literal truths, puns and deadpan side by
side, so no rule could read a mechanism off a category.

Lanes are the opposite. The generator page's first step is headed **"Pick a
vibe"**, and the thing it asks you to pick is the category. The categories
*are* the lanes, in the site's own words, chosen by whoever wrote them.
Deriving the lane from the category is not a shortcut around the work — it is
reading the answer off the place where the decision was already made, and it
means a name added to `namegen.py` arrives with its lane already right instead
of waiting for someone to remember to tag it.

Mechanism then refines it: a `sincere` name is in the sincere lane whatever
category it sits in, a deadpan mechanism is deadpan even inside the money lane,
and anything graded `double` joins the dock lane — because that is the lane a
customer picks when he is telling us who is aboard.

| lane | names |
|---|---|
| `pun` | 248 |
| `deadpan` | 232 |
| `absurd` | 189 |
| `dock` | 168 |
| `ironic` | 120 |
| `dark` | 100 |
| `nerd` | 80 |
| `sincere` | 53 |
| `pontoon_dad` | 50 |
| `brag` | 49 |
| `current` | 40 |
| `regional` | 39 |

Themes and boat types are keyword-derived, which keeps working for names nobody
has written yet. 270 names carry no theme and that is correct — "Kevin",
"Beige" and "TBD" are not *about* anything. 873 suit any boat, which is the
right default; `boat_types` is deliberately not a taxonomy of boats, just the
hulls where a name either fits or looks ridiculous.

`overuse_tier` is read from `gates.overuse_gate()`. One judgement, one place,
and a gate fails the build if the bank's copy disagrees.

### Two bugs the audit caught

1. **The `money` theme had no "money" keyword.** "A Boat Is A Hole You Pour
   Money In" was not being tagged as a money name.
2. **It was substring matching.** "Cur_rent_ Affairs" was tagged money via
   *rent*, "Cof_fee_" via *fee*, "_Bill_board" via *bill*. Every pattern is now
   anchored at a word start — but not the end, so `divorc` still reaches
   "divorced".

### Hand overrides

`mcp/tags/overrides.tsv`, applied last, validated against the vocabularies and
counted. **Currently empty**: the rules get every name in the bank right as it
stands. It exists so the first name they get wrong can be fixed in one line
rather than by bending a rule that works — and if it ever fills up, that is a
signal the rules are wrong, not a thing to quietly accumulate.

Gates, each proven against a deliberate break: no name may have an empty lane
(the ranker could never deal it), every value must be in its vocabulary, no
lane may hold fewer than 20 names (you cannot deal a round without repeating),
the bank's `overuse_tier` must match the gate, and a `sincere` name must never
sit in a joke lane.

## The naming engine — interview and ranker

`worker/engine.js`, exposed as the MCP tool `start_naming_session`. This is the
part the gates were built for.

Pure functions of (bank, profile): no model, no randomness beyond an explicit
seed. A round is **reproducible from its session**, which is the only way a
complaint about a round can ever be investigated.

### The interview

Seven questions, one required. Every one exists because it *changes what may be
dealt* — a question that would not change the round is not asked, and each
carries a `why` that a gate enforces.

The consequential one is **"who is usually aboard?"** It sets the ceiling on how
blue a name can be, and it **defaults to clean when nobody says.** Defaulting
the other way puts the cost of the mistake on the customer, and it is his
transom.

### What the ranker refuses

The spec's one hard rule is that it never returns an unfiltered list. A real
round, for a man naming a 22-foot pontoon with his grandkids aboard:

```
bank 1089 -> passed every gate 734 -> dealt 8
set aside: level 176, in_joke 124, fit 46, tier1 9, radio 0
```

- **level** — cruder than who is aboard allows
- **in_joke** — needs a trade the interview has not been told. An in-group
  joke lands on nobody outside the group, so dealing one to a stranger is not
  a risk, it is a wasted slot
- **fit** — will not go on the transom at any height we cut
- **tier1** — one of the names at every ramp, unless he asked for popular ones

Every round reports that breakdown. 1,089 in and 8 out is only defensible if
the other 1,081 can be accounted for.

### Three bugs in the first ranker, all of them invisible in a demo

1. **Alphabetical bias.** Ties were broken by name, so rounds came out *Actual
   In, Airman, Ails Sail, Alder & Oak, Alimony, Amicable, Ask Her* — which
   looks exactly like a list read off the top of a file, because it was. Ties
   now break on a seeded hash, still reproducible.
2. **A round of eight divorce jokes.** The dock lane spans divorce, money and
   marriage — three separate categories, so the category cap never bound.
   Capped by **theme** as well as mechanism and category.
3. **"Mortality Barge" was the top pick for a man with grandkids aboard.** It
   is clean and genuinely deadpan, so the lane hit scored and the `dark` lane
   cost nothing. A loud lane the customer did not ask for is now a penalty.

### Sessions, and the privacy work they forced

`naming_sessions` in D1 is the first thing on this site that stores what
somebody **told** us rather than what they ordered — a trade, a story, who is
aboard. So:

- a random id, no account, nothing that identifies a person
- never joined to an order; there is no column for one
- **purged after 30 days** by the existing cron, because a retention promise
  nothing enforces is not a promise, and a gate checks the purge still exists
- `harvest_optin` defaults to 0

**The privacy policy said "we collect what you typed into the order form…
that is it."** That would have been false the moment a session stored a story
about somebody's father-in-law. It now has a section on the naming assistant,
and a gate fails the build if the old sentence comes back.

### One tool is no longer read-only, and the gate says so by name

`start_naming_session` writes session state. Eight tools remain read-only.
Rather than keep a tidier claim, `verify.py` enforces the exact split: that one
tool may write, the other eight may not, **the only table the whole server may
name is `naming_sessions`**, and none of them may reach an order or a card.

Two bugs in those gates, found by trying to break them:

- the table check lowercased the source before matching uppercase SQL, so it
  never matched `FROM orders` and happily matched the words "from hearing" in a
  tool description. Case is the discriminator: SQL keywords here are uppercase,
  prose is not.
- the first version only counted annotations and would not have noticed a
  second writer.

## The tournament and the reveal

`vote_on_names` and `reveal_finalists`. Round 1 deals eight; after that it is
rounds of **four**, because four is a decision and eight is a shortlist.

**A vote is about the mechanism, not the name.** A customer who kills two
homophone puns has told us something far more useful than which two names he
disliked, and the next round stops offering puns rather than offering two
different ones. The thresholds:

- **two kills with nothing kept** retires a mechanism. One kill is a name he
  did not like; two is the joke itself not landing.
- **one keep protects it** — a mechanism he has liked once is not retired on
  kills alone.
- **two keeps and more keeps than kills** marks it proven, which is what a riff
  brief will later be allowed to write in.

### The reveal, and the one rule that governs it

The rationale is written **from the session profile and nothing else.** Every
clause is either a fixed phrase or a quotation of something the customer
actually typed. There is no branch that invents a fact about his boat, his
family or his job — a reveal that says "perfect for weekends with the
grandkids" to a man who never mentioned grandchildren is worse than no
rationale, because it tells him the whole thing was generated.

A real one, for a 19-foot bass boat:

> You asked for pun, and this is that; it is an in-joke for anybody who fishes,
> so most people will not get it — which is part of the point; it will cut at
> 6" tall on what you have.

Plus the readback to say aloud, the gates in plain words ("Clear on the radio |
Fits at 6" tall | Not one we see often"), a deep link into the real order form
with the name already in it, and a **card to send the family** to vote on.

### Four bugs found by running it, not reading it

1. **"Limit Out" was explained as "an in-joke for *I run a small HVAC
   company*".** It is angler jargon. The `pj` mechanism deliberately covers a
   trade, a region and a cohort, and the reveal assumed it was always the
   trade. Now `inGroupEvidence()` decides *which* group and what unlocks it:
   a fishing in-joke by the boat, a regional one by the port, a trade one by
   the job — and none of them by any of the others.
2. **"Three names for the a 22 foot pontoon."** A leading article has to come
   off before the heading puts one in front of it.
3. **All three finalists' reasons read identically**, because every clause came
   from the shared profile. Each reason now ends with one fact true of that
   name alone — the bank's own note where it has one ("anagram of Captain"),
   otherwise the spelling burden, the visual-only joke, or the height it cuts
   at.
4. **"it is an in-joke for X; an in-joke."** The mechanism clause duplicated
   the clause above it.

Also capped at three clauses. The first version ran to five semicolons, which
nobody reads as a reason — they read it as output.

## Riff briefs and the performance ledger

The bank is 1,089 names somebody judged funny once, in a room, in advance.
That is a hypothesis, not evidence. The ledger is the evidence.

### What "proven" means

`ledger` holds `(kind, lane, key, exposures, keeps, kills)` and nothing else —
`kind` is `mech` or `name`, `lane` is the lane the **customer asked for**,
because the question is "does this joke land on people who asked for deadpan",
not "which lane is this name filed in". Every session also files under `any`,
so a cold lane always has a fallback.

A mechanism is proven for a lane once it has **≥30 exposures** in that lane and
a **keep-rate in the top half of the lane**. Half the field is proven by
construction, which is the point: proven is relative to what else we have, not
an absolute bar nobody clears. One extra floor: a mechanism with thirty
exposures and zero keeps is not "top half of a field of one", it is a mechanism
nobody has ever liked, so a keep-rate of zero disqualifies it outright.

### Why there are two sets of counters

A lifetime keep-rate barely moves. A mechanism that landed all year and stopped
landing in October still reads as proven in December — which is the exact
failure the spec names. So the `w_` columns are the window the decision is made
on, and the monthly review **halves them after it snapshots**: an exponential
decay with a one-month half-life. The lifetime columns survive only so the
review can show the all-time figure beside the current one.

### It holds nothing personal, and that is load-bearing

The ledger is the only naming table that outlives the 30-day session purge, and
it is allowed to because a row is a lane, a mechanism and three integers. No
session id, no free text, nothing a customer typed. **Riff text never reaches
it**: a riff is built out of a man's wife, his dog or his hometown, so a riff
accrues to its mechanism's counters and its own words stay in the session row
that gets deleted. `verify.py` fails the build on a ledger column named
anything like a person, on a `DELETE FROM ledger`, and on `engine.js` losing
the line that keeps riff names out.

Its SQL lives in `worker/index.js`, not `worker/mcp.js`, so that the gate on
the MCP server can keep saying **the only table it names is
`naming_sessions`** — absolutely, with no list of exceptions. That gate is what
stands between an assistant and the orders table.

### The brief

The host model never free-associates. Before it riffs it gets:

- **his own words**, verbatim — the boat, the lake, the job, the story
- **the ceiling**, and what the line actually is ("dock humor is fine, jokes at
  his wife's expense are not")
- **the mechanisms that have been landing in his lane**, with their real
  keep-rates — and *only* proven ones
- **one slot** for something unproven, named as exploration, because that is
  how the ledger ever learns a new mechanism
- **3–5 exemplars** of those mechanisms, and whether they were chosen by
  keep-rate or, before there is any keep data, as the cleanest instances we
  have. A brief claiming "these are the highest keep-rate names" when nothing
  has ever been kept is a lie the host will write into a rationale, so the
  brief says which it is and `verify.py` fails if that sentence disappears.
- **the house register** — deadpan, double meanings left unexplained, the
  faux-official furniture, short enough to say once on a radio
- **a banned list** — mechanisms he has killed, meme-speak, Tier-1 names

The killed-mechanism subtraction is the whole point of the tournament: the
ledger knows what lands on strangers, he knows what lands on him, and he wins.

### `submit_riff_candidates`

The only path by which a non-bank name enters a round. Every candidate gets the
radio gate, the width against his transom, the overuse check, a crude screen
against the ceiling, and a **novelty check against all 1,089 bank names** —
a near-copy is a copy, not creativity. Failures are dropped with reasons for
the log, never shown to the customer with an apology.

Riffs then compete in the same pool as bank names with a bonus, because they
are built out of material no bank name can have. They do **not** get a free
slot: a weak riff still loses, which is the only thing that keeps the slots
worth having. Two hard caps survive every relaxation pass — riffs are at most
**a third** of a round, and an unproven mechanism takes at most **one** slot.

A riff's `humor_level` is recorded as `unrated`, not `clean` and not the
session's ceiling. Both would be claims we cannot make about a name a model
wrote one second ago that nobody has read.

**What this cannot do, said plainly:** a word list cannot catch a double
meaning — that is what a double meaning is. The crude screen is a floor for
the overt cases. The real protection for a man with his grandchildren aboard is
that the brief states the ceiling, riffs are capped at a third of a round, and
every riff still has to beat names a human read before they were banked.

### The monthly review

`/api/mech-review?k=…` behind the owner key. **Read-only by default** — it
shows what the review would say without snapshotting or decaying anything,
because the useful version of this is a page Ryan can open whenever he likes
and one that quietly halves the ledger on every refresh is a trap.
`&commit=1` records the month's snapshot and applies the decay; the hourly cron
does the same on the first of the month, guarded on the hour as well as the day
— without that guard it would halve the window twenty-four times in a day.

### What the first live session showed

Ran it against production as a retired Deere man with his wife and dog aboard.
The riff pipeline worked first time — two of six candidates survived, each of
the four drops a different gate, and "Deere Diary" won a slot in round two as
`source: riff`. Five things did not, and none of them were visible in a test:

1. **The brief claimed its exemplars were "chosen by keep-rate in real
   sessions" while every rate in the table was zero.** Exposures accrue the
   moment a round is dealt, and the check asked whether any name had a *row*
   rather than whether any name had ever been *kept*. Forty exposures and no
   keeps is a denominator, not a ranking signal — and this is the exact
   dishonesty the gate on that sentence exists to prevent, so the gate was
   watching the wrong variable.
2. **A cold ledger produced a brief with zero exemplars**, because the fallback
   read the ledger's exploring list and a cold ledger's is empty. A brief with
   nothing in it is a model free-associating.
3. **"Mayday, mayday, this is Loading...."** — four dots, on the one screen the
   whole session builds towards.
4. **"Three names for the 22 foot pontoon" over a card with two names on it.**
   The card a man forwards to his wife should not miscount itself.
5. **The brief told the host "children or his wife are aboard" when nobody had
   said who was aboard at all.** Clean is also the *default*. A fact handed to
   the one component whose entire job is writing rationales from facts.

Then a warm ledger was seeded into a local D1 — production will be cold for
months and the warm path is the whole feature — and that found the sixth: the
fixture customer killed deadpan, leaving exactly **one** proven mechanism in
his lane, and round two came back as "Boat", "Pending", "Loading…" and one
riff. Three literal-truth jokes. The exploration cap was doing it: with one
proven mechanism left, every slot that was not exploration had to be that
mechanism. **The cap now binds only once there are at least two proven
mechanisms to build a round out of**, and his kills come out of the proven set
before the cap sees it.

### Nine deliberate breaks, and the three that got away

Every rule above was tested by removing it:

| Break | Caught by |
|---|---|
| exploration cap deleted | a round of eight dealt 4 unproven mechanisms |
| riff third-of-a-round cap deleted | a round of **four** dealt 2 riffs |
| brief stops excluding killed mechanisms | the Round 2 brief offered `dp` back |
| zero-keep floor removed | 40 exposures / 0 keeps called proven |
| riff text filed in the permanent ledger | the privacy test |
| novelty gate skipped | a word-for-word bank name passed as invention |
| top-half median replaced with a pass-everything bar | bottom-half keep-rates called proven |
| exposure data read as keep data | exemplars claimed as keep-rate-chosen with every rate at zero |
| cold-ledger exemplar fallback removed | a brief with no exemplars at all |
| exploration cap binding on one proven mechanism | a round of four, three of them the same joke |

Three of these broke cleanly and the test said nothing, which is the only
interesting part of the exercise:

- **The riff cap.** A round of eight did not catch it. All six riffs share the
  category `riff`, so the diversity cap held them to two whether the riff cap
  existed or not. A third of four is one, so four is where the two caps
  disagree — and that is the case that fails.
- **The cold-ledger fallback.** The "break" replaced the assignment and left
  the guard below it intact, so the feature still worked. Breaking a line is
  not the same as removing a feature.
- **The exploration cap.** The test asked for two distinct mechanisms in a
  round of four and passed with the cap left in — because three literal-truth
  names plus one exploration slot *is* two distinct mechanisms, and is also the
  bug. What matters is dominance: no single joke may take three of the four.

A test that passes with the feature deleted is not a test.

One verify gate was weak the same way: `if _w not in _mcp` let the writer tool
be renamed to `submit_riffs` and still pass, because the old name appeared in
another tool's description. It now checks the **declared** tool names. A gate
that reads prose is not a gate.

## What the smoke test found

`mcp/live_check.py` runs the server against production. It failed on two of
its own assertions the first time, and both assertions were right.

### price_order quoted $19 for every product

`BASE` in `worker/index.js` is keyed by the labels the **website's form**
posts — `"Registration numbers"`, `"Boat name"`, `"Both"`. The MCP tool takes
`numbers` / `name` / `both` and passed those straight into `priceOf`, which
matched nothing and fell through its `?? 19` default. So an assistant quoted
**$19 for a $29 name and $19 for a $44 bundle**, silently, on every quote at
three inches. `get_products` advertises a *third* set of names — the catalog
ids — so a model reading the catalog and then pricing what it read was
guaranteed to miss.

The spec's hardest rule is one pricing source, and the gate for it checked
only that `priceOf` was *called*. It always was. **Calling the one pricing
function with a vocabulary it does not speak is exactly as wrong as keeping a
second copy of the price, and it fails more quietly.** There is now one alias
table beside the prices themselves, and the gate resolves every value of the
tool's own enum — and every product id in `catalog.json` — against the real
table.

Quotes price strictly and error on an unknown product. The order path stays
lenient, because this repo's standing judgement is that losing a real order to
a stale cached page is worse, and that row carries a `mismatch` flag.

One level up, the same class: the catalog derives every price from one dict in
`content.py`, the worker hardcodes three labels, and the gate holding them
together checked only the `19`. Raising `name_from` would have left the site
advertising the new figure while the card charged the old one. All three are
now checked, in both directions.

### The server never validated arguments

`dispatch()` handed `params.arguments` to the tool and never read the schema.
A call to `check_registration_layout` with the parameter misnamed — `text`
instead of `number` — was accepted, read nothing, and returned:

```json
{ "number": "", "verdict": "ok", "height_is_legal": true,
  "note": "Reads as a normal state format." }
```

A model would tell a customer their registration layout is fine having checked
nothing at all. Every schema already said
`required: [...], additionalProperties: false`; nothing read it.

Clients are meant to validate locally, and the ones that do were never the
problem. **The call that arrives with a hallucinated parameter name is by
definition from a client that did not** — which is exactly when the server has
to be the one that checks. Returned as a tool error rather than a `-32602`, so
the model can read it and fix its own call, and the message says plainly that
nothing was checked.

Removing the one line in `dispatch()` that calls the validator leaves every
unit test for `validate()` passing. That one needed a gate, not a test.

### Two stale claims and an `undefined`

`initialize`'s instructions — the first thing every client reads — said
"Every tool here is read-only" for as long as three tools have written. The
plain-GET response said the same. And `+/-undefined%` reached customer-facing
output from `fitGate`'s no-name path, which carries no `error_pct`.

### The ledger was learning from me

Two verification runs against production left it reading:

```
deadpan  hp   exp=2   keeps=2   rate=1.0     <- a riff a script kept twice
deadpan  dp   exp=4   keeps=0   kills=4      <- a script killing a slice
any      lt   exp=23  keeps=2                <- seven short of PROVEN
```

Seven more exposures and the brief would have started telling a host model
that literal-truth jokes are proven in the deadpan lane, on evidence a `for`
loop produced — the fabricated-evidence failure the warm fixture shouts about
in its header, arriving through the back door.

So **`live_check.py`'s writing half refuses to run unless the ledger is
empty**, and wipes it afterwards. The invariant is the point: it only ever
runs against a ledger it is allowed to destroy, and it proves it is allowed by
requiring there to be nothing there. The first real customer makes the ledger
non-empty for good, and from then on the script does only its read-only half —
which is the right answer, because by then the full flow belongs on local D1
with the warm fixture.

## Next

1. The Design Studio widget (spec §5/§6)
2. The social-harvest queue (spec §10), which is opt-in and owner-approved and
   should be built last, carefully
3. `backronym` still has zero bank examples — either fill the gap with ~20 new
   names or drop it from the taxonomy

## Commands

```
node mcp/extract_bank.mjs    # generator -> data/_bank_js.json
python3 mcp/build_bank.py    # + funny names + tags -> data/name_bank.json
python3 mcp/apply_tags.py    # tag coverage report on its own
python3 engine/build.py      # writes public/catalog.json
node mcp/test_engine.mjs     # the ranker, the brief, the ledger
python3 verify.py            # every gate
```

To exercise the **warm** ledger path against a real worker — production's
ledger will be cold for months, and the warm path is the whole feature:

```
npx wrangler d1 execute boatnumbershop --local --file=schema.sql
npx wrangler d1 execute boatnumbershop --local --file=mcp/fixtures/warm-ledger.local.sql
npx wrangler r2 object put nmb-fonts/lexicon.txt.gz --file=mcp/data/lexicon.txt.gz --local
npx wrangler dev --port 8798
```

Every number in that fixture is invented, which is why it is `--local` only and
says so twice. Loading it into the real database would have the brief telling
customers that invented evidence is "keep-rate in real sessions".
