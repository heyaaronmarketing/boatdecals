# Imagery

Generated illustrative product shots + their social crops.

```bash
python3 media/gen.py --list          # the shot list
python3 media/gen.py --batch         # render anything missing
python3 media/gen.py --only AL-03 --force
python3 media/social.py              # derive 4 social crops per master
```

## Read first

**[CAPTIONS.md](CAPTIONS.md) — the captioning rule.** These are illustrations,
never a named customer's boat. Breaking that turns an illustration into
fabricated social proof.

## Model

`gpt-image-2` via the OpenAI key at `~/.config/openai/key`. ~28s and roughly
$0.19 a render at these sizes.

**The intended model is Nano Banana Pro** (`~/.claude/skills/tradephoto/scripts/nano_banana.py`),
which holds reference-image consistency across a set far better — the same
lettering, hull and light on every shot. It is unavailable right now: the
Google AI Studio key returns `RESOURCE_EXHAUSTED`. **Top up at
https://ai.studio/projects and switch back** for any set where consistency
between shots matters.

## What makes these not look AI

Three things, all in `gen.py`:

1. **`REAL`** — the register. *"Casual smartphone snapshot taken by the boat
   owner, not a professional photograph."* Briefing it as commercial
   photography is precisely what produces the plastic look.
2. **`UPRIGHT`** — registration lettering must be plain vertical block. The
   first render leaned slightly: wrong under 33 CFR 173.27 and the kind of
   detail a boat owner spots instantly. Script transom names are exempt.
3. **`NEG`** — no faces, no logos, no stray text, **no golden hour**. Every
   model reaches for warm low sun, so it now reads as AI on sight.

Never add: `4K`, `8K`, `ultra-detailed`, `perfect lighting`, `masterpiece`.

## Shot set

`AL-*` — applied lettering, the gallery substitute. Covers **both contrast
directions on purpose** (light vinyl on dark hulls, dark on light), because
that is the federal rule the whole site teaches and the imagery has to
demonstrate it. Also covers the four awkward substrates the site makes claims
about: bare aluminium, PWC plastic, kayak polyethylene, pontoon rail.

Still to shoot: `HT-*` how-to steps (the seven in
`/guides/how-to-apply-boat-lettering/` — shoot that guide literally),
`VT-*` one hero per boat-type page, `AC-*` action/lifestyle for social only.
