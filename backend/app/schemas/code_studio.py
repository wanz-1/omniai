import uuid
from datetime import datetime
from pydantic import BaseModel


class StudioProjectCreate(BaseModel):
    name: str
    description: str | None = None
    project_type: str = "web"
    frontend_framework: str | None = None
    backend_framework: str | None = None
    database_type: str | None = None
    language: str = "python"
    organization_id: uuid.UUID | None = None


class StudioProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    project_type: str
    frontend_framework: str | None = None
    backend_framework: str | None = None
    database_type: str | None = None
    language: str
    status: str
    source: str
    file_tree: dict | None = None
    user_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class StudioFileResponse(BaseModel):
    id: uuid.UUID
    path: str
    name: str
    content: str | None = None
    language: str | None = None
    size: int
    is_binary: bool

    class Config:
        from_attributes = True


class AppGenerationRequest(BaseModel):
    name: str
    description: str
    project_type: str = "web"
    frontend_framework: str | None = None
    backend_framework: str | None = None
    database_type: str | None = None
    language: str = "python"
    organization_id: uuid.UUID | None = None
    additional_context: str | None = None


class AppGenerationResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    status: str
    files_created: int
    file_tree: dict | None = None
    summary: str | None = None


class CodeGenRequest(BaseModel):
    project_id: uuid.UUID
    prompt: str
    language: str | None = None
    context: str | None = None


class CodeGenResponse(BaseModel):
    code: str
    explanation: str | None = None
    language: str


class DebugRequest(BaseModel):
    project_id: uuid.UUID
    code: str | None = None
    error_message: str | None = None
    language: str = "python"
    context: str | None = None


class DebugResponse(BaseModel):
    root_cause: str
    solution: str
    fixed_code: str | None = None
    suggestions: list[str] = []


class RepositoryConnect(BaseModel):
    url: str
    provider: str = "github"
    token: str | None = None
    project_id: uuid.UUID | None = None


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str | None = None
    provider: str
    default_branch: str
    is_private: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class BuildResponse(BaseModel):
    id: uuid.UUID
    build_number: int
    status: str
    trigger: str
    branch: str
    commit_message: str | None = None
    errors: str | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    deployment_number: int
    status: str
    target: str
    url: str | None = None
    environment: str
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TestRunResponse(BaseModel):
    id: uuid.UUID
    name: str
    test_type: str
    status: str
    framework: str | None = None
    total_tests: int
    passed: int
    failed: int
    coverage: float | None = None
    duration_ms: int | None = None

    class Config:
        from_attributes = True


class SecurityScanResponse(BaseModel):
    id: uuid.UUID
    scan_type: str
    status: str
    risk_score: float | None = None
    summary: str | None = None
    vulnerabilities: list | None = None
    recommendations: list | None = None
    severity_counts: dict | None = None

    class Config:
        from_attributes = True


class DocGenResponse(BaseModel):
    id: uuid.UUID
    doc_type: str
    title: str
    content: str | None = None
    format: str
    sections: list | None = None

    class Config:
        from_attributes = True


class DeploymentRequest(BaseModel):
    target: str
    environment: str = "production"
    config: dict | None = None


class TestGenRequest(BaseModel):
    project_id: uuid.UUID
    test_type: str = "unit"
    framework: str | None = None
    files_to_test: list[str] | None = None


class SecurityScanRequest(BaseModel):
    project_id: uuid.UUID
    scan_type: str = "full"
