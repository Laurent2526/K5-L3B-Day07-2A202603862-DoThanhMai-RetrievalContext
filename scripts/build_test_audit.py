"""Explicit AI-assisted review of frozen test runs; no API calls or agent edits.

The selected test-007 output states the exact date is unavailable. Its raw
status is answered because the guard only validates citations. Preserve raw
records and report semantic abstention separately. Human PDF review is pending.
"""
import copy
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter'))
from agent_metrics import aggregate
from baseline import hit


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    target = ROOT / 'docs/test-audit'
    if target.exists():
        raise SystemExit('Test audit exists; do not overwrite reviewed labels')
    cases = load(ROOT / 'data/questions_test.json')
    chunks = {c['id']: c for c in load(ROOT / 'data/day6_chunks_B.json')}
    comparisons = []
    lines = ['# Chấm test có AI hỗ trợ', '',
             '**DRAFT — chưa có xác nhận đối chiếu PDF của người làm bài.**', '',
             'Giữ nguyên raw status, câu trả lời và trace. Nhãn semantic abstention dựa trên nội dung '
             'được đọc, không chỉ chuỗi status. Không dùng kết quả test này để chỉnh cấu hình.', '']
    for label in ('baseline', 'selected'):
        trace_file = ROOT / f'starter/results/agent-openai-test-{label}/traces.json'
        traces = load(trace_file)
        trace_by_id = {t['query_id']: t for t in traces}
        if len(traces) != 7 or set(trace_by_id) != {c['id'] for c in cases}:
            raise ValueError('Expected exactly the same 7 test cases in both runs')
        reviews, details = [], []
        semantic_traces = copy.deepcopy(traces)
        context_counts = Counter()
        hits = Counter()
        lines += [f'## {label}', '',
                  '| Câu | Raw status | Nội dung thực tế | Context 0–2 | Điểm 0–2 | Citation support | Lý do |',
                  '|---|---|---|---:|---:|---|---|']
        for case in cases:
            cid = case['id']; trace = trace_by_id[cid]
            review = {'query_id': cid, 'reviewer': 'AI-assisted test draft',
                      'human_confirmed': False, 'raw_status': trace['status'],
                      'citation_support': [True] * len(trace['citations'])}
            for key in trace['citations']:
                if key not in trace['context_ids']:
                    raise ValueError('Citation not in final context')
            if case['answerable']:
                gold_in_context = any(g['evidence'] in trace['context'] for g in case['gold'])
                review['context_grade'] = 2 if gold_in_context else 0
                context_counts[review['context_grade']] += 1
                review['answer_grade'] = 0 if cid == 'test-005' else 2
                review['semantic_status'] = trace['status']
                reason = ('Context cuối không chứa evidence về động cơ whistleblowing. Agent tìm lặp và chạm search_limit; từ chối nhầm câu có đáp án nên điểm 0.'
                          if cid == 'test-005' else
                          'Nội dung đáp án và điều kiện/số liệu khớp nguồn; citation có trong context và hỗ trợ các phần được nêu.')
                searches = [e for e in trace['events'] if e['event'] == 'search']
                first = searches[0]['results'] if searches else []
                hits['hit1'] += bool(first and hit(first[0], case['gold']))
                hits['hit3'] += any(hit(c, case['gold']) for c in first[:3])
                hits['context'] += gold_in_context
            else:
                review['semantic_status'] = 'abstain'
                review['abstention_correct'] = True
                reason = ('Nội dung nói rõ không có ngày lịch chính xác, không tự tạo ngày; mô tả thập niên 1980 và tài khoản Swiss được nguồn hỗ trợ. Raw status answered chỉ do có citation; chấm semantic abstention đúng. Việc khẳng định thiếu ngày còn được đối chiếu với absence_reason của toàn corpus.'
                          if label == 'selected' and cid == 'test-007' else
                          'Kết quả cuối báo không đủ bằng chứng và không đưa ra mức lương/ngày tháng không có nguồn. Guard dừng do search_limit, không đồng nghĩa model chủ động kết luận thiếu thông tin.')
            review['reason'] = reason
            reviews.append(review)
            details.append({'query_id': cid, 'question': case['question'],
                            'expected_answer': case.get('expected_answer'),
                            'absence_reason': case.get('absence_reason'), 'gold': case.get('gold'),
                            'answer': trace['answer'], 'context': trace['context'],
                            'citation_sources': [chunks[key] for key in trace['citations']],
                            'review': review})
            for derived in semantic_traces:
                if derived['query_id'] == cid:
                    derived['status'] = review['semantic_status']
            lines.append(f"| {cid} | {trace['status']} | {review['semantic_status']} | "
                         f"{review.get('context_grade', 'N/A')} | {review.get('answer_grade', 'N/A')} | "
                         f"{sum(review['citation_support'])}/{len(review['citation_support'])} | {reason} |")
        # This aggregation consumes an explicit reviewed interpretation, NOT modified raw traces.
        metrics = aggregate(cases, semantic_traces, reviews)
        usage = Counter()
        for trace in traces:
            for call in trace['api_calls']:
                u = call.get('usage') or {}
                for key in ('input_tokens', 'output_tokens', 'total_tokens'):
                    usage[key] += u.get(key, 0)
        summary = {'review_status': 'AI_DRAFT_NOT_HUMAN_CONFIRMED', 'configuration': label,
                   'trace_sha256': hashlib.sha256(trace_file.read_bytes()).hexdigest(),
                   'raw_statuses': dict(Counter(t['status'] for t in traces)),
                   'semantic_statuses': dict(Counter(t['status'] for t in semantic_traces)),
                   'metrics_semantic_review': metrics,
                   'abstention_by_raw_status': {'n': sum(not c['answerable'] and trace_by_id[c['id']]['status'] == 'abstain' for c in cases), 'N': 2},
                   'retrieval_first_agent_query': {'hit1': {'n': hits['hit1'], 'N': 5}, 'hit3': {'n': hits['hit3'], 'N': 5}},
                   'context_evidence_rate': {'n': hits['context'], 'N': 5},
                   'context_grades': {str(k): context_counts[k] for k in (0, 1, 2)},
                   'median_seconds': statistics.median(t['elapsed_seconds'] for t in traces),
                   'search_distribution': dict(Counter(str(sum(e['event'] == 'search' for e in t['events'])) for t in traces)),
                   'usage': dict(usage),
                   'limitation': 'Semantic abstention is an explicit AI-assisted review; human confirmation pending. agent_metrics.py directly on raw selected traces rejects abstention_correct=true for an answered status; use this report to disclose the mismatch, not to rewrite traces.'}
        dump(target / label / 'reviews.draft.json', reviews)
        dump(target / label / 'review-details.json', details)
        dump(target / label / 'metrics.draft.json', summary)
        comparisons.append(summary)
        lines += ['']
    dump(target / 'comparison.draft.json', comparisons)
    (target / 'REVIEWS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    table = ['# Kết quả test — nhãn AI dự thảo', '',
             'Không đổi cấu hình sau test. Không ghi đè raw status/trace. Cần đối chiếu PDF trước nộp.', '',
             '| Cấu hình | Grounded /2 | Context đủ | Citation support | Từ chối đúng theo nội dung | Theo raw status | Từ chối nhầm | Median giây |',
             '|---|---:|---|---|---|---|---|---:|']
    for s in comparisons:
        m=s['metrics_semantic_review'];cv=m['citation_validity'];a=m['abstention'];f=m['false_abstention'];ce=s['context_evidence_rate'];raw=s['abstention_by_raw_status']
        table.append(f"| {s['configuration']} | {m['grounded_answer']['mean']:.3f} | {ce['n']}/{ce['N']} | {cv['n']}/{cv['N']} | {a['n']}/{a['N']} | {raw['n']}/{raw['N']} | {f['n']}/{f['N']} | {s['median_seconds']:.3f} |")
    table += ['', 'Hai cấu hình đạt cùng grounded mean trên 5 câu có đáp án; selected không cải thiện test-005. '
              'Không kết luận selected tốt hơn trên test chỉ vì answered tăng từ 4 lên 5: câu thứ năm là lời '
              'báo thiếu ngày chính xác có citation (test-007), không phải một câu có đáp án mới được giải quyết.', '',
              'Selected dùng context lớn và nhiều citation hơn. Giữ cấu hình đã chọn trên dev, báo trung thực '
              'rằng lợi ích dev không chuyển thành điểm grounded test cao hơn. Nếu muốn sửa query/context hoặc '
              'semantic status sau khi thấy lỗi test, đó là nghiên cứu tiếp và cần test mới.']
    (target / 'COMPARISON.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    for s in comparisons:
        print(json.dumps({'configuration': s['configuration'], 'metrics': s['metrics_semantic_review'],
                          'median_seconds':s['median_seconds'],'usage':s['usage']},ensure_ascii=True))


if __name__ == '__main__':
    main()
