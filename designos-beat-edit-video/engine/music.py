"""Generative music. Usage: BEAT_SPEC=spec.json python music.py out.wav
spec.music = {"style": "house|lofi|trap|synthwave|cinematic|random", "seed": int, "key": 0-11 (optional)}
Every style has its own drums, bass, chord voicing, timbres and swing; seed changes progression/patterns.
Typed characters, clicks, bar-line hits and payoff pulses still trigger notes, so picture and sound stay locked."""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import beatlib

SPEC = beatlib.load(os.environ["BEAT_SPEC"]); tl = beatlib.Timeline(SPEC)
M = SPEC.get("music", {"style": "house", "seed": 1})
SR = 44100
N = int(tl.TOTAL * SR) + SR
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)

STYLES = {  # bpm range, scale (semitones), progressions (scale degrees), drums per 16 steps, feel
 "house":     dict(bpm=(120, 128), scale=[0,2,3,5,7,8,10], prog=[[0,5,2,6],[0,3,5,4],[5,3,0,4]], kick="x...x...x...x...", snare="....x.......x...", hat="..x...x...x...x.", swing=0.0, lead="pluck", bass="off", pad=0.25),
 "lofi":      dict(bpm=(72, 88),   scale=[0,2,3,5,7,9,10], prog=[[1,4,0,0],[0,5,1,4],[3,2,1,0]], kick="x.....x..x......", snare="....x.......x...", hat="x.x.x.x.x.x.x.x.", swing=0.18, lead="epiano", bass="soft", pad=0.35),
 "trap":      dict(bpm=(136, 150), scale=[0,2,3,5,7,8,11], prog=[[0,5,6,4],[0,6,5,4],[0,3,6,4]], kick="x.....x...x.....", snare="........x.......", hat="xxxxxxxxxxxxxxxx", swing=0.0, lead="bell", bass="808", pad=0.12),
 "synthwave": dict(bpm=(100, 116), scale=[0,2,3,5,7,8,10], prog=[[5,3,0,6],[0,6,5,6],[0,3,4,5]], kick="x...x...x...x...", snare="....x.......x...", hat="x.x.x.x.x.x.x.x.", swing=0.0, lead="saw", bass="8th", pad=0.3),
 "cinematic": dict(bpm=(84, 100),  scale=[0,2,3,5,7,8,10], prog=[[0,5,3,4],[0,2,5,4]], kick="x...............", snare="................", hat="..............x.", swing=0.0, lead="bell", bass="soft", pad=0.5),
}
names = sorted(STYLES)
rs = np.random.RandomState(M.get("seed", 1))
style = M.get("style", "house")
if style == "random": style = names[rs.randint(len(names))]
S = STYLES[style]
key = M.get("key", int(rs.randint(0, 12)))
prog = S["prog"][rs.randint(len(S["prog"]))]
rng = np.random.RandomState(M.get("seed", 1) + 1000)
STEP = tl.CH; BEAT = tl.BEAT; BAR = tl.BAR

def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = sig[: N - i]
    L[i:i + len(s)] += s * g * (1 - max(0, pan)); R[i:i + len(s)] += s * g * (1 + min(0, pan))
def tt(n): return np.arange(n) / SR
def env(n, a, d, c=3.0): t = tt(n); return (np.exp(-t * c / max(d, 1e-3)) * np.minimum(1, t / a)).astype(np.float32)
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def hz(n): return 440.0 * 2 ** ((n - 69) / 12.0)
def note(deg, octv=0):
    sc = S["scale"]; o, d = divmod(deg, len(sc))
    return 48 + key + sc[d] + 12 * (o + octv)

def kick(g=1.0):
    n = int(0.3 * SR); t = tt(n); f = 45 + 105 * np.exp(-t * 26)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32) * g
def snare(soft):
    n = int(0.22 * SR); x = rng.randn(n).astype(np.float32); x = x - lp(x, 1200 if not soft else 400)
    return (x * env(n, 0.002, 0.14, 5) * (0.5 if not soft else 0.35) + np.sin(2 * np.pi * 190 * tt(n)) * env(n, 0.001, 0.08, 6) * 0.3).astype(np.float32)
def hat(op=False):
    n = int((0.12 if op else 0.04) * SR); x = np.diff(rng.randn(n).astype(np.float32), prepend=0)
    return x * env(n, 0.001, 0.12 if op else 0.04, 5) * 0.4
def bass_n(f, dur, kind):
    n = int(dur * SR); t = tt(n)
    if kind == "808":
        fr = f * (1 + 0.5 * np.exp(-t * 18)); s = np.sin(2 * np.pi * np.cumsum(fr) / SR)
        return (s * env(n, 0.003, dur, 2.0)).astype(np.float32) * 0.9
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    if kind == "8th": s = s + 0.25 * np.sign(np.sin(2 * np.pi * f * t))
    return (s * env(n, 0.006, dur * 0.9, 3.5)).astype(np.float32) * 0.7
def lead_n(f, dur, kind):
    n = int(dur * SR); t = tt(n)
    if kind == "saw":
        s = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 7)); e = env(n, 0.005, dur * 0.7, 3)
    elif kind == "epiano":
        s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 8) + 0.1 * np.sin(2 * np.pi * 7 * f * t) * np.exp(-t * 30); e = env(n, 0.004, dur * 0.8, 3)
    elif kind == "bell":
        s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 6) + 0.25 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 12); e = env(n, 0.002, dur, 2.5)
    else:
        s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 14) + 0.18 * np.sin(6 * np.pi * f * t) * np.exp(-t * 22); e = env(n, 0.002, dur * 0.6, 4)
    return (s * e).astype(np.float32) * 0.4
def pad(notes, dur):
    n = int(dur * SR); t = tt(n); s = np.zeros(n, np.float32)
    for m in notes:
        for dt in (-0.5, 0.5): s += np.sin(2 * np.pi * (hz(m) + dt) * t).astype(np.float32)
    a = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.5)
    return (s * a / (len(notes) * 2)).astype(np.float32)
def whoosh(dur, up=True):
    n = int(dur * SR); x = rng.randn(n).astype(np.float32); out = np.zeros(n, np.float32); s = 0.0
    cut = np.linspace(300, 7000, n) if up else np.linspace(7000, 300, n)
    for i in range(n):
        a = np.exp(-2 * np.pi * cut[i] / SR); s = (1 - a) * x[i] + a * s; out[i] = s
    return out * (np.linspace(0, 1, n) ** 2 if up else np.linspace(1, 0, n) ** 2) * 2.2
def tick(hf=3500):
    n = int(0.04 * SR); x = rng.randn(n).astype(np.float32); x = x - lp(x, hf * 0.5)
    return x * env(n, 0.001, 0.03, 5) * 0.5

G0 = SPEC.get("audio", {}).get("groove_start", tl.SCENES[1][1] if len(tl.SCENES) > 1 else BAR)
G1 = SPEC.get("audio", {}).get("groove_end", tl.TOTAL - tl.SCENES[-1][2] + tl.SCENES[-1][1])
final_at = tl.SCENES[-1][1]
nbars = int(tl.TOTAL / BAR) + 1
for b in range(nbars):
    t0 = b * BAR
    if t0 >= tl.TOTAL - 1: break
    deg = prog[b % len(prog)]
    ch = [note(deg), note(deg + 2), note(deg + 4)]
    if t0 >= BAR: add(pad([c + 12 for c in ch], BAR + 0.05), t0, S["pad"])
    if t0 < G0 - 1e-6 or t0 >= G1 - 1e-6: continue
    for st in range(16):
        t = t0 + st * STEP * 2 + (S["swing"] * STEP * 2 if st % 2 else 0)
        beat_t = t0 + st * STEP * 2
        if S["kick"][st] == "x": add(kick(0.95), beat_t, 0.95)
        if S["snare"][st] == "x": add(snare(style in ("lofi", "cinematic")), beat_t, 0.5)
        if S["hat"][st] == "x": add(hat(style != "trap" and st % 4 == 2), t, 0.22 if st % 4 else 0.3, 0.2)
        if style == "trap" and st in (13, 14, 15) and b % 2: add(hat(), t + STEP, 0.15)
        if S["bass"] == "off" and st % 4 == 2: add(bass_n(hz(note(deg) - 24), STEP * 6, "x"), beat_t, 0.55)
        elif S["bass"] == "8th" and st % 2 == 0: add(bass_n(hz(note(deg) - 24), STEP * 3.5, "8th"), beat_t, 0.5)
        elif S["bass"] in ("soft", "808") and st in (0, 10): add(bass_n(hz(note(deg) - 24), BEAT * (2 if S["bass"] == "808" else 1.2), S["bass"]), beat_t, 0.6)
add(whoosh(1.2, True), G0 - 1.2, 0.5)
add(kick(1.1), G0, 1.1)

sc = S["scale"]
for k, c in enumerate(tl.CARDS):
    add(bass_n(hz(note(0) - 12), 0.5, "x"), c["T"], 0.5)
    add(tick(2200), c["clickT"], 0.8)
    for tv in c["dbl_video"]:
        add(tick(3000), tv, 0.9); add(tick(3400), tv + 0.14, 0.7)
    for i, ct in enumerate(c["chars"]):
        d = (i + k * 2) % len(sc) + (len(sc) if i % 5 == 4 else 0)
        add(lead_n(hz(note(d, 1)), 0.4, S["lead"]), ct, 0.7, pan=((i % 5) - 2) * 0.12)
        add(tick(5000), ct, 0.3)
if SPEC.get("audio", {}).get("whoosh_at"): add(whoosh(0.55, False), SPEC["audio"]["whoosh_at"], 0.7)
if tl.PAY:
    add(tick(2200), tl.PAY["menu"], 0.8); add(tick(2200), tl.PAY["fit"], 0.8); add(whoosh(0.35, True), tl.PAY["fit"] - 0.2, 0.5)
for i, tp in enumerate(tl.PULSES):
    d = (i * 2) % len(sc) + len(sc)
    add(lead_n(hz(note(d, 1)), 0.8, S["lead"]), tp, 0.8); add(lead_n(hz(note(d, 0)), 0.8, S["lead"]), tp, 0.4)
add(kick(1.1), final_at, 1.1)
add(pad([note(0) - 12, note(0), note(2), note(4), note(7)], 3.6), final_at, 0.9)
add(lead_n(hz(note(7, 1)), 1.8, S["lead"]), final_at, 0.7); add(whoosh(0.6, False), final_at - 0.3, 0.5)
if style == "lofi":  # vinyl bed
    add(lp(rng.randn(N).astype(np.float32), 6000) * 0.012, 0, 1.0)

Lm, Rm = np.tanh(L * 0.9), np.tanh(R * 0.9)
fade = np.ones(N, np.float32); f0 = int((tl.TOTAL - 0.7) * SR); f1 = int(tl.TOTAL * SR)
fade[f0:f1] = np.linspace(1, 0, f1 - f0); fade[f1:] = 0
Lm *= fade; Rm *= fade
pk = max(np.abs(Lm).max(), np.abs(Rm).max()); pkt = M.get("peak", 0.8)
data = (np.stack([Lm, Rm], 1) / pk * pkt)[: int(tl.TOTAL * SR)]
out = sys.argv[1] if len(sys.argv) > 1 else "bgm.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((data * 32767).astype(np.int16).tobytes())
print("music style=%s key=%d bpm=%s ->" % (style, key, SPEC["bpm"]), out)
