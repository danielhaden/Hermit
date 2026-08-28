"""The left-hand panel: a filter box and the table of books."""

from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLineEdit,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from hermit.model.book import Book
from hermit.ui.library_model import LibraryModel


class LibraryPanel(QWidget):
    """Lists the library and announces which book the user picked."""

    book_selected = Signal(object)  # Book, or None when the selection clears

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model = LibraryModel()
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self.model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # match title or author

        self._filter = QLineEdit(self)
        self._filter.setPlaceholderText("Filter by title or author")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._proxy.setFilterFixedString)

        self.table = QTableView(self)
        self.table.setModel(self._proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(1, 110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(self._filter)
        layout.addWidget(self.table)

        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    # -- selection --------------------------------------------------------

    def selected_book(self) -> Book | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.model.book_at(self._proxy.mapToSource(rows[0]).row())

    def select_book_id(self, book_id: int) -> None:
        row = self.model.row_of(book_id)
        if row < 0:
            return
        proxy_index = self._proxy.mapFromSource(self.model.index(row, 0))
        self.table.selectRow(proxy_index.row())
        self.table.scrollTo(proxy_index)

    def remove_selected(self) -> Book | None:
        """Drop the selected row from the table and return the book it held."""
        book = self.selected_book()
        if book is None:
            return None
        self.model.remove_row(self.model.row_of(book.id))
        return book

    def _on_selection(self) -> None:
        self.book_selected.emit(self.selected_book())
