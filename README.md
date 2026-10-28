<p align="center">
  <img src="assets/swaralipi-logo.png" alt="Swaralipi" width="560">
</p>

# Swaralipi

*Swara* (voice) + *lipi* (script): an offline desktop app for recording speech together with
its transcript, to build **speech datasets for ASR and TTS**.

Contributors download this repo, record on their own computer, and send back **one zip per
speaker**. The project team merges all zips with one command. Nothing is uploaded and no
server is needed.

---

## For contributors

### 1. Start the app

**Windows:** double-click **`run.bat`**.
**Linux / macOS:** run `./run.sh` (Linux also needs `sudo apt install libportaudio2`).

The first start creates a private Python environment (`.venv`) and installs the exact package
versions from `requirements.txt`. This needs internet **once**; after that everything works
offline. You need **Python 3.10 or newer** ([python.org](https://www.python.org/downloads/), tick
*"Add python.exe to PATH"*).

### 2. Record

1. **Choose mode**
   - *Record + write transcript*: type a sentence, press **OK**, then read it aloud.
     Use **Edit transcript** to fix it.
   - *Record from a script file*: load an `.xlsx`/`.csv` with columns `sentence_no, sentence`
     (see [samples/sample_script.csv](samples/sample_script.csv)) and read the sentences one by one.
2. **Audio settings**: keep the recommended preset (48 kHz / 24-bit / mono WAV + a 16 kHz ASR
   copy). Click **Test microphone** and check the level.
3. **Consent**: the speaker reads and accepts the terms.
4. **Speaker details**: name, mobile and email are private. Everything else is anonymous.
5. **Record**: Start, speak, Stop, Listen, Submit. Each take gets an automatic quality check.

| Key | Action |
|---|---|
| Space | Start / stop recording |
| P | Listen |
| Enter | Submit |
| ← / → | Previous / next sentence (script mode) |
| Ctrl+Enter | OK (confirm typed transcript) |

**Built-in safeguards:**
- The microphone type is filled in from the selected input device; correct it if it is wrong.
- Bluetooth microphones trigger a warning. They record in a low-quality call mode, so use a
  wired headset or USB microphone where possible.
- If the sentences are written in a different script from the recording language (for
  example, an English script while the language is set to Odia), the app asks you to correct
  the language.
- If a typed sentence contains the speaker's name, mobile number or email, the app asks
  before accepting it.
- If a returning speaker's earlier recordings used a different audio format, the app offers
  to switch back so all of their recordings match.

**Tips for good recordings:** quiet room, fans off, mic 10–15 cm from the mouth. Wait half a
second after Start before speaking and pause half a second before Stop. Read exactly what is
written.

### 3. Send your recordings

Click **Finish session → Export zip** (or **Export submission** on the home screen). The zip is
saved in `<recordings folder>/submissions/`. Send it to the project team.

---

## Output format

```
recordings/<speaker_id>/
  audio/<sentence_id>.wav        master recording (e.g. 48 kHz / 24-bit / mono)
  audio_16k/<sentence_id>.wav    16 kHz / 16-bit / mono copy for ASR
  transcripts.xlsx               sentence_id | sentence
  manifest.csv / manifest.jsonl  one row per clip: text, paths, duration, audio format,
                                 anonymous speaker metadata, QC metrics
  speaker.json                   anonymous speaker profile
  consent.json                   consent records (version, text hash, timestamp)
  private/contact.enc            name / mobile / email / full PIN (encrypted) - never published
```

### IDs: unique without a server

```
Speaker ID:   eng_OD_KHO_M_1999_7f3a9c2e
              │   │  │   │ │    └ fingerprint: first 8 hex of SHA-256(name, birth year,
              │   │  │   │ │      gender, PIN, mobile). One-way, cannot be reversed.
              │   │  │   │ └ birth year
              │   │  │   └ gender (M / F / O / X)
              │   │  └ district code
              │   └ state code
              └ language (ISO 639-3)

Sentence ID:  <speaker_id>_S000123        script mode (sentence number from the script)
              <speaker_id>_F261028153012  typed mode (yymmddHHMMSS)
```

The same person entering the same details on any computer gets the same Speaker ID. Different
people practically never collide.

### Privacy

- Name, mobile, email and the full PIN code are **never** written to the dataset files. They
  are stored only in `private/`, encrypted when a public key is configured (see below).
- Dataset metadata keeps only the first 3 digits of the PIN code (a broad region), plus birth
  year, gender, district and the other anonymous fields.

---

## For the project team

### Before distributing (do once)

1. **Edit [config/app_config.json](config/app_config.json):** organisation name, project name,
   contact email for withdrawal requests, minimum age, and `locked_audio_preset`.
   `locked_audio_preset` fixes the audio format for every contributor so the dataset never
   mixes formats. It is set to `"ASR + TTS (recommended)"`. Use `"ASR only"` or `"TTS only"`
   instead, or `null` to let contributors choose.
2. **Review [config/consent.md](config/consent.md)** with your legal / ethics team. It is a
   template. Change `consent_version` whenever you change the text.
3. **Create the encryption key pair:**
   ```
   .venv\Scripts\python tools\generate_keys.py
   ```
   Ship `config/public_key.pem` with the app. Keep `keys/private_key.pem` **secret and backed
   up**. It is git-ignored; never share it. Without a public key, contact details are saved
   unencrypted in `private/contact.json`.

### Merge received zips

```
.venv\Scripts\python tools\merge_submissions.py <folder-with-zips> <output-folder> --private-key keys\private_key.pem
```

This verifies SHA-256 checksums and merges speakers who sent several zips. It writes a master
`transcripts.xlsx`, `manifest.csv/.jsonl`, `speakers.csv` and `merge_report.txt`. The report
flags damaged files, missing consent, the same person under different IDs, and repeated
sentences. Contact details go to `PRIVATE_contacts.xlsx`, which is **internal only: never
include it in a release.**

### Quality targets used by the automatic check

| Metric | Target |
|---|---|
| Peak level | −20 to −1 dBFS, no clipping |
| SNR | ≥ 25 dB (ASR), ≥ 35 dB (TTS) |
| Noise floor | below −45 dBFS (ideally below −60) |
| Silence before / after speech | 0.2–3 s |
| Clip length | 1–30 s |

### Environment

`requirements.txt` pins exact versions (tested with Python 3.10.11 on Windows 11). To recreate
the environment manually:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python app.py
```

The interface uses IBM Plex Sans and IBM Plex Mono, bundled in
[recorder/ui/fonts/](recorder/ui/fonts/) under the SIL Open Font License (see `OFL.txt` there).

District lists are in [data/india_locations.json](data/india_locations.json). The dropdowns are
editable, so newly created districts can be typed in.

---

## License

[MIT](LICENSE) © 2026 Diptiman Mohanta. The bundled IBM Plex fonts are under the SIL Open Font
License.
