from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    test_mode: bool = False

    supabase_url: str
    supabase_service_key: SecretStr

    twilio_sid: str | None = None
    twilio_token: SecretStr | None = None
    twilio_phone_number: str | None = None

    webhook_secret: SecretStr
    app_base_url: str = "http://127.0.0.1:8000"
    cron_secret: SecretStr | None = None

    rate_limit_requests: int = Field(default=30, ge=1, le=10_000)
    rate_limit_window: int = Field(default=60, ge=1, le=86_400)

    @field_validator(
        "supabase_url",
        "twilio_sid",
        "twilio_phone_number",
        "app_base_url",
        mode="before",
    )
    @classmethod
    def reject_placeholder_strings(cls, value: str | None):
        if value and "REPLACE_ME" in value:
            raise ValueError("Replace placeholder value before starting")
        return value

    @field_validator(
        "supabase_service_key",
        "twilio_token",
        "webhook_secret",
        "cron_secret",
        mode="before",
    )
    @classmethod
    def reject_placeholder_secrets(cls, value: str | None):
        if value and "REPLACE_ME" in value:
            raise ValueError("Replace placeholder value before starting")
        return value

    def validate_production_requirements(self) -> None:
        if self.environment.lower() != "production":
            return

        required_for_production = {
            "TWILIO_SID": self.twilio_sid,
            "TWILIO_TOKEN": self.twilio_token,
            "TWILIO_PHONE_NUMBER": self.twilio_phone_number,
            "CRON_SECRET": self.cron_secret,
        }

        missing = [
            name for name, value in required_for_production.items()
            if value is None or (isinstance(value, str) and not value.strip())
        ]

        if missing:
            raise ValueError(
                "Missing production configuration: " + ", ".join(missing)
            )

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_requirements()
    return settings
