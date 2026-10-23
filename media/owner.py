#!/usr/bin/env python3
"""Real photographs of Ryan and the department, prepared for the site.

    python3 media/owner.py

Everything else in media/ GENERATES images. This script does the opposite: it
takes photographs that already exist and prepares them. The distinction
matters enough to keep the code separate.

`RP-*` is the only prefix on this site that is a real photograph. Every other
shot (AL, HT, GD, AC, PR, HB, ST) is generated and illustrative. If you are
ever unsure whether an image can carry a factual caption about a real person,
the prefix is the answer: RP yes, everything else no.

Sources:
  RP-1  Ryan's own Facebook profile picture, lifted from the full-page capture
        in ~/Downloads. 1002x979 native, which is enough for a 1400px hero
        with a 1.4x Lanczos resample. NO generative upscaling - see below.
  RP-2+ Original full-resolution phone photographs of Evansdale Fire & Rescue
        (5712x4284), straight from Ryan. No processing needed beyond resize.

On AI enhancement: not used, and not wanted. Generative upscalers do not
recover detail, they invent it. On a photograph of a real, named person that
means a synthetic face presented as a photograph of him - which is the same
line media/CAPTIONS.md draws for customers, and it matters more for the owner
of the shop, not less. Lanczos only. If a photo is too small, the answer is a
better photo, not a better hallucination.
"""
import pathlib, subprocess, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "shots"
DL = pathlib.Path.home() / "Downloads"
CAPTURE = DL / "screencapture-facebook-ryan-phillips-420847-2026-10-23-14_01_41.png"

# (id, source HEIC in ~/Downloads)
FROM_PHONE = [
    ("RP-2", "IMG_2802.HEIC"),   # turnout gear on the racks
    ("RP-3", "IMG_2809.HEIC"),   # Engine 201, front
    ("RP-4", "IMG_2813.HEIC"),   # the apparatus bay, looking through
]
# the motocross profile picture, measured off the capture
MX_BOX = (1299, 1971, 2301, 2950)


def from_capture():
    if not CAPTURE.exists():
        print("  skip RP-1: capture not in ~/Downloads"); return
    im = Image.open(CAPTURE).crop(MX_BOX)
    w, h = im.size
    # 1.4x is about the limit where Lanczos still looks like a photograph
    im = im.resize((int(w * 1.6), int(h * 1.6)), Image.LANCZOS)
    im.convert("RGB").save(OUT / "RP-1.jpg", quality=94, subsampling=0)
    print("  RP-1  %dx%d -> %dx%d" % (w, h, *im.size))


def from_phone():
    for rid, name in FROM_PHONE:
        src = DL / name
        if not src.exists():
            print("  skip %s: %s missing" % (rid, name)); continue
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92",
                        "-Z", "2200", str(src), "--out", str(OUT / (rid + ".jpg"))],
                       check=True, capture_output=True)
        print("  %s  <- %s" % (rid, name))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    from_capture()
    from_phone()
    print("done - run engine/build.py to size them for the web")
