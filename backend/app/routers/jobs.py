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
    min_score: int = Query(60, ge=0, le=100),
    country: Optional[str] = Query(None),
    match_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns jobs that:
    1. Have been analyzed (is_processed = True)
    2. Have an ATS score >= min_score for this user
    3. Are not dismissed by this user
    Sorted by ATS score descending.
    """
    # Join jobs with their analyses for this user
    query = (
        db.query(Job)
        .join(JobAnalysis, (JobAnalysis.job_id == Job.id) & (JobAnalysis.user_id == user_id))
        .filter(Job.is_processed == True)
        .filter(JobAnalysis.ats_score >= min_score)
        .filter(JobAnalysis.dismissed == False)
    )
 
    if country:
        query = query.filter(Job.country == country)
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
