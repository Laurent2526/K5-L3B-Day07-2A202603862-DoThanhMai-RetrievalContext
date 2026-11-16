# Results đang sử dụng

| Thư mục | Vai trò |
|---|---|
| `dev-tfidf/` | Benchmark retrieval TF-IDF trên dev, 15 câu có đáp án |
| `dev-dense/` | Benchmark dense pgvector trên cùng dev/corpus B |
| `dev-hybrid/` | Benchmark hybrid RRF trên cùng dev/corpus B |
| `agent-openai-dev-run2/` | Baseline agent OpenAI hoàn tất 17 câu dev; 12 answered, 5 abstain, 0 error |
| `agent-openai-dev-citation/` | Cải thiện citation trên dev; 14 answered, 3 abstain |
| `agent-openai-dev-context/` | Tăng top-k và context; 15 answered, 2 abstain |
| `agent-openai-test-baseline/` | Test baseline, hoàn tất 7 câu; 4 answered, 3 abstain |
| `agent-openai-test-selected/` | Test cấu hình chọn, hoàn tất 7 câu; raw status 5 answered, 2 abstain |
| `_archive/` | ZIP chứa các lần debug/smoke và lần chạy Gemini dở; manifest liệt kê thư mục gốc |

Các lần cũ đã được nén và kiểm tra nội dung trước khi dọn thư mục. Giữ archive
để tra lỗi API, quota và citation; không dùng các smoke run làm benchmark độc lập.
Mình giữ từng lần chạy riêng để so sánh. `answered` là status của chương trình,
chưa phải điểm đúng/sai; ví dụ test-007/selected có status này nhưng nội dung
nói rõ sách không cho ngày chính xác. Phần chấm nội dung nằm trong
`docs/dev-audit/` và `docs/test-audit/`.

Các thư mục kết quả chính trong bảng đã được bỏ ignore để đưa vào repo.
`_archive/` vẫn bị ignore vì chỉ chứa những lần debug cũ.
