"""Run one preselected test configuration after checking frozen source/data hashes."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', choices=('baseline', 'selected'), required=True)
    parser.add_argument('--dry-run', action='store_true', help='Check hashes and print command without any API call')
    args = parser.parse_args()
    config_path = ROOT / 'docs/selected-config.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'data/test_manifest.json').read_text(encoding='utf-8'))
    checks = dict(config['sha256'])
    checks['data/questions_test.json'] = manifest['test_sha256']
    checks['docs/selected-config.json'] = manifest['selection_sha256']
    for name, expected in checks.items():
        if sha(ROOT / name) != expected:
            raise SystemExit(f'Frozen file changed: {name}. Do not tune using test evidence.')
    parameters = config['baseline'] if args.configuration == 'baseline' else config
    command = [sys.executable, 'starter/openai_agent.py', '--chunks', 'data/day6_chunks_B.json',
               '--questions', 'data/questions_test.json', '--split', 'test', '--model', config['model'],
               '--citation-format', parameters['citation_format'], '--top-k', str(parameters['top_k']),
               '--budget', str(parameters['budget_chars']), '--max-searches', str(parameters['max_searches']),
               '--output', f'starter/results/agent-openai-test-{args.configuration}']
    print('Frozen hashes verified. Configuration:', args.configuration, flush=True)
    print(subprocess.list2cmdline(command), flush=True)
    if args.dry_run:
        return
    completed = subprocess.run(command, cwd=ROOT)
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
