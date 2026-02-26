import json
from typing import Any, Dict, Optional

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_pages",
            "description": "List all WordPress pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "default": 10},
                    "status": {"type": "string", "enum": ["publish", "draft", "pending", "private", "trash"], "default": "publish"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page",
            "description": "Get a specific page by ID.",
            "parameters": {
                "type": "object",
                "properties": {"page_id": {"type": "integer"}},
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_page",
            "description": "Create a new page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "status": {"type": "string", "enum": ["publish", "draft"]},
                    "acf_fields": {"type": "object"},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_page",
            "description": "Update an existing page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "acf_fields": {"type": "object"},
                },
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_page",
            "description": "Delete a page.",
            "parameters": {
                "type": "object",
                "properties": {"page_id": {"type": "integer"}, "force": {"type": "boolean", "default": False}},
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_posts",
            "description": "List all WordPress posts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "per_page": {"type": "integer", "default": 10},
                    "status": {"type": "string", "enum": ["publish", "draft", "pending", "private", "trash"], "default": "publish"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_post",
            "description": "Create a new post.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "status": {"type": "string", "enum": ["publish", "draft"]},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_post",
            "description": "Delete a post.",
            "parameters": {
                "type": "object",
                "properties": {"post_id": {"type": "integer"}, "force": {"type": "boolean", "default": False}},
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "upload_media",
            "description": "Upload a file to media library.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}, "title": {"type": "string"}},
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_site_info",
            "description": "Get site name and description.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

async def execute_tool(name: str, args: Dict[str, Any], wp_client: Optional[Any]) -> Dict[str, Any]:
    """Route tool calls to WordPress client functions."""
    try:
        if not wp_client:
            return {"error": "WordPress client not configured."}

        method = getattr(wp_client, name, None)
        if not method:
            return {"error": f"Tool '{name}' not found."}

        return await method(**args)
    except Exception as e:
        return {"error": str(e)}
