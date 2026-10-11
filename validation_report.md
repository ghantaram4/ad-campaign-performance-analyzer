# Independent Cloud-readiness review

Reviewed October 11, 2026. The latest uploaded ZIP was inspected directly. The user selected a public demo with sample/non-confidential data on Streamlit Community Cloud.

## Final results

- **71 tests passed in 11.43 seconds** in a clean Python 3.12.14/Linux virtual environment.
- Exact runtime installed from `requirements.lock.txt`; `requirements.txt` now delegates to that audited lock. `pip check`: no broken requirements.
- Fresh pip-audit: **41 runtime packages, no known vulnerabilities found**. Full result: `validation/cloud-ready-dependency-audit.json`.
- Browser checks passed for four views, filters, empty states/reset, CSV/XLSX uploads, date resets, separate-tab session isolation, explicit/native CSV exports, inert uploaded markup and mobile width.
- No browser page errors or shared `/media/` export requests observed.
- Effective config: maxUploadSize=10, maxMessageSize=32, enableCORS=True, enableXsrfProtection=True, enableStaticServing=False, showErrorDetails=none.
- The bundled CSV is byte-for-byte unchanged from the uploaded ZIP. Dataset controls and metric definitions are unchanged.

## Changes in this review

1. Spaced CSV headers previously let pandas infer campaign ID `001` as `1`. The normalized headers are now used before applying the string ID dtype. Tests cover ordinary/spaced headers and literal search.
2. Paired chart legends previously omitted escaping applied by other chart helpers. Both paired traces now display uploaded markup as text. Tests/browser checks cover uploaded link markup.
3. Channel comparison could allocate all dates multiplied by all channels. A pre-allocation bound now caps this at 20,000 table/plot rows. Users receive a clear message to group more coarsely or narrow filters. Tests cover preserved totals/gaps, the bound and recovery to regular trends.
4. Community Cloud discovers requirements.txt, which previously pinned only direct dependencies. It now installs the complete audited transitive lock, verified on Linux/Python 3.12.
5. Deployment instructions now match the selected public Cloud setup. Added the non-confidential upload policy and a 32 MiB WebSocket message bound.

Ink & Coral styling, chart composition, four tabs, filtering, search, source data, conversion estimation and reported-ROI convention were preserved.

## Dataset controls

| Control | Verified value |
| --- | ---: |
| Campaigns | 60 |
| Spend | $29,490 |
| Clicks | 304,450 |
| Impressions | 5,450,000 |
| Estimated conversions | 61,361 |
| CTR | 5.59% displayed |
| Mean reported ROI | 3.8583333333333334 percentage points, 3.86% displayed |
| Source dates | January 5–July 29, 2024 |

The earlier project includes workbook/CSV parity evidence. This pass verifies the uploaded CSV is unchanged and re-runs CSV/XLSX parser parity fixtures; it does not claim a new comparison against the original Excel attachment.

## Browser evidence

`validation/cloud-ready-browser-results.json` records final checks. A pinned Streamlit server and headless Chromium ran locally on Linux. Separate pages used independent Streamlit/WebSocket sessions within one browser context. Authentication-cookie isolation was not tested because this public app has no login.

| Check | Result |
| --- | --- |
| Health endpoint | ok |
| Four views, empty filters/reset | Passed |
| CSV upload, spaced ID header/date resets | Passed |
| XLSX upload | Passed |
| Separate session data | Passed |
| Three explicit exports | Passed |
| Native CSV formula protection | Passed |
| Uploaded chart/table markup inert | Passed |
| Invalid schema without cell-value disclosure | Passed |
| Upload above 10 MiB | Rejected |
| 390-pixel viewport | No page overflow |
| Browser errors | None |
| Shared-media export requests | None |

Five screenshots show only the bundled sample data under `screenshots/`.

## Security scope

Existing regressions cover upload/row/column/cell bounds, numeric overflow, duplicate/ragged CSV structure, Excel expansion, DTD/entities, external links, formulas, deceptive dimensions, sparse coordinates, formula-safe exports, label escaping and session-local data. Source review found no untrusted eval/exec/pickle path or upload-content write.

The current heuristic secret scan scanned 34 text files and found no matching secret patterns or sensitive credential paths. It reports locations/rules only, not values. Full result: `validation/cloud-ready-secret-scan.json`. Scope excludes GitHub history, deployment secrets and credentials on the user's Windows machine. A clean advisory/secret scan is scoped evidence, not a penetration test.

## Deployment status

**Deployed on Streamlit Community Cloud on October 11, 2026.**

- Source: https://github.com/ghantaram4/ad-campaign-performance-analyzer
- Dashboard: https://ad-campaign-performance-analyzer.streamlit.app/
- Deployment settings: branch `main`, entrypoint `app.py`, Python 3.12, no application secrets.
- The app's sharing panel shows **Make this app public** enabled.

| Hosted check | Result |
| --- | --- |
| Four tabs and charts | Rendered successfully |
| Default overview | 60 campaigns; $29,490 spend; 304,450 clicks; 61,361 estimated conversions; 5.59% CTR; 3.86% reported ROI |
| Facebook filter | 15 campaigns and $8,570 spend |
| Empty channel selection and Reset | No-data message, then all 60 campaigns restored |
| Time grouping | Monthly selection updated the chart |
| Search C001 | One campaign and 504 estimated conversions |
| Sample CSV upload | Accepted; 60 uploaded campaigns |
| Campaign export data | Valid CSV data URL; expected 16-column header, 60 rows and original campaign IDs |
| App warnings/errors | None observed; browser-extension metadata errors appeared in the final browser logs |

The final log check showed errors from a browser-extension content script sending metadata, rather than from the dashboard's domain.

Automatic capture of the CSV download timed out; receipt of a saved file was not verified on the live host. The export link is present and both enclosing iframes allow downloads. XLSX upload, invalid/oversized-file rejection, mobile width, separate-session isolation and all export variants passed in the local review and were not repeated on the live host. No anonymous/incognito session or live load test was run.

Public viewing and sample/non-confidential uploads are intentional. No confidential-data access policy, custom global rate limiter, concurrent-session gate or load-test capacity guarantee is claimed.

Earlier Windows Codex evidence remains under `validation/security-*`, `validation/ink-coral-*`, `validation/dependency-audit.json` and `validation/secret-scan.json`. Those describe the earlier local review. Historical validation PNGs remain in the reviewed ZIP; the public repository includes the five current sample screenshots.
