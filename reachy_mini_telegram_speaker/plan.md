# v0.1 plan

## Goal
Make the Reachy Mini Telegram beta more characterful while keeping the current Python app, Telegram polling, fixed robot IP config, and local TTS helper.

## State flow

### 1. Sleepy
- Default state when there are no unread messages.
- Reachy stays in a sleepy pose.

### 2. Message waiting / curious
- When a new Telegram message arrives, Reachy does not speak immediately.
- Reachy moves into a curious / alert pose.
- The message is stored as a pending message.

### 3. Playback confirmation trigger
- Reachy waits for the antennas to be moved down.
- This acts as the confirmation trigger.

### 4. Happy speaking / return to sleepy
- After trigger, wait a few seconds.
- Reachy makes a happy gesture.
- Reachy speaks the stored message.
- Reachy slowly returns to the sleepy pose.

## Minimum beta decisions
- Keep Telegram polling.
- Keep fixed robot IP in config.
- Keep local TTS via tts_to_wav.py.
- Store only one pending message.
- Use simple in-memory state.
- Ignore extra architecture until the full interaction works.