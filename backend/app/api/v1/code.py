import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.code_project import CodeGeneration, CodeProject
from app.models.user import User
from app.schemas.code import (
    CodeExplainRequest,
    CodeGenerateRequest,
    CodeGenerateResponse,
    CodeProjectCreateRequest,
    CodeProjectResponse,
    CodeProjectUpdateRequest,
    CodeReviewRequest,
    CodeReviewResponse,
)

router = APIRouter()


@router.get("/projects", response_model=list[CodeProjectResponse])
async def list_code_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: uuid.UUID | None = None,
):
    query = select(CodeProject).where(CodeProject.user_id == current_user.id)
    if project_id:
        query = query.where(CodeProject.project_id == project_id)
    query = query.order_by(CodeProject.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/projects", response_model=CodeProjectResponse)
async def create_code_project(
    body: CodeProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = CodeProject(
        name=body.name,
        description=body.description,
        project_id=body.project_id,
        language=body.language,
        framework=body.framework,
        user_id=current_user.id,
    )
    db.add(project)
    await db.flush()
    return project


@router.get("/projects/{code_project_id}", response_model=CodeProjectResponse)
async def get_code_project(
    code_project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(CodeProject, code_project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Code project", str(code_project_id))
    return project


@router.put("/projects/{code_project_id}", response_model=CodeProjectResponse)
async def update_code_project(
    code_project_id: uuid.UUID,
    body: CodeProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(CodeProject, code_project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Code project", str(code_project_id))

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.files is not None:
        project.files = body.files
    await db.flush()
    return project


@router.delete("/projects/{code_project_id}")
async def delete_code_project(
    code_project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await db.get(CodeProject, code_project_id)
    if not project or project.user_id != current_user.id:
        raise NotFoundError("Code project", str(code_project_id))
    await db.delete(project)
    await db.flush()
    return {"message": "Code project deleted"}


@router.post("/projects/{code_project_id}/generate", response_model=CodeGenerateResponse)
async def generate_code_for_project(
    code_project_id: uuid.UUID,
    body: CodeGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.code_service import CodeService
    service = CodeService(db)
    result = await service.generate_for_project(code_project_id, current_user.id, body)
    return result


@router.post("/generate", response_model=CodeGenerateResponse)
async def generate_code(
    body: CodeGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.code_service import CodeService
    service = CodeService(db)
    result = await service.generate(body, current_user.id)
    return result


@router.post("/explain")
async def explain_code(
    body: CodeExplainRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.code_service import CodeService
    service = CodeService(db)
    result = await service.explain(body)
    return result


@router.post("/review", response_model=CodeReviewResponse)
async def review_code(
    body: CodeReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.code_service import CodeService
    service = CodeService(db)
    result = await service.review(body)
    return result
