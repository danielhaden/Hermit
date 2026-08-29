"""Shared fixtures. Tests never touch the real library or the real data dir."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QGuiApplication, QPageSize, QPainter, QPdfWriter
from PySide6.QtWidgets import QApplication

from hermit.model.library import Library
from hermit.model.settings import Settings


@pytest.fixture(scope="session")
def qapp():
    """One QApplication for the whole session; Qt allows no more than one."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def settle(qapp):
    """Run the event loop for a moment, letting Qt's deferred work finish."""

    def _settle(ms: int = 300) -> None:
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    return _settle


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Point the app's data directory at a scratch folder."""
    target = tmp_path / "data"
    target.mkdir()
    monkeypatch.setenv("HERMIT_DATA_DIR", str(target))
    return target


@pytest.fixture
def library(data_dir):
    store = Library()
    yield store
    store.close()


@pytest.fixture
def settings(data_dir):
    store = Settings()
    yield store
    store.close()


def _write_pdf(path, pages: int, title: str = "") -> None:
    """Generate a real multi-page PDF, so tests need no committed fixtures."""
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    if title:
        writer.setTitle(title)
    painter = QPainter(writer)
    for number in range(pages):
        if number:
            writer.newPage()  # paging is the device's job, not the painter's
        painter.drawText(120, 220, f"Page {number + 1}")
    painter.end()


@pytest.fixture
def make_pdf(qapp, tmp_path):
    """Build a PDF on demand: ``make_pdf("book.pdf", pages=12)``."""

    def _make(name: str, pages: int = 12, title: str = ""):
        path = tmp_path / name
        _write_pdf(path, pages, title)
        return path

    return _make


@pytest.fixture
def book_pdf(make_pdf):
    return make_pdf("a-book.pdf", pages=12)


@pytest.fixture
def long_book_pdf(make_pdf):
    """A book long enough to reach the pages where the drift appears."""
    return make_pdf("a-long-book.pdf", pages=60)


@pytest.fixture
def drift_page():
    """A page deep enough to reproduce the reading-position drift.

    Below roughly page 35 (at the window size these tests use) a jump lands
    cleanly and nothing moves; past it, relayout tips the view onto the next
    page. 50 sits well clear of that boundary, so the regression reproduces
    reliably rather than depending on exact layout arithmetic.
    """
    return 50
