@echo off
REM build.bat — Build BedExitMonitor for Windows
REM ─────────────────────────────────────────────────────────────────────────────
REM Run this from the bed_exit_monitor folder with your venv activated:
REM
REM   venv\Scripts\activate
REM   build.bat
REM
REM Output:  dist\BedExitMonitor\BedExitMonitor.exe  (and supporting files)
REM
REM Zip the entire dist\BedExitMonitor\ folder to distribute.
REM ─────────────────────────────────────────────────────────────────────────────

echo.
echo ═══════════════════════════════════════════════════════
echo   Bed Exit Monitor  —  Windows Build
echo ═══════════════════════════════════════════════════════
echo.

REM Confirm we're in the right directory
if not exist main.py (
    echo ERROR: main.py not found. Run this script from the bed_exit_monitor folder.
    pause
    exit /b 1
)

REM Confirm virtual environment is active
python -c "import sys; print(sys.prefix)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Make sure your venv is activated.
    pause
    exit /b 1
)

echo [1/3] Installing / upgrading dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [2/3] Cleaning previous build artefacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [3/3] Running PyInstaller...
pyinstaller bed_exit_monitor.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ───────────────────────────────────────────────────────
echo   Build complete!
echo   Executable: dist\BedExitMonitor\BedExitMonitor.exe
echo.
echo   IMPORTANT — before distributing:
echo   1. Open dist\BedExitMonitor\_internal\config.py  (or edit config.py
echo      before building) and confirm N8N_UPLOAD_WEBHOOK is set correctly.
echo   2. Zip the entire dist\BedExitMonitor\ folder.
echo ───────────────────────────────────────────────────────
echo.
pause
