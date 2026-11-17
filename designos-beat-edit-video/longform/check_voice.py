# Usage: python check_voice.py a.wav b.wav ...   (pip install faster-whisper)
# Prints what Whisper hears in Vietnamese and English for each TTS variant.
import sys, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("small", compute_type="int8")
for f in sys.argv[1:]:
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    r = []
    for lang in ("vi", "en"):
        segs, _ = m.transcribe(a, language=lang); r.append(" ".join(s.text for s in segs).strip())
    print(f, "| vi:", r[0], "| en:", r[1])
