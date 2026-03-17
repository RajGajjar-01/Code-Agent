import logging
import mimetypes
import uuid
from typing import Optional
import asyncio

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """Service for handling image uploads to Supabase Storage via HTTP API."""

    @classmethod
    def _get_headers(cls) -> dict:
        """Get authorization headers for Supabase API."""
        return {
            "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
            "apikey": settings.SUPABASE_SECRET_KEY,
        }

    @classmethod
    def _get_content_type(cls, filename: str) -> str:
        """Determine content type from filename."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    @classmethod
    def _get_storage_url(cls) -> str:
        """Get base storage API URL."""
        return f"{settings.SUPABASE_URL}/storage/v1"

    @classmethod
    def _get_public_url(cls, storage_path: str) -> str:
        """Get public URL for a file."""
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET_NAME}/{storage_path}"

    @classmethod
    async def upload_image(
        cls,
        file_data: bytes,
        filename: str,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """Upload an image to Supabase Storage."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SECRET_KEY in environment."
            )

        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

        if folder:
            storage_path = f"{folder.strip('/')}/{unique_name}"
        else:
            storage_path = unique_name

        if not content_type:
            content_type = cls._get_content_type(filename)

        url = f"{cls._get_storage_url()}/object/{settings.SUPABASE_BUCKET_NAME}/{storage_path}"

        headers = cls._get_headers()
        headers["Content-Type"] = content_type
        headers["x-upsert"] = "false"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, content=file_data, headers=headers)

            if response.status_code not in (200, 201):
                logger.error(f"Failed to upload image: {response.status_code} {response.text}")
                raise Exception(f"Upload failed: {response.status_code} {response.text}")

            logger.info(f"Successfully uploaded image to Supabase: {storage_path}")

            return {
                "path": storage_path,
                "full_path": f"{settings.SUPABASE_BUCKET_NAME}/{storage_path}",
                "public_url": cls._get_public_url(storage_path),
            }

    @classmethod
    def upload_image_from_file(cls, file_path: str, folder: Optional[str] = None) -> dict:
        """Upload an image from a local file path (sync wrapper)."""

        with open(file_path, "rb") as f:
            file_data = f.read()

        filename = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
        return asyncio.run(cls.upload_image(file_data, filename, folder))

    @classmethod
    async def delete_image(cls, storage_path: str) -> bool:
        """Delete an image from Supabase Storage."""
        url = f"{cls._get_storage_url()}/object/{settings.SUPABASE_BUCKET_NAME}"

        headers = cls._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {"prefixes": [storage_path]}

        async with httpx.AsyncClient() as client:
            response = await client.request("DELETE", url, json=payload, headers=headers)

            if response.status_code not in (200, 204):
                logger.error(f"Failed to delete image: {response.status_code} {response.text}")
                raise Exception(f"Delete failed: {response.status_code} {response.text}")

            logger.info(f"Successfully deleted image from Supabase: {storage_path}")
            return True

    @classmethod
    def get_public_url(cls, storage_path: str) -> str:
        """Get the public URL for an image."""
        return cls._get_public_url(storage_path)

    @classmethod
    async def download_image(cls, storage_path: str) -> bytes:
        """Download an image from Supabase Storage."""
        url = cls._get_public_url(storage_path)

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to download image: {response.status_code}")
                raise Exception(f"Download failed: {response.status_code}")

            logger.info(f"Successfully downloaded image from Supabase: {storage_path}")
            return response.content

    @classmethod
    async def list_images(cls, folder: Optional[str] = None, limit: int = 100) -> list:
        """List images in a folder."""
        url = f"{cls._get_storage_url()}/object/list/{settings.SUPABASE_BUCKET_NAME}"

        headers = cls._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {"limit": limit}
        if folder:
            payload["prefix"] = folder.strip("/") + "/"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                logger.error(f"Failed to list images: {response.status_code} {response.text}")
                raise Exception(f"List failed: {response.status_code} {response.text}")

            return response.json()


async def upload_image(
    file_data: bytes,
    filename: str,
    folder: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    """Upload an image to Supabase Storage."""
    return await SupabaseStorageService.upload_image(file_data, filename, folder, content_type)


async def delete_image(storage_path: str) -> bool:
    """Delete an image from Supabase Storage."""
    return await SupabaseStorageService.delete_image(storage_path)


def get_public_url(storage_path: str) -> str:
    """Get the public URL for an image."""
    return SupabaseStorageService.get_public_url(storage_path)


async def download_image(storage_path: str) -> bytes:
    """Download an image from Supabase Storage."""
    return await SupabaseStorageService.download_image(storage_path)
