import base64
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger("omniai.data_protection")

SENSITIVE_PATTERNS: dict[str, str] = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\+?1?\d{10,15}",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "api_key": r"(?:sk-[a-zA-Z0-9]{32,}|pk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36,})",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "slack_token": r"xox[bpsa]-[0-9A-Za-z-]{10,}",
    "private_key": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
    "jwt": r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
    "stripe_key": r"(?:sk_live|sk_test|pk_live|pk_test)_[a-zA-Z0-9]+",
}


@dataclass
class ScanResult:
    has_sensitive_data: bool
    patterns_found: dict[str, int] = field(default_factory=dict)
    redacted_text: str = ""


class DataProtectionService:
    def __init__(self) -> None:
        self._fernet: Fernet | None = None

    def _get_cipher(self) -> Fernet:
        if self._fernet is None:
            key = settings.jwt_secret.encode("utf-8")
            key = key.ljust(32, b"\0")[:32]
            self._fernet = Fernet(base64.urlsafe_b64encode(key))
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        cipher = self._get_cipher()
        return cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        cipher = self._get_cipher()
        return cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    def scan_for_sensitive_data(self, text: str) -> ScanResult:
        patterns_found: dict[str, int] = {}
        redacted = text

        for name, pattern in SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, redacted, re.IGNORECASE)
            if matches:
                patterns_found[name] = len(matches)
                redacted = re.sub(pattern, f"[REDACTED_{name.upper()}]", redacted, flags=re.IGNORECASE)

        return ScanResult(
            has_sensitive_data=len(patterns_found) > 0,
            patterns_found=patterns_found,
            redacted_text=redacted,
        )

    async def validate_for_logging(self, text: str) -> str:
        result = self.scan_for_sensitive_data(text)
        if result.has_sensitive_data:
            logger.warning(
                "Sensitive data detected and redacted from log",
                extra={"patterns": list(result.patterns_found.keys())},
            )
        return result.redacted_text

    async def validate_for_ai(self, text: str) -> tuple[str, list[str]]:
        result = self.scan_for_sensitive_data(text)
        warnings: list[str] = []
        if result.has_sensitive_data:
            warnings = [f"Redacted {count} {name}(s)" for name, count in result.patterns_found.items()]
            logger.info(
                "Sensitive data redacted before AI processing",
                extra={"patterns": list(result.patterns_found.keys())},
            )
        return result.redacted_text, warnings

    def mask_email(self, email: str) -> str:
        at_index = email.find("@")
        if at_index < 2:
            return email
        return email[0] + "****" + email[at_index - 1 :]

    def mask_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 6:
            return phone
        return digits[:2] + "****" + digits[-4:]


data_protection = DataProtectionService()
