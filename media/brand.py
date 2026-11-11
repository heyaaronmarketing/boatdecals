#!/usr/bin/env python3
"""Brand assets, generated from the header logo itself.

WHY THIS IS GENERATED AND NOT DRAWN BY HAND. The logo Ryan uploads to Google
Business, Facebook and forty citation sites has to be the logo on the site. A
hand-made copy drifts the first time the header changes and then the listings
quietly disagree with the website for years. So this imports LOGO_MARK from
engine/build.py - the exact string the header renders - and sets the wordmark
in the exact TTF the pages load. There is one source for the logo.

Two square variants exist on purpose:

  icon/     the mark as designed, rounded tile, transparent around it. For
            anywhere it sits on a white page - directory listings, invoices,
            a favicon.
  profile/  full-bleed navy, artwork inset to 86%. Social platforms crop
            avatars to a CIRCLE. Feed a rounded tile to a circular crop and
            the corners get sliced off; a full-bleed square crops cleanly and
            the inset keeps the waves clear of the curve.

Run:  python3 media/brand.py
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

from build import LOGO_MARK  # noqa: E402  the header's own mark

OUT = ROOT / "brand"
FONT = ROOT / "media" / "fonts" / "ArchivoBlack-Regular.ttf"

NAVY = "#0e3a52"
NAVY2 = "#1b6382"
SKY = "#5fc4f5"
WHITE = "#ffffff"

NAME = "NumberMyBoat"
SUFFIX = ".com"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("FAILED %s\n%s" % (" ".join(map(str, cmd)), r.stderr))
    return r.stdout


_TT = None


def _font():
    global _TT
    if _TT is None:
        _TT = TTFont(FONT)
    return _TT


def wordmark(text, split_at, size=100):
    """`text` as glyph outlines, in two colourable halves.

    The header sets this as live text in Archivo Black. A PNG for a directory
    cannot, so the letters become paths from the same TTF the site loads.

    NOT opentype.js, which the worker uses for the order previews: fed this
    particular file it emits NaN coordinates partway through the second glyph,
    and every letter after that silently vanishes. fontTools draws it cleanly.
    (The copy in R2 that /api/outline serves is fine - checked - so this is a
    quirk of the local file, not a problem with the proofs.)

    No kerning: measured against a kerned layout of this exact string, the
    difference is 1.7 units in 1105, or 0.15%. Not worth a shaping engine.

    `split_at` is a character index; the glyphs before it are one colour and
    the rest the other.
    """
    f = _font()
    upm = f["head"].unitsPerEm
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    k = size / upm

    def cap_of(ch):
        pen = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(pen)
        return pen.bounds[3] * k          # top of a capital, in screen units

    x, head, tail = 0.0, [], []
    for i, ch in enumerate(text):
        gn = cmap.get(ord(ch))
        if gn is None:
            continue
        pen = SVGPathPen(gs)
        gs[gn].draw(pen)
        d = pen.getCommands()
        if d:
            # Font space is y-up with the baseline at 0; SVG is y-down. The
            # negative y scale is the flip, so the baseline lands on y=0.
            frag = ('<path transform="translate(%g,0) scale(%g,%g)" d="%s"/>'
                    % (x * k, k, -k, d))
            (head if i < split_at else tail).append(frag)
        x += hmtx[gn][0]

    return {"head": "".join(head), "tail": "".join(tail),
            "advance": x * k, "cap": cap_of("N"), "size": size}


def svg(w, h, body, bg=None):
    rect = ('<rect width="%g" height="%g" fill="%s"/>' % (w, h, bg)) if bg else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%g" height="%g" '
            'viewBox="0 0 %g %g">%s%s</svg>' % (w, h, w, h, rect, body))


def mark_at(x, y, side):
    """The header mark, placed and scaled. LOGO_MARK is drawn on a 32 grid."""
    return ('<g transform="translate(%g,%g) scale(%g)">%s</g>'
            % (x, y, side / 32.0, LOGO_MARK))


def mark_flat(x, y, side, inset=1.0):
    """The mark WITHOUT its rounded tile, for use on a full-bleed background.

    LOGO_MARK's first element is the rounded rect; everything after it is the
    artwork. Dropping it rather than redrawing the strokes keeps this tied to
    the real logo - if the hash or the waves change, this follows.
    """
    art = LOGO_MARK.split("/>", 1)[1]
    pad = (1 - inset) * 32 / 2.0
    return ('<g transform="translate(%g,%g) scale(%g)">'
            '<g transform="translate(%g,%g) scale(%g)">%s</g></g>'
            % (x, y, side / 32.0, pad, pad, inset, art))


# ---------------------------------------------------------------- lockups
def lockup_horizontal(bg=None):
    """Mark, then the name on one line. The wide format directories ask for."""
    wm = wordmark(NAME + SUFFIX, len(NAME))
    cap, adv = wm["cap"], wm["advance"]
    side = cap * 1.62           # mark a little taller than the capitals
    gap = side * 0.30
    pad = side * 0.22
    w = pad * 2 + side + gap + adv
    h = pad * 2 + side
    base = pad + side / 2 + cap / 2     # capitals centred on the mark
    tx = pad + side + gap
    body = (mark_at(pad, pad, side)
            + '<g transform="translate(%g,%g)">'
              '<g fill="%s">%s</g><g fill="%s">%s</g></g>'
              % (tx, base, NAVY, wm["head"], SKY, wm["tail"]))
    return svg(round(w, 1), round(h, 1), body, bg)


def lockup_stacked(bg=None):
    """Two lines, as the site header sets it: NumberMy / Boat.com."""
    top = wordmark("NumberMy", 8)
    bot = wordmark("Boat" + SUFFIX, 4)
    cap = top["cap"]
    lead = cap * 1.26
    side = (lead + cap) * 0.92
    gap = side * 0.26
    pad = side * 0.20
    tw = max(top["advance"], bot["advance"])
    w = pad * 2 + side + gap + tw
    h = pad * 2 + max(side, lead + cap)
    blocktop = pad + (h - pad * 2 - (lead + cap)) / 2
    tx = pad + side + gap
    body = (mark_at(pad, pad + (h - pad * 2 - side) / 2, side)
            + '<g transform="translate(%g,%g)" fill="%s">%s</g>'
              % (tx, blocktop + cap, NAVY, top["head"])
            + '<g transform="translate(%g,%g)">'
              '<g fill="%s">%s</g><g fill="%s">%s</g></g>'
              % (tx, blocktop + cap + lead, NAVY, bot["head"], SKY, bot["tail"]))
    return svg(round(w, 1), round(h, 1), body, bg)


def icon_svg():
    return svg(32, 32, LOGO_MARK)


def profile_svg():
    """Full-bleed navy, artwork inset - survives a circular crop."""
    return svg(512, 512,
               '<rect width="512" height="512" fill="%s"/>' % NAVY
               + mark_flat(0, 0, 512, inset=0.86))


def cover(w, h, tagline=True):
    """Centred lockup on the site's own hero gradient.

    The mark runs bigger here than in the lockup (1.85 vs 1.62 cap heights).
    In the lockup it carries its navy tile and reads as a solid block; stripped
    to flat strokes on a dark field it reads much lighter, and at the same
    ratio it looks shrunken beside the wordmark.
    """
    wm = wordmark(NAME + SUFFIX, len(NAME))
    cap, adv = wm["cap"], wm["advance"]
    side = cap * 1.85
    gap = side * 0.30
    block = side + gap + adv
    scale = min((w * 0.72) / block, (h * 0.42) / side)
    x = (w - block * scale) / 2

    # Centre the WHOLE stack, tagline included. Centring just the lockup and
    # nudging it up by a percentage left the tagline hanging in the top half
    # with a dead band underneath.
    t = ts = None
    gap_below = h * 0.085
    stack = side * scale
    if tagline:
        t = wordmark("$19 a pair - free shipping", 0)
        ts = min((w * 0.42) / t["advance"], side * scale * 0.30 / t["cap"])
        stack += gap_below + t["cap"] * ts
    y = (h - stack) / 2

    tag = ""
    if tagline:
        tx = (w - t["advance"] * ts) / 2
        ty = y + side * scale + gap_below + t["cap"] * ts
        tag = ('<g transform="translate(%g,%g) scale(%g)" fill="%s" '
               'opacity="0.92">%s</g>' % (tx, ty, ts, WHITE, t["tail"]))
    body = ('<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
            '</linearGradient></defs>'
            '<rect width="%g" height="%g" fill="url(#g)"/>'
            '<g transform="translate(%g,%g) scale(%g)">%s'
            '<g transform="translate(%g,%g)">'
            '<g fill="%s">%s</g><g fill="%s">%s</g></g></g>%s'
            % (NAVY, NAVY2, w, h, x, y, scale,
               mark_flat(0, 0, side, inset=0.92),
               side + gap, side / 2 + cap / 2,
               WHITE, wm["head"], SKY, wm["tail"], tag))
    return svg(w, h, body)


# ------------------------------------------------------------------ render
def png(src_svg, dest, w, h=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.svg")
    tmp.write_text(src_svg)
    cmd = ["rsvg-convert", "-w", str(w)]
    if h:
        cmd += ["-h", str(h)]
    cmd += ["-o", str(dest), str(tmp)]
    run(cmd)
    tmp.unlink()
    return dest


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    made = []

    def keep(p):
        made.append(p)
        return p

    # ---- vector masters
    (OUT / "svg").mkdir()
    for name, s in (("icon", icon_svg()),
                    ("lockup-horizontal", lockup_horizontal()),
                    ("lockup-horizontal-white", lockup_horizontal(bg=WHITE)),
                    ("lockup-stacked", lockup_stacked()),
                    ("profile", profile_svg())):
        p = OUT / "svg" / (name + ".svg")
        p.write_text(s)
        keep(p)

    # ---- the mark on transparent, for anything sitting on white
    ico = icon_svg()
    for size in (1024, 512, 256, 192, 180, 128, 96, 64, 48, 32, 16):
        keep(png(ico, OUT / "icon" / ("icon-%d.png" % size), size, size))

    # ---- full-bleed square, for avatars that get cropped to a circle
    prof = profile_svg()
    for size, who in ((1024, "master"), (720, "google-business"),
                      (500, "facebook"), (400, "x-twitter"),
                      (320, "instagram"), (300, "linkedin"), (250, "minimum")):
        keep(png(prof, OUT / "profile" / ("profile-%d.png" % size), size, size))

    # ---- horizontal + stacked lockups
    for stem, src in (("lockup-horizontal", lockup_horizontal()),
                      ("lockup-horizontal-white", lockup_horizontal(bg=WHITE)),
                      ("lockup-stacked", lockup_stacked()),
                      ("lockup-stacked-white", lockup_stacked(bg=WHITE))):
        for wpx in (2400, 1200, 600):
            keep(png(src, OUT / "lockup" / ("%s-%d.png" % (stem, wpx)), wpx))

    # ---- covers
    # Sizes are each platform's own, not one image reused. A Facebook PAGE
    # cover is 1640x624; 1200x630 is the link-preview card, a different slot.
    for stem, w, h in (("facebook-page-cover-1640x624", 1640, 624),
                       ("facebook-share-1200x630", 1200, 630),
                       ("google-business-cover-1024x576", 1024, 576),
                       ("x-header-1500x500", 1500, 500),
                       ("linkedin-cover-1128x191", 1128, 191)):
        s = cover(w, h, tagline=(h > 300))
        keep(png(s, OUT / "cover" / ("%s.png" % stem), w, h))

    # ---- real photographs, sized for the same slots
    # Google Business ranks a profile with real photos above a logo-only one,
    # and several directories have a media tab that stays conspicuously empty
    # otherwise. Masters live in media/photos/ rather than here, because this
    # script wipes brand/ on every run.
    photos = ROOT / "media" / "photos"
    for src_img in sorted(photos.glob("*.png")):
        base = Image.open(src_img).convert("RGB")
        # JPG, not PNG. A photograph has no transparency to preserve and PNG
        # stores it losslessly: the 1024 came out 1.5MB as a PNG against
        # 267KB as a JPG, for no visible difference, and it dragged the whole
        # zip to 4.8MB. One PNG is kept for the rare form that demands one.
        for size in (1024, 720, 500, 400, 320, 300, 250):
            d = OUT / "photo" / ("%s-%d.jpg" % (src_img.stem, size))
            d.parent.mkdir(parents=True, exist_ok=True)
            base.resize((size, size), Image.LANCZOS).save(
                d, quality=92, optimize=True)
            keep(d)
        d = OUT / "photo" / ("%s-1024.png" % src_img.stem)
        base.resize((1024, 1024), Image.LANCZOS).save(d)
        keep(d)

    # ---- one zip, because citation work means uploading the same set over
    # and over and nobody wants to click forty files.
    zp = OUT / "numbermyboat-logo-pack.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file() and f != zp:
                z.write(f, f.relative_to(OUT))

    files = [f for f in sorted(OUT.rglob("*")) if f.is_file()]
    total = sum(f.stat().st_size for f in files)
    print("brand: %d files, %.1f MB -> %s" % (len(files), total / 1e6, OUT))
    for f in files:
        print("   %-46s %6dKB" % (f.relative_to(OUT), f.stat().st_size // 1024))


if __name__ == "__main__":
    main()
