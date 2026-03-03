#!/bin/bash
# build.sh — Build BedExitMonitor for macOS
# ─────────────────────────────────────────────────────────────────────────────
# Run this from the bed_exit_monitor folder with your venv activated:
#
#   source venv/bin/activate
#   chmod +x build.sh
#   ./build.sh
#
# Output:  dist/BedExitMonitor/BedExitMonitor  (and supporting files)
#
# Zip the entire dist/BedExitMonitor/ folder to distribute.
# ─────────────────────────────────────────────────────────────────────────────

set -e   # exit immediately on any error

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Bed Exit Monitor  —  macOS Build"
echo "═══════════════════════════════════════════════════════"
echo ""

# Confirm we're in the right directory
if [ ! -f main.py ]; then
    echo "ERROR: main.py not found. Run this script from the bed_exit_monitor folder."
    exit 1
fi

echo "[1/3] Installing / upgrading dependencies…"
pip install -r requirements.txt --quiet

echo "[2/3] Cleaning previous build artefacts…"
rm -rf build dist

echo "[3/3] Running PyInstaller…"
pyinstaller bed_exit_monitor.spec --noconfirm

echo ""
echo "───────────────────────────────────────────────────────"
echo "  Build complete!"
echo "  Executable: dist/BedExitMonitor/BedExitMonitor"
echo ""
echo "  IMPORTANT — before distributing:"
echo "  1. Confirm N8N_UPLOAD_WEBHOOK in config.py is correct."
echo "  2. Zip the entire dist/BedExitMonitor/ folder."
echo "───────────────────────────────────────────────────────"
echo ""
