# Abstract base class — defines the interface all scrapers must follow
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright, Browser, Page
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job import Job
from app.models.scraper_run import ScraperRun
from loguru import logger
 
 
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
            with sync_playwright() as playwright:
                self.launch_browser(playwright)
                results = self.scrape(keywords)
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
