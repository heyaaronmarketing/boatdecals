#!/usr/bin/env python3
"""Generate the applied-lettering image set.

    python3 media/gen.py --list                 # show the shot list
    python3 media/gen.py --only AL-01           # one shot
    python3 media/gen.py --batch                # everything not already on disk
    python3 media/gen.py --batch --force        # re-render everything

Model: OpenAI gpt-image-2.5 (the Google AI Studio key is out of credits; swap
back to ~/.claude/skills/tradephoto/scripts/nano_banana.py when it is topped
up - that model holds reference-image consistency better across a set).

These are ILLUSTRATIVE product shots. They are never captioned as a named
customer's boat - see media/CAPTIONS.md. The house rule, from the tradephoto
skill: "Never present an AI image as a specific customer's job."
"""
import argparse, base64, json, os, pathlib, subprocess, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "shots"
KEY = (os.environ.get("OPENAI_API_KEY")
       or (pathlib.Path.home() / ".config/openai/key").read_text().strip()
       if (pathlib.Path.home() / ".config/openai/key").exists()
       else os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-image-2"   # 2.5 is listed but not callable on this key

# The register that stops it reading as AI. Appended to every prompt.
# Deliberately NOT "professional photo" - a commercial-photography brief is
# exactly what makes these look generated.
REAL = (" Casual smartphone snapshot taken by the boat owner, not a "
        "professional photograph. Flat overcast daylight, no direct sun and no "
        "golden hour. Slightly off-level handheld framing, a little too much "
        "foreground. Visible sensor noise, mild lens smudge, water spots and "
        "faint scuffs on the hull, a cluttered marina or driveway background. "
        "Natural muted colour, no HDR, no glow, no vignette, nothing airbrushed.")

# Registration numbers are legally required to be PLAIN VERTICAL block
# characters. The first render leaned them slightly, which is both wrong and
# the kind of detail a boat owner notices.
UPRIGHT = (" All registration lettering must be perfectly upright block "
           "capitals - never italic, slanted, condensed or stylised.")

NEG = (" Do not render: any human faces, any brand logos, any text other than "
       "what is specified in quotation marks, golden-hour light, glossy "
       "oversaturated colour, HDR halos, perfect symmetry, studio lighting, "
       "watermark, misspelled or garbled lettering.")


def shots():
    """Applied-lettering set: what the decals look like on a real hull.

    Covers both contrast directions deliberately - light vinyl on a dark hull
    AND dark vinyl on a light hull - because that is the federal rule the whole
    site teaches, and the gallery has to demonstrate it.
    """
    S = []

    def add(sid, subject, spec, aspect="1024x1024"):
        # Script transom names are exempt - the upright rule is for numbers.
        up = "" if "script" in spec.lower() or "serif" in spec.lower() else UPRIGHT
        S.append({"id": sid, "spec": spec, "aspect": aspect,
                  "prompt": subject + up + REAL + NEG})

    add("AL-01",
        'Close-up of the forward port side of a white fibreglass runabout hull '
        'on a trailer in a gravel driveway. Black vinyl registration numbers '
        'reading exactly "IA 3717 ZW" are applied in plain vertical block '
        'characters about three inches tall, correctly spaced, parallel to the '
        'rub rail, with a small square validation decal a few inches aft of '
        'them.',
        'Black on white hull · 3" block · bow', "1536x1024")

    add("AL-02",
        'Close-up of the forward side of a dark navy blue fibreglass bowrider '
        'hull floating at a wooden dock. White vinyl registration numbers '
        'reading exactly "MC 1234 AB" are applied in plain vertical block '
        'characters about three inches tall, correctly spaced, high above the '
        'waterline.',
        'White on navy hull · 3" block · bow', "1536x1024")

    add("AL-03",
        'The flat transom of a white fibreglass boat tied at a dock, '
        'photographed straight on from the dock. The boat name "KNOT WORKING" '
        'is applied across the transom in black vinyl script lettering about '
        'six inches tall, slightly weathered gelcoat around it, outboard motor '
        'partly in frame at the bottom.',
        'Black script transom name · 6"', "1536x1024")

    add("AL-04",
        'The side of a riveted aluminium jon boat on a trailer, bare metal with '
        'visible rivet lines and a painted olive stripe. Black vinyl '
        'registration numbers reading exactly "WS 1234 AB" are applied on a '
        'flat panel between two rivet rows, three inches tall.',
        'Black on bare aluminium · jon boat', "1536x1024")

    add("AL-05",
        'The hull side of a white and red personal watercraft (jet ski) sitting '
        'on a trailer beside a lake. Black vinyl registration numbers reading '
        'exactly "CF 1234 AB" are applied on the moulded plastic hull above the '
        'footwell, three inches tall, following the slight curve.',
        'Black on PWC plastic hull', "1024x1024")

    add("AL-06",
        'A yellow rotomoulded plastic kayak resting on grass beside a lake, '
        'photographed from the side. Black vinyl registration numbers reading '
        'exactly "MN 1234 AB" are applied on the bow section, three inches '
        'tall, on the textured plastic.',
        'Black on kayak · high-tack vinyl', "1536x1024")

    add("AL-07",
        'The aluminium fence panel on the side of a pontoon boat at a dock, '
        'brushed silver rails. Black vinyl registration numbers reading exactly '
        '"TX 1234 AB" are applied on the forward fence panel, three inches '
        'tall, with a validation decal beside them.',
        'Black on pontoon rail', "1536x1024")

    add("AL-08",
        'The curved white transom of a sailboat moored in a harbour, '
        'photographed from a dinghy slightly below. The boat name "SECOND WIND" '
        'in black vinyl serif lettering arcs to follow the transom curve, with '
        '"GALVESTON, TX" below it in smaller four-inch letters.',
        'Name + hailing port · curved transom', "1024x1024")

    add("AL-09",
        'Extreme close-up of vinyl registration lettering reading exactly '
        '"IA 3717 ZW" being squeegeed onto a white gelcoat hull, clear '
        'application tape still covering the lettering, a red felt squeegee '
        'pressing from the centre outward, droplets of soapy water beading at '
        'the edge. Only a gloved hand and the squeegee are in frame. The '
        'lettering must show the spaces between the groups.',
        'Application detail · wet method', "1024x1024")

    add("AL-10",
        'The forward side of a metalflake dark green bass boat on a trailer, '
        'sparkling gelcoat finish. White vinyl registration numbers reading '
        'exactly "MO 1234 AB" are applied three inches tall above the waterline '
        'stripe.',
        'White on metalflake · bass boat', "1536x1024")

    return S


def generate(prompt, size):
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": size,
                       "n": 1}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": "Bearer " + KEY,
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode())
    item = d["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    with urllib.request.urlopen(item["url"], timeout=120) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    S = shots()
    if a.list:
        for s in S:
            print("%-7s %-38s %s" % (s["id"], s["spec"], s["aspect"]))
        print("\n%d shots" % len(S))
        return

    todo = [s for s in S if (not a.only or s["id"] == a.only)]
    if not a.batch and not a.only:
        ap.error("need --list, --only ID, or --batch")
    OUT.mkdir(parents=True, exist_ok=True)

    for s in todo:
        dest = OUT / (s["id"] + ".jpg")
        if dest.exists() and not a.force:
            print("skip  %s (exists)" % s["id"]); continue
        print("gen   %s  %s ..." % (s["id"], s["spec"]), flush=True)
        t = time.time()
        try:
            raw = generate(s["prompt"], s["aspect"])
            # The API returns PNG; these are photographs, so store JPEG -
            # ~2.5MB vs ~250KB each, and git over HTTP rejects the PNG set.
            tmp = dest.with_suffix(".tmp.png")
            tmp.write_bytes(raw)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp),
                            "-q:v", "3", str(dest)], check=True)
            tmp.unlink()
            print("  ok  %s  %.0fs  %.0fKB" % (dest.name, time.time()-t,
                                               dest.stat().st_size/1024))
        except urllib.error.HTTPError as e:
            print("  FAIL %s: %s" % (s["id"], e.read().decode()[:220]))
        except Exception as e:
            print("  FAIL %s: %s" % (s["id"], e))

    (OUT / "shots.json").write_text(json.dumps(
        [{k: v for k, v in s.items() if k != "prompt"} for s in S], indent=1))


if __name__ == "__main__":
    main()
