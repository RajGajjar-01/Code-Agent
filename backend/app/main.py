from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, drive, scrape
from app.core.config import settings
from app.services.wordpress import WordPressClient

wp_client: Optional[WordPressClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global wp_client

    if settings.WP_BASE_URL and settings.WP_USERNAME and settings.WP_APP_PASSWORD:
        wp_client = WordPressClient(
            settings.WP_BASE_URL, settings.WP_USERNAME, settings.WP_APP_PASSWORD
        )

    chat.wp_client = wp_client

    yield

    if wp_client:
        await wp_client.close()


app = FastAPI(
    title="WordPress Agent",
    description="AI-powered WordPress site builder with Google Drive integration",
    version="0.3.0",
    lifespan=lifespan,
)

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
app.include_router(scrape.router)


@app.get("/health")
async def health():
    return {
        "status": "running",
        "groq": bool(settings.GROQ_API_KEY),
        "wp": bool(wp_client),
        "google_oauth": bool(settings.GOOGLE_CLIENT_ID),
    }
