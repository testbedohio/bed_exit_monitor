# main.py
# ─────────────────────────────────────────────────────────────
# Entry point for the Bed Exit Monitor.
# Responsibilities:
#   - Open the USB camera
#   - Run the main video loop (read frame → detect → check → draw → display)
#   - Handle mouse dragging to reposition the threshold line
#   - Draw the settings panel and handle toggle clicks
#   - Manage alert state and cooldown timer
#
# Run with:   python main.py
# ─────────────────────────────────────────────────────────────

import cv2
import numpy as np
import time

import config
from detector import PoseDetector, check_crossing
from alert import trigger_alert


# ── Settings state ────────────────────────────────────────────
settings = {
    "face_blur":     False,
    "skeleton_only": False,
}

# ── Threshold line state ──────────────────────────────────────
line_p1 = list(config.LINE_POINT_1)
line_p2 = list(config.LINE_POINT_2)
dragging_point = None

# ── Alert state ───────────────────────────────────────────────
consecutive_alert_frames = 0
last_alert_time          = 0.0
alert_active             = False

# ── Layout constants ──────────────────────────────────────────
PANEL_WIDTH   = 220    # width of the right-side settings panel in pixels
VIDEO_WIDTH   = config.FRAME_WIDTH
VIDEO_HEIGHT  = config.FRAME_HEIGHT
TOTAL_WIDTH   = VIDEO_WIDTH + PANEL_WIDTH

# Toggle button geometry (within the panel)
# Each toggle is a rounded rectangle the operator clicks to flip a setting.
TOGGLES = [
    {
        "key":   "face_blur",
        "label": "Face Blur",
        "desc":  "Hides patient identity",
        "y":     130,    # vertical position of this toggle in the panel
    },
    {
        "key":   "skeleton_only",
        "label": "Skeleton Only",
        "desc":  "Black background",
        "y":     230,
    },
]

TOGGLE_X      = VIDEO_WIDTH + 20   # left edge of toggle button
TOGGLE_W      = PANEL_WIDTH - 40   # toggle button width
TOGGLE_H      = 44                 # toggle button height


# ── Mouse callback ────────────────────────────────────────────

def mouse_callback(event, x, y, flags, param):
    """
    Handles all mouse interaction:
      - Dragging the threshold line endpoints (left side of window)
      - Clicking toggle buttons (right side / settings panel)
    """
    global dragging_point, line_p1, line_p2

    if event == cv2.EVENT_LBUTTONDOWN:

        # ── Check toggle buttons first ────────────────────────
        for toggle in TOGGLES:
            tx, ty = TOGGLE_X, toggle["y"]
            if tx <= x <= tx + TOGGLE_W and ty <= y <= ty + TOGGLE_H:
                settings[toggle["key"]] = not settings[toggle["key"]]
                return   # handled — don't also check line dragging

        # ── Check threshold line endpoints ────────────────────
        dist_p1 = np.hypot(x - line_p1[0], y - line_p1[1])
        dist_p2 = np.hypot(x - line_p2[0], y - line_p2[1])
        if dist_p1 < config.DRAG_RADIUS:
            dragging_point = "p1"
        elif dist_p2 < config.DRAG_RADIUS:
            dragging_point = "p2"

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging_point == "p1":
            line_p1[0], line_p1[1] = x, y
        elif dragging_point == "p2":
            line_p2[0], line_p2[1] = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        dragging_point = None


# ── Drawing helpers ───────────────────────────────────────────

def draw_settings_panel(canvas: np.ndarray):
    """
    Draw the settings panel on the right side of the canvas.

    HOW THE PANEL IS DRAWN:
    OpenCV doesn't have a built-in GUI widget system — it's primarily
    a computer vision library. So we draw the panel manually using
    rectangles, lines, and text, just like drawing on an image.
    Mouse clicks are then checked against these rectangles to detect
    button presses.
    """
    # Panel background
    cv2.rectangle(canvas,
                  (VIDEO_WIDTH, 0),
                  (TOTAL_WIDTH, VIDEO_HEIGHT),
                  (30, 30, 30), -1)   # dark grey, filled

    # Panel border line
    cv2.line(canvas,
             (VIDEO_WIDTH, 0),
             (VIDEO_WIDTH, VIDEO_HEIGHT),
             (80, 80, 80), 1)

    # Title
    cv2.putText(canvas, "SETTINGS",
                (VIDEO_WIDTH + 20, 40),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (200, 200, 200), 1)
    cv2.line(canvas,
             (VIDEO_WIDTH + 20, 55),
             (TOTAL_WIDTH - 20, 55),
             (80, 80, 80), 1)

    # Draw each toggle button
    for toggle in TOGGLES:
        is_on = settings[toggle["key"]]
        tx    = TOGGLE_X
        ty    = toggle["y"]

        # Button background — green when ON, dark when OFF
        btn_color = (0, 140, 0) if is_on else (60, 60, 60)
        cv2.rectangle(canvas,
                      (tx, ty),
                      (tx + TOGGLE_W, ty + TOGGLE_H),
                      btn_color, -1)
        cv2.rectangle(canvas,
                      (tx, ty),
                      (tx + TOGGLE_W, ty + TOGGLE_H),
                      (120, 120, 120), 1)   # border

        # Toggle label
        cv2.putText(canvas, toggle["label"],
                    (tx + 10, ty + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # ON / OFF indicator text
        status_text  = "ON" if is_on else "OFF"
        status_color = (180, 255, 180) if is_on else (160, 160, 160)
        cv2.putText(canvas, status_text,
                    (tx + 10, ty + 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, status_color, 1)

        # Description text below button
        cv2.putText(canvas, toggle["desc"],
                    (tx + 2, ty + TOGGLE_H + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (120, 120, 120), 1)


def draw_threshold_line(frame: np.ndarray, alert: bool):
    """Draw the draggable threshold line and its endpoint handles."""
    color = config.COLOR_LINE_ALERT if alert else config.COLOR_LINE_NORMAL
    p1    = tuple(line_p1)
    p2    = tuple(line_p2)

    cv2.line(frame, p1, p2, color, 2)
    cv2.circle(frame, p1, config.DRAG_RADIUS, color,
               -1 if dragging_point == "p1" else 2)
    cv2.circle(frame, p2, config.DRAG_RADIUS, color,
               -1 if dragging_point == "p2" else 2)
    cv2.putText(frame, "Bed Edge", (p1[0] + 10, p1[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def draw_alert_overlay(frame: np.ndarray):
    """Semi-transparent red overlay + warning text when alert is active."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]),
                  config.COLOR_ALERT_OVERLAY, -1)
    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

    text  = "! BED EXIT DETECTED !"
    scale = 1.4
    thick = 3
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, thick)
    cx = (frame.shape[1] - tw) // 2
    cy = (frame.shape[0] + th) // 2
    cv2.putText(frame, text, (cx, cy), cv2.FONT_HERSHEY_DUPLEX,
                scale, (255, 255, 255), thick)


def draw_hud(frame: np.ndarray, fps: float):
    """FPS counter and keyboard instructions."""
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "Drag circles to move bed edge line  |  Q to quit",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)


def draw_offending_points(frame: np.ndarray, points: list):
    """Highlight leg joints that have crossed the line."""
    for pt in points:
        cv2.circle(frame, pt, 12, config.COLOR_LINE_ALERT, -1)
        cv2.circle(frame, pt, 14, (255, 255, 255), 2)


# ── Main loop ─────────────────────────────────────────────────

def main():
    global consecutive_alert_frames, last_alert_time, alert_active

    print(f"[Main] Opening camera index {config.CAMERA_INDEX}...")
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  VIDEO_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)

    if not cap.isOpened():
        print(f"[Main] ERROR: Could not open camera {config.CAMERA_INDEX}.")
        print("  Try changing CAMERA_INDEX in config.py (0, 1, 2...)")
        return

    cv2.namedWindow(config.WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_TITLE, TOTAL_WIDTH, VIDEO_HEIGHT)
    cv2.setMouseCallback(config.WINDOW_TITLE, mouse_callback)

    detector = PoseDetector()

    print("[Main] Running. Press Q in the window to quit.")

    fps_timer   = time.time()
    fps         = 0.0
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Main] Camera read failed.")
            break

        # ── Apply privacy settings ──────────────────────────
        if settings["face_blur"]:
            frame = detector.apply_face_blur(frame)

        if settings["skeleton_only"]:
            # Replace the video feed with a black canvas + skeleton
            video_frame = detector.render_skeleton_only(frame)
        else:
            # Draw the full annotated skeleton on the real video
            video_frame = detector.draw_skeleton(frame)

        # ── Pose / crossing logic ───────────────────────────
        # Always run crossing check on the real frame (not the black canvas)
        leg_points = detector.get_leg_keypoints(frame)

        crossing, offending_pts = check_crossing(
            leg_points,
            tuple(line_p1),
            tuple(line_p2)
        )

        if crossing:
            consecutive_alert_frames += 1
        else:
            consecutive_alert_frames = max(0, consecutive_alert_frames - 1)

        now             = time.time()
        cooldown_passed = (now - last_alert_time) > config.ALERT_COOLDOWN_SECONDS
        should_alert    = (consecutive_alert_frames >= config.ALERT_FRAME_THRESHOLD
                           and cooldown_passed)

        if should_alert:
            alert_active             = True
            last_alert_time          = now
            consecutive_alert_frames = 0
            trigger_alert()

        if alert_active and (now - last_alert_time) > 3.0:
            alert_active = False

        # ── Drawing ──────────────────────────────────────────
        if alert_active:
            draw_alert_overlay(video_frame)

        draw_offending_points(video_frame, offending_pts)
        draw_threshold_line(video_frame, alert=bool(offending_pts))

        frame_count += 1
        elapsed = now - fps_timer
        if elapsed >= 1.0:
            fps         = frame_count / elapsed
            fps_timer   = now
            frame_count = 0

        draw_hud(video_frame, fps)

        # ── Compose final canvas (video + settings panel) ────
        # Create a wide canvas and place the video on the left,
        # then draw the settings panel on the right.
        canvas = np.zeros((VIDEO_HEIGHT, TOTAL_WIDTH, 3), dtype=np.uint8)
        canvas[0:VIDEO_HEIGHT, 0:VIDEO_WIDTH] = video_frame
        draw_settings_panel(canvas)

        cv2.imshow(config.WINDOW_TITLE, canvas)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[Main] Exited cleanly.")


if __name__ == "__main__":
    main()
