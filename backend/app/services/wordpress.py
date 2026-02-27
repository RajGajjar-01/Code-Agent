

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
        response = await self.client.post(
            f"{self.api_url}/pages/{page_id}", json=kwargs
        )
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



    async def upload_media(
        self, file_path: str, title: Optional[str] = None
    ) -> dict:
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
            await self.client.post(
                f"{self.api_url}/media/{m['id']}", json={"title": title}
            )
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

    async def update_acf_fields(
        self, post_id: int, fields: dict, post_type: str = "pages"
    ) -> dict:
        """Update ACF fields on a page or post."""
        payload = {"acf": fields}
        response = await self.client.post(
            f"{self.api_url}/{post_type}/{post_id}", json=payload
        )
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
            response = await self.client.get(
                f"{self.base_url}/wp-json/acf/v3/field-groups"
            )
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
        response = await self.client.get(
            f"{self.api_url}/themes", params={"status": "active"}
        )
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

    async def create_theme_file(
        self, theme_slug: str, file_path: str, content: str
    ) -> dict:
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

        # If the standard endpoint fails, try using the WP filesystem approach
        if response.is_error:
            # Fallback: Use the WordPress theme file editor AJAX endpoint
            edit_url = (
                f"{self.base_url}/wp-admin/admin-ajax.php"
            )
            form_data = {
                "action": "edit-theme-plugin-file",
                "theme": theme_slug,
                "file": file_path,
                "newcontent": content,
                "nonce": "",  # Would need to be fetched
            }
            # If AJAX also fails, report what we know
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
        """Get site overview."""
        response = await self.client.get(f"{self.base_url}/wp-json")
        response.raise_for_status()
        d = response.json()
        return {
            "name": d.get("name"),
            "description": d.get("description"),
            "url": d.get("url"),
        }


# ── IDE file-system helpers (standalone, not part of WordPressClient) ──

import os
import shutil
import tempfile

from app.core.config import settings
from app.schemas.ide import FileNode, FileReadResponse, FileWriteResponse

ALLOWED_EXTENSIONS = {
    ".php", ".css", ".js", ".json", ".html",
    ".txt", ".md", ".xml", ".svg", ".ts", ".jsx",
}

SKIP_NAMES = {"node_modules", ".git", "vendor", "__pycache__", ".DS_Store"}

EXTENSION_LANGUAGE_MAP = {
    ".php": "php",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".css": "css",
    ".json": "json",
    ".html": "html",
    ".md": "markdown",
    ".xml": "xml",
}


def validate_path(relative_path: str) -> tuple[bool, str]:
    """Ensure the resolved path stays within WP_ROOT_PATH."""
    if not relative_path:
        return False, "Path cannot be empty"
    if "\x00" in relative_path:
        return False, "Path contains null bytes"
    if os.path.isabs(relative_path):
        return False, "Absolute paths are not allowed"
    if ".." in relative_path.split("/"):
        return False, "Path traversal (..) is not allowed"

    resolved = os.path.realpath(os.path.join(settings.WP_ROOT_PATH, relative_path))
    wp_root = os.path.realpath(settings.WP_ROOT_PATH)

    if not resolved.startswith(wp_root + os.sep) and resolved != wp_root:
        return False, "Path is outside the WordPress root"

    return True, ""


def _is_editable(relative_path: str) -> bool:
    """Check whether a relative path falls inside one of WP_EDITABLE_DIRS."""
    for d in settings.WP_EDITABLE_DIRS:
        if relative_path == d or relative_path.startswith(d + "/"):
            return True
    return False


def get_file_tree(base_dir: str, relative_to: str, _depth: int = 0) -> FileNode:
    """Recursively build a FileNode tree for *base_dir*.

    *relative_to* is the WP_ROOT_PATH so all emitted paths are relative.
    Max recursion depth is 5.
    """
    abs_path = os.path.realpath(base_dir)
    rel_path = os.path.relpath(abs_path, os.path.realpath(relative_to))
    name = os.path.basename(abs_path)

    if not os.path.isdir(abs_path):
        ext = os.path.splitext(name)[1].lower()
        return FileNode(
            name=name,
            path=rel_path,
            type="file",
            extension=ext or None,
            size=os.path.getsize(abs_path),
        )

    children: list[FileNode] | None = None
    if _depth < 5:
        entries: list[FileNode] = []
        try:
            items = sorted(os.listdir(abs_path))
        except PermissionError:
            items = []

        dirs: list[FileNode] = []
        files: list[FileNode] = []
        for item in items:
            if item in SKIP_NAMES:
                continue
            full = os.path.join(abs_path, item)
            if os.path.isdir(full):
                dirs.append(get_file_tree(full, relative_to, _depth + 1))
            elif os.path.isfile(full):
                ext = os.path.splitext(item)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    item_rel = os.path.relpath(full, os.path.realpath(relative_to))
                    files.append(
                        FileNode(
                            name=item,
                            path=item_rel,
                            type="file",
                            extension=ext,
                            size=os.path.getsize(full),
                        )
                    )
        # directories first (alphabetical), then files (alphabetical)
        children = dirs + files

    return FileNode(
        name=name,
        path=rel_path,
        type="directory",
        children=children,
    )


def read_file(relative_path: str) -> FileReadResponse:
    """Read a file from the WordPress root, with security checks."""
    ok, err = validate_path(relative_path)
    if not ok:
        raise ValueError(err)

    abs_path = os.path.realpath(os.path.join(settings.WP_ROOT_PATH, relative_path))

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"File not found: {relative_path}")

    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension '{ext}' is not allowed")

    size = os.path.getsize(abs_path)
    if size > settings.MAX_FILE_SIZE_KB * 1024:
        raise ValueError(f"File exceeds {settings.MAX_FILE_SIZE_KB}KB limit")

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    language = EXTENSION_LANGUAGE_MAP.get(ext, "plaintext")
    last_modified = os.path.getmtime(abs_path)

    return FileReadResponse(
        path=relative_path,
        content=content,
        language=language,
        size=size,
        last_modified=last_modified,
    )


def write_file(relative_path: str, content: str) -> FileWriteResponse:
    """Atomically write content to a file inside an editable directory."""
    ok, err = validate_path(relative_path)
    if not ok:
        raise ValueError(err)

    if not _is_editable(relative_path):
        raise PermissionError("Writing is only allowed inside editable directories (themes/plugins/mu-plugins)")

    ext = os.path.splitext(relative_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension '{ext}' is not allowed")

    abs_path = os.path.realpath(os.path.join(settings.WP_ROOT_PATH, relative_path))

    # Create backup if file already exists
    if os.path.isfile(abs_path):
        shutil.copy2(abs_path, abs_path + ".bak")

    # Atomic write: write to temp, then rename
    dir_name = os.path.dirname(abs_path)
    os.makedirs(dir_name, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        shutil.move(tmp_path, abs_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    last_modified = os.path.getmtime(abs_path)

    return FileWriteResponse(
        path=relative_path,
        success=True,
        message=f"File saved: {relative_path}",
        last_modified=last_modified,
    )


def create_node(parent_path: str, name: str, node_type: str) -> str:
    """Create a new file or directory inside parent_path."""
    full_rel_path = os.path.join(parent_path, name)
    ok, err = validate_path(full_rel_path)
    if not ok:
        raise ValueError(err)

    if not _is_editable(full_rel_path):
        raise PermissionError("Creation is only allowed inside editable directories")

    abs_path = os.path.realpath(os.path.join(settings.WP_ROOT_PATH, full_rel_path))

    if os.path.exists(abs_path):
        raise FileExistsError(f"Path already exists: {full_rel_path}")

    if node_type == "directory":
        os.makedirs(abs_path, exist_ok=True)
    else:
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{ext}' is not allowed")

        # Create empty file
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write("")

    return full_rel_path
