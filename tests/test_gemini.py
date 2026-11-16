import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from gemini_agent import GeminiController


class GeminiAdapterTests(unittest.TestCase):
    def test_search_uses_interactions_and_only_search_tool_initially(self):
        received = {}
        call = SimpleNamespace(type='function_call', name='search', arguments={'query': 'OSHA'})
        call.model_dump = lambda **kwargs: {'name': call.name, 'arguments': call.arguments}
        def create(**kwargs):
            received.update(kwargs)
            return SimpleNamespace(id='fake', model='fake-model', steps=[call], usage=None)
        client = SimpleNamespace(interactions=SimpleNamespace(create=create))
        controller = GeminiController(client, 'fake-model')
        self.assertEqual(controller.decide('When was OSHA passed?', []),
                         {'action': 'search', 'query': 'OSHA'})
        self.assertEqual([t['name'] for t in received['tools']], ['search'])
        self.assertEqual(controller.calls[0]['api'], 'interactions')

    def test_finish_receives_actual_context_and_normalizes_json_arguments(self):
        call = SimpleNamespace(type='function_call', name='finish',
                               arguments='{"answer":"1970 [c1]","citations":["c1"]}')
        call.model_dump = lambda **kwargs: {'name': call.name, 'arguments': call.arguments}
        received = {}
        def create(**kwargs):
            received.update(kwargs)
            return SimpleNamespace(id='fake', steps=[call], usage=None)
        controller = GeminiController(SimpleNamespace(interactions=SimpleNamespace(create=create)), 'fake')
        result = controller.decide('When?', [{'context': '1970', 'context_ids': ['c1']}])
        self.assertEqual(result['citations'], ['c1'])
        self.assertIn('context_ids', received['input'])
        self.assertEqual([t['name'] for t in received['tools']], ['search', 'finish'])
