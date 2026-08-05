# OmniAI V6.0.0 — Release Candidate 1 (v6.0.0-rc1)

**Status:** RC APPROVED — pending GA readiness review
**Freeze:** Code frozen at RC approval; no feature work before GA
**Validation baseline:** 418 functional tests passing, 185 security tests passing, 70% statement coverage

## What's New in V6

### AI Governance (V6)
- Prompt registry with versioned templates and lifecycle states (draft → production → archived)
- Evaluation engine with accuracy/safety/citation scoring and pass/fail gates
- Hallucination detection with claim-level evidence tracking
- Model monitoring with per-model metrics, quality reports, and latency/cost aggregates
- Human approval workflows for high-risk decisions (create / approve / reject)
- AI decision logging with risk levels and review states
- User feedback capture linked to decisions and models

### Subscription & Marketplace
- Subscription plans, user subscriptions, and invoice lifecycle
- Marketplace item publishing, purchasing, reviews with rating aggregation
- Creator profiles, dashboards, and 30-day analytics
- Plugin registry and AI-driven verification workflows
- Enterprise visibility rules (public / enterprise-scoped listings)

### Integration Layer
- Integration connections with sync history and status tracking
- Sync records with processed/failed counts

## Release Hardening (Sprint 6)

### API Contract Hardening
- Coverage raised from 64% to 70% (18,081 statements)
- OpenAPI contract validation suite added: 501 paths / 624 operations verified
- All success responses now reference typed Pydantic schemas; untyped `response_model=dict` responses eliminated (8 endpoints typed: vision scan, ecosystem app generation, governance reviews/feedback/dashboard)
- Regression protection: `test_no_untyped_success_responses` guards the entire API against untyped response drift
- UUID serialization consistency verified across all typed responses

### Defects Fixed During Hardening
| # | Defect | Fix |
|---|--------|-----|
| 1 | `agent_communication.send_message` crashed with `NameError: meta_data` (undefined param) — every message send failed | `meta_data=metadata or {}` |
| 2 | Analytics endpoint referenced nonexistent `satisfaction_score` column | `avg_satisfaction` |
| 3 | `CodeProjectResponse.files` typed `dict` but routes store a list → ResponseValidationError | `Optional[list[dict]]` |
| 4 | Ecosystem app generate route called nonexistent `generate_app_from_prompt` service method (hidden 500) | `generate_from_prompt(app_id=...)` + 404 for missing apps |
| 5 | Alembic migration `0002` referenced missing base revision `0001` → broken revision graph | `down_revision = None` (now single head `0002`) |
| 6 | `alembic.ini` `script_location = .` broke execution from repo root | `%(here)s` — works from any CWD |

### Release Checklist (automated)
- `tests/test_release_checklist.py` — migration graph single-head, migration↔model parity, env-var documentation parity, version consistency, health probes
- `.env.example` documents all 56 Settings fields
- `coverage.xml` refreshed at 70%

## Security Validation Summary (RC-2)
- Prompt injection / guard pipeline: green
- SSRF guard: blocks private ranges, cloud metadata, localhost, internal hostnames, non-http schemes
- Authorization & tenant isolation: green across bots, agents, connectors, documents, governance
- Data protection (PII redaction): green

See `docs/security-validation-summary.md` for the full breakdown.

## Known Accepted Observations (no release blockers)
1. `/health` returns 200 with component-level detail even when DB/Redis are unreachable — consumers should evaluate `checks`; use `/ready` for orchestration gates.
2. Alembic controls the 7 sprint-managed tables; the remaining schema is created idempotently via `Base.metadata.create_all` at startup. **Ticket DB-001:** move all tables under Alembic ownership.
3. AI features require at least one provider API key (OpenAI, Anthropic, Gemini, DeepSeek, Mistral, or OpenRouter); no provider fallback UI exists yet.
4. `ENVIRONMENT=production` does not force `DEBUG=false` — production deployments must set `DEBUG=false` explicitly to disable SQLAlchemy echo and debug logging (documented in `.env.example` and the deployment runbook).

## Operational Entry Points
- `/live` — process liveness (no dependencies)
- `/ready` — dependency readiness (503 when DB/Redis/storage/ai_router unavailable)
- `/health` — diagnostic overview with per-component checks
- `/metrics` — Prometheus metrics (HTTP request counters, latency histograms)
- `/docs` — OpenAPI interactive documentation (version 6.0.0)

## GA Readiness Checklist
- [x] Baseline commit + tag `v6.0.0-rc1` (baseline `49fac70`; hardening shipped on `master` after — see `docs/v6.0.1-hardening-report.md`)
- [x] Release notes reviewed
- [ ] Deployment runbook executed in staging (`docs/deployment-runbook.md`)
- [ ] Rollback procedure dry-run (`docs/rollback-procedure.md`)
- [x] Security validation summary distributed (`docs/security-validation-summary.md`)
- [ ] GA readiness review

> **Post-RC hardening (v6.0.1):** AI-service fixes, Stripe webhook rewrite, DEBUG guardrail, API auth closure, real Celery tasks and agent tools, Docker/CI hardening, and live frontend analytics — validation now 422 tests / 68.79% coverage. See `docs/v6.0.1-hardening-report.md`.
