import sys
from pathlib import Path
sys.path.insert(0,str(Path('.browser-tools').resolve()))
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=b.new_page()
    page.goto('http://127.0.0.1:8503')
    page.get_by_role('tab',name='Overview',exact=True).wait_for()
    page.locator('[data-testid="stMultiSelect"]').first.wait_for()
    print(page.locator('[data-testid="stMultiSelect"]').filter(has=page.get_by_text('Channel',exact=True)).evaluate('(e)=>({buttons:Array.from(e.querySelectorAll("button,[role=button]" )).map(x=>({label:x.getAttribute("aria-label"),title:x.getAttribute("title"),text:x.innerText})),inputs:Array.from(e.querySelectorAll("input")).map(x=>({label:x.getAttribute("aria-label")}))})'))
    print(page.locator('[data-testid="stFileUploader"]').inner_text())
    b.close()
