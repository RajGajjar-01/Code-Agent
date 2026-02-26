from typing import Optional

from pydantic import BaseModel


class DriveItem(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: Optional[str] = None
    size: Optional[str] = None
    icon_link: Optional[str] = None
    web_view_link: Optional[str] = None


class DriveFolderResponse(BaseModel):
    folder_id: str
    folder_name: str
    items: list[DriveItem]
    next_page_token: Optional[str] = None
