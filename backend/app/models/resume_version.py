import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
 
class ResumeVersion(Base):
    __tablename__ = "resume_versions"
 
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    version_type = Column(String)  # original / ats_optimized / humanized / final
    content_text = Column(Text)
    storage_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
