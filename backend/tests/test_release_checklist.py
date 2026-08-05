"""Release checklist tests.

Locks down the operational prerequisites for a v6.0.0 release:
a single, resolvable alembic migration chain; the presence of required
environment variables in `.env.example`; version consistency between
settings and the OpenAPI doc; and functional liveness/readiness probes.
"""
import os

import pytest

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import settings
from app.main import app

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.unit
def test_migration_graph_is_single_head():
    cfg = Config()
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"expected exactly one head, got {heads}"
    # every revision's down_revision must resolve (no dangling references)
    for rev in script.walk_revisions():
        if rev.down_revision:
            assert script.get_revision(rev.down_revision), \
                f"{rev.revision} references missing down_revision {rev.down_revision}"


@pytest.mark.unit
def test_migration_tables_match_model_metadata():
    """Tables created by migrations must exist in the ORM metadata (no drift)."""
    import re
    import app.models  # noqa: F401  (registers all models on Base.metadata)
    from app.models.base import Base

    versions_dir = os.path.join(BACKEND_DIR, "alembic", "versions")
    migrated = set()
    for fname in os.listdir(versions_dir):
        if not fname.endswith(".py"):
            continue
        src = open(os.path.join(versions_dir, fname), encoding="utf-8").read()
        migrated |= set(re.findall(r'op\.create_table\(\s*["\']([^"\']+)', src))
    assert migrated, "no create_table ops found in migrations"

    model_tables = set(Base.metadata.tables.keys())
    missing = sorted(t for t in migrated if t not in model_tables)
    assert not missing, f"migration tables missing from ORM metadata: {missing}"


@pytest.mark.unit
def test_env_example_documents_required_vars():
    example_path = os.path.join(BACKEND_DIR, ".env.example")
    assert os.path.exists(example_path)
    content = open(example_path, encoding="utf-8").read().upper()
    for var in ("JWT_SECRET", "DATABASE_URL", "DATABASE_URL_SYNC", "REDIS_URL",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FRONTEND_URL"):
        assert var in content, f".env.example is missing {var}"


@pytest.mark.unit
def test_env_example_covers_all_settings_fields():
    """Every Settings field must be documented in .env.example."""
    example = open(os.path.join(BACKEND_DIR, ".env.example"), encoding="utf-8").read()
    missing = [
        name for name in sorted(settings.model_fields)
        if name.upper() not in example.upper()
    ]
    assert not missing, f"settings fields missing from .env.example: {missing}"


@pytest.mark.unit
def test_version_consistency_between_settings_and_openapi():
    assert app.openapi()["info"]["version"] == settings.app_version


@pytest.mark.unit
def test_debug_guardrail_blocks_production_with_debug():
    from app.core.config import Settings

    with pytest.raises(ValueError, match="DEBUG must be False"):
        Settings(
            _env_file=None,
            environment="production",
            debug=True,
            jwt_secret="x" * 32,
        )


@pytest.mark.unit
def test_debug_guardrail_blocks_staging_with_debug():
    from app.core.config import Settings

    with pytest.raises(ValueError, match="DEBUG must be False"):
        Settings(
            _env_file=None,
            environment="staging",
            debug=True,
            jwt_secret="x" * 32,
        )


@pytest.mark.unit
def test_debug_guardrail_allows_development_with_debug():
    from app.core.config import Settings

    s = Settings(_env_file=None, environment="development", debug=True)
    assert s.debug is True


@pytest.mark.unit
def test_debug_guardrail_allows_production_without_debug():
    from app.core.config import Settings

    s = Settings(
        _env_file=None,
        environment="production",
        debug=False,
        jwt_secret="x" * 32,
    )
    assert s.environment == "production"


@pytest.mark.unit
def test_observability_endpoints_registered():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/health" in paths
    assert "/live" in paths
    assert "/ready" in paths


@pytest.mark.integration
@pytest.mark.asyncio
async def test_liveness_probe_responds(stateful_client):
    client, _db = stateful_client
    resp = await client.get("/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["version"] == settings.app_version
    assert isinstance(body["checks"], list)
    assert any(c["name"] == "app" and c["healthy"] for c in body["checks"])
