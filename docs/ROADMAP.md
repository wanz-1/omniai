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

## v6.1

- **DB-001: Migration ownership** — make Alembic the authoritative source for the full schema.
  - Milestones:
    1. Inventory tables currently created via `create_all()` (227 ORM tables; 7 migration-tracked).
    2. Generate migration equivalents.
    3. Validate upgrade/downgrade paths.
    4. Remove runtime schema creation once migration parity is complete.
  - **Success criteria:** migration graph covers all tables; downgrade path clean; `create_all()` removal verified by tests.

## v7.0

- **Mobile App Builder** — new capability (resume feature development after release hardening).
  - **Design phase deliverables:** architecture, API contracts, data model, security considerations, test strategy — design proposal reviewed before implementation.
  - **Implementation milestones:** schema → services → API routes → tests → integration.

## Future Ideas

- Exploratory only, not yet committed: Business & Finance Assistant, Data Analytics, Automation Engine, AI Agent Builder, Design Studio.
