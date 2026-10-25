# User Stories — Archivum Buczkovianum

> Derived from `docs/brief.md`. Each story has an ID, scope and acceptance criteria (AC).
> A story is done when every AC passes. Agents take one story per task and reference its ID in the branch name and PR title.

## Conventions

**Roles**

- **RA — Relational Archivist.** Anonymous public reader. Never logs in.
- **WR — Editor.** Logged-in user working in Django admin. All editors have the same permissions.

**Scope**

- **v1** — first version.
- **Later** — out of scope for v1; listed so that nobody builds it by accident.

**Priority** (within v1)

- **Must** — required for v1.
- **Should** — build if it fits; v1 can ship without it.

**Glossary** (Polish term in parentheses)

| Term | Meaning |
|------|---------|
| Work (utwór) | A literary work as an idea, independent of any edition or document. |
| Edition (wydanie) | A published edition of a work. |
| Typescript (maszynopis) | A typescript version of a work: scan + OCR text. Belongs to exactly one work. |
| Main typescript | The one typescript per work that is fragment-tagged and highlighted on the work page. |
| Note (zapisek) | Manuscript material: manuscripts, drafts, notes. Can relate to many works. |
| Secondary text (tekst sekundarny) | Review, opinion, letter or letter fragment. Can relate to many works. |
| Contextual material (materiał kontekstowy) | Any medium plus description. Can relate to many works. |
| Tag | A name for a relation: a Buczkowski keyword or an editorial interpretation. |
| Fragment | A tagged character range within a text (OCR or plain text). |
| Work link | The relation between a work and a secondary text or contextual material. A work link can itself be tagged. |
| Content page | A free-form text page (about the team, about the project, conference…). |

---

## 1. Cross-cutting rules

These rules apply to every public page. Stories reference them instead of repeating them.

**R-01 Navigation (Must, v1).** Every entity shown on a page links to that entity's own page. From any page the RA can reach any entity it displays.

**R-02 Empty blocks (Must, v1).** If a page has no content for a block (e.g. no notes), the block is not rendered at all: no heading, no empty state.

**R-03 Related works (Must, v1).** Every entity page except the work page shows a list of related works. The work page shows the list of editions instead.

**R-04 Uniform representation (Must, v1).** Every entity has a type label and a title. Wherever an entity is listed outside its own page (search results, relation lists), it is shown as `type: title`.

**R-05 Relation component (Must, v1).** A reusable block of related entities, rendered on the tag, typescript, secondary text, note and contextual material pages. It contains, in this order:

1. tags,
2. highlighted typescript fragment,
3. typescripts,
4. highlighted note,
5. notes,
6. gallery of visual contextual materials.

Which entities count as "related" is defined per page.

**R-06 Published only (Must, v1).** The public site shows only entities with status `published`. Draft entities are invisible: not listed, not searchable, and their URLs return 404.

**R-07 Common layout (Must, v1).** Every public page has the global menu and footer.

---

## 2. Archivist (RA)

### 2.1 Home page

**US-RA-01 — Home page (Must, v1)**
As an RA, I land on a home page that introduces Buczkowski and lets me start exploring.

AC:
1. The page shows, in order: menu; the title "Archivum Buczkovianum"; an introduction (short text about LB plus a large portrait); a gallery of works; a tag cloud; the footer.
2. The background shows a slowly animated epicycloid. The animation respects `prefers-reduced-motion` (static when reduced motion is requested).
3. Gallery of works: one tile per published work showing its cover image (book or typescript cover). Clicking a tile opens the work page.
4. Tag cloud: all published tags that have at least one tagged item. Tag size reflects the number of tagged items. Clicking a tag opens the tag page.
5. Introduction text and portrait are editable by WR (US-WR-11).

**US-RA-02 — Featured fragments on home page (Should, v1)**
As an RA, I see a few featured fragments on the home page.

AC:
1. Shows the fragments WR marked as featured on the home page (US-WR-11), each with its source in `type: title` form.
2. Clicking a fragment opens the source document scrolled to that fragment.

**US-RA-03 — Footer (Must, v1)**
AC:
1. The footer shows the funding note (editable by WR), a link to the team page and a link to the project page.

### 2.2 Work page

**US-RA-04 — Key information about a work (Must, v1)**
As an RA, I see the body of information about a work, with only the key information at first glance.

AC:
1. Title displayed over a hero image, selected by WR from the work's contextual materials.
2. Short description (editorial text).
3. List of editions.
4. Tags of the work: tags on the work itself plus relation tags on its work links (see US-RA-05).
5. Highlighted fragment of the main typescript. Clicking it opens the typescript page scrolled to that fragment.
6. List of typescripts. Clicking one opens its typescript page.
7. Highlighted note: the note WR marked as featured for this work, showing the fragment WR chose for this work link.
8. List of notes related to the work.
9. Gallery of visual contextual materials related to the work.
10. R-02 applies to each block.

**US-RA-05 — Relation tags on a work page (Must, v1)**
As an RA, I see how secondary texts and contextual materials relate to the work.

AC:
1. If a work link (work ↔ secondary text, or work ↔ contextual material) carries tags, those tags appear in the work's tag list.
2. Each relation tag shown on the work page links to the tag page.

**US-RA-06 — Drill-down from a work (Must, v1)**
As an RA, I can open a dedicated page for each tag, typescript, note, secondary text and contextual material shown on the work page.

AC:
1. Every item in blocks 4–9 of US-RA-04 links to its own page (R-01).

### 2.3 Tag page

**US-RA-07 — Tag page (Must, v1)**
As an RA, I see everything connected to a tag.

AC:
1. Title displayed over an image selected by WR (preferably a contextual material).
2. Tag description (a biography or a short scholarly note).
3. Tag kind: "Buczkowski's keyword" or "interpretation".
4. Links to every work the tag refers to. A tag refers to a work if it is applied to the work, to any entity related to the work, to a fragment of such an entity, or to a work link of that work.
5. Several highlighted tagged fragments from typescripts. Each shows the fragment text and its source, and links to the typescript page scrolled to the fragment.
6. Related tags (symmetric, untyped).
7. Relation component (R-05), where "related" means: entities tagged with this tag, as a whole or by fragment.

### 2.4 Typescript page

**US-RA-08 — Typescript page (Must, v1)**
As an RA, I read a typescript and see what it relates to.

AC:
1. Title and optional description.
2. Highlighted related content: the first tagged fragment of this typescript, if any.
3. Related works (R-03).
4. Relation component (R-05), where "related" means: entities sharing at least one tag with this typescript or its fragments.

**US-RA-09 — Reading the full typescript (Must, v1)**
As an RA, I read the whole typescript with scan and text side by side.

AC:
1. Each scan page is shown next to the OCR text of the same page. The whole document scrolls continuously.
2. In the main typescript, tagged fragments are highlighted in the text. Clicking a highlight shows its tags; each tag links to its tag page.
3. Opening the page with a fragment reference scrolls to that fragment and highlights it.

### 2.5 Secondary text page

**US-RA-10 — Secondary text page (Must, v1)**
As an RA, I see a secondary text and its relations.

AC:
1. Title over an image selected by WR (optional). For a letter: date and sender/recipient.
2. Optional description.
3. Highlighted related content: the fragment WR marked as highlighted (e.g. a letter fragment).
4. Full text (OCR or plain), with tagged fragments highlighted as in US-RA-09 AC2.
5. Related works (R-03).
6. Relation component (R-05), with the same definition of "related" as US-RA-08.

### 2.6 Note page

**US-RA-11 — Note page (Must, v1)**
Not detailed in the brief; defined by analogy with the typescript and secondary text pages.

AC:
1. Title and optional description.
2. Content rendered by type:
   - image: shown inline,
   - document: shown inline if PDF, otherwise as a download,
   - external audio/video link: embedded player if the provider allows it, otherwise a link,
   - OCR text: shown next to the scan, as in US-RA-09,
   - plain text: rendered as text.
3. Tagged fragments are highlighted as in US-RA-09 AC2.
4. Related works (R-03).
5. Relation component (R-05), with the same definition of "related" as US-RA-08.

### 2.7 Contextual material page

**US-RA-12 — Contextual material page (Must, v1)**
Not detailed in the brief; defined by analogy with the note page.

AC:
1. Title and optional description.
2. Content rendered by type, as in US-RA-11 AC2.
3. Related works (R-03).
4. Relation component (R-05), with the same definition of "related" as US-RA-08.

### 2.8 Content pages

**US-RA-13 — Content page (Must, v1)**
As an RA, I read text pages such as "About the team" and "About the project".

AC:
1. Hero with title, a graphic, and a rich-text body.
2. Menu and footer (R-07).
3. v1 ships with at least the team page and the project page.

### 2.9 Search

**US-RA-14 — Search entry (Must, v1)**
AC:
1. The initial search state shows only a search field with a magnifying-glass icon; no results.
2. Search is reachable from the menu on every page.

**US-RA-15 — Search results (Must, v1)**
As an RA, I find works, tags and fragments by typing a phrase.

AC:
1. All published entities are indexed: titles, descriptions, tag names and descriptions, OCR texts and plain texts.
2. Ranking:
   - work titles first,
   - then tags,
   - then occurrences in texts; more occurrences rank higher.
3. Each result has the form `type: title` (R-04) and is clickable.
4. For a match inside a larger object, the result shows the matching snippet with the search terms highlighted. Clicking it opens the object scrolled to the match.
5. Results for works show no snippet.
6. Search handles Polish inflection: e.g. "potoku" finds "potok".

**US-RA-16 — Search scope (Must, v1)**
AC:
1. An advanced option limits the search to: everywhere (default), tags only, or typescripts only.
2. An empty query returns all entities in the selected scope.

**US-RA-17 — Autocomplete (Should, v1)**
AC:
1. While typing (e.g. "czarny p…"), the field suggests matching work titles and tag names.
2. Choosing a suggestion opens that entity's page.

---

## 3. Editor (WR)

All editor stories take place in Django admin.

**US-WR-01 — Log in (Must, v1)**
AC:
1. An editor logs in with an account created by the administrator. There is no public registration.
2. All editors have identical permissions.

**US-WR-02 — Draft and publish (Must, v1)**
As a WR, I prepare content before it goes public.

AC:
1. Every entity has a status: `draft` (default) or `published`.
2. Only published entities are public (R-06).

**US-WR-03 — Add a work (Must, v1)**
AC:
1. Fields:
   - title (required),
   - description (rich text),
   - cover image for the home page gallery,
   - bibliography (rich text with links).
2. Editions are added inline. Each edition has publisher, place, year and an optional cover image.
3. Hero image: chosen from the contextual materials linked to this work.
4. Featured note: chosen from the notes linked to this work.

**US-WR-04 — Add a typescript (Must, v1)**
AC:
1. Fields:
   - parent work (required, must already exist),
   - title (required),
   - description (optional),
   - scan file (required),
   - OCR file (required).
2. The system validates that the OCR file has the same number of pages as the scan. If not, the save is rejected with a message stating both page counts.
3. A checkbox marks the typescript as the main typescript of its work. Only one typescript per work can be main; marking a new one unmarks the previous one.
4. Saving updates the search index.

**US-WR-05 — Add a note (Must, v1)**
AC:
1. Fields: title (required), optional description, content.
2. Content is one of:
   - image,
   - document,
   - external audio/video link,
   - OCR text (scan + OCR file, validated as in US-WR-04 AC2),
   - plain text (e.g. a letter transcription).
3. Linked to one or more works.
4. For each work link, the editor selects which fragment is highlighted on that work's page.

**US-WR-06 — Add a secondary text (Must, v1)**
AC:
1. Fields:
   - title (required),
   - optional description,
   - optional date and sender/recipient (for letters),
   - text as OCR (scan + OCR file) or plain text.
2. Linked to one or more works. Each work link can carry tags (US-WR-10).
3. The editor marks one fragment as highlighted (shown in US-RA-10 AC3).

**US-WR-07 — Add a contextual material (Must, v1)**
AC:
1. Fields: title (required), optional description, content.
2. Content is one of: image, document, external audio/video link, OCR text, plain text.
3. Linked to one or more works. Each work link can carry tags (US-WR-10).
4. Images are available for selection as hero images (US-WR-03, US-WR-08).

**US-WR-08 — Manage tags (Must, v1)**
AC:
1. Fields:
   - name (required, unique),
   - kind: "Buczkowski's keyword" or "interpretation" (required),
   - description (rich text: a biography or a short scholarly note),
   - image for the tag page header.
2. Related tags: selecting tag B as related to tag A makes A related to B automatically.
3. A tag cannot be deleted while it is applied anywhere. The error lists where it is used.

**US-WR-09 — Tag fragments (Must, v1)**
As a WR, I tag fragments of texts by selecting them.

AC:
1. Available for: the main typescript, notes with OCR or plain text, and secondary texts.
2. The editor selects a text range in the tagging screen and assigns one or more existing tags to it.
3. Fragments may overlap. The same text can carry several tags.
4. A fragment stores the selected text. If the underlying text changes and the fragment no longer matches, the fragment is flagged for review, not silently moved or deleted.
5. No manual markup (TEI or otherwise) is ever required from the editor.

**US-WR-10 — Tag whole entities and work links (Must, v1)**
AC:
1. Any work, typescript, note, secondary text or contextual material can be tagged as a whole.
2. A work link (work ↔ secondary text, work ↔ contextual material) can be tagged. These tags appear on the work page (US-RA-05).

**US-WR-11 — Edit home page and footer content (Must, v1)**
AC:
1. Editable fields:
   - introduction text,
   - portrait image,
   - funding note in the footer,
   - featured fragments (selected from existing tagged fragments; Should, follows US-RA-02).

**US-WR-12 — Manage content pages (Must, v1)**
AC:
1. Fields:
   - title,
   - slug (URL),
   - hero text,
   - graphic,
   - body (rich text).
2. A new content page can be created at any time without code changes (e.g. a conference page).
3. The editor chooses whether the page appears in the menu.

---

## 4. Later (out of scope for v1)

- **Ukrainian version.** A separate, structurally similar, simplified service. A menu and footer marker switches to it and always lands on its home page. Relations between language versions of a work (e.g. "Czarny potok" PL ↔ UA) live in the Ukrainian service.
- **SEO decision.** v1 serves per-URL title and description meta tags only.
- **TEI export.**

Explicitly rejected:

- A dedicated subpage for a letter fragment.

---

## 5. Open questions

Each question lists the default that the stories above already assume.

1. **Bibliography.** The brief lists it in the ontology but not among the work page blocks. *Default: a rich-text field on the work, shown below the key information.*
2. **Tag metadata record (metryczka).** What fields does it have beyond name, kind, description and image? *Default: none.*
3. **Highlighted typescript fragment on the work page.** *Default: the first tagged fragment of the main typescript, unless WR marks a different one.*
4. **"Related" in the relation component.** *Default: entities sharing at least one tag (US-RA-08 AC4).*
5. **Scan and OCR formats.** *Default: scan as PDF; OCR as UTF-8 text with one page separator per page. To be fixed in `architecture.md`.*
6. **Ordering of lists.** *Default: editions by year; all other lists by title.*
7. **Video and audio.** The brief keeps them hosted elsewhere for notes. *Default: same rule for contextual materials, so no media uploads except images and documents.*
8. **Example of a tagged relation.** Still to be found by the editors.
