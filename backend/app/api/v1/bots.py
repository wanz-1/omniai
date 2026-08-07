import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.bot import Bot, BotConversation, BotMessage
from app.models.user import User
from app.schemas.bot import (
    BotAnalyticsResponse,
    BotConversationResponse,
    BotCreateRequest,
    BotDeployRequest,
    BotEmbedRequest,
    BotEmbedResponse,
    BotMessageResponse,
    BotResponse,
    BotTestRequest,
    BotTestResponse,
    BotTrainRequest,
    BotUpdateRequest,
)
from app.ws.manager import manager

router = APIRouter()


@router.get("", response_model=list[BotResponse])
async def list_bots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: uuid.UUID | None = None,
):
    query = select(Bot).where(Bot.user_id == current_user.id)
    if project_id:
        query = query.where(Bot.project_id == project_id)
    query = query.order_by(Bot.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=BotResponse)
async def create_bot(
    body: BotCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    bot = Bot(
        name=body.name,
        description=body.description,
        project_id=body.project_id,
        system_prompt=body.system_prompt,
        model=body.model,
        temperature=body.temperature,
        industry=body.industry,
        tone=body.tone,
        knowledge_base_config=body.knowledge_base_config,
        widget_config=body.widget_config,
        user_id=current_user.id,
    )
    db.add(bot)
    await db.flush()
    return bot


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != current_user.id:
        raise NotFoundError("Bot", str(bot_id))
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: uuid.UUID,
    body: BotUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != current_user.id:
        raise NotFoundError("Bot", str(bot_id))

    if body.name is not None:
        bot.name = body.name
    if body.description is not None:
        bot.description = body.description
    if body.system_prompt is not None:
        bot.system_prompt = body.system_prompt
    if body.model is not None:
        bot.model = body.model
    if body.temperature is not None:
        bot.temperature = body.temperature
    if body.is_active is not None:
        bot.is_active = body.is_active
    if body.industry is not None:
        bot.industry = body.industry
    if body.tone is not None:
        bot.tone = body.tone
    if body.knowledge_base_config is not None:
        bot.knowledge_base_config = body.knowledge_base_config
    if body.widget_config is not None:
        bot.widget_config = body.widget_config
    await db.flush()
    return bot


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != current_user.id:
        raise NotFoundError("Bot", str(bot_id))
    await db.delete(bot)
    await db.flush()
    return {"message": "Bot deleted"}


@router.post("/{bot_id}/train")
async def train_bot(
    bot_id: uuid.UUID,
    body: BotTrainRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.bot_service import BotService
    service = BotService(db)
    task_id = await service.train(bot_id, current_user.id, body)
    return {"task_id": task_id, "status": "training_started"}


@router.post("/{bot_id}/test", response_model=BotTestResponse)
async def test_bot(
    bot_id: uuid.UUID,
    body: BotTestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.bot_service import BotService
    service = BotService(db)
    result = await service.test(bot_id, current_user.id, body)
    return result


@router.post("/{bot_id}/deploy")
async def deploy_bot(
    bot_id: uuid.UUID,
    body: BotDeployRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.bot_service import BotService
    service = BotService(db)
    result = await service.deploy(bot_id, current_user.id, body)
    return result


@router.post("/{bot_id}/test/stream")
async def test_bot_stream(
    bot_id: uuid.UUID,
    body: BotTestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.bot_service import BotService
    service = BotService(db)

    async def event_generator():
        async for token in service.test_stream(bot_id, current_user.id, body):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/{bot_id}/embed", response_model=BotEmbedResponse)
async def get_embed_code(
    bot_id: uuid.UUID,
    body: BotEmbedRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.bot_service import BotService
    service = BotService(db)
    result = await service.get_embed_code(bot_id, current_user.id, body)
    return result


@router.websocket("/{bot_id}/ws")
async def bot_websocket(
    bot_id: uuid.UUID,
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await manager.connect(websocket, f"bot:{bot_id}")
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "message":
                from app.services.bot_service import BotService
                service = BotService(db)
                try:
                    response = await service.test(
                        bot_id, uuid.UUID(int=0),
                        type("Req", (), {"message": data.get("content", "")})(),
                    )
                    await websocket.send_json({
                        "type": "reply",
                        "content": response.reply,
                        "latency_ms": response.latency_ms,
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"bot:{bot_id}")


@router.get("/{bot_id}/analytics", response_model=BotAnalyticsResponse)
async def get_bot_analytics(
    bot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    conv_count = await db.execute(
        select(func.count(BotConversation.id)).where(BotConversation.bot_id == bot_id)
    )
    msg_count = await db.execute(
        select(func.count(BotMessage.id))
        .join(BotConversation)
        .where(BotConversation.bot_id == bot_id)
    )
    return BotAnalyticsResponse(
        total_conversations=conv_count.scalar() or 0,
        total_messages=msg_count.scalar() or 0,
        daily_activity=await _bot_daily_activity(db, bot_id),
    )


async def _bot_daily_activity(db: AsyncSession, bot_id: uuid.UUID, days: int = 14) -> list[dict]:
    """Bucket conversation/message counts per day for the last ``days`` days."""
    today = datetime.now(UTC).date()
    cutoff = datetime.combine(today - timedelta(days=days - 1), datetime.min.time(), tzinfo=UTC)
    conv_rows = await db.execute(
        select(BotConversation.created_at).where(
            BotConversation.bot_id == bot_id,
            BotConversation.created_at >= cutoff,
        )
    )
    msg_rows = await db.execute(
        select(BotMessage.created_at)
        .join(BotConversation, BotMessage.conversation_id == BotConversation.id)
        .where(
            BotConversation.bot_id == bot_id,
            BotMessage.created_at >= cutoff,
        )
    )
    conv_by_day: dict[str, int] = {}
    msg_by_day: dict[str, int] = {}
    for (created_at,) in conv_rows.all():
        key = created_at.date().isoformat() if created_at is not None else None
        if key:
            conv_by_day[key] = conv_by_day.get(key, 0) + 1
    for (created_at,) in msg_rows.all():
        key = created_at.date().isoformat() if created_at is not None else None
        if key:
            msg_by_day[key] = msg_by_day.get(key, 0) + 1
    return [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "conversations": conv_by_day.get((today - timedelta(days=offset)).isoformat(), 0),
            "messages": msg_by_day.get((today - timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(days - 1, -1, -1)
    ]


@router.get("/{bot_id}/conversations", response_model=list[BotConversationResponse])
async def list_conversations(
    bot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(BotConversation)
        .where(BotConversation.bot_id == bot_id)
        .order_by(BotConversation.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{bot_id}/conversations/{conversation_id}/messages", response_model=list[BotMessageResponse])
async def get_conversation_messages(
    bot_id: uuid.UUID,
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != current_user.id:
        raise NotFoundError("Bot", str(bot_id))
    conv = await db.get(BotConversation, conversation_id)
    if not conv or conv.bot_id != bot_id:
        raise NotFoundError("Conversation", str(conversation_id))
    result = await db.execute(
        select(BotMessage)
        .where(BotMessage.conversation_id == conversation_id)
        .order_by(BotMessage.created_at)
    )
    return result.scalars().all()
