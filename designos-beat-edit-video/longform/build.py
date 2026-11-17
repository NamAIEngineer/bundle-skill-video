import sys, json, re, subprocess, os
from lib import *
import soundfile as sf

ROOT = os.path.abspath(os.environ.get("ROOT", ".")); os.makedirs(f"{ROOT}/out", exist_ok=True)
SCRIPT = dict(json.load(open(f"{ROOT}/script.json")))
CARD_T, LEAD, TAIL = 3.0, 0.8, 3.2
STEPS = ["Nhập mẫu", "Đọc Layers", "Sửa chữ", "Màn mobile", "Kiểu dáng", "Xem trước"]
URL = "jangtrinh.github.io/design-os-studio"
CHP = {  # id: dict(step, title, sub, segs, zmax, callouts)
 "c0_hook": dict(kind="hook"),
 "c1_intro": dict(kind="intro"),
 "c2_import": dict(step=0, title="Nhập mẫu", sub="Import file .fig vào Design OS Studio", zmax=1.6,
   segs=[("c2", 0, 5.5, 4.0), ("c2", 5.5, 18.5, 3.0), ("c2", 18.5, 34.2, 7.0), ("c2b", 0, 11, 5.5), ("c2b", 11, 22.3, 5.5)],
   co=[("c2", 4.1, "Bấm Import"), ("c2", 12.0, "Chọn file .fig trong hộp thoại"), ("c2b", 3.0, "Mở file vừa nhập"), ("c2b", 10.1, "Chọn trang App Pages")]),
 "c3_layers": dict(step=1, title="Đọc cấu trúc", sub="Layers cho biết mọi thứ nằm ở đâu", zmax=1.6,
   segs=[("c3", 0, 15.0, 22.4)], co=[("c3", 3.5, "Bảng Layers · mở từng cấp"), ("c3", 7.2, "Canvas đánh dấu đúng phần tử"), ("c3", 10.9, "Tiêu đề · mô tả · nút")]),
 "c4_text": dict(step=2, title="Sửa nội dung", sub="Return → gõ → Escape", zmax=1.6,
   segs=[("c4", 0, 33, 22.6)], co=[("c4", 3.8, "Page not found → Design faster"), ("c4", 10.1, "Mô tả → Click. Type. Done."), ("c4", 16.7, "Nút → Try it free"), ("c4", 23.4, "Bố cục giữ nguyên")]),
 "c5_mobile": dict(step=3, title="Màn hình mobile", sub="Cùng thao tác, cùng một file", zmax=1.6,
   segs=[("c5", 0, 26, 22.6)], co=[("c5", 3.5, "Chọn khung mobile"), ("c5", 5.6, "Tiêu đề: Any screen"), ("c5", 11.6, "Mô tả: Same layout"), ("c5", 17.9, "Nút: Get started")]),
 "c6_style": dict(step=4, title="Chỉnh kiểu dáng", sub="Fill của nút bấm", zmax=1.6,
   segs=[("c6", 0, 15.3, 19.1)], co=[("c6", 4.9, "Fill · bấm vào mã màu"), ("c6", 8.0, "Gõ mã hex FF7A1A")]),
 "c7_preview": dict(step=5, title="Xem trước", sub="Bấm Play, xem như người dùng thật", zmax=1.6, zclicks=[4.2, 15.2], zhold=1.6, colife=2.4,
   segs=[("c7p", 0, 26.3, 26.3)], co=[("c7p", 4.2, "Chọn khung 404"), ("c7p", 6.7, "Nút xem trước (Play)"), ("c7p", 9.8, "Trông như trang thật", "below"), ("c7p", 15.2, "Chọn khung mobile"), ("c7p", 20.8, "Nút cam · Get started", "below")]),
 "c8_recap": dict(kind="recap"),
 "c9_outro": dict(kind="outro"),
}
ORDER = list(CHP)
VO = {k: sentences_from_wav(f"{ROOT}/vo/{k}.wav") for k in ORDER}
def vdur(k): return len(VO[k][0]) / VO[k][1]
def chdur(k):
    c = CHP[k]
    if "step" in c: return CARD_T + LEAD + vdur(k) + TAIL
    return LEAD + vdur(k) + TAIL + ({"hook": 2.0, "outro": 5.0}.get(c["kind"], 0))
def voff(k): return (CARD_T if "step" in CHP[k] else 0) + LEAD
AGENDA_T = 8.0
def gstart(k):  # global start (agenda after hook)
    t = 0
    for q in ORDER:
        if q == "c1_intro": t += AGENDA_T
        if q == k: return t
        t += chdur(q)
TOTAL = sum(chdur(k) for k in ORDER) + AGENDA_T

CUR = {c: Cursor(f"{ROOT}/raw/{c}.cursor.json") for c in ["c2", "c2b", "c3", "c4", "c5", "c6", "c7p"]}

def sents(k): return re.split(r"(?<=[.!?])\s+", SCRIPT[k].strip())

def caption(im, k, tv):
    """tv = time within voice"""
    segs = VO[k][2]; ss = sents(k)
    idx = None
    for i, (a, b) in enumerate(segs):
        if a - 0.05 <= tv <= b + 0.35: idx = i; break
    if idx is None or idx >= len(ss): return
    a, b = segs[idx]; words = ss[idx].split()
    fnt = font(40, "Bold")
    wts = np.array([len(w) + 1.5 for w in words]); cum = np.cumsum(wts) / wts.sum()
    prog = (tv - a) / max(0.3, b - a)
    # layout
    lines = []; cur = []; cw = 0
    for i, w in enumerate(words):
        wl = fnt.getlength(w + " ")
        if cw + wl > 1380 and cur: lines.append(cur); cur = []; cw = 0
        cur.append((i, w)); cw += wl
    lines.append(cur)
    lh = 56; bh = lh * len(lines) + 34; y0 = 1056 - bh - 6
    bw = max(sum(fnt.getlength(w + " ") for _, w in l) for l in lines) + 70
    x0 = (W - bw) / 2
    al = min(1, (tv - (a - 0.05)) / 0.18) if tv < a + 0.2 else 1
    pill(im, (x0, y0 + (1 - eo(al)) * 14, x0 + bw, y0 + bh + (1 - eo(al)) * 14), (255, 255, 255, 245), 30)
    d = ImageDraw.Draw(im); yy = y0 + 17 + (1 - eo(al)) * 14
    for l in lines:
        lw = sum(fnt.getlength(w + " ") for _, w in l); xx = (W - lw) / 2
        for i, w in l:
            done = prog >= cum[i] - wts[i] / wts.sum() * 0.5
            cur_w = (cum[i] - wts[i] / wts.sum() <= prog < cum[i])
            col = CORAL if cur_w else (INK if done else (170, 170, 182))
            d.text((xx, yy), w, font=fnt, fill=col); xx += fnt.getlength(w + " ")
        yy += lh

def rail(im, step, t):
    d = ImageDraw.Draw(im)
    d.text((40, 52), "Design OS", font=font(30, "ExtraBold"), fill=INK)
    d.text((40, 90), "STUDIO · FREE", font=font(16, "Bold"), fill=CORAL)
    d.text((40, 960), "Tải miễn phí", font=font(17, "Bold"), fill=CORAL)
    d.text((40, 986), "jangtrinh.github.io/", font=font(19, "Bold"), fill=INK)
    d.text((40, 1012), "design-os-studio", font=font(19, "Bold"), fill=INK)
    for i, s in enumerate(STEPS):
        y = 190 + i * 112; act = i == step
        if act:
            pill(im, (24, y - 8, 276, y + 74), CORAL + (255,), 26)
            d.text((50, y + 33), f"{i+1:02d}", font=font(32, "ExtraBold"), fill=(255, 255, 255), anchor="lm")
            d.text((112, y + 33), s, font=font(23, "Bold"), fill=(255, 255, 255), anchor="lm")
        else:
            doneS = i < step
            col = MINT if doneS else (205, 200, 192)
            d.ellipse((40, y + 12, 78, y + 50), fill=col)
            d.text((59, y + 31), "✓" if False else f"{i+1}", font=font(20, "Bold"), fill=(255, 255, 255), anchor="mm")
            d.text((112, y + 31), s, font=font(23, "Bold"), fill=(120, 120, 132) if not doneS else INK, anchor="lm")

def progress(im, gt):
    d = ImageDraw.Draw(im); d.rectangle((0, H - 7, W, H), fill=(240, 228, 212)); d.rectangle((0, H - 7, int(W * gt / TOTAL), H), fill=CORAL)

def callout(im, anchor, text, age, life, pos=None, box_lim=(CX0 + 40, CY0 + 40, CX0 + CW - 40, CY0 + CH - 40)):
    if age < 0 or age > life: return
    a = eo(age / 0.35) * (1 - ease((age - (life - 0.4)) / 0.4)); s = 0.6 + 0.4 * eo(age / 0.35)
    fnt = font(30, "Bold"); tw = fnt.getlength(text); bw = tw + 56; bh = 64
    ax, ay = anchor
    bx = min(max(ax + 70, box_lim[0]), box_lim[2] - bw); by = ay - 120
    by = min(max(by, box_lim[1]), box_lim[3] - bh)
    if pos == "below": by = ay + 70
    if abs(by - ay) < 40 and bx < ax < bx + bw: by = ay + 60 if ay + 60 + bh < box_lim[3] else ay - 130
    cx, cy = bx + bw / 2, by + bh / 2
    nb = (cx - bw * s / 2, cy - bh * s / 2, cx + bw * s / 2, cy + bh * s / 2)
    d = ImageDraw.Draw(im)
    # dotted line anchor -> bubble edge
    ex, ey = min(max(ax, bx), bx + bw), min(max(ay, by), by + bh)
    L = math.hypot(ex - ax, ey - ay); n = int(L / 14)
    for i in range(n):
        u = i / max(1, n); px, py = ax + (ex - ax) * u, ay + (ey - ay) * u
        if a > 0.5: d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=CORAL)
    d.ellipse((ax - 9, ay - 9, ax + 9, ay + 9), outline=CORAL, width=4)
    if a > 0.3:
        pill(im, nb, (255, 255, 255, int(255 * min(1, a))), 24, outline=CORAL + (255,), w=3)
        d.text((cx, cy), text, font=fnt, fill=INK, anchor="mm")

# ---------- footage chapter ----------
def seg_table(c):
    tot = sum(s[3] for s in c["segs"]); D = vdur_k = None
    return tot

def render_footage(k, out):
    c = CHP[k]; D = chdur(k); n = int(round(D * FPS)); vo0 = voff(k)
    body = D - CARD_T; segs = c["segs"]; tot = sum(s[3] for s in segs); sc = body / tot
    tab = []; t0 = 0
    for clip, a, b, od in segs: tab.append((clip, a, b, t0, t0 + od * sc)); t0 += od * sc
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                           "-c:v", "libx264", "-crf", "15", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    srcs = {}
    def src_for(i):
        clip, a, b, s0, s1 = tab[i]
        if i not in srcs:
            for j in list(srcs): srcs[j].close(); del srcs[j]
            srcs[i] = Src(f"{ROOT}/raw/{clip}.mp4", a, b)
        return srcs[i]
    gs = gstart(k); gtot = TOTAL
    for fi in range(n):
        t = fi / FPS
        if t < CARD_T:
            im = chapter_card(k, t)
        else:
            tb = t - CARD_T
            i = next((j for j, s in enumerate(tab) if s[3] <= tb < s[4]), len(tab) - 1)
            clip, a, b, s0, s1 = tab[i]; ts = a + (min(tb, s1) - s0) / (s1 - s0) * (b - a)
            fr = src_for(i).get(ts); cur = CUR[clip]
            # camera
            envs = []
            for cc in cur.clicks:
                if "zclicks" in c and not any(abs(cc - z) < 0.3 for z in c["zclicks"]): continue
                hold = c.get("zhold", 4.6)
                e = ease((ts - (cc - 0.9)) / 0.8) * (1 - ease((ts - (cc + hold)) / 1.0)); envs.append((e, cur.pos(cc)))
            mx = max([e for e, _ in envs] + [0]); se = sum(e for e, _ in envs)
            fx = (sum(e * p[0] for e, p in envs) + (1 - mx) * 800) / (se + (1 - mx)); fy = (sum(e * p[1] for e, p in envs) + (1 - mx) * 481) / (se + (1 - mx))
            z = 1 + (c["zmax"] - 1) * mx
            im = bg(t).convert("RGB")
            ap = eo(tb / 0.6); box, place = draw_card(im, fr, (z, fx, fy), 1.0, (0, int((1 - ap) * 40)), 0.9 + 0.1 * ap)
            cur.draw(im, ts, box, place)
            for coi in c["co"]:
                cl, st, text = coi[:3]; pos = coi[3] if len(coi) > 3 else None
                if cl != clip: continue
                # time at which source time st occurs
                if not (a <= st <= b): continue
                tcl = s0 + (st - a) / (b - a) * (s1 - s0)
                ax, ay = raw2scr(*cur.pos(st), box, place)
                callout(im, (ax, ay), text, tb - (tcl - 0.4), c.get("colife", 3.4), pos=pos)
            rail(im, c["step"], t)
            # title chip
            d = ImageDraw.Draw(im)
            tv = t - vo0
            if tv >= 0: caption(im, k, tv)
            progress(im, gs + t)
        ff.stdin.write(np.asarray(im.convert("RGB")).tobytes())
    ff.stdin.close(); ff.wait()

def chapter_card(k, t):
    c = CHP[k]; im = bg(t + 3).convert("RGB"); d = ImageDraw.Draw(im)
    p = eo(t / 0.7); q = 1 - ease((t - (CARD_T - 0.45)) / 0.45)
    cols = [CORAL, BLUE, MINT, PURPLE, PINK, CORAL]; col = cols[c["step"]]
    # big shape bursts
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for i in range(7):
        ang = i * 0.9 + t * 0.6; r = 260 + 70 * math.sin(t * 2 + i); x = 1450 + math.cos(ang) * r * p; y = 520 + math.sin(ang) * r * 0.9 * p
        s = 36 + 14 * i; od.rounded_rectangle((x - s, y - s, x + s, y + s), 18 if i % 2 else s, fill=col + (60 + 18 * i,))
    im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
    num = f"{c['step']+1:02d}"; y = 330 + (1 - p) * 90
    d.text((150, y), num, font=font(360, "ExtraBold"), fill=col + () if False else col)
    d.text((170, 690 + (1 - p) * 40), "BƯỚC " + str(c["step"] + 1), font=font(34, "Bold"), fill=GRAY)
    tw = font(96, "ExtraBold").getlength(c["title"])
    d.text((150, 760 + (1 - p) * 60), c["title"], font=font(96, "ExtraBold"), fill=INK)
    d.rounded_rectangle((150, 890, 150 + (tw * 0.6) * eo((t - 0.2) / 0.6), 904), 7, fill=col)
    d.text((150, 925 + (1 - p) * 30), c["sub"], font=font(38, "Medium"), fill=(110, 110, 124))
    for i in range(len(STEPS)):
        x = 150 + i * 46; d.ellipse((x, 1000, x + 26, 1026), fill=col if i <= c["step"] else (222, 214, 204))
    if q < 1: im = Image.blend(bg(t + 3).convert("RGB"), im, q)
    return im

def render_special(k, out):
    c = CHP[k]; D = chdur(k); n = int(round(D * FPS)); vo0 = voff(k); gs = gstart(k)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                           "-c:v", "libx264", "-crf", "15", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    kind = c["kind"]
    def grab(clip, t):
        s = Src(f"{ROOT}/raw/{clip}.mp4", max(0, t - 0.1), t + 0.5); f = s.get(t); s.close(); return f
    if kind == "intro": F0 = grab("c2", 1.0)
    if kind == "recap": FB = grab("c2b", 21.0); FA = grab("c6", 14.0)
    if kind == "hook": H1 = Src(f"{ROOT}/raw/c4.mp4", 8, 8 + D * 0.4);
    for fi in range(n):
        t = fi / FPS; tv = t - vo0; im = bg(t).convert("RGB"); d = ImageDraw.Draw(im)
        if kind == "intro":
            ap = eo(t / 0.7); z = 1.0 + 0.06 * (t / D)
            box, place = draw_card(im, F0, (z, 800, 481), 1.0, (0, int((1 - ap) * 40)), 0.9 + 0.1 * ap)
            rail(im, -1, t)
            chips = [("FREE", "Miễn phí, chạy ngay trên máy", MINT), ("source-available", "Mã nguồn công khai, ai cũng xem được", BLUE),
                     (".fig", "Đọc được file thiết kế có sẵn", CORAL), ("CC0", "Tailwind Figma Free Edition · Themesberg", PURPLE),
                     ("Not affiliated with Figma", "Design OS không liên kết với Figma", GRAY)]
            sg = VO[k][2]; starts = [LEAD + sg[1][0], LEAD + sg[1][0] + 2.6, LEAD + sg[2][0], LEAD + sg[3][0], LEAD + sg[4][0]]
            for i, (big, small, col) in enumerate(chips):
                age = t - starts[i]
                if age < 0: continue
                a = eo(age / 0.45); x = 900 + (1 - a) * 300; y = 150 + i * 138
                pill(im, (x, y, x + 760, y + 112), (255, 255, 255, int(255 * a)), 28, outline=col + (255,), w=4)
                d.text((x + 34, y + 38), big, font=font(34 if len(big) < 14 else 28, "ExtraBold"), fill=col if col != GRAY else INK, anchor="lm")
                d.text((x + 34, y + 80), small, font=font(24, "Medium"), fill=(100, 100, 112), anchor="lm")
        elif kind == "hook":
            fr = H1.get(8 + min(t, D * 0.4 - 1) * 1.0)
            ap = eo(t / 0.8)
            box, place = draw_card(im, fr, (1.5, 900, 420), 1.0, (250 + int((1 - ap) * 200), 40), 0.84)
            lines = [("Một file mẫu.", INK, 0.3), ("Sáu lần sửa.", BLUE, 1.2), ("Dưới 5 phút.", CORAL, 2.1)]
            for i, (tx, col, st) in enumerate(lines):
                a = eo((t - st) / 0.6); xx = 60 - (1 - a) * 80
                if a > 0: d.text((xx, 250 + i * 150), tx, font=font(86, "ExtraBold"), fill=col)
            a = eo((t - 3.2) / 0.6)
            if a > 0: d.text((64, 720), "Design OS Studio · quay thật 100%", font=font(32, "Bold"), fill=GRAY)
        elif kind == "recap":
            ap = eo(t / 0.6); box, place = draw_card(im, FB, (1.0, 800, 481), 1.0, (0, int((1 - ap) * 40)), 0.9 + 0.1 * ap)
            u = ease((t - (LEAD + 3.0)) / 3.0); xcut = CX0 + CW * u
            if u > 0:
                crop = FA.resize((CW, CH), Image.BILINEAR); w = int(CW * u)
                m = _m = Image.new("L", (CW, CH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, CW - 1, CH - 1), 22, fill=255)
                m2 = Image.new("L", (CW, CH), 0); ImageDraw.Draw(m2).rectangle((0, 0, w, CH), fill=255)
                from PIL import ImageChops
                im.paste(crop, (CX0, CY0), ImageChops.multiply(m, m2))
                d.rounded_rectangle((xcut - 4, CY0, xcut + 4, CY0 + CH), 4, fill=CORAL)
            pill(im, (CX0 + 24, CY0 + 24, CX0 + 190, CY0 + 80), (255, 255, 255, 235), 20); d.text((CX0 + 107, CY0 + 52), "Trước", font=font(28, "Bold"), fill=INK, anchor="mm")
            if u > 0.2: pill(im, (CX0 + CW - 190, CY0 + 24, CX0 + CW - 24, CY0 + 80), CORAL + (255,), 20); d.text((CX0 + CW - 107, CY0 + 52), "Sau", font=font(28, "Bold"), fill=(255, 255, 255), anchor="mm")
            tl = [("6", "lần sửa chữ", BLUE, LEAD + 9.0), ("1", "lần đổi màu", CORAL, LEAD + 11.0), ("0", "lần lệch bố cục", MINT, LEAD + 13.0)]
            for i, (nm, lb, col, st) in enumerate(tl):
                a = eo((t - st) / 0.5)
                if a <= 0: continue
                x = 330 + i * 450; y = 700 - (1 - a) * 60
                pill(im, (x, y, x + 400, y + 130), (255, 255, 255, int(255 * a)), 30, outline=col + (255,), w=4)
                d.text((x + 70, y + 65), nm, font=font(76, "ExtraBold"), fill=col, anchor="mm"); fs = 30
                while font(fs, "Bold").getlength(lb) > 236 and fs > 18: fs -= 1
                d.text((x + 140, y + 65), lb, font=font(fs, "Bold"), fill=INK, anchor="lm")
            rail(im, -1, t)
        elif kind == "outro":
            sg = VO[k][2]; habits = [("1", "Chọn lớp trong Layers", "thay vì bấm trên canvas", BLUE, LEAD + sg[1][0]), ("2", "Vào chế độ sửa", "rồi mới gõ", CORAL, LEAD + sg[2][0]), ("3", "Kiểm tra từng bước", "trước khi đi tiếp", MINT, LEAD + sg[3][0])]
            d.text((W / 2, 130), "3 thói quen", font=font(78, "ExtraBold"), fill=INK, anchor="mm")
            for i, (nm, a1, a2, col, st) in enumerate(habits):
                a = eo((t - st) / 0.5)
                if a <= 0: continue
                x = 160 + i * 580; y = 250 + (1 - a) * 60
                pill(im, (x, y, x + 540, y + 380), (255, 255, 255, int(255 * a)), 40, outline=col + (255,), w=5)
                d.ellipse((x + 40, y + 40, x + 140, y + 140), fill=col); d.text((x + 90, y + 90), nm, font=font(56, "ExtraBold"), fill=(255, 255, 255), anchor="mm")
                d.text((x + 40, y + 220), a1, font=font(38, "ExtraBold"), fill=INK); d.text((x + 40, y + 280), a2, font=font(32, "Medium"), fill=(110, 110, 124))
            a = eo((t - (LEAD + sg[4][0])) / 0.6)
            if a > 0:
                y0 = 680 - (1 - a) * 40
                pill(im, (W / 2 - 600, y0, W / 2 + 600, y0 + 150), CORAL + (255,), 75)
                d.text((W / 2, y0 + 48), "Design OS Studio — miễn phí, tải tại", font=font(34, "Bold"), fill=(255, 240, 225), anchor="mm")
                d.text((W / 2, y0 + 104), "https://" + URL + "/", font=font(46, "ExtraBold"), fill=(255, 255, 255), anchor="mm")
                d.text((W / 2, y0 + 190), "Source-available · Not affiliated with Figma", font=font(24, "Medium"), fill=GRAY, anchor="mm")
        if tv >= 0: caption(im, k, tv)
        progress(im, gs + t)
        ff.stdin.write(np.asarray(im).tobytes())
    ff.stdin.close(); ff.wait()

def render_agenda(out):
    n = int(AGENDA_T * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                           "-c:v", "libx264", "-crf", "15", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    cols = [CORAL, BLUE, MINT, PURPLE, PINK, CORAL]
    for fi in range(n):
        t = fi / FPS; im = bg(t + 9).convert("RGB"); d = ImageDraw.Draw(im)
        a0 = eo(t / 0.5); d.text((W / 2, 150 - (1 - a0) * 30), "Lộ trình 6 bước", font=font(84, "ExtraBold"), fill=INK, anchor="mm")
        for i, s in enumerate(STEPS):
            a = eo((t - 0.5 - i * 0.55) / 0.45)
            if a <= 0: continue
            col = cols[i]; x = 150 + (i % 3) * 580; y = 300 + (i // 3) * 330 + (1 - a) * 50
            pill(im, (x, y, x + 540, y + 270), (255, 255, 255, int(255 * a)), 40, outline=col + (255,), w=4)
            d.text((x + 40, y + 90), f"{i+1:02d}", font=font(110, "ExtraBold"), fill=col, anchor="lm")
            d.text((x + 40, y + 200), s, font=font(42, "ExtraBold"), fill=INK, anchor="lm")
        out_a = 1 - ease((t - (AGENDA_T - 0.4)) / 0.4)
        if out_a < 1: im = Image.blend(bg(t + 9).convert("RGB"), im, out_a)
        progress(im, gstart("c1_intro") - AGENDA_T + t)
        ff.stdin.write(np.asarray(im).tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == "__main__":
    what = sys.argv[1]
    if what == "agenda": render_agenda(f"{ROOT}/out/agenda.mp4")
    elif what == "info":
        for k in ORDER: print(k, round(chdur(k), 2), round(gstart(k), 1))
        print("total", round(TOTAL, 1))
    else:
        out = f"{ROOT}/out/{what}.mp4"
        if len(sys.argv) > 2: CHP[what]["_test"] = 1
        (render_footage if "step" in CHP[what] else render_special)(what, out)
