# Status

_Last updated: 2026-08-28_

Hermit is a desktop app for keeping track of digital books: a library table on
the left, the selected book rendered on the right. PDF only for now.

## Working

- **Library** — books indexed in place from a file or a folder, listed in a
  sortable, filterable table (Title / Author / Pages). Title and author are
  editable in the table; both persist.
- **Detection** — PDFs recognised by their `%PDF` header, so books saved
  without a `.pdf` extension are picked up. Non-PDFs and duplicates are
  rejected.
- **Metadata** — title and author read from the PDF, falling back to the file
  name when the document carries none.
- **Reader** — continuous-scroll `QPdfView` with page navigation, jump-to-page,
  and fit-width / fit-page / fixed zoom.
- **Reading position** — saved as you scroll, restored on reopen. Verified
  stable across repeated reopens.
- **Missing files** — a book whose file has moved shows in red italics and
  stays in the library rather than disappearing.
- **Settings** — `Settings > Default Library Folder…` nominates where books
  live; file dialogs open there and Hermit offers to index it. Falls back to
  the home folder when unset or when the folder has moved.

## Not built yet

- **No automated tests.** Everything above was verified by offscreen scripts
  run by hand. This is the biggest gap: the page-drift bug was invisible to
  manual use and only surfaced from a deliberate probe.
- **No CI.**
- **No formats besides PDF.** EPUB is the intended next one and needs a
  different renderer, so `ReaderView` would become an interface with a
  per-format implementation.
- **No library-wide search** across book contents.
- **No cover thumbnails.**

## Known rough edges

- The reader reloads the document on every selection change; large books
  re-render rather than being cached.
- Removing a book asks for confirmation, but there is no undo.
- A folder scan is synchronous — indexing a very large folder will briefly
  block the UI.

## Layout

    hermit/
      __main__.py          entry point
      model/               Qt-free apart from pdf_info's use of QtPdf
        paths.py           data directory and database location
        book.py            the Book record
        library.py         SQLite index: add, remove, record position
        settings.py        key/value preferences
        pdf_info.py        PDF sniffing and metadata extraction
      ui/
        main_window.py     splitter, menus, wiring
        library_panel.py   filter box and table (left)
        library_model.py   table model over the library
        reader_view.py     QPdfView plus page and zoom controls (right)
