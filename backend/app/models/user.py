import uuid
from sqlalchemy import Column, String, Boolean, Integer, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    target_market = Column(String, default="both")  # "vietnam" | "us" | "both"
    visa_check_enabled = Column(Boolean, default=False)
    min_match_score = Column(Integer, default=70)
    job_keywords = Column(ARRAY(String))
    resume_url = Column(String)
    resume_text = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


