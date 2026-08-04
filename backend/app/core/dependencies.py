import uuid
from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import verify_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    from app.main import async_session_factory
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    x_api_key: Annotated[Optional[str], Header()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> User:
    if credentials:
        payload = verify_token(credentials.credentials, expected_type="access")
        if not payload:
            raise AuthError("Invalid or expired access token")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid token payload")
        result = await db.execute(
            select(User)
            .options(selectinload(User.organizations))
            .where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthError("User not found or deactivated")
        return user

    if x_api_key:
        from app.models.api_key import ApiKey
        from app.core.security import verify_password
        result = await db.execute(select(ApiKey).where(ApiKey.is_active == True))
        api_keys = result.scalars().all()
        for ak in api_keys:
            if verify_password(x_api_key, ak.key_hash):
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.organizations))
                    .where(User.id == ak.user_id)
                )
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    return user
        raise AuthError("Invalid API key")

    raise AuthError("Authentication required")


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials, expected_type="access")
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    return result.scalar_one_or_none()


def require_role(*roles: str):
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(f"Requires one of these roles: {', '.join(roles)}")
        return current_user
    return role_checker


async def get_organization_id(
    organization_id: Annotated[Optional[uuid.UUID], Query()] = None,
) -> Optional[uuid.UUID]:
    return organization_id
