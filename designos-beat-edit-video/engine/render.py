"""Frame renderer. Usage: BEAT_SPEC=spec.json BEAT_ROOT=<dir with raw takes> python render.py [scene ...]

Output: <BEAT_OUT or BEAT_ROOT>/q_<scene>.mp4 (one encoded file per scene, 1920x1080 30 fps).
Spec-driven port of the original make8.py; same drawing order and constants.
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool
import beatlib
import cursor as C2

SPEC = beatlib.load(os.environ["BEAT_SPEC"])
ROOT = os.environ.get("BEAT_ROOT", ".")
OUT = os.environ.get("BEAT_OUT", ROOT)
tl = beatlib.Timeline(SPEC)

W, H = SPEC["size"]
FPS = SPEC["fps"]
PAL = {k: tuple(v) for k, v in SPEC["palette"].items()}
OR, BGC, TXT, GREY, SUB = PAL["accent"], PAL["bg"], PAL["text"], PAL["grey"], PAL["sub"]
WIN = SPEC["window"]
AX, AY, AS = WIN["x"], WIN["y"], WIN["scale"]
RW, RH = WIN["raw_size"]
AW, AH = int(RW * AS), int(RH * AS)
RAD = WIN.get("radius", 14)
NCARDS = len(tl.CARDS)
CAP_FROM = SPEC["payoff"]["caption_from"] if SPEC.get("payoff") else 1e9

_f = {}


def _font(kind, sz, index=0):
    for p in SPEC["fonts"][kind]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz, index=index) if index else ImageFont.truetype(p, sz)
            except Exception:
                try:
                    return ImageFont.truetype(p, sz)
                except Exception:
                    pass
    return ImageFont.load_default()


def sans(sz, bold=True):
    k = ("s", sz, bold)
    if k not in _f:
        _f[k] = _font("sans", sz, 1 if bold else 0)
    return _f[k]


def mono(sz):
    k = ("m", sz)
    if k not in _f:
        _f[k] = _font("mono", sz)
    return _f[k]


def clip(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(p): return 1 - (1 - clip(p)) ** 3


def eback(p):
    p = clip(p); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


_bg = _shadow = _mask = None


def init():
    global _bg, _shadow, _mask
    if _bg is not None:
        return
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    g = np.clip(1 - d * 1.3, 0, 1) ** 2 * 10
    arr = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(BGC):
        arr[..., i] = c + g
    _bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((AX, AY + 14, AX + AW, AY + AH + 14), 16, fill=(0, 0, 0, 170))
    _shadow = sh.filter(ImageFilter.GaussianBlur(26))
    m = Image.new("L", (AW, AH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, AW - 1, AH - 1), RAD, fill=255)
    _mask = m


def txt(img, s, x, y, font, color, alpha=1.0, blur=0.0, anchor="la"):
    if alpha <= 0.003:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).text((x, y), s, font=font, fill=tuple(color) + (int(255 * clip(alpha)),), anchor=anchor)
    if blur > 0.5:
        ov = ov.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(ov)


def rise_text(img, s, x, y, font, color, t, t0, dur=0.5, rise=30, anchor="la"):
    p = clip((t - t0) / dur)
    if p <= 0:
        return
    txt(img, s, x, y + (1 - eo(p)) * rise, font, color, alpha=clip(p * 1.8), blur=(1 - eo(p)) * 14, anchor=anchor)


def hud(img, t):
    d = ImageDraw.Draw(img)
    d.text((AX, 10), SPEC["hud_left"], font=mono(17), fill=(120, 118, 130))
    bar, beat = tl.beat_info(t)
    d.text((AX + AW, 10), "BAR %02d   BEAT %d" % (bar, beat), font=mono(17), fill=(170, 168, 182), anchor="ra")
    pulse = clip(1 - ((t % tl.BEAT) / tl.BEAT) * 1.6)
    for i in range(4):
        cx, cy = 40, 520 + i * 26
        on = (beat - 1 == i)
        rr = 7 + (3 * pulse if on else 0)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=OR if on else (60, 58, 66))


def sequencer(img, t):
    d = ImageDraw.Draw(img)
    loop = int(t // 4); st = int((t % 4) / tl.CH) % 32
    evs = set()
    for c in tl.CARDS:
        for ct in c["chars"]:
            if int(ct // 4) == loop and ct <= t + 1e-6:
                evs.add(int(round((ct % 4) / tl.CH)) % 32)
    cw = AW / 32.0; y0, y1 = H - 26, H - 10
    for i in range(32):
        x0 = AX + i * cw + 1.5; x1 = AX + (i + 1) * cw - 1.5
        col = (64, 62, 72) if i % 4 == 0 else (46, 44, 52)
        if i in evs: col = (150, 66, 28)
        if i == st: col = OR if i in evs else (235, 233, 240)
        d.rounded_rectangle((x0, y0, x1, y1), 3, fill=col)


def caption(img, t):
    cur = None
    for i, c in enumerate(tl.CARDS):
        if t >= c["T"] - 0.001:
            cur = (i, c)
    if cur is None:
        return
    i, c = cur
    p = clip((t - c["T"]) / 0.35)
    txt(img, "EDIT %02d / %02d   ·   %s" % (i + 1, NCARDS, c["name"].upper()), AX, 930, mono(26), OR, alpha=clip(p * 2), blur=(1 - eo(p)) * 8)
    k = sum(1 for ct in c["chars"] if t >= ct)
    f = sans(78)
    if k == 0:
        rise_text(img, c["old"], AX, 962, f, GREY, t, c["T"], 0.35, 22)
    else:
        s = c["new"][:k]
        ImageDraw.Draw(img).text((AX, 962), s, font=f, fill=TXT)
        cx = AX + f.getlength(s) + 4
        if k < c["N"] or (t % 0.5) < 0.3:
            ImageDraw.Draw(img).rectangle((cx, 972, cx + 5, 1036), fill=OR)


def draw_cursor(img, t):
    x, y = C2.human_pos(t, tl.WPS, RW, RH)
    px, py = AX + x * AS, AY + y * AS
    for tc in tl.CLICKS:
        p = (t - tc) / 0.5
        if 0 <= p <= 1:
            r = int(8 + 40 * eo(p)); a = int(255 * (1 - p))
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse((px - r, py - r, px + r, py + r), outline=tuple(OR) + (a,), width=4)
            img.alpha_composite(ov)
    press = 1.0
    for tc in tl.CLICKS:
        if tc - 0.05 <= t <= tc + 0.12:
            press = 0.82
    C2.paste_cursor(img, px, py, 1.2 * press, 1.0)


def flash(img, t, t0, a0=0.45, dur=0.14):
    p = (t - t0) / dur
    if 0 <= p <= 1:
        img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(255 * a0 * (1 - p)))))


def app_frame(img, frame_rgb):
    a = Image.fromarray(frame_rgb).resize((AW, AH), Image.LANCZOS).convert("RGBA")
    img.alpha_composite(_shadow)
    img.paste(a, (AX, AY), _mask)
    ImageDraw.Draw(img).rounded_rectangle((AX, AY, AX + AW - 1, AY + AH - 1), RAD, outline=(255, 255, 255, 26), width=1)


def pulses(img, t):
    boxes = [c["box"] for c in tl.CARDS if "pulse" in c]
    for k, tp in enumerate(tl.PULSES):
        p = (t - tp) / 0.5
        if 0 <= p <= 1:
            bx = boxes[k]
            x0, y0 = AX + bx[0] * AS, AY + bx[1] * AS
            x1, y1 = AX + bx[2] * AS, AY + bx[3] * AS
            g = int(10 * (1 - p)) + 3
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dd = ImageDraw.Draw(ov)
            dd.rounded_rectangle((x0 - g, y0 - g, x1 + g, y1 + g), 18, outline=tuple(OR) + (int(255 * (1 - p)),), width=5)
            dd.rounded_rectangle((x0, y0, x1, y1), 14, fill=tuple(OR) + (int(40 * (1 - p)),))
            img.alpha_composite(ov)


def payoff_caption(img, t):
    k = -1
    for i, tp in enumerate(tl.PULSES):
        if t >= tp:
            k = i
    if k < 0:
        return
    cards = [c for c in tl.CARDS if "pulse" in c]
    c = cards[k]
    p = clip((t - tl.PULSES[k]) / 0.3)
    txt(img, "EDIT %02d / %02d   ·   %s" % (tl.CARDS.index(c) + 1, NCARDS, c["name"].upper()), AX, 930, mono(26), OR)
    txt(img, c["new"], AX, 962, sans(78), TXT, alpha=clip(p * 2), blur=(1 - eo(p)) * 10)


def intro(img, t):
    d = ImageDraw.Draw(img)
    cfg = SPEC["intro"]
    bar, beat = tl.beat_info(t)
    f = sans(210)
    x = 230
    for text, col, at, mode in cfg["words"]:
        c = PAL[col]
        if mode == "rise":
            rise_text(img, text, x, 300, f, c, t, at, 0.55, 60)
        else:
            p = clip((t - at) / 0.6)
            if p > 0:
                ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(ov).text((x, 300 + (1 - eback(p)) * 80), text, font=f, fill=tuple(c) + (int(255 * clip(p * 3)),))
                img.alpha_composite(ov)
        x += f.getlength(text + " ")
    rise_text(img, cfg["sub"], 234, 600, sans(58, False), SUB, t, cfg["sub_at"], 0.5, 24)
    for i in range(4):
        on = (beat - 1 == i) and t < tl.SCENES[0][2]
        cx, cy = 234 + i * 70, 800
        pulse = clip(1 - ((t % tl.BEAT) / tl.BEAT) * 1.6)
        r = 14 + (6 * pulse if on else 0)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=OR if on else (58, 56, 64))
    txt(img, cfg["bpm_label"], 234 + 4 * 70 + 10, 786, mono(30), (150, 148, 160))
    txt(img, cfg["kicker"], 234, 120, mono(28), (150, 148, 160))


def outro(img, t):
    cfg = SPEC["outro"]
    u = t - cfg["start"]
    fo = clip((tl.TOTAL - t) / 0.6)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    y = 250
    for text, col, at in cfg["lines"]:
        rise_text(layer, text, 234, y, sans(170), PAL[col], u, at, 0.55, 60)
        y += 180
    rise_text(layer, cfg["mono"], 234, 760, mono(38), (170, 168, 182), u, 1.5, 0.5, 20)
    rise_text(layer, cfg["sub"], 234, 830, sans(46, False), SUB, u, 2.0, 0.5, 20)
    layer.putalpha(layer.split()[3].point(lambda v: int(v * fo)))
    img.alpha_composite(layer)


def read_frames(src, idx_list):
    path = os.path.join(ROOT, SPEC["takes"][str(src)]["file"])
    s0, e0 = min(idx_list), max(idx_list) + 1
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=30,trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS" % (s0, e0),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
    fs = RW * RH * 3
    cur = s0 - 1; last = None
    for idx in idx_list:
        while cur < idx:
            b = p.stdout.read(fs)
            if len(b) < fs:
                break
            last = np.frombuffer(b, np.uint8).reshape(RH, RW, 3); cur += 1
        yield last
    p.stdout.close(); p.kill()


def render_scene(a):
    name, v0, v1, src = a
    init()
    out = os.path.join(OUT, "q_%s.mp4" % name); tmp = os.path.join(OUT, "q_%s.tmp.mp4" % name)
    n = int(round((v1 - v0) * FPS))
    ts = [v0 + k / FPS for k in range(n)]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = None
    if src:
        mx = int(SPEC["takes"][str(src)]["seconds"] * 30) - 1
        idx = [min(mx, int(round(tl.raw_time(name, t) * 30))) for t in ts]
        frames = read_frames(src, idx)
    for t in ts:
        img = _bg.copy()
        if name == "intro":
            intro(img, t)
        elif name == "outro":
            outro(img, t)
        else:
            app_frame(img, next(frames))
            pulses(img, t)
            if SPEC.get("cursor", {}).get("overlay", True): draw_cursor(img, t)
            if t < CAP_FROM:
                caption(img, t)
            else:
                payoff_caption(img, t)
            sequencer(img, t)
            for hh in tl.HITS:
                flash(img, t, hh, 0.16, 0.12)
            flash(img, t, tl.WHOOSH, 0.5, 0.16)
            hud(img, t)
        enc.stdin.write(img.tobytes())
    enc.stdin.close()
    if enc.wait() != 0: raise RuntimeError("Video encoder failed")
    os.rename(tmp, out)
    return out


def run():
    jobs = list(tl.SCENES)
    if len(sys.argv) > 1:
        jobs = [s for s in jobs if s[0] in sys.argv[1:]]
    with Pool(4) as p:
        for r in p.imap_unordered(render_scene, jobs):
            print("done", r, flush=True)


if __name__ == "__main__":
    run()
