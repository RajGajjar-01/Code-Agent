import mimetypes
from pathlib import Path
from typing import Optional

import httpx


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
    """Async client for the WordPress REST API."""

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
            "pages": [
                {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]}
                for p in response.json()
            ],
            "total": int(response.headers.get("X-WP-Total", 0)),
        }

    async def get_page(self, page_id: int) -> dict:
        """Get page by ID."""
        response = await self.client.get(f"{self.api_url}/pages/{page_id}")
        response.raise_for_status()
        p = response.json()
        return {
            "id": p["id"],
            "title": p["title"]["rendered"],
            "content": p["content"]["rendered"],
            "acf": p.get("acf", {}),
        }

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
        """Delete page."""
        response = await self.client.delete(
            f"{self.api_url}/pages/{page_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": page_id, "deleted": True}

    async def list_posts(self, **kwargs) -> dict:
        """List site posts."""
        response = await self.client.get(f"{self.api_url}/posts", params=kwargs)
        response.raise_for_status()
        return {
            "posts": [
                {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]}
                for p in response.json()
            ],
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
        """Delete post."""
        response = await self.client.delete(
            f"{self.api_url}/posts/{post_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": post_id, "deleted": True}

    async def upload_media(self, file_path: str, title: Optional[str] = None) -> dict:
        """Upload file to media library."""
        p = Path(file_path)
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        headers = {
            "Content-Disposition": f'attachment; filename="{p.name}"',
            "Content-Type": mime,
        }
        with open(p, "rb") as f:
            response = await self.client.post(
                f"{self.api_url}/media", content=f.read(), headers=headers
            )
        response.raise_for_status()
        m = response.json()
        if title:
            await self.client.post(f"{self.api_url}/media/{m['id']}", json={"title": title})
        return {"id": m["id"], "url": m["source_url"]}

    async def get_acf_fields(self, post_id: int, post_type: str = "pages") -> dict:
        """Get ACF fields for a page or post."""
        response = await self.client.get(f"{self.api_url}/{post_type}/{post_id}")
        response.raise_for_status()
        data = response.json()
        return {
            "id": data["id"],
            "title": data["title"]["rendered"],
            "acf": data.get("acf", {}),
        }

    async def update_acf_fields(self, post_id: int, fields: dict, post_type: str = "pages") -> dict:
        """Update ACF fields on a page or post."""
        payload = {"acf": fields}
        response = await self.client.post(f"{self.api_url}/{post_type}/{post_id}", json=payload)
        response.raise_for_status()
        data = response.json()
        return {
            "id": data["id"],
            "updated_acf": data.get("acf", {}),
        }

    async def list_acf_field_groups(self) -> dict:
        """List all ACF field groups (requires ACF Pro REST API support).

        Falls back to a basic approach if the ACF Pro API endpoint is unavailable.
        """
        # ACF Pro exposes field groups at /wp-json/acf/v3/
        try:
            response = await self.client.get(f"{self.base_url}/wp-json/acf/v3/field-groups")
            if response.is_success:
                groups = response.json()
                return {
                    "field_groups": [
                        {
                            "id": g.get("id"),
                            "title": g.get("title", {}).get("rendered", g.get("title", "")),
                            "key": g.get("key", ""),
                            "fields": g.get("fields", []),
                        }
                        for g in groups
                    ]
                }
        except Exception:
            # ACF endpoint may not be available if ACF is not installed or REST API is disabled
            # This is expected behavior, not an error
            pass

        # Fallback: try /wp-json/acf/v3/options or return helpful message
        return {
            "field_groups": [],
            "note": "ACF field group listing requires ACF Pro with REST API enabled. "
            "You can still use get_acf_fields and update_acf_fields on individual pages/posts.",
        }

    async def list_themes(self) -> dict:
        """List installed themes."""
        response = await self.client.get(f"{self.api_url}/themes")
        response.raise_for_status()
        themes = response.json()
        return {
            "themes": [
                {
                    "slug": t.get("stylesheet", ""),
                    "name": t.get("name", {}).get("rendered", t.get("name", "")),
                    "status": t.get("status", "inactive"),
                    "version": t.get("version", ""),
                    "template": t.get("template", ""),
                }
                for t in themes
            ]
        }

    async def get_active_theme(self) -> dict:
        """Get the currently active theme details."""
        response = await self.client.get(f"{self.api_url}/themes", params={"status": "active"})
        response.raise_for_status()
        themes = response.json()
        if themes:
            t = themes[0]
            return {
                "slug": t.get("stylesheet", ""),
                "name": t.get("name", {}).get("rendered", t.get("name", "")),
                "version": t.get("version", ""),
                "template": t.get("template", ""),
                "theme_uri": t.get("theme_uri", ""),
            }
        return {"error": "No active theme found."}

    async def create_theme_file(self, theme_slug: str, file_path: str, content: str) -> dict:
        """Create or overwrite a file inside a WP theme."""
        # WordPress doesn't have a native REST API for writing theme files.
        # We use the theme-edit endpoint (WP 5.9+) which edits theme code.
        endpoint = f"{self.base_url}/wp-json/wp/v2/themes/{theme_slug}"

        # First, try the block-based theme file editing API
        payload = {
            "file": file_path,
            "content": content,
        }
        response = await self.client.post(endpoint, json=payload)

        # If the standard endpoint fails, return fallback message
        if response.is_error:
            return {
                "status": "fallback_needed",
                "theme_slug": theme_slug,
                "file_path": file_path,
                "message": (
                    f"Direct theme file writing via REST API returned {response.status_code}. "
                    f"Consider using FTP/SSH or a file manager plugin to upload theme files. "
                    f"The theme file content has been generated and can be manually placed at: "
                    f"wp-content/themes/{theme_slug}/{file_path}"
                ),
                "content_preview": content[:500],
            }

        return {
            "status": "success",
            "theme_slug": theme_slug,
            "file_path": file_path,
            "message": f"File '{file_path}' created/updated in theme '{theme_slug}'.",
        }

    async def read_theme_file(self, theme_slug: str, file_path: str) -> dict:
        """Read a theme file's content."""
        endpoint = f"{self.base_url}/wp-json/wp/v2/themes/{theme_slug}"
        response = await self.client.get(endpoint, params={"file": file_path})

        if response.is_error:
            return {
                "error": f"Could not read theme file '{file_path}' from '{theme_slug}'. "
                f"Status: {response.status_code}",
            }

        data = response.json()
        return {
            "theme_slug": theme_slug,
            "file_path": file_path,
            "content": data.get("content", ""),
        }

    async def activate_theme(self, theme_slug: str) -> dict:
        """Activate a theme by its slug."""
        response = await self.client.post(
            f"{self.api_url}/themes/{theme_slug}",
            json={"status": "active"},
        )
        if response.is_error:
            _raise_for_status(response)

        return {
            "theme_slug": theme_slug,
            "status": "active",
            "message": f"Theme '{theme_slug}' activated successfully.",
        }

    async def get_site_info(self) -> dict:
        response = await self.client.get(f"{self.base_url}/wp-json")
        response.raise_for_status()
        d = response.json()
        return {
            "name": d.get("name"),
            "description": d.get("description"),
            "url": d.get("url"),
        }
