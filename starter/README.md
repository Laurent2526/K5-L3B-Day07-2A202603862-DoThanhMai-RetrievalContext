# Code triển khai Day 7

Mình mở rộng khung có sẵn để thử ba cách retrieval và xây agent. Bài hiện dùng
OpenAI `gpt-4.1-mini`; Gemini được giữ lại từ các lần thử trước. Các lệnh chạy
đầy đủ nằm trong [RUNBOOK](../docs/RUNBOOK.md).

## Agent Gemini

Cài `python -m pip install --upgrade google-genai`, đặt `GEMINI_API_KEY`
trong môi trường và chọn model bằng `--model` hoặc `GEMINI_MODEL`.
Không ghi key vào source hay commit `.env`.

```powershell
python starter/gemini_agent.py --chunks data/day6_chunks_B.json --questions data/questions.json --split dev --query-id dev-001 --model gemini-flash-latest --output starter/results/agent-gemini-smoke
```

Adapter dùng Gemini Interactions API `v1beta`, function calling thủ công, TF-IDF
local và cùng prompt/context budget với agent OpenAI. Bỏ `--query-id` để chạy
cả split, gồm câu thiếu evidence. Mỗi output directory phải mới. Không gửi gold
hoặc đáp án chuẩn tới model. Trace ghi model version thực tế, token usage,
tool calls và context; chi phí chưa tính là `null`, không mặc định bằng 0.
Alias `gemini-flash-latest` có thể thay đổi model; dùng model version cụ thể
còn được tài khoản hỗ trợ khi chốt cấu hình. Cần tự chấm grounding, citation
và abstention; unit test hiện có không thay thế lần gọi Gemini thật.

## Dense và Hybrid trên dữ liệu Day 6

`dense.py` và `hybrid.py` dùng `DATABASE_URL` từ biến môi trường, chỉ đọc
snapshot B của `BAAI/bge-small-en-v1.5` trong bảng `ingestion_chunks`.
Cài `psycopg[binary]` và `fastembed==0.9.1`, bật database Day 6 trước khi chạy.
Các script kiểm tra corpus database khớp `--chunks`, loại câu `answerable: false`
khỏi retrieval metrics và từ chối ghi đè kết quả đã tồn tại.

```powershell
python starter/hybrid.py --chunks data/day6_chunks_B.json --questions data/questions.json --split dev --output starter/results/dev-hybrid --candidate-k 10 --rrf-constant 60
```

Có thể thêm `--cache-dir <cache-FastEmbed-Day6>` để dùng lại model đã tải.
Hybrid lấy 10 candidates mỗi retriever, cộng `1 / (60 + rank)` theo chunk ID,
phá hòa theo ID và lấy top-3; giữ context budget 800 ký tự như baseline.
Trace lưu cả candidates, rank/score thành phần và điểm RRF. Summary ghi
thời gian setup riêng; thời gian query gồm embedding, SQL, TF-IDF, fusion và
chọn context. Không dùng gold để truy vấn hay hợp nhất ranking.

| File | Công dụng |
|---|---|
| `agentic.py` | Khung agent ví dụ với số lượt search, top-k và context budget có thể cấu hình |
| `baseline.py` | TF-IDF lexical baseline, chạy offline |
| `convert_day6.py` | Chuyển một số trường JSON từ Day 6 |
| `agent_metrics.py` | Tổng hợp nhãn đánh giá do bạn tự chấm |
| `dense.py` | Truy vấn exact cosine trên pgvector, chỉ đọc snapshot B |
| `hybrid.py` | Kết hợp dense và TF-IDF bằng RRF |
| `openai_agent.py` | Agent OpenAI, xử lý citation và lưu trace |
| `gemini_agent.py` | Adapter Gemini dùng lại vòng lặp agent |

Mình đã nối model và vector store thật, chạy TF-IDF, dense và hybrid trên dev,
sau đó đánh giá agent trên dev và test. Các unit test dùng mock để kiểm tra
logic; kết quả benchmark được lấy từ những lần chạy riêng có lưu trace.

## 1. Kết nối agent

`agentic.py` chứa vòng lặp chung với hai interface:

- `Controller.decide`: trả yêu cầu `search` hoặc câu trả lời `answer` cùng citations.
- `Retriever.search`: nhận query và trả các chunk theo [định dạng dữ liệu](../data/README.md).

Mình nối hai phần này trong `openai_agent.py`. Agent đang dùng TF-IDF; dense và
hybrid có script benchmark riêng. Các tham số `max_searches`, `top_k` và
`budget` được truyền qua CLI. Bộ kiểm tra chỉ xác nhận ID citation nằm trong
context; nội dung có thực sự được nguồn hỗ trợ hay không được chấm riêng.

## 2. Chạy TF-IDF baseline

Chạy từ thư mục gốc với Python 3.11 trở lên:

```bash
python3 -m unittest discover -s tests -v
python3 starter/baseline.py --chunks data/example_chunks.json --questions data/example_questions.json --split dev --output starter/results/example-dev
```

Kết quả có `summary.json` và `traces.json`. Dữ liệu mẫu chỉ có một câu, không đủ để nộp bài. TF-IDF là lexical retrieval, không dùng filter và không thay dense retrieval.

## 3. Dùng dữ liệu Day 6

Xuất chunk và câu hỏi thành hai JSON array. Starter Day 6 không quy định tên bảng hay cách xuất; bạn cần tự thực hiện. Nếu chunk có `chunk_id`, `document_id`, `source`, `page`, `text`, `metadata` và câu hỏi có `gold_source_id`, `gold_page`, `evidence_quote`, chạy:

```bash
python3 starter/convert_day6.py --chunks <day6_chunks.json> --questions <day6_questions.json> --output starter/data/converted
python3 starter/baseline.py --chunks starter/data/converted/chunks.json --questions starter/data/converted/questions.json --split dev --output starter/results/dev-tfidf
```

Thay phần trong `< >` bằng đường dẫn thật. Script chỉ đổi tên trường, không tự truy cập database hay đoán evidence. Nếu cấu trúc khác, tự viết adapter. Đối chiếu lại nguồn, trang và evidence.

`--split dev` chỉ chấm dev. Sau khi chốt cấu hình, dùng `--split test` và chọn thư mục kết quả khác. Nếu test Day 6 từng dùng để chỉnh hệ thống, tạo test mới theo [GUIDE.md](../GUIDE.md). Baseline mẫu dùng evidence nằm trong một chunk và context từ top-3; cần mở rộng hoặc tự đánh giá nếu dùng multi-hop, context từ nhiều lượt hay schema khác. Khớp nguyên văn bằng code không thay thế đánh giá thủ công.

## 4. Tổng hợp đánh giá agent

Sau khi chạy agent thật và tự chấm, chuẩn bị ba JSON array:

- `cases.json`: mỗi câu có `id`, `split`, `answerable` (`true` nếu có đủ evidence).
- `traces.json`: mỗi kết quả có `query_id`, `status` (`answered`, `abstain`, `error`), `events`, `citations`. Thêm `query_id` vào kết quả `run_agent`; lỗi kết nối ghi riêng với `status: "error"`. Script đếm tool use qua event `search`: nếu dùng nhiều tool, chuẩn hóa mỗi lượt retrieval về event này và ghi tên tool trong trường khác, hoặc tự viết metric tương đương.
- `reviews.json`: mỗi nhãn có `query_id`, `citation_support` là danh sách đúng/sai ứng với từng citation. Câu có đáp án cần `answer_grade` 0–2 theo [BENCHMARK.md](../BENCHMARK.md); nếu bị từ chối, chấm 0. Câu thiếu evidence cần `abstention_correct` (`true`/`false`) do người chấm xác nhận. Lần chạy lỗi không cần nhãn.

```bash
python3 starter/agent_metrics.py --cases <cases.json> --traces <traces.json> --reviews <reviews.json> --split test --output starter/results/agent-test/summary.json
```

Thay đường dẫn trong `< >`. Script tổng hợp nhãn bạn đã chấm, không tự đánh giá nội dung. Mẫu số bằng 0 nghĩa là không áp dụng. Lỗi kết nối được báo riêng, không tính vào chất lượng; giữ trace và nhãn để đối chiếu.

## Lưu ý

TF-IDF dùng cách tách từ đơn giản. `baseline.py` mặc định gói context tối đa
800 ký tự, gồm cả nguồn; chunk không vừa sẽ bị bỏ. Script baseline có thể ghi
đè file cùng tên, còn dense, hybrid và agent yêu cầu thư mục output mới.
Các thư mục kết quả chính đã được cho phép theo dõi bằng Git trong `.gitignore`.
Debug cũ nằm trong `_archive/` và không đưa vào bài nộp.

Khung agent ưu tiên giữ chunk từ lần search trước. Khi chunk đầu chiếm gần hết budget, lần search sau có thể không thêm được evidence; hãy kiểm tra trace và thử cách chọn context phù hợp trên dev. Citation ID hợp lệ hoặc verifier trả “đúng” không đảm bảo câu trả lời được hỗ trợ; cần chấm thủ công.
