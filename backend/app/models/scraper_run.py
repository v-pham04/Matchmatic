import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
 
class ScraperRun(Base):
    __tablename__ = "scraper_runs"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String)         # which site was scraped
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    status = Column(String)         # success / failed / partial
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
