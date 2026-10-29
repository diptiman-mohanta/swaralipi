"""On-screen letter keys for every recording language, built from Unicode.

Brahmic scripts (Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada,
Malayalam) share one layout of 128 code points, so the groups are found by character
name. Ol Chiki and Meetei Mayek come from their own Unicode ranges; Perso-Arabic letters
come from per-language alphabets in data/languages.json.
"""

import unicodedata

from ..config import ARABIC_LETTERS, LANGUAGE_INFO, SCRIPTS

DOTTED_CIRCLE = "◌"   # shows where a vowel sign attaches, e.g. ◌ि

_VOWEL_LETTERS = {"A", "AA", "I", "II", "U", "UU", "VOCALIC R", "VOCALIC RR", "VOCALIC L",
                  "VOCALIC LL", "E", "EE", "AI", "O", "OO", "AU", "SHORT E", "SHORT O",
                  "CANDRA E", "CANDRA O", "SHORT A", "AW", "OE", "OOE", "UE", "UUE"}
# Rare, historical or symbolic characters that would only clutter the keys
# (matched as whole words in the character name).
_SKIP_WORDS = ("VEDIC", "ABBREVIATION", "GLOTTAL", "HEADSTROKE", "UDATTA", "ANUDATTA",
               "GRAVE", "ACUTE", "ISSHAR", "CURRENCY", "FRACTION", "NUMERATOR", "ISOLATED",
               "INVERTED", "HIGH", "ARCHAIC", "YAMAKKAN", "PRISHTHAMATRA", "SIDDHAM",
               "LENGTH", "LIGATURE", "SPACING", "WHITE", "RUPEE", "RUPII", "ANNA", "DOUBLE",
               "PAMUDPOD", "THREE-DOT", "QUARTER", "DATE", "CIRCLE", "AREA", "SIGN TO",
               "NUMBER", "EK ONKAR", "ABOVE", "BELOW")
# Devanagari letters used only by other languages or old texts (Kashmiri, Sindhi vowels,
# Dravidian transliteration); hidden so the Hindi keys stay readable.
_DEVANAGARI_RARE = {0x0904, 0x090E, 0x0912, 0x0929, 0x0934, 0x093A, 0x093B, 0x0946, 0x094A,
                    0x094E, 0x094F, 0x0955, 0x0956, 0x0957, *range(0x0973, 0x0980)}


def _usable(ch: str) -> str | None:
    name = unicodedata.name(ch, "")
    padded = f" {name} "
    if not name or ord(ch) in _DEVANAGARI_RARE \
            or any(f" {w} " in padded for w in _SKIP_WORDS):
        return None
    return name


def _brahmic_groups(block: int) -> list[tuple[str, list[tuple[str, str]]]]:
    vowels, signs_v, consonants, marks, digits = [], [], [], [], []
    for cp in range(block, block + 128):
        ch = chr(cp)
        name = _usable(ch)
        if not name:
            continue
        rest = name.split(" ", 1)[1]
        if rest.startswith("LETTER "):
            letter = rest[len("LETTER "):]
            (vowels if letter in _VOWEL_LETTERS else consonants).append(ch)
        elif rest.startswith("VOWEL SIGN"):
            signs_v.append(ch)
        elif rest.startswith("DIGIT"):
            digits.append(ch)
        elif rest.startswith("SIGN") or rest == "AU LENGTH MARK":
            marks.append(ch)
    marks += ["।", "॥"]
    show = lambda c: (c, DOTTED_CIRCLE + c if unicodedata.category(c).startswith("M") else c)
    return [("Vowels", [show(c) for c in vowels]),
            ("Vowel signs", [show(c) for c in signs_v]),
            ("Consonants", [show(c) for c in consonants]),
            ("Signs", [show(c) for c in marks]),
            ("Digits", [show(c) for c in digits])]


def _range_groups(first: int, last: int) -> list[tuple[str, list[tuple[str, str]]]]:
    letters, signs, digits, punct = [], [], [], []
    for cp in range(first, last + 1):
        ch = chr(cp)
        name = _usable(ch) if unicodedata.name(ch, "") else None
        if not name:
            continue
        shown = DOTTED_CIRCLE + ch if unicodedata.category(ch).startswith("M") else ch
        if "DIGIT" in name:
            digits.append((ch, shown))
        elif "LETTER" in name:
            letters.append((ch, shown))
        elif "PUNCTUATION" in name or unicodedata.category(ch).startswith("P") \
                or "CHEIKHEI" in name:
            punct.append((ch, shown))
        else:
            signs.append((ch, shown))
    return [("Letters", letters), ("Signs", signs), ("Digits", digits), ("Punctuation", punct)]


def _arabic_groups(language: str) -> list[tuple[str, list[tuple[str, str]]]]:
    letters = ARABIC_LETTERS.get(language, ARABIC_LETTERS["Urdu"]).split()
    marks = ARABIC_LETTERS["marks"].split()
    punct = ARABIC_LETTERS["punctuation"].split()
    digits = [chr(cp) for cp in range(0x06F0, 0x06FA)]
    return [("Letters", [(c, c) for c in letters]),
            ("Marks", [(c, DOTTED_CIRCLE + c) for c in marks]),
            ("Punctuation", [(c, c) for c in punct]),
            ("Digits", [(c, c) for c in digits])]


def key_groups(language: str, script: str | None = None) -> list[tuple[str, list[tuple[str, str]]]]:
    """[(group title, [(character to insert, label to show)])] for a language's keys."""
    info = LANGUAGE_INFO.get(language)
    if not info:
        return []
    script = script or info["scripts"][0]
    data = SCRIPTS[script]
    if script == "Arab":
        groups = _arabic_groups(language)
    elif "block" in data:
        groups = _brahmic_groups(data["block"])
    elif "range" in data:
        groups = _range_groups(*data["range"])
    else:
        return []
    return [(title, keys) for title, keys in groups if keys]
