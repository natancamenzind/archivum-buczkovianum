# AGENTS.md

Archivum Buczkovianum: a digital archive of Leopold Buczkowski's work.
Django serves the API, the editor panel (Django admin) and a React SPA. One repo, one app, one domain.

Read before any task:

- `docs/user-stories.md` — every task implements one story. Its acceptance criteria (AC) are the definition of done.
- `docs/architecture.md` — data model, search, API. Do not contradict it. If a task requires a change to it, stop and ask.

## Commands

Run everything from the repo root.

| Command | What it does |
|---------|--------------|
| `make setup` | Install dependencies (uv for Python, npm for frontend) |
| `make dev` | Run Django and Vite together |
| `make test` | pytest and Vitest, both with coverage thresholds |
| `make lint` | Ruff (lint + format check), ESLint, Prettier check |
| `make typecheck` | mypy (strict) and `tsc --noEmit` |
| `make check` | All of the above. Must pass before every commit. |
| `make test-backend`, `make lint-frontend`, … | One side only: `test`, `lint` and `typecheck` each have a `-backend` and a `-frontend` target. |
| `make build-frontend` | Production build of the frontend into `frontend/dist/` |
| `make api-client` | Regenerate `frontend/src/api/` from the OpenAPI schema |
| `make check-api-client` | Regenerate the client and fail if `frontend/src/api/` changed |
| `make messages` | Update and compile the editor panel's Polish catalogue in `backend/locale/pl/` (needs gettext) |

## Workflow

- One story per branch, named `us-ra-07-tag-page`. The PR title starts with the story ID.
- Never commit to `main`. Never merge your own PR.
- Keep the diff to the story. Do not refactor, rename or reformat code outside it.
- If the story is ambiguous or conflicts with the docs, stop and ask. Do not guess.

## Ownership

The core is `backend/archive/`, `backend/search/`, `backend/api/` and all migrations. Core changes require the core owner's review, enforced by CODEOWNERS.

A page story's PR builds that page's own endpoint, and the core owner reviews it (`docs/plan.md`, D11). Beyond that, frontend work uses the API as it is. If another endpoint lacks data a page needs, say so in the PR. Do not change the backend to get it.

## Tests

All code is tested. There are no exceptions for small changes.

**General**

- Coverage thresholds: 90% for backend and frontend, enforced by `make test`. Never lower them.
- Every AC has at least one test named after it, e.g. `test_us_ra_07_ac4_lists_related_works`.
- A bug fix starts with a test that fails before the fix.

**Backend**

- Tools: pytest, pytest-django, factory_boy. Every model has a factory in its app's `tests/factories.py`.
- Tests run against PostgreSQL, never SQLite, because search depends on Postgres features.
- Test behaviour through model methods and API endpoints, not private helpers.

**Frontend**

- Tools: Vitest and Testing Library.
- Test what the user sees and does, not component internals.
- Mock the API at the network level with MSW, never by mocking modules.
- Helpers live in `frontend/src/test/`: `renderRoute(url)` renders a page through the real routes, and every component test expects `axeViolations(container)` to be empty (R-12).

## Types and linting

- Python: every function is fully annotated. Checked by mypy `--strict` with `django-stubs` and `djangorestframework-stubs`.
- TypeScript: `strict: true`, no `any`.
- Formatting and linting: Ruff for Python; ESLint (`typescript-eslint`) and Prettier for TypeScript.
- Django generics (`ModelAdmin[Work]`, `TabularInline[Edition, Work]`) work at runtime because settings call `django_stubs_ext.monkeypatch()`.
- factory_boy declarations are untyped, so `*.tests.factories` modules are exempt from mypy's `disallow_untyped_calls` (one override in `pyproject.toml`).
- Ruff also checks migrations. After `makemigrations`, write `dependencies` and `operations` as tuples (RUF012) and run `ruff format`.
- Never add `# type: ignore`, `# noqa`, `@ts-ignore`, `@ts-expect-error`, `eslint-disable` or `as any`, and never edit linter or type-checker config. If a suppression seems unavoidable, stop and ask. An approved suppression names the specific rule and carries a comment explaining why.

## Code rules

- Code, comments, docstrings and commit messages are in English. Polish UI copy lives in `frontend/src/copy/pl.ts`, never inline in components.
- The editor panel is in Polish. Backend strings an editor sees (`verbose_name` on every model and field, `help_text`, choice labels, validation messages, admin templates) are written in English and marked with `gettext_lazy` / `{% translate %}`, and use `ngettext` for counts. Run `make messages`, translate the new entries in `backend/locale/pl/LC_MESSAGES/django.po` with the terms from the glossary in `docs/user-stories.pl.md`, run it again and commit the `.po` and `.mo`. The OpenAPI schema stays in English (`make api-client` passes `--lang en`).
- No Django signals. Side effects go in the model's `save()` and `delete()`.
- No bulk QuerySet operations (`update`, `bulk_create`, `bulk_update`, `delete`) on `Publishable` models, `Document` or `Fragment`, except in migrations and management commands (architecture §6).
- No new dependencies without approval. Name and justify any new dependency in the PR.
- No Replit services in code (database, auth, object storage). Configuration comes only from environment variables.
- No Celery, Redis, Elasticsearch or Docker.
- Never edit `frontend/src/api/` by hand. Run `make api-client` instead.
- UI is built from shadcn/ui components, following the Figma designs. Use Tailwind theme tokens; no hardcoded colours or sizes.
  The Tailwind theme holds only the tokens from `design/tokens/tokens.css` (mapping in `frontend/src/index.css`), and typography uses the `.text-*` classes from that file.

## Definition of done

- [ ] Every AC of the story is met and has a test.
- [ ] `make check` passes.
- [ ] Migrations are committed if models changed.
- [ ] `make api-client` has been run if the API changed.
- [ ] The PR description contains:
  - the story ID,
  - what changed,
  - how to verify it manually,
  - anything left undone.
- [ ] If a convention changed, this file is updated in the same PR.
