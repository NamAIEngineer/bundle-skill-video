# Voiceover (approved by Nam 2026-11-16): VieNeu-TTS v3 Turbo, voice "Hải Đăng"

Install (Mac, once): `python3 -m venv venv && venv/bin/pip install vieneu` (CPU/ONNX, 48 kHz). Existing venv: `.venv-voice/bin/python`.
Generate: `venv/bin/python longform/gen_tts.py script_tts.json vo/ [chapter_id ...]` (~0.3x real time on the Mac Mini M1).
- Sentence by sentence, 0.18 s exact zeros between sentences; captions are timed from those gaps. Display text and TTS text must have the same sentence count (`longform/script2.py` asserts it).
- Not used: VietVoice-TTS (far too slow), cloning Jang (only with his written OK).

Approved respellings (display -> TTS):
| Display | TTS |
|---|---|
| Design OS Studio | Đi-giai Âu-ét Studio |
| Figma | Phích-ma |
| .fig | phích |
| megabyte | mê-ga-bai |
Rejected: "DESIGN OS" in caps (spelled letter by letter), "Xì-tiu-đi-ô" (sounds split), English UI words read aloud (Layers, Return, Escape, canvas, App Pages...). Say them in Vietnamese: bảng lớp, phím xuống dòng, phím thoát, vùng vẽ, bảng thuộc tính, màu nền; English UI strings only in callouts.

New word: write 5-7 variants, run `longform/check_voice.py *.wav` (faster-whisper, vi + en), pick the one heard as the real word, send Nam a short WAV, rebuild only after his OK.
