"""Reading a PDF's identity off disk: is it one, and what does it call itself?"""

from pathlib import Path

from PySide6.QtPdf import QPdfDocument

_MAGIC = b"%PDF-"


def is_pdf(path: Path) -> bool:
    """Whether the file is a PDF, judged by its header rather than its name.

    Some books arrive without a ``.pdf`` extension, so sniff the magic bytes.
    """
    try:
        with path.open("rb") as handle:
            return handle.read(len(_MAGIC)) == _MAGIC
    except OSError:
        return False


def read_metadata(path: Path) -> tuple[str, str, int]:
    """Return ``(title, author, page_count)`` for a PDF.

    Falls back to the file name when the document carries no title, which is
    the common case for scanned or converted books.
    """
    document = QPdfDocument()
    title = author = ""
    page_count = 0
    if document.load(str(path)) == QPdfDocument.Error.None_:
        title = str(document.metaData(QPdfDocument.MetaDataField.Title) or "").strip()
        author = str(document.metaData(QPdfDocument.MetaDataField.Author) or "").strip()
        page_count = document.pageCount()
    document.close()
    return (title or path.stem, author, page_count)
