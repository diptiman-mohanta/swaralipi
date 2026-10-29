"""English-letter typing for the languages beyond Hindi: Bengali, Assamese, Odia, Gujarati,
Punjabi, Tamil, Telugu, Kannada and Malayalam."""

import unicodedata
from pathlib import Path

import pytest

from recorder import config, langcheck
from recorder.typing import phonetic

DATA = Path(__file__).resolve().parent / "data" / "typing"
NFC = lambda s: unicodedata.normalize("NFC", s)
NEW = ["Bengali", "Assamese", "Odia", "Gujarati", "Punjabi", "Tamil", "Telugu", "Kannada",
       "Malayalam"]
TYPED = [n for n in config.LANGUAGES if phonetic.available(n)]


def test_which_languages_can_be_typed():
    devanagari = ["Hindi", "Marathi", "Nepali", "Sanskrit", "Konkani", "Maithili", "Dogri",
                  "Bodo"]
    assert sorted(TYPED) == sorted(devanagari + NEW)
    for name in ("English", "Urdu", "Kashmiri", "Sindhi", "Santali", "Manipuri"):
        assert not phonetic.available(name)


@pytest.mark.parametrize("language", TYPED)
def test_every_token_types_the_languages_own_script(language):
    """No letter from another script slips in (e.g. a Devanagari letter in Tamil)."""
    s = phonetic.scheme(language)
    script = config.LANGUAGE_INFO[language]["scripts"][0]
    for tok in list(s.consonants) + list(s.vowels):
        out = s.transliterate(tok + "a" if tok in s.consonants else tok)
        assert langcheck.dominant_script([out]) == script, (tok, out)


@pytest.mark.parametrize("language", TYPED)
def test_help_examples_are_accurate(language):
    s = phonetic.scheme(language)
    sheet = dict(s.cheat_sheet())
    assert {"Vowels", "Consonants", "Marks", "Control"} <= set(sheet)
    for latin, shown in phonetic.EXAMPLES.get(language, []):
        assert s.transliterate(latin) == NFC(shown), (latin, s.transliterate(latin))
    small, a, big, b = s.case_example()
    assert a != b and s.transliterate(small) and s.transliterate(big)


@pytest.mark.parametrize("language", NEW)
def test_examples_exist_for_every_new_language(language):
    assert len(phonetic.EXAMPLES[language]) >= 8


# ---------------------------------------------------------------- real text can be typed
def _words(language):
    """Distinct words of the sample text, without punctuation."""
    text = (DATA / f"{language.lower()}.txt").read_text(encoding="utf-8")
    words = set()
    for chunk in text.split():
        word = "".join(c for c in chunk if c.isalpha() or unicodedata.category(c)[0] == "M")
        if word:
            words.add(word)
    return sorted(words)


# Words the scheme deliberately cannot reproduce, with the reason.
UNTYPABLE = {
    "ਜਿ਼ੰਦਗੀ": "source text puts the nukta after the vowel sign (should be ਜ਼ਿੰਦਗੀ)",
}


@pytest.mark.parametrize("language", NEW)
def test_real_text_round_trips(language):
    """Each word -> the English letters for it -> back to exactly the same word."""
    s = phonetic.scheme(language)
    words = [w for w in _words(language) if NFC(w) not in map(NFC, UNTYPABLE)]
    assert len(words) >= 30
    failures = []
    for word in words:
        latin = s.to_latin(word)
        if not latin.isascii() or s.transliterate_text(latin) != word:
            failures.append((word, latin, s.transliterate_text(latin)))
    assert not failures, failures


@pytest.mark.parametrize("language", NEW)
def test_sentence_punctuation(language):
    s = phonetic.scheme(language)
    out = s.transliterate_text(s.to_latin("x") + ". " + "a, a?")
    assert s.full_stop in out and out.endswith("?")


# ---------------------------------------------------------------- language rules
@pytest.mark.parametrize("language,latin,expected", [
    # Bengali / Assamese: y, khanda ta, ng
    ("Bengali", "samay", "সময়"), ("Bengali", "yadi", "যদি"), ("Bengali", "byakti", "ব্যক্তি"),
    ("Bengali", "ut^sab", "উৎসব"), ("Bengali", "rang", "রং"), ("Bengali", "baanglaa", "বাংলা"),
    ("Bengali", "antar", "অন্তর"), ("Bengali", "panch", "পঞ্চ"), ("Bengali", "baRo", "বড়ো"),
    ("Assamese", "ghar", "ঘৰ"), ("Assamese", "guvaahaaTii", "গুৱাহাটী"),
    # Odia: short final a, y-phala ୟ, ୱ
    ("Odia", "kamaLa", "କମଳ"), ("Odia", "kamaL", "କମଳ"), ("Odia", "kamal", "କମଲ"), ("Odia", "satya", "ସତ୍ୟ"),
    ("Odia", "yaa", "ଯା"), ("Odia", "web", "ୱେବ"), ("Odia", "chandra", "ଚନ୍ଦ୍ର"),
    # Gujarati: anusvara, ળ
    ("Gujarati", "gangaa", "ગંગા"), ("Gujarati", "kaaLu", "કાળુ"), ("Gujarati", "zaDap", "ઝડપ"),
    # Punjabi: tippi/bindi, addak, subscript ਰ ਹ only
    ("Punjabi", "singh", "ਸਿੰਘ"), ("Punjabi", "maaM", "ਮਾਂ"), ("Punjabi", "dost", "ਦੋਸਤ"),
    ("Punjabi", "prem", "ਪ੍ਰੇਮ"), ("Punjabi", "unhaaM", "ਉਨ੍ਹਾਂ"), ("Punjabi", "akkh", "ਅੱਖ"),
    ("Punjabi", "zindagii", "ਜ਼ਿੰਦਗੀ"), ("Punjabi", "shahir", "ਸ਼ਹਿਰ"), ("Punjabi", "main", "ਮੈਂ"),
    # Tamil: no aspirates, three n's, final pulli
    ("Tamil", "naan", "நான்"), ("Tamil", "vandhaan", "வந்தான்"), ("Tamil", "enga", "எங்க"),
    ("Tamil", "maNdapam", "மண்டபம்"), ("Tamil", "pancham", "பஞ்சம்"), ("Tamil", "kaafi", "காஃபி"),
    ("Tamil", "Sri", "ஸ்ரி"), ("Tamil", "shrii", "ஸ்ரீ"), ("Tamil", "aRivu", "அறிவு"),
    # Telugu / Kannada: short and long e o, anusvara, final m in Telugu
    ("Telugu", "nEnu", "నేను"), ("Telugu", "nenu", "నెను"), ("Telugu", "kOpam", "కోపం"),
    ("Telugu", "bas", "బస్"), ("Kannada", "ondu", "ಒಂದು"), ("Kannada", "bEku", "ಬೇಕು"),
    ("Kannada", "bas", "ಬಸ್"),
    # Malayalam: chillu letters, final m, nt
    ("Malayalam", "avan", "അവൻ"), ("Malayalam", "paal", "പാൽ"), ("Malayalam", "kaN", "കൺ"),
    ("Malayalam", "ninte", "നിന്റെ"), ("Malayalam", "karmam", "കർമം"),
    ("Malayalam", "kaaryam", "കാര്യം"), ("Malayalam", "katha", "കത"),
    ("Malayalam", "kathha", "കഥ"), ("Malayalam", "Sari", "ശരി"),
    ("Malayalam", "vannu", "വന്നു"), ("Malayalam", "vann", "വന്ന്"), ("Malayalam", "amm", "അമ്മ്"),
    # Malayalam chillus before consonants, as Wikipedia writes them; ൻഡ; au; k_h
    ("Malayalam", "avaLkk", "അവൾക്ക്"), ("Malayalam", "laisans", "ലൈസൻസ്"),
    ("Malayalam", "alONsO", "അലോൺസോ"), ("Malayalam", "ulppannam", "ഉൽപ്പന്നം"),
    ("Malayalam", "aanDi", "ആൻഡി"), ("Malayalam", "kaaNDam", "കാണ്ഡം"),
    ("Malayalam", "kaNtu", "കണ്ടു"), ("Malayalam", "akkauNt", "അക്കൗണ്ട്"),
    ("Malayalam", "aar_es", "ആർഎസ്"),
    # Tamil ந்த after a consonant, ஃப at the start
    ("Tamil", "amarnthu", "அமர்ந்து"), ("Tamil", "faarm", "ஃபார்ம்"),
    # an initial ୟ / য় when wanted; Punjabi bindi after ਉ
    ("Odia", "Yaadab", "ୟାଦବ"), ("Bengali", "Yaanaam", "য়ানাম"), ("Punjabi", "kiuM", "ਕਿਉਂ"),
    # Bodo's own vowels
    ("Bodo", "gwra", "गोरा"), ("Bodo", "mohon", "महन"), ("Bodo", "mechao", "मेचाव"),
    ("Bodo", "khani", "खानि"),
])
def test_language_rules(language, latin, expected):
    assert phonetic.transliterate(latin, language) == NFC(expected)


def test_explicit_halant_is_kept():
    assert phonetic.transliterate("avan^", "Malayalam") == NFC("അവന്")
    assert phonetic.transliterate("namaskaaram^", "Telugu") == NFC("నమస్కారమ్")
    assert phonetic.transliterate("t^", "Punjabi") == NFC("ਤ੍")


def test_typed_names_are_caught_in_every_script():
    """The private-details check turns the speaker's name into the script."""
    from recorder import ids
    for language in NEW:
        typed = phonetic.scheme(language).transliterate("raamu")
        assert ids.normalize_name(typed), language


def test_typing_guide_matches_the_engine(tmp_path, monkeypatch, capsys):
    """docs/typing-indian-languages.md is generated; rerun tools/make_typing_docs.py."""
    import importlib.util
    root = DATA.parent.parent.parent
    spec = importlib.util.spec_from_file_location("make_typing_docs",
                                                  root / "tools" / "make_typing_docs.py")
    docs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(docs)
    monkeypatch.setattr(docs, "OUT", tmp_path / "guide.md")
    docs.main()
    expected = (root / "docs" / "typing-indian-languages.md").read_text(encoding="utf-8")
    assert (tmp_path / "guide.md").read_text(encoding="utf-8") == expected
