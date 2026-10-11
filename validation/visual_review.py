import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.browser-tools'))
from playwright.sync_api import sync_playwright

root = Path(__file__).parent
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8502')
    page.get_by_role('tab', name='Overview', exact=True).wait_for()
    page.locator('.js-plotly-plot').first.wait_for()
    page.screenshot(path=str(root / 'ink-coral-overview.png'), full_page=True)
    for label in ['Platform Comparison', 'Campaign Details', 'Time Series']:
        page.get_by_role('tab', name=label, exact=True).click()
        page.wait_for_timeout(600)
        page.screenshot(path=str(root / ('ink-coral-' + label.lower().replace(' ', '-') + '.png')), full_page=True)
    page.get_by_role('tab', name='Overview', exact=True).click()
    page.get_by_text('Clicks vs estimated conversions', exact=True).first.scroll_into_view_if_needed()
    page.screenshot(path=str(root / 'ink-coral-pairs.png'))
    page.set_viewport_size({'width': 390, 'height': 900})
    page.wait_for_timeout(600)
    page.get_by_text('Clicks vs estimated conversions', exact=True).first.scroll_into_view_if_needed()
    page.screenshot(path=str(root / 'ink-coral-mobile.png'), full_page=True)
    overflow = page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    report = {'browser_errors': errors, 'mobile_page_overflow': overflow, 'screenshots': 6, 'url': 'http://127.0.0.1:8502'}
    (root / 'ink-coral-browser-results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    browser.close()

