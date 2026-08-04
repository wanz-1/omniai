#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/omniai"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="${S3_BUCKET:-omniai-backups}"

mkdir -p "${BACKUP_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup_old() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete
}

backup_database() {
    local db_url="${DATABASE_URL_SQL:-postgresql://omniai:${DB_PASSWORD}@localhost:5432/omniai}"
    local backup_file="${BACKUP_DIR}/omniai_db_${TIMESTAMP}.sql.gz"

    log "Starting database backup..."
    pg_dump "${db_url}" \
        --format=custom \
        --verbose \
        --no-owner \
        --compress=9 \
        --file="${backup_file}" 2>&1 | tail -5

    if [ -f "${backup_file}" ]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log "Database backup completed: ${backup_file} (${size})"
    else
        log "ERROR: Database backup failed!"
        return 1
    fi
}

backup_s3() {
    local backup_file="${BACKUP_DIR}/omniai_s3_${TIMESTAMP}.tar.gz"

    log "Starting S3 backup..."
    if command -v aws &>/dev/null; then
        aws s3 sync "s3://${S3_BUCKET}" "${BACKUP_DIR}/s3_snapshot/" --quiet
        tar -czf "${backup_file}" -C "${BACKUP_DIR}" s3_snapshot/
        rm -rf "${BACKUP_DIR}/s3_snapshot/"
        local size=$(du -h "${backup_file}" | cut -f1)
        log "S3 backup completed: ${backup_file} (${size})"
    else
        log "WARNING: AWS CLI not found, skipping S3 backup"
    fi
}

upload_to_s3() {
    if ! command -v aws &>/dev/null; then
        log "WARNING: AWS CLI not found, skipping upload"
        return
    fi

    log "Uploading backups to s3://${S3_BUCKET}/backups/..."
    aws s3 sync "${BACKUP_DIR}" "s3://${S3_BUCKET}/backups/" \
        --exclude "s3_snapshot/*" \
        --quiet
    log "Upload completed"
}

verify_backup() {
    local latest=$(ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -1)
    if [ -n "${latest}" ]; then
        log "Verifying backup integrity: ${latest}"
        pg_restore --list "${latest}" >/dev/null 2>&1 && \
            log "Backup integrity check PASSED" || \
            log "WARNING: Backup integrity check FAILED"
    fi
}

main() {
    log "=== OmniAI Backup Script ==="
    log "Starting at $(date)"

    cleanup_old
    backup_database
    backup_s3
    upload_to_s3
    verify_backup

    log "Backup completed successfully at $(date)"
    log "================================"
}

main "$@"
