"""Gemini function-calling adapter; reuses the benchmark runner and local retrieval."""
import json
import os
import time

from openai_agent import PROMPT, SEARCH, FINISH, main


def create_gemini_client():
    key = os.environ.get('GEMINI_API_KEY', '')
    if len(key) < 20 or not key.isascii() or any(c.isspace() for c in key):
        raise ValueError('GEMINI_API_KEY is missing or malformed; copy the full API key from Google AI Studio')
    from google import genai
    from google.genai import types
    timeout_seconds = float(os.environ.get('GEMINI_TIMEOUT_SECONDS', '120'))
    if not 1 <= timeout_seconds <= 300:
        raise ValueError('GEMINI_TIMEOUT_SECONDS must be between 1 and 300')
    # Explicit beta supports the documented gemini-flash-latest alias.
    return genai.Client(api_key=key, vertexai=False,
                        http_options=types.HttpOptions(
                            api_version='v1beta', timeout=int(timeout_seconds * 1000),
                            retry_options=types.HttpRetryOptions(attempts=1)))


class GeminiController:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.calls = []
        self.request_delay = 0
        self.on_request = None

    def decide(self, question, history):
        if self.request_delay:
            print(f'  Waiting {self.request_delay:g}s before API request...', flush=True)
            time.sleep(self.request_delay)
        if self.on_request:
            self.on_request()
        # Rebuild each decision from the bounded, actual retrieval context.
        available = (SEARCH, FINISH) if history else (SEARCH,)
        tools = [{'type': 'function', 'name': tool['name'],
                  'description': tool['description'], 'parameters': tool['parameters']}
                 for tool in available]
        response = self.client.interactions.create(
            model=self.model,
            input=PROMPT + '\n\n' + json.dumps(
                {'question': question, 'retrieval_history': history}),
            tools=tools, generation_config={'tool_choice': 'any'},
            timeout=float(os.environ.get('GEMINI_TIMEOUT_SECONDS', '120')))
        calls = [step for step in (response.steps or []) if step.type == 'function_call']
        usage = getattr(response, 'usage', None)
        self.calls.append({
            'api': 'interactions', 'response_id': getattr(response, 'id', None),
            'model': getattr(response, 'model', None) or self.model,
            'usage': usage.model_dump(mode='json') if hasattr(usage, 'model_dump') else usage,
            'output': [call.model_dump(mode='json') for call in calls]})
        if len(calls) != 1:
            raise ValueError('Expected exactly one search or finish function call')
        call = calls[0]
        args = json.loads(call.arguments) if isinstance(call.arguments, str) else dict(call.arguments or {})
        if call.name == 'search':
            return {'action': 'search', 'query': args['query']}
        if call.name == 'finish' and history:
            return {'action': 'answer', 'answer': args['answer'], 'citations': args['citations']}
        raise ValueError('Unknown or premature Gemini tool call')


if __name__ == '__main__':
    main(provider='gemini')
