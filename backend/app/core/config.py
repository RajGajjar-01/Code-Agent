import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""


    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"


    WP_BASE_URL: str = ""
    WP_USERNAME: str = ""
    WP_APP_PASSWORD: str = ""


    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"


    DATABASE_URL: str = "postgresql+asyncpg://wordpress_agent:changeme@localhost:5432/wordpress_agent_db"


    APP_SECRET_KEY: str = "change-me-in-production"
    FRONTEND_ORIGIN: str = "http://localhost:8000"

    WP_ROOT_PATH: str = "/var/www/html/wordpress"
    WP_EDITABLE_DIRS: list = ["wp-content/themes", "wp-content/plugins", "wp-content/mu-plugins"]
    MAX_FILE_SIZE_KB: int = 500

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
