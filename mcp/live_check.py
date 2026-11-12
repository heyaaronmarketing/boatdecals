#!/usr/bin/env python3
"""The production smoke test, and the one rule that makes it safe to run.

Verifying the naming engine against production means running a real session,
which means the ledger learns from it - and a script that keeps the first
name in a list is not a person with taste. After two verification runs the
production ledger read:

    deadpan  hp   exp=2   keeps=2   rate=1.0      <- a riff a script kept
    deadpan  dp   exp=4   keeps=0   kills=4       <- a script killing a slice
    any      lt   exp=23  keeps=2                 <- seven short of proven

Seven more exposures and the brief would have started telling a host model
that literal-truth jokes are PROVEN in the deadpan lane, on evidence a for
loop produced. That is the fabricated-evidence failure the warm-ledger
fixture shouts about in its header, arriving through the back door.

SO THE WRITING HALF OF THIS SCRIPT REFUSES TO RUN UNLESS THE LEDGER IS
EMPTY, and wipes it afterwards. The invariant is the whole point: this only
ever runs against a ledger it is allowed to destroy, and it proves it is
allowed by requiring there to be nothing there. The first real customer makes
the ledger non-empty for good, and from then on this script will only do the
read-only half - which is the correct answer, because by then the full flow
belongs on local D1 with mcp/fixtures/warm-ledger.local.sql.

    python3 mcp/live_check.py
"""
import json
import os
import subprocess
import sys
import urllib.request

SITE = os.environ.get("NMB_SITE", "https://numbermyboat.com")
ACCOUNT = "681da9da7939c8989b00fb80ee4a791c"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def call(tool, args):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(SITE + "/mcp", body, {
        "content-type": "application/json", "user-agent": "nmb-live-check"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    r = d["result"]
    if r.get("isError"):
        raise RuntimeError(r["content"][0]["text"])
    return json.loads(r["content"][0]["text"])


def d1(sql):
    """One SQL statement against the remote database."""
    env = dict(os.environ, CLOUDFLARE_ACCOUNT_ID=ACCOUNT,
               NODE_EXTRA_CA_CERTS="/etc/ssl/cert.pem")
    p = subprocess.run(
        ["npx", "wrangler", "d1", "execute", "boatnumbershop", "--remote",
         "--json", "--command", sql],
        capture_output=True, text=True, cwd=ROOT, env=env)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-400:])
    # wrangler prints a banner before the JSON on some versions.
    out = p.stdout[p.stdout.index("["):]
    return json.loads(out)[0]["results"]


def check(cond, msg):
    if not cond:
        fails.append(msg)


# ---------------------------------------------------------------------------
# Read-only. Always safe, always run.
# ---------------------------------------------------------------------------
req = urllib.request.Request(SITE + "/mcp", json.dumps(
    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
    {"content-type": "application/json", "user-agent": "nmb-live-check"})
tools = json.load(urllib.request.urlopen(req, timeout=30))["result"]["tools"]
writers = sorted(t["name"] for t in tools
                 if not t["annotations"].get("readOnlyHint"))
print("%d tools live" % len(tools))
print("writers: %s" % ", ".join(writers))
check(writers == ["start_naming_session", "submit_riff_candidates",
                  "vote_on_names"] or set(writers) == {
          "start_naming_session", "submit_riff_candidates", "vote_on_names"},
      "the set of writing tools in production is %s" % writers)

r = call("test_boat_name", {"name": "Loading…"})
check(r["radio"]["readback"] == "Mayday, mayday, this is Loading.",
      "the readback is %r - trailing punctuation is back"
      % r["radio"]["readback"])
# The price, in all three vocabularies the site uses for the same three
# products. This is where price_order quoted $19 for a $44 bundle.
for kind, want in (("numbers", 19), ("name", 29), ("both", 44),
                   ("registration-numbers", 19), ("boat-name", 29)):
    r = call("price_order", {"kind": kind, "height": "3"})
    check(r["amount_usd"] == want,
          "price_order(%s) at 3 inches = $%s, should be $%s"
          % (kind, r["amount_usd"], want))
try:
    call("price_order", {"kind": "name-plus-port"})
    fails.append("price_order accepted a product we do not sell and quoted "
                 "a number for it")
except RuntimeError:
    pass
print("prices: ok in every vocabulary")

# The boundary. A misnamed parameter must be refused, not answered - this
# exact call came back verdict "ok" having read nothing.
try:
    bad = call("check_registration_layout",
               {"text": "IA 1234 AB", "state": "IA"})
    fails.append("a call with the parameter misnamed was ANSWERED: %s"
                 % json.dumps(bad)[:160])
except RuntimeError as e:
    check("not a result" in str(e),
          "the rejection does not say it is a rejection: %s" % e)
r = call("check_registration_layout", {"number": "IA 1234 AB"})
check(r["verdict"] in ("ok", "check"), "a real layout check returned %r"
      % r["verdict"])
check(r["width"]["accuracy"] is None,
      "no boat name was given and the accuracy figure is %r - this printed "
      "'+/-undefined%%' at a customer" % r["width"]["accuracy"])
r = call("check_registration_layout", {"number": "IA 1234 AB", "height_in": 2})
check("33 CFR 173.27" in json.dumps(r),
      "a 2-inch registration number no longer cites the federal minimum")
print("argument boundary: ok")

# What every client reads first.
init = urllib.request.Request(SITE + "/mcp", json.dumps(
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {}}).encode(),
    {"content-type": "application/json", "user-agent": "nmb-live-check"})
ins = json.load(urllib.request.urlopen(init, timeout=30))[
    "result"]["instructions"]
check("read-only" not in ins,
      "initialize still tells every client that every tool is read-only")
for w in ("start_naming_session", "vote_on_names", "submit_riff_candidates"):
    check(w in ins, "initialize does not name %s as a writer" % w)
print("instructions: ok")

# ---------------------------------------------------------------------------
# The writing half, behind the empty-ledger invariant.
# ---------------------------------------------------------------------------
rows = d1("SELECT count(*) AS n, COALESCE(sum(exposures),0) AS e FROM ledger")
have = rows[0]["n"]
if have:
    print("\nledger has %d rows (%d exposures) - SKIPPING the session flow."
          % (have, rows[0]["e"]))
    print("That data may be real. Run the full flow against local D1 with "
          "mcp/fixtures/warm-ledger.local.sql instead; see mcp/README.md.")
else:
    print("\nledger empty - running the full session flow, then wiping it")
    answers = {"boat": "a 19 foot bass boat",
               "aboard": "just me and my brother",
               "vibe": "puns, nothing crude", "transom": "44 inches",
               "work": "I run a small HVAC company", "port": "Clear Lake"}
    s = call("start_naming_session", {"answers": answers})
    sid = s["session_id"]
    check(len(s["names"]) == 8, "round one dealt %d names" % len(s["names"]))
    check(s["riff_brief"] is not None, "round one carried no riff brief")
    b = s["riff_brief"]
    check(len(b["exemplars"]) >= 3,
          "a cold brief carried %d exemplars" % len(b["exemplars"]))
    check("no keep data" in b["exemplars_chosen_by"],
          "a cold brief claims its exemplars were chosen by keep-rate")
    check("nothing crude" in (b["ceiling_means"] or "")
          or b["ceiling"] == "clean",
          "he asked for nothing crude and the ceiling is %s" % b["ceiling"])

    rr = call("submit_riff_candidates", {"session_id": sid, "candidates": [
        {"name": "Duct Season", "mechanism": "hp",
         "why": "he runs an HVAC company"},
        {"name": "Vitamin Sea", "mechanism": "dm", "why": "a cliche on purpose"},
        {"name": "Nauti-4-U", "mechanism": "hp", "why": "a rebus on purpose"},
    ]})
    kept_r = [x["name"] for x in rr["survived"]]
    check("Duct Season" in kept_r, "a clean trade pun did not survive: %s"
          % rr["why_they_dropped"])
    check(rr["dropped"] == 2, "%d of the two deliberate failures survived"
          % (2 - rr["dropped"]))

    dealt = s["names"]
    v = call("vote_on_names", {"session_id": sid,
                               "kept": [dealt[0]["name"]],
                               "killed": [n["name"] for n in dealt[1:3]]})
    check(v["next_round"], "the vote produced no next round")
    worst = {}
    for n in v["next_round"]:
        worst[n["mechanism_code"]] = worst.get(n["mechanism_code"], 0) + 1
    check(max(worst.values()) <= 2,
          "a round of four came back %d-of-one-joke: %s"
          % (max(worst.values()), [n["name"] for n in v["next_round"]]))
    v2 = call("vote_on_names", {"session_id": sid,
                                "kept": [n["name"] for n in v["next_round"][:2]],
                                "killed": []})
    f = call("reveal_finalists", {"session_id": sid})
    n_fin = len(f["finalists"])
    head = f["card_for_the_family"]["heading"]
    check(str(n_fin) in head or
          ["", "One name", "Two names", "Three names"][n_fin] in head,
          "the card says %r over %d names" % (head, n_fin))
    reasons = {x["why_this_one"] for x in f["finalists"]}
    check(len(reasons) == n_fin,
          "two finalists came back with the same reason - the reveal reads "
          "as generated")
    for x in f["finalists"]:
        print("  * %s - %s" % (x["name"], x["why_this_one"]))
    print("  card: %s -> %s" % (head, f["card_for_the_family"]["names"]))

    d1("DELETE FROM ledger")
    left = d1("SELECT count(*) AS n FROM ledger")[0]["n"]
    check(left == 0, "the ledger still has %d rows after the wipe" % left)
    print("\nledger wiped - this run's keeps were a script's, not a "
          "customer's")

for f_ in fails:
    print("FAIL: " + f_)
if fails:
    print("\n%d live check(s) failed" % len(fails))
    sys.exit(1)
print("\nlive check passes")
