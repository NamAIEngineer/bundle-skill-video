"""Runner. python run.py <command> <spec.json> [--root DIR] [--out DIR]
  validate   check the spec obeys the beat rules (bar-line edits, 16th typing grid, pauses)
  render     render all scenes (or: render F N) to <out>/q_<scene>.mp4
  audio      synthesise <out>/bgm.wav
  mux        concat scenes + audio -> <out>/final.mp4
  qa         run qa.py on final.mp4
  all        validate, render, audio, mux, qa
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import beatlib


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    cmd, spec = a[0], os.path.abspath(a[1]); rest = a[2:]
    root, out, scenes = os.getcwd(), None, []
    i = 0
    while i < len(rest):
        if rest[i] == "--root": root = os.path.abspath(rest[i + 1]); i += 2
        elif rest[i] == "--out": out = os.path.abspath(rest[i + 1]); i += 2
        else: scenes.append(rest[i]); i += 1
    out = out or root
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, BEAT_SPEC=spec, BEAT_ROOT=root, BEAT_OUT=out)
    S = beatlib.load(spec); tl = beatlib.Timeline(S)

    def validate():
        bad = tl.validate()
        for b in bad: print("RULE:", b)
        if bad: sys.exit(1)
        print("spec ok:", len(tl.CARDS), "edits, all on bar lines")

    def render():  subprocess.check_call([sys.executable, os.path.join(HERE, "render.py")] + scenes, env=env)
    def audio():   subprocess.check_call([sys.executable, os.path.join(HERE, "music.py" if S.get("music") else "audio.py"), os.path.join(out, "bgm.wav")], env=env)

    def mux():
        lst = os.path.join(out, "concat.txt")
        with open(lst, "w") as f:
            for s in tl.SCENES: f.write("file '%s'\n" % os.path.join(out, "q_%s.mp4" % s[0]))
        v = os.path.join(out, "video.mp4")
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", v])
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", os.path.join(out, "bgm.wav"), "-map", "0:v", "-map", "1:a",
                               "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", os.path.join(out, "final.mp4")])
        print("wrote", os.path.join(out, "final.mp4"))

    def qa(): subprocess.check_call([sys.executable, os.path.join(HERE, "qa.py"), os.path.join(out, "final.mp4"), spec])

    steps = {"validate": [validate], "render": [validate, render], "audio": [audio], "mux": [mux], "qa": [qa],
             "all": [validate, render, audio, mux, qa]}
    for f in steps[cmd]: f()


main()
