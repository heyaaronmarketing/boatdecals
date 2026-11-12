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
