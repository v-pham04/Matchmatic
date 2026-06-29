"""Delete all scraped jobs and related analyses/applications for a fresh scrape."""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import SessionLocal
from app.models.application import Application
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.utils.cache import redis_client


def clear_all_jobs(clear_redis_cache: bool = True) -> None:
    db = SessionLocal()
    try:
        analyses = db.query(JobAnalysis).delete()
        applications = db.query(Application).delete()
        jobs = db.query(Job).delete()
        db.commit()
        print(f"Deleted {jobs} jobs, {analyses} analyses, {applications} applications")

        if clear_redis_cache:
            deleted = 0
            for key in redis_client.scan_iter("analysis:*"):
                redis_client.delete(key)
                deleted += 1
            print(f"Cleared {deleted} Redis analysis cache keys")
    finally:
        db.close()


if __name__ == "__main__":
    if "--yes" not in sys.argv:
        print("This removes ALL jobs, job_analyses, and applications from your local DB.")
        print("Re-run with --yes to confirm:")
        print("  python clear_jobs.py --yes")
        sys.exit(0)
    clear_all_jobs()
