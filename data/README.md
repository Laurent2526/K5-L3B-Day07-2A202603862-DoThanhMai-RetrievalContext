# Định dạng dữ liệu

## Dữ liệu mình dùng trong bài

- `day6_chunks_B.json`: 449 chunks từ cấu hình B của Day 6.
- `questions.json`: 17 câu dev, gồm 15 câu có đáp án và 2 câu thiếu bằng chứng.
- `questions_test.json`: 7 câu test mới, gồm 5 câu có đáp án và 2 câu thiếu bằng chứng.
- `source_manifest.json`: nguồn sách, giấy phép, trang được chọn và thông tin embedding.
- `test_manifest.json`: hash bộ test và cấu hình đã chốt trước khi tạo test.

Các file `example_*.json` và `agent_cases_example.json` là mẫu của đề, không
phải dữ liệu được dùng trong các bảng kết quả của mình.

## Schema

Các file `example_*.json` chỉ minh họa định dạng, không đủ để nộp bài. Dữ liệu thật là JSON array UTF-8; nếu dùng định dạng khác, ghi cách chuyển trong README.

- **Chunk:** `id`, `text`, `source_id`, `source`, `page`, `metadata`. ID phải duy nhất; giữ phiên bản hoặc ngày nếu có.
- **Câu có đáp án:** `id`, `split` (`dev` hoặc `test`), `question`, `expected_answer`, `gold`: danh sách `{source_id, page, evidence}`. Với schema mẫu, mỗi evidence phải nằm trọn trong một chunk đúng nguồn và trang; các phần tử `gold` là evidence thay thế. Với câu multi-hop cần nhiều đoạn, bạn có thể mở rộng schema, ghi rõ nhóm evidence bắt buộc và cách chấm. Có thể thêm `filter` do người dùng cung cấp trước.
- **Câu thiếu evidence:** `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`. Xem `agent_cases_example.json`.

Không đưa `gold` hoặc nhãn đáp án vào model và retrieval tool. Ghi nguồn dữ liệu và quyền sử dụng. Cách chuyển một số định dạng Day 6: [starter/README.md](../starter/README.md).
