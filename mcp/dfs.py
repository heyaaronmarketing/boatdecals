"""Minimal DataForSEO client for this repo: cached, cost-logged, on purpose.

STRATEGY.md says "all volumes from live DataForSEO pulls, 2026-10-22, re-pull
before acting on anything here in six months" - and until now there was no
script to re-pull with and no raw responses kept, so none of it was checkable.
This is that script.

RUN IT BY HAND. The worker's weekly cron samples rankings and backlinks, which
cannot be backfilled; it deliberately does NOT touch search volumes. A job that
rewrote the volumes STRATEGY.md reasons from, every Monday, would change the
premises of a document without anyone deciding to.

Credentials: DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD from the environment, or
from a .env beside this repo root. Never committed - .env is gitignored.

Every call is saved to research/raw/<endpoint>__<label>__<date>.json and logged
to research/api-log.md with its cost. An identical endpoint+payload is never
paid for twice (cache hit). The account is PREPAID: check the balance first.

    python3 mcp/dfs.py appendix/user_data
    python3 mcp/dfs.py keywords_data/google_ads/search_volume \
        '{"keywords":["boat registration numbers"],"location_code":2840}' vol-check
"""
import base64, hashlib, json, os, re, sys, time, urllib.request, urllib.error
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "research", "raw")
LOG = os.path.join(ROOT, "research", "api-log.md")
INDEX = os.path.join(RAW, "_cache-index.json")
BASE = "https://api.dataforseo.com/v3/"
TODAY = date.today().isoformat()
US = 2840  # location_code for the United States - this shop ships to all 50.


def _env():
    l = os.environ.get("DATAFORSEO_LOGIN")
    p = os.environ.get("DATAFORSEO_PASSWORD")
    if l and p:
        return l, p
    # A .env at the repo root, then one canonical file in the home directory.
    # The home file is there so the same account is not copied into a dozen
    # repos, each of which is one .gitignore mistake away from publishing it.
    for envf in (os.path.join(ROOT, ".env"),
                 os.path.expanduser("~/.dataforseo.env")):
        if not os.path.exists(envf):
            continue
        env = {}
        for line in open(envf):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k.strip()] = v.strip()
        if env.get("DATAFORSEO_LOGIN") and env.get("DATAFORSEO_PASSWORD"):
            return env["DATAFORSEO_LOGIN"], env["DATAFORSEO_PASSWORD"]
    sys.exit("Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD - in the "
             "environment, in a .env at the repo root, or once in "
             "~/.dataforseo.env (chmod 600).")


def _auth():
    l, p = _env()
    return "Basic " + base64.b64encode(f"{l}:{p}".encode()).decode()


def _index():
    return json.load(open(INDEX)) if os.path.exists(INDEX) else {}


def _slug(s):
    return re.sub(r"[^a-zA-Z0-9.-]+", "-", s).strip("-")[:90]


def call(endpoint, payload=None, label="", method="POST"):
    """POST a single-task payload (dict) or list. Returns parsed JSON (cached)."""
    os.makedirs(RAW, exist_ok=True)
    body = None if payload is None else json.dumps(payload if isinstance(payload, list) else [payload])
    key = hashlib.sha1(f"{endpoint}|{body}".encode()).hexdigest()
    idx = _index()
    if key in idx and os.path.exists(os.path.join(RAW, idx[key])):
        return json.load(open(os.path.join(RAW, idx[key])))
    req = urllib.request.Request(BASE + endpoint, data=body.encode() if body else None,
                                 method=method if body else "GET",
                                 headers={"Authorization": _auth(), "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            data = {"status_code": e.code, "status_message": e.read().decode()[:500], "cost": 0, "tasks": []}
            break
        except Exception as e:  # network
            if attempt == 2:
                data = {"status_code": -1, "status_message": str(e), "cost": 0, "tasks": []}
            time.sleep(3)
    # appendix/user_data echoes the ACCOUNT back - login email included - and
    # this repo is public. It is a free call, so it is never cached to disk.
    if endpoint.startswith("appendix/"):
        _log(endpoint, label, data, "(not cached: account response)")
        return data
    fname = f"{_slug(endpoint.replace('/', '_'))}__{_slug(label) or key[:8]}__{TODAY}.json"
    if os.path.exists(os.path.join(RAW, fname)):
        fname = fname.replace(".json", f"__{key[:6]}.json")
    # A FAILED call must never enter the cache. The ported version of this
    # client cached everything, so a 404 from a mistyped endpoint came back
    # from disk for ever and looked like an empty result - which is how you
    # end up reporting that a keyword has no search volume because you spelled
    # the endpoint wrong. Proven: the first money-term pull here 404'd on a
    # missing /live suffix and was served from cache on the retry.
    _t = (data.get("tasks") or [{}])[0]
    if _t.get("status_code") != 20000:
        _log(endpoint, label, data, "(not cached: failed)")
        return data
    # These files are committed, and the repo is public. A keyword response
    # has no business carrying an email address, so if one appears - in a SERP
    # snippet, in a WHOIS field, in an account echo - it is redacted on the
    # way to disk rather than discovered later by whoever reads the repo.
    blob = _no_emails(json.dumps(data, indent=1))
    open(os.path.join(RAW, fname), "w").write(blob)
    idx[key] = fname
    json.dump(idx, open(INDEX, "w"), indent=1)
    _log(endpoint, label, data, fname)
    return data


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _no_emails(s):
    return EMAIL_RE.sub("<redacted-email>", s)


def _log(endpoint, label, data, fname):
    t = (data.get("tasks") or [{}])[0]
    # Collapsed to one line: DataForSEO returns a multi-line JSON blob as the
    # status_message on some errors, and a newline inside a markdown table
    # cell destroys the table.
    status = " ".join(str(f"{t.get('status_code', data.get('status_code'))} "
                          f"{t.get('status_message', data.get('status_message'))}").split())
    first = not os.path.exists(LOG)
    with open(LOG, "a") as f:
        if first:
            f.write("# DataForSEO API log\n\nEvery paid call this repo has "
                    "made, with its cost and the raw response it produced.\n"
                    "An identical endpoint+payload is a cache hit and is never "
                    "paid for twice.\n\n"
                    "| When | Endpoint | Label / params | Status | Cost $ | Raw file |\n|---|---|---|---|---|---|\n")
        f.write(f"| {time.strftime('%Y-%m-%d %H:%M')} | `{endpoint}` | {label} | {status[:80]} | {data.get('cost', 0)} | `{fname}` |\n")


def result(data, i=0):
    """First task's result list (or [])."""
    try:
        return data["tasks"][i]["result"] or []
    except (KeyError, IndexError, TypeError):
        return []


def task_ok(data, i=0):
    try:
        return data["tasks"][i]["status_code"] == 20000
    except (KeyError, IndexError, TypeError):
        return False


if __name__ == "__main__":
    print(json.dumps(call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else ""), indent=1)[:3000])
