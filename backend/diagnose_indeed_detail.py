import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from app.scraper.playwright_env import configure_playwright_browsers
import time

# Use one of the failing URLs from your logs
TEST_URL = "https://www.indeed.com/viewjob?jk=2559e214b1ebe40b"

configure_playwright_browsers()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    page.goto(TEST_URL, wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)

    print("Title:", page.title())

    selectors = [
        "#jobDescriptionText",
        "[class*='jobsearch-jobDescriptionText']",
        "[class*='JobDescription']",
        "[class*='job-description']",
        "div[data-testid='job-description']",
        "div[data-testid='jobDescriptionText']",
        "[class*='jobDescriptionContent']",
        "[class*='description']",
        "div[id*='description']",
        "div[id*='jobDescription']",
    ]

    print("\n--- Testing selectors ---")
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                text = el.inner_text().strip()[:200]
                print(f"\n  FOUND: {sel}")
                print(f"  Preview: {text}")
        except:
            pass

    print("\nOpen 20 seconds — right-click the description text → Inspect to see the real class name")
    time.sleep(20)
    browser.close()