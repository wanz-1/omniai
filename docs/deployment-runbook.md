# OmniAI V6.0.0-rc1 — Deployment Runbook

Operational procedures for deploying OmniAI V6.0.0-rc1. Run every step in staging
first, then repeat for production. Escalate to rollback (`docs/rollback-procedure.md`)
if any gate fails.

## 1. Pre-Deploy Verification (gate 1)

```bash
cd backend
python -m pytest tests/ -q --no-header -p no:cacheprovider -W ignore
```

- Expect: **418 passed, 0 failed**, coverage report ≥ 70%
- Also run the focused suites that gate the release:
  - `tests/test_release_checklist.py` — migration chain, env parity, health probes
  - `tests/test_openapi_contract.py` — OpenAPI structural contract
  - `tests/test_security_regression.py` — prompt guard + tenant isolation

## 2. Environment Configuration (gate 2)

```bash
cp .env.example .env   # then fill real values
```

Required for startup:

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | asyncpg URL, e.g. `postgresql+asyncpg://user:pass@host:5432/omniai` |
| `DATABASE_URL_SYNC` | psycopg2 URL for tooling |
| `REDIS_URL` | e.g. `redis://redis:6379/0` |
| `JWT_SECRET` | random ≥ 32 bytes (`openssl rand -hex 32`) |
| `FRONTEND_URL` | CORS origin |
| `DEBUG` | **MUST be `false` in production/staging.** `ENVIRONMENT=production` does not force this; `debug=true` enables SQLAlchemy `echo` (SQL query logging) and verbose debug logging |
| One AI provider key | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` / `GOOGLE_GEMINI_API_KEY` / `DEEPSEEK_API_KEY` / `MISTRAL_API_KEY` / `OPENROUTER_API_KEY` |

Verify parity: every key in `Settings` is documented in `.env.example`
(locked by `test_env_example_covers_all_settings_fields`).

Full environment matrix (tiers, per-service requirements, secrets hygiene,
DEBUG sign-off): see `docs/environment-configuration.md`.

## 3. Database Migration (gate 3)

Alembic now executes from any working directory (`script_location = %(here)s`).

```bash
cd backend
# offline sanity check (no DB connection required)
alembic upgrade head --sql > /tmp/migration_plan.sql

# apply
alembic upgrade head
alembic current          # expect: 0002
```

Notes:
- Single migration head `0002`; tables tracked: `user_sessions`,
  `subscription_plans`, `subscriptions`, `invoices`,
  `integration_connections`, `marketplace_items`, `marketplace_purchases`.
- Remaining schema is created idempotently by `Base.metadata.create_all` at
  application startup (tracked as future tech debt, ticket DB-001).
- Migration↔model parity is enforced by
  `test_migration_tables_match_model_metadata`.

## 4. Application Startup

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Startup log events to confirm healthy boot:
- `app_startup` ("Starting OmniAI backend")
- `db_tables_created` ("Database tables created/verified")

## 5. Health Gates (gate 4) — verify after each deploy

| Endpoint | Expected | Semantics |
|----------|----------|-----------|
| `GET /live` | **200** `status: healthy` | process alive, no dependencies touched |
| `GET /ready` | **200** when dependencies up; **503** when DB/Redis/storage/ai_router unavailable | readiness gate for orchestrators |
| `GET /health` | **200** with per-component `checks` | diagnostic overview — evaluate component status individually |

Orchestrators: use `/live` for restart decisions, `/ready` for traffic gating.
Probes must treat 503 on `/ready` as normal during dependency startup.

## 6. Observability Verification (gate 5)

- `GET /metrics` → 200; confirm `http_requests_total` is exposed (Prometheus).
- Structured JSON logs on stdout with `request_id` on every request
  (`Request started` / `Request completed` events with latency).
- Error responses are structured:
  ```json
  {"error": {"code": "...", "message": "...", "correlation_id": "...", "timestamp": "..."}}
  ```
- If `SENTRY_DSN` is set, errors are also forwarded with release `6.0.0`.

## 7. Smoke Test Checklist (gate 6)

- [ ] `POST /api/v1/auth/register` + `/login` issue tokens
- [ ] `/api/v1/agents` CRUD round-trip
- [ ] `POST /api/v1/v6/governance/decisions` returns typed `AIDecisionResponse`
- [ ] `GET /api/v1/v6/governance/dashboard` returns typed counts
- [ ] `POST /api/v1/vision/scan` returns typed `ScanDocumentResponse`
- [ ] `POST /api/v1/v4/ecosystem/builder/apps/{id}/generate` → 200 (or 404 for unknown app — never 500)
- [ ] Marketplace publish + purchase flow
- [ ] Tenant isolation spot check: user A cannot read user B's documents (404)

## 8. Container Deployment

```bash
docker build -t omniai/backend:6.0.0-rc1 -f backend/Dockerfile backend/
# run with docker-compose (local/dev)
docker compose -f deploy/docker-compose.yml up -d
```

Kubernetes manifests live in `deploy/kubernetes/` (refer to `infra/` for
Terraform provisioning and `docs/deployment-guide.md` for the full topology).

## 9. Post-Deploy Verification

- [ ] `/live` + `/ready` 200 for 15+ minutes
- [ ] No 5xx in structured logs (`request_end` events with `status_code` 5xx)
- [ ] Prometheus error-rate alert baseline recorded
- [ ] `alembic current` still reports head after restarts
