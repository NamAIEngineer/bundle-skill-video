"""Design in 4/4 - shared timeline (120 BPM, beat = 0.5 s, bar = 2 s). All times in video seconds."""
import numpy as np
FPS = 30
BEAT = 0.5
CH = 0.125  # 16th note per typed char
TOTAL = 39.0
SCENES = [("intro", 0, 4, 0), ("A", 4, 9, 1), ("F", 9, 13, 1), ("N", 13, 19, 1), ("S", 19, 25, 1), ("T", 25, 35, 3), ("outro", 35, 39, 0)]

def mk(name, T, src, tc, hit, td, ts, te, N, row, pt, old, new, dbls=None, tstart=None):
    return dict(name=name, T=T, src=src, tc=tc, hit=hit, td=td, ts=ts, te=te, N=N, row=row, pt=pt, old=old, new=new,
                dbls=dbls, tstart=tstart)

CARDS = [
    mk("Activity", 6, 1, 8.07, 8.57, 9.9, 10.83, 11.37, 4, 0.404, (0.348, 0.395), "3.1", "12.4"),
    mk("Focus", 10, 1, 13.38, 13.83, 15.19, 16.13, 16.87, 5, 0.371, (0.412, 0.498), "13:27", "25:00"),
    mk("Note", 14, 1, 26.87, 27.33, 28.67, 29.6, 31.43, 12, 0.339, (0.504, 0.492), "Ship the small thing today.", "Make it sing"),
    mk("Sign in", 20, 1, 33.44, 33.90, 35.25, 36.17, 37.70, 10, 0.305, (0.398, 0.231), "Welcome back", "Hello, Nam"),
    mk("Stat", 26, 3, 7.47, 7.97, 9.58, 11.4, 12.07, 6, 0.271, (0.348, 0.545), "1,284", "12,840",
       dbls=[(27.0, 9.58), (27.5, 10.42)], tstart=28.0),
]
for c in CARDS:
    c["zd"] = c["hit"] - c["tc"]
    c["clickT"] = c["T"] - c["zd"]
    if c["dbls"] is None:
        c["dbls"] = [(c["T"] + 1.0, c["td"])]
        c["tstart"] = c["T"] + 1.5
    c["chars"] = [c["tstart"] + CH * i for i in range(c["N"])]
    c["tend"] = c["chars"][-1]
    c["dbl_video"] = [d[0] for d in c["dbls"]]

def anchors(c):
    T = c["T"]
    a = [(T - 1.0, c["tc"] - 1.0), (c["clickT"], c["tc"]), (T, c["hit"]), (T + 0.4, c["hit"] + 0.4)]
    for tv, tr in c["dbls"]:
        a.append((tv, tr))
    a.append((c["tstart"], c["ts"]))
    a.append((c["tend"], c["te"]))
    a.append((c["tend"] + 0.6, c["te"] + 0.6))
    return a

PAY_MENU, PAY_FIT = 30.5, 31.5

def anchors_T():
    c = CARDS[4]
    a = [(25.0, 7.0)] + anchors(c)[1:]
    a += [(PAY_MENU, 14.59), (PAY_FIT, 15.43), (32.5, 16.4)]
    return a

SCENE_ANCH = {
    "A": [(4.0, 7.0)] + anchors(CARDS[0])[1:],
    "F": anchors(CARDS[1]),
    "N": anchors(CARDS[2]),
    "S": anchors(CARDS[3]),
    "T": anchors_T(),
}
def fix(a):
    out = []
    for t, r in a:
        if out and t <= out[-1][0]: t = out[-1][0] + 1e-3
        if out and r < out[-1][1]: r = out[-1][1]
        out.append((t, r))
    return out
SCENE_ANCH = {k: fix(v) for k, v in SCENE_ANCH.items()}

def raw_time(scene, vt):
    a = SCENE_ANCH[scene]
    return float(np.interp(vt, [x[0] for x in a], [x[1] for x in a]))

def waypoints():
    w = [(0.0, 0.69, 0.78, "m")]
    for c in CARDS:
        rx, ry = 0.076, c["row"]
        w.append((c["clickT"], rx, ry, "c"))
        w.append((c["T"] + 0.1, rx, ry, "m"))
        for tv, _ in c["dbls"]:
            w.append((tv, c["pt"][0], c["pt"][1], "c"))
        w.append((c["tend"] + 0.6, c["pt"][0], c["pt"][1], "m"))
    w.append((PAY_MENU, 0.976, 0.125, "c"))
    w.append((PAY_FIT, 0.903, 0.28, "c"))
    w.append((PAY_FIT + 1.5, 0.903, 0.28, "m"))
    return w
WPS = waypoints()

def clicks():
    out = []
    for c in CARDS:
        out.append(c["clickT"])
        for tv, _ in c["dbls"]:
            out += [tv, tv + 0.14]
    out += [PAY_MENU, PAY_FIT]
    return out
CLICKS = clicks()
HITS = [c["T"] for c in CARDS] + [PAY_FIT + 0.08]
PULSES = [32.5, 33.0, 33.5, 34.0, 34.5]
WHOOSH = 25.0

if __name__ == "__main__":
    for c in CARDS:
        print(c["name"], "click", round(c["clickT"], 3), "hit", c["T"], "dbl", c["dbl_video"], "chars", c["chars"][0], "->", c["tend"])
    for k, v in SCENE_ANCH.items(): print(k, [(round(a, 2), round(b, 2)) for a, b in v])
