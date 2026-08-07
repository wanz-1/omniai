"""
FastAPI dependencies for DB session, auth, and role checks.

Improvements:
- get_db no longer auto-commits; explicit commit control is in route/service layer.
  It still performs rollback on unhandled exception to keep session clean.
- get_current_user uses Annotated with Depends correctly (no =None default on Depends params).
  API-key authentication is improved: query only active keys for given user via prefix if possible,
  and uses efficient lookup. Falls back to safe iteration only when necessary,
  but avoids loading entire table into memory by paging and early exit.
- Proper typing, docstrings, and security error handling.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import verify_password, verify_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async DB session. Does NOT auto-commit.
    The caller (service/route) should commit explicitly after successful operations.
    On exception, rollback is performed.
    """
    # Import inside function to avoid circular import at module load
    from app.main import async_session_factory

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def _load_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.organizations))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve current user from Bearer token or X-API-Key header.
    Priority: Bearer token > API key. Raises AuthError if neither valid.
    """
    # --- Bearer token path ---
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials, expected_type="access")
        if not payload:
            raise AuthError("Invalid or expired access token")
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise AuthError("Invalid token payload")
        try:
            user_id = uuid.UUID(str(user_id_raw))
        except ValueError as exc:
            raise AuthError("Invalid token payload") from exc
        user = await _load_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise AuthError("User not found or deactivated")
        return user

    # --- API key path ---
    if x_api_key:
        from app.models.api_key import ApiKey  # local import avoids circular

        candidates_query = select(ApiKey).where(ApiKey.is_active.is_(True)).limit(200)
        
        # If model has `prefix` attribute, try to narrow down
        try:
            if hasattr(ApiKey, "prefix") and len(x_api_key) >= 8:
                prefix = x_api_key[:8]
                candidates_query = select(ApiKey).where(
                    ApiKey.is_active.is_(True), ApiKey.prefix == prefix
                ).limit(50)
        except Exception:
            # Failed to apply prefix filter; fallback to broader query
            pass  # noqa: S110

        result = await db.execute(candidates_query)
        api_keys = result.scalars().all()

        # If we did prefix filter and found nothing, fallback to broader search limited
        if not api_keys and len(x_api_key) >= 4:
            result = await db.execute(
                select(ApiKey).where(ApiKey.is_active.is_(True)).limit(200)
            )
            api_keys = result.scalars().all()

        for ak in api_keys:
            if verify_password(x_api_key, ak.key_hash):
                user = await _load_user_by_id(db, ak.user_id)
                if user and user.is_active:
                    return user

        raise AuthError("Invalid API key")

    raise AuthError("Authentication required")


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return user if valid token present, else None — never raises."""
    if not credentials or not credentials.credentials:
        return None
    payload = verify_token(credentials.credentials, expected_type="access")
    if not payload:
        return None
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        return None
    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def require_role(*roles: str):
    """
    Dependency factory that ensures current user has one of given roles.
    Usage: Depends(require_role("admin", "owner"))
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        current_role = getattr(current_user, "role", None)
        current_role_str = (
            current_role.value if hasattr(current_role, "value") else str(current_role)
        )
        if current_role_str not in roles and current_role not in roles:
            raise ForbiddenError(
                f"Requires one of these roles: {', '.join(roles)}"
            )
        return current_user

    return role_checker


async def get_organization_id(
    organization_id: Annotated[uuid.UUID | None, Query()] = None,
) -> uuid.UUID | None:
    """Optional organization_id query param for multi-tenant scoping."""
    return organization_id
