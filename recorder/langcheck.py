"""Checks that sentences are written in the writing system of the recording language.

Catches the common mistake of reading an English script while the speaker's
recording language is set to, say, Odia - which would put the wrong language code
in the Speaker ID and in every clip's metadata.
"""

import unicodedata
from collections import Counter

# Recording language -> first word of the Unicode character names of its script.
SCRIPT_OF_LANGUAGE = {
    "English": "LATIN", "Hindi": "DEVANAGARI", "Marathi": "DEVANAGARI", "Odia": "ORIYA",
    "Bengali": "BENGALI", "Assamese": "BENGALI", "Gujarati": "GUJARATI", "Punjabi": "GURMUKHI",
    "Tamil": "TAMIL", "Telugu": "TELUGU", "Kannada": "KANNADA", "Malayalam": "MALAYALAM",
    "Urdu": "ARABIC",
}
SCRIPT_LABELS = {
    "LATIN": "Latin letters (as used for English)", "DEVANAGARI": "Devanagari script",
    "ORIYA": "Odia script", "BENGALI": "Bengali-Assamese script", "GUJARATI": "Gujarati script",
    "GURMUKHI": "Gurmukhi script", "TAMIL": "Tamil script", "TELUGU": "Telugu script",
    "KANNADA": "Kannada script", "MALAYALAM": "Malayalam script", "ARABIC": "Perso-Arabic script",
}


def dominant_script(texts) -> str | None:
    counts = Counter()
    for text in texts:
        for ch in text:
            if ch.isalpha():
                name = unicodedata.name(ch, "")
                if name:
                    counts[name.split()[0]] += 1
    return counts.most_common(1)[0][0] if counts else None


def mismatch_message(language: str, texts) -> str | None:
    """A message if the texts use a different writing system than the language, else None."""
    expected = SCRIPT_OF_LANGUAGE.get(language)
    found = dominant_script(texts)
    if not expected or not found or found == expected:
        return None
    label = lambda s: SCRIPT_LABELS.get(s, s.title() + " script")
    return (f"The sentences are written in {label(found)}, but the recording language is set "
            f"to {language}, which is written in {label(expected)}.")
