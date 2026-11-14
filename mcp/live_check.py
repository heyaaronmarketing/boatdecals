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
# The price, in all the vocabularies the site uses for the same three
# products. This is where price_order quoted the registration-number base for
# the bundle, in every vocabulary, silently.
#
# The figures are read from the deployed /api/price rather than written in
# here, because a constant in a smoke test is a fourth copy of the price list
# - and a smoke test that asserts last month's figure fails for the wrong
# reason on the day the price changes. What is being checked is that the MCP
# tool and the website's own pricing authority answer the SAME number for the
# same order, which is the thing that would send a customer an argument.
#
# "Ox" is the lettering for the name cases: a boat name is priced by the
# width it finishes at, so a quote needs the text and the face.
def api_price(args):
    """The website's own pricing authority, over HTTP, as a customer hits it."""
    body = json.dumps(args).encode()
    req = urllib.request.Request(SITE + "/api/price", body, {
        "content-type": "application/json", "user-agent": "nmb-live-check"})
    return json.load(urllib.request.urlopen(req, timeout=30))


NAME_CASE = {"boatname": "Ox", "font": "Arial Bold"}
for kind, body in (("numbers", {}), ("name", NAME_CASE), ("both", NAME_CASE),
                   ("registration-numbers", {}), ("boat-name", NAME_CASE)):
    args = dict(kind=kind, height="3", **body)
    r = call("price_order", args)
    authority = api_price(args)
    check(r["amount_usd"] == authority["amount"],
          "price_order(%s) says $%s and /api/price says $%s - an assistant "
          "would quote one and the card would charge the other"
          % (kind, r["amount_usd"], authority["amount"]))
    check(r["amount_usd"] >= 28,
          "price_order(%s) at 3 inches = $%s, which is below the cheapest "
          "thing the shop sells" % (kind, r["amount_usd"]))
try:
    call("price_order", {"kind": "name-plus-port"})
    fails.append("price_order accepted a product we do not sell and quoted "
                 "a number for it")
except RuntimeError:
    pass
# A boat name is priced by the width it finishes at, so a quote without the
# lettering is a question the tool cannot answer. It must refuse rather than
# quote the cheapest band - that is the undercharge bug's shape.
try:
    q = call("price_order", {"kind": "name", "height": "3"})
    fails.append("price_order quoted $%s for a boat name without being told "
                 "what the name is - it cannot know the width, so that "
                 "figure is a guess" % q.get("amount_usd"))
except RuntimeError:
    pass
# The bundle discount, live. The site advertises a flat saving in four places.
_n = call("price_order", {"kind": "numbers", "height": "3"})["amount_usd"]
_m = call("price_order", dict(kind="name", height="3", **NAME_CASE))["amount_usd"]
_b = call("price_order", dict(kind="both", height="3", **NAME_CASE))["amount_usd"]
check(_b == _n + _m - 10,
      "the live bundle is $%s and the parts are $%s + $%s, so the saving is "
      "$%s and the site advertises $10" % (_b, _n, _m, _n + _m - _b))
print("prices: ok in every vocabulary, and they match /api/price")

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
# The accuracy figure is real here: this tool measures the registration
# NUMBER's own width, so there is something to be accurate about. The
# "+/-undefined%" only appeared when `number` itself was missing, which is
# the path validation now refuses at the boundary - the acc() guard stays as
# the second layer rather than the only one.
check(r["width"]["accuracy"] == "+/-1.5%",
      "the width accuracy is %r, not the measured +/-1.5%%"
      % r["width"]["accuracy"])
r = call("check_registration_layout", {"number": "IA 1234 AB", "height_in": 2})
check("33 CFR 173.27" in json.dumps(r),
      "a 2-inch registration number no longer cites the federal minimum")
print("argument boundary: ok")

# ---------------------------------------------------------------------------
# The transport. A connector that cannot be added is not a connector, and
# every one of these was wrong when the server was first called "live".
# ---------------------------------------------------------------------------
import urllib.error


def raw(method, path="/mcp", headers=None, body=None):
    # The user-agent is not optional. Without it Cloudflare bot management
    # answers urllib with its own 403 ("error code: 1010") - and the Origin
    # check below asserts a 403, so the whole transport block passed for the
    # wrong reason the first time it ran.
    h = {"user-agent": "nmb-live-check", **(headers or {})}
    req = urllib.request.Request(SITE + path, body, h, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


# GET and DELETE must be refused: this is a Streamable HTTP endpoint, there is
# no stream to open and no session to delete. GET used to answer 200 with a
# friendly JSON blob, which is neither a stream nor a refusal.
for meth in ("GET", "DELETE"):
    st, _ = raw(meth)
    check(st == 405, "%s /mcp returned %s, not 405" % (meth, st))
st, _ = raw("GET", "/mcp-info")
check(st == 200, "/mcp-info returned %s - the human-readable description "
                 "has nowhere to live" % st)

# Origin. A wildcard on an endpoint that writes is a standing invitation.
st, _ = raw("POST", headers={"content-type": "application/json",
                             "origin": "https://evil.example.com"},
            body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}')
check(st == 403, "a POST from an arbitrary website origin returned %s, not "
                 "403 - any page could open naming sessions in our database"
      % st)
st, _ = raw("POST", headers={"content-type": "application/json",
                             "origin": "https://claude.ai"},
            body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}')
check(st == 200, "a POST from claude.ai returned %s" % st)
st, _ = raw("POST", headers={"content-type": "application/json"},
            body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}')
check(st == 200, "a POST with no Origin at all returned %s - that is every "
                 "real MCP client" % st)

# The header mirror the current revision requires.
st, _ = raw("POST", headers={"content-type": "application/json",
                             "mcp-method": "tools/list"},
            body=b'{"jsonrpc":"2.0","id":1,"method":"tools/call",'
                 b'"params":{"name":"get_products"}}')
check(st == 400, "a Mcp-Method header contradicting the body returned %s - "
                 "a proxy routing on the header and this server acting on "
                 "the body would be two sources of truth" % st)
st, body = raw("POST", headers={"content-type": "application/json",
                                "mcp-protocol-version": "1999-01-01"},
               body=b'{"jsonrpc":"2.0","id":1,"method":"ping"}')
check(st == 400 and "supported" in body,
      "an unsupported protocol version returned %s without the supported "
      "list" % st)

# The version we claim. "2024-11-05" named the deprecated HTTP+SSE transport,
# which this server has never implemented.
for asked in ("2026-07-28", "2025-06-18"):
    st, body = raw("POST", headers={"content-type": "application/json",
                                    "mcp-protocol-version": asked},
                   body=('{"jsonrpc":"2.0","id":1,"method":"initialize",'
                         '"params":{"protocolVersion":"%s","capabilities":{},'
                         '"clientInfo":{"name":"probe","version":"1"}}}'
                         % asked).encode())
    got = json.loads(body)["result"]["protocolVersion"]
    check(got == asked,
          "client asked for %s and the server answered %s" % (asked, got))
print("transport: ok")

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
