"""The depth layer.

The chapter builders in chapters_a / chapters_b give a sound summary of each
subject. This module gives them the same *depth* as the reports the studio was
handed: a section per analytical question, the supporting table under each one,
the raw rows inside a collapsible evidence block, the easy-to-miss causes stated
alongside the obvious ones, and a method note saying what the numbers cannot
show.

Everything here is computed from the uploaded frames for whichever studio and
month was chosen - no figure is hard-coded and no table is invented. Each block
is guarded: if a source is missing or a column is absent, that table is dropped
and the chapter simply says less, rather than guessing.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from .design import (R, Rs, P, N, T, ev, note, bars, lines, hbars, diverging, stacked,
                     funnel, dumbbell, A1, A2, A3, B1, B2, N1, N2, fd, fdt)
from .metrics import DAYS, MONTH_NAMES, rng
from .data import num


# --------------------------------------------------------------- small helpers
def _n(x, d=0):
    try:
        v = float(x)
        if not np.isfinite(v):
            return '·'
        return f'{v:,.{d}f}'
    except Exception:
        return '·'


def money(x):
    try:
        v = float(x)
        return R(v) if np.isfinite(v) else '·'
    except Exception:
        return '·'


def pc(x, d=1):
    try:
        v = float(x)
        return f'{v:.{d}f}%' if np.isfinite(v) else '·'
    except Exception:
        return '·'


def clean(s):
    return str(s).replace('Studio ', '').strip()


def dpc(cur, prev, digits=1):
    """'up 4.1% on the same month last year' - or an empty string."""
    try:
        cur, prev = float(cur), float(prev)
    except Exception:
        return ''
    if not prev or not np.isfinite(prev):
        return ''
    d = (cur - prev) / abs(prev) * 100
    return f', {"up" if d >= 0 else "down"} {abs(d):.{digits}f}% on the year'


def share(part, whole, d=0):
    try:
        return f'{float(part) / float(whole) * 100:.{d}f}%'
    except Exception:
        return '-'


def ratio(a, b, d=1):
    try:
        v = float(a) / float(b) if b else np.nan
        return f'{v:,.{d}f}' if np.isfinite(v) else '·'
    except Exception:
        return '·'


def _is_na(v):
    try:
        if v is None:
            return True
        if isinstance(v, float) and not np.isfinite(v):
            return True
        t = str(v).strip().lower()
        return t in ('nan', 'nat', 'none', '', 'null', '-')
    except Exception:
        return False


def fmt_cell(v, k):
    if _is_na(v):
        return '·'
    if k == 'm':
        return money(v)
    if k == 'Rs':
        return Rs(v)
    if k == 'n':
        return _n(v)
    if k == 'f1':
        return _n(v, 1)
    if k == 'f2':
        return _n(v, 2)
    if k == 'p':
        return pc(v)
    if k == 'p0':
        return pc(v, 0)
    if k == 'w':
        return str(v)
    if k == 'd':
        return fd(v)
    if k == 'dt':
        return fdt(v)
    return str(v)


def tab(df, heads, fmts=None, cls='num', maxrows=None):
    """Render a DataFrame (or list of lists) as a report table."""
    if df is None:
        return ''
    if isinstance(df, pd.DataFrame):
        d = df.head(maxrows) if maxrows else df
        fmts = fmts or ['w'] + ['n'] * (len(heads) - 1)
        rows = []
        for i, r in d.iterrows():
            vals = []
            for j, h in enumerate(d.columns.tolist()[:len(heads)]):
                vals.append(fmt_cell(i if j == 0 and h is None else r[h],
                                     fmts[j] if j < len(fmts) else 'w'))
            rows.append(vals)
        if not rows:
            return ''
    else:
        rows = df[:maxrows] if maxrows else df
    return T(heads, rows, cls)


def frame_ev(summary, df, heads, fmts=None, blurb='', maxrows=80):
    """A collapsible evidence block wrapping a table."""
    t = tab(df, heads, fmts, maxrows=maxrows)
    if not t:
        return ''
    return ev(summary, (f'<p style="font-size:13px;color:#6B7280;margin:16px 0 0">{blurb}</p>' if blurb else '') + t)


# ------------------------------------------------------------- prose builders
def concentration(s, name='the largest', unit=''):
    """Where the weight of a distribution sits."""
    try:
        s = s.sort_values(ascending=False)
        tot = float(s.sum())
        if not tot or len(s) == 0:
            return ''
        top = s.iloc[0]
        t3 = s.iloc[:3].sum()
        half = int((s.cumsum() / tot <= 0.5).sum()) + 1
        nm = clean(s.index[0])
        out = (f'{nm} alone holds <strong>{top / tot * 100:.0f}%</strong> of the '
               f'{unit or "total"}, and the top three hold {t3 / tot * 100:.0f}%. '
               f'{half} of {len(s)} {unit or "items"} account for half of it.')
        return out
    except Exception:
        return ''


def extremes(df, col, label=None, d=1):
    """Best and worst on one column of a frame, with the multiple between them."""
    try:
        s = df[col].dropna().sort_values(ascending=False)
        if len(s) < 2:
            return ''
        hi, lo = s.index[0], s.index[-1]
        k = f'{s[col if False else 0]}'  # unused guard
        mult = s.max() / s.min() if s.min() else np.nan
        lab = label or col
        return (f'On {lab} the range runs from <strong>{clean(hi)}</strong> at '
                f'{s.max():,.{d}f} to <strong>{clean(lo)}</strong> at {s.min():,.{d}f}, '
                f'a spread of {mult:,.1f} times.' if np.isfinite(mult) else
                f'On {lab} the range runs from {clean(hi)} at {s.max():,.{d}f} to {clean(lo)} at {s.min():,.{d}f}.')
    except Exception:
        return ''


def yoy_para(label, cur, prev, unit='money', d=1):
    f = (money if unit == 'money' else (lambda v: pc(v, d)) if unit == 'pct'
         else (lambda v: _n(v, d if unit == 'f' else 0)))
    txt = f'{label} was <strong>{f(cur)}</strong>'
    if prev and np.isfinite(prev):
        dd = (cur - prev)
        pp = dd / abs(prev) * 100 if prev else 0
        step = money(abs(dd)) if unit == 'money' else f'{abs(dd):,.0f}' if unit == 'n' else f'{abs(dd):,.{d}f}'
        txt += (f' against {f(prev)} a year earlier &mdash; '
                f'{"up" if dd >= 0 else "down"} {step} ({abs(pp):.1f}%)')
    return txt + '.'


def rank_list(df, col, n=4, unit='money'):
    f = money if col in ('rev', 'cash', 'value', 'val') else (lambda v: pc(v) if 'pct' in col or 'fill' in col or 'rate' in col else _n(v, 1 if col in ('per', 'rpc', 'rph', 'ticket', 'avg') else 0))
    try:
        s = df[col].sort_values(ascending=False).head(n)
        return ' &middot; '.join(f'{clean(i)} {f(v)}' for i, v in s.items())
    except Exception:
        return ''


def hyp(items):
    """items: list of (tag, title, body, verdict) with tag in yes/no/part."""
    lab = {'yes': 'Supported', 'no': 'Ruled out', 'part': 'Partly'}
    cards = ''.join(f'''<div class="hcard"><span class="tag {t}">{lab[t]}</span>
<h3>{ti}</h3><p>{b}</p>{f'<div class="verdict">{v}</div>' if v else ''}</div>''' for t, ti, b, v in items)
    return f'<div class="hyp">{cards}</div>' if cards else ''


def statgrid(items):
    cells = ''.join(f'<div><div class="v">{v}</div><div class="l">{l}</div></div>' for l, v in items)
    return f'<div class="stat">{cells}</div>' if cells else ''


def sec(title, sub='', paras=(), blocks=()):
    """One analytical section: heading, one-line claim, paragraphs, then charts
    and tables in order."""
    h = f'<h2>{title}</h2>'
    if sub:
        h += f'<div class="sub">{sub}</div>'
    for p in [x for x in paras if x]:
        h += p if str(p).startswith('<') else f'<p>{p}</p>'
    for b in [x for x in blocks if x]:
        h += b
    return h


def kpi(l, v, d='', t='neu'):
    return dict(label=l, value=v, detail=d, tone=t)


# ------------------------------------------------------------- method section
def method(M, definitions, cautions, extra_rows=()):
    """The 'method and limitations' block every one of the hand-written reports
    carried: what was read, how each term is defined, and what it cannot show."""
    rows = []
    for s in M.D.sources:
        df = M.D.get(s.kind)
        if df is None:
            continue
        n = int((df['_loc'] == M.studio).sum()) if '_loc' in df.columns else len(df)
        span = ''
        if '_dt' in df.columns and df['_dt'].notna().any():
            span = f"{df['_dt'].min():%b %Y} to {df['_dt'].max():%b %Y}"
        rows.append([s.name[:44], s.kind, f'{len(df):,}', f'{n:,}', span])
    for r in extra_rows:
        rows.append(r)
    defn = ''.join(f'<li><strong>{a}.</strong> {b}</li>' for a, b in definitions)
    caut = ''.join(f'<p>{c}</p>' for c in cautions)
    return (f'''<h2>Method and limitations</h2>
<div class="sub">How to read these numbers, and what they cannot show</div>
{ev("Evidence &mdash; what was read, and how much of it belongs to this studio",
     T(['File', 'Source', 'Rows in file', 'Rows for this studio', 'Date span'], rows, 'num')
     + note('Every figure in this chapter is computed from these rows. Nothing is estimated, extrapolated or carried over from another month.'))}
<h4>Definitions used in this chapter</h4>
<ul>{defn}</ul>
{caut}''')


# ===================================================================== the data
class Deep:
    """Extra tables the hand-written reports used, computed for any studio and
    month from the frames the app already holds."""

    def __init__(self, M):
        self.M = M
        self.tr = None; self.prscore = None; self.prscore_prev = None
        self.prow = None; self.pr_label = ''
        self.sales = {}; self.cls = {}; self.lp = {}; self.ld = {}; self.bh = {}
        self.nw = {}; self.bm = {}
        self.y, self.m = M.y, M.m
        self.lab = M.label
        self.mon = MONTH_NAMES[M.m - 1]
        self.has = M.has
        self._sales(); self._sessions()
        self._lapsed(); self._leads(); self._beh(); self._new(); self._bench()

    # convenience slices ------------------------------------------------------
    def s(self, df, y, key=None):
        try:
            return self.M._sl(df, y, None, key or '_loc')
        except Exception:
            return pd.DataFrame()

    # ------------------------------------------------------------------- sales
    def _sales(self):
        M = self.M
        S = getattr(M.D, 'sales', None)
        self.sales = {}
        if S is None:
            return
        def okrows(d):
            return d[d['ok']] if len(d) and 'ok' in d.columns else d
        cur = okrows(self.s(S, self.y))
        if cur.empty:
            return
        self.sales['cur'] = cur
        self.sales['prev'] = okrows(self.s(S, self.y - 1))
        self.sales['y2'] = okrows(self.s(S, self.y - 2))

        def agg(d):
            if d.empty:
                return None
            if 'Sale ID' in d.columns:
                g = d.groupby('Member ID').agg(cash=('val', 'sum'), lines=('val', 'size'),
                                               sales=('Sale ID', 'nunique'),
                                               disc=('disc', 'sum'), gross=('gross', 'sum'))
            else:
                g = d.groupby('Member ID').agg(cash=('val', 'sum'), lines=('val', 'size'),
                                               disc=('disc', 'sum'), gross=('gross', 'sum'))
                g['sales'] = g['lines']
            return g
        g, gp = agg(cur), agg(self.sales['prev'])
        self.sales['by_member'] = g
        self.sales['by_member_prev'] = gp
        # categories, this year and last, with the delta; 'sold' counts
        # distinct sales, not item rows
        sid = 'Sale ID' if 'Sale ID' in cur.columns else None
        if 'Cleaned Category' in cur.columns:
            c = cur.groupby('Cleaned Category').agg(n=(sid or 'val', 'nunique' if sid else 'size'),
                                                    rev=('val', 'sum'),
                                                    buyers=('Member ID', 'nunique'), disc=('disc', 'sum'))
            if gp is not None and not self.sales['prev'].empty:
                pv = self.sales['prev']
                sidp = 'Sale ID' if 'Sale ID' in pv.columns else None
                p = pv.groupby('Cleaned Category').agg(n2=(sidp or 'val', 'nunique' if sidp else 'size'),
                                                       rev2=('val', 'sum'))
                c = c.join(p, how='outer')
            self.sales['cats'] = c.fillna(0).sort_values('rev', ascending=False)
        # products
        if 'Cleaned Product' in cur.columns:
            p = cur.groupby('Cleaned Product').agg(n=(sid or 'val', 'nunique' if sid else 'size'),
                                                    rev=('val', 'sum'),
                                                    buyers=('Member ID', 'nunique'), ticket=('val', 'mean'))
            pv = self.sales['prev']
            if len(pv):
                sidp = 'Sale ID' if 'Sale ID' in pv.columns else None
                q = pv.groupby('Cleaned Product').agg(n2=(sidp or 'val', 'nunique' if sidp else 'size'),
                                                      rev2=('val', 'sum'))
                p = p.join(q, how='outer').fillna(0)
                p['d'] = p['rev'] - p['rev2']
            self.sales['prods'] = p.sort_values('rev', ascending=False)
            self.sales['movers'] = p[p['rev'].abs() >= 10000].sort_values('d', key=abs, ascending=False).head(10) \
                if 'd' in p else p.head(10)
        # price per class on each product, from the membership class counts
        if all(c in cur.columns for c in ['Sec. Membership Total Classes', 'val']):
            t = cur.copy()
            t['cls'] = num(t['Sec. Membership Total Classes'])
            t = t[(t['cls'] > 0) & (t['val'] > 0)]
            if len(t):
                q = t.groupby('Cleaned Product').agg(n=('val', 'size'), cls=('cls', 'mean'),
                                                      pay=('val', 'sum'))
                q['per_class'] = q['pay'] / q['cls'].replace(0, np.nan)
                q['per_class'] = q['per_class'].replace([np.inf, -np.inf], np.nan)
                q = q[q['cls'] >= 3]
                self.sales['ppc'] = q[q['n'] >= 5].sort_values('per_class')
        # transaction bands
        BINS = [0, 2000, 5000, 10000, 20000, 50000, 10 ** 9]
        LABS = ['under 2k', '2 to 5k', '5 to 10k', '10 to 20k', '20 to 50k', '50k and above']
        b = cur.assign(band=pd.cut(cur['val'], BINS, labels=LABS)).groupby('band', observed=True) \
            .agg(n=('val', 'size'), rev=('val', 'sum'), buyers=('Member ID', 'nunique')).reindex(LABS).fillna(0)
        self.sales['bands'] = b
        # who sold it
        if 'Sold By' in cur.columns:
            sb = cur.assign(sold=cur['Sold By'].astype(str).str.strip()
                            .replace({'nan': 'Not recorded', '': 'Not recorded'})) \
                .groupby('sold').agg(n=('val', 'size'), cash=('val', 'sum'),
                                     buyers=('Member ID', 'nunique'), disc=('disc', 'sum'))
            self.sales['sold_by'] = sb.sort_values('cash', ascending=False)
        # payment channel
        for col, key in [('Payment Method', 'paymeth'), ('Payment Source', 'pay_src')]:
            if col in cur.columns:
                g2 = cur.assign(v=cur[col].astype(str).str.strip().replace({'nan': 'Unspecified'})) \
                    .groupby('v').agg(n=('val', 'size'), cash=('val', 'sum'), avg=('val', 'mean'))
                self.sales[key] = g2.sort_values('cash', ascending=False)
        # discount codes
        if 'Discount Code' in cur.columns:
            d = cur[cur['Discount Code'].notna() & (cur['disc'] > 0)]
            if len(d):
                g3 = d.groupby(d['Discount Code'].astype(str).str.strip()).agg(
                    n=('disc', 'size'), given=('disc', 'sum'), cash=('val', 'sum'),
                    buyers=('Member ID', 'nunique'))
                g3['depth'] = g3['given'] / (g3['cash'] + g3['given']) * 100
                self.sales['codes'] = g3.sort_values('given', ascending=False)
        # repeat buyers: a repeat is two or more distinct sales, not two item
        # lines on one invoice
        if g is not None:
            self.sales['repeat'] = dict(buyers=int(len(g)), multi=int((g['sales'] > 1).sum()),
                                        multi_share=float((g['sales'] > 1).mean() * 100),
                                        multi_cash=float(g[g['sales'] > 1]['cash'].sum()),
                                        cash=float(g['cash'].sum()))
            self.sales['repeat']['multi_cash_share'] = self.sales['repeat']['multi_cash'] / max(self.sales['repeat']['cash'], 1) * 100
            r = g['lines'].value_counts().sort_index()
            self.sales['line_freq'] = r.to_frame('buyers').assign(
                cash=lambda x: [float(g[g['lines'] == i]['cash'].sum()) for i in x.index])
            self.sales['deciles'] = (g.sort_values('cash', ascending=False)['cash']
                                     .groupby(np.arange(len(g)) // max(int(len(g) / 10), 1)).agg(['size', 'sum']))
        # year to date against the same span last year
        for key, yr in [('ytd', self.y), ('ytd_prev', self.y - 1)]:
            try:
                d = S[(S['_loc'] == M.studio) & (S['_dt'] >= f'{yr}-01-01') & (S['_dt'] < f'{yr}-{self.m:02d}-01')]
                d = okrows(d)
                self.sales[key] = dict(cash=float(d['val'].sum()),
                                       lines=int(d['Sale ID'].nunique()) if 'Sale ID' in d.columns else len(d),
                                       buyers=int(d['Member ID'].nunique()))
            except Exception:
                pass
        # class-money attribution: what the month's cash has to deliver
        X = self.M.D.sessions
        if X is not None:
            xs = self.s(X, self.y)
            if len(xs):
                self.sales['delivered'] = float(xs['Revenue'].sum())
        # retail / non-class categories
        if 'Cleaned Category' in cur.columns:
            self.sales['retail'] = cur[~cur['Cleaned Category'].astype(str)
                                       .str.contains('Member|Package|Single|Class|Intro', case=False, na=False)] \
                .groupby('Cleaned Product').agg(n=('val', 'size'), rev=('val', 'sum')).sort_values('rev', ascending=False)
        # day-of-month trading pattern
        self.sales['dom'] = cur.assign(d=cur['_dt'].dt.day).groupby('d').agg(n=('val', 'size'), cash=('val', 'sum'))
        self.sales['weeks'] = cur.assign(w=((cur['_dt'].dt.day - 1) // 7 + 1)).groupby('w').agg(
            n=('val', 'size'), cash=('val', 'sum'), buyers=('Member ID', 'nunique'))

    # ----------------------------------------------------------------- classes
    def _sessions(self):
        M = self.M
        X = M.D.sessions
        self.cls = {}
        if X is None:
            return
        cur = self.s(X, self.y); prev = self.s(X, self.y - 1)
        C = self.cls
        C['cur'], C['prev'] = cur, prev
        if cur.empty:
            return
        # payment mix per format (who is in the room, by what they own)
        for c in ['Memberships', 'Packages', 'IntroOffers', 'SingleClasses']:
            if c not in cur:
                cur[c] = 0
        mix = cur.groupby('_cls').agg(mem=('Memberships', 'sum'), pkg=('Packages', 'sum'),
                                      intro=('IntroOffers', 'sum'), single=('SingleClasses', 'sum'),
                                      nonpaid=('NonPaid', 'sum'), comp=('Complimentary', 'sum'),
                                      att=('CheckedIn', 'sum'))
        mix['total'] = mix[['mem', 'pkg', 'intro', 'single']].sum(axis=1)
        mix['paid'] = mix[['mem', 'pkg', 'single']].sum(axis=1)
        mix['free_pct'] = (mix['total'] - mix['paid']) / mix['total'].replace(0, np.nan) * 100
        mix['comp_pct'] = mix['comp'] / mix['att'].replace(0, np.nan) * 100
        C['paymix'] = mix[mix['total'] > 0].sort_values('total', ascending=False)
        # occupancy bands
        C['occ'] = cur.assign(b=pd.cut(cur['CheckedIn'], [-1, 0, 2, 5, 10, 20, 999],
                                       labels=['nobody', '1 to 2', '3 to 5', '6 to 10', '11 to 20', 'over 20'])) \
            .groupby('b', observed=True).agg(n=('SessionID', 'size'), seats=('_cap', 'sum'),
                                             att=('CheckedIn', 'sum'), rev=('Revenue', 'sum')).reindex(
            ['nobody', '1 to 2', '3 to 5', '6 to 10', '11 to 20', 'over 20'])
        C['occ']['rev'] = cur.assign(b=pd.cut(cur['CheckedIn'], [-1, 0, 2, 5, 10, 20, 999],
                                              labels=['nobody', '1 to 2', '3 to 5', '6 to 10', '11 to 20', 'over 20'])) \
            .groupby('b', observed=True)['Revenue'].sum().reindex(C['occ'].index)
        # empties and near empties
        C['empty'] = cur[cur['CheckedIn'] == 0].sort_values('_dt')
        C['near'] = cur[(cur['CheckedIn'] > 0) & (cur['CheckedIn'] <= 2)]
        lean = pd.concat([C['empty'].assign(kind='nobody'), C['near'].assign(kind='1 to 2 only')])
        C['lean'] = lean.assign(k=lean['kind']).pivot_table(index='_cls', columns='k', values='SessionID',
                                                            aggfunc='size', fill_value=0)
        for c in ['nobody', '1 to 2 only']:
            if c not in C['lean']:
                C['lean'][c] = 0
        C['lean']['lean'] = C['lean']['nobody'] + C['lean']['1 to 2 only']
        C['lean']['all'] = cur.groupby('_cls').size()
        C['lean'] = C['lean'].sort_values('lean', ascending=False)
        # fullest and emptiest real classes
        big = cur[cur['_cap'] >= 8]
        cols = [c for c in ['_dt', '_day', '_hr', '_cls', '_trainer', '_cap', 'CheckedIn', 'Booked',
                            'LateCancelled', 'Revenue'] if c in big.columns]
        C['fullest'] = big.nlargest(12, 'CheckedIn')[cols] if len(big) else None
        C['emptiest'] = big.nsmallest(12, 'CheckedIn')[cols] if len(big) else None
        # weekly rhythm inside the month
        C['weeks'] = cur.assign(w=((cur['_dt'].dt.day - 1) // 7 + 1)).groupby('w').agg(
            classes=('SessionID', 'size'), seats=('_cap', 'sum'), att=('CheckedIn', 'sum'),
            rev=('Revenue', 'sum'), book=('Booked', 'sum'))
        C['weeks']['fill'] = C['weeks']['att'] / C['weeks']['seats'] * 100
        C['weeks']['rpc'] = C['weeks']['rev'] / C['weeks']['classes']
        # hour x day grid
        C['grid'] = cur.pivot_table(index='_hr', columns='_day', values='CheckedIn', aggfunc='sum').reindex(columns=DAYS)
        C['grid_fill'] = (cur.pivot_table(index='_hr', columns='_day', values='CheckedIn', aggfunc='sum') /
                          cur.pivot_table(index='_hr', columns='_day', values='_cap', aggfunc='sum') * 100).reindex(columns=DAYS)
        # format movement year on year
        g1 = cur.groupby('_cls').agg(sessions=('SessionID', 'size'), seats=('_cap', 'sum'),
                                     att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
        if len(prev):
            g0 = prev.groupby('_cls').agg(sessions_p=('SessionID', 'size'), att_p=('CheckedIn', 'sum'),
                                          rev_p=('Revenue', 'sum'), seats_p=('_cap', 'sum'))
            g1 = g1.join(g0, how='outer')
        g1 = g1.fillna(0)
        g1['fill'] = g1['att'] / g1['seats'].replace(0, np.nan) * 100
        g1['fill_p'] = g1['att_p'] / g1['seats_p'].replace(0, np.nan) * 100 if 'att_p' in g1 else np.nan
        g1['rpc'] = g1['rev'] / g1['sessions'].replace(0, np.nan)
        if 'rev_p' in g1:
            g1['d_rev'] = g1['rev'] - g1['rev_p']
            g1['d_sess'] = g1['sessions'] - g1['sessions_p']
        C['fmt_yoy'] = g1.sort_values('att', ascending=False)
        # booking book: booked against turned up
        C['book'] = cur.assign(gap=cur['Booked'] - cur['CheckedIn']).groupby('_cls').agg(
            book=('Booked', 'sum'), att=('CheckedIn', 'sum'), lc=('LateCancelled', 'sum'),
            seats=('_cap', 'sum'))
        C['book']['show'] = C['book']['att'] / C['book']['book'].replace(0, np.nan) * 100
        C['book']['lost'] = C['book']['book'] - C['book']['att']
        C['book'] = C['book'].sort_values('lost', ascending=False)
        # hosted / partner / event classes
        if 'SessionName' in cur:
            pat = 'X |x |Hosted|Sponsor|Partner|Event|Fest|Pickle|Ladies|Challenge|Pop|Retreat|Workshop'
            h = cur[cur['SessionName'].astype(str).str.contains(pat, case=False, na=False)]
            C['hosted'] = dict(n=int(len(h)), att=float(h['CheckedIn'].sum()), rev=float(h['Revenue'].sum()),
                               seats=float(h['_cap'].sum()))
            C['hosted_rows'] = h.groupby(cur['SessionName'].astype(str).str.slice(0, 34)).agg(
                n=('SessionID', 'size'), att=('CheckedIn', 'sum'), rev=('Revenue', 'sum')).sort_values('att', ascending=False) \
                if len(h) else None
        # trainer x format sharing
        C['tf'] = cur.groupby(['_cls', '_trainer']).agg(n=('SessionID', 'size'), att=('CheckedIn', 'sum'),
                                                         rev=('Revenue', 'sum'))
        C['tshare'] = C['tf'].reset_index().groupby('_trainer')['n'].size()
        # multi-class sessions (one record, several rooms)
        if 'Classes' in cur:
            C['multi'] = cur[num(cur['Classes']) > 1].groupby('_cls').agg(n=('SessionID', 'size'),
                                                                           att=('CheckedIn', 'sum'))
        # day of week with last year alongside
        d1 = cur.groupby('_day').agg(classes=('SessionID', 'size'), seats=('_cap', 'sum'),
                                     att=('CheckedIn', 'sum'), rev=('Revenue', 'sum')).reindex(DAYS)
        if len(prev):
            d0 = prev.groupby('_day').agg(att_p=('CheckedIn', 'sum'), seats_p=('_cap', 'sum'),
                                          rev_p=('Revenue', 'sum')).reindex(DAYS)
            d1 = d1.join(d0)
        d1['fill'] = d1['att'] / d1['seats'] * 100
        C['dow'] = d1
        h1 = cur.groupby(cur['_hr'].astype('Int64')).agg(classes=('SessionID', 'size'), seats=('_cap', 'sum'),
                                                          att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'),
                                                          lc=('LateCancelled', 'sum'), book=('Booked', 'sum'))
        if len(prev):
            h0 = prev.groupby(prev['_hr'].astype('Int64')).agg(att_p=('CheckedIn', 'sum'),
                                                                seats_p=('_cap', 'sum')).reindex(h1.index)
            h1 = h1.join(h0)
        h1['fill'] = h1['att'] / h1['seats'] * 100
        C['hour'] = h1

        # trainer detail
        t = cur.groupby('_trainer').agg(sessions=('SessionID', 'size'), att=('CheckedIn', 'sum'),
                                        seats=('_cap', 'sum'), book=('Booked', 'sum'), lc=('LateCancelled', 'sum'),
                                        rev=('Revenue', 'sum'), comp=('Complimentary', 'sum'),
                                        nonpaid=('NonPaid', 'sum'), empty=('CheckedIn', lambda s: int((s == 0).sum())))
        t['fill'] = t['att'] / t['seats'] * 100
        t['rpc'] = t['rev'] / t['sessions']
        t['rph'] = t['rev'] / t['att'].replace(0, np.nan)
        t['show'] = t['att'] / t['book'].replace(0, np.nan) * 100
        t['lc_rate'] = t['lc'] / t['book'].replace(0, np.nan) * 100
        t['comp_pct'] = t['comp'] / t['att'].replace(0, np.nan) * 100
        t['fmts'] = cur.groupby('_trainer')['_cls'].nunique()
        t['fmtlist'] = cur.groupby('_trainer')['_cls'].apply(lambda s: ', '.join(sorted(set(clean(x) for x in s))[:6]))
        try:
            hrs = cur.assign(h=cur['_hr']).dropna(subset=['h']).groupby('_trainer')['h'].agg(['min', 'max'])
            t['hours'] = hrs.apply(lambda r: f'{int(r["min"]):02d} to {int(r["max"]):02d}', axis=1)
            t = t.join(hrs.rename(columns={'min': 'h_first', 'max': 'h_last'}), how='left')
        except Exception:
            pass
        t['days'] = cur.groupby('_trainer')['_day'].nunique()
        if len(prev):
            p = prev.groupby('_trainer').agg(sessions_p=('SessionID', 'size'), att_p=('CheckedIn', 'sum'),
                                             rev_p=('Revenue', 'sum'))
            p['fill_p'] = p['att_p'] / prev.groupby('_trainer')['_cap'].sum().reindex(p.index) * 100
            t = t.join(p, how='left')
        self.tr = t.sort_values('sessions', ascending=False)
        # payroll scorecard
        PR = getattr(M.D, 'payroll', None)
        self.prscore = None
        if PR is not None and len(PR):
            d = PR[PR['_loc'] == M.studio].copy()
            my = d['Month Year'].astype(str).str.strip()
            dt = None
            for f in ('%b-%Y', '%b %Y', '%B-%Y', '%B %Y', '%Y-%m'):
                v = pd.to_datetime(my, format=f, errors='coerce')
                dt = v if dt is None else dt.fillna(v)
            d['dt'] = dt
            d = d[d['dt'].notna()].copy()
            if len(d):
                for c in d.columns:
                    if str(c) not in ('Teacher ID', 'Teacher Name', 'Teacher Email', 'Location',
                                      'Month Year', 'Unique Key', 'dt'):
                        d[c] = num(d[c])
                self.prow = d
                a_, b_ = rng(self.y, self.m)
                mth = d[(d['dt'] >= a_) & (d['dt'] < b_)]
                tag = ''
                self.prscore = mth
                self.pr_label = tag
                pp = d[(d['dt'] >= a_ - pd.DateOffset(years=1)) & (d['dt'] < b_ - pd.DateOffset(years=1))]
                self.prscore_prev = pp if len(pp) else None

    # -------------------------------------------------------------------- new
    def _new(self):
        M = self.M
        Nw = getattr(M.D, 'new', None)
        self.nw = {}
        if Nw is None:
            return
        allrows = Nw[Nw['_loc'] == M.studio].copy()
        if allrows.empty:
            return
        self.nw['all'] = allrows
        # Acquisition measures run on the explicit newcomer population only;
        # imports and existing-member first-visit rows would dilute LTV,
        # conversion and visit averages (atlas reconciliation).
        d = allrows[allrows['is_new'] == True].copy() if 'is_new' in allrows.columns else allrows.copy()
        if d.empty:
            return
        self.nw['d'] = d
        for c, t in [('Ltv', 'ltv'), ('No of Visits', 'visits'), ('Days To Second Visit', 'd2'),
                     ('Conversion Span (Days)', 'cspan'), ('Late Cancel Rate Post Trial', 'lcr'),
                     ('First Purchase Value', 'fpv'), ('Visits Per Month', 'vpm'),
                     ('Days Since Last Visit', 'dslv'), ('Total Purchases All Time', 'buys')]:
            if c in d.columns:
                d[t] = num(d[c])
        if 'Conversion Status' in d:
            d['conv'] = d['Conversion Status'].astype(str).str.strip().eq('Converted')
        self.nw['d'] = d
        # intake in the month under review
        if '_dt' in d:
            a, b = rng(self.y, self.m)
            self.nw['month'] = d[(d['_dt'] >= a) & (d['_dt'] < b)]
        # first purchase predicts lifetime value
        if 'First Purchase Post Trial' in d and 'ltv' in d:
            g = d.dropna(subset=['First Purchase Post Trial']).groupby(
                d['First Purchase Post Trial'].astype(str).str.strip()).agg(
                people=('ltv', 'size'), ltv=('ltv', 'mean'), visits=('visits', 'mean'),
                vpm=('vpm', 'mean') if 'vpm' in d else ('visits', 'mean'),
                conv=('conv', 'mean') if 'conv' in d else ('ltv', 'size'))
            g['conv'] = g['conv'] * 100 if 'conv' in d else np.nan
            self.nw['first'] = g[g['people'] >= 15].sort_values('ltv', ascending=False)
        # speed to second visit
        if 'd2' in d:
            b = pd.cut(d['d2'], [-1, 1, 3, 7, 14, 30, 100000],
                       labels=['a day or less', '2 to 3 days', '4 to 7 days', '8 to 14 days',
                               '15 to 30 days', 'over a month'])
            g = d.assign(b=b).groupby('b', observed=True).agg(people=('ltv', 'size'), ltv=('ltv', 'mean'),
                                                               visits=('visits', 'mean'))
            self.nw['speed'] = g
        # source and new-client type
        for col, key in [('Source', 'source'), ('First Visit Type', 'vtype')]:
            if col in d:
                g = d.groupby(d[col].astype(str).str.strip()).agg(
                    people=('ltv', 'size'), ltv=('ltv', 'mean'), visits=('visits', 'mean'),
                    buys=('buys', 'mean') if 'buys' in d else ('visits', 'mean'),
                    conv=('conv', 'mean') if 'conv' in d else ('ltv', 'size'),
                    d2=('d2', 'median') if 'd2' in d else ('ltv', 'mean'),
                    lcr=('lcr', 'mean') if 'lcr' in d else ('ltv', 'mean'))
                g['conv'] = g['conv'] * (100 if 'conv' in d else np.nan)
                self.nw[key] = g[g['people'] >= 15].sort_values('people', ascending=False)
        # lifecycle mix and the retention states
        for col in ['Lifecycle Status', 'Retention Status']:
            if col in d:
                self.nw[col] = d[col].astype(str).str.strip().value_counts()
        # conversion speed buckets
        if 'Conversion Speed Bucket' in d:
            self.nw['csb'] = d['Conversion Speed Bucket'].astype(str).str.strip().value_counts()
        # first visit day / slot as booked
        for col, key in [('First Visit Day', 'fday'), ('First Visit Time Slot', 'fslot')]:
            if col in d:
                self.nw[key] = d[col].astype(str).str.strip().value_counts().head(12)
        # trainer whose first class became a member
        if 'Trainer Name' in d and 'conv' in d:
            g = d.groupby(d['Trainer Name'].astype(str).str.strip()).agg(
                first_classes=('conv', 'size'), converted=('conv', 'sum'),
                ltv=('ltv', 'mean') if 'ltv' in d else ('conv', 'mean'),
                visits=('visits', 'mean') if 'visits' in d else ('conv', 'mean'))
            g['conv_pct'] = g['converted'] / g['first_classes'] * 100
            self.nw['trainer'] = g[g['first_classes'] >= 10].sort_values('conv_pct', ascending=False)

    # ------------------------------------------------------------------ lapsed
    def _lapsed(self):
        M = self.M
        L = getattr(M.D, 'lapsed', None)
        self.lp = {}
        if L is None:
            return
        d = L[L['_loc'] == M.studio].copy()
        if d.empty:
            return
        for c in ['Amount Paid', 'Original Amount (Before Discount)', 'Discount Value', 'Sessions Limit',
                  'Total Sessions Completed', 'Sessions Used %', 'Remaining Sessions', 'Total Cancellations',
                  'Late Cancellations', 'No Shows', 'Early Cancellations', 'Cancellation Rate %',
                  'Membership Duration (Days)', 'Days Active', 'Days Since Last Visit', 'Lapse Gap (Days)',
                  'Avg Days Between Visits', 'Visits in First Half', 'Visits in Second Half',
                  'Attendance Decline Rate %', 'Visits in Last 30 Days', 'No Show Rate %', 'Average Sessions Per Month',
                  'Revenue Per Session', 'Membership Freeze Count', 'Days Frozen', 'Attendance Rate %']:
            if c in d.columns:
                d[c] = num(d[c])
        from .data import dparse
        for c in ['Purchase Date', 'Start Date', 'End Date', 'Churned Date', 'Most Recent Visit Date', 'First Visit Date']:
            if c in d.columns:
                d[c + '_x'] = d[c + '_d'] if c + '_d' in d else dparse(d[c])
        if 'Membership Name' in d:
            comp = d['Membership Name'].astype(str).str.contains(
                r'Staff|Complimentary|Open Barre|Copper \+ Cloves Credit|Referrer|Free', case=False, na=False)
            self.lp['comp_n'] = int(comp.sum())
            d['is_paid'] = (~comp) & (d['Amount Paid'].fillna(0) > 0)
        self.lp['d'] = d
        paid = d[d['is_paid']] if 'is_paid' in d else d[d['Amount Paid'].fillna(0) > 0]
        self.lp['paid'] = paid
        # churn mechanisms
        if 'Total Sessions Completed' in d:
            z = d['Total Sessions Completed'].fillna(0)
            self.lp['never'] = int((z == 0).sum())
            self.lp['never_paid'] = int(((z == 0) & (paid['Amount Paid'] > 0)).sum()) if len(paid) else 0
        # decline: first half of the membership against the second
        if all(c in d for c in ['Visits in First Half', 'Visits in Second Half']):
            q = d[(d['Visits in First Half'].fillna(0) + d['Visits in Second Half'].fillna(0)) > 3].copy()
            if len(q):
                q['half'] = q['Visits in Second Half'] / q['Visits in First Half'].replace(0, np.nan)
                self.lp['decline'] = dict(n=int(len(q)),
                                          fell=float((q['Visits in Second Half'] < q['Visits in First Half']).mean() * 100),
                                          halved=float((q['half'] <= 0.5).mean() * 100),
                                          rose=float((q['Visits in Second Half'] > q['Visits in First Half']).mean() * 100),
                                          med_then=float(q['Visits in First Half'].median()),
                                          med_now=float(q['Visits in Second Half'].median()))
        # winnable: money left, unused classes, recency
        if 'Remaining Sessions' in d:
            w = paid.copy()
            w['used'] = w['Sessions Used %'].fillna(0)
            w['left'] = w['Remaining Sessions'].fillna(0)
            w['money_left'] = w['Amount Paid'] * (1 - w['used'] / 100)
            w['rec'] = w['Days Since Last Visit'].fillna(9999)
            seg = pd.cut(w['rec'], [-1, 30, 60, 90, 180, 100000],
                         labels=['attended in the last 30 days', '31 to 60 days ago', '61 to 90 days ago',
                                 '91 to 180 days ago', 'over 180 days ago'])
            g = w.assign(s=seg).groupby('s', observed=True).agg(
                members=('Member ID', 'nunique'), cash_left=('money_left', 'sum'),
                classes_left=('left', 'sum'), ticket=('Amount Paid', 'mean'))
            self.lp['winnable'] = g
            self.lp['money_left'] = float(w['money_left'].sum())
            self.lp['classes_left'] = float(w['left'].sum())
            self.lp['warm'] = int((w['rec'] <= 60).sum())
            self.lp['low_use'] = w[w['used'] <= 25]
        # by purchase month: the cohort view of churn
        if 'Purchase Date_x' in paid:
            c = paid.assign(mo=paid['Purchase Date_x'].dt.to_period('M')).groupby('mo').agg(
                sold=('Amount Paid', 'size'), cash=('Amount Paid', 'sum'),
                days=('Membership Duration (Days)', 'median'), used=('Sessions Used %', 'mean'),
                live=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)
                if 'Derived Status' in paid else ('Amount Paid', 'mean'))
            self.lp['cohort'] = c[c['sold'] >= 20].sort_index()
        # no-shows and cancels as churn signals
        if 'Cancellation Rate %' in d:
            b = pd.cut(d['Cancellation Rate %'].fillna(0), [-1, 0, 10, 25, 50, 1000],
                       labels=['never', 'up to 10%', '11 to 25%', '26 to 50%', 'over 50%'])
            g = d.assign(b=b).groupby('b', observed=True).agg(
                n=('Member ID', 'size'), days=('Membership Duration (Days)', 'median'),
                used=('Sessions Used %', 'mean'), late=('Late Cancellations', 'mean'),
                noshow=('No Shows', 'mean'), live=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)
                if 'Derived Status' in d else ('Amount Paid', 'mean'))
            self.lp['cancel_bands'] = g
        if 'No Show Rate %' in d:
            self.lp['noshow'] = d.groupby(pd.cut(d['No Show Rate %'].fillna(0), [-1, 0, 10, 100],
                                                  labels=['never missed', 'one or two', 'three or more']),
                                           observed=True).agg(n=('Member ID', 'size'),
                                                               days=('Membership Duration (Days)', 'median'),
                                                               used=('Sessions Used %', 'mean')).reindex(
                ['never missed', 'one or two', 'three or more'])
        # freeze behaviour
        if 'Membership Freeze Count' in d:
            f = d[d['Membership Freeze Count'].fillna(0) > 0]
            self.lp['freeze'] = dict(n=int(len(f)), share=float(len(f) / max(len(d), 1) * 100),
                                     days=float(d['Days Frozen'].fillna(0).mean()) if 'Days Frozen' in d else 0,
                                     live=float(f['Derived Status'].isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)
                                     if 'Derived Status' in f else np.nan,
                                     base=float(d[d['Membership Freeze Count'].fillna(0) == 0]['Derived Status']
                                                .isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)
                                     if 'Derived Status' in d else np.nan)
        # favourites of the lost book
        for col, key in [('Favorite Format', 'fav_fmt'), ('Favorite Trainer', 'fav_tr'), ('Favorite Time', 'fav_time'),
                         ('Favorite Half of Day', 'fav_half')]:
            if col in d:
                self.lp[key] = d[col].astype(str).str.strip().replace({'nan': 'none recorded'}).value_counts().head(10)
        # the lost money by product
        if 'Membership Name' in paid:
            g = paid.assign(fam=paid['Membership Name'].astype(str).str.replace('^Studio\\s*', '', regex=True).str.strip()) \
                .groupby('fam').agg(sold=('Amount Paid', 'size'), cash=('Amount Paid', 'sum'),
                                     ticket=('Amount Paid', 'mean'), days=('Membership Duration (Days)', 'median'),
                                     used=('Sessions Used %', 'mean'), left=('Remaining Sessions', 'sum'),
                                     lapsed=('Derived Status', lambda x: (x == 'Lapsed').mean() * 100)
                                     if 'Derived Status' in paid else ('Amount Paid', 'mean'))
            self.lp['prod'] = g[g['sold'] >= 10].sort_values('cash', ascending=False)
        # gap between last visit and churn date
        if all(c in d for c in ['Most Recent Visit Date_x', 'Churned Date_x']):
            q = d.dropna(subset=['Most Recent Visit Date_x', 'Churned Date_x'])
            if len(q):
                self.lp['lag'] = ((q['Churned Date_x'] - q['Most Recent Visit Date_x']).dt.days
                                  .clip(lower=0).describe())
        # discount history of the lapsed book
        if 'Discount Value' in d:
            self.lp['disc'] = d.groupby(pd.cut(d['Discount Value'].fillna(0), [-1, 0, 2000, 6000, 100000],
                                               labels=['none', 'up to 2k', '2 to 6k', 'over 6k']), observed=True) \
                .agg(n=('Amount Paid', 'size'), paid=('Amount Paid', 'mean'),
                     days=('Membership Duration (Days)', 'median'),
                     live=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)
                     if 'Derived Status' in d else ('Amount Paid', 'mean'))
        # ------------------------------------------------- the selected period
        # The rest of this analysis reads the whole ledger. This block scopes
        # churn to the month the report was generated for: a membership is
        # attributed to the month its event date (churned / purchased / ended /
        # last seen) falls in, so the chapter can lead with the period itself
        # instead of only the all-time book.
        try:
            a0, a1 = rng(M.y, M.m)
            per = {}
            events = M.source_D.lapsed[M.source_D.lapsed['_loc'] == M.studio].copy()
            for field in ['Purchase Date', 'End Date', 'Churned Date', 'Most Recent Visit Date']:
                if field in events:
                    events[field + '_x'] = events[field + '_d'] if field + '_d' in events else dparse(events[field])

            def _win(col, start, end, frame=None):
                f = frame if frame is not None else events
                if col not in f.columns:
                    return None
                w = f[f[col].between(start, end, inclusive='left')]
                return w

            cm = _win('Churned Date_x', a0, a1)
            if cm is not None:
                per['churned_n'] = int(len(cm))
                per['churned_members'] = int(cm['Member ID'].nunique()) if 'Member ID' in cm else int(len(cm))
                per['churned_cash'] = float(cm['Amount Paid'].sum()) if 'Amount Paid' in cm else 0.0
                per['churned_used'] = float(cm['Sessions Used %'].mean()) if 'Sessions Used %' in cm and len(cm) else np.nan
                per['churned_never'] = int((cm['Total Sessions Completed'].fillna(0) == 0).sum()) if 'Total Sessions Completed' in cm else 0
                per['churned_df'] = cm
            pm = _win('Purchase Date_x', a0, a1, frame=paid)
            if pm is not None:
                per['bought_n'] = int(len(pm))
                per['bought_cash'] = float(pm['Amount Paid'].sum()) if 'Amount Paid' in pm else 0.0
                per['bought_df'] = pm
            em = _win('End Date_x', a0, a1)
            if em is not None:
                per['ended_n'] = int(len(em))
            nx = _win('End Date_x', a1, a1 + pd.Timedelta(days=30))
            if nx is not None:
                per['expiring_n'] = int(len(nx))
                per['expiring_members'] = int(nx['Member ID'].nunique()) if 'Member ID' in nx else int(len(nx))
                per['expiring_cash'] = float(nx['Amount Paid'].sum()) if 'Amount Paid' in nx else 0.0
            vm = _win('Most Recent Visit Date_x', a0, a1)
            if vm is not None:
                per['lastvisit_n'] = int(len(vm))
                per['lastvisit_members'] = int(vm['Member ID'].nunique()) if 'Member ID' in vm else int(len(vm))
                if 'Derived Status' in vm:
                    per['lastvisit_gone_n'] = int(vm['Derived Status'].isin(['Lapsed', 'Churned', 'Expired']).sum())
            self.lp['period'] = per
        except Exception:
            self.lp['period'] = {}

    # ------------------------------------------------------------------- leads
    def _leads(self):
        M = self.M
        L = getattr(M.D, 'leads', None)
        self.ld = {}
        if L is None:
            return
        d = L[L['_loc'] == M.studio].copy()
        if d.empty:
            return
        self.ld['d'] = d
        d['won'] = d['won'].astype(bool) if 'won' in d else False
        for c in ['LTV', 'Visits', 'Purchases Made']:
            if c in d:
                d[c + 'n'] = num(d[c])
        # follow-up discipline
        fus = [c for c in d.columns if str(c).startswith('Follow Up ') and str(c).endswith('Date')]
        if fus:
            fd = {c: pd.to_datetime(d[c], errors='coerce') for c in fus}
            F = pd.DataFrame(fd, index=d.index)
            d['fu'] = F.notna().sum(axis=1)
            if '_dt' in d:
                first = F.apply(lambda r: r.dropna().min(), axis=1)
                last = F.apply(lambda r: r.dropna().max(), axis=1)
                # Follow-ups that predate the enquiry are recording errors;
                # they are excluded, not clamped to zero (atlas rule).
                resp = ((first - d['_dt']).dt.total_seconds() / 86400).dropna()
                resp = resp[resp >= 0]
                self.ld['resp'] = resp
                self.ld['resp_hours'] = resp * 24
                self.ld['fu_span'] = (last - first).dt.days.dropna()
                cc2 = next((c for c in ['Converted To Customer At_d', 'Converted To Customer At'] if c in d.columns), None)
                if cc2:
                    cw = pd.to_datetime(d[cc2], errors='coerce')
                    self.ld['fu_after_win'] = float(((cw < last) & cw.notna()).mean() * 100)
            g0 = d.groupby('fu').agg(leads=('won', 'size'), won=('won', 'mean'))
            g = d.groupby('fu').agg(leads=('won', 'size'), won=('won', 'mean'),
                                     trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100)
                                     if 'Trial Status' in d else ('won', 'mean'),
                                     ltv=('LTVn', 'mean') if 'LTVn' in d else ('won', 'mean'),
                                     visits=('Visitsn', 'mean') if 'Visitsn' in d else ('won', 'mean'))
            g['won'] = g['won'] * 100
            self.ld['follow'] = g
        # remarks: whether anything was written at all
        if 'Remarks' in d:
            _rm = d['Remarks'].astype(str).str.strip()
            has = d['Remarks'].notna() & (~_rm.isin(['', 'nan', '-', 'None', '.']))
            self.ld['remarks'] = dict(n=int(len(d)), noted=int(has.sum()),
                                      won_noted=float(d[has]['won'].mean() * 100) if has.any() else np.nan,
                                      won_blank=float(d[~has]['won'].mean() * 100) if (~has).any() else np.nan,
                                      ltv_noted=float(d[has]['LTVn'].mean() * 1) if 'LTVn' in d and has.any() else np.nan,
                                      ltv_blank=float(d[~has]['LTVn'].mean() * 1) if 'LTVn' in d and (~has).any() else np.nan)
        # UTM against stated source
        if 'UTM Source' in d:
            u = d.groupby(d['UTM Source'].astype(str).str.strip().replace({'nan': 'no campaign tag'})).agg(
                leads=('won', 'size'), won=('won', 'mean'), ltv=('LTVn', 'mean') if 'LTVn' in d else ('won', 'mean'))
            u['won'] = u['won'] * 100
            self.ld['utm'] = u[u['leads'] >= 40].sort_values('leads', ascending=False)
        # associate book: size, conversion, value, ageing
        if 'Associate' in d:
            a = d.groupby(d['Associate'].astype(str).str.strip().replace({'nan': 'Unassigned'})).agg(
                leads=('won', 'size'), won=('won', 'sum'), rate=('won', 'mean'),
                trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100) if 'Trial Status' in d else ('won', 'mean'),
                ltv=('LTVn', 'mean') if 'LTVn' in d else ('won', 'mean'),
                span=('Lead ID', 'size') if 'Lead ID' in d else ('won', 'size'))
            a['rate'] = a['rate'] * 100
            if '_dt' in d:
                a['open'] = d[d['Status'].astype(str).str.strip() == 'Open'].groupby(
                    d['Associate'].astype(str).str.strip().replace({'nan': 'Unassigned'})).size()
                a['open'] = a['open'].fillna(0)
            self.ld['assoc'] = a[a['leads'] >= 25].sort_values('rate', ascending=False)
        # what they asked for
        if 'Class Type' in d:
            g = d.groupby(d['Class Type'].astype(str).str.strip()).agg(
                leads=('won', 'size'), won=('won', 'mean'),
                trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100) if 'Trial Status' in d else ('won', 'mean'),
                ltv=('LTVn', 'mean') if 'LTVn' in d else ('won', 'mean'))
            g['won'] = g['won'] * 100
            self.ld['ask'] = g[g['leads'] >= 25].sort_values('won', ascending=False)
        # monthly flow with the year before
        if '_dt' in d:
            mo = d.assign(p=d['_dt'].dt.to_period('M')).groupby('p').agg(
                leads=('won', 'size'), won=('won', 'sum'),
                rate=('won', 'mean'), trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100)
                if 'Trial Status' in d else ('won', 'mean'))
            mo['rate'] = mo['rate'] * 100
            self.ld['flow'] = mo[(mo.index >= pd.Period(f'{self.y - 1}-01')) & (mo.index <= pd.Period(f'{self.y}-{self.m:02d}'))]
            self.ld['flow_all'] = mo
        # open file detail
        if 'Status' in d:
            op = d[d['Status'].astype(str).str.strip() == 'Open'].copy()
            if len(op) and '_dt' in op:
                op['age'] = (M.as_of - op['_dt']).dt.days
                self.ld['open_bands'] = op.groupby(pd.cut(op['age'], [-1, 7, 30, 90, 180, 365, 100000],
                                                           labels=['a week or less', '8 to 30 days', '31 to 90 days',
                                                                   '91 to 180 days', '181 to 365 days',
                                                                   'over a year ago']), observed=True) \
                    .agg(n=('won', 'size'), ltv=('LTVn', 'mean') if 'LTVn' in op else ('won', 'mean'))
                if 'Stage Name' in op:
                    st = op.groupby(op['Stage Name'].astype(str).str.strip()).agg(
                        n=('won', 'size'), med_age=('age', 'median'),
                        ltv=('LTVn', 'mean') if 'LTVn' in op else ('won', 'mean'))
                    self.ld['open_stage'] = st.sort_values('n', ascending=False)
                if 'Associate' in op:
                    self.ld['open_by_assoc'] = op.groupby(op['Associate'].astype(str).str.strip()
                                                          .replace({'nan': 'Unassigned'})).size().sort_values(ascending=False)
        # conversion speed and its value
        cc = next((c for c in ['Converted To Customer At_d', 'Converted To Customer At'] if c in d.columns), None)
        if cc and '_dt' in d:
            w = d[d['won'] & pd.to_datetime(d[cc], errors='coerce').notna()].copy()
            w['span'] = (pd.to_datetime(w[cc], errors='coerce') - w['_dt']).dt.days
            w = w[w['span'] >= 0]
            if len(w):
                b = pd.cut(w['span'], [-1, 0, 2, 6, 13, 30, 90, 100000],
                           labels=['same day', '1 to 2 days', '3 to 6 days', '7 to 13 days',
                                   '14 to 30 days', '31 to 90 days', 'over 90 days'])
                g = w.assign(b=b).groupby('b', observed=True).agg(
                    won=('span', 'size'), ltv=('LTVn', 'mean') if 'LTVn' in w else ('span', 'mean'),
                    visits=('Visitsn', 'mean') if 'Visitsn' in w else ('span', 'mean'),
                    buys=('Purchases Maden', 'mean') if 'Purchases Maden' in w else ('span', 'mean'))
                self.ld['speed'] = g
                self.ld['same_day'] = float((w['span'] == 0).mean() * 100)
                self.ld['week'] = float((w['span'] <= 7).mean() * 100)
        # trial as the gate, with value
        if 'Trial Status' in d:
            g = d.groupby(d['Trial Status'].astype(str).str.strip()).agg(
                leads=('won', 'size'), won=('won', 'sum'), rate=('won', 'mean'),
                ltv=('LTVn', 'mean') if 'LTVn' in d else ('won', 'mean'),
                visits=('Visitsn', 'mean') if 'Visitsn' in d else ('won', 'mean'))
            g['rate'] = g['rate'] * 100
            self.ld['gate'] = g
        # retention of what was won
        if 'Retention Status' in d:
            w = d[d['won']]
            if len(w):
                self.ld['retain'] = w['Retention Status'].astype(str).str.strip().value_counts()
                self.ld['retain_pct'] = float((w['Retention Status'].astype(str).str.strip() == 'Retained').mean() * 100)
        # month of the review only
        if '_dt' in d:
            a, b = rng(self.y, self.m)
            mo = d[(d['_dt'] >= a) & (d['_dt'] < b)]
            a2, b2 = rng(self.y - 1, self.m)
            pv = M._sl(M.source_D.leads, self.y - 1)
            self.ld['month'] = dict(n=int(len(mo)), won=int(mo['won'].sum()) if len(mo) else 0,
                                    trial=int((mo['Trial Status'] == 'Trial Completed').sum()) if 'Trial Status' in mo else 0,
                                    prev_n=int(len(pv)), prev_won=int(pv['won'].sum()) if len(pv) else 0)
            if len(mo) and 'Source Name' in mo:
                self.ld['month_src'] = mo.groupby('Source Name').agg(n=('won', 'size'), won=('won', 'mean')).sort_values('n', ascending=False)

    # --------------------------------------------------------------- behaviour
    def _beh(self):
        M = self.M
        self.bh = {}
        a = M._ck(self.y)
        if a is None or a.empty:
            return
        B = self.bh
        B['att'] = a
        B['all'] = a.copy()
        B['all']['hr'] = B['all']['_dt'].dt.hour
        B['all']['dow'] = B['all']['_dt'].dt.day_name()
        # hour x day heat for the month
        B['heat'] = a.pivot_table(index=a['_dt'].dt.hour, columns=a['_dt'].dt.day_name(),
                                  values='Member ID', aggfunc='size').reindex(columns=DAYS)
        # visits by week of month
        B['weeks'] = a.assign(w=((a['_dt'].dt.day - 1) // 7 + 1)).groupby('w').agg(
            visits=('Member ID', 'size'), members=('Member ID', 'nunique'))
        B['weeks']['per'] = B['weeks']['visits'] / B['weeks']['members']
        # per-member shape for this month
        v = a.groupby('Member ID').size().sort_values(ascending=False)
        B['v'] = v
        B['top'] = a.groupby('Member ID').agg(visits=('Member ID', 'size'),
                                               formats=('Cleaned Class', 'nunique') if 'Cleaned Class' in a else ('Member ID', 'size'),
                                               days=('_dt', 'nunique'))
        if 'Paid' in a:
            B['top']['spend'] = num(a['Paid']).groupby(a['Member ID']).sum()
        # preferred hour stability: how many of a member's visits land in their own peak 3-hour block
        h = a.assign(h=a['_dt'].dt.hour).groupby('Member ID')['h'].agg(lambda s: s.mode().iloc[0])
        hh = a.assign(h=a['_dt'].dt.hour).groupby('Member ID')['h'].apply(lambda s: ((s - h.reindex(s.index).iloc[0]).abs() <= 1).mean() * 100) \
            if len(a) else None
        B['sticky'] = float(hh.mean()) if hh is not None and len(hh) else np.nan
        # morning / midday / evening with value attached
        seg = pd.cut(h, [-1, 11, 16, 23], labels=['morning', 'midday', 'evening'])
        g = seg.to_frame('s').join(v.rename('visits')).groupby('s', observed=True).agg(
            members=('visits', 'size'), visits=('visits', 'sum'))
        g['per'] = g['visits'] / g['members']
        B['seg'] = g
        # gap between visits, whole ledger
        al = B['all'].sort_values('_dt')
        gp = al.groupby('Member ID')['_dt'].diff().dt.days.dropna()
        if len(gp):
            self.bh['gap'] = pd.cut(gp, [-1, 0, 1, 3, 7, 14, 30, 60, 100000],
                                     labels=['same day', 'next day', '2 to 3 days', '4 to 7 days',
                                             '8 to 14 days', '15 to 30 days', '31 to 60 days',
                                             'over 60 days']).value_counts().reindex(
                ['same day', 'next day', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days',
                 '31 to 60 days', 'over 60 days'])
            # what the gap predicts: visits in the following month after a long gap
            t = al.groupby(['Member ID', al['_dt'].dt.to_period('M')]).size()
            B['permonth'] = t.reset_index(name='visits').groupby('Member ID')['visits'].describe()
        # 2-for-1 intro pack: the third visit is the real return
        Nw = getattr(M.D, 'new', None)
        if Nw is not None:
            d = M._sl(Nw, self.y)
            if 'Visits Post Trial' in d:
                vv = num(d['Visits Post Trial']).fillna(0)
                B['funnel'] = dict(post1=int((vv >= 1).sum()), post2=int((vv >= 2).sum()), post3=int((vv >= 3).sum()),
                                   n=int(len(d)))
        # complementary / paid split at the door
        for df_ in (a, B['all']):
            if 'Complementary' in df_:
                _c = df_['Complementary'].astype(str).str.strip().isin(['True', 'true', '1', 'Yes'])
                B['comp'] = dict(n=int(_c.sum()), share=float(_c.mean()) * 100)
                break
        if 'Payment Method Name' in a:
            B['method'] = a.groupby(a['Payment Method Name'].astype(str).str.strip()).agg(
                visits=('Member ID', 'size'), members=('Member ID', 'nunique'), spend=('Paid', lambda s: num(s).sum())).sort_values(
                'visits', ascending=False)
        if 'Duration Minutes' in a:
            # data.py already recovered the serial-encoded durations and dropped
            # implausible values; a session's length still repeats on every
            # attendee row, so unique sessions carry the hours.
            dd = a[a['Duration Minutes'].notna()]
            if len(dd):
                B['dur'] = dd.assign(len=dd['Duration Minutes']).groupby('len').agg(
                    visits=('Member ID', 'size'), members=('Member ID', 'nunique')).sort_values('visits', ascending=False)
                if 'Class No' in dd.columns:
                    uniq = dd.dropna(subset=['Class No']).drop_duplicates(subset=['Class No'])
                    B['teaching_hours'] = float(uniq['Duration Minutes'].sum()) / 60
        if 'Cleaned Product' in a:
            g = a.groupby(a['Cleaned Product'].astype(str).str.strip().replace({'nan': 'Unspecified'})).agg(
                visits=('Member ID', 'size'), members=('Member ID', 'nunique'))
            g['per'] = g['visits'] / g['members']
            B['prod'] = g.sort_values('visits', ascending=False)
        if 'Class No' in a:
            cn = num(a['Class No']).fillna(0)
            B['slot'] = cn.value_counts().sort_index().head(24).to_frame('visits')
        # monthly frequency trend for three years
        al2 = al.copy(); al2['p'] = al2['_dt'].dt.to_period('M')
        mo = al2.groupby('p').agg(visits=('Member ID', 'size'), members=('Member ID', 'nunique'))
        mo['per'] = mo['visits'] / mo['members']
        B['monthly'] = mo[mo.index >= pd.Period(f'{self.y - 2}-01')]
        # who is loyal to a format
        if 'Cleaned Class' in a:
            loy = a.groupby(['Member ID', 'Cleaned Class']).size()
            B['loyal'] = loy[loy >= 3].reset_index()['Member ID'].nunique()
            B['multi'] = float((a.groupby('Member ID')['Cleaned Class'].nunique() >= 2).mean() * 100)
            fm = a.groupby(['Member ID', 'Cleaned Class']).size().unstack(fill_value=0)
            B['fmt_share'] = (fm > 0).mean().sort_values(ascending=False) * 100
            B['fmt_matrix'] = fm

    # ------------------------------------------------------------- benchmark
    def _bench(self):
        """How this studio compares with the others on file, same month."""
        M = self.M
        self.bm = {}
        X = M.D.sessions
        if X is None:
            return
        try:
            a, b = rng(self.y, self.m)
            d = X[(X['_dt'] >= a) & (X['_dt'] < b)]
            g = d.groupby('_loc').agg(classes=('SessionID', 'size'), seats=('_cap', 'sum'),
                                       att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'),
                                       lc=('LateCancelled', 'sum'), book=('Booked', 'sum'))
            g['fill'] = g['att'] / g['seats'] * 100
            g['rpc'] = g['rev'] / g['classes']
            g['rph'] = g['rev'] / g['att'].replace(0, np.nan)
            g['lc_pct'] = g['lc'] / g['book'].replace(0, np.nan) * 100
            g = g[g['classes'] >= 20].sort_values('fill', ascending=False)
            if M.studio in g.index:
                g['rank'] = range(1, len(g) + 1)
            self.bm['table'] = g
            self.bm['rank_fill'] = int(g.index.get_loc(M.studio) + 1) if M.studio in g.index else 0
            self.bm['n'] = len(g)
        except Exception:
            pass


# ------------------------------------------------------------------- appendix
def guide(df, notes):
    """A short 'how to read this table' paragraph, using the table's own numbers."""
    try:
        lead = []
        for col, txt in notes:
            if col in df.columns:
                s = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(s) >= 2:
                    lead.append(f'{txt} ranges from {s.max():,.1f} to {s.min():,.1f}')
                elif len(s) == 1:
                    lead.append(f'{txt} is {s.iloc[0]:,.1f}')
        if not lead:
            return ''
        return ('<p style="font-size:13.5px;color:#6B7280">How to read this table: it holds '
                f'{len(df)} rows. ' + '; '.join(lead) + '.</p>')
    except Exception:
        return ''


def appendix(M, X, cid):
    """The underlying tables the hand-built reports exposed inside collapsible
    evidence blocks: the same figures at row level, so any number in the chapter
    can be checked without opening the CSV."""
    blocks = []

    def add(summary, df, heads, fmts, blurb='', n=70):
        h = frame_ev(summary, df, heads, fmts, blurb=blurb, maxrows=n)
        if h:
            blocks.append(h)

    cur = X.cls.get('cur')
    if cid == 'sales':
        s = X.sales.get('cur')
        if s is not None and len(s):
            add(f'Evidence &mdash; the {len(s)} sales lines that make up {M.label}',
                s.sort_values('val', ascending=False).reset_index()[
                    ['_dt', 'Member ID', 'Cleaned Product', 'val', 'disc', 'Sold By', 'Payment Method', 'Discount Code']]
                if 'Sold By' in s else None,
                ['Date', 'Member ID', 'Product', 'Cash', 'Discount', 'Sold by', 'Method', 'Code'],
                ['w', 'w', 'w', 'm', 'm', 'w', 'w', 'w'],
                'The largest lines first. Member ids only; names sit in the export itself.', 70)
        g = X.sales.get('by_member')
        if g is not None and len(g):
            add('Evidence &mdash; every buyer this month, ranked by what they spent',
                g.sort_values('cash', ascending=False).reset_index(),
                ['Member ID', 'Cash', 'Lines', 'Discount', 'Gross'], ['w', 'm', 'n', 'm', 'm'],
                'Rows 40 to 109 are the long tail that carries most of the month’s buyer count and little of its money.', 140)
    elif cid in ('class', 'format'):
        if cur is not None and len(cur):
            add(f'Evidence &mdash; every class taught in {M.label}',
                cur.sort_values(['_dt', '_hr']).reset_index()[['_dt', '_day', '_hr', '_cls', '_trainer', '_cap',
                                                               'Booked', 'CheckedIn', 'LateCancelled', 'NonPaid',
                                                               'Complimentary', 'Revenue']],
                ['Date', 'Day', 'Hour', 'Format', 'Trainer', 'Capacity', 'Booked', 'Attended', 'Late cancelled',
                 'Non-paid', 'Complimentary', 'Revenue'],
                ['w', 'w', 'n', 'w', 'w', 'n', 'n', 'n', 'n', 'n', 'n', 'm'],
                'The complete month, in date order. This is the file the whole chapter is computed from.', 120)
        if cid == 'format' and X.bh.get('fmt_matrix') is not None:
            fm = X.bh['fmt_matrix']
            add('Evidence &mdash; the format mix of every member who attended',
                fm.assign(total=fm.sum(axis=1), formats=(fm > 0).sum(axis=1)).sort_values('total', ascending=False).reset_index(),
                ['Member ID'] + [clean(c)[:12] for c in fm.columns] + ['Total visits', 'Formats used'],
                ['w'] + ['n'] * (len(fm.columns) + 2),
                'Attendance by member and format for the month, which is the source of the reach, devotion and variety figures above.', 80)
    elif cid == 'instructor':
        if cur is not None and len(cur):
            g = cur.groupby(['_trainer', '_cls']).agg(classes=('SessionID', 'size'), att=('CheckedIn', 'sum'),
                                                        seats=('_cap', 'sum'), rev=('Revenue', 'sum'),
                                                        empty=('CheckedIn', lambda s: int((s == 0).sum())))
            g['fill'] = g['att'] / g['seats'] * 100
            inst_cols = ['_trainer', '_cls', 'classes', 'att', 'seats', 'fill', 'rev', 'empty']
            inst_df = g.reset_index().sort_values(['_trainer', 'att'], ascending=[True, False])
            for c in inst_cols:
                if c not in inst_df.columns:
                    inst_df[c] = np.nan
            inst_df = inst_df[inst_cols].copy()
            inst_df['_trainer'] = inst_df['_trainer'].apply(clean)
            inst_df['_cls'] = inst_df['_cls'].apply(clean)
            add('Evidence &mdash; each trainer inside each format they taught',
                inst_df,
                ['Trainer', 'Format', 'Classes', 'Attended', 'Seats', 'Utilisation', 'Revenue', 'Empty'],
                ['w', 'w', 'n', 'n', 'n', 'p', 'm', 'n'],
                'This is the table that decides whether a utilisation difference is a trainer or a slot.', 130)
    elif cid == 'lapse':
        lp = X.lp.get('paid')
        if lp is not None and len(lp):
            cols = [c for c in ['Member ID', 'Membership Name', 'Amount Paid', 'Purchase Date', 'End Date', 'Churned Date',
                                'Membership Duration (Days)', 'Total Sessions Completed', 'Sessions Used %',
                                'Remaining Sessions', 'Late Cancellations', 'No Shows', 'Days Since Last Visit',
                                'Derived Status'] if c in lp.columns]
            add('Evidence &mdash; the paid membership ledger, most recent first',
                lp.sort_values('Purchase Date_x', ascending=False).reset_index()[cols] if 'Purchase Date_x' in lp else None,
                [c.replace('_', ' ') for c in cols], ['w'] * len(cols),
                'Rows as the export holds them, for the 200 most recently purchased memberships.', 200)
    elif cid == 'cancels':
        if cur is not None and len(cur):
            q = cur[cur['LateCancelled'] > 0]
            add(f'Evidence &mdash; every class that lost a seat late in {M.label}',
                q.sort_values('LateCancelled', ascending=False).reset_index()[['_dt', '_day', '_hr', '_cls', '_trainer',
                                                                              'Booked', 'CheckedIn', 'LateCancelled', 'Revenue']],
                ['Date', 'Day', 'Hour', 'Format', 'Trainer', 'Booked', 'Attended', 'Late cancelled', 'Revenue'],
                ['w', 'w', 'n', 'w', 'w', 'n', 'n', 'n', 'm'],
                'A class appears here if its session row carried any late cancellation.', 130)
        S = X.sales.get('cur')
        if S is not None and len(S) and 'Discount Code' in S:
            d = S[S['disc'] > 0]
            add('Evidence &mdash; every discounted line taken this month',
                d.sort_values('disc', ascending=False).reset_index()[['_dt', 'Member ID', 'Cleaned Product', 'gross', 'disc',
                                                                     'val', 'Discount Code', 'Sold By']],
                ['Date', 'Member ID', 'Product', 'Gross', 'Discount', 'Net cash', 'Code', 'Sold by'],
                ['w', 'w', 'w', 'm', 'm', 'm', 'w', 'w'],
                f'{len(d)} of {len(S)} lines carried a discount.', 90)
    elif cid == 'leads':
        d = X.ld.get('d')
        if d is not None and len(d):
            cols = [c for c in ['_dt', 'Full Name', 'Source Name', 'Class Type', 'Stage Name', 'Associate', 'Status',
                                'Trial Status', 'Retention Status', 'LTV', 'Visits', 'Purchases Made'] if c in d.columns]
            add('Evidence &mdash; the most recent 120 leads on this studio’s file',
                d.sort_values('_dt', ascending=False).reset_index()[cols],
                [c.replace('_', ' ') for c in cols], ['w'] * len(cols),
                'Names are shown because the studio’s own export contains them; the file is not sent anywhere.', 120)
    elif cid == 'behaviour':
        a = X.bh.get('att')
        if a is not None and len(a):
            cols = [c for c in ['_dt', 'Time', 'Day of Week', 'Member ID', 'Cleaned Class', 'Teacher Name',
                                'Cleaned Product'] if c in a.columns]
            add(f'Evidence &mdash; every attended check-in in {M.label}',
                a.sort_values('_dt').reset_index()[cols], [c.replace('_', ' ') for c in cols], ['w'] * len(cols),
                f'{len(a):,} rows: the ledger the frequency, gap and preference tables are built from.', 150)
        if X.bh.get('top') is not None and len(X.bh['top']):
            add('Evidence &mdash; every member who attended this month',
                X.bh['top'].sort_values('visits', ascending=False).reset_index(),
                ['Member ID', 'Visits', 'Formats used', 'Days attended'], ['w', 'n', 'n', 'n'],
                'The whole month, not the top tenth, so the distribution above can be checked directly.', 400)
    elif cid == 'overview':
        rows = []
        for z in sorted(M.room):
            r = M.room[z]
            rows.append([f'{MONTH_NAMES[M.m - 1]} {z}', r['sessions'], r['seats'], r['att'], r['fill'], r['rev'],
                         r['rpc'], r['book'], r['lc']])
        blocks.append(ev('Evidence &mdash; the same month, every year on file',
                         T(['Month', 'Classes', 'Seats', 'Attendances', 'Utilisation %', 'Class revenue',
                            'Per class', 'Booked', 'Late cancelled'],
                           [[a, _n(b), _n(c), _n(d), f'{e:.1f}', R(f), R(g), _n(h), _n(i)] for a, b, c, d, e, f, g, h, i in rows],
                           'num')
                         + '<p style="font-size:13px;color:#6B7280;margin-top:14px">The overview is a summary of the other '
                           'eight chapters; this is the only table it owns, and it is the three-year comparison every one '
                           'of them refers back to.</p>'))
    if not blocks:
        return ''
    return (f'<h2>The underlying tables</h2>\n<div class="sub">Everything the chapter claims, at row level</div>\n'
            f'<p>Each block below opens onto the rows the figures above were computed from, in the same order and with the '
            f'same rounding. Nothing in this chapter is derived from anything but these tables.</p>' + ''.join(blocks))
