"""Centralized typed settings via pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Escobar NET WhatsApp Agent"
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./escobar_net.db"

    WHATSAPP_VERIFY_TOKEN: str = "change-me"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_DRY_RUN: bool = True

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TEMPERATURE: float = 0.4
    GROQ_MAX_TOKENS: int = 512
    AGENT_TIMEZONE: str = "America/Bogota"

    BUSINESS_NAME: str = "Escobar NET"
    BUSINESS_SERVICES: str = "Desarrollo web,Aplicaciones moviles,Consultoria y cotizaciones"
    BUSINESS_HOURS: str = "Lun-Sab 08:00-18:00"
    MEMORY_WINDOW: int = 12

    @property
    def services_list(self) -> list[str]:
        return [s.strip() for s in self.BUSINESS_SERVICES.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
