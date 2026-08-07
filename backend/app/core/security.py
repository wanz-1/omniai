"""
Security utilities: password hashing, JWT handling, 2FA helpers, API-key generation.

Improvements over initial version:
- Uses UTC alias and explicit typing.
- Enforces non-empty JWT secret at call time (defense in depth beyond config validator).
- decode_token returns an empty dict only when no secret works, but verify_token handles it safely.
- Constant-time recovery-code comparison where feasible.
- Clear docstrings and error handling.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import pyotp
from jose import JWTError, jwt

from app.core.config import settings


def hash_token(token: str) -> str:
    """Return a one-way SHA-256 hex digest for at-rest session storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """
    Hash a password with bcrypt.
    Generates a salt automatically. Returns UTF-8 string.
    """
    if not password:
        raise ValueError("Password must not be empty")
    # bcrypt has 72-byte limit; truncate safely (common practice) or raise
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash, handling encoding safely."""
    try:
        if not plain_password or not hashed_password:
            return False
        pw_bytes = plain_password.encode("utf-8")
        if len(pw_bytes) > 72:
            pw_bytes = pw_bytes[:72]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        # Any bcrypt error -> fail closed
        return False


def _get_jwt_secret(key_version: int | None = None) -> str:
    """
    Resolve JWT secret by key version. Supports key rotation via jwt_secret_previous list.
    key_version=1 is current, 2 is previous[0], etc.
    """
    if key_version and key_version > 1:
        idx = key_version - 2
        if 0 <= idx < len(settings.jwt_secret_previous):
            candidate = settings.jwt_secret_previous[idx]
            if candidate:
                return candidate
    secret = settings.jwt_secret
    if not secret:
        raise RuntimeError(
            "JWT secret is not configured. Set JWT_SECRET environment variable. "
            "Refusing to sign tokens with empty secret."
        )
    return secret


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
    key_version: int | None = None,
) -> str:
    """
    Create a signed access token. Includes jti (token id), kid (key version), sub, exp, type.
    """
    if not subject:
        raise ValueError("subject must not be empty")
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta
    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "kid": key_version or settings.jwt_key_version,
        "jti": uuid.uuid4().hex,
        "iat": datetime.now(UTC),
    }
    if extra_claims:
        # Avoid overriding reserved claims
        for k in ("sub", "exp", "type", "kid", "jti", "iat"):
            extra_claims.pop(k, None)
        to_encode.update(extra_claims)
    secret = _get_jwt_secret(key_version)
    return jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a refresh token. Only current key is used to sign refresh tokens.
    Rotation can be added later if needed.
    """
    if not subject:
        raise ValueError("subject must not be empty")
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": datetime.now(UTC),
    }
    if extra_claims:
        for k in ("sub", "exp", "type", "jti", "iat"):
            extra_claims.pop(k, None)
        to_encode.update(extra_claims)
    secret = _get_jwt_secret()
    return jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Try to decode token with current and previous secrets.
    Returns payload dict if valid, empty dict if all secrets fail or token invalid.
    This function intentionally does NOT raise to keep callers simple;
    use verify_token if you need strict validation.
    """
    if not token:
        return {}
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


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any] | None:
    """
    Verify token signature and check type claim. Returns payload or None.
    """
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("type") != expected_type:
        return None
    # Additional sanity: sub must exist
    if not payload.get("sub"):
        return None
    return payload


def rotate_refresh_token(old_refresh_token: str) -> tuple[str | None, str | None]:
    """
    Validate old refresh token and issue new access+refresh pair.
    Returns (new_access, new_refresh) or (None, None) if invalid.
    Note: DB-layer revocation should still be performed by caller.
    """
    payload = verify_token(old_refresh_token, expected_type="refresh")
    if not payload:
        return None, None
    subject = payload.get("sub")
    if not subject:
        return None, None
    new_access = create_access_token(subject=subject)
    new_refresh = create_refresh_token(subject=subject)
    return new_access, new_refresh


# ---- 2FA ----

def generate_2fa_secret() -> str:
    """Generate a random base32 TOTP secret."""
    return pyotp.random_base32()


def get_2fa_otp_uri(secret: str, email: str) -> str:
    """Get provisioning URI for authenticator apps."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email, issuer_name=settings.mfa_issuer_name
    )


def verify_2fa_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify TOTP code, allowing small clock drift (valid_window).
    """
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code.strip(), valid_window=valid_window)
    except Exception:
        return False


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate cryptographically strong recovery codes."""
    return [secrets.token_hex(6) for _ in range(count)]  # 12 hex chars


def verify_recovery_code(code: str, stored_codes: list[str]) -> tuple[bool, list[str]]:
    """
    Constant-time-ish verification of recovery code.
    Removes used code from list. Returns (was_valid, remaining_codes).
    """
    if not code or not stored_codes:
        return False, stored_codes

    # Use hmac.compare_digest for constant-time comparison
    remaining: list[str] = []
    found = False
    for stored in stored_codes:
        if not found and hmac.compare_digest(stored, code):
            found = True
            continue
        remaining.append(stored)
    return found, remaining


# ---- API Keys ----

def create_api_key() -> tuple[str, str]:
    """
    Generate a new API key and its bcrypt hash.
    Format: om_<32hex><32hex> (66 chars + prefix = ~70). Uses secrets for entropy.
    Returns (plaintext_key, hashed_key_for_storage).
    """
    # 32 bytes hex entropy twice = 64 chars plus prefix
    key = f"om_{secrets.token_hex(32)}{secrets.token_hex(16)}"
    hashed = hash_password(key)
    return key, hashed


def get_api_key_prefix(key: str, length: int = 8) -> str:
    """Return prefix for indexing / display (safe to log)."""
    if not key:
        return ""
    return key[:length]

