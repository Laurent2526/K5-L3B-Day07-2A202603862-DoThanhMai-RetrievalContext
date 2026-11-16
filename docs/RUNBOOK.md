# Cài đặt và tái lập

Chạy lệnh từ gốc repo. Yêu cầu Python 3.11+, Docker Desktop nếu dùng dense/hybrid,
và OpenAI API key có quyền model `gpt-4.1-mini`. Kết quả API không hoàn toàn xác định.

## Cài Python và cấu hình

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Chỉ copy `.env.example` khi chưa có `.env`; không ghi đè key hiện có.
Mở `.env`, dán key đầy đủ sau `OPENAI_API_KEY=`, lưu file. Không commit hoặc gửi
file này. `.env.example` không chứa secret thật. Để chạy lại thử nghiệm Gemini
phụ, cài `requirements-gemini.txt`; Gemini không phải model được chọn cuối.

Nếu terminal có biến key/model sai, xóa biến đó bằng `Remove-Item Env:OPENAI_API_KEY`
hoặc `Remove-Item Env:OPENAI_MODEL` để agent đọc `.env`. Chỉ dùng
`$env:OPENAI_FORCE_IPV4 = "1"` nếu gặp lỗi kết nối tương tự lần thử trên máy mình.

```powershell
python -m unittest discover -s tests -v
```

## Dữ liệu

`data/day6_chunks_B.json`: 449 chunks trên 53 trang PDF được chọn từ Business
Ethics (OpenStax). Xem `data/source_manifest.json`: URL PDF, SHA-256, khoảng
trang, giấy phép CC BY-NC-SA 4.0 và ghi công. Trường source trong chunk là tên
tài liệu gốc; tải PDF theo manifest nếu cần mở nguồn để chấm. Không cần PDF để
chạy lexical agent, vì text/ID/nguồn/trang đã có trong JSON.

`data/questions.json`: dev 15 câu có đáp án + 2 thiếu bằng chứng.
`data/questions_test.json`: test mới 5 câu có đáp án + 2 thiếu bằng chứng.
Gold chỉ dùng chấm, không đưa vào model hoặc retrieval. Không dùng test để chỉnh.

## TF-IDF và agent

Ví dụ tái lập retrieval dev (dùng output mới, không ghi đè benchmark gốc):

```powershell
python starter/baseline.py --chunks data/day6_chunks_B.json --questions data/questions.json --split dev --output starter/results/reproduction-tfidf
```

Cấu hình đã chốt nằm ở `docs/selected-config.json`. Chạy test bằng wrapper kiểm
tra hash code, corpus, dev, test và cấu hình; output test không được ghi đè:

```powershell
python scripts/run_frozen_test.py --configuration baseline --dry-run
python scripts/run_frozen_test.py --configuration selected --dry-run
python scripts/run_frozen_test.py --configuration baseline
python scripts/run_frozen_test.py --configuration selected
```

Lần gọi API thật có thể phát sinh phí. Không dùng diagnostic/smoke làm benchmark.
Nếu test bị lỗi, giữ trace và báo lỗi; không chạy lại để chọn câu trả lời đẹp hơn.
`--resume` chỉ tiếp tục các câu chưa có, giữ kết quả lỗi đã ghi. Không sử dụng
`--retry-errors` trên test. Nếu cần tiếp tục sau ngắt kết nối, dùng lệnh wrapper
in ra và thêm `--resume`, giữ nguyên mọi cấu hình.

## Dense/hybrid: dùng lại database Day 6

Mở Docker Day 6. Biến sau cần đặt trong terminal; `dense.py` không tự đọc `.env`:

```powershell
$env:DATABASE_URL = "postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab"
python starter/dense.py --chunks data/day6_chunks_B.json --questions data/questions.json --split dev --output starter/results/reproduction-dense
python starter/hybrid.py --chunks data/day6_chunks_B.json --questions data/questions.json --split dev --candidate-k 10 --rrf-constant 60 --output starter/results/reproduction-hybrid
```

Cả hai script chỉ đọc snapshot B, kiểm tra khớp corpus và dùng FastEmbed
`query_embed`. Có thể chỉ định `--cache-dir` để dùng lại cache Day 6. Model tạo
document bằng `passage_embed`, 384 chiều; tìm exact cosine, không ANN.

## Tái tạo database nếu không có Day 6

Không ghi lại database Day 6. Dùng database riêng, cổng khác:

```powershell
docker compose -p day7_reproduction -f infra/compose.yaml up -d --wait
$env:DATABASE_URL = "postgresql://day7:day7_local_only@127.0.0.1:55434/day7_reproduction"
python scripts/rebuild_index.py
```

Script chỉ nhận tên DB `day7_reproduction`, từ chối bảng đã có dữ liệu, không
DELETE/TRUNCATE hoặc thay snapshot. Sau khi tạo index mới, chạy lệnh dense/hybrid
ở trên với DATABASE_URL cổng 55434. Script tái tạo đã được kiểm tra cú pháp;
mình chưa chạy lại toàn bộ bước này trên database mới. Nếu FastEmbed tải
model lần đầu cần mạng; `.cache/` không đưa lên Git.

## Chấm và nộp

Xem `docs/dev-audit/README.md`. Mình lưu riêng bản nhãn ban đầu và bản đã đối
chiếu PDF, có tên người kiểm tra. Nhãn context/dev đã có bản xác nhận.
Tạo nhãn test theo `starter/agent_metrics.py`, gồm điểm câu có đáp án 0/1/2,
support boolean cho từng citation, lý do và abstention_correct cho câu thiếu
evidence. Chấm thêm context 0/1/2; giữ trace, token và thời gian. Chi phí chưa
quy đổi được ghi null, không phải 0.

Kết quả chính đã được bỏ ignore; kiểm tra `git status` rồi add/commit/push các
file được phép chia sẻ. `_archive` vẫn bị ignore vì chỉ chứa debug cũ.
Không add `.env`, `.venv`, cache, secret. Báo cáo ở
`report/individual/2A202603862_DoThanhMai.md` phải cập nhật test và trạng thái
nhãn trước khi coi là hoàn tất. Phần nâng cao chưa thực hiện.
