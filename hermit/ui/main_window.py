"""The application's main window: library on the left, the book on the right."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QWidget,
)

from hermit.model.book import Book
from hermit.model.library import Library
from hermit.model.settings import Settings
from hermit.ui.library_panel import LibraryPanel
from hermit.ui.reader_view import ReaderView

_PDF_FILTER = "PDF files (*.pdf);;All files (*)"


class MainWindow(QMainWindow):
    """Wires the library table to the reading pane and keeps the two in step."""

    def __init__(self, library: Library, settings: Settings) -> None:
        super().__init__()
        self._library = library
        self._settings = settings
        self._current: Book | None = None

        self.setWindowTitle("Hermit")
        self.resize(1200, 800)

        self._panel = LibraryPanel()
        self._reader = ReaderView()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._panel)
        splitter.addWidget(self._reader)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 880])  # the reader takes most of the width
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        self._panel.book_selected.connect(self._on_book_selected)
        self._panel.model.dataChanged.connect(self._on_book_edited)
        self._reader.page_changed.connect(self._on_page_changed)

        self._build_menus()
        self.statusBar().showMessage("Ready")
        self._panel.model.set_books(self._library.books())

    # -- menus ------------------------------------------------------------

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        add_files = QAction("Add Books…", self)
        add_files.setShortcut(QKeySequence.StandardKey.Open)
        add_files.triggered.connect(self.add_books)
        file_menu.addAction(add_files)

        add_folder = QAction("Add Folder…", self)
        add_folder.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder)

        file_menu.addSeparator()

        self._remove_action = QAction("Remove from Library", self)
        self._remove_action.setShortcut(QKeySequence.StandardKey.Delete)
        self._remove_action.triggered.connect(self.remove_selected)
        self._remove_action.setEnabled(False)
        file_menu.addAction(self._remove_action)

        view_menu = self.menuBar().addMenu("&View")
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in.triggered.connect(self._reader.zoom_in)
        view_menu.addAction(zoom_in)

        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out.triggered.connect(self._reader.zoom_out)
        view_menu.addAction(zoom_out)

        settings_menu = self.menuBar().addMenu("&Settings")
        self._folder_action = QAction("Default Library Folder…", self)
        # macOS relocates actions it reads as preferences into the app menu;
        # keep this one where the user was told to look for it.
        self._folder_action.setMenuRole(QAction.MenuRole.NoRole)
        self._folder_action.triggered.connect(self.choose_library_folder)
        settings_menu.addAction(self._folder_action)
        self._refresh_folder_action()

    # -- adding books -----------------------------------------------------

    def add_books(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Books", str(self._settings.browse_folder()), _PDF_FILTER
        )
        if files:
            self._add_paths([Path(f) for f in files])

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Add Folder", str(self._settings.browse_folder())
        )
        if folder:
            added = self._library.add_folder(Path(folder))
            self._report_added(added, scanned_folder=True)

    def _add_paths(self, files: list[Path]) -> None:
        added = [book for book in (self._library.add_file(p) for p in files) if book]
        self._report_added(added, scanned_folder=False)

    def _report_added(self, added: list[Book], scanned_folder: bool) -> None:
        self._panel.model.add_books(added)
        if added:
            self._panel.select_book_id(added[0].id)
            noun = "book" if len(added) == 1 else "books"
            self.statusBar().showMessage(f"Added {len(added)} {noun}", 5000)
        else:
            hint = (
                "No new PDFs found in that folder."
                if scanned_folder
                else "Nothing added - those books are already in the library."
            )
            self.statusBar().showMessage(hint, 5000)

    # -- the default library folder ---------------------------------------

    def choose_library_folder(self) -> None:
        """Nominate the folder the user keeps books in, and offer to index it."""
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Default Library Folder", str(self._settings.browse_folder())
        )
        if not folder:
            return

        chosen = Path(folder)
        self._settings.set_library_folder(chosen)
        self._refresh_folder_action()
        self.statusBar().showMessage(f"Default library folder: {chosen}", 5000)

        scan = QMessageBox.question(
            self,
            "Add Books From This Folder",
            f"Add the PDFs in “{chosen.name}” to your library now?\n\n"
            "Files are indexed where they are - nothing is copied or moved.",
        )
        if scan == QMessageBox.StandardButton.Yes:
            self._report_added(self._library.add_folder(chosen), scanned_folder=True)

    def _refresh_folder_action(self) -> None:
        """Show the current folder on the menu item, so the setting is visible."""
        folder = self._settings.library_folder()
        self._folder_action.setToolTip(str(folder) if folder else "Not set")
        suffix = f"  ({folder.name})" if folder else ""
        self._folder_action.setText(f"Default Library Folder…{suffix}")

    # -- removing ---------------------------------------------------------

    def remove_selected(self) -> None:
        book = self._panel.selected_book()
        if book is None:
            return
        confirm = QMessageBox.question(
            self,
            "Remove from Library",
            f"Remove “{book.title}” from the library?\n\n"
            "The file stays where it is on disk.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._panel.remove_selected()
        self._library.remove(book.id)
        if self._current and self._current.id == book.id:
            self._current = None
            self._reader.clear()
        self.statusBar().showMessage(f"Removed {book.title}", 5000)

    # -- selection and reading -------------------------------------------

    def _on_book_selected(self, book: Book | None) -> None:
        self._remove_action.setEnabled(book is not None)
        if book is None:
            self._current = None
            self._reader.clear()
            self.setWindowTitle("Hermit")
            return

        if not book.exists:
            self._current = None
            self._reader.clear()
            self.statusBar().showMessage(f"File is missing: {book.path}")
            return

        error = self._reader.open(book.path, book.last_page)
        if error:
            self._current = None
            self.statusBar().showMessage(error)
            return

        self._current = book
        self.setWindowTitle(f"Hermit - {book.title}")
        self.statusBar().showMessage(str(book.path))

    def _on_page_changed(self, page: int, page_count: int) -> None:
        if self._current is None:
            return
        self._current.last_page = page
        self._current.page_count = page_count
        self._library.record_position(self._current.id, page, page_count)

    def _on_book_edited(self, top_left, bottom_right, roles=None) -> None:
        """Persist an in-place edit of a title or author cell."""
        book = self._panel.model.book_at(top_left.row())
        if book is None or top_left.column() not in (0, 1):
            return
        if top_left.column() == 0:
            self._library.set_title(book.id, book.title)
            if self._current and self._current.id == book.id:
                self.setWindowTitle(f"Hermit - {book.title}")
        else:
            self._library.set_author(book.id, book.author)

    def closeEvent(self, event) -> None:
        if self._current is not None:
            self._library.record_position(
                self._current.id,
                self._reader.current_page(),
                self._reader.page_count(),
            )
        super().closeEvent(event)
