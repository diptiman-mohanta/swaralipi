"""Shared fixtures. Tests never touch the real user_settings.json, recordings or keys,
and need no microphone, so they also run on CI machines."""

import os
import sys
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recorder import config, crypto  # noqa: E402


def speech_like(sr: int = 48000, seconds: float = 3.0, start: float = 0.6, end: float = 2.4,
                level: float = 0.3) -> np.ndarray:
    """A tone with silence before and after, plus a little noise: passes the quality check."""
    t = np.arange(int(sr * seconds)) / sr
    rng = np.random.default_rng(0)
    tone = np.where((t > start) & (t < end), level * np.sin(2 * np.pi * 220 * t), 0)
    return (0.0005 * rng.standard_normal(len(t)) + tone).astype(np.float32)[:, None]


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_SETTINGS_FILE", tmp_path / "user_settings.json")
    monkeypatch.setattr(config, "DEFAULT_OUTPUT_DIR", tmp_path / "recordings")
    monkeypatch.setattr(crypto, "PUBLIC_KEY_FILE", tmp_path / "no_public_key.pem")
    return tmp_path


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    from recorder.ui.style import STYLESHEET, light_palette, load_fonts
    app = QApplication.instance() or QApplication([])
    load_fonts()
    app.setStyle("Fusion")
    app.setPalette(light_palette())
    app.setStyleSheet(STYLESHEET)
    return app


@pytest.fixture
def dialogs(monkeypatch):
    """Answers message boxes automatically and records what was shown."""
    from PySide6.QtWidgets import QMessageBox
    log = {"shown": [], "answer": QMessageBox.Yes, "button": 0}

    def static(kind):
        def show(*args, **kwargs):
            log["shown"].append((kind, args[1]))
            return log["answer"]
        return staticmethod(show)

    def fake_exec(box):
        log["shown"].append(("dialog", box.windowTitle()))
        box.buttons()[log["button"]].click()
        return 0

    for kind in ("question", "information", "warning", "critical"):
        monkeypatch.setattr(QMessageBox, kind, static(kind))
    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    return log
