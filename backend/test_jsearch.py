# backend/test_jsearch.py
"""Smoke test: JSearch API fetch only (no DB, no Celery)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.config import settings
from app.scraper.jsearch import fetch_jobs


def main() -> None:
    if not settings.JSEARCH_API_KEY:
        print("Set JSEARCH_API_KEY in Matchmatic/.env")
        print("https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        sys.exit(1)

    jobs = fetch_jobs(["devops engineer"])
    print(f"Fetched {len(jobs)} usable jobs")
    for job in jobs[:3]:
        print(f"\n- {job['title']} @ {job['company']}")
        print(f"  URL: {job['url']}")
        print(f"  Description: {len(job['description'])} chars")


if __name__ == "__main__":
    main()
