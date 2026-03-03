# alert.py
# ─────────────────────────────────────────────────────────────
# Handles everything that happens when an alert is triggered:
#   1. Plays an audible beep
#   2. Plays a pre-recorded audio file (MP3)
#   3. Opens a Jitsi video call in the browser
#
# DESIGN NOTE — "pluggable" video call:
#   The function `trigger_video_call()` is intentionally isolated.
#   To swap Jitsi for Zoom, Teams, or a hospital nurse-call API,
#   you only need to change THIS function. Nothing else in the app
#   needs to change.
# ─────────────────────────────────────────────────────────────

import os
import webbrowser
import time
import threading
import numpy as np

import config

# We use pygame for audio because it works on both Mac and Windows
# without needing system-level permissions.
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_AVAILABLE = True
except Exception as e:
    print(f"[Alert] Audio unavailable: {e}. Beep will be skipped.")
    AUDIO_AVAILABLE = False


def _generate_beep_sound(frequency: float, duration: float) -> "pygame.mixer.Sound":
    """
    Generates a sine-wave beep programmatically — no audio file needed.

    HOW IT WORKS:
    A beep is just a sound wave oscillating at a given frequency (Hz).
    We calculate the wave mathematically and hand it to pygame to play.
    """
    sample_rate = 44100
    n_samples   = int(sample_rate * duration)
    t      = np.linspace(0, duration, n_samples, endpoint=False)
    wave   = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    wave_2d = np.column_stack([wave, wave])
    sound   = pygame.sndarray.make_sound(wave_2d)
    return sound


# Pre-generate the beep once at startup so there's no delay when alert fires
_beep_sound = None
if AUDIO_AVAILABLE:
    try:
        _beep_sound = _generate_beep_sound(config.BEEP_FREQUENCY, config.BEEP_DURATION)
    except Exception as e:
        print(f"[Alert] Could not pre-generate beep: {e}")


def play_beep():
    """Play the alert beep sound. Runs in a background thread so it doesn't freeze the video."""
    if not AUDIO_AVAILABLE or _beep_sound is None:
        print("[Alert] BEEP (audio not available)")
        return

    def _play():
        _beep_sound.play()
        time.sleep(config.BEEP_DURATION + 0.1)

    threading.Thread(target=_play, daemon=True).start()


def play_audio_file():
    """
    Play a pre-recorded audio file (MP3 or WAV) alongside the beep.

    The file path is set in config.py as ALERT_AUDIO_FILE.
    Place the audio file in the bed_exit_monitor folder.

    Runs in a background thread so it doesn't freeze the video stream.

    ── TO SWAP THE AUDIO FILE ───────────────────────────────────
    Just change ALERT_AUDIO_FILE in config.py to point to a different file.
    No code changes needed here.
    ─────────────────────────────────────────────────────────────
    """
    if not AUDIO_AVAILABLE:
        print("[Alert] Audio not available — skipping audio file playback.")
        return

    filepath = getattr(config, "ALERT_AUDIO_FILE", None)
    if not filepath:
        print("[Alert] No ALERT_AUDIO_FILE set in config.py — skipping.")
        return

    if not os.path.exists(filepath):
        print(f"[Alert] Audio file not found: '{filepath}'")
        print("  Place the MP3 in the bed_exit_monitor folder and check the filename in config.py.")
        return

    def _play():
        try:
            # pygame.mixer.music is best for MP3 files (streaming playback)
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            # Wait for playback to finish before thread exits
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"[Alert] Error playing audio file: {e}")

    threading.Thread(target=_play, daemon=True).start()


def trigger_video_call():
    """
    Opens a Jitsi video call in the default browser.

    ── HOW JITSI WORKS ──────────────────────────────────────────
    Jitsi Meet (meet.jit.si) is a free, open-source video call service.
    Any two people who open the same URL are instantly in a call together.
    No account, no app install needed — it runs in the browser.

    The nurse's workstation would have the same URL bookmarked or open.
    When the alert fires, THIS computer opens the URL and the call begins.

    ── TO SWAP TO ANOTHER PLATFORM ─────────────────────────────
    Replace the URL below with:
      - Zoom:  "https://zoom.us/j/YOUR_MEETING_ID"
      - Teams: "https://teams.microsoft.com/l/meetup-join/..."
      - Custom: any URL your hospital's system provides
    ─────────────────────────────────────────────────────────────
    """
    url = f"https://meet.jit.si/{config.JITSI_ROOM_NAME}"
    print(f"[Alert] Opening video call: {url}")
    webbrowser.open(url)


def trigger_alert():
    """
    Master alert function. Call this when a bed-exit is detected.
    Plays the beep, plays the audio file, and opens the video call simultaneously.
    """
    print("[Alert] *** BED EXIT DETECTED — TRIGGERING ALERT ***")
    play_beep()
    play_audio_file()
    trigger_video_call()
