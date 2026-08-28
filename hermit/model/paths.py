"""Filesystem locations for application data.

The data directory can be overridden with the ``HERMIT_DATA_DIR``
environment variable (useful for tests and headless runs).
"""

import os
import sys
from pathlib import Path

APP_NAME = "Hermit"


def data_dir() -> Path:
    """Return the per-user data directory, creating it if needed."""
    override = os.environ.get("HERMIT_DATA_DIR")
    if override:
        path = Path(override).expanduser()
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        path = Path(base) / APP_NAME
    else:  # linux / other
        base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
        path = Path(base) / APP_NAME

    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """Return the path to the library database (books and reading position)."""
    return data_dir() / "hermit.db"


def default_browse_dir() -> Path:
    """Return the folder the 'Add Books' dialog should open in.

    Purely a convenience starting point - Hermit indexes files wherever they
    live and treats no folder as special.
    """
    biblio = Path.home() / "biblio"
    return biblio if biblio.is_dir() else Path.home()
