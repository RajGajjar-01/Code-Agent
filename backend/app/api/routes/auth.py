"""Google OAuth 2.0 authentication routes using google-auth-oauthlib Flow."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    exchange_code_for_credentials,
    get_authorization_url,
    get_google_user_info,
    revoke_google_token,
)
from app.models.user import OAuthToken
from app.schemas.auth import AuthStatusResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory state storage (simple approach for single-server dev)
_pending_states: dict[str, float] = {}


@router.get("/login")
async def login():
    """Redirect user to Google's OAuth consent screen using the Flow SDK."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    # Use the Flow SDK to build the authorization URL
    authorization_url, state = get_authorization_url()

    # Store state for CSRF validation
    _pending_states[state] = datetime.now(timezone.utc).timestamp()

    # Clean up old states (older than 10 minutes)
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    expired = [k for k, v in _pending_states.items() if v < cutoff]
    for k in expired:
        _pending_states.pop(k, None)

    return RedirectResponse(url=authorization_url, status_code=307)


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback — uses Flow SDK to exchange code for credentials."""
    # Validate state for CSRF protection
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    _pending_states.pop(state)

    try:
        # Use Flow SDK to exchange authorization code for credentials
        credentials = exchange_code_for_credentials(code, state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")

    access_token = credentials.token
    refresh_token = credentials.refresh_token
    token_expiry = credentials.expiry

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    # Get user profile info
    try:
        user_info = await get_google_user_info(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to get user info: {str(e)}"
        )

    email = user_info.get("email", "")
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    # Upsert token in database
    result = await db.execute(select(OAuthToken).where(OAuthToken.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        existing.access_token = access_token
        if refresh_token:
            existing.refresh_token = refresh_token
        existing.token_expiry = token_expiry
        existing.name = name
        existing.picture = picture
        existing.updated_at = datetime.now(timezone.utc)
    else:
        scopes = " ".join(credentials.scopes) if credentials.scopes else ""
        new_token = OAuthToken(
            provider="google",
            email=email,
            name=name,
            picture=picture,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            scopes=scopes,
        )
        db.add(new_token)

    await db.commit()

    # Redirect back to frontend
    return RedirectResponse(
        url=f"{settings.FRONTEND_ORIGIN}?google_auth=success", status_code=302
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(db: AsyncSession = Depends(get_db)):
    """Check if there is an active Google connection."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.provider == "google").limit(1)
    )
    token = result.scalar_one_or_none()

    if not token:
        return AuthStatusResponse(connected=False)

    return AuthStatusResponse(
        connected=True,
        email=token.email,
        name=token.name,
        picture=token.picture,
    )


@router.post("/disconnect")
async def disconnect(db: AsyncSession = Depends(get_db)):
    """Revoke Google tokens and remove from database."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.provider == "google").limit(1)
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=404, detail="No Google connection found")

    # Try to revoke the token at Google
    if token.access_token:
        await revoke_google_token(token.access_token)

    await db.delete(token)
    await db.commit()

    return {"status": "disconnected"}
