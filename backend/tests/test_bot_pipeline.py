"""Bot API integration tests.

Covers the bot lifecycle (CRUD + ownership), training, testing (with and
without knowledge-base context), deployment, embed-code generation, and
conversation/analytics flows. The AI provider is mocked via
``ai_service.complete`` / ``complete_stream``.
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import get_current_user
from app.models.bot import Bot
from app.models.user import User
from app.services.ai_service import ai_service

PASSWORD = "TestPassword123!"


async def _create_bot(client, **overrides):
    payload = {
        "name": "Support Bot",
        "description": "Answers support questions",
        "system_prompt": "You are a helpful support assistant.",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "industry": "saas",
        "tone": "professional",
        **overrides,
    }
    resp = await client.post("/api/v1/bots", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# CRUD + OWNERSHIP
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_bot_crud_lifecycle(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)

    fetched = await client.get(f"/api/v1/bots/{bot['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Support Bot"
    assert fetched.json()["temperature"] == 0.3

    updated = await client.put(
        f"/api/v1/bots/{bot['id']}",
        json={"name": "Renamed Bot", "system_prompt": "New prompt", "is_active": False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Renamed Bot"
    assert updated.json()["is_active"] is False

    listed = await client.get("/api/v1/bots")
    assert listed.status_code == 200
    assert any(b["id"] == bot["id"] and b["name"] == "Renamed Bot" for b in listed.json())

    deleted = await client.delete(f"/api/v1/bots/{bot['id']}")
    assert deleted.status_code == 200
    assert (await client.get(f"/api/v1/bots/{bot['id']}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bot_ownership_enforced_across_users(stateful_client):
    import app.main as main_mod
    client, db = stateful_client
    owner = User(email="bot-owner@example.com", display_name="Owner", is_verified=True)
    intruder = User(email="bot-intruder@example.com", display_name="Intruder", is_verified=True)
    db.add(owner)
    db.add(intruder)

    main_mod.app.dependency_overrides[get_current_user] = lambda: owner
    bot = await _create_bot(client)

    main_mod.app.dependency_overrides[get_current_user] = lambda: intruder
    assert (await client.get(f"/api/v1/bots/{bot['id']}")).status_code == 404
    assert (await client.put(f"/api/v1/bots/{bot['id']}", json={"name": "Hijacked"})).status_code == 404
    assert (await client.delete(f"/api/v1/bots/{bot['id']}")).status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# TRAIN / TEST / DEPLOY / EMBED
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_train_persists_knowledge_base(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)

    resp = await client.post(
        f"/api/v1/bots/{bot['id']}/train",
        json={"files": ["guide.pdf"], "urls": ["https://docs.example.com"], "text": "Internal runbook content"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "training_started"
    assert data["task_id"]

    stored = db.find(Bot, id=uuid.UUID(bot["id"]))
    assert stored.knowledge_base_config == {
        "files": ["guide.pdf"],
        "urls": ["https://docs.example.com"],
        "text": "Internal runbook content",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_test_bot_with_knowledge_context(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)
    await client.post(
        f"/api/v1/bots/{bot['id']}/train",
        json={"text": "Pricing: Pro plan costs 49 USD per month."},
    )

    with patch.object(ai_service, "complete", new=AsyncMock(return_value={
        "content": "The Pro plan costs 49 USD per month.",
        "tokens_used": 32,
    })) as mocked:
        resp = await client.post(
            f"/api/v1/bots/{bot['id']}/test",
            json={"message": "How much is the Pro plan?"},
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reply"] == "The Pro plan costs 49 USD per month."
    assert data["tokens_used"] == 32
    assert data["latency_ms"] >= 0

    messages = mocked.await_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert "Context information" in messages[0]["content"]
    assert "49 USD" in messages[0]["content"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_test_bot_without_knowledge_uses_default_prompt(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client, system_prompt=None)

    with patch.object(ai_service, "complete", new=AsyncMock(return_value={
        "content": "Hello!", "tokens_used": 5,
    })) as mocked:
        resp = await client.post(
            f"/api/v1/bots/{bot['id']}/test",
            json={"message": "Hi"},
        )
    assert resp.status_code == 200, resp.text
    messages = mocked.await_args.kwargs["messages"]
    assert messages[0]["content"] == "You are a helpful AI assistant."
    assert "Context information" not in messages[0]["content"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_test_bot_unknown_returns_404(auth_client):
    client, _db, _user, _headers, _refresh = auth_client
    resp = await client.post(
        f"/api/v1/bots/{'00000000-0000-0000-0000-000000000000'}/test",
        json={"message": "Hi"},
    )
    assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_deploy_activates_channels(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)

    resp = await client.post(
        f"/api/v1/bots/{bot['id']}/deploy",
        json={"channels": ["web", "slack"]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["bot_id"] == bot["id"]
    assert data["deployment_url"].startswith("https://bots.omniai.app/")
    assert data["channels"]["web"] == {"enabled": True, "config": {}}
    assert data["channels"]["slack"] == {"enabled": True, "config": {}}

    stored = db.find(Bot, id=uuid.UUID(bot["id"]))
    assert stored.is_active is True
    assert stored.deployment_url == data["deployment_url"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_embed_code_contains_widget_config(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)

    resp = await client.post(
        f"/api/v1/bots/{bot['id']}/embed",
        json={"theme": {"primary": "#FF5733", "position": "left", "greeting": "Hi there!"}},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert bot["id"] in data["embed_code"]
    assert "#FF5733" in data["embed_code"]
    assert data["widget_url"] == f"https://bots.omniai.app/embed/{bot['id']}"
    assert data["config"]["position"] == "left"
    assert data["config"]["greeting"] == "Hi there!"

    stored = db.find(Bot, id=uuid.UUID(bot["id"]))
    assert stored.widget_config["primary_color"] == "#FF5733"


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATIONS + ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_messages_and_analytics(auth_client):
    client, db, user, _headers, _refresh = auth_client
    bot = await _create_bot(client)
    bot_id = uuid.UUID(bot["id"])

    from app.services.bot_service import BotService
    service = BotService(db)
    conv1 = await service.create_conversation(bot_id, session_id="sess-a", channel="web")
    await service.add_message(conv1.id, "user", "What is the refund policy?", tokens_used=5, latency_ms=120)
    await service.add_message(conv1.id, "bot", "Full refunds within 30 days.", tokens_used=40, latency_ms=900)
    await service.create_conversation(bot_id, session_id="sess-b", channel="slack")

    conversations = (await client.get(f"/api/v1/bots/{bot_id}/conversations")).json()
    assert len(conversations) == 2

    messages = (await client.get(
        f"/api/v1/bots/{bot_id}/conversations/{conv1.id}/messages"
    )).json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "bot"

    analytics = (await client.get(f"/api/v1/bots/{bot_id}/analytics")).json()
    assert analytics["total_conversations"] == 2
    assert isinstance(analytics["total_messages"], int)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_messages_ownership(auth_client):
    client, db, _user, _headers, _refresh = auth_client
    bot = await _create_bot(client)
    bot_id = uuid.UUID(bot["id"])

    from app.services.bot_service import BotService
    conv = await BotService(db).create_conversation(bot_id, session_id="sess", channel="web")

    other = await client.get(f"/api/v1/bots/{bot_id}/conversations/{uuid.uuid4()}/messages")
    assert other.status_code == 404, "Unknown conversation must 404"

    stranger = await client.get(f"/api/v1/bots/{uuid.uuid4()}/conversations/{conv.id}/messages")
    assert stranger.status_code == 404, "Foreign bot must 404"
