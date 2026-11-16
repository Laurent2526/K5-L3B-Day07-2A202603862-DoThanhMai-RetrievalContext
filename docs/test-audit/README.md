# Ghi chú rà soát kết quả test

Mình đã chạy hai cấu hình, mỗi cấu hình 7 câu. Bảng tổng hợp nằm trong
`COMPARISON.md`, nhận xét từng câu ở `REVIEWS.md`. Bản nhãn có AI hỗ trợ và
chưa đối chiếu xong với PDF nên vẫn giữ `human_confirmed: false`.

- Câu 001: PDF 166, giảm 23%.
- Câu 002: PDF 182, testing job applicants phổ biến nhất.
- Câu 003: PDF 193 và các nguồn bổ sung 156/204/210 của selected, thông tin mật.
- Câu 004: PDF 207, phân biệt foreign government official và private officer.
- Câu 005: PDF 211, evidence motive có trong corpus nhưng không vào context cuối;
  cả hai từ chối nhầm, điểm 0. Không sửa cấu hình theo test.
- Câu 006: PDF 198–199, có salary schedules nhưng không có monthly dollar amount.
- Câu 007: PDF 205, không cho ngày đầu trả tiền chính xác. Selected có raw status
  answered nhưng nói rõ thiếu ngày: nhãn semantic abstention phải đọc nội dung.

Giữ nguyên raw trace và bảng semantic review riêng. Không chạy
`agent_metrics.py` trực tiếp với nhãn selected/test-007 abstention_correct=true
trên raw answered: script đó có giả định status không phù hợp trường hợp này.
`build_test_audit.py` giữ raw_status và semantic_status tách biệt trong báo cáo,
không đổi raw trace. Grounding/citation support và semantic abstention phải
được người làm bài kiểm tra trước khi coi các số draft là nhãn đã xác nhận.

Copy `reviews.draft.json` sang bản nhãn đã kiểm tra riêng nếu cần, chỉ đổi
human_confirmed cho từng câu thật sự đã đọc và ghi human_reviewer/ngày.
Không chạy lại test để tìm một câu trả lời đẹp hơn hoặc sửa ID/status cho khớp
đáp án chuẩn. Từ đây mọi thử nghiệm tối ưu cần test mới độc lập.

Chi phí là token-price estimate trong `cost-estimate.json`, không phải hóa đơn.
