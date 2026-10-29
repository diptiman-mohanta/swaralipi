"""Drives the real window through a whole session (no microphone needed)."""

from pathlib import Path

import pytest

from recorder import audio, config, qc
from tests.conftest import speech_like

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture
def window(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(audio, "check_settings", lambda s: None)   # CI has no sound card
    monkeypatch.setattr(audio, "default_input_name", lambda: "Microphone Array (Test)")
    from recorder.ui.main_window import MainWindow
    w = MainWindow()
    w.resize(1180, 820)
    w.show()
    yield w
    w.record_page.take = None
    w.close()


def fill_speaker(page, language="English"):
    page.name.setText("Test Person")
    page.mobile.setText("9876501234")
    page.birth_year.setCurrentText("1995")
    page.gender.setCurrentText("Female")
    page.mother_tongue.setEditText("Odia")
    page.education.setCurrentText("Graduate")
    page.state.setCurrentText("Odisha")
    page.district.setCurrentText("Puri")
    page.pincode.setText("752001")
    page.area.setCurrentText("Urban")
    page.environment.setCurrentText("Quiet room (home)")
    page.select_language(language)


def start_session(w, mode, tmp_path, language="English"):
    w.set_mode(mode)
    w.audio_page.out_dir.setText(str(tmp_path / "rec"))
    w.audio_page.save()
    assert w.stack.currentWidget() is w.consent_page
    for c in w.consent_page.checks:
        c.setChecked(True)
    w.consent_page.accept()
    fill_speaker(w.speaker_page, language)
    w.speaker_page.save()


def give_take(page):
    page.take = speech_like()
    page.take_qc = qc.analyze(page.take, page.session.audio.sample_rate)
    page._update_ui()


def test_typed_session(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path)
    rp = window.record_page
    assert window.stack.currentWidget() is rp
    assert window.speaker_page.mic.currentText() == "Laptop built-in mic"   # from device name

    rp.transcript.setPlainText("  The train   leaves at six. ")
    rp.confirm_transcript()
    assert rp.locked_text == "The train leaves at six."
    give_take(rp)
    rp.submit()

    store = window.session.store
    rec = list(store.records.values())[0]
    assert rec["sentence_id"].startswith(store.speaker_id + "_F")
    assert rec["text"] == "The train leaves at six."
    assert rec["sample_rate"] == 48000 and rec["audio_16k_filepath"]   # locked preset
    assert (store.dir / rec["audio_filepath"]).exists()
    assert rp.locked_text == ""                                         # ready for the next one


def test_script_session_and_resume(window, tmp_path, dialogs):
    start_session(window, config.MODE_SCRIPT, tmp_path)
    rp = window.record_page
    rp.load_script_file(str(SAMPLES / "demo_script_english.csv"))
    assert rp.idx == 0
    give_take(rp)
    rp.submit()
    assert rp.idx == 1                                                  # moved on
    sid = window.session.store.speaker_id
    assert window.session.store.has(sid + "_S000001")

    rp.begin(window.session)                                            # reopen: resumes
    assert rp.idx == 1


def test_wrong_language_goes_back(window, tmp_path, dialogs, qapp):
    start_session(window, config.MODE_SCRIPT, tmp_path, language="Odia")
    first_id = window.session.store.speaker_id
    dialogs["button"] = 0                                               # "Change the language"
    window.record_page.load_script_file(str(SAMPLES / "demo_script_english.csv"))
    for _ in range(5):
        qapp.processEvents()
    assert ("dialog", "Check the recording language") in dialogs["shown"]
    assert window.stack.currentWidget() is window.speaker_page
    assert not (tmp_path / "rec" / first_id).exists()                  # empty folder removed


def test_private_details_in_typed_sentence(window, tmp_path, dialogs):
    from PySide6.QtWidgets import QMessageBox
    start_session(window, config.MODE_TYPED, tmp_path)
    rp = window.record_page
    dialogs["answer"] = QMessageBox.No
    rp.transcript.setPlainText("My name is Test Person")
    rp.confirm_transcript()
    assert ("question", "Personal details in the sentence") in dialogs["shown"]
    assert rp.locked_text == ""


def test_bluetooth_warning(window, tmp_path, dialogs):
    from PySide6.QtWidgets import QMessageBox
    window.set_mode(config.MODE_TYPED)
    ap = window.audio_page
    ap.device.addItem("Headset (realme Buds T310)  [MME]", "Headset (realme Buds T310)  [MME]")
    ap.device.setCurrentIndex(ap.device.count() - 1)
    assert not ap.device_note.isHidden()
    dialogs["answer"] = QMessageBox.No
    ap.save()
    assert ("question", "Bluetooth microphone") in dialogs["shown"]
    assert window.stack.currentWidget() is ap


def test_locked_format_disables_fields(window):
    window.set_mode(config.MODE_TYPED)
    assert window.locked_preset
    assert not window.audio_page.rate.isEnabled()
    assert not window.audio_page.lock_note.isHidden()
