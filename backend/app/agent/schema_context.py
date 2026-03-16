"""Dynamic WordPress schema context builder for agent prompts.

This module fetches WordPress post types and ACF field groups at runtime
and builds a compact, deterministic schema summary for injection into
the agent's system prompt.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.agent.config import get_agent_config

logger = logging.getLogger(__name__)

# Hard limits to prevent token bloat
MAX_POST_TYPES = 25
MAX_ACF_GROUPS = 20
MAX_FIELDS_PER_GROUP = 30


@dataclass
class SchemaCapabilities:
    """Tracks what schema features are available."""

    types_supported: bool = False
    acf_groups_supported: bool = False
    types_error: str | None = None
    acf_error: str | None = None


@dataclass
class SchemaCacheEntry:
    """Cached schema context with metadata."""

    site_id: int
    base_url: str
    fetched_at: datetime
    expires_at: datetime
    capabilities: SchemaCapabilities
    context_block: str
    post_types_count: int = 0
    acf_groups_count: int = 0


# In-memory cache: key = (site_id, base_url)
_schema_cache: dict[tuple[int, str], SchemaCacheEntry] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_cache_key(site_id: int, base_url: str) -> tuple[int, str]:
    """Generate cache key from site ID and base URL."""
    return (site_id, base_url.rstrip("/").lower())


def _get_cached_entry(site_id: int, base_url: str) -> SchemaCacheEntry | None:
    """Get cached entry if still valid."""
    key = _get_cache_key(site_id, base_url)
    entry = _schema_cache.get(key)
    if entry and entry.expires_at > _now():
        logger.debug(
            f"Schema cache hit for site {site_id}",
            extra={
                "site_id": site_id,
                "base_url": base_url,
                "age_seconds": (_now() - entry.fetched_at).total_seconds(),
            },
        )
        return entry
    return None


def _set_cache_entry(entry: SchemaCacheEntry) -> None:
    """Store entry in cache."""
    key = _get_cache_key(entry.site_id, entry.base_url)
    _schema_cache[key] = entry
    logger.debug(
        f"Schema cached for site {entry.site_id}",
        extra={
            "site_id": entry.site_id,
            "base_url": entry.base_url,
            "ttl_seconds": (entry.expires_at - entry.fetched_at).total_seconds(),
        },
    )


def _get_last_known_good(site_id: int, base_url: str, max_age_seconds: int = 3600) -> SchemaCacheEntry | None:
    """Get last known good cache entry even if expired (for fallback)."""
    key = _get_cache_key(site_id, base_url)
    entry = _schema_cache.get(key)
    if entry:
        age = (_now() - entry.fetched_at).total_seconds()
        if age < max_age_seconds:
            return entry
    return None


async def _fetch_post_types(wp_client: Any) -> tuple[dict[str, Any], SchemaCapabilities]:
    """Fetch post types from /wp-json/wp/v2/types.

    Returns:
        Tuple of (types_data, capabilities) where types_data is keyed by slug.
    """
    capabilities = SchemaCapabilities()

    try:
        # Use the existing client's base_url and HTTP client
        response = await wp_client.client.get(
            f"{wp_client.base_url}/wp-json/wp/v2/types",
            timeout=10.0,
        )

        if response.status_code == 401 or response.status_code == 403:
            capabilities.types_error = f"Auth error: {response.status_code}"
            logger.warning(
                f"Post types endpoint returned {response.status_code}",
                extra={"status_code": response.status_code},
            )
            return {}, capabilities

        if response.status_code == 429:
            capabilities.types_error = "Rate limited (429)"
            logger.warning("Post types endpoint rate limited")
            return {}, capabilities

        response.raise_for_status()
        types_data = response.json()
        capabilities.types_supported = True
        return types_data, capabilities

    except Exception as e:
        capabilities.types_error = str(e)
        logger.warning(
            f"Failed to fetch post types: {e}",
            extra={"error_type": type(e).__name__},
        )
        return {}, capabilities


async def _fetch_acf_field_groups(wp_client: Any) -> tuple[list[dict], SchemaCapabilities]:
    """Fetch ACF field groups using existing WordPressClient method.

    Returns:
        Tuple of (field_groups_list, capabilities).
    """
    capabilities = SchemaCapabilities()

    try:
        result = await wp_client.list_acf_field_groups()

        if "note" in result and "not available" in result.get("note", "").lower():
            capabilities.acf_error = result.get("note")
            return [], capabilities

        field_groups = result.get("field_groups", [])
        capabilities.acf_groups_supported = bool(field_groups)
        return field_groups, capabilities

    except Exception as e:
        capabilities.acf_error = str(e)
        logger.warning(
            f"Failed to fetch ACF field groups: {e}",
            extra={"error_type": type(e).__name__},
        )
        return [], capabilities


def _summarize_post_types(types_data: dict[str, Any]) -> list[dict]:
    """Summarize post types for LLM consumption.

    Args:
        types_data: Raw response from /wp/v2/types endpoint (keyed by slug).

    Returns:
        List of summarized post type dicts, sorted by slug.
    """
    summarized = []

    for slug, data in types_data.items():
        if not isinstance(data, dict):
            continue

        summary = {
            "slug": slug,
            "rest_base": data.get("rest_base", slug),
            "rest_namespace": data.get("rest_namespace", "wp/v2"),
            "taxonomies": data.get("taxonomies", []),
            "supports": list(data.get("supports", {}).keys()) if isinstance(data.get("supports"), dict) else [],
        }
        summarized.append(summary)

    # Sort by slug for determinism
    summarized.sort(key=lambda x: x["slug"])

    # Truncate if needed
    if len(summarized) > MAX_POST_TYPES:
        logger.info(
            f"Truncated post types from {len(summarized)} to {MAX_POST_TYPES}",
            extra={"original_count": len(summarized), "max": MAX_POST_TYPES},
        )
        summarized = summarized[:MAX_POST_TYPES]

    return summarized


def _summarize_acf_groups(field_groups: list[dict]) -> list[dict]:
    """Summarize ACF field groups for LLM consumption.

    Args:
        field_groups: Raw field groups from list_acf_field_groups().

    Returns:
        List of summarized field group dicts, sorted by title.
    """
    summarized = []

    for group in field_groups:
        if not isinstance(group, dict):
            continue
        fields = group.get("fields", [])
        if isinstance(fields, list):
            # Truncate fields per group
            if len(fields) > MAX_FIELDS_PER_GROUP:
                fields = fields[:MAX_FIELDS_PER_GROUP]

            # Extract only essential field info
            field_summaries = []
            for f in fields:
                if not isinstance(f, dict):
                    continue
                field_summaries.append({
                    "name": f.get("name", ""),
                    "label": f.get("label", ""),
                    "type": f.get("type", "text"),
                })

            # Sort fields by name for determinism
            field_summaries.sort(key=lambda x: x["name"])
        else:
            field_summaries = []

        summary = {
            "title": group.get("title", ""),
            "key": group.get("key", ""),
            "fields": field_summaries,
        }
        summarized.append(summary)

    # Sort by title for determinism
    summarized.sort(key=lambda x: x.get("title", ""))

    # Truncate if needed
    if len(summarized) > MAX_ACF_GROUPS:
        logger.info(
            f"Truncated ACF groups from {len(summarized)} to {MAX_ACF_GROUPS}",
            extra={"original_count": len(summarized), "max": MAX_ACF_GROUPS},
        )
        summarized = summarized[:MAX_ACF_GROUPS]

    return summarized


def _build_context_block(
    site_name: str,
    site_url: str,
    post_types: list[dict],
    acf_groups: list[dict],
    capabilities: SchemaCapabilities,
) -> str:
    """Build the deterministic context block for the LLM.

    This creates a stable, compact text representation of the schema.
    """
    lines = [
        "<wp_schema>",
        f"Site: {site_name}",
        f"URL: {site_url}",
        "",
    ]

    # Post types section
    if post_types:
        lines.append("## Post Types")
        for pt in post_types:
            rest_path = f"/wp-json/{pt.get('rest_namespace', 'wp/v2')}/{pt.get('rest_base', pt['slug'])}"
            lines.append(f"- {pt['slug']} → {rest_path}")
            if pt.get("taxonomies"):
                lines.append(f"  Taxonomies: {', '.join(pt['taxonomies'])}")
        lines.append("")
    elif capabilities.types_error:
        lines.append(f"## Post Types: Not available ({capabilities.types_error})")
        lines.append("")

    # ACF section
    if acf_groups:
        lines.append("## ACF Field Groups")
        for group in acf_groups:
            lines.append(f"- {group.get('title', 'Untitled')} (key: {group.get('key', '')})")
            for fld in group.get("fields", []):
                lines.append(f"    - {fld.get('name', '')}: {fld.get('type', 'text')} ({fld.get('label', '')})")
        lines.append("")
    elif capabilities.acf_error:
        lines.append(f"## ACF Field Groups: Not available ({capabilities.acf_error})")
        lines.append("Note: ACF fields may still be readable on individual posts via the 'acf' field.")
        lines.append("")

    # Limitations section
    limitations = []
    if not capabilities.types_supported:
        limitations.append("Post type discovery unavailable")
    if not capabilities.acf_groups_supported:
        limitations.append("ACF field group listing unavailable")

    if len(post_types) == MAX_POST_TYPES:
        limitations.append(f"Post types truncated to {MAX_POST_TYPES}")
    if len(acf_groups) == MAX_ACF_GROUPS:
        limitations.append(f"ACF groups truncated to {MAX_ACF_GROUPS}")

    if limitations:
        lines.append("## Limitations")
        for lim in limitations:
            lines.append(f"- {lim}")
        lines.append("")

    lines.append("</wp_schema>")

    return "\n".join(lines)


async def build_schema_context(
    wp_client: Any,
    site_id: int,
    site_name: str = "WordPress Site",
) -> tuple[str, SchemaCapabilities]:
    """Build dynamic schema context for a WordPress site.

    This is the main entry point. It fetches post types and ACF field groups,
    summarizes them, and returns a context block suitable for injection into
    the agent's system prompt.

    Args:
        wp_client: WordPressClient instance with active connection.
        site_id: Database ID of the WordPressSite (for caching).
        site_name: Human-readable site name.

    Returns:
        Tuple of (context_block, capabilities).
    """
    config = get_agent_config()
    base_url = wp_client.base_url

    # Check cache first
    cached = _get_cached_entry(site_id, base_url)
    if cached:
        return cached.context_block, cached.capabilities

    start_time = time.time()

    # Fetch concurrently for performance. Use a single overall timeout so we don't
    # accidentally block for ~30s when each await has its own timeout.
    try:
        (types_data, types_caps), (acf_groups, acf_caps) = await asyncio.wait_for(
            asyncio.gather(
                _fetch_post_types(wp_client),
                _fetch_acf_field_groups(wp_client),
            ),
            timeout=15.0,
        )
    except asyncio.TimeoutError:
        logger.error("Schema fetch timed out")
        # Try to use last known good cache
        last_good = _get_last_known_good(site_id, base_url)
        if last_good:
            return last_good.context_block, last_good.capabilities
        # Return minimal context
        caps = SchemaCapabilities(
            types_error="Timeout",
            acf_error="Timeout",
        )
        return _build_context_block(site_name, base_url, [], [], caps), caps

    # Combine capabilities
    capabilities = SchemaCapabilities(
        types_supported=types_caps.types_supported,
        acf_groups_supported=acf_caps.acf_groups_supported,
        types_error=types_caps.types_error,
        acf_error=acf_caps.acf_error,
    )

    # Summarize
    post_types = _summarize_post_types(types_data)
    acf_summary = _summarize_acf_groups(acf_groups)

    # Build context
    context_block = _build_context_block(
        site_name=site_name,
        site_url=base_url,
        post_types=post_types,
        acf_groups=acf_summary,
        capabilities=capabilities,
    )

    duration_ms = (time.time() - start_time) * 1000

    logger.info(
        f"Schema context built in {duration_ms:.0f}ms",
        extra={
            "site_id": site_id,
            "base_url": base_url,
            "duration_ms": duration_ms,
            "post_types_count": len(post_types),
            "acf_groups_count": len(acf_summary),
            "types_supported": capabilities.types_supported,
            "acf_supported": capabilities.acf_groups_supported,
        },
    )

    # Cache the result
    ttl_seconds = config.wp_dynamic_schema_ttl
    cache_entry = SchemaCacheEntry(
        site_id=site_id,
        base_url=base_url,
        fetched_at=_now(),
        expires_at=datetime.fromtimestamp(time.time() + ttl_seconds, tz=timezone.utc),
        capabilities=capabilities,
        context_block=context_block,
        post_types_count=len(post_types),
        acf_groups_count=len(acf_summary),
    )
    _set_cache_entry(cache_entry)

    return context_block, capabilities


def clear_schema_cache(site_id: int | None = None) -> None:
    """Clear schema cache.

    Args:
        site_id: If provided, clear only that site's cache. Otherwise clear all.
    """
    global _schema_cache

    if site_id is not None:
        keys_to_remove = [k for k in _schema_cache if k[0] == site_id]
        for k in keys_to_remove:
            del _schema_cache[k]
        logger.info(f"Cleared schema cache for site {site_id}")
    else:
        _schema_cache.clear()
        logger.info("Cleared all schema cache")
