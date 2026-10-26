# Delivery plan — v1

The order in which v1 is built, one pull request at a time.
`docs/user-stories.md` says **what** to build. This file says **in what order** and **which PR does what**.
If the two disagree, the stories win. Fix this file in the same PR.

## 1. Where we are

Done:

- Django skeleton, settings and CI (backend only).
- Domain models and admin (PR #5). They already meet US-WR-02, US-WR-10, US-WR-11 and US-WR-14, and parts of the other WR stories.
- Figma export in `design/`.

Missing:

- the `search`, `api` and `site_shell` apps;
- the whole frontend (no `frontend/`, and no frontend targets in the Makefile or CI);
- uploading a text on an item's form, the OCR page check, rich text, the tagger.

## 2. How we work

1. **Pick the first open step** in section 4 whose "Needs" are merged. Steps in the same phase without a dependency between them can run in parallel.
2. **One step = one branch = one PR.** The branch name is in the table. A page story's PR contains its endpoint, its page and their tests (D11). The core owner reviews the core part (CODEOWNERS).
3. **Brief the agent** with the step's row and its story. For example: *"Implement step 21 of `docs/plan.md` (US-RA-04). Read AGENTS.md, the story, architecture §… and the design files listed."*
4. **Definition of done** is the one in `AGENTS.md`. In the same PR, tick the step's box in section 4.
5. **When in doubt, stop and ask.** This applies to an ambiguous story, a conflict with the docs, a new dependency, or a change to `docs/architecture.md`. Do not guess.
6. A human reviews and merges. An agent never merges.

## 3. Decisions

Answered by the project owner on 2026-10-26. Each one lands in the step named in the last column.

| # | Question | Decision | Step |
|---|----------|----------|------|
| D1 | Re-anchoring. Architecture §4.4 moves a fragment when its quote occurs once in the new text. US-WR-09 AC4 says "never silently moved". | **Move and flag.** If the quote occurs exactly once in the new text, move the fragment there and set `needs_review`. Otherwise only set `needs_review`. A moved fragment is never silent, so the story holds. Update architecture §4.4. | 4 |
| D2 | New dependencies. | **Approved.** Backend: `pypdf` (PDF page count). Frontend: the architecture §2 stack, plus `openapi-fetch`, Vitest, Testing Library, MSW, `vitest-axe`, ESLint, `typescript-eslint`, Prettier, `@fontsource/lora`, `@fontsource/cousine`, and the Radix packages shadcn/ui pulls in. Each PR still names the ones it adds. | 1, 6 |
| D3 | `django-prose-editor` has no type stubs. | **One mypy override** (`ignore_missing_imports` for that module) in `pyproject.toml`, with a comment saying why. | 10 |
| D4 | When the main typescript changes, the old one keeps its fragments. Are they public? | **Yes, they stay visible.** A fragment is visible when its owner is published, as in architecture §4.4. The tagger still offers only the main typescript (US-WR-09 AC1). | 2 |
| D5 | R-08 shows author and source for contextual materials, but US-WR-07 gives them no such fields. | **No new fields.** A contextual material shows its title only (R-02: empty parts are not rendered). | 21 |
| D6 | US-WR-01 AC2: how do editors get "the same rights"? | **A "Redaktorzy" group.** A data migration creates it with all `archive` model permissions. The administrator adds editors to it. | 12 |
| D7 | Where does the footer funding note come from? | **Hardcoded** in `frontend/src/copy/pl.ts`. Remove "editable funding note" from US-RA-03 AC1 and US-WR-11 AC1 (`user-stories.md` and `user-stories.pl.md`), remove `SiteSettings.funding_note` with a migration, and update architecture §4.2. | 13 |
| D8 | Who is the core owner? | **@natancamenzind.** Add `.github/CODEOWNERS` for `backend/archive/`, `backend/search/`, `backend/api/` and `**/migrations/`. A human adds the new CI jobs to the required checks on `main`. | 1 |
| D9 | Production hosting (architecture §10). | **Open.** It blocks only the last step. | 35 |
| D10 | Architecture §2 says frontend tests are "`tsc` + ESLint", but AGENTS.md requires Vitest with 90% coverage. | **AGENTS.md wins.** Fix architecture §2. | 1 |
| D11 | AGENTS.md says frontend work uses the API as it is. Who builds a page's endpoint? | **One PR per page story**, with its endpoint, page and tests. The core owner reviews the backend part. AGENTS.md is updated (done in the PR that adds this plan). | 13+ |

## 4. Steps

### Phase 1 — Foundations

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 1 | FE: frontend scaffold and serving | `fe/scaffold` | — | `frontend/` with Vite, React, TS strict, React Router, TanStack Query, Tailwind on `design/tokens/tokens.css`, shadcn/ui, fonts, Vitest + Testing Library + MSW + axe, ESLint, Prettier. `copy/pl.ts` with the Polish plural helper. The generated client from `make api-client`. `site_shell`: Django serves `index.html` for every non-API URL, and Vite proxies in dev. Makefile `dev`/`test`/`lint`/`typecheck`/`api-client` cover both sides. CI runs the frontend jobs. One placeholder route proves the chain works. `.github/CODEOWNERS` (D8). Fix architecture §2 (D10). |
| [ ] | 2 | CORE: shared queries | `core/shared-queries` | — | Querysets in `archive`, reused by every endpoint and by search: published only (R-06), visible fragments (owner published, D4), published tags only, the year of a work, tag occurrences, the works an item relates to, and the works a tag refers to (US-RA-07 AC5). The preview helper with `PREVIEW_LIMIT` (§4.5), and fragment number and start page. Tests only, no endpoints. |
| [ ] | 3 | CORE: search index | `core/search-index` | 2 | The `backend/search/` app: `SearchEntry`, writes and removals from `save()`/`delete()` (§6), `Edition` saves its work, `rebuild_search_index`, and a test that the `polish` config exists. A query service with tabs, filters, facet counts, sorting, snippets and the "no results" tags. No endpoint yet. Meets US-WR-04 AC4. |
| [x] | 4 | US-WR-09 AC4: flag every moved fragment | `us-wr-09-reanchor` | — | `Fragment.reanchor()` sets `needs_review` whenever it moves a fragment (D1). Update architecture §4.4. |
| [ ] | 5 | DEV: demo data | `dev/demo-data` | 3 | `manage.py load_demo_data` loads the sample data from `design/rules.md`, including small committed PDF and OCR fixtures. It uses `save()` only, so the search index is filled. Every later PR is verified by hand with it. |

### Phase 2 — Editor panel (can run in parallel with Phase 3)

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 6 | US-WR-04: typescript text upload | `us-wr-04-typescript-upload` | 3 | Scan and OCR file on the typescript form, with the page-count check and its message (AC2). The upload is built so steps 7–9 can reuse it. |
| [ ] | 7 | US-WR-05: note content | `us-wr-05-note-content` | 6 | All five content kinds on the note form, with OCR or plain text entered on that form. |
| [ ] | 8 | US-WR-06: secondary text text | `us-wr-06-secondary-text` | 6 | OCR or plain text on the secondary text form. |
| [ ] | 9 | US-WR-07: contextual material content | `us-wr-07-material-content` | 6 | As in step 7, for contextual materials. |
| [ ] | 10 | CORE: rich text (US-WR-03, 08, 12) | `core/rich-text` | 3 | `ProseEditorField` for descriptions, with the mypy override (D3),, the About project text and the introductions. Search strips HTML from `body`. |
| [ ] | 11 | US-WR-09: tagger | `us-wr-09-tagger` | 4 | The tagger admin view (§5) and `/api/editor/fragments/`. Offered only for the main typescript and for notes, secondary texts and materials that have a text. |
| [ ] | 12 | US-WR-01: editors group | `us-wr-01-editors` | — | A data migration for the "Redaktorzy" group, and tests for both ACs. |

### Phase 3 — Public site: shell and simple pages

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 13 | US-RA-03: header, navigation, footer | `us-ra-03-footer` | 1 | The page shell from R-07 on desktop and mobile, the active navigation item. The funding note is hardcoded in `copy/pl.ts`; in this PR, update the stories, remove `SiteSettings.funding_note` and update architecture §4.2 (D7). The header search field comes in step 28. |
| [ ] | 14 | US-RA-13: About | `us-ra-13-about` | 13 | `/api/about/`, the About page. |
| [ ] | 15 | US-RA-18: works list | `us-ra-18-works-list` | 2, 13 | `/api/works/`, the work card, the list page. |
| [ ] | 16 | US-RA-20: tags list | `us-ra-20-tags-list` | 2, 13 | `/api/tags/`, the deterministic tag cloud, the alphabetical index. |
| [ ] | 17 | US-RA-01: home page | `us-ra-01-home` | 15, 16 | `/api/home/`, the hero with counts and portrait, works, tag cloud. |
| [ ] | 18 | US-RA-19: typescripts list | `us-ra-19-typescripts-list` | 2, 13 | `/api/typescripts/`, grouped by work. Order shelfmarks as numbers, not strings. |

### Phase 4 — Entity pages

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 19 | US-RA-08: typescript page | `us-ra-08-typescript-page` | 5, 18 | `/api/typescripts/<id>/`, `/api/documents/<id>/`. The shared parts first built here: subpage layout (R-05), section header and preview (R-09), the reader (R-11) with `pdfjs-dist`, the text renderer (§4.4), the mobile toggle, `?fragment=`. |
| [ ] | 20 | US-RA-09: reading the full typescript | `us-ra-09-full-typescript` | 19 | The reader handles a long typescript: pages render as they scroll into view. Fragments are highlighted wherever they exist (D4). |
| [ ] | 21 | US-RA-04: work page | `us-ra-04-work-page` | 19 | `/api/works/<slug>/`. Built here: the fragment card (R-10) with page thumbnail, the note card, the contextual materials block (R-08), where a contextual material shows its title only (D5). |
| [ ] | 22 | US-RA-05: relation tags | `us-ra-05-relation-tags` | 21 | Work link tags in the work page's tag column. |
| [ ] | 23 | US-RA-07: tag page | `us-ra-07-tag-page` | 21 | `/api/tags/<slug>/`, the tag page. |
| [ ] | 24 | US-RA-10: secondary text page | `us-ra-10-secondary-text-page` | 21 | `/api/secondary-texts/<id>/`. Built here: the "Powiązane fragmenty" query (shared tags), reused in steps 25–26. |
| [ ] | 25 | US-RA-11: note page | `us-ra-11-note-page` | 24 | `/api/notes/<id>/`, the content by type: image, PDF, download, embed or link, reader. |
| [ ] | 26 | US-RA-12: contextual material page | `us-ra-12-material-page` | 25 | `/api/materials/<id>/`. |
| [ ] | 27 | US-RA-06: drill-down from a work | `us-ra-06-drill-down` | 22, 23, 26 | A test that every item on the work page links to an existing page; fix any that don't. |
| [ ] | 28 | US-WR-13: preview a draft | `us-wr-13-draft-preview` | 26 | Entity endpoints return drafts to staff with `is_draft`. The banner "Szkic — niewidoczny publicznie". Anonymous readers get 404. |

### Phase 5 — Search

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 29 | US-RA-14: search entry | `us-ra-14-search-entry` | 3, 13 | The header field (the icon on mobile), the `/search` page shell, the hint text. |
| [ ] | 30 | US-RA-15: search results | `us-ra-15-search-results` | 29, 21 | `/api/search/`, groups, sorting, snippets, the loading state, no results. Opening a result scrolls to the first match (`?q=`, R-11 AC3). |
| [ ] | 31 | US-RA-16: tabs and filters | `us-ra-16-search-filters` | 30 | Tabs, filters, facet counts, the mobile filter panel, state kept in the URL, the empty query. |

### Phase 6 — Should

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 32 | US-RA-02: featured fragment | `us-ra-02-featured-fragment` | 17, 21, 31 | A random featured fragment on the home page, linking to the filtered search. |
| [ ] | 33 | US-RA-17: autocomplete | `us-ra-17-autocomplete` | 29 | `/api/search/autocomplete/` and the suggestions under the field. |

### Phase 7 — Release

| ✓ | # | PR | Branch | Needs | Scope |
|---|---|----|--------|-------|-------|
| [ ] | 34 | CORE: per-URL meta tags | `core/meta-tags` | 28 | `site_shell` sets `<title>` and the meta description for every route (user stories §4: SEO). |
| [ ] | 35 | Production setup | `ops/production` | D9 (open) | Production settings and deployment notes for the chosen host. |

## 5. Story coverage

| Story | Step | Story | Step |
|-------|------|-------|------|
| US-RA-01 | 17 | US-WR-01 | 12 |
| US-RA-02 (Should) | 32 | US-WR-02 | done (PR #5) |
| US-RA-03 | 13 (story changed, D7) | US-WR-03 | 10 (rest done) |
| US-RA-04 | 21 | US-WR-04 | 6; AC3 done; AC4 in 3 |
| US-RA-05 | 22 | US-WR-05 | 7 |
| US-RA-06 | 27 | US-WR-06 | 8 |
| US-RA-07 | 23 | US-WR-07 | 9 |
| US-RA-08 | 19 | US-WR-08 | 10 (rest done) |
| US-RA-09 | 20 | US-WR-09 | 4, 11 |
| US-RA-10 | 24 | US-WR-10 | done (PR #5) |
| US-RA-11 | 25 | US-WR-11 | done (PR #5); funding note removed in 13 |
| US-RA-12 | 26 | US-WR-12 | 10 (rest done) |
| US-RA-13 | 14 | US-WR-13 | AC1 done; 28 |
| US-RA-14 | 29 | US-WR-14 | done (PR #5) |
| US-RA-15 | 30 | | |
| US-RA-16 | 31 | | |
| US-RA-17 (Should) | 33 | | |
| US-RA-18 | 15 | | |
| US-RA-19 | 18 | | |
| US-RA-20 | 16 | | |

Rules R-01 to R-12 have no step of their own. Each page step meets them for its page.

## 6. Reminders for every step

- **Stories beat Figma** (open question 5). Figma has no reader, no note page and no contextual material page, and its fragment card shows a scan crop. Build these from the stories, using the existing Figma components.
- **Mobile is part of each page step**, not a separate PR. `design/rules.md` → Siatka gives the order.
- **Shared UI parts** (layout, section header, fragment card, reader, contextual materials block) are built in the step named above and reused after that, never rebuilt.
- **Each component test runs the axe check** (R-12). Polish copy lives in `copy/pl.ts` and counts use the plural helper.
- **Draft tags are never shown**: not as chips, not in the cloud, not in counts. Step 3's querysets handle this.
- **Links to pages built later are fine.** Step 28 checks them all.
- **Descriptions are HTML** once step 10 lands. Render them as the sanitized HTML the API returns.
- A page step builds only its own endpoint. If it needs anything else from the backend, say so in the PR (AGENTS.md). A change to `docs/architecture.md` needs asking first.
