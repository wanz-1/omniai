"""Failure-path and reliability tests.

Covers external AI provider failure handling (timeouts, rate limits,
overloads, all-providers-down), API failure paths (invalid UUIDs, unknown
resources, malformed payloads, forbidden access), and small core services
(storage, rate limiting, model routing, knowledge permissions).
"""
import uuid
from pathlib import Path

import pytest

from app.core.exceptions import AIServiceError, ProviderOverloadedError, ProviderRateLimitError
from app.core.rate_limit import InMemoryRateLimiter
from app.models.user import User
from app.services.ai_model_router import AIModelRouter
from app.services.ai_service import AIService
from app.services.knowledge_intelligence.permission_service import PermissionService
from app.services.storage_service import StorageService

AGENTS = "/api/v1/agents"
BOTS = "/api/v1/bots"
CONNECTOR = "/api/v1/v5/connector"


# ═══════════════════════════════════════════════════════════════════════════
# AI PROVIDER FAILURE PATHS
# ═══════════════════════════════════════════════════════════════════════════

class FakeProvider:
    def __init__(self, name, result=None, error=None):
        self.name = name
        self.result = result
        self.error = error

    async def chat_completion(self, **kwargs):
        if self.error:
            raise self.error
        return self.result


def _service_with_providers(*providers):
    svc = AIService()
    svc.providers = {p.name: p for p in providers}
    return svc


@pytest.mark.unit
async def test_no_providers_raises():
    svc = _service_with_providers()
    with pytest.raises(AIServiceError, match="No AI provider"):
        await svc.complete([{"role": "user", "content": "hi"}])


@pytest.mark.unit
async def test_all_providers_fail_raises_with_last_error():
    svc = _service_with_providers(
        FakeProvider("openai", error=TimeoutError("gateway timeout")),
        FakeProvider("anthropic", error=ProviderRateLimitError()),
    )
    with pytest.raises(AIServiceError, match="All AI providers failed"):
        await svc.complete([{"role": "user", "content": "hi"}])


@pytest.mark.unit
async def test_provider_overload_falls_back_to_next():
    fallback = FakeProvider("anthropic", result={"content": "ok", "model": "claude"})
    svc = _service_with_providers(
        FakeProvider("openai", error=ProviderOverloadedError()),
        fallback,
    )
    result = await svc.complete([{"role": "user", "content": "hi"}])
    assert result["content"] == "ok"


@pytest.mark.unit
async def test_timeout_falls_back_to_next():
    fallback = FakeProvider("deepseek", result={"content": "retried"})
    svc = _service_with_providers(
        FakeProvider("openai", error=TimeoutError("slow")),
        FakeProvider("mistral", error=ConnectionError("refused")),
        fallback,
    )
    result = await svc.complete([{"role": "user", "content": "hi"}], enable_retry=False)
    assert result["content"] == "retried"


@pytest.mark.unit
async def test_unexpected_exception_falls_back():
    fallback = FakeProvider("openai", result={"content": "recovered"})
    svc = _service_with_providers(
        FakeProvider("anthropic", error=RuntimeError("boom")),
        fallback,
    )
    result = await svc.complete([{"role": "user", "content": "hi"}])
    assert result["content"] == "recovered"


@pytest.mark.unit
async def test_preferred_provider_used_first():
    preferred = FakeProvider("deepseek", result={"content": "from deepseek"})
    svc = _service_with_providers(
        FakeProvider("openai", result={"content": "from openai"}),
        preferred,
    )
    result = await svc.complete([{"role": "user", "content": "hi"}], provider="deepseek")
    assert result["content"] == "from deepseek"


@pytest.mark.unit
async def test_stream_no_providers_raises():
    svc = _service_with_providers()
    with pytest.raises(AIServiceError, match="No AI provider"):
        async for _ in svc.complete_stream([{"role": "user", "content": "hi"}]):
            pass


@pytest.mark.unit
async def test_stream_fallback_on_failure():
    class StreamProvider(FakeProvider):
        async def chat_completion(self, **kwargs):
            if self.error:
                raise self.error
            async def gen():
                yield "tok1 "
                yield "tok2"
            return gen()

    svc = _service_with_providers(
        StreamProvider("openai", error=TimeoutError("x")),
        StreamProvider("anthropic"),
    )
    chunks = []
    async for chunk in svc.complete_stream([{"role": "user", "content": "hi"}], enable_metrics=False):
        chunks.append(chunk)
    assert "".join(chunks) == "tok1 tok2"


# ═══════════════════════════════════════════════════════════════════════════
# API FAILURE PATHS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_uuids_rejected_with_422(stateful_client):
    client, _db = stateful_client
    user = User(email="failpath@example.com", display_name="Fail Path", is_verified=True)
    _db.add(user)

    for path in (
        f"{AGENTS}/not-a-uuid",
        f"{BOTS}/not-a-uuid",
        f"{CONNECTOR}/integrations/not-a-uuid",
    ):
        resp = await client.get(path)
        assert resp.status_code == 422, f"{path}: {resp.status_code}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unknown_resources_return_404(stateful_client):
    client, _db = stateful_client
    user = User(email="missing@example.com", display_name="Missing", is_verified=True)
    _db.add(user)
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: user

    bogus = uuid.uuid4()
    assert (await client.get(f"{AGENTS}/{bogus}")).status_code == 404
    assert (await client.get(f"{BOTS}/{bogus}")).status_code == 404
    assert (await client.get(f"{CONNECTOR}/integrations/{bogus}")).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_payloads_rejected(stateful_client):
    client, _db = stateful_client
    user = User(email="malformed@example.com", display_name="Malformed", is_verified=True)
    _db.add(user)
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    main_mod.app.dependency_overrides[get_current_user] = lambda: user

    assert (await client.post(f"{AGENTS}", json={"name": 123})).status_code == 422
    assert (await client.post(f"{BOTS}", json={"name": ""})).status_code == 422
    assert (await client.post(f"{CONNECTOR}/install", json={})).status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_user_access_forbidden(stateful_client):
    client, db = stateful_client
    import app.main as main_mod
    from app.core.dependencies import get_current_user
    owner = User(email="own-fp@example.com", display_name="Owner", is_verified=True)
    db.add(owner)
    main_mod.app.dependency_overrides[get_current_user] = lambda: owner

    created = await client.post(f"{AGENTS}", json={
        "name": "Owner Agent", "role": "research_analyst",
        "description": "d", "system_prompt": "p",
        "skills": [], "tools": [],
    })
    assert created.status_code == 200, created.text
    agent_id = created.json()["id"]

    intruder = User(email="intruder-fp@example.com", display_name="Intruder", is_verified=True)
    db.add(intruder)
    main_mod.app.dependency_overrides[get_current_user] = lambda: intruder

    assert (await client.get(f"{AGENTS}/{agent_id}")).status_code == 404
    assert (await client.put(f"{AGENTS}/{agent_id}", json={"name": "x"})).status_code == 404
    assert (await client.delete(f"{AGENTS}/{agent_id}")).status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# STORAGE SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
async def test_storage_save_read_delete(tmp_path):
    svc = StorageService()
    svc.base_path = tmp_path

    saved = await svc.save_file("docs/a.txt", b"hello")
    assert saved.startswith(str(tmp_path))
    assert await svc.read_file("docs/a.txt") == b"hello"
    assert await svc.read_file("missing.txt") is None

    assert await svc.delete_file("docs/a.txt") is True
    assert await svc.delete_file("docs/a.txt") is False
    assert await svc.read_file("docs/a.txt") is None


@pytest.mark.unit
async def test_storage_audio_image_and_url(tmp_path):
    svc = StorageService()
    svc.base_path = tmp_path

    audio = await svc.save_audio(b"data", "clip.wav")
    assert Path(audio).parent.name == "audio"
    assert Path(audio).name == "clip.wav"
    image = await svc.save_image(b"img", "pic.png")
    assert Path(image).parent.name == "images"
    assert Path(image).name == "pic.png"
    assert svc.get_url("images/pic.png") == "/uploads/images/pic.png"


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_rate_limiter_allows_up_to_max():
    limiter = InMemoryRateLimiter()
    for _ in range(3):
        assert limiter.check("k1", max_requests=3) is True
    assert limiter.check("k1", max_requests=3) is False


@pytest.mark.unit
def test_rate_limiter_keys_are_independent():
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        limiter.check("busy", max_requests=5)
    assert limiter.check("idle", max_requests=5) is True


@pytest.mark.unit
def test_rate_limiter_window_expiry(monkeypatch):
    limiter = InMemoryRateLimiter()
    monkeypatch.setattr("app.core.rate_limit.time.time", lambda: 1000.0)
    for _ in range(2):
        limiter.check("k2", max_requests=2, window_seconds=10)
    assert limiter.check("k2", max_requests=2, window_seconds=10) is False

    monkeypatch.setattr("app.core.rate_limit.time.time", lambda: 1011.0)
    assert limiter.check("k2", max_requests=2, window_seconds=10) is True


# ═══════════════════════════════════════════════════════════════════════════
# AI MODEL ROUTER
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_model_router_default_strategy():
    router = AIModelRouter()
    choice = router.select_model("chat")
    assert choice["model"] == "gpt-4o"
    assert choice["tier"] == "primary"


@pytest.mark.unit
def test_model_router_prefer_local():
    router = AIModelRouter()
    choice = router.select_model("chat", prefer_local=True)
    assert choice["provider"] == "local"
    assert choice["tier"] == "local"


@pytest.mark.unit
def test_model_router_cost_first_over_budget():
    router = AIModelRouter(strategy="cost_first", cost_budget_monthly=100)
    router.track_usage("gpt-4o", 100, cost=90)
    assert router.monthly_spend == 90
    choice = router.select_model("chat")
    assert choice["tier"] == "cost"
    assert choice["model"] == "gpt-4o-mini"


@pytest.mark.unit
def test_model_router_unknown_capability_defaults_to_chat():
    router = AIModelRouter(strategy="quality_first")
    choice = router.select_model("brain_wave_control")
    assert choice["model"] == "gpt-4o"


@pytest.mark.unit
def test_model_router_available_models_and_voice(monkeypatch):
    import types
    fake_settings = types.SimpleNamespace(VOICE_STT_PROVIDER="whisper", VOICE_TTS_PROVIDER="openai")
    monkeypatch.setattr("app.services.ai_model_router.settings", fake_settings)
    router = AIModelRouter()
    assert "whisper-1" in router.get_available_models("voice_stt")
    voice = router.get_voice_providers()
    assert voice["stt"]["primary"] == "whisper"
    assert voice["tts"]["primary"] == "openai"


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE PERMISSION SERVICE
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
@pytest.mark.asyncio
async def test_permission_grant_check_revoke(stateful_client):
    _client, db = stateful_client
    svc = PermissionService(db)
    doc_id = uuid.uuid4()

    assert await svc.check_permission(doc_id, uuid.uuid4()) is False

    perm = await svc.grant_permission(
        document_id=doc_id, organization_id=uuid.uuid4(),
        principal_type="user", principal_id=uuid.uuid4(),
        permission_level="edit",
    )
    assert perm.permission_level == "edit"

    user_id = perm.principal_id
    assert await svc.check_permission(doc_id, user_id, required_level="view") is True
    assert await svc.check_permission(doc_id, user_id, required_level="edit") is True
    assert await svc.check_permission(doc_id, user_id, required_level="admin") is False

    listed = await svc.list_permissions(doc_id)
    assert len(listed) == 1

    revoked = await svc.revoke_permission(perm.id)
    assert revoked.id == perm.id
    assert await svc.check_permission(doc_id, user_id) is False
    assert len(await svc.list_permissions(doc_id)) == 0

    missing = await svc.revoke_permission(uuid.uuid4())
    assert missing is None
