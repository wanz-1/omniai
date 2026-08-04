# OmniAI Environment Configuration

### 1. Overview

All runtime configuration is supplied via environment variables, sourced from `.env` (never committed) and modeled on `.env.example` (committed, safe placeholder values only).

**Golden rule:** `.env.example` defaults are dev-only conveniences. Every value must be reviewed and, in most cases, replaced before an environment is promoted past local development.

### 2. Environment Tiers

| Tier | `ENVIRONMENT` value | Who manages secrets | Source of `.env` |
|---|---|---|---|
| Local dev | `development` | Individual developer | Copied from `.env.example`, edited locally |
| Staging | `staging` | Platform/ops team | Secrets manager (not a flat file) |
| Production | `production` | Platform/ops team | Secrets manager (not a flat file) |

Secrets manager here refers to whatever the deployment target uses (e.g. Docker secrets, k8s Secrets, Vault, cloud provider secret store) — the requirement is that staging/production never load credentials from a plaintext `.env` file on disk.

### 3. Required Variables (by service)

| Variable | Service | Dev default | Production requirement |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL (async, app runtime) | local Postgres | Managed/secured DB; credentials rotated, not the dev defaults |
| `DATABASE_URL_SYNC` | PostgreSQL (Alembic migrations) | local Postgres | Same DB as above, sync driver |
| `REDIS_URL` | Redis cache | local Redis | Managed Redis, auth enabled, TLS if available |
| `CELERY_BROKER_URL` | Celery broker (Redis DB 1) | local Redis | Managed Redis, isolated DB index |
| `CELERY_RESULT_BACKEND` | Celery results (Redis DB 2) | local Redis | Managed Redis, isolated DB index |
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION` | MinIO/S3 | `minioadmin`/`minioadmin` | Real S3 or hardened MinIO; least-privilege IAM keys, not root creds |
| `JWT_SECRET` | Auth | placeholder string | Cryptographically random (≥256-bit), stored in secrets manager |
| `JWT_ALGORITHM` | Auth | `HS256` | Confirm against threat model; consider RS256 if key rotation needed |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | Auth | `30` / `7` | Reviewed, not just inherited from dev |
| AI provider keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`) | AI providers | empty | At least one populated; leave unused ones empty — don't set fake/placeholder values |
| `OLLAMA_BASE_URL`, `VLLM_BASE_URL` | Local/self-hosted AI | localhost / empty | Only set if self-hosting models; otherwise leave empty |
| `QDRANT_URL` | Vector DB | local Qdrant | Managed/secured instance, network-restricted |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Billing | empty | Required if billing enabled; webhook secret must match the configured endpoint exactly |
| `OAUTH_GOOGLE_*`, `OAUTH_GITHUB_*`, `OAUTH_MICROSOFT_*`, `OAUTH_APPLE_*` | OAuth2 | empty | Set only for providers actually enabled; redirect URIs must match `FRONTEND_URL` |
| `SENTRY_DSN` | Observability | empty | Set in staging/production for error visibility |
| `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS` | API | `true` / `100` / `60` | Tune to expected load; don't disable in production |
| `ENVIRONMENT` | Backend | `development` | Must accurately reflect the deployed tier |
| `DEBUG` | Backend | `true` | **Must be `false`** — see §4 |
| `LOG_LEVEL` | Backend | `INFO` | `INFO` or stricter; never `DEBUG` level in production |
| `FRONTEND_URL` | Backend | `http://localhost:3000` | Real deployed frontend origin (drives CORS + OAuth redirects) |

### 4. DEBUG Requirement (pre-GA, blocking)

**Rule:** `DEBUG=false` is mandatory whenever `ENVIRONMENT` is `staging` or `production`. `DEBUG=true` is permitted only when `ENVIRONMENT=development`.

**Why it matters:** debug mode typically exposes stack traces, auto-reload, and verbose error detail in API responses — all of which leak internals and are unacceptable outside local dev.

**Scope of this change:** documentation/config only. No code was modified in this pass — specifically, no startup guard was added to reject `DEBUG=true` combined with a non-dev `ENVIRONMENT`.

**Validation:** deferred to an operator running the pre-GA infra checklist on a production-like host. Not retried or simulated in this environment, per prior agreement.

**Sign-off checklist (operator, before GA):**
- [ ] `DEBUG=false` confirmed in production secrets manager
- [ ] `DEBUG=false` confirmed in staging secrets manager
- [ ] `ENVIRONMENT` correctly set (`staging`/`production`) in each respective environment
- [ ] No `.env` file containing `DEBUG=true` is reachable from a staging/production container image or deploy artifact

**Suggested follow-up (out of scope here):** add a startup assertion (e.g. in `app/core/config.py`) that raises if `DEBUG` is true while `ENVIRONMENT != "development"`, turning this from a checklist item into a self-enforcing guard.

### 5. Secrets Hygiene

- Never commit a populated `.env` file. Only `.env.example` with placeholder/empty values belongs in version control.
- Rotate `JWT_SECRET`, database credentials, and any leaked or dev-shared keys before first production use.
- Treat every "empty by default" key (AI providers, Stripe, OAuth, Sentry) as opt-in — populate only what's actually enabled for that environment, to minimize the credential surface.

### 6. Change Log
| Date | Change | Author |
|---|---|---|
| 2026-08-04 | Documented DEBUG requirement (pre-GA, docs/config only) | _fill in_ |
