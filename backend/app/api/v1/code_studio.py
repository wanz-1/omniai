import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.code_studio import (
    BuildRecord,
    Repository,
    SecurityScan,
    StudioDeployment,
    StudioDocumentation,
    StudioFile,
    StudioProject,
    TestRun,
)
from app.models.user import User
from app.schemas.code_studio import (
    AppGenerationRequest,
    AppGenerationResponse,
    BuildResponse,
    CodeGenRequest,
    CodeGenResponse,
    DebugRequest,
    DebugResponse,
    DeploymentRequest,
    DeploymentResponse,
    DocGenResponse,
    RepositoryConnect,
    RepositoryResponse,
    SecurityScanRequest,
    SecurityScanResponse,
    StudioFileResponse,
    StudioProjectCreate,
    StudioProjectResponse,
    TestGenRequest,
    TestRunResponse,
)
from app.services.app_generator import AppGeneratorService
from app.services.code_debugger import CodeDebuggerService
from app.services.deployment_manager import DeploymentManagerService
from app.services.doc_generator import DocGeneratorService
from app.services.git_manager import GitManagerService
from app.services.security_scanner import SecurityScannerService
from app.services.test_engine import TestEngineService

router = APIRouter()


# ─── Projects ────────────────────────────────────────────────────────────────

@router.post("/projects", response_model=StudioProjectResponse)
async def create_project(
    req: StudioProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = StudioProject(
        name=req.name,
        description=req.description,
        project_type=req.project_type,
        frontend_framework=req.frontend_framework,
        backend_framework=req.backend_framework,
        database_type=req.database_type,
        language=req.language,
        user_id=current_user.id,
        organization_id=req.organization_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[StudioProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    organization_id: uuid.UUID | None = None,
):
    stmt = select(StudioProject).order_by(StudioProject.created_at.desc())
    if organization_id:
        stmt = stmt.where(StudioProject.organization_id == organization_id)
    else:
        stmt = stmt.where(StudioProject.user_id == current_user.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/projects/{project_id}", response_model=StudioProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudioProject).where(StudioProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudioProject).where(StudioProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}


# ─── Files ───────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/files", response_model=list[StudioFileResponse])
async def list_files(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudioFile).where(StudioFile.project_id == project_id)
    )
    return list(result.scalars().all())


@router.get("/files/{file_id}", response_model=StudioFileResponse)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudioFile).where(StudioFile.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(404, "File not found")
    return file


@router.put("/files/{file_id}")
async def update_file(
    file_id: uuid.UUID,
    content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudioFile).where(StudioFile.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(404, "File not found")
    file.content = content
    file.size = len(content)
    await db.commit()
    return {"message": "File updated"}


# ─── App Generator ───────────────────────────────────────────────────────────

@router.post("/generate", response_model=AppGenerationResponse)
async def generate_app(
    req: AppGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AppGeneratorService(db)
    project = await svc.generate(
        name=req.name,
        description=req.description,
        project_type=req.project_type,
        frontend_framework=req.frontend_framework,
        backend_framework=req.backend_framework,
        database_type=req.database_type,
        language=req.language,
        user_id=current_user.id,
        organization_id=req.organization_id,
        additional_context=req.additional_context,
    )
    return AppGenerationResponse(
        project_id=project.id,
        name=project.name,
        status=project.status,
        files_created=project.config.get("files_created", 0) if project.config else 0,
        file_tree=project.file_tree,
        summary=(project.config or {}).get("summary", ""),
    )


@router.post("/generate-code", response_model=CodeGenResponse)
async def generate_code(
    req: CodeGenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = AppGeneratorService(db)
    result = await svc.generate_code_snippet(req.prompt, req.language or "python", req.context)
    return CodeGenResponse(
        code=result.get("code", ""),
        explanation=result.get("explanation", ""),
        language=result.get("language", req.language or "python"),
    )


# ─── AI Debugger ─────────────────────────────────────────────────────────────

@router.post("/debug", response_model=DebugResponse)
async def debug_code(
    req: DebugRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CodeDebuggerService(db)
    result = await svc.debug(req.code, req.error_message, req.language, req.context)
    return DebugResponse(
        root_cause=result.get("root_cause", "Analysis complete"),
        solution=result.get("solution", ""),
        fixed_code=result.get("fixed_code", ""),
        suggestions=result.get("suggestions", []),
    )


@router.post("/review-code")
async def review_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    language: str = "python",
):
    svc = CodeDebuggerService(db)
    result = await svc.review_code(code, language)
    return result


# ─── Git Integration ─────────────────────────────────────────────────────────

@router.post("/repositories", response_model=RepositoryResponse)
async def connect_repository(
    req: RepositoryConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GitManagerService(db)
    repo = await svc.connect_repository(
        url=req.url,
        provider=req.provider,
        token=req.token,
        user_id=current_user.id,
        project_id=req.project_id,
    )
    return repo


@router.get("/repositories", response_model=list[RepositoryResponse])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id).order_by(Repository.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/repositories/{repo_id}/analyze")
async def analyze_repository(
    repo_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GitManagerService(db)
    analysis = await svc.analyze_repository(repo_id)
    return analysis


@router.post("/commit-message")
async def generate_commit_message(
    diff: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = GitManagerService(db)
    message = await svc.generate_commit_message(diff)
    return {"message": message}


# ─── Builds ──────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/build", response_model=BuildResponse)
async def build_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DeploymentManagerService(db)
    build = await svc.build_project(project_id, current_user.id)
    return build


@router.get("/projects/{project_id}/builds", response_model=list[BuildResponse])
async def list_builds(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BuildRecord).where(BuildRecord.project_id == project_id).order_by(BuildRecord.build_number.desc()).limit(20)
    )
    return list(result.scalars().all())


# ─── Deployments ─────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/deploy", response_model=DeploymentResponse)
async def deploy_project(
    project_id: uuid.UUID,
    req: DeploymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DeploymentManagerService(db)
    deploy = await svc.deploy(
        project_id=project_id,
        target=req.target,
        environment=req.environment,
        config=req.config,
        user_id=current_user.id,
    )
    return deploy


@router.get("/projects/{project_id}/deployments", response_model=list[DeploymentResponse])
async def list_deployments(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudioDeployment).where(StudioDeployment.project_id == project_id).order_by(StudioDeployment.deployment_number.desc()).limit(20)
    )
    return list(result.scalars().all())


@router.get("/deployments/{deployment_id}/dockerfile")
async def get_dockerfile(
    deployment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudioDeployment).where(StudioDeployment.id == deployment_id))
    deploy = result.scalar_one_or_none()
    if not deploy:
        raise HTTPException(404, "Deployment not found")
    return {"dockerfile": (deploy.config or {}).get("dockerfile", ""), "docker_compose": (deploy.config or {}).get("docker_compose", "")}


@router.post("/projects/{project_id}/ci-cd")
async def generate_ci_cd(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    platform: str = "github",
):
    svc = DeploymentManagerService(db)
    pipeline = await svc.generate_ci_cd(project_id, platform)
    return {"platform": platform, "pipeline": pipeline}


# ─── Tests ───────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/tests", response_model=TestRunResponse)
async def generate_tests(
    project_id: uuid.UUID,
    req: TestGenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TestEngineService(db)
    test_run = await svc.generate_tests(
        project_id=project_id,
        test_type=req.test_type,
        framework=req.framework,
        files_to_test=req.files_to_test,
        user_id=current_user.id,
    )
    return test_run


@router.get("/projects/{project_id}/tests", response_model=list[TestRunResponse])
async def list_test_runs(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestRun).where(TestRun.project_id == project_id).order_by(TestRun.created_at.desc()).limit(20)
    )
    return list(result.scalars().all())


# ─── Security Scans ──────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/security-scan", response_model=SecurityScanResponse)
async def security_scan(
    project_id: uuid.UUID,
    req: SecurityScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = SecurityScannerService(db)
    scan = await svc.scan_project(
        project_id=project_id,
        scan_type=req.scan_type,
        user_id=current_user.id,
    )
    return scan


@router.get("/projects/{project_id}/security-scans", response_model=list[SecurityScanResponse])
async def list_security_scans(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SecurityScan).where(SecurityScan.project_id == project_id).order_by(SecurityScan.created_at.desc()).limit(10)
    )
    return list(result.scalars().all())


@router.get("/projects/{project_id}/security-summary")
async def security_summary(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = SecurityScannerService(db)
    return await svc.get_vulnerability_count(project_id)


# ─── Documentation Generator ─────────────────────────────────────────────────

@router.post("/projects/{project_id}/docs")
async def generate_documentation(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    doc_type: str = "readme",
):
    svc = DocGeneratorService(db)
    doc = await svc.generate(project_id, doc_type, current_user.id)
    return DocGenResponse(
        id=doc.id,
        doc_type=doc.doc_type,
        title=doc.title,
        content=doc.content,
        format=doc.format,
        sections=doc.sections,
    )


@router.post("/projects/{project_id}/docs/all")
async def generate_all_documentation(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DocGeneratorService(db)
    docs = await svc.generate_all(project_id, current_user.id)
    return [
        DocGenResponse(id=d.id, doc_type=d.doc_type, title=d.title, content=d.content, format=d.format, sections=d.sections)
        for d in docs
    ]


@router.get("/projects/{project_id}/docs", response_model=list[DocGenResponse])
async def list_documentation(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudioDocumentation).where(StudioDocumentation.project_id == project_id).order_by(StudioDocumentation.created_at.desc())
    )
    return list(result.scalars().all())


# ─── Code Studio Dashboard ───────────────────────────────────────────────────

@router.get("/dashboard/{organization_id}")
async def code_studio_dashboard(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects_result = await db.execute(
        select(StudioProject).where(StudioProject.organization_id == organization_id).order_by(StudioProject.created_at.desc())
    )
    projects = list(projects_result.scalars().all())

    repos_result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id).order_by(Repository.created_at.desc()).limit(10)
    )
    repos = list(repos_result.scalars().all())

    total_builds = 0
    total_deploys = 0
    total_tests = 0
    total_scans = 0

    for p in projects:
        b = await db.execute(select(BuildRecord).where(BuildRecord.project_id == p.id))
        total_builds += len(list(b.scalars().all()))
        d = await db.execute(select(StudioDeployment).where(StudioDeployment.project_id == p.id))
        total_deploys += len(list(d.scalars().all()))
        t = await db.execute(select(TestRun).where(TestRun.project_id == p.id))
        total_tests += len(list(t.scalars().all()))
        s = await db.execute(select(SecurityScan).where(SecurityScan.project_id == p.id))
        total_scans += len(list(s.scalars().all()))

    return {
        "projects": [{"id": str(p.id), "name": p.name, "status": p.status, "type": p.project_type, "language": p.language} for p in projects],
        "repositories": [{"id": str(r.id), "name": r.name, "provider": r.provider, "url": r.url} for r in repos],
        "stats": {"projects": len(projects), "repos": len(repos), "builds": total_builds, "deployments": total_deploys, "tests": total_tests, "security_scans": total_scans},
    }
