"""Paths, option lists and persisted settings."""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"
CONSENT_FILE = CONFIG_DIR / "consent.md"
PUBLIC_KEY_FILE = CONFIG_DIR / "public_key.pem"
USER_SETTINGS_FILE = ROOT_DIR / "user_settings.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "recordings"

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

# ---------------------------------------------------------------- speaker options
LANGUAGES = {   # display name -> ISO 639-3 code
    "English": "eng", "Assamese": "asm", "Bengali": "ben", "Gujarati": "guj",
    "Hindi": "hin", "Kannada": "kan", "Malayalam": "mal", "Marathi": "mar",
    "Odia": "ory", "Punjabi": "pan", "Tamil": "tam", "Telugu": "tel", "Urdu": "urd",
}
MOTHER_TONGUES = ["Assamese", "Bengali", "Bhojpuri", "Bodo", "Dogri", "English", "Gujarati",
                  "Hindi", "Kannada", "Kashmiri", "Konkani", "Maithili", "Malayalam", "Manipuri",
                  "Marathi", "Nepali", "Odia", "Punjabi", "Sanskrit", "Santali", "Sindhi",
                  "Tamil", "Telugu", "Tulu", "Urdu", "Other"]
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
           "default_language": "English", "locked_audio_preset": None}
    cfg.update(_read_json(APP_CONFIG_FILE, {}))
    return cfg


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
