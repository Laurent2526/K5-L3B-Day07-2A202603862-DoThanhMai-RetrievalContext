"""Check fusion independently of database and embedding model availability."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from dense import HybridIndex


class RankedRetriever:
    def __init__(self, ids, scale):
        self.rows = [{'id': key, 'text': key, 'score': scale / rank}
                     for rank, key in enumerate(ids, 1)]

    def search(self, question, top_k=3):
        return self.rows[:top_k]


class HybridTests(unittest.TestCase):
    def test_shared_evidence_is_promoted_without_combining_raw_scores(self):
        dense = RankedRetriever(['a', 'shared', 'c'], 0.9)
        lexical = RankedRetriever(['b', 'shared', 'd'], 10000)
        index = HybridIndex(dense, lexical, candidate_k=3)
        rows = index.search('question')
        self.assertEqual([r['id'] for r in rows], ['shared', 'a', 'b'])
        self.assertAlmostEqual(rows[0]['score'], 2 / 62)
        self.assertEqual(rows[0]['component_ranks'], {'dense': 2, 'tfidf': 2})
        self.assertEqual(len(index.last_candidates['dense']), 3)
        self.assertEqual(len({r['id'] for r in rows}), 3)

    def test_empty_lexical_results_keep_dense_ranking(self):
        index = HybridIndex(RankedRetriever(['a', 'b', 'c'], 1), RankedRetriever([], 1))
        self.assertEqual([r['id'] for r in index.search('question')], ['a', 'b', 'c'])


if __name__ == '__main__':
    unittest.main()
