"""The library: a SQLite index of book files and where you left off in them."""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from hermit.model import paths
from hermit.model.book import Book
from hermit.model.pdf_info import is_pdf, read_metadata

_SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id         INTEGER PRIMARY KEY,
    path       TEXT    NOT NULL UNIQUE,
    title      TEXT    NOT NULL,
    author     TEXT    NOT NULL DEFAULT '',
    page_count INTEGER NOT NULL DEFAULT 0,
    last_page  INTEGER NOT NULL DEFAULT 0,
    added_at   TEXT    NOT NULL,
    opened_at  TEXT
);
"""


@dataclass
class AddReport:
    """What came of an attempt to add files: some land, some don't.

    Callers need the difference. A file skipped because it is already in the
    library is not the same as one skipped because it isn't a book, and a user
    who picked a file by hand deserves to be told which happened.
    """

    added: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    not_books: list = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_book(row: sqlite3.Row) -> Book:
    return Book(
        id=row["id"],
        path=Path(row["path"]),
        title=row["title"],
        author=row["author"],
        page_count=row["page_count"],
        last_page=row["last_page"],
        added_at=row["added_at"],
        opened_at=row["opened_at"],
    )


class Library:
    """Stores what the user owns. The book files themselves are never moved."""

    def __init__(self, database: Path | None = None) -> None:
        self._connection = sqlite3.connect(database or paths.database_path())
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def books(self) -> list[Book]:
        """Return every book in the library, newest addition last."""
        rows = self._connection.execute(
            "SELECT * FROM books ORDER BY added_at, id"
        ).fetchall()
        return [_to_book(row) for row in rows]

    def add_file(self, path: Path) -> Book | None:
        """Index one file. Returns ``None`` if it is not a PDF or is a duplicate."""
        book, _ = self._add_one(path)
        return book

    def _add_one(self, path: Path) -> tuple[Book | None, str]:
        """Index one file, reporting why it was skipped when it was."""
        path = Path(path).expanduser().resolve()
        if not is_pdf(path):
            return (None, "not_a_book")
        title, author, page_count = read_metadata(path)
        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO books "
            "(path, title, author, page_count, added_at) VALUES (?, ?, ?, ?, ?)",
            (str(path), title, author, page_count, _now()),
        )
        self._connection.commit()
        if cursor.rowcount == 0:  # already in the library
            return (None, "duplicate")
        row = self._connection.execute(
            "SELECT * FROM books WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return (_to_book(row), "added")

    def add_files(self, paths) -> AddReport:
        """Index several files, recording what happened to each."""
        report = AddReport()
        for path in paths:
            book, outcome = self._add_one(path)
            if outcome == "added":
                report.added.append(book)
            elif outcome == "duplicate":
                report.duplicates.append(Path(path))
            else:
                report.not_books.append(Path(path))
        return report

    def add_folder(self, folder: Path, recursive: bool = True) -> AddReport:
        """Index every PDF in a folder, skipping ones already tracked."""
        pattern = "**/*" if recursive else "*"
        return self.add_files(sorted(p for p in folder.glob(pattern) if p.is_file()))

    def remove(self, book_id: int) -> None:
        """Drop a book from the library. The file on disk is left alone."""
        self._connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._connection.commit()

    def set_title(self, book_id: int, title: str) -> None:
        self._connection.execute(
            "UPDATE books SET title = ? WHERE id = ?", (title, book_id)
        )
        self._connection.commit()

    def set_author(self, book_id: int, author: str) -> None:
        self._connection.execute(
            "UPDATE books SET author = ? WHERE id = ?", (author, book_id)
        )
        self._connection.commit()

    def record_position(self, book_id: int, page: int, page_count: int) -> None:
        """Remember the page the reader is on, so the book reopens there."""
        self._connection.execute(
            "UPDATE books SET last_page = ?, page_count = ?, opened_at = ? "
            "WHERE id = ?",
            (page, page_count, _now(), book_id),
        )
        self._connection.commit()
