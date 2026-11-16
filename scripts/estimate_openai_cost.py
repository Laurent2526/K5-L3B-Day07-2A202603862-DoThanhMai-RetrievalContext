"""Estimate recorded GPT-4.1 mini token cost; no API calls or trace modifications."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--traces', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    traces = json.loads(args.traces.read_text(encoding='utf-8'))
    totals = {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0, 'api_calls': 0}
    for trace in traces:
        for call in trace.get('api_calls', []):
            if not str(call.get('model', trace.get('model', ''))).startswith('gpt-4.1-mini'):
                raise ValueError('This rate card only applies to GPT-4.1 mini')
            usage = call.get('usage')
            if not usage or 'input_tokens' not in usage or 'output_tokens' not in usage:
                raise ValueError('Missing token usage; cannot estimate silently')
            totals['api_calls'] += 1
            totals['input_tokens'] += usage['input_tokens']
            totals['output_tokens'] += usage['output_tokens']
            totals['cached_input_tokens'] += (usage.get('input_tokens_details') or {}).get('cached_tokens', 0)
    cached = totals['cached_input_tokens']
    cost = ((totals['input_tokens'] - cached) * .40 + cached * .10 + totals['output_tokens'] * 1.60) / 1_000_000
    result = {'status': 'token_price_estimate_not_billing_receipt',
              'price_checked_date': '2026-11-16',
              'source': 'https://developers.openai.com/api/docs/models/gpt-4.1-mini',
              'usd_per_million_tokens': {'input': .40, 'cached_input': .10, 'output': 1.60},
              'traces': args.traces.as_posix(), 'usage': totals, 'estimated_usd': round(cost, 8),
              'limitations': 'Only recorded successful calls, standard text-token pricing. Excludes failed/unrecorded requests, other runs, tax, credits and account-specific billing adjustments.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'estimated_usd': result['estimated_usd'], 'usage': totals}))


if __name__ == '__main__':
    main()
