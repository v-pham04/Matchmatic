import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class JobAnalysis(Base):
    __tablename__ = "job_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)    # FK to jobs.id
    user_id = Column(UUID(as_uuid=True), nullable=False)   # FK to users.id
    ats_score = Column(Integer)                             # 0-100
    match_level = Column(String)                           # HIGH / MEDIUM / LOW
    matching_skills = Column(ARRAY(String))
    missing_skills = Column(ARRAY(String))
    experience_match = Column(String)                      # strong / partial / weak
    visa_compatible = Column(Boolean, nullable=True)       # null = not checked
    visa_signal = Column(String, nullable=True)            # open / citizen_only / unclear
    visa_evidence = Column(Text, nullable=True)
    summary = Column(Text)                                 # full written analysis
    dismissed = Column(Boolean, default=False)
    status = Column(String, default="pending")        # pending / complete / failed
    error_message = Column(Text, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
