"""Checks that sentences are written in a script used by the recording language.

Catches the common mistake of reading an English script while the speaker's
recording language is set to, say, Odia - which would put the wrong language code
in the Speaker ID and in every clip's metadata.
"""

import unicodedata
from collections import Counter

from .config import LANGUAGE_INFO, SCRIPTS

# First word of a character's Unicode name ("DEVANAGARI LETTER KA") -> ISO 15924 code.
_UNICODE_TO_SCRIPT = {info["unicode"]: code for code, info in SCRIPTS.items()}


def dominant_script(texts) -> str | None:
    """ISO 15924 code of the script most letters are written in, e.g. 'Deva', or None."""
    counts = Counter()
    for text in texts:
        for ch in text:
            if ch.isalpha() or unicodedata.category(ch).startswith("M"):
                code = _UNICODE_TO_SCRIPT.get(unicodedata.name(ch, "").split(" ")[0])
                if code:
                    counts[code] += 1
    return counts.most_common(1)[0][0] if counts else None


def mismatch_message(language: str, texts) -> str | None:
    """A message if the texts use a script the language is not written in, else None."""
    allowed = LANGUAGE_INFO.get(language, {}).get("scripts")
    found = dominant_script(texts)
    if not allowed or not found or found in allowed:
        return None
    names = [SCRIPTS[s]["name"] for s in allowed]
    expected = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]
    return (f"The sentences are written in {SCRIPTS[found]['name']} script, but the recording "
            f"language is set to {language}, which is written in {expected} script.")
