# Archivum Buczkovianum

A digital archive of the work of **Leopold Buczkowski**. It brings together typescripts,
manuscript notes, secondary texts and contextual materials, and connects them through tags, so
readers can follow a motif from one passage to every other place it appears.

> **Status:** early development. The Django and React skeletons are in place; the archive is
> being built story by story.

## Stack

Django (API, editor panel, public site), PostgreSQL (data and full-text search), and React +
TypeScript for the public website. No Docker, Celery, Redis or Elasticsearch.

## Getting started

You need Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 22+ with npm, and a running
PostgreSQL server. Search uses the `polish` text search configuration of PostgreSQL 19; check
with `\dF polish` in `psql`. On an older server, set `SEARCH_TS_CONFIG=simple` in `.env`: everything
works except Polish inflection (`potoku` no longer finds `potok`). After changing it, run
`uv run python backend/manage.py rebuild_search_index`: stored entries keep the old configuration.

```bash
make setup                 # install Python and npm dependencies, and pre-commit hooks
cp .env.example .env       # then set SECRET_KEY and DATABASE_URL
uv run python backend/manage.py migrate
make dev                   # Django and Vite together
```

Open the site at http://localhost:5173 (Vite, with hot reload). Vite passes `/api/`, `/admin/`,
`/static/` and `/media/` on to Django at http://localhost:8000, so the editor panel is at
http://localhost:5173/admin/ too.

To see the site as production serves it, build the frontend with `npm --prefix frontend run build`
and open http://localhost:8000: Django then serves the built `index.html` for every page URL.

After changing the API, run `make api-client` and commit the regenerated `frontend/src/api/`.
Run `make check` (lint, type check, tests for both sides) before every commit.

## Documentation

- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md): the idea, the users and the content model.
- [`docs/user-stories.md`](docs/user-stories.md): what we are building.
- [`docs/architecture.md`](docs/architecture.md): data model, search and API.
- [`AGENTS.md`](AGENTS.md): how we work. Read it before contributing.

## License

[MIT](LICENSE)
