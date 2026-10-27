# User Stories — Archivum Buczkovianum

Sources: `docs/PROJECT_BRIEF.md` and the Figma file "archiwum-buczkowski-model", page "po korekcie".

## How to read this

- A story is done when all its acceptance criteria (AC) pass. One story per branch and PR; both carry its ID.
- **RA (Relacyjny archiwista)** is the public reader: anonymous, never logs in. **WR (Wnikliwa Redaktorka)** is an editor working in admin panel; all editors have the same rights.
- Every story is in v1 and required, unless marked **(Should)**: build it if it fits. Section 4 lists what is out of scope.
- Rules R-01 to R-12 apply to every public page. Stories refer to them instead of repeating them.
- Quoted Polish text is exact UI copy. The UI uses only the Polish terms from the glossary.

## Glossary

| Term (UI term) | Meaning |
|----------------|---------|
| Work (utwór) | A literary work as an idea, independent of any edition or document, e.g. "Wertepy". |
| Edition (wydanie) | A published edition of a work: year, publisher, place. |
| Typescript (maszynopis) | A typescript of a work: scan + OCR text. Belongs to exactly one work. |
| Main typescript | The one typescript per work that is fragment-tagged. Its fragments appear on the work page. |
| Note (zapisek) | The author's manuscript material: a notebook page, a card, a draft. Relates to one or more works. |
| Secondary text (tekst sekundarny) | A review, study, letter or recording about a work. Relates to one or more works. |
| Contextual material (materiał kontekstowy) | Any medium plus a description. Relates to one or more works. |
| Visual material (materiał wizualny) | A contextual material that is an image: a photo or an illustrative scan. |
| Work link | The relation between a work and a secondary text or contextual material. Can be tagged. |
| Tag | A motif linking fragments and notes: a Buczkowski keyword or an editorial interpretation. |
| Fragment | A tagged character range in a text (OCR or plain), with optional shelfmark, location and description. |
| Occurrence (wystąpienie) | One published item carrying a tag: a fragment, a whole entity, or a work link. |
| Shelfmark (sygnatura) | Institution + number, shown as "ML, sygn. 1618". A fragment has its own number ("ML, sygn. 1618.0009") and takes the institution from its document. |

---

## 1. Rules for every public page

**R-01 Links.** Every entity shown on a page links to its own page. A fragment has no page: it links to its source document, scrolled to the fragment.

**R-02 Empty blocks.** A block with no content is not rendered: no heading, no empty state.

**R-03 Related works.** The context column of every entity page lists the related works. The work page lists its editions there instead.

**R-04 Type label.** Every entity has a type label and a title. Wherever it is listed outside its own page (search, lists, cards), the type label is shown with the title.

**R-05 Entity page layout.** Work, typescript, tag, note, secondary text and contextual material pages share one layout:

1. hero: a dark band with a type line (e.g. "Utwór · Leopold Buczkowski · 1947"), title and description;
2. context column on the left;
3. main column;
4. tag column on the right;
5. contextual materials block (R-08) below the columns, if the page has one.

On mobile the order is: main, context, tags, contextual materials.

**R-06 Published only.** The public sees only entities with status `published`. Drafts are not listed, not searchable, and their URLs return 404 to anonymous readers. A logged-in editor opening a draft's URL sees the page with a draft banner (US-WR-13). Drafts never appear in lists, previews or search, even for editors.

**R-07 Header, navigation, footer.**

- Header: service name and subtitle (links to home), "O archiwum" link, search field.
- Main navigation: Strona główna, Utwory, Maszynopisy, Tagi. On desktop it is in the footer. On mobile it is a bottom bar, and search becomes an icon in the header.
- Footer: service name and subtitle, main navigation (desktop), funding note.

Active navigation item: home → Strona główna; works list and work → Utwory; typescripts list and typescript → Maszynopisy; tags list and tag → Tagi. Other pages have none.

**R-08 Contextual materials block.** Titled "Materiały kontekstowe", in two parts:

1. "Teksty sekundarne": a numbered list of secondary texts and non-image contextual materials. First line: author and title. Second line: source (publisher, place, year, pages).
2. "Materiały wizualne": a gallery of visual materials. Each has a thumbnail and a caption: title and shelfmark.

Each page defines which items it includes.

**R-09 Counters and previews.**

- A section header shows a count: "3", or "2 z 24" when the section is a preview.
- A preview shows the first `PREVIEW_LIMIT` items (one setting, default 2): featured fragments first, then text order. It ends with a link naming its target and count, e.g. "Wszystkie fragmenty (24)".
- The fragment previews' "all" link opens no new page. On the typescript page it expands the list in place, in page order. On the work page it opens the main typescript's page with that list expanded.
- Counts use Polish plural forms: 1 fragment, 2–4 fragmenty, 5+ fragmentów.

**R-10 Fragment card.** Every fragment is shown as this card:

1. location line: work, number in its document ("fragment 01"), optional location ("rozdział I"); a chip with the source type ("Maszynopis", "Zapisek");
2. quote (the fragment text, cut to a few lines); for an OCR source, a thumbnail of the scan page where the fragment starts;
3. shelfmark, description, tags.

Clicking the card opens the source document scrolled to the fragment.

**R-11 Reader.** Every OCR document (typescript, note, secondary text, contextual material) uses one reader:

1. Desktop: each scan page next to its OCR text, scrolling continuously. Mobile: a "Skan" / "Transkrypcja" toggle.
2. Fragments are highlighted. Clicking one shows its tags, each linking to its tag page.
3. Opened with a fragment reference, it scrolls to that fragment and highlights it. Opened from a search result, it scrolls to the first match.

A plain-text document is shown as text, with fragments highlighted as in point 2.

**R-12 Accessibility.** WCAG 2.1 AA. Every image has a text alternative entered by WR. Animations respect `prefers-reduced-motion`. Every control works from the keyboard and has an accessible name (e.g. the filter panel's close icon is "Zamknij filtry").

---

## 2. Reader (RA)

### US-RA-01 — Home page

1. In order: header, hero, works, featured fragment (US-RA-02), tag cloud, footer (R-07).
2. Hero: the title "Archivum Buczkovianum" and the introduction over Buczkowski's portrait, plus counts of published works, visible fragments and published tags ("4 utwory · 62 fragmenty · 12 tagów").
3. Works: one card per published work, ordered by first edition: cover, genre and year, title, author, fragment count. The fragment count is the number of visible fragments of the work's main typescript; when it is 0 (no main typescript, a draft one, or no visible fragments), the card does not show it (R-02). Clicking opens the work page.
4. Tag cloud: every published tag with at least one occurrence. Five sizes by occurrence count: 1–3, 4–7, 8–15, 16–25, 26+; the two largest use the accent colour. The layout is deterministic: the same data always gives the same cloud. Clicking a tag opens its page.
5. The introduction and portrait are editable (US-WR-11).

### US-RA-02 — Featured fragment on the home page (Should)

1. One fragment card (R-10), picked at random from the visible fragments marked featured (US-WR-09 AC6). Counter: "1 z <all visible fragments>".
2. Below it, "Wszystkie fragmenty „<work>” (n)" opens search on the Fragmenty tab filtered to that fragment's work (US-RA-16).

### US-RA-03 — Footer

1. The footer follows R-07.

### US-RA-04 — Work page

Shows what we know about a work, key information first.

1. Hero: "Utwór · Leopold Buczkowski · <year of first edition>", title, description.
2. Context column: editions by year, each with year, publisher and place. The earliest is labelled "pierwsze wydanie".
3. Main column, in order:
   1. "Fragmenty maszynopisu": a preview (R-09) of the main typescript's fragments, as fragment cards (R-10);
   2. "Maszynopisy": a numbered list of the work's typescripts, each linking to its page;
   3. "Zapiski": the notes linked to the work, as note cards: location line, type chip, image (or a placeholder), shelfmark, description, tags.
4. Tag column: every published tag that refers to the work (definition in US-RA-07 AC5), including relation tags (US-RA-05).
5. Contextual materials (R-08): the secondary texts and contextual materials linked to the work.

### US-RA-05 — Relation tags on the work page

1. Tags on a work link (work ↔ secondary text, or work ↔ contextual material) appear in the work's tag column.
2. Each links to its tag page.

### US-RA-06 — Drill-down from a work

1. Every item in the work page's main column, tag column and contextual materials block links to its own page, or, for a fragment, to its place in the source (R-01).

### US-RA-07 — Tag page

Shows everything connected to a tag.

1. Hero: "Tag · <n> wystąpień w <m> utworach" (with Polish plural forms), title, description (a biography or a short scholarly note). The tag kind is not shown.
2. Context column: "Utwory", every work the tag refers to, by first edition. Each shows year, title and how many of its fragments carry the tag.
3. Main column, in order:
   1. "Fragmenty z tagiem": every visible fragment with the tag, as fragment cards (R-10), ordered by the work's first edition, then by position in the text;
   2. "Zapiski z tagiem": every note with the tag, on the whole note or on a fragment, as note cards (US-RA-04 AC3).
4. Tag column: "Powiązane tagi", the related tags (symmetric, untyped).
5. A tag refers to a work if it is on the work, on an entity related to the work, on a fragment of such an entity, or on one of the work's work links.
6. Contextual materials (R-08): secondary texts and contextual materials with the tag, on the whole item, on a fragment, or on its work link.

### US-RA-08 — Typescript page

1. Hero: "Maszynopis · <shelfmark> · <year of the work>", title, optional description.
2. Context column: the work (R-03) with year and fragment count; "Maszynopisy utworu", all typescripts of the same work with shelfmark and title, the current one marked.
3. Main column, in order:
   1. "Skan maszynopisu": the reader (R-11); the counter shows the page count;
   2. "Fragmenty z maszynopisu": a preview (R-09) of its fragments as a numbered list (fragment number, location, shelfmark), in page order.
4. Tag column: tags on the typescript and on its fragments.
5. Contextual materials (R-08): those linked to its work.

### US-RA-09 — Reading the full typescript

1. The whole typescript is read in the reader (R-11). Only the main typescript has fragments to highlight.

### US-RA-10 — Secondary text page

1. Hero: a type line with the kind and, for a letter, sender and date ("List · Leopold Buczkowski · 1.10.1947"); title; description. No header image.
2. Context column: "Powiązane utwory" (R-03).
3. Main column, in order:
   1. "Transkrypcja": the full text in the reader (R-11), or as plain text;
   2. "Powiązane fragmenty": a preview (R-09) of typescript fragments that share at least one tag with this text or its fragments, as fragment cards (R-10). No "all" link.
4. Tag column: "Powiązane tagi", tags on the text, its fragments and its work links.

### US-RA-11 — Note page

Not in Figma; uses the secondary text page layout.

1. Hero: "Zapisek · <shelfmark>", title, optional description.
2. Context column: related works (R-03).
3. Main column, in order:
   1. the content, by type:
      - image: shown inline;
      - document: inline if PDF, otherwise a download;
      - external audio/video link: an embedded player if the provider allows it, otherwise a link;
      - OCR or plain text: the reader (R-11);
   2. "Powiązane fragmenty", as in US-RA-10 AC3.
4. Tag column: tags on the note and its fragments.

### US-RA-12 — Contextual material page

Not in Figma; uses the secondary text page layout.

1. Hero: a type line with the kind and shelfmark, title, optional description.
2. Context column: related works (R-03).
3. Main column: the content, as in US-RA-11 AC3, then "Powiązane fragmenty", as in US-RA-10 AC3.
4. Tag column: tags on the material, its fragments and its work links.

### US-RA-18 — Works list

1. Opened from "Utwory" in the main navigation (R-07).
2. A grid of work cards (US-RA-01 AC3) for every published work, by first edition, with the count in the header.

### US-RA-19 — Typescripts list

1. Opened from "Maszynopisy" in the main navigation (R-07).
2. Every published typescript, grouped by work (works by first edition), two cards per row on desktop. Group header: work title, genre, year, count. Card: number, title, shelfmark; opens the typescript page.

### US-RA-20 — Tags list

1. Opened from "Tagi" in the main navigation (R-07).
2. The tag cloud (US-RA-01 AC4), then "Wszystkie tagi": every published tag with at least one occurrence, the same tags as the cloud, alphabetically, with its occurrence count ("4 wystąpienia").

On mobile, all three lists use one column of the same components.

### US-RA-13 — About page

1. Opened from "O archiwum" in the header (R-07).
2. Hero: the title "O archiwum" and an introduction.
3. "O projekcie": rich text about the goal, scope, partner institutions and funding.
4. "Zespół": team members in three groups, in this order: "Kierownictwo projektu", "Członkowie zespołu", "Opracowanie serwisu". Each member shows name, role and a short biography. Empty groups are hidden (R-02).

### US-RA-14 — Search entry

1. The search field is in every page header (R-07). Submitting opens the search page with results.
2. Under the field on the search page: what is searched ("Przeszukiwane: tytuły, opisy, transkrypcje i tagi") and a hint that quotes search for an exact phrase.

### US-RA-15 — Search results

Finds works, tags, fragments and notes by phrase.

1. Indexed: all published entities and visible fragments — titles, descriptions, tag names and descriptions, fragment quotes and descriptions, OCR and plain texts.
2. The header shows the query and the total ("7 wyników we wszystkich kategoriach").
3. The "Wszystko" tab groups results by type, each group with a count, in this order: Utwory, Tagi, Fragmenty, Zapiski, Maszynopisy, Teksty sekundarne, Materiały kontekstowe.
4. Within a group, results are sorted by relevance (more occurrences rank higher), or by title if the reader chooses.
5. Each result shows its type (R-04) and is clickable. A fragment result is a fragment card (R-10). A work result shows author, genre, year and how many of its fragments match.
6. A match inside a text shows a snippet with the search terms highlighted; clicking opens the object scrolled to the match. Work results show no snippet.
7. Polish inflection is handled: "potoku" finds "potok".
8. With no results, the page says so, suggests checking the spelling or shortening the phrase, and shows "Śladami motywów": the three tags with the most occurrences.

### US-RA-16 — Search tabs and filters

1. Tabs, each with its count: Wszystko (default), Utwory, Fragmenty, Zapiski, Tagi.
2. Filters, each value with its count:
   - Utwór: results related to the selected works;
   - Okres: results related to works first published in the selected decade (default "Wszystkie lata");
   - Dostępność: "Ze skanem", "Z transkrypcją".
3. On mobile, "Filtry (n)" opens the filters in a full-screen panel with an action bar pinned to the bottom. "Pokaż wyniki (n)" closes the panel and always shows the filtered result count. "Wyczyść" clears all filters and keeps the panel open.
4. Tab, filters and sort order are kept in the URL, so results can be linked.
5. An empty query returns everything in the selected tab and filters, sorted by title.

### US-RA-17 — Autocomplete (Should)

1. While typing (e.g. "czarny p…"), the field suggests matching work titles and tag names.
2. Choosing a suggestion opens that entity's page.

---

## 3. Editor (WR)

Everything happens in Django admin. Every image field requires a text alternative (R-12). Every "shelfmark" field is an institution chosen from a list (US-WR-14) plus a number.

### US-WR-01 — Log in

1. Accounts are created by the administrator. There is no public registration.
2. All editors have the same permissions.

### US-WR-02 — Draft and publish

1. Every entity has a status: `draft` (default) or `published`.
2. Only published entities are public (R-06).

### US-WR-03 — Add a work

1. Fields: title (required); genre (e.g. "powieść"); description (rich text); cover image for work cards.
2. Editions are added inline: publisher, place, year, optional cover image.

### US-WR-04 — Add a typescript

1. Fields: work (required, must exist); title (required, e.g. "Pierwsza wersja"); optional description; shelfmark; scan file (required); OCR file (required).
2. The OCR file must have as many pages as the scan. Otherwise the save is rejected with a message giving both page counts.
3. A "main typescript" checkbox. Only one per work: marking a new one unmarks the previous one.
4. Saving updates the search index.

### US-WR-05 — Add a note

1. Fields: title (required, e.g. "Notes 18 · karta 4"); optional description; shelfmark; content.
2. Content is one of: image; document; external audio/video link; OCR text (scan + OCR file, checked as in US-WR-04 AC2); plain text (e.g. a letter transcription).
3. Linked to one or more works.

### US-WR-06 — Add a secondary text

1. Fields: title (required); kind (e.g. letter, review, study, recording); shelfmark; text as OCR (scan + OCR file) or plain text. Optional: description; author; source (publisher, place, year, pages, as one line of text); date, sender and recipient (for letters).
2. Linked to one or more works. Each work link can be tagged (US-WR-10).

### US-WR-07 — Add a contextual material

1. Fields: title (required); optional description; shelfmark; content.
2. Content is one of: image; document; external audio/video link; OCR text; plain text.
3. Linked to one or more works. Each work link can be tagged (US-WR-10).

### US-WR-08 — Manage tags

1. Fields: name (required, unique); kind, "Buczkowski's keyword" or "interpretation" (required; filters the admin list, never shown publicly); description (rich text: a biography or a short scholarly note).
2. Related tags are symmetric: making B related to A makes A related to B.
3. A tag in use cannot be deleted. The error lists where it is used.

### US-WR-09 — Tag fragments

1. Available for the main typescript, and for notes, secondary texts and contextual materials with OCR or plain text.
2. In the tagging screen the editor selects a text range and assigns one or more existing tags.
3. Fragments may overlap, and the same text can carry several tags.
4. A fragment stores its selected text. If the underlying text changes so that it no longer matches, the fragment is flagged for review, never silently moved or deleted.
5. The editor never writes markup (TEI or otherwise).
6. The fragment's own form has: location (e.g. "rozdział I"), shelfmark number (e.g. "1618.0009"; the institution comes from the document), description, and a "featured" checkbox. Featured fragments come first in previews (R-09) and can appear on the home page (US-RA-02).

### US-WR-10 — Tag whole entities and work links

1. Any work, typescript, note, secondary text or contextual material can be tagged as a whole.
2. A work link can be tagged. Its tags appear on the work page (US-RA-05).

### US-WR-11 — Edit home page content

1. Editable: the introduction and the portrait image.

### US-WR-12 — Edit the About page

1. Editable: the introduction and the project text (rich text).
2. Team members can be added, edited and reordered. Each has name (required), role, short biography and group: "Kierownictwo projektu", "Członkowie zespołu" or "Opracowanie serwisu".

### US-WR-13 — Preview a draft

1. Every entity's admin form has a "View on site" link, drafts included.
2. A logged-in editor sees the draft page with the banner "Szkic — niewidoczny publicznie" (R-06). Anonymous readers get 404.

### US-WR-14 — Manage institutions

1. An institution has an abbreviation (required, unique, e.g. "ML") and a full name (e.g. "Muzeum Literatury").
2. Shelfmarks are always shown as "<abbreviation>, sygn. <number>", built from the two fields, never typed as one string.

---

## 4. Out of scope for v1

Later:

- **Ukrainian version.** A separate, similar but simpler service. A "Polski / Українська" switch in the menu and footer always lands on its home page. Links between language versions of a work (e.g. "Czarny potok" PL ↔ UA) live in the Ukrainian service.
- **Epicycloid.** The slowly animated background on the home page (brief 5.1). Not in Figma.
- **Bibliography of a work** as a separate rich-text field. In v1 the secondary texts list (R-08) is the bibliography.
- **Header images** on the work and tag pages.
- **More content pages** (e.g. a conference page).
- **SEO.** v1 has only per-URL title and description meta tags.
- **TEI export.**

Rejected:

- A page of its own for any fragment, including letter fragments (R-01).
- A generic relations component on every page. Replaced by the shared layout (R-05).
- Editor-picked highlighted notes per work and highlighted fragments per note link or secondary text. Replaced by previews led by featured fragments (R-09).

---

## 5. Open questions

The stories above already assume the default given for each.

1. **Tag metadata (metryczka).** Any fields beyond name, kind and description? *Default: none.*
2. **List order.** *Default: works by first edition; editions by year; typescripts by work, then shelfmark; tags alphabetically; fragments by position in the text; everything else by title.*
3. **Video and audio.** The brief hosts them elsewhere for notes. *Default: same for contextual materials, so the only uploads are images and documents.*
4. **Example of a tagged relation.** The editors still have to find one.
5. **Design follow-up.** Figma still shows a scan-only typescript viewer and fragment cards with a cropped scan. *Default: the stories win. The designer adds the side-by-side reader with the mobile toggle (R-11) and the fragment card with quote and page thumbnail (R-10).*
