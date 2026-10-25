# Archivum Buczkovianum — Project Brief

> Source: "archiwum cyfrowe Buczkowski" (Google Docs), tab "Brudnopis 10.10.26".
> Polish terms in parentheses are the team's original vocabulary.

---

## 1. Project

**Service name:** Archivum Buczkovianum — a digital archive devoted to the work of Leopold Buczkowski (LB).

The service lets advanced readers explore Buczkowski's works through normalized archival material (typescripts, manuscripts, notes, visual, audio and video material) and the relations between them, expressed through tags.

**Reference point:** [Derridex](https://www.idixa.net/) — a Derrida archive.

---

## 2. Users

### 2.1 Relational Archivist (Relacyjny Archiwista, RA)

Also referred to as the Explorer (Eksplorator Buczkovianista). The reader of the service.

- Buczkowski for advanced readers.
- Searches normalized archives, including OCR-ed manuscripts and typescripts, visual material, audio and video.
- Follows relations between pieces of content.
- Reads biographies (texts written by the editors).

### 2.2 Insightful Editor (Wnikliwa Redaktorka, WR)

The person who uploads content. Responsible for supplying content to the service and editing it. Her workflows are described in section 7.

---

## 3. Ontology (content model)

### 3.1 Work (utwór) — the idea

A work is associated with:

- different versions of typescripts (maszynopisy); they sometimes contain handwritten passages,
- notes (zapiski): manuscripts (sometimes handwritten passages inside a typescript), drafts, notes,
- a list of editions,
- fragments of secondary texts,
- a bibliography (potentially with links); the simpler option is continuous text,
- selected contextual materials,
- fragments of editorial texts.

### 3.2 Other entities

- **Tag** and its description (either a biography or a short scholarly note).
- **Secondary texts** (teksty sekundarne): reviews, opinions, letter fragments.
- **Contextual materials** (materiały kontekstowe): any medium plus a description.

### 3.3 What a tag is

**A tag is a name for a relation.** Tags cover:

- keywords taken from Buczkowski (e.g. "dezerter"),
- our interpretations of Buczkowski (e.g. "wielokulturowość" / multiculturalism),
- relations between tags,
- the tag's metadata record (metryczka).

### 3.4 How tagging works

- Everything can be tagged as a whole and by fragment: notes, secondary texts, typescripts.
- A relation can be tagged: secondary texts and contextual materials can be linked to a work, and that link can itself be tagged.
- Relation-type tags are applied to secondary texts. If they represent a link to a work, they are displayed on that work's page.
- To do: find an example.

---

## 4. Rules shared across pages

- **Navigation between entities is essential.** Every page links to the pages of all elements it shows. For example, from a tag page the user can open a typescript or a note, or move to another tag.
- If a page has no content in a given category, that category's block is not displayed.
- A list of related works appears everywhere except the work page, which shows the list of editions instead.

### "Relation" component (other related entities)

A repeated block used on the tag, secondary text and typescript pages:

1. list / overview of tags,
2. highlighted typescript fragment,
3. list of typescripts,
4. highlighted note,
5. list of notes,
6. gallery of visual contextual materials.

---

## 5. Pages (Archivist user stories)

### 5.1 Home page

1. Menu.
2. "Archivum Buczkovianum".
3. Background graphic: a slowly moving epicycloid (idea: a circling figure in the background).
4. Introduction: a short text about LB plus a large portrait of Buczkowski's face.
5. Book gallery: covers of books or typescripts.
6. A few highlighted fragments (?).
7. Tag cloud.
8. Footer: funding note ("sfinansowane…"), team (separate team page), separate project page.

### 5.2 Work page

**As an RA I can see the body of information about a given work.**

At first glance I see only the key information:

1. title, displayed over a selected visual contextual material (hero),
2. short description (editorial text),
3. list of editions,
4. list / overview of tags,
5. highlighted typescript fragment. Clicking it opens the full typescript. This is the "main" typescript, which is also the one that gets tagged.
6. list of typescripts; clicking one opens that typescript in full,
7. highlighted note,
8. list of notes,
9. gallery of visual contextual materials.

At second glance I can drill down into a separate page for:

1. a tag,
2. a typescript,
3. a note,
4. a secondary text,
5. a contextual material.

### 5.3 Tag page

**As an RA I can see a tag page.**

1. Title, displayed over a selected visual material (preferably a contextual one).
2. Content: a short description of the tag (or a typescript preview, or the content of a contextual material).
3. Relations:
   1. link to the page of the work, or several works, the tag refers to,
   2. highlighted related content: fragments of tagged typescripts (a few examples),
   3. other related entities: the "relation" component (section 4).

### 5.4 Secondary text page

**As an RA I can see a secondary text page.**

1. Title, displayed over a selected visual material. For a letter: date and sender/recipient. Optionally a description.
2. Highlighted related content (e.g. a letter fragment).
3. Other related entities:
   - link to the page of the work or works,
   - the "relation" component (section 4).

### 5.5 Typescript page

Similar in layout to the secondary text page, but a separate entity with its own page.

1. Title, optionally with a description.
2. Highlighted related content.
3. Other related entities:
   - link to the page of the work or works,
   - the "relation" component (section 4).

### 5.6 Note page, contextual material page

Both are listed as subpages reachable from the work page (section 5.2). They have no detailed specification yet.

### 5.7 Content page

A reusable template for text pages such as about the team, about the project, or a conference page when one is needed.

- menu + footer,
- hero: text (e.g. "about us"),
- graphic,
- body: editable rich text.

Planned pages of this type: team page and project page.

### 5.8 Search

**Requirements:**

- Results ranked by importance: work title first, then tags, then occurrences in fragments. More mentions means a higher rank. Ideally the searched words are highlighted immediately.
- Full-text search (search within texts?).
- Everything is indexed.
- Every item must be represented in the same way.
- When the match is inside a larger object, the matching fragment is highlighted.

**Flow:**

1. Initial state: nothing but a search bar with a magnifying-glass icon.
2. Typing (e.g. "czarny p…"): autocomplete would be nice.
3. Result list:
   - sorted by relevance,
   - advanced option to search everywhere, in tags only, or in typescripts only; an empty query returns everything,
   - each result shows what kind of object it is, in the format `type: title`,
   - every result is clickable,
   - where a fragment can be shown, the result shows it; this does not apply to works.

---

## 6. Side notes

- **Ukrainian version** (later):
  - a separate service, structurally similar but simplified,
  - the menu and footer get a marker that switches to the Ukrainian version; switching always lands on the Ukrainian home page, regardless of where the user was,
  - relations between language versions of a work (e.g. "Czarny potok" PL ↔ UA) are handled by the separate Ukrainian service.
- **Letter fragment subpage:** NO.
- **SEO** (Google ranking): to be decided.
- **Team page:** yes (see 5.7).
- **Circling figure** in the home page background (see 5.1).

---

## 7. Editor workflows (Insightful Editor)

### 7.1 Adding a work

- title,
- description,
- cover / graphic for presentation on the home page,
- list of editions,
- header photo, selected from the contextual materials.

### 7.2 Adding a typescript

- Attached to an existing work.
- File upload: the source file plus a second file, an OCR text used for search. The OCR file is directly linked to the typescript document, and the two must match.
- Typescript title.
- Typescript description: optional.
- Tagging happens in the content: the editor selects fragments of the typescript and tags them.
  - Only one typescript is tagged: the one highlighted on the work page.
  - Test and evaluate tagging via TEI.

### 7.3 Adding a note

- Title.
- Content, one of:
  - image,
  - document,
  - link (audio/video hosted elsewhere),
  - text: an OCR text fragment; tagging is done by fragment, the rest gets a single tag,
  - plain text (tekst lity), e.g. a letter transcription.
- Optional description.
- Can be related to multiple works.
- Manual choice of the link to a work, i.e. which fragment is highlighted.

### 7.4 Adding a secondary text

- title,
- optional description,
- text as OCR or as plain text.

### 7.5 Adding a contextual material

- title,
- optional description,
- OCR text, plain text, graphic, video, etc.

---

## 8. Open questions

- Typescripts or notes in OCR form: how should this work, and where should it live?
- Displaying tags on scanned material: how can this work without entering comments (TEI) by hand?
- Tagging via TEI: test the possibilities (see 7.2).
- Tagged relations: find an example (see 3.4).
- SEO: decision pending.

---

## 9. References

### 9.1 Visual inspirations

- [Derridex](https://www.idixa.net/) — Derrida archive, main reference point.
- [Shelley-Godwin Archive](https://shelleygodwinarchive.org/)
- [Conversation Taking Place — index](https://conversation-taking-place.com/index/) — text and image presented together in a single tile.
- [Shakespeare Documented — Arden of Faversham, first edition](https://shakespearedocumented.folger.edu/resource/document/arden-faversham-first-edition)

### 9.2 TEI readers

- Polish corpora: [tei.nplp.pl](https://www.tei.nplp.pl/)
  - [NPLP — "Dramat reaktywacja" collection](https://nplp.pl/kolekcja/dramat-reaktywacja/) — good presentation of footnotes.
  - [tei.nplp.pl/documents/1839](https://www.tei.nplp.pl/documents/1839) — markup types distinguished by color. Possibly reusable if we want to show which fragment belongs to which novel.
  - [tei.nplp.pl/documents/1751](https://www.tei.nplp.pl/documents/1751) — as above, plus the digital edition shown in parallel with the scan.
- [Shelley-Godwin Archive — MS Abinger d33, p3](https://shelleygodwinarchive.org/sc/oxford/ms_abinger/d33/#/p3) — scan and edition shown in parallel, with the whole file viewed by scrolling.