"""Shared job validation and DB persistence for all job sources."""
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.orm import Session

from app.config import jsearch_max_age_hours
from app.database import SessionLocal
from app.models.job import Job
from app.models.scraper_run import ScraperRun

MIN_DESCRIPTION_LENGTH = 150

JUNK_SIGNALS = [
    "sign in to view",
    "create an account",
    "sign in to continue",
    "register to view",
    "cloudflare",
    "ray id",
    "checking your browser",
    "enable javascript and cookies",
    "security check",
    "access denied",
    "403 forbidden",
    "this page is not available",
    "page not found",
    "404 not found",
]


def is_junk_description(text: str) -> bool:
    """Return True if text looks like an error page or login wall."""
    if not text:
        return True
    text_lower = text.lower()
    return any(signal in text_lower for signal in JUNK_SIGNALS)


class JobIngestionService:
    """Dedupes, validates, and persists job records; logs scraper runs."""

    def __init__(self, source: str, country: str):
        self.source = source
        self.country = country

    def is_duplicate(self, url: str, db: Session) -> bool:
        return db.query(Job).filter(Job.url == url).first() is not None

    def is_too_old(self, posted_at: datetime) -> bool:
        if posted_at is None:
            return False
        max_hours = jsearch_max_age_hours()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_hours)
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        return posted_at < cutoff

    def save_job(
        self,
        db: Session,
        *,
        title: str,
        company: str,
        location: str,
        url: str,
        description: str,
        posted_at: datetime,
        external_id: str | None = None,
    ) -> bool:
        if self.is_duplicate(url, db):
            logger.debug(f"Duplicate, skipping: {url}")
            return False

        if self.is_too_old(posted_at):
            logger.debug(f"Too old, skipping: {title} at {company}")
            return False

        if not description or len(description.strip()) < MIN_DESCRIPTION_LENGTH:
            logger.warning(f"Skipping job with short description: {title} at {company}")
            return False

        if is_junk_description(description):
            logger.warning(f"Skipping junk description: {title} at {company}")
            return False

        db.add(
            Job(
                source=self.source,
                external_id=external_id,
                url=url,
                title=title,
                company=company,
                location=location,
                country=self.country,
                description_raw=description,
                posted_at=posted_at,
            )
        )
        db.commit()
        logger.info(f"Saved new job: {title} at {company}")
        return True

    def run(self, keywords: list[str], fetch_jobs) -> dict:
        """
        Run a job source: call fetch_jobs(keywords) → list of job dicts,
        persist each, and record a ScraperRun summary.
        """
        db = SessionLocal()
        run_record = ScraperRun(source=self.source, status="running")
        db.add(run_record)
        db.commit()

        jobs_found = 0
        jobs_new = 0

        try:
            results = fetch_jobs(keywords) or []
            jobs_found = len(results)

            for job_data in results:
                if self.save_job(db, **job_data):
                    jobs_new += 1

            run_record.status = "success"
            run_record.jobs_found = jobs_found
            run_record.jobs_new = jobs_new
            run_record.finished_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"{self.source}: {jobs_new}/{jobs_found} new jobs saved")
            return {
                "source": self.source,
                "jobs_found": jobs_found,
                "jobs_new": jobs_new,
            }
        except Exception as exc:
            run_record.status = "failed"
            run_record.error_message = str(exc)
            run_record.finished_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"{self.source} ingestion failed: {exc}")
            raise
        finally:
            db.close()
