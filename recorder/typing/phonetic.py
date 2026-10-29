"""Phonetic typing: English letters -> an Indian script, as you type ("namaste" -> "नमस्ते").

One engine serves every Brahmic script. The letter tables are written once in Devanagari,
following the ITRANS convention (as in the indic_transliteration project's maps), and are
carried to the other scripts through Unicode's shared layout: every script block puts the
same letter at the same offset (क U+0915, ক U+0995, க U+0B95, ...). Each language then
adjusts what its speakers expect (LANGUAGE_RULES below).

    vowels      a aa/A i ii/ee/I u uu/oo/U RRi e ai o au   E (ॅ)  O (ॉ, as in doctor)
    consonants  k kh g gh ~N   ch/c chh/Ch j jh ~n   T Th D Dh N   t th d dh n
                p ph b bh m   y r l v/w   sh Sh/shh/S s h   L (ळ)
    clusters    x/ksh (क्ष)   GY (ज्ञ)   cch (च्छ)
    nukta       q (क़)  K (ख़)  G (ग़)  z (ज़)  f (फ़)  R (ड़)  Rh (ढ़)
    signs       M (ं anusvara)  MM (ँ chandrabindu)  H (ः visarga)  OM (ॐ)
    control     ^ forces a halant (विद्वान्: vidvaan^)   _ separates letters (k_h -> कह)

A consonant followed by another consonant gets a halant (st -> स्त). What happens at the
end of a word depends on the language ("schwa"):

    final_long  a final consonant keeps its inherent a (kamal -> कमल) and a final single
                "a" is long (mera -> मेरा): Hindi and most northern languages
    keep        a final "a" stays short (Odia: kamala -> କମଳ)
    explicit    a consonant with no vowel gets a halant (Tamil: naan -> நான்)

n/m before a consonant ("nasal"): anusvara writes हिंदी, homorganic writes the nasal
letter of that consonant (गङ्गा, অন্ত).
"""

import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

from ..config import LANGUAGE_INFO, SCRIPTS

VIRAMA = "्"
NUKTA = "़"
ANUSVARA = "ं"
# Halants the engine adds itself, kept apart from a typed ^ until the script decides how to
# write them (Gurmukhi drops most, Malayalam turns some into chillu letters).
JOIN, FINAL = "", ""
DEVANAGARI = 0x0900

# token -> (independent vowel, vowel sign); "" sign = inherent a
VOWELS = {
    "a": ("अ", ""), "aa": ("आ", "ा"), "A": ("आ", "ा"),
    "i": ("इ", "ि"), "ii": ("ई", "ी"), "ee": ("ई", "ी"), "I": ("ई", "ी"),
    "u": ("उ", "ु"), "uu": ("ऊ", "ू"), "oo": ("ऊ", "ू"), "U": ("ऊ", "ू"),
    "RRi": ("ऋ", "ृ"), "RRI": ("ॠ", "ॄ"),
    "e": ("ए", "े"), "ai": ("ऐ", "ै"), "o": ("ओ", "ो"), "au": ("औ", "ौ"),
    "E": ("ऍ", "ॅ"), "O": ("ऑ", "ॉ"),
}

CONSONANTS = {
    "k": "क", "kh": "ख", "g": "ग", "gh": "घ", "~N": "ङ",
    "ch": "च", "c": "च", "chh": "छ", "Ch": "छ", "j": "ज", "jh": "झ", "~n": "ञ",
    "T": "ट", "Th": "ठ", "D": "ड", "Dh": "ढ", "N": "ण",
    "t": "त", "th": "थ", "d": "द", "dh": "ध", "n": "न",
    "p": "प", "ph": "फ", "b": "ब", "bh": "भ", "m": "म",
    "y": "य", "r": "र", "l": "ल", "v": "व", "w": "व",
    "sh": "श", "Sh": "ष", "shh": "ष", "S": "ष", "s": "स", "h": "ह", "L": "ळ",
    # clusters
    "x": "क" + JOIN + "ष", "ksh": "क" + JOIN + "ष", "GY": "ज" + JOIN + "ञ",
    "cch": "च" + JOIN + "छ",
    # nukta letters (written as base + nukta, the NFC form)
    "q": "क" + NUKTA, "K": "ख" + NUKTA, "G": "ग" + NUKTA, "z": "ज" + NUKTA,
    "f": "फ" + NUKTA, "R": "ड" + NUKTA, "Rh": "ढ" + NUKTA,
}

SIGNS = {"M": ANUSVARA, "MM": "ँ", "H": "ः"}
STANDALONE = {"OM": "ॐ"}
HALANT, SEPARATOR = "^", "_"

# Varga (place of articulation) rows: stops, then their nasal.
_VARGAS = (("कखगघ", "ङ"), ("चछजझ", "ञ"), ("टठडढ", "ण"), ("तथदध", "न"), ("पफबभ", "म"))
# n/m before these keep their full form even in anusvara languages (अन्य, जन्म, सम्मान).
_KEEP_FULL_NASAL = "यरलवहनमणळऴऱऩ"

# Common Hindi words whose everyday spelling the rules cannot guess (nasalised endings).
HINDI_WORDS = {
    "main": "मैं", "mein": "में", "men": "में", "hain": "हैं", "nahin": "नहीं", "nahi": "नहीं",
    "nahiin": "नहीं", "kahin": "कहीं", "kahiin": "कहीं", "yahin": "यहीं", "vahin": "वहीं",
    "kahaan": "कहाँ", "yahaan": "यहाँ", "vahaan": "वहाँ", "wahaan": "वहाँ", "haan": "हाँ",
    "hoon": "हूँ", "hun": "हूँ", "kyon": "क्यों", "kyun": "क्यों", "kyonki": "क्योंकि",
    "kyunki": "क्योंकि", "unhen": "उन्हें", "inhen": "इन्हें", "hon": "हों", "gaanv": "गाँव",
    "gaon": "गाँव", "na": "न",
}

# A capital first letter is usually just sentence case ("Mera", "Hindi"), so it is read as
# lowercase - unless it starts one of these deliberate capitals.
_KEEP_INITIAL = {"T", "Th", "D", "Dh", "Sh", "GY", "OM", "RRi", "RRI", "O"}

# ---------------------------------------------------------------- language adjustments
# Values are Devanagari (carried to the language's script) or already in that script.
_NO_NUKTA = {"q": "क", "K": "ख", "G": "ग", "z": "ज", "f": "फ", "R": "ड", "Rh": "ढ"}
_DRAVIDIAN_VOWELS = {"e": ("ऎ", "ॆ"), "E": ("ए", "े"), "o": ("ऒ", "ॊ"), "O": ("ओ", "ो")}
_EASTERN = {   # Bengali-Assamese and Odia scripts
    "consonants": {"v": "ब", "z": "य", "f": "फ", "q": "क", "K": "ख", "G": "ग"},
    "vowels": {"E": ("ए", "े"), "O": ("ओ", "ो")},
}


def _merge(*rules: dict) -> dict:
    out = {}
    for r in rules:
        for key, value in r.items():
            out[key] = {**out.get(key, {}), **value} if isinstance(value, dict) else value
    return out


LANGUAGE_RULES = {
    "Hindi": {"words": HINDI_WORDS},
    # য় for y after a vowel (সময়), য after a consonant (ব্যক্তি) or at the start (যদি);
    # ng before a consonant or at the end is ং (বাংলা, রং).
    "Bengali": _merge(_EASTERN, {
        "consonants": {"w": "ब", "y": "য়", "Y": "য়", "L": "ल", "Ng": "ङ",
                       "ngg": "ङ" + JOIN + "ग"},
        "signs": {"ng": ANUSVARA}, "y_initial": "य", "y_phala": "य", "keep_initial": {"Y"}}),
    "Assamese": _merge(_EASTERN, {
        "consonants": {"r": "ৰ", "v": "ৱ", "w": "ৱ", "y": "য়", "Y": "য়", "L": "ल",
                       "Ng": "ङ", "ngg": "ङ" + JOIN + "ग"},
        "signs": {"ng": ANUSVARA}, "y_initial": "य", "y_phala": "य", "keep_initial": {"Y"}}),
    "Odia": _merge(_EASTERN, {
        "consonants": {"w": "ୱ", "y": "ୟ", "Y": "ୟ"}, "y_initial": "य", "keep_initial": {"Y"}}),
    "Gujarati": {"consonants": {**_NO_NUKTA, "z": "झ"}},
    "Punjabi": {
        "consonants": {"Sh": "श", "shh": "श", "S": "श", "R": "ੜ",
                       "Rh": "ੜ੍ਹ", "x": "क" + JOIN + "श", "ksh": "क" + JOIN + "श"},
        "vowels": {"RRi": ("रि", VIRAMA + "रि")}, "signs": {"MM": ANUSVARA},
        "words": {"main": "ਮੈਂ", "nahin": "ਨਹੀਂ", "nahiin": "ਨਹੀਂ", "haan": "ਹਾਂ"},
        "drop": {"GY", "RRI"}},
    "Tamil": {
        "consonants": {
            "t": "ट", "T": "ट", "Th": "ट", "d": "ट", "D": "ट", "Dh": "ट",
            "th": "त", "dh": "त", "kh": "क", "g": "क", "gh": "क", "chh": "च", "Ch": "च",
            "s": "च", "jh": "ज", "ph": "प", "b": "प", "bh": "प", "sh": "ष", "Sh": "ष",
            "S": "स", "f": "ःप", "z": "ऴ", "zh": "ऴ", "R": "ऱ", "n": "ऩ", "w": "न",
            "nj": "ञ", "q": "क", "K": "क", "G": "क", "cch": "च" + JOIN + "च"},
        "vowels": _DRAVIDIAN_VOWELS, "drop": {"Rh", "GY", "M", "MM"},
        "words": {"shrii": "ஸ்ரீ", "srii": "ஸ்ரீ"},
        "keep_initial": {"E", "O", "S"},
        "prefer": {"ட": "t", "த": "th", "ஷ": "sh", "ன": "n", "ழ": "zh", "ஞ": "nj"}},
    "Telugu": {"consonants": {**_NO_NUKTA, "R": "ऱ"}, "vowels": _DRAVIDIAN_VOWELS,
               "keep_initial": {"E", "O"}},
    "Kannada": {"consonants": {**_NO_NUKTA, "R": "ऱ"}, "vowels": _DRAVIDIAN_VOWELS,
                "keep_initial": {"E", "O"}},
    "Malayalam": {
        "consonants": {
            **_NO_NUKTA, "t": "ट", "th": "त", "thh": "थ", "sh": "ष", "S": "श", "z": "श",
            "zh": "ऴ", "R": "ऱ", "nt": "न" + JOIN + "ऱ", "nth": "न" + JOIN + "त",
            "ng": "ङ" + JOIN + "ङ", "nj": "ञ"},
        # au is written with the length mark alone (അക്കൗണ്ട്), as in nine words of ten.
        "vowels": {**_DRAVIDIAN_VOWELS, "au": ("औ", "ൗ")}, "drop": {"Rh"},
        "keep_initial": {"E", "O", "S"},
        # n before ഡ is ൻഡ (ആൻഡ്), far commoner than ണ്ഡ, which is typed ND.
        "plain_n": "ड",
        "prefer": {"ട": "t", "ത": "th", "ഷ": "sh", "ശ": "S", "ഞ": "nj"}},
    # Bodo is usually romanised with its own vowels: a is ा (narala: नाराला), o is the
    # inherent vowel (sonibarao: सनिबाराव), w is ो (kwmwr: कोमोर), ai and ao are ाय and ाव.
    "Bodo": {
        "vowels": {"a": ("आ", "ा"), "o": ("अ", ""), "w": ("ओ", "ो"), "ai": ("आय", "ाय"),
                   "ao": ("आव", "ाव"), "ou": ("औ", "ौ")},
        "keep_initial": set()},
}


# ---------------------------------------------------------------- script helpers
def _carry(text: str, block: int) -> str:
    """Devanagari -> the script whose block starts at `block` (dandas are shared)."""
    if block == DEVANAGARI:
        return text
    return "".join(chr(ord(c) - DEVANAGARI + block)
                   if DEVANAGARI <= ord(c) < DEVANAGARI + 0x80 and c not in "।॥" else c
                   for c in text)


def _valid(text: str, script: str) -> bool:
    """Every letter of `text` exists in `script` (Unicode has gaps, e.g. no Tamil ख)."""
    prefix = SCRIPTS[script]["unicode"]
    for c in text:
        if c in (JOIN, FINAL, "।", "॥"):
            continue
        if not unicodedata.name(c, "").startswith(prefix):
            return False
    return True


class Scheme:
    """English-letter typing for one language."""

    def __init__(self, language: str):
        info = LANGUAGE_INFO[language]
        rules = LANGUAGE_RULES.get(language, {})
        self.language = language
        self.script = info["scripts"][0]
        self.block = SCRIPTS[self.script]["block"]
        self.nasal = info.get("nasal", "anusvara")
        self.schwa = info.get("schwa", "final_long")
        self.full_stop = info.get("full_stop", "।")
        self.words = rules.get("words", {})
        # y may be written differently at the start of a word and after a consonant.
        self.y_initial = self._c(rules.get("y_initial", "")) or None
        self.y_phala = self._c(rules.get("y_phala", "")) or None
        self.plain_n = set(self._c(rules.get("plain_n", "")))
        c = self._c
        self.virama, self.anusvara, self.nukta = c(VIRAMA), c(ANUSVARA), c(NUKTA)

        drop = rules.get("drop", set())
        def table(base, extra, convert):
            out = {}
            for tok, value in {**base, **extra}.items():
                value = convert(value)
                if tok not in drop and value is not None:
                    out[tok] = value
            return out
        nfc = lambda v: unicodedata.normalize("NFC", c(v))
        def letters(v):
            v = nfc(v)
            return v if _valid(v, self.script) else None
        def vowel(pair):
            ind, sign = nfc(pair[0]), nfc(pair[1])
            return (ind, sign) if _valid(ind + sign, self.script) else None
        self.vowels = table(VOWELS, rules.get("vowels", {}), vowel)
        self.consonants = table(CONSONANTS, rules.get("consonants", {}), letters)
        self.signs = table(SIGNS, rules.get("signs", {}), letters)
        if "MM" not in self.signs and "MM" not in drop:   # no chandrabindu: plain anusvara
            self.signs["MM"] = self.anusvara
        self.standalone = table(STANDALONE, {}, letters)
        self.keep_initial = _KEEP_INITIAL | rules.get("keep_initial", set())
        # ड़ and ढ़ never join a following consonant (लड़का, পড়া, ਪੜ੍ਹਨਾ).
        flapped = self.consonants.get("R", "")
        self.no_conjunct = {"R", "Rh"} if flapped.endswith(self.nukta) or flapped == "ੜ" \
            else set()

        self.varga_nasal = {}
        for stops, nasal in _VARGAS:
            for ch in stops:
                self.varga_nasal.setdefault(c(ch), c(nasal))
        self.labials = {c(ch) for ch in "पफबभ"}
        self.keep_full = {c(ch) for ch in _KEEP_FULL_NASAL} | {
            self.consonants[t][0] for t in ("y", "r", "l", "v", "w", "h", "n", "m", "N", "L")
            if t in self.consonants}

        self._tokens = sorted(list(self.vowels) + list(self.consonants) + list(self.signs)
                              + list(self.standalone) + [HALANT, SEPARATOR],
                              key=len, reverse=True)
        self._max = max(map(len, self._tokens))
        self._build_inverse(rules.get("prefer", {}))
        self.plain_nasals = True
        # The token for the inherent vowel: a, or o in Bodo (where a is the long vowel).
        self._inherent = next(t for t, (_, sign) in self.vowels.items() if sign == "")

    def _c(self, text: str) -> str:
        return _carry(text, self.block)

    # ------------------------------------------------------------ typing
    def tokenize(self, word: str, sentence_case: bool = True) -> list[tuple[str, str]]:
        """Splits Latin text into (kind, token) pairs, longest match first."""
        if sentence_case and word[:1].isupper() \
                and not any(word.startswith(k) for k in self.keep_initial):
            word = word[0].lower() + word[1:]
        out, i = [], 0
        while i < len(word):
            for size in range(min(self._max, len(word) - i), 0, -1):
                chunk = word[i:i + size]
                # A capital with no meaning of its own is read as lowercase ("Bh" -> "bh",
                # "B" -> "b"); one that has a meaning keeps it (Malayalam "Nt" is ണ്ട, not nt).
                alt = chunk[0].lower() + chunk[1:]
                if alt == chunk or self._kind(chunk[0]):
                    alt = None
                for candidate in (chunk, alt) if alt else (chunk,):
                    kind = self._kind(candidate)
                    if kind:
                        out.append((kind, candidate))
                        i += size
                        break
                else:
                    continue
                break
            else:
                out.append(("other", word[i]))
                i += 1
        return out

    def _kind(self, tok: str) -> str | None:
        if tok in self.vowels:
            return "vowel"
        if tok in self.consonants:
            return "consonant"
        if tok in self.signs:
            return "sign"
        if tok in self.standalone:
            return "standalone"
        if tok == HALANT:
            return "halant"
        if tok == SEPARATOR:
            return "separator"
        return None

    def transliterate(self, word: str) -> str:
        """Converts one Latin word (no spaces) to the language's script."""
        if self.words and word.lower() in self.words:
            return self.words[word.lower()]
        tokens = self.tokenize(word)
        # Casual typing: a final single "a" means the long vowel ("mera" -> मेरा, "kya" -> क्या),
        # while a word ending in a consonant keeps the short inherent a ("kamal" -> कमल).
        # Exception: a "ya" closing a cluster inside the word stays short (anya -> अन्य,
        # satya -> सत्य, kaarya -> कार्य), unlike a word-initial cluster (kya -> क्या).
        if self.schwa == "final_long" and len(tokens) >= 2 \
                and tokens[-1] == ("vowel", "a") and tokens[-2][0] == "consonant":
            sanskrit_ya = (tokens[-2][1] == "y" and len(tokens) >= 4
                           and tokens[-3][0] == "consonant" and tokens[-4][0] == "vowel")
            if not sanskrit_ya:
                tokens[-1] = ("vowel", "aa")
        out = []
        after_consonant = False   # last output is a consonant still carrying its inherent a
        last_consonant = ""
        for idx, (kind, tok) in enumerate(tokens):
            nxt = tokens[idx + 1] if idx + 1 < len(tokens) else None
            if kind == "consonant":
                letter = self.consonants[tok]
                if tok == "y" and not out and self.y_initial:
                    letter = self.y_initial
                elif tok == "y" and after_consonant and self.y_phala:
                    letter = self.y_phala
                if after_consonant and last_consonant not in self.no_conjunct:
                    out.append(JOIN)
                last_consonant = tok
                nasal_form = self._nasal_before(tok, out, nxt)
                if nasal_form is not None:
                    out.append(nasal_form)
                    after_consonant = False
                    continue
                out.append(letter)
                after_consonant = True
            elif kind == "vowel":
                independent, sign = self.vowels[tok]
                out.append(sign if after_consonant else independent)
                after_consonant = False
            elif kind == "sign":
                out.append(self.signs[tok])
                after_consonant = False
            elif kind == "standalone":
                if after_consonant:
                    out.append(self.virama)
                out.append(self.standalone[tok])
                after_consonant = False
            elif kind == "halant":
                if after_consonant:
                    out.append(self.virama)
                after_consonant = False
            elif kind == "separator":
                if after_consonant and self.schwa == "explicit":
                    out.append(FINAL)   # k_h: two letters, each without a vowel (ആർഎസ്)
                after_consonant = False
            else:
                out.append(tok)
                after_consonant = False
        if after_consonant and self.schwa == "explicit":
            out.append(FINAL)
        text = self._post("".join(out))
        return unicodedata.normalize("NFC", text)

    def _nasal_before(self, tok, out, nxt):
        """Spelling of n/m when it sits between a vowel and a consonant, or None."""
        if tok not in ("n", "m", "N") or not out or not nxt or nxt[0] != "consonant":
            return None
        if out[-1] in (JOIN, self.virama):     # already in a cluster: keep the letter
            return None
        following = self.consonants[nxt[1]][0]
        if following in self.keep_full:
            return None
        if self.nasal == "anusvara":
            # m only merges before p ph b bh (संबंध); elsewhere it is a real म (तुम्को).
            if tok == "m" and following not in self.labials:
                return None
            return self.anusvara    # also before s sh h: संस्कृत, हिंसा
        if self.nasal == "homorganic" and tok != "m" and following in self.varga_nasal \
                and following not in self.labials \
                and not (tok == "n" and following in self.plain_n):
            return self.varga_nasal[following] + JOIN
        return None

    def _post(self, text: str) -> str:
        """Script spelling rules, then the engine's halants become real ones."""
        post = _POST.get(self.script)
        if post:
            text = post(text)
        return text.replace(JOIN, self.virama).replace(FINAL, self.virama)

    def transliterate_text(self, text: str) -> str:
        """Converts a whole Latin sentence; spaces, digits and punctuation are kept."""
        out, word = [], []
        for ch in text:
            if ch.isascii() and (ch.isalpha() or ch in "^_~"):
                word.append(ch)
                continue
            if word:
                out.append(self.transliterate("".join(word)))
                word = []
            out.append(self.full_stop if ch == "." else "।" if ch == "|" else ch)
        if word:
            out.append(self.transliterate("".join(word)))
        return "".join(out).replace("।।", "॥")

    # ------------------------------------------------------------ script -> Latin
    def _build_inverse(self, prefer: dict) -> None:
        def first(table, pick):
            inv = {}
            for tok, value in table.items():
                key = pick(value)
                if key and key not in inv:
                    inv[key] = tok
            return inv
        # One letter (with or without nukta) -> the first token that types it.
        self._inv_consonant = first(
            self.consonants, lambda v: v if len(v) == 1 or v[1:] == self.nukta else None)
        self._inv_consonant.update(prefer)
        # Letters written with the aytham sign in front (Tamil ஃப for f).
        self._inv_pair = {v: t for t, v in self.consonants.items()
                          if len(v) == 2 and v[0] == self.signs.get("H")}
        self._inv_consonant.update(self._inv_pair)
        vowel_toks = ("a", "aa", "i", "ii", "u", "uu", "RRi", "RRI", "e", "E", "ai", "o",
                      "O", "au")
        ordered_v = {t: self.vowels[t] for t in vowel_toks if t in self.vowels}
        ordered_v.update({t: v for t, v in self.vowels.items() if t not in ordered_v})
        self._inv_sign = first(ordered_v, lambda v: v[1] or None)
        self._inv_independent = first(ordered_v, lambda v: v[0])
        self._inv_other = {self.anusvara: "M", self.signs["H"]: "H", "।": ".", "॥": "||"}
        if self.signs.get("MM", self.anusvara) != self.anusvara:
            self._inv_other[self.signs.get("MM", self.anusvara)] = "MM"
        if "OM" in self.standalone:
            self._inv_other[self.standalone["OM"]] = "OM"
        if self.full_stop != "।":
            self._inv_other["।"] = "|"
        self._marks = {self.anusvara, self.signs.get("MM", self.anusvara), self.signs["H"]}

    def to_latin(self, text: str, plain_nasals: bool = True) -> str:
        """Script text -> the English letters that type it with this scheme (the inverse of
        transliterate_text). Used to check that real text can be typed. plain_nasals types
        a nasal before a consonant as n where that works (hindii); otherwise as M (hiMdii)."""
        self.plain_nasals = plain_nasals
        out, word = [], []
        for ch in unicodedata.normalize("NFC", text) + " ":
            if ch.isalpha() or unicodedata.category(ch).startswith("M"):
                word.append(ch)
                continue
            if word:
                out.append(self._word_to_latin("".join(word)))
                word = []
            out.append(self._inv_other.get(ch, ch))
        return "".join(out)[:-1]

    def _word_to_latin(self, target: str) -> str:
        pre = _PRE.get(self.script)
        word = pre(target) if pre else target
        pieces = []
        pending_a = False   # a consonant whose inherent 'a' has not been written yet
        last_vowel = False  # the previous output was a vowel (sign or independent)
        i = 0
        while i < len(word):
            ch = word[i]
            if i + 1 < len(word) and word[i + 1] == self.nukta \
                    and ch + self.nukta in self._inv_consonant:
                ch, i = ch + self.nukta, i + 1
            elif word[i:i + 2] in self._inv_pair:      # Tamil ஃப is typed f
                ch, i = word[i:i + 2], i + 1
            if ch in self._inv_consonant:
                if pending_a:
                    pieces.append(self._inherent)
                latin = self._consonant_latin(ch, word, i, pieces)
                if not pieces and latin[0].isupper() and not any(
                        latin.startswith(k) for k in self.keep_initial):
                    pieces.append(SEPARATOR)   # a capital first letter would read as lowercase
                pieces.append(latin)
                pending_a, last_vowel = True, False
                if i + 1 < len(word) and word[i + 1] == self.virama:
                    i += 1
                    pending_a = False
                    pieces.append(HALANT)    # removed below wherever it is not needed
            elif ch in self._inv_sign:
                self._append(pieces, self._inv_sign[ch])
                pending_a, last_vowel = False, True
            elif ch in self._inv_independent:
                latin = self._inv_independent[ch]
                if pieces and pieces[-1] == HALANT and self.schwa == "explicit":
                    pieces[-1] = SEPARATOR         # ആർഎസ്: r_es (the chillu stays)
                elif pending_a or last_vowel:
                    if pending_a:
                        pieces.append(self._inherent)
                    pieces.append(SEPARATOR)
                elif not pieces and latin[0].isupper() and latin not in self.keep_initial:
                    pieces.append(SEPARATOR)       # ઍ at the start: _E, not E (read as e)
                pieces.append(latin)
                pending_a, last_vowel = False, True
            elif ch in self._inv_other:
                if pending_a and ch in self._marks:
                    pieces.append(self._inherent)
                nxt = word[i + 1:i + 2]
                if ch == self.anusvara and self.plain_nasals and self.nasal == "anusvara" \
                        and nxt in self._inv_consonant and nxt not in self.keep_full \
                        and self._splits(["n", self._inv_consonant[nxt]]):
                    pieces.append("n")             # typed as heard: hindii, not hiMdii
                else:
                    self._append(pieces, self._inv_other[ch])
                pending_a, last_vowel = False, ch in self._marks
            else:
                pending_a = last_vowel = False
                pieces.append(ch)
            i += 1
        if pending_a and self.schwa == "explicit":
            pieces.append(self._inherent)
        latin = "".join(pieces)
        if self.words.get(latin.lower(), target) != target:   # मैन, not the listed मैं
            latin = latin[:-1] + SEPARATOR + latin[-1]
        # Drop each ^ and _ that typing does not need: keep a removal when the result is
        # still (or becomes, or gets closer to) the original word.
        closeness = lambda out: SequenceMatcher(None, out, target).ratio()
        for mark in (HALANT, SEPARATOR):
            j = latin.find(mark)
            while j != -1:
                shorter = latin[:j] + latin[j + 1:]
                now, then = self.transliterate(latin), self.transliterate(shorter)
                if then == target or now != target and closeness(then) >= closeness(now):
                    latin = shorter
                    j = latin.find(mark, j)
                else:
                    j = latin.find(mark, j + 1)
        return latin

    def _append(self, pieces: list[str], latin: str) -> None:
        """Adds a piece, kept apart from the one before if the two would merge (O + M would
        read as OM, ॐ)."""
        if pieces and pieces[-1] not in (HALANT, SEPARATOR) \
                and not self._splits([pieces[-1], latin]):
            pieces.append(SEPARATOR)
        pieces.append(latin)

    def _consonant_latin(self, ch, word, i, pieces) -> str:
        at_start = not pieces
        after_virama = bool(pieces) and pieces[-1] == HALANT
        if ch == self.y_initial and at_start or ch == self.y_phala and after_virama:
            return "y"
        if ch == self.consonants.get("Y") and (at_start and self.y_initial
                                               or after_virama and self.y_phala):
            return "Y"                             # ୟ where y would give ଯ (ୟାଦବ: Yaadab)
        if self.script == "Taml" and ch == "ந":
            dental = word[i + 1:i + 3] == "்த"
            return "n" if at_start or dental else "w"
        following = word[i + 2:i + 3] if word[i + 1:i + 2] == self.virama else ""
        if self.plain_nasals and self.nasal == "homorganic" and not at_start \
                and following not in self.labials and following not in self.plain_n \
                and self.varga_nasal.get(following) == ch \
                and self._splits(["n", self._inv_consonant[following]]):
            return "n"                             # typed as heard: gangaa, not ga~Ngaa
        return self._inv_consonant[ch]

    def _splits(self, tokens: list[str]) -> bool:
        """True if typing the tokens one after another reads them back the same way."""
        return [t for _, t in self.tokenize("".join(tokens), sentence_case=False)] == tokens

    # ------------------------------------------------------------ help
    def cheat_sheet(self) -> list[tuple[str, list[tuple[str, str]]]]:
        """Groups of (what to type, what appears) for the in-app typing help."""
        def grouped(tokens, value):
            seen = {}
            for tok in tokens:
                v = value(tok)
                if v is not None:
                    seen.setdefault(v, []).append(tok)
            return seen
        vowel_rows = grouped([t for t in VOWELS if t in self.vowels]
                             + [t for t in self.vowels if t not in VOWELS],
                             lambda t: self.vowels[t])
        vowels = [(" / ".join(toks), f"{ind} {sign}".strip())
                  for (ind, sign), toks in vowel_rows.items()]
        order = ["k", "kh", "g", "gh", "~N", "ng", "Ng", "ch", "chh", "Ch", "c", "j", "jh",
                 "~n", "nj", "T", "Th", "D", "Dh", "N", "t", "th", "thh", "d", "dh", "n", "w",
                 "p", "ph", "b", "bh", "m", "y", "r", "l", "v", "L", "sh", "Sh", "shh", "s",
                 "S", "h", "z", "zh", "R", "Rh", "f", "q", "K", "G", "x", "ksh", "GY", "cch",
                 "nt", "nth", "ngg"]
        letters = grouped([t for t in order if t in self.consonants]
                          + [t for t in self.consonants if t not in order],
                          lambda t: self.consonants[t])
        def label(letter, toks):   # the usual spelling first, at most three spellings
            best = self._inv_consonant.get(letter)
            plain = [t for t in toks if t not in ("q", "K", "G")]   # nukta letters it lacks
            toks = sorted(plain or toks, key=lambda t: (t != best, not t.islower(), len(t) > 1))
            return " / ".join(toks[:3])
        consonants = [(label(v, toks), v.replace(JOIN, self.virama))
                      for v, toks in letters.items()]
        mark = lambda c: ("◌" + c) if unicodedata.category(c[0]).startswith("M") else c
        marks = [(tok, mark(v)) for tok, v in self.signs.items()
                 if tok in ("M", "MM", "H", "ng") and not (tok == "MM" and v == self.anusvara)]
        if "OM" in self.standalone:
            marks.append(("OM", self.standalone["OM"]))
        stop = self.full_stop if self.full_stop != "." else ". full stop"
        control = [("^", f"halant ◌{self.virama}"), ("_", "keep letters apart"),
                   (".", stop), ("Ctrl+Space", "switch to English letters")]
        sheet = [("Vowels", vowels), ("Consonants", consonants), ("Marks", marks),
                 ("Control", control)]
        examples = EXAMPLES.get(self.language)
        if examples:
            sheet.append(("Examples", [(latin, script) for latin, script in examples]))
        return sheet

    def case_example(self) -> tuple[str, str, str, str]:
        """A small/capital pair with different letters, e.g. ("t", "त", "T", "ट")."""
        for small, big in (("t", "T"), ("n", "N"), ("d", "D"), ("s", "S"), ("l", "L")):
            a, b = self.consonants.get(small), self.consonants.get(big)
            if a and b and a != b:
                return small, a, big, b
        return "a", self.vowels["a"][0], "A", self.vowels["A"][0]


# ---------------------------------------------------------------- script spelling rules
# Each script's post-processing runs on the engine's output while its own halants are still
# marked (JOIN between consonants, FINAL at the end of a word).
VIRAMA_OF = {s: _carry(VIRAMA, info["block"]) for s, info in SCRIPTS.items() if "block" in info}
_GURU_PAIRS = [(_carry(p, 0x0A00), _carry(a, 0x0A00))
               for p, a in zip("कगचजटडतदपब", "खघछझठढथधफभ")]
_GURU_TIPPI_AFTER = "[ਕ-ਹਖ਼-ਫ਼਼ਿੁੂਅਇ]"   # ਅ ਇ, not ਉ (ਕਿਉਂ)
_CHILLU = {"ണ": "ൺ", "ന": "ൻ", "ര": "ർ", "ല": "ൽ",
           "ള": "ൾ"}   # ണ ന ര ല ള -> ൺ ൻ ർ ൽ ൾ


def _post_bengali(text):
    # A typed halant on ত is khanda ta: উৎসব (ut^sab), হঠাৎ (haThaat^).
    return text.replace("ত্", "ৎ")


def _post_gurmukhi(text):
    for nasal in "ਨਮ":   # ਧੰਨ, ਅੰਮਾ: a doubled nasal is written with tippi
        text = text.replace(nasal + JOIN + nasal, "ਂ" + nasal)
    for plain, aspirate in _GURU_PAIRS:   # ਪੱਕਾ, ਅੱਖ: addak marks a doubled consonant
        text = text.replace(plain + JOIN + aspirate, "ੱ" + aspirate)
    text = re.sub(f"(.){JOIN}(.)", lambda m: "ੱ" + m[2] if m[1] == m[2] else m[0], text)
    # Only ਰ and ਹ are written below another letter (ਪ੍ਰੇਮ, ਉਨ੍ਹਾਂ); other clusters are
    # written as plain letters (ਦੋਸਤ).
    text = re.sub(f"{JOIN}(?=[ਰਹ])", "੍", text)
    text = text.replace(JOIN, "")
    # Nasal sign: tippi after a short vowel or a bare consonant, bindi after a long vowel.
    return re.sub(f"(?<={_GURU_TIPPI_AFTER})ਂ", "ੰ", text)


def _post_malayalam(text):
    # Word-final n r l L N are chillu letters (അവൻ, അവർ, പാൽ), final m is anusvara
    # (മലയാളം), and r before a consonant other than യ is a chillu (കർമം). Not at the end
    # of a cluster: ന്ന് stays as it is.
    text = re.sub(f"(?<!{JOIN})([ണനരലള]){FINAL}", lambda m: _CHILLU[m[1]], text)
    text = re.sub(f"(?<!{JOIN})മ{FINAL}", "ം", text)
    # Before another consonant the chillu is written too (കർമം, അവൾക്ക്, ഉൽപ്പന്നം, ലൈസൻസ്,
    # അലോൺസോ), except in the clusters Malayalam Wikipedia writes joined: doubled letters,
    # before യ, ന with a dental or റ (ന്ത, ന്റ), and ണ with a retroflex (ണ്ട).
    keep = {"ര": "യര", "ല": "യല", "ള": "യള", "ന": "തഥദധനമയറവ", "ണ": "ടഠഡഢണയ"}
    return re.sub(f"(?<!{JOIN})([രലളനണ]){JOIN}(?=([ക-ഹ]))",
                  lambda m: m[0] if m[2] in keep[m[1]] else _CHILLU[m[1]], text)


def _post_telugu(text):
    return text.replace("మ" + FINAL, "ం")   # నమస్కారం


def _post_tamil(text):
    # ன never starts a word (நான், நன்றி), and n before த is ந even after another
    # consonant (அமர்ந்து, தொடர்ந்து).
    text = text.replace("ன" + JOIN + "த", "ந" + JOIN + "த")
    return "ந" + text[1:] if text.startswith("ன") else text


_POST = {"Beng": _post_bengali, "Guru": _post_gurmukhi, "Mlym": _post_malayalam,
         "Telu": _post_telugu, "Taml": _post_tamil}


# Reading text back (to_latin): undo the spellings above so each letter maps to a token.
def _pre_gurmukhi(word):
    plain_of = {a: p for p, a in _GURU_PAIRS}
    word = re.sub("ੱ(.)", lambda m: plain_of.get(m[1], m[1]) + "੍" + m[1], word)
    return word.replace("ੰ", "ਂ")


def _pre_malayalam(word):
    word = word.replace("ൌ", "ൗ")   # the older au sign, typed as au
    for base, chillu in _CHILLU.items():
        word = word.replace(chillu, base + "്")
    return re.sub("ം$", "മ്", word)


def _pre_telugu(word):
    return re.sub("ం$", "మ్", word)


def _pre_bengali(word):
    return word.replace("ৎ", "ত্")


_PRE = {"Guru": _pre_gurmukhi, "Mlym": _pre_malayalam, "Telu": _pre_telugu,
        "Beng": _pre_bengali}


# ---------------------------------------------------------------- examples (shown in help)
EXAMPLES = {
    "Bodo": [("gwra", "गोरा"), ("mechao", "मेचाव"), ("khani", "खानि"), ("mohon", "महन"),
             ("jadugwr", "जादुगोर"), ("gaisongiri", "गायसंगिरि"), ("halamao", "हालामाव"),
             ("aadorsh", "आदर्श")],
    "Hindi": [("namaste", "नमस्ते"), ("bhaarat", "भारत"), ("hindii", "हिंदी"),
              ("dhanyavaad", "धन्यवाद"), ("kRRipayaa", "कृपया"), ("mera", "मेरा"),
              ("kamal", "कमल"), ("main", "मैं"), ("laRkaa", "लड़का"), ("DOkTar", "डॉक्टर")],
    "Bengali": [("aami", "আমি"), ("tumi", "তুমি"), ("bhaalo", "ভালো"), ("jal", "জল"),
                ("baanglaa", "বাংলা"), ("dhanyabaad", "ধন্যবাদ"), ("samay", "সময়"),
                ("yadi", "যদি"), ("byakti", "ব্যক্তি"), ("ut^sab", "উৎসব")],
    "Assamese": [("asam", "অসম"), ("maanuh", "মানুহ"), ("paanii", "পানী"),
                 ("raati", "ৰাতি"), ("ghar", "ঘৰ"), ("kitaap", "কিতাপ"), ("aaji", "আজি"),
                 ("dhanyabaad", "ধন্যবাদ")],
    "Odia": [("oRishaa", "ଓଡ଼ିଶା"), ("bhaarata", "ଭାରତ"), ("jagannaatha", "ଜଗନ୍ନାଥ"),
             ("paaNi", "ପାଣି"), ("ghara", "ଘର"), ("pilaa", "ପିଲା"),
             ("dhanyabaada", "ଧନ୍ୟବାଦ"), ("samaya", "ସମୟ"), ("kaTak", "କଟକ")],
    "Gujarati": [("gujaraatii", "ગુજરાતી"), ("namaste", "નમસ્તે"), ("aabhaar", "આભાર"),
                 ("paaNii", "પાણી"), ("ghar", "ઘર"), ("amadaavaad", "અમદાવાદ"),
                 ("chho", "છો"), ("saaruM", "સારું"), ("hindii", "હિંદી")],
    "Punjabi": [("panjaab", "ਪੰਜਾਬ"), ("panjaabii", "ਪੰਜਾਬੀ"), ("pakkaa", "ਪੱਕਾ"),
                ("dhannvaad", "ਧੰਨਵਾਦ"), ("srii", "ਸ੍ਰੀ"), ("ghar", "ਘਰ"),
                ("paaNii", "ਪਾਣੀ"), ("gurduaaraa", "ਗੁਰਦੁਆਰਾ"), ("paRhnaa", "ਪੜ੍ਹਨਾ"),
                ("acchaa", "ਅੱਛਾ")],
    "Tamil": [("vaNakkam", "வணக்கம்"), ("thamizh", "தமிழ்"), ("nanRi", "நன்றி"),
              ("naan", "நான்"), ("ammaa", "அம்மா"), ("veedu", "வீடு"), ("anbu", "அன்பு"),
              ("chennai", "சென்னை"), ("thaNNiir", "தண்ணீர்"), ("Ezhu", "ஏழு"),
              ("sari", "சரி")],
    "Telugu": [("telugu", "తెలుగు"), ("namaskaaram", "నమస్కారం"), ("amma", "అమ్మ"),
               ("nEnu", "నేను"), ("illu", "ఇల్లు"), ("baagunnaanu", "బాగున్నాను"),
               ("haidaraabaad", "హైదరాబాద్"), ("telangaaNa", "తెలంగాణ"),
               ("dhanyavaadaalu", "ధన్యవాదాలు")],
    "Kannada": [("kannaDa", "ಕನ್ನಡ"), ("namaskaara", "ನಮಸ್ಕಾರ"), ("bengaLuuru", "ಬೆಂಗಳೂರು"),
                ("mane", "ಮನೆ"), ("niiru", "ನೀರು"), ("ondu", "ಒಂದು"), ("huDuga", "ಹುಡುಗ"),
                ("dhanyavaadagaLu", "ಧನ್ಯವಾದಗಳು")],
    "Malayalam": [("malayaaLam", "മലയാളം"), ("kEraLam", "കേരളം"), ("ente", "എന്റെ"),
                  ("njaan", "ഞാൻ"), ("amma", "അമ്മ"), ("kutti", "കുട്ടി"), ("avaL", "അവൾ"),
                  ("avar", "അവർ"), ("ningaL", "നിങ്ങൾ"), ("santhOsham", "സന്തോഷം"),
                  ("thiruvananthapuram", "തിരുവനന്തപുരം")],
}


@lru_cache(maxsize=None)
def scheme(language: str) -> Scheme:
    return Scheme(language)


def available(language: str) -> bool:
    return bool(LANGUAGE_INFO.get(language, {}).get("phonetic"))


# ---------------------------------------------------------------- Hindi shortcuts
def transliterate(word: str, language: str = "Hindi") -> str:
    return scheme(language).transliterate(word)


def transliterate_text(text: str, language: str = "Hindi") -> str:
    return scheme(language).transliterate_text(text)


def to_latin(text: str, language: str = "Hindi") -> str:
    return scheme(language).to_latin(text)


def cheat_sheet(language: str = "Hindi"):
    return scheme(language).cheat_sheet()
