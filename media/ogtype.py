#!/usr/bin/env python3
"""Set a line of type as SVG PATHS, not as <text>.

librsvg on macOS renders through CoreText, not fontconfig, so a font that is
not installed system-wide silently falls back to Helvetica - and the OG images
would ship in the wrong face without anything failing. Converting the glyphs
to outlines removes the question entirely: the PNG renders identically on any
machine, with no font to install.

It is also what actually happens to this lettering in real life. A plotter
does not set type either; it cuts a path.
"""
import pathlib
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONTS = pathlib.Path(__file__).resolve().parent / "fonts"
_CACHE = {}


def _font(name):
    if name not in _CACHE:
        f = TTFont(FONTS / name, lazy=True)
        _CACHE[name] = (f, f.getGlyphSet(), f["cmap"].getBestCmap(),
                        f["head"].unitsPerEm, f["hmtx"])
    return _CACHE[name]


def measure(text, ttf, size):
    _f, _gs, cmap, upem, hmtx = _font(ttf)
    adv = 0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            g = cmap.get(ord(" "))
        adv += hmtx[g][0] if g else 0
    return adv * size / upem


def path_for(text, ttf, size, x=0.0, y=0.0, tracking=0.0):
    """Outlines for `text`, baseline at (x, y), in SVG user units."""
    _f, glyphs, cmap, upem, hmtx = _font(ttf)
    s = size / upem
    out, pen_x = [], x
    for ch in text:
        name = cmap.get(ord(ch)) or cmap.get(ord(" "))
        if name is None:
            continue
        pen = SVGPathPen(glyphs)
        # y is flipped: font units go up, SVG goes down
        glyphs[name].draw(TransformPen(pen, (s, 0, 0, -s, pen_x, y)))
        d = pen.getCommands()
        if d:
            out.append(d)
        pen_x += hmtx[name][0] * s + tracking
    return " ".join(out), pen_x - x


def fit(text, ttf, max_w, max_size, tracking=0.0):
    """Largest size at which `text` fits `max_w`."""
    size = max_size
    while size > 8:
        w = measure(text, ttf, size) + tracking * max(0, len(text) - 1)
        if w <= max_w:
            return size, w
        size -= 1
    return size, measure(text, ttf, size)
