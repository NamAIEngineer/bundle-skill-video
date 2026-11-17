# Phân tích bundle — 2026-11-17

## Nguồn và phạm vi

Nhập từ `/Users/nam/Downloads/designos-beat-edit-video.zip`, bản có longform và tools bổ sung (timestamp archive 2026-11-16 19:32). File `_1.zip` được nhắc trước đó hiện không còn. Không nhập dữ liệu Studio, phiên agent, bản backup, credential hay footage quay thử từ workspace.

## Kiến trúc

SKILL.md là hướng dẫn agent. Engine ngắn dùng plan → times đo từ footage mới → spec → validate/render/audio/mux/QA. Longform là starter độc lập, có kịch bản, chương, thời gian và footage IDs cố định để người dùng thích nghi cho từng video; không phải engine tự tổng quát hóa.

## Các giới hạn cần xử lý khi dùng

- `tools/record.sh` mặc định dùng đường dẫn Openscreen của máy tác giả; đặt biến OPENSCREEN cho máy khác. Script chọn recording mới nhất toàn cục thay vì đọc đường dẫn từ project: có thể lấy nhầm take nếu quay đồng thời. Chỉ dùng một phiên quay khi chưa sửa cơ chế chọn file.
- `longform/lib.py` dùng font Inter ở đường dẫn Linux `/usr/share/fonts/opentype/inter/`; cần cung cấp font hoặc chỉnh đường dẫn trên macOS.
- `longform/build.py` gắn chapter/clip/timestamp của demo cũ; cần footage mới và ánh xạ mới. Một số zoom 2.3x vượt khuyến nghị <=1.6x trong SKILL.md.
- Engine ngắn thiết kế quanh thao tác sửa chữ và double-click; cảnh agent tạo cả dashboard không tự khớp các anchor này.
- Plan sinh seed 17 dài 42.162 giây; giới hạn thời lượng của brief cần kiểm tra và điều chỉnh riêng.
- Validator dùng dung sai nhịp rất nhỏ trong khi plan làm tròn T; cần xác minh spec thực tế. Validation không chứng minh tính năng sản phẩm hoặc chất lượng hình ảnh.
- Tài liệu nêu kết quả verified/approved lịch sử. Chưa tái hiện những kết quả đó trong lần nhập repo này.
- Không có license tổng thể trong archive. Không tự gán quyền sở hữu hoặc giấy phép cho code/media mẫu.

## Kiểm tra đã chạy

- 18 file Python parse thành công bằng AST, không chạy các module có side effect.
- CLI plan chạy thành công với 5 edits, seed 17; JSON đọc được và đủ 5 edits.
- Chưa kiểm tra ghi hình, TTS, render end-to-end hoặc các tuyên bố PSNR/audio giống mẫu.

Giữ nguyên source bundle; README và tài liệu này bổ sung hướng dẫn, không sửa engine.
