"""IDE file-system API routes."""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.schemas.ide import FileNode, FileWriteRequest, FileWriteResponse, FileReadResponse, FileCreateRequest
from app.services.wordpress import get_file_tree, read_file, write_file, validate_path, create_node

router = APIRouter()
logger = logging.getLogger("ide")


@router.get("/tree/roots")
async def tree_roots():
    """Return top-level editable directories as quick shortcuts."""
    label_map = {
        "wp-content/themes": "Themes",
        "wp-content/plugins": "Plugins",
        "wp-content/mu-plugins": "Must-Use Plugins",
    }
    roots = []
    for d in settings.WP_EDITABLE_DIRS:
        abs_dir = os.path.join(settings.WP_ROOT_PATH, d)
        if os.path.isdir(abs_dir):
            roots.append({"name": label_map.get(d, d), "path": d})
    return {"roots": roots}


@router.get("/tree")
async def file_tree(dir: str = Query("wp-content", description="Directory relative to WP root")):
    """Return a recursive FileNode tree for the requested directory."""
    ok, err = validate_path(dir)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    abs_dir = os.path.realpath(os.path.join(settings.WP_ROOT_PATH, dir))
    if not os.path.isdir(abs_dir):
        raise HTTPException(status_code=404, detail=f"Directory not found: {dir}")

    tree = get_file_tree(abs_dir, settings.WP_ROOT_PATH)
    return {"tree": tree}


@router.get("/file", response_model=FileReadResponse)
async def read_file_endpoint(path: str = Query(..., description="File path relative to WP root")):
    """Read a file's content and metadata."""
    try:
        return read_file(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/file", response_model=FileWriteResponse)
async def write_file_endpoint(req: FileWriteRequest):
    """Save content to a file (must be inside an editable directory)."""
    try:
        result = write_file(req.path, req.content)
        logger.info("IDE file written: %s at %s", req.path, datetime.now(timezone.utc).isoformat())
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/create")
async def create_node_endpoint(req: FileCreateRequest):
    """Create a new file or directory."""
    try:
        path = create_node(req.parent_path, req.name, req.type)
        logger.info("IDE node created: %s (%s)", path, req.type)
        return {"path": path, "success": True}
    except FileExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
