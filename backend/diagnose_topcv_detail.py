# backend/diagnose_topcv_detail.py
# Opens one TopCV job detail page visibly so we can find the description selector

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from app.scraper.playwright_env import configure_playwright_browsers
import time

# Use one of the URLs from your logs
TEST_URL = "https://www.topcv.vn/viec-lam/data-scientist/2147404.html"

configure_playwright_browsers()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--no-sandbox","--disable-blink-features=AutomationControlled","--disable-automation"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width":1366,"height":768},
        locale="vi-VN",
        timezone_id="Asia/Ho_Chi_Minh",
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    page.goto(TEST_URL, wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)

    print("Page title:", page.title())
    print("URL:", page.url)

    # Try every plausible description selector
    selectors = [
        "div.job-description",
        "div#job-detail-description",
        "div[class*='job-description']",
        "div[class*='description']",
        "div.content-tab",
        "div[class*='content']",
        "section.job-detail",
        "div[class*='job-detail']",
        "div[class*='detail']",
        "div[class*='requirement']",
        "div[class*='jd']",
        "div.box-body",
        "div[class*='body']",
        "article",
        "main",
    ]

    print("\n--- Testing selectors ---")
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                text = el.inner_text().strip()[:150]
                print(f"\n  FOUND: {sel}")
                print(f"  Preview: {text}")
        except Exception as e:
            pass

    print("\n\nBrowser open for 20 seconds — look at the page structure")
    time.sleep(20)
    context.close()
    browser.close()