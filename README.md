# Hermit

A small desktop app for keeping track of digital books. The library sits in a
table on the left; the selected book is rendered in the pane on the right.

Currently PDF only - other formats are planned.

## Running

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
.venv/bin/python -m hermit
```

## How it works

- **Books are indexed in place.** Adding a book records its path; Hermit never
  copies, moves, or modifies the file. Removing a book from the library leaves
  the file on disk.
- **The library lives in SQLite**, at
  `~/Library/Application Support/Hermit/hermit.db` on macOS. Set
  `HERMIT_DATA_DIR` to point somewhere else.
- **PDFs are detected by content**, not by file extension, so books saved
  without a `.pdf` suffix are still recognised.
- **Settings → Default Library Folder…** nominates the folder you keep books
  in. File dialogs open there, and Hermit offers to index it when you set it.
  Unset, dialogs open at your home folder. The setting is stored in the
  database, not hardcoded.
- **Your place is remembered.** The page you were on is saved as you read, and
  the book reopens there.
- Title and author are read from the PDF's own metadata, falling back to the
  file name. Both cells are editable - double-click to correct them.
- A book whose file has moved is shown in red italics rather than being
  dropped from the library.

## Layout

    hermit/
      __main__.py          entry point
      model/
        paths.py           data directory and database location
        book.py            the Book record
        library.py         SQLite index: add, remove, record position
        settings.py        key/value preferences (default library folder)
        pdf_info.py        PDF sniffing and metadata extraction
      ui/
        main_window.py     splitter, menus, wiring
        library_panel.py   filter box and table (left)
        library_model.py   table model over the library
        reader_view.py     QPdfView plus page and zoom controls (right)
