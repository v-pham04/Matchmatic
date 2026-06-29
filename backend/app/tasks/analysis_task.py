from app.tasks.scraper_task import celery_app
from app.database import SessionLocal
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.models.user import User
from app.scraper.base_scraper import is_junk_description
from loguru import logger
from app.utils.cache import get_cached_analysis, set_cached_analysis


@celery_app.task(name="analyze_job", bind=True, max_retries=3)
def analyze_job_task(self, job_id: str, user_id: str):
    """
    Run the full AI analysis pipeline for one job + one user.

    Pipeline:
    1. Check Redis cache — skip Gemini if already analyzed recently
    2. Create/update analysis record with status=pending
    3. Validate description (length + junk check) — mark failed if bad
    4. Run ATS Scorer → score, match level, skills
    5. Run Visa Analyzer (only if user opted in and it's a US job)
    6. Run Report Writer → 4-paragraph written analysis
    7. Save results, mark status=complete
    8. On any failure: set status=failed with error_message, re-raise for Celery retry
    """
    cached = get_cached_analysis(job_id, user_id)
    if cached:
        logger.info(f"Cache HIT for job {job_id} — skipping Gemini pipeline")
        return cached

    db = SessionLocal()
    analysis = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"analyze_job_task: Job {job_id} not found")
            return

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"analyze_job_task: User {user_id} not found")
            return

        if not user.resume_text:
            logger.warning(f"User {user_id} has no resume — skipping analysis")
            return

        # Create/reuse analysis record with status=pending so the frontend can show a spinner
        analysis = (
            db.query(JobAnalysis)
            .filter(JobAnalysis.job_id == job.id, JobAnalysis.user_id == user.id)
            .first()
        )
        if analysis:
            analysis.status = "pending"
            analysis.error_message = None
        else:
            analysis = JobAnalysis(job_id=job.id, user_id=user.id, status="pending")
            db.add(analysis)
        db.commit()

        # --- Description validation (after record creation so we can mark it failed) ---
        raw = job.description_raw or ""
        if len(raw.strip()) < 150:
            logger.warning(f"Job {job_id} description too short — skipping analysis")
            analysis.status = "failed"
            analysis.error_message = "No job description available"
            db.commit()
            return

        if is_junk_description(raw):
            logger.warning(f"Job {job_id} description is a junk/error page — skipping analysis")
            analysis.status = "failed"
            analysis.error_message = "Job description blocked (error page or login wall)"
            job.is_processed = True  # Prevent endless re-queuing
            db.commit()
            return
        # ---------------------------------------------------------------------------------

        logger.info(f"Analyzing: {job.title} at {job.company} for user {user.email}")

        from app.agents.ats_scorer import run_ats_scorer
        ats_result = run_ats_scorer(raw, user.resume_text)

        visa_result = None
        if user.visa_check_enabled and job.country == "us":
            from app.agents.visa_analyzer import run_visa_analyzer
            visa_result = run_visa_analyzer(raw)

        from app.agents.report_writer import run_report_writer
        summary = run_report_writer(
            job_description=raw,
            resume_text=user.resume_text,
            ats_result=ats_result,
        )

        analysis.ats_score = ats_result.get("score", 0)
        analysis.match_level = ats_result.get("match_level", "LOW")
        analysis.matching_skills = ats_result.get("matching_skills", [])
        analysis.missing_skills = ats_result.get("missing_skills", [])
        analysis.experience_match = ats_result.get("experience_match", "weak")
        analysis.visa_compatible = visa_result.get("f1_opt_compatible") if visa_result else None
        analysis.visa_signal = visa_result.get("visa_signal") if visa_result else None
        analysis.visa_evidence = visa_result.get("evidence") if visa_result else None
        analysis.summary = summary
        analysis.status = "complete"
        analysis.error_message = None

        job.is_processed = True
        db.commit()

        result = {"score": ats_result["score"], "match_level": ats_result["match_level"]}
        set_cached_analysis(job_id, user_id, result)

        logger.info(f"Analysis complete: score={ats_result['score']} match={ats_result['match_level']}")
        return result

    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {e}")
        if analysis is not None:
            try:
                analysis.status = "failed"
                analysis.error_message = str(e)[:500]
                db.commit()
            except Exception:
                db.rollback()
        else:
            db.rollback()
        raise  # Re-raise so Celery records the failure
    finally:
        db.close()
