"""Setup screens: welcome, mode, audio settings, consent, speaker details, export."""

import hashlib
import html
import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QCompleter, QDialog, QFileDialog, QFormLayout, QGridLayout,
    QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QScrollArea,
    QTextBrowser, QVBoxLayout, QWidget,
)

from .. import APP_VERSION, audio, config, crypto, ids
from ..audio import AudioSettings
from ..export import export_speaker
from ..storage import list_speakers, now_iso
from . import style
from .widgets import (LevelMeter, OptionButton, button, button_row, heading, label, rule,
                      section, set_invalid)

CURRENT_YEAR = datetime.now().year


def combo(items, editable=False, placeholder="Select") -> QComboBox:
    c = QComboBox()
    c.addItems(list(items))
    c.setEditable(editable)
    c.setMaxVisibleItems(14)
    if editable:
        c.lineEdit().setPlaceholderText(placeholder)
        c.setInsertPolicy(QComboBox.NoInsert)
        comp = QCompleter(list(items), c)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        c.setCompleter(comp)
    else:
        c.setPlaceholderText(placeholder)
    c.setCurrentIndex(-1)
    if editable:
        c.setEditText("")
    return c


def form() -> QFormLayout:
    f = QFormLayout()
    f.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    f.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    f.setHorizontalSpacing(16)
    f.setVerticalSpacing(10)
    f.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    return f


def align_forms(*forms: QFormLayout) -> None:
    """Gives stacked forms one shared label column so their fields line up."""
    labels = [f.itemAt(r, QFormLayout.LabelRole).widget() for f in forms
              for r in range(f.rowCount()) if f.itemAt(r, QFormLayout.LabelRole)]
    width = max((l.sizeHint().width() for l in labels if l), default=0)
    for l in labels:
        if l:
            l.setMinimumWidth(width)


def page_layout(widget: QWidget) -> QVBoxLayout:
    lay = QVBoxLayout(widget)
    lay.setContentsMargins(48, 32, 48, 28)
    lay.setSpacing(24)
    return lay


def scrolled(inner: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(inner)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return area


def fmt_duration(seconds: float) -> str:
    m = int(round(seconds / 60))
    return f"{m // 60} h {m % 60} min" if m >= 60 else f"{m} min"


# =================================================================== welcome
class WelcomePage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        cfg = app.app_config
        lay = QVBoxLayout(self)
        lay.setContentsMargins(64, 40, 64, 32)
        lay.setSpacing(0)

        lay.addWidget(label(f"{cfg['project_name']}  ·  {cfg['organisation_name']}", "Muted"))
        lay.addStretch(2)

        body = QVBoxLayout()
        body.setSpacing(16)
        title = label("Record people reading sentences aloud.", "Display", wrap=True)
        title.setMaximumWidth(760)
        body.addWidget(title)
        lede = label("Each recording is checked for volume and background noise before it is "
                     "saved. When a speaker has finished, export their recordings as one zip "
                     "file and send it to the project team. Nothing is uploaded from this "
                     "computer.", "Lede", wrap=True)
        lede.setMaximumWidth(620)
        body.addWidget(lede)
        body.addSpacing(12)
        start = button("Start a session", "Primary")
        start.setMinimumHeight(42)
        start.clicked.connect(app.go_mode)
        export = button("Export a speaker's recordings")
        export.setMinimumHeight(42)
        export.clicked.connect(app.open_export)
        body.addLayout(button_row(start, export, None, stretch_first=False))
        lay.addLayout(body)
        lay.addStretch(3)

        lay.addWidget(rule())
        lay.addSpacing(16)
        foot = QHBoxLayout()
        stats_col = QVBoxLayout()
        stats_col.setSpacing(4)
        stats_col.addWidget(label("On this computer", "Section"))
        self.stats = label("", "Muted")
        stats_col.addWidget(self.stats)
        self.folder = label("", "MonoMuted")
        self.folder.setTextInteractionFlags(Qt.TextSelectableByMouse)
        stats_col.addWidget(self.folder)
        foot.addLayout(stats_col, 1)
        foot.addWidget(label(f"Version {APP_VERSION}", "Note"), 0, Qt.AlignBottom)
        lay.addLayout(foot)

    def refresh(self):
        out = Path(self.app.session.audio.output_dir or config.DEFAULT_OUTPUT_DIR)
        speakers = list_speakers(out)
        if speakers:
            clips = sum(s["clips"] for s in speakers)
            secs = sum(s["seconds"] for s in speakers)
            n = len(speakers)
            self.stats.setText(f"{n} speaker{'s' * (n != 1)}, {clips} recordings, "
                               f"{fmt_duration(secs)} of audio")
        else:
            self.stats.setText("No recordings yet.")
        self.folder.setText(str(out))


# =================================================================== mode
class ModePage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        lay = page_layout(self)
        lay.addWidget(heading("How will this speaker record?",
                              "Both options save the audio and the transcript in the same "
                              "format, so they can be mixed in one dataset."))
        options = QVBoxLayout()
        options.setSpacing(0)
        typed = OptionButton("Type a sentence, then read it aloud",
                             "Type the sentence and confirm it, then record yourself reading "
                             "it. Use this when there is no prepared script.")
        script = OptionButton("Read sentences from a script file",
                              "Load an .xlsx or .csv file of numbered sentences. They are "
                              "shown one at a time, and the app keeps track of which ones are "
                              "already recorded.")
        for b, mode in ((typed, config.MODE_TYPED), (script, config.MODE_SCRIPT)):
            b.clicked.connect(lambda _=False, m=mode: app.set_mode(m))
            options.addWidget(b)
        options.addWidget(rule())
        options.setContentsMargins(0, 0, 0, 0)
        holder = QWidget()
        holder.setLayout(options)
        holder.setMaximumWidth(760)
        lay.addWidget(holder)
        lay.addStretch(1)
        back = button("Back")
        back.clicked.connect(app.go_welcome)
        lay.addLayout(button_row(back, None, stretch_first=False))


# =================================================================== audio settings
class AudioSettingsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._loading = False
        lay = page_layout(self)
        lay.addWidget(heading("Audio settings",
                              "Keep the recommended preset unless the project team asked for "
                              "something else. These settings are remembered on this "
                              "computer."))

        grid = QGridLayout()
        grid.setHorizontalSpacing(56)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # ---- format
        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(section("Format"))
        self.lock_note = label("The project team has fixed this format in "
                               "config/app_config.json, so every contributor records the same "
                               "way.", "Note", wrap=True)
        left.addWidget(self.lock_note)
        f = form()
        self.preset = combo(list(config.AUDIO_PRESETS) + [config.CUSTOM_PRESET])
        self.rate = combo([f"{r} Hz" for r in config.SAMPLE_RATES])
        self.depth = combo(config.BIT_DEPTHS)
        self.channels = combo(config.CHANNELS)
        self.fmt = combo(list(config.FILE_FORMATS) + config.LOSSY_FORMATS)
        for i in range(len(config.FILE_FORMATS), self.fmt.count()):
            self.fmt.model().item(i).setEnabled(False)
        self.asr_copy = QCheckBox("Also save a 16 kHz, 16-bit mono copy for ASR")
        f.addRow("Preset", self.preset)
        f.addRow("Sample rate", self.rate)
        f.addRow("Bit depth", self.depth)
        f.addRow("Channels", self.channels)
        f.addRow("File format", self.fmt)
        f.addRow("", self.asr_copy)
        left.addLayout(f)
        self.size_hint = label("", "MonoMuted")
        left.addWidget(self.size_hint)
        left.addWidget(label("Speech recognition (ASR) uses 16 kHz, 16-bit, mono. Speech "
                             "synthesis (TTS) uses 48 kHz, 24-bit, mono. The recommended "
                             "preset records for TTS and saves an ASR copy next to it.",
                             "Note", wrap=True))
        left.addStretch(1)

        # ---- microphone + storage
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(section("Microphone"))
        self.device = QComboBox()
        refresh = button("Refresh")
        refresh.clicked.connect(self.refresh_devices)
        drow = QHBoxLayout()
        drow.setSpacing(8)
        drow.addWidget(self.device, 1)
        drow.addWidget(refresh)
        right.addLayout(drow)
        self.device_note = label("", "Warning", wrap=True)
        self.device_note.hide()
        right.addWidget(self.device_note)
        self.device.currentIndexChanged.connect(self._update_device_note)
        self.test_btn = button("Test microphone")
        self.test_btn.setCheckable(True)
        self.test_btn.toggled.connect(self.toggle_test)
        right.addLayout(button_row(self.test_btn, None, stretch_first=False))
        self.meter = LevelMeter()
        right.addWidget(self.meter)
        right.addWidget(label("Speak at a normal volume. Peaks should land in the darker band "
                              "(-12 to -3 dBFS) and never reach 0.", "Note", wrap=True))
        right.addSpacing(18)
        right.addWidget(section("Save recordings in"))
        self.out_dir = QLineEdit()
        browse = button("Browse")
        browse.clicked.connect(self.browse)
        orow = QHBoxLayout()
        orow.setSpacing(8)
        orow.addWidget(self.out_dir, 1)
        orow.addWidget(browse)
        right.addLayout(orow)
        right.addStretch(1)

        grid.addLayout(left, 0, 0)
        grid.addLayout(right, 0, 1)
        lay.addLayout(grid, 1)

        back = button("Back")
        back.clicked.connect(self._back)
        nxt = button("Continue", "Primary")
        nxt.clicked.connect(self.save)
        lay.addLayout(button_row(back, None, nxt, stretch_first=False))

        self.preset.currentTextChanged.connect(self.apply_preset)
        for w in (self.rate, self.depth, self.channels, self.fmt):
            w.currentIndexChanged.connect(self.on_field_changed)
        self.asr_copy.toggled.connect(self.on_field_changed)

        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(lambda: self.meter.set_peak(self.app.recorder.read_peak()))

    # -------------------------------------------------------------- state
    def load(self, s: AudioSettings) -> None:
        self._loading = True
        self.refresh_devices(select=s.device_name)
        self.rate.setCurrentText(f"{s.sample_rate} Hz")
        self.depth.setCurrentText(s.bit_depth)
        self.channels.setCurrentIndex(list(config.CHANNELS.values()).index(s.channels))
        self.fmt.setCurrentText(s.file_format)
        self.asr_copy.setChecked(s.asr_copy)
        self.out_dir.setText(s.output_dir or str(config.DEFAULT_OUTPUT_DIR))
        self._loading = False
        self.preset.setCurrentText(s.preset if s.preset in config.AUDIO_PRESETS
                                   else self._matching_preset())
        self.on_field_changed()
        locked = bool(self.app.locked_preset)
        for w in (self.preset, self.rate, self.depth, self.channels, self.fmt, self.asr_copy):
            w.setEnabled(not locked)
        self.lock_note.setVisible(locked)
        self._update_device_note()

    def _update_device_note(self, *_):
        is_bt = audio.guess_mic_type(self.device.currentData() or "") == audio.BLUETOOTH
        self.device_note.setText("This looks like a Bluetooth device. Bluetooth microphones "
                                 "record in a low-quality call mode. Use a wired headset or a "
                                 "USB microphone if you can.")
        self.device_note.setVisible(is_bt)

    def current(self) -> AudioSettings:
        return AudioSettings(
            sample_rate=int(self.rate.currentText().split()[0]),
            bit_depth=self.depth.currentText(),
            channels=config.CHANNELS[self.channels.currentText()],
            file_format=self.fmt.currentText(),
            asr_copy=self.asr_copy.isChecked(),
            device_name=self.device.currentData() or "",
            output_dir=self.out_dir.text().strip(),
            preset=self.preset.currentText(),
        )

    def _matching_preset(self) -> str:
        s = self.current()
        for name, p in config.AUDIO_PRESETS.items():
            if all(getattr(s, k) == v for k, v in p.items()):
                return name
        return config.CUSTOM_PRESET

    def apply_preset(self, name: str) -> None:
        p = config.AUDIO_PRESETS.get(name)
        if not p or self._loading:
            return
        self._loading = True
        self.rate.setCurrentText(f"{p['sample_rate']} Hz")
        self.depth.setCurrentText(p["bit_depth"])
        self.channels.setCurrentIndex(list(config.CHANNELS.values()).index(p["channels"]))
        self.fmt.setCurrentText(p["file_format"])
        self.asr_copy.setChecked(p["asr_copy"])
        self._loading = False
        self.on_field_changed()

    def on_field_changed(self, *_):
        if self._loading:
            return
        self._loading = True
        self.preset.setCurrentText(self._matching_preset())
        self._loading = False
        s = self.current()
        if s.file_format == "FLAC" and s.subtype == "FLOAT":
            self.depth.setCurrentText("24-bit PCM")   # FLAC has no float format
            return
        self.size_hint.setText(f"About {s.bytes_per_minute() / 1e6:.1f} MB per minute of audio")
        if self.test_btn.isChecked():
            self.test_btn.setChecked(False)

    def refresh_devices(self, *_, select: str | None = None):
        previous = select if select is not None else (self.device.currentData() or "")
        self.device.clear()
        self.device.addItem("System default input", "")
        for name, _idx in audio.input_devices():
            self.device.addItem(name, name)
        i = self.device.findData(previous)
        self.device.setCurrentIndex(max(i, 0))

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Choose folder for recordings",
                                             self.out_dir.text())
        if d:
            self.out_dir.setText(d)

    def toggle_test(self, on: bool):
        if on:
            s = self.current()
            err = audio.check_settings(s)
            if err:
                QMessageBox.warning(self, "Microphone", "The microphone cannot record with "
                                    f"these settings.\n\n{err}")
                self.test_btn.setChecked(False)
                return
            try:
                self.app.recorder.start(s, keep=False)
            except Exception as e:
                QMessageBox.warning(self, "Microphone", f"The microphone could not be "
                                    f"started.\n\n{e}")
                self.test_btn.setChecked(False)
                return
            self.timer.start()
            self.test_btn.setText("Stop test")
        else:
            self.timer.stop()
            self.app.recorder.stop()
            self.meter.reset()
            self.test_btn.setText("Test microphone")

    def stop_test(self):
        if self.test_btn.isChecked():
            self.test_btn.setChecked(False)

    def _back(self):
        self.stop_test()
        self.app.go_mode()

    def save(self):
        self.stop_test()
        s = self.current()
        if not s.output_dir:
            QMessageBox.warning(self, "Audio settings", "Choose a folder to save recordings in.")
            return
        try:
            Path(s.output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.warning(self, "Audio settings", f"This folder cannot be used.\n\n{e}")
            return
        err = audio.check_settings(s)
        if err:
            QMessageBox.warning(self, "Audio settings",
                                "The selected microphone does not support these settings.\n\n"
                                f"{err}\n\nTry 'System default input' or another sample rate.")
            return
        if audio.guess_mic_type(s.device_name) == audio.BLUETOOTH:
            r = QMessageBox.question(
                self, "Bluetooth microphone",
                f"{audio.device_label(s.device_name)} looks like a Bluetooth device.\n\n"
                "While its microphone is in use, Bluetooth audio switches to a call mode that "
                "is usually limited to 8-16 kHz and compressed, which lowers the quality of the "
                "dataset (especially for TTS). A wired headset or USB microphone is much "
                "better.\n\nContinue with this device anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        self.app.audio_done(s)


# =================================================================== consent
def markdown_to_html(md: str) -> str:
    """Converts the small Markdown subset used in consent.md (headings, bullet lists,
    paragraphs, **bold**, *italic*, `code`, ---) to HTML with explicit sizes.
    Qt's own Markdown import ignores later font-size changes, so headings would render
    at body size."""
    def inline(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
        return re.sub(r"`(.+?)`", rf"<span style='font-family:\"{style.MONO}\"'>\1</span>", t)

    body = f"font-size:{style.BODY + 1}px; line-height:150%"
    heads = {1: 26, 2: 20, 3: 17}
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p style='{body}; margin:0 0 10px 0'>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            lis = "".join(f"<li style='{body}; margin-bottom:4px'>{inline(i)}</li>" for i in items)
            out.append(f"<ul style='margin:0 0 10px 0'>{lis}</ul>")
            items.clear()

    for line in md.splitlines():
        s = line.strip()
        m = re.match(r"(#{1,3})\s+(.*)", s)
        if not s:
            flush()
        elif m:
            flush()
            out.append(f"<p style='font-size:{heads[len(m.group(1))]}px; font-weight:600; "
                       f"margin:22px 0 8px 0'>{inline(m.group(2))}</p>")
        elif s.startswith(("- ", "* ")):
            if para:
                flush()
            items.append(s[2:])
        elif s == "---":
            flush()
            out.append(f"<hr style='color:{style.RULE}'>")
        else:
            if items:
                flush()
            para.append(s)
    flush()
    return "".join(out)


class ConsentPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        cfg = app.app_config
        lay = page_layout(self)
        lay.addWidget(heading("Consent",
                              "Read this with the speaker. Nothing is recorded or saved until "
                              "they agree."))
        raw = config.CONSENT_FILE.read_text(encoding="utf-8")
        self.text = (raw.replace("{ORG_NAME}", cfg["organisation_name"])
                        .replace("{PROJECT_NAME}", cfg["project_name"])
                        .replace("{CONTACT_EMAIL}", cfg["contact_email"])
                        .replace("{CONSENT_VERSION}", str(cfg["consent_version"]))
                        .replace("{MIN_AGE}", str(cfg["minimum_age"])))
        browser = QTextBrowser()
        browser.setObjectName("Document")
        browser.setOpenExternalLinks(False)
        browser.document().setDocumentMargin(6)
        browser.setHtml(markdown_to_html(self.text))
        browser.setMaximumWidth(860)
        lay.addWidget(browser, 1)

        checks = QVBoxLayout()
        checks.setSpacing(10)
        self.checks = [
            QCheckBox(f"The speaker is {cfg['minimum_age']} years of age or older."),
            QCheckBox("The speaker has read and understood these terms."),
            QCheckBox("The speaker agrees that their voice recordings, transcripts and "
                      "anonymous details can be used as described."),
        ]
        for c in self.checks:
            c.toggled.connect(self._update)
            checks.addWidget(c)
        lay.addLayout(checks)

        decline = button("Does not agree")
        decline.clicked.connect(self.decline)
        self.agree = button("Agree and continue", "Primary")
        self.agree.clicked.connect(self.accept)
        back = button("Back")
        back.clicked.connect(app.go_audio)
        lay.addLayout(button_row(back, None, decline, self.agree, stretch_first=False))

    def reset(self):
        for c in self.checks:
            c.setChecked(False)
        self._update()

    def _update(self):
        self.agree.setEnabled(all(c.isChecked() for c in self.checks))

    def decline(self):
        QMessageBox.information(self, "Consent", "Nothing has been recorded or saved.")
        self.app.go_welcome()

    def accept(self):
        cfg = self.app.app_config
        self.app.consent_done({
            "agreed": True,
            "consent_version": str(cfg["consent_version"]),
            "consent_text_sha256": hashlib.sha256(self.text.encode("utf-8")).hexdigest(),
            "statements": [c.text() for c in self.checks],
            "agreed_at": now_iso(),
            "app_version": APP_VERSION,
        })


# =================================================================== speaker
class SpeakerPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.locations = config.load_india_locations()
        self.min_age = int(app.app_config["minimum_age"])

        outer = page_layout(self)
        outer.addWidget(heading("Speaker details",
                                "Fields marked * are required. Spell the name the same way "
                                "every time: the Speaker ID is built from these details, so a "
                                "returning speaker gets the same ID on any computer."))
        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 12, 0)
        grid.setHorizontalSpacing(56)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        left, right = QVBoxLayout(), QVBoxLayout()
        left.setSpacing(10)
        right.setSpacing(10)
        grid.addLayout(left, 0, 0, Qt.AlignTop)
        grid.addLayout(right, 0, 1, Qt.AlignTop)

        # ---- private
        note = ("Never part of the dataset. Stored separately"
                + (" and encrypted" if crypto.encryption_available() else "")
                + ", and used only to contact the speaker about their recordings.")
        left.addWidget(section("Contact details", note))
        pf = form()
        self.name = QLineEdit()
        self.mobile = QLineEdit()
        self.mobile.setPlaceholderText("10 digits")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Optional")
        pf.addRow("Full name *", self.name)
        pf.addRow("Mobile number *", self.mobile)
        pf.addRow("Email", self.email)
        left.addLayout(pf)
        left.addSpacing(20)

        # ---- demographics
        left.addWidget(section("About the speaker", "Stored without the name, and used to "
                                                    "balance the dataset."))
        df = form()
        self.birth_year = combo([str(y) for y in range(CURRENT_YEAR - self.min_age, 1919, -1)],
                                placeholder="Year")
        self.age_lbl = label("", "Note")
        brow = QHBoxLayout()
        brow.setSpacing(12)
        brow.addWidget(self.birth_year, 1)
        brow.addWidget(self.age_lbl, 1)
        self.gender = combo(config.GENDERS)
        self.mother_tongue = combo(config.MOTHER_TONGUES, editable=True,
                                   placeholder="Select or type")
        self.other_langs = QLineEdit()
        self.other_langs.setPlaceholderText("For example: Hindi, English")
        self.education = combo(config.EDUCATION)
        self.occupation = combo(config.OCCUPATIONS, editable=True, placeholder="Select or type")
        df.addRow("Year of birth *", brow)
        df.addRow("Gender *", self.gender)
        df.addRow("Mother tongue *", self.mother_tongue)
        df.addRow("Other languages", self.other_langs)
        df.addRow("Education *", self.education)
        df.addRow("Occupation", self.occupation)
        left.addLayout(df)

        # ---- location
        right.addWidget(section("Where the speaker grew up",
                                "Only the district and the first three digits of the PIN code "
                                "go into the dataset."))
        lf = form()
        self.country = combo(config.COUNTRIES, editable=True)
        self.state = combo([], editable=True)
        self.district = combo([], editable=True, placeholder="Select or type")
        self.pincode = QLineEdit()
        self.pincode.setPlaceholderText("6 digits")
        self.area = combo(config.AREA_TYPES)
        lf.addRow("Country *", self.country)
        lf.addRow("State / UT *", self.state)
        lf.addRow("District *", self.district)
        lf.addRow("PIN code *", self.pincode)
        lf.addRow("Area *", self.area)
        right.addLayout(lf)
        right.addSpacing(20)

        # ---- session
        right.addWidget(section("This session"))
        sf = form()
        self.language = combo(config.LANGUAGES)
        self.environment = combo(config.ENVIRONMENTS)
        self.mic = combo(config.MIC_TYPES)
        sf.addRow("Recording language *", self.language)
        sf.addRow("Environment *", self.environment)
        sf.addRow("Microphone *", self.mic)
        self.mic_hint = label("", "Note", wrap=True)
        sf.addRow("", self.mic_hint)
        right.addLayout(sf)
        right.addSpacing(20)

        right.addWidget(section("Speaker ID"))
        self.id_lbl = label("", "SpeakerId")
        self.id_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right.addWidget(self.id_lbl)
        right.addWidget(label("language _ state _ district _ gender _ birth year _ fingerprint. "
                              "The fingerprint is a one-way code made from the contact details; "
                              "it cannot be turned back into them.", "Note", wrap=True))

        align_forms(pf, df)
        align_forms(lf, sf)
        outer.addWidget(scrolled(body), 1)
        back = button("Back")
        back.clicked.connect(app.go_consent)
        nxt = button("Save and start recording", "Primary")
        nxt.clicked.connect(self.save)
        outer.addLayout(button_row(back, None, nxt, stretch_first=False))

        self.country.currentTextChanged.connect(self._country_changed)
        self.state.currentTextChanged.connect(self._state_changed)
        for w in (self.name, self.mobile, self.pincode):
            w.textChanged.connect(self._preview)
        for w in (self.gender, self.district, self.language, self.birth_year):
            w.currentTextChanged.connect(self._preview)

    def _year(self) -> int:
        t = self.birth_year.currentText()
        return int(t) if t.isdigit() else 0

    def reset(self, keep_session_fields=True):
        """Clears speaker fields for a new speaker; keeps location and session defaults."""
        for w in (self.name, self.mobile, self.email, self.other_langs, self.pincode):
            w.clear()
        for c in (self.birth_year, self.gender, self.education):
            c.setCurrentIndex(-1)
        for c in (self.mother_tongue, self.occupation):
            c.setCurrentIndex(-1)
            c.setEditText("")
        if not keep_session_fields or not self.country.currentText():
            self.country.setCurrentText("India")
            self.language.setCurrentText(self.app.app_config.get("default_language", "English"))
        for w in self._all_fields():
            set_invalid(w, False)
        self._preview()

    def suggest_mic(self, device_name: str) -> None:
        """Pre-selects the microphone type from the input device's name."""
        guess = audio.guess_mic_type(device_name)
        device = audio.device_label(device_name)
        if guess:
            self.mic.setCurrentText(guess)
            self.mic_hint.setText(f"Filled in from the input device: {device}. Change it if "
                                  "it is wrong.")
        else:
            self.mic.setCurrentIndex(-1)
            self.mic_hint.setText(f"Input device: {device}. Choose the matching type.")

    def _all_fields(self):
        return [self.name, self.mobile, self.email, self.birth_year, self.gender,
                self.mother_tongue, self.education, self.country, self.state, self.district,
                self.pincode, self.area, self.language, self.environment, self.mic]

    # -------------------------------------------------------------- location
    def _is_india(self) -> bool:
        return self.country.currentText().strip().lower() == "india"

    def _country_changed(self, _text):
        self._set_items(self.state, list(self.locations) if self._is_india() else [])
        self.pincode.setPlaceholderText("6 digits" if self._is_india() else "Postal code")
        self._state_changed()

    def _state_changed(self, *_):
        info = self.locations.get(self.state.currentText().strip()) if self._is_india() else None
        self._set_items(self.district, info["districts"] if info else [])
        self._preview()

    @staticmethod
    def _set_items(c: QComboBox, items):
        c.blockSignals(True)
        c.clear()
        c.addItems(items)
        comp = QCompleter(items, c)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        comp.setFilterMode(Qt.MatchContains)
        c.setCompleter(comp)
        c.setCurrentIndex(-1)
        c.setEditText("")
        c.blockSignals(False)

    def _state_code(self) -> str:
        state = self.state.currentText().strip()
        info = self.locations.get(state) if self._is_india() else None
        return info["code"] if info else ids.region_code(state, 2)

    # -------------------------------------------------------------- id
    def _speaker_id(self) -> str | None:
        name, mobile = self.name.text(), self.mobile.text()
        year = self._year()
        gender = config.GENDERS.get(self.gender.currentText())
        district = self.district.currentText().strip()
        pincode = self.pincode.text().strip()
        lang = config.LANGUAGES.get(self.language.currentText())
        if not (ids.normalize_name(name) and ids.mobile_digits(mobile) and gender and lang
                and district and pincode and year and self.state.currentText().strip()):
            return None
        fp = ids.speaker_fingerprint(name, year, gender, pincode, mobile)
        return ids.make_speaker_id(lang, self._state_code(), ids.region_code(district, 3),
                                   gender, year, fp)

    def _preview(self, *_):
        year = self._year()
        if year:
            age = CURRENT_YEAR - year
            self.age_lbl.setText(f"Age about {age}, group {config.age_group(age)}")
        else:
            self.age_lbl.setText("")
        sid = self._speaker_id()
        self.id_lbl.setObjectName("SpeakerId" if sid else "Muted")
        self.id_lbl.style().unpolish(self.id_lbl)
        self.id_lbl.style().polish(self.id_lbl)
        self.id_lbl.setText(sid or "Appears when the required fields are filled in.")

    # -------------------------------------------------------------- save
    def _validate(self) -> list[str]:
        errors, bad = [], []

        def need(widget, ok, msg):
            set_invalid(widget, not ok)
            if not ok:
                errors.append(msg)
                bad.append(widget)

        need(self.name, len(ids.normalize_name(self.name.text())) >= 2, "Full name")
        digits = re.sub(r"\D", "", self.mobile.text())
        if self._is_india():
            ok = bool(re.fullmatch(r"(91|0)?[6-9]\d{9}", digits))
        else:
            ok = 7 <= len(digits) <= 15
        need(self.mobile, ok, "Mobile number (10 digits)")
        email = self.email.text().strip()
        need(self.email, not email or bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)),
             "Email address (or leave it empty)")
        for w, msg in ((self.birth_year, "Year of birth"), (self.gender, "Gender"),
                       (self.mother_tongue, "Mother tongue"), (self.education, "Education"),
                       (self.country, "Country"), (self.state, "State / UT"),
                       (self.district, "District"), (self.area, "Area"),
                       (self.language, "Recording language"),
                       (self.environment, "Environment"), (self.mic, "Microphone")):
            need(w, bool(w.currentText().strip()), msg)
        pin = self.pincode.text().strip()
        ok = bool(re.fullmatch(r"[1-9]\d{5}", pin)) if self._is_india() else \
            bool(re.fullmatch(r"[A-Za-z0-9 -]{3,10}", pin))
        need(self.pincode, ok, "PIN code (6 digits)" if self._is_india() else "Postal code")
        if self._is_india() and self.state.currentText().strip() \
                and self.state.currentText().strip() not in self.locations:
            need(self.state, False, "State / UT: choose one from the list")
        if bad:
            bad[0].setFocus()
        return errors

    def save(self):
        errors = self._validate()
        if errors:
            QMessageBox.warning(self, "Speaker details", "Check these fields:\n\n" +
                                "\n".join(errors))
            return
        sid = self._speaker_id()
        year = self._year()
        pin = re.sub(r"\s", "", self.pincode.text())
        public = {
            "speaker_id": sid,
            "language": self.language.currentText(),
            "language_code": config.LANGUAGES[self.language.currentText()],
            "gender": self.gender.currentText(),
            "birth_year": year,
            "age_group": config.age_group(CURRENT_YEAR - year),
            "mother_tongue": self.mother_tongue.currentText().strip(),
            "other_languages": self.other_langs.text().strip(),
            "education": self.education.currentText(),
            "occupation": self.occupation.currentText().strip(),
            "country": self.country.currentText().strip(),
            "state": self.state.currentText().strip(),
            "district": self.district.currentText().strip(),
            "pincode_prefix": pin[:3],
            "area_type": self.area.currentText(),
            "created_at": now_iso(),
            "app_version": APP_VERSION,
        }
        private = {"name": ids.normalize_text(self.name.text()),
                   "mobile": self.mobile.text().strip(),
                   "email": self.email.text().strip(),
                   "pincode": pin}
        session = {"recording_environment": self.environment.currentText(),
                   "microphone_type": self.mic.currentText()}
        self.app.speaker_done(public, private, session)


# =================================================================== export
class ExportDialog(QDialog):
    def __init__(self, app, output_dir: str, select: str = ""):
        super().__init__(app)
        self.setWindowTitle("Export recordings")
        self.resize(760, 500)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(16)
        lay.addWidget(heading("Export a speaker's recordings",
                              "Creates one zip file per speaker. Send it to the project team "
                              "by Google Drive, pen drive or email."))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.dir = QLineEdit(output_dir)
        browse = button("Browse")
        browse.clicked.connect(self.browse)
        row.addWidget(label("Recordings folder"))
        row.addWidget(self.dir, 1)
        row.addWidget(browse)
        lay.addLayout(row)
        lay.addWidget(rule())
        self.list = QListWidget()
        lay.addWidget(self.list, 1)
        close = button("Close")
        close.clicked.connect(self.reject)
        self.export_btn = button("Export zip", "Primary")
        self.export_btn.clicked.connect(self.export)
        lay.addLayout(button_row(close, self.export_btn))
        self.dir.editingFinished.connect(self.refresh)
        self.refresh(select)

    def browse(self):
        d = QFileDialog.getExistingDirectory(self, "Recordings folder", self.dir.text())
        if d:
            self.dir.setText(d)
            self.refresh()

    def refresh(self, select: str = ""):
        self.list.clear()
        for sp in list_speakers(Path(self.dir.text())):
            mins, secs = divmod(int(sp["seconds"]), 60)
            item = QListWidgetItem(f"{sp['speaker_id']}      {sp['clips']} recordings, "
                                   f"{mins}:{secs:02d}")
            item.setFont(QFont(style.MONO))
            item.setData(Qt.UserRole, str(sp["path"]))
            self.list.addItem(item)
            if sp["speaker_id"] == select:
                self.list.setCurrentItem(item)
        if self.list.count() and not self.list.currentItem():
            self.list.setCurrentRow(0)
        self.export_btn.setEnabled(self.list.count() > 0)
        if not self.list.count():
            self.list.addItem("No speakers have been recorded in this folder yet.")
            self.list.item(0).setFlags(Qt.NoItemFlags)

    def export(self):
        item = self.list.currentItem()
        if not item or not item.data(Qt.UserRole):
            return
        dest = Path(self.dir.text()) / "submissions"
        try:
            zip_path = export_speaker(Path(item.data(Qt.UserRole)), dest)
        except OSError as e:
            QMessageBox.critical(self, "Export", f"The export failed.\n\n{e}")
            return
        box = QMessageBox(self)
        box.setWindowTitle("Export complete")
        box.setText(f"Saved:\n{zip_path}\n\nSend this file to the project team.")
        open_btn = box.addButton("Open folder", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)
        box.exec()
        if box.clickedButton() is open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(dest)))
