from app.scraper.base_scraper import BaseScraper, is_junk_description
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

            # Read ALL card data from the search results page first, before visiting detail pages.
            # Also grab the card snippet here — used as a fallback if the detail page is blocked.
            card_data = []
            cards = self.page.query_selector_all(".job_seen_beacon")
            logger.info(f"Found {len(cards)} Indeed job cards for '{keyword}'")

            for card in cards:
                try:
                    link_el = card.query_selector("a[data-jk]")
                    if not link_el:
                        link_el = card.query_selector("h3.jobTitle a")
                    if not link_el:
                        continue

                    job_id = link_el.get_attribute("data-jk")

                    title_el = card.query_selector("h3.jobTitle span[title]")
                    if not title_el:
                        title_el = card.query_selector("h3.jobTitle span")
                    if not title_el:
                        title_el = card.query_selector("h3.jobTitle")

                    title = title_el.get_attribute("title") or title_el.inner_text().strip() if title_el else None
                    if not title:
                        continue

                    company_el = card.query_selector("[data-testid='company-name']")
                    if not company_el:
                        company_el = card.query_selector(".companyName")
                    company = company_el.inner_text().strip() if company_el else "Unknown Company"

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

                    # Grab the search-result snippet from the card — used as fallback
                    # if the detail page is blocked by a login wall or Cloudflare
                    snippet_el = (
                        card.query_selector(".job-snippet") or
                        card.query_selector("ul.job-snippet") or
                        card.query_selector("[class*='jobCardShelfContainer']") or
                        card.query_selector("[class*='snippet']")
                    )
                    snippet = (snippet_el.inner_text() or "").strip() if snippet_el else ""

                    card_data.append({
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "snippet": snippet,
                    })

                    logger.debug(f"Read card: {title} at {company} (snippet: {len(snippet)} chars)")

                except Exception as e:
                    logger.warning(f"Failed to read Indeed card: {e}")
                    continue

            logger.info(f"Successfully read {len(card_data)} cards for '{keyword}'")

            for item in card_data:
                try:
                    self.page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)

                    desc_el = (
                        self.page.query_selector("#jobDescriptionText") or
                        self.page.query_selector("[class*='jobsearch-jobDescriptionText']") or
                        self.page.query_selector("[class*='JobDescription']") or
                        self.page.query_selector("[class*='job-description']") or
                        self.page.query_selector("[class*='jobDescriptionContent']") or
                        self.page.query_selector("div[data-testid='job-description']") or
                        self.page.query_selector("div[data-testid='jobDescriptionText']") or
                        self.page.query_selector("[class*='description']")
                    )

                    if desc_el:
                        description = (desc_el.inner_text() or "").strip()
                        logger.info(f"Scraped: {item['title']} at {item['company']} ({len(description)} chars)")
                    else:
                        description = (self.page.evaluate("""
                            () => {
                                const remove = document.querySelectorAll(
                                    'nav, header, footer, script, style, [class*="header"], [class*="footer"], [class*="navbar"], [class*="mosaic"]'
                                );
                                remove.forEach(el => el.remove());
                                const text = document.body.innerText;
                                const markers = ['Job description', 'Full job description', 'About the job', 'About this role'];
                                for (const marker of markers) {
                                    const idx = text.indexOf(marker);
                                    if (idx !== -1) return text.substring(idx, idx + 4000);
                                }
                                return text.substring(0, 4000);
                            }
                        """) or "").strip()
                        logger.warning(f"Used body fallback for Indeed: {item['title']}")

                    # If the full page was blocked (login wall / Cloudflare), fall back to the
                    # card snippet captured from the search results page.
                    if is_junk_description(description) or len(description) < 150:
                        snippet = item.get("snippet", "")
                        if snippet and len(snippet) > 50 and not is_junk_description(snippet):
                            logger.warning(
                                f"Detail page blocked for '{item['title']}' — using card snippet fallback"
                            )
                            description = snippet
                        else:
                            logger.warning(
                                f"No usable description for '{item['title']}' — skipping"
                            )
                            continue

                    results.append({
                        "title": item["title"],
                        "company": item["company"],
                        "location": item["location"],
                        "url": item["url"],
                        "description": description,
                        "posted_at": datetime.now(timezone.utc),
                        "external_id": item["job_id"],
                    })

                except Exception as e:
                    logger.warning(f"Failed to get Indeed description for {item.get('title')}: {e}")
                    continue

        return results
