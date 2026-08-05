# OmniAI V6.0.0-rc1 — Rollback Procedure

Triggers (any of):
- Error rate above threshold (e.g., 5xx > 1% over 5 minutes) sustained 10+ minutes
- `/ready` returning 503 for 5+ consecutive minutes after dependency startup window
- Data integrity regression reported through support (duplicate/leaked records)
- Security incident requiring immediate take-down

Rollback order: **stop traffic → downgrade schema → restore data → redeploy → verify.**

## 1. Stop Traffic

Orchestrator (Kubernetes): scale replicas to 0.

```bash
kubectl scale deployment omniai-backend --replicas=0
```

Docker Compose: `docker compose down` or remove the backend container from the
load balancer.

## 2. Determine Rollback Scope

| Scenario | Action |
|----------|--------|
| Bad code, no schema change | redeploy previous image only (skip DB steps) |
| Bad code + schema change applied | full rollback: schema downgrade + data restore |
| Schema change not yet applied | just redeploy previous image |

Check whether the migration was applied: `alembic current` (expect `0002` if V6
migration ran).

## 3. Database Rollback

### Schema downgrade (verified path)

```bash
cd backend
alembic downgrade 0002:base --sql   # inspect plan first
alembic downgrade 0002:base         # execute
alembic current                     # expect: no revision (base)
```

This drops the V6 tables (`user_sessions`, `subscription_plans`,
`subscriptions`, `invoices`, `integration_connections`, `marketplace_items`,
`marketplace_purchases`) in a single transaction.

### Data restore (if downgrade is insufficient)

1. Restore the most recent pre-release `pg_dump`:
   ```bash
   pg_restore --clean --if-exists -d omniai /backups/omniai_pre_rc1.dump
   ```
2. Re-apply schema downgrade from step above after restore.
3. Verify row counts and recent records on core tables (`users`, `agents`,
   `documents`, `organizations`) before reopening traffic.

> Note: the schema is fully owned by Alembic (DB-001). A `downgrade base`
> (or downgrade to a specific revision) drops all migration-tracked tables in
> reverse dependency order, including the `0003` adopted tables. Schema
> downgrades are destructive — always restore from `pg_dump` per step above and
> verify row counts before reopening traffic.

## 4. Redeploy Previous Version

```bash
# rebuild from the last known-good tag/image
docker build -t omniai/backend:<previous> -f backend/Dockerfile backend/
```

Previous image tag reference: `omniai/backend:<last-green>` (see registry
history; GA checklist should record the last-green image per release).

## 5. Verify Rollback

- [ ] `/live` 200
- [ ] `/ready` 200 with DB/Redis reported healthy
- [ ] Smoke tests from `docs/deployment-runbook.md` §7 pass
- [ ] Error rate back to baseline in Prometheus
- [ ] `alembic current` matches pre-release revision
- [ ] A representative V5-era endpoint (e.g., documents list) returns data

## 6. Post-Incident

- Preserve structured logs (correlation IDs) for the incident window
- File a defect ticket with reproduction steps; do not hotfix during freeze
- Update the release notes with the regression
- Decide with the release owner whether to cut `v6.0.0-rc2` or proceed to GA

## Rollback Team Contact Path

1. On-call engineer executes §1–§5
2. Release owner notified within 15 minutes
3. QA re-runs the pre-deploy suite before any redeploy of rc1
