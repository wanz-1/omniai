import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v3_collaboration import (
    CommunicationResponse,
    DeviceTelemetryResponse,
    LearningPathResponse,
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    MeetingSessionResponse,
    PhysicalDeviceResponse,
)
from app.services.v3.collaboration_service import CollaborationService

router = APIRouter()


@router.post("/meetings/analyze", response_model=MeetingAnalysisResponse)
async def analyze_meeting(req: MeetingAnalysisRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    result = await svc.analyze_meeting(req.title, req.transcript, req.participants)
    await svc.save_meeting(current_user.id, req.title, req.transcript, req.participants, result["summary"], [], [])
    return result


@router.get("/meetings", response_model=list[MeetingSessionResponse])
async def list_meetings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.list_meetings(current_user.id)


@router.post("/communications", response_model=CommunicationResponse)
async def generate_communication(communication_type: str, title: str, content: str | None = None, recipient: str | None = None, tone: str = "professional", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.generate_communication(current_user.id, communication_type, title, content, recipient, tone)


@router.get("/communications", response_model=list[CommunicationResponse])
async def list_communications(communication_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.list_communications(current_user.id, communication_type)


@router.post("/learning", response_model=LearningPathResponse)
async def create_learning_path(title: str, subject: str, skill_level: str = "beginner", goals: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    path, curriculum = await svc.create_learning_path(
        current_user.id, title, subject, skill_level,
        goals.split(",") if goals else None,
    )
    return path


@router.get("/learning", response_model=list[LearningPathResponse])
async def list_learning_paths(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.list_learning_paths(current_user.id)


@router.post("/devices", response_model=PhysicalDeviceResponse)
async def register_device(name: str, device_type: str, protocol: str = "mqtt", endpoint: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.register_device(current_user.id, name, device_type, protocol, endpoint)


@router.get("/devices", response_model=list[PhysicalDeviceResponse])
async def list_devices(device_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.list_devices(current_user.id, device_type)


@router.post("/devices/{device_id}/telemetry", response_model=DeviceTelemetryResponse)
async def record_telemetry(device_id: uuid.UUID, metric_name: str, metric_value: float, unit: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationService(db)
    return await svc.record_telemetry(device_id, metric_name, metric_value, unit)
