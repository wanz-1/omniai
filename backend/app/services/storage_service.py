"""Simple storage service for media assets."""

import uuid
from pathlib import Path

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.base_path = Path(settings.UPLOAD_DIR) if hasattr(settings, "UPLOAD_DIR") else Path("uploads")
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, key: str, data: bytes) -> str:
        file_path = self.base_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return str(file_path)

    async def save_audio(self, data: bytes, filename: str) -> str:
        key = f"audio/{filename}"
        return await self.save_file(key, data)

    async def save_image(self, data: bytes, filename: str) -> str:
        key = f"images/{filename}"
        return await self.save_file(key, data)

    async def read_file(self, key: str) -> bytes | None:
        file_path = self.base_path / key
        if file_path.exists():
            return file_path.read_bytes()
        return None

    async def delete_file(self, key: str) -> bool:
        file_path = self.base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_url(self, key: str) -> str:
        return f"/uploads/{key}"
