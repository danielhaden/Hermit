"""Persistent user preferences, stored alongside the library."""

import sqlite3
from pathlib import Path

from hermit.model import paths

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_LIBRARY_FOLDER = "library_folder"


class Settings:
    """A small key/value store for preferences the user sets from the menu."""

    def __init__(self, database: Path | None = None) -> None:
        self._connection = sqlite3.connect(database or paths.database_path())
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def get(self, key: str, default: str = "") -> str:
        row = self._connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str) -> None:
        self._connection.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._connection.commit()

    # -- the default library folder ---------------------------------------

    def library_folder(self) -> Path | None:
        """The folder the user nominated as their book collection, if any."""
        stored = self.get(_LIBRARY_FOLDER)
        return Path(stored) if stored else None

    def set_library_folder(self, folder: Path) -> None:
        self.set(_LIBRARY_FOLDER, str(folder))

    def browse_folder(self) -> Path:
        """Where file dialogs should open: the nominated folder, else home.

        Falls back to home if the folder has since been moved or deleted, so a
        stale setting never leaves the dialog pointing at nothing.
        """
        folder = self.library_folder()
        return folder if folder and folder.is_dir() else Path.home()
