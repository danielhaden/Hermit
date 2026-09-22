"""The sidebar and its columns are the user's to size, and stay where put."""

from hermit.ui.main_window import _MIN_READER, _MIN_SIDEBAR
from hermit.ui.main_window import MainWindow


def _window(library, settings, settle, width=1200):
    window = MainWindow(library, settings)
    window.resize(width, 800)
    window.show()
    settle()
    return window


def _header(window):
    return window._panel.table.horizontalHeader()


def test_every_column_can_be_dragged(library, settings, book_pdf, settle):
    """Stretch and ResizeToContents look tidy but refuse to be resized."""
    library.add_file(book_pdf)
    window = _window(library, settings, settle)
    header = _header(window)

    for column, target in ((0, 150), (1, 200), (2, 90)):
        header.resizeSection(column, target)
        settle(50)
        assert header.sectionSize(column) == target
    window.close()


def test_title_fills_the_space_left_by_the_others(library, settings, book_pdf, settle):
    library.add_file(book_pdf)
    window = _window(library, settings, settle)
    panel = window._panel

    assert sum(panel.column_widths()) == panel.table.viewport().width()
    window.close()


def test_title_follows_the_sidebar_until_a_column_is_dragged(
    library, settings, book_pdf, settle
):
    library.add_file(book_pdf)
    window = _window(library, settings, settle)
    panel = window._panel
    before = panel.column_widths()[0]

    window._splitter.moveSplitter(520, 1)
    settle(120)
    assert panel.column_widths()[0] > before  # Title took the new room

    _header(window).resizeSection(1, 210)
    settle(60)
    chosen = panel.column_widths()
    window._splitter.moveSplitter(700, 1)
    settle(120)

    assert panel.column_widths() == chosen  # the header is theirs now
    window.close()


def test_neither_pane_can_be_squeezed_away(library, settings, book_pdf, settle):
    library.add_file(book_pdf)
    window = _window(library, settings, settle)

    window._splitter.moveSplitter(10, 1)
    settle(80)
    assert window._splitter.sizes()[0] >= _MIN_SIDEBAR

    window._splitter.moveSplitter(1190, 1)
    settle(80)
    assert window._splitter.sizes()[1] >= _MIN_READER
    window.close()


def test_the_splitter_handle_is_grabbable(library, settings, settle):
    """A 4px handle is the platform default and reads as 'not adjustable'."""
    window = _window(library, settings, settle)
    assert window._splitter.handleWidth() >= 6
    window.close()


def test_the_layout_survives_a_restart(library, settings, book_pdf, settle, data_dir):
    from hermit.model.library import Library
    from hermit.model.settings import Settings

    library.add_file(book_pdf)
    window = _window(library, settings, settle)
    _header(window).resizeSection(1, 205)
    window._splitter.moveSplitter(430, 1)
    settle(100)
    expected_columns = window._panel.column_widths()
    expected_sidebar = window._splitter.sizes()[0]
    window.close()
    settle(80)
    settings.close()

    reopened_settings = Settings()
    reopened_library = Library()
    window = _window(reopened_library, reopened_settings, settle)

    assert window._splitter.sizes()[0] == expected_sidebar
    assert window._panel.column_widths() == expected_columns
    window.close()
    reopened_library.close()
    reopened_settings.close()
