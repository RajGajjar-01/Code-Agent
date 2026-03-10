from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.crypto import maybe_decrypt_secret
from app.core.database import get_db
from app.models.wordpress_site import WordPressSite
from app.models.user import User
from app.services.wordpress import WordPressClient
from app.schemas.menus import (
    BulkCreateMenuItemsRequest,
    BulkCreateMenusRequest,
    CreateMenuTreeRequest,
)


router = APIRouter(prefix="/api/menus", tags=["menus"])


async def _get_wp_client(
    *,
    wp_site_id: int | None,
    current_user: User,
    db: AsyncSession,
) -> tuple[WordPressClient, WordPressClient | None]:
    """Return a WordPressClient for the request.

    If wp_site_id is provided, create a per-request client using encrypted credentials.
    Otherwise use the global client configured from env vars.

    Returns (client_to_use, created_client_or_none).
    """

    if wp_site_id is not None:
        res = await db.execute(
            select(WordPressSite).where(
                WordPressSite.id == wp_site_id,
                WordPressSite.user_id == current_user.id,
            )
        )
        site = res.scalar_one_or_none()
        if not site:
            raise HTTPException(status_code=404, detail="WordPress site not found")

        app_password = maybe_decrypt_secret(site.app_password_encrypted)
        created = WordPressClient(site.base_url, site.username, app_password)
        return created, created

    raise HTTPException(
        status_code=400,
        detail="wp_site_id is required for menu operations. Select an active WordPress site and retry.",
    )


@router.get("")
async def list_menus(
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.list_menus()
    finally:
        if created:
            await created.close()


@router.post("/items/{menu_item_id}")
async def update_menu_item(
    menu_item_id: int,
    body: dict,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        allowed = {"parent", "menu_order", "status", "title", "url"}
        payload = {k: v for k, v in (body or {}).items() if k in allowed}
        if not payload:
            raise HTTPException(status_code=400, detail="No updatable fields provided")
        return await wp.update_menu_item(menu_item_id=menu_item_id, **payload)
    finally:
        if created:
            await created.close()


@router.delete("/items/{menu_item_id}")
async def delete_menu_item(
    menu_item_id: int,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.delete_menu_item(menu_item_id=menu_item_id, force=True)
    finally:
        if created:
            await created.close()


@router.post("")
async def create_menu(
    body: dict,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    name = (body.get("name") or body.get("menu-name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.create_menu(name=name)
    finally:
        if created:
            await created.close()


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: int,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.delete_menu(menu_id)
    finally:
        if created:
            await created.close()


@router.get("/locations")
async def list_menu_locations(
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.list_menu_locations()
    finally:
        if created:
            await created.close()


@router.post("/{menu_id}/locations")
async def assign_menu_locations(
    menu_id: int,
    body: dict,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    locations = body.get("locations")
    if not isinstance(locations, list) or not [x for x in locations if str(x).strip()]:
        raise HTTPException(status_code=400, detail="locations must be a non-empty list")

    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        return await wp.assign_menu_locations(menu_id=menu_id, locations=locations)
    finally:
        if created:
            await created.close()


@router.get("/items")
async def list_menu_items(
    menu_id: int | None = None,
    wp_site_id: int | None = None,
    per_page: int = 100,
    page: int = 1,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        params: dict = {"per_page": min(per_page, 100), "page": max(page, 1)}
        if menu_id is not None:
            params["menus"] = menu_id
        return await wp.list_menu_items(**params)
    finally:
        if created:
            await created.close()


@router.post("/items")
async def create_menu_item(
    body: dict,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)

    menu_id = body.get("menu_id") or body.get("menu-id")
    if not menu_id:
        raise HTTPException(status_code=400, detail="menu_id is required")

    title = (body.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    try:
        return await wp.create_menu_item(
            menu_id=int(menu_id),
            title=title,
            type=body.get("type") or "custom",
            url=body.get("url"),
            object_id=body.get("object_id"),
            object=body.get("object"),
            parent=body.get("parent"),
            menu_order=body.get("menu_order"),
            status=body.get("status") or "publish",
        )
    finally:
        if created:
            await created.close()


@router.post("/batch")
async def bulk_create_menus(
    req: BulkCreateMenusRequest,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        menus = [{"name": m.name} for m in req.menus]
        return await wp.bulk_create_menus(menus)
    finally:
        if created:
            await created.close()


@router.post("/items/batch")
async def bulk_create_menu_items(
    req: BulkCreateMenuItemsRequest,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        items = [i.model_dump(by_alias=True) for i in req.items]
        return await wp.bulk_create_menu_items(items)
    finally:
        if created:
            await created.close()


@router.post("/tree")
async def create_menu_tree(
    req: CreateMenuTreeRequest,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)

    if req.menu_id is None and not (req.menu_name or "").strip():
        raise HTTPException(status_code=400, detail="menu_name is required when menu_id is not provided")

    def to_dict(node):
        # Enforce a max depth of 2 levels: (root -> child). No grandchildren.
        for c in node.children or []:
            if getattr(c, "children", None):
                if c.children:
                    raise HTTPException(status_code=400, detail="Only 2 menu levels are supported")
        return {
            "title": node.title,
            "url": node.url,
            "type": node.type,
            "status": node.status,
            "children": [to_dict(c) for c in (node.children or [])],
        }

    try:
        items = [to_dict(i) for i in req.items]
        return await wp.bulk_create_menu_tree(items=items, menu_name=req.menu_name, menu_id=req.menu_id)
    finally:
        if created:
            await created.close()


@router.get("/{menu_id}/tree")
async def get_menu_tree(
    menu_id: int,
    wp_site_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    wp, created = await _get_wp_client(wp_site_id=wp_site_id, current_user=current_user, db=db)
    try:
        page = 1
        all_items: list[dict[str, Any]] = []
        while True:
            res = await wp.list_menu_items(menus=menu_id, per_page=100, page=page)
            items = res.get("menu_items") or []
            if not isinstance(items, list):
                break
            all_items.extend(items)
            total_pages = int(res.get("total_pages") or 0)
            if total_pages and page >= total_pages:
                break
            if not total_pages and len(items) < 100:
                break
            page += 1

        nodes: dict[int, dict[str, Any]] = {}
        children_by_parent: dict[int, list[int]] = {}

        for it in all_items:
            try:
                it_id = int(it.get("id"))
            except Exception:
                continue
            parent = int(it.get("parent") or 0)
            nodes[it_id] = {
                "id": it_id,
                "title": it.get("title"),
                "url": it.get("url"),
                "menu_order": it.get("menu_order"),
                "parent": parent,
                "type": it.get("type"),
                "status": it.get("status"),
                "children": [],
            }
            children_by_parent.setdefault(parent, []).append(it_id)

        def sort_key(child_id: int):
            mo = nodes.get(child_id, {}).get("menu_order")
            try:
                return int(mo or 0)
            except Exception:
                return 0

        roots: list[dict[str, Any]] = []
        for root_id in sorted(children_by_parent.get(0, []), key=sort_key):
            root = nodes[root_id]
            # Only build 2 levels deep
            for child_id in sorted(children_by_parent.get(root_id, []), key=sort_key):
                root["children"].append(nodes[child_id])
            roots.append(root)

        return {"menu_id": menu_id, "items": roots, "total_items": len(all_items)}
    finally:
        if created:
            await created.close()
