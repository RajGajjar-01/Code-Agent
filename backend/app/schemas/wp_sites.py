from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WordPressSiteCreate(BaseModel):
    name: str | None = None
    base_url: str
    username: str
    app_password: str


class WordPressSiteUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    username: str | None = None
    app_password: str | None = None


class WordPressSiteOut(BaseModel):
    id: int
    name: str | None = None
    base_url: str
    username: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
