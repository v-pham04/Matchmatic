# backend/app/tasks/scraper_task.py
from celery import Celery
from app.config import settings
from loguru import logger

# Create the Celery app
# The broker is Redis — it acts as the message queue between your API and the worker
celery_app = Celery(
    "matchmatic",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
)

@celery_app.task(name="run_scrapers")
def run_scrapers_task(keywords: list[str] = None):
    if keywords is None:
        keywords = ["software engineer", "backend developer", "devops", "data engineer"]

    logger.info(f"Starting scraper task with keywords: {keywords}")

    from app.scraper.topcv import TopCVScraper
    from app.scraper.indeed import IndeedScraper

    results = {}

    try:
        topcv = TopCVScraper()
        results["topcv"] = topcv.run(keywords)
    except Exception as e:
        logger.error(f"TopCV scraper failed: {e}")
        results["topcv"] = {"error": str(e)}

    try:
        indeed = IndeedScraper()
        results["indeed"] = indeed.run(keywords)
    except Exception as e:
        logger.error(f"Indeed scraper failed: {e}")
        results["indeed"] = {"error": str(e)}

    logger.info(f"Scraper task complete: {results}")
    return results