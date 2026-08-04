.PHONY: dev dev-build dev-down test lint clean setup help

help:
	@echo "OmniAI Development Commands"
	@echo "=========================="
	@echo "make dev       - Start development environment"
	@echo "make dev-build - Build and start development environment"
	@echo "make dev-down  - Stop development environment"
	@echo "make test      - Run tests"
	@echo "make lint      - Run linters"
	@echo "make clean     - Clean up temporary files"
	@echo "make setup     - Initial project setup"

dev:
	docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up

dev-build:
	docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up --build

dev-down:
	docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml down

dev-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest tests/ -v --cov=app

test-frontend:
	cd frontend && npm run lint

lint:
	cd backend && ruff check .

lint-frontend:
	cd frontend && npm run lint

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(name)"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/
	rm -rf frontend/.next/

setup:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements/dev.txt
	cd frontend && npm install
	cp .env.example .env
	@echo "Setup complete! Edit .env with your settings then run 'make dev'"
