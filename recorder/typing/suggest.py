"""Word suggestions for English-letter typing, like a phone keyboard: "pani" offers पानी.

People rarely type the exact scheme (aa for the long a, T for ट); they write "pani",
"kitab", "ladka". Each language has a list of its most frequent words (from Wikipedia, see
data/wordlists/README.md) with a "loose key" for each: the word's English letters with the
distinctions casual typing drops (long and short vowels, the inherent a, doubled letters,
s/sh, ...) removed. What is typed gets the same treatment and is looked up.

The exact result of the scheme is always one of the suggestions, and it stays first when it
is itself a known word or when the typing is clearly deliberate (capitals inside the word,
^, _, ~ or a long vowel spelt out as aa ii uu). Otherwise the most frequent matching word
comes first.
"""

import gzip
import re
from difflib import SequenceMatcher
from functools import lru_cache

from .. import config
from . import phonetic

WORDLIST_DIR = config.DATA_DIR / "wordlists"
LIMIT = 5

_REPLACE = [("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"), ("w", "v"),
            ("z", "j"), ("q", "k"), ("f", "ph"), ("x", "ks"), ("ksh", "ks"), ("sh", "s"),
            ("chch", "ch"), ("cch", "ch"), ("ri", "r"), ("ru", "r"), ("iy", "i"), ("ey", "e"),
            ("ai", "e"), ("ay", "e"), ("au", "o")]
# Casual habits that differ by language.
_O_INHERENT = {"Bengali", "Assamese", "Odia"}   # o for the inherent vowel (kemon), v for b
_NG_ANUSVARA = {"Bengali", "Assamese"}           # ং typed ng (bangla, rang)
_LOOSE_DENTALS = {"Tamil", "Malayalam"}          # t or th, d or dh, l or zh (tamil, thamizh)
EXACT_BONUS = 20      # the scheme's own spelling wins unless another word is 20x as frequent
CLOSENESS_POWER = 6   # how much a closer spelling outweighs frequency (karna: करना, not कारण)


def _flap(language: str) -> str:
    """How casual typing writes ड़ / ড় / ଡ଼: d in Hindi and Odia (ladka, odisha), r in
    Bengali, Assamese and Punjabi (bari, parhna); R is ற, റ, ఱ in the south."""
    script = config.LANGUAGE_INFO[language]["scripts"][0]
    return "d" if script == "Deva" or language == "Odia" else "r"


def loose_key(latin: str, language: str = "Hindi", native: bool = False) -> str:
    """English letters with the distinctions casual typing drops removed. native=True for
    letters made by phonetic.to_latin (their capitals have exact meanings)."""
    s = latin
    if native:
        flap = _flap(language)
        nasal = "ng" if language in _NG_ANUSVARA else "n"
        for a, b in (("RRi", "ri"), ("RRI", "ri"), ("j~n", "gy"), ("GY", "gy"), ("MM", "n"),
                     ("M", nasal), ("Rh", flap + "h"), ("R", flap), ("H", ""), ("~N", "ng"),
                     ("~n", "nj")):
            s = s.replace(a, b)
    s = re.sub(r"[\^_~]", "", s.lower())
    if language in _LOOSE_DENTALS:
        s = s.replace("zh", "l")              # tamil, thamizh, kozhikode
    # A doubled sound written with two letters: thth, ngng, njnj (ആദ്യത്തെ: aadyathe)
    s = re.sub(r"(th|dh|ch|sh|kh|gh|ph|bh|jh|ng|nj)\1+", r"\1", s)
    s = re.sub("(?<=[aeiou])yi", "i", s)      # gayi = gaii, tayi = taai
    for a, b in _REPLACE:
        s = s.replace(a, b)
    s = re.sub("c(?!h)", "k", s)              # cricket, cup
    s = re.sub("eh(?![aeiou])", "ah", s)      # pehla = pahalaa, yeh = yah
    s = re.sub("(?<=[aeiou])h$", "", s)       # toh = to
    if not native:
        s = re.sub("(?<=[^aeiou])y$", "i", s)     # swamy = svaamii (but मुख्य is mukhy)
    if language in _LOOSE_DENTALS:
        s = s.replace("th", "t").replace("dh", "d")
    if language == "Malayalam":
        s = s.replace("d", "t")                # ട typed d (vadakku, palakkad)
        s = re.sub("u$", "", s)                # the final half-u: vadakku for വടക്ക്
    if language == "Tamil":
        # One letter each for k/g, t/d, p/b and ch/s; ன்ற typed ndr (pondra, nandri);
        # ஞ்ச typed nj (thanjavur); an initial ஏ typed ye (yerpadum).
        s = s.replace("njch", "nch").replace("nj", "nch").replace("ch", "s")
        s = s.replace("g", "k").replace("d", "t").replace("b", "p")
        s = s.replace("ntr", "nr").replace("tr", "r")
        s = re.sub("^ye", "e", s)
    if language in _O_INHERENT:
        # ক্ষ sounds kkh (shikkha), ভ is often v or b (ovineta), an initial অ is o (onchol)
        # and an initial য is j (jete).
        s = s.replace("ks", "kh").replace("v", "b").replace("bh", "b")
        s = re.sub("^o", "a", s)
        s = re.sub("^y", "j", s)
    s = re.sub("m(?=[pb])", "n", s)
    dropped = "ao" if language in _O_INHERENT else "a"
    s = s[:1] + re.sub(f"[{dropped}]", "", s[1:])   # the inherent vowel: kiratpur = kiratapur
    s = re.sub(r"(.)\1+", r"\1", s)
    return s.rstrip("a") or s


def word_keys(latin: str, language: str) -> list[str]:
    """The keys a listed word is found under: its loose key, and without a final nasal
    sign, which casual typing often leaves out (maa for ਮਾਂ, bhagma for ભાગમાં)."""
    keys = [loose_key(latin, language, native=True)]
    bare = re.sub("M+$", "", latin)
    if bare != latin and bare:
        keys.append(loose_key(bare, language, native=True))
    return list(dict.fromkeys(keys))

def _light(latin: str) -> str:
    """Spelling with only the differences that never matter removed (for closeness)."""
    s = re.sub(r"[\^_~]", "", latin.lower())
    for a, b in (("ee", "ii"), ("oo", "uu"), ("w", "v"), ("z", "j"), ("f", "ph"), ("q", "k")):
        s = s.replace(a, b)
    return re.sub("c(?!h)", "k", s)


def _tight(latin: str, language: str, native: bool = False) -> str:
    """Like the loose key, but a and aa stay different: what someone who spells out long
    vowels (vartmaan) agrees with."""
    s = latin
    if native:
        flap = _flap(language)
        for a, b in (("RRi", "ri"), ("j~n", "gy"), ("GY", "gy"), ("MM", "n"), ("M", "n"),
                     ("Rh", flap + "h"), ("R", flap), ("H", "")):
            s = s.replace(a, b)
    s = _light(s).replace("aa", "@").replace("ii", "i").replace("uu", "u")
    return s[:1] + s[1:].replace("a", "")    # only the silent a is free; doubles count


class WordList:
    """A language's frequent words with their counts and exact spellings, indexed by
    loose key."""

    def __init__(self, path, language: str):
        self.language = language
        self.count, self.latin, self.index = {}, {}, {}
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                word, keys, n, latin = line.rstrip("\n").split("\t")
                self.count[word] = int(n)
                self.latin[word] = latin
                for key in keys.split("|"):
                    self.index.setdefault(key, []).append(word)   # most frequent first

    def __contains__(self, word: str) -> bool:
        return word in self.count

    def matches(self, typed: str) -> list[str]:
        return self.index.get(loose_key(typed, self.language), [])


@lru_cache(maxsize=None)
def wordlist(language: str) -> WordList | None:
    code = config.LANGUAGES.get(language)
    path = WORDLIST_DIR / f"{code}.tsv.gz"
    return WordList(path, language) if code and path.is_file() else None


def available(language: str) -> bool:
    return phonetic.available(language) and wordlist(language) is not None


def deliberate(typed: str, language: str = "Hindi") -> bool:
    """Typing that uses the scheme on purpose: a capital inside the word, a capital first
    letter that means something (Dh for ढ), or ^ _ ~."""
    first_capital = typed[:1].isupper() and any(
        typed.startswith(k) for k in phonetic.scheme(language).keep_initial)
    return first_capital or typed[1:] != typed[1:].lower() or any(c in typed for c in "^_~")


def spelt_out(typed: str) -> bool:
    """A long vowel written out (aa ii uu): "laapattaa" means लापत्ता, not the commoner
    लापता, unless a listed word agrees with every vowel typed (vartmaan: वर्तमान)."""
    return any(v in typed.lower() for v in ("aa", "ii", "uu"))


def suggestions(language: str, typed: str, limit: int = LIMIT) -> list[str]:
    """What `typed` may mean, best first. The first is what Space writes."""
    exact = phonetic.scheme(language).transliterate(typed)
    words = wordlist(language)
    if not words or not typed:
        return [exact]
    others = [w for w in words.matches(typed) if w != exact]
    typed_light = _light(typed)

    def score(w: str) -> float:
        # Frequency, times how close the word's own spelling is to what was typed, with a
        # head start for the scheme's exact result ("bharat" is still भारत, far commoner
        # than the name भरत; "kal" stays कल).
        close = SequenceMatcher(None, typed_light, _light(words.latin[w])).ratio()
        return words.count[w] * close ** CLOSENESS_POWER * (EXACT_BONUS if w == exact else 1)

    others.sort(key=score, reverse=True)
    if deliberate(typed, language) or not others:
        return [exact] + others[:limit - 1]
    if exact not in words:
        if spelt_out(typed):
            tight = _tight(typed, language)
            agree = [w for w in others if _tight(words.latin[w], language, True) == tight]
            rest = [w for w in others if w not in agree]
            return (agree + [exact] + rest)[:limit] if agree else ([exact] + others)[:limit]
        return others[:limit - 1] + [exact]
    return sorted([exact] + others, key=score, reverse=True)[:limit]
