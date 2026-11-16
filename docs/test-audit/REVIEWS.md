# Ghi chú chấm các câu test

Mình dùng AI hỗ trợ đề xuất nhãn, phần đối chiếu với PDF chưa hoàn tất.

Mình giữ nguyên status và câu trả lời trong trace. Khi xét từ chối đúng hay
sai, mình xem cả nội dung vì có trường hợp status là `answered` nhưng câu trả
lời nói rõ không đủ thông tin. Cấu hình được giữ nguyên sau lần chạy test.

## baseline

| Câu | Raw status | Nội dung thực tế | Context 0–2 | Điểm 0–2 | Citation support | Lý do |
|---|---|---|---:|---:|---|---|
| test-001 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-002 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-003 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-004 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-005 | abstain | abstain | 0 | 0 | 0/0 | Context cuối không chứa evidence về động cơ whistleblowing. Agent tìm lặp và chạm search_limit; từ chối nhầm câu có đáp án nên điểm 0. |
| test-006 | abstain | abstain | N/A | N/A | 0/0 | Kết quả cuối báo không đủ bằng chứng và không đưa ra mức lương/ngày tháng không có nguồn. Guard dừng do search_limit, không đồng nghĩa model chủ động kết luận thiếu thông tin. |
| test-007 | abstain | abstain | N/A | N/A | 0/0 | Kết quả cuối báo không đủ bằng chứng và không đưa ra mức lương/ngày tháng không có nguồn. Guard dừng do search_limit, không đồng nghĩa model chủ động kết luận thiếu thông tin. |

## selected

| Câu | Raw status | Nội dung thực tế | Context 0–2 | Điểm 0–2 | Citation support | Lý do |
|---|---|---|---:|---:|---|---|
| test-001 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-002 | answered | answered | 2 | 2 | 2/2 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-003 | answered | answered | 2 | 2 | 4/4 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-004 | answered | answered | 2 | 2 | 1/1 | Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu. |
| test-005 | abstain | abstain | 0 | 0 | 0/0 | Context cuối không chứa evidence về động cơ whistleblowing. Agent tìm lặp và chạm search_limit; từ chối nhầm câu có đáp án nên điểm 0. |
| test-006 | abstain | abstain | N/A | N/A | 0/0 | Kết quả cuối báo không đủ bằng chứng và không đưa ra mức lương/ngày tháng không có nguồn. Guard dừng do search_limit, không đồng nghĩa model chủ động kết luận thiếu thông tin. |
| test-007 | answered | abstain | N/A | N/A | 3/3 | Nội dung nói rõ không có ngày lịch chính xác, không tự tạo ngày; mô tả thập niên 1980 và tài khoản Swiss được nguồn hỗ trợ. Raw status answered chỉ do có citation; chấm semantic abstention đúng. Việc khẳng định thiếu ngày còn được đối chiếu với absence_reason của toàn corpus. |

