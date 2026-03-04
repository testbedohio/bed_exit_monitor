# logger.py
# -----------------------------------------------------------------------------
# Alert event logging for the Bed Exit Monitor.
#
# Responsibilities:
#   - Write one log entry to THREE destinations every time an alert fires:
#       1. Local CSV file  (next to the .exe, opens in Excel)
#       2. Supabase PostgreSQL  (cloud database, permanent record)
#       3. n8n webhook  (forwards the entry to a Google Sheet)
#
# WHY THREE DESTINATIONS?
#   Redundancy. If the internet is down, the local CSV still has everything.
#   If the laptop is lost, Supabase and Google Sheets still have everything.
#   The three copies together mean no alert event can be silently lost.
#
# HOW FAILURES ARE HANDLED:
#   Each destination is attempted independently. If one fails, the others
#   still run. Errors are printed to the console but never crash the app.
#   The upload_status field records what actually succeeded.
# -----------------------------------------------------------------------------

import csv
import json
import os
import threading
import time
import urllib.request

import psycopg2

import config
import db_config as secrets


# -----------------------------------------------------------------------------
# Log entry builder
# -----------------------------------------------------------------------------
def build_log_entry(patient: dict, clip_filename: str, upload_status: str) -> dict:
    """
    Build a complete log entry dictionary from the current alert event.

    All fields that can be auto-filled are filled here. The four 'note'
    fields are left blank intentionally - they are for manual entry later.

    Args:
        patient:        The patient dict returned by patient.get_patient_at_startup()
        clip_filename:  The filename of the saved video clip (e.g. 'alert_20250304_143022.mp4')
                        Pass empty string "" if no clip was saved.
        upload_status:  A short status string, e.g. "Uploaded", "Upload failed", "Pending"
    """
    return {
        "timestamp":       time.strftime("%Y-%m-%d %H:%M:%S"),
        "mrn":             patient.get("mrn",            "UNKNOWN"),
        "last_name":       patient.get("last_name",      "UNKNOWN"),
        "first_name":      patient.get("first_name",     "UNKNOWN"),
        "room_number":     patient.get("room_number",    "UNKNOWN"),
        "assigned_staff":  patient.get("assigned_staff", "UNKNOWN"),
        "clip_filename":   clip_filename,
        "upload_status":   upload_status,
        "system_status":   "",   # blank - for manual entry later
        "reserved_note_1": "",   # blank - for manual entry later
        "reserved_note_2": "",   # blank - for manual entry later
        "reserved_note_3": "",   # blank - for manual entry later
    }


# -----------------------------------------------------------------------------
# Destination 1: Local CSV
# -----------------------------------------------------------------------------
def _write_csv(entry: dict):
    """
    Append one row to the local CSV log file.

    HOW CSV APPENDING WORKS:
    We open the file in 'append' mode ('a') so existing rows are never
    overwritten. If the file doesn't exist yet, we write a header row first.
    The csv.DictWriter handles quoting and escaping automatically.
    """
    csv_path = os.path.join(config.clips_dir(), "..", "alert_log.csv")
    csv_path = os.path.normpath(csv_path)   # clean up the ../ in the path

    fieldnames = [
        "timestamp", "mrn", "last_name", "first_name", "room_number",
        "assigned_staff", "clip_filename", "upload_status",
        "system_status", "reserved_note_1", "reserved_note_2", "reserved_note_3"
    ]

    file_exists = os.path.isfile(csv_path)

    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()   # write column names on first use only
            writer.writerow(entry)
        print(f"[Logger] CSV written: {csv_path}")

    except Exception as e:
        print(f"[Logger] CSV write failed: {e}")


# -----------------------------------------------------------------------------
# Destination 2: Supabase PostgreSQL
# -----------------------------------------------------------------------------
def _write_supabase(entry: dict):
    """
    Insert one row into the Supabase 'alert_logs' table.

    HOW THE INSERT WORKS:
    We open a fresh connection, run one INSERT statement, commit it, and
    close the connection immediately. We don't keep a persistent connection
    open because the app might run for hours between alerts and idle
    connections can time out.
    """
    try:
        conn = psycopg2.connect(
            host=secrets.DB_HOST,
            dbname=secrets.DB_NAME,
            port=secrets.DB_PORT,
            user=secrets.DB_USER,
            password=secrets.DB_PASSWORD,
            connect_timeout=8,
            sslmode="require",
        )
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO alert_logs (
                timestamp, mrn, last_name, first_name, room_number,
                assigned_staff, upload_status,
                system_status, reserved_note_1, reserved_note_2, reserved_note_3
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
        """, (
            entry["timestamp"],
            entry["mrn"],
            entry["last_name"],
            entry["first_name"],
            entry["room_number"],
            entry["assigned_staff"],
            entry["upload_status"],
            entry["system_status"],
            entry["reserved_note_1"],
            entry["reserved_note_2"],
            entry["reserved_note_3"],
        ))

        conn.commit()
        cur.close()
        conn.close()
        print("[Logger] Supabase row inserted.")

    except psycopg2.OperationalError as e:
        print(f"[Logger] Supabase connection failed: {e}")
    except Exception as e:
        print(f"[Logger] Supabase insert failed: {e}")


# -----------------------------------------------------------------------------
# Destination 3: n8n webhook -> Google Sheets
# -----------------------------------------------------------------------------
def _write_google_sheet(entry: dict):
    """
    POST the log entry as JSON to the n8n webhook.

    The n8n workflow receives this JSON and appends a row to the designated
    Google Sheet. We'll set that workflow up separately.

    HOW THE WEBHOOK CALL WORKS:
    We serialize the entry dict to JSON, then make an HTTP POST request
    using Python's built-in urllib (no extra library needed).
    """
    try:
        url = secrets.N8N_SHEET_WEBHOOK

        # Don't attempt if the webhook URL is still the placeholder
        if "YOUR_SHEET_WEBHOOK_ID" in url:
            print("[Logger] Google Sheet webhook not configured yet - skipping.")
            return

        payload = json.dumps(entry).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            print(f"[Logger] Google Sheet webhook responded: HTTP {status}")

    except Exception as e:
        print(f"[Logger] Google Sheet webhook failed: {e}")


# -----------------------------------------------------------------------------
# Public interface - called by main.py on every alert
# -----------------------------------------------------------------------------
def log_alert(patient: dict, clip_filename: str = "", upload_status: str = "Pending"):
    """
    Write one alert event to all three log destinations.

    This is the only function main.py needs to call. All three writes happen
    in a background thread so they never block the video loop.

    Args:
        patient:        Patient dict from patient.get_patient_at_startup()
        clip_filename:  Filename of the saved clip, or "" if none saved yet.
        upload_status:  "Pending", "Uploaded", "Upload failed", etc.

    WHAT IS A THREAD?
    The main video loop runs 15-30 times per second. Writing to a database
    or making an HTTP request can take 1-2 seconds. If we did that in the
    main loop, the video would freeze for 1-2 seconds on every alert.
    By running the log writes in a background thread, the video loop
    continues uninterrupted while logging happens in parallel.
    """
    entry = build_log_entry(patient, clip_filename, upload_status)

    def _run_all():
        _write_csv(entry)
        _write_supabase(entry)
        _write_google_sheet(entry)

    t = threading.Thread(target=_run_all, daemon=True)
    t.start()


def update_log_upload_status(patient: dict, clip_filename: str, upload_status: str):
    """
    Update the upload_status for an existing alert once the clip upload
    completes. Writes a new Supabase row with the final status.

    NOTE: For simplicity we insert a new row rather than updating the
    existing one. This is fine for an audit log - we can always query
    the most recent row for a given timestamp + MRN combination.
    """
    log_alert(patient, clip_filename, upload_status)
