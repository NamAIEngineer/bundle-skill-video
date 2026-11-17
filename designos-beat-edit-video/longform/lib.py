import numpy as np, json, subprocess, math, re, os, base64, io
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
FD = "/usr/share/fonts/opentype/inter/"
def F(sz, w="Bold"): return ImageFont.truetype(FD + f"Inter-{w}.otf", sz)
_fc = {}
def font(sz, w="Bold"):
    k = (sz, w)
    if k not in _fc: _fc[k] = F(sz, w)
    return _fc[k]

CREAM = (255, 248, 238); INK = (28, 28, 38); GRAY = (150, 150, 162)
CORAL = (255, 122, 26); BLUE = (28, 100, 242); MINT = (36, 190, 138); PURPLE = (140, 110, 255); PINK = (255, 96, 140)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def eo(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t

# ---------- background ----------
_BW, _BH = 192, 108
_yy, _xx = np.mgrid[0:_BH, 0:_BW].astype(np.float32)
_blobs = [(0.15, 0.2, 0.55, (255, 190, 150), 0.07, 0.11), (0.85, 0.25, 0.5, (170, 205, 255), 0.09, 0.06),
          (0.5, 0.95, 0.6, (190, 245, 220), 0.05, 0.1), (0.9, 0.85, 0.4, (225, 205, 255), 0.11, 0.08)]
def bg(t):
    img = np.zeros((_BH, _BW, 3), np.float32); img[:] = CREAM
    for cx, cy, r, col, sx, sy in _blobs:
        x = (cx + 0.12 * math.sin(t * sx * 6.283 + cx * 9)) * _BW; y = (cy + 0.12 * math.cos(t * sy * 6.283 + cy * 7)) * _BH
        d = np.hypot((_xx - x) / _BW, (_yy - y) / _BH) / r
        a = np.clip(1 - d, 0, 1) ** 2 * 0.85
        img = img * (1 - a[..., None]) + np.array(col, np.float32) * a[..., None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return im

# ---------- card (app window) ----------
CX0, CY0, CW, CH = 300, 46, 1400, 842
_mask = Image.new("L", (CW, CH), 0); ImageDraw.Draw(_mask).rounded_rectangle((0, 0, CW - 1, CH - 1), 22, fill=255)
_sh = Image.new("RGBA", (CW + 160, CH + 160), (0, 0, 0, 0))
ImageDraw.Draw(_sh).rounded_rectangle((80, 96, CW + 80, CH + 90), 26, fill=(60, 40, 20, 70))
_sh = _sh.filter(ImageFilter.GaussianBlur(26))

def draw_card(base, frame, cam, alpha=1.0, off=(0, 0), scale=1.0):
    """frame: PIL RGB 1600x962. cam=(zoom, fx, fy) focus in raw px."""
    z, fx, fy = cam
    cw, chh = 1600 / z, 962 / z
    x0 = min(max(fx - cw / 2, 0), 1600 - cw); y0 = min(max(fy - chh / 2, 0), 962 - chh)
    crop = frame.crop((int(x0), int(y0), int(x0 + cw), int(y0 + chh))).resize((CW, CH), Image.BILINEAR if z < 1.05 else Image.BICUBIC)
    box = (x0, y0, cw, chh)
    cx, cy = CX0 + off[0], CY0 + off[1]
    if scale != 1.0:
        nw, nh = int(CW * scale), int(CH * scale)
        crop = crop.resize((nw, nh), Image.BILINEAR); m = _mask.resize((nw, nh), Image.BILINEAR)
        cx += (CW - nw) // 2; cy += (CH - nh) // 2
    else: m = _mask
    if alpha < 1: m = m.point(lambda v: int(v * alpha))
    sh = _sh if scale == 1.0 else _sh.resize((int((CW + 160) * scale), int((CH + 160) * scale)))
    base.paste(sh, (cx - int(80 * scale), cy - int(80 * scale)), sh) if alpha >= 0.99 else None
    base.paste(crop, (cx, cy), m)
    return box, (cx, cy, scale)

def raw2scr(px, py, box, place):
    x0, y0, cw, chh = box; cx, cy, sc = place
    return cx + (px - x0) / cw * CW * sc, cy + (py - y0) / chh * CH * sc

# ---------- cursor ----------
class Cursor:
    def __init__(self, path):
        d = json.load(open(path)); s = d["samples"]
        self.t = np.array([a["timeMs"] / 1000 for a in s]); self.x = np.array([a["cx"] for a in s]) * 1600; self.y = np.array([a["cy"] for a in s]) * 962
        self.clicks = [a["timeMs"] / 1000 for a in s if a["interactionType"] == "click"]
        a = d["assets"][0]; im = Image.open(io.BytesIO(base64.b64decode(a["imageDataUrl"].split(",")[1]))).convert("RGBA")
        self.img = im.resize((int(im.width * 1.7), int(im.height * 1.7)), Image.LANCZOS); self.hot = (a["hotspotX"] * 1.7, a["hotspotY"] * 1.7)
    def pos(self, t): return float(np.interp(t, self.t, self.x)), float(np.interp(t, self.t, self.y))
    def draw(self, im, t, box, place, vis=1.0):
        px, py = self.pos(t); sx, sy = raw2scr(px, py, box, place)
        for c in self.clicks:
            d = t - c
            if 0 <= d < 0.55:
                r = 10 + 46 * eo(d / 0.55); a = int(150 * (1 - d / 0.55))
                ov = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); ImageDraw.Draw(ov).ellipse((100 - r, 100 - r, 100 + r, 100 + r), outline=CORAL + (a,), width=5)
                im.paste(ov, (int(sx - 100), int(sy - 100)), ov)
        sh = Image.new("RGBA", self.img.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 70), mask=self.img.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(2))
        im.paste(sh, (int(sx - self.hot[0] + 3), int(sy - self.hot[1] + 4)), sh)
        im.paste(self.img, (int(sx - self.hot[0]), int(sy - self.hot[1])), self.img)

# ---------- source frames ----------
class Src:
    """sequential reader of one clip at 30 fps, full 1600x962"""
    def __init__(self, path, a, b):
        self.a = a; self.n = 0
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.2:.3f}", "-i", path, "-vf", "fps=30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None; self.idx = -1
    def get(self, ts):
        want = max(0, int(round((ts - self.a) * 30)))
        while self.idx < want:
            buf = self.p.stdout.read(1600 * 962 * 3)
            if len(buf) < 1600 * 962 * 3: break
            self.last = Image.frombytes("RGB", (1600, 962), buf); self.idx += 1
        return self.last
    def close(self):
        try: self.p.stdout.close(); self.p.kill()
        except Exception: pass

# ---------- text helpers ----------
def wrap(text, fnt, maxw):
    words = text.split(); lines = []; cur = ""
    for w in words:
        tst = (cur + " " + w).strip()
        if fnt.getlength(tst) <= maxw: cur = tst
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def shadow_text(im, xy, text, fnt, fill, anchor="la"):
    d = ImageDraw.Draw(im); d.text(xy, text, font=fnt, fill=fill, anchor=anchor)

def pill(im, box, fill=(255, 255, 255, 255), r=28, shadow=True, outline=None, w=3):
    x0, y0, x1, y1 = [int(v) for v in box]
    if shadow:
        sh = Image.new("RGBA", (x1 - x0 + 120, y1 - y0 + 120), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((60, 70, x1 - x0 + 60, y1 - y0 + 66), r + 4, fill=(60, 40, 20, 60))
        sh = sh.filter(ImageFilter.GaussianBlur(16)); im.paste(sh, (x0 - 60, y0 - 60), sh)
    ov = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), r, fill=fill, outline=outline, width=w)
    im.paste(ov, (x0, y0), ov)

def sentences_from_wav(path):
    import soundfile as sf
    x, sr = sf.read(path); z = np.abs(x) < 1e-7
    runs = []; s = None
    for i, v in enumerate(np.r_[z, False]):
        if v and s is None: s = i
        if not v and s is not None:
            if (i - s) / sr >= 0.12: runs.append((s, i))
            s = None
    segs = []; st = 0
    for a, b in runs:
        if a > st: segs.append((st / sr, a / sr))
        st = b
    if st < len(x): segs.append((st / sr, len(x) / sr))
    return x, sr, [(a, b) for a, b in segs if b - a > 0.2]
