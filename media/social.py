#!/usr/bin/env python3
"""Derive social crops from each master shot.

    python3 media/social.py            # all masters -> media/social/<id>/

One master, many sizes - the rule from the social-media-content skill.

Blur-fill, not centre-crop. Going from a 3:2 master to 9:16 throws away about
two thirds of the width, and the lettering does not sit dead centre: the first
pass sliced the "M" off "MC 1234 AB". Scaling to FIT and padding with a blurred
copy of the same frame keeps the subject whole at every size, which matters
more here than filling the frame edge to edge.

Sizes match the skill's spec:
  1080x1350  4:5   Instagram/Facebook feed, LinkedIn
  1080x1920  9:16  Reels, TikTok, Shorts, Stories
  1080x1080  1:1   feed square, Pinterest square
  1000x1500  2:3   Pinterest tall
"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC, OUT = ROOT / "shots", ROOT / "social"
SIZES = [("feed-4x5", 1080, 1350), ("story-9x16", 1080, 1920),
         ("square-1x1", 1080, 1080), ("pin-2x3", 1000, 1500)]


def crop(src, dest, w, h):
    vf = (f"split[a][b];"
          f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,"
          f"crop={w}:{h},gblur=sigma=26[bg];"
          f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=({w}-overlay_w)/2:({h}-overlay_h)/2")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", vf, "-frames:v", "1", "-q:v", "3", str(dest)],
                   check=True)


def main():
    if not SRC.exists():
        sys.exit("no masters in %s - run gen.py first" % SRC)
    masters = sorted(p for pre in ("AL", "HT", "GD", "AC", "PR")
                 for p in SRC.glob("%s-*.jpg" % pre))
    if not masters:
        sys.exit("no AL-*.jpg masters yet")
    n = 0
    for m in masters:
        d = OUT / m.stem
        d.mkdir(parents=True, exist_ok=True)
        for name, w, h in SIZES:
            crop(m, d / f"{m.stem}-{name}.jpg", w, h)
            n += 1
        print("  %s -> %d crops" % (m.stem, len(SIZES)))
    print("\n%d crops from %d masters -> %s" % (n, len(masters), OUT))


if __name__ == "__main__":
    main()
