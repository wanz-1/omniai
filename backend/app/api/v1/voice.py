import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.media import VoiceSession
from app.models.user import User
from app.schemas.voice import (
    VoiceMessageResponse,
    VoiceSessionCreateRequest,
    VoiceSessionResponse,
)
from app.services.ai_model_router import ai_model_router
from app.services.voice_service import VoiceService

router = APIRouter()


@router.post("/sessions", response_model=VoiceSessionResponse)
async def create_voice_session(
    body: VoiceSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = VoiceService(db)
    session = await svc.create_session(
        user_id=current_user.id,
        organization_id=body.organization_id,
        agent_id=body.agent_id,
        language=body.language or "en",
    )
    return session


@router.get("/sessions", response_model=list[VoiceSessionResponse])
async def list_voice_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(VoiceSession).where(VoiceSession.user_id == current_user.id)
        .order_by(VoiceSession.created_at.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=VoiceSessionResponse)
async def get_voice_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    session = await db.get(VoiceSession, session_id)
    if not session:
        raise NotFoundError("VoiceSession", str(session_id))
    return session


@router.post("/sessions/{session_id}/end")
async def end_voice_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = VoiceService(db)
    session = await svc.end_session(session_id)
    return {"message": "Session ended", "session_id": str(session.id)}


@router.get("/sessions/{session_id}/messages", response_model=list[VoiceMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = VoiceService(db)
    return await svc.get_session_messages(session_id)


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    audio_data = await file.read()
    svc = VoiceService(db)
    result = await svc.transcribe_audio(audio_data, file.content_type or "audio/webm", language)
    return result


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice: str = Form("alloy"),
    language: str = Form("en"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    svc = VoiceService(db)
    audio_bytes = await svc.synthesize_speech(text, voice, language)
    from fastapi.responses import Response
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/sessions/{session_id}/process")
async def process_voice_message(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    audio_data = await file.read()
    svc = VoiceService(db)
    message = await svc.process_voice_message(session_id, audio_data, file.content_type or "audio/webm", language)

    from app.services.ai_service import ai_service
    ai_response = await ai_service.complete(
        prompt=message.text or "",
        system_prompt="You are a voice AI assistant. Respond conversationally and concisely.",
    )

    response_text = ai_response.get("content", ai_response.get("text", "")) if isinstance(ai_response, dict) else ai_response
    response_message = await svc.generate_voice_response(session_id, response_text)

    return {
        "user_message": VoiceMessageResponse.model_validate(message),
        "assistant_message": VoiceMessageResponse.model_validate(response_message),
    }


@router.get("/providers")
async def get_voice_providers():
    return ai_model_router.get_voice_providers()
