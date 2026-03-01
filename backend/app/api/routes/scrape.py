from fastapi import APIRouter, HTTPException

from app.schemas.chat import ScrapeRequest
from app.scraper import download_landing_page_assets

router = APIRouter(tags=["scrape"])


@router.post("/api/scrape")
async def scrape_assets(request: ScrapeRequest):
    """Download assets from a landing page URL."""
    result = await download_landing_page_assets(request.url, request.output_dir)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
