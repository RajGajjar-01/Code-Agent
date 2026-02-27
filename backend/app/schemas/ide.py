"""Pydantic schemas for the IDE file-system API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class FileNode(BaseModel):
    """Single node in the file tree (file or directory)."""
    name: str
    path: str  # relative to WP_ROOT_PATH
    type: Literal["file", "directory"]
    extension: Optional[str] = None
    size: Optional[int] = None
    children: Optional[list[FileNode]] = None


class FileReadResponse(BaseModel):
    """Response when reading a file's content."""
    path: str
    content: str
    language: str  # e.g. "php", "css", "javascript"
    size: int
    last_modified: float


class FileWriteRequest(BaseModel):
    """Request body for writing/saving a file."""
    path: str
    content: str


class FileCreateRequest(BaseModel):
    """Request body for creating a new file or directory."""
    name: str
    parent_path: str
    type: Literal["file", "directory"]



class FileWriteResponse(BaseModel):
    """Response after writing a file."""
    path: str
    success: bool
    message: str
    last_modified: float
