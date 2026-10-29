"""Compare Swaralipi's English-letter typing with Wikimedia's input methods (jquery.ime).

For every word of the typing test texts, the English letters Swaralipi needs are typed key
by key into the Wikimedia input method for the same language, and the two results are
compared. Wikimedia's rule files are GPL-licensed, so they are downloaded into a temporary
folder when the tool runs and are never stored in this project. Needs Node.js and internet.

    .venv\\Scripts\\python tools\\compare_wikimedia.py [--report docs\\typing-comparison.md]
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from recorder.script_loader import load_script  # noqa: E402
from recorder.typing import phonetic  # noqa: E402

RULES_URL = "https://raw.githubusercontent.com/wikimedia/jquery.ime/master/rules/{}.js"
# language -> Wikimedia input method (Assamese has none that works key by key: its Avro
# rules depend on a context that is always empty).
METHODS = {
    "Hindi": "hi/hi-transliteration", "Bengali": "bn/bn-avro", "Odia": "or/or-transliteration",
    "Gujarati": "gu/gu-transliteration", "Punjabi": "pa/pa-transliteration",
    "Tamil": "ta/ta-transliteration", "Telugu": "te/te-transliteration",
    "Kannada": "kn/kn-transliteration", "Malayalam": "ml/ml-transliteration",
}

# Types each word on stdin key by key, the way jquery.ime.js handles a key press.
HARNESS = r"""
const fs = require('fs'), vm = require('vm');
let im = null;
const $ = { ime: { register: (m) => { im = m; } } };
vm.runInNewContext(fs.readFileSync(process.argv[2], 'utf8'), { jQuery: $, $: $ });
function transliterate(input, context) {
  for (const rule of im.patterns) {
    const regex = new RegExp(rule[0] + '$');
    if (!regex.test(input)) continue;
    if (rule.length === 3 && !new RegExp(rule[1] + '$').test(context)) continue;
    return { noop: false, output: input.replace(regex, rule[rule.length - 1]) };
  }
  return { noop: true, output: input };
}
function type(word) {
  let text = '', context = '';
  for (const c of word) {
    const before = text.slice(Math.max(0, text.length - im.maxKeyLength));
    const r = transliterate(before + c, context);
    context += c;
    if (context.length > im.contextLength) context = context.slice(context.length - im.contextLength);
    text = r.noop ? text + c : text.slice(0, text.length - before.length) + r.output;
  }
  return text.normalize('NFC');
}
const words = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(words.map(type)));
"""


def sample_words(language: str) -> list[str]:
    if language == "Hindi":
        texts = [t for _, t in load_script(ROOT / "samples" / "demo_script_hindi.csv")]
    else:
        path = ROOT / "tests" / "data" / "typing" / f"{language.lower()}.txt"
        texts = path.read_text(encoding="utf-8").split()
    words = set()
    for chunk in " ".join(texts).split():
        word = "".join(c for c in chunk if c.isalpha() or unicodedata.category(c)[0] == "M")
        if word:
            words.add(word)
    words |= {w for _, w in phonetic.EXAMPLES.get(language, [])}
    return sorted(words)


def run_node(rules: Path, words: list[str]) -> list[str]:
    harness = rules.parent / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    result = subprocess.run(["node", str(harness), str(rules)], input=json.dumps(words),
                            capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(result.stdout)


def compare(language: str, tmp: Path) -> dict:
    rules = tmp / (METHODS[language].split("/")[1] + ".js")
    if not rules.exists():
        urllib.request.urlretrieve(RULES_URL.format(METHODS[language]), rules)
    scheme = phonetic.scheme(language)
    words = sample_words(language)
    # Swaralipi accepts n or M for a nasal before a consonant (hindii, hiMdii); Wikimedia's
    # schemes mostly need M, and the inherent a typed at the end of a word ("kamala").
    ours = [scheme.to_latin(w) for w in words]
    strict = [scheme.to_latin(w, plain_nasals=False) for w in words]
    tries = [run_node(rules, ours), run_node(rules, strict),
             run_node(rules, [latin + "a" for latin in ours]),
             run_node(rules, [latin + "a" for latin in strict])]
    rows, counts = [], Counter()
    for k, (word, latin) in enumerate(zip(words, ours)):
        word = unicodedata.normalize("NFC", word)
        results = [t[k] for t in tries]
        if word in results[:2]:
            counts["same"] += 1
        elif word in results[2:]:
            counts["same with final a"] += 1
        else:
            counts["different"] += 1
            rows.append((word, latin, results[0]))
    return {"words": len(words), "counts": counts, "differences": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", help="also write a Markdown report to this file")
    parser.add_argument("languages", nargs="*", default=list(METHODS))
    args = parser.parse_args()
    if not shutil.which("node"):
        print("Node.js is needed to run Wikimedia's input methods: https://nodejs.org")
        return 1
    lines = ["# Swaralipi typing compared with Wikimedia input methods", "",
             "Each word is typed with Swaralipi's English letters into the Wikimedia input "
             "method for the language (with n or M for a nasal before a consonant, both of "
             "which Swaralipi accepts). *Same with final a*: Wikimedia needs the inherent a "
             "typed at the end of the word, Swaralipi does not.", "",
             "| Language | Wikimedia method | Words | Same | Same with final a | Different |",
             "|---|---|---|---|---|---|"]
    details = []
    with tempfile.TemporaryDirectory() as tmp:
        for language in args.languages:
            r = compare(language, Path(tmp))
            c = r["counts"]
            same = c["same"] + c["same with final a"]
            print(f"{language:10} {same:4}/{r['words']:<4} agree "
                  f"({c['same']} as typed, {c['same with final a']} with final a)")
            lines.append(f"| {language} | {METHODS[language].split('/')[1]} | {r['words']} | "
                         f"{c['same']} | {c['same with final a']} | {c['different']} |")
            if r["differences"]:
                details += ["", f"## {language}", "", "| Word | Swaralipi keys | Wikimedia gives |",
                            "|---|---|---|"]
                details += [f"| {w} | `{latin}` | {out} |" for w, latin, out in r["differences"]]
    if args.report:
        Path(args.report).write_text("\n".join(lines + details) + "\n", encoding="utf-8")
        print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
