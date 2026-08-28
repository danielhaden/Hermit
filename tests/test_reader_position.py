"""The reader pane, and the bug that made it forget where you were.

Reopening a book used to advance the saved page by one every time: with
fit-to-width, the pane relayouts after the jump, and a jump landing exactly on
a page boundary tips onto the following page. That settle was recorded as a
real page turn, so a book opened ten times sat ten pages further on.

These tests only bite at a deep page — see the ``drift_page`` fixture. Run
against the unguarded reader they fail, which is the point of them.
"""

from hermit.ui.main_window import MainWindow


def _window(library, settings, settle):
    window = MainWindow(library, settings)
    window.resize(1200, 800)
    window.show()
    settle()
    return window


def _open_first_book(window, settle):
    window._panel.table.selectRow(0)
    settle()


def _reopen(window, settle):
    """Deselect and reselect, the way returning to a book in the table does."""
    window._panel.table.clearSelection()
    settle(100)
    window._panel.table.selectRow(0)
    settle()


def test_opens_a_book_at_its_first_page(library, settings, book_pdf, settle):
    library.add_file(book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)

    assert window._reader.page_count() == 12
    assert window._reader.current_page() == 0
    window.close()


def test_reading_position_is_recorded(
    library, settings, long_book_pdf, drift_page, settle
):
    library.add_file(long_book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)

    window._reader.go_to_page(drift_page)
    settle()

    assert window._reader.current_page() == drift_page
    assert library.books()[0].last_page == drift_page
    window.close()


def test_reopening_resumes_where_you_left_off(
    library, settings, long_book_pdf, drift_page, settle
):
    library.add_file(long_book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)
    window._reader.go_to_page(drift_page)
    settle()

    _reopen(window, settle)

    assert window._reader.current_page() == drift_page
    window.close()


def test_the_saved_page_does_not_drift_across_reopens(
    library, settings, long_book_pdf, drift_page, settle
):
    """The regression: five reopens must not move the reader a single page."""
    library.add_file(long_book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)
    window._reader.go_to_page(drift_page)
    settle()

    for _ in range(5):
        _reopen(window, settle)

    assert window._reader.current_page() == drift_page
    assert library.books()[0].last_page == drift_page
    window.close()


def test_a_real_page_turn_after_reopening_is_still_recorded(
    library, settings, long_book_pdf, drift_page, settle
):
    """The restore guard must not swallow genuine navigation afterwards."""
    library.add_file(long_book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)
    window._reader.go_to_page(drift_page)
    settle()
    _reopen(window, settle)

    window._reader.next_page()
    settle()

    assert window._reader.current_page() == drift_page + 1
    assert library.books()[0].last_page == drift_page + 1
    window.close()


def test_a_missing_file_keeps_its_saved_position(
    library, settings, long_book_pdf, drift_page, settle
):
    library.add_file(long_book_pdf)
    window = _window(library, settings, settle)
    _open_first_book(window, settle)
    window._reader.go_to_page(drift_page)
    settle()

    long_book_pdf.unlink()
    _reopen(window, settle)

    assert library.books()[0].last_page == drift_page
    window.close()
