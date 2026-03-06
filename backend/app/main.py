from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, chat, drive, menus, wp_sites
from app.core.config import settings
from app.agent.tools import ensure_wp_cli_installed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_wp_cli_installed()

    yield


app = FastAPI(
    title="WordPress Agent",
    description="AI-powered WordPress site builder with Google Drive integration",
    version="0.3.0",
    lifespan=lifespan,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_UPLOADS_ROOT = _BACKEND_ROOT / "uploads"
_UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(_UPLOADS_ROOT)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
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
