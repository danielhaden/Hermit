"""Table model backing the library list on the left-hand side."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont

from hermit.model.book import Book

_COLUMNS = ("Title", "Author", "Pages")
_MISSING = QColor(160, 60, 60)


class LibraryModel(QAbstractTableModel):
    """Presents the library's books as rows: title, author, page count."""

    def __init__(self, books: list[Book] | None = None) -> None:
        super().__init__()
        self._books: list[Book] = list(books or [])

    # -- population -------------------------------------------------------

    def set_books(self, books: list[Book]) -> None:
        self.beginResetModel()
        self._books = list(books)
        self.endResetModel()

    def add_books(self, books: list[Book]) -> None:
        if not books:
            return
        start = len(self._books)
        self.beginInsertRows(QModelIndex(), start, start + len(books) - 1)
        self._books.extend(books)
        self.endInsertRows()

    def remove_row(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._books[row]
        self.endRemoveRows()

    def book_at(self, row: int) -> Book | None:
        if 0 <= row < len(self._books):
            return self._books[row]
        return None

    def row_of(self, book_id: int) -> int:
        for row, book in enumerate(self._books):
            if book.id == book_id:
                return row
        return -1

    def refresh_row(self, row: int) -> None:
        if 0 <= row < len(self._books):
            left = self.index(row, 0)
            right = self.index(row, len(_COLUMNS) - 1)
            self.dataChanged.emit(left, right)

    # -- QAbstractTableModel ----------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._books)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        book = self._books[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return book.title
            if column == 1:
                return book.author
            return str(book.page_count) if book.page_count else ""

        if role == Qt.ItemDataRole.EditRole and column in (0, 1):
            return book.title if column == 0 else book.author

        if role == Qt.ItemDataRole.TextAlignmentRole and column == 2:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.ItemDataRole.ToolTipRole:
            location = str(book.path)
            if not book.exists:
                return f"File is missing:\n{location}"
            if book.last_page:
                return f"{location}\n\nLast read: page {book.last_page + 1}"
            return location

        # A book whose file has moved or been deleted still belongs to the
        # library - flag it rather than dropping it silently.
        if not book.exists:
            if role == Qt.ItemDataRole.ForegroundRole:
                return QBrush(_MISSING)
            if role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setItalic(True)
                return font

        return None

    def flags(self, index):
        flags = super().flags(index)
        if index.column() in (0, 1):  # title and author are user-editable
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or index.column() not in (0, 1):
            return False
        book = self._books[index.row()]
        text = str(value).strip()
        if index.column() == 0:
            if not text:
                return False
            book.title = text
        else:
            book.author = text
        self.dataChanged.emit(index, index)
        return True
