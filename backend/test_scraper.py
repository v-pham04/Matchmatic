# backend/test_scraper.py
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.database import SessionLocal
from app.models.user import User
from app.tasks.scraper_task import run_scrapers_task


def resolve_test_user_id() -> str:
    db = SessionLocal()
    try:
        user_id = os.getenv("TEST_USER_ID", "").strip()
        email = os.getenv("TEST_USER_EMAIL", "").strip()

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            label = user_id
        elif email:
            user = db.query(User).filter(User.email == email).first()
            label = email
        else:
            print("Missing TEST_USER_EMAIL or TEST_USER_ID in .env")
            print("Create a user: log in via the frontend once, or:")
            print('  curl -X POST "http://localhost:8000/users/?email=you@example.com"')
            sys.exit(1)

        if not user:
            print(f"No user found for {label} in your local database.")
            print("Each developer has their own DB — log in via the frontend once to create your user row.")
            sys.exit(1)

        if not user.resume_text:
            print(f"User {user.email} ({user.id}) has no resume uploaded.")
            print("Upload a resume in Settings before running scrape + analysis.")
            sys.exit(1)

        print(f"Using user: {user.email} ({user.id})")
        return str(user.id)
    finally:
        db.close()


if __name__ == "__main__":
    user_id = resolve_test_user_id()

    print("Queuing scraper task...")
    result = run_scrapers_task.delay(
        ["software engineer", "backend developer"],
        user_id=user_id,
    )
    print("Task queued with ID:", result.id)
    print("Check your Celery worker terminal to watch it run.")
    print("After scrape + analysis finish, refresh the Jobs page in the browser.")