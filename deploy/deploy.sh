#!/usr/bin/env bash
# Deploys the current main to the test environment (US-OPS-01 AC7). Run on the server from the
# repo root: deploy/deploy.sh
set -euo pipefail

compose() { docker compose -f deploy/compose.yml "$@"; }

# Reads one variable from deploy/.env, without sourcing the file (the bcrypt hash contains `$`).
env_value() {
	sed -n "s/^$1=//p" deploy/.env | tail -n 1 | sed "s/^['\"]//; s/['\"]$//"
}

site_domain=$(env_value SITE_DOMAIN)
if [[ -z "$site_domain" ]]; then
	echo "SITE_DOMAIN is not set in deploy/.env" >&2
	exit 1
fi

git pull --ff-only
compose build
compose run --rm app python backend/manage.py migrate --noinput
compose up -d

# Through Caddy on this host, so TLS, the proxy and the app are all checked.
echo "Waiting for https://$site_domain/healthz ..."
deadline=$((SECONDS + 60))
until curl -fsS -o /dev/null --max-time 5 --resolve "$site_domain:443:127.0.0.1" \
	"https://$site_domain/healthz"; do
	if ((SECONDS >= deadline)); then
		echo "Deploy failed: /healthz did not return 200 within 60 s." >&2
		compose ps >&2
		exit 1
	fi
	sleep 2
done
echo "Deployed: $(git rev-parse --short HEAD)"
