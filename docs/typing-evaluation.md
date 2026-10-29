# How well English-letter typing works

Measured with `tools/evaluate_typing.py` on AI4Bharat's
[Aksharantar](https://huggingface.co/datasets/ai4bharat/Aksharantar) test sets: real pairs of
a word and the way someone wrote it in English letters (foreign names left out). Run on
29 October 2026 with the word lists in [data/wordlists](../data/wordlists/README.md).

- **Can be typed**: share of the test words (spelling errors in the data set aside) that can be
  typed exactly with the scheme, checked by turning each word into English letters and back.
- **First choice**: how often the English spelling people actually used gives the right word
  as the first suggestion, which is what Space writes. *Weighted* counts each word as often as
  it occurs in Wikipedia, which is closer to typing ordinary sentences; the test sets are full
  of rare words.
- **Rules only**: the same, with suggestions turned off.
- **Exact typing changed**: how often typing a word exactly as the scheme spells it does
  *not* give that word first (mostly rare spellings corrected to the common one).

| Language | Can be typed | Rules only (weighted) | First choice (weighted) | In top 5 (weighted) | Exact typing changed (weighted) |
|---|---|---|---|---|---|
| Hindi | 99.9% | 40% | **83%** | 90% | 0.2% |
| Marathi | 99.8% | 17% | **78%** | 83% | 0.1% |
| Nepali | 100% | 27% | **78%** | 90% | 0.1% |
| Sanskrit | 100% | 27% | **52%** | 61% | 0.3% |
| Konkani | 100% | 49% | **84%** | 89% | 0.1% |
| Maithili | 100% | 40% | **92%** | 96% | 0.1% |
| Bodo | 100% | 15% | 15% (no word list) | 15% | 0% |
| Bengali | 99.9% | 13% | **65%** | 77% | 0.3% |
| Assamese | 100% | 23% | **68%** | 73% | 0.2% |
| Odia | 99.9% | 33% | **79%** | 88% | 0.1% |
| Gujarati | 100% | 23% | **68%** | 85% | 0.1% |
| Punjabi | 98.8% | 27% | **60%** | 77% | 0.4% |
| Tamil | 99.9% | 25% | **58%** | 69% | 0.2% |
| Telugu | 100% | 20% | **68%** | 70% | 0.2% |
| Kannada | 100% | 31% | **71%** | 78% | 0.4% |
| Malayalam | 98.3% | 17% | **55%** | 70% | 0.2% |

Dogri has no test set. What is left untypable is almost all non-standard spelling in the
data (a nukta on the wrong letter, Punjabi bindi where standard spelling has tippi, the old
Malayalam ൌ, the Bengali ra in Assamese words).

**What still goes wrong.** English words and names spelt the English way (`computer`,
`delhi`, `football`) rarely match their Indian-script spelling; the person picks from the
suggestions or uses the exact scheme. Sanskrit and Malayalam have long compound words that are
often not in the word lists.

**How the rules were chosen.** Script spelling (Punjabi tippi and bindi, Malayalam chillu
letters, the Malayalam au sign) follows what each language's Wikipedia actually writes, counted
word by word. Casual spelling habits (`kkh` for Bengali ক্ষ, `ndr` for Tamil ன்ற, `d` for
Malayalam ട, a dropped final nasal in Punjabi and Gujarati) come from the misses in this
evaluation. The ranking settings (`EXACT_BONUS`, `CLOSENESS_POWER` in
`recorder/typing/suggest.py`) were tuned on Hindi for the best first choice with the least
change to exact typing.

To rerun: `.venv\Scripts\python tools\evaluate_typing.py --data <folder for the download>`.
