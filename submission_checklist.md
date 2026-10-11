# Week 1 submission checklist

## Included in this package

- [x] Streamlit application with Overview, Platform Comparison, Campaign Details and Time Series.
- [x] Global date, channel, target audience, campaign goal and customer segment filters.
- [x] Source-driven dates, reset, and explicit empty results.
- [x] USD and percentage units, estimated conversions, reported ROI definitions.
- [x] Searchable/sortable campaign table and acquisition funnel.
- [x] Daily/weekly/monthly trends and channel comparison.
- [x] Bundled source CSV, upload handling and CSV exports.
- [x] Setup instructions, development log and automated tests.
- [x] Five updated screenshots and an independent validation report.
- [x] 71 passing tests and a fresh 41-package dependency audit.
- [x] Streamlit Cloud settings and pinned transitive dependencies.

## Complete before submitting

- [x] Run the uploaded/updated app in isolated Linux/Python 3.12.
- [ ] Use this reviewed version for further laptop development.
- [x] Create/push the source repository with the project files.
- [ ] Deploy app.py using Python 3.12 and requirements.txt, which includes the audited lock.
- [ ] Verify the deployed app's default metrics, filters, empty state, uploads and exports.
- [ ] Check every screenshot and replace any that need to reflect the deployed version.
- [ ] Add the real repository URL and deployment URL below.
- [ ] Confirm additional Week 1 deliverables against your course rubric.

Repository URL: https://github.com/ghantaram4/ad-campaign-performance-analyzer

Dashboard URL: ____________________

## Selected deployment route

Public demo on Streamlit Community Cloud. DEPLOYMENT.md provides the exact GitHub upload, Python 3.12, app.py entrypoint, sharing and live-check steps. No secrets are needed. Cloud provides HTTPS and compute quotas; the application bounds inputs and chart expansion. Live deployment is pending.

## Suggested demonstration

1. Show the unfiltered overview: $29,490 spend, 304,450 clicks, 61,361 estimated conversions and 3.86% mean reported ROI.
2. Select Facebook: every tab updates; spend becomes $8,570.
3. Apply audience, goal and date filters, then clear the channel selection to show the empty state.
4. Reset filters. Search C001 and show its table/funnel; overview totals stay global.
5. Compare CPA or ROI across channels, then change Time Series from monthly to weekly and enable channel comparison.
6. Download filtered campaigns and demonstrate upload of a valid campaign file.
