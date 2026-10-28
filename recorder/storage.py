"""Per-speaker output folder: audio, transcripts.xlsx, manifests, profile, consent.

Layout (one folder per speaker, which is also what gets zipped and sent):

    <output_dir>/<speaker_id>/
        audio/<sentence_id>.wav         master recording (chosen settings)
        audio_16k/<sentence_id>.wav     16 kHz / 16-bit mono ASR copy (optional)
        transcripts.xlsx                sentence_id | sentence
        manifest.jsonl / manifest.csv   full anonymous metadata, one row per clip
        speaker.json                    anonymous speaker profile
        consent.json                    consent records
        private/contact.enc             name / mobile / email (encrypted) - never published
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from . import crypto

MANIFEST_FIELDS = [
    "sentence_id", "speaker_id", "text", "audio_filepath", "audio_16k_filepath", "duration_sec",
    "sample_rate", "bit_depth", "channels", "file_format", "language", "mode", "script_file",
    "script_sentence_no", "gender", "birth_year", "age_at_recording", "age_group",
    "mother_tongue", "education", "occupation", "area_type", "country", "state", "district",
    "pincode_prefix", "recording_environment", "microphone_type", "input_device",
    "peak_dbfs", "noise_floor_dbfs", "snr_db", "clipped_samples", "lead_silence_sec",
    "trail_silence_sec", "qc_status", "qc_issues", "recorded_at", "app_version",
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8", newline="")
    os.replace(tmp, path)


class SpeakerStore:
    def __init__(self, output_dir: Path, speaker_id: str):
        self.speaker_id = speaker_id
        self.dir = Path(output_dir) / speaker_id
        self.audio_dir = self.dir / "audio"
        self.asr_dir = self.dir / "audio_16k"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, dict] = {}
        manifest = self.dir / "manifest.jsonl"
        if manifest.exists():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.records[rec["sentence_id"]] = rec

    # ------------------------------------------------------------ profile
    def save_profile(self, public: dict, private: dict) -> bool:
        """Writes the anonymous profile and the private contact file.
        Returns True if the private file was encrypted."""
        profile_path = self.dir / "speaker.json"
        if profile_path.exists():
            old = json.loads(profile_path.read_text(encoding="utf-8"))
            public = {**public, "created_at": old.get("created_at", public.get("created_at"))}
        _write_text_atomic(profile_path, json.dumps(public, indent=2, ensure_ascii=False))

        private_dir = self.dir / "private"
        private_dir.mkdir(exist_ok=True)
        payload = {"speaker_id": self.speaker_id, **private, "saved_at": now_iso()}
        if crypto.encryption_available():
            envelope = crypto.encrypt_json(payload)
            _write_text_atomic(private_dir / "contact.enc", json.dumps(envelope, indent=2))
            (private_dir / "contact.json").unlink(missing_ok=True)
            return True
        _write_text_atomic(private_dir / "contact.json",
                           json.dumps(payload, indent=2, ensure_ascii=False))
        return False

    def add_consent(self, consent: dict) -> None:
        path = self.dir / "consent.json"
        records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        records.append({"speaker_id": self.speaker_id, **consent})
        _write_text_atomic(path, json.dumps(records, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------ clips
    def audio_path(self, sentence_id: str, ext: str) -> Path:
        return self.audio_dir / f"{sentence_id}.{ext}"

    def asr_path(self, sentence_id: str) -> Path:
        return self.asr_dir / f"{sentence_id}.wav"

    def has(self, sentence_id: str) -> bool:
        return sentence_id in self.records

    def add_record(self, record: dict) -> None:
        """Adds or replaces a clip and rewrites all derived files.
        Raises PermissionError if transcripts.xlsx is open in Excel (manifests are
        still saved; the xlsx is rebuilt on the next submit)."""
        old = self.records.get(record["sentence_id"])
        if old and old.get("audio_filepath") != record.get("audio_filepath"):
            (self.dir / old["audio_filepath"]).unlink(missing_ok=True)
        self.records[record["sentence_id"]] = record
        self._write_manifests()
        self.write_transcripts_xlsx()

    def _write_manifests(self) -> None:
        rows = list(self.records.values())
        _write_text_atomic(self.dir / "manifest.jsonl",
                           "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        tmp = self.dir / "manifest.csv.part"
        with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, self.dir / "manifest.csv")

    def write_transcripts_xlsx(self) -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = "transcripts"
        ws.append(["sentence_id", "sentence"])
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for rec in self.records.values():
            ws.append([rec["sentence_id"], rec["text"]])
        ws.column_dimensions["A"].width = 48
        ws.column_dimensions["B"].width = 100
        ws.freeze_panes = "A2"
        tmp = self.dir / "transcripts.part.xlsx"
        wb.save(tmp)
        os.replace(tmp, self.dir / "transcripts.xlsx")

    def remove_if_empty(self) -> bool:
        """Deletes the speaker folder if no recording was ever saved in it (for example
        after the speaker details are corrected and the Speaker ID changes)."""
        if self.records or any(self.audio_dir.glob("*")) or any(self.asr_dir.glob("*")):
            return False
        known = ["speaker.json", "consent.json", "private/contact.json", "private/contact.enc"]
        for rel in known:
            (self.dir / rel).unlink(missing_ok=True)
        for d in (self.dir / "private", self.audio_dir, self.asr_dir, self.dir):
            try:
                d.rmdir()   # only succeeds when empty
            except OSError:
                pass
        return not self.dir.exists()

    def total_duration(self) -> float:
        return sum(float(r.get("duration_sec") or 0) for r in self.records.values())


def list_speakers(output_dir: Path) -> list[dict]:
    """Speaker folders in an output directory, with clip counts, for the export screen."""
    out = []
    root = Path(output_dir)
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if (d / "speaker.json").is_file():
            manifest = d / "manifest.jsonl"
            clips, seconds = 0, 0.0
            if manifest.exists():
                for line in manifest.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        clips += 1
                        seconds += float(json.loads(line).get("duration_sec") or 0)
            out.append({"speaker_id": d.name, "path": d, "clips": clips, "seconds": seconds})
    return out
