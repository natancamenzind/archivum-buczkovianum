#!/usr/bin/env bash
# Dumps the database to s3://$BACKUP_BUCKET/db/ and keeps the newest 14 dumps (US-OPS-01 AC8).
# Runs inside deploy/backup.Dockerfile, started daily by Railway cron. Reads DATABASE_URL,
# BACKUP_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_REGION_NAME and, for an
# S3-compatible service other than AWS, AWS_S3_ENDPOINT_URL.
set -euo pipefail

keep=14

: "${DATABASE_URL:?DATABASE_URL is not set}"
: "${BACKUP_BUCKET:?BACKUP_BUCKET is not set}"
: "${AWS_S3_REGION_NAME:?AWS_S3_REGION_NAME is not set}"

# The aws CLI's own names for what Django reads as AWS_S3_*.
export AWS_DEFAULT_REGION="$AWS_S3_REGION_NAME"
if [[ -n "${AWS_S3_ENDPOINT_URL:-}" ]]; then
	export AWS_ENDPOINT_URL="$AWS_S3_ENDPOINT_URL"
fi

# Dump to a file first, so a failed pg_dump never uploads a partial dump.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

name="$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --dbname="$DATABASE_URL" --file="$tmp/$name"
aws s3 cp --only-show-errors "$tmp/$name" "s3://$BACKUP_BUCKET/db/$name"
echo "Uploaded s3://$BACKUP_BUCKET/db/$name"

# Names sort by time, so everything before the newest $keep is old.
mapfile -t dumps < <(aws s3 ls "s3://$BACKUP_BUCKET/db/" | awk '{print $4}' | grep '\.dump$' | sort)
if ((${#dumps[@]} > keep)); then
	for old in "${dumps[@]:0:${#dumps[@]}-keep}"; do
		aws s3 rm --only-show-errors "s3://$BACKUP_BUCKET/db/$old"
		echo "Deleted s3://$BACKUP_BUCKET/db/$old"
	done
fi
