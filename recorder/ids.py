"""Globally unique, anonymous speaker and sentence IDs.

Contributors record on their own machines with no central server, so IDs must
never depend on a local counter. A speaker ID combines readable metadata with
an 8-character fingerprint of the speaker's private details:

    eng_OD_KHO_M_1999_7f3a9c2e
    lang state district gender birth-year fingerprint

The same person entering the same details on any device gets the same ID, and
the fingerprint cannot be reversed to recover the name or phone number.

Sentence IDs append a mode-specific suffix:
    script mode: _S000123        (sentence number from the script file)
    typed mode:  _F261028153012  (yymmddHHMMSS of submission)
"""

import hashlib
import re
import unicodedata
from datetime import datetime


def normalize_text(text: str) -> str:
    """NFC-normalise and collapse all whitespace (including newlines) to single spaces."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip()


def normalize_name(name: str) -> str:
    """Lowercase letters, digits and spaces only. Vowel signs of Indian scripts (combining
    marks) are kept, so names typed in Devanagari etc. stay intact."""
    name = normalize_text(name).casefold()
    kept = "".join(ch for ch in name if ch.isalnum() or ch in " _"
                   or unicodedata.category(ch).startswith("M"))
    return kept.strip()


def mobile_digits(mobile: str) -> str:
    """Digits only; the last 10 so that '+91 98765 43210' and '9876543210' match."""
    return re.sub(r"\D", "", mobile or "")[-10:]


def _letters(s: str) -> str:
    return re.sub(r"[^A-Za-z]", "", s).upper()


def region_code(name: str, length: int) -> str:
    """Short code from a place name, e.g. Khordha -> KHO, East Godavari -> EGO."""
    words = [w for w in (_letters(w) for w in (name or "").split()) if w]
    if not words:
        return "X" * length
    if len(words) == 1:
        code = words[0][:length]
    else:
        code = words[0][0] + words[-1][: length - 1]
    return code.ljust(length, "X")


def speaker_fingerprint(name: str, birth_year: int, gender_code: str, pincode: str,
                        mobile: str) -> str:
    key = "|".join([normalize_name(name), str(birth_year), gender_code,
                    re.sub(r"\s", "", pincode or ""), mobile_digits(mobile)])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


def make_speaker_id(lang_code: str, state_code: str, district_code: str, gender_code: str,
                    birth_year: int, fingerprint: str) -> str:
    return f"{lang_code}_{state_code}_{district_code}_{gender_code}_{birth_year}_{fingerprint}"


def script_sentence_id(speaker_id: str, number: str) -> str:
    return f"{speaker_id}_S{format_script_number(number)}"


def typed_sentence_id(speaker_id: str, when: datetime | None = None) -> str:
    return f"{speaker_id}_F{(when or datetime.now()).strftime('%y%m%d%H%M%S')}"


def format_script_number(number) -> str:
    """'12', 12, 12.0 -> '000012'; non-numeric labels keep their letters/digits."""
    s = str(number).strip()
    if re.fullmatch(r"\d+(\.0+)?", s):
        return f"{int(float(s)):06d}"
    return re.sub(r"[^A-Za-z0-9]", "", s)
