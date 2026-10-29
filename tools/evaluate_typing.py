"""Measure English-letter typing against real romanised words (AI4Bharat's Aksharantar test
sets: pairs of how a word is written in English letters and in its own script).

Two numbers per language:
  coverage  every native word can be typed (word -> English letters -> the same word)
  natural   the English spelling people actually used gives the right word

The data (CC-BY) is downloaded into a cache folder when the tool runs; nothing is stored in
this project. Words with digits, Latin letters or foreign named entities are skipped.

    .venv\\Scripts\\python tools\\evaluate_typing.py --data C:\\temp\\aksharantar [hin ben ...]
"""

import argparse
import json
import sys
import unicodedata
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from recorder.typing import phonetic, suggest  # noqa: E402

URL = "https://huggingface.co/datasets/ai4bharat/Aksharantar/resolve/main/{}.zip"
CODES = {"hin": "Hindi", "mar": "Marathi", "nep": "Nepali", "san": "Sanskrit",
         "kok": "Konkani", "mai": "Maithili", "brx": "Bodo", "doi": "Dogri",
         "ben": "Bengali", "asm": "Assamese", "ori": "Odia", "guj": "Gujarati",
         "pan": "Punjabi", "tam": "Tamil", "tel": "Telugu", "kan": "Kannada",
         "mal": "Malayalam"}


def load(code: str, data: Path, split: str = "test") -> list[dict]:
    folder = data / code
    path = folder / f"{code}_{split}.json"
    if not path.exists():
        folder.mkdir(parents=True, exist_ok=True)
        archive = data / f"{code}.zip"
        if not archive.exists():
            print(f"downloading {code}.zip ...", flush=True)
            urllib.request.urlretrieve(URL.format(code), archive)
        with zipfile.ZipFile(archive) as z:
            z.extract(f"{code}_{split}.json", folder)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [r for r in rows if r.get("source") != "AK-NEF"]   # skip foreign names


def well_formed(word: str, language: str) -> bool:
    """False for spelling errors in the source data: two vowel signs in a row (ाे for ो),
    a doubled nasal mark, a halant or nukta after a vowel sign, a sign with no letter."""
    kinds = []
    for c in word:
        name = unicodedata.name(c, "")
        if "VOWEL SIGN" in name or "AU LENGTH" in name:
            kinds.append("vsign")
        elif any(k in name for k in ("ANUSVARA", "CANDRABINDU", "BINDI", "TIPPI")):
            kinds.append("nasal")
        elif "VIRAMA" in name or "HALANT" in name:
            kinds.append("virama")
        elif "NUKTA" in name:
            kinds.append("nukta")
        elif "ADDAK" in name:
            kinds.append("addak")
        elif "LETTER" in name and any(f"LETTER {v}" in name for v in (
                "A", "AA", "I", "II", "U", "UU", "E", "EE", "AI", "O", "OO", "AU", "VOCALIC")) \
                and name.split("LETTER ")[1].split()[0] in (
                "A", "AA", "I", "II", "U", "UU", "E", "EE", "AI", "O", "OO", "AU", "VOCALIC"):
            kinds.append("vowel")
        else:
            kinds.append("consonant")
    if kinds and kinds[0] in ("vsign", "nasal", "virama", "nukta"):
        return False
    for a, b in zip(kinds, kinds[1:]):
        if (a, b) in {("vsign", "vsign"), ("nasal", "nasal"), ("vsign", "virama"),
                      ("vsign", "nukta"), ("vowel", "vsign"), ("vowel", "virama"),
                      ("nasal", "vsign"), ("addak", "vsign"), ("vowel", "addak")}:
            return False
    if language == "Assamese" and "র" in word:   # Bengali ra in Assamese text
        return False
    return True


def evaluate(code: str, data: Path, show: int) -> dict:
    language = CODES[code]
    s = phonetic.scheme(language)
    rows = load(code, data)
    native_ok = lambda w: all(c.isalpha() or unicodedata.category(c)[0] == "M" for c in w) \
        and not any(c.isascii() for c in w)
    rows = [r for r in rows if native_ok(r["native word"]) and r["english word"].isalpha()]
    words = sorted({unicodedata.normalize("NFC", r["native word"]) for r in rows})
    malformed = [w for w in words if not well_formed(w, language)]
    words = [w for w in words if well_formed(w, language)]
    untypable = []
    for w in words:
        latin = s.to_latin(w)
        if s.transliterate_text(latin) != w:
            untypable.append((w, latin, s.transliterate_text(latin)))
    # Words weigh as often as they occur (Wikipedia counts), which approximates typing
    # running text; the plain figures treat the test set's many rare words like common ones.
    words_list = suggest.wordlist(language)
    weight = (lambda w: words_list.count.get(w, 1)) if words_list else (lambda w: 1)
    score = Counter()
    for r in rows:
        want = unicodedata.normalize("NFC", r["native word"])
        typed, wt = r["english word"], weight(want)
        exact = s.transliterate(typed) == want
        options = suggest.suggestions(language, typed) if words_list else [s.transliterate(typed)]
        for name, ok in (("rules", exact), ("first", options[0] == want), ("top", want in options)):
            score[name] += ok
            score[name + "_w"] += ok * wt
        score["n"] += 1
        score["n_w"] += wt
    # Exact typing must keep working: the scheme's spelling of a word comes first even when
    # suggestions are on.
    bad = {u[0] for u in untypable}
    typeable = [w for w in words if w not in bad]
    overridden = [w for w in typeable if words_list
                  and suggest.suggestions(language, s.to_latin(w))[0] != w]
    pct = lambda a, b: f"{100 * a / max(1, b):5.1f}%"
    print(f"{language:10} coverage {pct(len(typeable), len(words))}  | rules only "
          f"{pct(score['rules'], score['n'])} ({pct(score['rules_w'], score['n_w'])} weighted)"
          f"  | with suggestions: first {pct(score['first'], score['n'])} "
          f"({pct(score['first_w'], score['n_w'])} w), top {suggest.LIMIT} "
          f"{pct(score['top'], score['n'])} ({pct(score['top_w'], score['n_w'])} w)"
          f"  | exact overridden {pct(len(overridden), len(typeable))} "
          f"({pct(sum(weight(w) for w in overridden), sum(weight(w) for w in typeable))} w)"
          f"  [{len(malformed)} misspelt skipped]", flush=True)
    for w, latin, back in untypable[:show]:
        print(f"   untypable  {w}  ->  {latin}  ->  {back}")
    return {"language": language, "untypable": untypable, "overridden": overridden,
            "score": score}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", required=True, help="cache folder for the downloaded data")
    parser.add_argument("--show", type=int, default=15, help="untypable words to list")
    parser.add_argument("codes", nargs="*", default=list(CODES))
    args = parser.parse_args()
    for code in args.codes:
        try:
            evaluate(code, Path(args.data), args.show)
        except KeyError:
            print(f"{CODES[code]:10} no test set in the data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
