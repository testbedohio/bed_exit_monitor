# buffer.py
# ──────────────────────────────────────────────────────────────────────────────
# Rolling in-memory video buffer.
#
# HOW IT WORKS:
#   Every camera frame is offered to add_frame(). Frames are sub-sampled to
#   BUFFER_FPS and compressed to JPEG before storage, so RAM usage stays
#   bounded. When an alert fires, save_clip_async() snapshots the deque and
#   writes an MP4 in a background thread, then calls a callback with the path.
#
# MEMORY ESTIMATE (default settings):
#   15 fps × 300 s = 4 500 frames × ~40 KB (JPEG q=60 at 1280×720) ≈ 180 MB
# ──────────────────────────────────────────────────────────────────────────────

import os
import threading
import time
from collections import deque

import cv2
import numpy as np

import config


class RollingBuffer:
    def __init__(self):
        max_frames = config.BUFFER_FPS * config.BUFFER_MAX_SECONDS
        self._frames: deque = deque(maxlen=max_frames)
        self._frame_counter = 0
        # Subsample: if the main loop runs at ~30 fps and BUFFER_FPS=15,
        # we keep every 2nd frame.
        self._sample_interval = max(1, round(30 / config.BUFFER_FPS))
        self._lock = threading.Lock()
        print(
            f"[Buffer] Initialized  ·  {config.BUFFER_MAX_SECONDS}s window  ·  "
            f"{config.BUFFER_FPS} fps  ·  {max_frames} frames max"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_frame(self, frame: np.ndarray):
        """
        Offer a raw camera frame to the buffer.
        Call this once per main-loop iteration BEFORE drawing overlays,
        so the saved clip shows the clean video + skeleton only.
        """
        self._frame_counter += 1
        if self._frame_counter % self._sample_interval != 0:
            return

        ok, encoded = cv2.imencode(
            ".jpg", frame,
            [cv2.IMWRITE_JPEG_QUALITY, config.BUFFER_JPEG_QUALITY],
        )
        if ok:
            with self._lock:
                self._frames.append(encoded.tobytes())

    def save_clip_async(self, output_path: str, callback=None):
        """
        Snapshot the buffer and write it to output_path in a background thread.

        callback(path: str | None) is called when done:
            · path  — success
            · None  — nothing in buffer or write error
        """
        with self._lock:
            snapshot = list(self._frames)

        if not snapshot:
            print("[Buffer] Buffer is empty — no clip saved.")
            if callback:
                callback(None)
            return

        print(f"[Buffer] Saving {len(snapshot)}-frame clip → {output_path}")
        threading.Thread(
            target=self._write_clip,
            args=(snapshot, output_path, callback),
            daemon=True,
        ).start()

    # ── Internal ───────────────────────────────────────────────────────────────

    @staticmethod
    def _write_clip(snapshot: list, output_path: str, callback):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            first = cv2.imdecode(
                np.frombuffer(snapshot[0], np.uint8), cv2.IMREAD_COLOR
            )
            if first is None:
                raise ValueError("Cannot decode first buffered frame.")

            h, w = first.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(
                output_path, fourcc, config.BUFFER_FPS, (w, h)
            )

            for raw in snapshot:
                frame = cv2.imdecode(
                    np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR
                )
                if frame is not None:
                    writer.write(frame)

            writer.release()
            duration_s = len(snapshot) / config.BUFFER_FPS
            print(
                f"[Buffer] Clip saved  ·  {len(snapshot)} frames  ·  "
                f"{duration_s:.1f}s  →  {output_path}"
            )
            if callback:
                callback(output_path)

        except Exception as exc:
            print(f"[Buffer] Error saving clip: {exc}")
            if callback:
                callback(None)
