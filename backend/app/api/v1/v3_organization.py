import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v3_organization import (
    AIDepartmentResponse,
    AIOrganizationOSResponse,
    AutonomousWorkflowResponse,
    DepartmentAgentResponse,
    OrganizationQuery,
    OrganizationQueryResponse,
)
from app.services.v3.organization_service import OrganizationAIService

router = APIRouter()


@router.post("/os/{organization_id}", response_model=AIOrganizationOSResponse)
async def create_organization_os(organization_id: uuid.UUID, name: str, description: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    return await svc.create_os(organization_id, name, description)


@router.get("/os/{organization_id}", response_model=AIOrganizationOSResponse)
async def get_organization_os(organization_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    os = await svc.get_os(organization_id)
    return os


@router.post("/os/{organization_id}/departments", response_model=AIDepartmentResponse)
async def create_department(organization_id: uuid.UUID, name: str, department_type: str, description: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    os = await svc.get_os(organization_id)
    if not os:
        os = await svc.create_os(organization_id, f"OS-{organization_id[:8]}")
    return await svc.create_department(os.id, name, department_type, description)


@router.get("/os/{organization_id}/departments", response_model=list[AIDepartmentResponse])
async def list_departments(organization_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    os = await svc.get_os(organization_id)
    if not os:
        return []
    return await svc.list_departments(os.id)


@router.get("/departments/{department_id}/agents", response_model=list[DepartmentAgentResponse])
async def list_department_agents(department_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    return await svc.list_department_agents(department_id)


@router.post("/os/{organization_id}/workflows", response_model=AutonomousWorkflowResponse)
async def create_workflow(organization_id: uuid.UUID, name: str, workflow_type: str, description: str | None = None, is_automatic: bool = False, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    os = await svc.get_os(organization_id)
    if not os:
        os = await svc.create_os(organization_id, f"OS-{str(organization_id)[:8]}")
    return await svc.create_workflow(os.id, name, workflow_type, description, is_automatic=is_automatic)


@router.get("/os/{organization_id}/workflows", response_model=list[AutonomousWorkflowResponse])
async def list_workflows(organization_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    os = await svc.get_os(organization_id)
    if not os:
        return []
    return await svc.list_workflows(os.id)


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    return await svc.execute_workflow(workflow_id)


@router.post("/query", response_model=OrganizationQueryResponse)
async def query_organization(req: OrganizationQuery, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = OrganizationAIService(db)
    return await svc.query_organization(req.organization_id, req.query, req.department)
