# config.py
# ─────────────────────────────────────────────────────────────
# Central configuration for the Bed Exit Monitor.
# Edit these values to customize the app for your deployment.
# ─────────────────────────────────────────────────────────────

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
ALERT_AUDIO_FILE = "alert_message.mp3"

# --- Colors (BGR format — OpenCV uses Blue, Green, Red not RGB) ---
COLOR_LINE_NORMAL   = (0, 255, 0)    # green
COLOR_LINE_ALERT    = (0, 0, 255)    # red
COLOR_SKELETON      = (255, 200, 0)  # cyan-ish
COLOR_KEYPOINT      = (0, 200, 255)  # orange
COLOR_ALERT_OVERLAY = (0, 0, 180)    # dark red
