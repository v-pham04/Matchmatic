import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

 
class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String)        # e.g. "jsearch_us"
    external_id = Column(String)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    country = Column(String)       # "us" or "vietnam"
    description_raw = Column(Text)
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_processed = Column(Boolean, default=False)

