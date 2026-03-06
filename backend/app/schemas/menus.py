from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class MenuCreate(BaseModel):
    name: str = Field(description="Menu name")


class MenuOut(BaseModel):
    id: int
    name: str | None = None
    slug: str | None = None
    count: int | None = None


class MenuItemCreate(BaseModel):
    menu_id: int = Field(alias="menu-id", description="Menu term ID")
    title: str = Field(description="Menu item title")
    type: Literal["custom", "post_type", "taxonomy", "post_type_archive"] = Field(
        default="custom", description="Menu item type"
    )
    url: Optional[str] = Field(default=None, description="URL for custom links")
    object_id: Optional[int] = Field(default=None, description="Linked object ID")
    object: Optional[str] = Field(default=None, description="Linked object type")
    parent: int = Field(default=0, description="Parent menu item ID")
    menu_order: Optional[int] = Field(default=None, description="Menu order")
    status: Literal["publish", "draft"] = Field(default="publish")

    model_config = {"populate_by_name": True}


class MenuItemOut(BaseModel):
    id: int
    menu_id: int | None = None
    title: str | None = None
    url: str | None = None
    parent: int | None = None
    menu_order: int | None = None
    type: str | None = None
    status: str | None = None


class MenuTreeItem(BaseModel):
    title: str
    url: Optional[str] = None
    type: Literal["custom", "post_type", "taxonomy", "post_type_archive"] = "custom"
    status: Literal["publish", "draft"] = "publish"
    children: list["MenuTreeItem"] = Field(default_factory=list)


class CreateMenuTreeRequest(BaseModel):
    menu_name: str
    items: list[MenuTreeItem]


class BulkCreateMenusRequest(BaseModel):
    menus: list[MenuCreate]


class BulkCreateMenuItemsRequest(BaseModel):
    items: list[MenuItemCreate]
