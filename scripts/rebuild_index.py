"""Recreate snapshot B in a NEW empty reproduction database, never replace data."""
import argparse
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chunks', type=Path, default=Path('data/day6_chunks_B.json'))
    parser.add_argument('--cache-dir', type=Path, default=Path('.cache/fastembed'))
    args = parser.parse_args()
    import os
    import psycopg
    from psycopg.types.json import Jsonb
    from fastembed import TextEmbedding
    url = os.environ.get('DATABASE_URL')
    if not url:
        parser.error('Set DATABASE_URL to the isolated reproduction database first')
    chunks = json.loads(args.chunks.read_text(encoding='utf-8'))
    if not chunks or len({c['id'] for c in chunks}) != len(chunks):
        parser.error('Empty corpus or duplicate IDs')
    with psycopg.connect(url, connect_timeout=10) as conn:
        if conn.execute('SELECT current_database()').fetchone()[0] != 'day7_reproduction':
            raise ValueError('Refusing to write: expected dedicated database day7_reproduction')
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        conn.execute('''CREATE TABLE IF NOT EXISTS ingestion_chunks (
            model_name text NOT NULL, strategy text NOT NULL, chunk_id text NOT NULL,
            document_id text NOT NULL, source text NOT NULL, page integer NOT NULL,
            content text NOT NULL, metadata jsonb NOT NULL, embedding vector(384) NOT NULL,
            PRIMARY KEY (model_name, strategy, chunk_id))''')
        conn.execute('LOCK TABLE ingestion_chunks IN EXCLUSIVE MODE')
        if conn.execute('SELECT count(*) FROM ingestion_chunks').fetchone()[0]:
            raise ValueError('Table is not empty; refusing to overwrite existing vectors')
        model = TextEmbedding(model_name='BAAI/bge-small-en-v1.5',
                              cache_dir=str(args.cache_dir), threads=4)
        vectors = list(model.passage_embed([c['text'] for c in chunks], batch_size=32))
        if len(vectors) != len(chunks):
            raise ValueError('Embedding count mismatch')
        rows = []
        for c, vector in zip(chunks, vectors):
            values = vector.tolist()
            if len(values) != 384 or not any(values) or not all(math.isfinite(v) for v in values):
                raise ValueError('Invalid document vector')
            rows.append(('BAAI/bge-small-en-v1.5', 'B', c['id'], c['source_id'],
                         c['source'], c['page'], c['text'], Jsonb(c['metadata']),
                         '[' + ','.join(str(float(v)) for v in values) + ']'))
        with conn.cursor() as cur:
            cur.executemany('''INSERT INTO ingestion_chunks
                (model_name,strategy,chunk_id,document_id,source,page,content,metadata,embedding)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::vector)''', rows)
    print(f'Committed {len(rows)} chunks to isolated day7_reproduction database.')


if __name__ == '__main__':
    main()
