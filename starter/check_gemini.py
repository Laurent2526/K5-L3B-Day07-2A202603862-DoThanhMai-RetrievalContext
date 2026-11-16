"""Isolate Gemini model access, basic generation and tool calling."""
import argparse
import json
import os
from importlib.metadata import version
from pathlib import Path

from gemini_agent import GeminiController, create_gemini_client
from openai_agent import error_details


def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default=os.environ.get('GEMINI_MODEL', 'gemini-flash-latest'))
    args = parser.parse_args()
    print('google-genai:', version('google-genai'), flush=True)
    client = create_gemini_client()
    try:
        print('1. List accessible Flash models', flush=True)
        try:
            models = list(client.models.list())
            for model in models:
                if 'flash' in (model.name or '').lower():
                    print(model.name, 'actions=', getattr(model, 'supported_actions', None), flush=True)
        except Exception as error:
            print(type(error).__name__, json.dumps(error_details(error), ensure_ascii=True))
            return
        print(f'2. Minimal generation: {args.model}', flush=True)
        try:
            from google.genai import types
            response = client.models.generate_content(
                model=args.model, contents='Reply with OK.',
                config=types.GenerateContentConfig(max_output_tokens=128))
            if not response.text:
                print('No text returned; inspect finish/block status before running agent.')
                return
            print('Text generation OK; model:', getattr(response, 'model_version', None), flush=True)
        except Exception as error:
            print(type(error).__name__, json.dumps(error_details(error), ensure_ascii=True))
            return
        print('3. Tool calling via Interactions API: one search decision', flush=True)
        try:
            decision = GeminiController(client, args.model).decide('In what year was OSHA passed?', [])
            print('Tool decision:', decision['action'], flush=True)
        except Exception as error:
            print(type(error).__name__, json.dumps(error_details(error), ensure_ascii=True))
    finally:
        client.close()


if __name__ == '__main__':
    main()
