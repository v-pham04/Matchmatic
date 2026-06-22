# backend/test_scraper.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tasks.scraper_task import run_scrapers_task

# Your Matchmatic backend user id — analysis is queued only when this is set
USER_ID = "c73c41a1-45b4-45b5-8425-f1e4c2f73745"

print("Queuing scraper task...")
result = run_scrapers_task.delay(
    ["software engineer", "backend developer"],
    user_id=USER_ID,
)
print("Task queued with ID:", result.id)
print("Check your Celery worker terminal to watch it run.")
print("After scrape + analysis finish, refresh the Jobs page in the browser.")
