#!/usr/bin/env python3
"""A library of standalone cards for posting into boating groups.

    python3 media/share.py

These are NOT page OG cards. They exist to be dropped straight into a Facebook
group with no link and no pitch - the domain is cut small into the bottom of
the card and that is the whole ad. A group that would delete a link post will
happily leave up a picture of a boat called Payment 12 Of 240.

Two kinds:

  NAMES   a funny name set in script, exactly as it would be cut onto a
          transom. The joke and the product demo are the same object.
  LINES   a short shout in block caps, Buc-ee's style - the ones that teach
          something surprising travel furthest, because people argue in the
          comments about whether it is true.

Names are lifted from the generator's own bank so the library and the tool
cannot drift apart.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import og                                            # noqa: E402

OUT = HERE.parent / "public" / "assets" / "share"


def _bank():
    src = (HERE.parent / "engine" / "namegen.py").read_text()
    body = re.search(r"var N = \{(.*?)\n\};", src, re.S).group(1)
    out = {}
    for cat in ("double", "wtf", "deadpan", "ironic", "misspelled",
                "payments", "divorce", "pontoon"):
        m = re.search(r"%s: \[(.*?)\],?\n" % cat, body, re.S)
        if m:
            out[cat] = re.findall(r'"(.*?)"', m.group(1))
    return out


# Hand-picked: short enough to read at thumbnail size, funny without needing
# the category label, and nothing that gets the post removed.
NAMES = [
    ("Nauti Buoy", "white"), ("Ship Faced", "red"), ("Pier Pressure", "navy"),
    ("Knot On Call", "teal"), ("Reel Estate", "green"), ("Wet Couch", "black"),
    ("Payment 12 Of 240", "red"), ("Her Half", "navy"),
    ("Aggressively Beige", "white"), ("Mildly Damp", "teal"),
    ("Dock Holiday", "green"), ("Berth Control", "black"),
    ("Unsinkabel", "red"), ("Da Bote", "navy"),
    ("Sea Section", "teal"), ("Marlin Monroe", "white"),
    ("Trailer Queen", "black"), ("Floating Debt", "green"),
]

LINES = [
    ("MICHIGAN IS MC|NOT MI", "yes, really", "navy"),
    ("CALIFORNIA BOATS|START WITH CF", "not CA", "teal"),
    ("SCRIPT IS ILLEGAL|ON YOUR NUMBERS", "fine on the transom", "black"),
    ("3 INCHES.|IT'S FEDERAL.", "33 CFR 173.27", "red"),
    ("YOUR KAYAK|MIGHT NEED|NUMBERS", "depends on your state", "green"),
    ("WHITE ON WHITE|IS NOT LEGAL", "the rule says contrast", "white"),
    ("AN $11 SET|IS AN $18 SET|WITH SHIPPING", "ours includes it", "black"),
    ("DOCUMENTED BOATS|DON'T GET|BOW NUMBERS", "4-inch name instead", "navy"),
    ("NOTHING STICKS|TO A KAYAK", "which is why high-tack exists", "teal"),
    ("WISCONSIN IS WS|NOT WI", "nobody believes us either", "red"),
]


# Native photo posts are the point of this set: a photo post out-reaches a
# link post, and a group that deletes links will leave a picture up. Feeds
# crop differently, so each card ships in three shapes.
SIZES = [("", 1200, 630), ("-sq", 1080, 1080), ("-tall", 1080, 1350)]


def _resize(src, suffix, w, h):
    """Letterbox onto the target canvas rather than crop.

    Cropping a 1.91:1 card to a square eats the headline, which is the only
    thing on it. Padding with the card's own background keeps every word.
    """
    import subprocess
    dst = src.with_name(src.stem + suffix + ".png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", "scale=%d:-1:flags=lanczos,pad=%d:%d:(ow-iw)/2:"
                           "(oh-ih)/2:color=0x0e3a52" % (w, w, h),
                    "-frames:v", "1", str(dst)], check=True)
    return dst


def build_all():
    OUT.mkdir(parents=True, exist_ok=True)
    og.OUT = OUT                       # same renderer, different shelf
    made = 0
    for name, hull in NAMES:
        slug = "name-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        og.render(slug, main=name, script=True, hull=hull,
                  kicker="we cut whatever you call her")
        made += 1
    for main, kicker, hull in LINES:
        slug = "line-" + re.sub(r"[^a-z0-9]+", "-",
                                main.split("|")[0].lower()).strip("-")
        og.render(slug, main=main, kicker=kicker, hull=hull)
        made += 1
    # square and portrait crops for Instagram-shaped feeds and Stories
    base = [f for f in sorted(OUT.glob("*.png"))
            if not f.stem.endswith(("-sq", "-tall"))]
    for f in base:
        for suffix, w, h in SIZES[1:]:
            _resize(f, suffix, w, h)
    total = sum(f.stat().st_size for f in OUT.glob("*.png"))
    print(" share: %d cards x3 sizes -> %s (%.1f MB)"
          % (made, OUT, total / 1e6))
    return made


if __name__ == "__main__":
    build_all()
