"""Indexing books, and the promise that their files are left alone."""

from hermit.model.library import Library


def test_adds_a_book(library, book_pdf):
    book = library.add_file(book_pdf)
    assert book is not None
    assert book.page_count == 12
    assert library.books() == [book] or len(library.books()) == 1


def test_never_touches_the_file(library, book_pdf):
    """Indexing is non-destructive: same location, same bytes."""
    before = book_pdf.read_bytes()
    stamp = book_pdf.stat().st_mtime
    library.add_file(book_pdf)
    assert book_pdf.exists()
    assert book_pdf.read_bytes() == before
    assert book_pdf.stat().st_mtime == stamp


def test_removing_leaves_the_file_on_disk(library, book_pdf):
    book = library.add_file(book_pdf)
    library.remove(book.id)
    assert library.books() == []
    assert book_pdf.exists()


def test_rejects_a_duplicate(library, book_pdf):
    assert library.add_file(book_pdf) is not None
    assert library.add_file(book_pdf) is None
    assert len(library.books()) == 1


def test_rejects_a_non_pdf(library, tmp_path):
    decoy = tmp_path / "notes.txt"
    decoy.write_text("plain text")
    assert library.add_file(decoy) is None


def test_adds_a_folder_skipping_non_pdfs(library, make_pdf, tmp_path):
    make_pdf("one.pdf", pages=2)
    make_pdf("two.pdf", pages=3)
    make_pdf("three-no-extension", pages=4)
    (tmp_path / "readme.txt").write_text("not a book")
    report = library.add_folder(tmp_path)
    assert len(report.added) == 3
    assert report.duplicates == []


def test_rescanning_a_folder_adds_nothing_new(library, make_pdf, tmp_path):
    make_pdf("one.pdf", pages=2)
    library.add_folder(tmp_path)
    rescan = library.add_folder(tmp_path)
    assert rescan.added == []
    assert len(rescan.duplicates) == 1


def test_title_and_author_edits_persist(library, book_pdf, data_dir):
    book = library.add_file(book_pdf)
    library.set_title(book.id, "Corrected Title")
    library.set_author(book.id, "A. Writer")
    library.close()

    reopened = Library()  # a fresh connection, as a restart would give
    stored = reopened.books()[0]
    assert (stored.title, stored.author) == ("Corrected Title", "A. Writer")
    reopened.close()


def test_reading_position_persists(library, book_pdf, data_dir):
    book = library.add_file(book_pdf)
    library.record_position(book.id, 7, 12)
    library.close()

    reopened = Library()
    assert reopened.books()[0].last_page == 7
    reopened.close()


def test_a_moved_file_stays_in_the_library(library, book_pdf):
    """A book whose file vanishes is flagged, not silently dropped."""
    book = library.add_file(book_pdf)
    book_pdf.unlink()
    assert len(library.books()) == 1
    assert not library.books()[0].exists
    assert book.id == library.books()[0].id


def test_a_book_without_a_pdf_extension_can_be_added(library, make_pdf):
    """The bug: books are routinely stored with no .pdf suffix.

    The model always handled these; the file dialog was hiding them. This
    pins the model half so the fix can't rot from underneath the UI.
    """
    bare = make_pdf("The Spiral Calendar and its Effects on Financial Markets")
    assert bare.suffix == ""
    report = library.add_files([bare])
    assert len(report.added) == 1
    assert report.added[0].page_count == 12


def test_add_files_separates_the_reasons_for_skipping(library, make_pdf, tmp_path):
    """A duplicate and a non-book are both 'not added' but not the same thing."""
    first = make_pdf("first.pdf", pages=2)
    library.add_file(first)
    fresh = make_pdf("fresh.pdf", pages=2)
    decoy = tmp_path / "notes.txt"
    decoy.write_text("not a book")

    report = library.add_files([first, fresh, decoy])

    assert [b.path.name for b in report.added] == ["fresh.pdf"]
    assert [p.name for p in report.duplicates] == ["first.pdf"]
    assert [p.name for p in report.not_books] == ["notes.txt"]
