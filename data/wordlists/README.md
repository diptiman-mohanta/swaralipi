# Word lists for typing suggestions

One file per language (`<ISO 639-3 code>.tsv.gz`): the 50,000 most frequent words of that
language's Wikipedia that can be typed exactly with Swaralipi's English-letter scheme. Each
line is

    word <TAB> loose keys <TAB> count <TAB> English letters

The loose keys (separated by `|`) are what casual spellings are matched against; see
`recorder/typing/suggest.py`. Rebuild with `tools/build_wordlists.py` after changing the
typing scheme (a test fails if a list no longer matches the engine).

**Source and licence.** Word counts come from the text of the Wikipedias in Assamese,
Bengali, Gujarati, Hindi, Kannada, Konkani (Goan), Maithili, Malayalam, Marathi, Nepali,
Odia, Punjabi, Sanskrit, Tamil and Telugu, as published in the `wikimedia/wikipedia`
dataset (dump of 1 November 2023). Wikipedia text is available under the
[Creative Commons Attribution-ShareAlike 4.0 licence](https://creativecommons.org/licenses/by-sa/4.0/);
these derived word lists are shared under the same licence, with thanks to the Wikipedia
contributors. The rest of Swaralipi is MIT-licensed.

Bodo and Dogri have no Wikipedia edition in that dataset, so they have no word list and
use the typing rules only.
