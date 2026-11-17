# Verification — 2026-11-17

- Fresh 8-second recording of the real design:os studio 0.7.13 window via the new recorder, editable-overlay cursor telemetry saved. The recording shows the library screen, not an agent dashboard demonstration. No existing documents edited.
- VieNeu preset Hải Đăng generated a new two-sentence Vietnamese WAV: 3.96 seconds at 48 kHz, using the installed voice environment.
- Fresh take rendered through engine/run.py all: 1920x1080, 30 fps, 8 seconds, lofi music. QA passed, true peak -4.3 dBFS.
- Newly generated TTS mixed with the rendered music and muxed into the same video. Final QA passed, true peak -2.2 dBFS. A frame was visually inspected: whole app visible, no blank frame.
- Three automated recorder tests passed: ownership despite unrelated newer media; refusal of existing names/locks and path traversal; failure produces no copied video.
- System-font fallback loaded Arial on macOS.

This is a technical smoke integration, not a finished marketing video or a full 3–5 minute longform acceptance. Linux/Windows rendering, a fresh pip install and subjective listening/pronunciation approval were not tested. Existing voice environment/model was reused. Native Studio recording is macOS only.

Local outputs (ignored by Git): out/integration/raw/portability01.mp4, out/integration/vo/smoke.wav, out/integration/render/final.mp4, out/integration/final-with-tts.mp4, out/integration/frame.png.
