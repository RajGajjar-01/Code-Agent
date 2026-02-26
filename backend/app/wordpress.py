import httpx
from typing import Optional

def _raise_for_status(response: httpx.Response):
    """Raise with WordPress error message body if request failed."""
    if response.is_error:
        try:
            detail = response.json()
            msg = detail.get("message") or detail.get("error") or response.text
        except Exception:
            msg = response.text
        raise ValueError(f"WordPress API error {response.status_code}: {msg}")

class WordPressClient:
    """Async client for WordPress API."""

    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.auth = (username, app_password)
        self.client = httpx.AsyncClient(
            auth=self.auth,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    async def close(self):
        """Close client sessions."""
        await self.client.aclose()

    async def list_pages(self, **kwargs) -> dict:
        """List site pages."""
        response = await self.client.get(f"{self.api_url}/pages", params=kwargs)
        response.raise_for_status()
        return {
            "pages": [{"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]} for p in response.json()],
            "total": int(response.headers.get("X-WP-Total", 0)),
        }

    async def get_page(self, page_id: int) -> dict:
        """Get page by ID."""
        response = await self.client.get(f"{self.api_url}/pages/{page_id}")
        response.raise_for_status()
        p = response.json()
        return {"id": p["id"], "title": p["title"]["rendered"], "content": p["content"]["rendered"], "acf": p.get("acf", {})}

    async def create_page(self, title: str, content: str, **kwargs) -> dict:
        """Create new page."""
        data = {"title": title, "content": content, **kwargs}
        response = await self.client.post(f"{self.api_url}/pages", json=data)
        response.raise_for_status()
        p = response.json()
        return {"id": p["id"], "link": p["link"], "status": p["status"]}

    async def update_page(self, page_id: int, **kwargs) -> dict:
        """Update existing page."""
        response = await self.client.post(f"{self.api_url}/pages/{page_id}", json=kwargs)
        response.raise_for_status()
        p = response.json()
        return {"id": p["id"], "link": p["link"]}

    async def delete_page(self, page_id: int, force: bool = True) -> dict:
        """Delete page. Defaults force=True to bypass WordPress trash."""
        response = await self.client.delete(f"{self.api_url}/pages/{page_id}", params={"force": "true" if force else "false"})
        _raise_for_status(response)
        return {"id": page_id, "deleted": True}

    async def list_posts(self, **kwargs) -> dict:
        """List site posts."""
        response = await self.client.get(f"{self.api_url}/posts", params=kwargs)
        response.raise_for_status()
        return {
            "posts": [{"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]} for p in response.json()],
            "total": int(response.headers.get("X-WP-Total", 0)),
        }

    async def create_post(self, title: str, content: str, **kwargs) -> dict:
        """Create new post."""
        data = {"title": title, "content": content, **kwargs}
        response = await self.client.post(f"{self.api_url}/posts", json=data)
        response.raise_for_status()
        p = response.json()
        return {"id": p["id"], "link": p["link"], "status": p["status"]}

    async def delete_post(self, post_id: int, force: bool = True) -> dict:
        """Delete post. Defaults force=True to bypass WordPress trash."""
        response = await self.client.delete(f"{self.api_url}/posts/{post_id}", params={"force": "true" if force else "false"})
        _raise_for_status(response)
        return {"id": post_id, "deleted": True}

    async def upload_media(self, file_path: str, title: Optional[str] = None) -> dict:
        """Upload file to media library."""
        from pathlib import Path
        import mimetypes
        p = Path(file_path)
        headers = {"Content-Disposition": f'attachment; filename="{p.name}"', "Content-Type": mimetypes.guess_type(str(p))[0]}
        with open(p, "rb") as f:
            response = await self.client.post(f"{self.api_url}/media", content=f.read(), headers=headers)
        response.raise_for_status()
        m = response.json()
        if title:
            await self.client.post(f"{self.api_url}/media/{m['id']}", json={"title": title})
        return {"id": m["id"], "url": m["source_url"]}

    async def get_site_info(self) -> dict:
        """Get site overview."""
        response = await self.client.get(f"{self.base_url}/wp-json")
        response.raise_for_status()
        d = response.json()
        return {"name": d.get("name"), "description": d.get("description"), "url": d.get("url")}
