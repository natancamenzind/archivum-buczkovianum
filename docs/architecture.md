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
| Scan viewer | `pdfjs-dist` (renders one PDF page at a time; also page thumbnails for fragment cards) |
| Tests | pytest, pytest-django, factory_boy (backend core); Vitest + Testing Library, `tsc` + ESLint (frontend) |
| Dev environment | Replit (editors), local or Claude Code (core) |

Hosting for production is not decided yet. The constraints above keep every option open.

## 3. Repository layout

```
/
├── AGENTS.md              # rules for AI agents (single source)
├── CLAUDE.md              # imports AGENTS.md
├── replit.md              # thin pointer to AGENTS.md
├── docs/
│   ├── PROJECT_BRIEF.md
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

Archival entities also inherit the abstract `Archival` mixin:

- `institution`: → `Institution` (optional),
- `shelfmark`: the number part of the shelfmark (optional), e.g. `1618`.

The display form `"<abbreviation>, sygn. <shelfmark>"` is a model property. It is never stored or entered as one text.

Every image field has a companion `<field>_alt` text field. `clean()` rejects an image without its text alternative (R-12).

### 4.2 Entities

| Model | Key fields | Relations |
|-------|-----------|-----------|
| `Institution` | `abbreviation` (unique), `name` | — |
| `Work` | `slug`, `genre`, `cover_image` | — |
| `Edition` | `publisher`, `place`, `year`, `cover_image` | → Work (inline in admin) |
| `Typescript` | `is_main` (one per work); `Archival` | → Work, → Document |
| `Note` | `content_kind`, `image`, `file`, `external_url`; `Archival` | `works`: many-to-many to Work; → Document (optional) |
| `SecondaryText` | `kind`, `author`, `source`, `letter_date`, `sender`, `recipient`; `Archival` | ↔ Works via `SecondaryTextWorkLink`; → Document |
| `ContextualMaterial` | `content_kind`, `image`, `file`, `external_url`; `Archival` | ↔ Works via `MaterialWorkLink`; → Document (optional) |
| `Tag` | `slug`, `name` (unique), `kind` (`keyword` \| `interpretation`) | `related`: symmetric many-to-many to `Tag` |
| `SiteSettings` | `intro_text`, `portrait`, `about_intro`, `about_project` | singleton |
| `TeamMember` | `name`, `role`, `bio`, `group` (`leadership` \| `team` \| `site`), `order` | — |

`Institution`, `Edition`, `SiteSettings` and `TeamMember` are not `Publishable`.

`content_kind` is one of `image`, `document`, `external_media`, `ocr_text`, `plain_text`. The two text kinds require a `Document`.

Derived values, computed in queries and never stored:

- **Year of a work**: the lowest `Edition.year`. Works are ordered by it everywhere. The edition with that year is the first edition.
- **Occurrences of a tag**: the number of visible fragments, published entities and work links carrying the tag.
- **Fragment number**: the 1-based position of a fragment among its document's fragments, ordered by `start`.

### 4.3 Work links

These are explicit through-models, because the brief attaches data to the link itself:

- `SecondaryTextWorkLink`: `secondary_text`, `work`, `tags`.
- `MaterialWorkLink`: `material`, `work`, `tags`.

Tags on these links are the relation tags shown on the work page (US-RA-05). A note's link to a work carries no data, so `Note.works` is a plain many-to-many.

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
- `location`: short text, optional (e.g. "rozdział I"),
- `shelfmark`: optional (e.g. `1618.0009`); the institution comes from the document's owner,
- `description`: plain text, optional,
- `is_featured`: bool (R-09, US-RA-02),
- `needs_review`: bool.

Fragments may overlap freely. A fragment is **visible** when its document's owner is published.

The scan page a fragment starts on is the index of the last `page_offsets` entry that is `≤ start`. The API returns it with every fragment, so the fragment card (R-10) can render that page's thumbnail.

**Re-anchoring.** When `Document.text` changes, each fragment is checked:

1. if `text[start:end] == quote`, nothing happens;
2. otherwise, if `quote` occurs exactly once in the new text, the offsets are moved there and `needs_review = True`, so a moved fragment is never silent (US-WR-09 AC4);
3. otherwise, `needs_review = True`.

Fragments are never deleted automatically, and only the editor clears `needs_review`.

**Rendering.** The frontend receives `text` and the fragment ranges. It splits the text at every range boundary into non-overlapping segments, and renders each segment as a `<span>` carrying the IDs of the fragments that cover it. No editor library is involved on the public side.

TEI is not a storage format. A TEI export can be generated from `Document` and `Fragment` later.

### 4.5 Previews

`PREVIEW_LIMIT` (default 2) is a single setting. A preview query orders fragments by `is_featured` descending, then by position in the text, and takes the first `PREVIEW_LIMIT`. The total count is returned with the preview, so the API serves "2 z 24" and the "all" link in one response.

## 5. Editor panel

- Django admin for all CRUD. Inlines handle editions, work links and team members.
- `django-prose-editor` is used for every rich-text field. It is configured with a minimal toolbar: bold, italic, link, lists and headings.
- **Tagger:** one custom admin view per `Document`.
  - The view shows the text in a plain `<div>`, with existing fragments highlighted.
  - The editor selects text. Vanilla JavaScript computes the offsets and the tag picker POSTs `{start, end, quote, tag_ids}` to a staff-only endpoint.
  - No build step and no framework.
  - The view lists every fragment, with a link to its admin form, where the editor sets `location`, `shelfmark`, `description` and `is_featured` (US-WR-09 AC6). Fragments with `needs_review` are listed first, so the editor can fix or delete them.
- The tagger is offered only where US-WR-09 allows it: main typescripts, and notes, secondary texts and contextual materials with a `Document`.
- The tag admin list can be filtered by `kind`.
- **Draft preview** (US-WR-13): every `Publishable` model defines `get_absolute_url()`, so admin shows "View on site" for drafts too.

## 6. Search

**`SearchEntry` table**

One row per published entity and one per visible fragment:

- `entity_type` (`work`, `tag`, `fragment`, `note`, `typescript`, `secondary_text`, `material`), `entity_id`, `title`, `url`,
- `body`: plain text used for snippets,
- `vector`: `tsvector` with a GIN index,
- `title_trgm`: GIN trigram index, for autocomplete,
- `work_ids`: integer array of the related *published* works (GIN index), for the work filter; drafts never reach search, not even as a filter value,
- `decades`: integer array of the decades of those works' years (e.g. `1940`), for the period filter,
- `has_scan`, `has_text`: booleans, for the availability filter.

A fragment's `body` is its quote and description. Its `url` points to its source document with `?fragment=<id>`.

The names of the published tags a work, an item or a fragment carries go into its own `vector` (D18), so a tag name finds what carries it. They are not in `body`: snippets show the entity's own text.

**Weights** (relevance within a group)

| Weight | Content |
|--------|---------|
| A | titles, tag names |
| B | tag descriptions, fragment quotes, the names of the tags an entity carries |
| C | other descriptions |
| D | document texts |

**Updating the index**

Updates are explicit, never via signals:

- `Publishable.save()` calls `super().save()` and then `self.update_search_entry()`. The entry is written if the entity is published and removed if it is a draft. For an entity that owns a `Document`, it also updates the entries of that document's fragments, because their visibility follows the owner.
- `Publishable.delete()` removes the entry, then calls `super().delete()`.
- `Fragment.save()` and `Fragment.delete()` write or remove the fragment's entry.
- `Document.save()` re-anchors fragments (section 4.4) and then calls `update_search_entry()` on its owning entity.
- `Work.save()` and `Work.delete()` also re-index the items related to the work (with their fragments) and every published tag, because the work's status and first-edition year are in their `work_ids` and `decades`. `Edition.save()` and `Edition.delete()` re-index the work and its entries this way, without saving the work.
- `Tag.save()` also re-indexes the works, items and fragments that carry the tag, because their entries hold its name while it is published. Renaming, publishing and unpublishing a tag all go through `save()`.
- Tag entries list the works a tag refers to through whatever carries it, so deletes re-index every published tag, and the admin re-indexes the saved item and every published tag after many-to-many fields and inlines are saved (they are saved after `save()`).
- The management command `rebuild_search_index` rebuilds the whole table.

Bulk QuerySet operations (`update()`, `bulk_create()`, `bulk_update()`, `delete()`) bypass `save()` and `delete()`. For `Publishable` models, `Document` and `Fragment` they are allowed only in migrations and management commands, and must be followed by `rebuild_search_index`. Django admin's "delete selected" action uses `QuerySet.delete()`, so it is disabled for these models.

**Query**

- `websearch_to_tsquery` + `ts_rank` for relevance. Exact phrases in quotes work through `websearch_to_tsquery`.
- `ts_headline` for highlighted snippets.
- The tab (US-RA-16) is a `WHERE entity_type IN (...)` clause. Filters are `work_ids && ...`, `decades && ...`, `has_scan` and `has_text`.
- Facet counts (per tab and per filter value) are `GROUP BY` queries over the same filtered set, in the same request.
- In the "Wszystko" tab, results are ordered by group, in the order of US-RA-15 AC3, then by `ts_rank` or by title. This guarantees "works first, then tags" without depending on weights.
- An empty query returns all rows in the tab and filters, sorted by title.
- No results: the response includes the three published tags with the most occurrences (US-RA-15 AC8).

**Polish inflection** (US-RA-15 AC7)

- The project targets PostgreSQL 19, which ships a built-in `polish` text search configuration.
- Development runs on the current 19 release candidate. Production waits for 19 GA.
- Before writing search code, verify on the dev database that `\dF polish` lists the configuration.
- The configuration name is a single setting, `SEARCH_TS_CONFIG`, read from the environment and `polish` by default. CI and production use `polish`; a development database older than 19 may set `simple` and lose only inflection. Search code always reads the setting; it never hardcodes a configuration name.

**Deep links.** A search result URL carries `?q=`, and the page highlights and scrolls to the first match. A fragment link carries `?fragment=<id>`.

## 7. API

Read-only and public: `GET` only, published entities and visible fragments only.

| Endpoint | Purpose |
|----------|---------|
| `/api/home/` | Settings, statistics, works, one random featured fragment, tag cloud with occurrence counts |
| `/api/works/` | Works list (US-RA-18) |
| `/api/works/<slug>/` | Work page payload (US-RA-04) |
| `/api/typescripts/` | Typescripts list, grouped by work (US-RA-19) |
| `/api/tags/` | Tags list with occurrence counts (US-RA-20) |
| `/api/tags/<slug>/` | Tag page payload |
| `/api/typescripts/<id>/`, `/api/notes/<id>/`, `/api/secondary-texts/<id>/`, `/api/materials/<id>/` | Entity page payloads |
| `/api/documents/<id>/` | Full text, page offsets, scan URL, fragments with tags and start page |
| `/api/about/` | About page: introduction, project text, team members by group |
| `/api/search/?q=&tab=&work=&decade=&has_scan=&has_text=&sort=` | Search results with facet counts |
| `/api/search/autocomplete/?q=` | Autocomplete suggestions |

Staff-only, session auth with CSRF:

| Endpoint | Purpose |
|----------|---------|
| `/api/editor/fragments/` | Create, update, delete fragments (used by the tagger) |

Each page endpoint returns everything its page needs, including previews with total counts (section 4.5) and the contextual materials block (R-08), in one response. The frontend never assembles a page from many requests.

**Drafts** (R-06). Entity page endpoints (`/api/<type>/<id or slug>/` and `/api/documents/<id>/`) return a draft only to an authenticated staff session, with `is_draft: true`. For anyone else a draft is a 404. List endpoints, previews, related items and search never include drafts, for any user.

The OpenAPI schema is generated by drf-spectacular. The frontend client in `frontend/src/api/` is regenerated from it and never edited by hand.

## 8. Frontend

- One route per public page:
  - `/`,
  - `/works`, `/works/:slug`,
  - `/typescripts`, `/typescripts/:id`,
  - `/tags`, `/tags/:slug`,
  - `/notes/:id`,
  - `/secondary-texts/:id`,
  - `/materials/:id`,
  - `/about`,
  - `/search` (tab, filters and sort in the query string).
- UI is assembled from shadcn/ui components, following the Figma designs.
- Shared components, reused by pages instead of reimplemented: the subpage layout (R-05), the contextual materials block (R-08), the section header with counter and preview link (R-09), the fragment card (R-10), the reader (R-11) and the text renderer (section 4.4).
- Reader (R-11): on desktop, each PDF page is rendered with `pdfjs-dist` next to the slice of `text` between consecutive `page_offsets`. On mobile, a toggle shows either the scan or the text.
- Tag cloud: the five size steps are computed in the frontend from occurrence counts. The layout uses a deterministic shuffle with a fixed seed, so the same data always gives the same cloud.
- Polish plural forms come from one helper next to the copy in `frontend/src/copy/pl.ts`.
- External audio/video: a provider embed when the URL is a known provider, otherwise a plain link.
- Accessibility (R-12): WCAG 2.1 AA, checked with an automated accessibility check in the component tests.

**Serving**

- In production, Django serves `index.html` for every non-API, non-admin URL. `site_shell` injects `<title>`, the meta description and OG tags for that URL.
- In development, Vite proxies `/api`, `/admin`, `/media` and `/static` to Django.

## 9. Not in v1

- Celery, Redis, Elasticsearch, Docker.
- Public accounts or registration.
- i18n machinery (the Ukrainian version is a separate service, later).
- SSR or prerendering beyond meta tags.
- TEI import or export.
- Graph visualisation, side-by-side comparison of documents.
- Free-form content pages; the About page is the only text page.
- Cropping fragments out of scans. Fragments are text ranges; the card shows the quote and a page thumbnail.

## 10. Open technical points

1. **Production hosting.** To decide before the first public release. It must offer PostgreSQL 19 (see section 6).
2. **Storage provider.** Most likely Amazon S3. The code depends only on the S3 API.
