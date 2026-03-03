# bed_exit_monitor.spec
# ──────────────────────────────────────────────────────────────────────────────
# PyInstaller spec for Bed Exit Monitor.
# Works on both Windows and macOS — the build scripts detect the platform.
#
# Build with:
#   Windows:  build.bat
#   macOS:    ./build.sh
#
# Output:   dist/BedExitMonitor/   (a folder you can zip and distribute)
#
# NOTE: Building must be done on each target OS — you cannot cross-compile.
#       Build the .exe on Windows, build the macOS app on a Mac.
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# ── Collect ultralytics (YOLO) package data ────────────────────────────────────
ultra_datas, ultra_binaries, ultra_hiddenimports = collect_all('ultralytics')

# ── Collect numpy data ─────────────────────────────────────────────────────────
# numpy's internal .libs / DLLs must be explicitly collected or PyInstaller
# bundles a broken stub that raises "Numpy is not available" at runtime.
try:
    numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
except Exception:
    numpy_datas, numpy_binaries, numpy_hiddenimports = [], [], []

# ── Collect torch data ─────────────────────────────────────────────────────────
try:
    torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
except Exception:
    torch_datas, torch_binaries, torch_hiddenimports = [], [], []

# ── App-specific data files ────────────────────────────────────────────────────
app_datas = [
    ('yolov8n-pose.pt',   '.'),   # YOLO model — bundled at root
    ('alert_message.mp3', '.'),   # Alert audio — bundled at root
]

all_datas    = app_datas + ultra_datas + torch_datas + numpy_datas
all_binaries = ultra_binaries + torch_binaries + numpy_binaries
all_hidden   = ultra_hiddenimports + torch_hiddenimports + numpy_hiddenimports + [
    'cv2',
    'numpy',
    'pygame',
    'pygame.mixer',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'PIL',
    'PIL._tkinter_finder',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PySide2',
        'PyQt5',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BedExitMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,        # keep console window for diagnostic output
    icon=None,           # add a .ico / .icns path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BedExitMonitor',
)
