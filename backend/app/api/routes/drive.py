from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_email, refresh_credentials
from app.models.user import OAuthToken
from app.schemas.drive import DriveFolderResponse
from app.services.google_drive import list_folder_contents

router = APIRouter(prefix="/api/drive", tags=["drive"])


async def _get_valid_token(
    db: AsyncSession,
    email: str | None,
) -> OAuthToken:
    """Get a valid Google OAuth token for the authenticated user, refreshing if expired."""
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated. Please connect first.")

    result = await db.execute(select(OAuthToken).where(OAuthToken.email == email))
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=401, detail="Not connected to Google Drive. Please connect first."
        )

    # Check if token is expired and refresh using the google-auth SDK
    if token.token_expiry and token.token_expiry < datetime.now(timezone.utc):
        if not token.refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Token expired and no refresh token available. Please reconnect.",
            )
        try:
            creds = refresh_credentials(token.refresh_token)
            token.access_token = creds.token
            token.token_expiry = creds.expiry
            token.updated_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Failed to refresh token: {str(e)}")

    return token


@router.get("/folders", response_model=DriveFolderResponse)
async def list_folders(
    parent_id: str = Query("root", description="Parent folder ID"),
    page_token: str = Query(None, description="Pagination token"),
    current_email: str | None = Depends(get_current_user_email),
    db: AsyncSession = Depends(get_db),
):
    """List folders and files inside a Google Drive folder for the authenticated user."""
    token = await _get_valid_token(db, current_email)

    try:
        result = list_folder_contents(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            folder_id=parent_id,
            page_token=page_token,
        )
        return DriveFolderResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list Drive contents: {str(e)}")


@router.get("/files/{folder_id}", response_model=DriveFolderResponse)
async def list_files_in_folder(
    folder_id: str,
    page_token: str = Query(None, description="Pagination token"),
    current_email: str | None = Depends(get_current_user_email),
    db: AsyncSession = Depends(get_db),
):
    """List files and subfolders inside a specific Google Drive folder."""
    token = await _get_valid_token(db, current_email)

    try:
        result = list_folder_contents(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            folder_id=folder_id,
            page_token=page_token,
        )
        return DriveFolderResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list folder contents: {str(e)}")
