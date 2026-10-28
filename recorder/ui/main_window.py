"""Main window: holds the session state and moves between screens."""

from dataclasses import dataclass, field

from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QVBoxLayout, QWidget

from .. import APP_NAME, APP_VERSION, config, ids
from ..audio import AudioSettings, Recorder
from ..storage import SpeakerStore
from .pages import (AudioSettingsPage, ConsentPage, ExportDialog, ModePage, SpeakerPage,
                    WelcomePage)
from .record_page import RecordPage
from .widgets import StepBar


@dataclass
class Session:
    mode: str = config.MODE_TYPED
    audio: AudioSettings = field(default_factory=AudioSettings)
    consent: dict | None = None
    store: SpeakerStore | None = None
    speaker_public: dict = field(default_factory=dict)
    session_details: dict = field(default_factory=dict)
    private_terms: list = field(default_factory=list)   # in memory only, never saved


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1180, 820)
        self.app_config = config.load_app_config()
        self.recorder = Recorder()
        self.user_settings = config.load_user_settings()
        self.session = Session(audio=AudioSettings.from_dict(self.user_settings.get("audio")))
        # A preset named in app_config.json fixes the format for every contributor.
        locked = self.app_config.get("locked_audio_preset")
        self.locked_preset = locked if locked in config.AUDIO_PRESETS else None
        if self.locked_preset:
            self.session.audio.apply_preset(self.locked_preset)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.steps = StepBar(APP_NAME)
        lay.addWidget(self.steps)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self.welcome = WelcomePage(self)
        self.mode_page = ModePage(self)
        self.audio_page = AudioSettingsPage(self)
        self.consent_page = ConsentPage(self)
        self.speaker_page = SpeakerPage(self)
        self.record_page = RecordPage(self)
        self.pages = [self.welcome, self.mode_page, self.audio_page, self.consent_page,
                      self.speaker_page, self.record_page]
        for p in self.pages:
            self.stack.addWidget(p)
        self.stack.currentChanged.connect(self._page_changed)
        self.speaker_page.reset(keep_session_fields=False)
        self.go_welcome()

    def _page_changed(self, index: int):
        self.steps.setVisible(index > 0)
        self.steps.set_step(index - 1)

    # -------------------------------------------------------------- navigation
    def go_welcome(self):
        self.welcome.refresh()
        self.stack.setCurrentWidget(self.welcome)
        self._page_changed(0)

    def go_mode(self):
        self.stack.setCurrentWidget(self.mode_page)

    def set_mode(self, mode: str):
        self.session.mode = mode
        self.go_audio()

    def go_audio(self):
        self.audio_page.load(self.session.audio)
        self.stack.setCurrentWidget(self.audio_page)

    def audio_done(self, settings: AudioSettings):
        self.session.audio = settings
        self.user_settings["audio"] = settings.to_dict()
        config.save_user_settings(self.user_settings)
        self.go_consent()

    def go_consent(self):
        self.consent_page.reset()
        self.stack.setCurrentWidget(self.consent_page)

    def consent_done(self, consent: dict):
        self.session.consent = consent
        self.go_speaker(keep=False)

    def go_speaker(self, keep: bool):
        if not keep:
            self.speaker_page.reset()
            self.speaker_page.suggest_mic(self.session.audio.device_name)
        self.stack.setCurrentWidget(self.speaker_page)

    def _match_earlier_format(self, store: SpeakerStore) -> None:
        """Keeps all of a speaker's clips in one audio format where possible."""
        if not store.records:
            return
        last = list(store.records.values())[-1]
        earlier = (last["sample_rate"], last["bit_depth"], last["channels"], last["file_format"])
        s = self.session.audio
        if earlier == s.format_key():
            return
        desc = (f"{earlier[0] / 1000:g} kHz, {earlier[1]}, "
                f"{'mono' if earlier[2] == 1 else 'stereo'}, {earlier[3]}")
        if self.locked_preset:
            QMessageBox.warning(self, "Different audio format",
                                f"This speaker's earlier recordings used {desc}. The project "
                                f"now fixes the format to {s.summary()}, so this speaker will "
                                "have recordings in two formats.")
            return
        r = QMessageBox.question(self, "Different audio format",
                                 f"This speaker's earlier recordings used {desc}, but the "
                                 f"current settings are {s.summary()}.\n\nSwitch to the earlier "
                                 "format so all of this speaker's recordings match?")
        if r == QMessageBox.Yes:
            s.sample_rate, s.bit_depth, s.channels, s.file_format = earlier
            s.asr_copy = bool(last.get("audio_16k_filepath"))
            s.preset = ""
            self.user_settings["audio"] = s.to_dict()
            config.save_user_settings(self.user_settings)

    def speaker_done(self, public: dict, private: dict, session_details: dict):
        s = self.session
        try:
            store = SpeakerStore(s.audio.output_dir, public["speaker_id"])
            store.save_profile(public, private)
            if s.consent:
                store.add_consent(s.consent)
        except OSError as e:
            QMessageBox.critical(self, "Speaker details", f"Could not save the speaker "
                                 f"profile:\n\n{e}")
            return
        if store.records:
            QMessageBox.information(self, "Welcome back",
                                    f"This speaker already has {len(store.records)} saved "
                                    "recordings. New recordings will be added to them.")
            self._match_earlier_format(store)
        s.store, s.speaker_public, s.session_details = store, public, session_details
        s.private_terms = [w for w in ids.normalize_name(private["name"]).split() if len(w) >= 3]
        s.private_terms += [t for t in (ids.mobile_digits(private["mobile"]),
                                        private["email"].casefold()) if t]
        self.record_page.begin(s)
        self.stack.setCurrentWidget(self.record_page)

    def new_speaker(self):
        """Same mode and audio settings; new consent and speaker details."""
        self.session.store = None
        self.go_consent()

    def open_export(self, select: str = ""):
        out = self.session.audio.output_dir or str(config.DEFAULT_OUTPUT_DIR)
        ExportDialog(self, out, select).exec()

    # -------------------------------------------------------------- close
    def closeEvent(self, event):
        if self.stack.currentWidget() is self.record_page and not self.record_page.leave():
            event.ignore()
            return
        self.audio_page.stop_test()
        self.recorder.stop()
        event.accept()
