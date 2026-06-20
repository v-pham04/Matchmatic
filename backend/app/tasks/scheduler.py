from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.tasks.scraper_task import run_scrapers_task
from loguru import logger
 
 
def start_scheduler():
    """
    Start the background scheduler.
    Call this once when the FastAPI app starts.
    """
    scheduler = BackgroundScheduler()
 
    # Run the scraper task every 6 hours
    scheduler.add_job(
        func=lambda: run_scrapers_task.delay(),  # .delay() sends the task to Celery
        trigger=IntervalTrigger(hours=6),
        id="scraper_job",
        name="Run job scrapers",
        replace_existing=True,
    )
 
    scheduler.start()
    logger.info("Scheduler started — scraper will run every 6 hours")
    return scheduler
