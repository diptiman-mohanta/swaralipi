"""Swaralipi - start the app with:  python app.py"""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from recorder import APP_NAME
from recorder.ui.main_window import MainWindow
from recorder.ui.style import STYLESHEET, light_palette, load_fonts


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "swaralipi-icon.png")))
    load_fonts()
    app.setStyle("Fusion")
    app.setPalette(light_palette())
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
