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

## Models — pick by whether the set needs to match

| Set | Model | Why |
|---|---|---|
| `AL-*` standalone shots | `gpt-image-2` (`media/gen.py`) | Each frame is independent, so consistency doesn't matter |
| `HT-*` the how-to sequence | **Nano Banana Pro** (`~/.claude/skills/tradephoto/scripts/nano_banana.py --ref`) | Seven frames of the *same* boat — only this model holds it |

The reference image is what does it:

```bash
python3 ~/.claude/skills/tradephoto/scripts/nano_banana.py \
  --batch media/howto-shots.json --outdir media/shots --ref media/shots/AL-01.jpg
```

Same hull, same trailer, same gravel, same overcast sky in all seven. `gpt-image-2`
cannot do that.

⚠️ **The reference leaks more than you want.** `AL-01` has finished lettering on
it, and the model copied that into steps 1, 3 and 5 — producing a how-to where
the job is already done in the first frame. Those needed an explicit
*"the hull is completely BARE — ignore any lettering in the reference image"*.
Then step 3 rendered the hinged sheet with **mirrored** text, which reads as an
AI glitch, and needed *"blank white paper backing, no printing of any kind"*.

Budget ~3 passes on any sequence shot. Check continuity across the set, not
just each frame on its own.

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

`HT-*` — the seven install steps, one boat, in order. Nano Banana Pro with
`--ref`; see the models table above.

`GD-*` — guide images, where a photograph does work the prose cannot: where the
numbers go on a whole hull, the ghost outline old lettering leaves behind, a
tape measure against 3-inch characters.

`AC-*` — action and atmosphere. **Social only, never used as proof.**

### Shots that were dropped

`GD-3` (cast vs calendared vinyl) was cut after two attempts. The model renders
"corners curled up half an inch" as a crumpled rubber blob, which is not what
shrink-back looks like — a misleading photo on a page that teaches material
differences is worse than no photo. The guide's table already makes the point.

Some things an image model cannot do. Check whether the picture is *true*
before checking whether it is pretty.
