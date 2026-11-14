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


PHOTO = ROOT / "public" / "assets" / "img"


def _b64(name):
    """Inline a JPEG so rsvg does not have to resolve a relative href."""
    import base64
    f = PHOTO / (name + "-1400.jpg")
    if not f.exists():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode()


def photo_card(photo, head, sub, badge_top="$28", badge_bot="A PAIR",
               side="left"):
    """Concept 1: the lettering on a hull, with the offer over it.

    A text-only card says what we sell; a card with the vinyl ON something
    shows it, which is the question a buyer actually has. The photo is one of
    our own product shots - illustrative, like everywhere else on the site -
    and the gradient is heavy enough that the type never fights it.
    """
    img = _b64(photo)
    if img is None:
        return None
    # headline column on one side, photo breathing on the other
    tx, grad_x1, grad_x2 = (72, "0", "1") if side == "left" else (W - 72, "1", "0")
    anchor = "start" if side == "left" else "end"

    lines = [l.strip() for l in head.split("|") if l.strip()]
    col_w = 620
    size = min(fit(l, BLOCK, col_w, 92, 1.2)[0] for l in lines)
    lh = size * 1.06
    y0 = H / 2 - (lh * len(lines)) / 2 - 18 + size * 0.74
    glyphs = []
    for i, line in enumerate(lines):
        w = measure(line, BLOCK, size) + 1.2 * max(0, len(line) - 1)
        x = tx if anchor == "start" else tx - w
        d, _ = path_for(line, BLOCK, size, x, y0 + i * lh, 1.2)
        glyphs.append('<path d="%s" fill="#ffffff"/>' % d)

    ss, sw = fit(sub, BLOCK, col_w, 34, 1.6)
    sx = tx if anchor == "start" else tx - sw
    sd, _ = path_for(sub, BLOCK, ss, sx, y0 + lh * (len(lines) - 1) + 58, 1.6)

    # price badge, opposite side, clear of the headline column
    bx = W - 190 if side == "left" else 190
    by = H / 2 - 40
    bt_s, bt_w = fit(badge_top, BLOCK, 190, 96, 0)
    bb_s, bb_w = fit(badge_bot, BLOCK, 196, 25, 1.8)
    btd, _ = path_for(badge_top, BLOCK, bt_s, bx - bt_w / 2, by + bt_s * 0.30, 0)
    bbd, _ = path_for(badge_bot, BLOCK, bb_s, bx - bb_w / 2, by + 74, 1.8)

    URL = "NUMBERMYBOAT.COM"
    bw = measure(URL, BLOCK, 24) + 2.2 * (len(URL) - 1)
    gw = 40 + 12 + bw
    gx = (W - gw) / 2
    ud, _ = path_for(URL, BLOCK, 24, gx + 52, H - 40, 2.2)

    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">'
            '<defs><linearGradient id="v" x1="%s" y1="0" x2="%s" y2="0">'
            '<stop offset="0" stop-color="#0a2a3d" stop-opacity=".93"/>'
            '<stop offset=".42" stop-color="#0a2a3d" stop-opacity=".74"/>'
            '<stop offset=".70" stop-color="#0a2a3d" stop-opacity=".16"/>'
            '<stop offset="1" stop-color="#0a2a3d" stop-opacity="0"/>'
            '</linearGradient></defs>'
            '<image href="%s" x="0" y="0" width="%d" height="%d" '
            'preserveAspectRatio="xMidYMid slice"/>'
            '<rect width="%d" height="%d" fill="url(#v)"/>'
            '%s<path d="%s" fill="#5fc4f5"/>'
            '<circle cx="%g" cy="%g" r="104" fill="#ffc72c"/>'
            '<path d="%s" fill="#0e3a52"/><path d="%s" fill="#0e3a52"/>'
            '<rect x="0" y="%d" width="%d" height="78" fill="#061c2a" opacity=".82"/>'
            '%s<path d="%s" fill="#ffffff" opacity=".92"/>'
            '</svg>'
            % (W, H, W, H, grad_x1, grad_x2, img, W, H, W, H,
               "".join(glyphs), sd, bx, by + 6, btd, bbd,
               H - 78, W, mark(gx, H - 72, 40, "#ffffff", "#5fc4f5"), ud))


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


# Must match build.OG_VERSION. Facebook caches by image URL, so a redesign
# ships under a new filename and the old one stays on disk - previously shared
# links keep rendering the card they were scraped with.
VERSION = "v2"


def slug_for(path):
    """A filename per page. "/" is home; everything else is its path."""
    s = path.strip("/").replace("/", "-")
    return (s or "home") + "-" + VERSION


def build_all(verbose=True):
    """Render a card for every page the site publishes."""
    sys.path.insert(0, str(ROOT / "engine"))
    sys.path.insert(0, str(ROOT / "media"))
    from og_lines import (LINES, state_card, photo_spec, has_photo,
                          register_states as og_lines_register)
    from content import STATES
    og_lines_register(STATES)

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

    PHOTOS = {p: photo_spec(p) for p in cards
              if photo_spec(p) is not None}

    made = {}
    for path, spec in sorted(cards.items()):
        name = slug_for(path)
        ph = PHOTOS.get(path)
        svg = None
        if ph:
            svg = photo_card(ph[0], ph[1], ph[2], ph[3], ph[4])
        if svg is None:
            render(name, **spec)
            made[path] = "/assets/og/%s.png" % name
        else:
            # A photograph in a PNG is 600-870KB; the same card as a quality
            # JPEG is well under 200. Facebook is happy with either, so long
            # as og:image:type agrees - which has_photo() keeps in step.
            OUT.mkdir(parents=True, exist_ok=True)
            f = OUT / (name + ".svg")
            tmp = OUT / (name + ".tmp.png")
            f.write_text(svg, encoding="utf-8")
            subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H),
                            str(f), "-o", str(tmp)], check=True)
            subprocess.run(["sips", "-s", "format", "jpeg", "-s",
                            "formatOptions", "86", str(tmp),
                            "--out", str(OUT / (name + ".jpg"))],
                           check=True, capture_output=True)
            f.unlink(); tmp.unlink()
            made[path] = "/assets/og/%s.jpg" % name
    if verbose:
        total = sum(f.stat().st_size for f in OUT.glob("*.png"))
        print("   og: %d cards -> %s (%.1f MB)"
              % (len(made), OUT, total / 1e6))
    return made


if __name__ == "__main__":
    build_all()
