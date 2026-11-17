# Video skill bundle for design:os studio

Bundle skill để lập kế hoạch, quay footage mới và dựng video marketing cho design:os studio. Điểm vào: [SKILL.md](designos-beat-edit-video/SKILL.md).

## Nội dung

- `engine/`: tạo plan đơn/batch, ánh xạ thao tác theo nhịp, nhạc, render và QA.
- `longform/`: starter cho tutorial tiếng Việt 3–5 phút, voiceover và captions.
- `tools/record.sh`: quay cửa sổ Studio bằng Openscreen.
- `references/`: creative brief, recording, voice, Prompt Motion, spec và hướng dẫn agent.
- `spec/`, `sample/`, `legacy/`: ví dụ và nguồn tham khảo; không dùng lại footage mẫu cho video mới.

## Bắt đầu

Cần Python 3, numpy, Pillow, ffmpeg/ffprobe. Quay Studio cần macOS, app Studio và Openscreen đã cài. Longform cần thêm soundfile và VieNeu; kiểm tra giọng cần faster-whisper. Các phụ thuộc giọng có thể tải model.

```sh
cd designos-beat-edit-video
python3 engine/ideate.py plan --edits 5 --seed 17 --out plan.json
# Điền marketing, viết hook/outro; quay mới và đo times.json.
python3 engine/ideate.py build plan.json times.json --out spec.json
python3 engine/run.py validate spec.json
python3 engine/run.py all spec.json --root /path/to/raw --out /path/to/output
```

Đọc [phân tích bundle](ANALYSIS.md) trước khi chạy. Đây là source bundle, chưa phải bản cài một lệnh. Giữ nguyên notices/attribution trong nguồn; bundle chưa có giấy phép phân phối tổng thể, không mặc định coi là open-source.

## Portable setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Optional voice environment:
python3 -m venv .venv-voice
.venv-voice/bin/pip install -r requirements-voice.txt
```

Install ffmpeg/ffprobe through your platform package manager. Recording requires macOS and Openscreen; rendering supports platforms with Python, ffmpeg and fonts installed. For Windows use the equivalent `.venv/Scripts/python` paths.

Recorder discovers `openscreen` on PATH, then standard macOS Applications locations. Override `OPENSCREEN` with the executable path if needed; `PYTHON` selects its Python interpreter. `tools/record.sh OUTPUT TAKE SECONDS` refuses existing take names, reserves a lock, and copies only the media named by both that recording's completion event and project. Failed/incomplete recordings remain in their original location with logs; choose a new take name after investigating.

Longform fonts: set `FONT_DIR` for Inter OTF/TTF; otherwise system Arial/DejaVu is used. Exact typography differs by platform. Keep fresh raw footage and measured timings outside Git.

Non-text scenes may declare `footage_anchors: {"scene": [[video_seconds, raw_seconds], ...]}` in a spec without inventing text/double-click events. Set `cursor.overlay` false to omit the synthetic cursor. This is an explicit spec input; ideate build does not generate these anchors automatically.

Tests: `python3 -m unittest discover -s tests -v`. See [integration evidence](TESTING.md) for actual recording/TTS/render results and scope.
