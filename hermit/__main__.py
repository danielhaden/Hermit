"""Entry point: ``python -m hermit``."""

import sys

from PySide6.QtWidgets import QApplication

from hermit.model.library import Library
from hermit.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Hermit")
    app.setApplicationDisplayName("Hermit")

    library = Library()
    try:
        window = MainWindow(library)
        window.show()
        return app.exec()
    finally:
        library.close()


if __name__ == "__main__":
    sys.exit(main())
