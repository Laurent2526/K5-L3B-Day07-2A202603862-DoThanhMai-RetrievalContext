# Ghi chú rà soát kết quả dev

## Các file

- `COMPARISON.md`: bảng tổng hợp nhãn dự thảo và đề xuất cấu hình.
- `REVIEWS.md`: 51 dòng nhận xét, 17 câu cho mỗi cấu hình.
- Mỗi thư mục `baseline`, `citation`, `context` có `reviews.draft.json`
  (nhãn), `review-details.json` (câu hỏi, đáp án, context, nguồn của từng
  citation), `metrics.draft.json` (metrics từ nhãn).
- `selected-config.proposed.json`: cấu hình đề xuất và SHA-256 của code/dữ
  liệu ở bước đánh giá ban đầu. Cấu hình chốt sau đó nằm trong
  `../selected-config.json`.
- `context/reviews.confirmed.json` và `context/metrics.confirmed.json`: 17 nhãn
  context mình đã kiểm tra và kết quả tổng hợp lại.

Mình có dùng AI hỗ trợ tạo bản nhãn ban đầu. Phần context đã kiểm tra xong;
baseline và citation vẫn giữ nhãn dự thảo để phân biệt với bản đã xác nhận.

## Thứ tự kiểm tra

1. Mở PDF Day 6 tại
   `C:/Users/84836/K5-L3B-Day06-DoThanhMai-2A202603862-DataIngestion/data/business-ethics_-_WEB.pdf`.
2. Đọc `COMPARISON.md`, sau đó `REVIEWS.md`. Với mỗi câu, đối chiếu
   `review-details.json` với trang PDF trong gold/citation, cả đơn vị và điều kiện.
3. Ưu tiên các nhận xét dễ tranh luận:
   - `citation/dev-008`: trang PDF 169; phần job titles/traditional pay scales.
   - `context/dev-004`: trang PDF 159; đủ evidence trong context nhưng citation
     được chọn không chứa danh sách hành vi quấy rối.
   - `context/dev-008`: trang PDF 169; phần gender/race vượt evidence đang dùng.
   - `context/dev-009`: trang PDF 172; pay/benefits có trong context khác nhưng
     không nằm trong hai đoạn được cite. Đây là vấn đề coverage dù hai citation
     đều có đóng góp hỗ trợ các phần còn lại.
   - Các câu từ chối: kiểm tra output cuối và lý do dừng, không mặc định guard
     từ chối đồng nghĩa model nhận biết đúng thiếu evidence.
4. Tạo bản nhãn đã kiểm tra riêng, ví dụ `reviews.confirmed.json`, dựa trên
   `reviews.draft.json`. Sửa grade/support/reason nếu cần. Chỉ đặt
   `human_confirmed: true` và ghi tên người kiểm tra cho câu thực sự đã đọc.
5. Tổng hợp lại bằng script đã có, ví dụ cho cấu hình context, chạy từ gốc repo:

```powershell
python starter/agent_metrics.py --cases data/questions.json --traces starter/results/agent-openai-dev-context/traces.json --reviews docs/dev-audit/context/reviews.confirmed.json --split dev --output docs/dev-audit/context/metrics.confirmed.json
```

Script này chỉ cộng điểm từ nhãn, không đọc lại PDF. Khi kiểm tra xong baseline
và citation, mình có thể dùng cùng lệnh với đường dẫn của hai cấu hình đó.

## Sau khi kiểm tra

Mình chọn cấu hình theo tiêu chí ở `docs/DEV_EXPERIMENTS.md`: grounded mean
trước, sau đó false abstention, citation support và thời gian/token. Cấu hình
chốt nằm trong `docs/selected-config.json`. Bộ test 7 câu đã được chạy cho cả
baseline và cấu hình được chọn; kết quả nằm ở `docs/test-audit/`.

Các file trong thư mục này chỉ tổng hợp dev. Chi phí token ước tính nằm trong
`cost-estimate.json` của từng cấu hình, còn trace gốc vẫn giữ chi phí null.
