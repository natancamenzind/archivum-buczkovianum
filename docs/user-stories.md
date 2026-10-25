# User Stories — Archivum Buczkovianum

> Derived from `docs/PROJECT_BRIEF.md` and the Figma file "archiwum-buczkowski-model", page "po korekcie" (sections 01, 04, 05). Each story has an ID, scope and acceptance criteria (AC).
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

**Glossary** (Polish UI term in parentheses; the UI uses only these terms)

| Term | Meaning |
|------|---------|
| Work (utwór) | A literary work as an idea, independent of any edition or document, e.g. "Wertepy". |
| Edition (wydanie) | A published edition of a work: year, publisher, place. |
| Typescript (maszynopis) | An archival unit holding a typescript of a work: scan + OCR text. Belongs to exactly one work. |
| Main typescript | The one typescript per work that is fragment-tagged. Its fragments are shown on the work page. |
| Note (zapisek) | The author's manuscript material: a notebook page, a card, a draft. Can relate to many works. |
| Secondary text (tekst sekundarny) | A review, study, letter or recording about the work. Can relate to many works. |
| Contextual material (materiał kontekstowy) | Any medium plus a description. Can relate to many works. |
| Visual material (materiał wizualny) | A contextual material whose content is an image: a photo or an illustrative scan. |
| Tag | A motif linking fragments and notes: a Buczkowski keyword or an editorial interpretation. |
| Occurrence (wystąpienie) | One published item carrying a tag: a fragment, a whole entity, or a work link. |
| Fragment | A tagged character range within a text (OCR or plain text), with an optional shelfmark, location and description. |
| Shelfmark (sygnatura) | Institution plus number, shown as "ML, sygn. 1618". A fragment has its own number ("ML, sygn. 1618.0009") and inherits the institution of its document. |
| Work link | The relation between a work and a secondary text or contextual material. A work link can itself be tagged. |

---

## 1. Cross-cutting rules

These rules apply to every public page. Stories reference them instead of repeating them.

**R-01 Navigation (Must, v1).** Every entity shown on a page links to that entity's own page. From any page the RA can reach any entity it displays. A fragment has no page of its own: it links to its source document, scrolled to the fragment.

**R-02 Empty blocks (Must, v1).** If a page has no content for a block (e.g. no notes), the block is not rendered at all: no heading, no empty state.

**R-03 Related works (Must, v1).** Every entity page except the work page shows the list of related works in its context column. The work page shows the list of editions there instead.

**R-04 Uniform representation (Must, v1).** Every entity has a type label and a title. Wherever an entity is listed outside its own page (search results, lists, cards), its type label is shown with its title.

**R-05 Subpage layout (Must, v1).** Every entity page (work, typescript, tag, note, secondary text, contextual material) has the same structure:

1. a dark hero band with a type line (e.g. "Utwór · Leopold Buczkowski · 1947"), the title and the description,
2. a context column on the left (R-03 and other context defined per page),
3. the main column with content blocks defined per page,
4. a tag column on the right,
5. the contextual materials block (R-08) below the columns, where the page defines one.

On mobile the columns stack in this order: main content, context, tags, contextual materials.

**R-06 Published only (Must, v1).** The public site shows only entities with status `published`. For anonymous readers, draft entities are invisible: not listed, not searchable, and their URLs return 404. A logged-in editor opening a draft's URL sees the page with a "draft" banner (US-WR-13). Drafts never appear in lists, previews or search, even for editors.

**R-07 Common layout (Must, v1).** Every public page has:

1. a header with the service name and subtitle (link to the home page), the "O archiwum" link and the search field;
2. the main navigation: Strona główna, Utwory, Maszynopisy, Tagi. On desktop it sits in the footer; on mobile it is a bottom bar, and search is an icon in the header;
3. a footer with the service name, the main navigation (desktop) and the funding note.

The active navigation item follows the page type: home → Strona główna; work and works list → Utwory; typescript and typescripts list → Maszynopisy; tag and tags list → Tagi. Other pages have no active item.

**R-08 Contextual materials block (Must, v1).** A block titled "Materiały kontekstowe" with two parts:

1. "Teksty sekundarne": a numbered list of secondary texts and non-image contextual materials, each as author and title on one line and source (publisher, place, year, pages) on the next;
2. "Materiały wizualne": a gallery of visual materials, each with a thumbnail and a caption made of title and shelfmark.

Which items count is defined per page.

**R-09 Counters and previews (Must, v1).** A section header shows a counter: the number of items ("3"), or shown out of all ("2 z 24") when the section is a preview. A preview shows the first `PREVIEW_LIMIT` items (one setting, default 2): featured fragments first, then the rest in text order. A preview ends with a link that names its target and count, e.g. "Wszystkie fragmenty (24)". Counts use correct Polish plural forms (1 fragment, 2–4 fragmenty, 5+ fragmentów).

**R-10 Fragment card (Must, v1).** Wherever a fragment is shown, it uses one card:

1. the location line: work, fragment number in its document ("fragment 01") and optional location ("rozdział I"); a type chip with the source type ("Maszynopis", "Zapisek");
2. the quote (the fragment text, shortened to a few lines) and, for an OCR source, a thumbnail of the scan page the fragment starts on;
3. the shelfmark, the description and the fragment's tags.

Clicking the card opens the source document scrolled to the fragment.

**R-11 Reader (Must, v1).** Every OCR document (typescript, note, secondary text, contextual material) is read in one reader:

1. On desktop each scan page is shown next to the OCR text of the same page, and the whole document scrolls continuously. On mobile a toggle switches between "Skan" and "Transkrypcja".
2. Fragments are highlighted in the text. Clicking a highlight shows its tags; each tag links to its tag page.
3. Opening the page with a fragment reference scrolls to that fragment and highlights it. Opening it from a search result scrolls to the first match.

A plain-text document is shown as text, with fragments highlighted as in point 2.

**R-12 Accessibility (Must, v1).** Public pages meet WCAG 2.1 AA. Every image has a text alternative entered by WR. Animations respect `prefers-reduced-motion`. Every control can be used from the keyboard and has an accessible name (e.g. the filter panel's close icon is labelled "Zamknij filtry").

---

## 2. Archivist (RA)

### 2.1 Home page

**US-RA-01 — Home page (Must, v1)**
As an RA, I land on a home page that introduces Buczkowski and lets me start exploring.

AC:
1. The page shows, in order: header; hero; works; featured fragment (US-RA-02); tag cloud; footer (R-07).
2. Hero: the title "Archivum Buczkovianum" and the introduction text over the portrait of Buczkowski, plus statistics: the number of published works, visible fragments and published tags ("4 utwory · 62 fragmenty · 12 tagów").
3. Works: one card per published work, in order of first edition, with cover image, genre and year, title, author and the number of fragments. Clicking a card opens the work page.
4. Tag cloud: every published tag with at least one occurrence. Size has five steps by occurrence count: 1–3, 4–7, 8–15, 16–25, 26+. Steps 4–5 use the accent colour. The layout is deterministic: the same data always gives the same cloud. Clicking a tag opens the tag page.
5. Introduction text and portrait are editable by WR (US-WR-11).

**US-RA-02 — Featured fragment on home page (Should, v1)**
As an RA, I see one fragment chosen by the editors.

AC:
1. Shows one fragment, chosen at random from the visible fragments WR marked as featured (US-WR-09 AC6), as a fragment card (R-10). The counter shows "1 z <all visible fragments>".
2. Below the card, a link to all fragments of that fragment's work: "Wszystkie fragmenty „<work>” (n)", which opens search with the Fragmenty tab and that work selected (US-RA-16).

**US-RA-03 — Footer (Must, v1)**
AC:
1. The footer shows the service name and subtitle, the main navigation on desktop (R-07) and the funding note (editable by WR, US-WR-11).

### 2.2 Work page

**US-RA-04 — Work page (Must, v1)**
As an RA, I see the body of information about a work, with only the key information at first glance.

AC:
1. Hero (R-05): type line "Utwór · Leopold Buczkowski · <year of first edition>", title, description.
2. Context column: editions, ordered by year. Each shows year, publisher and place; the earliest is labelled "pierwsze wydanie".
3. Main column, in order:
   1. "Fragmenty maszynopisu": a preview (R-09) of the fragments of the main typescript, as fragment cards (R-10), linking to all of them;
   2. "Maszynopisy": a numbered list of the work's typescripts; each opens its typescript page;
   3. "Zapiski": the notes linked to the work, each as a card with location line, type chip, image (or a placeholder), shelfmark, description and tags.
4. Tag column: every published tag that refers to the work, by the definition in US-RA-07 AC5. This includes tags on the work itself, relation tags on its work links (see US-RA-05), and tags on related entities and their fragments.
5. Contextual materials block (R-08): the secondary texts and contextual materials linked to the work.
6. R-02 applies to each block.

**US-RA-05 — Relation tags on a work page (Must, v1)**
As an RA, I see how secondary texts and contextual materials relate to the work.

AC:
1. If a work link (work ↔ secondary text, or work ↔ contextual material) carries tags, those tags appear in the work's tag column.
2. Each relation tag shown on the work page links to the tag page.

**US-RA-06 — Drill-down from a work (Must, v1)**
As an RA, I can open a dedicated page for each tag, typescript, note, secondary text and contextual material shown on the work page.

AC:
1. Every item in the main column, tag column and contextual materials block of US-RA-04 links to its own page, or for a fragment to its place in the source (R-01).

### 2.3 Tag page

**US-RA-07 — Tag page (Must, v1)**
As an RA, I see everything connected to a tag.

AC:
1. Hero (R-05): type line "Tag · <n> wystąpień w <m> utworach" (with correct plural forms), title, description (a biography or a short scholarly note). The tag kind is not shown.
2. Context column: "Utwory", every work the tag refers to, ordered by first edition. Each shows year, title and the number of its fragments carrying the tag.
3. Main column, in order:
   1. "Fragmenty z tagiem": every visible fragment carrying the tag, as fragment cards (R-10), ordered by the work's first edition and then by position in the text;
   2. "Zapiski z tagiem": every note carrying the tag, as a whole or by fragment, as note cards (US-RA-04 AC3).
4. Tag column: "Powiązane tagi", the related tags (symmetric, untyped).
5. A tag refers to a work if it is applied to the work, to any entity related to the work, to a fragment of such an entity, or to a work link of that work.
6. Contextual materials block (R-08): secondary texts and contextual materials carrying the tag, as a whole, by fragment, or on their work link.

### 2.4 Typescript page

**US-RA-08 — Typescript page (Must, v1)**
As an RA, I read a typescript and see what it relates to.

AC:
1. Hero (R-05): type line "Maszynopis · <shelfmark> · <year of the work>", title, optional description.
2. Context column: the work (R-03), with year and fragment count; "Maszynopisy utworu", every typescript of the same work with shelfmark and title, the current one marked.
3. Main column, in order:
   1. "Skan maszynopisu": the reader (R-11), with the page count in the counter;
   2. "Fragmenty z maszynopisu": a preview (R-09) of its fragments as a numbered list of fragment number, location and shelfmark, in page order, linking to all of them.
4. Tag column: tags on the typescript and on its fragments.
5. Contextual materials block (R-08): the secondary texts and contextual materials linked to its work.

**US-RA-09 — Reading the full typescript (Must, v1)**
As an RA, I read the whole typescript with scan and text side by side.

AC:
1. The typescript is read in the reader (R-11). Only the main typescript has fragments to highlight.

### 2.5 Secondary text page

**US-RA-10 — Secondary text page (Must, v1)**
As an RA, I see a secondary text and its relations.

AC:
1. Hero (R-05): type line with the kind and, for a letter, sender and date ("List · Leopold Buczkowski · 1.10.1947"); title; description. There is no header image.
2. Context column: "Powiązane utwory" (R-03).
3. Main column, in order:
   1. "Transkrypcja": the full text in the reader (R-11), or as plain text;
   2. "Powiązane fragmenty": a preview (R-09) of typescript fragments that share at least one tag with this text or its fragments, as fragment cards (R-10). There is no "all" link.
4. Tag column: "Powiązane tagi", tags on the text, on its fragments and on its work links.

### 2.6 Note page

**US-RA-11 — Note page (Must, v1)**
Not drawn in Figma; uses the secondary text page layout.

AC:
1. Hero (R-05): type line "Zapisek · <shelfmark>", title, optional description.
2. Context column: related works (R-03).
3. Main column, in order:
   1. the content, rendered by type:
      - image: shown inline,
      - document: shown inline if PDF, otherwise as a download,
      - external audio/video link: embedded player if the provider allows it, otherwise a link,
      - OCR text or plain text: the reader (R-11);
   2. "Powiązane fragmenty", as in US-RA-10 AC3.
4. Tag column: tags on the note and on its fragments.

### 2.7 Contextual material page

**US-RA-12 — Contextual material page (Must, v1)**
Not drawn in Figma; uses the secondary text page layout.

AC:
1. Hero (R-05): type line with the kind and shelfmark, title, optional description.
2. Context column: related works (R-03).
3. Main column: the content, rendered by type as in US-RA-11 AC3, then "Powiązane fragmenty" as in US-RA-10 AC3.
4. Tag column: tags on the material, on its fragments and on its work links.

### 2.8 Lists

**US-RA-18 — Works list (Must, v1)**
AC:
1. Reached from "Utwory" in the main navigation (R-07).
2. A grid of work cards (US-RA-01 AC3) of every published work, in order of first edition, with the count in the header.

**US-RA-19 — Typescripts list (Must, v1)**
AC:
1. Reached from "Maszynopisy" in the main navigation (R-07).
2. Every published typescript, grouped by work (works in order of first edition), two cards per row on desktop. Each group shows the work's title, genre, year and count; each card shows the number, title and shelfmark and opens the typescript page.

**US-RA-20 — Tags list (Must, v1)**
AC:
1. Reached from "Tagi" in the main navigation (R-07).
2. The tag cloud (US-RA-01 AC4), then "Wszystkie tagi": every published tag in alphabetical order with its occurrence count ("4 wystąpienia").

On mobile all three lists use one column of the same components.

### 2.9 About page

**US-RA-13 — About page (Must, v1)**
As an RA, I read about the project and the team.

AC:
1. Reached from "O archiwum" in the header (R-07).
2. Hero with the title "O archiwum" and an introduction.
3. "O projekcie": rich text about the goal, scope, partner institutions and funding.
4. "Zespół": team members in three groups, in this order: "Kierownictwo projektu", "Członkowie zespołu", "Opracowanie serwisu". Each member shows name, role and a short biography. A group with no members is not shown (R-02).

### 2.10 Search

**US-RA-14 — Search entry (Must, v1)**
AC:
1. The search field is in the header of every page (R-07). Submitting it opens the search page with results.
2. Under the field on the search page: what is searched ("Przeszukiwane: tytuły, opisy, transkrypcje i tagi") and a hint about exact phrases in quotes.

**US-RA-15 — Search results (Must, v1)**
As an RA, I find works, tags, fragments and notes by typing a phrase.

AC:
1. All published entities and all visible fragments are indexed: titles, descriptions, tag names and descriptions, fragment quotes and descriptions, OCR texts and plain texts.
2. The header shows the query and the total ("7 wyników we wszystkich kategoriach").
3. In the "Wszystko" tab, results are grouped by type in this order: Utwory, Tagi, Fragmenty, Zapiski, Maszynopisy, Teksty sekundarne, Materiały kontekstowe. Each group has a counter.
4. Within a group, results are sorted by relevance (more occurrences rank higher) or, if the reader chooses, by title.
5. Each result shows its type (R-04) and is clickable. A fragment result is a fragment card (R-10). A work result shows its author, genre and year, and how many of its fragments match.
6. For a match inside a text, the result shows the matching snippet with the search terms highlighted. Clicking it opens the object scrolled to the match. Work results show no snippet.
7. Search handles Polish inflection: e.g. "potoku" finds "potok".
8. With no results, the page says so, suggests checking the spelling or shortening the phrase, and shows "Śladami motywów": the three tags with the most occurrences.

**US-RA-16 — Search tabs and filters (Must, v1)**
AC:
1. Tabs: Wszystko (default), Utwory, Fragmenty, Zapiski, Tagi. Each tab shows its result count.
2. Filters, each value with its count:
   - Utwór: limit to results related to the selected works,
   - Okres: limit to results related to works first published in the selected decade ("Wszystkie lata" by default),
   - Dostępność: "Ze skanem" and "Z transkrypcją".
3. On mobile the filters open in a full-screen panel from a "Filtry (n)" button. The action bar is pinned to the bottom. "Pokaż wyniki (n)" closes the panel and always shows the number of results after filtering; "Wyczyść" clears all filters without closing the panel.
4. Tab, filters and sort order are kept in the URL, so a results page can be linked.
5. An empty query returns all items in the selected tab and filters, sorted by title.

**US-RA-17 — Autocomplete (Should, v1)**
AC:
1. While typing (e.g. "czarny p…"), the field suggests matching work titles and tag names.
2. Choosing a suggestion opens that entity's page.

---

## 3. Editor (WR)

All editor stories take place in Django admin. Every image field has a required text alternative (R-12). Every archival field "shelfmark" means an institution chosen from a list (US-WR-14) plus a number.

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
   - genre (e.g. "powieść"),
   - description (rich text),
   - cover image for the work cards, with text alternative.
2. Editions are added inline. Each edition has publisher, place, year and an optional cover image with text alternative.

**US-WR-04 — Add a typescript (Must, v1)**
AC:
1. Fields:
   - parent work (required, must already exist),
   - title (required, e.g. "Pierwsza wersja"),
   - description (optional),
   - shelfmark,
   - scan file (required),
   - OCR file (required).
2. The system validates that the OCR file has the same number of pages as the scan. If not, the save is rejected with a message stating both page counts.
3. A checkbox marks the typescript as the main typescript of its work. Only one typescript per work can be main; marking a new one unmarks the previous one.
4. Saving updates the search index.

**US-WR-05 — Add a note (Must, v1)**
AC:
1. Fields: title (required, e.g. "Notes 18 · karta 4"), optional description, shelfmark, content.
2. Content is one of:
   - image (with text alternative),
   - document,
   - external audio/video link,
   - OCR text (scan + OCR file, validated as in US-WR-04 AC2),
   - plain text (e.g. a letter transcription).
3. Linked to one or more works.

**US-WR-06 — Add a secondary text (Must, v1)**
AC:
1. Fields:
   - title (required),
   - kind (e.g. letter, review, study, recording),
   - optional description,
   - optional author,
   - optional source: publisher, place, year and pages, as one line of text,
   - optional date, sender and recipient (for letters),
   - shelfmark,
   - text as OCR (scan + OCR file) or plain text.
2. Linked to one or more works. Each work link can carry tags (US-WR-10).

**US-WR-07 — Add a contextual material (Must, v1)**
AC:
1. Fields: title (required), optional description, shelfmark, content.
2. Content is one of: image (with text alternative), document, external audio/video link, OCR text, plain text.
3. Linked to one or more works. Each work link can carry tags (US-WR-10).

**US-WR-08 — Manage tags (Must, v1)**
AC:
1. Fields:
   - name (required, unique),
   - kind: "Buczkowski's keyword" or "interpretation" (required; used to filter the tag list in the admin, not shown publicly),
   - description (rich text: a biography or a short scholarly note).
2. Related tags: selecting tag B as related to tag A makes A related to B automatically.
3. A tag cannot be deleted while it is applied anywhere. The error lists where it is used.

**US-WR-09 — Tag fragments (Must, v1)**
As a WR, I tag fragments of texts by selecting them.

AC:
1. Available for: the main typescript, and notes, secondary texts and contextual materials with OCR or plain text.
2. The editor selects a text range in the tagging screen and assigns one or more existing tags to it.
3. Fragments may overlap. The same text can carry several tags.
4. A fragment stores the selected text. If the underlying text changes and the fragment no longer matches, the fragment is flagged for review, not silently moved or deleted.
5. No manual markup (TEI or otherwise) is ever required from the editor.
6. In the fragment's own form, the editor can set: location (e.g. "rozdział I"), shelfmark number (e.g. "1618.0009"; the institution comes from the document), description, and a "featured" checkbox. Featured fragments come first in previews (R-09) and are candidates for the home page (US-RA-02).

**US-WR-10 — Tag whole entities and work links (Must, v1)**
AC:
1. Any work, typescript, note, secondary text or contextual material can be tagged as a whole.
2. A work link (work ↔ secondary text, work ↔ contextual material) can be tagged. These tags appear on the work page (US-RA-05).

**US-WR-11 — Edit home page and footer content (Must, v1)**
AC:
1. Editable fields:
   - introduction text,
   - portrait image, with text alternative,
   - funding note in the footer.

**US-WR-12 — Edit the About page (Must, v1)**
AC:
1. Editable fields: introduction, project text (rich text).
2. Team members are added, edited and reordered. Each has name (required), role, short biography, and group: "Kierownictwo projektu", "Członkowie zespołu" or "Opracowanie serwisu".

**US-WR-13 — Preview a draft (Must, v1)**
As a WR, I check how a page looks before I publish it.

AC:
1. Every entity's admin form has a "View on site" link, also for drafts.
2. While logged in, the editor sees the draft page with a "Szkic — niewidoczny publicznie" banner (R-06). Anonymous readers get 404.

**US-WR-14 — Manage institutions (Must, v1)**
AC:
1. An institution has an abbreviation (required, unique, e.g. "ML") and a full name (e.g. "Muzeum Literatury").
2. Shelfmarks are always shown as "<abbreviation>, sygn. <number>", built from the two fields, never typed as one text.

---

## 4. Later (out of scope for v1)

- **Ukrainian version.** A separate, structurally similar, simplified service. A menu and footer marker ("Polski / Українська") switches to it and always lands on its home page. Relations between language versions of a work (e.g. "Czarny potok" PL ↔ UA) live in the Ukrainian service.
- **Epicycloid.** The slowly animated epicycloid in the home page background (brief 5.1). Not in the Figma design.
- **Bibliography of a work** as its own rich-text field. In v1 the secondary texts list (R-08) serves as the bibliography.
- **Header images** for the work page and the tag page.
- **Additional content pages** (e.g. a conference page).
- **SEO decision.** v1 serves per-URL title and description meta tags only.
- **TEI export.**

Explicitly rejected:

- A dedicated subpage for a letter fragment, or for any fragment (R-01).
- A generic relation component repeated on every page. Replaced by the subpage layout (R-05).
- An editor-chosen highlighted note per work and a highlighted fragment per note link or secondary text. Replaced by previews with featured fragments (R-09).

---

## 5. Open questions

Each question lists the default that the stories above already assume.

1. **Tag metadata record (metryczka).** What fields does it have beyond name, kind and description? *Default: none.*
2. **Ordering of lists.** *Default: works by first edition; editions by year; typescripts by work, then shelfmark; tags alphabetically; fragments by position in the text; all other lists by title.*
3. **Video and audio.** The brief keeps them hosted elsewhere for notes. *Default: same rule for contextual materials, so no media uploads except images and documents.*
4. **Example of a tagged relation.** Still to be found by the editors.
5. **Design follow-up.** Figma still shows a scan-only typescript viewer and fragment cards with a cropped scan. *Default: the stories win. The designer adds the side-by-side reader with the mobile toggle (R-11) and the quote-plus-page-thumbnail fragment card (R-10).*
