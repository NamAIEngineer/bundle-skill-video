#!/bin/zsh
# Record the design:os studio window with Openscreen and copy the take next to your workspace.
# Usage: tools/record.sh <out_dir> <take_name> <seconds>
# Example: tools/record.sh ~/orca/workspaces/my-video/rec c3 30
# Start this, THEN do the actions in the app (click, pause ~0.8 s, type). Record longer than the action.
set -e
OUT=$1; NAME=$2; DUR=${3:-30}
OS_APP="${OPENSCREEN:-/Users/nam/orca/workspaces/openscreen-trial-20261114/Openscreen.app/Contents/MacOS/Openscreen}"
REC="$HOME/Library/Application Support/openscreen/recordings"
mkdir -p "$OUT"
"$OS_APP" record --window "design:os studio" --cursor editable-overlay --duration "$DUR" \
  --project "$OUT/$NAME.openscreen" --json > "$OUT/$NAME.log" 2>&1
F=$(ls -t "$REC"/recording-*.mp4 | head -1)
cp "$F" "$OUT/$NAME.mp4"; cp "$F.cursor.json" "$OUT/$NAME.cursor.json"
echo "saved $OUT/$NAME.mp4 (+ .cursor.json) from $F"
