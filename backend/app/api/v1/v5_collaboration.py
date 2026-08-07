import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.v5_collaboration import (
    AIMeetingInsightResponse,
    CollaborationAgentResponse,
    CollaborationDashboardResponse,
    CollaborationSessionResponse,
    CreateAgentRequest,
    CreateSessionRequest,
    CreateWhiteboardRequest,
    DocumentCollaborationResponse,
    JoinAgentRequest,
    MultimodalMessageResponse,
    ScreenShareSessionResponse,
    SendMessageRequest,
    SessionParticipantResponse,
    SessionRecordingResponse,
    UpdateWhiteboardRequest,
    WhiteboardSessionResponse,
)
from app.services.collaboration_platform.agent_service import CollaborationAgentService
from app.services.collaboration_platform.document_collab_service import DocumentCollaborationService
from app.services.collaboration_platform.meeting_intelligence import MeetingIntelligenceService
from app.services.collaboration_platform.realtime_service import RealtimeService
from app.services.collaboration_platform.recording_service import RecordingService
from app.services.collaboration_platform.screen_share_service import ScreenShareService
from app.services.collaboration_platform.session_manager import SessionManager
from app.services.collaboration_platform.whiteboard_service import WhiteboardService

router = APIRouter()


@router.post("/sessions", response_model=CollaborationSessionResponse)
async def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    return await mgr.create_session(
        current_user.organization_id or current_user.id,
        req.title, req.session_type, req.description,
        current_user.id, req.participants,
    )


@router.get("/sessions", response_model=list[CollaborationSessionResponse])
async def list_sessions(
    session_type: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    return await mgr.list_sessions(current_user.organization_id or current_user.id, session_type, status)


@router.get("/sessions/{session_id}", response_model=CollaborationSessionResponse)
async def get_session(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = SessionManager(db)
    return await mgr.get_session(session_id)


@router.post("/sessions/{session_id}/start", response_model=CollaborationSessionResponse)
async def start_session(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = SessionManager(db)
    return await mgr.start_session(session_id)


@router.post("/sessions/{session_id}/end", response_model=CollaborationSessionResponse)
async def end_session(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = SessionManager(db)
    return await mgr.end_session(session_id)


@router.post("/sessions/{session_id}/join", response_model=SessionParticipantResponse)
async def join_session(
    session_id: uuid.UUID,
    role: str = "participant",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    return await mgr.join_session(session_id, current_user.id, role)


@router.post("/sessions/{session_id}/leave")
async def leave_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    result = await mgr.leave_session(session_id, current_user.id)
    return {"status": "left" if result else "not_found"}


@router.get("/sessions/{session_id}/participants", response_model=list[SessionParticipantResponse])
async def get_participants(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = SessionManager(db)
    return await mgr.get_participants(session_id)


@router.post("/messages", response_model=MultimodalMessageResponse)
async def send_message(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    return await mgr.send_message(
        req.session_id, current_user.id, req.message_type,
        req.content, req.media_url, req.media_type,
        req.duration_seconds, req.parent_id,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MultimodalMessageResponse])
async def get_messages(session_id: uuid.UUID, limit: int = 100, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    mgr = SessionManager(db)
    return await mgr.get_messages(session_id, limit)


@router.post("/whiteboards", response_model=WhiteboardSessionResponse)
async def create_whiteboard(
    req: CreateWhiteboardRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = WhiteboardService(db)
    return await svc.create(req.session_id, req.title, current_user.id)


@router.get("/whiteboards/{whiteboard_id}", response_model=WhiteboardSessionResponse)
async def get_whiteboard(whiteboard_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = WhiteboardService(db)
    return await svc.get(whiteboard_id)


@router.patch("/whiteboards/{whiteboard_id}", response_model=WhiteboardSessionResponse)
async def update_whiteboard(
    whiteboard_id: uuid.UUID,
    req: UpdateWhiteboardRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = WhiteboardService(db)
    return await svc.update(whiteboard_id, req.strokes, req.shapes, req.annotations)


@router.get("/sessions/{session_id}/whiteboards", response_model=list[WhiteboardSessionResponse])
async def list_whiteboards(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = WhiteboardService(db)
    return await svc.list_by_session(session_id)


@router.post("/whiteboards/{whiteboard_id}/lock")
async def lock_whiteboard(whiteboard_id: uuid.UUID, locked: bool = True, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = WhiteboardService(db)
    result = await svc.lock(whiteboard_id, locked)
    return {"status": "locked" if result else "not_found"}


@router.post("/whiteboards/{whiteboard_id}/ai-suggest")
async def ai_whiteboard_suggest(whiteboard_id: uuid.UUID, prompt: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = WhiteboardService(db)
    result = await svc.ai_suggest(whiteboard_id, prompt)
    return {"suggestion": result}


@router.post("/sessions/{session_id}/insights", response_model=AIMeetingInsightResponse)
async def generate_insights(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MeetingIntelligenceService(db)
    return await svc.generate_insights(session_id, current_user.organization_id or current_user.id)


@router.get("/sessions/{session_id}/insights", response_model=AIMeetingInsightResponse)
async def get_insights(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = MeetingIntelligenceService(db)
    return await svc.get_insights(session_id)


@router.post("/recordings/start", response_model=SessionRecordingResponse)
async def start_recording(session_id: uuid.UUID, recording_type: str = "video", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RecordingService(db)
    return await svc.start_recording(session_id, recording_type)


@router.post("/recordings/{recording_id}/stop", response_model=SessionRecordingResponse)
async def stop_recording(
    recording_id: uuid.UUID,
    file_url: str | None = None,
    duration: float | None = None,
    file_size: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RecordingService(db)
    return await svc.stop_recording(recording_id, file_url, duration, file_size)


@router.post("/recordings/{recording_id}/transcribe")
async def transcribe_recording(recording_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RecordingService(db)
    transcript = await svc.transcribe(recording_id)
    return {"transcript": transcript}


@router.get("/sessions/{session_id}/recordings", response_model=list[SessionRecordingResponse])
async def list_recordings(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RecordingService(db)
    return await svc.list_by_session(session_id)


@router.post("/screen-share/start", response_model=ScreenShareSessionResponse)
async def start_screen_share(
    session_id: uuid.UUID,
    stream_url: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ScreenShareService(db)
    return await svc.start(session_id, current_user.id, stream_url)


@router.post("/screen-share/{share_id}/stop", response_model=ScreenShareSessionResponse)
async def stop_screen_share(share_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ScreenShareService(db)
    return await svc.stop(share_id)


@router.get("/sessions/{session_id}/screen-shares", response_model=list[ScreenShareSessionResponse])
async def list_screen_shares(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = ScreenShareService(db)
    return await svc.get_by_session(session_id)


@router.post("/agents", response_model=CollaborationAgentResponse)
async def create_collaboration_agent(
    req: CreateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CollaborationAgentService(db)
    return await svc.create_agent(
        current_user.organization_id or current_user.id,
        req.name, req.agent_type, req.capabilities, req.config, current_user.id,
    )


@router.get("/agents", response_model=list[CollaborationAgentResponse])
async def list_collaboration_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CollaborationAgentService(db)
    return await svc.list_agents(current_user.organization_id or current_user.id)


@router.post("/agents/join")
async def join_agent_to_session(req: JoinAgentRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CollaborationAgentService(db)
    link = await svc.join_session(req.agent_id, req.session_id, req.role)
    return {"status": "joined", "link_id": str(link.id)}


@router.post("/agents/{agent_id}/chat")
async def chat_with_agent(
    agent_id: uuid.UUID, session_id: uuid.UUID, message: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CollaborationAgentService(db)
    result = await svc.agent_chat(session_id, agent_id, message)
    return {"reply": result}


@router.post("/documents", response_model=DocumentCollaborationResponse)
async def create_document_collab(
    session_id: uuid.UUID, document_id: uuid.UUID, document_type: str, title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = DocumentCollaborationService(db)
    return await svc.create(session_id, document_id, document_type, title)


@router.patch("/documents/{doc_id}", response_model=DocumentCollaborationResponse)
async def update_document_collab(doc_id: uuid.UUID, content: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DocumentCollaborationService(db)
    return await svc.update_content(doc_id, content)


@router.post("/documents/{doc_id}/lock")
async def lock_document(doc_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DocumentCollaborationService(db)
    result = await svc.lock(doc_id, current_user.id)
    return {"status": "locked" if result else "already_locked_or_not_found"}


@router.post("/documents/{doc_id}/unlock")
async def unlock_document(doc_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DocumentCollaborationService(db)
    result = await svc.unlock(doc_id)
    return {"status": "unlocked" if result else "not_found"}


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentCollaborationResponse])
async def list_document_collabs(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DocumentCollaborationService(db)
    return await svc.list_by_session(session_id)


@router.post("/documents/{doc_id}/ai-edit")
async def ai_edit_document(doc_id: uuid.UUID, instruction: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = DocumentCollaborationService(db)
    result = await svc.ai_edit(doc_id, instruction)
    return {"result": result}


@router.get("/sessions/{session_id}/presence")
async def get_presence(session_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = RealtimeService(db)
    return {"participants": await svc.get_presence(session_id)}


@router.post("/sessions/{session_id}/broadcast")
async def broadcast_event(
    session_id: uuid.UUID, event_type: str, payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RealtimeService(db)
    msg = await svc.broadcast(session_id, current_user.id, event_type, payload)
    return {"event_id": str(msg.id)}


@router.get("/sessions/{session_id}/activity")
async def get_recent_activity(
    session_id: uuid.UUID,
    since: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = RealtimeService(db)
    from datetime import datetime
    since_dt = datetime.fromisoformat(since) if since else None
    messages = await svc.get_recent_activity(session_id, since_dt, limit)
    return {"messages": [{"id": str(m.id), "type": m.message_type, "content": m.content, "sender": str(m.sender_id), "created_at": m.created_at.isoformat()} for m in messages]}


@router.get("/dashboard", response_model=CollaborationDashboardResponse)
async def get_collaboration_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mgr = SessionManager(db)
    return await mgr.get_dashboard(current_user.organization_id or current_user.id)
