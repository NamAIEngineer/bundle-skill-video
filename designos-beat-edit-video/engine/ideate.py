"""Idea + plan generator. Different concept, music, palette and structure on every seed.
  python ideate.py plan  --edits 5 --seed 42 [--style house] [--out plan.json]
  python ideate.py batch --count 30 --seed 1 [--min 25 --max 45] --out batch/   (N different plans + manifest.json)
  python ideate.py build plan.json times.json --out spec.json
`plan` invents: concept, hook line, music style/bpm/key, palette (dark or light), scene structure placed on bar lines,
and where each edit lands. The agent must then WRITE the final copy (see references/creative-brief.md) - the generator
only supplies constraints and a random-but-valid starting point, so no two videos share a skeleton.
`build` merges measured footage times (times.json) into a full spec that run.py can validate/render."""
import colorsys, json, os, random, sys

MUSIC = {"house": (120, 128), "lofi": (72, 88), "trap": (136, 150), "synthwave": (100, 116), "cinematic": (84, 100)}
CONCEPTS = [
    ("on the beat",    "Every edit lands on the beat.",           "Placed on the grid.",            "edits sync to bars"),
    ("speedrun",       "One screen. {n} edits. {s} seconds.",     "Built by an agent, edited by you.", "timer counts up, each edit stamps a split time"),
    ("before / after", "Before. After. Same app.",                "Change anything. Keep the layout.", "each edit shows old text flashing to new"),
    ("one take",       "No cuts. No mockups. Just the app.",      "Real screen, real edits.",       "single continuous take feel, minimal text"),
    ("questions",      "What if your design reacted to you?",     "Your turn: what would you edit first?", "hook is a question, outro asks one too"),
    ("count-in",       "1, 2, 3, 4 - edit.",                      "Ready when you are.",            "4-count intro, edits drop on beat 1"),
    ("typography",     "Words move. Layouts follow.",             "Type it. See it.",               "big kinetic type leads, UI is supporting"),
]
STRUCT = ["cold_open", "title_first", "countdown"]

def palette(rs):
    light = rs.random() < 0.4
    h = rs.random()
    ac = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, 0.72, 0.95))
    if light:
        bg, tx, gr, sub = (244, 243, 240), (22, 22, 26), (130, 128, 138), (70, 68, 78)
    else:
        bg = tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, 0.25, 0.09)); tx, gr, sub = (243, 242, 245), (140, 138, 150), (190, 188, 200)
    return {"accent": list(ac), "bg": list(bg), "text": list(tx), "grey": list(gr), "sub": list(sub)}, ("light" if light else "dark")

def plan(a):
    seed = int(a.get("seed", random.randrange(10 ** 6))); rs = random.Random(seed)
    style = a.get("style") or rs.choice(sorted(MUSIC))
    lo, hi = MUSIC[style]; bpm = rs.randrange(lo, hi + 1, 2)
    bar = 4 * 60.0 / bpm
    n = int(a.get("edits", 5))
    concept = rs.choice(CONCEPTS); struct = rs.choice(STRUCT)
    pal, theme = palette(rs)
    intro_bars = {"cold_open": 1, "title_first": 2, "countdown": 2}[struct]
    gap = rs.choice([2, 3, 4])                      # bars between edits
    first = intro_bars + rs.choice([1, 2])
    edits, bar_i = [], first
    for i in range(n):
        edits.append({"index": i + 1, "bar": bar_i, "T": bar_i * bar}); bar_i += gap
    payoff_bars = rs.choice([2, 3]); outro_bars = 2
    total_bars = bar_i - gap + 2 + payoff_bars + outro_bars
    tot = round(total_bars * bar, 3)
    return {"seed": seed, "concept": {"name": concept[0], "hook": concept[1], "outro": concept[2], "device": concept[3]},
            "structure": struct, "music": {"style": style, "seed": seed, "peak": 0.8}, "bpm": bpm, "bar_seconds": bar,
            "palette": pal, "theme": theme, "edits": edits, "intro_bars": intro_bars, "payoff_bars": payoff_bars,
            "outro_bars": outro_bars, "total": tot,
            "marketing": {"feature": "<one shipped design:os studio feature this video sells>", "viewer_pain": "<who and what pain>", "promise": "<one line>", "cta": "<call to action: FREE, try design:os studio>", "guardrails": "FREE; source-available (never open-source); no Figma killer; only shipped features; every claim backed by real footage"},
            "note": "Rewrite hook/outro in your own words for THIS product. Do not reuse a previous video's concept. Record footage so each edit's click can finish 0.4-0.5 s before its T."}


# Candidate design:os studio features. VERIFY each one is shipped and works on the real app before filming it.
FEATURES = [
    "Claude Code builds a whole app/web screen on the canvas from one prompt",
    "Keep / Revert bar: review every change the agent made to your layers",
    "Edit any text or layer live on the canvas (double-click, type)",
    "Auto layout: frames that resize and flow as content changes",
    "Prototype tab: click-through flows from the same canvas",
    "Developer view: inspect the code of what you designed",
    "Copy a frame to a slide deck in one click",
    "Agent panel with several Claude Code sessions side by side",
    "Share a design straight from the canvas",
]
HOOK_STYLES = ["question", "bold claim (provable on screen)", "number / timer", "before-after contrast", "command ('watch this')", "curiosity gap"]

def batch(count, seed, outdir, tmin=25.0, tmax=45.0):
    os.makedirs(outdir, exist_ok=True)
    rs = random.Random(seed); used = set(); plans = []
    tries = 0
    while len(plans) < count and tries < 5000:
        tries += 1
        sd = rs.randrange(10 ** 6)
        r = random.Random(sd)
        edits = r.choice([3, 4, 5, 6])
        p = plan({"seed": sd, "edits": edits})
        if not (tmin <= p['total'] <= tmax):
            continue
        feat = FEATURES[len(plans) % len(FEATURES)]
        key = (p["music"]["style"], p["concept"]["name"], feat)
        hue = tuple(c // 40 for c in p["palette"]["accent"])
        # distinct: no repeated (style, concept, feature) and no repeated accent bucket + theme within 5 neighbours
        if key in used or any(q["palette"]["accent"] and tuple(c // 40 for c in q["palette"]["accent"]) == hue and q["theme"] == p["theme"] for q in plans[-5:]):
            continue
        if sum(1 for q in plans if q["music"]["style"] == p["music"]["style"]) > count // len(MUSIC) + 1:
            continue
        used.add(key)
        p["marketing"]["feature"] = feat
        p["marketing"]["hook_style"] = HOOK_STYLES[len(plans) % len(HOOK_STYLES)]
        p["index"] = len(plans) + 1
        plans.append(p)
    for p in plans:
        json.dump(p, open(os.path.join(outdir, "plan_%02d.json" % p["index"]), "w"), indent=1, ensure_ascii=False)
    man = [{"index": p["index"], "seed": p["seed"], "style": p["music"]["style"], "bpm": p["bpm"], "concept": p["concept"]["name"],
            "theme": p["theme"], "structure": p["structure"], "edits": len(p["edits"]), "total": p["total"],
            "feature": p["marketing"]["feature"], "hook_style": p["marketing"]["hook_style"], "status": "planned"} for p in plans]
    json.dump(man, open(os.path.join(outdir, "manifest.json"), "w"), indent=1, ensure_ascii=False)
    for m in man: print(m["index"], m["style"], m["bpm"], m["concept"], m["theme"], m["structure"], "%de" % m["edits"], "%.0fs" % m["total"], "|", m["feature"][:40], "|", m["hook_style"])
    print("wrote", len(plans), "plans ->", outdir)

def build(plan_p, times_p, out):
    p = json.load(open(plan_p)); t = json.load(open(times_p))
    bar = p["bar_seconds"]; sc = [["intro", 0, round(p["intro_bars"] * bar, 4), 0]]
    prev = sc[0][2]; cards = []
    for i, e in enumerate(p["edits"]):
        c = dict(t["cards"][i]); c["T"] = e["T"]
        end = e["T"] + (p["edits"][i + 1]["T"] - e["T"] if i + 1 < len(p["edits"]) else 2 * bar)
        c.setdefault("scene", "E%d" % (i + 1)); c.setdefault("pulse", None)
        sc.append([c["scene"], round(prev, 4), end, c.get("take", 1)]); prev = end; cards.append(c)
    total = p["total"]; start_out = round(total - p["outro_bars"] * bar, 4)
    if prev < start_out: sc[-1][2] = start_out
    sc.append(["outro", start_out, total, 0])
    spec = {"title": p["concept"]["name"], "fps": 30, "bpm": p["bpm"], "beats_per_bar": 4, "total": total, "size": [1920, 1080],
            "palette": p["palette"], "fonts": t["fonts"], "window": t["window"], "hud_left": t.get("hud_left", p["concept"]["name"].upper()),
            "takes": t["takes"], "scenes": sc, "intro": t["intro"], "outro": {**t["outro"], "start": start_out},
            "cursor": t.get("cursor", {"sidebar_x": 0.076, "start": [0.69, 0.78]}), "cards": cards, "music": p["music"],
            "audio": {"groove_start": sc[0][2], "groove_end": start_out, "whoosh_at": sc[0][2]}}
    json.dump(spec, open(out, "w"), indent=1, ensure_ascii=False); print("wrote", out)

if __name__ == "__main__":
    c = sys.argv[1]; args = sys.argv[2:]
    if c == "plan":
        o = dict(zip([x.lstrip("-") for x in args[::2]], args[1::2])); r = plan(o)
        json.dump(r, open(o.get("out", "plan.json"), "w"), indent=1, ensure_ascii=False)
        print(json.dumps({k: r[k] for k in ("seed", "concept", "structure", "music", "bpm", "theme", "total")}, ensure_ascii=False))
    elif c == "batch":
        o = dict(zip([x.lstrip("-") for x in args[::2]], args[1::2])); batch(int(o.get("count", 30)), int(o.get("seed", 1)), o.get("out", "batch"), float(o.get("min", 25)), float(o.get("max", 45)))
    elif c == "build":
        o = dict(zip([x.lstrip("-") for x in args[2::2]], args[3::2])); build(args[0], args[1], o.get("out", "spec.json"))
