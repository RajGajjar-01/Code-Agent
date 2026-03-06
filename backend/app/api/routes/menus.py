from __future__ import annotations

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
        # Ensure expected WP param key exists
        for it in items:
            if "menu-id" not in it and "menu_id" in it:
                it["menu-id"] = it.pop("menu_id")
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

    def to_dict(node):
        return {
            "title": node.title,
            "url": node.url,
            "type": node.type,
            "status": node.status,
            "children": [to_dict(c) for c in (node.children or [])],
        }

    try:
        items = [to_dict(i) for i in req.items]
        return await wp.bulk_create_menu_tree(menu_name=req.menu_name, items=items)
    finally:
        if created:
            await created.close()
