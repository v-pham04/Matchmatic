# Handles fetching job listings and their analysis results
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models.job import Job
from app.models.job_analysis import JobAnalysis

 
router = APIRouter(prefix="/jobs", tags=["jobs"])
 
 
class JobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    location: Optional[str]
    country: Optional[str]
    source: Optional[str]
    url: str
    posted_at: Optional[datetime]
    scraped_at: Optional[datetime]
    is_processed: bool
 
    class Config:
        from_attributes = True


class JobAnalysisResponse(BaseModel):
    id: str
    job_id: str
    ats_score: int
    match_level: str
    matching_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    experience_match: Optional[str]
    visa_compatible: Optional[bool]
    visa_signal: Optional[str]
    visa_evidence: Optional[str]
    summary: Optional[str]
 
    class Config:
        from_attributes = True

 
 
# GET /jobs — return all jobs, optionally filtered by country
# ?country=us   or   ?country=vietnam   or leave blank for both
# ?page=1&limit=20 for pagination
@router.get("/", response_model=List[JobResponse])
def get_jobs(
    country: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    if country:
        query = query.filter(Job.country == country)
    offset = (page - 1) * limit
    jobs = query.order_by(desc(Job.scraped_at)).offset(offset).limit(limit).all()
    return jobs

 
# GET /jobs/{job_id} — return a single job by ID
@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# GET /jobs/feed — return only jobs that have been analyzed and meet the score threshold
@router.get("/feed", response_model=List[JobResponse])
def get_job_feed(
    user_id: str,
    country: Optional[str] = Query(None),
    match_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns jobs that:
    1. Have been analyzed for this user (is_processed = True)
    2. Score at or above the user's saved min_match_score
    3. Match the user's saved target_market (country preference)
    4. Are not dismissed by this user
    Sorted by ATS score descending (HIGH first, then MEDIUM, then LOW).
    """
    # Load user preferences from database
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    # Use user saved preferences as defaults
    # Query params override saved settings if provided
    effective_min_score = user.min_match_score or 60
    effective_country = country
    if not effective_country and user.target_market and user.target_market != "both":
        effective_country = user.target_market
 
    # Join jobs with their analyses for this specific user
    query = (
        db.query(Job)
        .join(JobAnalysis, (JobAnalysis.job_id == Job.id) & (JobAnalysis.user_id == user_id))
        .filter(Job.is_processed == True)
        .filter(JobAnalysis.ats_score >= effective_min_score)
        .filter(JobAnalysis.dismissed == False)
    )
 
    if effective_country:
        query = query.filter(Job.country == effective_country)
 
    if match_level:
        query = query.filter(JobAnalysis.match_level == match_level.upper())
 
    offset = (page - 1) * limit
    jobs = query.order_by(desc(JobAnalysis.ats_score)).offset(offset).limit(limit).all()
    return jobs


# GET /jobs/{job_id}/analysis — return the AI analysis for a specific job and user
@router.get("/{job_id}/analysis", response_model=JobAnalysisResponse)
def get_job_analysis(job_id: str, user_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.job_id == job_id)
        .filter(JobAnalysis.user_id == user_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this job and user")
    return analysis

# POST /jobs/{job_id}/dismiss — mark a job as not interested for this user
@router.post("/{job_id}/dismiss")
def dismiss_job(job_id: str, user_id: str, db: Session = Depends(get_db)):
    """
    Mark a job as dismissed for a specific user.
    Dismissed jobs no longer appear in the feed.
    """
    from fastapi import HTTPException
    analysis = (
        db.query(JobAnalysis)
        .filter(JobAnalysis.job_id == job_id)
        .filter(JobAnalysis.user_id == user_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
 
    analysis.dismissed = True
    db.commit()
 
    # Also invalidate the Redis cache for this job+user pair
    from app.utils.cache import invalidate_analysis
    invalidate_analysis(job_id, user_id)
 
    logger.info(f"Job {job_id} dismissed by user {user_id}")
    return {"message": "Job dismissed successfully"}
 
# GET /admin/scraper-runs — see recent scraper run history
@router.get("/admin/scraper-runs")
def get_scraper_runs(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """
    Returns the most recent scraper run records.
    Use this to check if scraping is working and how many jobs are being found.
    """
    from app.models.scraper_run import ScraperRun
    from sqlalchemy import desc as sqldesc
    runs = (
        db.query(ScraperRun)
        .order_by(sqldesc(ScraperRun.started_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "source": r.source,
            "jobs_found": r.jobs_found,
            "jobs_new": r.jobs_new,
            "status": r.status,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "duration_seconds": (
                int((r.finished_at - r.started_at).total_seconds())
                if r.finished_at and r.started_at else None
            ),
        }
        for r in runs
    ]
