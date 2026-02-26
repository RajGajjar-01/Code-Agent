import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Groq AI ──────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── WordPress ────────────────────────────────────────────
    WP_BASE_URL: str = ""
    WP_USERNAME: str = ""
    WP_APP_PASSWORD: str = ""

    # ── Google OAuth 2.0 ─────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://wordpress_agent:changeme@localhost:5432/wordpress_agent_db"

    # ── App ──────────────────────────────────────────────────
    APP_SECRET_KEY: str = "change-me-in-production"
    FRONTEND_ORIGIN: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
