#!/usr/bin/env bash
# Swaralipi - Linux / macOS launcher.
# First run creates .venv and installs requirements.txt (needs internet once).
# Linux also needs PortAudio:  sudo apt install libportaudio2
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

if ! cmp -s requirements.txt .venv/requirements.installed; then
    echo "Installing required packages - this happens only once..."
    .venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
    cp requirements.txt .venv/requirements.installed
fi

exec .venv/bin/python app.py
