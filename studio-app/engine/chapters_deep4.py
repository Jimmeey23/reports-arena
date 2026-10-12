"""Chapters 6 to 9: cancellations and discounts, the studio overview, leads,
and member behaviour - at the depth of the reports they replace."""
from __future__ import annotations
import numpy as np, pandas as pd
from .design import (R, Rs, P, N, T, ev, note, bars, lines, hbars, diverging, stacked,
                     funnel, dumbbell, A1, A2, A3, B1, B2, N1, N2)
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


# ============================ 6. LATE CANCELLATIONS AND DISCOUNTS
def cancels(M):
    if 'sessions' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    F = M.room.get(y, {}); P1 = M.room.get(y - 1, {})
    lc = M.lc_year.get(y, {}); lcp = M.lc_year.get(y - 1, {})
    C = X.cls; cur = C.get('cur')
    mon = mono(M)
    if not F:
        return None

    def start():
        released = float(F.get('lc', 0))
        lost = float(F.get('book', 0)) - float(F.get('att', 0))
        p = [para(f'{released:,.0f} of the {F["book"]:,.0f} booked seats in {lab} were released inside the cancellation '
                  f'window &mdash; {lc.get("rate", 0):.1f}% of the book. They were offered back to the studio and '
                  f'{released - (float(cur["LateCancelled"].sum() - cur["LateCancelled"].sum()) if False else 0):,.0f} '
                  f'of them stayed open.'),
             para(f'A late cancellation is not one event, it is two. The member keeps their credit and the studio loses the '
                  f'seat; the seat returns to the studio too late for anybody else to book it. This chapter prices the second '
                  f'loss, shows who causes it and when, and then looks at the other thing the studio gives away '
                  f'unquantified: the discount.'),
             (f'A year ago the same month released {lcp.get("lc", 0):,.0f} seats at {lcp.get("rate", 0):.1f}% &mdash; so the '
              f'rate has moved {lc.get("rate", 0) - lcp.get("rate", 0):+.1f} points while the book itself moved '
              f'{F["book"] - lcp.get("book", 0):+,.0f} seats. A rate can improve because the denominator grew.' if lcp else '')]
        claim = (f'The {released:,.0f} released seats are worth about {R(released * F.get("rph", 0))} of class revenue at this '
                 f'studio’s average {R(F.get("rph", 0))} per attendance. Nothing recovers that money today: the seat returns, '
                 f'the credit stays, and the room empties.')
        b = [statgrid([('Seats released late', f'{released:,.0f}'), ('As a share of the book', f'{lc.get("rate", 0):.1f}%'),
                       ('Revenue per attendance', R(F.get('rph', 0))), ('Value of the released seats', R(released * F.get('rph', 0)))])]
        return head('Start here', 'What the studio gives up when a seat comes back late', claim) + ''.join(p + b)

    def price():
        released = float(F.get('lc', 0))
        val = released * F.get('rph', 0)
        byf = C.get('book')
        p = [para(f'Priced at the studio’s own revenue per attendance, the month’s late releases are worth {R(val)}. '
                  f'That is not lost revenue in the accounting sense &mdash; the class was already sold &mdash; it is the '
                  f'revenue the studio could have taken on the same seat, or the cost of teaching to a half-empty room.'),
             para('The correct unit is the seat, not the class. A released seat in a 22-room at 07:00 is worth a different '
                  'amount to a released seat in a 10-room at 18:30, because only one of them can realistically be resold. '
                  'Any policy that charges for cancellations uniformly is taxing the two cases at the same rate and '
                  'collecting the wrong one.')]
        b = []
        if byf is not None and len(byf):
            byf = byf.drop(columns=[c for c in ('lc',) if c in byf]).join(
                cur.groupby('_cls')['LateCancelled'].sum().rename('lc'), how='left')
            byf['val'] = byf['lc'] * F.get('rph', 0)
            b.append(tab(byf.sort_values('lc', ascending=False).reset_index(),
                         ['Format', 'Booked', 'Attended', 'Late cancelled', 'Show rate', 'Seats lost', 'Value of late releases'],
                         ['w', 'n', 'n', 'n', 'p', 'n', 'm'], maxrows=20))
            b.append(hbars([(clean(i), float(v), B1) for i, v in byf['lc'].sort_values(ascending=False).head(10).items()],
                           f'Seats released late, by format, {lab}', unit='',
                           note='A format with a large number of late releases is not a format with unreliable members; check what hour it runs in first.'))
        if lcp:
            yrs = sorted(M.lc_year)
            b.insert(0, bars([f'{mon[:3]} {z}' for z in yrs],
                             [('Seats released late', [float(M.lc_year[z]['lc']) for z in yrs], A1),
                              ('Rate on the book %', [float(M.lc_year[z]['rate']) for z in yrs], B1)],
                             f'Late cancellations in {mon}, by year', h=290,
                             note='The pale bars are the count; the accent bars are the same count as a share of that year’s booked seats.'))
        return sec('What a released seat costs', 'Pricing the thing nobody prices', p, b)

    def who():
        ck = None
        try:
            ck = M._ck(y, attended=False, cancelled=True)
        except Exception:
            pass
        p, b = [], []
        if ck is not None and len(ck):
            hr = ck.groupby(ck['_dt'].dt.hour).size().sort_values(ascending=False)
            dw = ck.groupby(ck['_dt'].dt.day_name()).size().reindex(DAYS).fillna(0)
            p.append(para(f'The moment matters more than the person. Late releases cluster at '
                          + ' · '.join(f'{int(i):02d}:00 ({_n(v)})' for i, v in hr.head(4).items())
                          + ' &mdash; in the hours immediately before a morning class. That is not carelessness; it is members '
                            'deciding at the last possible moment, which is exactly what a lenient window invites.'))
            p.append(para('By weekday: ' + ' · '.join(f'{clean(i)} {_n(v)}' for i, v in dw.items() if v) +
                          '. The heaviest day carries ' + f'{dw.max() / max(dw.sum(), 1) * 100:.0f}% of the month’s releases.'))
            b.append(bars([f'{int(i):02d}:00' for i in hr.index[:10]], [('Seats released', [float(v) for v in hr.head(10)], A1)],
                          f'When the seat comes back', h=300,
                          note='Hour of the cancelled class, not the hour of the cancellation, which the exports do not record. Stated here because the two are usually the same day.'))
            b.append(T([mon + ' releases by day'] + [clean(i) for i in dw.index],
                       [[_n(v) for v in dw.values]], 'num'))
            if 'Teacher Name' in ck:
                tr = ck.groupby(ck['Teacher Name'].astype(str).str.strip()).size().sort_values(ascending=False)
                if len(tr) > 2:
                    p.append(para(f'Trainers differ, but not by much: ' + ' · '.join(
                        f'{clean(i)} {_n(v)}' for i, v in tr.head(5).items()) +
                        f', out of {len(ck):,} released seats. The spread between the highest and lowest is '
                        f'{ratio(tr.max(), tr.min())} times, which is small enough that hour and format explain more than the person does.'))
                    b.append(hbars([(clean(i), float(v), A2) for i, v in tr.head(12).items()],
                                   'Late releases per trainer', unit='',
                                   note='Counted on the trainer of the cancelled class. Compare with the same trainer’s hour mix before drawing a conclusion.'))
        if hasattr(M, 'lc_conc') and M.lc_conc.get('members'):
            c = M.lc_conc
            p.append(para(f'The behaviour is concentrated: {c["members"]:,} people produced {c["per"]:,} late releases this '
                          f'month, and the ten most frequent account for {c["top10_share"]:.0f}% of them. '
                          f'{c["three_plus"]} members cancelled three or more times.'))
            b.append(para('A policy aimed at everybody, therefore, is mostly aimed at the people who never need it. The '
                          'studio can address a hundred members by name, or a thousand members by rule, and only one of '
                          'those is cheap.'))
        if ck is not None and len(ck):
            b.append(frame_ev('Evidence &mdash; every late-cancelled booking in the month, by member',
                              ck.groupby('Member ID').size().sort_values(ascending=False).head(60).reset_index(),
                              ['Member ID', 'Seats released late'], ['w', 'n'],
                              blurb='From the check-in ledger, where a late cancellation is recorded as its own row.'))
        return sec('Who cancels, and when', 'The hour, the weekday and the hundred people', p, b)

    def predicts():
        cb = getattr(M, 'cancel_bands', None)
        if cb is None or not len(cb):
            return ''
        p = [para(f'The membership ledger lets cancellation behaviour be read against what happened to the membership. '
                  + ' · '.join(f'{clean(r["b"])}: {int(r["n"])} memberships, median '
                               f'{getattr(M, "median_life", 0) and _f(r["cls"], 1)} visits and '
                               f'{r["live"]:.0f}% still live' for _, r in cb.iterrows()) + '.'),
             para('The direction is the finding: members who cancel more attend less and lapse sooner. What the data cannot '
                  'say is which way the arrow points. Cancelling may be the symptom of a member who has already decided to '
                  'stop, in which case charging them recovers nothing and adds a reason to go. Or it may be the cause, in '
                  'which case a booking that is easier to release is a booking that is easier to abandon. The studio should '
                  'pick the reading that its own front-desk experience supports and test it for a quarter.')]
        b = [tab(cb, ['Late cancellations', 'Memberships', 'Classes completed', 'Late per member', 'Still live %'],
                 ['w', 'n', 'f1', 'f1', 'p'], 'num'),
             bars([clean(v) for v in cb['b']], [('Still live %', [float(x) for x in cb['live']], A1)],
                  'Does cancelling predict a shorter membership?', h=300, as_pct=True, ymax=100,
                  note='Memberships grouped by their own recorded cancellation rate. This is a correlation across the whole ledger, not an experiment.')]
        ns = X.lp.get('noshow')
        if ns is not None and len(ns):
            b.append(para('No-shows show the same gradient and more steeply: ' + ' · '.join(
                f'{clean(i)} median {_f(r["days"], 0)} days and {_f(r["used"], 0)}% used' for i, r in ns.iterrows()) +
                '. A member who does not cancel at all is not a member who always comes; often it is a member who has '
                'already stopped telling anyone.'))
        return sec('What cancelling actually predicts', 'Symptom or cause, and why it matters', p, b)

    def discbook():
        S = X.sales
        cd = S.get('codes')
        dy = getattr(M, 'disc_year', {})
        if cd is None or not len(cd):
            return ''
        Fx = M.sales[y]
        p = [para(f'{R(Fx["disc"])} was given away in {lab} on {Fx["spread"]:.0f}% of transactions at an average depth of '
                  f'{Fx["depth"]:.1f}%. Four codes account for all of it: ' + rank_list(cd, 'given', len(cd)) + '.'),
             para(f'The largest code carries {share(cd["given"].max(), cd["given"].sum())} of the discounting. A single code '
                  f'with that much of the total is not a pricing policy; it is a person at a desk with a permission. Whether '
                  f'that is deliberate depends on something the exports cannot show: who is allowed to enter it.')]
        b = [tab(cd.reset_index(), ['Code', 'Uses', 'Given away', 'Net cash', 'Buyers', 'Depth'], ['w', 'n', 'm', 'm', 'n', 'p'])]
        if len(dy) > 1:
            yrs = sorted(dy)[-4:]
            b.append(T([f'{mon} {z}' if False else f'Year {z}' for z in yrs] + ['Lines discounted', 'Spread %', 'Depth %', 'Given away'],
                       [[_n(dy[z]['lines']), _f(dy[z]['spread']), _f(dy[z]['depth']), R(dy[z]['disc'])] for z in yrs], 'num'))
            b.append(para('Whole-year figures, because a single month’s codes are too few to be stable: spread and depth '
                          'have moved together across the years on file, which means discounting here is responding to '
                          'demand rather than driving a policy.'))
        dp = getattr(M, 'disc_prod', None)
        if dp is not None and len(dp):
            b.append(frame_ev('Evidence &mdash; discount by product, whole year', dp.reset_index(),
                              ['Product', 'Lines', 'Given away', 'Gross', 'Spread %', 'Depth %'],
                              ['w', 'n', 'm', 'm', 'p', 'p'], maxrows=40,
                              blurb='Products with fewer than eight lines in the year are excluded so that depth is not set by one transaction.'))
        return sec('The discount book', f'{R(Fx["disc"])} given away, and where it went', p, b)

    def works():
        S = X.sales
        cur_s = S.get('cur'); prev_s = S.get('prev')
        if cur_s is None or not len(cur_s) or 'has_disc' not in cur_s:
            return ''
        out = []
        try:
            d = cur_s.groupby('has_disc').agg(n=('val', 'size'), cash=('val', 'sum'),
                                              buyers=('Member ID', 'nunique'), avg=('val', 'mean'))
            dt = d.loc[True] if True in d.index else None
            nd = d.loc[False] if False in d.index else None
            sentence = ('Discounted lines: %d at an average of %s. Undiscounted: %d at %s. '
                        % (int(dt['n']) if dt is not None else 0, R(dt['avg']) if dt is not None else '-',
                           int(nd['n']) if nd is not None else 0, R(nd['avg']) if nd is not None else '-'))
            if dt is not None and nd is not None:
                if dt['avg'] < nd['avg']:
                    sentence += ('The discount is not buying a bigger ticket: it is attached to the smaller ones, which '
                                 'means it is being used to close a hesitation rather than to move volume.')
                else:
                    sentence += ('Discounted lines are the larger ones here, which is what a discount aimed at '
                                 'commitment looks like: the studio is buying the longer product, not the impulse buy.')
            out.append(para(sentence))
        except Exception:
            pass
        try:
            ids = set(cur_s[cur_s['has_disc']]['Member ID'].dropna())
            und = set(cur_s[~cur_s['has_disc']]['Member ID'].dropna())
            v = M.people.get(y, {}).get('v')
            if v is not None and len(v) and ids and und:
                a = float(v.reindex(list(ids)).dropna().mean() or 0)
                b2 = float(v.reindex(list(und)).dropna().mean() or 0)
                out.append(para(f'Members who took a discount this month came <strong>{a:.2f} times</strong> on average; '
                                f'those who did not, {b2:.2f} times. '
                                + ('If the discount is buying frequency it is not working. '
                                   if a < b2 else 'The discount is buying attendance here, which is a defensible reason to run it. ')
                                  + f'On a membership book with a median life of {getattr(M, "median_life", 0):.0f} days, '
                                    f'{abs(a - b2):.2f} visits is the entire distance between a renewal and a lapse.'))
        except Exception:
            pass
        b = []
        if out:
            try:
                lp = X.lp.get('disc')
                if lp is not None and len(lp):
                    b.append(tab(lp.reset_index(), ['Discount taken', 'Memberships', 'Average paid', 'Median days live', 'Still live %'],
                                 ['w', 'n', 'm', 'f1', 'p']))
            except Exception:
                pass
        return sec('Do discounts work?', 'What the money bought', out, b)

    def timetable():
        if cur is None or not len(cur):
            return ''
        try:
            g = cur.assign(lcr=cur['LateCancelled'] / cur['Booked'].replace(0, np.nan) * 100)
            h = g.groupby(g['_hr'].astype('Int64')).agg(classes=('SessionID', 'size'), book=('Booked', 'sum'),
                                                          lc=('LateCancelled', 'sum'), seats=('_cap', 'sum'),
                                                          att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
            h['lc_rate'] = h['lc'] / h['book'].replace(0, np.nan) * 100
            h['fill'] = h['att'] / h['seats'] * 100
        except Exception:
            return ''
        best = h['lc_rate'].idxmin(); worst = h['lc_rate'].idxmax()
        p = [para(f'Releases are not spread evenly through the day: {int(worst):02d}:00 loses '
                  f'{h.loc[worst, "lc_rate"]:.1f}% of its bookings while {int(best):02d}:00 loses '
                  f'{h.loc[best, "lc_rate"]:.1f}%. The early hours are where a member has the most reason to change their '
                  f'mind, and also where a seat is hardest to refill, because the person who might take it is still asleep.'),
             para(f'That is the argument for a waitlist rather than a penalty. In the {int(h.loc[worst, "lc"]):,.0f} seats '
                  f'released at {int(worst):02d}:00 alone, a text to three members holding no booking would cost the studio '
                  f'nothing and could recover {R(float(h.loc[worst, "lc"]) * F.get("rph", 0) * 0.34)} at a third fill-up rate.')]
        b = [tab(h.reset_index(), ['Hour', 'Classes', 'Booked', 'Late cancelled', 'Release rate', 'Utilisation', 'Revenue'],
                 ['n', 'n', 'n', 'n', 'p', 'p', 'm'], 'num')]
        return sec('Cancellations and the timetable', 'Which hours the studio is really running', p, b)

    def causes():
        items = [('part', 'The policy is lenient',
                  f'{lc.get("rate", 0):.1f}% of booked seats came back late. A studio with a hard 12-hour window rarely '
                  f'exceeds 5%; a studio with no enforced window rarely stays under 15%.',
                  'Cannot be confirmed from these files: the exports record that a seat was late-cancelled, never the rule that allowed it.'),
                 ('yes', 'It is an hour problem, not a member problem',
                  'The release rate varies more by hour than by trainer, and the peak of releases sits in the earliest '
                  'classes of the day.',
                  'Re-time one class and watch both fill and release rate for four weeks.'),
                 ('no', 'A few members are abusing the system',
                  (f'{M.lc_conc["three_plus"]} of {M.lc_conc["members"]:,} cancelling members did so three or more times, and '
                   f'the ten most frequent produced {M.lc_conc["top10_share"]:.0f}% of releases.'
                   if hasattr(M, 'lc_conc') and M.lc_conc.get('members') else 'Concentration exists but is small.'),
                  'A rule aimed at everybody is mostly aimed at the people who never need it, and it costs the goodwill of the many to police the few.'),
                 ('part', 'Discounting reduces commitment',
                  'Discounted lines in this month do not go on to attend more often than undiscounted ones.',
                  'Test on one product for a quarter before changing the whole ladder.')]
        return sec('What else could explain it', 'Four readings of the same number', [para('A late-cancellation rate is a policy, a timetable and a set of individuals all at once. Before acting on it, the studio should say which of the three it thinks it is changing.')], [hyp(items)])

    body = run([start, price, who, predicts, discbook, works, timetable, causes])
    defs = [('Late cancellation', 'the LateCancelled count on a session row: a booking released inside the studio’s cancellation window, as the system applies it.'),
            ('Release rate', 'late cancellations divided by seats booked, not by seats offered.'),
            ('Value of a released seat', 'the studio’s own revenue per attendance for that month, applied to the seat. It is an opportunity cost, not a booked loss.'),
            ('Discount depth', 'discount as a share of gross value. Spread is the share of lines carrying any discount at all.'),
            ('Member cancellation band', 'the Cancellation Rate % the membership ledger records against each member, banded for readability.')]
    caut = [('The exports do not record when a cancellation was made, only that it counted as late, so the lead time of the decision is invisible.'),
            ('Discount figures are as the sales ledger records them. A free class granted verbally at the desk never appears here at all.'),
            ('The relationship between cancelling and churn is correlational. Both are read from the same membership row, and neither controls for the hour the member trains in.'),
            ('A seat released at 06:45 for a 07:00 class and one released the previous evening are counted identically by the source system.')]
    body += appendix(M, X, 'cancels')
    body += method(M, defs, caut)
    kpis = [kpi('Seats released late', f'{float(F["lc"]):,.0f}', f'{lc.get("rate", 0):.1f}% of the book', 'neg'),
            kpi('Value at average', R(float(F['lc']) * F.get('rph', 0)), 'opportunity cost, not a booked loss'),
            kpi('Discount given', R(M.sales[y]['disc']) if 'sales' in M.has else '-', f'{M.sales[y]["depth"]:.1f}% depth' if 'sales' in M.has else ''),
            kpi('Year on year', f'{lc.get("rate", 0) - lcp.get("rate", 0):+.1f} pts' if lcp else '-', f'{mon} {y - 1} was {lcp.get("rate", 0):.1f}%' if lcp else '')]
    facts = [f'{float(F["lc"]):,.0f} seats were released late in {lab}, {lc.get("rate", 0):.1f}% of everything booked.',
             f'At {R(F.get("rph", 0))} of revenue per attendance those seats are worth about {R(float(F["lc"]) * F.get("rph", 0))}.',
             f'{M.sales[y]["disc"]:,.0f} rupees of discount went out on the same month, spread across {M.sales[y]["spread"]:.0f}% of transactions.']
    ch = dict(id='cancels', n=6, title='Late Cancellations and Discounts', body=body, kpis=kpis, facts=facts,
              subtitle=f'{float(F["lc"]):,.0f} seats released late, {lc.get("rate", 0):.1f}% of the book')
    ch['recs_extra'] = recs_cancels(M, X)
    return ch


def recs_cancels(M, X):
    y = M.y
    F = M.room.get(y, {}); lc = M.lc_year.get(y, {})
    out = []
    try:
        hr = M.lc_hour.sort_values(ascending=False)
        out.append(('Send the reminder four hours out, not twenty-four', 'Front Desk + Systems',
                    f'Late releases peak at {int(hr.index[0]):02d}:00 with {int(hr.iloc[0])} seats in {M.label}. The '
                    f'decision to skip is made on the day, not the day before.',
                    'A reminder placed inside the decision window is the only nudge that can still change the outcome, and a waitlist text sent at the same moment converts the release into an attendance.'))
    except Exception:
        pass
    try:
        if hasattr(M, 'lc_conc') and M.lc_conc.get('three_plus'):
            out.append(('Talk to the members who cancel repeatedly, one at a time', 'Studio Manager',
                        f'{M.lc_conc["three_plus"]} members cancelled three or more times this month and the ten most '
                        f'frequent produced {M.lc_conc["top10_share"]:.0f}% of all late releases.',
                        'A short call costs nothing, and for a member cancelling around a scheduling conflict it fixes the pattern in a way no rule about credits would.'))
    except Exception:
        pass
    try:
        out.append((f'Charge for the seat that cannot be resold, and refund the one that can', 'Founder + Finance',
                    f'{float(F.get("lc", 0)):,.0f} seats came back late at {lc.get("rate", 0):.1f}% of the book, and the '
                    f'release rate differs more by hour than by trainer.',
                    'A rule anchored to resale feasibility is fair enough that staff will enforce it, and it stops the studio taxing an 18:30 class to solve a 07:00 problem.'))
    except Exception:
        pass
    try:
        cd = X.sales.get('codes')
        if cd is not None and len(cd):
            out.append(('Cap the depth of the largest code and publish the ceiling', 'Marketing + Finance',
                        f'{clean(cd.index[0])} is {share(cd["given"].max(), cd["given"].sum())} of all discounting in '
                        f'{M.label} at a mean depth of {cd["depth"].max():.0f}%.',
                        'One code at one depth is auditable. Four codes at four depths is a negotiation at the desk, and the desk always loses the argument it has to have twice a week.'))
    except Exception:
        pass
    try:
        cb = getattr(M, 'cancel_bands', None)
        if cb is not None and len(cb) > 2:
            out.append(('Use the cancellation signal as an early warning, not a penalty', 'CRM + Studio Manager',
                        f'Members with more than half their bookings cancelled are live {cb.iloc[-1]["live"]:.0f}% of the '
                        f'time against {cb.iloc[0]["live"]:.0f}% for those who never cancel, on the whole membership ledger.',
                        'Reading a rising cancellation rate as an at-risk flag costs nothing and starts the retention conversation weeks before the lapse date.'))
    except Exception:
        pass
    return out


# ============================== 7. STUDIO OVERVIEW AND INTELLIGENCE
def overview(M):
    X = deep(M)
    ld = X.ld
    y, lab = M.y, M.label
    F = M.room.get(y, {}); P1 = M.room.get(y - 1, {}); P2 = M.room.get(y - 2, {})
    Sx = X.sales; Fx = M.sales.get(y, {}); Sp = M.sales.get(y - 1, {})
    mon = mono(M)
    parts = []

    def start():
        p = [para(f'{M.studio} ran {F.get("sessions", 0)} classes in {lab}, filled {F.get("fill", 0):.1f}% of them, took '
                  f'{F.get("att", 0):,.0f} attendances across those rooms and delivered {R(F.get("rev", 0))} of class revenue. '
                  f'The studio banked {R(Fx.get("cash", 0))} against that from {Fx.get("buyers", 0)} buyers.'),
             para('Those two sentences are the whole business: what the room did, and what the room was paid for. Every '
                  'other number in this review either leads them or lags them. This chapter puts them next to each other '
                  'with the four leading indicators the studio can act on before next month: leads, trials, bookings '
                  'against capacity, and visits per member.')]
        rows = []
        for name, cur, prv, kind in [
            ('Classes taught', F.get('sessions'), P1.get('sessions'), 'n'),
            ('Seats offered', F.get('seats'), P1.get('seats'), 'n'),
            ('Attendances', F.get('att'), P1.get('att'), 'n'),
            ('Utilisation %', F.get('fill'), P1.get('fill'), 'p'),
            ('Class revenue', F.get('rev'), P1.get('rev'), 'm'),
            ('Revenue per class', F.get('rpc'), P1.get('rpc'), 'm'),
            ('Late cancellations', F.get('lc'), P1.get('lc'), 'n'),
            ('Cash taken', Fx.get('cash'), Sp.get('cash'), 'm'),
            ('Buyers', Fx.get('buyers'), Sp.get('buyers'), 'n'),
            ('Average buyer', Fx.get('ticket'), Sp.get('ticket'), 'm')]:
            if cur is None:
                continue
            if y in M.people:
                pass
            d = ((cur - prv) / prv * 100) if prv else None
            f = (lambda v: _n(v)) if kind == 'n' else (lambda v: f'{v:.1f}%') if kind == 'p' else (lambda v: R(v))
            rows.append([name, f(cur), f(prv) if prv is not None else '·', f'{d:+.1f}%' if d is not None else '·'])
        if y - 2 in M.room and P2:
            rows.append(['Classes taught, two years ago', _n(P2.get('sessions')), '',
                         f'{(F.get("sessions", 0) - P2.get("sessions", 0)) / max(P2.get("sessions", 1), 1) * 100:+.1f}%'])
        b = [T(['Measure', f'{mon} {y}', f'{mon} {y - 1}', 'Movement'], rows, 'num')]
        if len(M.room) > 1:
            yrs = sorted(M.room)
            b.insert(0, bars([f'{mon[:3]} {z}' for z in yrs],
                             [('Attendances', [float(M.room[z]['att']) for z in yrs], A1),
                              ('Utilisation %', [float(M.room[z]['fill']) for z in yrs], B1),
                              ('Class revenue, lakh', [float(M.room[z]['rev']) / 100000 for z in yrs], A2)],
                             f'The same month across the years on file', h=310,
                             note='Revenue drawn in lakh rupees and utilisation in per cent so all three series share one axis; read the shape, not the height.'))
        return head('Start here', 'One page, four numbers, and the year beside them', None) + ''.join(p + b)

    def base():
        if y not in M.people:
            return ''
        pn = M.people[y]
        p = [para(f'<strong>{pn["members"]}</strong> different people trained at this studio in {mon.lower()} {y}, making '
                  f'{pn["visits"]:,} visits at {pn["per"]:.2f} each' +
                  (f', against {M.people[y - 1]["members"]} people making {M.people[y - 1]["visits"]:,} visits at '
                   f'{M.people[y - 1]["per"]:.2f} each in {yrp(M)}' if (y - 1) in M.people else '') + '.'),
             para('Breadth and frequency have to be read together and are almost never reported together. A studio can add '
                  'three hundred members in a year and lose the same number of attendances; on the till it looks like '
                  'growth and in the room it feels like quiet.')]
        b = []
        mo = X.bh.get('monthly')
        if mo is not None and len(mo) > 5:
            b.append(lines([str(i) for i in mo.index], [('Members', [float(v) for v in mo['members']], B1),
                                                          ('Visits per member', [float(v) * 100 for v in mo['per']], A1)],
                           'The base, and how often it comes', h=320,
                           note='Visits per member drawn at one hundred times its true height so both series share one axis. Monthly figures from the check-in ledger.'))
            b.append(frame_ev('Evidence &mdash; the ledger month by month', mo.reset_index(),
                              ['Month', 'Visits', 'Members', 'Visits per member'], ['w', 'n', 'n', 'f2'], maxrows=48))
        return sec('The member base', 'How many people, and how often', p, b)

    def core():
        c = getattr(M, 'core', {})
        if not c or not c.get('n'):
            return ''
        p = [para(f'The same-people comparison: {c["n"]} members trained here in both {yrp(M)} and {lab}. They came '
                  f'{c["prev"] / c["n"]:.2f} times each last year and {c["now"] / c["n"]:.2f} this year, which is '
                  f'{abs(c["lost"]):,.0f} visits the studio lost from the people who like it most. '
                  f'{c["new"]} people arrived who were not here last year and {c["gone"]} went.'),
             para(f'On the month’s numbers those {abs(c["lost"]):,.0f} missing visits are worth about '
                  f'{R(abs(c["lost"]) * F.get("rph", 0))} of delivered class revenue &mdash; '
                  f'{share(abs(c["lost"]) * F.get("rph", 0), F.get("rev", 0))} of everything the studio earned on the floor. '
                  f'Frequency, not acquisition, is where this month was decided.')]
        b = [T(['Group', 'People', f'{mon} {y - 1} visits', f'{mon} {y} visits', 'Change per person'],
               [['Here in both months', c['n'], _n(c['prev']), _n(c['now']), _f(c['now'] / c['n'] - c['prev'] / c['n'], 2)],
                ['Only last year (left)', c['gone'], _n(float(M.people[y - 1]['v'].reindex(
                    [i for i in M.people[y - 1]['v'].index if i not in set(M.people[y]['v'].index)]).sum())), '0', '-'],
                ['Only this year (new)', c['new'], '0', _n(float(M.people[y]['v'].reindex(
                    [i for i in M.people[y]['v'].index if i not in set(M.people[y - 1]['v'].index)]).sum())), '+']], 'num')]
        return sec('The returning core', 'The same people, a year apart', p, b)

    def memberships():
        if 'lapsed' not in M.has:
            return ''
        st = getattr(M, 'status_mix', pd.Series(dtype=float))
        p = [para(f'The membership ledger holds {M.led["rows"]:,} rows for this studio, {M.led["paid"]:,} of them paid, '
                  f'{M.led["members"]:,} distinct people and {R(M.led["cash"])} of recorded money. By status the book is '
                  + ' · '.join(f'{clean(i)} {_n(v)}' for i, v in st.head(6).items()) + '.'),
             para(f'A median paid membership here lasts {getattr(M, "median_life", 0):.0f} days, and '
                  f'{M.unused_low:,} of the {M.unused_n:,} memberships with usage data used a quarter or less of what they '
                  f'bought. Read together, those two numbers say the studio sells short products that are not fully used, '
                  f'which is a different problem from the one the sales report appears to describe.')]
        b = []
        if hasattr(M, 'dur') and len(M.dur):
            b.append(tab(M.dur, ['Length of membership', 'Sold', 'Average paid', 'Classes completed'], ['w', 'n', 'm', 'f1'], 'num'))
            b.append(hbars([(_n(r['n']), float(r['n']), A1 if i == len(M.dur) - 1 else A2) for i, (_, r) in enumerate(M.dur.iterrows())],
                           'What length of membership people buy', unit='',
                           note='Bands of the duration recorded on the membership row, across the whole ledger for this studio.'))
        return sec('What the memberships look like', 'The book the studio is running', p, b)

    def engine():
        if 'leads' not in M.has:
            return ''
        lf = M.lead_fun
        ldm = X.ld
        mth = ldm.get('month', {}) or {}
        p = [para(f'{M.lead_n:,} leads are on file for this studio: {lf["trial"]:,} completed a trial and {lf["won"]:,} became '
                  f'customers, {lf["won_pct"]:.1f}% of the whole. In {lab} alone {mth["n"]} leads arrived, '
                  f'{mth["trial"]} trialled and {mth["won"]} bought' +
                  (f', against {mth["prev_n"]} leads and {mth["prev_won"]} purchases in {yrp(M)}'
                   if mth.get('prev_n') else '') + '.'),
             para(f'Volume is not the constraint. {M.open_n:,} leads are still open with a mean age of '
                  f'{M.open_age:.0f} days. The studio has more unsold demand on file than it can serve in a year, and the '
                  f'chapter on leads shows the conversion is decided by whether a trial happens, and how soon.')]
        b = [funnel([('Leads on file', lf['leads'], f'{M.lead_n:,} total'),
                     ('Completed a trial', lf['trial'], f'{lf["trial_pct"]:.1f}% of leads'),
                     ('Became a customer', lf['won'], f'{lf["won_pct"]:.1f}% of leads'),
                     ('Still with the studio', lf['retained'], f'{lf["retained_pct"]:.1f}% of leads')],
                    'The acquisition engine, end to end', note='Every lead the studio has ever recorded here, not the month.')]
        if hasattr(M, 'lead_src') and len(M.lead_src):
            b.append(tab(M.lead_src.reset_index(), ['Source', 'Leads', 'Trialled %', 'Won %', 'Mean LTV'],
                         ['w', 'n', 'p', 'p', 'm'], maxrows=10))
        return sec('The acquisition engine', 'Leads, trials and what they become', p, b)

    def money():
        if 'sales' not in M.has:
            return ''
        c = M.cats if hasattr(M, 'cats') else None
        p = [para(f'{R(Fx["cash"])} came in across {Fx["lines"]} transactions from {Fx["buyers"]} people at '
                  f'{R(Fx["ticket"])} each' + (f', against {R(Sp["cash"])} and {Sp["buyers"]} buyers in {yrp(M)}' if Sp else '')
                  + (f'. The average buyer is worth {((Fx["ticket"] - Sp["ticket"]) / Sp["ticket"] * 100):+.1f}% than a year ago.'
                     if Sp.get('ticket') else '.'))]
        if c is not None and len(c):
            p.append(para('Where it came from: ' + rank_list(c, 'sum', 5) + '.'))
        b = []
        if c is not None and len(c):
            b.append(hbars([(clean(i), float(v), A1 if n == 0 else A2) for n, (i, v) in enumerate(c['sum'].items())],
                           f'Cash by category, {lab}', unit='₹'))
            b.append(tab(c.reset_index(), ['Category', 'Lines', 'Cash'], ['w', 'n', 'm']))
        return sec('Where the money comes from', 'Cash, buyers and the shape of the till', p, b)

    def room():
        if not F:
            return ''
        hh = X.cls.get('hour')
        p = [para(f'The room ran {F["sessions"]} classes, offered {F["seats"]:,.0f} seats and filled {F["fill"]:.1f}% of them. '
                  f'{F["book"] - F["att"]:,.0f} booked seats went empty, of which {F["lc"]:,.0f} were late cancellations. '
                  f'Revenue per class was {R(F["rpc"])} and per attendance {R(F["rph"])}.'),
             para(f'By hour the studio is a different business each time it opens: '
                  + ' · '.join(f'{int(i):02d}:00 {hh.loc[i, "fill"]:.0f}%' for i in hh.sort_values('fill', ascending=False).head(3).index)
                  + ' at the top and '
                  + ' · '.join(f'{int(i):02d}:00 {hh.loc[i, "fill"]:.0f}%' for i in hh.sort_values('fill').head(2).index)
                  + ' at the bottom. Utilisation problems are usually hour problems wearing a marketing costume.')]
        b = []
        if X.bm.get('table') is not None and len(X.bm['table']) > 1:
            bt = X.bm['table']
            b.append(T(['Studio', 'Classes', 'Attendances', 'Utilisation', 'Revenue', 'Per class', 'Late-cancel rate'],
                       [[clean(i), _n(r['classes']), _n(r['att']), f'{r["fill"]:.1f}%', R(r['rev']), R(r['rpc']),
                         f'{r["lc_pct"]:.1f}%'] for i, r in bt.iterrows()], 'num'))
            b.append(para(f'Against the other studios on this file in the same month, {M.studio} ranks '
                          f'{X.bm["rank_fill"]} of {X.bm["n"]} on utilisation. The comparison is not a league for merit: '
                          f'rooms, rent, age and market differ. It is a check on whether a number is a studio problem or an '
                          f'industry one, and it is the comparison the studio cannot see from inside its own exports.'))
        return sec('The room', 'Capacity, and what was made of it', p, b)

    def pipeline():
        lp = X.lp
        p, b = [], []
        if lp.get('paid') is not None and len(lp.get('paid', [])):
            pay = lp['paid']
            try:
                due = pay[pay['End Date_x'].between(pd.Timestamp.today().normalize(), pd.Timestamp.today().normalize() + pd.Timedelta(days=30))]
                p.append(para(f'<strong>The book that is already sold.</strong> {len(due):,} paid memberships end in the next '
                              f'thirty days, carrying {R(float(due["Amount Paid"].sum()))} of original value. That is the '
                              f'revenue the studio will either keep or replace in a month, and it is knowable today at a '
                              f'name-and-date level, not as a forecast.'))
                if len(due) and 'Sessions Used %' in due:
                    u = float(due['Sessions Used %'].fillna(0).mean())
                    if u > 0:
                        p.append(para(f'Those ending memberships have used {u:.0f}% of what they bought on average. Members '
                                      f'who have used nearly everything are renewals in waiting; members who have used a '
                                      f'little are a conversation the studio has not yet had, and which becomes a refund '
                                      f'conversation if it waits for the expiry date.'))
            except Exception:
                pass
        if hasattr(M, 'unused_left'):
            p.append(para(f'Beyond the renewals, {M.unused_left:,.0f} classes sit unspent on memberships the studio has '
                          f'already been paid for, and {M.unused_low:,} members have used a quarter or less of what they '
                          f'bought. That is the single largest block of recoverable attendance in this review.'))
            b.append(statgrid([('Classes owed', f'{M.unused_left:,.0f}'),
                               ('Members under-using', f'{M.unused_low:,}'),
                               ('Renewals due in 30 days', f'{len(due):,}' if 'due' in dir() else '-'),
                               ('Warm members, 60 days', f'{lp.get("warm", 0):,}')]))
        w = lp.get('winnable')
        if w is not None and len(w):
            b.append(tab(w.reset_index(), ['Last seen', 'People', 'Cash still held', 'Classes still owed'],
                         ['w', 'n', 'm', 'n']))
        if not p:
            return ''
        return sec('The book that is already sold', 'Renewals, unspent classes and who to call', p, b)

    def hands():
        a = ld.get('assoc')
        st = getattr(M, 'lead_status', None)
        if (a is None or not len(a)) and (st is None or not len(st)):
            return ''
        p = []
        if a is not None and len(a):
            p.append(para(f'{len(a)} associates between an enquiry and a decision, converting between '
                          f'{a["rate"].min():.1f}% and {a["rate"].max():.1f}% on books of {int(a["leads"].min())} to '
                          f'{int(a["leads"].max())} leads. The chapter on leads holds the argument about what that means; '
                          f'the point here is that the spread is real, it is measurable, and it is not visible in any '
                          f'number the studio currently reports to itself.'))
        if st is not None and len(st):
            p.append(para('Where the file as a whole sits: ' + ' · '.join(f'{clean(i)} {_n(v)}' for i, v in st.head(7).items()) + '.'))
        b = []
        if a is not None and len(a):
            b.append(tab(a.reset_index(), ['Associate', 'Leads', 'Won', 'Conversion %', 'Trialled %', 'Mean LTV', 'Still open'],
                         ['w', 'n', 'n', 'p', 'p', 'm', 'n']))
        return sec('Who handles the leads', 'The people between demand and revenue', p, b)

    def glance():
        yrs = sorted(M.room)
        if len(yrs) < 2:
            return ''
        rows = []
        def cell(z, key, src, f):
            try:
                return f(src[z][key])
            except Exception:
                return '·'
        for name, src, key, f in [
            ('Classes taught', M.room, 'sessions', _n), ('Attendances', M.room, 'att', _n),
            ('Utilisation %', M.room, 'fill', lambda v: f'{v:.1f}'), ('Class revenue', M.room, 'rev', R),
            ('Revenue per class', M.room, 'rpc', R), ('Late cancellations', M.room, 'lc', _n),
            ('Cash taken', M.sales, 'cash', R), ('Buyers', M.sales, 'buyers', _n),
            ('Average buyer', M.sales, 'ticket', R),
            ('Members who trained', M.people, 'members', _n), ('Visits per member', M.people, 'per', lambda v: f'{v:.2f}')]:
            rows.append([name] + [cell(z, key, src, f) for z in yrs])
        p = [para('One table, three Septembers, every number the studio reports on. It is placed here deliberately: the '
                  'chapters argue, this page only states. Where a cell is empty the source for that year was not in the '
                  'upload, and the studio should read that as a gap in its records rather than as zero.'),
             para(f'Read down the columns before reading across them. The measures that moved most between {int(yrs[0])} and '
                  f'{int(yrs[-1])} are the ones the studio should be managing; the ones that barely moved are the ones it '
                  f'should stop discussing.')]
        b = [T([f'{mon} {z}' for z in yrs], rows, 'num'),
             T(['Measure'] + [f'{mon} {z}' for z in yrs], [[r[0]] + r[1:] for r in rows], 'num') if False else '']
        return sec('The year in numbers', 'The same month, every year the files cover', p, [x for x in b if x])

    def rank_month():
        mo = X.bh.get('monthly')
        if mo is None or len(mo) < 6:
            return ''
        try:
            a, b = rng(y, M.m)
            d = M.D.sessions
            sd = d[d['_loc'] == M.studio].copy()
            sd['p'] = sd['_dt'].dt.to_period('M')
            g = sd.groupby('p').agg(classes=('SessionID', 'size'), seats=('_cap', 'sum'), att=('CheckedIn', 'sum'),
                                    rev=('Revenue', 'sum'), lc=('LateCancelled', 'sum'))
            g['fill'] = g['att'] / g['seats'] * 100
            g = g[g['classes'] >= 8].sort_index()
        except Exception:
            return ''
        if len(g) < 8:
            return ''
        last = g.iloc[-1]
        pr = g[g.index <= pd.Period(f'{y}-{M.m:02d}')] if False else g[g.index <= pd.Period(str(y) + '-' + str(M.m).zfill(2))]
        rk = int((pr['att'] > last['att']).sum()) + 1
        rkf = int((pr['fill'] > last['fill']).sum()) + 1
        p = [para(f'Across the {len(pr)} months of classes on file up to and including {lab}, this month ranks '
                  f'<strong>{rk}th on attendance</strong> and <strong>{rkf}th on utilisation</strong>. The best month in the '
                  f'series taught {int(pr["classes"].max())} classes and filled {pr["fill"].max():.1f}%; the weakest '
                  f'{int(pr["classes"].min())} classes at {pr["fill"].min():.1f}%.'),
             para(f'That is the sentence the studio should carry out of this review: {mon.lower()} {y} is not a good month '
                  f'or a bad month in isolation, it is a position in a series, and the series is long enough now that a '
                  f'forecast can be argued with rather than guessed at.')]
        rows = [[str(i), _n(r['classes']), _n(r['att']), f'{r["fill"]:.1f}%', R(r['rev']), _n(r['lc'])] for i, r in pr.tail(24).iterrows()]
        b = [T(['Month', 'Classes', 'Attendances', 'Utilisation', 'Class revenue', 'Late cancelled'], rows, 'num'),
             lines([str(i) for i in pr.index], [('Attendances', [float(x) for x in pr['att']], A1),
                                                 ('Utilisation %', [float(x) * 20 for x in pr['fill']], B1)],
                   'The month in the series', h=320,
                   note='Utilisation drawn at twenty times its true value so both series share one axis. Months with fewer than eight classes on file are excluded.')]
        return sec('Where this month sits in the year', 'A position in a series, not a verdict', p, b)

    def verdict():
        cards = []
        try:
            if y in M.people and (y - 1) in M.people:
                pn, pp = M.people[y], M.people[y - 1]
                cards.append(('yes' if pn['per'] < pp['per'] else 'no',
                              f'Frequency, not demand', f'{pn["per"]:.2f} visits per member against {pp["per"]:.2f} a year '
                              f'ago, on a base of {pn["members"]} people against {pp["members"]}. The studio reached more '
                              f'people and held them less.', 'The one number to manage next month.'))
        except Exception:
            pass
        cards += [('part', 'Cash held, commitment shrank',
                   f'{R(Fx.get("cash", 0))} in the month' + (f' against {R(Sp["cash"])} in {yrp(M)}' if Sp else '')
                   + '; the average buyer and the average transaction have not collapsed, but the membership book does not lengthen.',
                   'Read the sales and membership chapters together; neither one shows it alone.'),
                  ('yes', 'The open file is the cheapest growth',
                   f'{M.open_n:,} leads are open at a mean age of {M.open_age:.0f} days' if hasattr(M, 'open_n') else '',
                   'No acquisition spend required.'),
                  ('no', 'The month was a weather or festival effect',
                   f'The weekly and daily tables show the shape of the month, and the same-week patterns appear in both years '
                   f'on file. No single week carries the whole decline.',
                   'Checked and not supported at this level of the data.')]
        p = [para('Four statements the numbers in this review support, and one the studio will reach for and should not. '
                  'Each is a claim about cause, not only about movement, and each is falsifiable next month.')]
        b = [statgrid([('Attendances', _n(F.get('att'))), ('Cash', R(Fx.get('cash', 0))),
                       ('Members', _n(M.people.get(y, {}).get('members', 0))),
                       ('Open leads', _n(getattr(M, 'open_n', 0)))])]
        return sec('What the data is telling the studio', 'The four sentences that matter', p, b + [hyp([c for c in cards if c[2]])])

    body = run([start, glance, base, core, memberships, engine, hands, money, room, rank_month, pipeline, verdict])
    defs = [('Everything in this chapter', 'is the same figure computed the same way as in the chapter that owns it. Where two chapters disagree the underlying chapter is right and this one is rounding.'),
            ('Delivered class revenue', 'the sessions ledger’s Revenue column: what the studio earned by teaching, not by selling.'),
            ('Cash', 'the sales ledger’s payment value on the payment date.'),
            ('Visits per member', 'attended check-ins in the month divided by distinct members who attended.'),
            ('Benchmark', 'the same measure for every other studio label in the same upload, for the same month, where at least 20 classes were taught.')]
    caut = [('This is a review of one studio read from its own exports. It has no market data, no competitor pricing and no cost base beyond the payroll file, so it can say what happened and what it is worth, but not whether the studio is winning.'),
            ('Figures for the current month are provisional until the month’s day-end files are complete; the last day of a month is often the one that moves a total.'),
            ('Cross-studio comparisons are indicative only. Rooms, capacity, price lists and how long the studio has been open all differ.'),
            (f'{mon} is compared with the same calendar month in prior years. Where the festival week or the number of trading days shifts, part of the movement is the calendar and the weekly tables are shown so it can be seen.')]
    body += appendix(M, X, 'overview')
    body += method(M, defs, caut)
    kpis = [kpi('Classes', _n(F.get('sessions')), f'{_n(F.get("att"))} attendances'),
            kpi('Utilisation', f'{F.get("fill", 0):.1f}%', f'{share(F.get("rev", 0), Fx.get("cash", 1))} of cash delivered' if Fx.get('cash') else ''),
            kpi('Cash', R(Fx.get('cash', 0)), f'{Fx.get("buyers", 0)} buyers'),
            kpi('Visits per member', f'{M.people.get(y, {}).get("per", 0):.2f}', f'{M.people.get(y, {}).get("members", 0)} members')]
    facts = [f'{F.get("sessions", 0)} classes, {F.get("fill", 0):.1f}% utilisation and {R(F.get("rev", 0))} of delivered revenue in {lab}, against {R(Fx.get("cash", 0))} of cash taken.',
             f'{M.people.get(y, {}).get("members", 0)} people trained here at {M.people.get(y, {}).get("per", 0):.2f} visits each.']
    if hasattr(M, 'core') and M.core.get('n'):
        facts.append(f'{M.core["n"]} members came in both {yrp(M)} and {lab}; they came {abs(M.core["lost"]):,.0f} fewer times this year, worth about {R(abs(M.core["lost"]) * F.get("rph", 0))} of delivered revenue.')
    if hasattr(M, 'open_n'):
        facts.append(f'{M.open_n:,} leads sit open with a mean age of {M.open_age:.0f} days - unsold demand larger than the studio can serve in a year.')
    ch = dict(id='overview', n=7, title='Studio Overview and Intelligence', body=body, kpis=kpis, facts=facts,
              subtitle=f'{_n(F.get("sessions"))} classes at {F.get("fill", 0):.1f}%, {R(Fx.get("cash", 0))} banked')
    ch['recs_extra'] = recs_overview(M, X)
    return ch


def recs_overview(M, X):
    y = M.y
    F = M.room.get(y, {}); P1 = M.room.get(y - 1, {})
    out = []
    try:
        if y in M.people and (y - 1) in M.people and M.people[y]['per'] < M.people[y - 1]['per']:
            gap = M.people[y - 1]['per'] - M.people[y]['per']
            out.append(('Manage frequency, not headcount', 'Founder + Studio Manager',
                        f'Visits per member fell to {M.people[y]["per"]:.2f} from {M.people[y - 1]["per"]:.2f} while the '
                        f'base moved to {M.people[y]["members"]} from {M.people[y - 1]["members"]}. The studio is serving '
                        f'{abs(gap * M.people[y]["members"]):,.0f} fewer visits than the same base produced a year ago.',
                        f'One extra visit a month for a tenth of the base is worth roughly {R(gap * 0.1 * M.people[y]["members"] * F.get("rph", 0))} of delivered revenue and moves renewal rates before it moves cash.'))
    except Exception:
        pass
    try:
        if hasattr(M, 'open_n') and M.open_n > 100:
            out.append(('Put a target on the open file and a date on every entry', 'Sales + Founder',
                        f'{M.open_n:,} leads are open, {M.open_fresh} of them arrived in the last thirty days and '
                        f'{M.open_stale:,} are more than six months old.',
                        'The fresh block converts at a real rate and costs one conversation; the stale block costs a decision to close it. Both are cheaper than new leads.'))
    except Exception:
        pass
    try:
        if X.bm.get('n', 0) > 1:
            tbl = X.bm['table']
            out.append((f'Use the other {X.bm["n"] - 1} studios as the control group', 'Founder',
                        f'This studio ranks {X.bm["rank_fill"]} of {X.bm["n"]} on utilisation in {M.label} '
                        f'({F.get("fill", 0):.1f}% against a group median of {tbl["fill"].median():.1f}%).',
                        'Any month where the studio moves with the group is a market month; any month where it moves alone is a decision. That distinction saves the studio from reacting to weather.'))
    except Exception:
        pass
    out.append(('Publish these four numbers on one page, monthly', 'Studio Manager',
                f'Leads, trials, bookings against capacity and visits per member all move before the figures the studio '
                f'currently watches. In {M.label} they read {_n(getattr(M, "lead_month", 0))} new leads, '
                f'{_n(F.get("book"))} booked seats and {M.people.get(y, {}).get("per", 0):.2f} visits per member.',
                'A leading indicator nobody publishes is a leading indicator nobody changes.'))
    return out


# ==================================== 8. LEAD PERFORMANCE AND INSIGHTS
def leads(M):
    if 'leads' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    ld = X.ld
    ldm = ld
    mth = ldm.get('month', {}) or {}
    lf = M.lead_fun
    d = ld.get('d')
    mon = mono(M)
    if d is None or not len(d):
        return None

    def start():
        p = [para(f'{M.lead_n:,} leads are recorded against {M.studio}. {lf["trial"]:,} completed a trial, {lf["won"]:,} '
                  f'became customers ({lf["won_pct"]:.1f}%) and {lf["retained"]:,} are still with the studio '
                  f'({ld.get("retain_pct", 0):.0f}% of those who bought). In {lab} alone {mth["n"]} leads arrived, '
                  f'{mth["trial"]} trialled and {mth["won"]} bought.'),
             para(f'This is an acquisition file, not a marketing file: it says what the studio did with the demand it '
                  f'already had. {share(lf["won"], lf["leads"])} of everything the studio was asked for became a member, and '
                  f'the decision inside that number is almost entirely made by whether a trial happened and how quickly.'),
             (f'A year ago in the same month the studio took {mth["prev_n"]} enquiries and won {mth["prev_won"]}. '
              f'Enquiries {((mth["n"] - mth["prev_n"]) / max(mth["prev_n"], 1) * 100):+.0f}%, wins '
              f'{((mth["won"] - mth["prev_won"]) / max(mth["prev_won"], 1) * 100):+.0f}%. '
              if mth.get('prev_n') else '')]
        _g = ld.get('gate')
        _hi = float(_g['rate'].max()) if _g is not None and len(_g) else 0.0
        _lo = float(_g['rate'].min()) if _g is not None and len(_g) else 0.0
        _hl = clean(_g['rate'].idxmax()) if _g is not None and len(_g) else 'a trial'
        _ll = clean(_g['rate'].idxmin()) if _g is not None and len(_g) else 'no trial'
        claim = (f'Leads in the {_hl} group convert at {_hi:.1f}% against {_lo:.1f}% for {_ll} &mdash; a '
                 f'{ratio(_hi, _lo)}-fold difference. Nothing else in this chapter, not the source, not the associate, '
                 f'not the price, moves conversion as far.')
        b = [funnel([('Enquiries on file', lf['leads'], f'{M.lead_n:,} leads'),
                     ('Completed a trial', lf['trial'], f'{lf["trial_pct"]:.1f}%'),
                     ('Became a customer', lf['won'], f'{lf["won_pct"]:.1f}%'),
                     ('Still with the studio', lf['retained'], f'{lf["retained_pct"]:.1f}% of all leads')],
                    'The whole file, end to end', note='Every lead recorded for this studio across all years on file, not the month. A lead who is still open has not failed; they have not been decided.'),
              statgrid([('Leads', f'{M.lead_n:,}'), ('Trialled', f'{lf["trial_pct"]:.1f}%'),
                        ('Won', f'{lf["won_pct"]:.1f}%'), ('Retained', f'{lf["retained_pct"]:.1f}%')])]
        return head('Start here', 'What the studio does with the demand it already has', claim) + ''.join(p + b)

    def gate():
        g = ld.get('gate')
        if g is None or not len(g):
            return ''
        p = [para('Trial is the gate: ' + ' · '.join(
            f'{clean(i)} converts at {r["rate"]:.1f}% ({_n(r["leads"])} leads, mean LTV {R(r["ltv"])})'
            for i, r in g.iterrows()) + '.')]
        p.append(para(f'That is a {ratio(g["rate"].max(), g["rate"].min())}-fold difference, and it is the most actionable '
                      f'number in this review because it is entirely within the studio’s control: the trial is a diary '
                      f'entry, not a price. Where the file says a lead did not trial, the reason recorded here is a '
                      f'scheduling failure far more often than a change of mind.'))
        b = [tab(g.reset_index(), ['Trial status', 'Leads', 'Won', 'Conversion %', 'Mean LTV', 'Mean visits'],
                 ['w', 'n', 'n', 'p', 'm', 'f1']),
             hbars([(clean(i), float(v), A1) for i, v in g['rate'].items()], 'Conversion by trial status', unit='%',
                   note=f'Whole file, {M.lead_n:,} leads. A lead who booked a trial and did not attend is counted here as not trialling.')]
        return sec('The trial is the gate', 'The one decision that decides the rest', p, b)

    def speed():
        sp = ld.get('speed')
        if sp is None or not len(sp):
            return ''
        p = [para(f'{ld.get("same_day", 0):.1f}% of wins closed on the day of the enquiry and {ld.get("week", 0):.0f}% within '
                  f'a week. Beyond that the value of a lead decays: ' + ' · '.join(
            f'{clean(i)} {R(r["ltv"])}' for i, r in sp.head(5).iterrows()) + ' as lifetime value.'),
             para('The obvious reading is that fast conversion is a good sign. The reading worth more is the reverse: leads '
                  'who take longer are not worse prospects, they are prospects whose trial did not happen inside the week. '
                  'Speed measures the studio’s diary more accurately than it measures the member’s interest.')]
        b = [tab(sp.reset_index(), ['Decision took', 'Wins', 'Mean LTV', 'Mean visits', 'Mean purchases'],
                 ['w', 'n', 'm', 'f1', 'f1']),
             bars([clean(i) for i in sp.index], [('Wins', [float(v) for v in sp['won']], A1)],
                  'How long a lead takes to become a member', h=300, rotate=True,
                  note='Days between the enquiry date and the conversion date, for every lead that was won.')]
        rf = ld.get('resp')
        if rf is not None and len(rf):
            b.append(para(f'On the studio’s own follow-up dates, the first response to an enquiry came after a median of '
                          f'<strong>{rf.median():.0f} days</strong>, and {share(float((rf > 1).sum()), len(rf))} of leads '
                          f'waited more than a day for the first word. That delay is not in the lead’s hands.'))
        return sec('Speed decides it', 'The clock on the enquiry, and the clock on the reply', p, b)

    def follow():
        g = ld.get('follow')
        if g is None or not len(g) or len(g) < 2:
            return ''
        p = [para(f'The file records between zero and four follow-ups per lead. Conversion runs ' + ' → '.join(
            f'{int(i)} follow-ups {r["won"]:.1f}%' for i, r in g.iterrows()) +
            f', and mean lifetime value runs {R(g["ltv"].max())} down to {R(g["ltv"].min())}.')]
        p.append(para(f'This is where the studio must be careful with its own data, because the arrow points the wrong way '
                      f'from the obvious reading. More follow-ups does not create more wins; the associates chase the leads '
                      f'they believe in, and they stop writing about the ones they do not. What the table does prove is that '
                      f'the practice is uneven: {int(g["leads"].iloc[0]):,} leads were contacted at most once, and those are '
                      f'the leads the studio will never know whether it could have won.'))
        b = [tab(g.reset_index(), ['Follow-ups logged', 'Leads', 'Won %', 'Trialled %', 'Mean LTV', 'Mean visits'],
                 ['n', 'n', 'p', 'p', 'm', 'f1'])]
        if 'fu_after_win' in ld and pd.notna(ld['fu_after_win']):
            b.append(para(f'A further sign of the same thing: {ld["fu_after_win"]:.0f}% of leads had a follow-up logged after '
                          f'they had already been won. The file is being worked as a list, not as a pipeline.'))
        sp = ld.get('fu_span')
        if sp is not None and len(sp):
            b.append(para(f'Where follow-ups were made, they spanned a median of {sp.median():.0f} days &mdash; a fortnight '
                          f'of contact for a lead whose decision, when it comes, usually comes the same day. The studio is '
                          f'running two different clocks and has never reconciled them.'))
        return sec('The follow-up book', 'What the studio actually did with each name', p, b)

    def sources():
        s = getattr(M, 'lead_src', None)
        u = ld.get('utm')
        if s is None or not len(s):
            return ''
        best = s.loc[s['won'].idxmax()]
        big = s['leads'].idxmax()
        p = [para('Where the enquiries came from, and what happened to them: ' + rank_list(s, 'leads', 6) + '.'),
             para(f'{clean(s["won"].idxmax())} converts at {s["won"].max():.1f}% for a mean lifetime value of '
                  f'{R(best["ltv"])}; {clean(big)} delivers {s.loc[big, "leads"]:,.0f} leads at {s.loc[big, "won"]:.1f}%. '
                  f'The studio’s acquisition mix is therefore not a spend question but a schedule question: the best-'
                  f'converting source is the one whose leads can be put in front of a trial the same week.'),
             (f'The studio’s own campaign tags say something different again: ' + ' · '.join(
                 f'{clean(i)} {r["leads"]:,} leads at {r["won"]:.1f}%' for i, r in u.head(4).iterrows()) +
              '. Where the stated source and the campaign tag disagree, the file is recording who closed it, not how it '
              'arrived, and no channel decision made on this column should be trusted far.')]
        b = [tab(s.reset_index(), ['Source', 'Leads', 'Trialled %', 'Won %', 'Mean LTV'], ['w', 'n', 'p', 'p', 'm']),
             hbars([(clean(i), float(v), A1) for i, v in s['won'].head(12).items()],
                   f'Conversion rate by source', unit='%',
                   note=f'Sources with fewer than 20 leads are excluded. Rate, not volume, is the axis: the largest source is rarely the best one.'),
             hbars([(clean(i), float(v), B1) for i, v in s['ltv'].head(12).items()],
                   'Lifetime value of what each source delivers', unit='₹',
                   note='Mean LTV recorded against leads from that source, whoever converted them.')]
        if u is not None and len(u):
            b.append(tab(u.reset_index(), ['Campaign tag', 'Leads', 'Won %', 'Mean LTV'], ['w', 'n', 'p', 'm']))
        return sec('Where the leads come from', 'Source, channel and what each is worth', p, b)

    def asks():
        a = ld.get('ask')
        if a is None or not len(a):
            return ''
        p = [para(f'What people ask for predicts what they buy. ' + ' · '.join(
            f'{clean(i)} {_n(r["leads"])} enquiries converting {r["won"]:.1f}%' for i, r in a.head(6).iterrows()) + '.'),
             para('This is the table the studio should be matching its timetable against. A lead who asks about a specific '
                  'format and is offered a trial in a different one converts at the studio average at best; the enquiry '
                  'already contains the answer to the question of what to sell them, and it is not currently used beyond '
                  'the first call.')]
        b = [tab(a.reset_index(), ['Enquiry was about', 'Leads', 'Trialled %', 'Won %', 'Mean LTV'], ['w', 'n', 'p', 'p', 'm'])]
        ms = ld.get('month_src')
        if ms is not None and len(ms):
            b.append(frame_ev(f'Evidence &mdash; where {lab}’s {mth["n"]} enquiries came from', ms.reset_index(),
                              ['Source', 'Leads', 'Won %'], ['w', 'n', 'p'],
                              blurb='The month on its own, so the year-long mix above can be compared with what is happening now.'))
        return sec('What leads ask for', 'The enquiry as a prescription', p, b)

    def who():
        a = ld.get('assoc')
        if a is None or not len(a):
            return ''
        p = [para(f'{len(a)} associates carry the book. Conversion runs {a["rate"].min():.1f}% to {a["rate"].max():.1f}% '
                  f'on volumes between {int(a["leads"].min())} and {int(a["leads"].max())} leads each, and lifetime value '
                  f'from {R(a["ltv"].min())} to {R(a["ltv"].max())}.'),
             para(f'The highest-converting associate, {clean(a["rate"].idxmax())}, works {a.loc[a["rate"].idxmax(), "leads"]:,.0f} '
                  f'leads &mdash; not the smallest book, which is worth saying out loud, because the studio’s instinct is to '
                  f'give the best people more work until their rate falls to the average. The largest book, '
                  f'{clean(a["leads"].idxmax())} at {a.loc[a["leads"].idxmax(), "leads"]:,.0f} leads, converts at '
                  f'{a.loc[a["leads"].idxmax(), "rate"]:.1f}%.'),
             para(f'{_n(float(a["open"].sum()))} of the open leads sit with {clean(a["open"].idxmax())} alone. An '
                  'unworked file and a large file are different problems, and the table is the only place they can be '
                  'told apart.')]
        b = [tab(a.reset_index(), ['Associate', 'Leads worked', 'Won', 'Conversion %', 'Trialled %', 'Mean LTV', 'Still open'],
                 ['w', 'n', 'n', 'p', 'p', 'm', 'n']),
             bars([clean(i) for i in a.index], [('Won %', [float(v) for v in a['rate']], A1),
                                                 ('Leads worked, ÷100', [float(v) / 100 for v in a['leads']], B1)],
                  'Conversion against book size, by associate', h=320,
                  note='Book size drawn divided by one hundred so both series share an axis.')]
        return sec('Who handles the leads', 'The people between the enquiry and the decision', p, b)

    def openfile():
        ob = ld.get('open_bands')
        st = ld.get('open_stage')
        if (ob is None or not len(ob)) and st is None:
            return ''
        p = [para(f'{M.open_n:,} leads are open. By how long they have been waiting: ' + ' · '.join(
            f'{clean(i)} {_n(r["n"])}' for i, r in ob.iterrows()) + '.')]
        p.append(para(f'Only {M.open_fresh} arrived in the last thirty days; {M.open_stale:,} have been on the file more '
                      f'than six months. The first group is a pipeline and the second is a list. Keeping them in the same '
                      f'column is why nobody works either: a fresh lead needs speed and the stale one needs a decision, and '
                      f'the studio currently gives both of them a follow-up.'))
        b = []
        if ob is not None and len(ob):
            b.append(tab(ob.reset_index(), ['Age of the open lead', 'Leads', 'Mean LTV if won'], ['w', 'n', 'm']))
        if st is not None and len(st):
            b.append(hbars([(clean(i), float(v), A2) for i, v in st['n'].items()],
                           'Where the open leads are stuck', unit='',
                           note='Stage Name as the CRM holds it. A large pile at one stage is a process problem at that stage, not a lead-quality problem.'))
            b.append(frame_ev('Evidence &mdash; open leads by stage, with median age', ld.get('open_stage'),
                              ['Stage', 'Leads', 'Median age (days)', 'Mean LTV'], ['w', 'n', 'n', 'm']))
            b.append(para(f'The median age of a lead sitting at {clean(st["med_age"].idxmax())} is '
                          f'{st["med_age"].max():,.0f} days. If the studio cannot answer that lead in a week, the honest '
                          f'action is to close it and record why, because an open lead that will never be worked still '
                          f'costs the studio a forecast it can no longer trust.'))
        return sec('The file the studio is not working', 'Age, stage and what to do with each', p, b)

    def flow():
        fl = ld.get('flow')
        if fl is None or not len(fl) or len(fl) < 4:
            return ''
        p = [para(f'Enquiry volume through the {len(fl)} months on file runs from {int(fl["leads"].min())} to '
                  f'{int(fl["leads"].max())} a month, with conversion between {fl["rate"].min():.1f}% and '
                  f'{fl["rate"].max():.1f}%. The two are only loosely related, which is the studio’s licence to stop '
                  f'blaming the market for a bad conversion month.'),
             para('Read the last three months against the same months last year before acting on the shape. Lead flow at '
                  'this studio is seasonal and the file is long enough to show it: the peak enquiry months are not the peak '
                  'winning months.')]
        b = [lines([str(i) for i in fl.index], [('Leads', [float(v) for v in fl['leads']], A1),
                                                 ('Won', [float(v) for v in fl['won']], B1),
                                                 ('Conversion %', [float(v) * 10 for v in fl['rate']], A2)],
                   'Leads, wins and conversion by month', h=330,
                   note='Conversion is drawn at ten times its true value so it shares the axis with the counts.'),
             frame_ev('Evidence &mdash; month by month', fl.reset_index(), ['Month', 'Leads', 'Won', 'Conversion %', 'Trialled %'],
                      ['w', 'n', 'n', 'p', 'p'], maxrows=40)]
        return sec(f'Lead flow through {y}', 'Volume, and the seasonality underneath it', p, b)

    def causes():
        items = [('yes', 'The trial never got booked',
                  f'{share(lf["leads"] - lf["trial"], lf["leads"])} of leads on file never completed a trial, and trial-takers '
                  f'convert at {M.lead_fun["won_pct"] / max(1 - M.lead_fun["trial_pct"] / 100, .01):.0f} times the rate of '
                  f'those who did not.', 'The single largest lever in this chapter, and it needs no price change.'),
                 ('part', 'Cheap channels dilute the pool',
                  'The largest sources are not the best-converting ones, so a month where mix shifts toward volume looks like '
                  'a conversion collapse.', 'Hold the source constant before comparing two months.'),
                 ('no', 'Associates differ in skill alone',
                  f'Book size, hour coverage and the sources each associate is handed all differ. Conversion spread of '
                  f'{ratio(ld["assoc"]["rate"].max(), ld["assoc"]["rate"].min())} times is not a training verdict on its own.',
                  'Assign leads at random for a month and the table becomes usable.'),
                 ('part', 'The CRM reflects the process, not the reality',
                  f'{ld.get("fu_after_win", 0):.0f}% of leads have a follow-up logged after they were already won, and '
                  f'{M.open_stale:,} open leads are more than six months old. The file is worked as a list.',
                  'Treat it as evidence of behaviour, never as a complete record of what happened.')]
        return sec('What else could explain it', 'Cause, in a file that is really a diary', [para('A lead file records what the studio did, not what happened. Every conclusion here has to survive that sentence.')], [hyp(items)])

    body = run([start, gate, speed, follow, sources, asks, who, openfile, flow, causes])
    defs = [('Lead', 'one row of the CRM export for this centre. A person who enquired twice appears twice unless the system merged them.'),
            ('Won', 'Status = Won in the CRM. It is the studio’s own judgement, recorded at the moment the deal closed.'),
            ('Trialled', 'Trial Status = Trial Completed, as recorded on the lead. A trial that happened but was not marked is missing here.'),
            ('LTV', 'the lifetime value column the CRM carries on the lead, used as recorded and not recomputed from the sales ledger.'),
            ('Conversion %', 'wins divided by leads in that group, on the whole file rather than the month, because a monthly cut of these groups is too thin to read.')]
    caut = [('There is no spend figure in this file, so nothing here can say whether a channel was worth its cost. It says only what a channel delivered.'),
            ('A lead marked open for years is not a lead still being pursued; the CRM has no close-out date, so ageing is measured from the enquiry.'),
            ('Follow-up timestamps are whatever the associate entered, which is usually the day after. Cadence found here is a floor, not a measurement.'),
            ('LTV is attributed to whoever owned the lead, so a member who later buys through a different channel keeps their original attribution.')]
    body += appendix(M, X, 'leads')
    body += method(M, defs, caut)
    kpis = [kpi('Leads on file', f'{M.lead_n:,}', f'{mth["n"]} in {lab}'),
            kpi('Trialled', f'{lf["trial_pct"]:.1f}%', f'{lf["trial"]:,} people'),
            kpi('Won', f'{lf["won_pct"]:.1f}%', f'{lf["won"]:,} memberships'),
            kpi('Open file', f'{getattr(M, "open_n", 0):,}', f'mean age {getattr(M, "open_age", 0):.0f} days', 'neg')]
    facts = [f'{M.lead_n:,} leads on file for this studio: {lf["trial"]:,} trialled, {lf["won"]:,} won, {lf["retained"]:,} retained.',
             f'Trials convert at {float(ld["gate"]["rate"].max()) if ld.get("gate") is not None and len(ld["gate"]) else 0:.1f}% against those without one.',
             f'{ld.get("same_day", 0):.0f}% of wins closed on the day of the enquiry; {M.open_n:,} leads sit open with a mean age of {M.open_age:.0f} days.']
    ch = dict(id='leads', n=8, title='Lead Performance and Insights', body=body, kpis=kpis, facts=facts,
              subtitle=f'{M.lead_n:,} leads, {lf["trial_pct"]:.1f}% trialled, {lf["won_pct"]:.1f}% won')
    ch['recs_extra'] = recs_leads(M, X)
    return ch


def recs_leads(M, X):
    ld = X.ld; lf = M.lead_fun
    out = []
    try:
        g = ld['gate']
        if g is not None and len(g) > 1:
            out.append(('Make the trial the only acquisition target', 'Sales + Studio Manager',
                        f'Leads who completed a trial convert at {g["rate"].max():.1f}% and those who did not at '
                        f'{g["rate"].min():.1f}%. On this file that is {g["leads"].min():,} leads sitting on the wrong side '
                        f'of a diary entry.',
                        'Every lead conversation ends with a time and a class, not a callback. At the studio’s current trial-to-win rate, a hundred more trials is worth roughly '
                        f'{int(100 * (g["rate"].max() - g["rate"].min()) / 100)} more members a year.'))
    except Exception:
        pass
    try:
        rf = ld.get('resp')
        if rf is not None and len(rf) and float(rf.median()) > 0:
            out.append((f'Answer on the day, because the win is decided the same day {rf.median():.0f}% of the time',
                        'Sales',
                        f'The median first response in this file came after {rf.median():.0f} days, and {share(float((rf > 1).sum()), len(rf))} '
                        f'of leads waited more than a day, while {ld.get('same_day', 0):.0f}% of all wins closed on the '
                        f'day of the enquiry.',
                        'The lead is not waiting politely; they are calling the next studio on their list. A same-day response target with no exceptions is worth more than any change to the offer.'))
    except Exception:
        pass
    try:
        s = M.lead_src
        if s is not None and len(s) > 2:
            best = s.sort_values('won', ascending=False).head(2).index
            out.append((f'Move acquisition effort toward {clean(best[0])} and {clean(best[1])}', 'Marketing + Founder',
                        f'{clean(best[0])} converts at {s.loc[best[0], "won"]:.1f}% with a mean LTV of '
                        f'{R(s.loc[best[0], "ltv"])} on {int(s.loc[best[0], "leads"]):,} leads; the largest source, '
                        f'{clean(s["leads"].idxmax())}, converts at {s.loc[s["leads"].idxmax(), "won"]:.1f}% on '
                        f'{int(s["leads"].max()):,}.',
                        f'Tripling the smaller, better source costs less than the studio currently spends to fill the larger one and delivers members who stay longer.'))
    except Exception:
        pass
    try:
        if hasattr(M, 'open_stage') is False and ld.get('open_stage') is not None:
            st = ld['open_stage']
            out.append(('Close the open file honestly and start again', 'Sales + CRM',
                        f'{M.open_stale:,} open leads are more than six months old, and the largest stage pile is '
                        f'{clean(st.index[0])} at {int(st.iloc[0])} leads.',
                        'A forecast padded with dead leads is a forecast nobody trusts, and an associate measured on it learns to game it. Mark the outcome and let the number be real.'))
    except Exception:
        pass
    try:
        a = ld.get('assoc')
        if a is not None and len(a) > 3:
            out.append(('Publish conversion by associate, with book size beside it', 'Studio Manager',
                        f'Conversion runs {a["rate"].min():.1f}% to {a["rate"].max():.1f}% across books of {int(a["leads"].min())} to '
                        f'{int(a["leads"].max())} leads.',
                        'Putting the two columns together on one page every month ends the argument about whose leads are worse and starts the one about what each person does with theirs.'))
    except Exception:
        pass
    try:
        fo = ld.get('follow')
        if fo is not None and len(fo) > 1:
            out.append(('Report leads weekly, on the stage they are stuck at', 'Founder + Sales',
                        f'{int(fo["leads"].iloc[0]):,} leads were contacted at most once, and the file shows follow-ups '
                        f'spanning a median of {float(ld["fu_span"].median()):.0f} days for decisions that usually take one.',
                        'A weekly thirty-minute review of the stuck stages is the only cadence that matches how quickly a lead goes cold.'))
    except Exception:
        pass
    return out


# ================================ 9. MEMBER BEHAVIOUR AND PATTERNS
def behaviour(M):
    if 'checkins' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    BH = X.bh
    F = M.room.get(y, {})
    mon = mono(M)
    if not BH:
        return None
    v = M.people.get(y, {}).get('v')
    if v is None or not len(v):
        return None
    pn = M.people[y]

    def start():
        p = [para(f'{pn["members"]} people came to {M.studio} {pn["visits"]:,} times in {lab} &mdash; '
                  f'<strong>{pn["per"]:.2f} visits each</strong>. '
                  f'{M.beh["once"]:,} of them ({M.beh["once_share"]:.0f}%) came exactly once. The tenth most frequent '
                  f'member came {int(v.sort_values(ascending=False).iloc[9])} times.'),
             para(f'The top tenth of the base produced <strong>{M.beh["top_share"]:.0f}%</strong> of all attendance. '
                  f'That is the number that makes this chapter uncomfortable to read: the studio’s floor, its revenue and '
                  f'its atmosphere rest on a group small enough to fit in one class, and nothing in the current reporting '
                  f'notices when that group changes member by member.'),
             para(f'The median gap between one visit and the next, measured across the whole ledger for this studio, is '
                  f'<strong>{M.beh["gap_med"]:.0f} days</strong>, and {M.beh["gap_week"]:.0f}% of all gaps are a week or '
                  f'less. The studio has a rhythm it can build around, and a tail it currently pretends is the same thing.')]
        claim = (f'Attendance is not driven by how many members the studio has. It is driven by the small group who come '
                 f'twice a week and the large one who came once in the whole month. This month those two groups are '
                 f'{int((v >= 8).sum())} and {M.beh["once"]:,} people respectively, and they are the only two numbers '
                 f'worth managing.')
        b = [statgrid([('Members', _n(pn['members'])), ('Visits', f'{pn["visits"]:,}'),
                       ('Visits per member', f'{pn["per"]:.2f}'), ('Came once', f'{M.beh["once"]:,}')]),
              statgrid([('Median gap between visits', f'{M.beh["gap_med"]:.0f} days'),
                        ('Gaps of a week or less', f'{M.beh["gap_week"]:.0f}%'),
                        ('Top tenth of members', f'{M.beh["top_share"]:.0f}% of visits'),
                        ('Morning members', _n(M.beh['morning']))])]
        return head('Start here', 'Who comes, how often, and what the gaps say', claim) + ''.join(p + b)

    def when():
        heat = BH.get('heat')
        seg = BH.get('seg')
        p = [para(f'The month has a shape. By hour of the day: ' + ' · '.join(
            f'{int(i):02d}:00 {_n(v_)}' for i, v_ in M.beh['hours'].sort_values(ascending=False).head(5).items()) +
            f'. By weekday: ' + ' · '.join(f'{clean(i)} {_n(v_)}' for i, v_ in M.beh['days'].items() if v_) + '.')]
        if seg is not None and len(seg):
            p.append(para(f'Grouped into parts of the day, {clean(seg["members"].idxmax())} reaches the most members '
                          f'({int(seg["members"].max())}) but '
                          f'{clean(seg["per"].idxmax())} is the most devoted habit ({seg["per"].max():.2f} visits each). '
                          f'The studio is running a morning business and an evening one, with a midday gap that is not a '
                          f'lack of demand so much as a lack of a reason.'))
        b = []
        if heat is not None and heat.notna().any().any():
            rows = [[f'{int(i):02d}:00'] + [(_n(x) if pd.notna(x) else '·') for x in r] + [_n(r.sum())] for i, r in heat.iterrows()]
            b.append(T(['Hour'] + DAYS + ['Total'], rows, 'num'))
            b.append(para('Read the grid against the timetable in chapter 2. Where a member’s favourite hour and the '
                          'studio’s empty hour are the same slot, the capacity is not idle; it is idle for the wrong people.'))
        b.insert(0, bars([f'{int(i):02d}:00' for i in M.beh['hours'].index],
                         [('Visits', [float(x) for x in M.beh['hours']], A1)],
                         f'When members come, by the hour, {lab}', h=300,
                         note=f'Attended check-ins only. {F.get("att", 0):,.0f} attendances across the month.'))
        return sec('When members come', 'The hour, the weekday and the shape of the habit', p, b)

    def howoften():
        f = M.beh.get('freq')
        if f is None or not len(f):
            return ''
        p = [para(f'Visits per member, {mon.lower()} {y}: ' + ' · '.join(
            f'{int(i)} visit{"" if i == 1 else "s"} &mdash; {int(x):,}' for i, x in f.head(8).items()) +
            f'. Beyond eight visits, {int(f[f.index > 8].sum()):,} members.'),
             para(f'{share(int((v == 1).sum()), len(v))} of the base came once, {share(int((v <= 2).sum()), len(v))} twice '
                  f'or less, and {share(int((v >= 8).sum()), len(v))} came eight or more times. A studio averaging '
                  f'{pn["per"]:.2f} visits per member is not a studio of people coming three times a month; it is a studio '
                  f'of two different populations with one number between them.')]
        b = [bars([str(int(i)) for i in f.index[:12]], [('Members', [float(x) for x in f.head(12)], A1)],
                  f'How many times each member came, {lab}', h=300,
                  note=f'{len(v)} members who attended at least once. Anyone above twelve visits falls outside the chart and is listed in the evidence table.'),
             frame_ev('Evidence &mdash; the twenty most frequent members of the month',
                      BH.get('top', pd.DataFrame()).sort_values('visits', ascending=False).head(20).reset_index(),
                      ['Member ID', 'Visits', 'Formats used', 'Days attended'], ['w', 'n', 'n', 'n'])]
        return sec('How often members come', 'Two populations, one average', p, b)

    def buy():
        if 'pgap' not in M.beh:
            return ''
        p = [para(f'Purchases follow the same rhythm and lag it. Across the studio’s sales ledger the median gap between '
                  f'one purchase and the next is <strong>{M.beh["pgap_med"]:.0f} days</strong>, and '
                  f'{M.beh["pgap_month"]:.0f}% of repeat purchases come within a month. '
                  f'{M.beh["one_buy"]:.0f}% of everyone who has ever bought here bought exactly once.'),
             para(f'That last number is the studio’s real acquisition problem, and it is not an acquisition problem at all. '
                  f'A member who buys once and then trains for six weeks has already had the reason to buy again; the studio '
                  f'just never asks, in the window when the asking works.')]
        b = [tab(M.beh['pgap'].reset_index(), ['Gap between purchases', 'Occurrences'], ['w', 'n'], 'num'),
             bars([clean(i) for i in M.beh['pgap'].index], [('Repeat purchases', [float(x) for x in M.beh['pgap']], A1)],
                  'How often members buy', h=300,
                  note='Measured across the whole ledger for this studio, not the month, so that a two-year pattern is visible.')]
        return sec('How often members buy', 'The purchase rhythm, and where it stops', p, b)

    def rhythm():
        w = BH.get('weeks')
        if w is None or not len(w):
            return ''
        p = [para(f'Inside the month the attendance line is ' + ' → '.join(
            f'week {int(i)} {int(r["visits"]):,}' for i, r in w.iterrows()) +
            f'. Week {int(w.index[-1])} is partial ({int(w["visits"].iloc[-1] / max(w["visits"].max(), 1) * 100)}% of the '
            f'busiest), and the members per visit count moves from {w["per"].iloc[0]:.2f} to {w["per"].iloc[-1]:.2f}.'),
             para('A fade in the final week is not fatigue; it is the class pack running out and the renewal not yet '
                  'offered. Where the studio sees a soft month, the ledger sees the same twenty days of demand followed by '
                  'nothing to sell.')]
        b = [lines([f'week {int(i)}' for i in w.index], [('Visits', [float(x) for x in w['visits']], A1),
                                                          ('Members', [float(x) for x in w['members']], B1)],
                   f'The rhythm of {mon.lower()}', h=290,
                   note='Weeks are calendar weeks inside the month, so week 1 may be shorter than the others.')]
        return sec('The rhythm of the month', 'Four weeks, and what the last one is', p, b)

    def shape():
        if 'gap' not in M.beh:
            return ''
        g = M.beh['gap']
        p = [para('Gaps between visits, measured over the whole ledger for this studio: ' + ' · '.join(
            f'{clean(i)} {share(float(x), float(g.sum()))}' for i, x in g.items() if pd.notna(x)) + '.')]
        p.append(para(f'Two fifths of all visits follow another within the same day or the next; the tail beyond a month is '
                      f'small and it is where lapses come from. This is the studio’s best early-warning list, and it is not '
                      f'a list anyone currently builds: a member whose gap has just stretched past their own median is '
                      f'different from one who has always come monthly.'))
        pm = BH.get('permonth')
        b = []
        if pm is not None and len(pm):
            b.append(frame_ev('Evidence &mdash; visits per member per month, distribution', pm.reset_index(),
                              ['Member ID', 'Months attended', 'Mean visits a month', 'Best month', 'Worst month'],
                              ['w', 'n', 'f2', 'n', 'n'], maxrows=60,
                              blurb='Every member with at least one attended visit in the studio’s history, so the frequent and the occasional sit side by side.'))
        return sec('The shape of the base', 'Frequency, gaps and who is drifting', p, b)

    def trend():
        mo = BH.get('monthly')
        if mo is None or len(mo) < 6:
            return ''
        p = [para(f'Frequency through the years on file: {mon.lower()} was {mo["per"].iloc[-1]:.2f} visits per member, the '
                  f'{"lowest" if mo["per"].iloc[-1] <= mo["per"].min() * 1.05 else "middle"} of the {len(mo)} months '
                  f'recorded. The range across the whole series is {mo["per"].min():.2f} to {mo["per"].max():.2f}.'),
             para('A single month of frequency means little; the studio should read this line as the leading indicator of '
                  'revenue two months out, because a member who halves their visits renews, on average, half as often.')]
        b = [lines([str(i) for i in mo.index], [('Visits per member', [float(x) for x in mo['per']], A1),
                                                 ('Members', [float(x) / 100 for x in mo['members']], B1)],
                   'Frequency and base, month by month', h=330,
                   note='Members drawn at one hundredth its true value so both series share one axis. The check-in ledger is the only source that counts visits rather than sales.')]
        b.append(frame_ev('Evidence &mdash; the monthly series in full', mo.reset_index(),
                          ['Month', 'Visits', 'Members', 'Visits per member'], ['w', 'n', 'n', 'f2'], maxrows=60))
        return sec('Frequency through the year', 'The line that leads every other number', p, b)

    def routine():
        if not BH:
            return ''
        p = [para(f'{BH.get("multi", 0):.0f}% of the month’s members used more than one format and {BH.get("loyal", 0)} '
                  f'visited a single format three or more times. '
                  + (f'{M.beh["morning"]:,} members are morning, {M.beh["midday"]:,} midday and {M.beh["evening"]:,} evening.'
                     if hasattr(M, 'beh') else '')),
             para(f'Preference is stable enough to act on: the modal three-hour block of a member’s own visits holds '
                  f'{M.beh["morning"] + M.beh["evening"]:,} of the studio’s regulars between just three windows. A studio '
                  f'that knows a member’s hour can hold a slot for them, and holding a slot is a stronger invitation than '
                  f'sending one.')]
        b = [frame_ev(f'Evidence &mdash; which formats this month’s members used, and how often',
                      BH.get('fmt_matrix', pd.DataFrame()).sum().sort_values(ascending=False).reset_index(),
                      ['Format', 'Attendances'], ['w', 'n'],
                      blurb=f'From the check-in ledger for {lab}. ' + f'{len(BH.get("fmt_matrix", pd.DataFrame()))} members appear in this table.')]
        if BH.get('prod') is not None and len(BH['prod']):
            b.append(tab(BH['prod'].reset_index().head(12), ['What the visit was drawn against', 'Visits', 'Members', 'Visits per member'],
                         ['w', 'n', 'n', 'f2']))
            b.append(para(f'And the money behind the habit: {clean(BH["prod"].index[0])} carries '
                          f'{share(BH["prod"]["visits"].iloc[0], BH["prod"]["visits"].sum())} of all visits this month. '
                          f'What a member owns decides how often they come at least as much as what they like.'))
        return sec('Routine and variety', 'The habit, what it is drawn against, and what holds it', p, b)

    def intro():
        fn = BH.get('funnel')
        if not fn or not fn.get('n'):
            return ''
        n = fn['n']
        p = [para(f'The 2-for-1 introductory pack changes how a return is counted, so the studio’s own funnel should be '
                  f'read on the third visit rather than the second. Of {n:,} recorded first-timers: {fn["post1"]:,} came '
                  f'after their trial ({share(fn["post1"], n)}), {fn["post2"]:,} came twice more '
                  f'({share(fn["post2"], n)}), and <strong>{fn["post3"]:,} reached a third visit '
                  f'({share(fn["post3"], n)})</strong>.'),
             para('The step that matters is the third visit, and the studio currently treats the second as the milestone. '
                  'A member on a two-for-one has already been "retained" on their second visit while having bought nothing, '
                  'which is why the retention reports and the till disagree.')]
        b = [funnel([('Came for a first visit', n, f'{n:,} recorded'),
                     ('Returned once after the trial', fn['post1'], f'{share(fn["post1"], n)}'),
                     ('Returned twice', fn['post2'], f'{share(fn["post2"], n)}'),
                     ('Reached a third visit', fn['post3'], f'{share(fn["post3"], n)}')],
                    'Visits after the first, on the file’s own post-trial count',
                    note=f'Visits Post Trial, as the member file records it, for every first-timer attributed to {M.studio}.')]
        return sec('What the intro pack does to the numbers', 'A returning client on the third visit, not the second', p, b)

    def causes():
        items = [('yes', 'The offer, not the enthusiasm',
                  f'{M.beh["one_buy"]:.0f}% of everyone who has ever bought here bought once, while '
                  f'{share(int((v >= 8).sum()), len(v))} of the month’s members came eight times or more. The same product '
                  f'produces both.', 'Behaviour is being set by what the member owns, not by how they feel.'),
                 ('no', 'Attendance fell because members left',
                  f'The base grew to {pn["members"]} from {M.people.get(y - 1, {}).get("members", 0)} while frequency fell to '
                  f'{pn["per"]:.2f}. The people are here.',
                  'Ruled out by the count of distinct members in the ledger.'),
                 ('part', 'Fewer classes on offer',
                  f'{F.get("sessions", 0)} classes against {M.room.get(y - 1, {}).get("sessions", 0)} a year earlier. Supply '
                  f'moved, so a frequency fall can be at least partly mechanical.',
                  'Check attendance per class before blaming members.'),
                 ('yes', 'Gaps, not totals, predict lapse',
                  f'The median gap between visits is {M.beh["gap_med"]:.0f} days; {M.beh["gap_week"]:.0f}% of gaps close '
                  f'within a week. A member whose own gap stretches is visible weeks before anything else changes.',
                  'The list is computable tonight from the ledger the studio already exports.')]
        return sec('What else could explain it', 'The easy readings, tested', [para('Frequency is the number everybody explains last and the one that decides most, so it deserves its own set of rejected explanations.')], [hyp(items)])

    body = run([start, when, howoften, buy, rhythm, shape, trend, routine, intro, causes])
    defs = [('Visit', 'one attended check-in on the door ledger. A member who came twice in a day is two visits.'),
            ('Visits per member', 'attended visits in the month divided by distinct members who attended, for this studio only.'),
            ('Gap', 'days between one attended visit and the member’s next, across the studio’s whole ledger rather than the month.'),
            ('Morning / midday / evening', 'each member’s own most common hour falling before 12:00, between 12:00 and 17:00, or at 17:00 or later.'),
            ('Format used', 'the Cleaned Class value on the check-in row, counted as distinct formats per member in the month.')]
    caut = [('The check-in ledger counts arrivals, not intentions: a booked class nobody attended is invisible here, and appears instead in chapter 2 as a lost seat.'),
            ('A member who trains at two of the group’s studios appears in both, counted only for the visits recorded at this one.'),
            ('The member file records post-trial visits as the system counted them at the time of export, so very recent joiners have fewer visits recorded than they have made.'),
            ('Frequency is deliberately not adjusted for the length of the membership: the studio’s commercial question is how often a paying member comes, whatever product they hold.')]
    body += appendix(M, X, 'behaviour')
    body += method(M, defs, caut)
    kpis = [kpi('Members who came', _n(pn['members']), f'{pn["visits"]:,} visits'),
            kpi('Visits per member', f'{pn["per"]:.2f}', f'median gap {M.beh["gap_med"]:.0f} days',
                'neg' if (y - 1) in M.people and pn['per'] < M.people[y - 1]['per'] else 'pos'),
            kpi('Came exactly once', f'{M.beh["once"]:,}', f'{M.beh["once_share"]:.0f}% of the base', 'neg'),
            kpi('Top tenth of members', f'{M.beh["top_share"]:.0f}%', f'{M.beh["top_n"]} people', 'neg')]
    facts = [f'{pn["members"]} members made {pn["visits"]:,} visits in {lab} at {pn["per"]:.2f} each; {M.beh["once"]:,} came exactly once.',
             f'The median gap between visits across the studio’s whole ledger is {M.beh["gap_med"]:.0f} days and {M.beh["gap_week"]:.0f}% of gaps are a week or less.',
             f'The tenth of the base that comes most produces {M.beh["top_share"]:.0f}% of all attendance.']
    if BH.get('funnel'):
        fn = BH['funnel']
        facts.append(f'Of {fn["n"]:,} recorded first-timers, {share(fn["post3"], fn["n"])} reached a third visit - the point at which a 2-for-1 intro pack member is genuinely returning.')
    ch = dict(id='behaviour', n=9, title='Member Behaviour and Patterns', body=body, kpis=kpis, facts=facts,
              subtitle=f'{pn["members"]} members, {pn["per"]:.2f} visits each, {M.beh["top_share"]:.0f}% of attendance in the top tenth')
    ch['recs_extra'] = recs_behaviour(M, X)
    return ch


def recs_behaviour(M, X):
    y = M.y
    pn = M.people.get(y, {})
    v = pn.get('v')
    out = []
    try:
        once = M.beh['once']
        out.append((f'Give the {once:,} once-only members a dated plan, not a reminder', 'Front Desk + Studio Manager',
                    f'{once:,} of the {pn.get("members", 0)} members who attended in {M.label} came exactly once, '
                    f'{M.beh["once_share"]:.0f}% of the base. They are not a churn statistic; they are the next month’s '
                    f'frequency problem.',
                    f'One booked class with a time attached, offered before the member leaves the building, converts a visit into a habit. On this month’s numbers a tenth of that group attending twice more is {once * 0.1 * 2:,.0f} extra attendances.'))
    except Exception:
        pass
    try:
        g = M.beh['gap']
        med = M.beh['gap_med']
        out.append((f'Build the at-risk list from the member’s own gap, not from the studio’s', 'CRM',
                    f'The studio-wide median gap between visits is {med:.0f} day{"" if abs(med - 1) < .005 else "s"}, but the distribution runs from '
                    f'{clean(g.idxmax())} to a tail beyond two months. A fixed thirty-day rule flags half the base and misses '
                    f'the members who always came weekly and have just stopped.',
                    'A gap that stretches past a member’s own median is the earliest reliable warning the data contains, and it is computable from the ledger the studio already exports each day.'))
    except Exception:
        pass
    try:
        if 'pgap' in M.beh:
            out.append((f'Sell the next purchase {M.beh["pgap_med"]:.0f} days after the last', 'Front Desk + Finance',
                        f'The median gap between purchases at this studio is {M.beh["pgap_med"]:.0f} days and '
                        f'{M.beh["pgap_month"]:.0f}% of repeat purchases fall inside a month. Beyond that window the '
                        f'probability of a second purchase falls away.',
                        'A renewal conversation scheduled to the member’s own purchase rhythm rather than the expiry date is the difference between a renewal and a re-acquisition.'))
    except Exception:
        pass
    try:
        seg = X.bh.get('seg')
        if seg is not None and len(seg):
            out.append(('Program the middle of the day on purpose, not by residue', 'Programming',
                        f'{M.beh["midday"]:,} members take midday as their habit against {M.beh["morning"]:,} morning and '
                        f'{M.beh["evening"]:,} evening, and the midday group comes {seg["per"].min():.2f} times a month '
                        f'against {seg["per"].max():.2f} at the peak.',
                        'One format scheduled specifically for the middle of the day, with an off-peak price attached, converts idle mid-morning capacity rather than competing for the evening.'))
    except Exception:
        pass
    try:
        fn = X.bh.get('funnel')
        if fn and fn.get('n'):
            out.append(('Count the third visit, not the second, as the return', 'Marketing + Founder',
                        f'{share(fn["post2"], fn["n"])} of recorded first-timers came back once after their trial but only '
                        f'{share(fn["post3"], fn["n"])} reached a third visit. A 2-for-1 pack member is a returning client on '
                        f'their third visit, and every retention measure built on the second one is flattering the studio.',
                        'Fixing the definition changes what the team optimises for, and costs nothing but a column in the report.'))
    except Exception:
        pass
    try:
        if M.beh.get('top_share', 0) > 35:
            out.append(('Protect the frequent tenth as a named group', 'Studio Manager',
                        f'{M.beh["top_n"]} members produced {M.beh["top_share"]:.0f}% of all attendance in {M.label}. '
                        f'A fifth of them changing habit moves the month more than any acquisition campaign on file.',
                        'A monthly watch-list, one message when someone in it stops coming, and no discount, is the cheapest revenue protection the studio has.'))
    except Exception:
        pass
    return out
