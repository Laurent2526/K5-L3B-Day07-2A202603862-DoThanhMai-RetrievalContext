"""Read-only exact pgvector retrieval using the Day 6 FastEmbed model."""
import argparse
import json
import math
import os
import statistics
import time
from pathlib import Path

from baseline import TfidfIndex, evaluate, validate

MODEL = 'BAAI/bge-small-en-v1.5'


class DenseIndex:
    def __init__(self, connection, model):
        self.connection = connection
        self.model = model

    def search(self, question, top_k=3):
        if not question.strip():
            return []
        if type(top_k) is not int or top_k < 1:
            raise ValueError('top_k must be a positive integer')
        vector = next(iter(self.model.query_embed(question))).tolist()
        if len(vector) != 384 or not all(math.isfinite(v) for v in vector) or not any(vector):
            raise ValueError('Invalid query embedding')
        literal = '[' + ','.join(str(float(v)) for v in vector) + ']'
        rows = self.connection.execute(
            '''SELECT chunk_id AS id, document_id AS source_id, source, page,
                      content AS text, metadata,
                      1 - (embedding <=> %s::vector) AS score
               FROM ingestion_chunks WHERE model_name = %s AND strategy = %s
               ORDER BY embedding <=> %s::vector, chunk_id LIMIT %s''',
            (literal, MODEL, 'B', literal, top_k)).fetchall()
        return [{**row, 'strategy': 'dense', 'rank': rank}
                for rank, row in enumerate(rows, 1)]


class HybridIndex:
    """Equal-weight RRF over independently ranked dense and lexical candidates."""

    def __init__(self, dense, lexical, candidate_k=10, rrf_constant=60):
        if type(candidate_k) is not int or candidate_k < 3:
            raise ValueError('candidate_k must be an integer >= 3')
        if type(rrf_constant) is not int or rrf_constant < 1:
            raise ValueError('rrf_constant must be a positive integer')
        self.dense = dense
        self.lexical = lexical
        self.candidate_k = candidate_k
        self.rrf_constant = rrf_constant
        self.last_candidates = {}

    def search(self, question, top_k=3):
        if type(top_k) is not int or top_k < 1 or top_k > self.candidate_k:
            raise ValueError('top_k must be between 1 and candidate_k')
        candidates = {
            'dense': self.dense.search(question, top_k=self.candidate_k),
            'tfidf': self.lexical.search(question, top_k=self.candidate_k)}
        self.last_candidates = candidates
        fused = {}
        for method, rows in candidates.items():
            seen = set()
            for rank, row in enumerate(rows, 1):
                if row['id'] in seen:
                    continue
                seen.add(row['id'])
                if row['id'] not in fused:
                    fused[row['id']] = {**row, 'strategy': 'hybrid', 'score': 0.0,
                                        'component_ranks': {}, 'component_scores': {}}
                result = fused[row['id']]
                result['score'] += 1 / (self.rrf_constant + rank)
                result['component_ranks'][method] = rank
                result['component_scores'][method] = row['score']
        ranked = sorted(fused.values(), key=lambda row: (-row['score'], row['id']))
        return [{**row, 'rank': rank} for rank, row in enumerate(ranked[:top_k], 1)]


def main(default_method='dense'):
    parser = argparse.ArgumentParser(description=f'Read-only {default_method} pgvector benchmark')
    parser.add_argument('--chunks', required=True, type=Path)
    parser.add_argument('--questions', required=True, type=Path)
    parser.add_argument('--split', required=True, choices=('dev', 'test'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache-dir', type=Path, default=Path('.cache/fastembed'))
    if default_method == 'hybrid':
        parser.add_argument('--candidate-k', type=int, default=10)
        parser.add_argument('--rrf-constant', type=int, default=60)
    args = parser.parse_args()
    if default_method == 'hybrid' and (args.candidate_k < 3 or args.rrf_constant < 1):
        parser.error('candidate-k must be >= 3 and rrf-constant must be positive')
    url = os.environ.get('DATABASE_URL')
    if not url:
        parser.error('Set DATABASE_URL in this terminal first')
    if any((args.output / name).exists() for name in ('summary.json', 'traces.json')):
        parser.error('Output already exists; choose a new output directory')
    chunks = json.loads(args.chunks.read_text(encoding='utf-8'))
    questions = json.loads(args.questions.read_text(encoding='utf-8'))
    selected = [q for q in questions if q.get('split') == args.split]
    answerable = [q for q in selected if q.get('answerable') is not False]
    validate(chunks, answerable)

    import psycopg
    from psycopg.rows import dict_row
    from fastembed import TextEmbedding

    started = time.perf_counter()
    with psycopg.connect(url, row_factory=dict_row, connect_timeout=10) as connection:
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows = connection.execute(
            '''SELECT chunk_id AS id, document_id AS source_id, source, page, content AS text
               FROM ingestion_chunks WHERE model_name = %s AND strategy = %s''',
            (MODEL, 'B')).fetchall()
        fields = ('id', 'source_id', 'source', 'page', 'text')
        expected = {c['id']: tuple(c[k] for k in fields) for c in chunks}
        actual = {c['id']: tuple(c[k] for k in fields) for c in rows}
        if actual != expected:
            raise ValueError('Database snapshot B differs from --chunks; inspect Day 6 data before benchmarking')
        print(f'Database corpus verified: {len(rows)} chunks. Loading embedding model...', flush=True)
        model = TextEmbedding(model_name=MODEL, cache_dir=str(args.cache_dir), threads=4)
        index = DenseIndex(connection, model)
        if default_method == 'hybrid':
            index = HybridIndex(index, TfidfIndex(chunks), args.candidate_k, args.rrf_constant)
        setup_seconds = time.perf_counter() - started
        traces = []
        for question in answerable:
            trace = evaluate(index, [question], budget=800)[0]
            if default_method == 'hybrid':
                trace['candidate_results'] = index.last_candidates
            traces.append(trace)
    for trace in traces:
        trace['strategy'] = default_method
    summary = {
        'strategy': default_method, 'split': args.split, 'n': len(traces),
        'unanswerable_excluded': len(selected) - len(answerable),
        'model': MODEL, 'dimensions': 384, 'snapshot': 'B', 'corpus_chunks': len(rows),
        'search': 'exact cosine', 'top_k': 3, 'budget_chars': 800,
        'hit1': sum(t['hit1'] for t in traces),
        'hit3': sum(t['hit3'] for t in traces),
        'context_hit': sum(t['context_hit'] for t in traces),
        'avg_context_chars': statistics.mean(t['context_chars'] for t in traces),
        'median_ms': statistics.median(t['elapsed_ms'] for t in traces),
        'setup_seconds': setup_seconds, 'service_cost_usd': 0,
        'timing_note': 'Per-query time includes query embedding, SQL retrieval and context packing; setup is separate.'}
    if default_method == 'hybrid':
        summary.update(fusion='equal-weight RRF', candidate_k_per_retriever=args.candidate_k,
                       rrf_constant=args.rrf_constant,
                       timing_note='Per-query time includes embedding, SQL, lexical retrieval, RRF and context packing; setup is separate.')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (('summary.json', summary), ('traces.json', traces)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
