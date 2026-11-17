import sys, os, math, subprocess
sys.path.insert(0, "/Users/nam/orca/workspaces/openscreen-trial-20261114/v5")
sys.path.insert(0, "/Users/nam/orca/workspaces/openscreen-trial-20261114/keep/src")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tl
import cursor2 as C2
from multiprocessing import Pool

W, H, FPS = 1920, 1080, 30
D = "/Users/nam/orca/workspaces/openscreen-trial-20261114/v5"
FONTP = "/System/Library/Fonts/HelveticaNeue.ttc"
MONOP = "/System/Library/Fonts/SFNSMono.ttf"
OR = (226, 97, 34)
BGC = (18, 17, 20)
TXT = (243, 242, 245)
GREY = (140, 138, 150)
AX, AY, AS = 224, 34, 0.92          # app placement / scale
AW, AH = int(1600 * AS), int(962 * AS)
_f = {}
def sans(sz, bold=True):
    k = ("s", sz, bold)
    if k not in _f:
        try: _f[k] = ImageFont.truetype(FONTP, sz, index=1 if bold else 0)
        except Exception: _f[k] = ImageFont.truetype(FONTP, sz)
    return _f[k]
def mono(sz):
    k = ("m", sz)
    if k not in _f: _f[k] = ImageFont.truetype(MONOP, sz)
    return _f[k]
def clip(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(p): return 1 - (1 - clip(p)) ** 3
def eback(p):
    p = clip(p); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2

_bg = None; _shadow = None; _mask = None
def init():
    global _bg, _shadow, _mask
    if _bg is not None: return
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    g = np.clip(1 - d * 1.3, 0, 1) ** 2 * 10
    arr = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(BGC): arr[..., i] = c + g
    _bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((AX, AY + 14, AX + AW, AY + AH + 14), 16, fill=(0, 0, 0, 170))
    _shadow = sh.filter(ImageFilter.GaussianBlur(26))
    m = Image.new("L", (AW, AH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, AW - 1, AH - 1), 14, fill=255)
    _mask = m

def txt(img, s, x, y, font, color, alpha=1.0, blur=0.0, anchor="la"):
    if alpha <= 0.003: return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).text((x, y), s, font=font, fill=color + (int(255 * clip(alpha)),), anchor=anchor)
    if blur > 0.5: ov = ov.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(ov)

def rise_text(img, s, x, y, font, color, t, t0, dur=0.5, rise=30, anchor="la"):
    p = clip((t - t0) / dur)
    if p <= 0: return
    txt(img, s, x, y + (1 - eo(p)) * rise, font, color, alpha=clip(p * 1.8), blur=(1 - eo(p)) * 14, anchor=anchor)

def beat_info(t):
    bar = int(t // 2) + 1; beat = int((t % 2) // 0.5) + 1
    return bar, beat

def hud(img, t):
    d = ImageDraw.Draw(img)
    d.text((AX, 10), "DESIGN IN 4/4   ·   120 BPM   ·   4/4", font=mono(17), fill=(120, 118, 130))
    bar, beat = beat_info(t)
    d.text((AX + AW, 10), "BAR %02d   BEAT %d" % (bar, beat), font=mono(17), fill=(170, 168, 182), anchor="ra")
    pulse = clip(1 - ((t % 0.5) / 0.5) * 1.6)
    r = 7
    for i in range(4):
        cx = 40; cy = 520 + i * 26
        on = (beat - 1 == i)
        col = OR if on else (60, 58, 66)
        rr = r + (3 * pulse if on else 0)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col)

def sequencer(img, t):
    d = ImageDraw.Draw(img)
    loop = int(t // 4); st = int((t % 4) / tl.CH) % 32
    evs = set()
    for c in tl.CARDS:
        for ct in c["chars"]:
            if int(ct // 4) == loop and ct <= t + 1e-6: evs.add(int(round((ct % 4) / tl.CH)) % 32)
    cw = AW / 32.0; y0, y1 = 1054, 1070
    for i in range(32):
        x0 = AX + i * cw + 1.5; x1 = AX + (i + 1) * cw - 1.5
        beatcell = i % 4 == 0
        col = (46, 44, 52) if not beatcell else (64, 62, 72)
        if i in evs: col = (150, 66, 28)
        if i == st:
            col = OR if i in evs else (235, 233, 240)
        d.rounded_rectangle((x0, y0, x1, y1), 3, fill=col)

def caption(img, t):
    cur = None
    for i, c in enumerate(tl.CARDS):
        if t >= c["T"] - 0.001: cur = (i, c)
    if cur is None: return
    i, c = cur
    p = clip((t - c["T"]) / 0.35)
    lab = "EDIT %02d / 05   ·   %s" % (i + 1, c["name"].upper())
    txt(img, lab, AX, 930, mono(26), OR, alpha=clip(p * 2), blur=(1 - eo(p)) * 8)
    k = sum(1 for ct in c["chars"] if t >= ct)
    f = sans(78)
    if k == 0:
        s = c["old"]; col = GREY
        rise_text(img, s, AX, 962, f, col, t, c["T"], 0.35, 22)
    else:
        s = c["new"][:k]
        d = ImageDraw.Draw(img)
        d.text((AX, 962), s, font=f, fill=TXT)
        cx = AX + f.getlength(s) + 4
        if k < c["N"] or (t % 0.5) < 0.3:
            d.rectangle((cx, 972, cx + 5, 1036), fill=OR)

def cursor_pos(t):
    x, y = C2.human_pos(t, tl.WPS, 1600, 962)
    return AX + x * AS, AY + y * AS, x, y

def draw_cursor(img, t):
    px, py, _, _ = cursor_pos(t)
    for tc in tl.CLICKS:
        p = (t - tc) / 0.5
        if 0 <= p <= 1:
            r = int(8 + 40 * eo(p)); a = int(255 * (1 - p))
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse((px - r, py - r, px + r, py + r), outline=OR + (a,), width=4)
            img.alpha_composite(ov)
    press = 1.0
    for tc in tl.CLICKS:
        if tc - 0.05 <= t <= tc + 0.12: press = 0.82
    C2.paste_cursor(img, px, py, 1.2 * press, 1.0)

def flash(img, t, t0, a0=0.45, dur=0.14):
    p = (t - t0) / dur
    if 0 <= p <= 1:
        ov = Image.new("RGBA", img.size, (255, 255, 255, int(255 * a0 * (1 - p))))
        img.alpha_composite(ov)

def app_frame(img, frame_rgb):
    a = Image.fromarray(frame_rgb).resize((AW, AH), Image.LANCZOS).convert("RGBA")
    img.alpha_composite(_shadow)
    img.paste(a, (AX, AY), _mask)
    ImageDraw.Draw(img).rounded_rectangle((AX, AY, AX + AW - 1, AY + AH - 1), 14, outline=(255, 255, 255, 26), width=1)

# card boxes in the 1600x962 fit view (window px)
BOXES = [(354, 224, 623, 464), (690, 224, 959, 405), (1026, 224, 1295, 355), (354, 544, 623, 798), (690, 544, 959, 675)]
# order in BOXES: Activity, Focus, Note, Sign in, Stat  (matches tl.CARDS)

def pulses(img, t):
    for k, tp in enumerate(tl.PULSES):
        p = (t - tp) / 0.5
        if 0 <= p <= 1:
            bx = BOXES[k]
            x0 = AX + bx[0] * AS; y0 = AY + bx[1] * AS; x1 = AX + bx[2] * AS; y1 = AY + bx[3] * AS
            g = int(10 * (1 - p)) + 3
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dd = ImageDraw.Draw(ov)
            dd.rounded_rectangle((x0 - g, y0 - g, x1 + g, y1 + g), 18, outline=OR + (int(255 * (1 - p)),), width=5)
            dd.rounded_rectangle((x0, y0, x1, y1), 14, fill=OR + (int(40 * (1 - p)),))
            img.alpha_composite(ov)

def payoff_caption(img, t):
    if t < 32.4: return
    k = -1
    for i, tp in enumerate(tl.PULSES):
        if t >= tp: k = i
    if k < 0: return
    c = tl.CARDS[k]
    p = clip((t - tl.PULSES[k]) / 0.3)
    txt(img, "EDIT %02d / 05   ·   %s" % (k + 1, c["name"].upper()), AX, 930, mono(26), OR)
    txt(img, c["new"], AX, 962, sans(78), TXT, alpha=clip(p * 2), blur=(1 - eo(p)) * 10)

def intro(img, t):
    d = ImageDraw.Draw(img)
    bar, beat = beat_info(t)
    f = sans(210)
    cx = W // 2
    rise_text(img, "Design", 230, 300, f, TXT, t, 0.5, 0.55, 60)
    wd = f.getlength("Design ")
    rise_text(img, "in", 230 + wd, 300, f, GREY, t, 1.0, 0.55, 60)
    wi = f.getlength("in ")
    p = clip((t - 2.0) / 0.6)
    if p > 0:
        sc = 1.0 + 0.0 * p
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).text((230 + wd + wi, 300 + (1 - eback(p)) * 80), "4/4.", font=f, fill=OR + (int(255 * clip(p * 3)),))
        img.alpha_composite(ov)
    rise_text(img, "Five real edits. Every one lands on the beat.", 234, 600, sans(58, False), (190, 188, 200), t, 3.0, 0.5, 24)
    for i in range(4):
        on = (beat - 1 == i) and t < 4
        x = 234 + i * 70; y = 800
        pulse = clip(1 - ((t % 0.5) / 0.5) * 1.6)
        r = 14 + (6 * pulse if on else 0)
        d.ellipse((x - r, y - r, x + r, y + r), fill=OR if on else (58, 56, 64))
    txt(img, "120 BPM", 234 + 4 * 70 + 10, 786, mono(30), (150, 148, 160))
    txt(img, "design:os studio", 234, 120, mono(28), (150, 148, 160))

def outro(img, t):
    u = t - 35.0
    fo = clip((39.0 - t) / 0.6)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rise_text(layer, "Every edit", 234, 250, sans(170), TXT, u, 0.0, 0.55, 60)
    rise_text(layer, "on the beat.", 234, 430, sans(170), OR, u, 0.5, 0.55, 60)
    rise_text(layer, "design:os studio", 234, 760, mono(38), (170, 168, 182), u, 1.5, 0.5, 20)
    rise_text(layer, "Built by an agent. Placed on the grid.", 234, 830, sans(46, False), (190, 188, 200), u, 2.0, 0.5, 20)
    a = layer.split()[3].point(lambda v: int(v * fo)); layer.putalpha(a)
    img.alpha_composite(layer)

def read_frames(src, idx_list):
    path = D + "/raw%d.mp4" % src
    s0, e0 = min(idx_list), max(idx_list) + 1
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", "fps=30,trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS" % (s0, e0),
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
    fs = 1600 * 962 * 3
    cur = s0 - 1; last = None
    for idx in idx_list:
        while cur < idx:
            b = p.stdout.read(fs)
            if len(b) < fs: break
            last = np.frombuffer(b, np.uint8).reshape(962, 1600, 3); cur += 1
        yield last
    p.stdout.close(); p.kill()

NFR = {1: 53.1, 3: 16.4}

def render_scene(a):
    name, v0, v1, src = a
    init()
    out = D + "/q_%s.mp4" % name; tmp = D + "/q_%s.tmp.mp4" % name
    n = int(round((v1 - v0) * FPS))
    ts = [v0 + k / FPS for k in range(n)]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "%dx%d" % (W, H), "-r", "30", "-i", "-",
           "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = None
    if src:
        mx = int(NFR[src] * 30) - 1
        idx = [min(mx, int(round(tl.raw_time(name, t) * 30))) for t in ts]
        frames = read_frames(src, idx)
    for k, t in enumerate(ts):
        img = _bg.copy()
        if name == "intro": intro(img, t)
        elif name == "outro": outro(img, t)
        else:
            fr = next(frames)
            app_frame(img, fr)
            if t >= 30.4 or name == "T":
                pass
            pulses(img, t)
            cx, cy = None, None
            draw_cursor(img, t)
            if t < 32.4: caption(img, t)
            else: payoff_caption(img, t)
            sequencer(img, t)
            for hh in tl.HITS: flash(img, t, hh, 0.16, 0.12)
            flash(img, t, tl.WHOOSH, 0.5, 0.16)
        if name not in ("intro", "outro"): hud(img, t)
        else:
            if name == "intro": flash(img, t, 0.0, 0.0)
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait()
    os.rename(tmp, out)
    return out

def run():
    jobs = [s for s in tl.SCENES]
    if len(sys.argv) > 1: jobs = [s for s in jobs if s[0] in sys.argv[1:]]
    with Pool(4) as p:
        for r in p.imap_unordered(render_scene, jobs): print("done", r, flush=True)

if __name__ == "__main__":
    run()
