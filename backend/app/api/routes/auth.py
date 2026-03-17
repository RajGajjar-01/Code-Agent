from datetime import datetime, timezone, timedelta
import logging
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Response, Request, Cookie
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_jwt,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    exchange_code_for_credentials,
    get_authorization_url,
    get_current_user_email,
    get_google_user_info,
    hash_password,
    revoke_google_token,
    verify_password,
)
from app.models.user import OAuthToken, User
from app.schemas.auth import (
    AuthStatusResponse,
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import token_service
from app.api.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_pending_states: dict[str, float] = {}
_login_attempts: dict[str, list[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300


def check_rate_limit(identifier: str) -> None:
    """Check if identifier has exceeded rate limit."""
    now = time()
    cutoff = now - RATE_LIMIT_WINDOW

    _login_attempts[identifier] = [t for t in _login_attempts[identifier] if t > cutoff]

    if len(_login_attempts[identifier]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many attempts, please try again later")

    _login_attempts[identifier].append(now)


def _set_jwt_cookie(response, email: str):
    """Set JWT HttpOnly cookie on response."""
    token = create_jwt(email)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )
    return response


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Register new user with email and password."""
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token_data = {"email": user.email, "user_id": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await token_service.store_refresh_token(db, refresh_token, user.id, expires_at)

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"User registered: {user.email} at {datetime.now(timezone.utc)}")

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    """Login with email and password."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"login:{client_ip}")

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        logger.warning(f"Failed login attempt for {body.email} from {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    await token_service.delete_user_refresh_tokens(db, user.id)

    token_data = {"email": user.email, "user_id": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await token_service.store_refresh_token(db, refresh_token, user.id, expires_at)

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"User logged in: {user.email} at {datetime.now(timezone.utc)}")

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    if await token_service.is_blacklisted(db, refresh_token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    stored_token = await token_service.get_refresh_token(db, refresh_token)
    if not stored_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    email = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_data = {"email": email, "user_id": user_id}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    await token_service.add_to_blacklist(db, refresh_token, stored_token.expires_at)
    await token_service.delete_refresh_token(db, refresh_token)

    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await token_service.store_refresh_token(db, new_refresh_token, user_id, expires_at)

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"Token refreshed for user: {email} at {datetime.now(timezone.utc)}")

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    """Logout and invalidate refresh token."""
    if refresh_token:
        stored_token = await token_service.get_refresh_token(db, refresh_token)
        if stored_token:
            await token_service.add_to_blacklist(db, refresh_token, stored_token.expires_at)
            await token_service.delete_refresh_token(db, refresh_token)

    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/")
    response.delete_cookie(key=COOKIE_NAME, path="/")

    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
    )


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password and invalidate all refresh tokens."""
    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    current_user.hashed_password = hash_password(body.new_password)
    await db.commit()

    await token_service.delete_user_refresh_tokens(db, current_user.id)

    logger.info(f"Password changed for user: {current_user.email}")

    return {"status": "password_changed"}


@router.get("/google/login")
async def google_login():
    """Redirect user to Google's OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    authorization_url, state = get_authorization_url()
    _pending_states[state] = datetime.now(timezone.utc).timestamp()

    # Clean up old states
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    expired = [k for k, v in _pending_states.items() if v < cutoff]
    for k in expired:
        _pending_states.pop(k, None)

    return RedirectResponse(url=authorization_url, status_code=307)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback — exchange code, save tokens, set JWT cookie."""
    if state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    _pending_states.pop(state)

    try:
        credentials = exchange_code_for_credentials(code, state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")

    access_token = credentials.token
    refresh_token = credentials.refresh_token
    token_expiry = credentials.expiry

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    try:
        user_info = await get_google_user_info(access_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get user info: {str(e)}")

    email = user_info.get("email", "")
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    # Upsert OAuth token
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

    # Set JWT cookie and redirect to frontend
    response = RedirectResponse(
        url=f"{settings.FRONTEND_ORIGIN}?google_auth=success", status_code=302
    )
    _set_jwt_cookie(response, email)
    return response


# --- Google Drive Connection Status ---


@router.get("/status", response_model=AuthStatusResponse)
async def drive_status(
    current_email: str | None = Depends(get_current_user_email),
    db: AsyncSession = Depends(get_db),
):
    """Check if the current user has an active Google Drive connection."""
    if not current_email:
        return AuthStatusResponse(connected=False)

    result = await db.execute(select(OAuthToken).where(OAuthToken.email == current_email))
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
async def disconnect_drive(
    current_email: str | None = Depends(get_current_user_email),
    db: AsyncSession = Depends(get_db),
):
    """Revoke Google tokens for the current user."""
    if not current_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(OAuthToken).where(OAuthToken.email == current_email))
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=404, detail="No Google connection found")

    if token.access_token:
        await revoke_google_token(token.access_token)

    await db.delete(token)
    await db.commit()

    return {"status": "disconnected"}
