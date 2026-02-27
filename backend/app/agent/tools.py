

from typing import Any, Optional

from langchain_core.tools import tool



_wp_client: Optional[Any] = None


def set_wp_client(client: Any) -> None:
    """Set the global WP client for tool functions."""
    global _wp_client
    _wp_client = client


def _client():
    if not _wp_client:
        raise RuntimeError("WordPress client not configured. Check WP_BASE_URL, WP_USERNAME, and WP_APP_PASSWORD in .env")
    return _wp_client




@tool
async def list_pages(per_page: int = 10, status: str = "publish") -> dict:
    """List all WordPress pages. Returns page IDs, titles, and links."""
    return await _client().list_pages(per_page=per_page, status=status)


@tool
async def get_page(page_id: int) -> dict:
    """Get a specific WordPress page by ID. Returns title, content, and ACF fields."""
    return await _client().get_page(page_id)


@tool
async def create_page(title: str, content: str, status: str = "publish") -> dict:
    """Create a new WordPress page with the given title and HTML content."""
    return await _client().create_page(title=title, content=content, status=status)


@tool
async def update_page(page_id: int, title: str = "", content: str = "") -> dict:
    """Update an existing WordPress page. Only pass fields you want to change."""
    kwargs = {}
    if title:
        kwargs["title"] = title
    if content:
        kwargs["content"] = content
    return await _client().update_page(page_id, **kwargs)


@tool
async def delete_page(page_id: int, force: bool = True) -> dict:
    """Delete a WordPress page by ID. Use force=True to bypass trash."""
    return await _client().delete_page(page_id, force=force)




@tool
async def list_posts(per_page: int = 10, status: str = "publish") -> dict:
    """List all WordPress posts. Returns post IDs, titles, and links."""
    return await _client().list_posts(per_page=per_page, status=status)


@tool
async def create_post(title: str, content: str, status: str = "publish") -> dict:
    """Create a new WordPress post with the given title and HTML content."""
    return await _client().create_post(title=title, content=content, status=status)


@tool
async def delete_post(post_id: int, force: bool = True) -> dict:
    """Delete a WordPress post by ID. Use force=True to bypass trash."""
    return await _client().delete_post(post_id, force=force)




@tool
async def upload_media(file_path: str, title: str = "") -> dict:
    """Upload a file from local path to WordPress media library."""
    return await _client().upload_media(file_path, title=title or None)




@tool
async def get_acf_fields(post_id: int, post_type: str = "pages") -> dict:
    """Get all ACF field values for a given page or post.

    Args:
        post_id: The WordPress page/post ID.
        post_type: 'pages' or 'posts'.
    """
    return await _client().get_acf_fields(post_id, post_type=post_type)


@tool
async def update_acf_fields(post_id: int, fields: dict, post_type: str = "pages") -> dict:
    """Update ACF fields on a WordPress page or post.

    Args:
        post_id: The WordPress page/post ID.
        fields: A dictionary of ACF field name → value pairs to set.
        post_type: 'pages' or 'posts'.
    """
    return await _client().update_acf_fields(post_id, fields, post_type=post_type)


@tool
async def list_acf_field_groups() -> dict:
    """List all registered ACF field groups and their fields.

    Requires ACF Pro or the REST API to be enabled for field groups.
    """
    return await _client().list_acf_field_groups()




@tool
async def list_themes() -> dict:
    """List all installed WordPress themes with their status (active/inactive)."""
    return await _client().list_themes()


@tool
async def get_active_theme() -> dict:
    """Get details about the currently active WordPress theme."""
    return await _client().get_active_theme()


@tool
async def create_theme_file(theme_slug: str, file_path: str, content: str) -> dict:
    """Create or overwrite a file in a WordPress theme directory.

    Args:
        theme_slug: The theme directory name (e.g. 'my-custom-theme').
        file_path: Relative path within the theme (e.g. 'style.css', 'template-parts/hero.php').
        content: The full file content to write.
    """
    return await _client().create_theme_file(theme_slug, file_path, content)


@tool
async def read_theme_file(theme_slug: str, file_path: str) -> dict:
    """Read the contents of a file from a WordPress theme directory.

    Args:
        theme_slug: The theme directory name.
        file_path: Relative path within the theme.
    """
    return await _client().read_theme_file(theme_slug, file_path)


@tool
async def activate_theme(theme_slug: str) -> dict:
    """Activate a WordPress theme by its slug/directory name."""
    return await _client().activate_theme(theme_slug)




@tool
async def get_site_info() -> dict:
    """Get WordPress site name, description, and URL."""
    return await _client().get_site_info()




ALL_TOOLS = [
    # Pages
    list_pages,
    get_page,
    create_page,
    update_page,
    delete_page,
    # Posts
    list_posts,
    create_post,
    delete_post,
    # Media
    upload_media,
    # ACF
    get_acf_fields,
    update_acf_fields,
    list_acf_field_groups,
    # Themes
    list_themes,
    get_active_theme,
    create_theme_file,
    read_theme_file,
    activate_theme,
    # Site
    get_site_info,
]
