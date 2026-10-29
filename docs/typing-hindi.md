# Typing Hindi with English letters

In **Type a sentence, then read it aloud** mode with Hindi as the recording language, type
how a word sounds in English letters and it appears in Devanagari as you type:

```
mera naam raam hai.    →   मेरा नाम राम है।
aap kaise hain?        →   आप कैसे हैं?
```

Space, punctuation or Enter finishes the word. **Backspace** while typing a word removes
the last English letter, not the whole Hindi letter. **Ctrl+Space** switches between Hindi
and English letters, for English words or brand names.

## You do not have to be exact: word suggestions

Under the text box, the word you are typing is shown with up to five real Hindi words that
match it, best first: `pani` offers पानी, `kitab` किताब, `ladka` लड़का, `karna` करना.

```
mujhe pani chahiye.    →   मुझे पानी चाहिए।
```

**Space** takes the first suggestion, a **number key** (1–5) picks another, **Tab** steps
through them and **Esc** keeps exactly what the rules below give. If you type the scheme on
purpose (capitals such as `T` or `Dh`, `^`, `_`, or long vowels spelt out as `aa` `ii` `uu`),
your exact spelling comes first. The suggestions use the 50,000 most frequent words of Hindi
Wikipedia, stored on this computer. Turn them off with the **Suggestions** button.

The same typing works for the other Devanagari languages (Marathi, Nepali, Sanskrit,
Konkani, Maithili, Dogri and Bodo). For those it is in beta: check the result as you type.
Bengali, Assamese, Odia, Gujarati, Punjabi, Tamil, Telugu, Kannada and Malayalam (and Bodo's
own vowels) are in [typing-indian-languages.md](typing-indian-languages.md).

## Small and capital letters matter

| Type | Get | | Type | Get |
|---|---|---|---|---|
| `t` | त | | `T` | ट |
| `d` | द | | `D` | ड |
| `n` | न | | `N` | ण |
| `sh` | श | | `Sh` | ष |
| `a` | अ / (inherent a) | | `aa` or `A` | आ ा |

A capital at the **start** of a word is read as small letters, so sentence case like `Mera`
still gives मेरा. Retroflex letters (`T`, `D`, `Th`, `Dh`, `Sh`) keep their meaning there.

## Vowels

| Type | Letter | Sign | | Type | Letter | Sign |
|---|---|---|---|---|---|---|
| `a` | अ | | | `e` | ए | े |
| `aa` / `A` | आ | ा | | `ai` | ऐ | ै |
| `i` | इ | ि | | `o` | ओ | ो |
| `ii` / `ee` | ई | ी | | `au` | औ | ौ |
| `u` | उ | ु | | `O` | ऑ | ॉ (डॉक्टर: `DOkTar`) |
| `uu` / `oo` | ऊ | ू | | `RRi` | ऋ | ृ (कृपया: `kRRipayaa`) |

## Consonants

| | | | | | |
|---|---|---|---|---|---|
| `k` क | `kh` ख | `g` ग | `gh` घ | `~N` ङ | |
| `ch` च | `chh` छ | `j` ज | `jh` झ | `~n` ञ | |
| `T` ट | `Th` ठ | `D` ड | `Dh` ढ | `N` ण | |
| `t` त | `th` थ | `d` द | `dh` ध | `n` न | |
| `p` प | `ph` फ | `b` ब | `bh` भ | `m` म | |
| `y` य | `r` र | `l` ल | `v` / `w` व | `L` ळ | |
| `sh` श | `Sh` ष | `s` स | `h` ह | | |
| `x` / `ksh` क्ष | `GY` ज्ञ | `cch` च्छ | `shr` श्र | `tr` त्र | |

**Dot letters (nukta):** `z` ज़, `f` फ़, `q` क़, `K` ख़, `G` ग़, `R` ड़, `Rh` ढ़

## Marks

| Type | Get | Example |
|---|---|---|
| `M` | ं anusvara | `hiMdii` → हिंदी |
| `MM` | ँ chandrabindu | `haaMM` → हाँ |
| `H` | ः visarga | `duHkh` → दुःख |
| `OM` | ॐ | |
| `.` | । full stop | `||` → ॥ |
| `^` | ् halant | `vidvaan^` → विद्वान् |
| `_` | keeps letters apart | `na_ii` → नई, `k_h` → कह |

## How the rules work

- **Consonants join automatically:** `st` → स्त, `kya` → क्या, `shrii` → श्री.
- **A word ending in a consonant keeps its short a:** `kamal` → कमल.
- **A final single `a` is long:** `mera` → मेरा, `kya` → क्या. Words like अन्य, सत्य and
  कार्य keep the short a (`anya`, `satya`, `kaarya`).
- **n before a consonant becomes anusvara**, as in standard Hindi spelling:
  `hindii` → हिंदी, `gangaa` → गंगा. **m** does so only before p ph b bh (`sambandh` →
  संबंध); elsewhere it stays a letter (`tumko` → तुम्को; type `tumako` for तुमको). Type `^`
  to keep the half letter instead: `hin^dii` → हिन्दी. Before य र ल व ह न म the letter
  stays: `anya` → अन्य, `janm` → जन्म.
- **ड़ and ढ़ never join:** `laRkaa` → लड़का, `paRhnaa` → पढ़ना.
- **Common words with nasal endings are recognised:** `main` → मैं, `hain` → हैं,
  `nahin` → नहीं, `kyon` → क्यों, `hoon` → हूँ, `yahaan` → यहाँ, `gaon` → गाँव.

## Letter keys

Click **Letter keys** to show every Hindi letter, vowel sign and digit as buttons. Click a
consonant, then a vowel sign (shown on a dotted circle, ◌ि) to build a syllable. Letter keys
are available for all 22 scheduled languages.

## Prefer a Windows keyboard?

Switch to **English letters** and use any Windows input method, such as Microsoft's Hindi
Phonetic keyboard or Google Input Tools. Text typed in Devanagari is passed through
unchanged.
