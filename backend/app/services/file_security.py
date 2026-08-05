import logging
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("omniai.file_security")


@dataclass
class FileScanResult:
    allowed: bool
    reason: str = ""
    detected_mime: str = ""
    sanitized_data: bytes | None = None

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "detected_mime": self.detected_mime,
        }


ALLOWED_MIME_TYPES: dict[str, list[str]] = {
    "document": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/rtf",
    ],
    "image": [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/svg+xml",
        "image/bmp",
    ],
    "audio": [
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/mp4",
        "audio/webm",
    ],
    "video": [
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/quicktime",
    ],
    "code": [
        "text/x-python",
        "text/x-java",
        "text/javascript",
        "text/typescript",
        "text/x-go",
        "text/x-rust",
        "text/x-json",
        "text/x-yaml",
        "text/xml",
    ],
}

BANNED_EXTENSIONS: set[str] = {
    ".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".com",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh", ".msi",
    ".msp", ".scr", ".pif", ".application", ".gadget",
    ".hta", ".cpl", ".msc", ".jar", ".class",
}

MAX_FILE_SIZE_MB = settings.max_upload_size_mb
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class FileSecurityService:
    async def scan_file(
        self,
        filename: str,
        data: bytes,
        content_type: str = "",
    ) -> FileScanResult:
        if len(data) > MAX_FILE_SIZE_BYTES:
            return FileScanResult(
                allowed=False,
                reason=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB",
            )

        ext = Path(filename).suffix.lower()
        if ext in BANNED_EXTENSIONS:
            return FileScanResult(
                allowed=False,
                reason=f"File extension '{ext}' is not allowed",
            )

        detected_mime = self._detect_mime(data)
        if not self._is_mime_allowed(detected_mime, content_type):
            return FileScanResult(
                allowed=False,
                reason=f"File type '{detected_mime}' is not allowed",
                detected_mime=detected_mime,
            )

        sanitized = self._sanitize_data(data)

        return FileScanResult(
            allowed=True,
            detected_mime=detected_mime,
            sanitized_data=sanitized,
        )

    def _detect_mime(self, data: bytes) -> str:
        try:
            import magic
            mime = magic.from_buffer(data, mime=True)
            return mime or "application/octet-stream"
        except (ImportError, Exception):
            return "application/octet-stream"

    def _is_mime_allowed(self, detected_mime: str, claimed_type: str = "") -> bool:
        for category, mimes in ALLOWED_MIME_TYPES.items():
            if detected_mime in mimes:
                return True
        return False

    def _sanitize_data(self, data: bytes) -> bytes:
        try:
            import re
            text = data.decode("utf-8", errors="replace")
            text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
            return text.encode("utf-8")
        except Exception:
            return data


file_security_service = FileSecurityService()
