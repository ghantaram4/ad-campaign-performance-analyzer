import sys
from pathlib import Path
sys.path.insert(0,str(Path('.browser-tools').resolve()))
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=b.new_page(viewport={'width':1440,'height':1000})
    page.goto('http://127.0.0.1:8502')
    page.get_by_text('Spend and conversion outcomes', exact=True).wait_for()
    print(page.get_by_text('Spend and conversion outcomes', exact=True).evaluate('(el) => Array.from((function*(e){while(e){yield e;e=e.parentElement}})(el)).map(e=>[e.tagName,e.getAttribute("data-testid"),e.getAttribute("class"),e.getAttribute("style")])'))
    page.get_by_text('Clicks vs estimated conversions',exact=True).first.scroll_into_view_if_needed()
    page.screenshot(path='validation/ink-coral-pairs.png')
    b.close()
