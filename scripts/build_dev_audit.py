"""Package explicit AI-assisted draft reviews of the three existing dev runs.

Semantic exceptions below were identified by reading answers and source chunks.
These are draft annotations, not human confirmation or automatic correctness labels.
No API requests are made and no agent outputs are changed.
"""
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter'))
from agent_metrics import aggregate

RUNS = {
    'baseline': 'agent-openai-dev-run2',
    'citation': 'agent-openai-dev-citation',
    'context': 'agent-openai-dev-context',
}

# These judgements require the student to review the original PDF before submission.
PARTIAL = {
    ('citation', 'dev-008'): 'Đáp án chính đúng; bổ sung đối chiếu job titles/traditional pay scales không được nêu rõ trong context. Chấm bảo thủ 1/2.',
    ('context', 'dev-008'): 'Đáp án chính đúng; bổ sung gender/race không có evidence trong context. Chấm 1/2, citation không hỗ trợ đầy đủ phần mở rộng.',
}
SCOPE = {
    ('context', 'dev-004'): 'Grounded answer 2/2 vì đoạn liệt kê hành vi có trong context (dc145...). Tuy nhiên chỉ cite 76521..., vốn không liệt kê các hành vi; citation có hỗ trợ phần chính nhưng chưa hỗ trợ toàn bộ phạm vi đoạn trả lời.',
    ('context', 'dev-009'): 'Grounded answer 2/2: phần increased pay/benefits nằm trong context da7e1.... Hai citation đã chọn hỗ trợ vai trò union và dispute/lobby/industry norms, nhưng phần pay/benefits chưa gắn đúng citation. Giữ nhãn true cho đóng góp của từng citation và ghi riêng lỗ hổng coverage.',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / 'docs/dev-audit'
    if out.exists():
        raise SystemExit('docs/dev-audit already exists; preserve edited reviews rather than overwrite')
    cases = [q for q in read(ROOT / 'data/questions.json') if q['split'] == 'dev']
    chunks = {c['id']: c for c in read(ROOT / 'data/day6_chunks_B.json')}
    if len(cases) != 17 or sum(c['answerable'] for c in cases) != 15:
        raise ValueError('Expected current 17-case dev benchmark')
    comparisons = []
    lines = ['# Bản chấm dev có AI hỗ trợ', '',
             '**Trạng thái: DRAFT — chưa được người làm bài xác nhận với PDF.**', '',
             'Không gọi API, không thay đổi trace. Điểm grounded answer dựa trên toàn bộ context cuối; '
             'citation support được xét riêng theo nội dung nguồn được cite. Nhãn true của một citation '
             'có thể chỉ xác nhận đóng góp của nó; xem ghi chú coverage để tránh hiểu là mọi khẳng định đều được cite đủ.', '',
             'Nguồn PDF: Business Ethics, OpenStax; số trang trong bảng là trang PDF, không phải số in trên sách.', '']
    for label, run in RUNS.items():
        trace_file = ROOT / 'starter/results' / run / 'traces.json'
        traces = read(trace_file)
        by_id = {t['query_id']: t for t in traces}
        if len(traces) != len(cases) or len(by_id) != len(cases):
            raise ValueError(f'{run}: incomplete or duplicate traces')
        reviews = []
        details = []
        lines += [f'## {label}: {run}', '',
                  '| Câu | Status | Context 0–2 | Grounded 0–2 | Citation support | Lý do |',
                  '|---|---|---:|---:|---|---|']
        for case in cases:
            cid = case['id']
            trace = by_id[cid]
            answerable = case['answerable']
            citations = trace['citations']
            review = {'query_id': cid, 'reviewer': 'AI-assisted draft', 'human_confirmed': False,
                      'citation_support': [key in trace['context_ids'] for key in citations]}
            context_grade = None
            if answerable:
                evidence_found = any(g['evidence'] in trace['context'] for g in case['gold'])
                context_grade = 2 if evidence_found else 0
                grade = 0 if trace['status'] == 'abstain' else 2
                if (label, cid) in PARTIAL:
                    grade = 1
                    reason = PARTIAL[label, cid]
                    review['citation_support'] = [False] * len(citations)
                elif trace['status'] == 'abstain':
                    last = trace['events'][-1]['event']
                    reason = ('Context đủ evidence nhưng câu trả lời cuối bị guard từ chối do thiếu citation inline.'
                              if last == 'invalid_or_missing_citations' and evidence_found else
                              'Context cuối thiếu evidence time/distance; tìm lặp rồi chạm search limit. Từ chối câu có đáp án chấm 0.')
                else:
                    reason = 'Nội dung đáp án đáp ứng gold; evidence và citation tương ứng có trong context.'
                if (label, cid) in SCOPE:
                    reason = SCOPE[label, cid]
                    if cid == 'dev-004':
                        review['citation_support'] = [False] * len(citations)
                review.update(answer_grade=grade, context_grade=context_grade)
            else:
                review['abstention_correct'] = trace['status'] == 'abstain'
                cause = trace['events'][-1]['event']
                reason = ('Kết quả cuối nêu thiếu bằng chứng, không thêm khẳng định vô căn cứ. '
                          f'Lý do dừng: {cause}; cần phân biệt guard dừng với model chủ động từ chối. '
                          + case['absence_reason'])
            review['reason'] = reason
            reviews.append(review)
            citation_details = []
            for key, supported in zip(citations, review['citation_support']):
                source = chunks[key]
                citation_details.append({'id': key, 'page': source['page'], 'source': source['source'],
                                         'text': source['text'], 'support_draft': supported})
            details.append({'query_id': cid, 'question': case['question'],
                            'expected_answer': case.get('expected_answer'), 'gold': case.get('gold'),
                            'answer': trace['answer'], 'context': trace['context'],
                            'citation_sources': citation_details, 'review': review})
            support_text = ', '.join('true' if s else 'false' for s in review['citation_support']) or 'N/A'
            lines.append(f"| {cid} | {trace['status']} | {context_grade if context_grade is not None else 'N/A'} | "
                         f"{review.get('answer_grade', 'N/A')} | {support_text} | {reason.replace('|', '/')} |")
        metrics = aggregate(cases, traces, reviews)
        successful = [t for t in traces if t['status'] != 'error']
        context_counts = Counter(r['context_grade'] for r in reviews if 'context_grade' in r)
        usage = Counter()
        for trace in traces:
            for call in trace['api_calls']:
                u = call.get('usage') or {}
                for key in ('input_tokens', 'output_tokens', 'total_tokens'):
                    usage[key] += u.get(key, 0)
        summary = {'label': label, 'run': run, 'review_status': 'AI_DRAFT_NOT_HUMAN_CONFIRMED',
                   'trace_sha256': digest(trace_file), 'metrics': metrics,
                   'context_grades': {str(k): context_counts[k] for k in (0, 1, 2)},
                   'context_evidence_rate': {'n': context_counts[2], 'N': 15},
                   'median_seconds': statistics.median(t['elapsed_seconds'] for t in successful),
                   'search_distribution': dict(Counter(str(sum(e['event'] == 'search' for e in t['events'])) for t in traces)),
                   'usage': dict(usage), 'cost_usd': None}
        write(out / label / 'reviews.draft.json', reviews)
        write(out / label / 'review-details.json', details)
        write(out / label / 'metrics.draft.json', summary)
        comparisons.append(summary)
        lines += ['']
    write(out / 'comparison.draft.json', comparisons)
    header = ['# So sánh dev — bản nhãn dự thảo', '',
              '**Các số grounded/citation dưới đây dựa trên nhãn AI dự thảo; chưa phải chấm tay cuối cùng.**', '',
              '| Cấu hình | Grounded trung bình /2 | Điểm 0/1/2 | Citation hợp lệ | Context đủ | Từ chối nhầm | Từ chối đúng | Median giây | Input/output tokens |',
              '|---|---:|---|---|---|---|---|---:|---|']
    for s in comparisons:
        m = s['metrics']; g = m['grounded_answer']; cv = m['citation_validity']
        f = m['false_abstention']; a = m['abstention']; ce = s['context_evidence_rate']
        header.append(f"| {s['label']} | {g['mean']:.3f} | {g['0']}/{g['1']}/{g['2']} | "
                      f"{cv['n']}/{cv['N']} | {ce['n']}/{ce['N']} | {f['n']}/{f['N']} | "
                      f"{a['n']}/{a['N']} | {s['median_seconds']:.3f} | "
                      f"{s['usage'].get('input_tokens', 0)}/{s['usage'].get('output_tokens', 0)} |")
    header += ['', 'Không suy ra accuracy 100% từ số answered. Chi phí chưa tính, không coi là 0.', '',
               'Đề xuất cấu hình context (append, top-k=5, budget=2400), dựa trên grounded mean cao '
               'hơn và không từ chối nhầm trên dev. Cấu hình này dùng context/token lớn hơn và vẫn '
               'có lỗi phạm vi citation; không sửa thêm để chạy lại chọn output đẹp.', '',
               'Trước khi chốt: người làm bài kiểm tra các nhãn với PDF, đặc biệt citation/dev-008 '
               'và context/dev-004, dev-008, dev-009. Cập nhật nhãn theo bằng chứng và ghi người '
               'kiểm tra; không đổi human_confirmed chỉ vì đã mở file.', '',
               'Sau đó chốt cấu hình/source hash, tạo bộ test mới 5 câu có đáp án và 2 câu thiếu '
               'evidence, chạy baseline và cấu hình đã chọn trên cùng test. Chưa có test nào được '
               'tạo hoặc chạy trong bước đánh giá dev này.']
    out.mkdir(exist_ok=True)
    (out / 'REVIEWS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (out / 'COMPARISON.md').write_text('\n'.join(header) + '\n', encoding='utf-8')
    write(out / 'selected-config.proposed.json', {
        'status': 'proposed_pending_student_source_review', 'selection_split': 'dev',
        'provider': 'openai', 'model': 'gpt-4.1-mini', 'retriever': 'tfidf',
        'citation_format': 'append', 'top_k': 5, 'budget_chars': 2400, 'max_searches': 3,
        'baseline_run': RUNS['baseline'], 'selected_run': RUNS['context'],
        'selection_rule': 'grounded mean, then fewer false abstentions, then citation support, then resource use',
        'hashes': {name: digest(ROOT / name) for name in
                   ('data/questions.json', 'data/day6_chunks_B.json', 'starter/openai_agent.py',
                    'starter/agentic.py', 'starter/baseline.py')},
        'limitation': 'Human PDF review not yet confirmed. This proposal is not a completed test evaluation.'})
    for summary in comparisons:
        print(json.dumps({'configuration': summary['label'],
                          'grounded_mean_draft': summary['metrics']['grounded_answer']['mean'],
                          'citation_support_draft': summary['metrics']['citation_validity']}, ensure_ascii=True))
    print('Draft review artifacts: docs/dev-audit/')


if __name__ == '__main__':
    main()
