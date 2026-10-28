"""Swaralipi - start the app with:  python app.py"""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from recorder import APP_NAME
from recorder.config import APP_DIR, ASSETS_DIR
from recorder.ui.main_window import MainWindow
from recorder.ui.style import STYLESHEET, light_palette, load_fonts


def smoke_test(window) -> list[str]:
    """Checks that a packaged build can find its resources and audio libraries.
    Run with:  Swaralipi.exe --smoke-test   (exit code 0 = OK; details in smoke-test.log)"""
    import numpy as np
    import soundfile as sf
    import sounddevice  # noqa: F401  (loads the PortAudio library)
    import soxr
    from PySide6.QtGui import QFontDatabase
    from recorder import config, crypto

    problems = []
    if "IBM Plex Sans" not in QFontDatabase.families():
        problems.append("fonts not loaded")
    if QApplication.windowIcon().isNull():
        problems.append("window icon missing")
    if not config.load_india_locations():
        problems.append("location data missing")
    if not config.CONSENT_FILE.is_file():
        problems.append(f"consent text missing at {config.CONSENT_FILE}")
    if not crypto.encryption_available():
        problems.append("config/public_key.pem missing: contact details would not be encrypted")
    tone = np.sin(np.linspace(0, 2000, 48000)).astype(np.float32)
    tmp = APP_DIR / "smoke-test.wav"
    try:
        sf.write(str(tmp), soxr.resample(tone, 48000, 16000), 16000, subtype="PCM_16")
        if sf.info(str(tmp)).samplerate != 16000:
            problems.append("audio write/read mismatch")
    except Exception as e:
        problems.append(f"audio libraries: {e}")
    finally:
        tmp.unlink(missing_ok=True)
    if window.stack.count() != 6:
        problems.append("screens missing")
    return problems


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(ASSETS_DIR / "swaralipi-icon.png")))
    load_fonts()
    app.setStyle("Fusion")
    app.setPalette(light_palette())
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        problems = smoke_test(window)
        (APP_DIR / "smoke-test.log").write_text("\n".join(problems) or "OK", encoding="utf-8")
        QTimer.singleShot(0, app.quit)
        app.exec()
        return 1 if problems else 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
