"""Build the Windows app and zip it for a GitHub release.

    .venv\\Scripts\\python tools\\build_windows.py

Result: dist/Swaralipi-v<version>-windows.zip, containing
    Swaralipi/Swaralipi.exe     the app (double-click to start)
    Swaralipi/config/           editable settings, consent text and public key
    Swaralipi/samples/          demo scripts for script mode
    Swaralipi/README.txt        short instructions
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from recorder import APP_VERSION  # noqa: E402

QUICK_START = f"""Swaralipi {APP_VERSION} - offline speech dataset recorder
==========================================================

1. Double-click Swaralipi.exe.
   (Windows may show "Windows protected your PC" because the app is new and unsigned.
    Click "More info" and then "Run anyway".)
2. Choose a mode, check the microphone, read the consent page with the speaker,
   enter the speaker details and record.
3. When a speaker is finished, click "Finish session" and "Export zip now".
   Send the zip from the recordings\\submissions folder to the project team.

Recordings are saved in the "recordings" folder next to Swaralipi.exe unless you
choose another folder. Nothing is uploaded from this computer.

Demo scripts for "Read sentences from a script file" are in the samples folder.

Project page: https://github.com/diptiman-mohanta/swaralipi
"""


def main() -> int:
    dist = ROOT / "dist"
    subprocess.run([sys.executable, "-m", "PyInstaller", "swaralipi.spec", "--noconfirm",
                    "--clean"], cwd=ROOT, check=True)
    app_dir = dist / "Swaralipi"

    shutil.copytree(ROOT / "config", app_dir / "config", dirs_exist_ok=True)
    shutil.copytree(ROOT / "samples", app_dir / "samples", dirs_exist_ok=True)
    shutil.copy2(ROOT / "LICENSE", app_dir / "LICENSE.txt")
    (app_dir / "README.txt").write_text(QUICK_START, encoding="utf-8")

    zip_path = dist / f"Swaralipi-v{APP_VERSION}-windows.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(app_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(dist).as_posix())
    print(f"\nBuilt {zip_path} ({zip_path.stat().st_size / 1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
