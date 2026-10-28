"""Microphone capture, playback and file writing."""

import os
import threading
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import soxr

from .config import ASR_COPY_RATE, AUDIO_PRESETS, BIT_DEPTHS, FILE_FORMATS


@dataclass
class AudioSettings:
    sample_rate: int = 48000
    bit_depth: str = "24-bit PCM"
    channels: int = 1
    file_format: str = "WAV"
    asr_copy: bool = True
    device_name: str = ""          # "" = system default input
    output_dir: str = ""
    preset: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AudioSettings":
        fields = cls.__dataclass_fields__
        return cls(**{k: v for k, v in (d or {}).items() if k in fields})

    @property
    def subtype(self) -> str:
        return BIT_DEPTHS[self.bit_depth]

    @property
    def extension(self) -> str:
        return FILE_FORMATS[self.file_format]

    def apply_preset(self, name: str) -> None:
        for key, value in AUDIO_PRESETS[name].items():
            setattr(self, key, value)
        self.preset = name

    def format_key(self) -> tuple:
        return (self.sample_rate, self.bit_depth, self.channels, self.file_format)

    def summary(self) -> str:
        ch = "mono" if self.channels == 1 else "stereo"
        s = f"{self.sample_rate / 1000:g} kHz · {self.bit_depth} · {ch} · {self.file_format}"
        return s + (" + 16 kHz ASR copy" if self.asr_copy else "")

    def bytes_per_minute(self) -> int:
        bytes_per_sample = {"PCM_16": 2, "PCM_24": 3, "FLOAT": 4}[self.subtype]
        return self.sample_rate * self.channels * bytes_per_sample * 60


# ---------------------------------------------------------------- devices
def input_devices() -> list[tuple[str, int]]:
    """[(display name, device index)] for every device that can record."""
    out = []
    try:
        apis = sd.query_hostapis()
        for idx, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                out.append((f"{dev['name']}  [{apis[dev['hostapi']]['name']}]", idx))
    except Exception:
        pass
    return out


def default_input_name() -> str:
    try:
        return sd.query_devices(kind="input")["name"]
    except Exception:
        return "unknown"


def device_label(device_name: str) -> str:
    """Readable device name; "" means the system default input."""
    if device_name:
        return device_name.split("  [")[0]
    return f"System default ({default_input_name()})"


# Keyword hints in Windows / macOS / Linux device names -> config.MIC_TYPES entry.
BLUETOOTH = "Bluetooth headset"
_MIC_HINTS = [
    (BLUETOOTH, ("bluetooth", "hands-free", "handsfree", "buds", "airpods", "earbuds")),
    ("Professional XLR mic + interface", ("focusrite", "scarlett", "behringer", "umc",
                                          "presonus", "motu", "audient", "steinberg", "tascam")),
    ("USB microphone", ("usb", "yeti", "rode", "fifine", "hyperx", "samson", "audio-technica",
                        "maono", "boya")),
    ("Laptop built-in mic", ("microphone array", "internal mic", "built-in", "builtin",
                             "digital microphone")),
    ("Wired headset mic", ("headset", "headphone")),
]


def guess_mic_type(device_name: str) -> str | None:
    """Best guess of the microphone type from the device name, or None if unclear."""
    name = (device_name or default_input_name()).lower()
    for mic_type, hints in _MIC_HINTS:
        if any(h in name for h in hints):
            return mic_type
    return None


def resolve_device(device_name: str):
    """Device index for a stored display name, or None for the system default."""
    if device_name:
        for name, idx in input_devices():
            if name == device_name:
                return idx
    return None


def check_settings(settings: AudioSettings) -> str | None:
    """Returns an error message if the device cannot record with these settings."""
    try:
        sd.check_input_settings(device=resolve_device(settings.device_name),
                                channels=settings.channels,
                                samplerate=settings.sample_rate, dtype="float32")
    except Exception as e:
        return str(e)
    return None


# ---------------------------------------------------------------- capture
class Recorder:
    """Captures float32 audio in a background stream; the UI polls peak levels."""

    def __init__(self):
        self._stream = None
        self._chunks: list[np.ndarray] = []
        self._keep = False
        self._peak = 0.0
        self._frames = 0
        self._lock = threading.Lock()
        self.sample_rate = 0

    @property
    def active(self) -> bool:
        return self._stream is not None

    @property
    def is_recording(self) -> bool:
        return self.active and self._keep

    @property
    def seconds(self) -> float:
        return self._frames / self.sample_rate if self.sample_rate else 0.0

    def start(self, settings: AudioSettings, keep: bool = True) -> None:
        """keep=False only meters the input (microphone test)."""
        self.stop()
        self._chunks, self._keep, self._frames, self._peak = [], keep, 0, 0.0
        self.sample_rate = settings.sample_rate
        self._stream = sd.InputStream(samplerate=settings.sample_rate,
                                      channels=settings.channels, dtype="float32",
                                      device=resolve_device(settings.device_name),
                                      callback=self._callback)
        self._stream.start()

    def _callback(self, indata, frames, _time, _status):
        peak = float(np.max(np.abs(indata))) if frames else 0.0
        with self._lock:
            self._peak = max(self._peak, peak)
            if self._keep:
                self._chunks.append(indata.copy())
                self._frames += frames

    def read_peak(self) -> float:
        """Highest absolute sample since the last call (0..1)."""
        with self._lock:
            p, self._peak = self._peak, 0.0
        return p

    def stop(self) -> np.ndarray | None:
        if self._stream is None:
            return None
        try:
            self._stream.stop()
            self._stream.close()
        finally:
            self._stream = None
        with self._lock:
            chunks, self._chunks = self._chunks, []
        if not self._keep or not chunks:
            return None
        return np.concatenate(chunks, axis=0)


# ---------------------------------------------------------------- playback
def play(data: np.ndarray, sample_rate: int) -> None:
    sd.stop()
    sd.play(data, sample_rate)


def stop_playback() -> None:
    sd.stop()


# ---------------------------------------------------------------- files
def to_mono(data: np.ndarray) -> np.ndarray:
    return data.mean(axis=1) if data.ndim == 2 else data


def _atomic_write(path: Path, data: np.ndarray, sample_rate: int, subtype: str, fmt: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    sf.write(str(tmp), data, sample_rate, subtype=subtype, format=fmt)
    os.replace(tmp, path)


def save_recording(data: np.ndarray, settings: AudioSettings, path: Path) -> None:
    clipped = np.clip(data, -1.0, 1.0)
    _atomic_write(path, clipped, settings.sample_rate, settings.subtype,
                  settings.extension.upper())


def save_asr_copy(data: np.ndarray, sample_rate: int, path: Path) -> None:
    """16 kHz / 16-bit / mono WAV - the standard input for ASR training."""
    mono = to_mono(data).astype(np.float32)
    if sample_rate != ASR_COPY_RATE:
        mono = soxr.resample(mono, sample_rate, ASR_COPY_RATE, quality="HQ")
    _atomic_write(path, np.clip(mono, -1.0, 1.0), ASR_COPY_RATE, "PCM_16", "WAV")
