"""What the status bar says after an add, and why the dialog shows everything."""

from pathlib import Path

from hermit.model.library import AddReport
from hermit.ui.main_window import _FILE_FILTER, _describe


def _report(added=0, duplicates=0, not_books=()):
    return AddReport(
        added=[object()] * added,
        duplicates=[Path(f"dupe-{n}.pdf") for n in range(duplicates)],
        not_books=[Path(name) for name in not_books],
    )


def test_the_file_dialog_does_not_default_to_a_pdf_only_filter():
    """The bug: a *.pdf filter greys out books stored without an extension.

    They are readable, and the app detects them by header - so the dialog must
    not hide them before the header is ever looked at.
    """
    default_filter = _FILE_FILTER.split(";;")[0]
    assert "*.pdf" not in default_filter
    assert "(*)" in default_filter


def test_reports_a_single_book():
    assert _describe(_report(added=1), scanned_folder=False) == "Added 1 book"


def test_reports_several_books():
    assert _describe(_report(added=3), scanned_folder=False) == "Added 3 books"


def test_mentions_duplicates_alongside_what_was_added():
    message = _describe(_report(added=2, duplicates=1), scanned_folder=False)
    assert message == "Added 2 books · 1 already in the library"


def test_explains_a_hand_picked_file_that_is_not_a_pdf():
    """Silence here is what made the app feel broken."""
    message = _describe(_report(not_books=["notes.txt"]), scanned_folder=False)
    assert message == "“notes.txt” is not a PDF, so it was not added"


def test_explains_a_duplicate_picked_on_its_own():
    message = _describe(_report(duplicates=1), scanned_folder=False)
    assert message == "That book is already in the library"


def test_a_folder_scan_does_not_grumble_about_non_books():
    """Folders hold all sorts of files; passing over them is unremarkable."""
    message = _describe(
        _report(added=2, not_books=["a.txt", "b.zip"]), scanned_folder=True
    )
    assert message == "Added 2 books"


def test_an_empty_folder_says_so():
    message = _describe(_report(not_books=["a.txt"]), scanned_folder=True)
    assert message == "No books found in that folder"
