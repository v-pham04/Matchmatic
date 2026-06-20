# backend/test_scraper.py
import sys
import os

# Make sure Python can find your app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tasks.scraper_task import run_scrapers_task

print("Queuing scraper task...")
result = run_scrapers_task.delay(["software engineer", "backend developer"])
print("Task queued with ID:", result.id)
print("Check your Celery worker terminal to watch it run.")