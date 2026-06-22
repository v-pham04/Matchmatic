"""
Week 5 Step 2 — Celery Load Test

Simulates 50 jobs arriving at once and monitors the queue.
Confirms the worker handles real volume on Windows (--pool=solo) without crashing.

Usage:
  # Terminal 1 — start the Celery worker
  celery -A app.tasks.scraper_task:celery_app worker --loglevel=info --pool=solo --concurrency=1

  # Terminal 2 — run this script
  python test_celery_load.py

  # After tasks complete, verify results:
  docker compose exec postgres psql -U postgres -d matchmatic -c "SELECT status, COUNT(*) FROM job_analyses GROUP BY status;"

What you are checking:
  - Worker does NOT crash — stays running and processes all tasks
  - No tasks stuck in 'pending' — all eventually reach 'complete' or 'failed'
  - Failed tasks show a readable error_message in the DB (not null)
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.job import Job
from app.models.user import User

db = SessionLocal()
jobs = db.query(Job).limit(50).all()
user = db.query(User).first()
db.close()

if not user:
    print("ERROR: No users in database. Upload a resume first.")
    sys.exit(1)

if not jobs:
    print("ERROR: No jobs in database. Run the scraper first.")
    sys.exit(1)

print(f"Queuing {len(jobs)} analysis tasks for user: {user.email}")
print("-" * 60)

from app.tasks.analysis_task import analyze_job_task

task_ids = []
start = time.time()

for job in jobs:
    result = analyze_job_task.delay(str(job.id), str(user.id))
    task_ids.append(result.id)
    print(f"  Queued: {job.title[:50]:<50} — task {result.id[:8]}")

elapsed = time.time() - start
print("-" * 60)
print(f"Queued {len(task_ids)} tasks in {elapsed:.2f}s")
print()
print("Watch the Celery worker terminal — it should process them one by one.")
print("The worker should NOT crash. All tasks should eventually complete or fail gracefully.")
print()
print("After the worker finishes, run this to check results:")
print('  docker compose exec postgres psql -U postgres -d matchmatic -c "SELECT status, COUNT(*) FROM job_analyses GROUP BY status;"')
print()
print("Expected: no rows with status=pending (nothing stuck)")
