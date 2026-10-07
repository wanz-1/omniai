#!/bin/sh
set -e

export PORT="${PORT:-10000}"

if [ "$RUN_MODE" = "worker" ]; then
    cd /app/backend
    exec celery -A app.tasks.celery_app worker --loglevel=info
fi

# ── Web mode: backend + frontend + nginx ─────────────────────────────

# Run pending migrations (idempotent; preDeployCommand usually does this)
cd /app/backend
alembic upgrade head >/dev/null 2>&1 || true

# Start FastAPI backend on internal 127.0.0.1:8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 &

# Start Next.js frontend on internal 127.0.0.1:3000
cd /app/frontend
node_modules/.bin/next start -p 3000 &

# Render nginx config (substitute $PORT), then start nginx.
: "${NGINX_TEMPLATE:=/etc/nginx/templates/default.conf.template}"
envsubst '$PORT' < "$NGINX_TEMPLATE" > /tmp/nginx-default.conf
cp /tmp/nginx-default.conf /etc/nginx/conf.d/default.conf

# nginx -g 'daemon off;' runs in the foreground of this backgrounded job;
# `wait $!` keeps the container alive (blocking) as long as nginx runs.
nginx -g 'daemon off;' &
wait $!
