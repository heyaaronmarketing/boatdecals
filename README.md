# Boat Number Shop — boatnumbershop.com

Custom boat registration numbers, names and marine vinyl decals. National
e-commerce, not a local lead-gen site: the conversion element is an **order
configurator**, not a tap-to-call.

**Live:** https://boatdecals.aironz.workers.dev (Worker `boatdecals`, CF account `681da9da…`)

## Build & deploy

```bash
python3 engine/build.py          # regenerates public/ (60 pages)
npx wrangler deploy              # needs CLOUDFLARE_ACCOUNT_ID + NODE_EXTRA_CA_CERTS
```

`public/` is committed so Cloudflare Workers Builds can deploy without a Python
step. **Always rebuild before committing** — editing `public/` by hand gets
overwritten.

## Layout

| Path | What |
|---|---|
| `engine/content.py` | All page data: products, states, boat types, tools, guides, pricing. Search volumes recorded inline (DataForSEO, 2026-10-22). |
| `engine/build.py` | Static generator + all long-form body copy. |
| `engine/order.py` | The order configurator form + client price JS. |
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

## Bindings & secrets

- `DB` → D1 `boatnumbershop` (`43724d47-…`), schema in `schema.sql`
- `RESEND_API_KEY`, `ORDER_TO` → set ✅
- `ORDER_FROM` → currently `onboarding@resend.dev`. **Verify boatnumbershop.com
  in Resend and switch this to `orders@boatnumbershop.com` before launch.**

## Before launch

See the "Before this takes a real order" checklist in `STRATEGY.md`.
