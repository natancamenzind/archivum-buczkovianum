-include .env
export

MANAGE = uv run python backend/manage.py

.PHONY: setup dev test lint format typecheck check

setup:
	uv sync
	uv run pre-commit install

dev:
	$(MANAGE) runserver

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy backend

check: lint typecheck test
