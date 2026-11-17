# Long-form tutorial engine (DESIGN:OS 5-min video, 2026-11-16)

Files
- script2.py  : chapter texts (display = captions) + REP table -> script.json + script_tts.json (same sentence count asserted)
- gen_tts.py  : VieNeu v3 Turbo, voice "Hải Đăng", 48 kHz, 0.18 s zero gaps between sentences (run on Mac)
- lib.py      : background blobs, app card + camera crop, cursor from Openscreen cursor.json, callouts, captions helpers
- build.py    : chapters (CHP dict), rail, chapter cards, agenda, intro chips, recap wipe, outro + URL. `python build.py info|agenda|<chapter_id>`
- audio.py    : places voice by chapter, self-written bright music (104 bpm), ducked under voice -> out/audio.wav

Layout expected: ROOT/raw/<clip>.mp4 + <clip>.cursor.json (Openscreen), ROOT/vo/<id>.wav, ROOT/out/.
Concat: out/list.txt (hook, agenda, c1..c9) -> ffmpeg concat -> mux audio -> 4K upscale (crf 16) for YouTube.
Final delivered: out/final_v3.mp4, out/final_v3_4k.mp4 (4:21).
