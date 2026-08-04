import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationMemberAddRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdateRequest,
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    )
    orgs = result.scalars().all()
    responses = []
    for org in orgs:
        count_result = await db.execute(
            select(func.count(OrganizationMember.id))
            .where(OrganizationMember.organization_id == org.id)
        )
        member_count = count_result.scalar() or 0
        responses.append(
            OrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                logo_url=org.logo_url,
                plan=org.plan,
                is_active=org.is_active,
                member_count=member_count,
                created_at=org.created_at,
                updated_at=org.updated_at,
            )
        )
    return responses


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    body: OrganizationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=Role.OWNER,
    )
    db.add(member)
    await db.flush()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        logo_url=org.logo_url,
        plan=org.plan,
        is_active=org.is_active,
        member_count=1,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = await db.get(Organization, organization_id)
    if not org:
        raise NotFoundError("Organization", str(organization_id))

    count_result = await db.execute(
        select(func.count(OrganizationMember.id))
        .where(OrganizationMember.organization_id == org.id)
    )
    member_count = count_result.scalar() or 0

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        logo_url=org.logo_url,
        plan=org.plan,
        is_active=org.is_active,
        member_count=member_count,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: uuid.UUID,
    body: OrganizationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = await db.get(Organization, organization_id)
    if not org:
        raise NotFoundError("Organization", str(organization_id))

    if body.name is not None:
        org.name = body.name
    if body.logo_url is not None:
        org.logo_url = body.logo_url
    if body.settings is not None:
        org.settings = body.settings
    await db.flush()
    return org


@router.get("/{organization_id}/members", response_model=list[OrganizationMemberResponse])
async def list_members(
    organization_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == organization_id)
    )
    return result.scalars().all()
