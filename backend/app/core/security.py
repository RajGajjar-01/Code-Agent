import secrets
from datetime import datetime, timedelta, timezone

import httpx
import jwt as pyjwt
import bcrypt as _bcrypt
from fastapi import Cookie
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import settings

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
]

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
COOKIE_NAME = "wp_session"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
REFRESH_COOKIE_NAME = "refresh_token"


def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_jwt(email: str) -> str:
    """Create JWT containing user's email."""
    payload = {
        "sub": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return pyjwt.encode(payload, settings.APP_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> str | None:
    """Decode JWT and return email or None if invalid."""
    try:
        payload = pyjwt.decode(token, settings.APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


async def get_current_user_email(wp_session: str | None = Cookie(None)) -> str | None:
    """Extract user email from JWT cookie."""
    if not wp_session:
        return None
    return decode_jwt(wp_session)


def create_access_token(data: dict) -> str:
    """Create short-lived access token (15 minutes)."""
    payload = {
        "sub": data.get("email"),
        "user_id": data.get("user_id"),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return pyjwt.encode(payload, settings.APP_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create long-lived refresh token (7 days)."""
    import uuid

    payload = {
        "sub": data.get("email"),
        "user_id": data.get("user_id"),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return pyjwt.encode(payload, settings.APP_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate access token."""
    try:
        payload = pyjwt.decode(token, settings.APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


def decode_refresh_token(token: str) -> dict | None:
    """Decode and validate refresh token."""
    try:
        payload = pyjwt.decode(token, settings.APP_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


def _build_client_config() -> dict:
    """Build OAuth client config from env vars."""
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


def generate_state_token() -> str:
    return secrets.token_urlsafe(32)


def create_google_auth_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        client_config=_build_client_config(),
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


def get_authorization_url() -> tuple[str, str]:
    flow = create_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return authorization_url, state


def exchange_code_for_credentials(code: str, state: str) -> Credentials:
    flow = create_google_auth_flow(state=state)
    flow.fetch_token(code=code)
    return flow.credentials


def refresh_credentials(refresh_token: str) -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )
    from google.auth.transport.requests import Request

    creds.refresh(Request())
    return creds


async def get_google_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def revoke_google_token(token: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_REVOKE_URL,
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return response.status_code == 200
