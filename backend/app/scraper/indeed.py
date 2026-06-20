from app.scraper.base_scraper import BaseScraper
from datetime import datetime, timezone
from loguru import logger
import time


class IndeedScraper(BaseScraper):
    SOURCE_NAME = "indeed_us"
    COUNTRY = "us"

    def scrape(self, keywords: list[str]) -> list[dict]:
        results = []

        for keyword in keywords:
            logger.info(f"Searching Indeed for: {keyword}")

            search_url = (
                f"https://www.indeed.com/jobs"
                f"?q={keyword.replace(' ', '+')}"
                f"&fromage=1"
                f"&sort=date"
            )

            self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(4)

            # Use job_seen_beacon — these are the real job cards, not the preview panel
            # We read ALL data from the list first, before touching any detail pages
            card_data = []
            cards = self.page.query_selector_all(".job_seen_beacon")
            logger.info(f"Found {len(cards)} Indeed job cards for '{keyword}'")

            for card in cards:
                try:
                    # Get the data-jk attribute from the anchor inside the card
                    # This is the unique job ID Indeed uses
                    link_el = card.query_selector("a[data-jk]")
                    if not link_el:
                        # Try the h3 title link as fallback
                        link_el = card.query_selector("h3.jobTitle a")
                    if not link_el:
                        continue

                    job_id = link_el.get_attribute("data-jk")

                    # Read title from the h3 inside the card
                    title_el = card.query_selector("h3.jobTitle span[title]")
                    if not title_el:
                        title_el = card.query_selector("h3.jobTitle span")
                    if not title_el:
                        title_el = card.query_selector("h3.jobTitle")

                    title = title_el.get_attribute("title") or title_el.inner_text().strip() if title_el else None
                    if not title:
                        continue

                    # Company name
                    company_el = card.query_selector("[data-testid='company-name']")
                    if not company_el:
                        company_el = card.query_selector(".companyName")
                    company = company_el.inner_text().strip() if company_el else "Unknown Company"

                    # Location
                    location_el = card.query_selector("[data-testid='text-location']")
                    if not location_el:
                        location_el = card.query_selector(".companyLocation")
                    location = location_el.inner_text().strip() if location_el else "United States"

                    job_url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else None
                    if not job_url:
                        href = link_el.get_attribute("href")
                        if href:
                            job_url = "https://www.indeed.com" + href if not href.startswith("http") else href

                    if not job_url:
                        continue

                    card_data.append({
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                    })

                    logger.debug(f"Read card: {title} at {company}")

                except Exception as e:
                    logger.warning(f"Failed to read Indeed card: {e}")
                    continue

            logger.info(f"Successfully read {len(card_data)} cards for '{keyword}'")

            # NOW navigate to each job detail page to get the description
            for item in card_data:
                try:
                    self.page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)

                    desc_el = (
                        self.page.query_selector("#jobDescriptionText") or
                        self.page.query_selector("[class*='jobsearch-jobDescriptionText']") or
                        self.page.query_selector("[class*='JobDescription']")
                    )
                    description = desc_el.inner_text().strip() if desc_el else ""

                    results.append({
                        "title": item["title"],
                        "company": item["company"],
                        "location": item["location"],
                        "url": item["url"],
                        "description": description,
                        "posted_at": datetime.now(timezone.utc),
                        "external_id": item["job_id"],
                    })

                    logger.info(f"Scraped: {item['title']} at {item['company']}")

                except Exception as e:
                    logger.warning(f"Failed to get Indeed description for {item.get('title')}: {e}")
                    continue

        return results