"""Compact metric snapshot for one generated run.

The pack is the *only* context the assistant ever receives: a few kilobytes of
headline numbers, definitions and top-lists distilled from the engine's
Metrics object (at build time) or from the run's manifest (on demand).  Raw
rows never enter a prompt, which keeps answers cheap and grounded.
"""
from __future__ import annotations
import json, os

# Atlas metric dictionary - the calculation each headline number follows.
DEFINITIONS = {
    'cash': 'Collected cash: successful, non-voided payments summed on their payment date.',
    'transactions': 'Distinct sale IDs among successful, non-voided payments (not item rows).',
    'buyers': 'Distinct paying members in the period.',
    'aov': 'Average order value = collected cash / distinct transactions.',
    'ticket': 'Average spend per buyer = collected cash / distinct buyers.',
    'discount_rate': 'Item-level discounts / (collected cash + item-level discounts).',
    'sessions': 'Class occurrences on the timetable in the period.',
    'seats': 'Sum of class capacity across sessions.',
    'fill': 'Capacity utilisation = attended seats / seats offered (aggregate, never an average of per-class rates).',
    'show_up': 'Show-up rate = attended / booked.',
    'late_cancel_rate': 'Late cancellations / booked seats.',
    'no_show_rate': '(booked - attended - late cancellations) / booked.',
    'avg_class_size': 'Attendances / sessions.',
    'rev_per_session': 'Class-attributed revenue / sessions.',
    'rev_per_attendee': 'Class-attributed revenue / attendances.',
    'conversion': 'Converted newcomers / newcomers (explicit Is-New labels only).',
    'second_visit': 'Newcomers with at least one visit after their first.',
    'retention': 'Retained members / selected-month membership-purchase cohort. Status reflects the uploaded export.',
    'churn': 'Rows carrying a churned date / selected-month membership-purchase cohort. Status reflects the uploaded export.',
    'median_life': 'Median observed days through reporting month-end; open purchases are right-censored. This is not median completed lifetime.',
    'teaching_hours': 'Sum of session durations, counted once per valid attended session.',
    'lead_win': 'Leads with status Won / all leads.',
}

ALIASES = {
    'cash': ['cash', 'revenue', 'takings', 'collections', 'money taken', 'sales value', 'money'],
    'transactions': ['transactions', 'txns', 'sales count', 'number of sales', 'payments'],
    'buyers': ['buyers', 'paying members', 'customers', 'payers', 'unique buyers'],
    'aov': ['aov', 'average order', 'average sale', 'average transaction', 'ticket size', 'average ticket'],
    'discount_rate': ['discount rate', 'discount depth', 'depth', 'discounts given', 'discount'],
    'sessions': ['sessions', 'classes run', 'classes held', 'classes', 'timetable'],
    'seats': ['seats', 'capacity', 'seats offered'],
    'fill': ['fill', 'utilisation', 'utilization', 'occupancy', 'fill rate', 'capacity utilisation'],
    'show_up': ['show up', 'show-up', 'showup', 'attendance rate'],
    'late_cancel_rate': ['late cancel', 'late cancellations', 'late cancellation rate', 'cancellations'],
    'no_show_rate': ['no show', 'no-show', 'no shows'],
    'avg_class_size': ['class size', 'average class size', 'average attendance'],
    'rev_per_session': ['revenue per class', 'rev per class', 'revenue per session'],
    'rev_per_attendee': ['revenue per attendee', 'rev per head', 'revenue per head', 'yield'],
    'conversion': ['conversion', 'convert', 'conversion rate', 'new client conversion'],
    'second_visit': ['second visit', 'return visit', 'retention of new', 'came back'],
    'retention': ['retention', 'retained'],
    'churn': ['churn', 'churned', 'lapsed', 'lost members'],
    'median_life': ['median life', 'membership life', 'how long memberships last', 'median membership'],
    'lead_win': ['win rate', 'leads won', 'lead conversion', 'lead win'],
    'attendances': ['attendances', 'attendance', 'visits', 'check-ins', 'checkins', 'people attending'],
}


def _f(x, nd=0):
    try:
        return round(float(x), nd)
    except Exception:
        return None


def _inr(x):
    x = _f(x)
    return f'₹{x:,}' if x is not None else '—'


def from_metrics(M, chapters):
    """Build a pack from a live engine Metrics object (richest form)."""
    y = M.y
    S = M.sales.get(y, {}); P = M.sales.get(y - 1, {})
    F = M.room.get(y, {}); FP = M.room.get(y - 1, {})
    metrics = []

    def add(mid, value, detail='', unit='', chapter='overview'):
        if value is None:
            return
        metrics.append(dict(id=mid, value=value, detail=detail, unit=unit, chapter=chapter))

    if S:
        add('cash', _f(S.get('cash')), f"prior year {_inr(P.get('cash'))}", 'INR', 'sales')
        add('transactions', S.get('txn'), f"{S.get('lines')} sale lines", 'count', 'sales')
        add('buyers', S.get('buyers'), '', 'count', 'sales')
        add('aov', _f(S.get('aov')), '', 'INR', 'sales')
        add('ticket', _f(S.get('ticket')), '', 'INR', 'sales')
        add('discount_rate', _f(S.get('depth'), 1), f"discount value {_inr(S.get('disc'))}", '%', 'sales')
    if F:
        add('sessions', F.get('sessions'), f"prior year {FP.get('sessions')}", 'count', 'class')
        add('seats', _f(F.get('seats')), '', 'count', 'class')
        add('attendances', _f(F.get('att')), '', 'count', 'class')
        add('fill', _f(F.get('fill'), 1), f"prior year {_f(FP.get('fill'), 1)}%", '%', 'class')
        add('show_up', _f(F.get('conv'), 1), '', '%', 'class')
        add('late_cancel_rate', _f(F.get('lc_rate'), 1), f"{_f(F.get('lc'))} late cancellations", '%', 'class')
        add('no_show_rate', _f(F.get('noshow_rate'), 1), '', '%', 'class')
        add('avg_class_size', _f(F.get('classavg'), 1), '', 'people', 'class')
        add('rev_per_session', _f(F.get('rpc')), '', 'INR', 'class')
        add('rev_per_attendee', _f(F.get('rph')), '', 'INR', 'class')
        add('revenue_class', _f(F.get('rev')), 'class-attributed, attended sessions', 'INR', 'class')
    led = getattr(M, 'led', None)
    if led:
        add('memberships', led.get('rows'), f"{led.get('paid')} paid", 'count', 'lapse')
    if getattr(M, 'median_life', None) is not None:
        add('median_life', _f(M.median_life), 'Median observed days through month-end, not completed lifetime', 'days', 'lapse')
    lf = getattr(M, 'lead_fun', None)
    if lf:
        won = lf.get('won'); leads = lf.get('leads')
        add('leads', leads, '', 'count', 'leads')
        if leads:
            add('lead_win', _f(won / leads * 100, 1), f"{won} won", '%', 'leads')

    pack = dict(
        studio=getattr(M, 'studio', ''), period=getattr(M, 'label', ''),
        year=getattr(M, 'y', None), month=getattr(M, 'm', None),
        metrics=metrics, definitions=DEFINITIONS,
        chapters=[dict(id=c['id'], title=c['title'], summary=c.get('summary', ''),
                       kpis=c.get('kpis', []), facts=c.get('facts', []),
                       recs=[r[1] for r in c.get('recs', []) if isinstance(r, (list, tuple)) and len(r) > 1])
                  for c in chapters],
        tops=_tops(M))
    return pack


def _tops(M):
    """Small top-lists the assistant is allowed to quote."""
    out = {}
    try:
        if getattr(M, 'cats', None) is not None and len(M.cats):
            out['categories'] = [(str(i), _f(r['sum'])) for i, r in M.cats.head(5).iterrows()]
    except Exception:
        pass
    try:
        t = getattr(M, 'trainers', None)
        if t is not None and len(t):
            out['trainers_by_revenue'] = [(str(i), _f(r['rev']), _f(r['fill'], 1))
                                          for i, r in t.head(5).iterrows()]
    except Exception:
        pass
    try:
        f = getattr(M, 'formats', None)
        if f is not None and len(f):
            out['formats_by_attendance'] = [(str(i), int(r['att']), _f(r['fill'], 1))
                                            for i, r in f.head(5).iterrows()]
    except Exception:
        pass
    try:
        p = getattr(M, 'products', None)
        if p is not None and len(p):
            out['products_by_sold'] = [(str(i), int(r['sold'])) for i, r in p.head(5).iterrows()]
    except Exception:
        pass
    return out


LABEL_TO_CANONICAL = {
    'cash taken': 'cash', 'cash': 'cash', 'revenue': 'cash',
    'transactions': 'transactions', 'buyers': 'buyers', 'paying members': 'buyers',
    'average sale': 'aov', 'average buyer spend': 'ticket', 'average ticket': 'ticket',
    'discount given': 'discount_rate', 'discounts': 'discount_rate', 'discount value': 'discount_rate',
    'classes run': 'sessions', 'classes': 'sessions', 'sessions': 'sessions',
    'seats offered': 'seats', 'attendances': 'attendances', 'attendance': 'attendances',
    'capacity utilisation': 'fill', 'utilisation': 'fill', 'fill rate': 'fill',
    'average class size': 'avg_class_size', 'revenue per class': 'rev_per_session',
    'revenue per attendee': 'rev_per_attendee', 'show-up rate': 'show_up',
    'late-cancellation rate': 'late_cancel_rate', 'late cancellations': 'late_cancel_rate',
    'no-show rate': 'no_show_rate', 'median membership life': 'median_life',
    'conversion rate': 'conversion', 'new clients': 'conversion',
}


def from_manifest(manifest):
    """Fallback pack derived from a run's manifest.json (no live Metrics)."""
    metrics = []
    for c in manifest.get('chapters', []):
        for k in c.get('kpis', []):
            label = str(k.get('label', ''))
            mid = LABEL_TO_CANONICAL.get(label.lower()) or c['id'] + ':' + label
            metrics.append(dict(id=mid, label=label,
                                value=k.get('value'), detail=k.get('detail', ''), chapter=c['id']))
    # A reviewed source attachment can supersede an older generated population.
    # Keep fallback answers identical to the reconciled pack even if metrics.json
    # is absent on deployment. Overrides are frozen in the reviewed manifest.
    overrides = manifest.get('source_reconciliation', {}).get('metric_overrides', [])
    ids = {m['id'] for m in overrides}
    metrics = [m for m in metrics if m['id'] not in ids] + overrides
    return dict(
        studio=manifest.get('studio', ''), period=manifest.get('label', ''),
        year=manifest.get('year'), month=manifest.get('month'),
        metrics=metrics, definitions=DEFINITIONS,
        chapters=[dict(id=c['id'], title=c['title'], summary=c.get('summary', ''),
                       kpis=c.get('kpis', []), facts=c.get('facts', []),
                       recs=[r[1] for r in c.get('recs', []) if isinstance(r, (list, tuple)) and len(r) > 1])
                  for c in manifest.get('chapters', [])],
        tops={})


def pack_path(runs_dir, rid):
    return os.path.join(runs_dir, rid, 'metrics.json')


def load_pack(runs_dir, rid, manifest=None):
    """Load a run's pack, rebuilding the fallback from the manifest when the
    build-time snapshot is missing (older runs)."""
    p = pack_path(runs_dir, rid)
    if os.path.isfile(p):
        try:
            with open(p, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    if manifest is None:
        mf = os.path.join(runs_dir, rid, 'manifest.json')
        if not os.path.isfile(mf):
            return None
        with open(mf, encoding='utf-8') as f:
            manifest = json.loads(f.read())
    return from_manifest(manifest)


def dump(pack, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pack, f, ensure_ascii=False, separators=(',', ':'), default=str)


def token_estimate(text):
    """Rough token count used for budgeting (4 chars per token heuristic)."""
    return max(1, len(text) // 4)
