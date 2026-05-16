from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from ..config import settings

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class StorageResult:
    storage_provider: str
    file_path: str
    original_filename: str
    content_type: str
    file_size: int


async def read_and_validate_upload(file: UploadFile) -> tuple[bytes, str, str, str]:
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Apenas imagens JPG, PNG ou WebP sao permitidas")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo maior que 5MB")

    original_filename = safe_original_filename(file.filename or "evidencia")
    extension = ALLOWED_IMAGE_TYPES[content_type]
    return data, content_type, original_filename, extension


def safe_original_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "evidencia"
    safe = re.sub(r"[^A-Za-z0-9_. -]", "_", name)
    return safe[:255] or "evidencia"


class LocalStorageService:
    def __init__(self, upload_dir: str = settings.upload_dir) -> None:
        self.upload_dir = Path(upload_dir)

    async def save_file(self, file: UploadFile) -> StorageResult:
        data, content_type, original_filename, extension = await read_and_validate_upload(file)

        stored_name = f"{uuid4().hex}{extension}"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        target = self.upload_dir / stored_name
        target.write_bytes(data)

        return StorageResult(
            storage_provider="local",
            file_path=str(target),
            original_filename=original_filename,
            content_type=content_type,
            file_size=len(data),
        )


class SupabaseStorageService:
    def __init__(
        self,
        url: str | None = settings.supabase_url,
        service_role_key: str | None = settings.supabase_service_role_key,
        bucket: str | None = settings.supabase_storage_bucket,
    ) -> None:
        if not url or not service_role_key or not bucket:
            raise RuntimeError("Supabase Storage requer SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e SUPABASE_STORAGE_BUCKET")
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Dependencia supabase ausente. Instale o pacote supabase.") from exc

        self.client = create_client(url, service_role_key)
        self.bucket = bucket

    async def save_file(self, file: UploadFile) -> StorageResult:
        data, content_type, original_filename, extension = await read_and_validate_upload(file)
        object_path = f"checklist-evidences/{uuid4().hex}{extension}"
        self.client.storage.from_(self.bucket).upload(
            object_path,
            data,
            {"content-type": content_type},
        )
        return StorageResult(
            storage_provider="supabase",
            file_path=object_path,
            original_filename=original_filename,
            content_type=content_type,
            file_size=len(data),
        )

    def create_signed_url(self, object_path: str) -> str:
        response = self.client.storage.from_(self.bucket).create_signed_url(
            object_path,
            settings.supabase_signed_url_expires_seconds,
        )
        if isinstance(response, dict):
            url = response.get("signedURL") or response.get("signedUrl") or response.get("signed_url")
        else:
            url = getattr(response, "signed_url", None) or getattr(response, "signedURL", None)
        if not url:
            raise HTTPException(status_code=404, detail="Nao foi possivel gerar URL assinada da evidencia")
        return str(url)


def get_storage_service() -> LocalStorageService | SupabaseStorageService:
    if settings.storage_provider == "supabase":
        return SupabaseStorageService()
    return LocalStorageService()
