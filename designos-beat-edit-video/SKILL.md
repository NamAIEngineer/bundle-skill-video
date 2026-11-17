---
name: "designos-beat-edit-video"
description: "Make marketing videos that sell the design:os studio app itself - real Studio footage, a fresh idea, look, motion and music every time. For TikTok/Reels/Shorts beat edits and 3-5 minute YouTube tutorials with the approved Vietnamese voiceover."
---

# designos-beat-edit-video

**Purpose: marketing the design:os studio app.** Every video shows the real app doing something a viewer wants (one feature, one clear promise, one call to action). The app is the hero, not the editing trick.

**Not a fixed template. Every video must be different from every earlier one:** new idea, new feature or task shown, new footage, new structure, new palette and background, new motion language, new music. Creativity has to stand out in the first 3 seconds. Before planning, read the earlier briefs in the Project (`orca-briefs/*designos*`) and pick choices that none of them used; write the choices into the new brief so the next video can avoid them. (`engine/ideate.py`, `engine/music.py`, `references/creative-brief.md` help with this.) `spec/design-in-4-4.spec.json` is only one worked example (its footage is old: never reuse it, always record new footage).

One spec JSON drives everything: video (render.py), audio (audio.py), checks (beatlib.validate, qa.py).
A new video = a new spec + new raw takes. No code changes.

**Batch:** `python engine/ideate.py batch --count 30 --seed N --out batch/` makes N different plans (style, bpm, concept, palette, structure, edits, length, feature) plus manifest.json. See references/chatgpt-instructions.md.

## Hard rule
All footage comes from the real **design:os studio** app (Openscreen `--window "design:os studio"`), recorded fresh for each video. No mock-ups, no other app, no old takes.

## Pipeline
0. `python engine/ideate.py plan --edits N --seed <new> --out plan.json` -> concept, music style + bpm, palette, structure, where each edit lands. Rewrite the copy yourself.
   After recording: `ideate.py build plan.json times.json --out spec.json`. Music: 5 generative styles (house, lofi, trap, synthwave, cinematic), set in `spec.music`.
1. **Record** real footage of the app (Openscreen, `--window "design:os studio"`, cursor editable-overlay).
   Rules: click, pause about 0.8 s, then type. Show the whole app. Human-like cursor. Record longer than the action.
2. **Fill the spec** (`spec/design-in-4-4.spec.json` is the working example; fields in `references/spec-fields.md`).
   Per edit you only need raw-footage times: `tc` (cursor starts to click the sidebar), `hit` (screen changes),
   `td` (double-click on the text), `ts`/`te` (first/last typed character), plus `T` = the bar line (video seconds) where the edit lands.
3. `python engine/run.py validate spec.json` - fails if an edit is off a bar line, typing is off the 16th grid,
   the click-to-text pause is too short, or scenes do not tile the timeline.
4. `python engine/run.py all spec.json --root <dir with raw takes> --out <dir>` -> `final.mp4` (1920x1080, 30 fps, AAC) and runs `qa.py`.
   Partial: `render F N` (scenes), `audio`, `mux`, `qa`.
5. Look at 3-4 frames and the contact sheet before delivering. Nam posts himself; never post.

## Guardrails (Marketing HQ)
FREE, say "source-available" (never "open-source"), no "Figma killer", "Developer view", only shipped features,
every claim backed by real footage. The video is about the product, not about the making.

## Why it works
Footage time is mapped to video time by anchors (`beatlib.Timeline.anchors`), so a click lands on the bar line
whatever speed it was recorded at. 120 BPM: beat 0.5 s, bar 2 s, one typed character = 0.125 s.

## Verified
Scene F re-rendered from the spec is frame-identical (PSNR inf) to the original; the audio WAV is byte-identical.
Default peak 0.89 gave +0.7 dBFS true peak on the sample; for new videos set `audio.peak` to about 0.8.

## Requirements
python3, numpy, Pillow, ffmpeg/ffprobe; macOS fonts (HelveticaNeue.ttc, SFNSMono.ttf) or edit `fonts` in the spec.
`legacy/design-in-4-4/` keeps the original scripts (tl.py, make8.py, audio9.py, cursor2.py) for reference.

## Prompt Motion: use it on every video
The Prompt Motion Bridge tools (`Prompt_Motion_Bridge__recommend_motion_references`, `search_motion_references`, `get_motion_reference`) are the source of motion ideas. For every video:
- Describe each scene (hook, chapter cards, transitions, callouts, captions, stat/recap, end card) and ask for references; search with fresh keywords each time (kinetic type, mask reveal, morph, parallax, split-screen, glitch, liquid, stagger, counter, 3D tilt, ...).
- Pick at least 5 different references per video and build them in code (PIL/numpy/ffmpeg or Remotion). Note the reference ids in the brief and do not reuse the same set as the previous video.
- Bright, lots of animation, but the app footage stays the hero and readable.

## Long-form tutorial (3-5 min, Vietnamese voiceover, YouTube)
First one approved by Nam on 2026-11-16 (`final_v3.mp4`, 4:21: 6-step process from a .fig template to desktop+mobile screens). Treat it only as an example: the next long video needs a different topic, footage, structure and look.
Starter code: `longform/` in this skill (also on the Mac at `longform/`): README.md, script2.py, gen_tts.py, lib.py, build.py, audio.py. Copy it into a new workspace and change it: chapters, layout, card and caption design, background, palette, motion (from Prompt Motion), music style and tempo. Never ship the same look twice.

**Ideas:** each video picks its own angle and format, e.g. a challenge against a timer, before/after makeover, one feature deep-dive, "3 mistakes beginners make", redesign a real-looking screen, build a mini design system, mobile-first, speed-run, Q&A. Every chapter must show something the viewer wants; a chapter that is only "a mistake I made" was rejected as irrelevant. Shipped features only; check in the app before promising one (Play preview at top-right ▷ works and looks great).

**Footage:** record fresh with Openscreen for every video (different template or file, different screens, different edits). Openscreen records only the app window, not native macOS dialogs: show the file picker as a text callout, never a mock-up. Select text layers in Layers, press Return, check the text is highlighted, then type; typing into an unfocused field fires shortcuts. Before the voiceover claims an edit, check the app state again (an undo once silently reverted a button text).

**Voice (approved by Nam): VieNeu-TTS v3 Turbo, preset "Hải Đăng".** Runs on the Mac (`.venv-voice/bin/python`, `gen_tts.py`), 48 kHz, ~0.3x real time. Do not clone Jang's voice without his written OK.
- Generate sentence by sentence with 0.18 s of exact zeros between sentences; captions are timed from those gaps, so display text and TTS text must have the same sentence count.
- Keep two texts: display (captions, correct spelling) and TTS (respelled). Approved: "Design OS Studio" -> "Đi-giai Âu-ét Studio" (keep "Studio" in English), "Figma" -> "Phích-ma", ".fig" -> "phích", "megabyte" -> "mê-ga-bai". Never ALL CAPS "DESIGN OS" (spelled letter by letter).
- Nam rejects wrong English pronunciation: speak Vietnamese for UI words (bảng lớp, vùng vẽ, bảng thuộc tính, phím xuống dòng, phím thoát, màu nền); English UI strings go only in callouts.
- New respelling: try 5-7 variants, check them with faster-whisper (vi and en), send Nam a short sample WAV, and only rebuild after his OK.

**Picture rules:** 1920x1080, 30 fps. Openscreen raw is only 1600 px wide, so keep camera zoom at or below ~1.6x (higher looks soft on YouTube). Fit all text inside its card (auto-shrink) and check recap/stat frames for overflow. End card shows the full URL https://jangtrinh.github.io/design-os-studio/ large for 8-10 s plus "Source-available · Not affiliated with Figma".

**Delivery:** export 1080p plus a 4K upscale (lanczos, crf 16); send the 4K for YouTube, only after ffprobe reads its full duration. Tell Nam to keep the upload private until YouTube shows 2160p. Give one clear title suggestion plus a description with chapter timestamps, the link, the template credit and "Not affiliated with Figma". Never post; Jang approves last.

## Reference files in this bundle
- `references/openscreen.md` + `tools/record.sh`: exact Openscreen command, where takes land, cursor.json format, screen mapping.
- `references/voice.md` + `longform/gen_tts.py` + `longform/check_voice.py`: approved voice, install, respelling table, Whisper check.
- `references/prompt-motion.md`: how to use the Prompt Motion tools, references already used, fallback without the MCP.
- `references/chatgpt-instructions.md`: handoff for ChatGPT/ORCA/Codex, now with the long-form mode.
- `longform/`: starter engine for the long video (`ROOT=<workspace> python build.py info|agenda|<chapter>`, `python audio.py`).
