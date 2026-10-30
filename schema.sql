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

-- The paid finishes. `finish` is one of standard / colour / outline and is
-- what priceOf() charges for; `outline_color` is the second layer of vinyl
-- and is only set when finish = 'outline'.
ALTER TABLE orders ADD COLUMN finish TEXT DEFAULT 'standard';
ALTER TABLE orders ADD COLUMN outline_color TEXT;
