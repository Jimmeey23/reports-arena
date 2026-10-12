"""Provider-agnostic OpenAI-compatible chat client (standard library only).

Configuration via environment:

    OPENAI_API_KEY      API key (also settable at runtime through /api/ai/key)
    P57_AI_MODEL    model name, default gpt-4o-mini
    P57_AI_BASE     chat-completions base URL,
                    default https://api.openai.com/v1/chat/completions

The layer never invents numbers: callers pass grounded context and the reply is
checked before use.  Without a key every call raises AIUnavailable and the
agent falls back to the deterministic engine.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error

DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_BASE = 'https://api.openai.com/v1/chat/completions'

# Runtime override (set through /api/ai/key); env remains the source of truth
# on restart.
_runtime = dict(key=None, model=None, base=None)


class AIUnavailable(RuntimeError):
    pass


def configure(key=None, model=None, base=None):
    if key is not None:
        _runtime['key'] = key.strip() or None
    if model is not None:
        _runtime['model'] = model.strip() or None
    if base is not None:
        _runtime['base'] = base.strip() or None


def status():
    key = _runtime['key'] or os.environ.get('OPENAI_API_KEY', '').strip()
    return dict(configured=bool(key),
                model=_runtime['model'] or os.environ.get('P57_AI_MODEL') or DEFAULT_MODEL,
                base=_runtime['base'] or os.environ.get('P57_AI_BASE') or DEFAULT_BASE)


def complete(messages, max_tokens=320, temperature=0.2, timeout=45):
    """One chat completion. Returns the text; raises AIUnavailable if no key
    or the provider is unreachable."""
    cfg = status()
    if not cfg['configured']:
        raise AIUnavailable('No AI key is configured. Set OPENAI_API_KEY or use the AI settings in the app.')
    body = json.dumps(dict(model=cfg['model'], messages=messages,
                           max_tokens=max_tokens, temperature=temperature)).encode()
    req = urllib.request.Request(cfg['base'], data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (_runtime['key'] or os.environ.get('OPENAI_API_KEY', '').strip()),
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            data = json.loads(res.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        raise AIUnavailable(f'AI provider error {e.code}: {e.read()[:160]!r}') from e
    except Exception as e:
        raise AIUnavailable(f'AI provider unreachable: {e}') from e
    try:
        text = data['choices'][0]['message']['content'].strip()
    except Exception:
        raise AIUnavailable('Unexpected AI response shape')
    usage = data.get('usage', {})
    return dict(text=text,
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0))
