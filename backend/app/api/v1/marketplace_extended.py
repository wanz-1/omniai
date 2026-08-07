"""
Marketplace Extended API - products, reviews, creator dashboard, plugins, verification, enterprise, SDK.

Improved from compact style to explicit, readable functions with proper error handling.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.marketplace import MarketplaceItem
from app.models.marketplace_extended import (
    CreatorProfile,
    EnterpriseListing,
)
from app.models.user import User
from app.schemas.marketplace_extended import (
    CreatorDashboardResponse,
    CreatorProfileResponse,
    EnterpriseListingCreate,
    PluginDefinitionResponse,
    PluginInstallResponse,
    ProductCategoryResponse,
    ProductReviewCreate,
    ProductReviewResponse,
    ProductVersionResponse,
    PublishRequest,
    SDKGenerateRequest,
    VerificationResponse,
)
from app.services.marketplace_creator import MarketplaceCreatorService
from app.services.marketplace_plugin import MarketplacePluginService
from app.services.marketplace_product import MarketplaceProductService
from app.services.marketplace_review import MarketplaceReviewService
from app.services.marketplace_sdk import MarketplaceSDKService
from app.services.marketplace_verification import MarketplaceVerificationService

router = APIRouter()


# ─── Categories ──────────────────────────────────────────────────────────────


@router.post("/categories", response_model=ProductCategoryResponse)
async def create_category(
    name: str,
    slug: str,
    description: str | None = None,
    icon: str | None = None,
    parent_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    return await svc.create_category(name, slug, description, icon, parent_id)


@router.get("/categories", response_model=list[ProductCategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    svc = MarketplaceProductService(db)
    return await svc.list_categories()


# ─── Products ────────────────────────────────────────────────────────────────


@router.post("/products")
async def publish_product(
    req: PublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    item = await svc.publish_product(current_user.id, req.model_dump())
    return {"id": str(item.id), "name": item.name, "slug": item.slug, "status": item.status}


@router.get("/products")
async def list_products(
    category: str | None = None,
    item_type: str | None = None,
    search: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    return await svc.list_products(category, item_type, search, limit)


@router.get("/products/{product_id}")
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = MarketplaceProductService(db)
    item = await svc.get_product(product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


@router.post("/products/{product_id}/purchase")
async def purchase_product(
    product_id: uuid.UUID,
    organization_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    purchase = await svc.purchase_product(product_id, current_user.id, organization_id)
    return {"id": str(purchase.id), "amount": purchase.amount, "status": "completed"}


@router.get("/products/{product_id}/versions", response_model=list[ProductVersionResponse])
async def get_product_versions(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = MarketplaceProductService(db)
    return await svc.get_product_versions(product_id)


@router.post("/products/{product_id}/versions")
async def create_product_version(
    product_id: uuid.UUID,
    version: str,
    changelog: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    return await svc.create_version(product_id, version, changelog)


# ─── Reviews ─────────────────────────────────────────────────────────────────


@router.post("/reviews", response_model=ProductReviewResponse)
async def create_review(
    req: ProductReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceReviewService(db)
    return await svc.create_review(
        req.product_id, current_user.id, req.rating, req.title, req.content, req.pros, req.cons
    )


@router.get("/reviews/{product_id}", response_model=list[ProductReviewResponse])
async def get_product_reviews(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = MarketplaceReviewService(db)
    return await svc.get_product_reviews(product_id)


# ─── Creator ─────────────────────────────────────────────────────────────────


@router.get("/creator/profile", response_model=CreatorProfileResponse)
async def get_creator_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceCreatorService(db)
    display_name = getattr(current_user, "full_name", None) or current_user.email
    return await svc.get_or_create_profile(current_user.id, display_name)


@router.put("/creator/profile", response_model=CreatorProfileResponse)
async def update_creator_profile(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceCreatorService(db)
    return await svc.update_profile(current_user.id, **data)


@router.get("/creator/dashboard", response_model=CreatorDashboardResponse)
async def get_creator_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceCreatorService(db)
    return await svc.get_dashboard(current_user.id)


@router.get("/creator/analytics/{product_id}")
async def get_product_analytics(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceCreatorService(db)
    return await svc.get_analytics(product_id)


# ─── Plugins ─────────────────────────────────────────────────────────────────


@router.post("/plugins", response_model=PluginDefinitionResponse)
async def register_plugin(
    name: str,
    slug: str,
    plugin_type: str,
    description: str | None = None,
    entry_point: str | None = None,
    source_url: str | None = None,
    docs_url: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplacePluginService(db)
    return await svc.register_plugin(
        name, slug, plugin_type, current_user.id, description, entry_point, None, None, source_url, docs_url
    )


@router.get("/plugins", response_model=list[PluginDefinitionResponse])
async def list_plugins(plugin_type: str | None = None, db: AsyncSession = Depends(get_db)):
    svc = MarketplacePluginService(db)
    return await svc.list_plugins(plugin_type)


@router.post("/plugins/{plugin_id}/install", response_model=PluginInstallResponse)
async def install_plugin(
    plugin_id: uuid.UUID,
    organization_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplacePluginService(db)
    return await svc.install_plugin(plugin_id, current_user.id, organization_id)


@router.delete("/plugins/install/{installation_id}")
async def uninstall_plugin(
    installation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplacePluginService(db)
    await svc.uninstall_plugin(installation_id)
    return {"message": "Uninstalled"}


@router.get("/plugins/installed")
async def get_installed_plugins(
    organization_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplacePluginService(db)
    if organization_id:
        return await svc.get_org_plugins(organization_id)
    return await svc.get_user_plugins(current_user.id)


# ─── Verification ────────────────────────────────────────────────────────────


@router.post("/verify/{product_id}", response_model=VerificationResponse)
async def verify_product(
    product_id: uuid.UUID,
    level: str = "community",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceVerificationService(db)
    return await svc.verify_product(product_id, level, current_user.id)


@router.get("/verify/{product_id}/history", response_model=list[VerificationResponse])
async def get_verification_history(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = MarketplaceVerificationService(db)
    return await svc.get_verification_history(product_id)


# ─── Enterprise Listings ─────────────────────────────────────────────────────


@router.post("/enterprise")
async def create_enterprise_listing(
    req: EnterpriseListingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = EnterpriseListing(
        product_id=req.product_id,
        is_private=req.is_private,
        allowed_orgs=[str(o) for o in (req.allowed_orgs or [])],
        license_type=req.license_type,
        custom_price=req.custom_price,
        support_level=req.support_level,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return {
        "id": str(listing.id),
        "product_id": str(listing.product_id),
        "is_private": listing.is_private,
    }


@router.get("/enterprise/{product_id}")
async def get_enterprise_listing(
    product_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = MarketplaceProductService(db)
    listing = await svc.get_enterprise_listing(product_id, organization_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Enterprise listing not found")
    return listing


# ─── SDK Generation ──────────────────────────────────────────────────────────


@router.post("/sdk")
async def generate_sdk(
    req: SDKGenerateRequest,
    current_user: User | None = Depends(get_current_user),
):
    svc = MarketplaceSDKService()
    return await svc.generate_sdk(req.language, req.features)


@router.get("/sdk/{language}")
async def get_sdk_template(language: str = "python"):
    svc = MarketplaceSDKService()
    return await svc.get_sdk_template(language)


# ─── My Products (Creator) ───────────────────────────────────────────────────


@router.get("/my-products")
async def get_my_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MarketplaceItem)
        .where(MarketplaceItem.author_id == current_user.id)
        .order_by(MarketplaceItem.created_at.desc())
    )
    return list(result.scalars().all())


# ─── Dashboard ───────────────────────────────────────────────────────────────


@router.get("/dashboard")
async def marketplace_dashboard(db: AsyncSession = Depends(get_db)):
    products = await db.execute(
        select(func.count(MarketplaceItem.id)).where(MarketplaceItem.status == "approved")
    )
    total_products = products.scalar() or 0

    creators = await db.execute(select(func.count(CreatorProfile.id)))
    total_creators = creators.scalar() or 0

    top = await db.execute(
        select(MarketplaceItem)
        .where(MarketplaceItem.status == "approved")
        .order_by(MarketplaceItem.downloads.desc())
        .limit(5)
    )
    top_products = [
        {"id": str(p.id), "name": p.name, "downloads": p.downloads, "rating": p.rating}
        for p in list(top.scalars().all())
    ]

    return {
        "total_products": total_products,
        "total_creators": total_creators,
        "top_products": top_products,
    }
