# uploader.py
# ──────────────────────────────────────────────────────────────────────────────
# Uploads a saved alert clip to Google Drive via the n8n upload webhook.
#
# The n8n workflow receives a multipart POST, finds / creates the
# BuckeyeBedMonitor folder, and uploads the file to Google Drive.
#
# Everything runs in a background thread so the video loop is never blocked.
# ──────────────────────────────────────────────────────────────────────────────

import os
import threading

import requests

import config


def upload_clip(filepath: str, on_status=None):
    """
    Upload filepath to Google Drive via the n8n webhook.
    on_status(msg: str) is called with progress / result messages.
    Safe to call from any thread.
    """
    if not filepath:
        _status(on_status, "Upload skipped: no file path")
        return
    if not os.path.exists(filepath):
        _status(on_status, f"Upload error: file not found — {filepath}")
        return

    threading.Thread(
        target=_worker,
        args=(filepath, on_status),
        daemon=True,
    ).start()


# ── Internal ───────────────────────────────────────────────────────────────────

def _status(cb, msg: str):
    print(f"[Uploader] {msg}")
    if cb:
        cb(msg)


def _worker(filepath: str, on_status):
    filename = os.path.basename(filepath)
    _status(on_status, f"Uploading  {filename} …")

    try:
        with open(filepath, "rb") as fh:
            response = requests.post(
                config.N8N_UPLOAD_WEBHOOK,
                files={"video": (filename, fh, "video/mp4")},
                data={"folder": "BuckeyeBedMonitor"},
                timeout=300,        # 5-minute cap for large files on slow links
            )

        if response.status_code in (200, 201):
            _status(on_status, f"Uploaded ✓  {filename}")
            if config.DELETE_CLIP_AFTER_UPLOAD and os.path.exists(filepath):
                os.remove(filepath)
                print(f"[Uploader] Local clip deleted: {filename}")
        else:
            _status(on_status, f"Upload failed  HTTP {response.status_code}")

    except requests.exceptions.Timeout:
        _status(on_status, "Upload timed out")
    except requests.exceptions.ConnectionError:
        _status(on_status, "Upload error: cannot reach n8n — clip kept locally")
    except Exception as exc:
        _status(on_status, f"Upload error: {exc}")
