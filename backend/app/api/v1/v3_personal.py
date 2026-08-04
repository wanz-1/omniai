import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.v3_personal import (
    ExecutiveAssistantResponse, PersonalAssistantResponse, PersonalMemoryResponse,
    PersonalQuery, PersonalQueryResponse, PersonalTaskResponse,
)
from app.services.v3.personal_service import PersonalAIService

router = APIRouter()


@router.post("/assistants", response_model=PersonalAssistantResponse)
async def create_assistant(name: str, role: str, personality: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.create_assistant(current_user.id, name, role, personality)


@router.get("/assistants", response_model=list[PersonalAssistantResponse])
async def list_assistants(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.list_assistants(current_user.id)


@router.post("/assistants/query", response_model=PersonalQueryResponse)
async def query_assistant(req: PersonalQuery, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.query_assistant(req.assistant_id, req.query, req.context)


@router.get("/assistants/{assistant_id}/memories", response_model=list[PersonalMemoryResponse])
async def list_memories(assistant_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.search_memories(current_user.id)


@router.post("/assistants/{assistant_id}/memories", response_model=PersonalMemoryResponse)
async def store_memory(assistant_id: uuid.UUID, memory_type: str, title: str, content: str | None = None, importance: int = 0, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.store_memory(assistant_id, current_user.id, memory_type, title, content, importance=importance)


@router.get("/tasks", response_model=list[PersonalTaskResponse])
async def list_tasks(status: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.list_tasks(current_user.id, status)


@router.post("/tasks", response_model=PersonalTaskResponse)
async def create_task(title: str, description: str | None = None, priority: str = "medium", category: str | None = None, assistant_id: uuid.UUID | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    if not assistant_id:
        assistants = await svc.list_assistants(current_user.id)
        if not assistants:
            asst = await svc.create_assistant(current_user.id, "Chief Assistant", "chief")
            assistant_id = asst.id
        else:
            assistant_id = assistants[0].id
    return await svc.create_task(assistant_id, current_user.id, title, description, priority, category)


@router.post("/tasks/{task_id}/complete", response_model=PersonalTaskResponse)
async def complete_task(task_id: uuid.UUID, result: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    task = await svc.complete_task(task_id, result)
    return task


@router.post("/executives", response_model=ExecutiveAssistantResponse)
async def create_executive(role: str, name: str, description: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.create_executive(current_user.id, role, name, description)


@router.get("/executives", response_model=list[ExecutiveAssistantResponse])
async def list_executives(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.list_executives(current_user.id)


@router.post("/executives/{exec_id}/query")
async def query_executive(exec_id: uuid.UUID, query: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = PersonalAIService(db)
    return await svc.query_executive(exec_id, query)
