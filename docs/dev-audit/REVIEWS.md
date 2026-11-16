# Ghi chú chấm các câu dev

Mình đã kiểm tra xong phần context; hai phần baseline và citation còn dùng
nhãn dự thảo. Bản xác nhận context có tên người kiểm tra trong
`context/reviews.confirmed.json`.

Điểm grounded answer xét toàn bộ context cuối, còn citation support xét đoạn
được trích dẫn có hỗ trợ câu trả lời hay không. Một citation đúng chưa có nghĩa
là cả đoạn trả lời đã có đủ nguồn; mình ghi riêng các trường hợp còn thiếu.

Nguồn PDF: Business Ethics, OpenStax; số trang trong bảng là trang PDF, không phải số in trên sách.

## baseline: agent-openai-dev-run2

| Câu | Status | Context 0–2 | Grounded 0–2 | Citation support | Lý do |
|---|---|---:|---:|---|---|
| dev-001 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-002 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-003 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-004 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-005 | abstain | 2 | 0 | N/A | Context đủ evidence nhưng câu trả lời cuối bị guard từ chối do thiếu citation inline. |
| dev-006 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-007 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-008 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-009 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-010 | abstain | 2 | 0 | N/A | Context đủ evidence nhưng câu trả lời cuối bị guard từ chối do thiếu citation inline. |
| dev-011 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-012 | abstain | 0 | 0 | N/A | Context cuối thiếu evidence time/distance; tìm lặp rồi chạm search limit. Từ chối câu có đáp án chấm 0. |
| dev-013 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-014 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-015 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-016 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: invalid_or_missing_citations; cần phân biệt guard dừng với model chủ động từ chối. The scenario describes suspicions, not an identified culprit. Reviewed the jewelry-store scenario and surrounding chunks on PDF pages 181-182 and searched the corpus for jewelry, inventory, and stealing; the corpus does not identify two responsible employees. Do not infer names or guilt from suspicion. |
| dev-017 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: search_limit; cần phân biệt guard dừng với model chủ động từ chối. Reviewed the Lockard case and surrounding chunks on PDF pages 198-199, and searched all chunks mentioning Lockard, jury, verdict, and 360,000. The award and appeal outcome are given, but the exact day, month, and year of the jury verdict are not provided. |

## citation: agent-openai-dev-citation

| Câu | Status | Context 0–2 | Grounded 0–2 | Citation support | Lý do |
|---|---|---:|---:|---|---|
| dev-001 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-002 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-003 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-004 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-005 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-006 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-007 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-008 | answered | 2 | 1 | false | Đáp án chính đúng; bổ sung đối chiếu job titles/traditional pay scales không được nêu rõ trong context. Chấm bảo thủ 1/2. |
| dev-009 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-010 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-011 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-012 | abstain | 0 | 0 | N/A | Context cuối thiếu evidence time/distance; tìm lặp rồi chạm search limit. Từ chối câu có đáp án chấm 0. |
| dev-013 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-014 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-015 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-016 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: search_limit; cần phân biệt guard dừng với model chủ động từ chối. The scenario describes suspicions, not an identified culprit. Reviewed the jewelry-store scenario and surrounding chunks on PDF pages 181-182 and searched the corpus for jewelry, inventory, and stealing; the corpus does not identify two responsible employees. Do not infer names or guilt from suspicion. |
| dev-017 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: invalid_or_missing_citations; cần phân biệt guard dừng với model chủ động từ chối. Reviewed the Lockard case and surrounding chunks on PDF pages 198-199, and searched all chunks mentioning Lockard, jury, verdict, and 360,000. The award and appeal outcome are given, but the exact day, month, and year of the jury verdict are not provided. |

## context: agent-openai-dev-context

| Câu | Status | Context 0–2 | Grounded 0–2 | Citation support | Lý do |
|---|---|---:|---:|---|---|
| dev-001 | answered | 2 | 2 | true, true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-002 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-003 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-004 | answered | 2 | 2 | false | Grounded answer 2/2 vì đoạn liệt kê hành vi có trong context (dc145...). Tuy nhiên chỉ cite 76521..., vốn không liệt kê các hành vi; citation có hỗ trợ phần chính nhưng chưa hỗ trợ toàn bộ phạm vi đoạn trả lời. |
| dev-005 | answered | 2 | 2 | true, true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-006 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-007 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-008 | answered | 2 | 1 | false | Đáp án chính đúng; bổ sung gender/race không có evidence trong context. Chấm 1/2, citation không hỗ trợ đầy đủ phần mở rộng. |
| dev-009 | answered | 2 | 2 | true, true | Grounded answer 2/2: phần increased pay/benefits nằm trong context da7e1.... Hai citation đã chọn hỗ trợ vai trò union và dispute/lobby/industry norms, nhưng phần pay/benefits chưa gắn đúng citation. Giữ nhãn true cho đóng góp của từng citation và ghi riêng lỗ hổng coverage. |
| dev-010 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-011 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-012 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-013 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-014 | answered | 2 | 2 | true, true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-015 | answered | 2 | 2 | true | Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context. |
| dev-016 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: invalid_or_missing_citations; cần phân biệt guard dừng với model chủ động từ chối. The scenario describes suspicions, not an identified culprit. Reviewed the jewelry-store scenario and surrounding chunks on PDF pages 181-182 and searched the corpus for jewelry, inventory, and stealing; the corpus does not identify two responsible employees. Do not infer names or guilt from suspicion. |
| dev-017 | abstain | N/A | N/A | N/A | Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. Lý do dừng: invalid_or_missing_citations; cần phân biệt guard dừng với model chủ động từ chối. Reviewed the Lockard case and surrounding chunks on PDF pages 198-199, and searched all chunks mentioning Lockard, jury, verdict, and 360,000. The award and appeal outcome are given, but the exact day, month, and year of the jury verdict are not provided. |

