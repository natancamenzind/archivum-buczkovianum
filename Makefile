-include .env
export

MANAGE = uv run python backend/manage.py
NPM = npm --prefix frontend

.PHONY: setup dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend \
	lint-frontend format typecheck typecheck-backend typecheck-frontend build-frontend api-client \
	check-api-client messages check

setup:
	uv sync
	uv run pre-commit install
	$(NPM) ci

# Django on :8000 and Vite on :5173. Open http://localhost:5173; Vite proxies the rest to Django.
dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	$(MANAGE) runserver

dev-frontend:
	$(NPM) run dev

test: test-backend test-frontend

test-backend:
	uv run pytest

test-frontend:
	$(NPM) test

lint: lint-backend lint-frontend

lint-backend:
	uv run ruff check .
	uv run ruff format --check .

lint-frontend:
	$(NPM) run lint

format:
	uv run ruff check --fix .
	uv run ruff format .
	$(NPM) run format

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	uv run mypy backend

typecheck-frontend:
	$(NPM) run typecheck

# The production build into frontend/dist/. It catches what the type check misses: the token
# plugin reading design/tokens/tokens.css, asset paths and the /static/ base.
build-frontend:
	$(NPM) run build

# Regenerates frontend/src/api/ from the drf-spectacular schema. Commit the result.
api-client:
	$(MANAGE) spectacular --validate --lang en --file frontend/src/api/openapi.yaml
	$(NPM) run api-client

# Fails if the committed client differs from what `make api-client` generates (CI runs this).
check-api-client: api-client
	@git diff --exit-code -- frontend/src/api/ || { \
		echo "frontend/src/api/ is out of date: run 'make api-client' and commit the result." >&2; \
		exit 1; }

# Updates backend/locale/pl/ from the strings marked for translation in the backend, and compiles
# it. Translate the new entries in django.po, run it again and commit both files. Needs gettext.
messages:
	cd backend && uv run python manage.py makemessages --locale pl --no-location \
		--ignore "*/tests/*" --ignore "media/*" --ignore "staticfiles/*"
	cd backend && uv run python manage.py compilemessages --locale pl

check: lint typecheck test
