# Bed Exit Monitor — Setup & Usage Guide

A real-time pose estimation app that watches a patient in bed and alerts nursing
staff (via video call) when the patient's legs cross the bed edge.

---

## What you need before starting

- Python 3.10 or 3.11 installed  
  Download from: https://www.python.org/downloads/
- A USB webcam connected to your computer
- An internet connection (to download the YOLOv8 model on first run, ~6 MB)

---

## Installation (Mac — development)

Open Terminal and run these commands one at a time:

```bash
# 1. Go to the project folder
cd bed_exit_monitor

# 2. Create a virtual environment
#    (This is a sandboxed Python just for this project — good practice!)
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate
#    You should see "(venv)" appear at the start of your terminal prompt.

# 4. Install all required packages
pip install -r requirements.txt

# 5. Run the app
python main.py
```

---

## Installation (Windows — deployment)

Open Command Prompt or PowerShell and run:

```bat
REM 1. Go to the project folder
cd bed_exit_monitor

REM 2. Create a virtual environment
python -m venv venv

REM 3. Activate it
venv\Scripts\activate

REM 4. Install packages
pip install -r requirements.txt

REM 5. Run
python main.py
```

---

## First run

On first launch, the app will automatically download the YOLOv8 pose model
(~6 MB). This only happens once. After that it loads from your local disk.

---

## Using the app

1. **A window opens** showing your camera feed with a green line across it.
   This is the "bed edge" threshold line.

2. **Position the line**: Click and drag either of the two circle handles
   (at the top and bottom of the green line) to match where the real bed
   edge appears in your camera view.

3. **When a patient's leg crosses the line**:
   - The line turns red
   - A "BED EXIT DETECTED" warning appears on screen
   - A beep sounds
   - A Jitsi video call opens in your browser

4. **Press Q** to quit the application.

---

## Troubleshooting

**Wrong camera opens:**  
Edit `config.py` and change `CAMERA_INDEX = 0` to `1`, `2`, etc.

**Pose not detected / skeleton looks wrong:**  
Try lowering `POSE_CONFIDENCE = 0.5` to `0.3` in `config.py`.

**Too many false alerts:**  
Increase `ALERT_FRAME_THRESHOLD = 10` to a higher number (e.g. `20`).  
This means the leg must be past the line for more frames before alerting.

**Alert triggers too often:**  
Increase `ALERT_COOLDOWN_SECONDS = 30` to a longer value.

**No sound:**  
pygame audio sometimes needs additional system libraries on Linux.
On Mac and Windows it should work out of the box.

---

## File overview

```
bed_exit_monitor/
├── main.py          ← Start here. Runs the camera loop and UI.
├── detector.py      ← Pose estimation and line-crossing math.
├── alert.py         ← Beep sound and video call trigger.
├── config.py        ← All settings. Edit this to customize the app.
└── requirements.txt ← Python package list.
```

---

## Swapping Jitsi for another video platform

Open `alert.py` and find the `trigger_video_call()` function.
Replace the Jitsi URL with any other video call link:

```python
# Zoom example:
url = "https://zoom.us/j/YOUR_MEETING_ID"

# Microsoft Teams example:
url = "https://teams.microsoft.com/l/meetup-join/YOUR_MEETING_LINK"
```

That's the only change needed — everything else stays the same.
