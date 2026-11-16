# Thử nghiệm cải thiện agent trên dev

Bảng chấm từng câu nằm trong [dev-audit](dev-audit/README.md). Mình đã kiểm tra
xong nhãn của cấu hình context. Hai cấu hình còn lại vẫn dùng nhãn dự thảo.
Khi chấm, mình xét cả nội dung câu trả lời và nguồn trích dẫn, thay vì chỉ
đếm số câu `answered`.

## Kết quả đã quan sát

| Cấu hình | Answered | Abstain | Error | Từ chối câu có đáp án | Gold nguyên văn trong context cuối |
|---|---:|---:|---:|---:|---:|
| Baseline | 12/17 | 5/17 | 0/17 | 3/15 | 14/15 |
| Cải thiện 1 | 14/17 | 3/17 | 0/17 | 1/15 | 14/15 |
| Cải thiện 2 | 15/17 | 2/17 | 0/17 | 0/15 | 15/15 |

Đối chiếu trace: cải thiện 1 trả lời được `dev-005`, `dev-010` nhưng vẫn
từ chối `dev-012`. Cải thiện 2 trả lời `dev-012` đúng hai chiều giới hạn là
time/distance, citation `e7696e7f8a89ce8cc67b25cc` có trong context. Hai cấu
hình đều từ chối `dev-016`, `dev-017`. Đây là thống kê status và kiểm tra gold
nguyên văn, không thay thế nhãn grounded answer/citation support.

Một số lỗi còn lại ở cấu hình cải thiện 2: `dev-004` thêm danh sách
hành vi quấy rối nhưng chỉ cite chunk `76521a581244432f6a0e86fc`, vốn không
liệt kê các hành vi đó; cần chấm phạm vi hỗ trợ citation. `dev-008` bổ sung
đối chiếu gender/race ngoài nội dung chunk được cite; không mặc định mọi
khẳng định mở rộng được nguồn hỗ trợ. Không kết luận accuracy 100% chỉ vì
15 câu đã trả lời. Các lỗi này vẫn được giữ trong bản nhãn context đã xác nhận.

Giữ nguyên corpus B, 17 câu dev, model `gpt-4.1-mini`, prompt và TF-IDF.
Không xem hoặc dùng test để chọn cấu hình. Các lần mới gọi model thật;
không sửa kết quả cũ hoặc coi xử lý lại trace là benchmark mới.

| Cấu hình | Citation formatter | Top-k | Context budget (ký tự) | Thư mục |
|---|---|---:|---:|---|
| Baseline | strict | 3 | 800 | `starter/results/agent-openai-dev-run2` |
| Cải thiện 1 | append | 3 | 800 | `starter/results/agent-openai-dev-citation` |
| Cải thiện 2 | append | 5 | 2400 | `starter/results/agent-openai-dev-context` |

## Giả thuyết và lỗi baseline

- `dev-005`, `dev-010`: model trả nội dung đúng, chọn ID có trong context,
  nhưng thiếu marker inline nên bị guard từ chối. Formatter chỉ render ID do
  model đã chọn và có trong context, không thêm nguồn mới hoặc sửa nội dung.
  Trace giữ output gốc và ghi rõ `citation_formatting`; kiểm chứng hỗ trợ ngữ
  nghĩa vẫn phải thực hiện khi chấm. Không coi thao tác render là xác minh citation.
- `dev-012`: agent đổi query, context giữ một đoạn về Jimmy John's không đủ
  trả lời điều kiện thời gian/khoảng cách, sau đó chạm search limit. Thử top-k
  lớn hơn và context rộng hơn để tăng cơ hội giữ evidence. Đây là thay đổi gộp
  top-k/budget, không thể kết luận riêng tác động từng tham số. Không dùng gold
  để tạo query hoặc chọn chunk.

## Cách mình so sánh

1. Mình chạy hai cấu hình bằng `openai_agent.py`, lưu mỗi lần vào thư mục riêng.
2. Bản chấm xem xét câu trả lời, evidence và citation trên cùng 17 câu dev, gồm
   grounded answer 0/1/2, citation support, context 0/1/2 và abstention.
3. Mình so sánh chất lượng câu trả lời, evidence trong context, số lượt gọi,
   token, thời gian và chi phí nếu có giá được xác minh. Số `answered` không
   thay thế độ đúng. Báo cả kết quả không cải thiện.
4. Khi chọn cấu hình, mình ưu tiên grounded answer trung bình, sau đó false abstention thấp hơn,
   citation support cao hơn; khi chất lượng bằng nhau ưu tiên token/thời gian
   thấp hơn. Ghi cấu hình chọn và giới hạn trước khi đánh giá test mới.

Nếu API lỗi, giữ trace lỗi. `--resume` bỏ qua case đã có; `--retry-errors` chỉ
dành cho dev và lưu checkpoint trước khi chạy lại. Không chạy lại câu đã trả
lời để chọn một output đẹp hơn. Những trường hợp thiếu evidence vẫn nằm trong
đánh giá abstention, nhưng không vào mẫu số retrieval metrics.
