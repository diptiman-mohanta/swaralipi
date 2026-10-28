"""IDs, quality checks, script loading, language and microphone detection."""

import numpy as np
import pytest
from openpyxl import Workbook

from recorder import audio, ids, langcheck, qc
from recorder.script_loader import ScriptError, load_script
from tests.conftest import speech_like

SAMPLES = __import__("pathlib").Path(__file__).resolve().parent.parent / "samples"


# ---------------------------------------------------------------- IDs
def test_fingerprint_ignores_formatting():
    a = ids.speaker_fingerprint("Ravi  Kumar", 1999, "M", "751001", "+91 98765 43210")
    b = ids.speaker_fingerprint("ravi kumar", 1999, "M", "751 001", "9876543210")
    assert a == b and len(a) == 8


def test_fingerprint_differs_between_people():
    a = ids.speaker_fingerprint("Ravi Kumar", 1999, "M", "751001", "9876543210")
    b = ids.speaker_fingerprint("Ravi Kumar", 1999, "M", "751001", "9876543211")
    assert a != b


def test_speaker_and_sentence_ids():
    sid = ids.make_speaker_id("eng", "OD", ids.region_code("Khordha", 3), "M", 1999, "7f3a9c2e")
    assert sid == "eng_OD_KHO_M_1999_7f3a9c2e"
    assert ids.script_sentence_id(sid, "12") == sid + "_S000012"
    assert ids.script_sentence_id(sid, 12.0) == sid + "_S000012"
    assert ids.typed_sentence_id(sid).startswith(sid + "_F")


@pytest.mark.parametrize("name,code", [("Khordha", "KHO"), ("East Godavari", "EGO"),
                                       ("North 24 Parganas", "NPA"), ("", "XXX")])
def test_region_code(name, code):
    assert ids.region_code(name, 3) == code


def test_normalize_text():
    assert ids.normalize_text("  Hello\n  world  ") == "Hello world"


# ---------------------------------------------------------------- quality check
def test_good_take_passes():
    r = qc.analyze(speech_like(), 48000)
    assert r["status"] == qc.OK, r["issues"]
    assert r["snr_db"] > 30


def test_clipped_take_fails():
    assert qc.analyze(np.clip(speech_like() * 10, -1, 1), 48000)["status"] == qc.FAIL


def test_silent_take_fails():
    silent = (0.0005 * np.random.default_rng(1).standard_normal(48000 * 2)).astype(np.float32)
    assert qc.analyze(silent[:, None], 48000)["status"] == qc.FAIL


def test_empty_take_fails():
    assert qc.analyze(np.zeros((10, 1), np.float32), 48000)["status"] == qc.FAIL


# ---------------------------------------------------------------- scripts
def test_demo_scripts_load():
    csv_rows = load_script(SAMPLES / "demo_script_english.csv")
    xlsx_rows = load_script(SAMPLES / "demo_script_english.xlsx")
    assert len(csv_rows) == 30 and csv_rows == xlsx_rows
    assert csv_rows[6][1].startswith("Turn left at the big banyan tree,")


def test_script_without_header(tmp_path):
    wb = Workbook()
    wb.active.append([1, "Hello world"])
    wb.active.append([2, "Second line"])
    wb.save(tmp_path / "s.xlsx")
    assert load_script(tmp_path / "s.xlsx") == [("1", "Hello world"), ("2", "Second line")]


def test_script_rejects_duplicate_numbers(tmp_path):
    (tmp_path / "dup.csv").write_text("sentence_no,sentence\n1,A\n1,B\n", encoding="utf-8")
    with pytest.raises(ScriptError):
        load_script(tmp_path / "dup.csv")


# ---------------------------------------------------------------- language / microphone
def test_language_mismatch_detected():
    assert langcheck.mismatch_message("Odia", ["The quick brown fox."])
    assert langcheck.mismatch_message("English", ["ମୋ ନାମ ରାମ।"])
    assert langcheck.mismatch_message("English", ["The quick brown fox."]) is None
    assert langcheck.mismatch_message("Hindi", ["मेरा नाम राम है।"]) is None
    assert langcheck.mismatch_message("English", ["123 456"]) is None


@pytest.mark.parametrize("device,expected", [
    ("Headset (realme Buds T310)  [MME]", audio.BLUETOOTH),
    ("Headset (WH-1000XM4 Hands-Free AG Audio)  [MME]", audio.BLUETOOTH),
    ("Microphone Array (Intel® Smart  [MME]", "Laptop built-in mic"),
    ("Microphone (Yeti Stereo Microphone)  [MME]", "USB microphone"),
    ("Analogue 1 + 2 (Focusrite USB Audio)  [WASAPI]", "Professional XLR mic + interface"),
    ("Headset Microphone (Realtek(R) Audio)  [MME]", "Wired headset mic"),
    ("Microphone (Realtek(R) Audio)  [MME]", None),
])
def test_mic_type_guess(device, expected):
    assert audio.guess_mic_type(device) == expected
