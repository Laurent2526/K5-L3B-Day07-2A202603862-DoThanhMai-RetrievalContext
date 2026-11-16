"""Small live API probes; prints no credentials, prompts or model answers."""
import os
from urllib.parse import urlsplit

from openai_agent import SEARCH, FINISH, create_client, error_details, redact


def probe(label, operation):
    print(f'\n{label}', flush=True)
    try:
        response = operation()
        print(f'OK: id={getattr(response, "id", "n/a")}, model={getattr(response, "model", "n/a")}', flush=True)
        return True
    except Exception as error:
        import json
        details = error_details(error)
        response = getattr(error, 'response', None)
        if response is not None:
            details['body_bytes'] = len(response.content)
            details['content_type'] = response.headers.get('content-type')
            details['server'] = response.headers.get('server')
        print(type(error).__name__, json.dumps(details, ensure_ascii=True), flush=True)
        return False


def main():
    print('Diagnostic version: 4 (authorization header comparison)', flush=True)
    print('Script:', __file__, flush=True)
    if not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('Set OPENAI_API_KEY first')
    model = os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini')
    client = create_client(timeout=30)
    endpoint = urlsplit(str(client.base_url))
    print(f'Endpoint: {endpoint.hostname}{endpoint.path}; model: {model}')
    print('Force IPv4:', os.environ.get('OPENAI_FORCE_IPV4') == '1')
    print('Key has whitespace:', any(c.isspace() for c in os.environ['OPENAI_API_KEY']))
    key = os.environ['OPENAI_API_KEY']
    print('Key checks (no key printed):', {
        'characters': len(key), 'ascii_only': key.isascii(),
        'starts_with_sk_dash': key.startswith('sk-'),
        'contains_quote': any(c in key for c in ('"', "'", '`'))})
    print('Proxy environment variables set:', ', '.join(
        name for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'OPENAI_BASE_URL')
        if os.environ.get(name)) or '(none)')
    import httpx
    transport = httpx.HTTPTransport(local_address='0.0.0.0') if os.environ.get('OPENAI_FORCE_IPV4') == '1' else None
    print('\n0a. Python HTTPS without API key (expect 401 JSON)', flush=True)
    try:
        with httpx.Client(transport=transport, timeout=20) as network_client:
            response = network_client.get('https://api.openai.com/v1/models')
            print(f'HTTP {response.status_code}; body_bytes={len(response.content)}; '
                  f'content_type={response.headers.get("content-type")}; '
                  f'request_id={response.headers.get("x-request-id")}', flush=True)
            print('\n0a1. Dummy Bearer value (not your key; expect authentication error)', flush=True)
            dummy = network_client.get('https://api.openai.com/v1/models',
                headers={'Authorization': 'Bearer diagnostic-invalid-key'})
            print(f'HTTP {dummy.status_code}; body_bytes={len(dummy.content)}; '
                  f'content_type={dummy.headers.get("content-type")}; '
                  f'request_id={dummy.headers.get("x-request-id")}', flush=True)
            print('\n0a2. Direct HTTP authentication without OpenAI SDK', flush=True)
            response = network_client.get('https://api.openai.com/v1/models',
                headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY']})
            print(f'HTTP {response.status_code}; body_bytes={len(response.content)}; '
                  f'content_type={response.headers.get("content-type")}; '
                  f'request_id={response.headers.get("x-request-id")}', flush=True)
            if response.status_code >= 400:
                print('Error body:', redact(response.text) or '(empty)', flush=True)
    except Exception as error:
        print(type(error).__name__, flush=True)
    print('Optional SDK headers configured:', ', '.join(
        name for name in ('OPENAI_ORG_ID', 'OPENAI_PROJECT_ID') if os.environ.get(name)) or '(none)')
    if not probe('0b. API key authentication: list models (no text generation)', client.models.list):
        print('Stopped: resolve authentication/network before generation requests.')
        client.close()
        return
    ok = probe('1. Responses API: minimal text request',
               lambda: client.responses.create(model=model, input='Reply with OK.', store=False))
    if ok:
        probe('2. Responses API: agent tool schema',
              lambda: client.responses.create(
                  model=model, input='Search the corpus for the year OSHA was passed.',
                  tools=[SEARCH, FINISH], parallel_tool_calls=False,
                  tool_choice={'type': 'function', 'name': 'search'}, store=False))
    else:
        probe('2. Chat Completions: minimal text request',
              lambda: client.chat.completions.create(
                  model=model, messages=[{'role': 'user', 'content': 'Reply with OK.'}]))
    client.close()


if __name__ == '__main__':
    main()
