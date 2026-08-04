# OmniAI

> **One AI. Unlimited Possibilities.**

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

### Development with Docker

```bash
# Clone and enter the project
git clone <repo-url> omniai
cd omniai

# Copy environment file
cp .env.example .env
# Edit .env with your API keys (at minimum, set OPENAI_API_KEY)

# Start everything
make dev
```

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements/dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev

# Services (Docker for DB, Redis, etc.)
docker compose -f infra/docker/docker-compose.yml up postgres redis minio qdrant
```

### Access

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
└── docs/              # Documentation
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
