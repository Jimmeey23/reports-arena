"""Deterministic question answering over a metrics pack.

Zero model tokens: the question is parsed into an intent plus entities, the
answer is assembled verbatim from the pack, and every reply cites the chapter
the number came from.  Only questions this engine cannot resolve are handed to
the model layer (see agent.py).
"""
from __future__ import annotations
import re
from .metrics_pack import ALIASES, DEFINITIONS

_STOP = {'what', 'whats', "what's", 'is', 'are', 'was', 'were', 'the', 'a', 'an', 'of', 'in', 'for',
         'at', 'to', 'me', 'tell', 'show', 'give', 'how', 'many', 'much', 'did', 'do', 'does',
         'we', 'our', 'studio', 'please', 'can', 'you', 'there', 'this', 'that', 'month'}


def _norm(q):
    return re.sub(r'[^a-z0-9 %₹.-]', ' ', q.lower()).strip()


def _has(q, *words):
    """Word-boundary keyword test (avoids 'action' matching 'transactions')."""
    return any(re.search(r'\b' + re.escape(w) + r'\b', q) for w in words)


def _find_metric(q):
    """Return the best-matching metric id for the question text."""
    best, best_hits = None, 0
    for mid, aliases in ALIASES.items():
        hits = sum(1 for a in aliases if a in q)
        if hits > best_hits:
            best, best_hits = mid, hits
    return best


def _metric_by_id(pack, mid):
    for m in pack.get('metrics', []):
        if m.get('id') == mid:
            return m
    return None


def _fmt(m):
    v = m.get('value')
    if m.get('unit') == 'INR' and isinstance(v, (int, float)):
        return f'₹{v:,.0f}'
    if m.get('unit') == '%' and isinstance(v, (int, float)):
        return f'{v:.1f}%'
    if isinstance(v, float):
        return f'{v:,.1f}'
    if isinstance(v, int):
        return f'{v:,}'
    return str(v)


def _chapter(pack, cid):
    for c in pack.get('chapters', []):
        if c['id'] == cid:
            return c
    return None


def _reply(text, chapters=(), metrics=(), confidence=1.0):
    return dict(ok=True, answer=text, chapters=list(chapters), metrics=list(metrics),
                mode='deterministic', confidence=confidence)


def _miss(pack, q):
    hints = [m.get('label') or m.get('id') for m in pack.get('metrics', [])][:12]
    return dict(ok=False, mode='deterministic', confidence=0.0,
                answer='', hints=hints)


# ------------------------------------------------------------------ intents
def _answer_metric(pack, mid, compare):
    m = _metric_by_id(pack, mid)
    if not m:
        return None
    label = m.get('label') or DEFINITIONS.get(mid, mid).split(':')[0].split('.')[0]
    name = label if isinstance(label, str) else mid.replace('_', ' ')
    text = f"{name.title()} for {pack.get('studio','')} in {pack.get('period','')}: {_fmt(m)}"
    if m.get('detail'):
        text += f" ({m['detail'].strip()})"
    text += '.'
    if compare:
        text += ' The detail shown includes the prior-year comparison where the data carries one.'
    if mid in DEFINITIONS:
        text += f" Definition: {DEFINITIONS[mid]}"
    return _reply(text, [m.get('chapter')], [mid])


def _answer_top(pack, q):
    tops = pack.get('tops', {})
    if any(w in q for w in ('product', 'package', 'membership sold')):
        key, label = 'products_by_sold', 'Top products by memberships sold'
    elif 'trainer' in q or 'instructor' in q or 'teacher' in q:
        key, label = 'trainers_by_revenue', 'Top trainers by class revenue'
    elif 'format' in q or 'class type' in q:
        key, label = 'formats_by_attendance', 'Top class formats by attendance'
    elif 'categor' in q:
        key, label = 'categories', 'Top sale categories by cash'
    else:
        return None
    rows = tops.get(key)
    if not rows:
        return None
    lines = [f'{label}, {pack.get("period","")}:']
    for i, r in enumerate(rows, 1):
        if key == 'trainers_by_revenue':
            lines.append(f'{i}. {r[0]} — ₹{r[1]:,.0f} revenue, {r[2]:.1f}% utilisation')
        elif key == 'formats_by_attendance':
            lines.append(f'{i}. {r[0]} — {r[1]:,} attendances, {r[2]:.1f}% fill')
        elif key == 'categories':
            lines.append(f'{i}. {r[0]} — ₹{r[1]:,.0f}')
        else:
            lines.append(f'{i}. {r[0]} — {r[1]:,} sold')
    ch = {'products_by_sold': 'lapse', 'trainers_by_revenue': 'instructor',
          'formats_by_attendance': 'format', 'categories': 'sales'}[key]
    return _reply('\n'.join(lines), [ch], [])


def _answer_definition(pack, q):
    def compose(mid):
        text = f'{mid.replace("_", " ").title()}: {DEFINITIONS[mid]}'
        m = _metric_by_id(pack, mid)
        if m:
            text += f" This run: {_fmt(m)}"
            if m.get('detail'):
                text += f" ({m['detail'].strip()})"
            text += '.'
            return _reply(text, [m.get('chapter')], [mid])
        return _reply(text, [], [mid])
    for mid, aliases in ALIASES.items():
        if any(a in q for a in aliases) and mid in DEFINITIONS:
            return compose(mid)
    for mid in DEFINITIONS:
        if mid.replace('_', ' ') in q:
            return compose(mid)
    return None


def _answer_chapter(pack, q, kind):
    """Why/how explanations and recommendations, straight from the chapter."""
    topic_map = {
        'sales': ['sales', 'cash', 'revenue', 'discount', 'buyer', 'transaction', 'money'],
        'class': ['class', 'session', 'capacity', 'fill', 'utilisation', 'schedule', 'timetable', 'room'],
        'instructor': ['trainer', 'instructor', 'teacher', 'staff', 'roster'],
        'lapse': ['lapse', 'churn', 'retention', 'member', 'renew', 'cancel'],
        'format': ['format', 'barre', 'cycle', 'programme', 'program'],
        'cancels': ['cancellation', 'late cancel', 'no-show', 'no show', 'discount code'],
        'leads': ['lead', 'pipeline', 'trial', 'enquiry', 'inquiry', 'marketing', 'channel'],
        'behaviour': ['behaviour', 'behavior', 'attendance', 'visit', 'frequency', 'habit'],
        'overview': ['overall', 'summary', 'big picture', 'everything'],
    }
    cid = max(topic_map, key=lambda c: sum(1 for w in topic_map[c] if w in q))
    ch = _chapter(pack, cid) or (pack.get('chapters') or [{}])[0]
    if kind == 'recs':
        recs = ch.get('recs') or []
        if not recs:
            return None
        lines = [f'Recommended actions from "{ch.get("title", cid)}":']
        lines += [f'{i}. {r}' for i, r in enumerate(recs[:6], 1)]
        return _reply('\n'.join(lines), [ch.get('id')], [])
    if ch.get('summary'):
        text = ch['summary']
        if ch.get('facts'):
            text += '\n\nKey facts:\n' + '\n'.join('- ' + f for f in ch['facts'][:4])
        return _reply(text, [ch.get('id')], [], confidence=0.9)
    return None


def _answer_overview(pack):
    bits = []
    for mid in ('cash', 'fill', 'sessions', 'transactions'):
        m = _metric_by_id(pack, mid)
        if m:
            bits.append(f"{(m.get('label') or mid).lower()}: {_fmt(m)}")
    if not bits:
        return None
    text = (f"{pack.get('studio','')} — {pack.get('period','')}. " + '; '.join(bits) + '.')
    chs = [c['id'] for c in pack.get('chapters', [])]
    return _reply(text, chs[:4], [m['id'] for m in pack.get('metrics', [])][:0])


# ------------------------------------------------------------------ entry
_MONTHS = {'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april',
           'may': 'may', 'jun': 'june', 'jul': 'july', 'aug': 'august',
           'sep': 'september', 'oct': 'october', 'nov': 'november', 'dec': 'december'}


def _kpi_match(q, lab):
    """Score a KPI label against the question: every significant label word must
    be present (month abbreviations like 'Sep' match the full month name, and a
    generic 'the period / this month' matches the report's own month)."""
    month_words = set(_MONTHS) | set(_MONTHS.values())
    words = [w for w in re.split(r'\s+', lab.strip()) if len(w) > 1 and w not in ('in', 'of', 'the', 'for', 'and')]
    if not words:
        return 0
    q_months = {m for m in _MONTHS.values() if re.search(r'\b' + m + r'\b', q)}
    generic_period = not q_months and bool(re.search(r'\b(period|month)\b', q))
    hits = 0
    for w in words:
        if w in month_words:
            full = _MONTHS.get(w, w)
            if full in q_months:
                hits += 1
            elif generic_period:
                hits += 1
            elif re.search(r'\b' + re.escape(full[:3]), q):
                hits += 1
        elif (re.search(r'\b' + re.escape(w) + r'\b', q)
                or (len(w) > 3 and re.search(r'\b' + re.escape(w[:3]), q))):
            hits += 1
    return hits if hits == len(words) else 0


def answer(question, pack):
    q = _norm(question)
    if not q or not pack:
        return _miss(pack or {}, q)

    compare = _has(q, 'last year', 'previous year', 'vs', 'versus', 'compare', 'yoy', 'year on year', 'change', 'growth', 'trend')
    if _has(q, 'how is', 'how are', 'definition', 'calculated', 'what does', 'formula', 'measure'):
        r = _answer_definition(pack, q)
        if r:
            return r
    if _has(q, 'recommend', 'recommendation', 'recommendations', 'actions', 'what should', 'how do we fix', 'improve', 'advice'):
        r = _answer_chapter(pack, q, 'recs')
        if r:
            return r
    if _has(q, 'why', 'explain', 'reason', 'driver', 'cause', 'what happened', 'summary', 'summarise', 'summarize', 'overview', 'highlights', 'tell me about'):
        if _has(q, 'summary', 'summarise', 'summarize', 'overview', 'highlights', 'tell me about') and not _has(q, 'why', 'explain', 'reason'):
            r = _answer_overview(pack)
            if r:
                return r
        r = _answer_chapter(pack, q, 'why')
        if r:
            return r
    if _has(q, 'top', 'best', 'highest', 'biggest', 'largest'):
        r = _answer_top(pack, q)
        if r:
            return r
        r = _answer_chapter(pack, q, 'why')
        if r:
            return r
    mid = _find_metric(q)
    if mid:
        r = _answer_metric(pack, mid, compare)
        if r:
            return r
    # KPI-label fallback: match against the run's displayed KPI labels, both in
    # the flat metric list and in each chapter's KPI cards (where the new
    # period-scoped figures such as "Churned in Sep" live).
    candidates = []
    for m in pack.get('metrics', []):
        if m.get('label'):
            candidates.append((m.get('label'), m.get('value'), m.get('detail'), m.get('chapter')))
    for c in pack.get('chapters', []):
        for k in c.get('kpis', []):
            candidates.append((k.get('label'), k.get('value'), k.get('detail'), c.get('id')))
    best = None
    for lab, val, detail, chap in candidates:
        lab = (lab or '').lower()
        if not lab or val in (None, ''):
            continue
        score = _kpi_match(q, lab)
        if score and (best is None or score > best[0]):
            best = (score, lab, val, detail, chap)
    if best:
        _, lab, val, detail, chap = best
        text = f"{lab} for {pack.get('studio','')} in {pack.get('period','')}: {val}"
        if detail:
            text += f" ({detail})"
        return _reply(text + '.', [chap], [])
    return _miss(pack, q)
