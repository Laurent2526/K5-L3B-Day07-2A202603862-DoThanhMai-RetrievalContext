# So sánh các lần chạy dev

Mình tổng hợp kết quả của ba cấu hình dưới đây. Cấu hình context đã có bản
nhãn được mình kiểm tra và xác nhận; baseline và citation còn dùng bản dự thảo.

| Cấu hình | Grounded trung bình /2 | Điểm 0/1/2 | Citation hợp lệ | Context đủ | Từ chối nhầm | Từ chối đúng | Median giây | Input/output tokens |
|---|---:|---|---|---|---|---|---:|---|
| baseline | 1.600 | 3/0/12 | 12/12 | 14/15 | 3/15 | 2/2 | 3.065 | 18429/1646 |
| citation | 1.800 | 1/1/13 | 13/14 | 14/15 | 1/15 | 2/2 | 3.009 | 18256/1697 |
| context | 1.933 | 0/1/14 | 17/19 | 15/15 | 0/15 | 2/2 | 2.534 | 23969/1914 |

Số câu `answered` chỉ cho biết agent có trả lời, chưa cho biết đáp án đúng đến
đâu. Chi phí token đã được ước tính riêng trong `cost-estimate.json` của từng
cấu hình; trace gốc vẫn giữ `cost_usd: null`.

Mình chọn cấu hình context (`append`, top-k=5, budget=2400) vì grounded mean
cao hơn và không còn từ chối nhầm trên dev. Đổi lại, cấu hình này dùng nhiều
token hơn và vẫn có chỗ cite chưa đủ cho nội dung trả lời.

Ở cấu hình context, mình giữ điểm và nhận xét về lỗi citation của `dev-004`,
`dev-008`, `dev-009` sau khi kiểm tra. `dev-008` của cấu hình citation vẫn cần
đối chiếu lại. Nhận xét từng câu nằm trong `REVIEWS.md`.

Sau bước dev, cấu hình đã được lưu cùng hash trước khi tạo và chạy bộ test mới.
Kết quả test nằm ở [bảng so sánh test](../test-audit/COMPARISON.md).
