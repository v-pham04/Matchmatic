# Handles resume file upload, text extraction, and storage
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.supabase_client import supabase
import PyPDF2
import docx
import io

 
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
 
 
# POST /resume/upload
# Frontend sends the PDF/DOCX file here
# We extract the text and store both the file and the text
@router.post("/upload")
async def upload_resume(user_id: str, file: UploadFile = File(...)):
    # Read the file bytes
    file_bytes = await file.read()
 
    # Extract text based on file type
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        resume_text = extract_text_from_docx(file_bytes)
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
 
    if not resume_text or len(resume_text) < 100:
        raise HTTPException(status_code=400, detail="Could not extract text from file. Is it a scanned image?")
 
    # Upload the original file to Supabase Storage
    storage_path = f"resumes/{user_id}/master_resume{'.' + filename.split('.')[-1]}"
    supabase.storage.from_("resumes").upload(
        storage_path,
        file_bytes,
        {"content-type": file.content_type, "upsert": "true"}
    )
 
    # Get the public URL of the uploaded file
    file_url = supabase.storage.from_("resumes").get_public_url(storage_path)
 
    # Update the user record with the resume URL and extracted text
    from app.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.resume_url = file_url
            user.resume_text = resume_text
            db.commit()
    finally:
        db.close()
 
    return {
        "message": "Resume uploaded successfully",
        "file_url": file_url,
        "text_length": len(resume_text)
    }
