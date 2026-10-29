# Test environment runbook

The test environment (US-OPS-01) runs on Railway as one project with three services:

| Service | Built from | Role |
|---------|------------|------|
| `app` | `deploy/Dockerfile`, config `deploy/railway.app.toml` | gunicorn on `$PORT`. Migrations run as the pre-deploy command. Basic auth and `X-Robots-Tag` come from Django middleware. |
| `postgres` | image `postgres:19rc1` | The database, with a volume. Reachable only over the private network. |
| `backup` | `deploy/backup.Dockerfile`, config `deploy/railway.backup.toml` | Cron at 03:00 UTC: runs `deploy/backup.sh` once and exits. |

Media and backups are in S3, outside Railway. Every variable is described in `deploy/.env.example`; on Railway they are service variables, never a file.

For the restore and upgrade steps you need, on your own machine, the PostgreSQL 19 client tools (`pg_dump`, `pg_restore`) and the `aws` CLI with credentials for `BACKUP_BUCKET`.

## Setup

1. Create a Railway project and connect the GitHub repo.
2. **postgres.** Add a service from the Docker image `postgres:19rc1` and name it `postgres`.
   - Variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (see `deploy/.env.example`).
   - Add a volume mounted at `/var/lib/postgresql`. PostgreSQL 18+ images keep the data in a version-specific directory under it.
   - Do not generate a domain and do not enable a TCP proxy.
3. **app.** Add a service from the GitHub repo, branch `main`, and name it `app`.
   - Settings → Config-as-code: `/deploy/railway.app.toml`. Leave the root directory empty: the Dockerfile builds from the repo root.
   - Variables: everything in the "app" section of `deploy/.env.example`. `DATABASE_URL` references the postgres service, so it follows any change there:

     ```
     postgres://${{postgres.POSTGRES_USER}}:${{postgres.POSTGRES_PASSWORD}}@${{postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/${{postgres.POSTGRES_DB}}
     ```

   - Networking: generate a public domain (or add your own), then set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to it. `ALLOWED_HOSTS` must also contain `healthcheck.railway.app`, the host Railway's healthcheck sends; without it every deploy fails its healthcheck with 400.
4. **backup.** Add another service from the same repo and branch and name it `backup`.
   - Settings → Config-as-code: `/deploy/railway.backup.toml`.
   - Variables: the "backup" section of `deploy/.env.example`, with the same `DATABASE_URL` reference as the app.
   - No domain.
5. Deploy. The first app deploy runs every migration in the pre-deploy step.
6. Create an editor account. With the Railway CLI linked to the project: `railway ssh --service app`, then `python backend/manage.py createsuperuser`.
7. Check the backup after its first run at 03:00 UTC: the backup service's log ends with `Uploaded s3://…/db/<timestamp>.dump`, and the object is in the bucket.
8. Check the site: without credentials it answers 401, `/healthz` answers 200, and `curl -sI` shows `X-Robots-Tag: noindex, nofollow`.

## Routine deploy

Merge to `main`. Railway builds the new image, runs `python backend/manage.py migrate --noinput` in a one-off container, starts the new version and switches traffic once `/healthz` returns 200.

- If the build or migrations fail, the deploy stops and the old version keeps serving. The deploy's logs in the app service show why.
- To redeploy the same commit, use "Redeploy" on the app's latest deployment.

Watch out for migrations that the running version cannot live with (dropping or renaming a column it still reads): the old version keeps serving until the new one passes its healthcheck, against the already migrated database.

## Restore from backup

Dumps are in `s3://$BACKUP_BUCKET/db/`, named by UTC time (`20261029T030000Z.dump`); the newest 14 are kept.

1. **Stop writes.** In the app service, open the active deployment's menu and choose "Remove". The site is down until step 5.
2. **Open the database temporarily.** In the postgres service, Settings → Networking → enable TCP Proxy on port 5432. Railway shows a public host and port.
3. **Fetch the dump and restore.**

   ```bash
   aws s3 ls "s3://$BACKUP_BUCKET/db/"                  # pick a dump
   aws s3 cp "s3://$BACKUP_BUCKET/db/<name>.dump" restore.dump

   # The postgres service's credentials, with the TCP proxy's host and port.
   DB="postgres://<user>:<password>@<proxy-host>:<proxy-port>/<db>"
   pg_restore --clean --if-exists --no-owner --exit-on-error --dbname "$DB" restore.dump
   ```

4. **Close the database.** Remove the TCP proxy.
5. **Start the app.** Use "Redeploy" on the app's latest deployment.

Check the site, then delete `restore.dump`. Media is in its own S3 bucket and is not part of the dump.

## Upgrading PostgreSQL 19rc1 to 19 GA

The data directory of a release candidate is not guaranteed to work with the final release, so dump and restore into a new service instead of reusing the volume. The old service stays untouched until the end, so you can switch back. Plan for downtime of a few minutes.

1. **Stop writes.** In the app service, remove the active deployment, as in a restore.
2. **Dump the old database.** Enable a TCP proxy on `postgres`, then:

   ```bash
   OLD="postgres://<user>:<password>@<old-proxy-host>:<old-proxy-port>/<db>"
   pg_dump --format=custom --dbname "$OLD" --file upgrade.dump
   ```

3. **Create the new service.** Add a service from the image `postgres:19`, named `postgres-19`, with the same `POSTGRES_*` variables and a new volume at `/var/lib/postgresql`. Enable a TCP proxy on it too.
4. **Restore.**

   ```bash
   NEW="postgres://<user>:<password>@<new-proxy-host>:<new-proxy-port>/<db>"
   pg_restore --no-owner --exit-on-error --dbname "$NEW" upgrade.dump
   ```

5. **Switch `DATABASE_URL`.** In the app and backup services, replace `postgres` with `postgres-19` in the reference:

   ```
   postgres://${{postgres-19.POSTGRES_USER}}:${{postgres-19.POSTGRES_PASSWORD}}@${{postgres-19.RAILWAY_PRIVATE_DOMAIN}}:5432/${{postgres-19.POSTGRES_DB}}
   ```

6. **Start the app.** Redeploy it, and check the site.
7. **Update the backup image.** In a PR, change `FROM postgres:19rc1` to `FROM postgres:19` in `deploy/backup.Dockerfile`, and `postgres:19rc1` to `postgres:19` in US-OPS-01 AC2 and in this runbook. Once merged, check the next backup's log.
8. **Clean up.** Remove both TCP proxies. After a few days without problems, delete the old `postgres` service and its volume, and `upgrade.dump`.

To switch back before step 8, point `DATABASE_URL` at `postgres` again and redeploy. Anything written to the new database in between is lost.
