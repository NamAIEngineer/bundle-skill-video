import json
D = [
("c0_hook", "Một tệp thiết kế. Một bảng lớp. Và chưa tới năm phút. Hôm nay mình sẽ đi từ một mẫu giao diện có sẵn đến bản hoàn chỉnh, ngay trong Design OS Studio. Mọi thao tác đều quay thật trên ứng dụng, không dựng giả. Nếu bạn từng mất cả buổi chỉ để sửa vài dòng chữ trên một màn hình, video này dành cho bạn."),
("c1_intro", "Design OS Studio là một ứng dụng thiết kế chạy ngay trên máy của bạn. Nó miễn phí, và mã nguồn được công bố để ai cũng xem được, dù không phải mã nguồn mở. Điểm mình thích nhất là nó đọc được tệp đuôi .fig, nên bạn không phải làm lại từ đầu. Mình sẽ dùng một mẫu giao diện miễn phí, giấy phép cho dùng thoải mái. Một lưu ý cho rõ ràng, Design OS Studio không liên kết với Figma."),
("c2_import", "Bước một, nhập mẫu. Mình mở ứng dụng, chọn nhập tệp, rồi chọn tệp đuôi .fig vừa tải về. Tệp này nặng khoảng năm mươi hai megabyte, mà ứng dụng đọc xong khá nhanh. Mình mở tệp ra, và các trang hiện ra. Bên trái là danh sách trang, mỗi trang là một nhóm màn hình. Ở giữa là vùng vẽ, và bên phải là bảng thuộc tính. Mình chọn trang chứa các màn hình ứng dụng, và mọi thứ đã nằm sẵn trên vùng vẽ, sẵn sàng để sửa."),
("c3_layers", "Bước hai, đọc cấu trúc bằng bảng lớp. Đây là chỗ mình biết mọi thứ đang nằm trong lớp nào. Một khung chứa nhiều khung con. Khung con chứa tiêu đề, đoạn mô tả và nút bấm. Mình mở từng cấp ra, và mỗi lần bấm vào một dòng, vùng vẽ lại đánh dấu đúng phần tử đó. Cách này chắc chắn hơn nhiều so với việc cố bấm trúng một dòng chữ nhỏ ngay trên màn hình, nhất là khi các lớp chồng lên nhau."),
("c4_text", "Bước ba, sửa nội dung. Mình chọn lớp chữ trong bảng lớp, nhấn phím xuống dòng để vào chế độ sửa, chọn tất cả, rồi gõ chữ mới. Xong thì nhấn phím thoát. Tiêu đề báo lỗi được thay bằng một câu ngắn. Dòng mô tả cũng được viết lại. Và chữ trên nút bấm thành lời mời dùng thử. Ba lần sửa, bố cục không hề xê dịch, vì chữ mới vẫn nằm trong cùng một khung."),
("c5_mobile", "Bước bốn, màn hình điện thoại. Mẫu này có sẵn một khung cho điện thoại, mình chọn nó trong bảng lớp rồi làm lại đúng ba thao tác. Tiêu đề, mô tả, rồi nút bấm, mỗi chỗ một câu mới. Khi đặt hai màn hình cạnh nhau, bạn thấy cùng một câu chuyện, cùng một bố cục, chỉ khác kích thước. Đây chính là lợi ích của việc làm việc trên một tệp duy nhất, thay vì hai bản riêng."),
("c6_style", "Bước năm, chỉnh kiểu dáng. Mình chọn nút bấm trong bảng lớp, cuộn bảng thuộc tính bên phải xuống mục màu nền, rồi bấm vào mã màu. Khi chữ đã được bôi chọn, mình gõ mã màu mới. Nút đổi sang màu cam ngay lập tức trên vùng vẽ. Mỗi thay đổi đều hiện ngay, nên bạn không phải đoán kết quả."),
("c7_preview", "Bước sáu, xem trước như người dùng thật. Mình chọn khung máy tính, rồi bấm nút xem trước ở góc trên bên phải. Màn hình mở ra trông như một trang thật, không còn thước kẻ hay bảng thuộc tính. Đóng lại, chọn khung điện thoại, và bấm xem trước lần nữa. Nút màu cam, chữ mới, mọi thứ đúng như lúc sửa. Trước khi gửi cho ai, mình luôn xem qua một lần như thế này."),
("c8_recap", "Hãy nhìn lại những gì vừa làm. Từ một màn hình báo lỗi, giờ nó là một trang có tiêu đề rõ ràng, dòng mô tả gọn, và nút kêu gọi hành động. Cả bản máy tính lẫn bản điện thoại đều đã sửa xong. Sáu lần sửa chữ, một lần đổi màu, không thay đổi bố cục. Tất cả diễn ra trong một ứng dụng duy nhất, trên một tệp duy nhất."),
("c9_outro", "Tóm lại, ba thói quen. Một, chọn lớp trong danh sách lớp thay vì bấm trên vùng vẽ. Hai, vào chế độ sửa rồi mới gõ. Ba, kiểm tra từng bước trước khi đi tiếp. Từ một tệp có sẵn, qua sáu bước, bạn có hai màn hình hoàn chỉnh. Design OS Studio miễn phí, đường dẫn tải đang ở trên màn hình. Cảm ơn bạn đã xem, và hẹn gặp lại."),
]
REP = [("Design OS Studio", "Đi-giai Âu-ét Studio"), (".fig", "phích"), ("Figma", "Phích-ma"), ("megabyte", "mê-ga-bai")]
def tts(s):
    for a, b in REP: s = s.replace(a, b)
    return s
json.dump(D, open("script.json", "w"), ensure_ascii=False, indent=1)
json.dump([[k, tts(t)] for k, t in D], open("script_tts.json", "w"), ensure_ascii=False, indent=1)
import re
for k, t in D:
    a = re.split(r"(?<=[.!?])\s+", t); b = re.split(r"(?<=[.!?])\s+", tts(t)); assert len(a) == len(b), k
print("ok")
