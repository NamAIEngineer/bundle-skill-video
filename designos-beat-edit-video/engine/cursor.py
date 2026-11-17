import math
from PIL import Image, ImageDraw
ORANGE = (255, 106, 26)
def clip(x, a=0.0, b=1.0): return max(a, min(b, x))
def mj(u):
    u = clip(u); return 10 * u**3 - 15 * u**4 + 6 * u**5

def _seg(p0, p1, u, seed):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; dist = math.hypot(dx, dy) + 1e-9
    nx, ny = -dy / dist, dx / dist
    ov, split = 0.04, 0.78
    if u < split:
        s = mj((u / split) ** 0.88) * (1 + ov)
        off = (1 if seed % 2 == 0 else -1) * 0.075 * dist * math.sin(math.pi * (u / split))
    else:
        s = (1 + ov) - ov * mj((u - split) / (1 - split)); off = 0.0
    return p0[0] + dx * s + nx * off, p0[1] + dy * s + ny * off

def human_pos(t, wps, VW=1920, VH=960):
    # wps: (t, x, y, kind) normalized; kind 'c' arrives 0.2s before click time
    pts = [(w[0], w[1] * VW, w[2] * VH, w[3]) for w in wps]
    if t <= pts[0][0]: return pts[0][1], pts[0][2]
    prev_arrive = pts[0][0]
    for i in range(1, len(pts)):
        ti, x1, y1, kind = pts[i]; t0, x0, y0, _ = pts[i - 1]
        tarr = ti - (0.2 if kind == "c" else 0.0)
        if t <= ti:
            dist = math.hypot(x1 - x0, y1 - y0)
            T = clip(0.30 + 0.24 * math.log2(1 + dist / 70.0), 0.35, 1.5)
            T = min(T, max(0.3, tarr - prev_arrive - 0.08))
            dep = tarr - T
            if t < dep: return x0, y0
            if t >= tarr: return x1, y1
            return _seg((x0, y0), (x1, y1), (t - dep) / T, i)
        prev_arrive = tarr
    return pts[-1][1], pts[-1][2]

_tile = None
def tile():
    global _tile
    if _tile is None:
        S = 4; o = 20 * S; w, h = 64 * S, 80 * S
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pts = [(0, 0), (0, 36), (9, 28), (15, 42), (21, 39), (15, 26), (27, 26)]
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(o + x * S + 3 * S, o + y * S + 4 * S) for x, y in pts], fill=(0, 0, 0, 110))
        from PIL import ImageFilter
        sh = sh.filter(ImageFilter.GaussianBlur(3 * S)); im = Image.alpha_composite(im, sh)
        d = ImageDraw.Draw(im)
        d.polygon([(o + x * S, o + y * S) for x, y in pts], fill=(255, 255, 255, 255))
        d.line([(o + x * S, o + y * S) for x, y in pts + [pts[0]]], fill=(15, 15, 20, 255), width=int(2.4 * S))
        _tile = im.resize((64, 80), Image.LANCZOS)
    return _tile

def paste_cursor(img, px, py, scale=1.0, alpha=1.0):
    t = tile()
    if scale != 1.0: t = t.resize((max(1, int(64 * scale)), max(1, int(80 * scale))), Image.BICUBIC)
    ox, oy = 20 * scale, 20 * scale
    ix, iy = math.floor(px - ox), math.floor(py - oy); fx, fy = (px - ox) - ix, (py - oy) - iy
    t = t.transform(t.size, Image.AFFINE, (1, 0, -fx, 0, 1, -fy), Image.BICUBIC)
    if alpha < 1.0:
        a = t.split()[3].point(lambda v: int(v * alpha)); t = t.copy(); t.putalpha(a)
    img.paste(t, (ix, iy), t)

def draw_cursor2(img, fn, clicks, t, vy=60, ox=0.0, oy=0.0, sx=1.0, sy=1.0):
    # fn(tt) -> (x,y) in window px; map to canvas: px*sx+ox, vy + py*sy + oy
    def m(tt):
        x, y = fn(tt); return x * sx + ox, vy + y * sy + oy
    x, y = m(t)
    xp, yp = m(t - 0.033)
    sp = math.hypot(x - xp, y - yp) / 0.033
    if False:
        for k, a in ((2, 0.16), (1, 0.32)):
            gx, gy = m(t - 0.016 * k); paste_cursor(img, gx, gy, 1.0, a)
    press = 1.0
    for tc in clicks:
        if tc - 0.05 <= t <= tc + 0.14: press = 0.86
        p = (t - tc) / 0.5
        if 0 <= p <= 1:
            r = int(8 + 44 * (1 - (1 - p) ** 3)); a = int(255 * (1 - p))
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse((x - r, y - r, x + r, y + r), outline=ORANGE + (a,), width=4)
            img.paste(ov, (0, 0), ov)
    paste_cursor(img, x, y, press, 1.0)
