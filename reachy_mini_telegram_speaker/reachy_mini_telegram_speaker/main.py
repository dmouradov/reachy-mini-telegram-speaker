import json
import subprocess
import time
import sys
from pathlib import Path

import requests
from reachy_mini import ReachyMini, ReachyMiniApp

import numpy as np
from reachy_mini.utils import create_head_pose

from reachy_mini.motion.recorded_move import RecordedMoves

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"
STATE_SLEEPY = "sleepy"
STATE_MESSAGE_WAITING = "message_waiting"
STATE_TRIGGERED_CONFIRM = "triggered_confirm"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_updates(token, offset=None, timeout=30):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {
        "timeout": timeout,
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(url, params=params, timeout=timeout + 5)
    response.raise_for_status()
    return response.json()


class ReachyMiniTelegramSpeaker(ReachyMiniApp):
    def run(self, reachy_mini: ReachyMini, stop_event):
        config = load_config()
        token = config["telegram_bot_token"]
        allowed_chat_id = str(config["allowed_chat_id"])
        
        app_state = STATE_SLEEPY
        pending_message = None
        pending_update_id = None

        recorded_moves = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")
        head_trigger_baseline = None
        head_trigger_count = 0
        
        for wav_file in Path(".").glob("telegram_tts_*.wav"):
            try:
                wav_file.unlink()
                print(f"Deleted old temp file: {wav_file}")
            except Exception as e:
                print(f"Could not delete old temp file {wav_file}: {e}")

        helper_script = Path(__file__).resolve().parent.parent / "tts_to_wav.py"

        def set_state(new_state):
            nonlocal app_state
            if app_state != new_state:
                print(f"STATE: {app_state} -> {new_state}")
                app_state = new_state

        def speak_text(reachy_mini, text, update_id):
            output_file = Path(f"telegram_tts_{update_id}.wav")

            print("Starting TTS generation...")
            subprocess.run(
                [sys.executable, str(helper_script), str(output_file), text],
                check=True,
            )

            print("TTS generation finished.")
            print(f"Just generated for text: {text}")

            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"WAV ready: {output_file.resolve()}")
                print(f"WAV size: {output_file.stat().st_size} bytes")
                print("Starting robot playback...")
                reachy_mini.media.play_sound(str(output_file.resolve()))
                print("Playback command sent.")
                time.sleep(3)
            else:
                print("TTS failed: WAV file was not created.")

        print("App running. Waiting for Telegram messages...")
        set_state(STATE_SLEEPY)
        for wav_file in Path(".").glob("telegram_tts_*.wav"):
            try:
                wav_file.unlink()
                print(f"Deleted old temp file: {wav_file}")
            except Exception as e:
                print(f"Could not delete old temp file {wav_file}: {e}")

        helper_script = Path(__file__).resolve().parent.parent / "tts_to_wav.py"

        next_offset = None

        print("Checking for old pending updates to skip...")
        startup_data = get_updates(token, offset=None, timeout=1)

        if startup_data.get("result"):
            last_update_id = startup_data["result"][-1]["update_id"]
            next_offset = last_update_id + 1
            print(f"Skipping old updates up to {last_update_id}")
        else:
            print("No old updates to skip.")

        while not stop_event.is_set():
            data = get_updates(token, offset=next_offset, timeout=0)

            for update in data.get("result", []):
                next_offset = update["update_id"] + 1

                message = update.get("message")
                if not message:
                    continue

                chat_id = str(message.get("chat", {}).get("id"))
                text = message.get("text")

                if chat_id != allowed_chat_id:
                    continue

                if not text:
                    continue

                if pending_message is not None:
                    print("Already holding a pending message, skipping new one for now.")
                    continue

                pending_message = text
                pending_update_id = update["update_id"]

                print(f"Stored pending message: {pending_message}")
                print(f"Pending update ID: {pending_update_id}")

                print("Message received - waking Reachy up")
                reachy_mini.wake_up()
                time.sleep(1)

                baseline_pose = reachy_mini.get_current_head_pose()
                head_trigger_baseline = baseline_pose[0, 2]
                head_trigger_count = 0
                print(f"Head trigger baseline set to: {head_trigger_baseline:.6f}")

                set_state(STATE_MESSAGE_WAITING)

            if app_state == STATE_MESSAGE_WAITING and pending_message is not None:
                head_pose = reachy_mini.get_current_head_pose()
                current_value = head_pose[0, 2]
                delta = abs(current_value - head_trigger_baseline)

                print(f"Head trigger check - baseline: {head_trigger_baseline:.6f}, current: {current_value:.6f}, delta: {delta:.6f}, count: {head_trigger_count}")
                
                if delta > 0.015:
                    head_trigger_count += 1
                else:
                    head_trigger_count = 0

                if head_trigger_count >= 1:
                    print("Head trigger detected - preparing playback")
                    set_state(STATE_TRIGGERED_CONFIRM)

                    time.sleep(2)

                    print("Playing proud1 before speaking")
                    proud_move = recorded_moves.get("proud1")
                    reachy_mini.play_move(proud_move, initial_goto_duration=1.0,sound=False)

                    time.sleep(1)

                    message_to_speak = pending_message
                    update_id_to_speak = pending_update_id

                    pending_message = None
                    pending_update_id = None
                    head_trigger_baseline = None
                    head_trigger_count = 0

                    print(f"Speaking stored message: {message_to_speak}")
                    speak_text(reachy_mini, message_to_speak, update_id_to_speak)

                    print("Playback finished - returning to sleep")
                    reachy_mini.goto_sleep()
                    time.sleep(2)

                    set_state(STATE_SLEEPY)

            time.sleep(0.03)

if __name__ == "__main__":
    import threading

    stop_event = threading.Event()
    app = ReachyMiniTelegramSpeaker()

    try:
        config = load_config()
        robot_host = config.get("robot_host", "192.168.68.74")
        print(f"Connecting to Reachy Mini at {robot_host}")
        with ReachyMini(host=robot_host, media_backend="default") as mini:

            app.run(mini, stop_event)
    except KeyboardInterrupt:
        print("Stopping app...")
        stop_event.set()