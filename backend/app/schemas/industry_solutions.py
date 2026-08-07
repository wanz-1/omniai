import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IndustryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    is_active: bool = True
    sort_order: int = 0
    config: dict | None = None
    model_config = ConfigDict(from_attributes=True)


class SolutionPackageResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    version: str
    is_installed: bool = False
    installed_at: datetime | None = None
    capabilities: list | None = None
    model_config = ConfigDict(from_attributes=True)


class SolutionPackageInstall(BaseModel):
    organization_id: uuid.UUID | None = None


class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    title: str
    content: str | None = None
    category: str | None = None
    tags: list | None = None
    source: str | None = None
    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    source: str | None = None


class IndustryWorkflowResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    name: str
    description: str | None = None
    workflow_type: str
    steps: list | None = None
    is_active: bool = True
    trigger: str | None = None
    model_config = ConfigDict(from_attributes=True)


class IndustryWorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    workflow_type: str
    steps: list | None = None
    trigger: str | None = None


class ComplianceRuleResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    name: str
    description: str | None = None
    rule_type: str
    severity: str
    condition: dict | None = None
    action: dict | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class ComplianceRuleCreate(BaseModel):
    name: str
    description: str | None = None
    rule_type: str
    severity: str = "medium"
    condition: dict | None = None
    action: dict | None = None


class IndustryAgentResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    name: str
    slug: str
    agent_type: str
    description: str | None = None
    capabilities: list | None = None
    system_prompt: str | None = None
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class IndustryAgentCreate(BaseModel):
    name: str
    slug: str
    agent_type: str
    description: str | None = None
    capabilities: list[str] | None = None
    system_prompt: str | None = None


class IndustryTemplateResponse(BaseModel):
    id: uuid.UUID
    industry_id: uuid.UUID
    name: str
    template_type: str
    description: str | None = None
    content: dict | None = None
    variables: list | None = None
    category: str | None = None
    model_config = ConfigDict(from_attributes=True)


class IndustryTemplateCreate(BaseModel):
    name: str
    template_type: str
    description: str | None = None
    content: dict | None = None
    variables: list[str] | None = None
    category: str | None = None


class IndustryQuery(BaseModel):
    industry_slug: str
    query: str
    context: dict | None = None
    organization_id: uuid.UUID | None = None


class IndustryQueryResponse(BaseModel):
    response: str
    sources: list | None = None
    confidence: float | None = None
    agent_used: str | None = None
