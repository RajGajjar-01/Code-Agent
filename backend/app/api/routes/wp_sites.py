from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.models.wordpress_site import WordPressSite
from app.schemas.wp_sites import WordPressSiteCreate, WordPressSiteOut, WordPressSiteUpdate

router = APIRouter(prefix="/api/wp-sites", tags=["wp-sites"])


def _normalize_base_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        raise HTTPException(status_code=400, detail="base_url is required")
    return u.rstrip("/")


@router.get("", response_model=list[WordPressSiteOut])
async def list_wp_sites(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WordPressSite)
        .where(WordPressSite.user_id == current_user.id)
        .order_by(WordPressSite.updated_at.desc())
    )
    rows = result.scalars().all()
    return [WordPressSiteOut.model_validate(r) for r in rows]


@router.post("", response_model=WordPressSiteOut)
async def create_wp_site(
    body: WordPressSiteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    base_url = _normalize_base_url(body.base_url)
    username = (body.username or "").strip()
    app_password = (body.app_password or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="username is required")
    if not app_password:
        raise HTTPException(status_code=400, detail="app_password is required")

    site = WordPressSite(
        user_id=current_user.id,
        name=(body.name or "").strip() or None,
        base_url=base_url,
        username=username,
        app_password_encrypted=app_password,
    )

    db.add(site)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Site already exists for this user")

    except Exception:
        await db.rollback()
        raise

    await db.refresh(site)
    return WordPressSiteOut.model_validate(site)


@router.patch("/{site_id}", response_model=WordPressSiteOut)
async def update_wp_site(
    site_id: int,
    body: WordPressSiteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WordPressSite).where(
            WordPressSite.id == site_id,
            WordPressSite.user_id == current_user.id,
        )
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    if body.name is not None:
        site.name = (body.name or "").strip() or None
    if body.base_url is not None:
        site.base_url = _normalize_base_url(body.base_url)
    if body.username is not None:
        username = (body.username or "").strip()
        if not username:
            raise HTTPException(status_code=400, detail="username cannot be empty")
        site.username = username
    if body.app_password is not None:
        app_password = (body.app_password or "").strip()
        if not app_password:
            raise HTTPException(status_code=400, detail="app_password cannot be empty")
        site.app_password_encrypted = app_password

    await db.commit()
    await db.refresh(site)
    return WordPressSiteOut.model_validate(site)


@router.delete("/{site_id}")
async def delete_wp_site(
    site_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WordPressSite).where(
            WordPressSite.id == site_id,
            WordPressSite.user_id == current_user.id,
        )
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    await db.delete(site)
    await db.commit()
    return {"detail": "deleted"}
