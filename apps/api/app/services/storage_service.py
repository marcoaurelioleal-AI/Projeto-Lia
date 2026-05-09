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


class LocalStorageService:
    def __init__(self, upload_dir: str = settings.upload_dir) -> None:
        self.upload_dir = Path(upload_dir)

    async def save_file(self, file: UploadFile) -> StorageResult:
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Apenas imagens JPG, PNG ou WebP sao permitidas")

        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Arquivo maior que 5MB")

        original_filename = self._safe_original_filename(file.filename or "evidencia")
        extension = ALLOWED_IMAGE_TYPES[content_type]
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

    @staticmethod
    def _safe_original_filename(filename: str) -> str:
        name = Path(filename).name.strip() or "evidencia"
        safe = re.sub(r"[^A-Za-z0-9_. -]", "_", name)
        return safe[:255] or "evidencia"
