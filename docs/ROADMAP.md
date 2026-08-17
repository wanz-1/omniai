# OmniAI Roadmap

> This roadmap is subject to change based on production feedback after GA. If real-world usage uncovers critical issues, they take priority over the items below.

## Current Release

- **v6.0.0 (General Availability)** — code frozen; `v6.0.0-rc1` is the immutable RC baseline.
  - **Status:** Functional, security, and contract validation complete. Release docs/config committed.
  - **Remaining operational gate:** operator executes on live staging — `alembic upgrade head`, `/ready` → 200 with live dependencies, live smoke suite + log audit. Then tag `v6.0.0`, push `main` + tag, and publish the 4 release documents (`release-notes-v6.0.0-rc1.md`, `deployment-runbook.md`, `rollback-procedure.md`, `security-validation-summary.md`).

## v6.0.1 — ✅ COMPLETE

- **DEBUG startup guardrail** — detect production mode (e.g. `ENVIRONMENT=production`) and refuse to start if `DEBUG=True`, with a clear startup error explaining how to resolve the configuration. Converts a deployment misconfiguration into a fast, explicit failure.
  - **Status:** implemented and shipped in `1dbec8d`; covered by 4 guardrail tests in `tests/test_release_checklist.py` (blocks production and staging with `DEBUG=true`, allows dev with `DEBUG=true`, allows production with `DEBUG=false`).
- **Hardening release** — AI-service crash/leak fixes, Stripe webhook rewrites, API auth gaps closed, real Celery tasks and agent tools, Docker/CI hardening, and live frontend analytics. See `docs/v6.0.1-hardening-report.md`.

## v6.1 — ✅ COMPLETE

- **DB-001: Migration ownership** — Alembic is now the authoritative source for the full schema.
  - Milestones:
    1. Inventoried tables: 227 ORM tables (7 migration-tracked, 220 via `create_all`).
    2. Generated migration `0003_adopt_remaining_schema.py` — static, idempotent baseline (`IF NOT EXISTS`) covering all 220 tables + 536 indexes + 12 named enum types, with a clean `downgrade`.
    3. Validated offline upgrade (`--sql`) and downgrade paths; CI `backend-migrate` job runs real-Postgres upgrade → parity → downgrade → re-upgrade.
    4. Removed runtime `Base.metadata.create_all` from `app/main.py` startup.
  - **Success criteria met:** migration graph covers all 227 tables; downgrade path clean; `create_all()` removal verified by tests (full-coverage parity test + foreign-key integrity test in `test_release_checklist.py`).
  - **Bug found & fixed during adoption:** `ai_monitoring_events_v4.tenant_id` referenced a nonexistent `tenants` table, which made `Base.metadata.create_all` raise `NoReferencedTableError` at startup (the app could not boot against a real Postgres). The impossible FK was removed (column kept); FK-target integrity is now guarded by a release-checklist test.

## v7.0

- **Mobile App Builder** — new capability (resume feature development after release hardening).
  - **Design phase deliverables:** architecture, API contracts, data model, security considerations, test strategy — design proposal reviewed before implementation.
  - **Implementation milestones:** schema → services → API routes → tests → integration.

## Future Ideas

- Exploratory only, not yet committed: Business & Finance Assistant, Data Analytics, Automation Engine, AI Agent Builder, Design Studio.
