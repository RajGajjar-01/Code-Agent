import asyncio
import hashlib
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Optional

import httpx
from bs4 import BeautifulSoup

ASSET_DIR = Path("backend/assets")


async def download_landing_page_assets(url: str, output_dir: Optional[str] = None) -> dict:
    """Scrape and download website assets."""
    base_dir = Path(output_dir) if output_dir else ASSET_DIR
    for d in ["images", "css", "js", "fonts", "other"]:
        (base_dir / d).mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            return {"error": f"Failed to fetch URL: {str(e)}"}

        assets = []
        # Images
        for img in soup.find_all("img"):
            if src := img.get("src") or img.get("data-src"):
                assets.append(("images", urljoin(url, src)))
        # Link tags (CSS, Icons, Fonts)
        for link in soup.find_all("link"):
            href = link.get("href")
            if not href:
                continue
            full_url = urljoin(url, href)
            ext = Path(urlparse(full_url).path).suffix.lower()
            if link.get("rel") == ["stylesheet"] or ext == ".css":
                assets.append(("css", full_url))
            elif ext in [".woff", ".woff2", ".ttf", ".otf"]:
                assets.append(("fonts", full_url))
            elif "icon" in (link.get("rel") or []):
                assets.append(("images", full_url))
        # Scripts
        for script in soup.find_all("script", src=True):
            assets.append(("js", urljoin(url, script.get("src"))))

        downloaded = []
        errors = []
        seen = set()

        async def _dl(target_type, asset_url):
            if asset_url in seen:
                return
            seen.add(asset_url)
            try:
                fname = os.path.basename(urlparse(asset_url).path)
                if not fname:
                    # MD5 is fine for generating unique filenames (not security-related)
                    hash_digest = hashlib.md5(asset_url.encode(), usedforsecurity=False).hexdigest()
                    fname = f"asset_{hash_digest[:8]}"

                target_path = base_dir / target_type / fname
                r = await client.get(asset_url)
                r.raise_for_status()
                with open(target_path, "wb") as f:
                    f.write(r.content)
                downloaded.append({"type": target_type, "url": asset_url, "path": str(target_path)})
            except Exception as e:
                errors.append({"url": asset_url, "error": str(e)})

        await asyncio.gather(*[_dl(t, u) for t, u in assets])

        return {
            "url": url,
            "summary": {
                t: len([d for d in downloaded if d["type"] == t])
                for t in ["images", "css", "js", "fonts", "other"]
            },
            "total_downloaded": len(downloaded),
            "errors": errors,
        }
