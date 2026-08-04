#!/usr/bin/env bash
set -euo pipefail

RESTORE_DIR="${RESTORE_DIR:-/var/backups/omniai}"
TIMESTAMP="${1:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

confirm() {
    read -r -p "$1 [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

find_backup() {
    if [ -n "${TIMESTAMP}" ]; then
        echo "${RESTORE_DIR}/omniai_db_${TIMESTAMP}.sql.gz"
    else
        ls -t "${RESTORE_DIR}"/omniai_db_*.sql.gz 2>/dev/null | head -1
    fi
}

restore_database() {
    local backup_file="$1"
    local db_url="${DATABASE_URL_SQL:-postgresql://omniai:${DB_PASSWORD}@localhost:5432/omniai}"

    if [ ! -f "${backup_file}" ]; then
        log "ERROR: Backup file not found: ${backup_file}"
        return 1
    fi

    local size=$(du -h "${backup_file}" | cut -f1)
    log "Restoring database from: ${backup_file} (${size})"

    if ! confirm "This will DESTROY the current database and replace it. Continue?"; then
        log "Restore cancelled."
        return 1
    fi

    log "Terminating existing connections..."
    psql "${db_url}" -c "
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = 'omniai' AND pid <> pg_backend_pid();
    " 2>/dev/null || true

    log "Dropping and recreating database..."
    createdb -T template0 omniai_restore 2>/dev/null || true

    log "Restoring from backup..."
    pg_restore \
        --dbname="${db_url}" \
        --jobs=4 \
        --verbose \
        --no-owner \
        --clean \
        --if-exists \
        "${backup_file}" 2>&1 | tail -10

    log "Database restore completed successfully!"
}

download_from_s3() {
    local s3_bucket="${S3_BUCKET:-omniai-backups}"
    local backup_name="$1"

    if ! command -v aws &>/dev/null; then
        log "WARNING: AWS CLI not found, cannot download from S3"
        return 1
    fi

    log "Downloading backup from s3://${s3_bucket}/backups/${backup_name}..."
    aws s3 cp "s3://${s3_bucket}/backups/${backup_name}" "${RESTORE_DIR}/${backup_name}" --quiet
    log "Download completed: ${RESTORE_DIR}/${backup_name}"
}

list_backups() {
    local pattern="${RESTORE_DIR}/omniai_db_*.sql.gz"
    local count=$(ls ${pattern} 2>/dev/null | wc -l)

    if [ "${count}" -eq 0 ]; then
        log "No local backups found in ${RESTORE_DIR}"
        return 1
    fi

    log "Available local backups:"
    echo ""
    ls -lh ${pattern} 2>/dev/null | awk '{printf "  %s %s %s\n", $6, $7, $9}'
    echo ""
}

main() {
    log "=== OmniAI Restore Script ==="
    log "Starting at $(date)"

    if [ "${1:-}" = "--list" ]; then
        list_backups
        exit 0
    fi

    if [ "${1:-}" = "--from-s3" ]; then
        local s3_file="${2:-}"
        if [ -z "${s3_file}" ]; then
            log "Usage: $0 --from-s3 <backup-filename>"
            exit 1
        fi
        download_from_s3 "${s3_file}"
        backup_file="${RESTORE_DIR}/${s3_file}"
    else
        backup_file=$(find_backup)
        if [ -z "${backup_file}" ]; then
            log "No backup found. Use --list to see available backups."
            exit 1
        fi
    fi

    restore_database "${backup_file}"

    log "=== Restore completed at $(date) ==="
}

main "$@"
