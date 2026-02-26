"""Google OAuth 2.0 security utilities using the official google-auth-oauthlib SDK."""

import secrets

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import httpx

from app.core.config import settings

# Scopes for Google Drive read-only + user profile
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Google user info endpoint (not covered by Flow)
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


def _build_client_config() -> dict:
    """Build the OAuth client config dict from env vars (replaces client_secret.json)."""
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
    """Generate a cryptographically secure state token for CSRF protection."""
    return secrets.token_urlsafe(32)


def create_google_auth_flow(state: str | None = None) -> Flow:
    """Create a google_auth_oauthlib Flow instance from our app settings.

    This is the official Google SDK way to handle OAuth 2.0 for web apps.
    It replaces manually building URLs and exchanging tokens via raw HTTP.
    """
    flow = Flow.from_client_config(
        client_config=_build_client_config(),
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


def get_authorization_url() -> tuple[str, str]:
    """Generate the Google OAuth consent screen URL.

    Returns:
        (authorization_url, state) — redirect user to authorization_url
    """
    flow = create_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",   # Request refresh token
        prompt="consent",        # Force consent to always get refresh token
        include_granted_scopes="true",
    )
    return authorization_url, state


def exchange_code_for_credentials(code: str, state: str) -> Credentials:
    """Exchange authorization code for Google OAuth Credentials.

    Uses the Flow SDK to handle the token exchange. Returns a
    google.oauth2.credentials.Credentials object containing
    access_token, refresh_token, token_uri, etc.
    """
    flow = create_google_auth_flow(state=state)
    flow.fetch_token(code=code)
    return flow.credentials


def refresh_credentials(refresh_token: str) -> Credentials:
    """Create refreshed Credentials from a stored refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )
    # Force a refresh
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    return creds


async def get_google_user_info(access_token: str) -> dict:
    """Fetch user profile info from Google using the access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


async def revoke_google_token(token: str) -> bool:
    """Revoke a Google OAuth token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_REVOKE_URL,
            params={"token": token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return response.status_code == 200
