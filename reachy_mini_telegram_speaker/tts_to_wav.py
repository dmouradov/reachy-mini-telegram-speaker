from pathlib import Path
import sys
import pyttsx3

if len(sys.argv) < 3:
    raise SystemExit("Usage: python tts_to_wav.py <output_wav> <text>")

output_file = Path(sys.argv[1])
text = " ".join(sys.argv[2:])

engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

engine.save_to_file(text, str(output_file))
engine.runAndWait()

if not output_file.exists() or output_file.stat().st_size == 0:
    raise RuntimeError("WAV file was not created correctly.")

print(f"WAV created: {output_file.resolve()}")
print(f"Size: {output_file.stat().st_size} bytes")