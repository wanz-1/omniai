import uuid
import time
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatMessageResponse, ChatMessageSendRequest
from app.services.ai_service import ai_service


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_message(
        self, session_id: uuid.UUID, user_id: uuid.UUID, body: ChatMessageSendRequest
    ) -> ChatMessageResponse:
        session = await self.db.get(ChatSession, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session", str(session_id))

        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=body.content,
        )
        self.db.add(user_msg)
        await self.db.flush()

        history_result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        history = history_result.scalars().all()

        messages = []
        if session.system_prompt:
            messages.append({"role": "system", "content": session.system_prompt})
        for msg in history:
            if msg.id != user_msg.id:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": body.content})

        start = time.perf_counter()
        response = await ai_service.complete(
            messages=messages,
            model=session.model,
            temperature=0.7,
            stream=False,
        )
        latency = int((time.perf_counter() - start) * 1000)

        user_msg.tokens_used = response.get("tokens_used", 0) // 2
        user_msg.latency_ms = latency

        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response["content"],
            tokens_used=response.get("tokens_used", 0),
            latency_ms=latency,
        )
        self.db.add(assistant_msg)

        if session.title == "New Chat":
            title_response = await ai_service.complete(
                messages=[{"role": "user", "content": f"Generate a short title (max 6 words) for this conversation: {body.content}"}],
                temperature=0.3,
                model="gpt-4o-mini",
            )
            session.title = title_response["content"].strip().strip('"')[:200]

        await self.db.flush()

        return ChatMessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            tokens_used=assistant_msg.tokens_used,
            latency_ms=assistant_msg.latency_ms,
            created_at=assistant_msg.created_at,
        )

    async def send_message_stream(
        self, session_id: uuid.UUID, user_id: uuid.UUID, body: ChatMessageSendRequest
    ) -> AsyncGenerator[str, None]:
        session = await self.db.get(ChatSession, session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session", str(session_id))

        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=body.content,
        )
        self.db.add(user_msg)
        await self.db.flush()

        history_result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        history = history_result.scalars().all()

        messages = []
        if session.system_prompt:
            messages.append({"role": "system", "content": session.system_prompt})
        for msg in history:
            if msg.id != user_msg.id:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": body.content})

        full_content = ""
        stream = ai_service.complete_stream(
            messages=messages,
            model=session.model,
            temperature=0.7,
        )
        async for token in stream:
            full_content += token
            yield token

        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_content,
        )
        self.db.add(assistant_msg)

        if session.title == "New Chat":
            title_response = await ai_service.complete(
                messages=[{"role": "user", "content": f"Generate a short title (max 6 words) for this conversation: {body.content}"}],
                temperature=0.3,
                model="gpt-4o-mini",
            )
            session.title = title_response["content"].strip().strip('"')[:200]

        await self.db.flush()
