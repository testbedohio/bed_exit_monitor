# detector.py
# ─────────────────────────────────────────────────────────────
# Handles pose estimation and the "has a leg crossed the line?" logic.
#
# HOW YOLO POSE WORKS:
#   YOLOv8 Pose is a neural network trained to find people in images
#   and return the (x, y) pixel coordinates of 17 body joints per person.
#   We then check if any leg joint has crossed to the "wrong side" of
#   the operator-defined threshold line.
#
# COCO KEYPOINT INDEX REFERENCE:
#   0  = nose
#   1  = left eye,   2  = right eye
#   3  = left ear,   4  = right ear
#   5  = left shoulder, 6 = right shoulder
#   7  = left elbow,    8 = right elbow
#   9  = left wrist,   10 = right wrist
#   11 = left hip,     12 = right hip
#   13 = left knee,    14 = right knee
#   15 = left ankle,   16 = right ankle
# ─────────────────────────────────────────────────────────────

import cv2
import numpy as np
from ultralytics import YOLO

import config

# COCO skeleton connections — pairs of keypoint indices to draw as bones
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2),           # nose to eyes
    (1, 3), (2, 4),           # eyes to ears
    (5, 6),                   # shoulders
    (5, 7), (7, 9),           # left arm
    (6, 8), (8, 10),          # right arm
    (5, 11), (6, 12),         # torso sides
    (11, 12),                 # hips
    (11, 13), (13, 15),       # left leg
    (12, 14), (14, 16),       # right leg
]


class PoseDetector:
    def __init__(self):
        """
        Load the YOLOv8 pose model.
        'yolov8n-pose.pt' is the nano (smallest/fastest) version.
        Downloads automatically on first run (~6 MB).
        """
        print("[Detector] Loading YOLOv8 pose model...")
        self.model = YOLO("yolov8n-pose.pt")
        print("[Detector] Model ready.")

    def _run_model(self, frame: np.ndarray):
        """Run the model once and return results. Used internally."""
        return self.model(frame, conf=config.POSE_CONFIDENCE, verbose=False)

    def get_leg_keypoints(self, frame: np.ndarray) -> list:
        """
        Run pose detection and return (x, y) pixel positions for all
        leg joints found across ALL people in the frame.
        """
        results = self._run_model(frame)
        leg_points = []

        for result in results:
            if result.keypoints is None:
                continue
            keypoints_xy = result.keypoints.xy.cpu().numpy()
            for person_kps in keypoints_xy:
                for idx in config.LEG_KEYPOINT_INDICES:
                    x, y = person_kps[idx]
                    if x > 0 and y > 0:
                        leg_points.append((int(x), int(y)))

        return leg_points

    def get_all_keypoints(self, frame: np.ndarray) -> list:
        """
        Return all 17 keypoints for every person detected.
        Returns a list of arrays, one per person, shaped [17, 2].
        """
        results = self._run_model(frame)
        all_people = []

        for result in results:
            if result.keypoints is None:
                continue
            keypoints_xy = result.keypoints.xy.cpu().numpy()
            for person_kps in keypoints_xy:
                all_people.append(person_kps)

        return all_people

    def draw_skeleton(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw the full pose skeleton on the frame and return it.
        Uses ultralytics' built-in plot() for convenience.
        """
        results = self._run_model(frame)
        annotated = results[0].plot(
            boxes=False,
            labels=False,
            kpt_radius=5,
        )
        return annotated

    def render_skeleton_only(self, frame: np.ndarray) -> np.ndarray:
        """
        Returns a BLACK frame with only the pose skeleton drawn on it.
        No video feed visible — maximum privacy mode.

        HOW IT WORKS:
        Instead of drawing on the camera frame, we create a blank black
        canvas of the same size and draw the skeleton bones and joints on
        that instead.
        """
        h, w = frame.shape[:2]
        canvas = np.zeros((h, w, 3), dtype=np.uint8)   # black background

        all_people = self.get_all_keypoints(frame)

        for person_kps in all_people:
            # Draw bones (lines between connected joints)
            for (i, j) in SKELETON_CONNECTIONS:
                x1, y1 = person_kps[i]
                x2, y2 = person_kps[j]
                # Only draw if both endpoints were detected (not 0,0)
                if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                    cv2.line(canvas,
                             (int(x1), int(y1)),
                             (int(x2), int(y2)),
                             config.COLOR_SKELETON, 2)

            # Draw joint dots
            for idx in range(len(person_kps)):
                x, y = person_kps[idx]
                if x > 0 and y > 0:
                    cv2.circle(canvas, (int(x), int(y)), 5,
                               config.COLOR_KEYPOINT, -1)

        return canvas

    def apply_face_blur(self, frame: np.ndarray) -> np.ndarray:
        """
        Blur the head region of every detected person.

        HOW WE FIND THE HEAD:
        YOLOv8 gives us 5 face keypoints (nose, eyes, ears — indices 0-4).
        We find the bounding box around those points, expand it generously
        to cover the full head including hair, and apply a strong
        Gaussian blur to just that region.

        This runs on the frame in-place and returns it.
        """
        all_people = self.get_all_keypoints(frame)
        h, w = frame.shape[:2]

        for person_kps in all_people:
            # Collect face keypoints (indices 0–4)
            face_pts = []
            for idx in range(5):
                x, y = person_kps[idx]
                if x > 0 and y > 0:
                    face_pts.append((int(x), int(y)))

            if len(face_pts) < 2:
                # Not enough face points detected to locate head — skip
                continue

            # Bounding box around the detected face points
            xs = [p[0] for p in face_pts]
            ys = [p[1] for p in face_pts]
            cx = int(np.mean(xs))   # center x
            cy = int(np.mean(ys))   # center y

            # Estimate head radius: half the spread of the face points,
            # then expand by 80% to cover forehead, hair, chin
            spread = max(max(xs) - min(xs), max(ys) - min(ys))
            radius = int(max(spread * 0.9, 40))   # minimum 40px radius

            # Define blur region box, clamped to frame edges
            x1 = max(0, cx - radius)
            y1 = max(0, cy - radius)
            x2 = min(w, cx + radius)
            y2 = min(h, cy + radius)

            if x2 <= x1 or y2 <= y1:
                continue

            # Extract the region, blur it, paste it back
            region = frame[y1:y2, x1:x2]
            # Kernel size must be odd — larger = more blurred
            blurred = cv2.GaussianBlur(region, (99, 99), 30)
            frame[y1:y2, x1:x2] = blurred

        return frame


# ─────────────────────────────────────────────────────────────
# Line-crossing geometry
# ─────────────────────────────────────────────────────────────

def _side_of_line(point: tuple, p1: tuple, p2: tuple) -> float:
    """
    Determines which side of a line a point is on using the cross product.

        result = (p2.x - p1.x)(point.y - p1.y) - (p2.y - p1.y)(point.x - p1.x)

    Positive = one side, Negative = other side, Zero = on the line.
    Works for any line angle — vertical, horizontal, or diagonal.
    """
    px, py = point
    x1, y1 = p1
    x2, y2 = p2
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def check_crossing(
    leg_points: list,
    line_p1: tuple,
    line_p2: tuple,
    alert_side: str = None
) -> tuple:
    """
    Check if any leg keypoint has crossed to the alert side of the line.

    alert_side options:
      "above"  — alert when a point is ABOVE the line (smaller y value).
                 Use this for a horizontal bed-edge line at the bottom of frame.
      "below"  — alert when a point is BELOW the line (larger y value).
      "left"   — alert when a point is left of the line (cross product > 0).
      "right"  — alert when a point is right of the line (cross product < 0).

    Defaults to config.ALERT_SIDE if not specified.

    Returns:
        (crossing_detected: bool, offending_points: list)
    """
    import config as _config
    if alert_side is None:
        alert_side = getattr(_config, "ALERT_SIDE", "above")

    offending = []
    for pt in leg_points:
        px, py = pt
        x1, y1 = line_p1
        x2, y2 = line_p2

        if alert_side == "above":
            # Alert when the point's y is less than the line's y at that x.
            # For a roughly horizontal line, interpolate the line's y at px.
            if x2 != x1:
                line_y_at_px = y1 + (y2 - y1) * (px - x1) / (x2 - x1)
            else:
                line_y_at_px = (y1 + y2) / 2
            if py < line_y_at_px:
                offending.append(pt)

        elif alert_side == "below":
            if x2 != x1:
                line_y_at_px = y1 + (y2 - y1) * (px - x1) / (x2 - x1)
            else:
                line_y_at_px = (y1 + y2) / 2
            if py > line_y_at_px:
                offending.append(pt)

        else:
            # "left" / "right" — use cross product (works for any angle)
            side = _side_of_line(pt, line_p1, line_p2)
            if alert_side == "right" and side < 0:
                offending.append(pt)
            elif alert_side == "left" and side > 0:
                offending.append(pt)

    return len(offending) > 0, offending
