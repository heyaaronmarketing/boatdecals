#!/usr/bin/env python3
"""Bake the standard-English word list the radio gate needs.

WHY A BAKED FILE. The radio gate has to answer one question about every token
in a name: "if I say this out loud, will the listener spell it the way it is
written?" Answering that needs to know what the standard spelling of a word
IS - Bote is a radio problem precisely because `boat` exists and `bote` does
not. So the gate needs a dictionary.

It cannot read /usr/share/dict/words at gate time. A deterministic gate must
give the same verdict on Aaron's Mac, on a CI box and in the deployed worker,
and that file exists on exactly one of those three. So the list is DERIVED here
and committed, the same way the name bank is derived and committed: the source
is a system file, the generator is in the repo, and the artefact is the thing
the gate reads.

Source: /usr/share/dict/words (web2 - public domain, from Webster's 1913).
Filtered to <= 11 characters because the gate only ever asks about single
tokens inside a boat name, and stored gzipped at ~540 KB.

Run: python3 mcp/build_lexicon.py
"""
import gzip
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEST = HERE / "data" / "lexicon.txt.gz"
SRC = pathlib.Path("/usr/share/dict/words")
# 1,308 given names. Without these the gate tells a customer that "Larry" and
# "Kevin" have to be spelled out over the radio.
NAMES_SRC = pathlib.Path("/usr/share/dict/propernames")

# Words the shop's own world uses that a 1913 dictionary does not carry. These
# are standard spellings to any boater - the gate must not tell a customer that
# "pontoon" needs spelling out over the radio.
# web2 is Webster's 1913, and it is a HEADWORD list. It carries "pay" but not
# "paid", "have" but not "has", "hear" but not "heard" - and it predates most
# of the twentieth century. The first version of the radio gate told a customer
# that "Paid Off" and "Wave Goodbye" would need spelling out letter by letter,
# which is the kind of wrong answer that makes someone stop trusting every
# other answer on the page.
#
# Three groups: irregular inflections web2 omits by design, words the last
# century added, and the shop's own vocabulary.
EXTRA = """
has had paid said heard made took taken went gone done seen been got gotten
bought sold built lost found kept told left felt held brought caught taught
thought knew known grew grown drew drawn threw thrown blew blown flew flown
spent sent lent meant met led fed bled sat stood understood began begun
chose chosen rose risen wore worn bore born spoke spoken broke broken
goodbye hello okay

independence impermanence irreconcilable unsubscribe offsite pretax paycheck
rehired respawn repo decaf preapproved cosigned
lasagna marinara sushi burrito burritos taco tacos nacho nachos pizza
cookie cookies brownie crawlies yikes oops gonna gotta wanna kinda
lowkey highkey floatie floaties selfie hoodie podcast podcasts blog
minivan scalable disruptor deliverables bandwidth
collateral depreciating

pontoon pontoons koozie koozies coozie cooler coolers bimini kayak kayaks
kayaking paddleboard livewell transom transoms gunwale outboard inboard
trolling walleye walleyes crappie crappies bluegill muskie muskies bass
catfish sunfish bobber bobbers jig jigs lure lures stringer tackle
bilge cleat cleats fender fenders decal decals vinyl
boat boats lake lakes dock docks marina marinas anchor anchors
sunscreen snacks snack grandkids grandkid vibe vibes vibing
casserole hotdish bratwurst brats lutefisk jello
retirement mortgage escrow alimony prenup medicare pickleball
email online offline website wifi bluetooth emoji

monroe fett holliday archimedes bernoulli newton schrodinger davy
bermuda erie iowa minnesota wisconsin
""".split()


def main():
    if not SRC.exists():
        sys.exit("no %s on this machine - the lexicon can only be rebuilt "
                 "somewhere that has it; the committed data/lexicon.txt.gz is "
                 "the artefact the gate reads" % SRC)

    words = set()
    if NAMES_SRC.exists():
        for raw in NAMES_SRC.read_text(encoding="utf-8",
                                       errors="ignore").splitlines():
            w = raw.strip().lower()
            if 2 <= len(w) <= 11 and w.isalpha():
                words.add(w)
    for raw in SRC.read_text(encoding="utf-8", errors="ignore").splitlines():
        w = raw.strip().lower()
        # Single letters are not words for our purpose: "U" and "R" in a boat
        # name are letter-soup, which is exactly what the gate must catch.
        if 2 <= len(w) <= 11 and w.isalpha():
            words.add(w)
    before = len(words)
    words |= {w for w in EXTRA if w}

    DEST.parent.mkdir(exist_ok=True)
    with gzip.open(DEST, "wt", encoding="utf-8") as f:
        f.write("\n".join(sorted(words)))

    print("lexicon: %d words (%d from %s, %d shop-specific additions)"
          % (len(words), before, SRC.name, len(words) - before))
    print("-> %s  (%.0f KB)" % (DEST, DEST.stat().st_size / 1024))


if __name__ == "__main__":
    main()
