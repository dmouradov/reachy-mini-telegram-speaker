from pathlib import Path
import time

from reachy_mini import ReachyMini

WAV_FILE = Path("test.wav").resolve()

if not WAV_FILE.exists():
    raise FileNotFoundError(f"Could not find WAV file: {WAV_FILE}")

print(f"Using WAV file: {WAV_FILE}")

with ReachyMini(media_backend="default") as mini:
    print("Connected to Reachy Mini.")
    print("Playing WAV file...")
    mini.media.play_sound(str(WAV_FILE))
    time.sleep(3)
    print("Playback command sent.")