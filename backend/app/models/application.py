import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Application(Base):
    __tablename__ = "applications"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String, default="applied")  # applied/interview/pending/closed
    tailored_resume_url = Column(String, nullable=True)
    tailored_resume_text = Column(Text, nullable=True)
    ats_score_before = Column(Integer, nullable=True)
    ats_score_after = Column(Integer, nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)  # offer / rejected / ghosted
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
