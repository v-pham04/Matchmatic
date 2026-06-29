# Handles resume file upload, text extraction, and storage
import io
from uuid import UUID

import docx
import PyPDF2
from fastapi import APIRouter, File, HTTPException, UploadFile
from storage3.exceptions import StorageApiError

from app.database import SessionLocal
from app.models.user import User
from app.utils.supabase_client import RESUMES_BUCKET, ensure_resumes_bucket, supabase

router = APIRouter(prefix="/resume", tags=["resume"])


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file."""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX file."""
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


@router.post("/upload")
async def upload_resume(user_id: UUID, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Sign out and sign in again.")

        file_bytes = await file.read()
        filename = (file.filename or "").lower()
        if not filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        if filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_bytes)
        elif filename.endswith(".docx"):
            resume_text = extract_text_from_docx(file_bytes)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        if not resume_text or len(resume_text) < 100:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough text from file. Use a text-based PDF, not a scanned image.",
            )

        ensure_resumes_bucket()

        extension = filename.rsplit(".", 1)[-1]
        storage_path = f"{user_id}/master_resume.{extension}"
        content_type = file.content_type or (
            "application/pdf" if extension == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        try:
            supabase.storage.from_(RESUMES_BUCKET).upload(
                storage_path,
                file_bytes,
                {"content-type": content_type, "upsert": "true"},
            )
        except StorageApiError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Supabase storage upload failed: {exc.message}",
            ) from exc

        file_url = supabase.storage.from_(RESUMES_BUCKET).get_public_url(storage_path)

        user.resume_url = file_url
        user.resume_text = resume_text
        db.commit()

        return {
            "message": "Resume uploaded successfully",
            "file_url": file_url,
            "text_length": len(resume_text),
        }
    finally:
        db.close()
