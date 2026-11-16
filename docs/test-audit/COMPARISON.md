# So sánh kết quả test

Mình chạy baseline và cấu hình đã chọn trên cùng 7 câu test, giữ nguyên code
và tham số đã chốt từ dev. Các nhãn có AI hỗ trợ, còn cần đối chiếu lại với PDF.

| Cấu hình | Grounded /2 | Context đủ | Citation support | Từ chối đúng theo nội dung | Theo raw status | Từ chối nhầm | Median giây |
|---|---:|---|---|---|---|---|---:|
| baseline | 1.600 | 4/5 | 4/4 | 2/2 | 2/2 | 1/5 | 5.321 |
| selected | 1.600 | 4/5 | 11/11 | 2/2 | 1/2 | 1/5 | 3.791 |

Hai cấu hình có cùng grounded mean trên 5 câu có đáp án và đều bỏ lỡ
`test-005`. Số `answered` của selected tăng từ 4 lên 5, nhưng câu thêm vào
là `test-007`: agent nói không có ngày chính xác và kèm citation. Vì vậy,
đây không phải một câu có đáp án được giải quyết thêm.

Context lớn giúp agent lấy thêm thông tin và cite nhiều đoạn hơn, nhưng lần
thử này chưa làm điểm test tăng. Mình giữ cấu hình đã chọn từ dev và ghi nhận
kết quả này trong báo cáo. Nếu thử cách chọn context hoặc phân loại câu từ
chối khác, mình sẽ đánh giá bằng bộ test mới.
