from pathlib import Path
import pyttsx3

output_file = Path("tts_test.wav")

engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

engine.save_to_file("Hello from the Telegram speaker test.", str(output_file))
engine.runAndWait()

if output_file.exists() and output_file.stat().st_size > 0:
    print(f"WAV created successfully: {output_file.resolve()}")
    print(f"File size: {output_file.stat().st_size} bytes")
else:
    raise RuntimeError("WAV file was not created correctly.")