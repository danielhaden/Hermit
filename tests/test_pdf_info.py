"""PDFs are identified by their header, not their file name."""

from hermit.model.pdf_info import is_pdf, read_metadata


def test_recognises_a_pdf(book_pdf):
    assert is_pdf(book_pdf)


def test_recognises_a_pdf_saved_without_an_extension(make_pdf):
    """Books are routinely stored with no .pdf suffix; they must still count."""
    bare = make_pdf("Some Book Without An Extension", pages=3)
    assert bare.suffix == ""
    assert is_pdf(bare)


def test_rejects_a_non_pdf(tmp_path):
    decoy = tmp_path / "notes.pdf"  # right name, wrong contents
    decoy.write_text("I am not a PDF")
    assert not is_pdf(decoy)


def test_rejects_a_missing_file(tmp_path):
    assert not is_pdf(tmp_path / "nothing-here.pdf")


def test_reads_page_count(book_pdf):
    _, _, pages = read_metadata(book_pdf)
    assert pages == 12


def test_falls_back_to_the_file_name_when_untitled(make_pdf):
    untitled = make_pdf("Quiet Book.pdf", pages=2)
    title, _, _ = read_metadata(untitled)
    assert title == "Quiet Book"


def test_prefers_the_embedded_title(make_pdf):
    titled = make_pdf("filename.pdf", pages=2, title="The Real Title")
    title, _, _ = read_metadata(titled)
    assert title == "The Real Title"
