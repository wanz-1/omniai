# OmniAI Disaster Recovery Plan

## Overview

This document describes the procedures for recovering OmniAI in the event of a disaster, including total infrastructure loss, data corruption, or region-wide outage.

## Recovery Objectives

- **RPO (Recovery Point Objective)**: 1 hour (maximum acceptable data loss)
- **RTO (Recovery Time Objective)**: 4 hours (maximum acceptable downtime)

## Backup Strategy

| Component | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL | Every 6 hours | 30 days | `pg_dump` custom format |
| File Storage (S3/MinIO) | Daily | 30 days | S3 sync |
| Kubernetes Configs | On change | Git history | GitOps (ArgoCD/Flux) |
| Secrets | On change | Git (encrypted) | SOPS + Git |
| Monitoring Data | 7 days | 7 days | Prometheus TSDB snapshot |

## Recovery Procedures

### 1. Infrastructure Recovery (Total Loss)

```bash
# Step 1: Restore Terraform state (if lost)
aws s3 cp s3://omniai-terraform-state/infra/terraform.tfstate ./terraform.tfstate

# Step 2: Apply Terraform to rebuild infrastructure
cd infra/terraform
terraform init
terraform apply -var="environment=production"

# Step 3: Configure kubectl
aws eks update-kubeconfig --name omniai-production --region us-east-1

# Step 4: Deploy Kubernetes manifests
kubectl apply -f infra/k8s/
kubectl apply -f deploy/kubernetes/

# Step 5: Restore secrets from AWS Secrets Manager
SECRETS=$(aws secretsmanager get-secret-value --secret-id omniai-production-secrets --query SecretString --output text)
echo "$SECRETS" | kubectl create secret generic omniai-secrets --from-literal=... --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Database Recovery

```bash
# List available backups
./infra/scripts/restore.sh --list

# Restore latest backup
./infra/scripts/restore.sh

# Restore from specific timestamp
./infra/scripts/restore.sh 20240730_120000

# Download and restore from S3
./infra/scripts/restore.sh --from-s3 omniai_db_20240730_120000.sql.gz
```

### 3. File Storage Recovery

```bash
# Sync from S3 backup
aws s3 sync s3://omniai-backups/files/ s3://omniai-production-storage/

# Or restore from local backup
tar -xzf /var/backups/omniai/omniai_s3_20240730_120000.tar.gz -C /tmp/s3_restore/
aws s3 sync /tmp/s3_restore/s3_snapshot/ s3://omniai-production-storage/
```

### 4. Application Recovery (Pod Failure)

```bash
# Check pod status
kubectl get pods -l app=omniai

# Restart specific deployment
kubectl rollout restart deployment/omniai-backend
kubectl rollout status deployment/omniai-backend

# Rollback to previous version
kubectl rollout undo deployment/omniai-backend
kubectl rollout status deployment/omniai-backend

# Scale up if needed
kubectl scale deployment/omniai-backend --replicas=5
```

### 5. Monitoring Recovery

```bash
# Restore Prometheus data from snapshot
kubectl exec -n monitoring deployment/prometheus -- tar -xzf /backups/prometheus-snapshot.tar.gz -C /prometheus/

# Reload Prometheus configuration
kubectl exec -n monitoring deployment/prometheus -- kill -HUP 1

# Re-import Grafana dashboards
kubectl cp infra/monitoring/grafana/dashboards/ monitoring/grafana-0:/etc/grafana/provisioning/dashboards/
```

## Automated Backup Schedule

The backup script should be run as a cron job:

```cron
# Database backup every 6 hours
0 */6 * * * /opt/omniai/infra/scripts/backup.sh

# S3 backup daily at 2 AM
0 2 * * * /opt/omniai/infra/scripts/backup.sh
```

Or as a Kubernetes CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: omniai-database-backup
spec:
  schedule: "0 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16-alpine
              command: ["/bin/sh", "-c"]
              args:
                - pg_dump "postgresql://omniai:$(DB_PASSWORD)@omniai-postgres:5432/omniai" --format=custom --compress=9 | aws s3 cp - s3://omniai-backups/db/omniai_$(date +%Y%m%d_%H%M%S).sql.gz
              envFrom:
                - secretRef:
                    name: omniai-secrets
          restartPolicy: OnFailure
```

## Failure Scenarios

| Scenario | Detection | Recovery Action | Expected RTO |
|----------|-----------|----------------|--------------|
| Single pod crash | Liveness probe | Kubernetes auto-restarts | < 1 minute |
| Node failure | Node status | Cluster autoscaler replaces | < 5 minutes |
| Database corruption | Application errors | Restore from backup | < 30 minutes |
| AZ outage | Multiple pod failures | Spread across AZs | < 15 minutes |
| Region outage | All pods down | Cross-region DR (future) | < 4 hours |
| Secrets leak | Security alert | Rotate all keys/secrets | < 1 hour |
| Container image vulnerability | Image scan | Rebuild and redeploy | < 2 hours |

## Testing Schedule

- **Weekly**: Pod restart test, verify auto-healing
- **Monthly**: Database backup restore test (in staging)
- **Quarterly**: Full DR drill (infrastructure rebuild from Terraform)
- **Annually**: Cross-region failover test

## Contact Information

| Role | Contact |
|------|---------|
| On-call Engineer | ops@omniai.example.com |
| Security Team | security@omniai.example.com |
| Database Admin | dba@omniai.example.com |
| Infrastructure Lead | infra@omniai.example.com |
