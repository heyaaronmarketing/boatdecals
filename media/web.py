#!/usr/bin/env python3
"""Turn the masters into web assets.

    python3 media/web.py

Writes public/assets/img/<id>-{800,1400}.{webp,jpg} — WebP for browsers that
take it, JPEG as the fallback, two widths for srcset. The 2.4MB masters are
the archive; nothing that large is ever served.
"""
import pathlib, shutil, subprocess, sys

CWEBP = shutil.which('cwebp')

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "shots"
OUT = ROOT.parent / "public" / "assets" / "img"
WIDTHS = [800, 1400]


def build(src, stem, w):
    """JPEG via ffmpeg, WebP via cwebp.

    This ffmpeg build has no WebP encoder, so cwebp (homebrew libwebp) does
    that half. Resize once to the JPEG, then convert it - cwebp reads JPEG
    directly and the double encode is invisible at q82 from a q4 source.
    """
    jpg = OUT / f"{stem}-{w}.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", f"scale={w}:-2:flags=lanczos", "-q:v", "4",
                    "-frames:v", "1", str(jpg)], check=True)
    if CWEBP:
        subprocess.run([CWEBP, "-quiet", "-q", "82", str(jpg),
                        "-o", str(OUT / f"{stem}-{w}.webp")], check=True)


def main():
    masters = sorted(p for pre in ("AL", "HT", "GD", "AC", "PR", "ST", "HB")
                 for p in SRC.glob("%s-*.jpg" % pre))
    if not masters:
        sys.exit("no masters in %s" % SRC)
    OUT.mkdir(parents=True, exist_ok=True)
    for m in masters:
        for w in WIDTHS:
            build(m, m.stem, w)
    if not CWEBP:
        print("NOTE: cwebp not found - JPEG only. brew install webp")
    total = sum(f.stat().st_size for f in OUT.glob("*"))
    print("%d masters -> %d files, %.1f MB total"
          % (len(masters), len(list(OUT.glob("*"))), total / 1e6))


if __name__ == "__main__":
    main()
