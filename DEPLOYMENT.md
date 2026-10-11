# Deploy the public demo on Streamlit Community Cloud

Selected October 11, 2026: public viewing, sample/non-confidential campaign data, Streamlit Community Cloud. No API key, database or login feature is needed for this demo. Python 3.12/Linux was verified locally; the live deployment is still pending.

Source repository: https://github.com/ghantaram4/ad-campaign-performance-analyzer

## Upload the extracted project to GitHub

1. Extract the ZIP. Open the inner `Ad_Campaign_Performance_Analyzer` folder containing `app.py`.
2. Create a GitHub repository named `ad-campaign-performance-analyzer`.
3. Upload the **contents** of that inner folder, preserving directories. Do not upload the ZIP itself as the application.
4. Verify these files exist at the repository root or in the indicated directories:

- `app.py`
- `utils/`, including every helper
- `data/social_media_advertising_sample.csv`
- `.streamlit/config.toml`
- `requirements.txt` and `requirements.lock.txt`

For the simplest public demo, use a public repository. This also publishes the source and bundled sample dataset. A private source repository is supported but needs additional Streamlit GitHub access and an explicit public-app sharing setting.

VS Code Source Control can initialize, commit and publish the extracted folder to GitHub. If using the GitHub web uploader, verify that `.streamlit/config.toml` is included afterward: it preserves the theme and upload/security settings. Documentation, tests and sample screenshots may be included. Do not commit virtual environments, credentials, caches or private uploads; these generated/private items are excluded from this package.

## Create the Cloud app

1. Sign in at https://share.streamlit.io/ and connect the GitHub account owning the repository.
2. Click **Create app**, then **Yup, I have an app** if prompted.
3. Choose the repository, branch `main`, and main file path `app.py`.
4. In **Advanced settings**, select **Python 3.12**.
5. Leave Secrets empty. Save and deploy.
6. Keep the resulting actual `https://...streamlit.app/` URL.
7. In App settings → Sharing, confirm public viewing.

Cloud detects `requirements.txt`, which includes the complete audited `requirements.lock.txt`. It therefore installs the verified transitive versions. No system `packages.txt` is needed. The config must be at `.streamlit/config.toml` in the repository root, even if using a different entrypoint location.

## Resolve the hosting concerns

| Concern | Selected public-demo setup |
| --- | --- |
| HTTPS | Community Cloud serves apps over HTTPS and HSTS. Verify the resulting URL and browser upload/WebSocket connections after deployment. No self-signed certificate or custom proxy is needed. |
| Access control | Public viewing and non-confidential uploads were selected. The sidebar states this policy. This is not a confidential-data deployment. For future private business data, configure Cloud private-app access and verify it before uploading. |
| Resources | Cloud manages CPU/memory quotas. The app bounds uploads, parsed records, categories, Excel expansion, WebSocket messages and channel/date comparison expansion. View current workspace quotas under Workspace settings → Limits. |

No custom global rate limiter, concurrent-session gate or CPU quota controls are implemented. Cloud does not expose the same controls as a self-managed server. This is a modest public assignment demo; live traffic capacity has not been load-tested.

## Verify the actual live URL

In an incognito browser, check:

- Four tabs, dark sidebar, coral/teal charts and initial Weekly grouping.
- 60 campaigns, $29,490 spend, 304,450 clicks, 61,361 estimated conversions, 5.59% CTR and 3.86% mean reported ROI.
- Facebook filter: $8,570 spend across the same filtered population in every tab.
- Clearing Channel shows empty states; Reset restores the original data.
- Search `C001`: one campaign and 504 estimated conversions; the export retains `C001`.
- Sample CSV/XLSX upload, source date resets, invalid-schema feedback and rejection above 10 MiB.
- Two independent sessions retain separate upload data.
- All three explicit exports and native table CSV downloads.
- Mobile layout and Cloud build/runtime logs without errors.

Record the repository and live dashboard URLs in `submission_checklist.md`. These live checks have not been marked complete.

## Safeguards included

- At most 10 MiB uploaded, 10,000 rows, 64 columns, 2,048 characters per cell and 100 distinct values per filter category. Numeric and duration bounds prevent overflow.
- XLSX: at most 256 members, 40 MiB expanded bytes and 200:1 per-member compression ratio. DTD/entities, macros, external workbook links, formulas and excessive sparse coordinates are rejected.
- Uploads stay in the originating session; no shared upload cache, upload-content persistence or content logging.
- All uploaded chart labels are escaped. Formula-like CSV text is neutralized without changing numeric analytics. Explicit CSV downloads stay in the browser.
- CORS/XSRF enabled, static serving disabled, upload limit 10 MiB, WebSocket message limit 32 MiB, detailed browser errors hidden.
- Channel/date comparison expansion is checked before allocation and capped at 20,000 rows. Large selections receive instructions to narrow filters/group more coarsely.

## Run locally

Windows PowerShell, from the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, use `python3.12 -m venv .venv`, then `.venv/bin/python` for the install/run commands. For tests, install `requirements-dev.txt` and run `python -m pytest -q`. For a fresh audit, install pip-audit as a development tool and run `python -m pip_audit -r requirements.lock.txt`.

## Evidence and official guidance

See `validation_report.md`, `validation/cloud-ready-browser-results.json`, `validation/cloud-ready-dependency-audit.json`, `validation/cloud-ready-secret-scan.json` and five updated screenshots.

Official guidance consulted October 11, 2026:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
