# Handles reading and updating the logged-in user's profile and settings
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
 
router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    target_market: str
    visa_check_enabled: bool
    min_match_score: int
    job_keywords: Optional[List[str]]
    resume_url: Optional[str]
 
    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    target_market: Optional[str] = None
    visa_check_enabled: Optional[bool] = None
    min_match_score: Optional[int] = None
    job_keywords: Optional[List[str]] = None


# GET /users/{user_id} — fetch a user by ID
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
 
 
# PATCH /users/{user_id}/settings — update a user's preferences
@router.patch("/{user_id}/settings", response_model=UserResponse)
def update_settings(user_id: str, settings: UserSettingsUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = settings.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# POST /users/ — create a new user (called after first Google login)
@router.post("/", response_model=UserResponse)
def create_user(email: str, full_name: Optional[str], db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing
    user = User(email=email, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
