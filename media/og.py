#!/usr/bin/env python3
"""Open Graph cards: a line of vinyl, cut onto a transom.

    python3 media/og.py              # render everything into public/assets/og

The format is lifted from a Buc-ee's billboard, and it works here for a reason
that has nothing to do with billboards: we SELL lettering, so a funny line set
in big vinyl IS the product demo. Someone screenshots the joke and posts it to
a boating group, and the thing they have shared is a picture of our work with
the domain cut into the corner.

Every card is therefore the same object - a transom with something on it - and
the only variable is what it says. No photographs, nothing generated, nothing
that can be mistaken for a particular person's boat.

1200x630 because that is what Facebook crops to. The safe area is roughly the
middle 1200x600; nothing that matters goes in the outer 40px.
"""
import pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ogtype import fit, path_for, measure            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "assets" / "og"
BLOCK = "ArchivoBlack-Regular.ttf"
SCRIPT = "Pacifico-Regular.ttf"

W, H = 1200, 630
NAVY, SEA, INK = "#0e3a52", "#5fc4f5", "#12242e"

# Hull colours. A card is a transom, so the background is a hull and the
# lettering is the vinyl on it - which means the pair has to pass the same
# contrast test we sell on.
HULLS = {
    "navy":   ("#0d3348", "#07202f", "#ffffff"),
    "black":  ("#1b1f23", "#0d1013", "#ffffff"),
    "white":  ("#eef2f4", "#d7e0e6", "#16222b"),
    "red":    ("#7d1420", "#4f0b14", "#ffffff"),
    "green":  ("#14402c", "#0a2619", "#ffffff"),
    "teal":   ("#0f4a52", "#072e34", "#ffffff"),
}


def mark(x, y, size, ink, acc):
    """The brand mark, drawn without its navy plate.

    The plate would disappear on a navy hull and fight a red one, so the mark
    is drawn in the card's own ink and accent instead - the same two colours
    the URL beside it already uses. Paths are the 32x32 originals from
    build.LOGO_MARK, scaled in place.
    """
    k = size / 32.0
    return ('<g transform="translate(%g,%g) scale(%g)" opacity=".85">'
            '<path d="M12.8 5 9.8 27M21.8 5 18.8 27" stroke="%s" '
            'stroke-width="2.9" stroke-linecap="round" fill="none"/>'
            '<path d="M4 12.2c4 0 4 -2.2 8 0c4 0 4 2.2 8 0c4 0 4 -2.2 8 0" '
            'stroke="%s" stroke-width="2.8" fill="none" stroke-linecap="round"/>'
            '<path d="M4 20.4c4 0 4 -2.2 8 0c4 0 4 2.2 8 0c4 0 4 -2.2 8 0" '
            'stroke="%s" stroke-width="2.8" fill="none" stroke-linecap="round"/>'
            '</g>' % (x, y, k, ink, acc, acc))


def card(main, kicker="", script=False, hull="navy", accent=None):
    """One card. `main` is the shout; `kicker` is the small line under it."""
    top, bottom, ink = HULLS.get(hull, HULLS["navy"])
    acc = accent or (SEA if ink == "#ffffff" else NAVY)
    ttf = SCRIPT if script else BLOCK
    track = 0 if script else 1.5

    # Up to three lines, broken on the pipe so the copy controls the rhythm.
    lines = [l.strip() for l in main.split("|") if l.strip()]
    box_w = W - 180
    cap = {1: 128, 2: 104, 3: 82}.get(len(lines), 76)
    size = min(fit(l, ttf, box_w, cap, track)[0] for l in lines)
    lh = size * (1.16 if script else 1.04)

    block_h = lh * len(lines)
    cy = H / 2 - (34 if kicker else 8)
    y0 = cy - block_h / 2 + size * (0.74 if not script else 0.70)

    glyphs = []
    for i, line in enumerate(lines):
        w = measure(line, ttf, size) + track * max(0, len(line) - 1)
        d, _ = path_for(line, ttf, size, (W - w) / 2, y0 + i * lh, track)
        glyphs.append('<path d="%s" fill="%s"/>' % (d, ink))

    sub = ""
    if kicker:
        ks, kw = fit(kicker.upper(), BLOCK, box_w, 30, 2.4)
        kd, _ = path_for(kicker.upper(), BLOCK, ks, (W - kw) / 2,
                         cy + block_h / 2 + 46, 2.4)
        sub = '<path d="%s" fill="%s" opacity=".92"/>' % (kd, acc)

    # brand lockup, bottom centre: mark + URL, centred as one group so the
    # pair reads as a maker's mark rather than two things that happen to be
    # near each other.
    URL = "NUMBERMYBOAT.COM"
    bsz, btrack, msz, gap = 26, 2.2, 46, 14
    bw = measure(URL, BLOCK, bsz) + btrack * (len(URL) - 1)
    gw = msz + gap + bw
    gx = (W - gw) / 2
    base = H - 46
    bd, _ = path_for(URL, BLOCK, bsz, gx + msz + gap, base, btrack)
    lock = (mark(gx, base - bsz * 0.72 / 2 - msz / 2, msz, ink, acc)
            + '<path d="%s" fill="%s" opacity=".85"/>' % (bd, ink))

    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
            '</linearGradient></defs>'
            '<rect width="%d" height="%d" fill="url(#g)"/>'
            # the waterline: a thin band of light along the bottom, the way a
            # transom catches reflection off the water
            '<rect x="0" y="%d" width="%d" height="%d" fill="%s" opacity=".10"/>'
            '<rect x="0" y="%d" width="%d" height="3" fill="%s" opacity=".55"/>'
            '%s%s%s'
            '</svg>'
            % (W, H, W, H, top, bottom, W, H,
               H - 96, W, 96, acc, H - 96, W, acc,
               "".join(glyphs), sub, lock))


def render(name, **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / (name + ".svg")
    svg.write_text(card(**kw), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                    str(svg), "-o", str(OUT / (name + ".png"))], check=True)
    svg.unlink()
    return OUT / (name + ".png")


def slug_for(path):
    """A filename per page. "/" is home; everything else is its path."""
    s = path.strip("/").replace("/", "-")
    return s or "home"


def build_all(verbose=True):
    """Render a card for every page the site publishes."""
    sys.path.insert(0, str(ROOT / "engine"))
    sys.path.insert(0, str(ROOT / "media"))
    from og_lines import LINES, state_card
    from content import STATES

    POSTAL = {"iowa": "IA", "florida": "FL", "michigan": "MI", "new-york": "NY",
              "california": "CA", "south-carolina": "SC", "wisconsin": "WI",
              "minnesota": "MN", "texas": "TX", "pennsylvania": "PA",
              "north-carolina": "NC", "georgia": "GA", "virginia": "VA",
              "ohio": "OH", "illinois": "IL", "missouri": "MO",
              "washington": "WA", "louisiana": "LA", "alabama": "AL",
              "tennessee": "TN", "indiana": "IN"}

    cards = dict(LINES)
    for i, st in enumerate(STATES):
        cards["/registration-numbers/%s/" % st["slug"]] = state_card(
            i, st["name"], st["ab"], POSTAL[st["slug"]])

    made = {}
    for path, spec in sorted(cards.items()):
        name = slug_for(path)
        render(name, **spec)
        made[path] = "/assets/og/%s.png" % name
    if verbose:
        total = sum(f.stat().st_size for f in OUT.glob("*.png"))
        print("   og: %d cards -> %s (%.1f MB)"
              % (len(made), OUT, total / 1e6))
    return made


if __name__ == "__main__":
    build_all()
