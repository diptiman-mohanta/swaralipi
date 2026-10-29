"""Write docs/typing-indian-languages.md from the typing engine itself, so the guide always
matches what the app does.

    .venv\\Scripts\\python tools\\make_typing_docs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from recorder import config  # noqa: E402
from recorder.typing import phonetic  # noqa: E402

OUT = ROOT / "docs" / "typing-indian-languages.md"
LANGUAGES = ["Bengali", "Assamese", "Odia", "Gujarati", "Punjabi", "Tamil", "Telugu",
             "Kannada", "Malayalam", "Bodo"]

# What a speaker of each language should know beyond the shared scheme.
NOTES = {
    "Bengali": [
        "`a` is the inherent vowel and `o` is always ো / ও: type `jal` for জল and `bhaalo` "
        "for ভালো. (This differs from Avro, where `a` is া.)",
        "`y` after a vowel is য় (`samay` সময়); at the start of a word or after a consonant "
        "it is য (`yadi` যদি, `byakti` ব্যক্তি). `z` is always য.",
        "`ng` at the end of a word or before a consonant is ং (`rang` রং, `baanglaa` বাংলা); "
        "`Ng` is ঙ.",
        "n before k, ch, T, t is written as a joined letter: `antar` অন্তর, `panch` পঞ্চ.",
        "`t^` is khanda ta: `ut^sab` উৎসব.",
    ],
    "Assamese": [
        "As Bengali, with Assamese letters: `r` is ৰ and `v` / `w` is ৱ (`guvaahaaTii` "
        "গুৱাহাটী).",
        "`y` after a vowel is য় (`samay` সময়); at the start or after a consonant it is য.",
    ],
    "Odia": [
        "A final `a` stays short: `bhaarata` and `bhaarat` both give ଭାରତ; type `aa` for ା.",
        "`L` is ଳ (`kamaLa` କମଳ), `R` is ଡ଼ (`oRishaa` ଓଡ଼ିଶା).",
        "`y` is ୟ (`samaya` ସମୟ, `dhanyabaada` ଧନ୍ୟବାଦ); at the start of a word it is ଯ "
        "(`yaa` ଯା). `w` is ୱ, `v` is ବ.",
        "n before k, ch, T, t is written as a joined letter: `chandra` ଚନ୍ଦ୍ର.",
    ],
    "Gujarati": [
        "n before a consonant is anusvara, as in everyday spelling: `gangaa` ગંગા.",
        "`L` is ળ (`kaaLu` કાળુ); `z` is ઝ.",
    ],
    "Punjabi": [
        "Doubled consonants get addak: `pakkaa` ਪੱਕਾ, `akkh` ਅੱਖ.",
        "n or m before a consonant becomes tippi or bindi as the vowel needs: `panjaab` ਪੰਜਾਬ, "
        "`maaM` ਮਾਂ, `dhannvaad` ਧੰਨਵਾਦ.",
        "Only ਰ and ਹ are written below a letter (`prem` ਪ੍ਰੇਮ, `unhaaM` ਉਨ੍ਹਾਂ); other "
        "clusters are plain letters (`dost` ਦੋਸਤ).",
        "`sh` is ਸ਼, `z` ਜ਼, `f` ਫ਼, `K` ਖ਼, `G` ਗ਼, `R` ੜ, `L` ਲ਼.",
    ],
    "Tamil": [
        "Tamil has one letter for k/g, ch/s, T/D, t/d (dental), p/b: `t` or `d` is ட, `th` "
        "or `dh` is த, `s` or `ch` is ச.",
        "`n` is ன, but ந at the start of a word or before த (`naan` நான், `vandhaan` "
        "வந்தான்); `w` is ந anywhere. `N` is ண.",
        "`zh` is ழ, `L` is ள, `R` is ற, `S` is ஸ, `f` is ஃப.",
        "`e` and `o` are short (எ ஒ); `E` and `O` are long (ஏ ஓ). `ee` and `oo` are ஈ and ஊ.",
        "A consonant with no vowel gets a pulli: `naan` நான்.",
    ],
    "Telugu": [
        "`e` and `o` are short (ఎ ఒ); `E` and `O` are long (ఏ ఓ): `nEnu` నేను.",
        "A word ending in m is written with anusvara: `namaskaaram` నమస్కారం.",
        "A consonant with no vowel gets a halant: `bas` బస్.",
    ],
    "Kannada": [
        "`e` and `o` are short (ಎ ಒ); `E` and `O` are long (ಏ ಓ): `bEku` ಬೇಕು.",
        "n before a consonant is anusvara: `bengaLuuru` ಬೆಂಗಳೂರು.",
    ],
    "Malayalam": [
        "`t` is ട, `th` is ത, `thh` is ഥ; `nt` is ന്റ (`ente` എന്റെ) and `nth` is ന്ത.",
        "n, r, l, L, N without a vowel become chillu letters (`avan` അവൻ, `avar` അവർ, "
        "`avaLkk` അവൾക്ക്, `laisans` ലൈസൻസ്) except in the clusters written joined "
        "(ന്ത, ന്റ, ണ്ട, doubled letters, before യ); a final m is anusvara "
        "(`malayaaLam` മലയാളം). `nD` is ൻഡ, `ND` is ണ്ഡ.",
        "`au` is ൗ (`akkauNt` അക്കൗണ്ട്).",
        "`ng` is ങ്ങ (`ningaL` നിങ്ങൾ), `nj` is ഞ (`njaan` ഞാൻ).",
        "`sh` is ഷ, `S` is ശ (`Sari` ശരി), `zh` is ഴ, `R` is റ.",
        "`e` and `o` are short; `E` and `O` are long (`kEraLam` കേരളം).",
    ],
    "Bodo": [
        "Typed the way Bodo is written in English letters: `a` is ा (`khani` खानि), `o` "
        "is the inherent vowel (`mohon` महन), `w` is ो (`gwra` गोरा), `ai` is ाय and `ao` "
        "is ाव (`mechao` मेचाव). The consonants are as in Hindi.",
        "Bodo has no word list, so there are no word suggestions.",
    ],
}


def table(items, columns=3):
    rows = ["| " + " | ".join(["Type", "Get"] * columns) + " |",
            "|" + "---|" * (2 * columns)]
    for i in range(0, len(items), columns):
        chunk = items[i:i + columns] + [("", "")] * (columns - len(items[i:i + columns]))
        rows.append("| " + " | ".join(f"`{k}` | {v}" if k else " | " for k, v in chunk) + " |")
    return rows


def main() -> int:
    lines = [
        "# Typing Indian languages with English letters", "",
        "In **Type a sentence, then read it aloud** mode, type how a word sounds in English "
        "letters and it appears in the language's script as you type. It works offline, "
        "the same way for every language below; Hindi has its own guide in "
        "[typing-hindi.md](typing-hindi.md).", "",
        "The scheme is the ITRANS convention used across Indian-language computing (as in "
        "the [indic_transliteration](https://github.com/indic-transliteration/"
        "indic_transliteration_py) project's letter tables), with each language's own "
        "spelling rules. These languages are in **beta**: check the text as you type, and "
        "use the **Letter keys** for anything the scheme does not produce.", "",
        "Shared by every language:", "",
        "- Small and capital letters mean different sounds (`t` and `T`). A capital at the "
        "start of a word is read as small unless it has its own meaning.",
        "- `aa` or `A` for the long a, `ii` / `ee` / `I` for the long i, `uu` / `oo` / `U` "
        "for the long u.",
        "- `^` adds a halant where typing would not, `_` keeps two letters apart (`k_h`).",
        "- Space or punctuation finishes the word; **Backspace** edits the English letters "
        "of the word you are typing; **Ctrl+Space** switches to plain English letters.", "",
        "## Word suggestions", "",
        "You do not have to type the scheme exactly. While you type a word, up to five real "
        "words that match how it sounds appear under the text box, best first: `pani` "
        "offers पानी, `kitab` किताब, `bangla` বাংলা, `madurai` மதுரை. **Space** takes the "
        "first, a **number key** picks another, **Tab** steps through them and **Esc** keeps "
        "exactly what the scheme gives. The exact result is always one of the choices, and "
        "it comes first whenever you type the scheme on purpose (a capital inside the word, "
        "a meaningful capital first letter such as `Dh`, `^`, `_`, `~`, or a long vowel "
        "spelt out as `aa` `ii` `uu` when no listed word agrees with it). Turn suggestions "
        "off with the **Suggestions** button.", "",
        "The suggestions come from each language's 50,000 most frequent Wikipedia words, "
        "stored on this computer ([data/wordlists](../data/wordlists/README.md)); nothing "
        "is looked up online. Every language here has them except Bodo.", "",
        "## The languages", "",
        "| Language | Native | A final consonant | n before a consonant | Full stop |",
        "|---|---|---|---|---|",
    ]
    schwa = {"final_long": "keeps its a; a final `a` is long",
             "keep": "keeps its a; a final `a` stays short",
             "explicit": "gets a halant (type `a` to keep the vowel)"}
    nasal = {"anusvara": "anusvara", "homorganic": "joined nasal letter"}
    for name in LANGUAGES:
        s = phonetic.scheme(name)
        lines.append(f"| [{name}](#{name.lower()}) | {config.LANGUAGE_INFO[name]['native']} | "
                     f"{schwa[s.schwa]} | {nasal[s.nasal]} | {s.full_stop} |")
    for name in LANGUAGES:
        s = phonetic.scheme(name)
        sheet = dict(s.cheat_sheet())
        lines += ["", f"### {name}", ""]
        lines += [f"- {note}" for note in NOTES[name]]
        lines += ["", "**Examples**", ""] + table(sheet["Examples"], 2)
        lines += ["", "**Vowels**", ""] + table(sheet["Vowels"])
        lines += ["", "**Consonants**", ""] + table(sheet["Consonants"])
        lines += ["", "**Marks**", ""] + table(sheet["Marks"])
    lines += ["", "---", "",
              "Generated by `tools/make_typing_docs.py` from the typing engine. "
              "`tools/compare_wikimedia.py` compares the results with Wikimedia's input "
              "methods."]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
