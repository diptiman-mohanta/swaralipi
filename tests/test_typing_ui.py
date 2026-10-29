"""Typing Indian languages in the real recording screen, key by key."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from recorder import audio, config
from recorder.typing import phonetic
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


def test_typing_hindi_sentence(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    ed = rp.transcript
    assert ed.phonetic_on and rp.typing_row.isVisible()
    ed.setFocus()
    QTest.keyClicks(ed, "mera naam raam")
    assert rp.suggestion_bar.latin.text() == "raam" and rp.suggestion_bar.buttons[0].text().endswith("राम")
    QTest.keyClicks(ed, " hai. aap kaise hain?")
    assert ed.toPlainText() == "मेरा नाम राम है। आप कैसे हैं?"

    QTest.keyClicks(ed, " namastee")
    QTest.keyClick(ed, Qt.Key_Backspace)          # edits the Latin letters, not the script
    assert ed.toPlainText().endswith(" नमस्ते")
    for _ in range(8):
        QTest.keyClick(ed, Qt.Key_Backspace)
    assert ed.toPlainText() == "मेरा नाम राम है। आप कैसे हैं?"

    rp.confirm_transcript()
    give_take(rp)
    rp.submit()
    rec = list(window.session.store.records.values())[0]
    assert rec["text"] == "मेरा नाम राम है। आप कैसे हैं?"
    assert (rec["language"], rec["language_code"], rec["script"]) == ("Hindi", "hin", "Deva")
    assert window.session.store.speaker_id.startswith("hin_")


def test_ctrl_space_switches_to_english_letters(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    ed = rp.transcript
    ed.setFocus()
    QTest.keyClick(ed, Qt.Key_Space, Qt.ControlModifier)
    assert not ed.phonetic_on and rp.latin_btn.isChecked()
    QTest.keyClicks(ed, "OK")
    assert ed.toPlainText() == "OK"
    QTest.keyClick(ed, Qt.Key_Space, Qt.ControlModifier)
    assert ed.phonetic_on


def test_letter_keys_insert_characters(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    rp.keys_btn.setChecked(True)
    assert rp.keys_panel.isVisible()
    for ch in ("क", "ि", "त", "ा", "ब"):
        rp.keys_panel.keys.key_pressed.emit(ch)
    assert rp.transcript.toPlainText() == "किताब"


def test_name_in_hindi_is_flagged(window, tmp_path, dialogs):
    from PySide6.QtWidgets import QMessageBox
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    dialogs["answer"] = QMessageBox.No
    rp.transcript.setFocus()
    QTest.keyClicks(rp.transcript, "mera naam test hai")   # speaker is "Test Person"
    rp.confirm_transcript()
    assert ("question", "Personal details in the sentence") in dialogs["shown"]
    assert rp.locked_text == ""


def test_urdu_is_right_to_left_with_letter_keys(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Urdu")
    rp = window.record_page
    assert not rp.phonetic_btn.isVisible() and rp.keys_btn.isVisible()
    assert rp.transcript.layoutDirection() == Qt.RightToLeft
    rp.keys_btn.setChecked(True)
    rp.keys_panel.keys.key_pressed.emit("ا")
    assert rp.transcript.toPlainText() == "ا"


def test_hindi_script_mode(window, tmp_path, dialogs):
    start_session(window, config.MODE_SCRIPT, tmp_path, language="Hindi")
    rp = window.record_page
    rp.load_script_file(str(tmp_path.parent.parent / "x.csv"))   # missing file: ignored
    from pathlib import Path
    rp.load_script_file(str(Path(__file__).resolve().parent.parent / "samples"
                            / "demo_script_hindi.csv"))
    assert not any(kind == "dialog" for kind, _ in dialogs["shown"])   # no language warning
    give_take(rp)
    rp.submit()
    rec = list(window.session.store.records.values())[0]
    assert rec["sentence_id"].endswith("_S000001") and rec["script"] == "Deva"


@pytest.mark.parametrize("language,keys,expected,code,script", [
    ("Tamil", "naan thamizh pEchuvEn.", "நான் தமிழ் பேசுவேன்.", "tam", "Taml"),
    ("Malayalam", "ente pEru raamu aaNu.", "എന്റെ പേരു രാമു ആണു.", "mal", "Mlym"),
    ("Punjabi", "panjaab vich pakkaa ghar.", "ਪੰਜਾਬ ਵਿਚ ਪੱਕਾ ਘਰ।", "pan", "Guru"),
    ("Odia", "mo naama raama.", "ମୋ ନାମ ରାମ।", "ory", "Orya"),
])
def test_typing_other_languages(window, tmp_path, dialogs, language, keys, expected, code,
                                script):
    start_session(window, config.MODE_TYPED, tmp_path, language=language)
    rp = window.record_page
    ed = rp.transcript
    assert ed.phonetic_on and rp.phonetic_btn.isVisible() and rp.help_btn.isVisible()
    first_latin, first_shown = phonetic.EXAMPLES[language][0]
    assert first_latin in ed.placeholderText() and first_shown in ed.placeholderText()
    ed.setFocus()
    QTest.keyClicks(ed, keys)
    assert ed.toPlainText() == expected
    rp.confirm_transcript()
    give_take(rp)
    rp.submit()
    rec = list(window.session.store.records.values())[0]
    assert (rec["text"], rec["language_code"], rec["script"]) == (expected, code, script)


@pytest.mark.parametrize("language", ["Hindi", "Bengali", "Assamese", "Odia", "Gujarati",
                                      "Punjabi", "Tamil", "Telugu", "Kannada", "Malayalam"])
def test_typing_help_for_each_language(qapp, language):
    from recorder.ui.typing_widgets import TypingHelpDialog
    dlg = TypingHelpDialog(None, language)
    text = " ".join(lbl.text() for lbl in dlg.findChildren(QLabel))
    assert f"Typing {language}" in dlg.windowTitle()
    assert "Examples" in text and "Ctrl+Space" in text
    dlg.close()
