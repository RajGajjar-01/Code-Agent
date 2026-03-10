import mimetypes
import asyncio
import re
from pathlib import Path
from typing import Any, Optional

import httpx


class WordPressAPIError(ValueError):
    def __init__(self, status_code: int, message: str, wp_code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.wp_code = wp_code


def _raise_for_status(response: httpx.Response):
    if response.is_error:
        try:
            detail = response.json()
            msg = detail.get("message") or detail.get("error") or response.text
            code = detail.get("code")
            if code:
                msg = f"{code}: {msg}"
        except Exception:
            msg = response.text
        raise WordPressAPIError(
            status_code=response.status_code,
            message=f"WordPress API error {response.status_code}: {msg}",
            wp_code=code if "code" in locals() else None,
        )


class WordPressClient:
    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.auth = (username, app_password)
        self.client = httpx.AsyncClient(
            auth=self.auth,
            timeout=30.0,
        )
        self._supports_batch_v1: bool | None = None
        self._max_batch_size: int | None = None
        self._acf_field_groups_supported: bool | None = None
        self._menu_items_assignment_key: str | None = None

    async def close(self):
        await self.client.aclose()

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        response = await self.client.request(method, url, **kwargs)
        _raise_for_status(response)
        return response

    async def _request_json(self, method: str, url: str, **kwargs) -> Any:
        response = await self._request(method, url, **kwargs)
        try:
            return response.json()
        except Exception:
            return response.text

    async def _options(self, url: str) -> dict | None:
        try:
            response = await self.client.options(url)
        except Exception:
            return None
        if response.is_error:
            return None
        try:
            return response.json()
        except Exception:
            return None

    async def _detect_batch_v1(self) -> bool:
        if self._supports_batch_v1 is not None:
            return self._supports_batch_v1

        url = f"{self.base_url}/wp-json/batch/v1"
        meta = await self._options(url)
        if not meta:
            self._supports_batch_v1 = False
            return False

        try:
            endpoints = meta.get("endpoints") or []
            if endpoints and isinstance(endpoints, list):
                args = endpoints[0].get("args") or {}
                requests = args.get("requests") or {}
                max_items = requests.get("maxItems")
                if isinstance(max_items, int):
                    self._max_batch_size = max_items
        except Exception:
            pass

        self._supports_batch_v1 = True
        return True

    async def _detect_menu_items_assignment_key(self) -> str:
        if self._menu_items_assignment_key is not None:
            return self._menu_items_assignment_key

        url = f"{self.api_url}/menu-items"
        meta = await self._options(url)
        key: str | None = None
        try:
            endpoints = (meta or {}).get("endpoints") or []
            for ep in endpoints:
                if not isinstance(ep, dict):
                    continue
                if ep.get("methods") != ["POST"] and ep.get("methods") != ["POST", "PUT", "PATCH"]:
                    continue
                args = ep.get("args") or {}
                if isinstance(args, dict):
                    if "menus" in args:
                        key = "menus"
                        break
                    if "menu-id" in args:
                        key = "menu-id"
                        break
        except Exception:
            key = None

        self._menu_items_assignment_key = key or "menu-id"
        return self._menu_items_assignment_key

    async def _batch_v1(self, requests: list[dict], validation: str | None = None) -> dict:
        ok = await self._detect_batch_v1()
        if not ok:
            return {"mode": "client_side", "error": "batch_v1_not_available"}

        payload: dict[str, Any] = {"requests": requests}
        if validation:
            payload["validation"] = validation

        response = await self.client.post(f"{self.base_url}/wp-json/batch/v1", json=payload)
        _raise_for_status(response)
        data = response.json()
        data["mode"] = "batch_v1"
        if self._max_batch_size is not None:
            data["max_batch_size"] = self._max_batch_size
        return data

    async def _bulk_client_side(
        self,
        coros: list,
        concurrency: int = 5,
    ) -> dict:
        sem = asyncio.Semaphore(max(1, concurrency))

        async def run_one(idx: int, c):
            async with sem:
                try:
                    result = await c
                    return {"index": idx, "status": "success", "result": result}
                except Exception as e:
                    return {"index": idx, "status": "error", "error": str(e)}

        results = await asyncio.gather(
            *(run_one(i, c) for i, c in enumerate(coros)),
            return_exceptions=False,
        )
        return {"mode": "client_side", "results": results}

    async def list_pages(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/pages", params=kwargs)
        return {
            "pages": [
                {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]}
                for p in response.json()
            ],
            "total": int(response.headers.get("X-WP-Total", 0)),
            "total_pages": int(response.headers.get("X-WP-TotalPages", 0)),
        }

    def _slugify_title(self, title: str) -> str:
        raw = (title or "").strip().lower()
        raw = re.sub(r"[^a-z0-9]+", "-", raw)
        raw = re.sub(r"-+", "-", raw).strip("-")
        return raw

    def _normalize_title(self, title: str) -> str:
        return re.sub(r"\s+", " ", (title or "").strip()).lower()

    async def find_page_by_slug_or_title(self, title: str) -> dict | None:
        """Best-effort duplicate detection.

        Checks `slug` first, then falls back to `search` and exact title comparison.
        Returns minimal page info if found, otherwise None.
        """
        slug = self._slugify_title(title)
        if slug:
            try:
                resp = await self._request(
                    "GET",
                    f"{self.api_url}/pages",
                    params={"slug": slug, "status": "any", "per_page": 1},
                )
                items = resp.json()
                if isinstance(items, list) and items:
                    p = items[0]
                    return {
                        "id": p.get("id"),
                        "title": (p.get("title") or {}).get("rendered", ""),
                        "link": p.get("link"),
                        "slug": p.get("slug"),
                        "status": p.get("status"),
                    }
            except Exception:
                pass

        # Fallback: search then exact-match on title.rendered (case/whitespace normalized)
        try:
            resp = await self._request(
                "GET",
                f"{self.api_url}/pages",
                params={"search": title, "status": "any", "per_page": 10},
            )
            items = resp.json()
        except Exception:
            items = []

        want = self._normalize_title(title)
        if isinstance(items, list) and want:
            for p in items:
                rendered = (p.get("title") or {}).get("rendered", "")
                if self._normalize_title(rendered) == want:
                    return {
                        "id": p.get("id"),
                        "title": rendered,
                        "link": p.get("link"),
                        "slug": p.get("slug"),
                        "status": p.get("status"),
                    }

        return None

    async def get_page(self, page_id: int) -> dict:
        response = await self._request("GET", f"{self.api_url}/pages/{page_id}")
        p = response.json()
        return {
            "id": p["id"],
            "title": p["title"]["rendered"],
            "content": p["content"]["rendered"],
            "acf": p.get("acf", {}),
        }

    async def create_page(self, title: str, content: str, **kwargs) -> dict:
        data = {"title": title, "content": content, **kwargs}
        response = await self._request("POST", f"{self.api_url}/pages", json=data)
        p = response.json()
        return {"id": p["id"], "link": p["link"], "status": p["status"]}

    async def update_page(self, page_id: int, **kwargs) -> dict:
        response = await self._request("POST", f"{self.api_url}/pages/{page_id}", json=kwargs)
        p = response.json()
        return {"id": p["id"], "link": p["link"], "status": p.get("status")}

    async def delete_page(self, page_id: int, force: bool = True) -> dict:
        response = await self.client.delete(
            f"{self.api_url}/pages/{page_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": page_id, "deleted": True}

    async def list_posts(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/posts", params=kwargs)
        return {
            "posts": [
                {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]}
                for p in response.json()
            ],
            "total": int(response.headers.get("X-WP-Total", 0)),
            "total_pages": int(response.headers.get("X-WP-TotalPages", 0)),
        }

    async def get_post(self, post_id: int) -> dict:
        response = await self._request("GET", f"{self.api_url}/posts/{post_id}")
        p = response.json()
        return {
            "id": p["id"],
            "title": p["title"]["rendered"],
            "content": p["content"]["rendered"],
            "excerpt": p.get("excerpt", {}).get("rendered", ""),
            "status": p.get("status"),
            "link": p.get("link"),
            "date": p.get("date", ""),
            "categories": p.get("categories", []),
            "tags": p.get("tags", []),
            "featured_media": p.get("featured_media", 0),
            "acf": p.get("acf", {}),
        }

    async def create_post(self, title: str, content: str, **kwargs) -> dict:
        data = {"title": title, "content": content, **kwargs}
        response = await self._request("POST", f"{self.api_url}/posts", json=data)
        p = response.json()
        return {"id": p["id"], "link": p["link"], "status": p["status"]}

    async def update_post(self, post_id: int, **kwargs) -> dict:
        response = await self._request("POST", f"{self.api_url}/posts/{post_id}", json=kwargs)
        p = response.json()
        return {"id": p["id"], "link": p.get("link"), "status": p.get("status")}

    async def delete_post(self, post_id: int, force: bool = True) -> dict:
        response = await self.client.delete(
            f"{self.api_url}/posts/{post_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": post_id, "deleted": True}

    async def upload_media(self, file_path: str, title: Optional[str] = None) -> dict:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        headers = {
            "Content-Disposition": f'attachment; filename="{p.name}"',
            "Content-Type": mime,
        }
        with open(p, "rb") as f:
            response = await self._request(
                "POST", f"{self.api_url}/media", content=f.read(), headers=headers
            )
        m = response.json()
        if title:
            await self._request("POST", f"{self.api_url}/media/{m['id']}", json={"title": title})
        return {"id": m["id"], "url": m["source_url"]}

    async def list_media(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/media", params=kwargs)
        return {
            "media": [
                {
                    "id": m.get("id"),
                    "url": m.get("source_url"),
                    "title": (m.get("title") or {}).get("rendered", ""),
                    "mime_type": m.get("mime_type", ""),
                }
                for m in response.json()
            ],
            "total": int(response.headers.get("X-WP-Total", 0)),
            "total_pages": int(response.headers.get("X-WP-TotalPages", 0)),
        }

    async def delete_media(self, media_id: int, force: bool = True) -> dict:
        response = await self.client.delete(
            f"{self.api_url}/media/{media_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": media_id, "deleted": True}

    async def list_categories(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/categories", params=kwargs)
        data = response.json()
        return {
            "categories": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "slug": c.get("slug"),
                    "count": c.get("count", 0),
                }
                for c in data
            ]
        }

    async def create_category(self, name: str, **kwargs) -> dict:
        payload = {"name": name, **kwargs}
        c = await self._request_json("POST", f"{self.api_url}/categories", json=payload)
        if not isinstance(c, dict):
            return {"error": str(c)}
        return {"id": c.get("id"), "name": c.get("name"), "slug": c.get("slug")}

    async def list_tags(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/tags", params=kwargs)
        data = response.json()
        return {
            "tags": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "slug": t.get("slug"),
                    "count": t.get("count", 0),
                }
                for t in data
            ]
        }

    async def create_tag(self, name: str, **kwargs) -> dict:
        payload = {"name": name, **kwargs}
        t = await self._request_json("POST", f"{self.api_url}/tags", json=payload)
        if not isinstance(t, dict):
            return {"error": str(t)}
        return {"id": t.get("id"), "name": t.get("name"), "slug": t.get("slug")}

    async def list_users(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/users", params=kwargs)
        data = response.json()
        return {
            "users": [
                {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "slug": u.get("slug"),
                    "roles": u.get("roles", []),
                }
                for u in data
            ]
        }

    async def get_current_user(self) -> dict:
        u = await self._request_json("GET", f"{self.api_url}/users/me")
        if not isinstance(u, dict):
            return {"error": str(u)}
        return {
            "id": u.get("id"),
            "name": u.get("name"),
            "email": u.get("email", ""),
            "roles": u.get("roles", []),
        }

    async def get_settings(self) -> dict:
        s = await self._request_json("GET", f"{self.api_url}/settings")
        return s if isinstance(s, dict) else {"error": str(s)}

    async def update_settings(self, **kwargs) -> dict:
        s = await self._request_json("POST", f"{self.api_url}/settings", json=kwargs)
        return s if isinstance(s, dict) else {"error": str(s)}

    async def fetch_all_posts(self, per_page: int = 100, **kwargs) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            data = await self.list_posts(page=page, per_page=per_page, **kwargs)
            posts = data.get("posts", [])
            items.extend(posts)
            total_pages = data.get("total_pages", 0)
            if not posts or (isinstance(total_pages, int) and total_pages and page >= total_pages):
                break
            page += 1
        return items

    async def fetch_all_pages(self, per_page: int = 100, **kwargs) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            data = await self.list_pages(page=page, per_page=per_page, **kwargs)
            pages = data.get("pages", [])
            items.extend(pages)
            total_pages = data.get("total_pages", 0)
            if not pages or (isinstance(total_pages, int) and total_pages and page >= total_pages):
                break
            page += 1
        return items

    async def get_acf_fields(self, post_id: int, post_type: str = "pages") -> dict:
        response = await self._request("GET", f"{self.api_url}/{post_type}/{post_id}")
        data = response.json()
        return {
            "id": data["id"],
            "title": data["title"]["rendered"],
            "acf": data.get("acf", {}),
        }

    async def update_acf_fields(self, post_id: int, fields: dict, post_type: str = "pages") -> dict:
        payload = {"acf": fields}
        response = await self._request("POST", f"{self.api_url}/{post_type}/{post_id}", json=payload)
        data = response.json()
        return {
            "id": data["id"],
            "updated_acf": data.get("acf", {}),
        }

    async def list_acf_field_groups(self) -> dict:
        if self._acf_field_groups_supported is False:
            return {
                "field_groups": [],
                "note": "ACF field group listing is not available on this site.",
            }
        try:
            response = await self.client.get(f"{self.base_url}/wp-json/acf/v3/field-groups")
            if response.is_error:
                self._acf_field_groups_supported = False
                return {
                    "field_groups": [],
                    "note": "ACF field group listing is not available on this site.",
                }
            groups = response.json()
            self._acf_field_groups_supported = True
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
            self._acf_field_groups_supported = False
        return {
            "field_groups": [],
            "note": "ACF field group listing requires ACF Pro with REST API enabled. "
            "You can still use get_acf_fields and update_acf_fields on individual pages/posts.",
        }

    async def list_themes(self) -> dict:
        response = await self._request("GET", f"{self.api_url}/themes")
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
        response = await self._request("GET", f"{self.api_url}/themes", params={"status[]": "active"})
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
        endpoint = f"{self.base_url}/wp-json/wp/v2/themes/{theme_slug}"
        payload = {
            "file": file_path,
            "content": content,
        }
        try:
            response = await self.client.post(endpoint, json=payload)
        except Exception as e:
            return {"error": str(e)}
        if response.is_error:
            return {"error": f"Theme file write not supported. Status: {response.status_code}", "status_code": response.status_code}
        return {
            "status": "success",
            "theme_slug": theme_slug,
            "file_path": file_path,
            "message": f"File '{file_path}' created/updated in theme '{theme_slug}'.",
        }

    async def read_theme_file(self, theme_slug: str, file_path: str) -> dict:
        endpoint = f"{self.base_url}/wp-json/wp/v2/themes/{theme_slug}"
        try:
            response = await self.client.get(endpoint, params={"file": file_path})
        except Exception as e:
            return {"error": str(e)}
        if response.is_error:
            return {"error": f"Theme file read not supported. Status: {response.status_code}", "status_code": response.status_code}
        data = response.json()
        return {
            "theme_slug": theme_slug,
            "file_path": file_path,
            "content": data.get("content", ""),
        }

    async def activate_theme(self, theme_slug: str) -> dict:
        try:
            response = await self.client.post(
                f"{self.api_url}/themes/{theme_slug}",
                json={"status": "active"},
            )
        except Exception as e:
            return {"error": str(e)}
        if response.is_error:
            return {"error": f"Theme activation not supported. Status: {response.status_code}", "status_code": response.status_code}
        try:
            data = response.json()
        except Exception:
            data = {}
        return {"theme_slug": theme_slug, "status": "active", "result": data}

    async def get_site_info(self) -> dict:
        response = await self._request("GET", f"{self.base_url}/wp-json")
        d = response.json()
        return {
            "name": d.get("name"),
            "description": d.get("description"),
            "url": d.get("url"),
        }

    async def _detect_menus_supported(self) -> bool:
        url = f"{self.api_url}/menus"
        meta = await self._options(url)
        return bool(meta)

    async def list_menus(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/menus", params=kwargs)
        data = response.json()
        menus = []
        for m in data:
            menus.append(
                {
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "slug": m.get("slug"),
                    "count": m.get("count"),
                }
            )
        return {"menus": menus}

    async def create_menu(self, name: str, **kwargs) -> dict:
        ok = await self._detect_menus_supported()
        if not ok:
            raise ValueError(
                "Menus endpoint not available on this WordPress site. "
                "This typically requires WordPress 6.8+ (or an appropriate plugin) exposing /wp/v2/menus."
            )
        payload = {"name": name, **kwargs}
        # Back-compat for any code paths expecting the older alias.
        payload.setdefault("menu-name", name)
        m = await self._request_json("POST", f"{self.api_url}/menus", json=payload)
        if not isinstance(m, dict):
            return {"error": str(m)}
        return {
            "id": m.get("id"),
            "name": m.get("name"),
            "slug": m.get("slug"),
        }

    async def list_menu_locations(self) -> dict:
        response = await self._request("GET", f"{self.api_url}/menu-locations")
        data = response.json()
        locations: list[dict[str, Any]] = []
        if isinstance(data, list):
            for loc in data:
                if not isinstance(loc, dict):
                    continue
                locations.append(
                    {
                        "location": loc.get("location") or loc.get("name") or loc.get("slug"),
                        "name": loc.get("name"),
                        "description": loc.get("description"),
                        "menu": loc.get("menu"),
                    }
                )
        return {"menu_locations": locations}

    async def assign_menu_locations(self, menu_id: int, locations: list[str]) -> dict:
        if not menu_id:
            raise ValueError("menu_id is required")
        clean = [str(x).strip() for x in (locations or []) if str(x).strip()]
        payload = {"locations": clean}
        m = await self._request_json("POST", f"{self.api_url}/menus/{menu_id}", json=payload)
        if not isinstance(m, dict):
            return {"error": str(m)}
        return {"id": m.get("id") or menu_id, "locations": m.get("locations") or clean}

    async def delete_menu(self, menu_id: int, force: bool = True) -> dict:
        params = {"force": "true" if force else "false"}
        response = await self.client.delete(f"{self.api_url}/menus/{menu_id}", params=params)
        _raise_for_status(response)
        return {"id": menu_id, "deleted": True}

    async def list_menu_items(self, **kwargs) -> dict:
        response = await self._request("GET", f"{self.api_url}/menu-items", params=kwargs)
        data = response.json()
        items = []
        for it in data:
            title_obj = it.get("title") or {}
            title = title_obj.get("rendered") if isinstance(title_obj, dict) else title_obj
            items.append(
                {
                    "id": it.get("id"),
                    "title": title,
                    "url": it.get("url"),
                    "menu_order": it.get("menu_order"),
                    "parent": it.get("parent"),
                    "type": it.get("type"),
                    "object": it.get("object"),
                    "object_id": it.get("object_id"),
                    "status": it.get("status"),
                }
            )
        return {
            "menu_items": items,
            "total": int(response.headers.get("X-WP-Total", 0)),
            "total_pages": int(response.headers.get("X-WP-TotalPages", 0)),
        }

    async def create_menu_item(
        self,
        menu_id: int,
        title: str,
        type: str = "custom",
        url: str | None = None,
        object_id: int | None = None,
        object: str | None = None,
        parent: int | None = None,
        menu_order: int | None = None,
        status: str = "publish",
        **kwargs,
    ) -> dict:
        if (type or "").strip() == "custom" and not (url or "").strip():
            raise ValueError("url is required when using a custom menu item type")

        menu_id_int = int(menu_id)

        base_payload: dict[str, Any] = {
            "title": title,
            "type": type,
            "status": status,
        }
        if url is not None:
            base_payload["url"] = url
        if object_id is not None:
            base_payload["object_id"] = object_id
        if object is not None:
            base_payload["object"] = object
        if parent is not None:
            base_payload["parent"] = parent
        if menu_order is not None:
            base_payload["menu_order"] = menu_order
        base_payload.update(kwargs)

        # Different WP installs accept different ways to assign menu items to a menu.
        # We try the detected key first, but fall back based on WP error codes/messages.
        assignment_key = await self._detect_menu_items_assignment_key()

        candidates: list[dict[str, Any]] = []
        if assignment_key == "menus":
            candidates.append({**base_payload, "menus": menu_id_int})
            candidates.append({**base_payload, "menus": [menu_id_int]})
            candidates.append({**base_payload, "menu-id": menu_id_int})
        else:
            candidates.append({**base_payload, "menu-id": menu_id_int})
            candidates.append({**base_payload, "menus": menu_id_int})
            candidates.append({**base_payload, "menus": [menu_id_int]})

        last_err: Exception | None = None
        it: Any = None
        for payload in candidates:
            try:
                it = await self._request_json("POST", f"{self.api_url}/menu-items", json=payload)
                last_err = None
                break
            except WordPressAPIError as e:
                last_err = e
                msg = str(e)
                # If this is a known "wrong assignment param" case, try next candidate.
                if (
                    e.status_code == 400
                    and (
                        e.wp_code in {"rest_invalid_param", "invalid_menu_id"}
                        or "Invalid parameter(s): menus" in msg
                        or "Invalid menu ID" in msg
                    )
                ):
                    continue
                raise

        if last_err is not None:
            raise last_err

        if not isinstance(it, dict):
            return {"error": str(it)}

        menu_from_response: int | None = None
        menus = it.get("menus")
        if isinstance(menus, int):
            menu_from_response = menus
        elif isinstance(menus, list) and menus:
            try:
                menu_from_response = int(menus[0])
            except Exception:
                menu_from_response = None
        if menu_from_response is None:
            maybe_menu_id = it.get("menu-id") or it.get("menu_id")
            if maybe_menu_id is not None:
                try:
                    menu_from_response = int(maybe_menu_id)
                except Exception:
                    menu_from_response = None

        return {
            "id": it.get("id"),
            "menu_id": menu_from_response or menu_id,
            "title": (it.get("title") or {}).get("rendered")
            if isinstance(it.get("title"), dict)
            else it.get("title"),
            "url": it.get("url"),
            "parent": it.get("parent"),
            "menu_order": it.get("menu_order"),
            "type": it.get("type"),
            "status": it.get("status"),
        }

    async def update_menu_item(self, menu_item_id: int, **kwargs) -> dict:
        it = await self._request_json(
            "POST",
            f"{self.api_url}/menu-items/{menu_item_id}",
            json=kwargs,
        )
        if not isinstance(it, dict):
            return {"error": str(it)}
        return {
            "id": it.get("id"),
            "status": it.get("status"),
            "parent": it.get("parent"),
            "menu_order": it.get("menu_order"),
            "url": it.get("url"),
        }

    async def delete_menu_item(self, menu_item_id: int, force: bool = True) -> dict:
        response = await self.client.delete(
            f"{self.api_url}/menu-items/{menu_item_id}",
            params={"force": "true" if force else "false"},
        )
        _raise_for_status(response)
        return {"id": menu_item_id, "deleted": True}

    async def bulk_create_menus(self, menus: list[dict], validation: str | None = None) -> dict:
        requests = []
        for item in menus:
            name = item.get("name") or item.get("menu-name")
            if not name:
                requests.append({"method": "POST", "path": "/wp/v2/menus", "body": item})
                continue
            body = {**item}
            body.pop("name", None)
            body.setdefault("name", name)
            body.setdefault("menu-name", name)
            requests.append({"method": "POST", "path": "/wp/v2/menus", "body": body})

        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch

        coros = []
        for item in menus:
            name = item.get("name") or item.get("menu-name")
            if not name:
                async def _missing():
                    raise ValueError("name is required")
                coros.append(_missing())
            else:
                body = {k: v for k, v in item.items() if k not in {"name"}}
                coros.append(self.create_menu(name=name, **body))
        return await self._bulk_client_side(coros)

    async def bulk_create_menu_items(
        self,
        items: list[dict],
        validation: str | None = None,
        concurrency: int = 5,
    ) -> dict:
        assignment_key = await self._detect_menu_items_assignment_key()
        requests = []
        for item in items:
            body = {**(item or {})}
            menu_id = body.pop("menu_id", None)
            if menu_id is None:
                menu_id = body.pop("menu-id", None)
            if menu_id is not None:
                if assignment_key == "menus":
                    body["menus"] = int(menu_id)
                else:
                    body["menu-id"] = menu_id
            body.pop("menu-item-parent-id", None)
            body.pop("menu-item-title", None)
            body.pop("menu-item-type", None)
            body.pop("menu-item-url", None)
            body.pop("menu-item-object-id", None)
            body.pop("menu-item-object", None)
            body.pop("menu-item-position", None)
            body.pop("menu-item-status", None)
            requests.append({"method": "POST", "path": "/wp/v2/menu-items", "body": body})

        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch

        coros = []
        for item in items:
            menu_id = item.get("menu_id") or item.get("menu-id")
            coros.append(
                self.create_menu_item(
                    menu_id=menu_id,
                    title=item.get("title") or item.get("menu-item-title") or "",
                    type=item.get("type") or item.get("menu-item-type") or "custom",
                    url=item.get("url") or item.get("menu-item-url"),
                    object_id=item.get("object_id") or item.get("menu-item-object-id"),
                    object=item.get("object") or item.get("menu-item-object"),
                    parent=item.get("parent") or item.get("menu-item-parent-id"),
                    menu_order=item.get("menu_order") or item.get("menu-item-position"),
                    status=item.get("status") or item.get("menu-item-status") or "publish",
                )
            )
        return await self._bulk_client_side(coros, concurrency=concurrency)

    async def bulk_create_menu_tree(
        self,
        items: list[dict],
        menu_name: str | None = None,
        menu_id: int | None = None,
    ) -> dict:
        if menu_id is None:
            clean_name = (menu_name or "").strip()
            if not clean_name:
                raise ValueError("menu_name is required when menu_id is not provided")
            menu = await self.create_menu(name=clean_name)
            created_menu_id = menu.get("id")
            if not created_menu_id:
                return {"error": "menu_create_failed", "menu": menu}
            try:
                menu_id = int(created_menu_id)
            except Exception:
                return {"error": "menu_create_failed", "menu": menu}
        else:
            menu = {"id": menu_id}

        flat: list[dict] = []

        def walk(children: list[dict], parent_ref: str | None = None):
            for idx, it in enumerate(children):
                ref = it.get("ref") or f"{parent_ref or 'root'}:{idx}"
                flat.append({"ref": ref, "parent_ref": parent_ref, **it})
                walk(it.get("children") or [], parent_ref=ref)

        walk(items)

        created_by_ref: dict[str, int] = {}
        results: list[dict] = []

        # Create items sequentially in a way that ensures parents exist before children.
        # (We still keep the function signature ready for future optimization.)
        for it in flat:
            parent_id = 0
            parent_ref = it.get("parent_ref")
            if parent_ref:
                parent_id = created_by_ref.get(parent_ref, 0)

            it_type = (it.get("type") or "custom").strip()
            it_url = it.get("url")
            if it_type == "custom" and not (it_url or "").strip():
                raise ValueError("url is required when using a custom menu item type")

            res = await self.create_menu_item(
                menu_id=menu_id,
                title=(it.get("title") or "").strip(),
                url=it.get("url"),
                type=it.get("type") or "custom",
                parent=parent_id or 0,
                status=it.get("status") or "publish",
            )
            results.append({"ref": it.get("ref"), "result": res})
            if res.get("id"):
                created_by_ref[it.get("ref")] = int(res["id"])

        return {"menu": menu, "items": results}

    async def bulk_update_pages(self, updates: list[dict], validation: str | None = None) -> dict:
        requests = []
        for item in updates:
            page_id = item.get("page_id") or item.get("id")
            if not page_id:
                requests.append({"method": "POST", "path": "/wp/v2/pages", "body": item})
                continue
            body = {k: v for k, v in item.items() if k not in {"id", "page_id"}}
            requests.append({"method": "POST", "path": f"/wp/v2/pages/{page_id}", "body": body})
        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch
        coros = []
        for item in updates:
            page_id = item.get("page_id") or item.get("id")
            if not page_id:
                coros.append(self.create_page(**item))
            else:
                body = {k: v for k, v in item.items() if k not in {"id", "page_id"}}
                coros.append(self.update_page(page_id, **body))
        return await self._bulk_client_side(coros)

    async def bulk_delete_pages(self, page_ids: list[int], force: bool = True, validation: str | None = None) -> dict:
        requests = [
            {
                "method": "DELETE",
                "path": f"/wp/v2/pages/{pid}?force={'true' if force else 'false'}",
            }
            for pid in page_ids
        ]
        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch
        coros = [self.delete_page(pid, force=force) for pid in page_ids]
        return await self._bulk_client_side(coros)

    async def bulk_update_posts(self, updates: list[dict], validation: str | None = None) -> dict:
        requests = []
        for item in updates:
            post_id = item.get("post_id") or item.get("id")
            if not post_id:
                requests.append({"method": "POST", "path": "/wp/v2/posts", "body": item})
                continue
            body = {k: v for k, v in item.items() if k not in {"id", "post_id"}}
            requests.append({"method": "POST", "path": f"/wp/v2/posts/{post_id}", "body": body})
        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch
        coros = []
        for item in updates:
            post_id = item.get("post_id") or item.get("id")
            if not post_id:
                coros.append(self.create_post(**item))
            else:
                body = {k: v for k, v in item.items() if k not in {"id", "post_id"}}
                coros.append(self.update_post(post_id, **body))
        results = await self._bulk_client_side(coros)
        return results

    async def bulk_delete_posts(self, post_ids: list[int], force: bool = True, validation: str | None = None) -> dict:
        requests = [
            {
                "method": "DELETE",
                "path": f"/wp/v2/posts/{pid}?force={'true' if force else 'false'}",
            }
            for pid in post_ids
        ]
        batch = await self._batch_v1(requests, validation=validation)
        if batch.get("mode") == "batch_v1" and "responses" in batch:
            return batch
        coros = [self.delete_post(pid, force=force) for pid in post_ids]
        return await self._bulk_client_side(coros)

    async def bulk_upload_media(self, files: list[dict], concurrency: int = 3) -> dict:
        coros = []
        for item in files:
            file_path = item.get("file_path") or item.get("path")
            title = item.get("title")
            if not file_path:
                async def _missing():
                    raise ValueError("file_path is required")
                coros.append(_missing())
            else:
                coros.append(self.upload_media(str(file_path), title=title))
        return await self._bulk_client_side(coros, concurrency=concurrency)
