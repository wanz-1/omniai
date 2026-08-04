import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = False,
    page: int = 1,
    limit: int = 20,
):
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    total = await db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == current_user.id)
    )
    return {
        "items": result.scalars().all(),
        "total": total.scalar() or 0,
        "page": page,
        "limit": limit,
    }


@router.get("/unread-count")
async def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    return {"unread_count": result.scalar() or 0}


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    notif = await db.get(Notification, notification_id)
    if not notif or notif.user_id != current_user.id:
        raise NotFoundError("Notification", str(notification_id))
    notif.is_read = True
    await db.flush()
    return {"message": "Notification marked as read"}


@router.put("/read-all")
async def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
    return {"message": "All notifications marked as read"}
