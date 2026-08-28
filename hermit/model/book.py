"""The library's one record type: a book file tracked on disk."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Book:
    """A single digital book. Files are indexed in place, never copied."""

    id: int
    path: Path
    title: str
    author: str = ""
    page_count: int = 0
    last_page: int = 0
    added_at: str = ""
    opened_at: str | None = None

    @property
    def exists(self) -> bool:
        """Whether the file is still where the library last saw it."""
        return self.path.is_file()

    @property
    def progress(self) -> float:
        """Fraction of the book read so far, 0.0 to 1.0."""
        if self.page_count <= 1:
            return 0.0
        return min(1.0, self.last_page / (self.page_count - 1))
