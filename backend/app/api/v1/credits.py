from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.credit import CreditTransaction
from app.models.user import User

router = APIRouter()


@router.get("/balance")
async def get_balance(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return {"balance": current_user.credits_balance}


@router.get("/transactions")
async def get_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    total = await db.execute(
        select(func.count(CreditTransaction.id))
        .where(CreditTransaction.user_id == current_user.id)
    )
    return {
        "items": result.scalars().all(),
        "total": total.scalar() or 0,
        "page": page,
        "limit": limit,
    }
