# Ad Campaign Performance Analyzer

A Streamlit dashboard for comparing campaign spend, clicks, estimated conversions and reported ROI across Facebook, Instagram, Pinterest and Twitter. It loads the supplied 60-campaign dataset immediately and accepts CSV or Excel uploads with the same schema.

## Run on Windows

Install Python 3.12, extract the ZIP, open the project folder in VS Code, and open a PowerShell terminal in that folder. Then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed in the terminal, usually http://localhost:8501. Keep the terminal running. No API key, database or model training is required.

## Run on macOS or Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Python 3.12/Linux was independently verified for the selected Streamlit Cloud demo. The earlier Windows review used Python 3.13. Runtime dependencies are pinned in requirements.lock.txt, included by requirements.txt.

## Dashboard views

| View | Features |
| --- | --- |
| Overview | Spend, clicks, estimated conversions, CTR and mean reported ROI; weekly initial grouping with Daily/Weekly/Monthly options; slim spend bars and conversion line with separate axes; paired clicks/conversions and CTR/CVR charts; Top 5 campaigns by reported ROI; CPC, CPA and CVR |
| Platform Comparison | Metric selector, channel comparison chart, aggregate metric table, CSV export |
| Campaign Details | Literal, case-insensitive search, native column sorting, per-campaign metrics, CSV export, acquisition funnel |
| Time Series | Daily, weekly (initial) and monthly groups; paired clicks/conversions and CTR/CVR charts with separate axes; metric selector; channel comparison; aggregate table; CSV export |

Global date, channel, target audience, campaign goal and customer segment filters apply to every view. Reset restores the full source range and all categories. Clearing a category produces an explicit empty state. Campaign search is local to Campaign Details and also filters its funnel and export.

## Source data and definitions

`data/social_media_advertising_sample.csv` was converted from the user's `Ad Campaign Performance Dataset.xlsx`. All 60 records and all 16 original columns were checked against the workbook. Dates remain January 5 through July 29, 2024. CSV files do not store Excel column widths; `########` in Excel is usually a display issue. If the characters are literally saved in the CSV instead of dates, the app rejects them.

One row represents one complete campaign. The date groups whole campaign outcomes, not daily ad delivery. The app does not spread campaign totals over duration. Weekly groups start Monday. Dates without recorded campaigns are omitted. Missing channel periods remain gaps rather than fabricated zero outcomes.

| Metric | Formula / unit |
| --- | --- |
| Spend | Sum of cleaned Acquisition_Cost, USD |
| Estimated conversions | For each row, round(Clicks × Conversion_Rate), then sum; nearest integer, ties to even |
| CTR | Sum(Clicks) ÷ Sum(Impressions), displayed as % |
| CPC | Sum(Spend) ÷ Sum(Clicks), USD per click |
| CPA | Sum(Spend) ÷ Sum(estimated conversions), USD per conversion |
| CVR | Sum(estimated conversions) ÷ Sum(Clicks), displayed as % |
| Average reported ROI | Arithmetic mean of the supplied ROI values, displayed as percentage points |

The solution kit explicitly appends `%` to the ROI field, so a raw value of `3.2` displays as `3.20%`. The workbook does not independently document whether these values represent percentage points or a return multiple. This implementation follows the kit's percentage convention and identifies ROI as reported. It does not infer revenue, calculate portfolio ROI, or weight campaign ROI by spend. If the data owner confirms a multiplier convention, update labels and formatting before using the dashboard for financial decisions.

N/A means a ratio has a zero denominator. Zero spend is valid; missing or invalid spend is rejected. All aggregate ratios use totals rather than means of per-campaign ratios.

### Required upload schema

```text
Campaign_ID, Target_Audience, Campaign_Goal, Duration, Channel_Used,
Conversion_Rate, Acquisition_Cost, ROI, Location, Language, Clicks,
Impressions, Engagement_Score, Customer_Segment, Date, Company
```

Upload a UTF-8 CSV or an `.xlsx` workbook with headers in the first row of its first worksheet. Column order can vary. Extra columns are ignored. Required columns cannot be missing; campaign IDs must be unique and category values cannot be blank.

- Acquisition_Cost accepts `420`, `420.50`, or `$1,420.50`. Currency is USD.
- Conversion_Rate accepts decimals such as `0.12`, or percentage text such as `12%`. Numeric `12` is rejected.
- ROI accepts finite numeric values or percent text. Its raw value is treated as percentage points.
- Date accepts `YYYY-MM-DD` or native Excel dates. Ambiguous dates such as `01/05/2024` are rejected.
- Duration accepts a positive whole number or a label such as `15 Days`.
- Clicks and impressions must be non-negative whole counts; clicks cannot exceed impressions.

Malformed uploads show the cause and stop rendering that source. Records are not silently dropped and invalid spend is not turned into zero. Changing a source resets the global filters to the new source bounds.

## Verified dataset totals

| Metric | Expected result |
| --- | ---: |
| Campaigns | 60 |
| Spend | $29,490.00 |
| Clicks | 304,450 |
| Impressions | 5,450,000 |
| Estimated conversions | 61,361 |
| CTR | 5.59% |
| CPC | $0.10 |
| CPA | $0.48 |
| CVR | 20.15% |
| Mean reported ROI | 3.86% |

Ratios use full precision before display rounding. These are dataset outputs, not industry benchmarks.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

On macOS/Linux, replace the executable with `.venv/bin/python`. Tests cover independent dataset controls, currency cleaning, conversions, source validation, weighted rates, zero denominators, CSV/Excel parity, aggregation reconciliation, source preservation, and Streamlit interactions. See `validation_report.md` for the completed checks.

## Project structure

- `app.py`: Streamlit UI, session-local loading, source state, shared filters and four views.
- `utils/data_processing.py`: file loading, schema validation, transformations, filters and search.
- `utils/metrics.py`: totals, derived ratios and platform/time aggregation.
- `utils/charts.py`: Plotly chart generation and shared styling.
- `data/social_media_advertising_sample.csv`: faithful CSV copy of the supplied workbook.
- `tests/`: analytics tests and Streamlit AppTest interactions.
- `development_log.md`: actual requests, implementation choices, issues and fixes.
- `submission_checklist.md`: submission items and deployment steps.

## Deploy

The selected host is Streamlit Community Cloud for a public sample-data demo. Follow [DEPLOYMENT.md](DEPLOYMENT.md) to upload the extracted project contents to GitHub and deploy branch `main`, entrypoint `app.py`, with Python 3.12. requirements.txt includes the audited transitive lock. No secrets are needed. A public GitHub repository also makes the source and bundled dataset public. Source repository: [ghantaram4/ad-campaign-performance-analyzer](https://github.com/ghantaram4/ad-campaign-performance-analyzer). The live Cloud deployment is pending.

## References

Requirements and reference method: the user's `Oct Week 1_ Ad Campaign Performance Analyzer Solution Kit.pdf`, especially dataset transformations, four views, common defects and shared filter architecture. The application is independently implemented with separate analytics modules, strict input validation, additional audience filters, CSV/Excel uploads and exports.

Streamlit API references checked during development:
- https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
- https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.numbercolumn

## Visualization design

Ink & Coral uses a dark ink sidebar, warm off-white canvas, white panels, coral and teal outcome series, and stable channel colours. Charts use straight thin lines, observed period markers, subtle count/spend fills, and slim bars. Paired plots label both axes; channel comparisons use solid lines for the left metric and dotted lines for the right. On narrow screens, chart panels stack. Rates continue to use grouped totals.

## Pre-deployment security review

See [DEPLOYMENT.md](DEPLOYMENT.md) for the reviewed installation, upload limits, session isolation, export protection, audit evidence and hosting requirements. Uploads are limited to 10 MB and 10,000 rows; XLSX expansion is bounded and Excel formulas must be exported as values. CSV exports protect formula-like text, including dataframe toolbar downloads. The audited runtime resolution is pinned in requirements.lock.txt.

## Independent Cloud-readiness review

71 tests passed on Linux/Python 3.12, browser checks passed, and a fresh 41-package audit found no known vulnerabilities. Spaced CSV headers preserve numeric-looking campaign IDs, paired chart labels escape uploaded markup, and channel/date comparisons are bounded before expansion. The sample dataset and analytics are unchanged. See validation_report.md for the exact scope. This public demo accepts sample/non-confidential uploads; private business data needs restricted hosting access.
