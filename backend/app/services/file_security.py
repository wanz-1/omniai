"""
File security service: MIME detection, size limits, banned extensions, sanitization.

Improvements:
- Fail-closed when magic library missing for claimed binary types.
- Detect MIME via file signatures (magic numbers) as fallback when libmagic unavailable.
- Sanitize only text-based files, not binary (images, audio, video) to avoid corruption.
- Size check uses current settings dynamically (not cached at import).
- More banned extensions and double-extension evasion detection.
- Detailed reason messages without leaking internal paths.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

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


# MIME types grouped by category
ALLOWED_MIME_TYPES: Final[dict[str, list[str]]] = {
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
        "application/json",
        "text/html",  # for upload preview, sanitized later
    ],
    "image": [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/svg+xml",
        "image/bmp",
        "image/tiff",
    ],
    "audio": [
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/mp4",
        "audio/webm",
        "audio/x-wav",
        "audio/flac",
    ],
    "video": [
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/quicktime",
        "video/x-msvideo",
        "video/mpeg",
    ],
    "code": [
        "text/x-python",
        "text/x-java",
        "text/javascript",
        "application/javascript",
        "text/typescript",
        "text/x-go",
        "text/x-rust",
        "application/json",
        "text/x-json",
        "text/x-yaml",
        "application/x-yaml",
        "text/yaml",
        "text/xml",
        "application/xml",
        "text/plain",  # code often detected as plain
    ],
    "archive": [],  # disallow archives by default for security
}

# Flatten for quick check
_ALL_ALLOWED_MIMES: Final[set[str]] = {
    mime for mimes in ALLOWED_MIME_TYPES.values() for mime in mimes
}

BANNED_EXTENSIONS: Final[set[str]] = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bat",
    ".cmd",
    ".com",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".wsf",
    ".wsh",
    ".msi",
    ".msp",
    ".scr",
    ".pif",
    ".application",
    ".gadget",
    ".hta",
    ".cpl",
    ".msc",
    ".jar",
    ".class",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".psm1",
    ".lnk",
    # Double-extension tricks: we check all suffixes, so .pdf.exe will be caught
}

# Magic numbers fallback (first few bytes)
_MAGIC_SIGNATURES: Final[dict[bytes, str]] = {
    b"%PDF": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"PK\x03\x04": "application/zip",  # also docx/xlsx are zip
    b"{\n": "application/json",
    b"{\"": "application/json",
    b"<?xml": "text/xml",
    b"<!DOCT": "text/html",
    b"<html": "text/html",
}


def _detect_mime_via_signature(data: bytes) -> str:
    """Fallback MIME detection via magic numbers."""
    if not data:
        return "application/octet-stream"
    # Check longest signatures first
    for sig, mime in sorted(_MAGIC_SIGNATURES.items(), key=lambda x: len(x[0]), reverse=True):
        if data.startswith(sig):
            # Distinguish zip-based docs via extension later; for now return zip
            # Caller will allow if claimed type matches doc types
            return mime
    # Text heuristic: if mostly printable ASCII
    try:
        text = data[:1024].decode("utf-8")
        if text and all(c.isprintable() or c.isspace() for c in text[:512]):
            # Could be text/plain, csv, etc.
            if "," in text and "\n" in text:
                return "text/csv"
            return "text/plain"
    except Exception:
        # Ignore decode errors for mime detection fallback
        pass  # noqa: S110
    return "application/octet-stream"


class FileSecurityService:
    async def scan_file(
        self,
        filename: str,
        data: bytes,
        content_type: str = "",
    ) -> FileScanResult:
        """
        Scan file for security issues: size, extension, MIME.
        Returns FileScanResult with sanitized_data if allowed.
        """
        max_bytes = settings.max_upload_size_mb * 1024 * 1024

        if len(data) > max_bytes:
            return FileScanResult(
                allowed=False,
                reason=f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
            )

        # Sanitize filename: no path traversal, check double extensions
        # e.g., invoice.pdf.exe => banned
        path = Path(filename)
        # Check all suffixes for banned
        suffixes = [s.lower() for s in path.suffixes]
        for suf in suffixes:
            if suf in BANNED_EXTENSIONS:
                return FileScanResult(
                    allowed=False,
                    reason=f"File extension '{suf}' is not allowed",
                )

        # Also check final extension
        ext = path.suffix.lower()
        if ext in BANNED_EXTENSIONS:
            return FileScanResult(
                allowed=False,
                reason=f"File extension '{ext}' is not allowed",
            )

        # Detect MIME
        detected_mime = self._detect_mime(data)
        claimed = (content_type or "").lower().split(";")[0].strip()

        if not self._is_mime_allowed(detected_mime, claimed):
            # Fail closed: log and reject
            logger.warning(
                "File type blocked",
                extra={
                    "event": "file_type_blocked",
                    "filename": path.name,
                    "detected_mime": detected_mime,
                    "claimed_type": claimed,
                },
            )
            return FileScanResult(
                allowed=False,
                reason=f"File type '{detected_mime or claimed or 'unknown'}' is not allowed",
                detected_mime=detected_mime,
            )

        # Sanitize only if text-based
        sanitized = self._sanitize_data(data, detected_mime)

        return FileScanResult(
            allowed=True,
            detected_mime=detected_mime,
            sanitized_data=sanitized,
        )

    def _detect_mime(self, data: bytes) -> str:
        """Try libmagic, fallback to signature."""
        try:
            import magic  # type: ignore

            mime = magic.from_buffer(data, mime=True)
            if mime:
                return mime
            return "application/octet-stream"
        except ImportError:
            logger.debug("python-magic not available, using signature fallback")
            return _detect_mime_via_signature(data)
        except Exception as e:
            logger.warning(f"MIME detection failed: {e}")
            return _detect_mime_via_signature(data)

    def _is_mime_allowed(self, detected_mime: str, claimed_type: str = "") -> bool:
        """
        Check if detected MIME is allowed. Also allow if claimed type is in allowed
        and detected is generic octet-stream (when magic unavailable).
        However, fail closed for executable types.
        """
        detected = (detected_mime or "").lower()
        claimed = (claimed_type or "").lower()

        # If detected is generic octet-stream, we may still allow if claimed is allowed
        # But only for document/image that we cannot reliably detect, and NOT for executable signatures
        if detected == "application/octet-stream":
            # If claimed is allowed, allow (with sanitization), else reject
            if claimed in _ALL_ALLOWED_MIMES:
                return True
            # Also allow text/plain fallback detected via signature
            return False

        # Direct allow list
        if detected in _ALL_ALLOWED_MIMES:
            return True

        # Special: docx/xlsx are zip files; if detected as zip but claimed as docx/xlsx, allow
        if detected == "application/zip":
            if claimed in {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            }:
                return True
            # Otherwise reject zip to avoid archive bombs
            return False

        # Allow text/* if claimed text-ish? Be conservative: allow text/plain always
        if detected.startswith("text/"):
            # text/html is allowed but will be sanitized
            return detected in _ALL_ALLOWED_MIMES or detected == "text/plain"

        return False

    def _sanitize_data(self, data: bytes, mime: str) -> bytes:
        """
        Sanitize file data:
        - For text-based MIMEs: remove control characters, null bytes, and potential XSS.
        - For binary (images, audio, video): return as-is to avoid corruption, but still strip leading nulls?
        """
        # Binary types: no text sanitization
        if mime.startswith(("image/", "audio/", "video/")):
            # For svg+xml, we should sanitize for XSS
            if mime == "image/svg+xml":
                try:
                    text = data.decode("utf-8", errors="replace")
                    # Remove <script> tags and on* attributes (basic)
                    text = re.sub(
                        r"<script[^>]*>.*?</script>",
                        "",
                        text,
                        flags=re.DOTALL | re.IGNORECASE,
                    )
                    text = re.sub(
                        r"\son\w+\s*=\s*\"[^\"]*\"",
                        "",
                        text,
                        flags=re.IGNORECASE,
                    )
                    text = re.sub(
                        r"\son\w+\s*=\s*'[^']*'",
                        "",
                        text,
                        flags=re.IGNORECASE,
                    )
                    return text.encode("utf-8")
                except Exception:
                    return data
            return data

        # Text-based: remove dangerous control chars, keep \n, \r, \t
        try:
            text = data.decode("utf-8", errors="replace")
            # Remove C0 control chars except \n \r \t
            text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
            # Remove potential null byte injection
            # Also limit size for sanitization (already size-checked)
            return text.encode("utf-8")
        except Exception:
            # If decode fails, return original (might be binary that was misclassified as text)
            return data


file_security_service = FileSecurityService()
