"""Browser checks use in-memory fixtures and delete temporary downloads."""
import json
import sys
from io import BytesIO
from urllib.parse import urlparse
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.browser-tools'))
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
raw = pd.read_csv(root / 'data/social_media_advertising_sample.csv')
fixture = raw.head(2).copy()
fixture['Date'] = ['2025-01-01', '2025-01-08']
fixture['Company'] = ['=1+1', '<img src=x onerror=alert(1)>']
fixture.loc[0, 'Channel_Used'] = '<img src=x onerror=alert(1)>'
workbook = BytesIO()
raw.head(2).to_excel(workbook, index=False)
results = {}
errors = []
media_requests = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    first = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    # Exercise the native dataframe fallback download rather than an OS save dialog.
    first.add_init_script('window.showSaveFilePicker = undefined')
    second = browser.new_context(viewport={'width': 1440, 'height': 1000})
    page = first.new_page()
    other = second.new_page()
    for view in [page, other]:
        view.on('pageerror', lambda e: errors.append(type(e).__name__))
        view.on('request', lambda request: media_requests.append(request.url) if urlparse(request.url).path.startswith('/media/') else None)
        view.goto('http://127.0.0.1:8503')
        expect(view.get_by_role('tab', name='Overview', exact=True)).to_be_visible()
        expect(view.get_by_test_id('stMetricValue').first).to_have_text('$29,490.00')
    tabs = ['Overview', 'Platform Comparison', 'Campaign Details', 'Time Series']
    for tab in tabs:
        page.get_by_role('tab', name=tab, exact=True).click()
        expect(page.get_by_role('tabpanel', name=tab)).to_be_visible()
    results['four_tabs'] = True
    channel = page.get_by_test_id('stMultiSelect').filter(has=page.get_by_text('Channel', exact=True))
    channel.get_by_role('button', name='Clear all', exact=True).click()
    for tab in tabs:
        page.get_by_role('tab', name=tab, exact=True).click()
        expect(page.get_by_role('tabpanel', name=tab).get_by_text('No data for selected filters.', exact=False)).to_be_visible()
    results['global_empty_states'] = True
    page.get_by_role('button', name='Reset filters', exact=True).click()
    page.get_by_role('tab', name='Overview', exact=True).click()
    expect(page.get_by_test_id('stMetricValue').first).to_have_text('$29,490.00')
    results['filter_reset'] = True
    page.locator('input[type=file]').set_input_files({'name':'campaigns.csv','mimeType':'text/csv','buffer':fixture.to_csv(index=False).encode()})
    expect(page.get_by_test_id('stMetricValue').first).to_have_text('$1,100.00')
    expect(other.get_by_test_id('stMetricValue').first).to_have_text('$29,490.00')
    expect(page.get_by_text('Uploaded data: 2 campaigns', exact=True)).to_be_visible()
    results['csv_upload_and_session_isolation'] = True
    assert page.locator('img[src=x]').count() == 0
    results['uploaded_html_inert'] = True
    expect(page.get_by_test_id('stDateInput').filter(has=page.get_by_text('From',exact=True)).locator('input')).to_have_value('2025-01-01')
    results['source_filter_reset'] = True
    for tab, label in [('Platform Comparison','Download channel summary'), ('Campaign Details','Download campaign results'), ('Time Series','Download time summary')]:
        page.get_by_role('tab', name=tab, exact=True).click()
        with page.expect_download() as downloaded:
            next(frame for frame in page.frames if frame.get_by_role('link', name=label, exact=True).count()).get_by_role('link', name=label, exact=True).click()
        download = downloaded.value
        try:
            exported = pd.read_csv(download.path())
            assert not exported.empty
            if tab == 'Campaign Details':
                assert exported.Company.iloc[0] == "'=1+1"
        finally:
            download.delete()
        results[tab.lower().replace(' ', '_') + '_download'] = True
    page.get_by_role('tab', name='Campaign Details', exact=True).click()
    page.get_by_role('tabpanel',name='Campaign Details').get_by_test_id('stDataFrame').hover()
    with page.expect_download() as native_downloaded:
        page.get_by_role('tabpanel',name='Campaign Details').get_by_role('button',name='Download as CSV',exact=True).click()
    native_download = native_downloaded.value
    try:
        native_export = pd.read_csv(native_download.path())
        assert native_export.Company.iloc[0] == "'=1+1"
    finally:
        native_download.delete()
    results['native_table_export_formula_protection'] = True
    page.get_by_label('Search campaigns', exact=True).fill('NO_MATCH_TEST')
    page.get_by_label('Search campaigns', exact=True).press('Enter')
    expect(page.get_by_text('No campaigns match your search.', exact=False)).to_be_visible()
    page.get_by_label('Search campaigns', exact=True).fill('')
    page.get_by_label('Search campaigns', exact=True).press('Enter')
    results['local_search_empty_state'] = True
    page.locator('input[type=file]').set_input_files({'name':'campaigns.xlsx','mimeType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','buffer':workbook.getvalue()})
    page.get_by_role('tab', name='Overview', exact=True).click()
    expect(page.get_by_test_id('stMetricValue').first).to_have_text('$1,100.00')
    expect(page.get_by_test_id('stDateInput').filter(has=page.get_by_text('From',exact=True)).locator('input')).to_have_value('2024-01-05')
    results['xlsx_upload'] = True
    page.locator('input[type=file]').set_input_files({'name':'bad.csv','mimeType':'text/csv','buffer':b'Company\nprivate-value\n'})
    expect(page.get_by_text('Missing required columns:', exact=False)).to_be_visible()
    assert 'private-value' not in page.locator('body').inner_text()
    results['invalid_schema_without_content_disclosure'] = True
    page.locator('input[type=file]').set_input_files({'name':'large.csv','mimeType':'text/csv','buffer':b'x' * (10 * 1024 * 1024 + 1)})
    expect(page.get_by_text('File must be 10.0MB or smaller.', exact=False)).to_be_visible()
    results['browser_upload_size_limit'] = True
    page.locator('input[type=file]').set_input_files({'name':'campaigns.csv','mimeType':'text/csv','buffer':raw.to_csv(index=False).encode()})
    expect(page.get_by_test_id('stMetricValue').first).to_have_text('$29,490.00')
    page.set_viewport_size({'width': 390, 'height': 900})
    page.get_by_role('tab', name='Overview', exact=True).click()
    page.get_by_text('Clicks vs estimated conversions', exact=True).first.scroll_into_view_if_needed()
    page.screenshot(path=str(root / 'validation/security-mobile.png'))
    assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    results['mobile_no_page_overflow'] = True
    assert not media_requests
    results['no_shared_media_export_requests'] = True
    assert not errors
    results['no_browser_errors'] = True
    first.close()
    second.close()
    browser.close()
(root / 'validation/security-browser-results.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results))
