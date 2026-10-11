# Development log

## Actual user requests

1. Build the Week 1 Ad Campaign Performance Analyzer: four views, shared filters, metrics with units, empty-state handling, and documentation of prompts, bugs and iterations.
2. Inspect the uploaded solution kit and source dataset.
3. Investigate the dates displayed as `########` in Excel. The prior conversation identified column width as the display issue. This build preserved the source dates and independently checked the CSV against the workbook.
4. Decide whether to build a model or dashboard first. The agreed approach was to build data preparation and analytics first, then Streamlit. No machine-learning model is required.
5. Start implementation: “okay lets start doing”.

## Implementation brief used by the coding assistant

The following is a record of the implementation specification derived from those requests, not a claim that the user typed this exact prompt:

> Build an independent Python/Streamlit dashboard from the supplied workbook. Bundle a faithful CSV conversion. Validate the 16-column schema, parse source dates, clean Acquisition_Cost to USD Spend, extract Duration_Days and derive rounded conversions. Use reusable analytics functions and summed numerators/denominators. Render Overview, Platform Comparison, Campaign Details and Time Series from one globally filtered DataFrame. Add source-driven date bounds, channel/audience/goal/segment selectors, reset, explicit empty states, search, a readable acquisition funnel, daily/weekly/monthly controls, Top 5 by reported ROI and CSV exports. Identify conversions as estimated and ROI as reported. Document the kit's percentage-point assumption. Test real controls, malformed input, zero denominators, filter interactions and aggregation reconciliation. Preserve Streamlit's security defaults.

## Iterations and checks

### 1. Source inspection

- Read the 13-page solution kit and inspected the workbook's Campaign Data worksheet.
- Confirmed 60 rows, 16 columns, four channels, no missing cells, and dates from 2024-01-05 to 2024-07-29.
- Noted that Acquisition_Cost is already numeric in this workbook, although the kit describes dollar strings. The loader supports both forms.
- Exported the workbook to CSV with ISO dates, without changing values.

### 2. Analytics

- Separated cleaning/validation from totals and UI.
- Computed conversions per campaign before summing.
- Added independent expected dataset totals and checks that platform/time totals reconcile.
- Used aggregate rates to prevent incorrect averaging of row-level ratios.
- Retained source ROI values and displayed percentages according to the kit. Revenue-based ROI cannot be established from this data.

### 3. Dashboard

- Added four tabs and one shared filter result in `main()`.
- Added target-audience and customer-segment selectors, source-bound dates and reset.
- Added separate spend/conversion axes, per-channel comparisons, search, funnel, trend controls and exports.
- Kept source-change state tied to file-content hashes so new uploads get new date bounds and category defaults.

### 4. Issues observed and resolved

| Issue | Cause | Resolution / evidence |
| --- | --- | --- |
| Initial source-vs-CSV check failed on Date dtype | The Excel reader returned strings while the CSV comparison parsed datetimes | Normalized the Excel dates to ISO text for the comparison; every row and column matched |
| pandas warnings in mixed-format input test | The test inserted currency and percentage strings into numeric columns | Made those test columns object dtype before insertion; production cleaning was unaffected |
| Runtime dependency range did not include the installed Plotly version | Initial draft requested Plotly below version 7 | Pinned runtime dependencies to the actual tested versions |
| Browser download unavailable through the usual Playwright route | The download returned an invalid archive in this environment | Recorded as a test-environment issue; browser verification details are in validation_report.md |
| Conversion-stage text invisible inside the funnel | The conversion count is much smaller than impressions | Visual review identified the issue; moved labels outside the funnel and reviewed the corrected screenshot |

### 5. Reference defects prevented

The kit's hardcoded date range, missing ROI unit, clipped funnel labels and zero-row crashes were treated as acceptance cases. They were not invented as bugs encountered in this build. Dates come from the loaded source, formatting is centralized, funnel stage counts also appear as cards, and every tab guards empty results.

## Remaining submission work

Run on the user's laptop, push source to a remote repository, deploy to a suitable Streamlit host, and add real source/deployment links to the submission checklist. The exact course-wide Week 1 rubric was not supplied, so confirm additional submission requirements against that rubric. Browser checks subsequently verified CSV and Excel uploads, changed date bounds, malformed-file errors, campaign downloads and all four rendered views.

## October 11, 2026 — chart refinement

Implemented requested Ink & Coral styling after inspecting all four supplied screenshots. Added paired metric charts with separate axes, Weekly defaults and responsive stacking, slim bars, thin straight lines, light count/spend fills, clean value hovers and stable channel colours. Aggregation and source data remain unchanged. All 42 tests pass; local Chrome review of four tabs and phone width found no page errors or horizontal page overflow. Dashboard remains available on port 8502. See validation_report.md and validation/ink-coral-* for evidence and runtime limitations.

## October 11, 2026 — pre-deployment hardening

Implemented content-aware CSV/XLSX parsing with a 10 MB envelope, row/column/cell and numeric bounds, ZIP expansion checks, defused XML preflight and sparse-coordinate rejection. Removed shared upload caching in favor of session state. Escaped chart labels and protected formula-like CSV text in both explicit and native table downloads. Explicit exports now stay in the browser to avoid shared media endpoints. Enabled CORS/XSRF explicitly, disabled static serving and hid browser error details. Added security regressions and locked the audited runtime: 41 packages, no known advisory findings. All 65 tests and real Chrome workflow checks pass. See DEPLOYMENT.md and validation_report.md for complete evidence, deployment steps and remaining hosting requirements.

## Independent uploaded-project review — October 11, 2026

The user uploaded the updated clean ZIP and selected a public sample-data demo on Streamlit Community Cloud. Reproduced the original 65 tests in isolated Linux/Python 3.12 and repeated the 41-package audit. Fixed spaced CSV headers losing leading-zero campaign IDs and paired legends omitting escaping. Bounded channel/date expansion before allocation and WebSocket messages to 32 MiB. requirements.txt now includes the audited lock. Six additional regression cases bring the total to 71 passing tests. Final browser checks passed. Deployment instructions describe the selected Cloud setup. Data, analytics and Ink & Coral styling are preserved. Account sign-in, publication and live-host verification are pending.


## GitHub publication — October 11, 2026

Published the reviewed application, sample dataset, tests, configuration and validation reports to https://github.com/ghantaram4/ad-campaign-performance-analyzer. The five current sample screenshots are included. Older validation images are retained in the reviewed ZIP and excluded from the public repository. Streamlit Cloud deployment and live verification remain pending.
