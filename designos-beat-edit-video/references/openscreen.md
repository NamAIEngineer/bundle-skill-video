# Openscreen (screen capture of design:os studio)

- Binary on Nam's Mac: `/Users/nam/orca/workspaces/openscreen-trial-20261114/Openscreen.app/Contents/MacOS/Openscreen`
- Command: `Openscreen record --window "design:os studio" --cursor editable-overlay --duration <s> --project <x>.openscreen --json`
  Wrapper: `tools/record.sh <out_dir> <name> <seconds>` (records, then copies the take + cursor file into out_dir).
- Raw files land in `~/Library/Application Support/openscreen/recordings/recording-<epoch_ms>.mp4` plus `.mp4.cursor.json`. Copy them out right away; the newest file is your take.
- Output: only the app window, ~1600x962, variable frame rate (resample with `-vf fps=30`). Native macOS dialogs (file picker, alerts) are NOT captured: never fake them, describe them with a callout.
- `cursor.json`: `samples[{timeMs, cx, cy (0-1 of the frame), visible, interactionType: move|click|mouseup}]`, `assets[0]` = cursor PNG (base64 data URL) with `hotspotX/Y`. Clicks give anchor times for retiming, camera zoom and callouts; draw the cursor yourself from it (see `longform/lib.py` Cursor).
- Screen-to-raw mapping on Nam's 1456x819 display (app window x 123-1334, y 20-746): raw = ((x-123)*1.321, (y-20)*1.325).
- Raw is only 1600 px wide: zoom <= ~1.6x or it looks soft on YouTube.
- Driving the app: Claude uses computer-use on the Mac (app "designos"); ORCA/Codex or Nam can do it by hand. Click, pause ~0.8 s, then type; select text layers in Layers, Return, check the highlight, then type; Escape to finish. Check the app state after any undo.
