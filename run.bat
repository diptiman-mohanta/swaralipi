@echo off
REM Swaralipi - double-click to start.
REM First run creates .venv and installs the exact versions in requirements.txt
REM (needs internet once). Later runs work fully offline.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo.
        echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/
        echo and tick "Add python.exe to PATH" during installation.
        pause
        exit /b 1
    )
)

fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo Installing required packages - this happens only once...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Package installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
    copy /y requirements.txt .venv\requirements.installed >nul
)

".venv\Scripts\python.exe" app.py
if errorlevel 1 pause
