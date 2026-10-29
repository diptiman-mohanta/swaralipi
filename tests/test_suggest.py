"""Word suggestions: casual spellings find real words, exact typing keeps working."""

import gzip
import itertools

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from recorder import audio, config
from recorder.typing import phonetic, suggest
from tests.test_app_flow import start_session

LISTED = [name for name, code in config.LANGUAGES.items()
          if (suggest.WORDLIST_DIR / f"{code}.tsv.gz").is_file()]


def test_word_lists_exist_for_typed_languages():
    expected = {"Hindi", "Bengali", "Assamese", "Odia", "Gujarati", "Punjabi", "Tamil",
                "Telugu", "Kannada", "Malayalam", "Marathi", "Nepali", "Sanskrit", "Konkani",
                "Maithili"}
    assert set(LISTED) == expected
    assert not suggest.available("Bodo") and not suggest.available("English")


@pytest.mark.parametrize("language", LISTED)
def test_word_list_matches_the_typing_engine(language):
    """Each listed word can be typed exactly, and its stored key is the one the engine makes
    now (rerun tools/build_wordlists.py after changing the scheme)."""
    scheme = phonetic.scheme(language)
    path = suggest.WORDLIST_DIR / f"{config.LANGUAGES[language]}.tsv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as f:
        rows = [line.rstrip("\n").split("\t") for line in itertools.islice(f, 0, 50000, 97)]
    assert len(rows) > 200     # Konkani and Maithili have smaller Wikipedias
    for word, keys, count, latin in rows:
        assert scheme.to_latin(word) == latin, (word, latin)
        assert scheme.transliterate_text(latin) == word, (word, latin)
        assert keys.split("|") == suggest.word_keys(latin, language), (word, latin, keys)
        assert int(count) >= 3


@pytest.mark.parametrize("typed,word", [
    ("pani", "पानी"), ("kitab", "किताब"), ("ladka", "लड़का"), ("bharat", "भारत"),
    ("sarkar", "सरकार"), ("mahila", "महिला"), ("aaj", "आज"), ("karna", "करना"),
    ("toh", "तो"), ("mujhe", "मुझे"), ("chahiye", "चाहिए"), ("vartmaan", "वर्तमान"),
])
def test_casual_hindi_finds_the_word(typed, word):
    assert suggest.suggestions("Hindi", typed)[0] == word


@pytest.mark.parametrize("language,typed,word", [
    ("Bengali", "bangla", "বাংলা"), ("Tamil", "tamil", "தமிழ்"), ("Odia", "odisha", "ଓଡ଼ିଶା"),
    ("Telugu", "telugu", "తెలుగు"), ("Malayalam", "keralam", "കേരളം"),
    ("Gujarati", "gujarat", "ગુજરાત"), ("Punjabi", "panjab", "ਪੰਜਾਬ"),
    ("Bengali", "shikkha", "শিক্ষা"), ("Bengali", "onchol", "অঞ্চল"),
    ("Tamil", "pondra", "போன்ற"), ("Tamil", "madurai", "மதுரை"),
    ("Malayalam", "santhosham", "സന്തോഷം"), ("Gujarati", "bhagma", "ભાગમાં"),
    ("Kannada", "karnataka", "ಕರ್ನಾಟಕ"),
])
def test_casual_spelling_in_other_languages(language, typed, word):
    if language not in LISTED:
        pytest.skip("word list not built")
    assert word in suggest.suggestions(language, typed)


def test_hindi_or_hindi():
    assert suggest.suggestions("Hindi", "hindi")[0] in ("हिंदी", "हिन्दी")


def test_exact_typing_stays_first():
    for typed in ("laapattaa", "pAnI", "kitaab", "laRkaa", "hin^dii", "Dhankakar", "kal"):
        assert suggest.suggestions("Hindi", typed)[0] == phonetic.transliterate(typed)


def test_exact_result_is_always_offered():
    for typed in ("pani", "xyzzy", "kal", "zindagi"):
        options = suggest.suggestions("Hindi", typed)
        assert phonetic.transliterate(typed) in options
        assert len(options) == len(set(options)) <= suggest.LIMIT


def test_loose_key_ignores_casual_differences():
    k = suggest.loose_key
    assert k("pani") == k("paanii") == k("paanee")
    assert k("kiratpur") == k("kiratapur")
    assert k("accha") == k("achha") == k("achcha")
    assert k("main", ) != k("man")


# ---------------------------------------------------------------- in the recording screen
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


def test_typing_with_suggestions(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    ed, bar = rp.transcript, rp.suggestion_bar
    assert rp.suggest_btn.isVisible() and rp.suggest_btn.isChecked() and bar.isVisible()
    ed.setFocus()
    QTest.keyClicks(ed, "mujhe pani")
    assert bar.latin.text() == "pani" and bar.buttons[0].text() == "1  पानी"
    assert bar.buttons[0].isChecked() and bar.buttons[1].isVisible()
    QTest.keyClicks(ed, " chahiye.")
    assert ed.toPlainText() == "मुझे पानी चाहिए।"

    ed.clear()
    QTest.keyClicks(ed, "pani")
    QTest.keyClick(ed, Qt.Key_Escape)                 # exactly what was typed
    assert ed.toPlainText() == "पनि" and not bar.latin.text()

    ed.clear()
    QTest.keyClicks(ed, "pani")
    QTest.keyClick(ed, Qt.Key_Tab)                    # next suggestion, still composing
    second = suggest.suggestions("Hindi", "pani")[1]
    assert ed.toPlainText() == second and bar.buttons[1].isChecked()
    QTest.keyClicks(ed, " ")
    assert ed.toPlainText() == second + " "

    ed.clear()
    QTest.keyClicks(ed, "pani")
    QTest.keyClick(ed, Qt.Key_2)                      # number key picks and ends the word
    assert ed.toPlainText() == second

    ed.clear()
    QTest.keyClicks(ed, "pani")
    bar.buttons[0].click()
    assert ed.toPlainText() == "पानी" and not bar.latin.text()


def test_suggestions_can_be_turned_off(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Hindi")
    rp = window.record_page
    rp.suggest_btn.setChecked(False)
    QTest.keyClicks(rp.transcript, "pani")
    assert rp.transcript.toPlainText() == "पनि"
    assert config.load_user_settings()["typing"]["suggest"] is False
    rp.suggest_btn.setChecked(True)
    assert config.load_user_settings()["typing"]["suggest"] is True


def test_no_suggestions_without_a_word_list(window, tmp_path, dialogs):
    start_session(window, config.MODE_TYPED, tmp_path, language="Bodo")
    rp = window.record_page
    assert not rp.suggest_btn.isVisible() and rp.suggestion_bar.isVisible()
    QTest.keyClicks(rp.transcript, "bodo")
    assert rp.suggestion_bar.buttons[0].text() == phonetic.transliterate("bodo", "Bodo")
    assert not rp.suggestion_bar.buttons[1].isVisible()
