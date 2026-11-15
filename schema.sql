CREATE TABLE IF NOT EXISTS orders (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  ref      TEXT NOT NULL,
  kind     TEXT, text TEXT, state TEXT, height TEXT, font TEXT, color TEXT,
  upgrades TEXT, name TEXT, email TEXT, phone TEXT, boat TEXT, notes TEXT,
  page     TEXT, total INTEGER, quoted INTEGER, mismatch INTEGER DEFAULT 0,
  ua       TEXT, country TEXT, ts TEXT NOT NULL,
  status   TEXT DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_orders_ts  ON orders(ts);
CREATE INDEX IF NOT EXISTS idx_orders_ref ON orders(ref);

-- Added with the Stripe checkout flow.
ALTER TABLE orders ADD COLUMN boatname TEXT;
ALTER TABLE orders ADD COLUMN paid INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN payment TEXT;

-- Sandbox checkout. card_last4/card_brand only; a full PAN is refused at the
-- API boundary and has no column here by design.
ALTER TABLE orders ADD COLUMN test_mode INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN card_brand TEXT;
ALTER TABLE orders ADD COLUMN card_last4 TEXT;

-- DORMANT. Added for a paid finish tier (colour / two-colour outline) that
-- was removed on 2026-10-30 when the colour picker was simplified to eight
-- colours, all included. Nothing writes these now. They are left in place
-- because dropping a column in SQLite means rebuilding the table, and the
-- rows written while the feature was live still carry real values.
ALTER TABLE orders ADD COLUMN finish TEXT DEFAULT 'standard';
ALTER TABLE orders ADD COLUMN outline_color TEXT;

-- ---------------------------------------------------------------------------
-- The proof cycle, added 2026-11-10.
--
-- Every order gets an emailed proof about twelve hours after it is placed,
-- then up to three reminders if nobody approves it. Nothing is cut until
-- approved_at is set. The timestamps are what the cron reads to decide who is
-- due, so they are the schedule - there is no queue anywhere else.
ALTER TABLE orders ADD COLUMN proof_token TEXT;
ALTER TABLE orders ADD COLUMN proof_sent_at TEXT;
ALTER TABLE orders ADD COLUMN proof_nudges INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN proof_nudged_at TEXT;
ALTER TABLE orders ADD COLUMN approved_at TEXT;
ALTER TABLE orders ADD COLUMN changes_at TEXT;
ALTER TABLE orders ADD COLUMN changes_note TEXT;
CREATE INDEX IF NOT EXISTS idx_orders_proof ON orders(approved_at, proof_sent_at);

-- ---------------------------------------------------------------------------
-- Font inventory reports, added 2026-11-11.
--
-- Ryan opens /fonts-check/ on the cutter PC and sends back what is installed,
-- so we know which of the site's faces he already has. Font names and a
-- browser string, nothing else - and only after he presses the button.
CREATE TABLE IF NOT EXISTS font_reports (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  ts       TEXT NOT NULL,
  who      TEXT,
  ua       TEXT,
  platform TEXT,
  method   TEXT,
  have     TEXT,
  missing  TEXT,
  all_sys  TEXT,
  picks    TEXT   -- "block:Block=Archivo Black | ...", the faces he wants offered
);

-- ---------------------------------------------------------------------------
-- Shipping address, added 2026-11-11.
--
-- The form collected a name and an email and nothing else, which meant every
-- order placed before today was unshippable - including a real one that had
-- already been approved. Collected by our own fields rather than Stripe's
-- Address Element on purpose: an address is required for the business to
-- function at all, so capturing it must not depend on a third party being up.
ALTER TABLE orders ADD COLUMN ship_line1 TEXT;
ALTER TABLE orders ADD COLUMN ship_line2 TEXT;
ALTER TABLE orders ADD COLUMN ship_city  TEXT;
ALTER TABLE orders ADD COLUMN ship_state TEXT;
ALTER TABLE orders ADD COLUMN ship_zip   TEXT;

-- Naming Engine sessions. Added with the MCP naming engine.
--
-- This is the first thing on the site that stores what somebody TOLD us rather
-- than what they ordered: a trade, a story, who is usually aboard. So it is
-- deliberately short-lived and deliberately not joined to anything.
--
--   * a random id, no account, no email, nothing that identifies a person
--   * never joined to an order; there is no foreign key and no column for one
--   * purged after 30 days by the scheduled handler
--   * harvest_optin defaults to 0, and nothing from a session may be used for
--     anything public without it (spec section 10)
--
-- The privacy policy had to change for this table to exist. It said "when you
-- send an order we collect what you typed into the form... that is it", which
-- would have been false the moment this stored a story about somebody's
-- father-in-law.
CREATE TABLE IF NOT EXISTS naming_sessions (
  id            TEXT PRIMARY KEY,
  ts            TEXT NOT NULL,
  updated       TEXT NOT NULL,
  answers       TEXT,                  -- JSON: the interview, as typed
  profile       TEXT,                  -- JSON: derived, what the ranker reads
  shown         TEXT,                  -- JSON: names already dealt
  killed_mechs  TEXT,                  -- JSON: mechanisms the customer rejected
  kept          TEXT,                  -- JSON: names the customer kept
  rounds        INTEGER DEFAULT 0,
  harvest_optin INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_ts ON naming_sessions(ts);

-- Tournament state. Added with the reveal.
ALTER TABLE naming_sessions ADD COLUMN killed_names TEXT;  -- JSON
ALTER TABLE naming_sessions ADD COLUMN kept_mechs TEXT;    -- JSON: what landed

-- Riffs the host model invented and the server gated, for this session only.
ALTER TABLE naming_sessions ADD COLUMN riffs TEXT;        -- JSON: survivors

-- ---------------------------------------------------------------------------
-- The performance ledger. Added with riff briefs.
--
-- What has actually been landing, per lane, per joke mechanism - and per bank
-- name, which is what picks the exemplars a riff brief shows the host model.
-- This is the only table on the site that learns.
--
-- IT HOLDS NOTHING PERSONAL, and that is load-bearing rather than incidental:
-- it is the one naming table that outlives the 30-day session purge, so it is
-- (lane, mechanism, three integers) and nothing else. No session id, no free
-- text, no column that could carry a story somebody told us. Riff TEXT never
-- reaches it either - a riff is built out of a man's wife, his dog or his
-- hometown, so a riff accrues to its mechanism's counters and its own words
-- stay in the session row that gets deleted.
--
-- Two sets of counters on purpose. The lifetime columns are the all-time
-- figure for the monthly review to show. The w_ columns are the window the
-- proven/unproven decision is actually made on, and the monthly review HALVES
-- them after it snapshots - an exponential decay with a one-month half-life,
-- because a lifetime keep-rate barely moves and a mechanism that stopped
-- landing in October would still read as proven in December.
CREATE TABLE IF NOT EXISTS ledger (
  kind         TEXT NOT NULL,          -- 'mech' | 'name'
  lane         TEXT NOT NULL,          -- style lane the customer asked for, or 'any'
  key          TEXT NOT NULL,          -- mechanism code, or the bank name
  exposures    INTEGER DEFAULT 0,
  keeps        INTEGER DEFAULT 0,
  kills        INTEGER DEFAULT 0,
  w_exposures  INTEGER DEFAULT 0,
  w_keeps      INTEGER DEFAULT 0,
  w_kills      INTEGER DEFAULT 0,
  updated      TEXT,
  PRIMARY KEY (kind, lane, key)
);

-- Monthly snapshots. The review is a DIFF - what crossed the threshold, what
-- decayed out - and a diff needs a previous state, so each review writes what
-- was proven at the moment it ran.
CREATE TABLE IF NOT EXISTS ledger_review (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  ts       TEXT NOT NULL,
  proven   TEXT,      -- JSON: { lane: [mechanism codes] }
  report   TEXT       -- JSON: the full review output, as the owner saw it
);
CREATE INDEX IF NOT EXISTS idx_ledger_review_ts ON ledger_review(ts);

-- ---------------------------------------------------------------- traffic
-- WHAT GA4 CANNOT SEE. GA4 is JavaScript, and a crawler does not run
-- JavaScript - so the entire question "is ChatGPT actually reading this
-- site" is invisible to it. This site is built to be quoted by answer
-- engines; this table is the only place that shows whether they came.
--
-- It also catches the other half: a human arriving FROM an answer engine.
-- Those do run JavaScript, so GA4 sees them too - but only if the referrer
-- survives, and several AI clients strip or rewrite it.
--
-- DELIBERATELY NOT A WEB LOG. It records a row only when the request is a
-- recognised crawler or carries a referrer worth knowing about; ordinary
-- human traffic writes nothing. That keeps it small, and it keeps it from
-- becoming a record of what individual people read.
--
-- `user_agent` IS ONLY EVER SET FOR A BOT. A crawler's user-agent is a
-- product name and worth keeping so a new one can be spotted and named in
-- AI_CRAWLERS. A person's user-agent is a fingerprinting surface and is
-- never written here - on a referral row that column stays NULL. There is
-- no IP column, by design, and no session or visitor id: two rows from the
-- same person cannot be joined.
--
-- Purged at 180 days by the hourly cron, like the naming sessions. A
-- retention promise nothing enforces is not a retention promise.
CREATE TABLE IF NOT EXISTS traffic_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  path TEXT NOT NULL,
  bot TEXT,                 -- the crawler's name, or NULL for a referral
  referer_host TEXT,        -- the answer engine that sent a person, or NULL
  country TEXT,
  user_agent TEXT           -- BOTS ONLY. NULL on every referral row.
);
CREATE INDEX IF NOT EXISTS idx_traffic_ts ON traffic_log(ts DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_bot ON traffic_log(bot);
CREATE INDEX IF NOT EXISTS idx_traffic_ref ON traffic_log(referer_host);

-- -------------------------------------------------------------- case study
-- The self-measurement tables behind /api/case-study.json, which aaron.chat
-- bakes into a live /work report. Created by the worker on first use too
-- (ensureCaseStudySchema), so this block is for a fresh database and for
-- anyone reading the schema to find out what exists.
--
-- Nothing here is personal. GSC gives aggregate query and day rows, the AI
-- citation counts are monthly totals, and the crawl side is read from
-- traffic_log rather than duplicated.
CREATE TABLE IF NOT EXISTS cs_gsc_daily (
  date TEXT PRIMARY KEY, clicks INTEGER NOT NULL DEFAULT 0,
  impressions INTEGER NOT NULL DEFAULT 0, position REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS cs_gsc_query (
  query TEXT PRIMARY KEY, clicks INTEGER NOT NULL DEFAULT 0,
  impressions INTEGER NOT NULL DEFAULT 0, position REAL NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cs_ai_monthly (
  month TEXT PRIMARY KEY, citations INTEGER NOT NULL DEFAULT 0,
  crawls INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cs_meta (
  k TEXT PRIMARY KEY, v TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Weekly third-party visibility sample (DataForSEO).
--
-- Search Console cannot answer "how many keywords does this domain rank for"
-- (a keyword we sit at #74 for produces no impressions worth reporting) and
-- knows nothing about who links to us. These two tables hold the answers, and
-- they are the only place the case-study feed's ranked_keywords_top_100 and
-- unique_referring_domains come from.
--
-- cs_rank_snap is keyed by date so the series is append-only and a second run
-- on the same day corrects that day rather than inventing a data point.
CREATE TABLE IF NOT EXISTS cs_rank_snap (
  date              TEXT PRIMARY KEY,
  ranked_top100     INTEGER NOT NULL DEFAULT 0,
  ranked_top10      INTEGER NOT NULL DEFAULT 0,
  ranked_top3       INTEGER NOT NULL DEFAULT 0,
  referring_domains INTEGER,
  backlinks         INTEGER,
  domain_rank       INTEGER
);

-- The current picture only. History lives in cs_rank_snap; every keyword at
-- every position for ever would be a different product.
CREATE TABLE IF NOT EXISTS cs_rank_kw (
  keyword    TEXT PRIMARY KEY,
  position   INTEGER NOT NULL,
  volume     INTEGER,
  url        TEXT,
  updated_at TEXT NOT NULL
);

-- Auto-approval after five business days (2026-11-15).
--
-- number_flag is the validator's verdict AT ORDER TIME. '' means checked and
-- clean, NULL means never checked - and the sweep refuses NULL, which is what
-- keeps it away from every row placed before this existed.
ALTER TABLE orders ADD COLUMN number_flag TEXT;
-- The checkbox at checkout. 0 (the default) means the five-day rule applies.
ALTER TABLE orders ADD COLUMN auto_cut_optout INTEGER DEFAULT 0;
-- Set alongside approved_at, so an auto-approval is always distinguishable
-- from a customer who actually clicked the button. Ryan needs to know which
-- he is holding before he cuts.
ALTER TABLE orders ADD COLUMN auto_approved_at TEXT;
-- Resend's message id for the proof. The deadline runs off whether THIS
-- message was delivered, which cannot be asked later without its id.
ALTER TABLE orders ADD COLUMN proof_msg_id TEXT;
