"""Catching a speaker's own name, mobile number or email in a sentence they type.

The check works on salted one-way hashes, so it can be remembered for a returning speaker
(in speaker_checks.json next to user_settings.json, never exported) without keeping their
name or number in readable form on this computer.
"""

import hashlib
import json
import os
import secrets
import unicodedata

from . import config, ids
from .typing import phonetic, suggest

CHECKS_FILE = config.APP_DIR / "speaker_checks.json"


def _digits(text: str) -> str:
    """Digits in any script (९८७६ or 9876) as plain numbers."""
    return "".join(str(unicodedata.digit(ch, "")) for ch in text if ch.isdigit())


class PrivateCheck:
    def __init__(self, salt: str = "", words=(), numbers=(), emails=()):
        self.salt = salt or secrets.token_hex(16)
        self.words, self.numbers, self.emails = set(words), set(numbers), set(emails)

    def _h(self, text: str) -> str:
        return hashlib.sha256((self.salt + text).encode("utf-8")).hexdigest()

    @classmethod
    def from_details(cls, name: str, mobile: str, email: str, language: str) -> "PrivateCheck":
        check = cls()
        words = [w for w in ids.normalize_name(name).split() if len(w) >= 3]
        if phonetic.available(language):   # also the name typed in the language's script,
            for w in [w for w in words if w.isascii()]:   # exactly or as a suggested word
                words += [ids.normalize_name(t) for t in suggest.suggestions(language, w)]
        check.words = {check._h(w) for w in words if w}
        mobile = ids.mobile_digits(mobile)
        if mobile:
            check.numbers = {f"{len(mobile)}:{check._h(mobile)}"}
        if email.strip():
            check.emails = {check._h(email.strip().casefold())}
        return check

    def found_in(self, text: str) -> bool:
        if any(self._h(w) in self.words for w in ids.normalize_name(text).split()):
            return True
        digits = _digits(text)
        for entry in self.numbers:
            size, digest = entry.split(":")
            n = int(size)
            if any(self._h(digits[i:i + n]) == digest for i in range(len(digits) - n + 1)):
                return True
        return any(self._h(token.strip(".,;:!?()<>\"'").casefold()) in self.emails
                   for token in text.split() if "@" in token)

    def to_dict(self) -> dict:
        return {"salt": self.salt, "words": sorted(self.words), "numbers": sorted(self.numbers),
                "emails": sorted(self.emails)}

    @classmethod
    def from_dict(cls, d: dict) -> "PrivateCheck":
        return cls(d.get("salt", ""), d.get("words", ()), d.get("numbers", ()),
                   d.get("emails", ()))


def _load() -> dict:
    try:
        return json.loads(CHECKS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def remember(speaker_id: str, check: PrivateCheck) -> None:
    """Keeps the hashed check so the speaker can continue later without re-entering details."""
    data = _load()
    data[speaker_id] = check.to_dict()
    try:
        tmp = CHECKS_FILE.with_name(CHECKS_FILE.name + ".part")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, CHECKS_FILE)
    except OSError:
        pass   # the check still works for this session


def recall(speaker_id: str) -> PrivateCheck | None:
    d = _load().get(speaker_id)
    return PrivateCheck.from_dict(d) if d else None
