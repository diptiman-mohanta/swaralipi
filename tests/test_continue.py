"""Continuing with a speaker recorded earlier, and the private-details check behind it."""

import json

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox

from recorder import audio, config, privacy
from tests.test_app_flow import give_take, start_session


@pytest.fixture
def window(qapp, monkeypatch):
    monkeypatch.setattr(audio, "check_settings", lambda s: None)
    monkeypatch.setattr(audio, "default_input_name", lambda: "Microphone Array (Test)")
    from recorder.ui.main_window import MainWindow
    w = MainWindow()
    w.resize(1180, 820)
    w.show()
    yield w
    w.record_page.take = None
    w.close()


def record_one(window, tmp_path, language="Hindi"):
    start_session(window, config.MODE_TYPED, tmp_path, language=language)
    rp = window.record_page
    rp.transcript.setFocus()
    QTest.keyClicks(rp.transcript, "namaste")
    rp.confirm_transcript()
    give_take(rp)
    rp.submit()
    return window.session.store


def continue_dialog(window):
    from recorder.ui.pages import ContinueDialog
    return ContinueDialog(window, window.session.audio.output_dir)


def test_continue_without_entering_details_again(window, tmp_path, dialogs):
    store = record_one(window, tmp_path)
    speaker_id = store.speaker_id
    window.go_welcome()
    assert window.welcome.continue_btn.isVisible()

    dlg = continue_dialog(window)
    assert dlg.list.count() == 1 and speaker_id in dlg.list.item(0).text()
    assert "Hindi" in dlg.list.item(0).text() and "1 recording" in dlg.list.item(0).text()
    assert dlg.mode.currentText().startswith("Type a sentence")
    assert dlg.environment.currentText() == "Quiet room (home)"
    assert "Consent was given" in dlg.consent_lbl.text()
    dlg.start()

    s = window.session
    assert window.stack.currentWidget() is window.record_page
    assert s.continued and s.store.speaker_id == speaker_id and len(s.store.records) == 1
    assert window.record_page.back_btn.text() == "Back to home"
    consent = json.loads((s.store.dir / "consent.json").read_text(encoding="utf-8"))
    assert len(consent) == 1                              # not asked again

    # The speaker's name is still caught, from the remembered (hashed) check.
    rp = window.record_page
    dialogs["answer"] = QMessageBox.No
    rp.transcript.setFocus()
    QTest.keyClicks(rp.transcript, "mera naam test hai")
    rp.confirm_transcript()
    assert ("question", "Personal details in the sentence") in dialogs["shown"]

    rp.transcript.clear()
    QTest.keyClicks(rp.transcript, "dhanyavaad")
    rp.confirm_transcript()
    give_take(rp)
    rp.submit()
    assert len(s.store.records) == 2
    rp.go_back()
    assert window.stack.currentWidget() is window.welcome


def test_search_filters_speakers(window, tmp_path, dialogs):
    record_one(window, tmp_path)
    dlg = continue_dialog(window)
    dlg.search.setText("lucknow")
    assert dlg.selected() is None and not dlg.start_btn.isEnabled()
    dlg.search.setText("hindi puri")
    assert dlg.selected() is not None


def test_consent_comes_first_when_missing(window, tmp_path, dialogs):
    store = record_one(window, tmp_path)
    (store.dir / "consent.json").unlink()
    window.go_welcome()
    dlg = continue_dialog(window)
    assert "No consent" in dlg.consent_lbl.text()
    dlg.start()
    assert window.stack.currentWidget() is window.consent_page
    for c in window.consent_page.checks:
        c.setChecked(True)
    window.consent_page.accept()
    assert window.stack.currentWidget() is window.record_page
    assert window.session.continued
    assert len(json.loads((store.dir / "consent.json").read_text(encoding="utf-8"))) == 1


def test_no_continue_button_without_speakers(window):
    window.go_welcome()
    assert not window.welcome.continue_btn.isVisible()


# ---------------------------------------------------------------- hashed check
def test_private_check_finds_name_number_and_email():
    check = privacy.PrivateCheck.from_details("Ravi Kumar", "98765 43210", "ravi@example.com",
                                              "Hindi")
    assert check.found_in("my friend ravi came")
    assert check.found_in("मेरा नाम रवि है")                       # the name typed in Hindi
    assert check.found_in("call ९८७६५४३२१० now")                     # digits in Devanagari
    assert check.found_in("write to Ravi@Example.com.")
    assert not check.found_in("the weather is nice today")
    assert not check.found_in("call 1234567890")


def test_private_check_is_remembered_without_plain_details():
    check = privacy.PrivateCheck.from_details("Ravi Kumar", "9876543210", "", "Hindi")
    privacy.remember("hin_X", check)
    stored = privacy.CHECKS_FILE.read_text(encoding="utf-8")
    assert "ravi" not in stored.lower() and "9876543210" not in stored and "रवि" not in stored
    again = privacy.recall("hin_X")
    assert again.found_in("ravi") and again.found_in("9876543210")
    assert privacy.recall("someone_else") is None


# ---------------------------------------------------------------- export several at once
def test_export_shows_what_is_not_exported_yet(window, tmp_path, dialogs):
    from recorder.ui.pages import ExportDialog
    store = record_one(window, tmp_path)
    out = window.session.audio.output_dir
    dlg = ExportDialog(window, out)
    assert "not exported yet" in dlg.list.item(0).text()
    assert dlg.checked() == [store.dir] and dlg.export_btn.text() == "Export zip"
    dlg.export()
    assert len(list((tmp_path / "rec" / "submissions").glob("*.zip"))) == 1
    assert "exported" in dlg.list.item(0).text() and not dlg.checked()
    assert not dlg.export_btn.isEnabled()

    # More recordings later: the speaker is offered again.
    window.go_welcome()
    continue_dialog(window).start()
    rp = window.record_page
    QTest.keyClicks(rp.transcript, "dhanyavaad")
    rp.confirm_transcript()
    give_take(rp)
    rp.submit()
    dlg = ExportDialog(window, out)
    assert "new recordings since the export" in dlg.list.item(0).text()
    assert dlg.checked() == [store.dir]
