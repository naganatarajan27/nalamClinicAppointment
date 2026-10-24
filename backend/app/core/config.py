from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Nalam Clinic"
    clinic_timezone: str = "Asia/Kolkata"
    frontend_origin: str = "http://localhost:5173"

    database_url: str = "postgresql+psycopg://user:password@localhost:5432/nalam_clinic"

    session_secret: str = "replace-with-a-long-random-secret"
    admin_session_cookie_secure: bool = False
    admin_session_max_age_seconds: int = 60 * 60 * 8  # 8 hours

    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 60

    whatsapp_provider: Literal["mock", "cloud_api"] = "mock"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_api_version: str = "v20.0"
    whatsapp_webhook_verify_token: str = ""
    whatsapp_template_confirmation: str = ""
    whatsapp_template_alternate_slot: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
