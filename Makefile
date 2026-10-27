-include .env
export

MANAGE = uv run python backend/manage.py
NPM = npm --prefix frontend

.PHONY: setup dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend \
	lint-frontend format typecheck typecheck-backend typecheck-frontend api-client check

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

# Regenerates frontend/src/api/ from the drf-spectacular schema. Commit the result.
api-client:
	$(MANAGE) spectacular --validate --file frontend/src/api/openapi.yaml
	$(NPM) run api-client

check: lint typecheck test
