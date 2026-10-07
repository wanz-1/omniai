# OmniAI on Render — Single-URL Deployment Guide

Deploy the entire OmniAI platform (frontend **and** backend) to
[Render](https://render.com) behind **one public URL**, using the
[`render.yaml`](../render.yaml) blueprint in the repo root.

## How it works (single URL)

A single **combined Docker image** (`Dockerfile.render`) runs three processes
inside one container, with `nginx` as the ingress:

```
Browser ──► https://<app>.onrender.com
                │
             nginx (port $PORT, default 10000)
             ├── /api/*, /ws, /live, /ready, /health, /metrics, /docs
             │        └──► uvicorn (FastAPI backend, 127.0.0.1:8000)
             └── everything else
                      └──► next start (Next.js frontend, 127.0.0.1:3000)
```

- The Next.js app is a client-side SPA that calls the backend on the **same
  origin** (`NEXT_PUBLIC_API_URL=/api/v1`), so no CORS issues.
- WebSocket URL is derived from the current origin automatically.

## Topology on Render

| Resource            | Render type   | Runs                                                                 |
|---------------------|---------------|----------------------------------------------------------------------|
| `omniai`            | Web Service   | frontend + backend + nginx (the **public URL**)                      |
| `omniai-celery`     | Worker (opt.) | Celery worker (`RUN_MODE=worker`) for async tasks                    |
| `omniai-postgres`   | Postgres 16   | Managed database                                                     |
| `omniai-redis`      | Key Value     | Cache + Celery broker + results                                      |

## Deploy (Blueprint) — go live

1. **Push this repo** (with all the files below) to GitHub/GitLab/Bitbucket.
2. Render Dashboard → **New + → Blueprint** → select the repo.
3. Render reads `render.yaml`, provisions Postgres + Redis, builds
   `Dockerfile.render`, and deploys `omniai` as a web service.
4. During creation you'll be prompted for the `sync: false` secrets (see
   below). Fill in at least **one AI provider key** and hit create.
5. Render gives you the public URL: `https://omniai-xxxx.onrender.com`.
   That single URL serves both the website and the API.

> Blueprint needs a paid workspace to keep the web service from sleeping.
> `plan: starter` is the default in `render.yaml`.

## Secrets to set (prompted at creation, `sync: false`)

**`omniai` web service**
| Variable | Required | Notes |
|---|---|---|
| `OPENAI_API_KEY` (or Anthropic/Gemini/etc.) | Yes | At least one AI provider for AI features |
| `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET` | No | AWS S3 / Cloudflare R2 object storage |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | No | Billing |
| `SENTRY_DSN` | No | Error tracking |
| `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | No | Agent email tool |
| `VLLM_BASE_URL` | No | Only if self-hosting models |

`JWT_SECRET` is auto-generated (`generateValue: true`).

**`omniai-celery` worker** — same AI/S3/Stripe/Sentry keys so tasks can run.

## Variables wired automatically

- `DATABASE_URL` / `DATABASE_URL_SYNC` — from `omniai-postgres`
  (`connectionString`). The backend normalizes Render's `postgres://` to
  `postgresql+asyncpg://` for the async engine (`app/core/config.py`) and uses
  `psycopg2-binary` for Alembic.
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — from
  `omniai-redis`.
- `NEXT_PUBLIC_API_URL=/api/v1`, `NEXT_PUBLIC_WS_URL=""` (derived) — build with
  same-origin API calls.
- `ENVIRONMENT=production`, `DEBUG=false`, `TRUSTED_PROXIES=["127.0.0.1"]`.

## Files added for this deployment

| File | Purpose |
|---|---|
| `render.yaml` | Blueprint: web + worker + postgres + redis |
| `Dockerfile.render` | Combined image (nginx + Next.js + FastAPI) |
| `deploy/render/nginx.template.conf` | nginx proxy (rendered with `$PORT`) |
| `deploy/render/entrypoint.sh` | Starts uvicorn + next, renders nginx, runs nginx |
| `.dockerignore` | Keeps secrets/local artifacts out of the build |
| `backend/.dockerignore`, `frontend/.dockerignore` | Context hygiene for the standalone images |
| `frontend/src/lib/ws-client.ts` | Derives WS URL from the current origin |

## Post-deploy smoke checks

- `GET https://<app>.onrender.com/live` → 200 `healthy`
- `GET https://<app>.onrender.com/ready` → 200 when DB + Redis are up
- Open `https://<app>.onrender.com` in a browser — the signup/login page loads
- `POST /api/v1/auth/register` + `/login` issue tokens (same origin)

## Notes & pitfalls

- The **web service must bind to Render's `$PORT`** (default 10000). nginx does
  this via `envsubst` in `entrypoint.sh`; the backend/frontend bind internally
  on 127.0.0.1:8000/:3000. The standalone `backend/Dockerfile` and
  `frontend/Dockerfile` were also updated to honor `${PORT:-8000}` /
  `${PORT:-3000}` so they work on Render too.
- `omniai-celery` is optional. Without it, background tasks (document
  processing, bot deployment) don't run. Add it in the same Blueprint.
- To attach a custom domain, Render Dashboard → `omniai` → Settings → Custom
  Domain; add your TLS cert (Render manages certs for you).
- Free instances sleep after ~15 min idle. Use a paid plan for a persistent
  public service.
