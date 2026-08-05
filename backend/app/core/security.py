import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import pyotp
from jose import JWTError, jwt

from app.core.config import settings


def hash_token(token: str) -> str:
    """Return a one-way SHA-256 hash of a token for at-rest session storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _get_jwt_secret(key_version: int | None = None) -> str:
    if key_version and key_version > 1:
        idx = key_version - 2
        if idx < len(settings.jwt_secret_previous):
            return settings.jwt_secret_previous[idx]
    return settings.jwt_secret if settings.jwt_secret else ""


def create_access_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
    key_version: int | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "kid": key_version or settings.jwt_key_version,
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    secret = _get_jwt_secret(key_version)
    return jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    secrets_to_try = [settings.jwt_secret, *settings.jwt_secret_previous]
    for secret in secrets_to_try:
        if not secret:
            continue
        try:
            payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            continue
    return {}


def verify_token(token: str, expected_type: str = "access") -> Optional[dict[str, Any]]:
    payload = decode_token(token)
    if not payload or payload.get("type") != expected_type:
        return None
    return payload


def rotate_refresh_token(old_refresh_token: str) -> tuple[Optional[str], Optional[str]]:
    payload = verify_token(old_refresh_token, expected_type="refresh")
    if not payload:
        return None, None
    subject = payload.get("sub")
    if not subject:
        return None, None
    new_access = create_access_token(subject=subject)
    new_refresh = create_refresh_token(subject=subject)
    return new_access, new_refresh


def generate_2fa_secret() -> str:
    return pyotp.random_base32()


def get_2fa_otp_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.mfa_issuer_name)


def verify_2fa_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_recovery_codes(count: int = 8) -> list[str]:
    return [uuid.uuid4().hex[:12] for _ in range(count)]


def verify_recovery_code(code: str, stored_codes: list[str]) -> tuple[bool, list[str]]:
    remaining = [c for c in stored_codes if c != code]
    was_valid = len(remaining) < len(stored_codes)
    return was_valid, remaining


def create_api_key() -> tuple[str, str]:
    key = f"om_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    hashed = hash_password(key)
    return key, hashed
