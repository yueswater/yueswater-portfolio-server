import uuid
import os
import httpx
from app.config import settings


async def upload_image(file_bytes: bytes, original_filename: str, content_type: str) -> str:
    ext = os.path.splitext(original_filename)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    bucket = settings.SUPABASE_STORAGE_BUCKET
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{filename}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            content=file_bytes,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": content_type,
            },
        )
        resp.raise_for_status()

    return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"


async def delete_image(public_url: str) -> None:
    bucket = settings.SUPABASE_STORAGE_BUCKET
    prefix = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/"
    if not public_url.startswith(prefix):
        return
    filename = public_url[len(prefix):]
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}"

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            "DELETE",
            url,
            json={"prefixes": [filename]},
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
        resp.raise_for_status()
