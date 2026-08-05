import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProjectType
from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    type: Optional[ProjectType] = None,
):
    query = select(Project).where(Project.user_id == current_user.id)
    if type:
        query = query.where(Project.type == type)
    query = query.order_by(Project.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = Project(
        name=body.name,
        description=body.description,
        type=body.type,
        user_id=current_user.id,
        organization_id=body.organization_id,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Project", str(project_id))
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Project", str(project_id))

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.is_archived is not None:
        project.is_archived = body.is_archived
    await db.flush()
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Project", str(project_id))
    await db.delete(project)
    await db.flush()
    return {"message": "Project deleted"}
