# Typing Indian languages with English letters

In **Type a sentence, then read it aloud** mode, type how a word sounds in English letters and it appears in the language's script as you type. It works offline, the same way for every language below; Hindi has its own guide in [typing-hindi.md](typing-hindi.md).

The scheme is the ITRANS convention used across Indian-language computing (as in the [indic_transliteration](https://github.com/indic-transliteration/indic_transliteration_py) project's letter tables), with each language's own spelling rules. These languages are in **beta**: check the text as you type, and use the **Letter keys** for anything the scheme does not produce.

Shared by every language:

- Small and capital letters mean different sounds (`t` and `T`). A capital at the start of a word is read as small unless it has its own meaning.
- `aa` or `A` for the long a, `ii` / `ee` / `I` for the long i, `uu` / `oo` / `U` for the long u.
- `^` adds a halant where typing would not, `_` keeps two letters apart (`k_h`).
- Space or punctuation finishes the word; **Backspace** edits the English letters of the word you are typing; **Ctrl+Space** switches to plain English letters.

## Word suggestions

You do not have to type the scheme exactly. While you type a word, up to five real words that match how it sounds appear under the text box, best first: `pani` offers पानी, `kitab` किताब, `bangla` বাংলা, `madurai` மதுரை. **Space** takes the first, a **number key** picks another, **Tab** steps through them and **Esc** keeps exactly what the scheme gives. The exact result is always one of the choices, and it comes first whenever you type the scheme on purpose (a capital inside the word, a meaningful capital first letter such as `Dh`, `^`, `_`, `~`, or a long vowel spelt out as `aa` `ii` `uu` when no listed word agrees with it). Turn suggestions off with the **Suggestions** button.

The suggestions come from each language's 50,000 most frequent Wikipedia words, stored on this computer ([data/wordlists](../data/wordlists/README.md)); nothing is looked up online. Every language here has them except Bodo.

## The languages

| Language | Native | A final consonant | n before a consonant | Full stop |
|---|---|---|---|---|
| [Bengali](#bengali) | বাংলা | keeps its a; a final `a` is long | joined nasal letter | । |
| [Assamese](#assamese) | অসমীয়া | keeps its a; a final `a` is long | joined nasal letter | । |
| [Odia](#odia) | ଓଡ଼ିଆ | keeps its a; a final `a` stays short | joined nasal letter | । |
| [Gujarati](#gujarati) | ગુજરાતી | keeps its a; a final `a` is long | anusvara | . |
| [Punjabi](#punjabi) | ਪੰਜਾਬੀ | keeps its a; a final `a` is long | anusvara | । |
| [Tamil](#tamil) | தமிழ் | gets a halant (type `a` to keep the vowel) | joined nasal letter | . |
| [Telugu](#telugu) | తెలుగు | gets a halant (type `a` to keep the vowel) | anusvara | . |
| [Kannada](#kannada) | ಕನ್ನಡ | gets a halant (type `a` to keep the vowel) | anusvara | . |
| [Malayalam](#malayalam) | മലയാളം | gets a halant (type `a` to keep the vowel) | joined nasal letter | . |
| [Bodo](#bodo) | बड़ो | keeps its a; a final `a` is long | anusvara | । |

### Bengali

- `a` is the inherent vowel and `o` is always ো / ও: type `jal` for জল and `bhaalo` for ভালো. (This differs from Avro, where `a` is া.)
- `y` after a vowel is য় (`samay` সময়); at the start of a word or after a consonant it is য (`yadi` যদি, `byakti` ব্যক্তি). `z` is always য.
- `ng` at the end of a word or before a consonant is ং (`rang` রং, `baanglaa` বাংলা); `Ng` is ঙ.
- n before k, ch, T, t is written as a joined letter: `antar` অন্তর, `panch` পঞ্চ.
- `t^` is khanda ta: `ut^sab` উৎসব.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `aami` | আমি | `tumi` | তুমি |
| `bhaalo` | ভালো | `jal` | জল |
| `baanglaa` | বাংলা | `dhanyabaad` | ধন্যবাদ |
| `samay` | সময় | `yadi` | যদি |
| `byakti` | ব্যক্তি | `ut^sab` | উৎসব |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | অ | `aa / A` | আ া | `i` | ই ি |
| `ii / ee / I` | ঈ ী | `u` | উ ু | `uu / oo / U` | ঊ ূ |
| `RRi` | ঋ ৃ | `RRI` | ৠ ৄ | `e / E` | এ ে |
| `ai` | ঐ ৈ | `o / O` | ও ো | `au` | ঔ ৌ |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ক | `kh` | খ | `g` | গ |
| `gh` | ঘ | `~N / Ng` | ঙ | `ch / c` | চ |
| `chh / Ch` | ছ | `j` | জ | `jh` | ঝ |
| `~n` | ঞ | `T` | ট | `Th` | ঠ |
| `D` | ড | `Dh` | ঢ | `N` | ণ |
| `t` | ত | `th` | থ | `d` | দ |
| `dh` | ধ | `n` | ন | `b / w / v` | ব |
| `p` | প | `ph / f` | ফ | `bh` | ভ |
| `m` | ম | `y / Y` | য় | `r` | র |
| `l / L` | ল | `sh` | শ | `Sh / shh / S` | ষ |
| `s` | স | `h` | হ | `z` | য |
| `R` | ড় | `Rh` | ঢ় | `x / ksh` | ক্ষ |
| `GY` | জ্ঞ | `cch` | চ্ছ | `ngg` | ঙ্গ |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ং | `MM` | ◌ঁ | `H` | ◌ঃ |
| `ng` | ◌ং |  |  |  |  |

### Assamese

- As Bengali, with Assamese letters: `r` is ৰ and `v` / `w` is ৱ (`guvaahaaTii` গুৱাহাটী).
- `y` after a vowel is য় (`samay` সময়); at the start or after a consonant it is য.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `asam` | অসম | `maanuh` | মানুহ |
| `paanii` | পানী | `raati` | ৰাতি |
| `ghar` | ঘৰ | `kitaap` | কিতাপ |
| `aaji` | আজি | `dhanyabaad` | ধন্যবাদ |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | অ | `aa / A` | আ া | `i` | ই ি |
| `ii / ee / I` | ঈ ী | `u` | উ ু | `uu / oo / U` | ঊ ূ |
| `RRi` | ঋ ৃ | `RRI` | ৠ ৄ | `e / E` | এ ে |
| `ai` | ঐ ৈ | `o / O` | ও ো | `au` | ঔ ৌ |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ক | `kh` | খ | `g` | গ |
| `gh` | ঘ | `~N / Ng` | ঙ | `ch / c` | চ |
| `chh / Ch` | ছ | `j` | জ | `jh` | ঝ |
| `~n` | ঞ | `T` | ট | `Th` | ঠ |
| `D` | ড | `Dh` | ঢ | `N` | ণ |
| `t` | ত | `th` | থ | `d` | দ |
| `dh` | ধ | `n` | ন | `v / w` | ৱ |
| `p` | প | `ph / f` | ফ | `b` | ব |
| `bh` | ভ | `m` | ম | `y / Y` | য় |
| `r` | ৰ | `l / L` | ল | `sh` | শ |
| `Sh / shh / S` | ষ | `s` | স | `h` | হ |
| `z` | য | `R` | ড় | `Rh` | ঢ় |
| `x / ksh` | ক্ষ | `GY` | জ্ঞ | `cch` | চ্ছ |
| `ngg` | ঙ্গ |  |  |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ং | `MM` | ◌ঁ | `H` | ◌ঃ |
| `ng` | ◌ং |  |  |  |  |

### Odia

- A final `a` stays short: `bhaarata` and `bhaarat` both give ଭାରତ; type `aa` for ା.
- `L` is ଳ (`kamaLa` କମଳ), `R` is ଡ଼ (`oRishaa` ଓଡ଼ିଶା).
- `y` is ୟ (`samaya` ସମୟ, `dhanyabaada` ଧନ୍ୟବାଦ); at the start of a word it is ଯ (`yaa` ଯା). `w` is ୱ, `v` is ବ.
- n before k, ch, T, t is written as a joined letter: `chandra` ଚନ୍ଦ୍ର.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `oRishaa` | ଓଡ଼ିଶା | `bhaarata` | ଭାରତ |
| `jagannaatha` | ଜଗନ୍ନାଥ | `paaNi` | ପାଣି |
| `ghara` | ଘର | `pilaa` | ପିଲା |
| `dhanyabaada` | ଧନ୍ୟବାଦ | `samaya` | ସମୟ |
| `kaTak` | କଟକ |  |  |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | ଅ | `aa / A` | ଆ ା | `i` | ଇ ି |
| `ii / ee / I` | ଈ ୀ | `u` | ଉ ୁ | `uu / oo / U` | ଊ ୂ |
| `RRi` | ଋ ୃ | `RRI` | ୠ ୄ | `e / E` | ଏ େ |
| `ai` | ଐ ୈ | `o / O` | ଓ ୋ | `au` | ଔ ୌ |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | କ | `kh` | ଖ | `g` | ଗ |
| `gh` | ଘ | `~N` | ଙ | `ch / c` | ଚ |
| `chh / Ch` | ଛ | `j` | ଜ | `jh` | ଝ |
| `~n` | ଞ | `T` | ଟ | `Th` | ଠ |
| `D` | ଡ | `Dh` | ଢ | `N` | ଣ |
| `t` | ତ | `th` | ଥ | `d` | ଦ |
| `dh` | ଧ | `n` | ନ | `w` | ୱ |
| `p` | ପ | `ph / f` | ଫ | `b / v` | ବ |
| `bh` | ଭ | `m` | ମ | `y / Y` | ୟ |
| `r` | ର | `l` | ଲ | `L` | ଳ |
| `sh` | ଶ | `Sh / shh / S` | ଷ | `s` | ସ |
| `h` | ହ | `z` | ଯ | `R` | ଡ଼ |
| `Rh` | ଢ଼ | `x / ksh` | କ୍ଷ | `GY` | ଜ୍ଞ |
| `cch` | ଚ୍ଛ |  |  |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ଂ | `MM` | ◌ଁ | `H` | ◌ଃ |

### Gujarati

- n before a consonant is anusvara, as in everyday spelling: `gangaa` ગંગા.
- `L` is ળ (`kaaLu` કાળુ); `z` is ઝ.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `gujaraatii` | ગુજરાતી | `namaste` | નમસ્તે |
| `aabhaar` | આભાર | `paaNii` | પાણી |
| `ghar` | ઘર | `amadaavaad` | અમદાવાદ |
| `chho` | છો | `saaruM` | સારું |
| `hindii` | હિંદી |  |  |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | અ | `aa / A` | આ ા | `i` | ઇ િ |
| `ii / ee / I` | ઈ ી | `u` | ઉ ુ | `uu / oo / U` | ઊ ૂ |
| `RRi` | ઋ ૃ | `RRI` | ૠ ૄ | `e` | એ ે |
| `ai` | ઐ ૈ | `o` | ઓ ો | `au` | ઔ ૌ |
| `E` | ઍ ૅ | `O` | ઑ ૉ |  |  |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ક | `kh` | ખ | `g` | ગ |
| `gh` | ઘ | `~N` | ઙ | `ch / c` | ચ |
| `chh / Ch` | છ | `j` | જ | `jh / z` | ઝ |
| `~n` | ઞ | `T` | ટ | `Th` | ઠ |
| `D / R` | ડ | `Dh / Rh` | ઢ | `N` | ણ |
| `t` | ત | `th` | થ | `d` | દ |
| `dh` | ધ | `n` | ન | `v / w` | વ |
| `p` | પ | `ph / f` | ફ | `b` | બ |
| `bh` | ભ | `m` | મ | `y` | ય |
| `r` | ર | `l` | લ | `L` | ળ |
| `sh` | શ | `Sh / shh / S` | ષ | `s` | સ |
| `h` | હ | `x / ksh` | ક્ષ | `GY` | જ્ઞ |
| `cch` | ચ્છ |  |  |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ં | `MM` | ◌ઁ | `H` | ◌ઃ |
| `OM` | ૐ |  |  |  |  |

### Punjabi

- Doubled consonants get addak: `pakkaa` ਪੱਕਾ, `akkh` ਅੱਖ.
- n or m before a consonant becomes tippi or bindi as the vowel needs: `panjaab` ਪੰਜਾਬ, `maaM` ਮਾਂ, `dhannvaad` ਧੰਨਵਾਦ.
- Only ਰ and ਹ are written below a letter (`prem` ਪ੍ਰੇਮ, `unhaaM` ਉਨ੍ਹਾਂ); other clusters are plain letters (`dost` ਦੋਸਤ).
- `sh` is ਸ਼, `z` ਜ਼, `f` ਫ਼, `K` ਖ਼, `G` ਗ਼, `R` ੜ, `L` ਲ਼.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `panjaab` | ਪੰਜਾਬ | `panjaabii` | ਪੰਜਾਬੀ |
| `pakkaa` | ਪੱਕਾ | `dhannvaad` | ਧੰਨਵਾਦ |
| `srii` | ਸ੍ਰੀ | `ghar` | ਘਰ |
| `paaNii` | ਪਾਣੀ | `gurduaaraa` | ਗੁਰਦੁਆਰਾ |
| `paRhnaa` | ਪੜ੍ਹਨਾ | `acchaa` | ਅੱਛਾ |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | ਅ | `aa / A` | ਆ ਾ | `i` | ਇ ਿ |
| `ii / ee / I` | ਈ ੀ | `u` | ਉ ੁ | `uu / oo / U` | ਊ ੂ |
| `RRi` | ਰਿ ੍ਰਿ | `e` | ਏ ੇ | `ai` | ਐ ੈ |
| `o` | ਓ ੋ | `au` | ਔ ੌ |  |  |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ਕ | `kh` | ਖ | `g` | ਗ |
| `gh` | ਘ | `~N` | ਙ | `ch / c` | ਚ |
| `chh / Ch` | ਛ | `j` | ਜ | `jh` | ਝ |
| `~n` | ਞ | `T` | ਟ | `Th` | ਠ |
| `D` | ਡ | `Dh` | ਢ | `N` | ਣ |
| `t` | ਤ | `th` | ਥ | `d` | ਦ |
| `dh` | ਧ | `n` | ਨ | `v / w` | ਵ |
| `p` | ਪ | `ph` | ਫ | `b` | ਬ |
| `bh` | ਭ | `m` | ਮ | `y` | ਯ |
| `r` | ਰ | `l` | ਲ | `L` | ਲ਼ |
| `sh / shh / S` | ਸ਼ | `s` | ਸ | `h` | ਹ |
| `z` | ਜ਼ | `R` | ੜ | `Rh` | ੜ੍ਹ |
| `f` | ਫ਼ | `q` | ਕ਼ | `K` | ਖ਼ |
| `G` | ਗ਼ | `x / ksh` | ਕ੍ਸ਼ | `cch` | ਚ੍ਛ |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ਂ | `H` | ◌ਃ |  |  |

### Tamil

- Tamil has one letter for k/g, ch/s, T/D, t/d (dental), p/b: `t` or `d` is ட, `th` or `dh` is த, `s` or `ch` is ச.
- `n` is ன, but ந at the start of a word or before த (`naan` நான், `vandhaan` வந்தான்); `w` is ந anywhere. `N` is ண.
- `zh` is ழ, `L` is ள, `R` is ற, `S` is ஸ, `f` is ஃப.
- `e` and `o` are short (எ ஒ); `E` and `O` are long (ஏ ஓ). `ee` and `oo` are ஈ and ஊ.
- A consonant with no vowel gets a pulli: `naan` நான்.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `vaNakkam` | வணக்கம் | `thamizh` | தமிழ் |
| `nanRi` | நன்றி | `naan` | நான் |
| `ammaa` | அம்மா | `veedu` | வீடு |
| `anbu` | அன்பு | `chennai` | சென்னை |
| `thaNNiir` | தண்ணீர் | `Ezhu` | ஏழு |
| `sari` | சரி |  |  |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | அ | `aa / A` | ஆ ா | `i` | இ ி |
| `ii / ee / I` | ஈ ீ | `u` | உ ு | `uu / oo / U` | ஊ ூ |
| `e` | எ ெ | `ai` | ஐ ை | `o` | ஒ ொ |
| `au` | ஔ ௌ | `E` | ஏ ே | `O` | ஓ ோ |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k / g / kh` | க | `~N` | ங | `ch / c / s` | ச |
| `j / jh` | ஜ | `nj / ~n` | ஞ | `t / d / T` | ட |
| `N` | ண | `th / dh` | த | `n` | ன |
| `w` | ந | `p / b / ph` | ப | `m` | ம |
| `y` | ய | `r` | ர | `l` | ல |
| `v` | வ | `L` | ள | `sh / shh / Sh` | ஷ |
| `S` | ஸ | `h` | ஹ | `zh / z` | ழ |
| `R` | ற | `f` | ஃப | `x / ksh` | க்ஷ |
| `cch` | ச்ச |  |  |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `H` | ஃ | `OM` | ௐ |  |  |

### Telugu

- `e` and `o` are short (ఎ ఒ); `E` and `O` are long (ఏ ఓ): `nEnu` నేను.
- A word ending in m is written with anusvara: `namaskaaram` నమస్కారం.
- A consonant with no vowel gets a halant: `bas` బస్.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `telugu` | తెలుగు | `namaskaaram` | నమస్కారం |
| `amma` | అమ్మ | `nEnu` | నేను |
| `illu` | ఇల్లు | `baagunnaanu` | బాగున్నాను |
| `haidaraabaad` | హైదరాబాద్ | `telangaaNa` | తెలంగాణ |
| `dhanyavaadaalu` | ధన్యవాదాలు |  |  |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | అ | `aa / A` | ఆ ా | `i` | ఇ ి |
| `ii / ee / I` | ఈ ీ | `u` | ఉ ు | `uu / oo / U` | ఊ ూ |
| `RRi` | ఋ ృ | `RRI` | ౠ ౄ | `e` | ఎ ె |
| `ai` | ఐ ై | `o` | ఒ ొ | `au` | ఔ ౌ |
| `E` | ఏ ే | `O` | ఓ ో |  |  |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | క | `kh` | ఖ | `g` | గ |
| `gh` | ఘ | `~N` | ఙ | `ch / c` | చ |
| `chh / Ch` | ఛ | `j / z` | జ | `jh` | ఝ |
| `~n` | ఞ | `T` | ట | `Th` | ఠ |
| `D` | డ | `Dh / Rh` | ఢ | `N` | ణ |
| `t` | త | `th` | థ | `d` | ద |
| `dh` | ధ | `n` | న | `v / w` | వ |
| `p` | ప | `ph / f` | ఫ | `b` | బ |
| `bh` | భ | `m` | మ | `y` | య |
| `r` | ర | `l` | ల | `L` | ళ |
| `sh` | శ | `Sh / shh / S` | ష | `s` | స |
| `h` | హ | `R` | ఱ | `x / ksh` | క్ష |
| `GY` | జ్ఞ | `cch` | చ్ఛ |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ం | `MM` | ◌ఁ | `H` | ◌ః |

### Kannada

- `e` and `o` are short (ಎ ಒ); `E` and `O` are long (ಏ ಓ): `bEku` ಬೇಕು.
- n before a consonant is anusvara: `bengaLuuru` ಬೆಂಗಳೂರು.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `kannaDa` | ಕನ್ನಡ | `namaskaara` | ನಮಸ್ಕಾರ |
| `bengaLuuru` | ಬೆಂಗಳೂರು | `mane` | ಮನೆ |
| `niiru` | ನೀರು | `ondu` | ಒಂದು |
| `huDuga` | ಹುಡುಗ | `dhanyavaadagaLu` | ಧನ್ಯವಾದಗಳು |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | ಅ | `aa / A` | ಆ ಾ | `i` | ಇ ಿ |
| `ii / ee / I` | ಈ ೀ | `u` | ಉ ು | `uu / oo / U` | ಊ ೂ |
| `RRi` | ಋ ೃ | `RRI` | ೠ ೄ | `e` | ಎ ೆ |
| `ai` | ಐ ೈ | `o` | ಒ ೊ | `au` | ಔ ೌ |
| `E` | ಏ ೇ | `O` | ಓ ೋ |  |  |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ಕ | `kh` | ಖ | `g` | ಗ |
| `gh` | ಘ | `~N` | ಙ | `ch / c` | ಚ |
| `chh / Ch` | ಛ | `j / z` | ಜ | `jh` | ಝ |
| `~n` | ಞ | `T` | ಟ | `Th` | ಠ |
| `D` | ಡ | `Dh / Rh` | ಢ | `N` | ಣ |
| `t` | ತ | `th` | ಥ | `d` | ದ |
| `dh` | ಧ | `n` | ನ | `v / w` | ವ |
| `p` | ಪ | `ph / f` | ಫ | `b` | ಬ |
| `bh` | ಭ | `m` | ಮ | `y` | ಯ |
| `r` | ರ | `l` | ಲ | `L` | ಳ |
| `sh` | ಶ | `Sh / shh / S` | ಷ | `s` | ಸ |
| `h` | ಹ | `R` | ಱ | `x / ksh` | ಕ್ಷ |
| `GY` | ಜ್ಞ | `cch` | ಚ್ಛ |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ಂ | `MM` | ◌ಁ | `H` | ◌ಃ |

### Malayalam

- `t` is ട, `th` is ത, `thh` is ഥ; `nt` is ന്റ (`ente` എന്റെ) and `nth` is ന്ത.
- n, r, l, L, N without a vowel become chillu letters (`avan` അവൻ, `avar` അവർ, `avaLkk` അവൾക്ക്, `laisans` ലൈസൻസ്) except in the clusters written joined (ന്ത, ന്റ, ണ്ട, doubled letters, before യ); a final m is anusvara (`malayaaLam` മലയാളം). `nD` is ൻഡ, `ND` is ണ്ഡ.
- `au` is ൗ (`akkauNt` അക്കൗണ്ട്).
- `ng` is ങ്ങ (`ningaL` നിങ്ങൾ), `nj` is ഞ (`njaan` ഞാൻ).
- `sh` is ഷ, `S` is ശ (`Sari` ശരി), `zh` is ഴ, `R` is റ.
- `e` and `o` are short; `E` and `O` are long (`kEraLam` കേരളം).

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `malayaaLam` | മലയാളം | `kEraLam` | കേരളം |
| `ente` | എന്റെ | `njaan` | ഞാൻ |
| `amma` | അമ്മ | `kutti` | കുട്ടി |
| `avaL` | അവൾ | `avar` | അവർ |
| `ningaL` | നിങ്ങൾ | `santhOsham` | സന്തോഷം |
| `thiruvananthapuram` | തിരുവനന്തപുരം |  |  |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a` | അ | `aa / A` | ആ ാ | `i` | ഇ ി |
| `ii / ee / I` | ഈ ീ | `u` | ഉ ു | `uu / oo / U` | ഊ ൂ |
| `RRi` | ഋ ൃ | `RRI` | ൠ ൄ | `e` | എ െ |
| `ai` | ഐ ൈ | `o` | ഒ ൊ | `au` | ഔ ൗ |
| `E` | ഏ േ | `O` | ഓ ോ |  |  |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | ക | `kh` | ഖ | `g` | ഗ |
| `gh` | ഘ | `~N` | ങ | `ng` | ങ്ങ |
| `ch / c` | ച | `chh / Ch` | ഛ | `j` | ജ |
| `jh` | ഝ | `nj / ~n` | ഞ | `t / T` | ട |
| `Th` | ഠ | `D` | ഡ | `Dh` | ഢ |
| `N` | ണ | `th` | ത | `thh` | ഥ |
| `d` | ദ | `dh` | ധ | `n` | ന |
| `v / w` | വ | `p` | പ | `ph / f` | ഫ |
| `b` | ബ | `bh` | ഭ | `m` | മ |
| `y` | യ | `r` | ര | `l` | ല |
| `L` | ള | `sh / shh / Sh` | ഷ | `s` | സ |
| `S / z` | ശ | `h` | ഹ | `zh` | ഴ |
| `R` | റ | `x / ksh` | ക്ഷ | `GY` | ജ്ഞ |
| `cch` | ച്ഛ | `nt` | ന്റ | `nth` | ന്ത |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ം | `MM` | ◌ഁ | `H` | ◌ഃ |

### Bodo

- Typed the way Bodo is written in English letters: `a` is ा (`khani` खानि), `o` is the inherent vowel (`mohon` महन), `w` is ो (`gwra` गोरा), `ai` is ाय and `ao` is ाव (`mechao` मेचाव). The consonants are as in Hindi.
- Bodo has no word list, so there are no word suggestions.

**Examples**

| Type | Get | Type | Get |
|---|---|---|---|
| `gwra` | गोरा | `mechao` | मेचाव |
| `khani` | खानि | `mohon` | महन |
| `jadugwr` | जादुगोर | `gaisongiri` | गायसंगिरि |
| `halamao` | हालामाव | `aadorsh` | आदर्श |

**Vowels**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `a / aa / A` | आ ा | `i` | इ ि | `ii / ee / I` | ई ी |
| `u` | उ ु | `uu / oo / U` | ऊ ू | `RRi` | ऋ ृ |
| `RRI` | ॠ ॄ | `e` | ए े | `ai` | आय ाय |
| `o` | अ | `au / ou` | औ ौ | `E` | ऍ ॅ |
| `O` | ऑ ॉ | `w` | ओ ो | `ao` | आव ाव |

**Consonants**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `k` | क | `kh` | ख | `g` | ग |
| `gh` | घ | `~N` | ङ | `ch / c` | च |
| `chh / Ch` | छ | `j` | ज | `jh` | झ |
| `~n` | ञ | `T` | ट | `Th` | ठ |
| `D` | ड | `Dh` | ढ | `N` | ण |
| `t` | त | `th` | थ | `d` | द |
| `dh` | ध | `n` | न | `v / w` | व |
| `p` | प | `ph` | फ | `b` | ब |
| `bh` | भ | `m` | म | `y` | य |
| `r` | र | `l` | ल | `L` | ळ |
| `sh` | श | `Sh / shh / S` | ष | `s` | स |
| `h` | ह | `z` | ज़ | `R` | ड़ |
| `Rh` | ढ़ | `f` | फ़ | `q` | क़ |
| `K` | ख़ | `G` | ग़ | `x / ksh` | क्ष |
| `GY` | ज्ञ | `cch` | च्छ |  |  |

**Marks**

| Type | Get | Type | Get | Type | Get |
|---|---|---|---|---|---|
| `M` | ◌ं | `MM` | ◌ँ | `H` | ◌ः |
| `OM` | ॐ |  |  |  |  |

---

Generated by `tools/make_typing_docs.py` from the typing engine. `tools/compare_wikimedia.py` compares the results with Wikimedia's input methods.
