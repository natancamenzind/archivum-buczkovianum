# Demo scans and OCR texts

Used by `manage.py load_demo_data` (docs/plan.md, step 5). Each `.pdf` has as many pages as its
`.txt`, whose pages are separated by a form feed (`\f`), as Tesseract writes them.

| Files | Content |
|-------|---------|
| `czarny-potok-1609.*` | Leopold Buczkowski, *Czarny potok*: pages 5–9 of the edition in the "Kolekcja prozy polskiej XX wieku" series, as the scan, and their text as the OCR file. Used with the permission obtained by the project. Only the PDF's font errors (`Ŝ` for `ż`, `ś` for `Ż`), book page numbers and line-end hyphenation were fixed; other OCR errors of the source are kept. |
| all others | Placeholders written for the demo: short invented sentences, and a one-line PDF page per text page. |
