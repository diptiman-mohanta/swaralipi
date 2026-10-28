"""Merge contributors' submission zips into one dataset (run by the project team).

    .venv\\Scripts\\python tools\\merge_submissions.py <folder with zips> <output folder>
        [--private-key keys\\private_key.pem]

Output:
    <output>/speakers/<speaker_id>/...   all audio and per-speaker files
    <output>/transcripts.xlsx           sentence_id | sentence  (all speakers)
    <output>/manifest.csv / .jsonl      full anonymous metadata (all clips)
    <output>/speakers.csv               anonymous speaker profiles
    <output>/merge_report.txt           checksum failures, duplicates, conflicts
    <output>/PRIVATE_contacts.xlsx      names / mobiles / emails - INTERNAL ONLY,
                                        never include in a dataset release
"""

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font  # noqa: E402

from recorder.crypto import decrypt_json  # noqa: E402
from recorder.storage import MANIFEST_FIELDS  # noqa: E402

PRIVATE_FIELDS = ["speaker_id", "name", "mobile", "email", "pincode", "saved_at", "source_zip"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_xlsx(path: Path, header: list, rows: list) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    ws.freeze_panes = "A2"
    wb.save(path)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("zips", type=Path, help="folder containing submission .zip files")
    ap.add_argument("output", type=Path, help="output folder for the merged dataset")
    ap.add_argument("--private-key", type=Path, help="private_key.pem to decrypt contact details")
    args = ap.parse_args()

    out = args.output
    speakers_dir = out / "speakers"
    speakers_dir.mkdir(parents=True, exist_ok=True)
    report = []
    clips: dict[str, dict] = {}
    profiles: dict[str, dict] = {}
    contacts: list[dict] = []
    consents: dict[str, list] = defaultdict(list)

    zips = sorted(args.zips.glob("*.zip"))
    if not zips:
        print(f"No .zip files found in {args.zips}")
        return 1

    for zp in zips:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            try:
                with zipfile.ZipFile(zp) as zf:
                    zf.extractall(tmp)
            except zipfile.BadZipFile:
                report.append(f"[BAD ZIP] {zp.name}: cannot be opened - ask for it again.")
                continue
            for sdir in [d for d in tmp.iterdir() if d.is_dir()]:
                sid = sdir.name
                # --- verify checksums
                bad = []
                sums = sdir / "checksums.sha256"
                if sums.exists():
                    for line in sums.read_text(encoding="utf-8").splitlines():
                        digest, _, rel = line.partition("  ")
                        f = sdir / rel
                        if not f.exists() or sha256(f) != digest:
                            bad.append(rel)
                else:
                    report.append(f"[NO CHECKSUMS] {zp.name}")
                if bad:
                    report.append(f"[CHECKSUM FAIL] {zp.name}: {len(bad)} damaged/missing files "
                                  f"(e.g. {bad[0]}) - skipped those clips.")

                # --- private contact details (kept out of the dataset folder)
                priv_dir = sdir / "private"
                enc, plain = priv_dir / "contact.enc", priv_dir / "contact.json"
                contact = None
                if enc.exists():
                    if args.private_key:
                        try:
                            contact = decrypt_json(json.loads(enc.read_text()), args.private_key)
                        except Exception as e:
                            report.append(f"[DECRYPT FAIL] {zp.name}: {e}")
                    else:
                        report.append(f"[ENCRYPTED] {sid}: contact details need --private-key")
                elif plain.exists():
                    contact = json.loads(plain.read_text(encoding="utf-8"))
                if contact:
                    contacts.append({**contact, "source_zip": zp.name})
                shutil.rmtree(priv_dir, ignore_errors=True)

                # --- copy files, detecting conflicts
                dest = speakers_dir / sid
                for f in sdir.rglob("*"):
                    if not f.is_file():
                        continue
                    rel = f.relative_to(sdir).as_posix()
                    if rel in bad or rel in ("checksums.sha256", "submission_info.json"):
                        continue
                    target = dest / rel
                    if target.exists() and rel.startswith(("audio/", "audio_16k/")) \
                            and sha256(target) != sha256(f):
                        report.append(f"[CONFLICT] {sid}/{rel}: different audio in "
                                      f"{zp.name}; kept the newer submission.")
                    if f.suffix in (".json", ".jsonl", ".csv", ".xlsx"):
                        continue   # metadata is merged across submissions below
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, target)

                # --- metadata
                if (sdir / "speaker.json").exists():
                    profiles[sid] = json.loads((sdir / "speaker.json").read_text(encoding="utf-8"))
                if (sdir / "consent.json").exists():
                    for c in json.loads((sdir / "consent.json").read_text(encoding="utf-8")):
                        if c not in consents[sid]:
                            consents[sid].append(c)
                bad_ids = {Path(b).stem for b in bad}
                for rec in read_jsonl(sdir / "manifest.jsonl"):
                    if rec["sentence_id"] in bad_ids:
                        continue
                    rec["audio_filepath"] = f"speakers/{sid}/{rec['audio_filepath']}"
                    if rec.get("audio_16k_filepath"):
                        rec["audio_16k_filepath"] = f"speakers/{sid}/{rec['audio_16k_filepath']}"
                    clips[rec["sentence_id"]] = rec
                print(f"  merged {zp.name}")

    # --- duplicates: same person under different IDs, repeated sentences
    by_fp = defaultdict(set)
    for sid in profiles:
        by_fp[sid.rsplit("_", 1)[-1]].add(sid)
    for fp, sids in by_fp.items():
        if len(sids) > 1:
            report.append(f"[SAME PERSON?] fingerprint {fp} appears in: {', '.join(sorted(sids))}")
    seen = defaultdict(list)
    for rec in clips.values():
        seen[(rec["speaker_id"], rec["text"].casefold())].append(rec["sentence_id"])
    for (sid, _), sids in seen.items():
        if len(sids) > 1:
            report.append(f"[REPEATED TEXT] {sid}: {', '.join(sids)}")

    # --- write merged files
    rows = sorted(clips.values(), key=lambda r: r["sentence_id"])
    for sid, profile in profiles.items():
        sdest = speakers_dir / sid
        sdest.mkdir(parents=True, exist_ok=True)
        (sdest / "speaker.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False),
                                            encoding="utf-8")
        (sdest / "consent.json").write_text(json.dumps(consents[sid], indent=2,
                                                       ensure_ascii=False), encoding="utf-8")
        if not consents[sid]:
            report.append(f"[NO CONSENT] {sid}: no consent record - do not use this data.")
        own = [r for r in rows if r["speaker_id"] == sid]
        (sdest / "manifest.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in own), encoding="utf-8")
        write_xlsx(sdest / "transcripts.xlsx", ["sentence_id", "sentence"],
                   [[r["sentence_id"], r["text"]] for r in own])
    (out / "manifest.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    with open(out / "manifest.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    write_xlsx(out / "transcripts.xlsx", ["sentence_id", "sentence"],
               [[r["sentence_id"], r["text"]] for r in rows])
    if profiles:
        fields = list(dict.fromkeys(k for p in profiles.values() for k in p))
        with open(out / "speakers.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(profiles.values())
    if contacts:
        write_xlsx(out / "PRIVATE_contacts.xlsx", PRIVATE_FIELDS,
                   [[c.get(k, "") for k in PRIVATE_FIELDS] for c in contacts])

    hours = sum(float(r.get("duration_sec") or 0) for r in rows) / 3600
    summary = (f"Zips: {len(zips)}   Speakers: {len(profiles)}   Clips: {len(rows)}   "
               f"Audio: {hours:.2f} h")
    (out / "merge_report.txt").write_text(summary + "\n\n" + ("\n".join(report) or "No issues.")
                                          + "\n", encoding="utf-8")
    print("\n" + summary)
    print(f"Report: {out / 'merge_report.txt'}  ({len(report)} notes)")
    if contacts:
        print(f"PRIVATE contact list: {out / 'PRIVATE_contacts.xlsx'}  (internal only!)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
