# OmniAI V6.0.1 — Production Hardening Release

**Status:** RELEASE PACKAGE — tag after staging validation
**Baseline:** `v6.0.0-rc1` (freeze commit `49fac70`)
**Includes:** hardening commits `1dbec8d`, `c7e0c4e`, `b5f7d5f`, `b807f85`, `db95371` on `master`

## What's In This Release

- **Security hardening completed** — DEBUG startup guardrail (production/staging refuse to boot with `DEBUG=True`), API auth enforced on v5 connector/collaboration and global infrastructure route groups, unknown/cross-tenant resources return 404.
- **SSRF protection integrated** — validated outbound-URL guard (`app/core/ssrf.py`) used by connector webhooks; private-range/cloud-metadata/localhost blocking remains green.
- **Security middleware validated** — security headers, request correlation, request logging, and rate-limiting middleware in `app/core/middleware.py` are covered and active.
- **CI container scanning added** — Trivy filesystem scans of `backend/` and `frontend/` (blocking on CRITICAL) plus IaC config scan of `infra/`.
- **AI + payments reliability** — provider-response crash/leak fixes with string-prompt compat shim; Stripe webhook signature handling and checkout flow rewritten.
- **Async workload implementation** — real Celery task bodies (bot training, document processing, website generation) with durable session handling; agent tool executor.
- **Frontend live analytics** — bot daily-activity bar chart and agent daily-usage/task-outcome charts backed by new `daily_activity` API payload; pre-existing broken production build fixed.

## Validation

- **422 tests passing** (was 418 at RC)
- **68.79% statement coverage** (CI gate `--cov-fail-under=30`)
- **Frontend build / typecheck / lint passing** (0 errors; 22 pre-existing non-blocking warnings)
- **Lint gate clean:** `ruff check app/ tests/ --select F`
- **Migration gate:** Alembic single-head graph (`0002`), offline `upgrade head --sql` generates valid DDL
- **Phase 14 validation completed** — see `docs/v6.0.1-hardening-report.md`

## Release Gate

- [ ] Staging: `alembic upgrade head` applies cleanly
- [ ] Staging: `GET /ready` → HTTP 200 with live dependencies
- [ ] Staging: live smoke suite (auth, core APIs, AI pipeline, document processing, webhooks/connectors, background jobs, audit logging, tenant isolation) and frontend production deploy
- [ ] Tag `v6.0.1` and publish release notes

## Deferred (planned future work, not in this release)

- v7 — Mobile application builder
- Provider fallback UI improvements
- Style-only Ruff cleanup

## Post-release (v6.1, branch `feature/v6.1-migration-ownership`)

- Alembic migration ownership completed: migration `0003` adopts the remaining 220 tables (Alembic owns all 227), `Base.metadata.create_all` removed from startup, CI `backend-migrate` job validates upgrade/parity/downgrade on real Postgres, and a phantom `tenants` FK that blocked real-Postgres boot was fixed.
