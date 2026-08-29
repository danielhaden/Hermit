# Status

_Last updated: 2026-08-29_

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
- **Adding explains itself** — the status bar distinguishes books added,
  books already in the library, and files that aren't PDFs, naming the file
  when it was picked by hand.
- **Tests** — 38 of them, offscreen, generating their own PDFs against a
  scratch data directory. `pytest`.
- **VS Code** — run configurations for the app and for a scratch library.

## Not built yet

- **No CI.** The tests exist but nothing runs them on push. This is the
  biggest remaining gap; PySide6 on a GitHub runner needs system libraries
  (`libegl1`, `libxkbcommon-x11-0`) that can't be verified from this Mac, so
  the first workflow will need a run or two to settle.
- **No VS Code test integration.** `python.testing.pytestEnabled` and a
  debug-tests launch configuration are not set up yet.
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
        main_window.py     splitter, menus, wiring, add reporting
        library_panel.py   filter box and table (left)
        library_model.py   table model over the library
        reader_view.py     QPdfView plus page and zoom controls (right)
    tests/                 offscreen; fixtures generate their own PDFs
