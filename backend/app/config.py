from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/postgres"

    # App
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "info"

    # Owner (MVP single user)
    owner_user_email: str = "owner@competetrack.com"

    # External APIs (not used in Phase 1, but defined for config completeness)
    google_places_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    resend_from_email: Optional[str] = None
    apify_api_token: Optional[str] = None
    frontend_url: str = "http://localhost:3000"

    # Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # Scheduler
    collect_hour: int = 8
    collect_minute: int = 0
    digest_email_hour: int = 8
    digest_email_minute: int = 30
    timezone: str = "Asia/Ho_Chi_Minh"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
