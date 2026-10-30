# The daily database backup (US-OPS-01 AC8). A Render cron job (render.yaml) builds it from the
# repo root, runs deploy/backup.sh once and the container exits.
# pg_dump must match the server's major version: keep this tag on the database's PostgreSQL major.
FROM postgres:18

RUN apt-get update \
    && apt-get install -y --no-install-recommends awscli ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY deploy/backup.sh /usr/local/bin/backup.sh

USER postgres

CMD ["/usr/local/bin/backup.sh"]
