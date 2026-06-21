from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Monorepo: .env lives at repo root (Matchmatic/.env), not in backend/
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
ROOT_DIR = ENV_FILE.parent
DEFAULT_PLAYWRIGHT_BROWSERS_PATH = ROOT_DIR / ".playwright-browsers"


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    PLAYWRIGHT_BROWSERS_PATH: str = str(DEFAULT_PLAYWRIGHT_BROWSERS_PATH)

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")


settings = Settings()
