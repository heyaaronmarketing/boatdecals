-- FABRICATED DATA. LOCAL D1 ONLY. NEVER --remote.
--
-- Production's ledger will be cold for months, and the warm path - proven
-- mechanisms, real keep-rate ordering on the exemplars, the exploration slot -
-- is the entire feature. This seeds a deadpan lane that looks like it has seen
-- traffic, so the warm path can be exercised end to end against a real worker
-- with real D1 reads rather than only in unit tests.
--
-- Every number in here is invented. Loading it into the real database would
-- make the brief tell customers that invented evidence is "keep-rate in real
-- sessions", which is the one sentence the whole design is built to keep true.
-- The file name ends in .local.sql so that it reads wrong in a --remote
-- command, and this header is here so it reads wrong even then.
--
--   npx wrangler d1 execute boatnumbershop --local --file=schema.sql
--   npx wrangler d1 execute boatnumbershop --local \
--     --file=mcp/fixtures/warm-ledger.local.sql
--   npx wrangler r2 object put nmb-fonts/lexicon.txt.gz \
--     --file=mcp/data/lexicon.txt.gz --local
--   npx wrangler dev --port 8798
--
-- Four mechanisms past the 30-exposure threshold: dp and lt landing, hp and
-- md not, pm still short of the threshold. That makes dp/lt proven, hp/md
-- bottom-half, pm exploration.
DELETE FROM ledger;
INSERT INTO ledger (kind,lane,key,exposures,keeps,kills,w_exposures,w_keeps,w_kills,updated) VALUES
  ('mech','deadpan','dp',420,96,324,420,96,324,'seed'),
  ('mech','any','dp',420,96,324,420,96,324,'seed'),
  ('mech','deadpan','lt',380,74,306,380,74,306,'seed'),
  ('mech','any','lt',380,74,306,380,74,306,'seed'),
  ('mech','deadpan','hp',350,19,331,350,19,331,'seed'),
  ('mech','any','hp',350,19,331,350,19,331,'seed'),
  ('mech','deadpan','md',300,11,289,300,11,289,'seed'),
  ('mech','any','md',300,11,289,300,11,289,'seed'),
  ('mech','deadpan','pm',22,8,14,22,8,14,'seed'),
  ('mech','any','pm',22,8,14,22,8,14,'seed');
-- Per-name keep data, so the exemplars are ordered by keep-rate for real.
INSERT INTO ledger (kind,lane,key,exposures,keeps,kills,w_exposures,w_keeps,w_kills,updated) VALUES
  ('name','any','Mortality Barge',60,22,38,60,22,38,'seed'),
  ('name','any','Tuesday Boat',60,14,46,60,14,46,'seed'),
  ('name','any','Mild Wake',55,6,49,55,6,49,'seed'),
  ('name','any','Loading…',58,21,37,58,21,37,'seed'),
  ('name','any','Pending',50,9,41,50,9,41,'seed'),
  ('name','any','Actual In',40,3,37,40,3,37,'seed');
