"""Beat timeline for designos-beat-edit-video.

Everything here is in VIDEO seconds unless a name says raw. One spec JSON drives
render.py, audio.py and qa.py, so a new video is a new spec, not new code.
"""
import json
import numpy as np


def load(path):
    with open(path) as f:
        return json.load(f)


class Timeline:
    def __init__(self, spec):
        s = self.spec = spec
        self.FPS = s["fps"]
        self.BEAT = 60.0 / s["bpm"]
        self.BAR = self.BEAT * s.get("beats_per_bar", 4)
        self.CH = self.BEAT / 4.0              # one typed character = one 16th note
        self.LOOP = 32 * self.CH               # the 32-step sequencer bar
        self.TOTAL = float(s["total"])
        self.SCENES = [tuple(x) for x in s["scenes"]]
        self.PAY = s.get("payoff")
        self.CARDS = [self._card(c) for c in s["cards"]]
        self.SCENE_ANCH = {c["scene"]: self._fix(self.anchors(c)) for c in self.CARDS}
        for name, anchors in s.get("footage_anchors", {}).items():
            if name in self.SCENE_ANCH:
                raise ValueError("Scene cannot have both card and footage anchors")
            if len(anchors) < 2 or any(len(a) != 2 for a in anchors):
                raise ValueError("Footage anchors require at least two [video, raw] pairs")
            if any(b[0] <= a[0] or b[1] < a[1] for a, b in zip(anchors, anchors[1:])):
                raise ValueError("Footage anchors must move forward")
            self.SCENE_ANCH[name] = anchors
        self.WPS = self._waypoints()
        self.CLICKS = self._clicks()
        self.HITS = [c["T"] for c in self.CARDS] + ([self.PAY["fit"] + 0.08] if self.PAY else [])
        self.PULSES = [c["pulse"] for c in self.CARDS if "pulse" in c]
        self.WHOOSH = s.get("audio", {}).get("whoosh_at", 0.0)

    def _card(self, raw):
        c = dict(raw)
        c["zd"] = c["hit"] - c["tc"]
        c["clickT"] = c["T"] - c["zd"]
        if not c.get("dbls"):
            c["dbls"] = [[c["T"] + 1.0, c["td"]]]
            c["tstart"] = c["T"] + np.ceil(1.8 / self.CH) * self.CH
        c["chars"] = [c["tstart"] + self.CH * i for i in range(c["N"])]
        c["tend"] = c["chars"][-1]
        c["dbl_video"] = [d[0] for d in c["dbls"]]
        return c

    def anchors(self, c):
        """(video_t, raw_t) pairs. raw_time() interpolates between them, so the
        footage is retimed and every click lands on the bar line."""
        T = c["T"]
        first = tuple(c["scene_in"]) if c.get("scene_in") else (T - 1.0, c["tc"] - 1.0)
        a = [first, (c["clickT"], c["tc"]), (T, c["hit"]), (T + 0.4, c["hit"] + 0.4)]
        for tv, tr in c["dbls"]:
            a.append((tv, tr))
        a.append((c["tstart"], c["ts"]))
        a.append((c["tend"], c["te"]))
        a.append((c["tend"] + 0.6, c["te"] + 0.6))
        a += [tuple(x) for x in c.get("extra_anchors", [])]
        return a

    @staticmethod
    def _fix(a):
        out = []
        for t, r in a:
            if out and t <= out[-1][0]:
                t = out[-1][0] + 1e-3
            if out and r < out[-1][1]:
                r = out[-1][1]
            out.append((t, r))
        return out

    def raw_time(self, scene, vt):
        a = self.SCENE_ANCH[scene]
        return float(np.interp(vt, [x[0] for x in a], [x[1] for x in a]))

    def _waypoints(self):
        cur = self.spec.get("cursor", {})
        sx = cur.get("sidebar_x", 0.076)
        st = cur.get("start", [0.69, 0.78])
        w = [(0.0, st[0], st[1], "m")]
        for c in self.CARDS:
            w.append((c["clickT"], sx, c["row"], "c"))
            w.append((c["T"] + 0.1, sx, c["row"], "m"))
            for tv, _ in c["dbls"]:
                w.append((tv, c["pt"][0], c["pt"][1], "c"))
            w.append((c["tend"] + 0.6, c["pt"][0], c["pt"][1], "m"))
        p = self.PAY
        if p:
            w.append((p["menu"], p["menu_xy"][0], p["menu_xy"][1], "c"))
            w.append((p["fit"], p["fit_xy"][0], p["fit_xy"][1], "c"))
            w.append((p["fit"] + 1.5, p["fit_xy"][0], p["fit_xy"][1], "m"))
        return w

    def _clicks(self):
        out = []
        for c in self.CARDS:
            out.append(c["clickT"])
            for tv, _ in c["dbls"]:
                out += [tv, tv + 0.14]
        if self.PAY:
            out += [self.PAY["menu"], self.PAY["fit"]]
        return out

    def beat_info(self, t):
        return int(t // self.BAR) + 1, int((t % self.BAR) // self.BEAT) + 1

    def validate(self):
        """Return a list of problems. Empty list = the spec obeys the rules."""
        bad = []
        eps = 1e-6
        # scenes contiguous and covering the whole video
        pos = 0.0
        for name, v0, v1, src in self.SCENES:
            if abs(v0 - pos) > eps:
                bad.append("scene %s starts at %.3f, expected %.3f" % (name, v0, pos))
            pos = v1
        if abs(pos - self.TOTAL) > eps:
            bad.append("scenes end at %.3f but total is %.3f" % (pos, self.TOTAL))
        scene_rng = {n: (a, b) for n, a, b, _ in self.SCENES}
        takes = self.spec.get("takes", {})
        for c in self.CARDS:
            n = c["name"]
            if abs((c["T"] / self.BAR) - round(c["T"] / self.BAR)) > 1e-6:
                bad.append("%s: edit lands at %.3f, not on a bar line" % (n, c["T"]))
            if abs(((c["tstart"] - c["T"]) / self.CH) - round((c["tstart"] - c["T"]) / self.CH)) > 1e-6:
                bad.append("%s: typing start is off the 16th-note grid" % n)
            if c["scene"] not in scene_rng:
                bad.append("%s: scene %s is not in scenes" % (n, c["scene"]))
            else:
                a, b = scene_rng[c["scene"]]
                if not (a <= c["clickT"] and c["tend"] + 0.6 <= b + 1e-6):
                    bad.append("%s: click/typing leaves scene %s [%.2f, %.2f]" % (n, c["scene"], a, b))
            if len(c["new"]) != c["N"]:
                bad.append("%s: N=%d but new text has %d characters" % (n, c["N"], len(c["new"])))
            if c["clickT"] > c["T"] - 0.4:
                bad.append("%s: pointer needs at least 0.4 s between click and the bar line" % n)
            gap = c["tstart"] - max(d[0] for d in c["dbls"])
            if gap < 0.45:
                bad.append("%s: pause between last click and first character is %.2f s (rule: about 0.8 s)" % (n, gap))
            a = self.SCENE_ANCH.get(c["scene"], [])
            if any(a[i][1] > a[i + 1][1] + 1e-9 for i in range(len(a) - 1)):
                bad.append("%s: raw anchors go backwards" % n)
        return bad
