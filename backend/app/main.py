from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, drive, menus, wp_sites
from app.core.config import settings
from app.agent.tools import ensure_wp_cli_installed


def _configure_logging() -> None:
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(levelname)s %(name)s %(message)s",
        )
    else:
        root.setLevel(level)

    logging.getLogger("app").setLevel(level)

    # Debug: Log FRONTEND_ORIGIN
    logger = logging.getLogger(__name__)
    logger.info(f"FRONTEND_ORIGIN configured as: {settings.FRONTEND_ORIGIN}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    await ensure_wp_cli_installed()

    yield


app = FastAPI(
    title="WordPress Agent",
    description="AI-powered WordPress site builder with Google Drive integration",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(drive.router)
app.include_router(chat.router)
app.include_router(menus.router)
app.include_router(wp_sites.router)


@app.get("/health")
async def health():
    return {
        "status": "running",
        "groq": bool(settings.GROQ_API_KEY),
        "wp": True,
        "google_oauth": bool(settings.GOOGLE_CLIENT_ID),
    }
