#!/usr/bin/env python3
"""Tell Bing a page changed, instead of waiting to be found.

WHY THIS AND NOT KEYWORD RESEARCH. Bing is a rounding error of search share,
but its index is what ChatGPT search reads, and this site is built to be
quoted by answer engines - the guides, the free tools and llms.txt all exist
for that. So the question that matters here is not "where do we rank on Bing",
it is "how long after a change does Bing know". IndexNow turns that from
whenever-a-crawler-comes into about a second.

The November price change is the case in point: 55 pages changed price at once
and nothing told anybody. A crawler finds that on its own schedule, and until
it does, the figure an assistant quotes from Bing's index is last month's.

HOW IT WORKS. Two halves, and both have to be true:

  * a key file served at https://numbermyboat.com/<key>.txt whose entire
    contents are the key - that is how Bing checks that whoever is submitting
    URLs controls the site. engine/build.py writes it, so it cannot be
    forgotten in a rebuild, and verify.py fails the build if it goes missing
    while a key is configured.

  * a POST to api.indexnow.org naming the host, the key and the URLs. One
    request covers up to 10,000 URLs; this site has 55.

THE KEY IS NOT A SECRET. It is served from a public URL by design - that is
the whole verification mechanism. It lives in engine/content.py next to the
analytics ids rather than in a Worker secret, for the same reason: treating a
public string as a credential only means nobody can rebuild the site.

WHAT IT SUBMITS. By default, only the pages whose sitemap lastmod is today -
which is what "this changed" means. Submitting all 55 on every run is not
more thorough, it is noise, and IndexNow's own guidance is to send what
changed. Pass --all for a genuine full resubmit (a new domain, a recovered
index), and --dry-run to see the list without sending anything.

    python3 mcp/indexnow.py              # what changed today
    python3 mcp/indexnow.py --all        # every page in the sitemap
    python3 mcp/indexnow.py --dry-run    # show, do not send

Run it AFTER the deploy has landed. Submitting a URL that still serves the old
page asks Bing to come and re-read the thing it already has.
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))

from content import SITE, INDEXNOW_KEY          # noqa: E402

ENDPOINT = "https://api.indexnow.org/IndexNow"
HOST = SITE["domain"]
SITEMAP = os.path.join(ROOT, "public", "sitemap.xml")


def sitemap_entries():
    """[(url, lastmod)] straight out of the built sitemap."""
    xml = open(SITEMAP, encoding="utf-8").read()
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        mod = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if loc:
            out.append((loc.group(1), mod.group(1) if mod else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="submit every URL in the sitemap, not just today's")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be sent and exit")
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="submit pages changed on or after this date")
    args = ap.parse_args()

    if not INDEXNOW_KEY:
        print("No IndexNow key configured. Get one from Bing Webmaster Tools\n"
              "(Settings -> API access -> IndexNow) and paste it into\n"
              "INDEXNOW_KEY in engine/content.py, then rebuild.")
        return 2

    entries = sitemap_entries()
    if not entries:
        print("public/sitemap.xml has no URLs - run python3 engine/build.py")
        return 1

    if args.all:
        urls, why = [u for u, _ in entries], "every page in the sitemap"
    else:
        cutoff = args.since or str(datetime.date.today())
        urls = [u for u, m in entries if m and m >= cutoff]
        why = "changed on or after %s" % cutoff

    if not urls:
        # Not a failure. It means nothing changed, which is the normal state.
        print("Nothing %s - nothing to submit." % why)
        return 0

    # The key file has to be live before the URLs are accepted. Checking costs
    # one request and turns a silent 403 into a sentence.
    key_url = "https://%s/%s.txt" % (HOST, INDEXNOW_KEY)
    try:
        got = urllib.request.urlopen(urllib.request.Request(
            key_url, headers={"user-agent": "nmb-indexnow"}),
            timeout=20).read().decode().strip()
        if got != INDEXNOW_KEY:
            print("The key file at %s does not contain the key.\n"
                  "It holds %r. Bing will reject every submission until that "
                  "matches." % (key_url, got[:40]))
            return 1
    except urllib.error.HTTPError as e:
        print("The key file is not live: %s returned %s.\n"
              "It is written by engine/build.py - has the deploy landed?"
              % (key_url, e.code))
        return 1

    print("Submitting %d URL(s) - %s" % (len(urls), why))
    for u in urls[:8]:
        print("   ", u)
    if len(urls) > 8:
        print("    ... and %d more" % (len(urls) - 8))

    if args.dry_run:
        print("\n--dry-run: nothing sent.")
        return 0

    body = json.dumps({"host": HOST, "key": INDEXNOW_KEY,
                       "keyLocation": key_url, "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, body, {
        "content-type": "application/json; charset=utf-8",
        "user-agent": "nmb-indexnow"})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        code = r.status
    except urllib.error.HTTPError as e:
        code = e.code

    # IndexNow's status codes are worth spelling out: a bare number here has
    # sent people looking for a bug in the submission when the key file was
    # the problem, and 200 vs 202 means different things on different days.
    meaning = {
        200: "accepted",
        202: "accepted, key validation pending",
        400: "bad request - the JSON or the URL list is malformed",
        403: "key not valid - the key file did not match",
        422: "a URL does not belong to this host, or the key does not match",
        429: "too many requests - slow down",
    }.get(code, "unexpected")
    print("\nIndexNow returned %s (%s)" % (code, meaning))
    return 0 if code in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
