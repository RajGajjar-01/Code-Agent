import asyncio
import json
import os
import urllib.request
import contextvars
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
    BulkCreateMenuItemsInput,
    BulkCreateMenusInput,
    CreateCategoryInput,
    CreateMenuInput,
    CreateMenuItemInput,
    CreateMenuTreeInput,
    CreatePageInput,
    CreatePostInput,
    CreateTagInput,
    CreateThemeFileInput,
    DeleteMenuInput,
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
    ListMenuItemsInput,
    ListMenusInput,
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
    ListMenuLocationsInput,
    AssignMenuLocationsInput,
    WpCliMenuCreateInput,
    WpCliMenuLocationAssignInput,
    WpCliMenuLocationListInput,
    WpCliMenuItemAddCustomInput,
    WpCliMenuItemAddPostInput,
    WpCliScaffoldThemeInput,
    WpCliScaffoldPostTypeInput,
    WpCliScaffoldTaxonomyInput,
    WpCliThemeDeleteInput,
)

_wp_client_var: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "wp_client",
    default=None,
)
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


def set_wp_client(client: Any) -> contextvars.Token:
    return _wp_client_var.set(client)


def reset_wp_client(token: contextvars.Token) -> None:
    _wp_client_var.reset(token)


def set_wp_cli_context(wp_path: str | None = None, default_url: str | None = None) -> None:
    global _wp_cli_wp_path_override, _wp_cli_default_url_override
    _wp_cli_wp_path_override = wp_path
    _wp_cli_default_url_override = default_url


def _find_wordpress_path(start_path: str | Path | None = None) -> Path | None:
    """
    Search upward from start_path to find a WordPress installation.
    
    Looks for wp-config.php in current directory and all parent directories.
    Returns the first directory containing wp-config.php, or None if not found.
    
    Similar to how git finds .git directories.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    while True:
        if (current / "wp-config.php").exists():
            return current
        
        parent = current.parent
        if parent == current:  # Reached root
            return None
        current = parent
    
    return None


def discover_wordpress_path() -> dict:
    """
    Discover WordPress installation path.
    
    Returns dict with found path or error message.
    Useful for API endpoints that need to validate/preview discovery.
    """
    # 1. Try upward search from current directory
    discovered = _find_wordpress_path()
    if discovered:
        return {
            "found": True,
            "path": str(discovered),
            "wp_config_exists": (discovered / "wp-config.php").exists(),
            "source": "cwd_search",
        }
    
    # 2. Search Local by Flywheel common locations
    home = Path.home()
    local_sites = home / "Local Sites"
    if local_sites.exists():
        for site_dir in local_sites.iterdir():
            if site_dir.is_dir():
                wp_path = site_dir / "app" / "public"
                if (wp_path / "wp-config.php").exists():
                    return {
                        "found": True,
                        "path": str(wp_path),
                        "wp_config_exists": True,
                        "source": "local_by_flywheel",
                        "site_name": site_dir.name,
                    }
    
    # 3. Search other common locations
    common_paths = [
        "/var/www/html",
        "/var/www",
        "/opt/lampp/htdocs",
        "/usr/share/nginx/html",
        home / "www",
        home / "sites",
        home / "public_html",
    ]
    for base_path in common_paths:
        base = Path(base_path)
        if base.exists():
            for wp_dir in base.iterdir():
                if wp_dir.is_dir() and (wp_dir / "wp-config.php").exists():
                    return {
                        "found": True,
                        "path": str(wp_dir),
                        "wp_config_exists": True,
                        "source": "common_path",
                    }
    
    return {
        "found": False,
        "path": None,
        "cwd": str(Path.cwd()),
        "message": "No WordPress installation found. Searched: current directory tree, Local by Flywheel sites, and common web roots.",
    }


def _client():
    client = _wp_client_var.get()
    if not client:
        raise RuntimeError(
            "WordPress client not configured. Select an active WordPress site (wp_site_id) and retry."
        )
    return client


def _get_wp_cli_args() -> tuple[str, list[str]]:
    config = get_agent_config()
    wp_bin = config.wp_cli_path

    # Prefer a vendored WP-CLI binary if present. This makes local/dev setups
    # work even if PATH doesn't contain `wp` and env vars aren't configured.
    local_path = _default_local_wp_cli_path()
    if wp_bin == "wp" and local_path.exists():
        wp_bin = str(local_path)

    if config.wp_cli_auto_install:
        if wp_bin == "wp" or (wp_bin and wp_bin != "wp" and not Path(wp_bin).exists()):
            if local_path.exists():
                wp_bin = str(local_path)

    wp_path = _wp_cli_wp_path_override or config.wp_cli_wp_path
    
    if not wp_path:
        # Auto-discover WordPress installation
        discovered = _find_wordpress_path()
        if discovered:
            wp_path = str(discovered)
        else:
            raise RuntimeError(
                "WP-CLI path not configured and no WordPress installation found. "
                "Provide WP_CLI_WP_PATH (path containing wp-config.php) or run from within a WordPress directory."
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


async def _create_page(
    title: str,
    content: str,
    status: str = "publish",
    allow_duplicate: bool = False,
) -> dict:
    existing = await _client().find_page_by_slug_or_title(title)
    if existing and not allow_duplicate:
        clean_title = (existing.get("title") or title or "").strip()
        return {
            "status": "exists",
            "needs_confirmation": True,
            "message": (
                f"A page titled '{clean_title}' already exists. "
                "Are you sure you want to create another page with the same name?"
            ),
            "existing": {
                "title": existing.get("title"),
                "link": existing.get("link"),
                "status": existing.get("status"),
                "slug": existing.get("slug"),
            },
            "next_call": {
                "tool": "create_page",
                "arguments": {
                    "title": title,
                    "content": content,
                    "status": status,
                    "allow_duplicate": True,
                },
            },
        }

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


async def _wp_cli_menu_create(name: str, porcelain: bool = True) -> dict:
    cmd = ["menu", "create", name]
    if porcelain:
        cmd.append("--porcelain")
    res = await _run_wp_cli(cmd)
    menu_id: int | None = None
    if porcelain:
        try:
            menu_id = int((res.get("stdout") or "").strip())
        except Exception:
            menu_id = None
    return {"menu_id": menu_id, "stdout": res.get("stdout"), "stderr": res.get("stderr")}


async def _wp_cli_menu_location_list(format: str = "json") -> dict:
    res = await _run_wp_cli(["menu", "location", "list", f"--format={format}"])
    if format == "json":
        try:
            return {"locations": json.loads(res.get("stdout") or "[]")}
        except Exception:
            return {"locations": [], "stdout": res.get("stdout"), "stderr": res.get("stderr")}
    return {"stdout": res.get("stdout"), "stderr": res.get("stderr")}


async def _wp_cli_menu_location_assign(menu: str, location: str) -> dict:
    res = await _run_wp_cli(["menu", "location", "assign", str(menu), str(location)])
    return {"status": "assigned", "menu": menu, "location": location, "stdout": res.get("stdout")}


async def _wp_cli_menu_item_add_post(
    menu: str,
    post_id: int,
    title: str | None = None,
    position: int | None = None,
    parent_id: int | None = None,
    porcelain: bool = True,
) -> dict:
    cmd: list[str] = ["menu", "item", "add-post", str(menu), str(int(post_id))]
    if title:
        cmd.append(f"--title={title}")
    if position is not None:
        cmd.append(f"--position={int(position)}")
    if parent_id is not None:
        cmd.append(f"--parent-id={int(parent_id)}")
    if porcelain:
        cmd.append("--porcelain")
    res = await _run_wp_cli(cmd)
    menu_item_id: int | None = None
    if porcelain:
        try:
            menu_item_id = int((res.get("stdout") or "").strip())
        except Exception:
            menu_item_id = None
    return {"menu_item_id": menu_item_id, "stdout": res.get("stdout"), "stderr": res.get("stderr")}


async def _wp_cli_menu_item_add_custom(
    menu: str,
    title: str,
    link: str,
    position: int | None = None,
    parent_id: int | None = None,
    porcelain: bool = True,
) -> dict:
    clean_link = (link or "").strip()
    if not clean_link:
        raise ValueError("link is required")
    cmd: list[str] = ["menu", "item", "add-custom", str(menu), str(title), clean_link]
    if position is not None:
        cmd.append(f"--position={int(position)}")
    if parent_id is not None:
        cmd.append(f"--parent-id={int(parent_id)}")
    if porcelain:
        cmd.append("--porcelain")
    res = await _run_wp_cli(cmd)
    menu_item_id: int | None = None
    if porcelain:
        try:
            menu_item_id = int((res.get("stdout") or "").strip())
        except Exception:
            menu_item_id = None
    return {"menu_item_id": menu_item_id, "stdout": res.get("stdout"), "stderr": res.get("stderr")}


async def _wp_cli_scaffold_theme(
    theme_slug: str,
    theme_name: str | None = None,
    author: str | None = None,
    author_uri: str | None = None,
    theme_uri: str | None = None,
    sassify: bool = True,
    activate: bool = False,
    force: bool = False,
) -> dict:
    """
    Scaffold a classic WordPress theme using WP-CLI scaffold _s command.
    
    This creates a complete theme based on Underscores (_s) starter theme
    with all required files following WordPress best practices.
    """
    cmd: list[str] = ["scaffold", "_s", theme_slug]
    
    if theme_name:
        cmd.append(f"--theme_name={theme_name}")
    if author:
        cmd.append(f"--author={author}")
    if author_uri:
        cmd.append(f"--author_uri={author_uri}")
    if theme_uri:
        cmd.append(f"--theme_uri={theme_uri}")
    if sassify:
        cmd.append("--sassify")
    if activate:
        cmd.append("--activate")
    if force:
        cmd.append("--force")
    
    res = await _run_wp_cli(cmd)
    return {
        "status": "created",
        "theme_slug": theme_slug,
        "theme_name": theme_name or theme_slug,
        "sassify": sassify,
        "activated": activate,
        "stdout": res.get("stdout"),
        "message": f"Theme '{theme_name or theme_slug}' created successfully."
    }


async def _wp_cli_scaffold_post_type(
    post_type: str,
    label: str | None = None,
    theme: str | None = None,
    dashicon: str | None = None,
    textdomain: str | None = None,
) -> dict:
    """
    Scaffold a custom post type using WP-CLI.
    
    Generates PHP code for registering a custom post type.
    If theme is provided, saves to theme directory; otherwise outputs to stdout.
    """
    cmd: list[str] = ["scaffold", "post-type", post_type]
    
    if label:
        cmd.append(f"--label={label}")
    if theme:
        cmd.append(f"--theme={theme}")
    if dashicon:
        cmd.append(f"--dashicon={dashicon}")
    if textdomain:
        cmd.append(f"--textdomain={textdomain}")
    
    res = await _run_wp_cli(cmd)
    return {
        "status": "created",
        "post_type": post_type,
        "label": label or post_type,
        "theme": theme,
        "stdout": res.get("stdout"),
        "message": f"Custom post type '{post_type}' scaffolded."
    }


async def _wp_cli_scaffold_taxonomy(
    taxonomy: str,
    post_types: str,
    label: str | None = None,
    theme: str | None = None,
) -> dict:
    """
    Scaffold a custom taxonomy using WP-CLI.
    
    Generates PHP code for registering a custom taxonomy.
    """
    cmd: list[str] = ["scaffold", "taxonomy", taxonomy, f"--post_types={post_types}"]
    
    if label:
        cmd.append(f"--label={label}")
    if theme:
        cmd.append(f"--theme={theme}")
    
    res = await _run_wp_cli(cmd)
    return {
        "status": "created",
        "taxonomy": taxonomy,
        "post_types": post_types,
        "label": label or taxonomy,
        "theme": theme,
        "stdout": res.get("stdout"),
        "message": f"Taxonomy '{taxonomy}' scaffolded for post types: {post_types}."
    }


async def _wp_cli_theme_delete(theme_slug: str) -> dict:
    """
    Delete a WordPress theme using WP-CLI.
    """
    res = await _run_wp_cli(["theme", "delete", theme_slug, "--force"])
    return {
        "status": "deleted",
        "theme_slug": theme_slug,
        "stdout": res.get("stdout"),
        "message": f"Theme '{theme_slug}' deleted."
    }


async def _list_menu_locations() -> dict:
    return await _client().list_menu_locations()


async def _assign_menu_locations(menu_id: int, locations: list[str]) -> dict:
    return await _client().assign_menu_locations(menu_id=menu_id, locations=locations)


async def _get_site_info() -> dict:
    return await _client().get_site_info()


async def _list_menus(per_page: int = 100) -> dict:
    per_page = min(max(per_page, 1), 100)
    return await _client().list_menus(per_page=per_page)


async def _create_menu(name: str) -> dict:
    return await _client().create_menu(name=name)


async def _delete_menu(menu_id: int, force: bool = True) -> dict:
    return await _client().delete_menu(menu_id, force=force)


async def _list_menu_items(menu_id: int | None = None, per_page: int = 100) -> dict:
    per_page = min(max(per_page, 1), 100)
    params: dict[str, Any] = {"per_page": per_page}
    if menu_id is not None:
        params["menus"] = menu_id
    return await _client().list_menu_items(**params)


async def _create_menu_item(
    menu_id: int,
    title: str,
    type: str = "custom",
    url: str | None = None,
    object_id: int | None = None,
    object: str | None = None,
    parent: int | None = 0,
    menu_order: int | None = None,
    status: str = "publish",
) -> dict:
    if (type or "").strip() == "custom" and not (url or "").strip():
        raise ValueError("url is required when using a custom menu item type")
    return await _client().create_menu_item(
        menu_id=menu_id,
        title=title,
        type=type,
        url=url,
        object_id=object_id,
        object=object,
        parent=parent,
        menu_order=menu_order,
        status=status,
    )


async def _bulk_create_menus(menus: list[dict]) -> dict:
    return await _client().bulk_create_menus(menus)


async def _bulk_create_menu_items(items: list[dict]) -> dict:
    return await _client().bulk_create_menu_items(items)


async def _create_menu_tree(
    items: list[dict],
    menu_name: str | None = None,
    menu_id: int | None = None,
) -> dict:
    if menu_id is None and not (menu_name or "").strip():
        raise ValueError("menu_name is required when menu_id is not provided")

    def _clean_str(v: Any | None) -> str:
        return str(v or "").strip()

    def _walk(nodes: list[dict], *, level: int, parent_ref: str) -> None:
        if level > 2:
            raise ValueError("Only 2 menu levels are supported")

        for idx, node in enumerate(nodes or []):
            if not isinstance(node, dict):
                raise ValueError("Invalid menu tree item: expected object")

            ref = _clean_str(node.get("ref")) or f"{parent_ref}:{idx}"
            title = _clean_str(node.get("title"))
            item_type = _clean_str(node.get("type")) or "custom"

            if item_type == "custom":
                url = _clean_str(node.get("url"))
                if not url:
                    raise ValueError(
                        "url is required when using a custom menu item type "
                        f"(ref='{ref}', title='{title or 'unknown'}')"
                    )

            children = node.get("children") or []
            if children:
                if level == 2:
                    raise ValueError("Only 2 menu levels are supported")
                if not isinstance(children, list):
                    raise ValueError(
                        f"Invalid children for menu tree item (ref='{ref}'): expected list"
                    )
                _walk(children, level=level + 1, parent_ref=ref)

    _walk(items, level=1, parent_ref="root")

    return await _client().bulk_create_menu_tree(items=items, menu_name=menu_name, menu_id=menu_id)


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

wp_cli_menu_create = StructuredTool.from_function(
    func=_wp_cli_menu_create,
    name="wp_cli_menu_create",
    description="Create a navigation menu using WP-CLI.",
    args_schema=WpCliMenuCreateInput,
    coroutine=_wp_cli_menu_create,
)

wp_cli_menu_location_list = StructuredTool.from_function(
    func=_wp_cli_menu_location_list,
    name="wp_cli_menu_location_list",
    description="List available theme menu locations using WP-CLI.",
    args_schema=WpCliMenuLocationListInput,
    coroutine=_wp_cli_menu_location_list,
)

wp_cli_menu_location_assign = StructuredTool.from_function(
    func=_wp_cli_menu_location_assign,
    name="wp_cli_menu_location_assign",
    description="Assign a menu to a theme location using WP-CLI.",
    args_schema=WpCliMenuLocationAssignInput,
    coroutine=_wp_cli_menu_location_assign,
)

wp_cli_menu_item_add_post = StructuredTool.from_function(
    func=_wp_cli_menu_item_add_post,
    name="wp_cli_menu_item_add_post",
    description="Add a page/post as a menu item using WP-CLI (supports submenu via parent_id).",
    args_schema=WpCliMenuItemAddPostInput,
    coroutine=_wp_cli_menu_item_add_post,
)

wp_cli_menu_item_add_custom = StructuredTool.from_function(
    func=_wp_cli_menu_item_add_custom,
    name="wp_cli_menu_item_add_custom",
    description="Add a custom link as a menu item using WP-CLI (supports submenu via parent_id).",
    args_schema=WpCliMenuItemAddCustomInput,
    coroutine=_wp_cli_menu_item_add_custom,
)

wp_cli_scaffold_theme = StructuredTool.from_function(
    func=_wp_cli_scaffold_theme,
    name="wp_cli_scaffold_theme",
    description=(
        "Create a complete WordPress classic theme using WP-CLI scaffold _s. "
        "Generates all required files (style.css, index.php, functions.php, etc.) "
        "based on the Underscores (_s) starter theme. "
        "Use sassify=True for SASS support. "
        "Use activate=True to immediately activate the theme."
    ),
    args_schema=WpCliScaffoldThemeInput,
    coroutine=_wp_cli_scaffold_theme,
)

wp_cli_scaffold_post_type = StructuredTool.from_function(
    func=_wp_cli_scaffold_post_type,
    name="wp_cli_scaffold_post_type",
    description=(
        "Scaffold a custom post type registration using WP-CLI. "
        "Generates PHP code for register_post_type(). "
        "Provide theme slug to save the file in the theme directory."
    ),
    args_schema=WpCliScaffoldPostTypeInput,
    coroutine=_wp_cli_scaffold_post_type,
)

wp_cli_scaffold_taxonomy = StructuredTool.from_function(
    func=_wp_cli_scaffold_taxonomy,
    name="wp_cli_scaffold_taxonomy",
    description=(
        "Scaffold a custom taxonomy registration using WP-CLI. "
        "Generates PHP code for register_taxonomy(). "
        "Provide theme slug to save the file in the theme directory."
    ),
    args_schema=WpCliScaffoldTaxonomyInput,
    coroutine=_wp_cli_scaffold_taxonomy,
)

wp_cli_theme_delete = StructuredTool.from_function(
    func=_wp_cli_theme_delete,
    name="wp_cli_theme_delete",
    description="Delete a WordPress theme by its slug using WP-CLI.",
    args_schema=WpCliThemeDeleteInput,
    coroutine=_wp_cli_theme_delete,
)

list_menu_locations = StructuredTool.from_function(
    func=_list_menu_locations,
    name="list_menu_locations",
    description="List theme menu locations (REST: /wp/v2/menu-locations).",
    args_schema=ListMenuLocationsInput,
    coroutine=_list_menu_locations,
)

assign_menu_locations = StructuredTool.from_function(
    func=_assign_menu_locations,
    name="assign_menu_locations",
    description="Assign a menu to one or more theme menu locations (REST: update /wp/v2/menus/{id} with locations).",
    args_schema=AssignMenuLocationsInput,
    coroutine=_assign_menu_locations,
)

get_site_info = StructuredTool.from_function(
    func=_get_site_info,
    name="get_site_info",
    description="Get WordPress site name, description, and URL.",
    coroutine=_get_site_info,
)


list_menus = StructuredTool.from_function(
    func=_list_menus,
    name="list_menus",
    description="List WordPress navigation menus (requires /wp/v2/menus support on site).",
    args_schema=ListMenusInput,
    coroutine=_list_menus,
)
create_menu = StructuredTool.from_function(
    func=_create_menu,
    name="create_menu",
    description="Create a WordPress navigation menu.",
    args_schema=CreateMenuInput,
    coroutine=_create_menu,
)
delete_menu = StructuredTool.from_function(
    func=_delete_menu,
    name="delete_menu",
    description="Delete a WordPress navigation menu by ID.",
    args_schema=DeleteMenuInput,
    coroutine=_delete_menu,
)
list_menu_items = StructuredTool.from_function(
    func=_list_menu_items,
    name="list_menu_items",
    description="List menu items, optionally filtered by menu ID.",
    args_schema=ListMenuItemsInput,
    coroutine=_list_menu_items,
)
create_menu_item = StructuredTool.from_function(
    func=_create_menu_item,
    name="create_menu_item",
    description="Create a menu item. Use parent=<menu_item_id> to create a submenu item.",
    args_schema=CreateMenuItemInput,
    coroutine=_create_menu_item,
)
bulk_create_menus = StructuredTool.from_function(
    func=_bulk_create_menus,
    name="bulk_create_menus",
    description="Bulk create menus (uses WP batch/v1 when available).",
    args_schema=BulkCreateMenusInput,
    coroutine=_bulk_create_menus,
)
bulk_create_menu_items = StructuredTool.from_function(
    func=_bulk_create_menu_items,
    name="bulk_create_menu_items",
    description="Bulk create menu items (uses WP batch/v1 when available).",
    args_schema=BulkCreateMenuItemsInput,
    coroutine=_bulk_create_menu_items,
)
create_menu_tree = StructuredTool.from_function(
    func=_create_menu_tree,
    name="create_menu_tree",
    description="Create a menu and a hierarchical tree of menu items/submenu items.",
    args_schema=CreateMenuTreeInput,
    coroutine=_create_menu_tree,
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
    wp_cli_list_themes,
    wp_cli_activate_theme,
    wp_cli_menu_create,
    wp_cli_menu_location_list,
    wp_cli_menu_location_assign,
    wp_cli_menu_item_add_post,
    wp_cli_menu_item_add_custom,
    wp_cli_scaffold_theme,
    wp_cli_scaffold_post_type,
    wp_cli_scaffold_taxonomy,
    wp_cli_theme_delete,
    # Site
    get_site_info,
    # Menus
    list_menu_locations,
    assign_menu_locations,
    list_menus,
    create_menu,
    delete_menu,
    list_menu_items,
    create_menu_item,
    bulk_create_menus,
    bulk_create_menu_items,
    create_menu_tree,
]


# Token-optimized tool subsets. Binding fewer tools reduces prompt size significantly
# because tool schemas/descriptions are included in each LLM call.
READ_TOOLS = [
    # Pages
    list_pages,
    get_page,
    # Posts
    list_posts,
    get_post,
    # Media
    list_media,
    # Categories / Tags
    list_categories,
    list_tags,
    # Users / Settings
    list_users,
    get_current_user,
    get_settings,
    # ACF
    get_acf_fields,
    list_acf_field_groups,
    # Themes
    list_themes,
    get_active_theme,
    wp_cli_list_themes,
    wp_cli_menu_location_list,
    # Site
    get_site_info,
    # Menus
    list_menu_locations,
    list_menus,
    list_menu_items,
]


WRITE_TOOLS = [
    # Pages
    create_page,
    update_page,
    delete_page,
    bulk_update_pages,
    bulk_delete_pages,
    fetch_all_pages,
    # Posts
    create_post,
    update_post,
    delete_post,
    bulk_update_posts,
    bulk_delete_posts,
    fetch_all_posts,
    # Media
    upload_media,
    delete_media,
    bulk_upload_media,
    # Categories / Tags
    create_category,
    create_tag,
    # Settings
    update_settings,
    # ACF
    update_acf_fields,
    # Themes
    create_theme_file,
    read_theme_file,
    wp_cli_activate_theme,
    wp_cli_menu_create,
    wp_cli_menu_location_assign,
    wp_cli_menu_item_add_post,
    wp_cli_menu_item_add_custom,
    wp_cli_scaffold_theme,
    wp_cli_scaffold_post_type,
    wp_cli_scaffold_taxonomy,
    wp_cli_theme_delete,
    # Menus
    assign_menu_locations,
    create_menu,
    delete_menu,
    create_menu_item,
    bulk_create_menus,
    bulk_create_menu_items,
    create_menu_tree,
]
