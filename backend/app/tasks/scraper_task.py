# backend/app/tasks/scraper_task.py
from celery import Celery
from app.config import settings
from loguru import logger

# Create the Celery app
# The broker is Redis — it acts as the message queue between your API and the worker
celery_app = Celery(
    "matchmatic",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.scraper_task",
        "app.tasks.analysis_task",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
)

@celery_app.task(name="run_scrapers")
def run_scrapers_task(keywords: list[str] = None, user_id: str = None):
    if keywords is None:
        keywords = ["software engineer", "backend developer", "devops", "data engineer"]
 
    logger.info(f"Starting scraper task with keywords: {keywords}")
 
    from app.scraper.topcv import TopCVScraper
    from app.scraper.indeed import IndeedScraper
    from app.scraper.jsearch import JSearchScraper
    from app.tasks.analysis_task import analyze_job_task
    from app.database import SessionLocal
    from app.models.job import Job

    results = {}

    if settings.SCRAPER_USE_PLAYWRIGHT:
        try:
            topcv = TopCVScraper()
            results["topcv"] = topcv.run(keywords)
        except Exception as e:
            logger.error(f"TopCV scraper failed: {e}")
            results["topcv"] = {"error": str(e)}

    if settings.JSEARCH_API_KEY:
        try:
            jsearch = JSearchScraper()
            results["jsearch"] = jsearch.run(keywords)
        except Exception as e:
            logger.error(f"JSearch scraper failed: {e}")
            results["jsearch"] = {"error": str(e)}
    elif settings.SCRAPER_USE_PLAYWRIGHT:
        try:
            indeed = IndeedScraper()
            results["indeed"] = indeed.run(keywords)
        except Exception as e:
            logger.error(f"Indeed scraper failed: {e}")
            results["indeed"] = {"error": str(e)}
    else:
        logger.warning("No job source configured — set JSEARCH_API_KEY or SCRAPER_USE_PLAYWRIGHT=true")
    # If a user_id was provided, queue analysis for all unprocessed jobs
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


# Import so Celery worker registers analyze_job when started with -A app.tasks.scraper_task:celery_app
import app.tasks.analysis_task  # noqa: F401, E402
