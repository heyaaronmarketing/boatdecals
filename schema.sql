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
