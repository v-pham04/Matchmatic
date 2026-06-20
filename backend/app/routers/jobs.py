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