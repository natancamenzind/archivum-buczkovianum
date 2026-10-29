# Test environment runbook

The test environment (US-OPS-01) runs on one arm64 Linux host with `docker compose`: `postgres`, `app` (gunicorn) and `caddy` (HTTPS, basic auth, `X-Robots-Tag`). Everything is in `deploy/`. Run every command below on the server, from the repo root.

All commands use this shorthand:

```bash
compose() { docker compose -f deploy/compose.yml "$@"; }
```

## First deploy

1. Install Docker Engine with the compose plugin, git and curl. Open ports 80 and 443. Point the site's DNS record at the server.
2. Clone the repo and check out `main`.
3. Copy `deploy/.env.example` to `deploy/.env` and fill in every value. The comments say how to generate each secret. Keep the single quotes around `BASIC_AUTH_HASH`.
4. Run `deploy/deploy.sh`. On the first run Caddy gets a certificate, which can take a minute.
5. Create an editor account: `compose exec app python backend/manage.py createsuperuser`.
6. Schedule the daily backup with `crontab -e`:

   ```
   0 3 * * * cd /path/to/repo && deploy/backup.sh >> /var/log/buczkovianum-backup.log 2>&1
   ```

   Run `deploy/backup.sh` once by hand to check that the bucket and credentials work.

## Routine deploy

```bash
deploy/deploy.sh
```

It pulls `main` (fast-forward only), builds the image, runs migrations, restarts the services and waits up to 60 s for `/healthz` to return 200 through Caddy. If it fails, `compose logs app` shows why.

## Restore from backup

Dumps are in `s3://$BACKUP_BUCKET/db/`, named by UTC time; the newest 14 are kept.

```bash
# Read the bucket, the credentials and the database names from deploy/.env.
set -a; . <(grep -E '^(AWS_|BACKUP_BUCKET|POSTGRES_)' deploy/.env); set +a
aws() {
  docker run --rm -v "$PWD:/aws" -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
    -e AWS_DEFAULT_REGION="$AWS_S3_REGION_NAME" amazon/aws-cli:2.31.0 "$@"
}

aws s3 ls "s3://$BACKUP_BUCKET/db/"                     # pick a dump
aws s3 cp "s3://$BACKUP_BUCKET/db/<name>.dump" restore.dump

compose stop app
compose exec -T postgres dropdb -U "$POSTGRES_USER" "$POSTGRES_DB"
compose exec -T postgres createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner < restore.dump
compose start app
rm restore.dump
```

Media is in its own S3 bucket and is not part of the dump.

## Upgrading PostgreSQL 19rc1 to 19 GA

The data directory of a release candidate is not guaranteed to work with the final release, so dump and restore instead of reusing the volume. Plan a few minutes of downtime.

```bash
set -a; . <(grep -E '^POSTGRES_' deploy/.env); set +a

# 1. Stop writes and take a dump. Also run deploy/backup.sh, so there is a copy in S3.
compose stop app
compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > upgrade.dump

# 2. Change the tag: in deploy/compose.yml, postgres:19rc1 -> postgres:19. Commit it to main
#    through a PR and `git pull --ff-only` here.

# 3. Recreate the volume. Only the postgres volume: caddy_data holds the certificates.
compose down
docker volume rm deploy_postgres

# 4. Start the new server on the empty volume and restore.
compose up -d --wait postgres
compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner < upgrade.dump

# 5. Start everything.
deploy/deploy.sh
```

Check the site, then delete `upgrade.dump`.
