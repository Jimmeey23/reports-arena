"""Orchestration: deterministic answers first, model only where it adds value.

Token discipline:

* questions the deterministic engine resolves cost zero tokens;
* the model only ever sees the compact metrics pack (~1-2k tokens) plus the
  last few turns - never raw rows;
* identical questions are served from the cache;
* every model reply is grounded: a number that does not exist in the pack is
  rejected, so answers cannot drift away from the computed metrics.
"""
from __future__ import annotations
import hashlib, json, re
from . import llm, qa
from .metrics_pack import token_estimate

MAX_HISTORY_TURNS = 4  # pairs kept in the prompt
CACHE_PREFIX = 'v1'


def _pack_text(pack):
    """The entire grounded context as a tiny plain-text block."""
    lines = [f"Studio: {pack.get('studio')} | Period: {pack.get('period')}"]
    for m in pack.get('metrics', []):
        name = m.get('label') or m.get('id', '').replace('_', ' ')
        detail = f" ({m['detail']})" if m.get('detail') else ''
        unit = m.get('unit', '')
        v = m.get('value')
        if unit == 'INR' and isinstance(v, (int, float)):
            v = f'₹{v:,.0f}'
        elif unit == '%' and isinstance(v, (int, float)):
            v = f'{v:.1f}%'
        lines.append(f'- {name}: {v}{detail} [{m.get("chapter", "")}]')
    for key, rows in (pack.get('tops') or {}).items():
        lines.append(f'top:{key} = ' + ' | '.join(str(r[0]) for r in rows))
    for c in pack.get('chapters', []):
        if c.get('summary'):
            lines.append(f'chapter:{c["id"]} = {c["summary"][:300]}')
        for r in (c.get('recs') or [])[:4]:
            lines.append(f'rec:{c["id"]} = {r}')
    return '\n'.join(lines)


def history_block(store, studio, exclude_rid=None, limit=3):
    """Compact digest of earlier persisted reviews for the same studio, so the
    assistant can answer period-comparison questions. A few headline KPIs per
    period - deliberately tiny to keep token cost near zero."""
    if not store or not studio:
        return ''
    try:
        rows = store.list_reports(studio=studio, limit=limit + 2)
    except Exception:
        return ''
    lines = []
    for r in rows:
        if exclude_rid and r.get('run_id') == exclude_rid:
            continue
        meta = r.get('meta') or {}
        bits = []
        for c in (meta.get('chapters') or []):
            if c.get('id') not in ('sales', 'class', 'lapse', 'leads'):
                continue
            for k in (c.get('kpis') or [])[:2]:
                if k.get('value'):
                    bits.append(f'{k.get("label", "")} {k.get("value")}')
        if bits:
            lines.append(f'- {meta.get("label", r.get("label", ""))}: ' + ' · '.join(bits[:6]))
        if len(lines) >= limit:
            break
    if not lines:
        return ''
    return 'EARLIER PERIODS (same studio, persisted reviews):\n' + '\n'.join(lines)


def _ground(reply, pack):
    """Reject model output that introduces numbers absent from the pack."""
    nums = set(re.findall(r'\d[\d,]*(?:\.\d+)?', reply))
    known = set()
    blob = json.dumps(pack, default=str)
    for n in re.findall(r'\d[\d,]*(?:\.\d+)?', blob):
        known.add(n)
        known.add(n.replace(',', ''))
    for n in nums:
        if len(re.sub(r'\D', '', n)) >= 3 and n not in known and n.replace(',', '') not in known:
            return False, n
    return True, None


def chat(question, pack, store, session_id, extra_context='', run_id=None):
    """Answer a question about the run. Returns dict(answer, mode, tokens, cached)."""
    q = question.strip()
    if not q:
        return dict(answer='Ask me about any metric in this review.', mode='none', tokens=0, cached=False)
    key = f'{CACHE_PREFIX}:{pack.get("studio","")}:{pack.get("period","")}:{hashlib.sha1(q.lower().encode()).hexdigest()}'
    hit = store.cache_get(key) if store else None
    if hit:
        return dict(**hit, cached=True)

    det = qa.answer(q, pack)
    history = store.history(session_id, MAX_HISTORY_TURNS) if store else []
    result = None

    if det.get('ok') and det.get('confidence', 0) >= 0.9:
        result = dict(answer=det['answer'], mode='deterministic', tokens=0,
                      chapters=det.get('chapters', []))
    elif llm.status()['configured']:
        hist = history_block(store, pack.get('studio'), exclude_rid=run_id)
        sys_prompt = (
            'You are the data assistant for a studio performance review. Answer ONLY from the '
            'METRICS block; never invent figures. Keep answers under 120 words, lead with the '
            'number, cite the chapter in square brackets. If the block lacks the data, say so.\n\n'
            'METRICS:\n' + _pack_text(pack) +
            (('\n\n' + hist + '\nUse EARLIER PERIODS only for comparisons; the current review is '
              'the METRICS block.') if hist else ''))
        msgs = [{'role': 'system', 'content': sys_prompt}]
        for h in history[-MAX_HISTORY_TURNS * 2:]:
            msgs.append({'role': h.get('role', 'user'), 'content': str(h.get('content', ''))[:400]})
        prompt = q
        if det.get('answer'):
            prompt += f"\n\n(Context the metrics engine already resolved: {det['answer'][:300]})"
        if extra_context:
            prompt += f'\n\n(Selected report content: {extra_context[:500]})'
        msgs.append({'role': 'user', 'content': prompt[:1600]})
        try:
            out = llm.complete(msgs, max_tokens=300)
            ok, bad = _ground(out['text'], pack)
            if ok:
                result = dict(answer=out['text'], mode='ai',
                              tokens=out['prompt_tokens'] + out['completion_tokens'],
                              chapters=det.get('chapters', []))
            else:
                result = dict(answer=(det.get('answer') or
                                      'I could not verify that against the computed metrics, so I am '
                                      'not going to guess. Ask about a headline metric or a chapter.'),
                              mode='deterministic', tokens=out['prompt_tokens'],
                              chapters=det.get('chapters', []))
        except llm.AIUnavailable as e:
            result = dict(answer=det.get('answer') or f'{e}', mode='deterministic', tokens=0,
                          chapters=det.get('chapters', []))
    else:
        result = dict(answer=det.get('answer') or
                      ('I could not resolve that from the computed metrics. Ask about a headline '
                       'figure (cash, fill, attendance, discounts, churn, leads), a top list, or a '
                       'chapter - or configure an AI key for free-form questions.'),
                      mode='deterministic', tokens=0, chapters=det.get('chapters', []))

    if store:
        store.save_message(session_id, 'user', q)
        store.save_message(session_id, 'assistant', result['answer'],
                           meta=dict(mode=result['mode'], tokens=result.get('tokens', 0)))
        if result['mode'] == 'deterministic' and det.get('ok'):
            store.cache_put(key, dict(answer=result['answer'], mode=result['mode'],
                                      tokens=0, chapters=result.get('chapters', [])))
    return dict(**result, cached=False)


# ------------------------------------------------------------------ editing
_DETERMINISTIC_EDITS = {
    'shorten': lambda h: re.sub(r'\s+', ' ', h).strip()[:max(120, int(len(h) * 0.55))].rsplit(' ', 1)[0] + '…',
    'tighten': lambda h: re.sub(r'\s+', ' ', h).strip(),
}


def _strip_tags(html):
    return re.sub(r'<[^>]+>', '', html)


def edit_element(instruction, current_html, pack):
    """Rewrite an existing element. Returns dict(html|error, mode, tokens)."""
    ins = (instruction or '').lower().strip()
    text = _strip_tags(current_html or '')
    for word, fn in _DETERMINISTIC_EDITS.items():
        if ins in (word, 'make it ' + word, 'please ' + word):
            return dict(html=fn(_strip_tags(current_html)), mode='deterministic', tokens=0)

    if not llm.status()['configured']:
        if 'shorten' in ins:
            return dict(html=_DETERMINISTIC_EDITS['shorten'](text), mode='deterministic', tokens=0)
        return dict(error='Editing with AI needs a key. Set P57_AI_KEY (or AI settings) - '
                          'manual editing works without one.')
    sys_prompt = ('You rewrite ONE fragment of a studio report. Rules: keep every number exactly as '
                  'given; add no new facts; output only the rewritten text, no markup, no preamble; '
                  'under 140 words.')
    try:
        out = llm.complete([
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': f'Instruction: {instruction[:220]}\n\nFragment: {text[:900]}'},
        ], max_tokens=420)
    except llm.AIUnavailable as e:
        return dict(error=str(e))
    nums_before = set(re.findall(r'[\d][\d,]*(?:\.\d+)?', text))
    nums_after = set(re.findall(r'[\d][\d,]*(?:\.\d+)?', out['text']))
    if nums_before and not (nums_before & nums_after) and len(nums_before) > 1:
        return dict(error='The rewrite dropped the figures in that block, so it was discarded.')
    return dict(html=out['text'].strip(), mode='ai',
                tokens=out['prompt_tokens'] + out['completion_tokens'])


def create_element(instruction, pack):
    """Create a small new block grounded in the pack. Returns dict(html, mode)."""
    det = qa.answer(instruction or '', pack)
    if not llm.status()['configured']:
        if det.get('ok'):
            return dict(html=f'<p>{det["answer"]}</p>', mode='deterministic', tokens=0)
        return dict(error='Creating with AI needs a key. Set P57_AI_KEY - or use the manual tools '
                          'to add and edit blocks yourself.')
    try:
        out = llm.complete([
            {'role': 'system',
             'content': 'You write ONE short paragraph (max 90 words) for a studio report using ONLY '
                        'figures from the METRICS block. Plain text, no markup, no preamble.'},
            {'role': 'user', 'content': f'Request: {instruction[:260]}\n\nMETRICS:\n{_pack_text(pack)}'},
        ], max_tokens=340)
    except llm.AIUnavailable as e:
        return dict(error=str(e))
    ok, _bad = _ground(out['text'], pack)
    if not ok:
        if det.get('ok'):
            return dict(html=f'<p>{det["answer"]}</p>', mode='deterministic', tokens=0)
        return dict(error='The generated text contained figures not in the computed metrics, so it '
                          'was discarded.')
    return dict(html=f'<p>{out["text"].strip()}</p>', mode='ai',
                tokens=out['prompt_tokens'] + out['completion_tokens'])


def context_estimate(pack):
    """Approximate tokens the pack costs when sent to a model."""
    return token_estimate(_pack_text(pack))
