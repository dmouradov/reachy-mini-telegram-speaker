import json
import time
from pathlib import Path

import requests
from reachy_mini import ReachyMini, ReachyMiniApp


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_updates(token, offset=None, timeout=30):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"timeout": timeout}
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

        next_offset = None

        while not stop_event.is_set():
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

                print(f"Telegram message received: {text}")

            time.sleep(1)