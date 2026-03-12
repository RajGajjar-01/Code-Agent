from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ListPagesInput(BaseModel):
    per_page: int = Field(default=10, description="Number of pages per request")
    status: str = Field(default="publish", description="Post status filter")


class GetPageInput(BaseModel):
    page_id: int = Field(description="WordPress page ID")


class CreatePageInput(BaseModel):
    title: str = Field(description="Page title")
    content: str = Field(description="HTML content")
    status: str = Field(default="publish", description="Post status")
    allow_duplicate: bool = Field(
        default=False,
        description="If false, the tool will ask for confirmation when a page with the same title/slug already exists.",
    )


class UpdatePageInput(BaseModel):
    page_id: int = Field(description="WordPress page ID")
    title: Optional[str] = Field(default=None, description="New page title")
    content: Optional[str] = Field(default=None, description="New HTML content")


class DeletePageInput(BaseModel):
    page_id: int = Field(description="WordPress page ID")
    force: bool = Field(default=True, description="Bypass trash")


class ListPostsInput(BaseModel):
    per_page: int = Field(default=10, description="Number of posts per request")
    status: str = Field(default="publish", description="Post status filter")


class GetPostInput(BaseModel):
    post_id: int = Field(description="WordPress post ID")


class CreatePostInput(BaseModel):
    title: str = Field(description="Post title")
    content: str = Field(description="HTML content")
    status: str = Field(default="publish", description="Post status")


class UpdatePostInput(BaseModel):
    post_id: int = Field(description="WordPress post ID")
    title: Optional[str] = Field(default=None, description="New post title")
    content: Optional[str] = Field(default=None, description="New HTML content")


class DeletePostInput(BaseModel):
    post_id: int = Field(description="WordPress post ID")
    force: bool = Field(default=True, description="Bypass trash")


class UploadMediaInput(BaseModel):
    file_path: str = Field(description="Local file path")
    title: Optional[str] = Field(default=None, description="Optional media title")


class ListMediaInput(BaseModel):
    per_page: int = Field(default=10, description="Number of media items per request")


class DeleteMediaInput(BaseModel):
    media_id: int = Field(description="Media item ID")
    force: bool = Field(default=True, description="Bypass trash")


class ListCategoriesInput(BaseModel):
    per_page: int = Field(default=50, description="Number of categories per request")


class CreateCategoryInput(BaseModel):
    name: str = Field(description="Category name")


class ListTagsInput(BaseModel):
    per_page: int = Field(default=50, description="Number of tags per request")


class CreateTagInput(BaseModel):
    name: str = Field(description="Tag name")


class ListUsersInput(BaseModel):
    per_page: int = Field(default=10, description="Number of users per request")


class UpdateSettingsInput(BaseModel):
    settings: dict = Field(description="Settings payload")


class FetchAllPostsInput(BaseModel):
    per_page: int = Field(default=100, description="Page size for pagination")
    status: str = Field(default="any", description="Post status filter")


class FetchAllPagesInput(BaseModel):
    per_page: int = Field(default=100, description="Page size for pagination")
    status: str = Field(default="any", description="Post status filter")


class BulkUpdatePagesInput(BaseModel):
    updates: list[dict] = Field(description="List of create/update payloads")


class BulkDeletePagesInput(BaseModel):
    page_ids: list[int] = Field(description="Page IDs")
    force: bool = Field(default=True, description="Bypass trash")


class BulkUpdatePostsInput(BaseModel):
    updates: list[dict] = Field(description="List of create/update payloads")


class BulkDeletePostsInput(BaseModel):
    post_ids: list[int] = Field(description="Post IDs")
    force: bool = Field(default=True, description="Bypass trash")


class BulkUploadMediaInput(BaseModel):
    files: list[dict] = Field(description="List of file upload payloads")
    concurrency: int = Field(default=3, description="Parallel uploads")


class ListMenusInput(BaseModel):
    """List WordPress navigation menus.

    Note: Requires WordPress 5.9+ for native REST API menu endpoints.
    WordPress 6.8+ allows public menu access without authentication.
    """
    per_page: int = Field(default=100, description="Number of menus per request")


class CreateMenuInput(BaseModel):
    name: str = Field(description="Menu name")


class DeleteMenuInput(BaseModel):
    menu_id: int = Field(description="Menu ID")
    force: bool = Field(default=True, description="Bypass trash")


class ListMenuItemsInput(BaseModel):
    menu_id: Optional[int] = Field(default=None, description="Optional menu ID filter")
    per_page: int = Field(default=100, description="Items per page")


class CreateMenuItemInput(BaseModel):
    menu_id: int = Field(description="Menu ID")
    title: str = Field(description="Menu item title")
    type: str = Field(default="custom", description="Menu item type. If type='custom', url is required.")
    url: Optional[str] = Field(default=None, description="URL for custom link (required when type='custom')")
    object_id: Optional[int] = Field(default=None, description="Linked object ID")
    object: Optional[str] = Field(default=None, description="Linked object type")
    parent: Optional[int] = Field(default=0, description="Parent menu item ID")
    menu_order: Optional[int] = Field(default=None, description="Menu order")
    status: str = Field(default="publish", description="publish or draft")


class BulkCreateMenusInput(BaseModel):
    menus: list[dict] = Field(description="List of menus, each containing at least {name}")


class BulkCreateMenuItemsInput(BaseModel):
    items: list[dict] = Field(description="List of menu-item payloads")


class CreateMenuTreeInput(BaseModel):
    menu_name: Optional[str] = Field(default=None, description="Menu name (required if menu_id is not provided)")
    menu_id: Optional[int] = Field(default=None, description="Existing menu ID to append items into")
    items: list[dict] = Field(description="Tree items, each item may include children")


class GetAcfFieldsInput(BaseModel):
    post_id: int = Field(description="WordPress post/page ID")
    post_type: str = Field(default="pages", description="'pages' or 'posts'")


class UpdateAcfFieldsInput(BaseModel):
    post_id: int = Field(description="WordPress post/page ID")
    fields: dict = Field(description="ACF fields payload")
    post_type: str = Field(default="pages", description="'pages' or 'posts'")


class CreateThemeFileInput(BaseModel):
    theme_slug: str = Field(description="Theme directory slug")
    file_path: str = Field(description="Relative file path within theme")
    content: str = Field(description="Full file content")


class ReadThemeFileInput(BaseModel):
    theme_slug: str = Field(description="Theme directory slug")
    file_path: str = Field(description="Relative file path within theme")


class ActivateThemeInput(BaseModel):
    theme_slug: str = Field(description="Theme directory slug")


class WpCliActivateThemeInput(BaseModel):
    theme_slug: str = Field(description="Theme directory slug")


class WpCliListThemesInput(BaseModel):
    pass


class ListMenuLocationsInput(BaseModel):
    pass


class AssignMenuLocationsInput(BaseModel):
    menu_id: int = Field(description="Menu term ID")
    locations: list[str] = Field(description="List of theme menu location slugs")


class WpCliMenuCreateInput(BaseModel):
    name: str = Field(description="Menu name")
    porcelain: bool = Field(default=True, description="Return only the created menu id")


class WpCliMenuLocationListInput(BaseModel):
    format: str = Field(default="json", description="Output format: table|csv|json|yaml")


class WpCliMenuLocationAssignInput(BaseModel):
    menu: str = Field(description="Menu name, slug, or term ID")
    location: str = Field(description="Theme menu location slug")


class WpCliMenuItemAddPostInput(BaseModel):
    menu: str = Field(description="Menu name, slug, or term ID")
    post_id: int = Field(description="Post/Page ID")
    title: Optional[str] = Field(default=None, description="Optional menu label")
    position: Optional[int] = Field(default=None, description="Optional menu order")
    parent_id: Optional[int] = Field(default=None, description="Optional parent menu item ID")
    porcelain: bool = Field(default=True, description="Return only the created menu item id")


class WpCliMenuItemAddCustomInput(BaseModel):
    menu: str = Field(description="Menu name, slug, or term ID")
    title: str = Field(description="Menu label")
    link: str = Field(description="Target URL")
    position: Optional[int] = Field(default=None, description="Optional menu order")
    parent_id: Optional[int] = Field(default=None, description="Optional parent menu item ID")
    porcelain: bool = Field(default=True, description="Return only the created menu item id")


class WpCliScaffoldThemeInput(BaseModel):
    """Input for WP-CLI scaffold _s command to create a classic theme."""
    theme_slug: str = Field(
        description="Theme directory slug (lowercase, hyphens, no spaces). Used for function prefixes."
    )
    theme_name: Optional[str] = Field(
        default=None,
        description="Human-readable theme name for style.css header. Defaults to slug if not provided."
    )
    author: Optional[str] = Field(
        default=None,
        description="Author name for style.css header"
    )
    author_uri: Optional[str] = Field(
        default=None,
        description="Author website URL"
    )
    theme_uri: Optional[str] = Field(
        default=None,
        description="Theme website URL"
    )
    sassify: bool = Field(
        default=True,
        description="Include SASS/SCSS stylesheets instead of plain CSS"
    )
    activate: bool = Field(
        default=False,
        description="Activate the theme immediately after creation"
    )
    force: bool = Field(
        default=False,
        description="Overwrite existing theme files if theme already exists"
    )


class WpCliScaffoldPostTypeInput(BaseModel):
    """Input for WP-CLI scaffold post-type command."""
    post_type: str = Field(
        description="Custom post type slug (lowercase, no spaces)"
    )
    label: Optional[str] = Field(
        default=None,
        description="Human-readable label for the post type"
    )
    theme: Optional[str] = Field(
        default=None,
        description="Theme slug to add the post type file to. If not provided, outputs to stdout."
    )
    dashicon: Optional[str] = Field(
        default=None,
        description="Dashicon name for menu icon (e.g., 'dashicons-book')"
    )
    textdomain: Optional[str] = Field(
        default=None,
        description="Text domain for translations"
    )


class WpCliScaffoldTaxonomyInput(BaseModel):
    """Input for WP-CLI scaffold taxonomy command."""
    taxonomy: str = Field(
        description="Taxonomy slug (lowercase, no spaces)"
    )
    post_types: str = Field(
        description="Comma-separated list of post types the taxonomy applies to"
    )
    label: Optional[str] = Field(
        default=None,
        description="Human-readable label for the taxonomy"
    )
    theme: Optional[str] = Field(
        default=None,
        description="Theme slug to add the taxonomy file to"
    )


class WpCliThemeDeleteInput(BaseModel):
    """Input for WP-CLI theme delete command."""
    theme_slug: str = Field(
        description="Theme directory slug to delete"
    )
