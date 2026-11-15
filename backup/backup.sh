#!/bin/sh
set -eu

: "${DB_HOST:?DB_HOST is required}"
: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"

BACKUP_INTERVAL_SECONDS=${BACKUP_INTERVAL_SECONDS:-86400}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-14}

case "$DB_NAME" in
    ''|*[!A-Za-z0-9_-]*)
        echo "DB_NAME may contain only letters, numbers, underscores, and hyphens" >&2
        exit 1
        ;;
esac

case "$BACKUP_INTERVAL_SECONDS" in
    ''|*[!0-9]*)
        echo "BACKUP_INTERVAL_SECONDS must be a positive integer" >&2
        exit 1
        ;;
esac

case "$BACKUP_RETENTION_DAYS" in
    ''|*[!0-9]*)
        echo "BACKUP_RETENTION_DAYS must be a positive integer" >&2
        exit 1
        ;;
esac

if [ "$BACKUP_INTERVAL_SECONDS" -le 0 ] || [ "$BACKUP_RETENTION_DAYS" -le 0 ]; then
    echo "Backup interval and retention must be greater than zero" >&2
    exit 1
fi

temporary_dump=
temporary_archive=

cleanup() {
    [ -z "$temporary_dump" ] || rm -f "$temporary_dump"
    [ -z "$temporary_archive" ] || rm -f "$temporary_archive"
}

trap cleanup EXIT
trap 'exit 1' HUP INT TERM

mkdir -p /backups

while :; do
    timestamp=$(date -u '+%Y%m%dT%H%M%SZ')
    backup_file="/backups/${DB_NAME}_${timestamp}.sql.gz"
    temporary_dump=$(mktemp "/backups/.${DB_NAME}_${timestamp}.XXXXXX")
    temporary_archive="${temporary_dump}.gz"

    echo "Creating database backup: ${DB_NAME}_${timestamp}.sql.gz"
    MYSQL_PWD="$DB_PASSWORD" mysqldump \
        --host="$DB_HOST" \
        --port="${DB_PORT:-3306}" \
        --user="$DB_USER" \
        --single-transaction \
        --quick \
        --routines \
        --events \
        --triggers \
        --hex-blob \
        --no-tablespaces \
        --default-character-set=utf8mb4 \
        "$DB_NAME" > "$temporary_dump"
    gzip -c "$temporary_dump" > "$temporary_archive"
    mv "$temporary_archive" "$backup_file"
    rm -f "$temporary_dump"
    temporary_dump=
    temporary_archive=

    find /backups -maxdepth 1 -type f \
        -name "${DB_NAME}_*.sql.gz" \
        -mtime "+${BACKUP_RETENTION_DAYS}" \
        -delete

    sleep "$BACKUP_INTERVAL_SECONDS"
done
