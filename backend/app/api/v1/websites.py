import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.website import Website
from app.schemas.website import (
    BrandingRequest,
    BrandingResponse,
    WebsiteCreateRequest,
    WebsiteCustomizeRequest,
    WebsiteDeployRequest,
    WebsiteExportRequest,
    WebsiteGenerateRequest,
    WebsitePublishRequest,
    WebsiteResponse,
    WebsiteUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=list[WebsiteResponse])
async def list_websites(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: uuid.UUID | None = None,
):
    query = select(Website).where(Website.user_id == current_user.id)
    if project_id:
        query = query.where(Website.project_id == project_id)
    query = query.order_by(Website.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=WebsiteResponse)
async def create_website(
    body: WebsiteCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    website = Website(
        name=body.name,
        project_id=body.project_id,
        template_id=body.template_id,
        framework=body.framework,
        styling=body.styling,
        user_id=current_user.id,
    )
    db.add(website)
    await db.flush()
    return website


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    website = await db.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise NotFoundError("Website", str(website_id))
    return website


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: uuid.UUID,
    body: WebsiteUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    website = await db.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise NotFoundError("Website", str(website_id))

    if body.name is not None:
        website.name = body.name
    if body.pages is not None:
        website.pages = body.pages
    if body.theme_config is not None:
        website.theme_config = body.theme_config
    await db.flush()
    return website


@router.delete("/{website_id}")
async def delete_website(
    website_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    website = await db.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise NotFoundError("Website", str(website_id))
    await db.delete(website)
    await db.flush()
    return {"message": "Website deleted"}


@router.post("/{website_id}/generate")
async def generate_website(
    website_id: uuid.UUID,
    body: WebsiteGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    result = await service.generate(website_id, current_user.id, body)
    return result


@router.post("/{website_id}/customize", response_model=WebsiteResponse)
async def customize_website(
    website_id: uuid.UUID,
    body: WebsiteCustomizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    website = await db.get(Website, website_id)
    if not website or website.user_id != current_user.id:
        raise NotFoundError("Website", str(website_id))

    if body.theme_config is not None:
        website.theme_config = body.theme_config
    if body.pages is not None:
        website.pages = body.pages
    await db.flush()
    return website


@router.post("/{website_id}/preview")
async def preview_website(
    website_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    preview_url = await service.generate_preview(website_id, current_user.id)
    return {"preview_url": preview_url}


@router.post("/{website_id}/publish")
async def publish_website(
    website_id: uuid.UUID,
    body: WebsitePublishRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    result = await service.publish(website_id, current_user.id, body)
    return result


@router.post("/{website_id}/deploy")
async def deploy_website(
    website_id: uuid.UUID,
    body: WebsiteDeployRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    result = await service.deploy(website_id, current_user.id, body)
    return result


@router.get("/templates/list")
async def list_templates():
    from app.services.template_service import TEMPLATES
    return list(TEMPLATES.values())


@router.post("/branding", response_model=BrandingResponse)
async def generate_branding(
    body: BrandingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    result = await service.generate_branding(body)
    return result


@router.post("/{website_id}/export")
async def export_website(
    website_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    body: WebsiteExportRequest = WebsiteExportRequest(),
):
    from app.services.website_service import WebsiteService
    service = WebsiteService(db)
    content, media_type, filename = await service.export_site(website_id, current_user.id, body)
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
