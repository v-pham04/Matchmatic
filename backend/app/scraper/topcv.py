from app.scraper.base_scraper import BaseScraper
from datetime import datetime, timezone
from loguru import logger
import time


class TopCVScraper(BaseScraper):
    SOURCE_NAME = "topcv"
    COUNTRY = "vietnam"

    # TopCV IT jobs category URL — loads all IT jobs, no keyword needed in URL
    # The stealth browser can access this fine as proven by the diagnostic
    BASE_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257"

    def launch_browser(self, playwright):
        """Override to use stealth settings — TopCV uses Cloudflare."""
        self.browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-automation",
            ]
        )

        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            extra_http_headers={
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        self.page = self.context.new_page()

        # Remove the webdriver flag that Cloudflare checks for
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'vi', 'en'] });
        """)

        logger.info(f"Stealth browser launched for {self.SOURCE_NAME}")

    def close_browser(self):
        """Override to close the context too."""
        if hasattr(self, 'context') and self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
            logger.info(f"Browser closed for {self.SOURCE_NAME}")

    def scrape(self, keywords: list[str]) -> list[dict]:
        results = []

        # TopCV IT category page already shows all tech jobs — 3,000+ listings
        # No keyword search needed — the category does the filtering for us
        # Vietnamese tech keywords to search within the page title text
        vn_keywords = [
            "software", "backend", "frontend", "fullstack", "devops",
            "cloud", "data", "python", "java", "engineer", "developer",
            "lập trình", "kỹ sư", "phần mềm"
        ]

        logger.info("Loading TopCV IT jobs category page")
        self.page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        logger.info(f"TopCV page title: {self.page.title()}")
        logger.info(f"TopCV URL: {self.page.url}")

        # Use the confirmed selector from the diagnostic
        job_cards = self.page.query_selector_all("div[class*='job-item-search-result']")
        if not job_cards:
            job_cards = self.page.query_selector_all("div[class*='job-item-search']")

        logger.info(f"TopCV found {len(job_cards)} total job cards")

        # Collect card data — filter by keyword relevance
        card_data = []
        for card in job_cards[:50]:  # Read up to 50 cards
            try:
                title_el = card.query_selector("h3.title a")
                if not title_el:
                    continue

                title = title_el.inner_text().strip()
                href = title_el.get_attribute("href") or ""
                job_url = href if href.startswith("http") else "https://www.topcv.vn" + href

                # Only keep jobs that match tech keywords in the title
                title_lower = title.lower()
                is_relevant = any(kw in title_lower for kw in vn_keywords)
                if not is_relevant:
                    logger.debug(f"Skipping non-tech job: {title}")
                    continue

                # Company name
                company_el = (
                    card.query_selector("a.company") or
                    card.query_selector("[class*='company-name']") or
                    card.query_selector("h4 a")
                )
                company = company_el.inner_text().strip() if company_el else "Unknown"

                # Location
                location_el = (
                    card.query_selector("[class*='location']") or
                    card.query_selector("label.address") or
                    card.query_selector("[class*='city']")
                )
                location = location_el.inner_text().strip() if location_el else "Vietnam"

                job_id = card.get_attribute("data-job-id") or href.split("/")[-1].split(".")[0]

                card_data.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "external_id": job_id,
                })

                logger.debug(f"Queued: {title} at {company}")

            except Exception as e:
                logger.warning(f"Failed to read TopCV card: {e}")
                continue

        logger.info(f"TopCV queued {len(card_data)} relevant jobs to scrape")

        # Visit each job detail page for the full description
        for item in card_data[:15]:  # Cap at 15 detail pages per run
            try:
                self.page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)

                desc_el = (
                    self.page.query_selector("div.job-description") or
                    self.page.query_selector("[class*='job-description']") or
                    self.page.query_selector("div#job-detail-description") or
                    self.page.query_selector("div.content-tab")
                )
                description = desc_el.inner_text().strip() if desc_el else ""

                results.append({
                    "title": item["title"],
                    "company": item["company"],
                    "location": item["location"],
                    "url": item["url"],
                    "description": description,
                    "posted_at": datetime.now(timezone.utc),
                    "external_id": item["external_id"],
                })

                logger.info(f"Scraped: {item['title']} at {item['company']}")

                self.page.go_back(wait_until="domcontentloaded")
                time.sleep(1)

            except Exception as e:
                logger.warning(f"Failed to get TopCV job detail: {e}")
                continue

        return results