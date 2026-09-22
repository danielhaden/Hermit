"""The left-hand panel: a filter box and the table of books."""

from PySide6.QtCore import QEvent, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QFont
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

# The library is a dense list beside the page being read; a point smaller
# than the interface default keeps it subordinate to the book.
_FONT_REDUCTION = 1

_MIN_COLUMN = 48
_MIN_TITLE = 80
_DEFAULT_AUTHOR = 110
_DEFAULT_PAGES = 64


def _smaller(font: QFont, points: int = _FONT_REDUCTION) -> QFont:
    """A copy of a font a point smaller, in whichever unit it happens to use."""
    smaller = QFont(font)
    if font.pointSizeF() > 0:
        smaller.setPointSizeF(max(1.0, font.pointSizeF() - points))
    else:
        smaller.setPixelSize(max(1, font.pixelSize() - points))
    return smaller


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
        # The header keeps its own font rather than inheriting the view's, so
        # it needs setting too or the column labels stay a point larger.
        self.table_font = _smaller(self.font())
        self.table.setFont(self.table_font)
        self.table.horizontalHeader().setFont(self.table_font)
        self.model.set_base_font(self.table_font)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Every column is Interactive so every one can be dragged. Stretch and
        # ResizeToContents both look tidy and both refuse to be resized by
        # hand, which is what made most of this header feel stuck.
        header = self.table.horizontalHeader()
        for column in range(self.model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(_MIN_COLUMN)
        header.setStretchLastSection(False)
        self._columns_customised = False
        self._applying_widths = False
        self._set_section(1, _DEFAULT_AUTHOR)
        self._set_section(2, _DEFAULT_PAGES)
        header.sectionResized.connect(self._on_section_resized)
        # The panel's own resizeEvent arrives before the table has been laid
        # out inside it, so Title would be fitted against a stale width.
        # Watching the viewport catches the size that actually matters.
        self.table.viewport().installEventFilter(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(self._filter)
        layout.addWidget(self.table)

        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    # -- column widths ----------------------------------------------------

    def _set_section(self, column: int, width: int) -> None:
        """Resize a column without it counting as the user's own choice."""
        self._applying_widths = True
        self.table.horizontalHeader().resizeSection(column, width)
        self._applying_widths = False

    def _on_section_resized(self, *_args) -> None:
        if not self._applying_widths:
            self._columns_customised = True

    def _fit_title_column(self) -> None:
        """Give Title whatever room the other columns leave.

        Only until the user sizes a column themselves - after that the header
        is theirs, and widening the sidebar leaves their proportions alone.
        """
        if self._columns_customised:
            return
        header = self.table.horizontalHeader()
        spare = self.table.viewport().width() - (
            header.sectionSize(1) + header.sectionSize(2)
        )
        self._set_section(0, max(_MIN_TITLE, spare))

    def column_widths(self) -> list[int]:
        header = self.table.horizontalHeader()
        return [header.sectionSize(c) for c in range(self.model.columnCount())]

    def apply_column_widths(self, widths: list[int]) -> None:
        """Restore widths saved from a previous session."""
        if not widths:
            return
        for column, width in enumerate(widths[: self.model.columnCount()]):
            self._set_section(column, max(_MIN_COLUMN, width))
        self._columns_customised = True

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table.viewport() and event.type() == QEvent.Type.Resize:
            self._fit_title_column()
        return super().eventFilter(watched, event)

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
