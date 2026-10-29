#!/usr/bin/env bash
# Dumps the database to s3://$BACKUP_BUCKET/db/ and keeps the newest 14 dumps (US-OPS-01 AC8).
# Run daily from cron on the server, from the repo root: deploy/backup.sh
set -euo pipefail

keep=14
aws_image=amazon/aws-cli:2.31.0

compose() { docker compose -f deploy/compose.yml "$@"; }

# Reads one variable from deploy/.env, without sourcing the file (the bcrypt hash contains `$`).
env_value() {
	sed -n "s/^$1=//p" deploy/.env | tail -n 1 | sed "s/^['\"]//; s/['\"]$//"
}

bucket=$(env_value BACKUP_BUCKET)
if [[ -z "$bucket" ]]; then
	echo "BACKUP_BUCKET is not set in deploy/.env" >&2
	exit 1
fi
endpoint=$(env_value AWS_S3_ENDPOINT_URL)

# Dump to a file first, so a failed pg_dump never uploads a partial dump.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# The aws CLI runs in a container, so nothing is installed on the host.
aws() {
	docker run --rm -v "$tmp:/backup:ro" \
		-e AWS_ACCESS_KEY_ID="$(env_value AWS_ACCESS_KEY_ID)" \
		-e AWS_SECRET_ACCESS_KEY="$(env_value AWS_SECRET_ACCESS_KEY)" \
		-e AWS_DEFAULT_REGION="$(env_value AWS_S3_REGION_NAME)" \
		${endpoint:+-e AWS_ENDPOINT_URL="$endpoint"} \
		"$aws_image" "$@"
}

name="buczkovianum-$(date -u +%Y%m%dT%H%M%SZ).dump"
compose exec -T postgres pg_dump --format=custom \
	-U "$(env_value POSTGRES_USER)" -d "$(env_value POSTGRES_DB)" >"$tmp/$name"
aws s3 cp "/backup/$name" "s3://$bucket/db/$name"
echo "Uploaded s3://$bucket/db/$name"

# Names sort by time, so everything before the newest $keep is old.
mapfile -t dumps < <(aws s3 ls "s3://$bucket/db/" | awk '{print $4}' | grep '\.dump$' | sort)
if ((${#dumps[@]} > keep)); then
	for old in "${dumps[@]:0:${#dumps[@]}-keep}"; do
		aws s3 rm "s3://$bucket/db/$old"
	done
fi
