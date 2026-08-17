# OmniAI

**One AI. Unlimited Possibilities.**

OmniAI is an all-in-one AI platform that helps individuals, businesses, NGOs, developers, and educational institutions humanize documents, build websites, create chatbots, generate code, analyze data, automate workflows, and more.

## Features

### Phase 1
- **AI Document Humanizer** — Humanize, summarize, translate, and check grammar
- **Website Builder** — Generate complete websites from prompts with 10 templates
- **AI Bot Builder** — Create and deploy intelligent chatbots
- **AI Chat Assistant** — General-purpose AI chat with streaming
- **Code Generator** — Generate, explain, and review code
- **User Dashboard** — Central hub for all activities

### Future Phases
- Mobile App Builder
- Business & Finance Assistant
- Data Analytics
- Automation Engine
- AI Agent Builder
- Design Studio

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+ / FastAPI |
| Frontend | Next.js 14 / TypeScript / Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Vector DB | Qdrant |
| File Storage | MinIO / S3 |
| AI | OpenAI / Anthropic / Ollama / vLLM |
| Task Queue | Celery |
| Auth | JWT / OAuth2 / 2FA |
| Container | Docker / Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Environment Setup

```bash
# Clone and enter the project
git clone <repo-url> omniai
cd omniai

# Copy environment file
cp .env.example .env
# Edit .env with your API keys (at minimum, set OPENAI_API_KEY)
```

> ⚠️ **Security note:** `.env` is for local development only and must never be committed. Staging and production do not read from a flat `.env` file — secrets are managed separately. `.env.example` also ships with `DEBUG=true` and default MinIO credentials (`minioadmin`/`minioadmin`); these are dev-only and must not carry into any deployed environment. See `docs/environment-configuration.md` for the full variable reference, environment tiers, and the DEBUG production requirement.

### Development with Docker

```bash
# Start everything
make dev

# Run database migrations (first run, and after pulling schema changes)
docker compose -f infra/docker/docker-compose.yml exec backend alembic -c alembic/alembic.ini upgrade head
```

### Local Development

**Backend**

```bash
cd backend
python -m venv .venv

# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements/dev.txt
alembic -c alembic/alembic.ini upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend** (in another terminal)

```bash
cd frontend
npm install
npm run dev
```

**Supporting services** (Docker, for DB/cache/storage/vector search)

```bash
docker compose -f infra/docker/docker-compose.yml up postgres redis minio qdrant
```

**Celery worker** (required for async tasks — document processing, bot deployment, etc.)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info

# Optional, if scheduled/periodic tasks are used
celery -A app.tasks.celery_app beat --loglevel=info
```

### Running Tests

```bash
cd backend
pytest
```

## Access

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

## Project Structure

```
omniai/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── core/      # Config, security, middleware
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response
│   │   ├── api/v1/    # API routes
│   │   ├── services/  # Business logic
│   │   ├── tasks/     # Celery async tasks
│   │   └── ws/        # WebSocket handlers
│   ├── alembic/       # Database migrations
│   └── tests/         # Test suite
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/       # Pages
│       ├── components/# UI components
│       ├── modules/   # Feature components
│       ├── hooks/     # Custom hooks
│       ├── lib/       # Utilities
│       └── providers/ # React providers
├── shared/            # Shared types/constants
├── infra/             # Docker, k8s, terraform
└── docs/              # Documentation (see environment-configuration.md for env/config reference)
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Backend fails to start with a DB connection error | Postgres container not up yet, or migrations not applied — run `alembic upgrade head` |
| `OPENAI_API_KEY` / provider errors on AI features | No AI provider key set in `.env` — at least one of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. is required |
| Bot/document tasks silently never complete | Celery worker isn't running — see "Celery worker" step above |
| Port already in use (3000 / 8000 / 5432 / 6379 / 9000) | Another local process or container is bound to that port — stop it or remap the port in `docker-compose.yml` |
| MinIO Console loads but uploads fail | Console (9001) and API (9000) are different ports/endpoints — confirm `S3_ENDPOINT` points to 9000, not 9001 |

## Contributing

- Branch from `main`, open a PR against `main`.
- Run `pytest` (backend) and your frontend's lint/test scripts before opening a PR.
- Keep PRs scoped to one feature/fix; note any config or migration changes explicitly in the PR description.

## License

MIT — see [LICENSE](./LICENSE).
