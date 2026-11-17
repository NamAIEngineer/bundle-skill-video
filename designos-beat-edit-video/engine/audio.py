"""Audio: 120 BPM bed synthesised with numpy (kick, hat, clap, pluck, bass, pad, whoosh).
Usage: BEAT_SPEC=spec.json python audio.py out.wav
Same RNG call order as the original audio9.py, so the sound is reproducible.
"""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import beatlib

SPEC = beatlib.load(os.environ["BEAT_SPEC"])
tl = beatlib.Timeline(SPEC)
AU = SPEC["audio"]
SR = 44100
N = int(tl.TOTAL * SR) + SR
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
rng = np.random.RandomState(AU["seed"])

def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = sig[: N - i]
    L[i:i + len(s)] += s * g * (1 - max(0, pan)); R[i:i + len(s)] += s * g * (1 + min(0, pan))

def env(n, a=0.003, d=0.2, curve=3.0):
    t = np.arange(n) / SR
    e = np.exp(-t * curve / max(d, 1e-3))
    at = np.minimum(1, t / a)
    return (e * at).astype(np.float32)

def sine(f, dur, g=1.0, dec=None):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * env(n, 0.004, dec or dur)).astype(np.float32) * g

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def kick():
    n = int(0.32 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 9)).astype(np.float32)

def hat(open_=False):
    n = int((0.16 if open_ else 0.05) * SR)
    x = rng.randn(n).astype(np.float32)
    x = np.diff(x, prepend=0)  # highpass-ish
    return x * env(n, 0.001, 0.16 if open_ else 0.05, 5) * 0.5

def clap():
    n = int(0.2 * SR); x = rng.randn(n).astype(np.float32)
    x = x - lowpass(x, 900)
    return x * env(n, 0.002, 0.12, 5) * 0.6

def pluck(f, dur=0.45, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 14) * bright + 0.18 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 22)
    return (s * env(n, 0.002, dur * 0.6, 4)).astype(np.float32) * 0.5

def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    return (s * env(n, 0.006, dur * 0.9, 3.5)).astype(np.float32) * 0.9

def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n, np.float32)
    for f in freqs:
        for dt in (-0.4, 0.4):
            s += np.sin(2 * np.pi * (f + dt) * t).astype(np.float32)
    a = np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.6)
    return (s * a).astype(np.float32) / (len(freqs) * 2) * 0.55

def tick(hf=3500):
    n = int(0.04 * SR); x = rng.randn(n).astype(np.float32)
    x = x - lowpass(x, hf * 0.5)
    return x * env(n, 0.001, 0.03, 5) * 0.5

def whoosh(dur=0.5, up=True):
    n = int(dur * SR); x = rng.randn(n).astype(np.float32)
    out = np.zeros(n, np.float32); s = 0.0; cut = np.linspace(300, 7000, n) if up else np.linspace(7000, 300, n)
    for i in range(n):
        a = np.exp(-2 * np.pi * cut[i] / SR); s = (1 - a) * x[i] + a * s; out[i] = s
    e = (np.linspace(0, 1, n) ** 2 if up else np.linspace(1, 0, n) ** 2)
    return out * e * 2.2


def hz(n): return 440.0 * 2 ** ((n - 69) / 12.0)

A = AU["root"]; PENT = AU["pent"]; CHORDS = AU["chords"]; BASSN = AU["bass"]
G0, G1 = AU["groove_start"], AU["groove_end"]
BEAT = tl.BEAT; BAR = tl.BAR

for b in range(int(tl.TOTAL / BAR)):
    t0 = b * BAR
    if t0 >= AU["pad_end"]: break
    if t0 >= BAR:
        add(pad([hz(n) for n in CHORDS[b % 4]], BAR + 0.05), t0, 0.28 if t0 < G1 else 0.4)
t = 0.0
while t < G1 - 1e-6:
    bar = int(t // BAR); beat = int((t % BAR) / BEAT)
    if t >= G0:
        add(kick(), t, 0.95)
        add(hat(), t + BEAT / 2, 0.32, 0.25)
        if beat in (1, 3): add(clap(), t, 0.28)
        add(hat(), t, 0.12, -0.2)
        bn = BASSN[bar % 4]
        add(bass(hz(bn), 0.45), t, 0.55)
        if beat == 2: add(bass(hz(bn + 12), 0.2), t + BEAT / 2, 0.28)
    else:
        if t >= BAR: add(kick(), t, 0.5)
        add(tick(), t, 0.5)
        if t >= BAR: add(hat(), t + BEAT / 2, 0.25)
    t += BEAT
add(whoosh(1.5, True), G0 - 1.5, 0.5)
add(kick(), G0, 1.1)
for k, c in enumerate(tl.CARDS):
    add(sine(hz(33 + 12), 0.5, 0.5, 0.5), c["T"], 0.45)
    add(tick(2200), c["clickT"], 0.8)
    for tv in c["dbl_video"]:
        add(tick(3000), tv, 0.9); add(tick(3400), tv + 0.14, 0.7)
    for i, ct in enumerate(c["chars"]):
        n = A + 12 + PENT[(i + k * 2) % len(PENT)]
        add(pluck(hz(n), 0.4), ct, 0.55, pan=((i % 5) - 2) * 0.12)
        add(tick(5000), ct, 0.35)
add(whoosh(0.55, False), AU["whoosh_at"], 0.7)
if tl.PAY:
    add(tick(2200), tl.PAY["menu"], 0.8); add(tick(2200), tl.PAY["fit"], 0.8)
    add(whoosh(0.35, True), tl.PAY["fit"] - 0.2, 0.5)
for i, tp in enumerate(tl.PULSES):
    n = A + 12 + PENT[i * 2 % len(PENT)]
    add(pluck(hz(n), 0.8, 1.2), tp, 0.7)
    add(pluck(hz(n - 12), 0.8, 0.8), tp, 0.35)
FA = AU["final_at"]
add(kick(), FA, 1.1)
for n in (45, 57, 60, 64, 69):
    add(pad([hz(n)], 3.6), FA, 0.7)
add(pluck(hz(81), 1.8, 1.2), FA, 0.6)
add(pluck(hz(76), 1.8, 1.0), FA + BEAT, 0.4)
add(whoosh(0.6, False), FA - 0.3, 0.5)

Lm, Rm = np.tanh(L * 0.9), np.tanh(R * 0.9)
fade = np.ones(N, np.float32); fo0 = int(AU["fade"][0] * SR); fo1 = int(AU["fade"][1] * SR)
fade[fo0:fo1] = np.linspace(1, 0, fo1 - fo0); fade[fo1:] = 0
Lm *= fade; Rm *= fade
pk = max(np.abs(Lm).max(), np.abs(Rm).max())
Lm = Lm / pk * AU["peak"]; Rm = Rm / pk * AU["peak"]
data = np.stack([Lm, Rm], 1)[: int(tl.TOTAL * SR)]
out = sys.argv[1] if len(sys.argv) > 1 else "bgm.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((data * 32767).astype(np.int16).tobytes())
print("peak_before_norm", round(float(pk), 4), "->", out)
