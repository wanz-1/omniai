import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatMessageSendRequest,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatSessionUpdateRequest,
)

router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    responses = []
    for session in sessions:
        msg_count = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        responses.append(ChatSessionResponse(
            id=session.id,
            title=session.title,
            model=session.model,
            system_prompt=session.system_prompt,
            is_archived=session.is_archived,
            user_id=session.user_id,
            message_count=msg_count.scalar() or 0,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ))
    return responses


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    body: ChatSessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    session = ChatSession(
        title=body.title,
        model=body.model,
        system_prompt=body.system_prompt,
        user_id=current_user.id,
    )
    db.add(session)
    await db.flush()
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        model=session.model,
        system_prompt=session.system_prompt,
        is_archived=session.is_archived,
        user_id=session.user_id,
        message_count=0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise NotFoundError("Chat session", str(session_id))

    msg_count = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
    )
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        model=session.model,
        system_prompt=session.system_prompt,
        is_archived=session.is_archived,
        user_id=session.user_id,
        message_count=msg_count.scalar() or 0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    body: ChatSessionUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise NotFoundError("Chat session", str(session_id))

    if body.title is not None:
        session.title = body.title
    if body.model is not None:
        session.model = body.model
    if body.system_prompt is not None:
        session.system_prompt = body.system_prompt
    if body.is_archived is not None:
        session.is_archived = body.is_archived
    await db.flush()
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise NotFoundError("Chat session", str(session_id))
    await db.delete(session)
    await db.flush()
    return {"message": "Session deleted"}


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return result.scalars().all()


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: uuid.UUID,
    body: ChatMessageSendRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.chat_service import ChatService
    service = ChatService(db)
    result = await service.send_message(session_id, current_user.id, body)
    return result


@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: uuid.UUID,
    body: ChatMessageSendRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.chat_service import ChatService
    service = ChatService(db)

    async def event_generator():
        async for token in service.send_message_stream(session_id, current_user.id, body):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
