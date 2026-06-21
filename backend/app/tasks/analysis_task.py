from app.tasks.scraper_task import celery_app
from app.database import SessionLocal
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.models.user import User
from loguru import logger
import uuid


@celery_app.task(name="analyze_job")
def analyze_job_task(job_id: str, user_id: str):
    """
    Run the full AI analysis pipeline for one job + one user.

    Pipeline:
    1. Load the job description from the database
    2. Load the user resume text from the database
    3. Run ATS Scorer → get score, match level, skills
    4. Run Visa Analyzer (only if user has visa toggle ON)
    5. Run Report Writer → get substantive written analysis
    6. Save all results to job_analyses table
    7. Mark the job as processed
    """
    db = SessionLocal()
    try:
        # Load the job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"analyze_job_task: Job {job_id} not found")
            return

        # Load the user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"analyze_job_task: User {user_id} not found")
            return

        # Cannot analyze without a resume
        if not user.resume_text:
            logger.warning(f"User {user_id} has no resume — skipping analysis")
            return

        logger.info(f"Analyzing: {job.title} at {job.company} for user {user.email}")

        # Step 1 — ATS Scoring
        from app.agents.ats_scorer import run_ats_scorer
        ats_result = run_ats_scorer(job.description_raw or "", user.resume_text)

        # Step 2 — Visa Analysis (only if user opted in AND it is a US job)
        visa_result = None
        if user.visa_check_enabled and job.country == "us":
            from app.agents.visa_analyzer import run_visa_analyzer
            visa_result = run_visa_analyzer(job.description_raw or "")

        # Step 3 — Report Writer (substantive written analysis)
        from app.agents.report_writer import run_report_writer
        summary = run_report_writer(
            job_description=job.description_raw or "",
            resume_text=user.resume_text,
            ats_result=ats_result,
        )

        # Step 4 — Save everything to job_analyses table
        analysis = JobAnalysis(
            job_id=job.id,
            user_id=user.id,
            ats_score=ats_result.get("score", 0),
            match_level=ats_result.get("match_level", "LOW"),
            matching_skills=ats_result.get("matching_skills", []),
            missing_skills=ats_result.get("missing_skills", []),
            experience_match=ats_result.get("experience_match", "weak"),
            visa_compatible=visa_result.get("f1_opt_compatible") if visa_result else None,
            visa_signal=visa_result.get("visa_signal") if visa_result else None,
            visa_evidence=visa_result.get("evidence") if visa_result else None,
            summary=summary,
        )
        db.add(analysis)

        # Step 5 — Mark the job as processed
        job.is_processed = True
        db.commit()

        logger.info(f"Analysis complete: score={ats_result['score']} match={ats_result['match_level']}")
        return {"score": ats_result["score"], "match_level": ats_result["match_level"]}

    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()