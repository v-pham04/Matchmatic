# backend/app/tasks/scraper_task.py
from celery import Celery
from loguru import logger

from app.config import settings

celery_app = Celery(
    "matchmatic",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.scraper_task",
        "app.tasks.analysis_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
)

DEFAULT_KEYWORDS = [
    "devops engineer",
    "system engineer",
    "cloud engineer",
]


@celery_app.task(name="run_scrapers")
def run_scrapers_task(keywords: list[str] | None = None, user_id: str | None = None):
    keywords = keywords or DEFAULT_KEYWORDS
    logger.info(f"Starting JSearch ingestion with keywords: {keywords}")

    from app.database import SessionLocal
    from app.models.job import Job
    from app.scraper.jsearch import run_jsearch_ingestion
    from app.tasks.analysis_task import analyze_job_task

    if not settings.JSEARCH_API_KEY:
        raise ValueError("JSEARCH_API_KEY is required — set it in Matchmatic/.env")

    results = {}
    try:
        results["jsearch"] = run_jsearch_ingestion(keywords)
    except Exception as exc:
        logger.error(f"JSearch ingestion failed: {exc}")
        results["jsearch"] = {"error": str(exc)}

    if user_id:
        db = SessionLocal()
        try:
            unprocessed = db.query(Job).filter(Job.is_processed == False).all()
            logger.info(f"Queuing analysis for {len(unprocessed)} unprocessed jobs")
            for job in unprocessed:
                analyze_job_task.delay(str(job.id), user_id)
        finally:
            db.close()

    logger.info(f"Scraper task complete: {results}")
    return results


import app.tasks.analysis_task  # noqa: F401, E402
