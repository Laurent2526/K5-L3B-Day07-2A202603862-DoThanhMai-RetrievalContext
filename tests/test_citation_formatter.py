import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from openai_agent import CitationFormatter


class ControllerStub:
    def __init__(self, action):
        self.action = action
        self.calls = [{}]

    def decide(self, question, history):
        return self.action


class CitationFormatterTests(unittest.TestCase):
    def test_only_selected_ids_are_rendered_and_raw_answer_is_preserved(self):
        controller = ControllerStub({'action': 'answer', 'answer': '1970.', 'citations': ['a', 'a']})
        result = CitationFormatter(controller).decide('When?', [{'context_ids': ['a', 'unused']}])
        self.assertEqual(result['answer'], '1970. [a]')
        self.assertEqual(controller.action['answer'], '1970.')
        audit = controller.calls[-1]['citation_formatting']
        self.assertEqual(audit['original_answer'], '1970.')
        self.assertFalse(audit['semantic_support_verified'])

    def test_invalid_citation_is_not_repaired(self):
        action = {'action': 'answer', 'answer': '1970.', 'citations': ['invented']}
        controller = ControllerStub(action)
        self.assertEqual(CitationFormatter(controller).decide('When?', [{'context_ids': ['a']}]), action)
        self.assertNotIn('citation_formatting', controller.calls[-1])

    def test_abstention_and_existing_inline_citations_are_unchanged(self):
        for action in ({'action': 'answer', 'answer': 'Insufficient evidence.', 'citations': []},
                       {'action': 'answer', 'answer': '1970 [a].', 'citations': ['a']},
                       {'action': 'search', 'query': 'OSHA'}):
            controller = ControllerStub(action)
            self.assertEqual(CitationFormatter(controller).decide('When?', [{'context_ids': ['a']}]), action)
            self.assertNotIn('citation_formatting', controller.calls[-1])
