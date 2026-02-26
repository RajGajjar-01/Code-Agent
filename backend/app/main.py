from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, chat, drive, scrape
from app.core.config import settings
from app.services.wordpress import WordPressClient

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

wp_client: Optional[WordPressClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global wp_client

    # Initialize WordPress client
    if settings.WP_BASE_URL and settings.WP_USERNAME and settings.WP_APP_PASSWORD:
        wp_client = WordPressClient(
            settings.WP_BASE_URL, settings.WP_USERNAME, settings.WP_APP_PASSWORD
        )

    # Inject WP client into chat route module
    chat.wp_client = wp_client

    yield

    # Shutdown
    if wp_client:
        await wp_client.close()


app = FastAPI(
    title="WordPress Agent",
    description="AI-powered WordPress site builder with Google Drive integration",
    version="0.2.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(drive.router)
app.include_router(chat.router)
app.include_router(scrape.router)


# ── Health Check ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "running",
        "groq": bool(settings.GROQ_API_KEY),
        "wp": bool(wp_client),
        "google_oauth": bool(settings.GOOGLE_CLIENT_ID),
    }


# ── Serve Frontend ───────────────────────────────────────────
if FRONTEND_DIR.exists():
    app.mount(
        "/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend"
    )
