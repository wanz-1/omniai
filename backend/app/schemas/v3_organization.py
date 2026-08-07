import uuid

from pydantic import BaseModel, ConfigDict


class AIOrganizationOSResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    status: str = "active"
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class AIDepartmentResponse(BaseModel):
    id: uuid.UUID
    organization_os_id: uuid.UUID
    name: str
    department_type: str
    description: str | None = None
    capabilities: list | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class AutonomousWorkflowResponse(BaseModel):
    id: uuid.UUID
    organization_os_id: uuid.UUID
    name: str
    description: str | None = None
    workflow_type: str
    status: str = "active"
    is_automatic: bool = False
    trigger: str | None = None
    execution_count: int = 0
    steps: list | None = None
    model_config = ConfigDict(from_attributes=True)


class DepartmentAgentResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    agent_type: str
    description: str | None = None
    capabilities: list | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class OrganizationQuery(BaseModel):
    organization_id: uuid.UUID
    query: str
    department: str | None = None


class OrganizationQueryResponse(BaseModel):
    response: str
    department: str | None = None
    recommendations: list | None = None
