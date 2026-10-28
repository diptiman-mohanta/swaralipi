"""The recording screen for both modes."""

from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import APP_VERSION, audio, config, ids, langcheck, qc
from ..script_loader import ScriptError, load_script
from . import style
from .widgets import LevelMeter, button, button_row, icon, label, rule

QC_COLORS = {qc.OK: style.GREEN, qc.WARN: style.AMBER, qc.FAIL: style.RED}
QC_WORDS = {qc.WARN: "Check", qc.FAIL: "Problem"}


def fmt_time(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_readout(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


class RecordPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.recorder = app.recorder
        self.session = None
        self.take = None
        self.take_qc = None
        self.locked_text = ""
        self.script: list[tuple[str, str]] = []
        self.script_name = ""
        self.idx = 0
        self._play_token = 0
        self._language_confirmed = set()   # (speaker_id, source) pairs already checked
        self.setFocusPolicy(Qt.StrongFocus)
        self._dots = {k: icon("dot", c) for k, c in QC_COLORS.items()}

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ============================================================ main column
        main_w = QWidget()
        main = QVBoxLayout(main_w)
        main.setContentsMargins(48, 28, 40, 24)
        main.setSpacing(0)

        meta = QHBoxLayout()
        self.position_lbl = label("", "Muted")
        meta.addWidget(self.position_lbl, 1)
        self.settings_lbl = label("", "MonoMuted")
        meta.addWidget(self.settings_lbl)
        main.addLayout(meta)
        main.addSpacing(18)

        self.prompt_stack = QStackedWidget()
        self.prompt_stack.addWidget(self._build_typed_prompt())
        self.prompt_stack.addWidget(self._build_script_prompt())
        main.addWidget(self.prompt_stack)
        main.addSpacing(24)
        main.addWidget(rule())
        main.addSpacing(20)

        # ---- transport
        readout_row = QHBoxLayout()
        self.readout = label("00:00.0", "Readout")
        readout_row.addWidget(self.readout)
        readout_row.addSpacing(18)
        self.status_lbl = QLabel()
        self.status_lbl.setWordWrap(True)
        readout_row.addWidget(self.status_lbl, 1)
        main.addLayout(readout_row)
        main.addSpacing(10)
        self.meter = LevelMeter()
        main.addWidget(self.meter)
        main.addSpacing(16)

        self.start_btn = button("Record", "Record", "record")
        self.stop_btn = button("Stop", "", "stop")
        self.play_btn = button("Listen", "", "play")
        self.submit_btn = button("Submit", "Primary", "check")
        for b in (self.start_btn, self.stop_btn, self.play_btn, self.submit_btn):
            b.setFocusPolicy(Qt.NoFocus)
            b.setMinimumHeight(40)
            b.setMinimumWidth(110)
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.play_btn.clicked.connect(self.toggle_play)
        self.submit_btn.clicked.connect(self.submit)
        main.addLayout(button_row(self.start_btn, self.stop_btn, self.play_btn, None,
                                  self.submit_btn, stretch_first=False))
        main.addSpacing(8)
        main.addWidget(label("Space starts and stops recording, P plays it back, Enter submits. "
                             "Leave about half a second of silence before and after speaking.",
                             "Note", wrap=True))
        main.addSpacing(22)
        main.addWidget(rule())
        main.addSpacing(16)

        # ---- quality
        main.addWidget(label("Quality check", "Section"))
        main.addSpacing(10)
        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(2)
        self.qc_vals = {}
        for i, (key, name) in enumerate([("duration_sec", "Length"), ("peak_dbfs", "Peak"),
                                         ("noise_floor_dbfs", "Noise floor"),
                                         ("snr_db", "Signal / noise"),
                                         ("lead_silence_sec", "Silence before"),
                                         ("trail_silence_sec", "Silence after")]):
            grid.addWidget(label(name, "Note"), 0, i)
            v = label("–", "Figure")
            grid.addWidget(v, 1, i)
            self.qc_vals[key] = v
        grid.setColumnStretch(6, 1)
        main.addLayout(grid)
        main.addSpacing(10)
        self.qc_issues = QLabel()
        self.qc_issues.setWordWrap(True)
        self.qc_issues.setTextFormat(Qt.RichText)
        main.addWidget(self.qc_issues)
        main.addStretch(1)

        back = button("Back to speaker details")
        back.setFocusPolicy(Qt.NoFocus)
        back.clicked.connect(self.go_back)
        main.addLayout(button_row(back, None, stretch_first=False))
        root.addWidget(main_w, 1)
        root.addWidget(rule(vertical=True))

        # ============================================================ side column
        side_w = QWidget()
        side_w.setFixedWidth(340)
        side = QVBoxLayout(side_w)
        side.setContentsMargins(28, 28, 32, 24)
        side.setSpacing(4)
        side.addWidget(label("Speaker", "Note"))
        self.speaker_lbl = label("", "SpeakerId")
        self.speaker_lbl.setWordWrap(True)
        self.speaker_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        side.addWidget(self.speaker_lbl)
        side.addSpacing(12)
        side.addWidget(label("Input device", "Note"))
        self.device_lbl = label("", "Muted", wrap=True)
        side.addWidget(self.device_lbl)
        side.addSpacing(18)
        side.addWidget(label("Saved", "Section"))
        self.stats_lbl = label("", "Muted")
        side.addWidget(self.stats_lbl)
        side.addSpacing(8)
        side.addWidget(rule())
        self.saved_list = QListWidget()
        self.saved_list.setFocusPolicy(Qt.NoFocus)
        self.saved_list.setWordWrap(True)
        self.saved_list.itemDoubleClicked.connect(self._jump_to_saved)
        side.addWidget(self.saved_list, 1)
        side.addSpacing(12)
        finish = button("Finish session", "Primary")
        finish.setFocusPolicy(Qt.NoFocus)
        finish.clicked.connect(self.finish)
        side.addWidget(finish)
        root.addWidget(side_w)

        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)

    # ================================================================ prompts
    def _build_typed_prompt(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.typed_hint = label("", "Muted", wrap=True)
        lay.addWidget(self.typed_hint)
        self.transcript = QPlainTextEdit()
        self.transcript.setObjectName("Transcript")
        self.transcript.setPlaceholderText("Type the sentence exactly as it will be spoken")
        self.transcript.setFixedHeight(120)
        lay.addWidget(self.transcript)
        self.locked_lbl = label("", "Prompt", wrap=True)
        self.locked_lbl.setMinimumHeight(96)
        self.locked_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.locked_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.locked_lbl)
        self.ok_btn = button("Confirm sentence", "Primary")
        self.edit_btn = button("Edit sentence", "Quiet")
        self.ok_btn.clicked.connect(self.confirm_transcript)
        self.edit_btn.clicked.connect(self.edit_transcript)
        for b in (self.ok_btn, self.edit_btn):
            b.setFocusPolicy(Qt.NoFocus)
        lay.addLayout(button_row(self.ok_btn, self.edit_btn, None, stretch_first=False))
        sc = QShortcut(QKeySequence("Ctrl+Return"), self.transcript)
        sc.setContext(Qt.WidgetShortcut)
        sc.activated.connect(self.confirm_transcript)
        return w

    def _build_script_prompt(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.sentence_no_lbl = label("", "Muted")
        lay.addWidget(self.sentence_no_lbl)
        self.sentence_lbl = label("Load a script file to begin.", "Prompt", wrap=True)
        self.sentence_lbl.setMinimumHeight(96)
        self.sentence_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.sentence_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.sentence_lbl)
        self.prev_btn = button("Previous")
        self.next_btn = button("Next")
        self.next_new_btn = button("Next unrecorded")
        self.goto = QLineEdit()
        self.goto.setFixedWidth(64)
        self.goto.setValidator(QIntValidator(1, 999999, self))
        self.goto.setPlaceholderText("No.")
        go = button("Go")
        load = button("Load script", "Quiet")
        self.prev_btn.clicked.connect(lambda: self.show_sentence(self.idx - 1))
        self.next_btn.clicked.connect(lambda: self.show_sentence(self.idx + 1))
        self.next_new_btn.clicked.connect(self.next_unrecorded)
        go.clicked.connect(self._go_to)
        self.goto.returnPressed.connect(self._go_to)
        load.clicked.connect(self.choose_script)
        for b in (self.prev_btn, self.next_btn, self.next_new_btn, go, load):
            b.setFocusPolicy(Qt.NoFocus)
        lay.addLayout(button_row(self.prev_btn, self.next_btn, self.next_new_btn, None,
                                 label("Position", "Muted"), self.goto, go, load,
                                 stretch_first=False))
        return w

    # ================================================================ lifecycle
    def begin(self, session) -> None:
        self.session = session
        self.take = self.take_qc = None
        self.locked_text = ""
        store = session.store
        is_typed = session.mode == config.MODE_TYPED
        self.speaker_lbl.setText(store.speaker_id)
        self.settings_lbl.setText(session.audio.summary())
        self.device_lbl.setText(audio.device_label(session.audio.device_name))
        self.prompt_stack.setCurrentIndex(0 if is_typed else 1)
        self.transcript.clear()
        self._set_locked(False)
        if not is_typed:
            last = config.load_user_settings().get("last_script", "")
            if self.script:
                self.next_unrecorded(start=0)
                self._check_language(self.script_name, [t for _, t in self.script])
            elif last and Path(last).is_file():
                self.load_script_file(last, quiet=True)   # also jumps to first unrecorded
        self._update_position()
        self._clear_qc()
        self._refresh_saved()
        self._update_ui()
        self.setFocus()

    def leave(self) -> bool:
        """Stops audio; returns False if the user wants to keep an unsaved take."""
        if self.recorder.is_recording:
            self.stop_recording()
        if self.take is not None:
            r = QMessageBox.question(self, "Unsaved recording",
                                     "This recording has not been submitted. Discard it?")
            if r != QMessageBox.Yes:
                return False
        audio.stop_playback()
        self.timer.stop()
        self.recorder.stop()
        self.take = self.take_qc = None
        return True

    def go_back(self):
        if self.leave():
            self.session.store.remove_if_empty()
            self.app.go_speaker(keep=True)

    def finish(self):
        if not self.leave():
            return
        store = self.session.store
        box = QMessageBox(self)
        box.setWindowTitle("Session finished")
        box.setText(f"{len(store.records)} recordings saved for {store.speaker_id} "
                    f"({fmt_time(store.total_duration())} of audio).")
        export = box.addButton("Export zip now", QMessageBox.AcceptRole)
        another = box.addButton("Next speaker", QMessageBox.ActionRole)
        box.addButton("Home", QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is export:
            self.app.go_welcome()
            self.app.open_export(select=store.speaker_id)
        elif clicked is another:
            self.app.new_speaker()
        else:
            self.app.go_welcome()

    # ================================================================ typed mode
    def _set_locked(self, locked: bool):
        """Locked: the confirmed sentence is shown like a script prompt, not as an editor."""
        self.transcript.setVisible(not locked)
        self.locked_lbl.setVisible(locked)
        self.locked_lbl.setText(self.locked_text if locked else "")
        self.ok_btn.setVisible(not locked)
        self.edit_btn.setVisible(locked)
        self.typed_hint.setText(
            "Read this sentence aloud." if locked else
            "Type the sentence exactly as it will be spoken, then confirm it (Ctrl+Enter).")

    def confirm_transcript(self):
        text = ids.normalize_text(self.transcript.toPlainText())
        if not text:
            QMessageBox.information(self, "Sentence", "Type the sentence first.")
            return
        if self._contains_private_details(text):
            r = QMessageBox.question(
                self, "Personal details in the sentence",
                "This sentence seems to contain the speaker's name, mobile number or email. "
                "Personal details must not appear in the dataset.\n\nKeep the sentence anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return
        if not self._check_language("typed", [text]):
            return
        self.transcript.setPlainText(text)
        self.locked_text = text
        self._set_locked(True)
        self.setFocus()
        self._update_ui()

    def _contains_private_details(self, text: str) -> bool:
        words = set(ids.normalize_name(text).split())
        flat = text.casefold()
        digits = "".join(ch for ch in text if ch.isdigit())
        for term in self.session.private_terms:
            if term.isdigit():
                if term in digits:
                    return True
            elif term in words or ("@" in term and term in flat):
                return True
        return False

    def edit_transcript(self):
        self._set_locked(False)
        self.locked_text = ""
        self.transcript.setFocus()
        self._update_ui()

    # ================================================================ script mode
    def choose_script(self):
        start = config.load_user_settings().get("last_script", "")
        path, _ = QFileDialog.getOpenFileName(self, "Load script",
                                              str(Path(start).parent) if start else "",
                                              "Script files (*.xlsx *.csv *.tsv *.txt)")
        if path:
            self.load_script_file(path)

    def load_script_file(self, path: str, quiet=False):
        try:
            script = load_script(path)
        except (ScriptError, OSError, ValueError) as e:
            if not quiet:
                QMessageBox.warning(self, "Script", f"The script could not be loaded.\n\n{e}")
            return
        self.script = script
        self.script_name = Path(path).name
        settings = config.load_user_settings()
        settings["last_script"] = str(path)
        config.save_user_settings(settings)
        if self.session:
            self.next_unrecorded(start=0)
            self._check_language(self.script_name, [t for _, t in script])

    def _check_language(self, source: str, texts) -> bool:
        """Warns once per speaker and source when the sentences are not written in the
        recording language. Returns False if the user goes back to change the language."""
        key = (self.session.store.speaker_id, source)
        if key in self._language_confirmed:
            return True
        msg = langcheck.mismatch_message(self.session.speaker_public["language"], texts)
        if msg:
            box = QMessageBox(self)
            box.setWindowTitle("Check the recording language")
            box.setText(f"{msg}\n\nThe language is part of the Speaker ID and of every "
                        "recording's metadata, so it must match what is being read.")
            change = box.addButton("Change the language", QMessageBox.AcceptRole)
            box.addButton("Continue anyway", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is change:
                QTimer.singleShot(0, self.go_back)   # after the page switch in progress
                return False
        self._language_confirmed.add(key)
        return True

    def _script_sid(self, i: int) -> str:
        return ids.script_sentence_id(self.session.store.speaker_id, self.script[i][0])

    def _is_done(self, i: int) -> bool:
        return self.session.store.has(self._script_sid(i))

    def _go_to(self):
        if self.goto.text().isdigit():
            self.show_sentence(int(self.goto.text()) - 1)
            self.goto.clear()
            self.setFocus()

    def show_sentence(self, i: int):
        if not self.script:
            return
        if self.take is not None and i != self.idx:
            r = QMessageBox.question(self, "Unsaved recording",
                                     "This recording has not been submitted. Discard it?")
            if r != QMessageBox.Yes:
                return
            self.take = self.take_qc = None
            self._clear_qc()
        self.idx = max(0, min(i, len(self.script) - 1))
        number, text = self.script[self.idx]
        note = "   Already recorded. Recording again replaces it." if self._is_done(self.idx) \
            else ""
        self.sentence_no_lbl.setText(f"Sentence {number}{note}")
        self.sentence_lbl.setText(text)
        self._update_position()
        self._update_ui()

    def next_unrecorded(self, *_, start: int | None = None):
        if not self.script:
            return
        begin = self.idx + 1 if start is None else start
        n = len(self.script)
        for k in range(n):
            i = (begin + k) % n
            if not self._is_done(i):
                self.show_sentence(i)
                return
        self.show_sentence(begin % n if start is None else 0)
        QMessageBox.information(self, "Script", "Every sentence in this script is recorded.")

    def _update_position(self):
        if self.session is None:
            return
        if self.session.mode == config.MODE_TYPED:
            self.position_lbl.setText("Type a sentence, then read it aloud")
        elif self.script:
            done = sum(self._is_done(i) for i in range(len(self.script)))
            self.position_lbl.setText(f"{self.script_name}   ·   position {self.idx + 1} of "
                                      f"{len(self.script)}   ·   {done} recorded")
        else:
            self.position_lbl.setText("No script loaded. Use 'Load script' below the sentence.")

    def _jump_to_saved(self, item: QListWidgetItem):
        if self.session.mode != config.MODE_SCRIPT:
            return
        sid = item.data(Qt.UserRole)
        for i in range(len(self.script)):
            if self._script_sid(i) == sid:
                self.show_sentence(i)
                return

    # ================================================================ recording
    def current_text(self) -> str:
        if self.session.mode == config.MODE_TYPED:
            return self.locked_text
        return self.script[self.idx][1] if self.script else ""

    def start_recording(self):
        if self.recorder.is_recording or not self.current_text():
            return
        audio.stop_playback()
        try:
            self.recorder.start(self.session.audio, keep=True)
        except Exception as e:
            QMessageBox.critical(self, "Microphone", f"Recording could not start.\n\n{e}")
            return
        self.take = self.take_qc = None
        self._clear_qc()
        self.timer.start()
        self._update_ui()

    def stop_recording(self):
        if not self.recorder.is_recording:
            return
        data = self.recorder.stop()
        self.timer.stop()
        self.meter.reset()
        if data is None or len(data) == 0:
            self._update_ui()
            return
        self.take = data
        self.take_qc = qc.analyze(data, self.session.audio.sample_rate)
        self._show_qc(self.take_qc)
        self._update_ui()

    def toggle_play(self):
        if self.take is None:
            return
        self._play_token += 1
        if self.play_btn.text() == "Stop playback":
            audio.stop_playback()
            self.play_btn.setText("Listen")
            return
        audio.play(self.take, self.session.audio.sample_rate)
        self.play_btn.setText("Stop playback")
        token = self._play_token
        ms = int(len(self.take) / self.session.audio.sample_rate * 1000) + 150
        QTimer.singleShot(ms, lambda: token == self._play_token and
                          self.play_btn.setText("Listen"))

    def _tick(self):
        self.meter.set_peak(self.recorder.read_peak())
        if self.recorder.is_recording:
            self.readout.setText(fmt_readout(self.recorder.seconds))

    # ================================================================ submit
    def submit(self):
        if self.take is None or not self.current_text():
            return
        s = self.session
        store = s.store
        if self.take_qc["status"] == qc.FAIL:
            problems = "\n".join(m for lvl, m in self.take_qc["issues"] if lvl == qc.FAIL)
            r = QMessageBox.question(self, "Recording has problems",
                                     f"{problems}\n\nRecording again is better. "
                                     "Submit this one anyway?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r != QMessageBox.Yes:
                return

        if s.mode == config.MODE_SCRIPT:
            number = self.script[self.idx][0]
            sid = self._script_sid(self.idx)
            if store.has(sid):
                r = QMessageBox.question(self, "Already recorded",
                                         f"Sentence {number} is already recorded. Replace it?")
                if r != QMessageBox.Yes:
                    return
        else:
            number = ""
            when = datetime.now()
            sid = ids.typed_sentence_id(store.speaker_id, when)
            while store.has(sid):
                when += timedelta(seconds=1)
                sid = ids.typed_sentence_id(store.speaker_id, when)

        audio_path = store.audio_path(sid, s.audio.extension)
        asr_path = store.asr_path(sid) if s.audio.asr_copy else None
        try:
            audio.save_recording(self.take, s.audio, audio_path)
            if asr_path:
                audio.save_asr_copy(self.take, s.audio.sample_rate, asr_path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"The audio file could not be saved.\n\n{e}")
            return

        record = self._build_record(sid, number, audio_path, asr_path)
        try:
            store.add_record(record)
        except PermissionError:
            QMessageBox.warning(self, "transcripts.xlsx is open",
                                "The recording was saved, but transcripts.xlsx is open in "
                                "another program such as Excel. Close it and it will be "
                                "updated on the next submit.")
        except OSError as e:
            QMessageBox.critical(self, "Save failed", f"The metadata could not be updated.\n\n{e}")
            return

        audio.stop_playback()
        self.take = self.take_qc = None
        self._clear_qc()
        self._refresh_saved(select=sid)
        short = sid.removeprefix(store.speaker_id + "_")
        if s.mode == config.MODE_TYPED:
            self.transcript.clear()
            self._set_locked(False)
            self.locked_text = ""
            self.transcript.setFocus()
            self._update_ui()
        else:
            self.next_unrecorded()
        self._status(f"Saved as {short}.", style.GREEN)

    def _build_record(self, sid, number, audio_path: Path, asr_path) -> dict:
        s = self.session
        sp = s.speaker_public
        rel = lambda p: p.relative_to(s.store.dir).as_posix() if p else ""
        q = self.take_qc
        device = s.audio.device_name or f"System default ({audio.default_input_name()})"
        age = datetime.now().year - sp["birth_year"]
        return {
            "sentence_id": sid,
            "speaker_id": s.store.speaker_id,
            "text": self.current_text(),
            "audio_filepath": rel(audio_path),
            "audio_16k_filepath": rel(asr_path),
            "duration_sec": q["duration_sec"],
            "sample_rate": s.audio.sample_rate,
            "bit_depth": s.audio.bit_depth,
            "channels": s.audio.channels,
            "file_format": s.audio.file_format,
            "language": sp["language"],
            "mode": s.mode,
            "script_file": self.script_name if s.mode == config.MODE_SCRIPT else "",
            "script_sentence_no": number,
            "gender": sp["gender"],
            "birth_year": sp["birth_year"],
            "age_at_recording": age,
            "age_group": config.age_group(age),
            "mother_tongue": sp["mother_tongue"],
            "education": sp["education"],
            "occupation": sp["occupation"],
            "area_type": sp["area_type"],
            "country": sp["country"],
            "state": sp["state"],
            "district": sp["district"],
            "pincode_prefix": sp["pincode_prefix"],
            "recording_environment": s.session_details["recording_environment"],
            "microphone_type": s.session_details["microphone_type"],
            "input_device": device,
            "peak_dbfs": q["peak_dbfs"],
            "noise_floor_dbfs": q["noise_floor_dbfs"],
            "snr_db": q["snr_db"],
            "clipped_samples": q["clipped_samples"],
            "lead_silence_sec": q["lead_silence_sec"],
            "trail_silence_sec": q["trail_silence_sec"],
            "qc_status": q["status"],
            "qc_issues": "; ".join(m for _, m in q["issues"]),
            "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "app_version": APP_VERSION,
        }

    # ================================================================ display
    def _status(self, text: str, color: str = style.INK_2):
        self.status_lbl.setText(f"<span style='color:{color}'>{text}</span>")

    def _clear_qc(self):
        for v in self.qc_vals.values():
            v.setText("–")
        self.qc_issues.setText(f"<span style='color:{style.MUTED}'>Results appear after each "
                               "recording.</span>")

    def _show_qc(self, r: dict):
        fmt = {"duration_sec": "{:.1f} s", "peak_dbfs": "{:.1f} dB",
               "noise_floor_dbfs": "{:.0f} dB", "snr_db": "{:.0f} dB",
               "lead_silence_sec": "{:.2f} s", "trail_silence_sec": "{:.2f} s"}
        for key, f in fmt.items():
            self.qc_vals[key].setText(f.format(r[key]))
        if not r["issues"]:
            self.qc_issues.setText(f"<span style='color:{style.GREEN}'>Passed. Listen to it "
                                   "once, then submit.</span>")
            return
        lines = [f"<span style='color:{QC_COLORS[lvl]}; font-weight:600'>{QC_WORDS[lvl]}</span>"
                 f"&nbsp;&nbsp;{m}" for lvl, m in r["issues"]]
        self.qc_issues.setText("<br>".join(lines))

    def _refresh_saved(self, select: str = ""):
        store = self.session.store
        self.saved_list.clear()
        prefix = store.speaker_id + "_"
        for rec in reversed(list(store.records.values())):
            short = rec["sentence_id"].removeprefix(prefix)
            text = rec["text"] if len(rec["text"]) <= 70 else rec["text"][:68] + "…"
            item = QListWidgetItem(f"{short}\n{text}")
            dot = self._dots.get(rec.get("qc_status"))
            if dot:
                item.setIcon(dot)
            item.setToolTip(f"{rec['sentence_id']}\n{rec['text']}\n{rec['duration_sec']} s, "
                            f"quality: {rec.get('qc_status', '')}")
            item.setData(Qt.UserRole, rec["sentence_id"])
            self.saved_list.addItem(item)
            if rec["sentence_id"] == select:
                self.saved_list.setCurrentItem(item)
        n = len(store.records)
        self.stats_lbl.setText(f"{n} recording{'s' * (n != 1)}, "
                               f"{fmt_time(store.total_duration())} of audio")
        if self.session.mode == config.MODE_SCRIPT:
            self._update_position()

    def _update_ui(self):
        if self.session is None:
            return
        recording = self.recorder.is_recording
        has_text = bool(self.current_text())
        has_take = self.take is not None
        self.start_btn.setEnabled(has_text and not recording)
        self.start_btn.setText("Record again" if has_take else "Record")
        self.stop_btn.setEnabled(recording)
        self.play_btn.setEnabled(has_take and not recording)
        self.play_btn.setText("Listen")
        self.submit_btn.setEnabled(has_take and has_text and not recording)
        self.edit_btn.setEnabled(bool(self.locked_text) and not recording)
        is_script = self.session.mode == config.MODE_SCRIPT
        for b in (self.prev_btn, self.next_btn, self.next_new_btn):
            b.setEnabled(is_script and bool(self.script) and not recording)
        if recording:
            self._status("Recording", style.RED)
            return
        if has_take:
            self.readout.setText(fmt_readout(self.take_qc["duration_sec"]))
            self._status("Listen to the recording, then submit it or record again.")
        else:
            self.readout.setText(fmt_readout(0))
            if not has_text:
                self._status("Load a script to begin." if is_script else
                             "Confirm the sentence before recording.", style.MUTED)
            else:
                self._status("Ready. Press Record or Space, wait half a second, then speak.")

    # ================================================================ keyboard
    def keyPressEvent(self, e):
        if (self.transcript.hasFocus() and not self.transcript.isReadOnly()) \
                or self.goto.hasFocus():
            return super().keyPressEvent(e)
        key = e.key()
        if key == Qt.Key_Space and not e.isAutoRepeat():
            self.stop_recording() if self.recorder.is_recording else self.start_recording()
        elif key == Qt.Key_P:
            self.toggle_play()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.submit()
        elif key == Qt.Key_Right and self.session.mode == config.MODE_SCRIPT:
            self.show_sentence(self.idx + 1)
        elif key == Qt.Key_Left and self.session.mode == config.MODE_SCRIPT:
            self.show_sentence(self.idx - 1)
        else:
            return super().keyPressEvent(e)
