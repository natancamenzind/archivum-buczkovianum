#!/usr/bin/env bash
# Dumps the database to s3://$BACKUP_BUCKET/db/ and keeps the newest 14 dumps (US-OPS-01 AC8).
# Runs daily inside deploy/backup.Dockerfile as a Render cron job, and also runs as is on any
# machine with bash, pg_dump of the server's major version and the aws CLI. Reads DATABASE_URL,
# BACKUP_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION and, for an
# S3-compatible service other than AWS, AWS_ENDPOINT_URL (all but the first two read by aws).
set -euo pipefail

keep=14

: "${DATABASE_URL:?DATABASE_URL is not set}"
: "${BACKUP_BUCKET:?BACKUP_BUCKET is not set}"
: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION is not set}"
for tool in pg_dump aws; do
	command -v "$tool" >/dev/null || {
		echo "$tool is not installed" >&2
		exit 1
	}
done

# Dump to a file first, so a failed pg_dump never uploads a partial dump.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

name="$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --dbname="$DATABASE_URL" --file="$tmp/$name"
aws s3 cp --only-show-errors "$tmp/$name" "s3://$BACKUP_BUCKET/db/$name"
echo "Uploaded s3://$BACKUP_BUCKET/db/$name"

# Names sort by time, so everything after the newest $keep is old. No mapfile: macOS ships bash 3.
aws s3 ls "s3://$BACKUP_BUCKET/db/" | awk '$4 ~ /\.dump$/ {print $4}' | sort -r | tail -n +$((keep + 1)) |
	while read -r old; do
		aws s3 rm --only-show-errors "s3://$BACKUP_BUCKET/db/$old"
		echo "Deleted s3://$BACKUP_BUCKET/db/$old"
	done
