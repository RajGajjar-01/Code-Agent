import asyncio
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import StructuredTool

from app.agent.config import get_agent_config
from app.agent.tools_schema import (
    ActivateThemeInput,
    BulkDeletePagesInput,
    BulkDeletePostsInput,
    BulkUpdatePagesInput,
    BulkUpdatePostsInput,
    BulkUploadMediaInput,
    CreateCategoryInput,
    CreatePageInput,
    CreatePostInput,
    CreateTagInput,
    CreateThemeFileInput,
    DeleteMediaInput,
    DeletePageInput,
    DeletePostInput,
    FetchAllPagesInput,
    FetchAllPostsInput,
    GetAcfFieldsInput,
    GetPageInput,
    GetPostInput,
    ListCategoriesInput,
    ListMediaInput,
    ListPagesInput,
    ListPostsInput,
    ListTagsInput,
    ListUsersInput,
    ReadThemeFileInput,
    UpdateAcfFieldsInput,
    UpdatePageInput,
    UpdatePostInput,
    UpdateSettingsInput,
    UploadMediaInput,
    WpCliActivateThemeInput,
    WpCliListThemesInput,
)

_wp_client: Optional[Any] = None
_wp_cli_wp_path_override: str | None = None
_wp_cli_default_url_override: str | None = None
_wp_cli_install_lock: asyncio.Lock | None = None


def _get_wp_cli_install_lock() -> asyncio.Lock:
    global _wp_cli_install_lock
    if _wp_cli_install_lock is None:
        _wp_cli_install_lock = asyncio.Lock()
    return _wp_cli_install_lock


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_local_wp_cli_path() -> Path:
    return _backend_root() / "bin" / "wp"


def _download_wp_cli_to(target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    url = "https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
    tmp_path = target_path.with_suffix(".tmp")
    urllib.request.urlretrieve(url, tmp_path)  # noqa: S310
    os.replace(tmp_path, target_path)
    os.chmod(target_path, 0o755)


async def ensure_wp_cli_installed() -> str | None:
    """Ensure WP-CLI is available if auto-install is enabled.

    Returns the local wp binary path if installed/available, else None.
    """
    config = get_agent_config()
    if not config.wp_cli_auto_install:
        return None

    # If user explicitly provided a path and it exists, respect it.
    if config.wp_cli_path and config.wp_cli_path != "wp":
        wp_path = Path(config.wp_cli_path)
        if wp_path.exists():
            return str(wp_path)

    local_path = _default_local_wp_cli_path()
    if local_path.exists():
        return str(local_path)

    lock = _get_wp_cli_install_lock()
    async with lock:
        if local_path.exists():
            return str(local_path)
        await asyncio.to_thread(_download_wp_cli_to, local_path)
        return str(local_path)


def set_wp_client(client: Any) -> None:
    """Set the global WP client for tool functions."""
    global _wp_client
    _wp_client = client


def set_wp_cli_context(wp_path: str | None = None, default_url: str | None = None) -> None:
    global _wp_cli_wp_path_override, _wp_cli_default_url_override
    _wp_cli_wp_path_override = wp_path
    _wp_cli_default_url_override = default_url


def _client():
    if not _wp_client:
        raise RuntimeError(
            "WordPress client not configured. Check WP_BASE_URL, WP_USERNAME, "
            "and WP_APP_PASSWORD in .env"
        )
    return _wp_client


def _get_wp_cli_args() -> tuple[str, list[str]]:
    config = get_agent_config()
    wp_bin = config.wp_cli_path

    if config.wp_cli_auto_install:
        local_path = _default_local_wp_cli_path()
        if wp_bin == "wp" or (wp_bin and wp_bin != "wp" and not Path(wp_bin).exists()):
            if local_path.exists():
                wp_bin = str(local_path)

    wp_path = _wp_cli_wp_path_override or config.wp_cli_wp_path
    if not wp_path:
        raise RuntimeError(
            "WP-CLI path not configured. Provide WP_CLI_WP_PATH (path containing wp-config.php)."
        )

    wp_path_obj = Path(wp_path)
    if not (wp_path_obj / "wp-config.php").exists():
        raise RuntimeError(
            f"Invalid WP_CLI_WP_PATH: wp-config.php not found at {wp_path_obj}"
        )

    args: list[str] = [f"--path={str(wp_path_obj)}"]

    default_url = _wp_cli_default_url_override or config.wp_cli_default_url
    if default_url:
        args.append(f"--url={default_url}")

    if config.wp_cli_allow_root:
        args.append("--allow-root")

    return wp_bin, args


async def _run_wp_cli(command: list[str]) -> dict:
    wp_bin, base_args = _get_wp_cli_args()
    full_cmd = [wp_bin, *base_args, *command]

    try:
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        config = get_agent_config()
        if config.wp_cli_auto_install:
            installed_path = await ensure_wp_cli_installed()
            if installed_path:
                wp_bin2, base_args2 = _get_wp_cli_args()
                full_cmd2 = [wp_bin2, *base_args2, *command]
                proc = await asyncio.create_subprocess_exec(
                    *full_cmd2,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                out_b, err_b = await proc.communicate()
                out = (out_b or b"").decode("utf-8", errors="replace").strip()
                err = (err_b or b"").decode("utf-8", errors="replace").strip()

                if proc.returncode != 0:
                    raise RuntimeError(
                        err or out or f"WP-CLI failed (exit_code={proc.returncode})"
                    )

                return {"stdout": out, "stderr": err, "command": full_cmd2}

        raise RuntimeError(
            "wp binary not found. Install WP-CLI or set WP_CLI_PATH to the wp executable."
        )

    out_b, err_b = await proc.communicate()
    out = (out_b or b"").decode("utf-8", errors="replace").strip()
    err = (err_b or b"").decode("utf-8", errors="replace").strip()

    if proc.returncode != 0:
        raise RuntimeError(err or out or f"WP-CLI failed (exit_code={proc.returncode})")

    return {"stdout": out, "stderr": err, "command": full_cmd}


async def _list_pages(per_page: int = 10, status: str = "publish") -> dict:
    return await _client().list_pages(per_page=per_page, status=status)


async def _get_page(page_id: int) -> dict:
    return await _client().get_page(page_id)


async def _create_page(title: str, content: str, status: str = "publish") -> dict:
    return await _client().create_page(title=title, content=content, status=status)


async def _update_page(
    page_id: int, title: Optional[str] = None, content: Optional[str] = None
) -> dict:
    kwargs = {}
    if title:
        kwargs["title"] = title
    if content:
        kwargs["content"] = content
    return await _client().update_page(page_id, **kwargs)


async def _delete_page(page_id: int, force: bool = True) -> dict:
    return await _client().delete_page(page_id, force=force)


async def _list_posts(per_page: int = 10, status: str = "publish") -> dict:
    return await _client().list_posts(per_page=per_page, status=status)


async def _get_post(post_id: int) -> dict:
    return await _client().get_post(post_id)


async def _create_post(title: str, content: str, status: str = "publish") -> dict:
    return await _client().create_post(title=title, content=content, status=status)


async def _update_post(
    post_id: int, title: Optional[str] = None, content: Optional[str] = None
) -> dict:
    kwargs = {}
    if title:
        kwargs["title"] = title
    if content:
        kwargs["content"] = content
    return await _client().update_post(post_id, **kwargs)


async def _delete_post(post_id: int, force: bool = True) -> dict:
    return await _client().delete_post(post_id, force=force)


async def _upload_media(file_path: str, title: Optional[str] = None) -> dict:
    return await _client().upload_media(file_path, title=title or None)


async def _list_media(per_page: int = 10) -> dict:
    return await _client().list_media(per_page=per_page)


async def _delete_media(media_id: int, force: bool = True) -> dict:
    return await _client().delete_media(media_id, force=force)


async def _list_categories(per_page: int = 50) -> dict:
    return await _client().list_categories(per_page=per_page)


async def _create_category(name: str) -> dict:
    return await _client().create_category(name)


async def _list_tags(per_page: int = 50) -> dict:
    return await _client().list_tags(per_page=per_page)


async def _create_tag(name: str) -> dict:
    return await _client().create_tag(name)


async def _list_users(per_page: int = 10) -> dict:
    return await _client().list_users(per_page=per_page)


async def _get_current_user() -> dict:
    return await _client().get_current_user()


async def _get_settings() -> dict:
    return await _client().get_settings()


async def _update_settings(settings: dict) -> dict:
    return await _client().update_settings(**settings)


async def _fetch_all_posts(per_page: int = 100, status: str = "any") -> dict:
    return {"posts": await _client().fetch_all_posts(per_page=per_page, status=status)}


async def _fetch_all_pages(per_page: int = 100, status: str = "any") -> dict:
    return {"pages": await _client().fetch_all_pages(per_page=per_page, status=status)}


async def _bulk_update_pages(updates: list[dict]) -> dict:
    return await _client().bulk_update_pages(updates)


async def _bulk_delete_pages(page_ids: list[int], force: bool = True) -> dict:
    return await _client().bulk_delete_pages(page_ids, force=force)


async def _bulk_update_posts(updates: list[dict]) -> dict:
    return await _client().bulk_update_posts(updates)


async def _bulk_delete_posts(post_ids: list[int], force: bool = True) -> dict:
    return await _client().bulk_delete_posts(post_ids, force=force)


async def _bulk_upload_media(files: list[dict], concurrency: int = 3) -> dict:
    return await _client().bulk_upload_media(files, concurrency=concurrency)


async def _get_acf_fields(post_id: int, post_type: str = "pages") -> dict:
    return await _client().get_acf_fields(post_id, post_type=post_type)


async def _update_acf_fields(post_id: int, fields: dict, post_type: str = "pages") -> dict:
    return await _client().update_acf_fields(post_id, fields, post_type=post_type)


async def _list_acf_field_groups() -> dict:
    return await _client().list_acf_field_groups()


async def _list_themes() -> dict:
    return await _client().list_themes()


async def _get_active_theme() -> dict:
    return await _client().get_active_theme()


async def _create_theme_file(theme_slug: str, file_path: str, content: str) -> dict:
    return await _client().create_theme_file(theme_slug, file_path, content)


async def _read_theme_file(theme_slug: str, file_path: str) -> dict:
    return await _client().read_theme_file(theme_slug, file_path)


async def _activate_theme(theme_slug: str) -> dict:
    return await _client().activate_theme(theme_slug)


async def _wp_cli_list_themes() -> dict:
    res = await _run_wp_cli(["theme", "list", "--format=json"])
    try:
        themes = json.loads(res.get("stdout") or "[]")
    except Exception:
        themes = []
    return {"themes": themes}


async def _wp_cli_activate_theme(theme_slug: str) -> dict:
    await _run_wp_cli(["theme", "activate", theme_slug])
    return {"status": "activated", "theme_slug": theme_slug}


async def _get_site_info() -> dict:
    return await _client().get_site_info()


list_pages = StructuredTool.from_function(
    func=_list_pages,
    name="list_pages",
    description="List all WordPress pages. Returns page IDs, titles, and links.",
    args_schema=ListPagesInput,
    coroutine=_list_pages,
)
get_page = StructuredTool.from_function(
    func=_get_page,
    name="get_page",
    description="Get a specific WordPress page by ID. Returns title, content, and ACF fields.",
    args_schema=GetPageInput,
    coroutine=_get_page,
)
create_page = StructuredTool.from_function(
    func=_create_page,
    name="create_page",
    description="Create a new WordPress page with the given title and HTML content.",
    args_schema=CreatePageInput,
    coroutine=_create_page,
)
update_page = StructuredTool.from_function(
    func=_update_page,
    name="update_page",
    description="Update an existing WordPress page. Only pass fields you want to change.",
    args_schema=UpdatePageInput,
    coroutine=_update_page,
)
delete_page = StructuredTool.from_function(
    func=_delete_page,
    name="delete_page",
    description="Delete a WordPress page by ID. Use force=True to bypass trash.",
    args_schema=DeletePageInput,
    coroutine=_delete_page,
)

list_posts = StructuredTool.from_function(
    func=_list_posts,
    name="list_posts",
    description="List all WordPress posts. Returns post IDs, titles, and links.",
    args_schema=ListPostsInput,
    coroutine=_list_posts,
)
get_post = StructuredTool.from_function(
    func=_get_post,
    name="get_post",
    description="Get a specific WordPress post by ID.",
    args_schema=GetPostInput,
    coroutine=_get_post,
)
create_post = StructuredTool.from_function(
    func=_create_post,
    name="create_post",
    description="Create a new WordPress post with the given title and HTML content.",
    args_schema=CreatePostInput,
    coroutine=_create_post,
)
update_post = StructuredTool.from_function(
    func=_update_post,
    name="update_post",
    description="Update an existing WordPress post. Only pass fields you want to change.",
    args_schema=UpdatePostInput,
    coroutine=_update_post,
)
delete_post = StructuredTool.from_function(
    func=_delete_post,
    name="delete_post",
    description="Delete a WordPress post by ID. Use force=True to bypass trash.",
    args_schema=DeletePostInput,
    coroutine=_delete_post,
)

upload_media = StructuredTool.from_function(
    func=_upload_media,
    name="upload_media",
    description="Upload a file from local path to WordPress media library.",
    args_schema=UploadMediaInput,
    coroutine=_upload_media,
)
list_media = StructuredTool.from_function(
    func=_list_media,
    name="list_media",
    description="List media items from the WordPress media library.",
    args_schema=ListMediaInput,
    coroutine=_list_media,
)
delete_media = StructuredTool.from_function(
    func=_delete_media,
    name="delete_media",
    description="Delete a media item by ID.",
    args_schema=DeleteMediaInput,
    coroutine=_delete_media,
)

list_categories = StructuredTool.from_function(
    func=_list_categories,
    name="list_categories",
    description="List WordPress categories.",
    args_schema=ListCategoriesInput,
    coroutine=_list_categories,
)
create_category = StructuredTool.from_function(
    func=_create_category,
    name="create_category",
    description="Create a WordPress category.",
    args_schema=CreateCategoryInput,
    coroutine=_create_category,
)
list_tags = StructuredTool.from_function(
    func=_list_tags,
    name="list_tags",
    description="List WordPress tags.",
    args_schema=ListTagsInput,
    coroutine=_list_tags,
)
create_tag = StructuredTool.from_function(
    func=_create_tag,
    name="create_tag",
    description="Create a WordPress tag.",
    args_schema=CreateTagInput,
    coroutine=_create_tag,
)

list_users = StructuredTool.from_function(
    func=_list_users,
    name="list_users",
    description="List WordPress users (requires proper permissions).",
    args_schema=ListUsersInput,
    coroutine=_list_users,
)
get_current_user = StructuredTool.from_function(
    func=_get_current_user,
    name="get_current_user",
    description="Get the currently authenticated user (users/me).",
    coroutine=_get_current_user,
)
get_settings = StructuredTool.from_function(
    func=_get_settings,
    name="get_settings",
    description="Get WordPress site settings (requires admin).",
    coroutine=_get_settings,
)
update_settings = StructuredTool.from_function(
    func=_update_settings,
    name="update_settings",
    description="Update WordPress site settings (requires admin).",
    args_schema=UpdateSettingsInput,
    coroutine=_update_settings,
)

fetch_all_posts = StructuredTool.from_function(
    func=_fetch_all_posts,
    name="fetch_all_posts",
    description="Fetch all posts (auto-paginates).",
    args_schema=FetchAllPostsInput,
    coroutine=_fetch_all_posts,
)
fetch_all_pages = StructuredTool.from_function(
    func=_fetch_all_pages,
    name="fetch_all_pages",
    description="Fetch all pages (auto-paginates).",
    args_schema=FetchAllPagesInput,
    coroutine=_fetch_all_pages,
)

bulk_update_pages = StructuredTool.from_function(
    func=_bulk_update_pages,
    name="bulk_update_pages",
    description="Bulk create/update pages.",
    args_schema=BulkUpdatePagesInput,
    coroutine=_bulk_update_pages,
)
bulk_delete_pages = StructuredTool.from_function(
    func=_bulk_delete_pages,
    name="bulk_delete_pages",
    description="Bulk delete pages by ID.",
    args_schema=BulkDeletePagesInput,
    coroutine=_bulk_delete_pages,
)
bulk_update_posts = StructuredTool.from_function(
    func=_bulk_update_posts,
    name="bulk_update_posts",
    description="Bulk create/update posts.",
    args_schema=BulkUpdatePostsInput,
    coroutine=_bulk_update_posts,
)
bulk_delete_posts = StructuredTool.from_function(
    func=_bulk_delete_posts,
    name="bulk_delete_posts",
    description="Bulk delete posts by ID.",
    args_schema=BulkDeletePostsInput,
    coroutine=_bulk_delete_posts,
)
bulk_upload_media = StructuredTool.from_function(
    func=_bulk_upload_media,
    name="bulk_upload_media",
    description="Bulk upload media files.",
    args_schema=BulkUploadMediaInput,
    coroutine=_bulk_upload_media,
)

get_acf_fields = StructuredTool.from_function(
    func=_get_acf_fields,
    name="get_acf_fields",
    description="Get all ACF field values for a given page or post.",
    args_schema=GetAcfFieldsInput,
    coroutine=_get_acf_fields,
)
update_acf_fields = StructuredTool.from_function(
    func=_update_acf_fields,
    name="update_acf_fields",
    description="Update ACF fields on a WordPress page or post.",
    args_schema=UpdateAcfFieldsInput,
    coroutine=_update_acf_fields,
)
list_acf_field_groups = StructuredTool.from_function(
    func=_list_acf_field_groups,
    name="list_acf_field_groups",
    description="List all registered ACF field groups and their fields.",
    coroutine=_list_acf_field_groups,
)

list_themes = StructuredTool.from_function(
    func=_list_themes,
    name="list_themes",
    description="List all installed WordPress themes with their status (active/inactive).",
    coroutine=_list_themes,
)
get_active_theme = StructuredTool.from_function(
    func=_get_active_theme,
    name="get_active_theme",
    description="Get details about the currently active WordPress theme.",
    coroutine=_get_active_theme,
)
create_theme_file = StructuredTool.from_function(
    func=_create_theme_file,
    name="create_theme_file",
    description="Create or overwrite a file in a WordPress theme directory.",
    args_schema=CreateThemeFileInput,
    coroutine=_create_theme_file,
)
read_theme_file = StructuredTool.from_function(
    func=_read_theme_file,
    name="read_theme_file",
    description="Read the contents of a file from a WordPress theme directory.",
    args_schema=ReadThemeFileInput,
    coroutine=_read_theme_file,
)
activate_theme = StructuredTool.from_function(
    func=_activate_theme,
    name="activate_theme",
    description="Activate a WordPress theme by its slug/directory name.",
    args_schema=ActivateThemeInput,
    coroutine=_activate_theme,
)

wp_cli_list_themes = StructuredTool.from_function(
    func=_wp_cli_list_themes,
    name="wp_cli_list_themes",
    description="List installed WordPress themes using WP-CLI.",
    args_schema=WpCliListThemesInput,
    coroutine=_wp_cli_list_themes,
)

wp_cli_activate_theme = StructuredTool.from_function(
    func=_wp_cli_activate_theme,
    name="wp_cli_activate_theme",
    description="Activate a WordPress theme using WP-CLI.",
    args_schema=WpCliActivateThemeInput,
    coroutine=_wp_cli_activate_theme,
)

get_site_info = StructuredTool.from_function(
    func=_get_site_info,
    name="get_site_info",
    description="Get WordPress site name, description, and URL.",
    coroutine=_get_site_info,
)


ALL_TOOLS = [
    # Pages
    list_pages,
    get_page,
    create_page,
    update_page,
    delete_page,
    bulk_update_pages,
    bulk_delete_pages,
    fetch_all_pages,
    # Posts
    list_posts,
    get_post,
    create_post,
    update_post,
    delete_post,
    bulk_update_posts,
    bulk_delete_posts,
    fetch_all_posts,
    # Media
    upload_media,
    list_media,
    delete_media,
    bulk_upload_media,
    # Categories / Tags
    list_categories,
    create_category,
    list_tags,
    create_tag,
    # Users / Settings
    list_users,
    get_current_user,
    get_settings,
    update_settings,
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
    wp_cli_list_themes,
    wp_cli_activate_theme,
    # Site
    get_site_info,
]
