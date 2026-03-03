# config.py
# ──────────────────────────────────────────────────────────────────────────────
# Central configuration for the Bed Exit Monitor.
# Edit these values to customize the app for your deployment.
# ──────────────────────────────────────────────────────────────────────────────

import os
import sys


def resource_path(relative: str) -> str:
    """
    Return the absolute path to a bundled resource.
    Works both when running from source (plain Python) and when packaged
    by PyInstaller (sys._MEIPASS is set to the temp extraction folder).
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative)


def clips_dir() -> str:
    """
    Return the directory where alert clips are saved locally.
    When packaged, clips land beside the executable, not in the temp bundle.
    """
    if getattr(sys, "_MEIPASS", None):
        # Running as a PyInstaller bundle — save clips next to the .exe
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.abspath(".")
    path = os.path.join(exe_dir, CLIPS_DIRECTORY)
    os.makedirs(path, exist_ok=True)
    return path


# --- Camera ---
# 0 = built-in webcam, 1 = first USB camera, 2 = second USB camera, etc.
CAMERA_INDEX = 0

# --- Display ---
WINDOW_TITLE = "Bed Exit Monitor"
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720

# --- Threshold Line ---
# The line starts as a horizontal line near the BOTTOM of the frame.
# This represents the foot-end edge of the bed in a typical camera view.
# The operator can drag the two circle handles to reposition it at runtime.
#
# LINE_POINT_1 = left end of the line
# LINE_POINT_2 = right end of the line
LINE_POINT_1 = (100,  580)   # left end, near bottom
LINE_POINT_2 = (1180, 580)   # right end, near bottom

# How close (in pixels) the mouse must be to grab and drag an endpoint.
# Larger = easier to grab.
DRAG_RADIUS = 30

# --- Pose Detection ---
# Confidence threshold: 0.0 = detect everything, 1.0 = only very confident.
POSE_CONFIDENCE = 0.5

# Which body landmarks count as "legs" for the crossing check.
# 13 = left knee, 14 = right knee, 15 = left ankle, 16 = right ankle
LEG_KEYPOINT_INDICES = [13, 14, 15, 16]

# Which side of the line triggers the alert.
# "above" = alert when legs go ABOVE the line (toward top of screen)
# This is correct for a horizontal bed-edge line at the bottom of the frame:
# the patient's legs crossing upward = moving toward the bed edge.
ALERT_SIDE = "above"

# --- Alert ---
# How many consecutive frames a leg must be past the line before alerting.
ALERT_FRAME_THRESHOLD = 10

# Jitsi room name — both the bedside computer and nurse open this URL.
JITSI_ROOM_NAME = "NurseStation-BedMonitor-Room1"

# How long (seconds) before the alert can trigger again.
ALERT_COOLDOWN_SECONDS = 30

# --- Audio ---
BEEP_FREQUENCY = 880   # Hz
BEEP_DURATION  = 1.0   # seconds

# Pre-recorded audio file — place it in the bed_exit_monitor folder.
# Set to None to disable.
ALERT_AUDIO_FILE = resource_path("alert_message.mp3")

# --- Model ---
MODEL_FILE = resource_path("yolov8n-pose.pt")

# --- Rolling Video Buffer ---
# Frames are JPEG-compressed and stored in a deque so RAM stays bounded.
#
# Memory estimate at default settings:
#   15 fps × 300 s = 4 500 frames × ~40 KB ≈ 180 MB
#
BUFFER_MAX_SECONDS  = 300   # seconds of footage to keep (5 minutes)
BUFFER_FPS          = 15    # frames per second stored in the buffer
BUFFER_JPEG_QUALITY = 60    # JPEG quality for buffered frames (1–100)

# --- Clip Storage ---
CLIPS_DIRECTORY = "clips"           # sub-folder name for saved clip files
DELETE_CLIP_AFTER_UPLOAD = True     # remove local file once upload succeeds

# --- n8n Upload Webhook ---
# URL of the n8n webhook workflow that receives the clip and uploads it to
# the BuckeyeBedMonitor folder in Google Drive.
# After importing n8n_upload_workflow.json and activating it, paste the
# Production webhook URL here.
N8N_UPLOAD_WEBHOOK = "https://testbed999.app.n8n.cloud/webhook/bed-exit-upload"

# --- Colors (BGR format — OpenCV uses Blue, Green, Red not RGB) ---
COLOR_LINE_NORMAL    = (0, 255, 0)    # green
COLOR_LINE_ALERT     = (0, 0, 255)    # red
COLOR_SKELETON       = (255, 200, 0)  # cyan-ish
COLOR_KEYPOINT       = (0, 200, 255)  # orange
COLOR_ALERT_OVERLAY  = (0, 0, 180)    # dark red
