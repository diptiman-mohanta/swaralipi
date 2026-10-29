"""Paths, option lists and persisted settings."""

import json
import sys
from pathlib import Path

# From source, everything lives in the repo folder. In the packaged Windows app,
# read-only resources are unpacked by PyInstaller (sys._MEIPASS), while config/,
# recordings/ and user_settings.json sit next to Swaralipi.exe so they can be edited.
FROZEN = getattr(sys, "frozen", False)
SOURCE_DIR = Path(__file__).resolve().parent.parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", SOURCE_DIR))
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else SOURCE_DIR

CONFIG_DIR = APP_DIR / "config"
DATA_DIR = BUNDLE_DIR / "data"
ASSETS_DIR = BUNDLE_DIR / "assets"
APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"
CONSENT_FILE = CONFIG_DIR / "consent.md"
PUBLIC_KEY_FILE = CONFIG_DIR / "public_key.pem"
USER_SETTINGS_FILE = APP_DIR / "user_settings.json"
DEFAULT_OUTPUT_DIR = APP_DIR / "recordings"

MODE_TYPED = "typed"      # type transcript first, then read it aloud
MODE_SCRIPT = "script"    # read sentences from a loaded xlsx/csv script

# ---------------------------------------------------------------- audio options
SAMPLE_RATES = [8000, 16000, 22050, 24000, 32000, 44100, 48000, 96000]
BIT_DEPTHS = {          # label -> soundfile subtype
    "16-bit PCM": "PCM_16",
    "24-bit PCM": "PCM_24",
    "32-bit float": "FLOAT",
}
CHANNELS = {"Mono (1 channel)": 1, "Stereo (2 channels)": 2}
FILE_FORMATS = {"WAV": "wav", "FLAC": "flac"}   # lossless only
LOSSY_FORMATS = ["MP3 (lossy - not allowed for datasets)"]
ASR_COPY_RATE = 16000

AUDIO_PRESETS = {
    "ASR + TTS (recommended)": dict(sample_rate=48000, bit_depth="24-bit PCM", channels=1,
                                    file_format="WAV", asr_copy=True),
    "ASR only": dict(sample_rate=16000, bit_depth="16-bit PCM", channels=1,
                     file_format="WAV", asr_copy=False),
    "TTS only": dict(sample_rate=48000, bit_depth="24-bit PCM", channels=1,
                     file_format="WAV", asr_copy=False),
}
CUSTOM_PRESET = "Custom"

# ---------------------------------------------------------------- languages and scripts
# English plus the 22 scheduled languages of India, from data/languages.json.
_LANG_DATA = json.loads((DATA_DIR / "languages.json").read_text(encoding="utf-8"))
LANGUAGE_INFO = {lang["name"]: lang for lang in _LANG_DATA["languages"]}   # name -> details
LANGUAGES = {name: info["code"] for name, info in LANGUAGE_INFO.items()}   # name -> ISO 639-3
SCRIPTS = _LANG_DATA["scripts"]                                            # ISO 15924 -> details
ARABIC_LETTERS = _LANG_DATA["arabic_letters"]


def language_label(name: str) -> str:
    """'Hindi — हिन्दी' for dropdowns; English stays 'English'."""
    native = LANGUAGE_INFO[name]["native"]
    return name if native == name else f"{name} — {native}"


def language_font(name: str) -> str:
    """Font family for text in this language's main script."""
    info = LANGUAGE_INFO.get(name, {})
    return info.get("font") or SCRIPTS[info.get("scripts", ["Latn"])[0]]["font"]


def is_rtl(name: str) -> bool:
    info = LANGUAGE_INFO.get(name, {})
    return SCRIPTS[info.get("scripts", ["Latn"])[0]].get("rtl", False)


# ---------------------------------------------------------------- speaker options
MOTHER_TONGUES = sorted([n for n in LANGUAGES] +
                        ["Bhili", "Bhojpuri", "Garo", "Gondi", "Ho", "Khasi", "Kurukh", "Mizo",
                         "Tulu"]) + ["Other"]
GENDERS = {"Male": "M", "Female": "F", "Other / Non-binary": "O", "Prefer not to say": "X"}
EDUCATION = ["No formal education", "Primary (up to Class 5)", "Middle (Class 6-8)",
             "Secondary (Class 10)", "Higher Secondary (Class 12)", "Diploma / ITI",
             "Graduate", "Postgraduate", "Doctorate (PhD)", "Prefer not to say"]
OCCUPATIONS = ["Student", "Salaried - private sector", "Salaried - government",
               "Self-employed / Business", "Farmer / Agriculture", "Daily wage worker",
               "Homemaker", "Teacher / Academic", "Healthcare worker", "IT / Technology",
               "Retired", "Unemployed", "Prefer not to say", "Other"]
AREA_TYPES = ["Urban", "Semi-urban", "Rural"]
COUNTRIES = ["India", "Bangladesh", "Bhutan", "Nepal", "Sri Lanka", "Pakistan",
             "United States", "United Kingdom", "Canada", "Australia", "Other"]
ENVIRONMENTS = ["Quiet room (treated / studio)", "Quiet room (home)", "Office", "Classroom",
                "Outdoor", "Vehicle", "Other"]
MIC_TYPES = ["Laptop built-in mic", "Wired headset mic", "USB microphone",
             "Professional XLR mic + interface", "Bluetooth headset", "Phone mic", "Other"]
AGE_GROUPS = [(18, 25), (26, 35), (36, 45), (46, 55), (56, 65), (66, 120)]


def age_group(age: int) -> str:
    if age < 18:
        return "under-18"
    for lo, hi in AGE_GROUPS:
        if lo <= age <= hi:
            return f"{lo}-{hi}" if hi < 120 else f"{lo}+"
    return "unknown"


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def load_app_config() -> dict:
    cfg = {"organisation_name": "Your Organisation", "project_name": "Speech Dataset",
           "contact_email": "", "consent_version": "1.0", "minimum_age": 18,
           "default_language": "English", "locked_audio_preset": None,
           "submission_instructions": ""}
    cfg.update(_read_json(APP_CONFIG_FILE, {}))
    return cfg


def contact_configured(cfg: dict) -> bool:
    """False while app_config.json still has the template placeholders."""
    email = cfg.get("contact_email", "")
    return "@" in email and not email.endswith(".example") \
        and cfg.get("organisation_name") not in ("", "Your Organisation Name", "Your Organisation")


def where_to_send(cfg: dict) -> str:
    """Tells contributors where their zip goes. The app never sends anything itself."""
    custom = cfg.get("submission_instructions", "").strip()
    if custom:
        return custom
    if contact_configured(cfg):
        return f"Send it to {cfg['organisation_name']} at {cfg['contact_email']}."
    return ("Send it to the person or organisation that asked you to record. This copy of the "
            "app has no contact details set up.")


def load_india_locations() -> dict:
    """Returns {state_name: {"code": "OD", "districts": [...]}}."""
    data = _read_json(DATA_DIR / "india_locations.json", {"states": []})
    return {s["name"]: {"code": s["code"], "districts": s["districts"]} for s in data["states"]}


def load_user_settings() -> dict:
    return _read_json(USER_SETTINGS_FILE, {})


def save_user_settings(settings: dict) -> None:
    try:
        USER_SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass   # remembering settings is a convenience only
