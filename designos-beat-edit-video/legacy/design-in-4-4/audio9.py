import sys, wave
sys.path.insert(0, "/Users/nam/orca/workspaces/openscreen-trial-20261114/v5")
import numpy as np
import tl
SR = 44100
N = int(tl.TOTAL * SR) + SR
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
rng = np.random.RandomState(7)

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
A = 57  # A3
PENT = [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27]
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]  # Am F C G
BASSN = [33, 29, 36, 31]

# bed: intro bars 0-2 hats ticks + riser, groove from 4.0
for b in range(int(tl.TOTAL / 2)):
    t0 = b * 2.0
    if t0 >= 37.5: break
    ch = CHORDS[b % 4]
    if t0 >= 2.0 and t0 < 35.0 or t0 >= 35.0:
        add(pad([hz(n) for n in ch], 2.05), t0, 0.28 if t0 < 35 else 0.4)
for b in range(2, 17):
    pass
t = 0.0
while t < 35.0 - 1e-6:
    bar = int(t // 2); beat = int((t % 2) / 0.5)
    if t >= 4.0:
        add(kick(), t, 0.95)
        add(hat(), t + 0.25, 0.32, 0.25)
        if beat in (1, 3): add(clap(), t, 0.28)
        add(hat(), t, 0.12, -0.2)
        bn = BASSN[bar % 4]
        add(bass(hz(bn), 0.45), t, 0.55)
        if beat == 2: add(bass(hz(bn + 12), 0.2), t + 0.25, 0.28)
    else:
        if t >= 2.0: add(kick(), t, 0.5)
        add(tick(), t, 0.5)
        if t >= 2.0: add(hat(), t + 0.25, 0.25)
    t += 0.5
# intro riser into 4.0
add(whoosh(1.5, True), 2.5, 0.5)
add(kick(), 4.0, 1.1)
# card hits + typed plucks
for k, c in enumerate(tl.CARDS):
    add(sine(hz(33 + 12), 0.5, 0.5, 0.5), c["T"], 0.45)
    add(tick(2200), c["clickT"], 0.8)
    for tv in c["dbl_video"]:
        add(tick(3000), tv, 0.9); add(tick(3400), tv + 0.14, 0.7)
    for i, ct in enumerate(c["chars"]):
        n = A + 12 + PENT[(i + k * 2) % len(PENT)]
        add(pluck(hz(n), 0.4), ct, 0.55, pan=((i % 5) - 2) * 0.12)
        add(tick(5000), ct, 0.35)
add(whoosh(0.55, False), 25.0, 0.7)
add(tick(2200), tl.PAY_MENU, 0.8); add(tick(2200), tl.PAY_FIT, 0.8)
add(whoosh(0.35, True), tl.PAY_FIT - 0.2, 0.5)
# payoff arpeggio on pulses (Am pent ascending) + final chord
for i, tp in enumerate(tl.PULSES):
    n = A + 12 + PENT[i * 2 % len(PENT)]
    add(pluck(hz(n), 0.8, 1.2), tp, 0.7)
    add(pluck(hz(n - 12), 0.8, 0.8), tp, 0.35)
add(kick(), 35.0, 1.1)
for n in (45, 57, 60, 64, 69):
    add(pad([hz(n)], 3.6), 35.0, 0.7)
add(pluck(hz(81), 1.8, 1.2), 35.0, 0.6)
add(pluck(hz(76), 1.8, 1.0), 35.5, 0.4)
add(whoosh(0.6, False), 34.7, 0.5)
# master
def finish(x):
    return np.tanh(x * 0.9)
Lm, Rm = finish(L), finish(R)
fade = np.ones(N, np.float32); fo0 = int(38.3 * SR); fo1 = int(39.0 * SR)
fade[fo0:fo1] = np.linspace(1, 0, fo1 - fo0); fade[fo1:] = 0
Lm *= fade; Rm *= fade
pk = max(np.abs(Lm).max(), np.abs(Rm).max()); print("peak", pk)
Lm = Lm / pk * 0.89; Rm = Rm / pk * 0.89
data = np.stack([Lm, Rm], 1)[: int(tl.TOTAL * SR)]
with wave.open("/Users/nam/orca/workspaces/openscreen-trial-20261114/v5/bgm9.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((data * 32767).astype(np.int16).tobytes())
print("ok")
