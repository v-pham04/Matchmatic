from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    SUPABASE_JWT_SECRET: str = ""
    TEST_USER_EMAIL: str = ""
    TEST_USER_ID: str = ""
    JSEARCH_API_KEY: str = ""
    JSEARCH_NUM_PAGES: int = 2
    JSEARCH_DATE_POSTED: str = "today"
    JSEARCH_JOB_REQUIREMENTS: str = "under_3_years_experience"

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


# Max age for saved jobs — should match JSEARCH_DATE_POSTED (JSearch filters at API; this is a safety net)
JSEARCH_MAX_AGE_HOURS: dict[str, int] = {
    "today": 48,
    "3days": 72,
    "week": 168,
    "month": 720,
}


def jsearch_max_age_hours() -> int:
    return JSEARCH_MAX_AGE_HOURS.get(settings.JSEARCH_DATE_POSTED, 168)


settings = Settings()
