from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.core.security import create_api_key
from app.models.api_key import ApiKey
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "created_at": k.created_at,
            "last_used_at": k.last_used_at,
            "is_active": k.is_active,
        }
        for k in keys
    ]


@router.post("")
async def create_api_key_endpoint(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    raw_key, hashed_key = create_api_key()
    api_key = ApiKey(
        user_id=current_user.id,
        name=name,
        key_prefix=raw_key[:12],
        key_hash=hashed_key,
    )
    db.add(api_key)
    await db.flush()
    return {"id": api_key.id, "name": api_key.name, "key": raw_key}


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise NotFoundError("API Key", key_id)
    await db.delete(api_key)
    await db.flush()
    return {"message": "API key deleted"}


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise NotFoundError("API Key", key_id)
    api_key.is_active = False
    await db.flush()
    return {"message": "API key revoked"}
