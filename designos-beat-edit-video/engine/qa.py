"""QA for a finished video. Usage: python qa.py final.mp4 spec.json
Checks: 1920x1080, 30 fps, duration, audio present, true peak <= 0 dBFS (warns near 0), and spec rules."""
import json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beatlib


def probe(p):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration",
                                 "-of", "json", p])
    return json.loads(o)["streams"]


def main(video, spec_path):
    spec = beatlib.load(spec_path); tl = beatlib.Timeline(spec)
    bad = list(tl.validate()); ok = []
    st = probe(video)
    v = [s for s in st if s["codec_type"] == "video"][0]
    a = [s for s in st if s["codec_type"] == "audio"]
    if (v["width"], v["height"]) != tuple(spec["size"]): bad.append("size %sx%s" % (v["width"], v["height"]))
    num, den = v["r_frame_rate"].split("/")
    if round(int(num) / int(den)) != spec["fps"]: bad.append("fps %s" % v["r_frame_rate"])
    if abs(float(v["duration"]) - tl.TOTAL) > 0.1: bad.append("duration %s vs %s" % (v["duration"], tl.TOTAL))
    if not a: bad.append("no audio track")
    else:
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        tp = None
        for line in r.splitlines():
            if line.strip().startswith("Peak:"): tp = float(line.split()[1])
        if tp is not None:
            (bad if tp > 0.0 else ok).append("true peak %.1f dBFS" % tp)
            if -1.0 < tp <= 0.0: print("warn: true peak %.1f dBFS is close to clipping; lower audio.peak to about 0.8" % tp)
    print("OK:", ok or "-")
    if bad:
        print("PROBLEMS:"); [print(" -", b) for b in bad]; sys.exit(1)
    print("QA passed")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
