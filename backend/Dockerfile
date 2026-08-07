# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base

# Security: create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies - layer cache
COPY requirements/base.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r base.txt

# Copy application
COPY --chown=appuser:appuser . .

# Create needed dirs and set permissions
RUN mkdir -p /app/data/agent_workspace /app/logs && chown -R appuser:appuser /app

# Drop privileges
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form for proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
