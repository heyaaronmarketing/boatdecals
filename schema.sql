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
