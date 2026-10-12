"""Chapters 1 to 5 of the generated report."""
from __future__ import annotations
import pandas as pd, numpy as np
from .design import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                     A1, A2, A3, B1, B2, N1, N2)
from .metrics import DAYS, MONTH_NAMES


def _k(l, v, d='', t='neu'):
    return dict(label=l, value=v, detail=d, tone=t)


# ====================================================================== 1 sales
def sales(M):
    if not hasattr(M, 'sales') or M.y not in M.sales:
        return None
    F, P1 = M.sales[M.y], M.sales.get(M.y - 1)
    L = M.room.get(M.y, {})
    body = []
    kpis = [_k('Cash taken', R(F['cash']), f"{F['txn']} transactions from {F['buyers']} buyers", 'pos'),
            _k('Average buyer', R(F['ticket']), (f"{F['ticket']/P1['ticket']*100-100:+.0f}% on {M.y-1}" if P1 else ''), 'pos'),
            _k('Class revenue', R(L.get('rev', 0)), 'attributed to attended classes', 'pos'),
            _k('Revenue per class', R(L.get('rpc', 0)), f"against {R(M.room[M.y-1]['rpc'])} a year earlier" if (M.y-1) in M.room else '', 'pos')]

    body.append(f'''<h2>Start here</h2>
<p>{F['buyers']} people bought something at {M.studio} in {M.label}, for <strong>{R(F['cash'])}</strong> across {F['txn']} transactions.
That is an average of {R(F['ticket'])} a buyer{f", against {R(P1['ticket'])} in {MONTH_NAMES[M.m-1]} {M.y-1}" if P1 else ""}.</p>
<p>The month's class revenue of {R(L.get('rev', 0))} was earned on {L.get('sessions', 0)} classes, at
<strong>{R(L.get('rpc', 0))} a class and {R(L.get('rph', 0))} for every seat filled</strong>. Revenue per class is the number worth watching: it rises when the
studio fills better, prices better, or sells better products, and it is the only one of those three that the timetable does not control.</p>''')

    if hasattr(M, 'cats') and len(M.cats):
        c = M.cats.head(6)
        body.append(hbars([(str(i)[:30], float(v), A1 if n == 0 else A2) for n, (i, v) in enumerate(c['sum'].items())],
                          f'Where {M.label}’s money came from, by product category', maxv=None,
                          note=f"The month's {R(F['cash'])} split across {len(M.cats)} categories."))
        body.append(ev('Evidence — cash by category and by transaction',
                       T(['Category', 'Transactions', 'Cash', 'Average transaction'],
                         [[str(i), int(r['size']), R(r['sum']), R(r['sum'] / max(r['size'], 1))] for i, r in M.cats.iterrows()], 'num')))

    if P1:
        d = F['cash'] - P1['cash']
        body.append(f'''<h2>The year in context</h2>
<p>Against {MONTH_NAMES[M.m-1]} {M.y-1}, cash is {'up' if d >= 0 else 'down'} {R(abs(d))} and the average buyer is
{'worth more' if F['ticket'] >= P1['ticket'] else 'worth less'}. The counts moved differently from the value:
{F['txn']} transactions against {P1['txn']}, from {F['buyers']} buyers against {P1['buyers']}.</p>
<p>Discounted sales account for {F['spread']:.0f}% of the month{f", against {P1['spread']:.0f}% a year earlier" if P1 else ""}, at an average depth of
{F['depth']:.1f}%{f" against {P1['depth']:.1f}%" if P1 else ""}.</p>''')
        body.append(bars([f'{MONTH_NAMES[M.m-1][:3]} {y}' for y in sorted(M.sales)],
                         [('Cash taken', [M.sales[y]['cash'] for y in sorted(M.sales)], A1),
                          ('Average buyer, ×3', [M.sales[y]['ticket'] * 3 for y in sorted(M.sales)], B1)],
                         f'Cash and buyer value, {MONTH_NAMES[M.m-1]} across the years on file', h=300,
                         note='The second series is the average buyer value drawn at three times its true height so both fit one axis.'))

    if hasattr(M, 'sale_hours') and len(M.sale_hours):
        h = M.sale_hours
        best = int(h['size'].idxmax())
        body.append(bars([f'{int(i):02d}:00' for i in h.index], [('Transactions', [int(v) for v in h['size']], A1)],
                         'The hour of the day the studio takes its money', h=290,
                         note=f'The busiest trading hour of the month was {best:02d}:00.'))

    facts = [f'{M.label}: {R(F["cash"])} taken from {F["buyers"]} buyers across {F["txn"]} transactions.',
             f'Average buyer value {R(F["ticket"])}' + (f', against {R(P1["ticket"])} a year earlier.' if P1 else '.'),
             f'Class revenue {R(L.get("rev", 0))} at {R(L.get("rpc", 0))} a class and {R(L.get("rph", 0))} per seat filled.']
    return dict(id='sales', n=1, title='Sales Performance', lede=body[0].split('</h2>')[1][:400],
                body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{R(F["cash"])} of cash, {F["buyers"]} buyers, {R(F["ticket"])} each')


# ====================================================================== 2 class
def classperf(M):
    if 'sessions' not in M.has:
        return None
    F = M.room.get(M.y, {}); P1 = M.room.get(M.y - 1, {})
    body, kpis = [], [
        _k('Classes run', f"{F.get('sessions', 0):,}", (f"{F['sessions']/P1['sessions']*100-100:+.1f}% on {M.y-1}" if P1 else ''), 'neu'),
        _k('Capacity utilisation', P(F.get('fill', 0)), (f"from {P1['fill']:.1f}% a year earlier" if P1 else ''), 'pos'),
        _k('Attendances', f"{F.get('att', 0):,}", f"{F.get('classavg', 0):.1f} a class", 'neu'),
        _k('Empty sessions', f"{int((M._sl(M.D.sessions, M.y)['CheckedIn'] == 0).sum())}",
           f"{int((M._sl(M.D.sessions, M.y)['CheckedIn'] <= 2).sum())} ran to two people or fewer", 'neu')]

    body.append(f'''<h2>Start here</h2>
<p>{M.studio} ran <strong>{F.get('sessions', 0)} classes in {M.label}</strong>, offering {F.get('seats', 0):,.0f} seats and filling
{F.get('att', 0):,.0f} of them. Utilisation came in at <strong>{F.get('fill', 0):.1f}%</strong>{f", against {P1['fill']:.1f}% in the same month last year" if P1 else ""}.</p>
<p>Revenue per class was {R(F.get('rpc', 0))} and revenue per seat filled {R(F.get('rph', 0))}. Both matter more than attendance on their own, because a
timetable can raise attendance by adding classes and still earn less for every hour of the room.</p>''')

    if P1:
        rows = []
        for y in sorted(M.room):
            r = M.room[y]
            rows.append([str(y), f"{r['sessions']:,}", f"{r['seats']:,.0f}", f"{r['att']:,.0f}", P(r['fill']),
                         f"{r['lc']:.0f}", R(r['rev']), R(r['rpc']), R(r['rph'])])
        body.append(ev(f'Evidence — {MONTH_NAMES[M.m-1]} across the years on file',
                       T(['Year', 'Classes', 'Seats offered', 'Attended', 'Utilisation', 'Late cancels', 'Class revenue',
                          'Revenue / class', 'Revenue / attendee'], rows, 'num')))
        body.append(bars([str(y) for y in sorted(M.room)],
                         [('Seats offered', [M.room[y]['seats'] for y in sorted(M.room)], N2),
                          ('Seats filled', [M.room[y]['att'] for y in sorted(M.room)], A1)],
                         'What the room offered, and what it filled', h=310, ymax=None,
                         note='The gap between the two bars is the studio’s unused capacity.'))

    # where the empty seats sit
    if hasattr(M, 'hours') and len(M.hours):
        h = M.hours.dropna()
        weak = h.nsmallest(2, 'fill'); strong = h.nlargest(2, 'fill')
        body.append(f'''<h2>Where the empty seats are</h2>
<p>Unused capacity is not spread evenly across the week. The weakest hours were
<strong>{', '.join(f'{int(i):02d}:00 at {r["fill"]:.0f}%' for i, r in weak.iterrows())}</strong>;
the strongest were {', '.join(f'{int(i):02d}:00 at {r["fill"]:.0f}%' for i, r in strong.iterrows())}.</p>''')
        body.append(bars([f'{int(i):02d}:00' for i in h.index],
                         [('Seats offered', [float(v) for v in h['seats']], N2),
                          ('Seats filled', [float(v) for v in h['att']], A1)],
                         'Supply against demand, hour by hour', h=320,
                         note='The two bars sum to the seats the studio put on the board in that hour.'))

    if hasattr(M, 'days') and len(M.days.dropna()):
        d = M.days.dropna()
        body.append(bars([str(i)[:3] for i in d.index],
                         [('Seats offered', [float(v) for v in d['seats']], N2),
                          ('Seats filled', [float(v) for v in d['att']], A1)],
                         'Supply against demand, day by day', h=300,
                         note=f"{d['fill'].idxmax()} is the fullest day of the week at {d['fill'].max():.0f}%; {d['fill'].idxmin()} the emptiest at {d['fill'].min():.0f}%."))

    if hasattr(M, 'rooms') and len(M.rooms):
        r = M.rooms
        body.append(f'''<h2>Room size</h2>
<p>Small rooms fill; large rooms do not. Sessions in <strong>{r.iloc[0]['band']} filled {r.iloc[0]['fill']:.1f}%</strong>,
against {r.iloc[-1]['fill']:.1f}% in {r.iloc[-1]['band']}.</p>''')
        body.append(bars([str(i) for i in r['band']],
                         [('Seats offered', [float(v) * float(s) for v, s in zip(r['att'] / r['fill'] * 100, r['seats'])], N2),
                          ('Seats filled', [float(v) * float(s) for v, s in zip(r['att'], r['seats'])], A1)],
                         'Fill rate by the number of seats the room holds', h=300,
                         note='Rooms are grouped by their average capacity across the month.'))

    facts = [f'{F.get("sessions", 0)} classes, {F.get("seats", 0):,.0f} seats offered, {F.get("att", 0):,.0f} filled — {F.get("fill", 0):.1f}% utilisation.',
             f'Revenue per class {R(F.get("rpc", 0))}, revenue per attendee {R(F.get("rph", 0))}.',
             f'{int((M._sl(M.D.sessions, M.y)["CheckedIn"] == 0).sum())} classes had nobody in them and {int((M._sl(M.D.sessions, M.y)["CheckedIn"] <= 2).sum())} ran to two people or fewer.']
    return dict(id='class', n=2, title='Class Performance', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f"{F.get('sessions', 0)} classes at {F.get('fill', 0):.1f}% utilisation")


# ====================================================================== 3 instructor
def instructor(M):
    if not hasattr(M, 'trainers') or not len(M.trainers):
        return None
    t = M.trainers
    body, kpis = [], [
        _k('Trainers teaching', f'{len(t)}', f"{t['sessions'].sum():,.0f} classes between them", 'neu'),
        _k('Best utilisation', P(t['fill'].max()), f"{t['fill'].idxmax()} — {t['sessions'].max():.0f} classes", 'pos'),
        _k('Lowest utilisation', P(t['fill'].min()), f"{t['fill'].idxmin()} — {t['sessions'].min():.0f} classes", 'neg'),
        _k('Revenue span', f"{t['rev'].max()/max(t['rev'].min(),1):.0f}×", f"{R(t['rev'].min())} to {R(t['rev'].max())}", 'neu')]

    spread = t['fill'].max() / max(t['fill'].min(), 0.1)
    rph = t['rph'].dropna()
    body.append(f'''<h2>Start here</h2>
<p>{len(t)} trainers taught {t['sessions'].sum():,.0f} classes at {M.studio} in {M.label}, drawing {t['att'].sum():,.0f} attendances and
<strong>{R(t['rev'].sum())} of class revenue</strong>. Utilisation ranges from {t['fill'].min():.1f}% to {t['fill'].max():.1f}% — the strongest
trainer fills <strong>{spread:.1f} times as many seats as the weakest</strong>.</p>
<p>Revenue per attendee, though, is nearly flat, from {R(rph.min())} to {R(rph.max())} — a spread of only {rph.max()/rph.min()*100-100:.0f}%.
That matters more than it sounds: it means trainers are not teaching audiences of different value. They are being handed
<strong>differently sized rooms at differently attractive times</strong>, and the scorecard below is substantially a picture of the timetable.</p>''')

    body.append(hbars([(str(i)[:22], float(v), A1 if v >= t['fill'].median() else B1) for i, v in t['fill'].items()],
                      'Capacity utilisation by trainer', as_pct=True, unit='', maxv=100,
                      note='Attendance as a share of the seats each trainer was given. Utilisation is the cleanest measure of whether the slots are right.'))

    rows = [[str(i), f"{r['sessions']:.0f}", f"{r['att']:.0f}", f"{r['att']/max(r['sessions'],1):.2f}", P(r['fill']),
             P(r['lc_rate']) if pd.notna(r['lc_rate']) else '—', f"{r['formats']:.0f}", R(r['rev']), R(r['rpc']),
             R(r['rph']) if pd.notna(r['rph']) else '—'] for i, r in t.iterrows()]
    body.append(ev('Evidence — the full trainer scorecard',
                   T(['Trainer', 'Classes', 'Attendees', 'Avg class', 'Utilisation', 'Late-cancel rate', 'Formats',
                      'Revenue', 'Revenue / class', 'Revenue / attendee'], rows, 'num')))

    if 'checkins' in M.has:
        a = M._ck(M.y)
        first = a.groupby('Member ID')['_dt'].min()
        new_ids = set(first[first.dt.to_period('M') == pd.Period(f'{M.y}-{M.m:02d}')].index)
        by_t = a[a['Member ID'].isin(new_ids)].groupby('Teacher Name')['Member ID'].nunique() if 'Teacher Name' in a.columns else None
        if by_t is not None and len(by_t):
            body.append(f'''<h2>Who brings people in</h2>
<p>{len(new_ids):,} members made their first visit in {M.label}. {by_t.idxmax()} taught {int(by_t.max())} of them,
more than any other trainer — new-member flow is a second dimension on which trainers differ, and it is not the same
list as the utilisation table.</p>''')
            body.append(hbars([(str(i)[:22], float(v), A2) for i, v in by_t.sort_values(ascending=False).head(10).items()],
                              'New members taught, by trainer', unit='', maxv=None,
                              note=f'Members whose first visit to {M.studio} fell in {M.label}, counted against the trainer who took that class.'))

    body.append(f'''<h2>Reading the scorecard fairly</h2>
<p>A trainer who holds Saturday mornings and 11:00 slots will fill their rooms. A trainer who holds Monday 07:30 and Thursday 18:00 will not, whatever
they do. The honest way to use this table is in two passes: first assess how well each trainer fills <em>the slots they hold</em>, and separately ask whether
those slots should exist at all.</p>''')
    facts = [f'{len(t)} trainers taught {t["sessions"].sum():,.0f} classes for {R(t["rev"].sum())}.',
             f'Utilisation runs {t["fill"].min():.1f}% to {t["fill"].max():.1f}% — a {spread:.1f}-fold spread.',
             f'Revenue per attendee is nearly flat at {R(rph.min())} to {R(rph.max())}, so the spread is mostly the slots, not the trainers.']
    return dict(id='instructor', n=3, title='Instructor Performance', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{len(t)} trainers, {spread:.1f}× spread in utilisation')


# ====================================================================== 4 lapse
def lapse(M):
    if 'lapsed' not in M.has:
        return None
    body, kpis = [], [
        _k('Memberships in the ledger', f"{M.led['rows']:,}", f"{M.led['members']:,} people", 'neu'),
        _k('Paid memberships', f"{M.led['paid']:,}", f"from {M.led['paid_members']:,} members", 'neu'),
        _k('Still running after 30 days', P(getattr(M, 'surv', pd.DataFrame()).set_index('Point')['still'].get('Day 30', float('nan')))
           if hasattr(M, 'surv') else '—', 'the sharpest retention number here', 'neg'),
        _k('Median membership life', f"{int(getattr(M, 'median_life', 0))} days", f"average ticket {R(getattr(M, 'ticket', 0))}", 'neg')]

    body.append(f'''<h2>Start here</h2>
<p>Every membership ever sold at {M.studio} sits in this ledger: <strong>{M.led['rows']:,} memberships taken out by {M.led['members']:,} people</strong>,
of which {M.led['paid']:,} were paid. Read forward from purchase, the pattern is stark and consistent:
{'<strong>' + P(M.surv.set_index('Point')['still'].get('Day 30', 0)) + ' of paid memberships are still running after thirty days</strong>' if hasattr(M, 'surv') else ''}
{('and the median membership lasts ' + str(int(M.median_life)) + ' days — not months, days.') if hasattr(M, 'median_life') else ''}</p>
<p>This is the number every other conversation depends on. A studio that replaces most of its book every month is not running a retention business;
it is running a subscription with a very short billing cycle, and the acquisition engine has to run hard just to stand still.</p>''')

    if hasattr(M, 'surv'):
        s = M.surv
        body.append(bars([str(i) for i in s['Point']], [('Still in force', [float(v) / 100 for v in s['still']], A1)],
                         f'How long a paid membership actually lasts', h=310, as_pct=True, ymax=1.0,
                         note=f'Paid memberships bought at {M.studio} with dates on file, n = {M.surv_n:,}. Memberships still open count as surviving, so the curve is a floor.'))
        body.append(ev('Evidence — survival of the paid book',
                       T(['Point', 'Still in force', 'Ended by then'],
                         [[str(i), P(r['still']), P(r['ended'])] for i, r in s.iterrows()], 'num')))

    if hasattr(M, 'dur') and len(M.dur):
        d = M.dur
        body.append(f'''<h2>How people are lost</h2>
<p>Split the membership book by how long it actually ran and the shape of the loss appears. The most common band is
<strong>{d.loc[d['n'].idxmax(), 'Membership Duration (Days)'] if 'Membership Duration (Days)' in d else d.iloc[d['n'].argmax()][0]}</strong>,
carrying {int(d['n'].max()):,} memberships. Members in the shortest bands paid {R(d['ticket'].min())} on average and completed
{d['cls'].min():.1f} classes; the longest-running paid {R(d['ticket'].max())} and completed {d['cls'].max():.1f}.</p>''')
        body.append(bars([str(i) for i in d.iloc[:, 0]],
                         [('Memberships', [int(v) for v in d['n']], A1),
                          ('Mean classes completed, ×50', [float(v) * 50 for v in d['cls']], B1)],
                         'Memberships by how long they ran, and how much was used', h=310,
                         note='The second series is mean classes completed, drawn at fifty times its true value.'))
        body.append(ev('Evidence — membership lifetime bands',
                       T(['How long it lasted', 'Memberships', 'Mean price paid', 'Mean classes completed'],
                         [[str(r.iloc[0]), int(r['n']), R(r['ticket']), f"{r['cls']:.1f}"] for _, r in d.iterrows()], 'num')))

    if hasattr(M, 'products') and len(M.products):
        p = M.products.head(10)
        body.append(f'''<h2>Product by product</h2>
<p>Sorted by how many are still alive, the products separate cleanly. <strong>{p.index[0]} renews or stays live {p['live'].iloc[0]:.0f}% of the time</strong>;
{p.index[-1]} manages {p['live'].iloc[-1]:.0f}%. Commitment length predicts survival far better than price does — the products sold as a
programme keep their members, and the products sold as a quantity of classes do not.</p>''')
        body.append(hbars([(str(i)[:26], float(v), A1 if v >= 30 else B1) for i, v in p['live'].items()],
                          'Share of each product still live or renewed', as_pct=True, unit='', maxv=100,
                          note=f'Paid memberships at {M.studio}, products with ten or more sold.'))

    if hasattr(M, 'recency') and len(M.recency):
        r = M.recency
        body.append(f'''<h2>Who is winnable</h2>
<p>Sorted by how long it has been since they last came, the book splits into groups with very different economics.
The warm group — in the room within the last sixty days — is <strong>{int(r.iloc[0]['members']):,} members</strong> who paid
{R(r.iloc[0]['cash'])} on average. The group gone more than six months is {int(r.iloc[-1]['members']):,} members who paid {R(r.iloc[-1]['cash'])}.</p>
<p>The instinct is to chase whoever spent the most over their lifetime. The data says the opposite: the members still worth winning are the ones
who have been gone the least time, and they are usually the ones who were worth the most.</p>''')
        body.append(bars([str(i) for i in r.iloc[:, 0]],
                         [('Members', [int(v) for v in r['members']], A1),
                          ('Mean cash paid, ÷500', [float(v) / 500 for v in r['cash']], B1)],
                         'Time since the last visit, against what those members paid', h=300,
                         note='The second series is mean recorded cash per member, divided by five hundred so it shares the axis.'))

    if hasattr(M, 'cancel_bands') and len(M.cancel_bands):
        c = M.cancel_bands
        body.append(f'''<h2>What cancelling predicts</h2>
<p>Across the paid book, members who never released a seat late completed {c['cls'].iloc[0]:.1f} classes on average; those who cancelled most
completed {c['cls'].iloc[-1]:.1f} and averaged {c['late'].iloc[-1]:.1f} late cancellations each. Renewal rates barely move between the bands —
<strong>cancelling is a symptom of a life getting busier, not a cause of leaving</strong>. Which is precisely what makes it useful: it appears weeks
before the member stops coming, and it is already recorded.</p>''')
        body.append(ev('Evidence — the paid book by how often the member cancelled',
                       T(['Cancellation band', 'Memberships', 'Mean classes', 'Mean late cancels', 'Still live or renewed'],
                         [[str(r.iloc[0]), int(r['n']), f"{r['cls']:.1f}", f"{r['late']:.1f}", P(r['live'])] for _, r in c.iterrows()], 'num')))

    if hasattr(M, 'unused_n'):
        body.append(f'''<h2>Unused credit</h2>
<p>Session allowance is recorded for {M.unused_n:,} package and credit memberships. <strong>{M.unused_full:,} of them used every class they bought</strong>,
while {M.unused_low:,} used a quarter or less — leaving {M.unused_left:,.0f} classes unspent.</p>
<p>A member who has paid and not attended has received nothing for their money. That is a commercial liability and a human one, and it is countable today.</p>''')

    facts = [f'{M.led["rows"]:,} memberships, {M.led["paid"]:,} of them paid, in the {M.studio} ledger.']
    if hasattr(M, 'surv'):
        s = M.surv.set_index('Point')['still']
        facts.append(f'{s.get("Day 30", 0):.0f}% of paid memberships survive thirty days, {s.get("Day 180", 0):.0f}% survive six months.')
    if hasattr(M, 'median_life'):
        facts.append(f'The median paid membership lasts {int(M.median_life)} days and carries {R(M.ticket)} of recorded cash.')
    return dict(id='lapse', n=4, title='Memberships Lapsed and Churned', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{M.led["paid"]:,} paid memberships, median life {int(getattr(M, "median_life", 0))} days')


# ====================================================================== 5 format
def formatcmp(M):
    if not hasattr(M, 'formats') or not len(M.formats):
        return None
    f = M.formats
    fm_ = getattr(M, 'formats_main', f)
    top = fm_.iloc[0]
    body, kpis = [], [
        _k('Formats run', f'{len(f)}', f"{f['sessions'].sum():,.0f} classes, {f['att'].sum():,.0f} attendances", 'neu'),
        _k('Biggest format', str(f.index[0]).replace('Studio ', ''),
           f"{top['sessions']:.0f} classes, {top['fill']:.1f}% full", 'neu'),
        _k('Fullest format', str(f['fill'].idxmax()).replace('Studio ', ''), P(f['fill'].max()), 'pos'),
        _k('Widest gap', f"{f['fill'].max()/max(f['fill'].min(),1):.0f}×", f"{f['fill'].min():.0f}% to {f['fill'].max():.0f}%", 'neg')]

    body.append(f'''<h2>Start here</h2>
<p>{M.label} ran {f['sessions'].sum():,.0f} classes across <strong>{len(fm_)} formats that ran three times or more</strong>, drawing {f['att'].sum():,.0f} attendances and
{R(f['rev'].sum())} of revenue. No format wins everything, and the pattern of who wins what is the finding.</p>
<p><strong>{str(fm_['fill'].idxmax()).replace('Studio ', '')} fills {fm_['fill'].max():.1f}% of its seats on {fm_.loc[fm_['fill'].idxmax(), 'sessions']:.0f} classes</strong>,
while {str(fm_['fill'].idxmin()).replace('Studio ', '')} manages {fm_['fill'].min():.1f}%.</p>''')

    body.append(hbars([(str(i).replace('Studio ', '')[:24], float(v), A1 if v >= fm_['fill'].median() else B1) for i, v in fm_['fill'].items()],
                      'Capacity utilisation by format', as_pct=True, unit='', maxv=100,
                      note='Attendance as a share of the seats each format put on the board.'))

    rows = [[str(i).replace('Studio ', ''), f"{r['sessions']:.0f}", f"{r['seats']:,.0f}", f"{r['att']:,.0f}", P(r['fill']),
             R(r['rev']), R(r['rpc']), R(r['rph']) if pd.notna(r['rph']) else '—', P(r['share_sessions'])]
            for i, r in f.iterrows()]
    body.append(ev('Evidence — the format league table',
                   T(['Format', 'Classes', 'Seats', 'Attendance', 'Utilisation', 'Revenue', 'Revenue / class',
                      'Revenue / attendee', 'Share of timetable'], rows, 'num')))

    if hasattr(M, 'fmt_members') and len(M.fmt_members):
        fm = M.fmt_members
        body.append(f'''<h2>Reach against regularity</h2>
<p>Two measures describe a format better than attendance: how many different members it reaches, and how often those members come back inside the month.
<strong>{str(fm['members'].idxmax()).replace('Studio ', '')} reaches the most members ({int(fm['members'].max())})</strong>, while
{str(fm['per'].idxmax()).replace('Studio ', '')} has the highest visits per member at {fm['per'].max():.2f}.</p>
<p>A format that reaches many people occasionally is a different product from one that reaches fewer people repeatedly — and the studio is currently
scheduling as though they were interchangeable.</p>''')
        body.append(bars([str(i).replace('Studio ', '')[:16] for i in fm.sort_values('members', ascending=False).head(8).index],
                         [('Members reached', [int(v) for v in fm.sort_values('members', ascending=False).head(8)['members']], A1),
                          ('Visits per member, ×20', [float(v) * 20 for v in fm.sort_values('members', ascending=False).head(8)['per']], B1)],
                         'Reach against regularity, by format', h=320, rotate=True,
                         note='The second series is visits per member drawn at twenty times its true value.'))

    if hasattr(M, 'fmt_members') and hasattr(M, 'beh'):
        body.append(f'''<h2>Routine and variety</h2>
<p>{M.beh.get('multi', 0):.0f}% of the month's members used more than one format, and {M.beh.get('same3_members', 0)} members made three or more
visits to a single format. Both behaviours are associated with longer membership lives, and neither is currently managed: nothing in the studio uses a
member's own favourite format to hold their slot or to invite them into the next one.</p>''')

    facts = [f'{len(fm_)} formats ran {f["sessions"].sum():,.0f} classes for {R(f["rev"].sum())} in {M.label}.',
             f'{str(fm_["fill"].idxmax()).replace("Studio ", "")} is the fullest format at {fm_["fill"].max():.1f}%; {str(fm_["fill"].idxmin()).replace("Studio ", "")} the emptiest at {fm_["fill"].min():.1f}%.',
             f'{str(f["rpc"].idxmax()).replace("Studio ", "")} earns the most per class at {R(f["rpc"].max())}.']
    return dict(id='format', n=5, title='Format Comparisons', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{len(fm_)} formats, {f["sessions"].sum():,.0f} classes, {fm_["fill"].max():.0f}% to {fm_["fill"].min():.0f}% fill')
