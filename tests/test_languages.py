"""The 22 scheduled languages: scripts, fonts, language check, keys and Hindi typing."""

import unicodedata
from pathlib import Path

import pytest

from recorder import config, langcheck
from recorder.script_loader import load_script
from recorder.typing import phonetic
from recorder.typing.keys import key_groups

ROOT = Path(__file__).resolve().parent.parent
SCHEDULED = [n for n, info in config.LANGUAGE_INFO.items() if info["scheduled"]]
NFC = lambda s: unicodedata.normalize("NFC", s)


def test_all_22_scheduled_languages():
    assert len(SCHEDULED) == 22
    assert {"Hindi", "Odia", "Santali", "Manipuri", "Urdu", "Sanskrit"} <= set(SCHEDULED)
    assert len(set(config.LANGUAGES.values())) == len(config.LANGUAGES)   # unique codes
    assert list(config.LANGUAGES)[0] == "English"


@pytest.mark.parametrize("language", SCHEDULED)
def test_native_name_is_in_the_languages_own_script(language):
    """The language check accepts each language's own name, and rejects English for it."""
    info = config.LANGUAGE_INFO[language]
    assert langcheck.dominant_script([info["native"]]) == info["scripts"][0]
    assert langcheck.mismatch_message(language, [info["native"]]) is None
    if "Latn" not in info["scripts"]:
        assert langcheck.mismatch_message(language, ["The quick brown fox."])


@pytest.mark.parametrize("language", SCHEDULED)
def test_every_language_has_letter_keys(language):
    groups = dict(key_groups(language))
    letters = sum(len(v) for k, v in groups.items() if k in ("Vowels", "Consonants", "Letters"))
    assert letters >= 25, groups.keys()
    assert len(groups.get("Digits", [])) == 10


@pytest.mark.parametrize("language", SCHEDULED)
def test_bundled_font_covers_the_language(qapp, language):
    from PySide6.QtGui import QRawFont
    family = config.language_font(language)
    files = {f.stem.split("-")[0]: f for f in (ROOT / "recorder/ui/fonts/noto").glob("*.ttf")}
    font_file = files[family.replace(" ", "")]
    raw = QRawFont(str(font_file), 16)
    text = config.LANGUAGE_INFO[language]["native"]
    missing = [c for c in text if not raw.supportsCharacter(ord(c))]
    assert not missing, (language, family, missing)


def test_rtl_languages():
    assert config.is_rtl("Urdu") and config.is_rtl("Kashmiri") and config.is_rtl("Sindhi")
    assert not config.is_rtl("Hindi") and not config.is_rtl("English")


# ---------------------------------------------------------------- Hindi phonetic typing
HINDI = [
    ("namaste", "नमस्ते"), ("bhaarat", "भारत"), ("hindii", "हिंदी"), ("kitaab", "किताब"),
    ("dhanyavaad", "धन्यवाद"), ("gangaa", "गंगा"), ("sanskRRit", "संस्कृत"), ("kshamaa", "क्षमा"),
    ("xamaa", "क्षमा"), ("GYaan", "ज्ञान"), ("ichchhaa", "इच्छा"), ("acchaa", "अच्छा"),
    ("kRRipayaa", "कृपया"), ("laRkaa", "लड़का"), ("paRhnaa", "पढ़ना"), ("zindagii", "ज़िंदगी"),
    ("skool", "स्कूल"), ("DOkTar", "डॉक्टर"), ("OM", "ॐ"), ("haaMM", "हाँ"), ("duHkh", "दुःख"),
    ("vidvaan^", "विद्वान्"), ("na_i", "नइ"), ("janm", "जन्म"), ("anya", "अन्य"),
    ("sammaan", "सम्मान"), ("sambandh", "संबंध"), ("panDit", "पंडित"), ("kaNTh", "कंठ"),
    ("aaiye", "आइये"), ("gaurav", "गौरव"), ("Bhaarat", "भारत"), ("Mera", "मेरा"),
    ("mera", "मेरा"), ("kya", "क्या"), ("kamal", "कमल"), ("Is", "इस"), ("Aaj", "आज"),
    ("fal", "फ़ल"), ("shrii", "श्री"), ("svaagat", "स्वागत"), ("uttar", "उत्तर"),
    ("TamaaTar", "टमाटर"), ("naee", "नई"), ("ghaRii", "घड़ी"), ("main", "मैं"), ("hain", "हैं"),
    ("nahin", "नहीं"), ("kyon", "क्यों"), ("hoon", "हूँ"), ("na", "न"),
    ("satya", "सत्य"), ("kaarya", "कार्य"), ("dhanya", "धन्य"), ("kiya", "किया"),
]


@pytest.mark.parametrize("latin,devanagari", HINDI)
def test_hindi_words(latin, devanagari):
    assert phonetic.transliterate(latin) == NFC(devanagari)


def test_m_merges_only_before_p_ph_b_bh():
    assert phonetic.transliterate("champaa") == "चंपा"
    assert phonetic.transliterate("tumko") == "तुम्को"     # not तुंको
    assert phonetic.transliterate("tumako") == "तुमको"


def test_sanskrit_uses_matching_nasal_letters():
    assert phonetic.transliterate("gangaa", "Sanskrit") == "गङ्गा"
    assert phonetic.transliterate("panchaa", "Sanskrit") == "पञ्चा"
    assert phonetic.transliterate("kaNTh", "Sanskrit") == "कण्ठ"
    assert phonetic.transliterate("saMsaar", "Sanskrit") == "संसार"


def test_hindi_sentence_with_punctuation():
    text = phonetic.transliterate_text("aap kaise hain? main Thiik hoon.")
    assert text == "आप कैसे हैं? मैं ठीक हूँ।"
    assert phonetic.transliterate_text("mera naam raam hai||") == "मेरा नाम राम है॥"


def test_output_is_nfc():
    for latin, _ in HINDI:
        out = phonetic.transliterate(latin)
        assert out == NFC(out)


def test_cheat_sheet_examples_are_accurate():
    examples = dict(phonetic.cheat_sheet())["Examples"]
    for latin, shown in examples:
        assert phonetic.transliterate(latin) == NFC(shown)


# ---------------------------------------------------------------- scripts in Indian languages
def test_hindi_demo_script():
    rows = load_script(ROOT / "samples" / "demo_script_hindi.csv")
    assert len(rows) == 30 and rows == load_script(ROOT / "samples" / "demo_script_hindi.xlsx")
    texts = [t for _, t in rows]
    assert langcheck.dominant_script(texts) == "Deva"
    assert langcheck.mismatch_message("Hindi", texts) is None
    assert all(t == NFC(t) for t in texts)


def test_utf16_script_from_excel(tmp_path):
    """Excel's 'Unicode Text' export is UTF-16 with tabs."""
    f = tmp_path / "hindi.txt"
    f.write_text("sentence_no\tsentence\n1\tनमस्ते दुनिया।\n2\tआप कैसे हैं?\n", encoding="utf-16")
    assert load_script(f) == [("1", "नमस्ते दुनिया।"), ("2", "आप कैसे हैं?")]


def test_every_demo_word_can_be_typed():
    """Each sentence of the Hindi demo script -> English letters -> back to the same Hindi."""
    for number, sentence in load_script(ROOT / "samples" / "demo_script_hindi.csv"):
        latin = phonetic.to_latin(sentence)
        assert latin.isascii(), (number, latin)
        assert phonetic.transliterate_text(latin) == sentence, (number, latin)


@pytest.mark.parametrize("word", ["हिन्दी", "हिंदी", "अन्य", "लड़का", "ख़ुश", "नई", "गए", "जाइए",
                                  "ॐ", "दुःख", "विद्वान्", "क्षमा", "ज्ञान", "श्री", "कृपया"])
def test_round_trip_tricky_words(word):
    assert phonetic.transliterate_text(phonetic.to_latin(word)) == NFC(word)
