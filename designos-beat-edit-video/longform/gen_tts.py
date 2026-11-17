# Run on the Mac with the VieNeu venv:
#   .venv-voice/bin/python gen_tts.py script_tts.json vo/
# Splits each chapter into sentences, inserts 0.18 s of exact zeros between them
# (build.py finds caption boundaries from those zero gaps).
import json, re, sys, os, time, soundfile as sf, numpy as np
from vieneu import Vieneu
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
only = set(sys.argv[3:])
tts = Vieneu(); v = tts.get_preset_voice("Hải Đăng")
for k, t in json.load(open(src)):
    if only and k not in only: continue
    t0 = time.time(); parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', t) if p.strip()]; y = []
    for p in parts:
        y += [np.asarray(tts.infer(text=p, voice=v), dtype=np.float32), np.zeros(int(48000 * 0.18), np.float32)]
    y = np.concatenate(y); sf.write(f"{out}/{k}.wav", y, 48000); print(k, round(len(y) / 48000, 2), "s", round(time.time() - t0, 1), flush=True)
