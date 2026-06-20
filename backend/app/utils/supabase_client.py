from loguru import logger
from supabase import Client, create_client

from app.config import settings

RESUMES_BUCKET = "resumes"

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,
)


def ensure_resumes_bucket() -> None:
    """Create the resumes storage bucket if it does not exist yet."""
    try:
        supabase.storage.get_bucket(RESUMES_BUCKET)
    except Exception:
        logger.info(f"Creating Supabase storage bucket: {RESUMES_BUCKET}")
        supabase.storage.create_bucket(
            RESUMES_BUCKET,
            options={"public": True},
        )
