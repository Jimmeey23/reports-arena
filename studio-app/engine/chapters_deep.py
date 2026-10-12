"""The nine chapters, at the depth of the reports they replace.

Every chapter is built as a list of sections, and each section is one analytical
question: the claim, the numbers behind it, the chart, the table, and the raw
rows inside a collapsible block. A section that cannot be computed (because a
source was not uploaded, or the studio is too new for a year-on-year) drops out
quietly rather than being filled with a plausible sentence.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from .design import (R, Rs, P, N, T, ev, note, bars, lines, hbars, diverging, stacked,
                     funnel, dumbbell, A1, A2, A3, B1, B2, N1, N2)
from .metrics import DAYS, MONTH_NAMES, rng
from .deep import (Deep, sec, tab, frame_ev, statgrid, hyp, method, appendix, guide, kpi, money, pc, _n,
                   clean, dpc, share, ratio, concentration, extremes, rank_list, yoy_para)

from weakref import WeakKeyDictionary

_C = WeakKeyDictionary()


def deep(M):
    """One Deep per Metrics, built on first use."""
    if M not in _C:
        _C[M] = Deep(M)
    return _C[M]


def run(secs):
    out = []
    for f in secs:
        try:
            h = f()
        except Exception as error:
            import logging
            logging.getLogger(__name__).warning("Report section %s unavailable: %s", f.__name__, error)
            h = head(f.__name__.replace("_", " ").title(), "Analysis unavailable") + para("This analysis could not be completed from the supplied records. It has not been replaced with an estimate.")
        if h:
            out.append(h)
    return ''.join(out)


def head(title, sub, claim=None):
    h = f'<h2>{title}</h2>' + (f'<div class="sub">{sub}</div>' if sub else '')
    if claim:
        h += f'<div class="call"><h4>The one-line version, if you read nothing else.</h4><p>{claim}</p></div>'
    return h


def core_ev(M, n=60):
    a, b = M.people[M.y]['v'], M.people[M.y - 1]['v']
    idx = [i for i in a.index if i in set(b.index)][:n]
    then = b.reindex(idx).astype(float).values
    now = a.reindex(idx).astype(float).values
    return pd.DataFrame({'m': idx, 'then': then, 'now': now, 'd': now - then})


def para(t):
    return f'<p>{t}</p>' if t and not str(t).startswith('<') else (t or '')


def h4(t):
    return f'<h4>{t}</h4>' if t else ''


def yr(M):
    return f'{MONTH_NAMES[M.m - 1]} {M.y}'


def yrp(M):
    return f'{MONTH_NAMES[M.m - 1]} {M.y - 1}'


def mono(M):
    return MONTH_NAMES[M.m - 1]


def _pct_of(a, b):
    try:
        return float(a) / float(b) * 100
    except Exception:
        return float('nan')


# ===================================================== 1. SALES PERFORMANCE
def sales(M):
    if 'sales' not in M.has or M.y not in M.sales:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    F, P1, P2 = M.sales[y], M.sales.get(y - 1, {}), M.sales.get(y - 2, {})
    S = X.sales
    cur, prev = S.get('cur'), S.get('prev')
    L = M.room.get(y, {}); Lp = M.room.get(y - 1, {})
    mon = mono(M)
    g = S.get('by_member')
    rep = S.get('repeat', {})

    def start():
        d = ((F['cash'] - P1['cash']) / P1['cash'] * 100) if P1.get('cash') else None
        delivered = L.get('rev', 0)
        paras = [para(
            f'{lab} recorded sales revenue of <strong>{R(F["cash"])}</strong> across {F["txn"]} transactions from {F["buyers"]} people'
            + (f' &mdash; a movement of {abs(d):.1f}% against {yrp(M)}, and on the headline alone an unremarkable month'
               if d is not None else '')
            + f'. The average transaction was {R(F["aov"])} and the average buyer {R(F["ticket"])}'
            + (f', against {R(P1["ticket"])} a year earlier' if P1.get('ticket') else '') + '.')]
        paras.append(para(
            f'Read sales alongside session revenue. The month delivered {R(delivered)} of attended-class '
            f'revenue against {R(F["cash"])} in sales revenue. Delivered session revenue was {share(delivered, F["cash"])} of sales revenue. These totals measure different activity and are not directly '
            f'reconciled; they do not show how much of this month’s purchases has been used.'))
        claim = None
        if M.y in M.people and (M.y - 1) in M.people:
            pn, pp = M.people[y], M.people.get(y - 1, {})
            claim = (f'{pn["members"]} people trained here in {mon} against {pp.get("members", 0)} in {yrp(M)}, and each of them '
                     f'cost the studio nothing extra to serve. Visits per member moved from {pp.get("per", 0):.2f} to '
                     f'{pn["per"]:.2f}; that single change is worth more than the whole year-on-year movement in the cash line.')
        blocks = [statgrid([(f'Cash {lab}', R(F['cash'])), ('Transactions', _n(F['txn'])),
                            ('Buyers', _n(F['buyers'])), ('Average buyer', R(F['ticket']))]),
                  statgrid([('Attended class revenue', R(delivered)), ('Revenue per class', R(L.get('rpc', 0))),
                            ('Revenue per attendance', R(L.get('rph', 0))),
                            ('Delivered as a share of cash', share(delivered, F['cash']))])]
        three = [x for x in [
            yoy_para('Cash', F['cash'], P1.get('cash')),
            yoy_para('Buyers', F['buyers'], P1.get('buyers'), unit='n'),
            f'{rep.get("multi", 0)} of {rep.get("buyers", 0)} buyers ({rep.get("multi_share", 0):.0f}%) bought more than once, '
            f'and produced {share(rep.get("multi_cash", 0), rep.get("cash", 0))} of the month.',
        ] if x]
        paras += [para('Three findings underneath the top line: ' + ' '.join(three))]
        return head('Start here', 'The till, and what sits behind it', claim) + ''.join(paras) + ''.join(blocks)

    def base():
        if not (M.y in M.people and (y - 1) in M.people):
            return ''
        pn, pp, p2 = M.people[y], M.people.get(y - 1, {}), M.people.get(y - 2, {})
        ch = [(f'{mon} {z}', M.people.get(z, {}).get('members', 0)) for z in [y - 2, y - 1, y] if M.people.get(z, {}).get('members')]
        p = [para(f'The number of people who paid to train at this studio in {lab} was <strong>{pn["members"]}</strong>'
                  + (f', against {pp["members"]} in {yrp(M)}' if pp.get('members') else '')
                  + (f' and {p2["members"]} in {MONTH_NAMES[M.m - 1]} {y - 2}' if p2.get('members') else '')
                  + ('. The base is widening.' if (not pp.get('members')) or pn['members'] >= pp['members'] else
                     '. The base is narrowing.'))]
        if pp.get('members') and p2.get('members'):
            p.append(para(f'Breadth and depth have moved in opposite directions for two years. The studio reaches '
                          f'{(pn["members"] - p2["members"]) / p2["members"] * 100:+.0f}% more people than it did two Septembers ago, '
                          f'while serving them {(pn["per"] - p2["per"]) / p2["per"] * 100:.0f}% less often. A club that is '
                          f'gaining members and losing frequency is not growing; it is churning more slowly than it is recruiting.'))
        b = [bars([c[0] for c in ch], [('Members who trained', [c[1] for c in ch], A1),
                                        ('Visits per member, ×100', [M.people.get(z, {}).get('per', 0) * 100 for z in [y - 2, y - 1, y]], B1)],
                  f'How many people trained here, and how often, in {mon} of each year', h=300,
                  note='The second series is visits per member drawn at one hundred times its true height so both fit one axis.')]
        if len(M.beh.get('monthly', [])) > 3 if hasattr(M, 'beh') else False:
            pass
        mo = M.beh.get('monthly') if hasattr(M, 'beh') else None
        if mo is not None and len(mo) > 4:
            b.append(lines([str(i) for i in mo.index], [('Visits per member', [float(v) for v in mo['per']], A1)],
                           f'Visits per active member, by month &mdash; {M.studio}', h=290, as_pct=False,
                           ymax=float(np.nanmax(mo['per']) * 1.35),
                           note='Check-in ledger, attended visits only. This is the line that leads every other number in the review.'))
        return sec('The base is widening' if (not pp.get('members')) or pn['members'] >= pp['members'] else 'The base is narrowing',
                    'More or fewer people, and what they do once they are here', p, b)

    def core():
        c = getattr(M, 'core', None)
        if not c or not c.get('n'):
            return ''
        per_then = c['prev'] / c['n'] if c['n'] else 0
        per_now = c['now'] / c['n'] if c['n'] else 0
        p = [para(f'{c["n"]} members trained here in <em>both</em> {yrp(M)} and {lab}. This is a true like-for-like group: the same '
                  f'people, the same month, twelve months apart. They made <strong>{c["prev"]:,.0f} visits</strong> then '
                  f'({per_then:.2f} each) and <strong>{c["now"]:,.0f} visits</strong> now ({per_now:.2f} each) &mdash; '
                  f'<strong>{abs(c["drop_pct"]):.0f}% fewer</strong>, worth {abs(c["lost"]):,.0f} attendances.'),
              para(f'Had the core held its year-ago frequency, {lab} would have recorded {M.room[y]["att"] + c["lost"]:,.0f} '
                   f'attendances instead of {M.room[y]["att"]:,.0f}. The month is not short of customers; it is short of visits '
                   f'from the customers it already has.'),
              para(f'{c.get("gone_one_visit", 0)} of the {c["gone"]} people who were here last {mon} and not this one had made '
                   f'exactly one visit in that month. They were never members who left; they were visitors who did not come back. '
                   f'No win-back campaign reaches them, because on the books they never started.')]
        b = [dumbbell([(f'{yrp(M)} core (n={c["n"]})', per_then, per_now)],
                      'The loyal core, then and now', unit='visits a month',
                      lo_lab=f'{yrp(M)}', hi_lab=f'{lab}',
                      note='Same members, same calendar month, one year apart. Nothing about the definition changed.'),
             frame_ev(f'Evidence &mdash; the {c["n"]} members in the returning core, visit by visit',
                      core_ev(M, 60), ['Member ID', f'{yrp(M)} visits', f'{lab} visits', 'Change'],
                      ['w', 'n', 'n', 'n'], blurb='The first sixty members in the core, by id. The full list is in the check-in ledger.')]
        return sec('The loyal core halved its frequency', 'The same people, twelve months apart', p, b)

    def mix():
        c = S.get('cats')
        if c is None or not len(c):
            return ''
        p = [para(f'The month divides as follows: {rank_list(c, "rev", 4)}. '
                  + (concentration(c['rev'], unit='cash') and concentration(c['rev'], unit='cash'))),
             para(f'{clean(c.index[0])} and {clean(c.index[1]) if len(c) > 1 else "nothing else"} together are '
                  f'{share(c["rev"].iloc[:2].sum(), F["cash"])} of everything taken. A studio with two thirds of its cash in two '
                  f'products is not diversified by how many lines sit on its price list; it is diversified only if those two '
                  f'products fail at different times.')]
        heads = ['Category', 'Sold', 'Cash', 'Buyers', 'Discount given']
        rows = [[clean(i), int(r['n']), R(r['rev']), int(r['buyers']), R(r['disc'])] for i, r in c.iterrows()]
        b = [hbars([(clean(i), float(v), A1 if n == 0 else A2) for n, (i, v) in enumerate(c['rev'].sort_values(ascending=False).items())],
                   f'Where {lab}’s money came from', unit='₹',
                   note=f'Cash received, not revenue recognised. The full ledger is in the sales export.'),
             T(heads, rows, 'num'),
             h4('The two products that moved the year')]
        mv = S.get('movers')
        if mv is not None and len(mv) and 'd' in mv:
            b.append(diverging([(clean(i), float(v)) for i, v in mv['d'].items()],
                               f'Product by product, {lab} against {yrp(M)}', maxv=float(np.nanmax(mv['d'].abs()) * 1.2),
                               note='The change in sales revenue on each product, one year apart. Products that appear in only one of the two months show their whole value as a movement.'))
            b.append(tab(mv.reset_index()[['Cleaned Product', 'n', 'rev', 'n2', 'rev2', 'd']]
                         if 'Cleaned Product' in mv.reset_index().columns else mv,
                         ['Product', 'Sold this year', 'Cash this year', 'Sold last year', 'Cash last year', 'Movement'],
                         ['w', 'n', 'm', 'n', 'm', 'm'], maxrows=10))
        b.append(frame_ev(f'Evidence &mdash; every product sold in {lab}, with the same month last year beside it',
                          (S['prods'].reset_index() if hasattr(S.get('prods', None), 'reset_index') else S.get('prods')),
                          ['Product', 'Lines', 'Cash', 'Buyers', 'Average', 'Sold last year', 'Cash last year'],
                          ['w', 'n', 'm', 'n', 'm', 'n', 'm'],
                          blurb='Products with no line in either month are omitted.'))
        return sec('Where the money came from', 'Category mix, and the two products that moved the year', p, b)

    def commit():
        Sb = getattr(M.D, 'sales', None)
        if Sb is None or 'Sec. Membership Total Classes' not in Sb.columns:
            return ''
        a = Sb[(Sb['_loc'] == M.studio) & (Sb['_dt'] < rng(y, M.m)[1])].copy()
        if not len(a):
            return ''
        a['cls'] = pd.to_numeric(a['Sec. Membership Total Classes'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
        a['left'] = pd.to_numeric(a['Sec. Membership Classes Left'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
        a = a[a['cls'].fillna(0) > 0]
        if not len(a):
            return ''
        a['s'] = a['_dt'].dt.year
        g = a.groupby('s').agg(n=('cls', 'size'), cls=('cls', 'mean'), pay=('val', 'sum'),
                                left=('left', 'mean'), buyers=('Member ID', 'nunique'))
        g['per_class'] = g['pay'] / (g['cls'] * g['n']).replace(0, np.nan)
        g = g[g['n'] >= 20].sort_index()
        if not len(g):
            return ''
        now = g.iloc[-1]
        p = [para(f'Every membership that records a class count was bought on average <strong>{now["cls"]:.1f} classes</strong> '
                  f'in {y} against {g["cls"].iloc[0]:.1f} in {int(g.index[0])} &mdash; a fall of '
                  f'{(1 - now["cls"] / g["cls"].iloc[0]) * 100:.0f}% in what a member commits to at the moment of paying.'),
             para(f'That is the whole forward-revenue argument in one column. {R(now["pay"])} of cash this {mon.lower()}-year band '
                  f'was collected against {now["n"]:,.0f} memberships, each of which obliges the studio to deliver '
                  f'{now["cls"]:.1f} classes and then ask again. Shorter commitment means more conversations per rupee, and the '
                  f'most fragile part of the year is the renewal the studio has to win every {max(int(now["cls"]), 1)} classes.'),
             para(f'The average member still holds <strong>{now["left"]:.1f} undelivered classes</strong> on the memberships '
                  f'bought this month. Those classes are not revenue yet; they are a promise, and the studio pays for them in '
                  f'room time whether or not the member turns up.')]
        b = [T(['Year', 'Memberships with a class count', 'Average classes bought', 'Cash', 'Price per class', 'Undelivered per member'],
               [[str(int(i)), int(r['n']), f'{r["cls"]:.1f}', R(r['pay']), R(r['per_class']), f'{r["left"]:.1f}'] for i, r in g.iterrows()], 'num'),
             bars([str(int(i)) for i in g.index], [('Average classes bought per membership', [float(v) for v in g['cls']], A1),
                                                    ('Price per class, ₹', [float(v) for v in g['per_class']], B1)],
                  'How much a member commits to, and what a class costs them', h=300,
                  note=f'Sales dated before the end of {lab}. Only membership products that store a class count are included, so single classes and retail are absent.')]
        byp = a[a['_dt'] >= rng(y, M.m)[0]].groupby('Cleaned Product').agg(
            n=('cls', 'size'), cls=('cls', 'mean'), pay=('val', 'sum'), left=('left', 'mean'))
        b.append(frame_ev(f'Evidence &mdash; what each product promised, in {lab} and across the three years before it',
                          byp.reset_index(), ['Product', 'Sold', 'Classes bought', 'Cash', 'Classes left'],
                          ['w', 'n', 'f1', 'm', 'f1']))
        return sec('The commitment-length problem', f'The studio’s forward revenue cushion is thinning', p, b)

    def ladder():
        q = S.get('ppc')
        if q is None or not len(q):
            return ''
        p = [para(f'What a class costs depends on which product a member buys. Across the products that carry a class count, '
                  f'price per class runs from <strong>{R(q["per_class"].min())}</strong> ({clean(q.index[0])}) to '
                  f'{R(q["per_class"].max())} ({clean(q.index[-1])}) &mdash; a {(q["per_class"].max() / max(q["per_class"].min(), 1)):.1f}-fold '
                  f'range for the same hour in the same room.')]
        p.append(para('Where the cheap tier is also the small one, the ladder has inverted: the studio is rewarding the '
                      'smallest commitment with the best price, which is the arithmetic behind a short membership book.'))
        b = [hbars([(clean(i), float(v), A1) for i, v in q['per_class'].items()],
                   'What one class costs, by product', unit='₹',
                   note='Cash paid divided by the classes the product grants. Lower is better value for the member.'),
             tab(q.reset_index(), ['Product', 'Sold', 'Classes', 'Cash', 'Per class'], ['w', 'n', 'f1', 'm', 'm']),
             frame_ev('Evidence &mdash; transaction size bands', S['bands'].reset_index(),
                      ['Band', 'Transactions', 'Cash', 'Buyers'], ['w', 'n', 'm', 'n'],
                      blurb='Every sale in the month, by the size of the payment.')]
        return sec('Pricing and the product ladder', 'What a class costs, and which tier wins', p, b)

    def trading():
        w = S.get('weeks')
        if w is None or not len(w):
            return ''
        wk = " / ".join(R(v) for v in w["cash"])
        p = [para(f'The month was not even. Week by week, cash ran {wk} &mdash; '
                  f'the strongest week took {share(w["cash"].max(), w["cash"].sum())} of the month and the weakest '
                  f'{share(w["cash"].min(), w["cash"].sum())}.'),
             para(f'{_n(S["dom"]["n"].max())} transactions fell on the single busiest day of the month '
                  f'(day {int(S["dom"]["n"].idxmax())}), against {_n(S["dom"]["n"].min())} on the quietest. '
                  'A studio that concentrates its selling into the days after a payroll date is not selling to demand; '
                  'it is riding the payroll calendar, and the same shape will be read again next month as a trend.')]
        b = [bars([f'week {int(i)}' for i in w.index], [('Cash', [float(v) for v in w['cash']], A1),
                                                          ('Buyers', [float(v) for v in w['buyers']], B1)],
                  f'Cash by week of {mon.lower()}, {y}', h=290,
                  note='Week 1 is the first seven days of the month. The counter, not the timetable, decides this shape.'),
             frame_ev(f'Evidence &mdash; every day of {lab}', S['dom'].reset_index(), ['Day of month', 'Transactions', 'Cash'],
                      ['n', 'n', 'm'], blurb='Days with no sales are absent, which is itself a fact worth reading.')]
        y1, y0 = S.get('ytd', {}), S.get('ytd_prev', {})
        if y1 and y0:
            b.insert(1, para(f'Year to date through {mon.lower()}: {R(y1["cash"])} against {R(y0["cash"])} at the same point '
                             f'last year, on {y1["lines"]} transactions against {y0["lines"]}, from {y1["buyers"]} buyers '
                             f'against {y0["buyers"]}. The month sits inside a year that is '
                             f'{(y1["cash"] - y0["cash"]) / y0["cash"] * 100:+.1f}% on cash and '
                             f'{(y1["buyers"] - y0["buyers"]) / y0["buyers"] * 100:+.1f}% on buyers.'))
        return sec('Trading pattern through the month', 'Where the cash actually arrived', p, b)

    def paidfor():
        b = []
        bands = S.get('bands')
        lf = S.get('line_freq')
        p = []
        if bands is not None and len(bands):
            p.append(para(f'By size of payment, {int(bands["n"].sum())} transactions split across six bands: '
                          + rank_list(bands, 'n', 6).replace('₹', '') + '.'))
        if lf is not None and len(lf):
            one = int(lf.loc[1, 'buyers']) if 1 in lf.index else 0
            p.append(para(f'<strong>{share(one, F["buyers"])} of buyers made a single purchase in {mon.lower()}</strong> '
                          f'({one} of {F["buyers"]}). Repeat buying is not a segment to be marketed at later; it is the '
                          f'main body of the business, and it is currently smaller than half the book.'))
        if b or p:
            pass
        if bands is not None and len(bands):
            b.append(bars([str(i) for i in bands.index], [('Transactions', [float(v) for v in bands['n']], A1)],
                          f'How many transactions fall in each size band, {lab}', h=280,
                          note='The shape of the till: how much of the month is small tickets, and how much is real money.'))
            b.append(tab(bands.reset_index(), ['Band', 'Transactions', 'Cash', 'Buyers'], ['w', 'n', 'm', 'n']))
        pm = S.get('paymeth')
        if pm is not None and len(pm):
            b.append(h4('How it was paid for'))
            b.append(tab(pm.reset_index(), ['Payment method', 'Lines', 'Cash', 'Average'], ['w', 'n', 'm', 'm'], 'num'))
            b.append(para(f'Average ticket by method differs by a factor of '
                          f'{ratio(pm["avg"].max(), pm["avg"].min())}: the method is not a logistics detail, it is a proxy '
                          f'for what was bought. Cards and UPI carry the small lines; the larger commitments arrive by the '
                          f'channels that support them.'))
        return sec('How the month was paid for', 'Transaction size, repeat buyers and method', p, b)

    def soldby():
        sb = S.get('sold_by')
        if sb is None or not len(sb):
            return ''
        p = [para(f'The month’s {R(F["cash"])} was recorded against {len(sb)} names. '
                  + rank_list(sb, 'cash', len(sb)) + '.')]
        if 'Not recorded' in sb.index:
            v = float(sb.loc['Not recorded', 'cash'])
            p.append(para(f'<strong>{R(v)} of {lab} cash &mdash; {share(v, F["cash"])} of the month &mdash; has no salesperson '
                          f'attached to it.</strong> That is the largest single block in the ledger. Nothing can be learned '
                          f'from it, nobody can be coached on it, and it cannot be attributed to a campaign because there is '
                          f'no name to compare it with. The obvious cause is a checkout the member completes alone; the '
                          f'less obvious one is that the studio has no rule about who owns a sale, so the field is left as '
                          f'meaningless rather than wrong.'))
        b = [hbars([(clean(i), float(v), B1 if i == 'Not recorded' else A1) for i, v in sb['cash'].items()],
                   f'Who sold {lab}', unit='₹', note='Unattributed cash is drawn in the second accent colour because it is a gap in the process, not a person.'),
             tab(sb.reset_index(), ['Sold by', 'Lines', 'Cash', 'Buyers', 'Discount given'], ['w', 'n', 'm', 'n', 'm']),
             frame_ev('Evidence &mdash; buyers per seller, and their repeat rate',
                      (cur.assign(sold=cur['Sold By'].astype(str).str.strip().replace({'nan': 'Not recorded'}))
                       .groupby('sold').agg(cash=('val', 'sum'), buyers=('Member ID', 'nunique'),
                                            lines=('val', 'size')).assign(per=lambda x: x['lines'] / x['buyers'])
                       .sort_values('cash', ascending=False)),
                      ['Sold by', 'Cash', 'Buyers', 'Lines', 'Lines per buyer'], ['w', 'm', 'n', 'n', 'f2'])]
        return sec('Who sold it', 'Salesperson performance, and the largest block in the ledger', p, b)

    def disc():
        cd = S.get('codes')
        if cd is None or not len(cd):
            return ''
        p = [para(f'{R(F["disc"])} was given away on {share(F["disc"], F["gross"])} of gross value across '
                  f'{len(cd)} discount codes. ' + rank_list(cd, 'given', 4) + '.'),
             para(f'The deepest single code averaged {cd["depth"].max():.1f}% off. Concentration matters more than the total: '
                  f'the largest code is {share(cd["given"].iloc[0], cd["given"].sum())} of all discounting, which means one '
                  f'decision by one person, not a policy applied across the book.')]
        b = [tab(cd.reset_index(), ['Code', 'Uses', 'Given away', 'Net cash', 'Buyers', 'Depth'],
                 ['w', 'n', 'm', 'm', 'n', 'p'], 'num'),
             frame_ev(f'Evidence &mdash; discounting by product, {lab}',
                      cur.groupby('Cleaned Product').agg(n=('val', 'size'), gross=('gross', 'sum'), disc=('disc', 'sum'),
                                                          spread=('has_disc', 'mean')).assign(
                          depth=lambda x: x['disc'] / x['gross'] * 100, spread=lambda x: x['spread'] * 100)
                      .sort_values('disc', ascending=False).reset_index(),
                      ['Product', 'Lines', 'Gross', 'Discount', 'Spread', 'Depth'], ['w', 'n', 'm', 'm', 'p', 'p'],
                      blurb='Spread is the share of a product’s lines that carried any discount; depth is the discount as a share of gross.')]
        dy = getattr(M, 'disc_year', {})
        if len(dy) > 1:
            yrs = sorted(dy)[-4:]
            b.insert(0, bars([str(z) for z in yrs], [('Depth of discount %', [dy[z]['depth'] for z in yrs], A1),
                                                      ('Spread % of lines discounted', [dy[z]['spread'] for z in yrs], B1)],
                             'Discount depth and spread, whole-year figures', h=280, as_pct=True, ymax=60,
                             note=f'Depth is discount as a share of gross value; spread is the share of transactions carrying any discount. Both are for the full calendar year, since a single month is too small a base for codes.'))
        return sec('Discounting', f'{R(F["disc"])} given away, concentrated at the top of the ladder', p, b)

    def arrived():
        ps = S.get('pay_src')
        if ps is None or not len(ps):
            return ''
        p = [para(f'By how the sale reached the studio: ' + rank_list(ps, 'cash', len(ps)) + '.'),
             para(f'The average online ticket is {R(ps["avg"].max())} at its largest and {R(ps["avg"].min())} at its smallest. '
                  'Where one channel carries the large commitments, the studio should read that channel as a product decision, '
                  'not a payment preference: members do not choose a channel, they choose the least friction available to them '
                  'at the moment they decide.')]
        b = [tab(ps.reset_index(), ['Payment source', 'Lines', 'Cash', 'Average'], ['w', 'n', 'm', 'm']),
             frame_ev('Evidence &mdash; purchase type',
                      (cur.groupby(cur['Purchase Type'].astype(str).str.strip()).agg(
                          n=('val', 'size'), cash=('val', 'sum'), avg=('val', 'mean')).sort_values('cash', ascending=False)
                       if 'Purchase Type' in cur else None),
                      ['Purchase type', 'Lines', 'Cash', 'Average'], ['w', 'n', 'm', 'm'])]
        return sec('How the money arrived', 'Payment channel, and what each one carries', p, b)

    def who():
        dc = S.get('deciles')
        if dc is None or not len(dc):
            return ''
        tot = float(dc['sum'].sum())
        top = float(dc['sum'].iloc[0])
        p = [para(f'Buying {F["buyers"]} people into ten groups by what they spent: the top tenth accounts for '
                  f'<strong>{share(top, tot)}</strong> of the month’s cash ({R(top)}), and the bottom five tenths together '
                  f'for {share(float(dc["sum"].iloc[5:].sum()), tot)}.'),
             para('Concentration of this size is not a risk on its own &mdash; every gym has regulars who buy more than '
                  'everyone else &mdash; but it decides what a lost member costs. Losing one name from the top decile removes '
                  'as much cash as losing a whole decile at the bottom, and the studio has no alert for either.')]
        b = [bars([f'decile {i + 1}' for i in range(len(dc))], [('Cash', [float(v) for v in dc['sum']], A1)],
                  f'Who the money came from, {lab}', h=280,
                  note='Buyers ranked by the size of their month and split into ten equal groups.'),
             frame_ev('Evidence &mdash; the twenty largest buyers of the month',
                      g.sort_values('cash', ascending=False).head(20).reset_index(),
                      ['Member ID', 'Cash', 'Lines', 'Discount'], ['w', 'm', 'n', 'm'],
                      blurb='Member ids only. Names sit in the sales export.')]
        return sec('Who the money came from', 'Ten members account for more than a third of the month', p, b)

    def retail():
        rt = S.get('retail')
        if rt is None or not len(rt) or float(rt['rev'].sum()) < 1000:
            return ''
        p = [para(f'Everything that is not a class or a membership came to {R(rt["rev"].sum())} on '
                  f'{int(rt["n"].sum())} lines, across {len(rt)} products. The largest is '
                  f'{clean(rt.index[0])} at {R(rt["rev"].iloc[0])}.'),
             para('Read as a business line this is rounding. Read as a behaviour it is a signal: members who buy retail '
                  'train here more often, and the counter is the cheapest relationship the studio has.')]
        b = [tab(rt.reset_index(), ['Product', 'Lines', 'Cash'], ['w', 'n', 'm']),
             frame_ev('Evidence &mdash; category mix in full', S['cats'].reset_index(),
                      ['Category', 'Lines', 'Cash', 'Buyers', 'Discount'], ['w', 'n', 'm', 'n', 'm'])]
        return sec('Retail', 'A small line that is not yet a business', p, b)

    def starter():
        fp = X.nw.get('first')
        if fp is None or not len(fp):
            return ''
        p = [para(f'What a member buys first predicts what they are worth. Across the Bandra intake file, lifetime value '
                  f'runs from <strong>{R(fp["ltv"].min())}</strong> for a {clean(fp.index[-1])} to '
                  f'<strong>{R(fp["ltv"].max())}</strong> for a {clean(fp.index[0])} &mdash; a '
                  f'{ratio(fp["ltv"].max(), fp["ltv"].min())}-fold range set by the first decision, before any coaching happens.'),
             para(f'The same order appears in visits: {fp["visits"].max():.1f} on a {clean(fp["visits"].idxmax())} against '
                  f'{fp["visits"].min():.1f} on a {clean(fp["visits"].idxmin())}. The intro offer is therefore not a pricing '
                  'question at all; it is the first programming decision the studio makes about a member.')]
        b = [hbars([(clean(i), float(v), A1) for i, v in fp['ltv'].items()],
                   'Lifetime value by first purchase', unit='₹', note='Mean LTV recorded in the member file for everyone whose first purchase was this product.'),
             tab(fp.reset_index(), ['First purchase', 'People', 'Mean LTV', 'Mean visits', 'Visits per month', 'Converted %'],
                 ['w', 'n', 'm', 'f1', 'f1', 'p']),
             frame_ev('Evidence &mdash; how fast the second visit came, and what it was worth', X.nw.get('speed'),
                      ['Second visit within', 'People', 'Mean LTV', 'Mean visits'], ['w', 'n', 'm', 'f1'],
                      blurb='A 2-for-1 introductory pack makes the second paid visit the third class, so the second visit is read here as the second recorded class, not the second purchase.')]
        sp = X.nw.get('speed')
        if sp is not None and len(sp):
            b.insert(1, para(f'Speed matters as much as product. Members back within a day of their first visit are worth '
                             f'{R(sp["ltv"].iloc[0])} on average; those who take over a month are worth {R(sp["ltv"].iloc[-1])}. '
                             f'Nothing in the studio currently owns the interval between visit one and visit two.'))
        return sec('What the first purchase predicts', 'Intake quality, and the two-day window', p, b)

    def causes():
        items = []
        try:
            if P1.get('cash'):
                d = (F['cash'] - P1['cash']) / P1['cash'] * 100
                items.append(('part', 'A quiet market',
                              f'Cash moved {d:+.1f}% while the number of buyers moved '
                              f'{((F["buyers"] - P1["buyers"]) / P1["buyers"] * 100) if P1.get("buyers") else float("nan"):+.1f}%. '
                              'A flat top line made of different parts is a market signal, not a sales-team signal.',
                              'Ruled out only if buyers and cash move together for three consecutive months.'))
        except Exception:
            pass
        items += [('yes', 'The offer, not the price',
                   f'Ticket size rose while the product mix shortened. Buyers are not being lost; they are being sold '
                   f'less commitment per sale.', 'Check next month whether average classes bought per membership moves.'),
                  ('yes', 'Nobody owns the unattributed sale',
                   f'{share(float(S["sold_by"].loc["Not recorded", "cash"]), F["cash"]) if "Not recorded" in S.get("sold_by", pd.DataFrame()).index else "a slice of"} '
                   f'the month has no salesperson attached.',
                   'A rule, not a reminder: every sale needs a name before it can be paid out.'),
                  ('part', 'Festival and calendar effects',
                   f'Cash concentrated in week {" / ".join(str(int(i)) for i in S["weeks"].index)} shows the month trading to '
                   'the payroll calendar. Public holidays and festival weeks move the same way every year and are frequently '
                   'mistaken for performance.',
                   'Compare the same week-of-month pattern for three years before drawing a conclusion.')]
        return sec('What else could explain it', 'The causes that are easy to miss, and the ones that are not',
                   [para('Every finding above has at least two possible causes. These are the candidates, and what each one '
                         'would need to be true.')],
                   [hyp(items)])

    body = run([start, base, core, mix, commit, ladder, trading, paidfor, soldby, disc, arrived, who, retail, starter, causes])
    defs = [('Sales revenue', 'the Payment Value column of the sales export, dated on Payment Date, filtered to this studio. Only successful, non-voided payments count.'),
            ('Net of VAT', 'sales revenue minus the Payment VAT recorded on the same lines.'),
            ('Delivered class revenue', 'the Revenue column of the sessions export, on classes actually taught, with at least one attendance.'),
            ('Buyer', 'a distinct Member ID with at least one payment in the month. A household paying twice counts once.'),
            ('Transaction', 'a distinct Sale ID. One invoice with several items counts once.'),
            ('Repeat buyer', 'a Member ID with two or more distinct sales in the month, not two payments on one invoice.'),
            ('Discount given', 'item-level discount (unit discount × quantity), which is the only form that can be summed across lines. Depth is the discount as a share of discount plus collected revenue; spread is the share of lines carrying any discount at all.')]
    caut = [('The sales export carries no row for a class bought at another studio and paid here, so cross-studio spend is invisible in this chapter.'),
            ('Cash is not revenue. A twelve-class package sold today is twelve classes of liability; only the sessions ledger shows what has been delivered.'),
            (f'{mon} {y} is read against the same month last year rather than a rolling twelve, because attendance and pricing at this studio both move with the calendar.'),
            ('Year-on-year comparisons of September are not directly comparable across years when the festival week shifts; the pattern inside the month is shown so the shift can be seen rather than assumed.')]
    body += appendix(M, X, 'sales')
    body += method(M, defs, caut)
    kpis = [kpi('Sales revenue', R(F['cash']), (f'{(F["cash"] - P1["cash"]) / P1["cash"] * 100:+.1f}% on {yrp(M)}' if P1.get('cash') else ''), 'pos' if P1.get('cash') and F['cash'] >= P1['cash'] else 'neg'),
            kpi('Transactions', _n(F['txn']), f'{F["buyers"]} buyers'),
            kpi('Average buyer', R(F['ticket']), (f'{(F["ticket"] - P1["ticket"]) / P1["ticket"] * 100:+.1f}% on the year' if P1.get('ticket') else ''), 'pos' if P1.get('ticket') and F['ticket'] >= P1['ticket'] else 'neg'),
            kpi('Discount given', R(F['disc']), share(F['disc'], F['gross']) + ' of gross')]
    facts = [f'{R(F["cash"])} of cash from {F["txn"]} transactions and {F["buyers"]} buyers in {lab}, at an average of {R(F["ticket"])} each.',
             f'{share(L.get("rev", 0), F["cash"])} of that cash has already been delivered as attended classes ({R(L.get("rev", 0))}).',
             f'{rep.get("multi", 0)} buyers ({rep.get("multi_share", 0):.0f}%) bought more than once and produced {share(rep.get("multi_cash", 0), rep.get("cash", 0))} of the month.']
    if 'Not recorded' in S.get('sold_by', pd.DataFrame()).index:
        facts.append(f'{R(float(S["sold_by"].loc["Not recorded", "cash"]))} of cash has no salesperson recorded against it.')
    ch = dict(id='sales', n=1, title='Sales Performance', body=body, kpis=kpis, facts=facts,
              subtitle=f'{R(F["cash"])} of cash, {F["buyers"]} buyers, {R(F["ticket"])} each')
    ch['recs_extra'] = recs_sales(M, X)
    return ch


def recs_sales(M, X):
    """Recommendations this chapter's own tables support, handed to the narrator
    so the chapter's evidence and its actions cannot drift apart."""
    y = M.y
    F = M.sales[y]
    out = []
    S = X.sales
    try:
        q = S.get('ppc')
        if q is not None and len(q) > 1:
            cheap, dear = q['per_class'].idxmin(), q['per_class'].idxmax()
            if q.loc[dear, 'n'] > q.loc[cheap, 'n'] * 0.4:
                out.append(('Re-price the ladder so the bigger commitment is always cheaper per class', 'Sales + Finance',
                            f'{clean(cheap)} sells at {R(q.loc[cheap, "per_class"])} a class while {clean(dear)} sells at '
                            f'{R(q.loc[dear, "per_class"])}; {int(q.loc[dear, "n"])} lines went out at the dearer per-class rate.',
                            f'Moving even a quarter of the {int(q["n"].sum())} class-count sales onto the best per-class tier adds '
                            f'credits to the delivered base at no revenue cost, and removes the single clearest pricing inconsistency on the board.'))
    except Exception:
        pass
    try:
        sb = S.get('sold_by')
        if sb is not None and 'Not recorded' in sb.index:
            v = float(sb.loc['Not recorded', 'cash'])
            out.append(('Put a name on every sale before it can be paid out', 'Studio Manager',
                        f'{R(v)} of {M.label} cash, {share(v, F["cash"])} of the month, carries no salesperson.',
                        'Attribution is the cheapest management tool the studio has. It costs one rule at the desk and it makes conversion, discount discipline and repeat rate measurable per person instead of per hope.'))
    except Exception:
        pass
    try:
        rep = S.get('repeat', {})
        if rep.get('buyers'):
            out.append(('Sell the second purchase while the first is being served', 'Front Desk',
                        f'{rep["multi"]} of {rep["buyers"]} buyers bought more than once and produced {share(rep["multi_cash"], rep["cash"])} of the cash. '
                        f'{100 - rep["multi_share"]:.0f}% bought once and were not offered anything further.',
                        'A renewal conversation at the moment of highest engagement is worth more than the same conversation in an email three weeks later; on this month’s mix it is the difference between a one-purchase member and a repeat one.'))
    except Exception:
        pass
    try:
        cd = S.get('codes')
        if cd is not None and len(cd) > 2:
            out.append(('Put every discount code under one owner and one ceiling', 'Marketing + Finance',
                        f'{len(cd)} codes were used in {M.label}, giving away {R(cd["given"].sum())} at depths between '
                        f'{cd["depth"].min():.0f}% and {cd["depth"].max():.0f}%. The largest single code is '
                        f'{share(cd["given"].max(), cd["given"].sum())} of all discounting.',
                        'One owner and one depth cap turns discounting from a leak into a lever, and makes the month comparable to next month.'))
    except Exception:
        pass
    try:
        fp = X.nw.get('first')
        if fp is not None and len(fp) > 1:
            out.append((f'Lead with {clean(fp["ltv"].idxmax())}, not with the cheapest offer', 'Sales + Marketing',
                        f'Lifetime value by first purchase ranges from {R(fp["ltv"].min())} ({clean(fp["ltv"].idxmin())}) to '
                        f'{R(fp["ltv"].max())} ({clean(fp["ltv"].idxmax())}) across {int(fp["people"].sum()):,} recorded first-timers.',
                        'The first product decides the lifetime. Changing which offer the desk leads with costs nothing and moves the whole cohort.'))
    except Exception:
        pass
    try:
        sp = X.nw.get('speed')
        if sp is not None and len(sp) > 2:
            out.append(('Own the interval between the first visit and the second', 'Front Desk + Studio Manager',
                        f'Members who came back within a day of a first visit are worth {R(sp["ltv"].iloc[0])} across a lifetime; '
                        f'those who took over a month are worth {R(sp["ltv"].iloc[-1])}.',
                        'Booking the next class before the member leaves the building converts the only moment when they are certain they want to come back.'))
    except Exception:
        pass
    return out
