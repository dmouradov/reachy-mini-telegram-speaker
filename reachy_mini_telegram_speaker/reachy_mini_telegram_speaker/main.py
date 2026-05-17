import json
import subprocess
import time
import sys
from pathlib import Path

import requests
from reachy_mini import ReachyMini, ReachyMiniApp


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"


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

        print("App running. Waiting for Telegram messages...")
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
            print(f"Polling Telegram with offset={next_offset}")
            data = get_updates(token, offset=next_offset, timeout=30)

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

                print(f"Speaking: {text}")
                print(f"Update ID: {update['update_id']}")
                print("Starting TTS generation...")

                output_file = Path(f"telegram_tts_{update['update_id']}.wav")

                if hasattr(reachy_mini, "media") and hasattr(reachy_mini.media, "play_sound"):
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
                else:
                    print("[local test mode] No robot media, skipping speech.")

            time.sleep(1)

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