# Báo cáo Day 7 — Agentic RAG

- Họ tên: Đỗ Thanh Mai.
- MSSV: 2A202603862. Lớp: K5-L3B.
- Tiến độ: mình đã chạy xong dev và test, đã kiểm tra 17 nhãn dev của cấu hình
  context. Nhãn baseline, cấu hình citation và test còn ở bản dự thảo.

## 1. Dữ liệu và benchmark

Mình dùng sách *Business Ethics* của Stephen M. Byars và Kurt Stanberry, OpenStax/Rice
University. Access for free at openstax.org. Giấy phép CC BY-NC-SA 4.0; giữ
ghi công và kiểm tra ngoại lệ ảnh/bên thứ ba khi chia sẻ. Manifest và URL PDF:
[`data/source_manifest.json`](../../data/source_manifest.json).

Sách gốc có 355 trang. Trong bài này, mình dùng **53 trang** thuộc chương 6
và chương 7, gồm các trang PDF 156–182 và 190–215. Mình chỉ làm phần cơ bản,
chưa xử lý toàn bộ sách hoặc nội dung đa phương thức của phần nâng cao.

Mình dùng lại cấu hình B của Day 6 với **449 chunks**, chia theo block, tối đa 500 ký tự,
không overlap và không ghép qua trang. ID, text, nguồn, trang, chapter và số
trang in được giữ lại. `page` là vị trí PDF 1-based, khác số in trên sách.

Embedding local FastEmbed 0.9.1, `BAAI/bge-small-en-v1.5`, 384 chiều.
Document dùng `passage_embed`, query dùng `query_embed`; không thêm prefix thủ
công. PostgreSQL 16.16 + pgvector 0.8.7, exact cosine (`<=>`), score=1-distance,
không ANN index. Bảng `ingestion_chunks`, lọc model_name và strategy B.

Ban đầu mình thử Gemini nhưng gặp giới hạn quota, sau đó chuyển sang OpenAI
`gpt-4.1-mini`. Mình giữ riêng kết quả OpenAI để so sánh cùng một model.
Phiên bản model thực tế được API trả về có lưu trong từng trace.

| Split | Có đáp án | Thiếu evidence | Tình trạng |
|---|---:|---:|---|
| Dev (`data/questions.json`) | 15 | 2 | Đã chạy 3 phương pháp và 3 cấu hình agent |
| Test (`data/questions_test.json`) | 5 | 2 | Đã chạy baseline và selected, 7/7 mỗi cấu hình, không lỗi API |

Câu có đáp án có gold source/page/evidence. Câu thiếu evidence được kiểm tra
trong toàn bộ corpus và ghi absence_reason, không suy ra thiếu thông tin chỉ
từ việc top-k không tìm thấy. Test mới không dùng lại câu hỏi Day 6 hoặc diễn
đạt lại cùng đáp án của dev Day 7. Test được chuẩn bị sau cấu hình chốt;
manifest ghi hash và thời điểm. Không gửi gold/expected_answer vào model.

## 2. Retrieval trên dev

Mình chạy cả ba phương pháp trên cùng corpus B và 15 câu có đáp án. Hai câu thiếu
evidence không vào mẫu số retrieval metrics. Dùng top-3 và context 800 ký tự,
bao gồm ID/nguồn/trang; context deduplicate và bỏ chunk không vừa budget.

| Phương pháp | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median/query | Chi phí API |
|---|---|---|---|---:|---:|
| TF-IDF | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | khoảng 1,03 ms | 0 USD |
| Dense pgvector | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 17,34 ms | 0 USD |
| Hybrid RRF | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 24,63 ms | 0 USD |

Hybrid lấy 10 candidates mỗi retriever, hợp nhất theo ID với tổng
`1/(60+rank)`, trọng số bằng nhau; không cộng trực tiếp hai loại score.
Trace hybrid giữ ranking/score thành phần và score RRF. Phá hòa theo chunk ID.

Thời gian dense gồm query embedding, SQL và context packing; hybrid thêm lexical
retrieval/fusion. Thời gian nạp model được đo riêng. Mình không so sánh trực
tiếp thời gian khởi động vì cache giữa các lần chạy có thể khác nhau. Chi phí
API bằng 0 chưa bao gồm điện và phần cứng. Cả ba phương pháp đều đạt 15/15 trên
dev, nhưng bộ câu hỏi còn nhỏ nên mình chưa kết luận được cách nào tốt hơn
trên dữ liệu khác.

Kết quả ở `starter/results/dev-{tfidf,dense,hybrid}/`. Retrieval query gốc ở các
run này khác query do agent viết lại; không đánh đồng metrics hai pipeline.

## 3. Agent, context và điều kiện dừng

Model gọi function `search`, chương trình tìm TF-IDF, gói context có nguồn rồi
gửi lại cho model quyết định tìm tiếp hoặc `finish`. Giới hạn 3 lượt retrieval;
model có thể được gọi tối đa 4 lần để kết thúc. Context tích lũy deduplicate,
ưu tiên chunk tìm thấy trước. Chạm search limit hoặc thiếu citation hợp lệ dẫn
đến abstain. Trace ghi nguyên output API, queries, tool results, context cuối,
answer, citations, thời gian và token usage. Lỗi API được giữ riêng, không dùng
mock fallback. Tài liệu/tool output được coi là dữ liệu, không phải chỉ dẫn.

Formatter `append` chỉ render `[chunk-id]` mà model đã chọn và có trong context;
không thêm nguồn mới, không đổi nội dung đáp án hoặc tự chứng minh grounding.
Trace ghi original_answer/formatted_answer/appended_ids. Cần đọc nguồn để chấm.

## 4. Hai cấu hình cải thiện và đánh giá dev

| Cấu hình | Citation | Top-k | Budget (ký tự) | Answered/17 | Abstain/17 | Error/17 |
|---|---|---:|---:|---:|---:|---:|
| Baseline | strict | 3 | 800 | 12/17 | 5/17 | 0/17 |
| Cải thiện 1 | append | 3 | 800 | 14/17 | 3/17 | 0/17 |
| Cải thiện 2 | append | 5 | 2400 | 15/17 | 2/17 | 0/17 |

Mình đã xác nhận nhãn của cấu hình cải thiện 2 trong
`docs/dev-audit/context/reviews.confirmed.json` và tổng hợp lại thành
`metrics.confirmed.json`. Điểm của baseline và cải thiện 1 vẫn lấy từ bản
nhãn dự thảo.

| Cấu hình | Grounded 0/1/2 (N=15) | Trung bình /2 | Citation support | Context đủ | Tool use | Từ chối đúng | Từ chối nhầm |
|---|---|---:|---|---|---|---|---|
| Baseline | 3/0/12 | 1,600 | 12/12 | 14/15 | 17/17 | 2/2 | 3/15 |
| Cải thiện 1 | 1/1/13 | 1,800 | 13/14 | 14/15 | 17/17 | 2/2 | 1/15 |
| Cải thiện 2 | 0/1/14 | 1,933 | 17/19 | 15/15 | 17/17 | 2/2 | 0/15 |

Citation support được chấm theo đóng góp của nguồn với claim được gán; xem lý
do từng nhãn vì một citation hỗ trợ một phần không chứng minh toàn bộ đoạn đã
được cite đủ. Ví dụ dev-009/context có phần pay/benefits được context hỗ trợ
nhưng thiếu citation tương ứng. Vì vậy, mình không dùng số câu `answered` để
thay cho độ chính xác.

| Cấu hình | Median/câu | Input tokens | Output tokens | Chi phí token ước tính |
|---|---:|---:|---:|---|
| Baseline | 3,065 s | 18.429 | 1.646 | 0,0100052 USD |
| Cải thiện 1 | 3,009 s | 18.256 | 1.697 | 0,0100176 USD |
| Cải thiện 2 | 2,534 s | 23.969 | 1.914 | 0,0126500 USD |

Mỗi cấu hình mới được đo một lần. Dù lần chạy context lớn có thời gian thấp
hơn, mình chưa thể kết luận đó là nguyên nhân vì độ trễ API có thể thay đổi. Cải thiện 2
dùng nhiều token hơn. Trace gốc giữ chi phí null. Ước tính riêng theo token đã
ghi và [giá GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
kiểm tra ngày 16/11/2026: input 0,40 USD, cached input 0,10 USD, output 1,60 USD
trên một triệu token. Các run này ghi 0 cached input. Xem
`docs/dev-audit/{baseline,citation,context}/cost-estimate.json` và script
`scripts/estimate_openai_cost.py`. Đây không phải hóa đơn: không gồm thử nghiệm
debug/Gemini, request lỗi chưa ghi usage, thuế/credit hoặc điều chỉnh tài khoản.

### Phân tích lỗi và giả thuyết

1. **dev-005/dev-010 baseline:** context đủ và model trả đúng, có citation array
   nhưng thiếu marker inline; guard biến thành từ chối. Giả thuyết formatter
   giảm từ chối do định dạng. Run cải thiện 1 trả lời được cả hai câu.
2. **dev-012 baseline/cải thiện 1:** query agent viết lại đưa đoạn Jimmy John's
   lên đầu, context nhỏ không giữ đoạn time/distance; tìm lặp rồi chạm giới hạn.
   Giả thuyết tăng top-k/budget tăng evidence trong context. Run cải thiện 2
   trả lời đúng time/distance và cite `e7696e7f8a89ce8cc67b25cc`. Vì thay cùng
   top-k và budget, không tách được tác động riêng từng yếu tố.
3. **dev-004/context:** thêm ví dụ quấy rối đúng theo context nhưng citation chỉ
   trỏ đoạn Title VII không liệt kê ví dụ. **dev-008/context:** thêm gender/race
   ngoài evidence. Context rộng giúp agent có thêm thông tin, nhưng câu trả lời
   cũng dễ dài hơn và có phần chưa được cite đủ. Mình giữ nguyên các output này.

Hai câu thiếu evidence đều có kết quả cuối từ chối, nhưng phải phân biệt model
chủ động báo thiếu với guard/search limit dừng. Không diễn giải 2/2 thành khả
năng nhận biết thiếu evidence hoàn hảo.

## 5. Chọn cấu hình trước test

Mình chọn cấu hình cải thiện 2 dựa trên tiêu chí đã đặt ra từ dev: grounded mean,
sau đó false abstention, citation support, tài nguyên khi chất lượng ngang nhau.
Mình chọn TF-IDF vì trên bộ dev này, chất lượng retrieval bằng hai phương
pháp còn lại nhưng thời gian tìm kiếm thấp hơn.

[`docs/selected-config.json`](../../docs/selected-config.json) ghi cấu hình,
thời điểm và hash code/corpus/dev trước khi chuẩn bị test. Mình chốt lựa chọn
từ kết quả dev. Sau đó, mình đã kiểm tra lại 17 nhãn của cấu hình context;
điểm tổng hợp không thay đổi.
Sau khi chốt, mình giữ nguyên prompt và tham số khi chạy test. Nếu thử sửa
tiếp từ lỗi test, mình sẽ cần một bộ test mới.

## 6. Đánh giá test

Test gồm 5 câu có đáp án và 2 câu thiếu evidence. Mình chạy cả hai cấu hình
bằng terminal. Script kiểm tra hash trước khi chạy để bảo đảm code và cấu
hình không thay đổi. Các trace được giữ nguyên để đánh giá.

Chạy từ terminal đã cấu hình theo [`docs/RUNBOOK.md`](../../docs/RUNBOOK.md):

```powershell
python scripts/run_frozen_test.py --configuration baseline
python scripts/run_frozen_test.py --configuration selected
```

Bảng dưới là kết quả chấm hiện tại; mình còn cần hoàn tất phần đối chiếu nhãn
với PDF.

| Cấu hình test | Grounded /2 | Citation support | Context đủ | Từ chối đúng theo nội dung | Từ chối nhầm | Lỗi API |
|---|---|---|---|---|---|---|
| Baseline | 1,600 (0/1/2: 1/0/4) | 4/4 | 4/5 | 2/2 | 1/5 | 0/7 |
| Selected | 1,600 (0/1/2: 1/0/4) | 11/11 | 4/5 | 2/2 | 1/5 | 0/7 |

Mỗi cấu hình: context grade 0/1/2 là 1/0/4 trên 5 câu có đáp án. Cả hai gọi
retrieval ở 7/7 câu. Xem từng câu trong `docs/test-audit/REVIEWS.md`, evidence
và nguồn citation trong `review-details.json` của mỗi cấu hình.

| Cấu hình | Raw answered/abstain | Median/câu | Input/output tokens | Chi phí token ước tính |
|---|---|---:|---|---:|
| Baseline | 4/3 | 5,321 s | 9.413/695 | 0,0048772 USD |
| Selected | 5/2 | 3,791 s | 13.291/1.045 | 0,0069884 USD |

Chi phí dùng cùng rate card đã ghi ở mục 4, không phải hóa đơn. Xem
`docs/test-audit/{baseline,selected}/cost-estimate.json`. Độ trễ một lần đo
không đủ kết luận context lớn nhanh hơn; selected dùng nhiều token hơn.

**Lỗi chung test-005:** context cuối không có đoạn nói động cơ whistleblowing
là tuân thủ pháp luật/bảo vệ nạn nhân, không phải trả thù. Cả hai tìm lặp rồi
chạm search_limit, dẫn đến từ chối nhầm. Không sửa query/budget theo test này.

**Khác biệt status và ngữ nghĩa test-007/selected:** raw status `answered`,
nhưng câu thực tế nói rõ sách không cung cấp ngày/tháng/năm, không bịa ngày,
và chỉ bổ sung thông tin thập niên 1980/tài khoản Swiss có nguồn. Đánh giá
nội dung là semantic abstention đúng; raw status vẫn giữ nguyên. Theo raw
status, tỷ lệ abstain câu thiếu evidence của selected chỉ 1/2; theo nội dung
đã đọc là 2/2. `agent_metrics.py` trực tiếp trên raw trace giả định abstention
phải có status abstain, nên không phản ánh trường hợp này. Script
`scripts/build_test_audit.py` tổng hợp nhãn diễn giải riêng và ghi rõ cả hai;
Phần tổng hợp này giữ nguyên trace gốc và code agent đã dùng khi chạy test.

Trên bộ test mới, cấu hình mình chọn chưa tăng grounded mean so với baseline.
Cả hai đều bỏ lỡ một câu có đáp án, còn cấu hình context lớn dùng nhiều token
hơn. Mình giữ lựa chọn đã chốt từ dev và ghi nhận đây là giới hạn của lần thử.
Nếu làm tiếp, mình sẽ xem lại cách chọn context và phân loại câu từ chối, rồi
đánh giá trên bộ test khác.

## 7. File kết quả, cách chạy lại và giới hạn

- Code và dependencies: `starter/`, `scripts/`, `requirements.txt`.
- Bảng dev: `docs/dev-audit/COMPARISON.md`, `REVIEWS.md`, từng
  `reviews.draft.json`, `review-details.json`, `metrics.draft.json`.
- Trace gốc: `starter/results/agent-openai-dev-run2/`,
  `agent-openai-dev-citation/`, `agent-openai-dev-context/`.
- Nguồn, config, hash, benchmark: `data/source_manifest.json`,
  `docs/selected-config.json`, `data/test_manifest.json`, các file questions.
- Hướng dẫn tái tạo vector trong DB riêng: `infra/compose.yaml` và
  `scripts/rebuild_index.py`. Không yêu cầu người chấm truy cập volume riêng
  trên máy hiện tại. Mình chưa kiểm tra bước này trên môi trường hoàn toàn mới.
- Unit test: 22 test đã pass ở lần kiểm tra trước; không thay thế benchmark API.
- Mình có dùng AI hỗ trợ viết code, chuẩn bị câu hỏi và đề xuất nhãn đánh giá.
  Mình đã kiểm tra nhãn dev của cấu hình context; các bản nhãn còn lại vẫn
  cần được đối chiếu với tài liệu gốc.
- Giới hạn: corpus nhỏ và tiếng Anh; benchmark ít; không OCR/multimodal; chưa
  stress-test prompt injection; citation formatter không phải semantic verifier;
  API version/cache/độ trễ có thể thay đổi; chi phí mới là ước tính token,
  chưa đối chiếu hóa đơn tài khoản.
- Mình chưa làm phần nâng cao.

## 8. Việc còn thiếu trước khi nộp

- [x] Kiểm tra 17 nhãn dev của cấu hình context, ghi người kiểm tra và tổng hợp lại metrics.
- [ ] Kiểm tra nhãn dev của baseline và cấu hình citation.
- [x] Chạy baseline và selected trên cùng 7 câu test, giữ trace và điền kết quả dự thảo mục 6.
- [ ] Đối chiếu PDF và xác nhận hoặc sửa 14 nhãn test.
- [x] Ghi chi phí token ước tính dev có nguồn giá và ngày kiểm tra; trace gốc không đổi.
- [x] Ước tính chi phí test theo token và bảng giá đã xác minh; chưa phải tổng billing tài khoản.
- [ ] Kiểm tra cài và chạy lại bằng môi trường Python, database mới.
- [ ] Commit/push code, benchmark, trace được phép chia sẻ và báo cáo; kiểm tra
      người chấm có quyền xem repo. Không commit `.env`, token, cache hoặc `.venv`.
