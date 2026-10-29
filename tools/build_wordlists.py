"""Build data/wordlists/<code>.tsv.gz: each language's most frequent words, for typing
suggestions. Words are counted in that language's Wikipedia (the 2023-11-01 dump published
on Hugging Face as wikimedia/wikipedia) and kept only if they can be typed exactly with the
English-letter scheme. Each line is "word<TAB>loose keys<TAB>count<TAB>English letters",
most frequent first; a word can have more than one key, separated by "|".

Needs pyarrow (not an app dependency):  .venv\\Scripts\\pip install pyarrow
    .venv\\Scripts\\python tools\\build_wordlists.py --cache C:\\temp\\wiki [hin ben ...]

Word counts are cached in the cache folder, so after a change to the typing scheme the
lists rebuild in seconds.
"""

import argparse
import gzip
import json
import sys
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from recorder import config  # noqa: E402
from recorder.typing import phonetic, suggest  # noqa: E402

DUMP = "20231101"
URL = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/{}.{}/{}"
WIKI = {"hin": "hi", "ben": "bn", "asm": "as", "ory": "or", "guj": "gu", "pan": "pa",
        "tam": "ta", "tel": "te", "kan": "kn", "mal": "ml", "mar": "mr", "nep": "ne",
        "san": "sa", "kok": "gom", "mai": "mai"}
WORDS = 50000      # words kept per language
MIN_COUNT = 3      # seen at least this often


def shard(code: str, cache: Path) -> Path:
    """The first parquet file of the language's Wikipedia (enough for word frequencies)."""
    wiki = WIKI[code]
    api = f"https://huggingface.co/api/datasets/wikimedia/wikipedia/tree/main/{DUMP}.{wiki}"
    with urllib.request.urlopen(api) as r:
        name = sorted(f["path"].split("/")[-1] for f in json.load(r))[0]
    path = cache / f"{wiki}-{name}"
    if not path.exists():
        print(f"  downloading {wiki} {name} ...", flush=True)
        urllib.request.urlretrieve(URL.format(DUMP, wiki, name), path)
    return path


def count_words(code: str, cache: Path, prefix: str) -> Counter:
    """Word counts from the Wikipedia text, cached as <wiki>-counts.tsv."""
    cached = cache / f"{WIKI[code]}-counts.tsv"
    if cached.exists():
        counts = Counter()
        for line in cached.read_text(encoding="utf-8").splitlines():
            word, n = line.split("\t")
            counts[word] = int(n)
        return counts
    import pyarrow.parquet as pq
    counts = Counter()
    letter = lambda c: unicodedata.name(c, "").startswith(prefix) \
        and (c.isalpha() or unicodedata.category(c)[0] == "M")
    for batch in pq.read_table(shard(code, cache), columns=["text"]).to_batches(5000):
        for text in batch.column(0).to_pylist():
            word = []
            for ch in text + " ":
                if letter(ch):
                    word.append(ch)
                elif word:
                    counts[unicodedata.normalize("NFC", "".join(word))] += 1
                    word = []
    keep = [(w, n) for w, n in counts.most_common() if n >= MIN_COUNT]
    cached.write_text("".join(f"{w}\t{n}\n" for w, n in keep), encoding="utf-8")
    return Counter(dict(keep))


def build(code: str, cache: Path) -> None:
    language = next(n for n, c in config.LANGUAGES.items() if c == code)
    scheme = phonetic.scheme(language)
    prefix = config.SCRIPTS[scheme.script]["unicode"]
    print(f"{language} ({code})", flush=True)
    lines = []
    for word, n in count_words(code, cache, prefix).most_common():
        if n < MIN_COUNT or len(lines) >= WORDS:
            break
        latin = scheme.to_latin(word)
        if scheme.transliterate_text(latin) == word:    # typeable exactly: well spelt
            keys = "|".join(suggest.word_keys(latin, language))
            lines.append(f"{word}\t{keys}\t{n}\t{latin}")
    out = suggest.WORDLIST_DIR / f"{code}.tsv.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8", compresslevel=9) as f:
        f.write("\n".join(lines) + "\n")
    print(f"  {len(lines)} words -> {out.name} ({out.stat().st_size // 1024} KB)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache", required=True, help="folder for the downloaded Wikipedia files")
    parser.add_argument("codes", nargs="*", default=list(WIKI))
    args = parser.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    for code in args.codes:
        build(code, cache)
    return 0


if __name__ == "__main__":
    sys.exit(main())
