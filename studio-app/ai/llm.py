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
import json, os, urllib.request, urllib.error, hashlib, threading, time
from collections import OrderedDict

DEFAULT_MODEL = 'gpt-4o-mini'
DEFAULT_BASE = 'https://api.openai.com/v1/chat/completions'

# Runtime override (set through /api/ai/key); env remains the source of truth
# on restart. The endpoint is deliberately not overridable at runtime: the key
# travels to it as a Bearer token.
_runtime = dict(key=None, model=None)


class AIUnavailable(RuntimeError):
    pass


def configure(key=None, model=None):
    if key is not None:
        _runtime['key'] = key.strip() or None
    if model is not None:
        _runtime['model'] = model.strip() or None


def status():
    key = _runtime['key'] or os.environ.get('OPENAI_API_KEY', '').strip()
    return dict(configured=bool(key),
                model=_runtime['model'] or os.environ.get('P57_AI_MODEL') or DEFAULT_MODEL,
                base=os.environ.get('P57_AI_BASE') or DEFAULT_BASE)


def _request(messages, max_tokens=320, temperature=0.2, timeout=45, cfg=None, credential=None):
    """One chat completion. Returns the text; raises AIUnavailable if no key
    or the provider is unreachable."""
    cfg = cfg or status()
    if not cfg['configured']:
        raise AIUnavailable('No AI key is configured. Set OPENAI_API_KEY or use the AI settings in the app.')
    body = json.dumps(dict(model=cfg['model'], messages=messages,
                           max_tokens=max_tokens, temperature=temperature)).encode()
    req = urllib.request.Request(cfg['base'], data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (credential or _runtime['key'] or os.environ.get('OPENAI_API_KEY', '').strip()),
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
    if data['choices'][0].get('finish_reason') == 'length':
        raise AIUnavailable('The provider returned an incomplete generation. It has not been saved or cached; retry with a smaller component.')
    if not text:
        raise AIUnavailable('The provider returned an empty generation.')
    usage = data.get('usage', {})
    return dict(text=text,
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                cached_prompt_tokens=usage.get('prompt_tokens_details', {}).get('cached_tokens', 0))


# Exact-input reuse preserves the complete output and model settings. Never
# reuse across a changed evidence pack, instruction, model or credential.
_cache = OrderedDict()
_flights = {}
_lock = threading.Lock()
CACHE_TTL = 86400
CACHE_LIMIT = 128


def complete(messages, max_tokens=320, temperature=0.2, timeout=45, key_override=None, model_override=None, base_override=None):
    cfg = status()
    credential = key_override or _runtime['key'] or os.environ.get('OPENAI_API_KEY', '').strip()
    if model_override: cfg['model'] = model_override
    if base_override: cfg['base'] = base_override
    cfg['configured'] = bool(credential)
    if not credential:
        raise AIUnavailable('No AI key is configured.')
    identity = [cfg, hashlib.sha256(credential.encode()).hexdigest(), messages, max_tokens, temperature]
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    with _lock:
        entry = _cache.get(key)
        if entry and time.monotonic() - entry[0] < CACHE_TTL:
            _cache.move_to_end(key)
            return dict(entry[1], cached=True, prompt_tokens=0, completion_tokens=0, _cache_key=key)
        flight = _flights.get(key)
        owner = flight is None
        if owner:
            flight = {'event': threading.Event()}
            _flights[key] = flight
    if not owner:
        if not flight['event'].wait(timeout + 5):
            raise AIUnavailable('An identical generation is still running. Try again shortly.')
        if 'error' in flight:
            raise AIUnavailable(str(flight['error']))
        return dict(flight['result'], cached=True, prompt_tokens=0, completion_tokens=0, _cache_key=key)
    try:
        result = _request(messages, max_tokens, temperature, timeout, cfg, credential)
        with _lock:
            _cache[key] = (time.monotonic(), result)
            while len(_cache) > CACHE_LIMIT:
                _cache.popitem(last=False)
            flight['result'] = result
        return dict(result, cached=False, _cache_key=key)
    except Exception as error:
        flight['error'] = error
        raise
    finally:
        with _lock:
            _flights.pop(key, None)
            flight['event'].set()


def discard(result):
    """Remove a transport-successful response rejected by grounding checks."""
    with _lock:
        _cache.pop(result.get('_cache_key'), None)
