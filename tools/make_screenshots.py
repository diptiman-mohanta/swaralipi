"""Regenerate the README screenshots in docs/screenshots/ with made-up demo data.

    .venv\\Scripts\\python tools\\make_screenshots.py
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from recorder import audio, config, crypto, qc  # noqa: E402
from tests.conftest import speech_like  # noqa: E402

OUT = ROOT / "docs" / "screenshots"


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    config.USER_SETTINGS_FILE = tmp / "user_settings.json"
    config.DEFAULT_OUTPUT_DIR = tmp / "recordings"
    crypto.PUBLIC_KEY_FILE = tmp / "none.pem"
    audio.check_settings = lambda s: None
    audio.default_input_name = lambda: "Microphone (USB Audio Device)"
    for kind in ("question", "information", "warning"):
        setattr(QMessageBox, kind, staticmethod(lambda *a, **k: QMessageBox.Yes))

    from recorder.ui.main_window import MainWindow
    from recorder.ui.style import STYLESHEET, light_palette, load_fonts
    app = QApplication([])
    load_fonts()
    app.setStyle("Fusion")
    app.setPalette(light_palette())
    app.setStyleSheet(STYLESHEET)
    OUT.mkdir(parents=True, exist_ok=True)

    w = MainWindow()
    w.resize(1180, 780)
    w.show()

    def shot(name):
        app.processEvents()
        w.grab().save(str(OUT / f"{name}.png"))

    shown_path = r"C:\Swaralipi\recordings"   # neutral path instead of the real temp folder
    w.set_mode(config.MODE_SCRIPT)
    w.audio_page.out_dir.setText(shown_path)
    shot("2-audio-settings")
    w.audio_page.out_dir.setText(str(tmp / "recordings"))
    w.audio_page.save()
    w.consent_page.checks[0].setChecked(True)
    shot("3-consent")
    for c in w.consent_page.checks:
        c.setChecked(True)
    w.consent_page.accept()
    sp = w.speaker_page
    sp.name.setText("Demo Speaker")
    sp.mobile.setText("9000000001")
    sp.birth_year.setCurrentText("1998")
    sp.gender.setCurrentText("Female")
    sp.mother_tongue.setEditText("Odia")
    sp.other_langs.setText("Hindi, English")
    sp.education.setCurrentText("Graduate")
    sp.occupation.setEditText("Teacher / Academic")
    sp.state.setCurrentText("Odisha")
    sp.district.setCurrentText("Cuttack")
    sp.pincode.setText("753001")
    sp.area.setCurrentText("Urban")
    sp.environment.setCurrentText("Quiet room (home)")
    shot("4-speaker")
    sp.save()

    rp = w.record_page
    rp.load_script_file(str(ROOT / "samples" / "demo_script_english.csv"))
    for _ in range(4):
        rp.take = speech_like()
        rp.take_qc = qc.analyze(rp.take, 48000)
        rp.submit()
    rp.take = speech_like(level=0.25)
    rp.take_qc = qc.analyze(rp.take, 48000)
    rp._show_qc(rp.take_qc)
    rp._update_ui()
    shot("5-record")

    # Hindi speaker typing with English letters, letter keys open.
    rp.leave()
    w.session.mode = config.MODE_TYPED
    w.new_speaker()
    for c in w.consent_page.checks:
        c.setChecked(True)
    w.consent_page.accept()
    sp.name.setText("Demo Speaker Two")
    sp.mobile.setText("9000000002")
    sp.birth_year.setCurrentText("1990")
    sp.gender.setCurrentText("Male")
    sp.mother_tongue.setEditText("Hindi")
    sp.education.setCurrentText("Postgraduate")
    sp.state.setCurrentText("Uttar Pradesh")
    sp.district.setCurrentText("Lucknow")
    sp.pincode.setText("226001")
    sp.area.setCurrentText("Urban")
    sp.environment.setCurrentText("Quiet room (home)")
    sp.select_language("Hindi")
    sp.save()
    rp.keys_btn.setChecked(True)
    rp.transcript.setFocus()
    QTest.keyClicks(rp.transcript, "mera naam raam hai. aap kaise ")
    QTest.keyClicks(rp.transcript, "hain")
    shot("6-hindi-typing")
    rp.transcript.clear()
    rp.keys_btn.setChecked(False)

    w.go_welcome()
    w.welcome.folder.setText(shown_path)
    shot("1-welcome")
    print(f"Screenshots written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
