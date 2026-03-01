from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.core.config import settings


def _build_drive_service(access_token: str, refresh_token: str | None = None):
    """Build a Google Drive API v3 service from OAuth credentials."""
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    return build("drive", "v3", credentials=creds)


def list_folder_contents(
    access_token: str,
    refresh_token: str | None = None,
    folder_id: str = "root",
    page_token: str | None = None,
    page_size: int = 50,
) -> dict:
    """List files and folders inside a specific Google Drive folder."""
    service = _build_drive_service(access_token, refresh_token)

    # Get folder name
    folder_name = "My Drive"
    if folder_id != "root":
        try:
            folder_meta = service.files().get(fileId=folder_id, fields="name").execute()
            folder_name = folder_meta.get("name", folder_id)
        except Exception:
            folder_name = folder_id

    query = f"'{folder_id}' in parents and trashed = false"

    results = (
        service.files()
        .list(
            q=query,
            pageSize=page_size,
            pageToken=page_token,
            fields=(
                "nextPageToken, files(id, name, mimeType, modifiedTime, "
                "size, iconLink, webViewLink)"
            ),
            orderBy="folder, name",
        )
        .execute()
    )

    items = []
    for f in results.get("files", []):
        items.append(
            {
                "id": f["id"],
                "name": f["name"],
                "mime_type": f["mimeType"],
                "modified_time": f.get("modifiedTime"),
                "size": f.get("size"),
                "icon_link": f.get("iconLink"),
                "web_view_link": f.get("webViewLink"),
            }
        )

    return {
        "folder_id": folder_id,
        "folder_name": folder_name,
        "items": items,
        "next_page_token": results.get("nextPageToken"),
    }
