# patient.py
# -----------------------------------------------------------------------------
# Patient profile management for the Bed Exit Monitor.
#
# Responsibilities:
#   - Show a startup dialog box where the operator types in the patient's MRN
#   - Look up that MRN in the Supabase 'patients' table
#   - Return the patient's info (name, room, assigned staff) to main.py
#   - If the MRN is not found, allow the operator to enter details manually
#
# WHY A SEPARATE FILE?
#   Keeping patient logic here means main.py stays focused on the camera loop.
#   It also makes it easy to change how patients are looked up in the future
#   without touching the rest of the app.
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, simpledialog
import psycopg2

import db_config as secrets


# -----------------------------------------------------------------------------
# Data structure: a plain dictionary representing one patient session.
# This gets populated at startup and passed around the app.
# -----------------------------------------------------------------------------
def empty_patient() -> dict:
    """Return a blank patient record (used as fallback if lookup fails)."""
    return {
        "mrn":            "UNKNOWN",
        "last_name":      "UNKNOWN",
        "first_name":     "UNKNOWN",
        "room_number":    "UNKNOWN",
        "assigned_staff": "UNKNOWN",
    }


# -----------------------------------------------------------------------------
# Database lookup
# -----------------------------------------------------------------------------
def lookup_patient_by_mrn(mrn: str) -> dict | None:
    """
    Query the Supabase 'patients' table for a matching MRN.

    HOW THIS WORKS:
    We use psycopg2, a Python library that speaks the PostgreSQL wire protocol.
    It opens a direct TCP connection to the Supabase database server, sends a
    SQL SELECT query, and returns the result as a Python tuple.

    Returns a patient dict if found, or None if the MRN doesn't exist.
    """
    try:
        conn = psycopg2.connect(
            host=secrets.DB_HOST,
            dbname=secrets.DB_NAME,
            port=secrets.DB_PORT,
            user=secrets.DB_USER,
            password=secrets.DB_PASSWORD,
            connect_timeout=8,          # fail fast if server unreachable
            sslmode="require",          # Supabase requires SSL
        )
        cur = conn.cursor()

        # %s is a safe placeholder - psycopg2 handles quoting/escaping for us.
        # Never build SQL strings with f-strings - that opens a security hole
        # called SQL injection.
        cur.execute(
            "SELECT mrn, last_name, first_name, room_number, assigned_staff "
            "FROM patients WHERE mrn = %s",
            (mrn,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return None

        return {
            "mrn":            row[0],
            "last_name":      row[1],
            "first_name":     row[2],
            "room_number":    row[3] or "N/A",
            "assigned_staff": row[4] or "N/A",
        }

    except psycopg2.OperationalError as e:
        # Network or credentials error - log it and return None so the
        # caller can fall back to manual entry.
        print(f"[Patient] Database connection failed: {e}")
        return None

    except Exception as e:
        print(f"[Patient] Unexpected error during lookup: {e}")
        return None


# -----------------------------------------------------------------------------
# Manual entry fallback dialog
# -----------------------------------------------------------------------------
def _manual_entry_dialog(mrn: str) -> dict:
    """
    Show a simple form for the operator to enter patient details manually.
    Used when the MRN is not found in the database, or the DB is unreachable.

    HOW TKINTER DIALOGS WORK:
    Tkinter is Python's built-in GUI toolkit. We create a temporary root
    window, build a small form on top of it, and then destroy it when done.
    The main OpenCV window is separate and unaffected.
    """
    root = tk.Tk()
    root.withdraw()   # hide the blank root window - we only want the dialog

    messagebox.showwarning(
        "MRN Not Found",
        f"MRN '{mrn}' was not found in the database.\n"
        "Please enter patient details manually."
    )

    last_name      = simpledialog.askstring("Manual Entry", "Patient Last Name:",  parent=root) or "UNKNOWN"
    first_name     = simpledialog.askstring("Manual Entry", "Patient First Name:", parent=root) or "UNKNOWN"
    room_number    = simpledialog.askstring("Manual Entry", "Room Number:",        parent=root) or "UNKNOWN"
    assigned_staff = simpledialog.askstring("Manual Entry", "Assigned Staff:",     parent=root) or "UNKNOWN"

    root.destroy()

    return {
        "mrn":            mrn,
        "last_name":      last_name,
        "first_name":     first_name,
        "room_number":    room_number,
        "assigned_staff": assigned_staff,
    }


# -----------------------------------------------------------------------------
# Main startup dialog - called once by main.py before monitoring begins
# -----------------------------------------------------------------------------
def get_patient_at_startup() -> dict:
    """
    Show the MRN entry dialog and return a populated patient dict.

    This is the only function main.py needs to call. It handles the full flow:
      1. Ask operator for MRN
      2. Try database lookup
      3. If found, confirm with operator
      4. If not found, fall back to manual entry
      5. Return the patient dict

    Returns empty_patient() if the operator cancels without entering anything.
    """
    root = tk.Tk()
    root.withdraw()

    mrn = simpledialog.askstring(
        "Bed Exit Monitor — Patient Setup",
        "Enter Patient MRN to load profile:\n"
        "(Leave blank to enter details manually)",
        parent=root
    )
    root.destroy()

    # Operator pressed Cancel
    if mrn is None:
        print("[Patient] Startup cancelled by operator.")
        return empty_patient()

    mrn = mrn.strip().upper()

    # Blank MRN — go straight to manual entry
    if not mrn:
        return _manual_entry_dialog("MANUAL")

    # Try database lookup
    print(f"[Patient] Looking up MRN: {mrn} ...")
    patient = lookup_patient_by_mrn(mrn)

    if patient:
        print(f"[Patient] Found: {patient['first_name']} {patient['last_name']}, "
              f"Room {patient['room_number']}, Staff: {patient['assigned_staff']}")

        # Confirm with operator before starting
        root2 = tk.Tk()
        root2.withdraw()
        confirmed = messagebox.askyesno(
            "Confirm Patient",
            f"Patient found:\n\n"
            f"  Name:   {patient['first_name']} {patient['last_name']}\n"
            f"  Room:   {patient['room_number']}\n"
            f"  Staff:  {patient['assigned_staff']}\n\n"
            "Start monitoring this patient?",
            parent=root2
        )
        root2.destroy()

        if confirmed:
            return patient
        else:
            # Operator said No - let them re-enter
            return get_patient_at_startup()

    else:
        # MRN not found or DB unreachable
        return _manual_entry_dialog(mrn)
