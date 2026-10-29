# The daily database backup (US-OPS-01 AC8). A Railway cron service builds it from the repo root
# (deploy/railway.backup.toml), runs deploy/backup.sh once and the container exits.
# Same image as the database, so pg_dump always matches the server's major version.
FROM postgres:19rc1

RUN apt-get update \
    && apt-get install -y --no-install-recommends awscli ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/backup.sh /usr/local/bin/backup.sh

USER postgres

CMD ["/usr/local/bin/backup.sh"]
