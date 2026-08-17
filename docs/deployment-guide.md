# OmniAI Deployment Guide

## Architecture Overview

```
                         ┌─────────────┐
                         │  CloudFront  │
                         │  / CDN       │
                         └──────┬──────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
            ┌──────┴──────┐          ┌───────┴───────┐
            │  Frontend    │          │   Backend      │
            │  Next.js 14  │          │  FastAPI       │
            │  Port 3000   │          │  Port 8000     │
            └──────┬──────┘          └───────┬───────┘
                   │                         │
                   └──────────┬──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │     Redis          │
                    │  Cache + Broker    │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────┴──────┐ ┌─────┴─────┐ ┌───────┴───────┐
       │  PostgreSQL │ │  MinIO/S3 │ │  Celery Worker│
       │  Database   │ │  Storage  │ │  Async Tasks  │
       └─────────────┘ └───────────┘ └───────────────┘
```

## Prerequisites

- Docker & Docker Compose (local development)
- Kubernetes cluster (production: EKS, AKS, GKE)
- Terraform >= 1.6 (infrastructure provisioning)
- PostgreSQL 16
- Redis 7
- Node.js 20+ (frontend build)
- Python 3.12+ (backend)

## Local Development

```bash
# 1. Clone and configure
git clone https://github.com/your-org/omniai.git
cd omniai
cp .env.example .env
# Edit .env with your API keys

# 2. Start infrastructure
docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up -d

# 3. Install dependencies
cd backend && pip install -r requirements/dev.txt
cd ../frontend && npm install

# 4. Run migrations (auto-created on startup)
cd backend && uvicorn app.main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm run dev
```

## Production Deployment

### 1. Infrastructure Provisioning (Terraform)

```bash
cd infra/terraform
terraform init
terraform workspace new production
terraform apply -var="environment=production" -auto-approve
```

### 2. Build and Push Docker Images

```bash
# Backend
docker build -t omniai/backend:latest -f backend/Dockerfile backend/
docker tag omniai/backend:latest <ecr-repo>/omniai/production/backend:latest
docker push <ecr-repo>/omniai/production/backend:latest

# Frontend
docker build -t omniai/frontend:latest -f frontend/Dockerfile frontend/
docker tag omniai/frontend:latest <ecr-repo>/omniai/production/frontend:latest
docker push <ecr-repo>/omniai/production/frontend:latest
```

### 3. Deploy to Kubernetes

```bash
# Configure kubectl
aws eks update-kubeconfig --name omniai-production --region us-east-1

# Create secrets
kubectl apply -f infra/k8s/secrets.example.yml
# Or fetch from AWS Secrets Manager
kubectl create secret generic omniai-secrets --from-literal=secret_key=...

# Apply manifests
kubectl apply -f infra/k8s/configmap.yml
kubectl apply -f infra/k8s/
kubectl apply -f deploy/kubernetes/

# Verify
kubectl get pods -l app=omniai
kubectl get ingress
```

### 4. Database Migration

Alembic is the authoritative source for the full schema (DB-001). Run the migration before starting the application — the app no longer auto-creates tables at startup:

```bash
cd backend
alembic -c alembic/alembic.ini upgrade head
```

### 5. Monitoring Setup

```bash
# Install Prometheus Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Apply OmniAI monitoring configs
kubectl apply -f infra/k8s/monitoring.yml
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Async PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET` | Yes | JWT signing secret (min 64 chars) |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `S3_ENDPOINT` | Yes | S3-compatible storage endpoint |
| `S3_ACCESS_KEY` | Yes | Storage access key |
| `S3_SECRET_KEY` | Yes | Storage secret key |
| `STRIPE_SECRET_KEY` | No | Stripe secret key |
| `SENTRY_DSN` | No | Sentry error tracking DSN |
| `FRONTEND_URL` | Yes | Frontend URL for CORS |

## Scaling

### Horizontal Pod Autoscaling
- Backend: 3-20 pods (CPU > 70% triggers scale-up)
- Frontend: 2-10 pods (CPU > 60% triggers scale-up)
- Celery Workers: 2-10 pods (CPU > 70% triggers scale-up)

### Database Scaling
- Start with `db.t3.medium` (2 vCPU, 4GB RAM)
- Enable Performance Insights for monitoring
- Add read replicas when queries exceed 1000 QPS
- Configure `pg_bouncer` for connection pooling at scale

### Cache Scaling
- Redis cluster mode enabled for > 10GB dataset
- Multiple cache tiers: hot (Redis), warm (ElastiCache), cold (S3)

## Backup & Disaster Recovery

See `infra/scripts/disaster-recovery.md` for complete DR procedures.

### Automated Backups
```bash
# Database backup (runs every 6 hours)
0 */6 * * * /opt/omniai/infra/scripts/backup.sh

# Or use Kubernetes CronJob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: omniai-backup
spec:
  schedule: "0 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16-alpine
              command: ["pg_dump", "postgresql://...", "--format=custom"]
          restartPolicy: OnFailure
EOF
```

## Security Checklist

- [ ] JWT secret is a random 64+ character string
- [ ] All API keys and secrets stored in Kubernetes Secrets / AWS Secrets Manager
- [ ] HTTPS enabled via cert-manager + Let's Encrypt
- [ ] Network policies restrict pod-to-pod communication
- [ ] Database accessible only from within VPC
- [ ] S3 bucket access limited to IAM roles (not public)
- [ ] Rate limiting enabled on all API endpoints
- [ ] CORS configured to allow only frontend domain
- [ ] Input validation on all user-facing endpoints
- [ ] MFA and account lockout enabled
- [ ] Security scanning on all container images
- [ ] Regular dependency updates (Dependabot/Renovate)
- [ ] Audit logging enabled for sensitive operations
