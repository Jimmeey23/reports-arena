"""Chapters 4 and 5: the membership book and the format league table."""
from __future__ import annotations
import numpy as np, pandas as pd
from .design import (R, Rs, P, N, T, ev, note, bars, lines, hbars, diverging, stacked,
                     funnel, dumbbell, A1, A2, A3, B1, B2, N1, N2, fd, fdt)
from .metrics import DAYS, MONTH_NAMES, rng
from .deep import (sec, tab, frame_ev, statgrid, hyp, method, appendix, guide, kpi, money, pc, _n,
                   clean, dpc, share, ratio, concentration, extremes, rank_list)
from .chapters_deep import deep, run, head, para, h4, yr, yrp, mono


def _f(x, d=1):
    try:
        v = float(x)
        if not np.isfinite(v):
            return '·'
        return f'{v:,.{d}f}'
    except Exception:
        return '·'


def _ok(series):
    try:
        return series is not None and len(series) and float(pd.Series(series).abs().max()) > 0
    except Exception:
        return False


# ==================================== 4. MEMBERSHIPS LAPSED AND CHURNED
def lapse(M):
    if 'lapsed' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    LP = X.lp
    d = LP.get('d')
    pay = LP.get('paid')
    if d is None or not len(d):
        return None
    surv = getattr(M, 'surv', None)
    mon = mono(M)

    def start():
        p = [para(f'The membership ledger for {M.studio} holds {M.led["rows"]:,} rows covering {M.led["members"]:,} people. '
                  f'{M.led["paid"]:,} of them were paid for, carrying {R(M.led["cash"])} of recorded money. '
                  + (f'{share(M.led["lapsed_cash"], M.led["cash"])} of that money belongs to memberships now marked lapsed.'
                     if M.led.get('lapsed_cash') else '')),
             para(f'This chapter is written for <strong>{lab} at {clean(M.studio)}</strong>: the first sections date the '
                  f'churn to that month alone &mdash; what was bought, what closed, and what runs out next. The rest reads '
                  f'the selected-month membership-purchase cohort as a funnel: what a membership is worth when it is bought, '
                  f'how long it lasts, how much of it is used, and how it ends &mdash; the context the month\u2019s numbers '
                  f'need to be judged against.')]
        if hasattr(M, 'median_life'):
            p.append(para(f'The median paid membership at this studio lasts <strong>{M.median_life:.0f} days</strong>. Not '
                          f'months. And the way it ends is not a single story: {LP.get("never", 0):,} memberships recorded no '
                          f'attendance at all, while the rest ran down their classes and stopped. Those are different '
                          f'failures, they cost different things to fix, and the studio currently treats them as one number '
                          f'called churn.'))
        claim = (f'{M.unused_left:,.0f} classes sit unspent on memberships the studio has already been paid for &mdash; '
                 f'about {R(LP.get("money_left", 0))} of value sitting in members\u2019 hands. The people who have used a '
                 f'quarter or less of what they bought are the most winnable names on the file and the least contacted.')
        blocks = [statgrid([('Memberships purchased in selected month', f'{M.led["rows"]:,}'), ('Paid', f'{M.led["paid"]:,}'),
                            ('Money recorded', R(M.led['cash'])), ('Median observed days', f'{getattr(M, "median_life", 0):.0f} days')])]
        return head('Start here', 'Memberships purchased in the reporting month', claim) + ''.join(p + blocks)

    def periodsec():
        per = LP.get('period') or {}
        if not per:
            return ''
        cn = per.get('churned_n', 0)
        bn = per.get('bought_n', 0)
        en = per.get('ended_n', 0)
        xn = per.get('expiring_n', 0)
        if not (cn or bn or en or xn):
            return ''
        p = [para(f'The ledger dates every membership, so {lab} can be read on its own with event dates scoped to the reporting month. '
                  f'During {lab}, <strong>{cn:,} memberships were recorded as churned</strong> at {clean(M.studio)}'
                  + (f' &mdash; {R(per.get("churned_cash", 0))} of paid money closing out' if per.get('churned_cash') else '')
                  + (f', and {per.get("churned_never", 0):,} of them had never produced a single attendance.'
                     if per.get('churned_never') else '.'))]
        if bn:
            p.append(para(f'On the other side of the same month, {bn:,} paid memberships were bought for '
                          f'{R(per.get("bought_cash", 0))}. Those two numbers together are the net movement of the book in '
                          f'{lab}. The following sections describe the selected-month purchase cohort, '
                          f'because the month\u2019s churn can only be judged against what this studio usually loses.'))
        if xn:
            p.append(para(f'{xn:,} memberships ({per.get("expiring_members", xn):,} people) run out within thirty days after '
                          f'{lab}, carrying {R(per.get("expiring_cash", 0))} of paid value. That is next month\u2019s churn '
                          f'list, already known and already contactable.'))
        used = per.get('churned_used')
        grid = [('Churned in ' + mon, f'{cn:,}'),
                ('Cash closed out', R(per.get('churned_cash', 0))),
                ('Bought in ' + mon, f'{bn:,}'),
                ('Ending within 30 days after', f'{xn:,}')]
        blocks = [statgrid(grid)]
        cm = per.get('churned_df')
        if cm is not None and len(cm):
            keep = [c for c in ['Member ID', 'Membership Name', 'Amount Paid', 'Purchase Date_x',
                                'Churned Date_x', 'Sessions Used %', 'Derived Status'] if c in cm.columns]
            heads = {'Member ID': 'Member', 'Membership Name': 'Product', 'Amount Paid': 'Paid',
                     'Purchase Date_x': 'Bought', 'Churned Date_x': 'Churned', 'Sessions Used %': 'Used %',
                     'Derived Status': 'Status'}
            fmts = {'Member ID': 'w', 'Membership Name': 'w', 'Amount Paid': 'm', 'Purchase Date_x': 'd',
                    'Churned Date_x': 'd', 'Sessions Used %': 'p', 'Derived Status': 'w'}
            view = cm[keep].sort_values('Amount Paid', ascending=False) if 'Amount Paid' in keep else cm[keep]
            blocks.append(frame_ev(f'Evidence &mdash; the memberships churned during {lab}, largest first',
                                   view.head(60), [heads[c] for c in keep], [fmts[c] for c in keep],
                                   blurb='Dates shown in IST as the ledger records them. Only the selected month is listed.'))
            if used is not None and used == used:
                p.append(para(f'The churn of {lab} was not mostly burnt-out loyalists: those closed memberships had used '
                              f'{used:.0f}% of their classes on average, and the table below shows the largest of them.'))
        return sec(f'{lab}, dated', 'Churn that actually happened in the selected month', p, blocks)

    def shape():
        st = getattr(M, 'status_mix', None)
        p = []
        if st is not None and len(st):
            p.append(para('The book, by the state the system holds it in: ' + ' · '.join(
                f'{clean(i)} {_n(v)}' for i, v in st.items()) + '.'))
            live = float(st.reindex(['Active', 'Renewed', 'Renewal Grace Period', 'New']).fillna(0).sum())
            p.append(para(f'{share(live, st.sum())} of the ledger is live or in a grace window. Everything else is finished. '
                          f'A studio that reads only its live book sees a healthy club and a small one; the whole file says '
                          f'the club has met, and lost, {int(st.sum()) - int(live):,} people.'))
        if surv is not None and len(surv):
            p.append(para(f'Survival falls fastest at the start and never really stops: {surv.iloc[0]["still"]:.0f}% of paid '
                          f'memberships are still running after {str(surv.iloc[0]["Point"])}s, {surv.iloc[2]["still"]:.0f}% '
                          f'after thirty days, and {surv.iloc[-1]["still"]:.1f}% after a year. The shape says the problem is '
                          f'in the first month, where nothing is charged and nothing is measured.'))
        b = []
        if surv is not None and len(surv):
            b.append(lines([str(i) for i in surv['Point']], [('Still running %', [float(v) for v in surv['still']], A1)],
                           f'What proportion of paid memberships is still alive, {M.studio}', h=300, as_pct=True, ymax=105,
                           note='Measured from the purchase date recorded in the ledger, with open memberships treated as censored rather than as survivors.'))
            b.append(tab(surv, ['Checkpoint', 'Still open %', 'Ended %', 'Eligible purchases'], ['w', 'p', 'p', 'n']))
        if st is not None and len(st):
            b.append(hbars([(clean(i), float(v), A1 if i in ('Active', 'Renewed') else B2) for i, v in st.items()],
                           'The book, by status', unit='', note='Derived Status as the system computes it.'))
        dh = X.prow if hasattr(X, 'prow') else None
        co = LP.get('cohort')
        if co is not None and len(co):
            b.append(frame_ev('Evidence &mdash; the book by month of purchase', co.reset_index(),
                              ['Month bought', 'Sold', 'Cash', 'Median days', 'Used %', 'Still live %'],
                              ['w', 'n', 'm', 'n', 'p', 'p'], maxrows=60,
                              blurb='Every membership bought in that month, whatever has happened since.'))
        return sec('The shape of the churn book', 'How a membership ends, and when', p, b)

    def twoways():
        never = LP.get('never', 0)
        lp_ = pay if pay is not None and len(pay) else d
        p = [para(f'<strong>{never:,} memberships recorded no attendance at all</strong>'
                  + (f', {share(never, len(d))} of the ledger' if len(d) else '') +
                  f'. {LP.get("never_paid", 0):,} of them were paid for. These people bought a promise and never used it; '
                  f'the studio has their money and their goodwill, and it is losing both quietly.'),
             para('The other failure is the opposite: a member who came, used the product, and finished it. Those memberships '
                  'are not churn in any meaningful sense &mdash; they are short products selling short. The distinction decides '
                  'whether the fix is an activation programme or a pricing change, and today it is not made anywhere in the '
                  'reporting.')]
        used = None
        if 'Sessions Used %' in lp_:
            used = lp_.groupby(pd.cut(lp_['Sessions Used %'].fillna(0), [-1, 1, 25, 50, 75, 100, 100000],
                                      labels=['nothing used', 'up to a quarter', 'a quarter to a half',
                                              'a half to three quarters', 'three quarters to all', 'everything or more']),
                               observed=True).agg(n=('Amount Paid', 'size'), paid=('Amount Paid', 'mean'),
                                                  days=('Membership Duration (Days)', 'median'),
                                                  late=('Late Cancellations', 'mean') if 'Late Cancellations' in lp_ else ('Amount Paid', 'mean'))
            used['days'] = used['days'].fillna(0)
        if used is not None and len(used):
            p.append(para(f'Usage tells the difference cleanly: ' + ' · '.join(
                f'{clean(i)} {_n(r["n"])}' for i, r in used.iterrows()) + '. The members who used nothing have a median '
                f'membership of {used["days"].iloc[0]:.0f} days; those who used everything ran '
                f'{used["days"].iloc[-1] if used["days"].iloc[-1] else 0:.0f} days. One group left; the other finished.'))
        b = []
        if used is not None and len(used):
            b.append(T(['Usage of what they paid for', 'Memberships', 'Average paid', 'Median days live', 'Late cancellations'],
                       [[clean(i), _n(r['n']), R(r['paid']), _f(r['days'], 0), _f(r['late'])] for i, r in used.iterrows()], 'num'))
            b.append(bars([clean(i) for i in used.index], [('Memberships', [float(v) for v in used['n']], A1)],
                           'Did they use what they paid for?', h=300,
                           note='Sessions Used % as the ledger records it, for every paid membership on file.'))
        return sec('The two ways to lose a member', 'One never started. One finished.', p, b)

    def used():
        if not hasattr(M, 'unused_n'):
            return ''
        p = [para(f'{M.unused_n:,} paid memberships have a usage figure recorded. Of them, <strong>{M.unused_low:,} used a '
                  f'quarter or less</strong> of what they bought, leaving {M.unused_left:,.0f} classes undelivered, and '
                  f'{M.unused_full:,} used everything.'),
             para('Undelivered classes are the studio’s cheapest retention tool and its largest unmanaged liability. '
                  'They are worth real money to the member, they cost nothing to grant as visits, and every one of them '
                  'represents a member who has already decided to come and has not come.')]
        lu = LP.get('low_use')
        b = [statgrid([('Memberships under-used', f'{M.unused_low:,}'), ('Classes left undelivered', f'{M.unused_left:,.0f}'),
                       ('Used everything', f'{M.unused_full:,}'), ('Money attached to the under-used', R(float(lu['Amount Paid'].sum())) if lu is not None and len(lu) and 'Amount Paid' in lu else '-')]),
             ]
        if lu is not None and len(lu) and 'Membership Name' in lu:
            g = lu.groupby(lu['Membership Name'].astype(str).str.replace('^Studio\\s*', '', regex=True).str.strip()).agg(
                n=('Amount Paid', 'size'), left=('Remaining Sessions', 'sum'), paid=('Amount Paid', 'sum')).sort_values('left', ascending=False)
            b.append(tab(g.reset_index(), ['Product', 'Under-used memberships', 'Classes left', 'Money paid'], ['w', 'n', 'n', 'm']))
        return sec('Did they use what they paid for?', 'The classes the studio owes and nobody is claiming', p, b)

    def decline():
        dn = LP.get('decline')
        if not dn:
            return ''
        p = [para(f'Churn shows up in the visit pattern long before it shows up in the status. Comparing each '
                  f'membership’s first half against its second, across {dn["n"]:,} memberships with more than three '
                  f'visits to split: <strong>{dn["fell"]:.0f}% came less often in the second half</strong>, {dn["halved"]:.0f}% '
                  f'by at least half, and only {dn["rose"]:.0f}% came more often. The median run fell from {dn["med_then"]:.0f} '
                  f'visits to {dn["med_now"]:.0f}.'),
             para('That is the leading indicator the studio is missing. Attendance decline is visible weeks before a '
                  'membership lapses, it is computable from data the studio already exports, and it identifies people who can '
                  'still be reached &mdash; unlike lapsed members, whom the file says are gone.')]
        b = [statgrid([('Declining in the second half', f'{dn["fell"]:.0f}%'), ('More than halved', f'{dn["halved"]:.0f}%'),
                       ('Held or grew', f'{dn["rose"]:.0f}%'), ('Memberships measurable', f'{dn["n"]:,}')]),
             frame_ev('Evidence &mdash; the at-risk ledger, first half against second',
                      (pay if pay is not None else d).dropna(subset=['Visits in First Half']).assign(
                          drop=lambda x: x['Visits in Second Half'] / x['Visits in First Half'].replace(0, np.nan))
                      .sort_values('drop').head(60).reset_index(),
                      ['Membership', 'First half visits', 'Second half visits', 'Change', 'Days since last visit'],
                      ['n', 'n', 'n', 'f1', 'n'],
                      blurb='Sixty memberships with the steepest fade, ordered by the ratio of second half to first.')]
        ns = LP.get('noshow')
        if ns is not None and len(ns):
            b.append(tab(ns.reset_index(), ['Missed classes', 'Memberships', 'Median days live', 'Usage %'],
                         ['w', 'n', 'f1', 'p']))
            b.append(para(f'No-shows behave the same way: ' + ' · '.join(
                f'{clean(i)} runs {_f(r["days"], 0)} days at {_f(r["used"], 0)}% usage' for i, r in ns.iterrows()) +
                '. Missing a class is not a booking error; in this file it is a prediction.'))
        return sec('The decline that comes first', 'What the visit pattern says weeks before the status changes', p, b)

    def prod():
        g = LP.get('prod')
        if g is None or not len(g):
            return ''
        if 'lapsed' in g and 'live' not in g:
            g = g.assign(live=100 - g['lapsed'].fillna(0))
        p = [para(f'Product by product, the churn is not evenly spread: ' + rank_list(g, 'cash', 5) + '.'),
             para(f'The largest seller is {clean(g.index[0])} ({int(g["sold"].iloc[0])} sold, {R(g["cash"].iloc[0])}), which '
                  f'runs {_f(g["days"].iloc[0], 0)} days at a mean usage of {_f(g["used"].iloc[0], 0)}%, and is still live on '
                  f'{_f(g["live"].iloc[0], 0)}% of them. The products that hold best are not the ones that sell most, and that '
                  f'gap is the studio\u2019s product question: the file is being steered by a number nobody chose on purpose.')]
        if 'live' in g:
            p.append(para(f'{share(float(g[g["live"] < 10]["cash"].sum()), float(g["cash"].sum()))} of the money in these '
                          f'products sits on memberships that are live fewer than one time in ten. That is the pool the '
                          f'studio re-sells to every month, at full acquisition cost, and it is a product decision rather '
                          f'than a marketing one.'))
        b = [tab(g.reset_index(), ['Product', 'Sold', 'Members', 'Cash', 'Average paid', 'Median days', 'Usage %', 'Still live %'],
                 ['w', 'n', 'n', 'm', 'm', 'n', 'p', 'p'], maxrows=25),
             hbars([(clean(i), float(v), (A1 if v >= g['live'].median() else B1)) for i, v in g['live'].head(12).items()],
                   'How much of each product is still live or renewed', unit='%',
                   note='Accent bars are the products holding better than the median of this book; the others are the ones quietly draining it.')]
        if 'left' in g and float(g['left'].fillna(0).sum()) > 0:
            b.append(para(f'Across these products {float(g["left"].sum()):,.0f} classes remain unspent on memberships paid for '
                          f'with {R(float(g["cash"].sum()))}. Every one of them is a member who has already said yes and has '
                          f'not yet been served.'))
        return sec('Product by product', 'Which membership churns, and which merely ends', p, b)

    def winnable():
        w = LP.get('winnable')
        if w is None or not len(w):
            return ''
        p = [para(f'By recency rather than by value, the winnable book looks like this: ' + ' · '.join(
            f'{clean(i)} {_n(r["members"])} people holding {R(r["cash_left"])}' for i, r in w.iterrows()) + '.'),
             para(f'{_n(float(w["members"].iloc[0]) + (float(w["members"].iloc[1]) if len(w) > 1 else 0))} people have been '
                  f'in the building within the last sixty days and still hold {R(float(w["cash_left"].iloc[:2].sum()))} of '
                  f'undelivered value. They are not a win-back campaign; they are an existing member with an unspent credit, '
                  f'and the difference in contact cost between the two is the entire difference in outcome.')]
        b = [T(['Last seen', 'People', 'Cash still held', 'Classes still owed', 'Average paid'],
               [[clean(i), _n(r['members']), R(r['cash_left']), _n(r['classes_left']), R(r['ticket'])] for i, r in w.iterrows()], 'num'),
             bars([clean(i) for i in w.index], [('People', [float(v) for v in w['members']], A1),
                                                 ('Cash still held, lakh', [float(v) / 100000 for v in w['cash_left']], B1)],
                  'Who is winnable, by how recently they were here', h=310,
                  note='The second series is cash still held, drawn in lakh rupees so that both series share one axis.')]
        fz = LP.get('freeze')
        if fz and fz.get('n'):
            b.append(para(f'A separate signal the studio is not using: {fz["n"]:,} memberships were frozen at some point '
                          f'({fz["share"]:.1f}% of the ledger), and those are live more often than the ones that were not '
                          f'&mdash; {fz["live"]:.1f}% against {fz["base"]:.1f}%. A member who asks to pause is not leaving; '
                          f'they are the one who intends to come back and wants the clock stopped.'))
            _fav = []
            for key, name in [('fav_fmt', 'Favourite format'), ('fav_tr', 'Favourite trainer'),
                              ('fav_time', 'Favourite time'), ('fav_half', 'Half of the day')]:
                v = LP.get(key)
                if v is not None and len(v):
                    _fav.append(h4(name + ' of the whole book'))
                    _fav.append(T([name, 'Memberships'], [[clean(a), _n(b)] for a, b in v.head(8).items()], 'num'))
            if _fav:
                b.append(ev('Evidence &mdash; what the ledger says these members liked', ''.join(_fav)
                            + '<p style="font-size:13px;color:#6B7280">Preference columns as the studio records them on the '
                              'membership row. It is the cheapest programme clue in the file and it is not used anywhere in '
                              'the current renewal process.</p>'))
        return sec('Who is winnable', 'Recency, unspent value, and the ones who asked to pause', p, b)

    def cost():
        if not M.led.get('cash'):
            return ''
        acq = None
        try:
            Fx = M.sales.get(y, {})
            acq = float(Fx.get('cash', 0)) / max(Fx.get('buyers', 1), 1)
        except Exception:
            pass
        p = [para(f'The lost book is not an abstraction. {R(M.led.get("lapsed_cash", 0))} of recorded membership money has '
                  f'been paid for and finished &mdash; {share(M.led.get("lapsed_cash", 0), M.led["cash"])} of everything the '
                  f'studio has ever booked on this ledger. With an average ticket of {R(getattr(M, "ticket", 0))} and a '
                  f'median life of {getattr(M, "median_life", 0):.0f} days, that ticket has to be re-earned every '
                  f'{getattr(M, "median_life", 0):.0f} days per member.'),
             (f'Put beside what a sale costs to win &mdash; the studio collected {R(acq)} per buyer in {mon.lower()} &mdash; '
              f'churn stops being a marketing problem and becomes the reason the marketing budget exists.' if acq else '')]
        dl = LP.get('disc')
        b = [statgrid([('Money on finished memberships', R(M.led.get('lapsed_cash', 0))),
                       ('Average ticket', R(getattr(M, 'ticket', 0))),
                       ('Median observed days', f'{getattr(M, "median_life", 0):.0f} days'),
                       ('Warm members, 60 days', f'{LP.get("warm", 0):,}')])]
        if dl is not None and len(dl):
            b.append(tab(dl.reset_index(), ['Discount taken at purchase', 'Memberships', 'Average paid', 'Median days', 'Still live %'],
                         ['w', 'n', 'm', 'f1', 'p']))
            b.append(para('Discounting at the point of sale does not buy durability here: ' + ' · '.join(
                f'{clean(i)} is live {r["live"]:.0f}% of the time' for i, r in dl.iterrows()) +
                '. Discount and churn are close to independent in this file, which is its own finding &mdash; the studio can '
                'stop buying retention with price and start buying it with programming.'))
        b.append(frame_ev(f'Evidence &mdash; the twenty largest finished memberships by money',
                          (pay if pay is not None else d).sort_values('Amount Paid', ascending=False).head(20)[
                              ['Member ID', 'Membership Name', 'Amount Paid', 'Membership Duration (Days)',
                               'Total Sessions Completed', 'Sessions Used %', 'Days Since Last Visit', 'Derived Status']],
                          ['Member ID', 'Product', 'Paid', 'Days', 'Sessions', 'Used %', 'Days since last visit', 'Status'],
                          ['w', 'w', 'm', 'n', 'n', 'p', 'n', 'w']))
        return sec('What the lost book cost', 'Churn, priced', p, b)

    def thismonth():
        if pay is None or not len(pay):
            return ''
        a, bb = rng(y, M.m)
        try:
            bought = pay[pay['Purchase Date_x'].between(a, bb - pd.Timedelta(days=1))] if 'Purchase Date_x' in pay else None
            ended = pay[pay['Churned Date_x'].between(a, bb - pd.Timedelta(days=1))] if 'Churned Date_x' in pay else None
        except Exception:
            bought = ended = None
        if bought is None:
            return ''
        p = [para(f'{len(bought)} paid memberships were bought at this studio in {lab}, for {R(float(bought["Amount Paid"].sum()))}, '
                  f'at an average of {R(float(bought["Amount Paid"].mean())) if len(bought) else "-"} and a median granted length '
                  f'of {float(bought["Membership Duration (Days)"].median()):.0f} days.'
                  if len(bought) else f'No paid membership was recorded as bought in {lab}; the file dates them elsewhere.')]
        try:
            if ended is not None and len(ended):
                _u = float(ended['Sessions Used %'].mean()) if 'Sessions Used %' in ended else float('nan')
                p.append(para(f'{len(ended)} memberships that were sold earlier ended during {lab}. Their average paid value '
                              f'was {R(float(ended["Amount Paid"].mean()))}'
                              + (f' and their average usage was {_u:.0f}%' if _u == _u else '')
                              + '. That is the churn the studio will read next month as a bad sales month, when it is the '
                                 'tail of a good one three months ago.'))
        except Exception:
            pass
        p.append(para(f'Of everything sold in {lab}, {share(float((bought["Sessions Used %"].fillna(0) >= 100).sum()), len(bought)) if len(bought) and "Sessions Used %" in bought else "0%"} '
                      f'has already been fully used, and {share(float((bought["Total Sessions Completed"].fillna(0) == 0).sum()), len(bought)) if len(bought) and "Total Sessions Completed" in bought else "0%"} '
                      f'has not produced a single attendance. The sale is the least informative moment in a membership\u2019s life.'))
        b = []
        if len(bought):
            g = bought.groupby(bought['Membership Name'].astype(str).str.replace('^Studio\\s*', '', regex=True).str.strip()).agg(
                sold=('Amount Paid', 'size'), cash=('Amount Paid', 'sum'),
                days=('Membership Duration (Days)', 'median'), used=('Sessions Used %', 'mean'),
                left=('Remaining Sessions', 'sum')).sort_values('sold', ascending=False)
            b.append(T(['What was bought in ' + mon, 'Sold', 'Cash', 'Median days', 'Used %', 'Classes left'],
                       [[clean(i), _n(r['sold']), R(r['cash']), _f(r['days'], 0), _f(r['used']), _n(r['left'])]
                        for i, r in g.iterrows()], 'num'))
            b.append(frame_ev(f'Evidence &mdash; every paid membership bought in {lab}',
                              bought.reset_index()[['Member ID', 'Membership Name', 'Amount Paid', 'Start Date', 'End Date',
                                                     'Membership Duration (Days)', 'Total Sessions Completed', 'Sessions Used %',
                                                     'Remaining Sessions', 'Derived Status']].head(70),
                              ['Member ID', 'Product', 'Paid', 'Start', 'End', 'Days', 'Sessions', 'Used %', 'Left', 'Status'],
                              ['w', 'w', 'm', 'd', 'd', 'n', 'n', 'p', 'n', 'w'],
                              blurb='Rows as the ledger holds them. Dates shown in IST.'))
        return sec(f'The month inside the ledger', 'What was sold, and what it is already worth', p, b)

    def causes():
        items = [('yes', 'The product is short, not the member disloyal',
                  f'The median paid membership runs {getattr(M, "median_life", 0):.0f} days and the modal product is a '
                  f'one-month or small-pack purchase. A short product that is fully used is not churn.',
                  'Split the churn number by whether usage exceeded 90% before deciding what to fix.'),
                 ('yes', 'Nobody is onboarded',
                  f'{LP.get("never", 0):,} memberships never produced a single attendance, and {LP.get("never_paid", 0):,} of '
                  f'those were paid for.', 'An activation contact in the first fourteen days is the whole intervention.'),
                 ('part', 'Price and discount',
                  'Discount taken at purchase shows no consistent relationship with how long a membership lives in this file.',
                  'Do not conclude discounts cause churn; conclude they do not prevent it, which is a different decision.'),
                 ('no', 'The competition took them',
                  'The exports contain no competitor or cancellation-reason field. Anything said about why members went to '
                  'another studio is a hypothesis, not a finding.',
                  'Ask directly, on the day the status changes, and record the answer in the same file.')]
        return sec('What else could explain it', 'Causes the studio has not considered', [para('Churn is the chapter where the obvious explanation is usually wrong, so each candidate is stated with what would have to be true.')], [hyp(items)])

    body = run([start, periodsec, thismonth, shape, twoways, used, decline, prod, winnable, cost, causes])
    defs = [('Membership', 'one row of the lapsed and new-members export, filtered to purchases in the selected reporting month. Status and usage attributes reflect the uploaded export.'),
            ('Paid', 'a membership whose amount paid is above zero and whose name is not a staff, complimentary, credit or referral product.'),
            ('Lapsed', 'the Derived Status column as the system computes it, cross-checked against the churn and end dates on the row.'),
            ('Lifetime', 'end date minus purchase date, or, for memberships still open, today minus purchase date. Open memberships are therefore treated as censored, not as survivors.'),
            ('Usage', 'the Sessions Used % column, which the studio records against the classes granted, not the money paid.')]
    caut = [('The ledger starts wherever the export starts. Memberships that were created and deleted before the file’s first day are not in it, so very early churn may be understated.'),
            ('No cancellation reason is recorded anywhere in these files. The reports say what happened to a membership, never why the member says it happened.'),
            ('Money shown is what the studio recorded as paid for the membership, not revenue recognised; unused classes are still a liability rather than income.'),
            ('A member may hold several memberships at once. Counts of memberships and counts of people are deliberately kept apart in every table.')]
    body += appendix(M, X, 'lapse')
    body += method(M, defs, caut)
    st = getattr(M, 'status_mix', pd.Series(dtype=float))
    per = LP.get('period') or {}
    kpis = []
    if per.get('churned_n') or per.get('bought_n'):
        kpis.append(kpi(f'Churned in {mon}', f'{per.get("churned_n", 0):,}',
                        R(per.get('churned_cash', 0)) + ' closed out', 'neg'))
        kpis.append(kpi(f'Bought in {mon}', f'{per.get("bought_n", 0):,}',
                        R(per.get('bought_cash', 0)) + ' of new money', 'pos'))
    kpis += [kpi('Memberships purchased in selected month', f'{M.led["rows"]:,}', f'{M.led["members"]:,} people'),
             kpi('Paid memberships', f'{M.led["paid"]:,}', R(M.led['cash']) + ' of recorded money'),
             kpi('Median observed days', f'{getattr(M, "median_life", 0):.0f} days', 'through month-end; not completed lifetime', 'neg')]
    if per.get('expiring_n'):
        kpis.append(kpi('Expiring next 30 days', f'{per["expiring_n"]:,}',
                        R(per.get('expiring_cash', 0)) + ' at risk', 'neg'))
    else:
        kpis.append(kpi('Never attended', f'{LP.get("never", 0):,}', share(LP.get('never', 0), M.led['rows']) + ' of the ledger', 'neg'))
    facts = []
    if per.get('churned_n') or per.get('bought_n'):
        facts.append(f'{per.get("churned_n", 0):,} memberships churned during {lab} ({R(per.get("churned_cash", 0))} of paid '
                     f'money closed out), while {per.get("bought_n", 0):,} were bought for {R(per.get("bought_cash", 0))}.')
    facts += [f'{M.led["rows"]:,} memberships at this studio, {M.led["paid"]:,} of them paid for, across {R(M.led["cash"])} of recorded money.',
              f'The median paid membership lasts {getattr(M, "median_life", 0):.0f} days; {LP.get("never", 0):,} produced no attendance at all.',
              f'{LP.get("classes_left", 0):,.0f} classes sit unspent on the book, worth about {R(LP.get("money_left", 0))} of delivered value.']
    if surv is not None and len(surv):
        facts.insert(1, f'{surv.iloc[2]["still"]:.0f}% of paid memberships survive thirty days and {surv.iloc[-1]["still"]:.1f}% survive a year.')
    ch = dict(id='lapse', n=4, title='Memberships Lapsed and Churned', body=body, kpis=kpis, facts=facts,
              subtitle=f'{lab} first, then the whole book · {M.led["paid"]:,} paid memberships, median life {getattr(M, "median_life", 0):.0f} days')
    ch['recs_extra'] = recs_lapse(M, X)
    return ch


def recs_lapse(M, X):
    LP = X.lp
    out = []
    try:
        never = LP.get('never', 0)
        if never:
            out.append((f'Run a fourteen-day activation on the {int(share(never, M.led["rows"])).__str__()}% who never arrive',
                         'Studio Manager + Front Desk',
                         f'{never:,} of the {M.led["rows"]:,} memberships on file recorded no attendance at all, and '
                         f'{LP.get("never_paid", 0):,} of those were paid for.',
                         'One contact in the first fortnight, made by a person with the member’s own favourite slot in front of them, converts a purchase into a habit. Nobody who has attended once belongs in this programme.'))
    except Exception:
        pass
    try:
        lu = LP.get('low_use')
        if lu is not None and len(lu):
            out.append(('Write the unspent classes back as visits, with a date on them', 'Front Desk + Finance',
                        f'{M.unused_low:,} memberships used a quarter or less of what they bought, leaving '
                        f'{M.unused_left:,.0f} classes undelivered worth about {R(float(lu["Amount Paid"].sum()))}.',
                        'Converting credit into booked attendance moves money the studio already holds onto the balance sheet and pulls the member back into a routine - the single cheapest retention action available.'))
    except Exception:
        pass
    try:
        w = LP.get('winnable')
        if w is not None and len(w) > 2:
            out.append(('Segment win-back by recency, not by lifetime value', 'CRM + Marketing',
                        f'{_n(w["members"].iloc[0])} people were here in the last thirty days and still hold '
                        f'{R(float(w["cash_left"].iloc[0]))}; the largest group, {_n(w["members"].iloc[-1])} people, has not '
                        f'been inside a year.',
                        'Contact cost per recovered member falls by an order of magnitude between those two groups, and the studio currently sends the same message to both.'))
    except Exception:
        pass
    try:
        fz = LP.get('freeze')
        if fz and fz.get('n') and fz.get('live', 0) > fz.get('base', 0):
            out.append(('Freeze, do not lose: treat a pause request as a save', 'Front Desk',
                        f'{fz["n"]:,} memberships were frozen at some point and {fz["live"]:.1f}% are still live, against '
                        f'{fz["base"]:.1f}% of those that were never frozen.',
                        'A member who asks to pause is planning to return. Offering the pause before they offer the cancellation converts a churn event into a deferred one.'))
    except Exception:
        pass
    try:
        dn = LP.get('decline')
        if dn and dn.get('n'):
            out.append(('Put every member on a plan at the halfway point of their membership', 'Studio Manager',
                        f'{dn["fell"]:.0f}% of measurable memberships attended less in their second half than their first, '
                        f'and {dn["halved"]:.0f}% attended at least half as often. The change is visible before the status moves.',
                        'A mid-membership review - attendance so far, what is left, one specific class to book - is the only intervention in this chapter that can act before the lapse rather than after it.'))
    except Exception:
        pass
    try:
        g = LP.get('prod')
        if g is not None and len(g) > 2:
            short = g[g['days'] <= 40].sort_values('sold', ascending=False)
            if len(short):
                out.append(('Price the short product deliberately rather than by default',
                            'Founder + Finance',
                            f'{clean(short.index[0])} sold {int(short["sold"].iloc[0])} memberships at a median life of '
                            f'{short["days"].iloc[0]:.0f} days and renews {short["live"].iloc[0]:.0f}% of the time.',
                            'The short product is doing a job - it is the cheapest way for a member to say yes - and it should be priced and marketed as an on-ramp with a defined exit into a longer product, not as a best-seller.'))
    except Exception:
        pass
    return out


# ============================================== 5. FORMAT COMPARISONS
def formatcmp(M):
    if 'sessions' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    fm = getattr(M, 'formats', None)
    if fm is None or not len(fm):
        return None
    C, BH = X.cls, X.bh
    cur = C.get('cur')
    mon = mono(M)
    tot_att = float(fm['att'].sum())

    def start():
        full, thin = fm['fill'].idxmax(), fm['fill'].idxmin()
        p = [para(f'{len(fm)} formats ran {int(fm["sessions"].sum()):,} classes in {lab}. The fullest, {clean(full)}, filled '
                  f'{fm.loc[full, "fill"]:.1f}% of its seats; the emptiest, {clean(thin)}, {fm.loc[thin, "fill"]:.1f}%. '
                  f'Revenue per class ranges from {R(fm["rpc"].min())} to {R(fm["rpc"].max())}.'),
             para('A format is not a class type. It is a product with its own capacity, price, room, hour, trainer pool and '
                  'member base, and the studio sets those five things for each of them independently while judging them all '
                  'on one number, attendance. This chapter separates the five.')]
        claim = (f'{clean(fm["share_sessions"].idxmax())} takes {fm["share_sessions"].max():.0f}% of the timetable and fills '
                 f'{fm.loc[fm["share_sessions"].idxmax(), "fill"]:.0f}% of it. The format that fills best takes '
                 f'{fm.loc[fm["fill"].idxmax(), "share_sessions"]:.0f}%. The studio’s programming decisions and its '
                 f'demand are pointing in different directions.')
        b = [statgrid([(clean(i), f'{r["fill"]:.0f}% fill') for i, r in fm.sort_values('fill', ascending=False).head(4).iterrows()]),
              statgrid([(clean(i), f'{r["share_sessions"]:.0f}% of classes') for i, r in fm.sort_values('share_sessions', ascending=False).head(4).iterrows()])]
        return head('Start here', 'Every format, on more than one measure', claim) + ''.join(p + b)

    def league():
        s = fm.sort_values('att', ascending=False)
        p = [para('The league table, in full. Sessions, seats, attendance, utilisation, revenue and the two efficiency '
                  'measures - what a class earns and what a body in the room earns. Nothing else in the review will '
                  'contradict this table, so it is the one to argue with.'),
             para(f'{concentration(s["att"], unit="attendances")} Concentration at this level means the studio has, in '
                  f'effect, two products and a portfolio of experiments, and the experiments are consuming the same '
                  f'scarce resource as the products: the good hour.')]
        b = [tab(s.reset_index(), ['Format', 'Classes', 'Share of timetable', 'Seats', 'Attended', 'Utilisation', 'Revenue',
                                   'Per class', 'Per attendance', 'Booked', 'Late cancelled', 'Complimentary'],
                 ['w', 'n', 'p', 'n', 'n', 'p', 'm', 'm', 'm', 'n', 'n', 'n'], maxrows=25),
             bars([clean(i) for i in s.index[:10]], [('Utilisation %', [float(v) for v in s['fill'].head(10)], A1)],
                  'Utilisation, format by format', h=320, as_pct=True, ymax=float(s['fill'].max()) * 1.25, rotate=True,
                  note='Formats with fewer than three classes in the month are shown here because the league table is honest; they should not be judged on this. A revenue per class of zero means the sessions ledger records no value against that class - hosted, partner and complimentary sessions - not that the studio taught it for nothing.'),
             hbars([(clean(i), float(v), A2) for i, v in s['rpc'].sort_values(ascending=False).head(12).items()],
                   'What a class earns, by format', unit='₹', note='Revenue per class. A format can fill a room and still earn least per class if the room is cheap.')]
        return sec('The league table', 'Twelve numbers per format, and no averaging', p, b)

    def reach():
        mf = getattr(M, 'fmt_members', None)
        if mf is None or not len(mf):
            return ''
        p = [para('Reach and regularity are different properties and formats have them in different proportions. '
                  + f'{clean(mf["members"].idxmax())} reached {int(mf["members"].max())} members at {mf.loc[mf["members"].idxmax(), "per"]:.2f} '
                    f'visits each; {clean(mf["per"].idxmax())} reached {int(mf.loc[mf["per"].idxmax(), "members"])} members at '
                    f'{mf["per"].max():.2f} visits each.'),
             para('A format with high reach and low frequency is an acquisition and sampling product; a format with low '
                  'reach and high frequency is a habit. Scheduling them as though they had the same purpose is why one of '
                  'them is under capacity and the other has a waiting list.')]
        b = [mf.sort_values('members', ascending=False).reset_index().pipe(
            lambda x: tab(x, ['Format', 'Members reached', 'Attendances', 'Visits per member'], ['w', 'n', 'n', 'f2'])),
             bars([clean(i) for i in mf.sort_values('members', ascending=False).head(10).index],
                  [('Members reached', [float(v) for v in mf.sort_values('members', ascending=False).head(10)['members']], A1),
                   ('Visits per member, ×20', [float(v) * 20 for v in mf.sort_values('members', ascending=False).head(10)['per']], B1)],
                  'Reach against regularity, by format', h=330, rotate=True,
                  note='The second series is visits per member drawn at twenty times its true height so both fit one axis.')]
        return sec('Reach against regularity', 'Two different jobs, one timetable', p, b)

    def multiplier():
        if not BH:
            return ''
        fm2 = cur.groupby('_cls').agg(members=('CheckedIn', 'sum'))
        try:
            mem = cur.assign(k=1).groupby('_cls')['k'].size()
        except Exception:
            mem = None
        p = [para(f'{BH.get("multi", 0):.0f}% of the members who trained here in {mon.lower()} used more than one format, '
                  f'and {BH.get("loyal", 0)} made three or more visits to a single format. The two behaviours are not in '
                  f'conflict: variety keeps a member coming, and a favourite keeps them accountable.')]
        p.append(para(f'The studio currently manages neither. Nothing in the booking flow uses a member’s own favourite '
                      f'format to hold their slot, and nothing offers the second format to the person who has been coming to '
                      f'the first for months. The cross-sell exists in the membership; it has never been scheduled.'))
        b = [hbars([(clean(i), float(v), A1) for i, v in BH.get('fmt_share', pd.Series(dtype=float)).head(10).items()],
                   f'What proportion of the month’s members touched each format', unit='%',
                   note=f'Out of {len(BH.get("v", []))} members who attended at least once in {lab}.')]
        return sec('The multi-format multiplier', 'Variety as a retention mechanism', p, b)

    def devotee():
        mat = BH.get('fmt_matrix')
        if mat is None or not len(mat):
            return ''
        mx = mat.max(axis=1)
        tot = mat.sum(axis=1)
        share_max = (mx / tot.replace(0, np.nan))
        loyal = share_max[share_max >= 0.6]
        gen = share_max[share_max <= 0.35]
        p = [para(f'Of the {len(tot)} members who attended this month, {len(loyal)} gave at least 60% of their visits to a '
                  f'single format and {len(gen)} spread themselves so widely that no format held a third of them. The '
                  f'faithful average {tot.reindex(loyal.index).mean():.2f} visits a month; the generalists '
                  f'{tot.reindex(gen.index).mean():.2f}.'),
             para('Frequency, not preference, is what the studio is buying: on this month’s numbers the devoted visit '
                  f'{ratio(tot.reindex(loyal.index).mean(), max(tot.reindex(gen.index).mean(), 0.1))} times as often as the '
                  'unattached. The commercial question is whether a generalist is a devotee who has not found their room yet, '
                  'or a member about to stop.')]
        b = [frame_ev('Evidence &mdash; the format mix of the most devoted members',
                      mat.loc[loyal.sort_values(ascending=False).head(40).index].assign(total=tot, devoted=share_max).reset_index(),
                      ['Member ID'] + [clean(c)[:14] for c in mat.columns] + ['Total visits', 'Devotion %'],
                      ['w'] + ['n'] * (len(mat.columns) + 2), maxrows=45,
                      blurb='Devotion is the largest single-format share of that member’s visits in the month.')]
        return sec('What a devotee is worth', 'Faithfulness measured, not assumed', p, b)

    def when():
        try:
            grid = cur.pivot_table(index='_cls', columns='_day', values='CheckedIn', aggfunc='sum').reindex(columns=DAYS)
            hrs = cur.pivot_table(index='_cls', columns=cur['_hr'].astype('Int64'), values='CheckedIn', aggfunc='sum')
        except Exception:
            return ''
        if grid is None or not grid.notna().any().any():
            return ''
        _hot = grid.sum(axis=1).idxmax()
        _hotday = grid.loc[_hot].idxmax()
        p = [para(f'Each format lives in a part of the week. The busiest day for {clean(_hot)} is a {_hotday} '
                  f'({int(grid.loc[_hot].max())} attendances), and '
                  f'{int((grid.fillna(0) == 0).sum().sum())} format-day combinations were never used at all.'),
             para(f'That last number is the whole opportunity. A format that never runs on a Tuesday is not a format that '
                  f'cannot run on a Tuesday; it is a format nobody has tried. The white space in a grid like this is where a '
                  f'studio finds its next full room without touching price.')]
        rows = [[clean(i)] + [(_n(v) if pd.notna(v) else '·') for v in r] + [_n(r.sum())] for i, r in grid.iterrows()]
        b = [T(['Format'] + DAYS + ['Total'], rows, 'num'),
             frame_ev('Evidence &mdash; attendances by format and hour',
                      hrs.fillna(0).reset_index().rename(columns={'_hr': 'hour'}),
                      ['Format'] + [f'{int(c)}:00' if str(c).isdigit() else str(c) for c in hrs.columns],
                      ['w'] + ['n'] * len(hrs.columns), maxrows=20)]
        return sec('When each format is used', 'The grid, and the space inside it', p, b)

    def free():
        mx = C.get('paymix')
        if mx is None or not len(mx):
            return ''
        p = [para('Complimentary and non-paid seats are allocated by habit, and they land unevenly: ' + ' · '.join(
            f'{clean(i)} {r["free_pct"]:.0f}%' for i, r in mx.iterrows() if pd.notna(r['free_pct']))[:400] + '.'),
             para(f'The formats that carry the free seats are subsidising the formats that do not, and nobody has decided '
                  f'that. Set the budget by format against a stated purpose &mdash; trial volume, a new launch, a partner '
                  f'deal &mdash; and the emptiest room in the building becomes an asset with a price on it.')]
        b = [tab(mx.reset_index(), ['Format', 'Memberships', 'Packages', 'Intro offers', 'Singles', 'Total drawn',
                                    'Free %', 'Complimentary %'], ['w', 'n', 'n', 'n', 'n', 'n', 'p', 'p'])]
        return sec('Where the free seats sit', 'The subsidy nobody authorised', p, b)

    def causes():
        s = fm.sort_values('fill', ascending=False)
        items = [('yes', 'Capacity, not popularity',
                  f'Utilisation is seats, and seats are chosen by the studio: the largest room carries '
                  f'{clean(s["share_sessions"].idxmax())}. A format filling 35% of a 30-seat room is outperforming one '
                  f'filling 60% of a 12-seat room on revenue per class, and does not look like it.',
                  'Judge formats on revenue per class and revenue per attendance alongside fill.'),
                 ('part', 'The trainer, not the format',
                  f'{clean(fm.index[0])} is taught by {int(cur[cur["_cls"] == fm.index[0]]["_trainer"].nunique())} different '
                  f'trainers this month. Where one format has many hands, its average is a mix of standards.',
                  'The instructor chapter holds the within-format comparison.'),
                 ('no', 'The hour is neutral',
                  'Formats occupy different hours almost by definition, and hour is the strongest single predictor of fill in '
                  'this data set. Any format comparison that does not hold the hour constant is measuring the clock.',
                  'Read the when-each-format-is-used grid before reading the league table.'),
                 ('yes', 'A new format looks like a failing one',
                  f'{int((fm["sessions"] <= 3).sum())} formats ran three classes or fewer this month.',
                  'A format needs a dozen classes and two trainers before its fill means anything.')]
        return sec('What else could explain it', 'Why the league table can be read the wrong way', [para('A format comparison is a comparison of five different decisions at once. Here is which of them the table can and cannot attribute.')], [hyp(items)])

    body = run([start, league, reach, multiplier, devotee, when, free, causes])
    defs = [('Format', 'the Class column of the sessions export, with the Studio prefix removed so that two spellings of one format are one format.'),
            ('Utilisation', 'attended places over seats offered, for that format, in the month.'),
            ('Members reached', 'distinct member ids with at least one check-in to that format in the month, from the check-in ledger.'),
            ('Devotion', 'a member’s largest single-format share of their own visits that month.'),
            ('Free seat', 'an attendance recorded against an introductory offer, a comp or no payment record.')]
    caut = [('Formats are not comparable on price: a 45-minute strength class and a 60-minute cycle class are not the same product even when the room fills identically.'),
            ('A format introduced or retired inside the month will appear with a handful of classes and an extreme fill. Every table here carries the class count so those rows can be seen for what they are.'),
            ('Where the check-in ledger is used, it counts who walked in; the sessions ledger counts who was booked. The two differ by the show rate in chapter 2.'),
            ('The comparison is within the month. A format whose members renew is not visible here at all; that is chapter 4.')]
    body += appendix(M, X, 'format')
    body += method(M, defs, caut)
    kpis = [kpi('Formats', _n(len(fm)), f'{int(fm["sessions"].sum())} classes'),
            kpi('Fullest', f'{fm["fill"].max():.0f}%', clean(fm['fill'].idxmax()), 'pos'),
            kpi('Emptiest', f'{fm["fill"].min():.0f}%', clean(fm['fill'].idxmin()), 'neg'),
            kpi('Best per class', R(fm['rpc'].max()), clean(fm['rpc'].idxmax()))]
    facts = [f'{len(fm)} formats ran {int(fm["sessions"].sum())} classes for {R(fm["rev"].sum())} in {lab}.',
             f'{clean(fm["fill"].idxmax())} is the fullest at {fm["fill"].max():.1f}%; {clean(fm["fill"].idxmin())} the emptiest at {fm["fill"].min():.1f}%.',
             f'{clean(fm["rpc"].idxmax())} earns the most per class at {R(fm["rpc"].max())}.']
    ch = dict(id='format', n=5, title='Format Comparisons', body=body, kpis=kpis, facts=facts,
              subtitle=f'{len(fm)} formats, {fm["fill"].max():.0f}% to {fm["fill"].min():.0f}% fill')
    ch['recs_extra'] = recs_format(M, X)
    return ch


def recs_format(M, X):
    fm = getattr(M, 'formats', None)
    C, BH = X.cls, X.bh
    out = []
    try:
        big = fm['share_sessions'].idxmax()
        out.append((f'Rebuild {clean(big)} around what actually fills', 'Programming + Founder',
                    f'{clean(big)} holds {fm.loc[big, "share_sessions"]:.0f}% of the timetable and fills '
                    f'{fm.loc[big, "fill"]:.0f}%. The best-filling format in the studio, {clean(fm["fill"].idxmax())}, gets '
                    f'{fm.loc[fm["fill"].idxmax(), "share_sessions"]:.0f}%.',
                    f'Moving ten per cent of {clean(big)}’s classes into the hours and rooms that already fill is worth '
                    f'roughly {abs(fm["fill"].max() - fm.loc[big, "fill"]) * fm.loc[big, "seats"] * 0.1:,.0f} attendances a month at current prices.'))
    except Exception:
        pass
    try:
        best = fm['fill'].idxmax()
        if fm.loc[best, 'sessions'] < fm['sessions'].max() / 3:
            out.append((f'Scale {clean(best)} on purpose, and measure it', 'Programming + Marketing',
                        f'{clean(best)} fills {fm.loc[best, "fill"]:.0f}% on {int(fm.loc[best, "sessions"])} classes - the '
                        f'best in the studio and among the smallest programmes.',
                        'A format at capacity cannot tell the studio anything about demand. Doubling its classes for a month is the only way to learn whether the fill was scarcity or quality.'))
    except Exception:
        pass
    try:
        mx = C['paymix']
        worst = mx['free_pct'].idxmax()
        if pd.notna(mx.loc[worst, 'free_pct']) and mx.loc[worst, 'free_pct'] > 8:
            out.append((f'Set the complimentary budget by format, not by goodwill', 'Studio Manager + Finance',
                        f'{clean(worst)} runs {mx.loc[worst, "free_pct"]:.0f}% free of charge, against '
                        f'{mx["free_pct"].min():.0f}% at the other end, on a month-wide utilisation of '
                        f'{M.room[M.y]["fill"]:.1f}%.',
                        'A stated budget with a stated purpose converts an unmanaged subsidy into a marketing line the studio can switch off when the purpose is met.'))
    except Exception:
        pass
    try:
        if BH and BH.get('loyal'):
            out.append(('Market the second format to the devoted, not to everyone', 'Marketing + Front Desk',
                        f'{BH["loyal"]} members made three or more visits to one format this month and '
                        f'{BH.get("multi", 0):.0f}% of members touched more than one format. Frequency concentrates in the '
                        f'members who already come.',
                        'One named class offered to a member in their fourth week of a single format is the highest-yield cross-sell the studio has, and it costs nothing but the message.'))
    except Exception:
        pass
    try:
        grid = None
        cur = C['cur']
        grid = cur.pivot_table(index='_cls', columns='_day', values='CheckedIn', aggfunc='sum')
        gaps = int((grid.isna()).sum().sum())
        if gaps:
            out.append(('Try the empty day, once, before calling it unfillable', 'Programming',
                        f'{gaps} format-and-day combinations had no class at all this month. The studio has never tested them.',
                        'One four-week trial per gap, with the same trainer and hour as the successful version, turns an assumption into a fact at the cost of one slot.'))
    except Exception:
        pass
    return out
