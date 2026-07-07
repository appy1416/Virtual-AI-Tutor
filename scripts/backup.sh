#!/bin/bash
# EduTwin Automated Daily DB Backup

# Exit immediately if any command fails
set -e

BACKUP_DIR="backups"
DB_NAME=${DATABASE_NAME:-edutwin_prod}
DB_USER=${DATABASE_USER:-edutwin_prod}
S3_BUCKET=${S3_BUCKET_NAME:-edutwin-backups}

mkdir -p "$BACKUP_DIR"

DATE_STR=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/edutwin_${DATE_STR}.sql"

echo "Starting automated database backup for database '${DB_NAME}'..."
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" > "$BACKUP_FILE"

echo "Backup file created at '${BACKUP_FILE}'."

# If AWS CLI is configured, copy to S3 bucket
if command -v aws &> /dev/null; then
    echo "AWS CLI found. Uploading to S3 bucket 's3://${S3_BUCKET}'..."
    aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/"
    echo "Upload complete."
else
    echo "AWS CLI not installed. Skipping S3 replication."
fi

# Clean up backups older than 7 days locally
find "$BACKUP_DIR" -name "edutwin_*.sql" -mtime +7 -delete

echo "Database backup completed successfully."
