import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.integration import IntegrationConnection
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/connections")
async def list_connections(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.user_id == current_user.id
        )
    )
    return result.scalars().all()


@router.delete("/connections/{connection_id}", response_model=MessageResponse)
async def delete_connection(
    connection_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conn = await db.get(IntegrationConnection, connection_id)
    if not conn:
        raise NotFoundError("IntegrationConnection", str(connection_id))
    await db.delete(conn)
    return MessageResponse(message="Integration connection removed")
