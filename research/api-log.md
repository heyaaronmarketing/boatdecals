# DataForSEO API log

Every paid call this repo has made, with its cost and the raw response it produced.
An identical endpoint+payload is a cache hit and is never paid for twice.

| When | Endpoint | Label / params | Status | Cost $ | Raw file |
|---|---|---|---|---|---|
| 2026-11-14 14:58 | `appendix/user_data` |  | 20000 Ok. | 0 | `(not cached: account response)` |
| 2026-11-14 14:59 | `keywords_data/google_ads/search_volume/live` | money-terms-recheck | 20000 Ok. | 0.09 | `keywords-data-google-ads-search-volume-live__money-terms-recheck__2026-11-14.json` |
| 2026-11-16 02:34 | `keywords_data/google_ads/search_volume` | requirements-vs-fees | 404 { "version": "0.1.20261103", "status_code": 40400, "status_message": "Not Fo | 0 | `(not cached: failed)` |
| 2026-11-16 02:35 | `keywords_data/google_ads/search_volume/live` | requirements-vs-fees | 20000 Ok. | 0.09 | `keywords-data-google-ads-search-volume-live__requirements-vs-fees__2026-11-16.json` |
| 2026-11-16 05:05 | `appendix/user_data` |  | 20000 Ok. | 0 | `(not cached: account response)` |
| 2026-11-16 05:05 | `keywords_data/google_ads/search_volume/live` | states-phase2 | 20000 Ok. | 0.09 | `keywords-data-google-ads-search-volume-live__states-phase2__2026-11-16.json` |
| 2026-11-16 07:56 | `keywords_data/google_ads/search_volume/live` | brand-honest-intent | 20000 Ok. | 0.09 | `keywords-data-google-ads-search-volume-live__brand-honest-intent__2026-11-16.json` |
| 2026-11-16 07:57 | `keywords_data/google_ads/search_volume/live` | vessel-expansion | 20000 Ok. | 0.09 | `keywords-data-google-ads-search-volume-live__vessel-expansion__2026-11-16.json` |
