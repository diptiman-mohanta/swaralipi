"""Packs a speaker folder into a submission zip with SHA-256 checksums."""

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

from . import APP_VERSION
from .storage import now_iso

AUDIO_EXTS = {".wav", ".flac"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def export_speaker(speaker_dir: Path, dest_dir: Path) -> Path:
    speaker_dir, dest_dir = Path(speaker_dir), Path(dest_dir)
    speaker_id = speaker_dir.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{speaker_id}_{datetime.now():%Y%m%d_%H%M%S}.zip"

    files = sorted(p for p in speaker_dir.rglob("*")
                   if p.is_file() and not p.name.endswith(".part"))
    checksums = []
    clips = 0
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in files:
            rel = p.relative_to(speaker_dir).as_posix()
            is_audio = p.suffix.lower() in AUDIO_EXTS
            clips += is_audio and rel.startswith("audio/")
            zf.write(p, f"{speaker_id}/{rel}",
                     compress_type=zipfile.ZIP_STORED if is_audio else zipfile.ZIP_DEFLATED)
            checksums.append(f"{sha256_file(p)}  {rel}")
        info = {"speaker_id": speaker_id, "exported_at": now_iso(), "app_version": APP_VERSION,
                "clip_count": clips, "file_count": len(files)}
        zf.writestr(f"{speaker_id}/submission_info.json", json.dumps(info, indent=2))
        zf.writestr(f"{speaker_id}/checksums.sha256", "\n".join(checksums) + "\n")
    return zip_path
