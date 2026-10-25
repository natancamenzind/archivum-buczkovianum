# Architecture — Archivum Buczkovianum (v1)

> Scope: what is needed to deliver `docs/user-stories.md` v1, and nothing more.
> Rule of thumb: if a feature is not in a user story, it does not need architecture.

## 1. Principles

1. **One repo, one app, one domain.** Django serves the API, the admin and the built frontend. There is no CORS, no JWT and no second service.
2. **Boring and portable.** Use standard Postgres, S3-compatible storage and environment variables. Replit-specific services (database, auth, storage) are never used in code, so moving off Replit is a configuration change.
3. **No background infrastructure.** No Celery, no Redis, no Elasticsearch. Everything that v1 needs runs synchronously inside the request.
4. **Small core.** The data model, fragment tagging and search are the core. They are owned by one person and covered by tests. Everything else is built on top of the API.
5. **No Django signals.** Side effects of saving or deleting a model are written explicitly in that model's `save()` and `delete()`, so reading the model shows every side effect of saving it.

## 2. Stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.12+, Django 5.2 LTS, Django REST Framework, drf-spectacular |
| Database | PostgreSQL 19, accessed only via `DATABASE_URL` |
| Editor panel | Django admin + one custom admin view (the tagger) |
| Rich text | `django-prose-editor[sanitize]` (HTML, sanitized server-side) |
| Media | Amazon S3 (or any S3-compatible storage) via `django-storages` |
| Static files | WhiteNoise (Django static + built frontend) |
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, Tailwind, shadcn/ui |
| API client | Generated from the OpenAPI schema with `openapi-typescript` |
| Scan viewer | `pdfjs-dist` (renders one PDF page at a time) |
| Tests | pytest, pytest-django, factory_boy (backend core); `tsc` + ESLint (frontend) |
| Dev environment | Replit (editors), local or Claude Code (core) |

Hosting for production is not decided yet. The constraints above keep every option open.

## 3. Repository layout

```
/
├── AGENTS.md              # rules for AI agents (single source)
├── CLAUDE.md              # imports AGENTS.md
├── replit.md              # thin pointer to AGENTS.md
├── docs/
│   ├── brief.md
│   ├── user-stories.md
│   └── architecture.md
├── backend/
│   ├── config/            # settings, urls, wsgi
│   ├── archive/           # domain models, admin, tagger view   ← core
│   ├── search/            # search index and query               ← core
│   ├── api/               # DRF serializers, viewsets, schema
│   └── site_shell/        # serves the SPA index.html with meta tags
└── frontend/
    └── src/
        ├── api/           # generated client (never edited by hand)
        ├── components/    # shadcn/ui + project components
        └── pages/         # one file per public page
```

## 4. Domain model

### 4.1 Shared behaviour

Every public entity inherits from an abstract `Publishable` with:

- `status`: `draft` | `published`,
- `title`,
- `description` (rich text, optional),
- `tags`: many-to-many to `Tag` (tags on the whole entity),
- `created_at`, `updated_at`.

### 4.2 Entities

| Model | Key fields | Relations |
|-------|-----------|-----------|
| `Work` | `slug`, `cover_image`, `bibliography` (rich text) | `hero_material` → ContextualMaterial, `featured_note` → Note, `highlighted_fragment` → Fragment (optional override) |
| `Edition` | `publisher`, `place`, `year`, `cover_image` | → Work (inline in admin) |
| `Typescript` | `is_main` (one per work) | → Work, → Document |
| `Note` | `content_kind`, `image`, `file`, `external_url` | ↔ Works via `NoteWorkLink`; → Document (optional) |
| `SecondaryText` | `letter_date`, `sender`, `recipient` | ↔ Works via `SecondaryTextWorkLink`; → Document; `highlighted_fragment` → Fragment |
| `ContextualMaterial` | `content_kind`, `image`, `file`, `external_url` | ↔ Works via `MaterialWorkLink`; → Document (optional) |
| `Tag` | `slug`, `name` (unique), `kind` (`keyword` \| `interpretation`), `header_image` | `related`: symmetric many-to-many to `Tag` |
| `ContentPage` | `slug`, `hero_text`, `graphic`, `body`, `in_menu` | — |
| `SiteSettings` | `intro_text`, `portrait`, `funding_note` | singleton |

`content_kind` is one of `image`, `document`, `external_media`, `ocr_text`, `plain_text`. The two text kinds require a `Document`.

### 4.3 Work links

These are explicit through-models, because the brief attaches data to the link itself:

- `NoteWorkLink`: `note`, `work`, `highlighted_fragment`.
- `SecondaryTextWorkLink`: `secondary_text`, `work`, `tags`.
- `MaterialWorkLink`: `material`, `work`, `tags`.

Tags on `SecondaryTextWorkLink` and `MaterialWorkLink` are the relation tags shown on the work page (US-RA-05).

### 4.4 Document and Fragment — the core

All taggable text lives in one model. This gives one tagging mechanism, one tagger screen and one search source.

**`Document`**

- `kind`: `ocr` | `plain`.
- `scan`: PDF file (only for `ocr`).
- `text`: the full text.
- `page_offsets`: list of character offsets where each page starts (only for `ocr`).

OCR upload format: one UTF-8 `.txt` file with a form-feed character (`\f`) between pages, which is Tesseract's plain-text output. On upload:

- the text is split on `\f`,
- the page count is compared with the PDF page count (US-WR-04 AC2),
- `page_offsets` is stored.

**`Fragment`**

- `document`,
- `start`, `end`: character offsets into `Document.text`,
- `quote`: the selected text, copied at creation time,
- `tags`: many-to-many to `Tag`,
- `needs_review`: bool,
- `featured_on_home`: bool.

Fragments may overlap freely.

**Re-anchoring.** When `Document.text` changes, each fragment is checked:

1. if `text[start:end] == quote`, nothing happens;
2. otherwise, if `quote` occurs exactly once in the new text, the offsets are moved there;
3. otherwise, `needs_review = True`.

Fragments are never deleted automatically.

**Rendering.** The frontend receives `text` and the fragment ranges. It splits the text at every range boundary into non-overlapping segments, and renders each segment as a `<span>` carrying the IDs of the fragments that cover it. No editor library is involved on the public side.

TEI is not a storage format. A TEI export can be generated from `Document` and `Fragment` later.

## 5. Editor panel

- Django admin for all CRUD. Inlines handle editions and work links.
- `django-prose-editor` is used for every rich-text field. It is configured with a minimal toolbar: bold, italic, link, lists and headings.
- **Tagger:** one custom admin view per `Document`.
  - The view shows the text in a plain `<div>`, with existing fragments highlighted.
  - The editor selects text. Vanilla JavaScript computes the offsets and the tag picker POSTs `{start, end, quote, tag_ids}` to a staff-only endpoint.
  - No build step and no framework.
  - The view also lists fragments with `needs_review`, so the editor can fix or delete them.
- The tagger is offered only where US-WR-09 allows it: main typescripts, notes, secondary texts.

## 6. Search

**`SearchEntry` table**

One row per published entity, which satisfies R-04:

- `entity_type`, `entity_id`, `title`, `url`,
- `body`: plain text used for snippets,
- `vector`: `tsvector` with a GIN index,
- `title_trgm`: GIN trigram index, for autocomplete.

**Weights**, implementing US-RA-15:

| Weight | Content |
|--------|---------|
| A | work titles |
| B | tag names and descriptions |
| C | other titles and descriptions |
| D | document texts |

**Updating the index**

Updates are explicit, never via signals:

- `Publishable.save()` calls `super().save()` and then `self.update_search_entry()`. The entry is written if the entity is published and removed if it is a draft.
- `Publishable.delete()` removes the entry, then calls `super().delete()`.
- `Document.save()` re-anchors fragments (section 4.4) and then calls `update_search_entry()` on its owning entity.
- The management command `rebuild_search_index` rebuilds the whole table.

Bulk QuerySet operations (`update()`, `bulk_create()`, `bulk_update()`, `delete()`) bypass `save()` and `delete()`. For `Publishable` models and `Document` they are allowed only in migrations and management commands, and must be followed by `rebuild_search_index`. Django admin's "delete selected" action uses `QuerySet.delete()`, so it is disabled for these models.

**Query**

- `websearch_to_tsquery` + `ts_rank` for ranking.
- `ts_headline` for highlighted snippets.
- The scope filter (US-RA-16) is a `WHERE entity_type IN (...)` clause.
- An empty query returns all rows in the scope, sorted by title.

**Polish inflection** (US-RA-15 AC6)

- The project targets PostgreSQL 19, which ships a built-in `polish` text search configuration.
- Development runs on the current 19 release candidate. Production waits for 19 GA.
- Before writing search code, verify on the dev database that `\dF polish` lists the configuration.
- The configuration name is a single setting, `SEARCH_TS_CONFIG = "polish"`. Search code always reads the setting; it never hardcodes a configuration name.

**Deep links.** A search result URL carries `?q=`, and the page highlights and scrolls to the first match. A fragment link carries `?fragment=<id>`.

## 7. API

Read-only and public: `GET` only, published entities only.

| Endpoint | Purpose |
|----------|---------|
| `/api/home/` | Settings, works gallery, tag cloud, featured fragments |
| `/api/works/<slug>/` | Work page payload (all blocks of US-RA-04) |
| `/api/tags/<slug>/` | Tag page payload |
| `/api/typescripts/<id>/`, `/api/notes/<id>/`, `/api/secondary-texts/<id>/`, `/api/materials/<id>/` | Entity page payloads |
| `/api/documents/<id>/` | Full text, page offsets, scan URL, fragments with tags |
| `/api/pages/<slug>/` | Content page |
| `/api/search/?q=&scope=` | Search results |
| `/api/search/autocomplete/?q=` | Autocomplete suggestions |

Staff-only, session auth with CSRF:

| Endpoint | Purpose |
|----------|---------|
| `/api/editor/fragments/` | Create, update, delete fragments (used by the tagger) |

Each page endpoint returns everything its page needs, including the relation component (R-05), in one response. The frontend never assembles a page from many requests.

The OpenAPI schema is generated by drf-spectacular. The frontend client in `frontend/src/api/` is regenerated from it and never edited by hand.

## 8. Frontend

- One route per public page:
  - `/`,
  - `/works/:slug`,
  - `/tags/:slug`,
  - `/typescripts/:id`,
  - `/notes/:id`,
  - `/secondary-texts/:id`,
  - `/materials/:id`,
  - `/pages/:slug`,
  - `/search`.
- UI is assembled from shadcn/ui components, following the Figma designs.
- The relation component (R-05) and the text renderer (section 4.4) are shared components. Pages reuse them instead of reimplementing them.
- Scan + text view (US-RA-09) renders the PDF page with `pdfjs-dist` next to the slice of `text` between consecutive `page_offsets`.
- External audio/video: a provider embed when the URL is a known provider, otherwise a plain link.

**Serving**

- In production, Django serves `index.html` for every non-API, non-admin URL. `site_shell` injects `<title>`, the meta description and OG tags for that URL.
- In development, Vite proxies `/api`, `/admin`, `/media` and `/static` to Django.

## 9. Not in v1

- Celery, Redis, Elasticsearch, Docker.
- Public accounts or registration.
- i18n machinery (the Ukrainian version is a separate service, later).
- SSR or prerendering beyond meta tags.
- TEI import or export.
- Graph visualisation, side-by-side comparison.

## 10. Open technical points

1. **Production hosting.** To decide before the first public release. It must offer PostgreSQL 19 (see section 6).
2. **Storage provider.** Most likely Amazon S3. The code depends only on the S3 API.
