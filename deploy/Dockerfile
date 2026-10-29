# The app image for the test environment (US-OPS-01). Build from the repo root:
#   docker build -f deploy/Dockerfile .
# Every base image is multi-arch, so the build runs natively on linux/arm64.

# --- Frontend: the built SPA, served by Django through WhiteNoise -------------------------------
FROM node:24-bookworm-slim AS frontend

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
# tailwind-tokens.ts reads the design tokens from outside frontend/.
COPY design/tokens/tokens.css /app/design/tokens/tokens.css
COPY frontend/ ./
RUN npm run build

# --- uv binary, pinned ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

# --- App -----------------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/ backend/
COPY --from=frontend /app/frontend/dist/ frontend/dist/

# collectstatic needs settings to load, not a working database or real secrets. These values
# exist only for this command and are not stored in the image.
RUN SECRET_KEY=collectstatic-only DATABASE_URL=postgres://collectstatic-only/none DEBUG=true \
    python backend/manage.py collectstatic --noinput

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 8000

# Migrations are not run here: the deploy script runs them (US-OPS-01 AC7).
# A long timeout, because editors upload large PDF scans through the admin.
CMD ["gunicorn", "config.wsgi:application", \
     "--chdir", "backend", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--no-control-socket"]
