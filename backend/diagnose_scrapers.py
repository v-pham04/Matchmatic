# Opens a real visible browser so you can see what Playwright sees
# and prints the HTML structure so we can find the right selectors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from app.scraper.playwright_env import configure_playwright_browsers
import time

def diagnose_topcv():
    print("\n" + "="*60)
    print("DIAGNOSING TOPCV (with stealth)")
    print("="*60)

    configure_playwright_browsers()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-automation",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page.goto("https://www.topcv.vn/viec-lam-it?keyword=software+engineer&sort=new",
                  wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        print("\nPage title:", page.title())
        print("Current URL:", page.url)

        selectors = [
            "div.job-item",
            "[data-job-id]",
            "div[class*='job-item-search']",
            "div.box-job",
            "h3.title a",
            "a[href*='viec-lam']",
        ]

        print("\n--- Trying selectors ---")
        for sel in selectors:
            try:
                elements = page.query_selector_all(sel)
                if elements:
                    print(f"  FOUND {len(elements)} elements with: {sel}")
                    first_html = page.evaluate("(el) => el.outerHTML.substring(0, 400)", elements[0])
                    print(f"  Preview: {first_html[:300]}\n")
            except Exception as e:
                print(f"  Error with {sel}: {e}")

        print("\nBrowser staying open for 20 seconds — screenshot what you see")
        time.sleep(20)
        context.close()
        browser.close()

if __name__ == "__main__":
    diagnose_topcv()