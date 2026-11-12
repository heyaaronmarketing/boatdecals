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

## Next

1. **Tag the bank.** Every name needs `humor_mechanism`, `humor_level`,
   `style_lanes`, `boat_types`, `themes`, `overuse_tier`. Spec §2 and §4b:
   offline task, human-spot-checked, no runtime LLM guessing. **Nothing in the
   engine can be built on an untagged bank** — all 1,089 are currently
   untagged, and the gates deal only tagged names.
2. The deterministic gates (radio, fit, overuse, photo, dedupe) — pure
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
python3 mcp/build_bank.py    # + funny names -> data/name_bank.json
python3 engine/build.py      # writes public/catalog.json
python3 verify.py            # gates, including catalog/worker drift
```
