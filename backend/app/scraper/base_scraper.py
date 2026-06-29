# Abstract base class — defines the interface all scrapers must follow
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.scraper.playwright_env import configure_playwright_browsers
from app.models.job import Job
from app.models.scraper_run import ScraperRun
from loguru import logger


# Strings that indicate the scraper hit an error page, login wall, or Cloudflare block
# instead of the real job description. Any match → reject the job.
JUNK_SIGNALS = [
    # Indeed login walls
    "sign in to view",
    "create an indeed account",
    "you must create an indeed account",
    "sign in to continue",
    "register to view",
    # Cloudflare / security blocks
    "cloudflare",
    "ray id",
    "checking your browser",
    "enable javascript and cookies",
    "security check",
    "ddos protection by cloudflare",
    "access denied",
    "403 forbidden",
    "please complete the security check",
    # Generic HTTP errors
    "this page is not available",
    "page not found",
    "404 not found",
    "502 bad gateway",
    "503 service unavailable",
    # Vietnamese equivalents
    "trang này không tồn tại",
    "đăng nhập để xem",
]


def is_junk_description(text: str) -> bool:
    """Return True if text looks like an error page, login wall, or Cloudflare block."""
    if not text:
        return True
    text_lower = text.lower()
    return any(signal in text_lower for signal in JUNK_SIGNALS)


class BaseScraper(ABC):
    """
    Every scraper (VietnamWorks, Indeed) inherits from this class.
    It handles browser startup/shutdown, deduplication, and run logging.
    Subclasses only need to implement the scrape() method.
    """
 
    SOURCE_NAME = "unknown"  # Override in each subclass
    COUNTRY = "unknown"
 
    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
 
    def launch_browser(self, playwright):
        """Start a Chromium browser in headless mode (no visible window)."""
        self.browser = playwright.chromium.launch(
            headless=True,   # Set to False if you want to WATCH the browser work (useful for debugging)
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.page = self.browser.new_page()
        # Set a realistic browser user-agent so the website thinks we are a normal person
        self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        logger.info(f"Browser launched for {self.SOURCE_NAME}")
 
    def close_browser(self):
        """Shut down the browser cleanly."""
        if self.browser:
            self.browser.close()
            logger.info(f"Browser closed for {self.SOURCE_NAME}")

    def extract_description(self, selectors: list[str], min_length: int = 100) -> str:
        """Try multiple CSS selectors and return the first substantial text block."""
        for selector in selectors:
            try:
                el = self.page.query_selector(selector)
                if not el:
                    el = self.page.wait_for_selector(selector, timeout=3000)
                if el:
                    text = (el.inner_text() or "").strip()
                    if len(text) >= min_length:
                        return text
            except Exception:
                continue
        return ""
 
    def is_duplicate(self, url: str, db: Session) -> bool:
        """Check if we have already saved this job URL. Returns True if it exists."""
        existing = db.query(Job).filter(Job.url == url).first()
        return existing is not None
 
    def is_too_old(self, posted_at: datetime) -> bool:
        """Return True if the job was posted more than 24 hours ago."""
        if posted_at is None:
            return False  # If we cannot determine the date, keep the job
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        # Make sure posted_at is timezone-aware before comparing
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        return posted_at < cutoff
 
    def save_job(self, db: Session, title: str, company: str, location: str,
                 url: str, description: str, posted_at: datetime, external_id: str = None) -> bool:
        """
        Save a job to the database.
        Returns True if saved, False if it was a duplicate or too old.
        """
        if self.is_duplicate(url, db):
            logger.debug(f"Duplicate, skipping: {url}")
            return False
 
        if self.is_too_old(posted_at):
            logger.debug(f"Too old, skipping: {title} at {company}")
            return False

        if not description or len((description or "").strip()) < 150:
            logger.warning(f"Skipping job with no description: {title} at {company}")
            return False

        if is_junk_description(description):
            logger.warning(f"Skipping junk/blocked description: {title} at {company}")
            return False

        job = Job(
            source=self.SOURCE_NAME,
            external_id=external_id,
            url=url,
            title=title,
            company=company,
            location=location,
            country=self.COUNTRY,
            description_raw=description,
            posted_at=posted_at,
        )
        db.add(job)
        db.commit()
        logger.info(f"Saved new job: {title} at {company}")
        return True
 
    def run(self, keywords: list[str]) -> dict:
        """
        Main entry point. Launches browser, runs the scrape, logs the run.
        Returns a summary dict with jobs_found and jobs_new counts.
        """
        db = SessionLocal()
        run_record = ScraperRun(source=self.SOURCE_NAME, status="running")
        db.add(run_record)
        db.commit()
 
        jobs_found = 0
        jobs_new = 0
 
        try:
            configure_playwright_browsers()

            with sync_playwright() as playwright:
                self.launch_browser(playwright)
                results = self.scrape(keywords) or []
                jobs_found = len(results)
 
                for job_data in results:
                    saved = self.save_job(db, **job_data)
                    if saved:
                        jobs_new += 1
 
                self.close_browser()
 
            run_record.status = "success"
            run_record.jobs_found = jobs_found
            run_record.jobs_new = jobs_new
            run_record.finished_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"{self.SOURCE_NAME}: {jobs_new}/{jobs_found} new jobs saved")
            return {"source": self.SOURCE_NAME, "jobs_found": jobs_found, "jobs_new": jobs_new}
 
        except Exception as e:
            run_record.status = "failed"
            run_record.error_message = str(e)
            run_record.finished_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"{self.SOURCE_NAME} scraper failed: {e}")
            raise
        finally:
            db.close()
 
    @abstractmethod
    def scrape(self, keywords: list[str]) -> list[dict]:
        """
        Subclasses implement this. Return a list of dicts, each with:
        title, company, location, url, description, posted_at, external_id
        """
        pass
