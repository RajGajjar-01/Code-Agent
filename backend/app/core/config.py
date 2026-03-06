from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import logging
import secrets

load_dotenv(override=True)


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    WP_CONNECTOR_FERNET_KEYS: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    DATABASE_URL: str = (
        "postgresql+asyncpg://wordpress_agent:changeme@localhost:5432/wordpress_agent_db"
    )

    APP_SECRET_KEY: str = "change-me-in-production"
    FRONTEND_ORIGIN: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


def _ensure_strong_app_secret_key(settings: Settings) -> Settings:
    key = (settings.APP_SECRET_KEY or "").strip()
    if len(key.encode("utf-8")) >= 32:
        return settings

    generated = secrets.token_urlsafe(48)
    settings.APP_SECRET_KEY = generated
    logger.warning(
        "APP_SECRET_KEY is missing/too short (<32 bytes). Generated an ephemeral dev key. "
        "Persist this value in backend/.env as APP_SECRET_KEY to avoid auth token invalidation on restart."
    )
    logger.warning("Generated APP_SECRET_KEY=%s", generated)
    return settings


settings = _ensure_strong_app_secret_key(Settings())
