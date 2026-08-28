"""The reading pane: the selected book, rendered, with page and zoom controls."""

from pathlib import Path

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QSpinBox,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

_ZOOM_STEPS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0)
_PLACEHOLDER = "Select a book from the library to read it."

# Anchor the restored page a few points below its top edge. Landing exactly on
# a page boundary lets a later relayout tip the view onto the following page.
_ANCHOR_Y = 4.0
_SETTLE_MS = 250


class ReaderView(QWidget):
    """Displays one PDF at a time and reports the page the reader is on."""

    page_changed = Signal(int, int)  # current page, total pages

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document = QPdfDocument(self)
        self._view = QPdfView(self)
        self._view.setDocument(self._document)
        self._view.setPageMode(QPdfView.PageMode.MultiPage)
        self._view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        self._placeholder = QLabel(_PLACEHOLDER)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setEnabled(False)

        self._pages = QStackedWidget(self)
        self._pages.addWidget(self._placeholder)
        self._pages.addWidget(self._view)

        self._toolbar = self._build_toolbar()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._pages)

        self._navigator = self._view.pageNavigator()
        self._navigator.currentPageChanged.connect(self._on_page_changed)
        self._restoring = False  # true while re-opening at a saved page
        self._show_document(False)

    # -- construction -----------------------------------------------------

    def _build_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Reading", self)
        toolbar.setMovable(False)

        self._previous_action = QAction("‹  Previous", self)
        self._previous_action.setShortcut(QKeySequence.StandardKey.MoveToPreviousPage)
        self._previous_action.triggered.connect(self.previous_page)
        toolbar.addAction(self._previous_action)

        self._page_spin = QSpinBox(self)
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.setToolTip("Jump to page")
        self._page_spin.valueChanged.connect(self._on_spin_changed)
        toolbar.addWidget(self._page_spin)

        self._page_total = QLabel(" of 0 ")
        toolbar.addWidget(self._page_total)

        self._next_action = QAction("Next  ›", self)
        self._next_action.setShortcut(QKeySequence.StandardKey.MoveToNextPage)
        self._next_action.triggered.connect(self.next_page)
        toolbar.addAction(self._next_action)

        toolbar.addSeparator()

        self._zoom_box = QComboBox(self)
        self._zoom_box.addItem("Fit width", "fit-width")
        self._zoom_box.addItem("Fit page", "fit-page")
        for step in _ZOOM_STEPS:
            self._zoom_box.addItem(f"{step:.0%}", step)
        self._zoom_box.currentIndexChanged.connect(self._on_zoom_selected)
        toolbar.addWidget(self._zoom_box)
        return toolbar

    # -- opening ----------------------------------------------------------

    def open(self, path: Path, page: int = 0) -> str | None:
        """Show a book, resuming at ``page``. Returns an error message on failure."""
        error = self._document.load(str(path))
        if error != QPdfDocument.Error.None_:
            self.clear()
            return f"Could not open {path.name}: {error.name}"

        total = self._document.pageCount()
        self._page_spin.blockSignals(True)
        self._page_spin.setMaximum(max(1, total))
        self._page_spin.blockSignals(False)
        self._page_total.setText(f" of {total} ")
        self._show_document(True)
        self._restore_page(max(0, min(page, total - 1)))
        return None

    def _restore_page(self, page: int) -> None:
        """Jump to a saved page once the pane has finished laying itself out.

        Restoring is done behind a guard: the view emits a flurry of page
        changes as it settles, and recording those would walk the saved
        position forward a page on every reopen.
        """
        self._restoring = True
        QTimer.singleShot(0, lambda: self._navigator.jump(page, QPointF(0, _ANCHOR_Y), 0))
        QTimer.singleShot(_SETTLE_MS, self._finish_restore)

    def _finish_restore(self) -> None:
        self._restoring = False

    def clear(self) -> None:
        self._restoring = False
        self._document.close()
        self._page_total.setText(" of 0 ")
        self._show_document(False)

    def _show_document(self, visible: bool) -> None:
        self._pages.setCurrentWidget(self._view if visible else self._placeholder)
        self._toolbar.setEnabled(visible)

    # -- navigation -------------------------------------------------------

    def current_page(self) -> int:
        return self._navigator.currentPage()

    def page_count(self) -> int:
        return self._document.pageCount()

    def go_to_page(self, page: int) -> None:
        if 0 <= page < self._document.pageCount():
            self._navigator.jump(page, QPointF(0, _ANCHOR_Y), 0)

    def previous_page(self) -> None:
        self.go_to_page(self.current_page() - 1)

    def next_page(self) -> None:
        self.go_to_page(self.current_page() + 1)

    def _on_page_changed(self, page: int) -> None:
        self._page_spin.blockSignals(True)
        self._page_spin.setValue(page + 1)
        self._page_spin.blockSignals(False)
        self._previous_action.setEnabled(page > 0)
        self._next_action.setEnabled(page < self._document.pageCount() - 1)
        if not self._restoring:
            self.page_changed.emit(page, self._document.pageCount())

    def _on_spin_changed(self, value: int) -> None:
        self.go_to_page(value - 1)

    # -- zoom -------------------------------------------------------------

    def _on_zoom_selected(self, index: int) -> None:
        mode = self._zoom_box.itemData(index)
        if mode == "fit-width":
            self._view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        elif mode == "fit-page":
            self._view.setZoomMode(QPdfView.ZoomMode.FitInView)
        else:
            self._view.setZoomMode(QPdfView.ZoomMode.Custom)
            self._view.setZoomFactor(float(mode))

    def zoom_in(self) -> None:
        self._step_zoom(1)

    def zoom_out(self) -> None:
        self._step_zoom(-1)

    def _step_zoom(self, direction: int) -> None:
        """Move to the next fixed zoom step above or below the current factor."""
        current = self._view.zoomFactor()
        steps = _ZOOM_STEPS if direction > 0 else tuple(reversed(_ZOOM_STEPS))
        target = next(
            (s for s in steps if (s > current if direction > 0 else s < current)),
            steps[-1],
        )
        self._zoom_box.setCurrentIndex(self._zoom_box.findData(target))
