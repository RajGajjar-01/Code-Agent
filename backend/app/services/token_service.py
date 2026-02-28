from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken, TokenBlacklist


async def add_to_blacklist(db: AsyncSession, token: str, expires_at: datetime) -> None:
    """Add token to blacklist."""
    blacklist_entry = TokenBlacklist(token=token, expires_at=expires_at)
    db.add(blacklist_entry)
    await db.commit()


async def is_blacklisted(db: AsyncSession, token: str) -> bool:
    """Check if token is blacklisted."""
    result = await db.execute(
        select(TokenBlacklist).where(TokenBlacklist.token == token)
    )
    return result.scalar_one_or_none() is not None


async def cleanup_expired_tokens(db: AsyncSession) -> None:
    """Remove expired tokens from blacklist and refresh token tables."""
    now = datetime.utcnow()
    
    await db.execute(
        delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
    )
    await db.execute(
        delete(RefreshToken).where(RefreshToken.expires_at < now)
    )
    await db.commit()


async def store_refresh_token(
    db: AsyncSession, token: str, user_id: int, expires_at: datetime
) -> None:
    """Store refresh token in database."""
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(refresh_token)
    await db.commit()


async def get_refresh_token(db: AsyncSession, token: str) -> RefreshToken | None:
    """Retrieve refresh token from database."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    return result.scalar_one_or_none()


async def delete_refresh_token(db: AsyncSession, token: str) -> None:
    """Delete specific refresh token."""
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token == token)
    )
    await db.commit()


async def delete_user_refresh_tokens(db: AsyncSession, user_id: int) -> None:
    """Delete all refresh tokens for a user."""
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    await db.commit()
