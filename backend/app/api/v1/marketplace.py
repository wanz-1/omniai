import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.marketplace import MarketplaceItem, MarketplacePurchase
from app.models.user import User
from app.schemas.marketplace import (
    MarketplaceItemCreateRequest,
    MarketplaceItemResponse,
    MarketplaceItemUpdateRequest,
    PurchaseResponse,
)

router = APIRouter()


@router.get("/items", response_model=list[MarketplaceItemResponse])
async def list_marketplace(
    category: str | None = Query(None),
    item_type: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("downloads"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    query = select(MarketplaceItem).where(MarketplaceItem.status == "approved")

    if category:
        query = query.where(MarketplaceItem.category == category)
    if item_type:
        query = query.where(MarketplaceItem.item_type == item_type)
    if search:
        query = query.where(
            or_(
                MarketplaceItem.name.ilike(f"%{search}%"),
                MarketplaceItem.description.ilike(f"%{search}%"),
                MarketplaceItem.short_description.ilike(f"%{search}%"),
            )
        )

    if sort == "newest":
        query = query.order_by(MarketplaceItem.created_at.desc())
    elif sort == "price":
        query = query.order_by(MarketplaceItem.price.asc())
    elif sort == "rating":
        query = query.order_by(MarketplaceItem.rating.desc().nullslast())
    else:
        query = query.order_by(MarketplaceItem.downloads.desc())

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    responses = []
    for item in items:
        user_result = await db.get(User, item.author_id)
        responses.append(
            MarketplaceItemResponse(
                **{c.name: getattr(item, c.name) for c in item.__table__.columns},
                author_name=user_result.display_name if user_result else None,
            )
        )
    return responses


@router.get("/items/{item_id}", response_model=MarketplaceItemResponse)
async def get_marketplace_item(
    item_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(MarketplaceItem, item_id)
    if not item:
        raise NotFoundError("MarketplaceItem", str(item_id))

    user_result = await db.get(User, item.author_id)
    return MarketplaceItemResponse(
        **{c.name: getattr(item, c.name) for c in item.__table__.columns},
        author_name=user_result.display_name if user_result else None,
    )


@router.post("/items", response_model=MarketplaceItemResponse)
async def create_marketplace_item(
    body: MarketplaceItemCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = MarketplaceItem(
        author_id=current_user.id,
        item_type=body.item_type,
        name=body.name,
        slug=body.slug,
        description=body.description,
        short_description=body.short_description,
        category=body.category,
        tags=body.tags,
        price=body.price,
        currency=body.currency,
        preview_image_url=body.preview_image_url,
        demo_url=body.demo_url,
        source_type=body.source_type,
        source_id=uuid.UUID(body.source_id) if body.source_id else None,
        config=body.config,
    )
    db.add(item)
    await db.flush()
    return item


@router.put("/items/{item_id}", response_model=MarketplaceItemResponse)
async def update_marketplace_item(
    item_id: uuid.UUID,
    body: MarketplaceItemUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(MarketplaceItem, item_id)
    if not item:
        raise NotFoundError("MarketplaceItem", str(item_id))
    if item.author_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenError("Only the author can edit this item")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    return item


@router.post("/items/{item_id}/purchase", response_model=PurchaseResponse)
async def purchase_item(
    item_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    item = await db.get(MarketplaceItem, item_id)
    if not item:
        raise NotFoundError("MarketplaceItem", str(item_id))

    purchase = MarketplacePurchase(
        item_id=item_id,
        user_id=current_user.id,
        amount=item.price,
        currency=item.currency,
    )
    item.downloads = (item.downloads or 0) + 1
    db.add(purchase)
    await db.flush()

    return PurchaseResponse(
        id=purchase.id,
        item_id=item_id,
        item_name=item.name,
        amount=item.price,
        currency=item.currency,
        created_at=purchase.created_at,
    )


@router.get("/my-items", response_model=list[MarketplaceItemResponse])
async def my_marketplace_items(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(MarketplaceItem)
        .where(MarketplaceItem.author_id == current_user.id)
        .order_by(MarketplaceItem.created_at.desc())
    )
    items = result.scalars().all()
    return [
        MarketplaceItemResponse(
            **{c.name: getattr(item, c.name) for c in item.__table__.columns},
            author_name=current_user.display_name,
        )
        for item in items
    ]


@router.get("/my-purchases", response_model=list[PurchaseResponse])
async def my_purchases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(MarketplacePurchase)
        .where(MarketplacePurchase.user_id == current_user.id)
        .order_by(MarketplacePurchase.created_at.desc())
    )
    purchases = result.scalars().all()
    responses = []
    for p in purchases:
        item = await db.get(MarketplaceItem, p.item_id)
        responses.append(
            PurchaseResponse(
                id=p.id,
                item_id=p.item_id,
                item_name=item.name if item else None,
                amount=p.amount,
                currency=p.currency,
                created_at=p.created_at,
            )
        )
    return responses


@router.get("/categories")
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(MarketplaceItem.category, func.count(MarketplaceItem.id))
        .where(MarketplaceItem.status == "approved")
        .group_by(MarketplaceItem.category)
        .order_by(func.count(MarketplaceItem.id).desc())
    )
    return [{"category": row[0], "count": row[1]} for row in result.all()]
