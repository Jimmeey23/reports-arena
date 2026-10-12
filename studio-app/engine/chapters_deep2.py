"""Chapters 2 to 5, at report depth."""
from __future__ import annotations
import numpy as np, pandas as pd
from .design import (R, Rs, P, N, T, ev, note, bars, lines, hbars, diverging, stacked,
                     funnel, dumbbell, A1, A2, A3, B1, B2, N1, N2)
from .metrics import DAYS, MONTH_NAMES, rng
from .deep import (sec, tab, frame_ev, statgrid, hyp, method, appendix, guide, kpi, money, pc, _n,
                   clean, dpc, share, ratio, concentration, extremes, rank_list, yoy_para)
from .chapters_deep import deep, run, head, para, h4, yr, yrp, mono, core_ev, recs_sales


def _f(x, d=1):
    try:
        v = float(x)
        if not np.isfinite(v):
            return '·'
        return f'{v:,.{d}f}'
    except Exception:
        return '·'


# ==================================================== 2. CLASS PERFORMANCE
def classperf(M):
    if 'sessions' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    F, P1 = M.room.get(y, {}), M.room.get(y - 1, {})
    C = X.cls
    cur = C.get('cur')
    mon = mono(M)
    if not F or cur is None or not len(cur):
        return None

    def start():
        p = [para(f'{F["sessions"]} classes ran at {M.studio} in {lab}. They offered <strong>{F["seats"]:,.0f} seats</strong>, '
                  f'{F["book"]:,.0f} were booked and <strong>{F["att"]:,.0f} were occupied</strong> &mdash; '
                  f'{F["fill"]:.1f}% of the room, and a show rate of {F["conv"]:.1f}% on the seats that were booked. '
                  f'{R(F["rev"])} of class revenue was earned at {R(F["rpc"])} a class and {R(F["rph"])} per attendance.'),
             para('Utilisation is the only number here the studio cannot fix by selling harder. It is set by the timetable '
                  'the month before, by the weather of the month, and by how many of the booked seats turn up. Revenue follows '
                  'all three, which is why the class report and the sales report disagree so usefully when they are read '
                  'one after the other.')]
        if P1:
            d = F['fill'] - P1['fill']
            p.append(para(f'A year ago the same month ran {P1["sessions"]} classes and filled {P1["fill"]:.1f}% of them. The studio '
                          f'taught {F["sessions"] - P1["sessions"]:+d} classes and moved utilisation {d:+.1f} points. '
                          + ('More rooms and a fuller room at the same time is the best possible combination, and it is rare.'
                             if d > 0 and F['sessions'] > P1['sessions'] else
                             'More rooms on a flat or falling fill is the timetable outrunning demand.'
                             if F['sessions'] > P1['sessions'] else
                             'A smaller timetable with a falling fill means the studio is shrinking and not yet choosing where.')))
        claim = (f'{F["book"] - F["att"]:,.0f} booked seats went empty in {mon.lower()}. Late cancellations account for '
                 f'{share(F["lc"], F["book"] - F["att"]) if F["book"] - F["att"] else "0%"} of them; the rest never cancelled, '
                 f'and never came. The first number is a policy question and the second is not being measured at all.')
        blocks = [statgrid([('Classes', _n(F['sessions'])), ('Seats offered', _n(F['seats'])),
                            ('Attendances', _n(F['att'])), ('Utilisation', f'{F["fill"]:.1f}%')]),
                  statgrid([('Booked', _n(F['book'])), ('Booked and absent', _n(F['book'] - F['att'])),
                            ('Late cancellations', _n(F['lc'])), ('Class revenue', R(F['rev']))])]
        return head('Start here', 'The room, the booking book and what actually turned up', claim) + ''.join(p + blocks)

    def core():
        c = getattr(M, 'core', None)
        if not c or not c.get('n'):
            return ''
        p = [para(f'The studio did not lose its members between {yrp(M)} and {lab}. Of the {M.people.get(y - 1, {}).get("members", 0)} '
                  f'people who trained here last {mon.lower()}, <strong>{c["n"]} came back this year</strong> and '
                  f'{c["new"]} were new to the month. What changed is frequency: the returning core made {c["prev"]:,.0f} visits '
                  f'last year and {c["now"]:,.0f} this year, <strong>{abs(c["lost"]):,.0f} fewer</strong>.'),
             para(f'Those {abs(c["lost"]):,.0f} missing attendances are {share(c["lost"], F["att"])} of this month\’s '
                  f'total attendance. Read as a demand problem it looks unsolvable; read as the same people coming every ten '
                  f'days instead of every seven, it is a scheduling and habit problem, and the studio owns both.')]
        b = [frame_ev('Evidence &mdash; the returning core, member by member', core_ev(M, 80),
                      ['Member ID', f'{yrp(M)} visits', f'{lab} visits', 'Change'], ['w', 'n', 'n', 'n'],
                      blurb='First eighty members of the core by id, sorted as they appear in the ledger.')]
        return sec('Nobody was lost. Nothing was converted', 'Where the missing attendances came from', p, b)

    def booking():
        bk = C.get('book')
        if bk is None or not len(bk):
            return ''
        lost = float(bk['lost'].sum())
        p = [para(f'{_n(F["book"])} seats were booked and {lost:,.0f} were not occupied. '
                  f'{share(float(F["lc"]), lost) if lost else "-"} of those empty seats were formally released as late '
                  f'cancellations; the remaining {lost - float(F["lc"]):,.0f} were booked, paid for or not, and simply did not '
                  f'appear. A studio that counts only the cancelled seats believes its no-show problem is a tenth the size '
                  f'it is.'),
             para('The booking book is also where the waitlist opportunity sits. '
                  + (f'{clean(bk["lost"].idxmax())} alone left {int(bk["lost"].max())} booked seats empty at a '
                     f'{bk.loc[bk["lost"].idxmax(), "show"]:.0f}% show rate.' if len(bk) else ''))]
        bk_cols = ['_cls', 'book', 'att', 'lc', 'lost', 'show']
        bk_df = bk.reset_index()
        for c in bk_cols:
            if c not in bk_df.columns:
                bk_df[c] = np.nan
        bk_df = bk_df[bk_cols].copy()
        bk_df['_cls'] = bk_df['_cls'].apply(clean)
        b = [tab(bk_df, ['Format', 'Booked', 'Attended', 'Late cancelled', 'Seats lost', 'Show rate'],
                 ['w', 'n', 'n', 'n', 'n', 'p']),
             hbars([(clean(i), float(v), B1) for i, v in bk['lost'].sort_values(ascending=False).head(10).items()],
                   'Booked seats that went empty, by format', unit='',
                   note='Booked minus attended. Includes members who never cancelled.')]
        return sec('What the booking book says', 'Booked is not the same as attended', p, b)

    def room():
        rm = getattr(M, 'rooms', None)
        gr = C.get('grid')
        p = []
        if rm is not None and len(rm):
            p.append(para('The room is not one size. ' + ' '.join(
                f'{clean(r["band"])} seats carried {_n(r["sessions"])} classes at {_f(r["fill"])}% fill' for _, r in rm.iterrows())
                + '. Where a smaller room fills and a larger one does not, the fix is the allocation, not the marketing.'))
        if gr is not None and gr.notna().any().any():
            rows = [[f'{int(i):02d}:00'] + [_n(v) if pd.notna(v) else '·' for v in r] + [_n(r.sum())] for i, r in gr.iterrows()]
            p.append(para(f'The grid below is the whole month in one view: attendances by hour and weekday. '
                          f'The heaviest cell is {int(gr.stack().idxmax()[0]):02d}:00 on a {gr.stack().idxmax()[1]} at '
                          f'{_n(gr.stack().max())} attendances; the timetable placed {_n(gr.fillna(0).to_numpy().size)} '
                          f'slots across this grid and demand filled a fraction of it.'))
        b = []
        if rm is not None and len(rm):
            b.append(T(['Room size', 'Classes', 'Seats per class', 'Average attendance', 'Utilisation', 'Revenue per class'],
                       [[clean(r['band']), _n(r['sessions']), _f(r['seats']), _f(r['att']), f'{r["fill"]:.1f}%', R(r['rev'])]
                        for _, r in rm.iterrows()], 'num'))
        hh = C.get('hour')
        if hh is not None and len(hh):
            b.append(bars([f'{int(i):02d}:00' for i in hh.index],
                          [('Seats offered', [float(v) for v in hh['seats']], B1),
                           ('Attended', [float(v) for v in hh['att']], A1)],
                          f'Where the {mon.lower()} capacity went, by hour', h=310,
                          note='The pale bars are what the timetable offered; the accent bars are what arrived. The white space between them is the decision to make.'))
            hh_cols = ['_hr', 'sessions', 'seats', 'att', 'fill', 'rev', 'att_p']
            hh_df = hh.reset_index()
            for c in hh_cols:
                if c not in hh_df.columns:
                    hh_df[c] = np.nan
            hh_df = hh_df[hh_cols].copy()
            b.append(tab(hh_df, ['Hour', 'Classes', 'Seats', 'Attended', 'Utilisation', 'Revenue', 'Attended last year'],
                         ['n', 'n', 'n', 'n', 'p', 'm', 'n'], 'num'))
        if gr is not None and gr.notna().any().any():
            b.append(frame_ev('Evidence &mdash; attendances by hour and day, the whole month',
                              pd.DataFrame(rows, columns=['Hour'] + DAYS + ['Total']),
                              ['Hour'] + DAYS + ['Total'], ['w'] + ['n'] * 8))
        return sec('The room is bigger than the demand', 'Capacity, where it was put, and where it landed', p, b)

    def free():
        oc = C.get('occ')
        mx = C.get('paymix')
        p = []
        if oc is not None and len(oc):
            empty = float(oc.loc['nobody', 'n']) if 'nobody' in oc.index else 0
            seats = float(oc['seats'].sum())
            p.append(para(f'By how many people turned up: ' + ' · '.join(
                f'{clean(i)} {_n(r["n"])} classes' for i, r in oc.iterrows()) + '.'))
            if seats:
                p.append(para(f'Across the month {share(float(oc["seats"].sum() - oc["att"].sum()), float(oc["seats"].sum()) * 1.0)} '
                              f'of every seat the studio offered sat empty. In the classes that ran to nobody, '
                              f'{float(oc.loc["nobody", "seats"]) if "nobody" in oc.index else 0:,.0f} seats were held '
                              f'and released without anyone using them.'))
        if mx is not None and len(mx):
            free_pct = float((mx['intro'] + mx['nonpaid']).sum() / max(mx['total'].sum(), 1) * 100)
            p.append(para(f'The seat mix says who was in the room. {share(float(mx["mem"].sum()), mx["total"].sum())} of '
                          f'attendances were drawn against a membership, {share(float(mx["pkg"].sum()), mx["total"].sum())} '
                          f'against a package, {share(float(mx["single"].sum()), mx["total"].sum())} bought as a single class, '
                          f'and {share(float(mx["intro"].sum()), mx["total"].sum())} arrived as an introductory offer. '
                          f'A studio with a high free share is running a marketing budget through its timetable.'))
        b = []
        if oc is not None and len(oc):
            b.append(bars([str(i) for i in oc.index], [('Classes', [float(v) for v in oc['n']], A1)],
                          f'Classes by how full they ran, {lab}', h=280,
                          note='Counted from the sessions ledger, which records every class the studio taught.'))
            b.append(T(['Attendance band', 'Classes', 'Seats offered', 'Attended', 'Revenue'],
                       [[clean(i), _n(r['n']), _n(r['seats']), _n(r['att']), R(r['rev'])] for i, r in oc.iterrows()], 'num'))
        if mx is not None and len(mx):
            b.append(frame_ev('Evidence &mdash; what each format was paid for with',
                              mx.reset_index(), ['Format', 'Memberships', 'Packages', 'Intro offers', 'Singles',
                                                  'Non-paid', 'Complimentary', 'Free %'],
                              ['w', 'n', 'n', 'n', 'n', 'n', 'n', 'p'],
                              blurb='Counts of attendances by what they were drawn against, not of seats.'))
        return sec('The free seats', 'Who was in the room, and on what', p, b)

    def firstclass():
        nw = X.nw
        v = nw.get('vtype')
        sl = X.bh.get('slot')
        p = []
        if v is not None and len(v):
            p.append(para(f'What a first class does: of the {int(v["people"].sum()):,} recorded first-timers at this studio, '
                          + ' '.join(f'{clean(i)} brought {int(r["people"])} of them, converting {r["conv"]:.0f}% and arriving '
                                     f'at a lifetime value of {R(r["ltv"])}' for i, r in v.head(4).iterrows()) + '.'))
        if sl is not None and len(sl):
            one = int(sl.loc[1, 'visits']) if 1 in sl.index else 0
            p.append(para(f'In {lab} the check-in ledger recorded <strong>{one:,} visits that were someone\’s first class '
                          f'with us</strong> out of {_n(F["att"])} attendances. Every one of those is a lead the studio has '
                          f'already converted into an hour of its own time, and the follow-up on them is currently nobody\’s '
                          f'job.'))
        b = []
        if nw.get('first') is not None and len(nw['first']):
            b.append(tab(nw['first'].reset_index(), ['First purchase', 'People', 'Mean LTV', 'Mean visits', 'Converted %'],
                         ['w', 'n', 'm', 'f1', 'p']))
        if sl is not None and len(sl):
            b.append(frame_ev(f'Evidence &mdash; which visit number in the member\’s history each {mon.lower()} attendance was',
                              sl.reset_index(), ['Visit number', 'Attendances'], ['n', 'n'],
                              blurb='Visit 1 is a genuinely new member. Visit 2 and 3 are where a 2-for-1 introductory pack makes the difference between a trial and a habit.'))
        if not p and not b:
            return ''
        return sec('Who a first class brings in', 'New blood, and what happens to it', p, b)

    def byformat():
        fm = C.get('fmt_yoy')
        if fm is None or not len(fm):
            return ''
        p = [para('Format by format, the month reads: ' + rank_list(fm, 'att', 5) + '.'),
             extremes(fm, 'fill', 'utilisation'),
             (f'Two thirds of the classes sit in {share(float(fm["sessions"].iloc[:2].sum()), float(fm["sessions"].sum()))} of '
              f'the timetable while {int((fm["sessions"] <= 3).sum())} formats ran three classes or fewer. That is not a '
              f'portfolio, it is a schedule with a long tail attached, and the tail costs the same to staff as the head.')]
        fm_cols = ['_cls', 'sessions', 'seats', 'att', 'fill', 'rev', 'rpc', 'att_p', 'rev_p']
        fm_df = fm.reset_index()
        for c in fm_cols:
            if c not in fm_df.columns:
                fm_df[c] = np.nan
        fm_df = fm_df[fm_cols].copy()
        fm_df['_cls'] = fm_df['_cls'].apply(clean)
        b = [tab(fm_df, ['Format', 'Classes', 'Seats', 'Attended', 'Utilisation', 'Revenue', 'Per class',
                         'Attended last year', 'Revenue last year'],
                 ['w', 'n', 'n', 'n', 'p', 'm', 'm', 'n', 'm'], maxrows=20),
             bars([clean(i) for i in fm.index[:10]], [('Utilisation %', [float(v) for v in fm['fill'].head(10)], A1)],
                  f'Utilisation by format, {lab}', h=300, as_pct=True, ymax=float(np.nanmax(fm['fill'].head(10))) * 1.25,
                  note='Only formats that ran at least once in the month appear. A format with one or two classes will look extreme on this chart and should not be treated as one.'),
             frame_ev('Evidence &mdash; every class taught, with capacity and attendance',
                      cur.sort_values('_dt')[['_dt', '_day', '_hr', '_cls', '_trainer', '_cap', 'CheckedIn', 'Booked',
                                               'LateCancelled', 'Revenue']].head(90),
                      ['Date', 'Day', 'Hour', 'Format', 'Trainer', 'Capacity', 'Attended', 'Booked', 'Late cancelled', 'Revenue'],
                      ['w', 'w', 'n', 'w', 'w', 'n', 'n', 'n', 'n', 'm'],
                      blurb='The first ninety rows of the month, in date order. The full ledger is in the upload.')]
        return sec('Format by format', 'The league table, with last year beside it', p, b)

    def busy():
        d = C.get('dow')
        if d is None or not len(d):
            return ''
        p = [para('The week is not flat. ' + ' · '.join(
            f'{clean(i)} {r["fill"]:.0f}%' for i, r in d.iterrows() if pd.notna(r['fill'])) +
            f'. The gap between the best and worst day is {d["fill"].max() - d["fill"].min():.0f} points, which is larger '
            f'than most of the differences the studio spends money trying to move.'),
            (f'Against last year, {mon.lower()} attendance on {d["att"].idxmax()} '
             + (f'held at {int(d.loc[d["att"].idxmax(), "att"])} against {int(d.loc[d["att"].idxmax(), "att_p"])}'
                if 'att_p' in d and pd.notna(d.loc[d['att'].idxmax(), 'att_p']) else 'moved') + '.')]
        if 'att_p' in d:
            p.append(para(f'Day by day the year-on-year picture differs from the shape of the month: '
                          + ' '.join(f'{clean(i)} {((r["att"] - r["att_p"]) / r["att_p"] * 100):+.0f}%'
                                     for i, r in d.iterrows() if pd.notna(r['att_p']) and r['att_p']) + '.'))
        b = [T(['Day', 'Classes', 'Seats', 'Attended', 'Utilisation', 'Revenue', f'{mon[:3]} last year attendance'],
               [[str(i), _n(r['classes']), _n(r['seats']), _n(r['att']), f'{r["fill"]:.1f}%', R(r['rev']),
                 _n(r['att_p']) if 'att_p' in r and pd.notna(r['att_p']) else '·'] for i, r in d.iterrows()], 'num'),
             bars([str(i)[:3] for i in d.index], [('Attended', [float(v) for v in d['att']], A1),
                                                   ('Seats offered', [float(v) for v in d['seats']], B1)],
                  f'Where the {mon.lower()} week actually went', h=300,
                  note='The pale bars are the studio\’s choice; the accent bars are the members\’.')]
        return sec('When the studio is busy', 'The week, the hour and the year before', p, b)

    def lean():
        ln = C.get('lean')
        emp = C.get('empty')
        if ln is None or not len(ln):
            return ''
        p = [para(f'{_n(len(emp))} classes ran to nobody at all and {int(C["near"].shape[0])} ran to one or two people. '
                  f'They are not scattered: ' + ', '.join(f'{clean(i)} ({_n(r["nobody"])} empty)' for i, r in ln.head(4).iterrows() if r['nobody'])
                  + '. Every one of those classes was scheduled, staffed and lit.'),
             para('Empty classes are cheap to ignore because each one individually costs little. In a month they are the '
                  'single largest block of recoverable capacity: they consume trainer hours that the filled classes could '
                  'have used, and they are the first place a member looks when they want a room with nobody in it.')]
        if 'share' not in ln.columns:
            ln['share'] = ln['lean'] / ln['all'].replace(0, np.nan) * 100
        ln_cols = ['_cls', 'nobody', '1 to 2 only', 'lean', 'all', 'share']
        ln_df = ln.reset_index()
        for c in ln_cols:
            if c not in ln_df.columns:
                ln_df[c] = np.nan
        ln_df = ln_df[ln_cols].copy()
        ln_df['_cls'] = ln_df['_cls'].apply(clean)
        b = [tab(ln_df, ['Format', 'Nobody came', '1 to 2 only', 'Lean classes', 'All classes', 'Lean share'],
                 ['w', 'n', 'n', 'n', 'n', 'p']),
             frame_ev(f'Evidence &mdash; every class that ran to nobody in {lab}', emp[['_dt', '_day', '_hr', '_cls', '_trainer', '_cap', 'Booked', 'LateCancelled']],
                      ['Date', 'Day', 'Hour', 'Format', 'Trainer', 'Capacity', 'Booked', 'Late cancelled'],
                      ['w', 'w', 'n', 'w', 'w', 'n', 'n', 'n'],
                      blurb='A class with zero check-ins and a class with zero bookings are different problems; the Booked column tells you which one you are looking at.')]
        if emp is not None and len(emp) and '_hr' in emp:
            h = emp.groupby(emp['_hr'].astype('Int64')).size().sort_values(ascending=False)
            b.insert(1, para('They cluster in time: ' + ' · '.join(f'{int(i):02d}:00 {_n(v)}' for i, v in h.head(5).items())
                             + '. An hour that runs empty is a scheduling decision, not a membership problem.'))
        return sec('The classes nobody came to', 'Where the timetable is asking for something that is not there', p, b)

    def within():
        w = C.get('weeks')
        if w is None or not len(w):
            return ''
        p = [para(f'Split into weeks, the month ran ' + ' → '.join(f'week {int(i)} {r["fill"]:.0f}%' for i, r in w.iterrows())
                  + f'. {'The fade is in the last week' if w['fill'].iloc[-1] < w['fill'].iloc[0] else 'The month strengthened as it went'}: '
                  f'week {int(w.index[0])} filled {w["fill"].iloc[0]:.0f}% and week {int(w.index[-1])} filled {w["fill"].iloc[-1]:.0f}%, '
                  f'on {int(w["classes"].iloc[-1])} classes against {int(w["classes"].iloc[0])}.'),
             para('A single-month review that ignores this shape will attribute a calendar effect to management. Weeks are '
                  'also where a studio can act fastest: a class moved from week four to week one costs nothing but a text.')]
        b = [lines([f'week {int(i)}' for i in w.index], [('Utilisation %', [float(v) for v in w['fill']], A1)],
                   f'Utilisation by week of {mon.lower()}, {y}', h=280, as_pct=True,
                   ymax=float(np.nanmax(w['fill'])) * 1.3, note='Weeks are the calendar, not the timetable: week 1 is days 1 to 7.'),
             T(['Week', 'Classes', 'Seats', 'Attended', 'Utilisation', 'Booked', 'Revenue per class'],
               [[f'{int(i)}', _n(r['classes']), _n(r['seats']), _n(r['att']), f'{r["fill"]:.1f}%', _n(r['book']), R(r['rpc'])]
                for i, r in w.iterrows()], 'num')]
        return sec('The month within the month', 'Four weeks, four different studios', p, b)

    def pays():
        fm = C.get('fmt_yoy')
        if fm is None or not len(fm):
            return ''
        tot_rev = float(fm['rev'].sum())
        s = fm.sort_values('rpc', ascending=False)
        p = [para(f'The room pays for itself unevenly. Revenue per class ranges from {R(s["rpc"].min())} '
                  f'({clean(s.index[-1])}) to {R(s["rpc"].max())} ({clean(s.index[0])}) &mdash; a '
                  f'{ratio(s["rpc"].max(), s["rpc"].min())}-fold difference for an hour of the same floor, the same sound '
                  f'system and the same rent. The difference is capacity, price and who owns the visit, and all three are '
                  f'set by the studio, not by the member.'),
             para(f'{clean(s["rev"].idxmax())} earns the most in total ({R(s["rev"].max())}, '
                  f'{share(s["rev"].max(), tot_rev)} of the month) while {s["rpc"].idxmax()} earns most per class. '
                  'A format that earns most per class and fewest classes is a pricing opportunity; the opposite is a '
                  'scheduling one.')]
        if 'rph' not in s.columns:
            s['rph'] = s['rev'] / s['att'].replace(0, np.nan)
        s_cols = ['_cls', 'sessions', 'rev', 'rpc', 'rph', 'att', 'fill']
        s_df = s.reset_index()
        for c in s_cols:
            if c not in s_df.columns:
                s_df[c] = np.nan
        s_df = s_df[s_cols].copy()
        s_df['_cls'] = s_df['_cls'].apply(clean)
        b = [diverging([(clean(i), float(v)) for i, v in (fm['rev'] - fm['rev_p']).sort_values().items()] if 'rev_p' in fm
                       else [(clean(i), float(v) - float(v)) for i, v in fm['rev'].items()],
                       f'Change in class revenue by format, {lab} against {yrp(M)}',
                       note='Where a format did not exist in one of the two months, the whole of its value appears as a movement.'),
             tab(s_df, ['Format', 'Classes', 'Revenue', 'Revenue per class', 'Revenue per attendance',
                        'Attended', 'Utilisation'], ['w', 'n', 'm', 'm', 'm', 'n', 'p'])]
        return sec('How the room pays for itself', 'Revenue per class, and what moves it', p, b)

    def hosted():
        h = C.get('hosted', {})
        if not h or not h.get('n'):
            return ''
        p = [para(f'{h["n"]} classes in {lab} were hosted, partner or event sessions, taking {h["att"]:,.0f} of the month\’s '
                  f'{F["att"]:,.0f} attendances ({share(h["att"], F["att"])}) for {R(h["rev"])} of recorded revenue. They were '
                  f'offered {h["seats"]:,.0f} seats, so they consumed {share(h["seats"], F["seats"])} of the studio\’s capacity.'),
             para('Event classes are neither a marketing line nor a programming line as things stand, so they are counted in '
                  'both and owned by neither. Put them on one page with a purpose attached &mdash; reach, goodwill or cash &mdash; '
                  'and the next month can be judged on whichever was chosen.')]
        b = [frame_ev('Evidence &mdash; the hosted and partner sessions', C.get('hosted_rows'),
                      ['Session', 'Classes', 'Attended', 'Revenue'], ['w', 'n', 'n', 'm'],
                      blurb='Identified from the session name; the filter is deliberately broad, so a partner class named after a brand will be caught and a quiet recurring class will not.')]
        return sec('Hosted and partner classes', 'Capacity that is spent on something else', p, b)

    def causes():
        items = []
        try:
            items.append(('part', 'Fewer classes, or fewer people?',
                          f'The timetable ran {F["sessions"]} classes against {P1.get("sessions", 0)} a year earlier, so '
                          f'{share(F["seats"], P1.get("seats", 1) * 1.0)} of last year\’s capacity was on offer. '
                          'Utilisation moves on both numerator and denominator; read the seats before blaming the demand.',
                          'If seats fell and fill held, the studio cut supply; if seats rose and fill fell, it added supply ahead of demand.'))
        except Exception:
            pass
        try:
            items.append(('yes', 'The 2-for-1 pack changes what counts as a return',
                          'A member on an introductory two-for-one is a returning client on their third visit, not their '
                          'second. Read on the second visit, the repeat rate of any month looks collapsed.',
                          'Applied throughout: frequency here is visits per member from the check-in ledger, which counts what happened rather than what was paid for.'))
        except Exception:
            pass
        items += [('no', 'The weather and the calendar',
                   f'A {mon.lower()} month at this studio contains public holidays and festival weeks that move between years. '
                   f'The weekly split above is shown so the effect can be seen in the data instead of argued about.',
                   'Cannot be confirmed from these files: the exports carry no closed-day or weather record.'),
                  ('yes', 'Nobody was told the room was half empty',
                   f'Show rate was {F["conv"]:.1f}% on {F["book"]:,.0f} booked seats. Published capacity, bookings and waitlist '
                   'turn an unused seat into a sold one at no cost.', 'This is the only lever in this chapter that needs no price change.')]
        return sec('What else could explain it', 'The causes that are easy to miss, and the ones that are not',
                   [para('Utilisation is the most over-attributed number in a studio. These are the candidate explanations for this month, in order of how much of the gap they can actually carry.')],
                   [hyp(items)])

    body = run([start, core, booking, room, free, firstclass, byformat, busy, lean, within, pays, hosted, causes])
    defs = [('Class', 'one row of the sessions export. Where a row carries a class count above one, it is read as one scheduled slot.'),
            ('Utilisation', 'attended places divided by seats offered (Capacity), not by bookings.'),
            ('Show rate', 'attended divided by booked.'),
            ('Late cancellation', 'the LateCancelled count on the session row: a member who released the seat inside the cancellation window.'),
            ('Empty class', 'a scheduled class with zero check-ins, whether or not anybody booked it.')]
    caut = [('The sessions ledger records capacity as it was configured, not as it was sold: a class capped at 12 and sold 8 has 4 seats here whether the studio meant to hold them or not.'),
            ('Attendance is counted from check-ins on the door. A member who arrived and did not scan is invisible.'),
            ('No revenue in this chapter is cash. It is the value of classes delivered, which is why it will not agree with the sales ledger and should not.'),
            (f'The year-on-year compares the same calendar month, not a rolling four-week window, so a month of differing length or a shifted festival week will show as a movement that is not one.')]
    body += appendix(M, X, 'class')
    body += method(M, defs, caut)
    kpis = [kpi('Classes taught', _n(F['sessions']), (f'{F["sessions"] - P1["sessions"]:+d} on last year' if P1 else '')),
            kpi('Utilisation', f'{F["fill"]:.1f}%', (f'{F["fill"] - P1["fill"]:+.1f} points' if P1 else ''), 'pos' if P1 and F['fill'] >= P1['fill'] else 'neg'),
            kpi('Attendances', _n(F['att']), f'{share(F["att"], F["book"])} of booked seats'),
            kpi('Revenue per class', R(F['rpc']), f'{R(F["rph"])} per attendance')]
    facts = [f'{F["sessions"]} classes, {F["seats"]:,.0f} seats, {F["att"]:,.0f} attendances and {F["fill"]:.1f}% utilisation in {lab}.',
             f'{R(F["rev"])} of class revenue at {R(F["rpc"])} a class and {R(F["rph"])} per attendance.',
             f'{F["book"] - F["att"]:,.0f} booked seats went empty; {F["lc"]:,.0f} of those were late cancellations.']
    ch = dict(id='class', n=2, title='Class Performance', body=body, kpis=kpis, facts=facts,
              subtitle=f'{F["sessions"]} classes at {F["fill"]:.1f}% utilisation, {R(F["rpc"])} a class')
    ch['recs_extra'] = recs_class(M, X)
    return ch


def recs_class(M, X):
    y = M.y
    F = M.room.get(y, {})
    C = X.cls
    out = []
    try:
        bk = C['book']
        w = bk.loc[bk['lost'].idxmax()]
        out.append((f'Recover the {int(w["lost"])} booked seats {clean(bk["lost"].idxmax())} leaves empty',
                    'Studio Manager + Programming',
                    f'{clean(bk["lost"].idxmax())} is the largest single source of unoccupied booked seats this month: '
                    f'{int(w["lost"])} of them, on a {w["show"]:.0f}% show rate against a studio-wide '
                    f'{float(F["att"]) / max(float(F["book"]), 1) * 100:.0f}%.',
                    f'The scale of the format is what makes the number worth chasing: one class a week tighter, or a '
                    f'waitlist that fires the moment a seat returns, recovers roughly {int(w["lost"] / 4)} seats a month '
                    f'without a single new member being asked for money.'))
    except Exception:
        pass
    try:
        ln = C['lean']
        e = int(ln['nobody'].sum())
        if e:
            out.append(('Review every class that ran to nobody before it is scheduled again', 'Programming',
                        f'{e} classes in {M.label} were taught to an empty room, concentrated in '
                        f'{clean(ln["nobody"].idxmax())} ({int(ln.loc[ln["nobody"].idxmax(), "nobody"])}).',
                        'Each one is a paid hour that produced nothing. A monthly rule - three empties and the slot is retired or re-timed - is the cheapest capacity the studio has.'))
    except Exception:
        pass
    try:
        hh = C['hour']
        worst = hh.sort_values('fill').head(1).index[0]
        best = hh['fill'].idxmax()
        out.append(('Close or re-time the hour nobody uses', 'Programming + Studio Manager',
                    f'{int(best):02d}:00 fills at {hh.loc[best, "fill"]:.0f}% while {int(worst):02d}:00 fills at '
                    f'{hh.loc[worst, "fill"]:.0f}% on {int(hh.loc[worst, "classes"])} classes.',
                    'Moving an hour of capacity from the weakest slot to the strongest is a same-month change to utilisation that needs no new members, no price change and no marketing spend.'))
    except Exception:
        pass
    try:
        oc = C['occ']
        nn = float(oc.loc['1 to 2', 'n']) if '1 to 2' in oc.index else 0
        if nn:
            out.append(('Set a minimum viable class size and publish it', 'Programming',
                        f'{nn:.0f} classes ran to one or two people out of {int(oc["n"].sum())}. A room of two costs the same '
                        f'as a room of ten and reads, to the member in it, as a class nobody wants.',
                        'Merging thin classes into the adjacent slot protects the format and raises the perceived quality of both.'))
    except Exception:
        pass
    try:
        h = C.get('hosted', {})
        if h.get('n'):
            out.append(('Give event classes a purpose and a number', 'Marketing + Studio Manager',
                        f'{h["n"]} hosted or partner sessions took {int(h["att"])} attendances ({share(h["att"], F["att"])}) '
                        f'and {R(h["rev"])} of revenue on {share(h["seats"], F["seats"])} of the month\’s capacity.',
                        'Decide in advance whether each event is buying reach or making money, and the next month can be judged on the one that was chosen.'))
    except Exception:
        pass
    try:
        mx = C['paymix']
        fr = float((mx['intro'] + mx['nonpaid']).sum() / max(mx['total'].sum(), 1) * 100)
        if fr > 4:
            out.append(('Put a ceiling on the free seat, by format', 'Studio Manager + Finance',
                        f'{fr:.1f}% of this month\’s attendances arrived on an introductory offer or unpaid, against a '
                        f'monthly board occupancy of {F.get("fill", 0):.1f}%.',
                        'A stated budget turns complimentary seats into a marketing spend with a return attached instead of a habit with none.'))
    except Exception:
        pass
    return out


# ================================================= 3. INSTRUCTOR PERFORMANCE
def instructor(M):
    if 'sessions' not in M.has:
        return None
    X = deep(M)
    y, lab = M.y, M.label
    t = X.tr
    if t is None or not len(t):
        return None
    F = M.room.get(y, {})
    pr = X.prscore
    prv = getattr(X, 'prscore_prev', None)
    mon = mono(M)

    def start():
        best, worst = t['fill'].idxmax(), t['fill'].idxmin()
        p = [para(f'{len(t)} trainers taught {int(t["sessions"].sum()):,} classes at {M.studio} in {lab}, filling '
                  f'{t["att"].sum():,.0f} of {t["seats"].sum():,.0f} seats and delivering {R(t["rev"].sum())} of class '
                  f'revenue. Utilisation ranged from {t.loc[worst, "fill"]:.1f}% ({clean(worst)}) to '
                  f'{t.loc[best, "fill"]:.1f}% ({clean(best)}), a spread of {ratio(t["fill"].max(), t["fill"].min())} times.'),
             para(f'That spread is the number that gets managers excited and is nearly always misread. Revenue per attendee '
                  f'for the same trainers runs {R(t["rph"].dropna().min())} to {R(t["rph"].dropna().max())} &mdash; a spread of '
                  f'{ratio(t["rph"].dropna().max(), t["rph"].dropna().min())} times. Most of what looks like performance is '
                  f'the slot, the format and the room size the trainer was handed.'),
             para(f'Two figures belong beside every utilisation number in this chapter: {t["empty"].sum():.0f} classes ran to '
                  f'nobody, and {t["lc"].sum():,.0f} seats were late-cancelled against the {t["book"].sum():,.0f} that were '
                  f'booked. Those are the two things a trainer controls that the timetable does not.')]
        claim = None
        if pr is not None and len(pr):
            try:
                conv = pd.to_numeric(pr['Conversion Rate'].astype(str).str.replace('%', '', regex=False), errors='coerce')
                claim = (f'The studio\’s own payroll scorecard rates these {len(pr)} trainers on conversion '
                         f'({conv.min():.0f}% to {conv.max():.0f}%) and retention. Neither column correlates with who actually '
                         f'filled a room this month, and both are used to decide who gets the good slots.')
            except Exception:
                pass
        blocks = [statgrid([('Trainers', _n(len(t))), ('Classes', _n(t['sessions'].sum())),
                            ('Attendances', _n(t['att'].sum())), ('Revenue', R(t['rev'].sum()))]),
                  statgrid([('Best fill', f'{t["fill"].max():.0f}%'), ('Worst fill', f'{t["fill"].min():.0f}%'),
                            ('Empty classes', _n(t['empty'].sum())), ('Late-cancel rate', f'{float(t["lc"].sum() / max(t["book"].sum(), 1)) * 100:.1f}%')])]
        return head('Start here', 'Who taught, what happened, and what the studio can actually learn from it', claim) + ''.join(p + blocks)

    def scorecard():
        p = [para('This is the table the studio should be reading, and the only one that treats a trainer as a production '
                  'resource rather than a personality. Sessions, seats, attendance, revenue and the two numbers that expose '
                  'circumstance: revenue per attendee and the late-cancellation rate of their book.')]
        sc_cols = ['_trainer', 'sessions', 'att', 'seats', 'fill', 'rev', 'rpc', 'rph', 'empty', 'lc_rate', 'fmts', 'hours', 'days']
        sc_df = t.reset_index()
        for c in sc_cols:
            if c not in sc_df.columns:
                sc_df[c] = np.nan
        sc_df = sc_df[sc_cols].copy()
        sc_df['_trainer'] = sc_df['_trainer'].apply(clean)
        b = [tab(sc_df, ['Trainer', 'Classes', 'Attendances', 'Seats', 'Utilisation', 'Revenue', 'Per class',
                         'Per attendee', 'Empty classes', 'Late-cancel rate', 'Formats', 'Hours', 'Days'],
                 ['w', 'n', 'n', 'n', 'p', 'm', 'm', 'm', 'n', 'p', 'n', 'w', 'n'], maxrows=30),
             bars([clean(i) for i in t.sort_values('att', ascending=False).head(12).index],
                  [('Attendances', [float(v) for v in t.sort_values('att', ascending=False).head(12)['att']], A1),
                   ('Classes', [float(v) for v in t.sort_values('att', ascending=False).head(12)['sessions']], B1)],
                  'Who taught what, and who it brought in', h=320, rotate=True,
                  note='Attendances and classes together, so a trainer with a large number of thin classes is visible as such.'),
             bars([clean(i) for i in t.sort_values('fill', ascending=False).index],
                  [('Utilisation %', [float(v) for v in t.sort_values('fill', ascending=False)['fill']], A1)],
                  f'Who filled the room, {lab}', h=340, as_pct=True, rotate=True,
                  ymax=float(t['fill'].max()) * 1.2,
                  note='Sorted by utilisation. Read this against the controlled test below: the order changes when the format is held constant.'),
             hbars([(clean(i), float(v), A2) for i, v in t.sort_values('rph', ascending=False)['rph'].dropna().head(12).items()],
                   'Revenue delivered per attendee, by trainer', unit='₹',
                   note='What a body in the room is worth to the studio, whoever is teaching it. A narrow band here is the argument that the spread above is the slot, not the person.')]
        return sec('The scorecard', f'Every trainer, every class, {lab}', p, b)

    def controlled():
        tf = X.cls.get('tf')
        if tf is None or not len(tf) or tf.empty:
            return ''
        rows = []
        for f_, sub in tf.groupby(level=0):
            sub = sub[sub['n'] >= 4]
            if len(sub) < 3:
                continue
            seats = X.cls['cur'].groupby(['_cls', '_trainer'])['_cap'].sum().reindex(sub.index)
            fill = (sub['att'] / seats * 100).dropna()
            if len(fill) < 3:
                continue
            best_idx = fill.idxmax()
            worst_idx = fill.idxmin()
            best_tr = best_idx[1] if isinstance(best_idx, tuple) else best_idx
            worst_tr = worst_idx[1] if isinstance(worst_idx, tuple) else worst_idx
            rows.append([clean(f_), len(fill), fill.max(), fill.min(), fill.max() - fill.min(),
                         clean(best_tr), clean(worst_tr)])
        if not rows:
            return ''
        rows.sort(key=lambda r: -r[4])
        p = [para('The same format, taught by several people, is the closest thing to a controlled test a studio runs by '
                  f'accident. In {clean(rows[0][0])} {rows[0][1]} trainers filled rooms between {rows[0][2]:.0f}% and '
                  f'{rows[0][3]:.0f}% &mdash; {rows[0][4]:.0f} points apart with the same music, the same length and the same '
                  f'price. Whatever is causing that is trainable.'),
             para('Read the other way, the table also protects trainers: where two people in the same format are within a few '
                  'points of each other, the difference in their headline utilisation is the hour they were given, not the '
                  'class they teach.')]
        tf_ev = tf.reset_index()[['_cls', '_trainer', 'n', 'att', 'rev']].copy()
        tf_ev['_cls'] = tf_ev['_cls'].apply(clean)
        tf_ev['_trainer'] = tf_ev['_trainer'].apply(clean)
        b = [T(['Format', 'Trainers with four or more classes', 'Best fill', 'Worst fill', 'Gap (points)', 'Best', 'Worst'],
               [[r[0], r[1], f'{r[2]:.0f}%', f'{r[3]:.0f}%', f'{r[4]:.0f}', r[5], r[6]] for r in rows], 'num'),
             frame_ev('Evidence &mdash; every trainer by format, with classes, attendance and revenue',
                      tf_ev, ['Format', 'Trainer', 'Classes', 'Attended', 'Revenue'],
                      ['w', 'w', 'n', 'n', 'm'], maxrows=90)]
        return sec('The controlled test', 'Same format, different hands', p, b)

    def yoy():
        if 'sessions_p' not in t or t['sessions_p'].isna().all():
            return ''
        d = t.copy()
        d['dsess'] = d['sessions'] - d['sessions_p'].fillna(0)
        d['drev'] = d['rev'] - d['rev_p'].fillna(0)
        d['datt'] = d['att'] - d['att_p'].fillna(0)
        d = d[(d['sessions'].fillna(0) + d['sessions_p'].fillna(0)) >= 10].sort_values('drev')
        if not len(d):
            return ''
        p = [para(f'Between {yrp(M)} and {lab} the roster changed shape. '
                  f'{int((d["dsess"] < 0).sum())} trainers taught fewer classes and {int((d["dsess"] > 0).sum())} taught more; '
                  f'{R(abs(d.loc[d["drev"] > 0, "drev"].sum()))} of revenue moved to busier hands and '
                  f'{R(abs(d.loc[d["drev"] < 0, "drev"].sum()))} away from quieter ones. '
                  f'{int(d["sessions"].isna().sum())} names are new to this month since last year and '
                  f'{int(d["sessions_p"].isna().sum())} who taught then are not teaching now.'),
             para(f'The largest single movement is {clean(d["drev"].idxmin())} at {R(d.loc[d["drev"].idxmin(), "drev"])}. '
                  f'A year-on-year change in one trainer\’s book is almost never only about that trainer: it is the '
                  f'slots, the format mix and the leave calendar read out through one name, which is exactly why this '
                  f'table is paired with the controlled test above.')]
        yoy_cols = ['_trainer', 'sessions', 'sessions_p', 'att', 'rev', 'rev_p', 'drev']
        yoy_df = d.reset_index()
        for c in yoy_cols:
            if c not in yoy_df.columns:
                yoy_df[c] = np.nan
        yoy_df = yoy_df[yoy_cols].copy()
        yoy_df['_trainer'] = yoy_df['_trainer'].apply(clean)
        b = [diverging([(clean(i), float(v)) for i, v in d['drev'].items()],
                       f'Change in delivered class revenue per trainer, {lab} against {yrp(M)}',
                       note='Read as a shift in the roster rather than a judgement of a person: a trainer given a new format this year shows the whole format as a gain.'),
             tab(yoy_df, ['Trainer', 'Classes this year', 'Classes last year', 'Attended this year',
                          'Revenue this year', 'Revenue last year', 'Change'],
                 ['w', 'n', 'n', 'n', 'm', 'm', 'm'])]
        return sec('What changed in a year', 'The same month, twelve months apart', p, b)

    def week():
        try:
            cur = X.cls['cur']
            g = cur.pivot_table(index='_trainer', columns='_day', values='CheckedIn', aggfunc='sum').reindex(columns=DAYS)
            cnt = cur.pivot_table(index='_trainer', columns='_day', values='SessionID', aggfunc='size').reindex(columns=DAYS)
        except Exception:
            return ''
        p = [para(f'The week belongs to a small number of trainers. '
                  f'{clean(g.sum(axis=1).idxmax())} carries the most attendances ({int(g.sum(axis=1).max())}), and '
                  f'{clean(g.sum(axis=1).nsmallest(1).index[0])} the least ({int(g.sum(axis=1).min())}). '
                  f'{int((cnt.fillna(0) > 0).sum(axis=1).ge(6).sum())} trainers work six or seven days.'),
             para('A roster that puts one person on every good slot is not efficiency; it is a single point of failure and a '
                  'ceiling on how full the studio can get. The hours column in the scorecard shows how narrow the good part '
                  'of the day has become.')]
        rows = [[clean(i)] + [(_n(v) if pd.notna(v) else '·') for v in r] + [_n(r.sum())] for i, r in g.iterrows()]
        b = [stacked([clean(i) for i in g.index][:14],
                     [(str(d_), [float(g.loc[i, d_]) if pd.notna(g.loc[i, d_]) else 0.0 for i in g.index[:14]], c)
                      for d_, c in zip(DAYS, [A1] * 4 + [A2] * 3)],
                     'Attendance by trainer and day of week', h=360,
                     note='Where a trainer has a column and everyone else has a gap, the roster is carrying the studio on one name.') if len(g) else '',
             T(['Trainer'] + DAYS + ['Total attendances'], rows, 'num'),
             frame_ev('Evidence &mdash; classes taught per trainer per day',
                      [[clean(i)] + [(_n(v) if pd.notna(v) else '·') for v in r] + [_n(r.sum())] for i, r in cnt.fillna(0).iterrows()],
                      ['Trainer'] + DAYS + ['Total'], ['w'] + ['n'] * 8)]
        return sec('Where the week actually goes', 'The roster, drawn as a grid', p, b)

    def clients():
        tr = X.nw.get('trainer')
        if tr is None or not len(tr):
            return ''
        p = [para(f'What happens to the people a trainer teaches. Across the studio\’s recorded intake, '
                  f'{clean(tr["conv_pct"].idxmax())} turned {tr.loc[tr["conv_pct"].idxmax(), "conv_pct"]:.0f}% of the first '
                  f'classes they taught into a membership, against {tr["conv_pct"].min():.0f}% for the lowest name with a '
                  f'similar volume. Those are different outcomes from the same product, the same price and the same '
                  f'forty-five minutes.'),
             para('Convert is not the same as liked. The members a high-converting trainer leaves behind arrive with a '
                  'habit already attached, which shows up later as attendance and renewal; a trainer who is liked but books '
                  'nothing produces a warm memory and an empty next month. The two columns should be read together and '
                  'neither should be used alone.')]
        cl_cols = ['Trainer Name', 'first_classes', 'converted', 'conv_pct', 'ltv', 'visits']
        cl_df = tr.reset_index()
        for c in cl_cols:
            if c not in cl_df.columns:
                cl_df[c] = np.nan
        cl_df = cl_df[cl_cols].copy()
        cl_df['Trainer Name'] = cl_df['Trainer Name'].apply(clean)

        lc_cols = ['_trainer', 'sessions', 'book', 'lc', 'lc_rate', 'empty']
        lc_df = t.sort_values('lc_rate', ascending=False).reset_index()
        for c in lc_cols:
            if c not in lc_df.columns:
                lc_df[c] = np.nan
        lc_df = lc_df[lc_cols].copy()
        lc_df['_trainer'] = lc_df['_trainer'].apply(clean)

        b = [tab(cl_df, ['Trainer', 'First classes taught', 'Converted', 'Conversion %', 'Mean LTV', 'Mean visits'],
                 ['w', 'n', 'n', 'p', 'm', 'f1']),
             frame_ev('Evidence &mdash; the late-cancellation rate of each trainer\’s book',
                      lc_df,
                      ['Trainer', 'Classes', 'Booked', 'Late cancelled', 'Late-cancel rate', 'Empty classes'],
                      ['w', 'n', 'n', 'n', 'p', 'n'],
                      blurb='A member who cancels late on a particular trainer\’s class repeatedly is telling the studio something the survey does not capture.')]
        return sec('What happens to the clients', 'First classes, conversions and what the member does next', p, b)

    def own_measure():
        if pr is None or not len(pr):
            return ''
        d = pr.copy()
        for c in ['Conversion Rate', 'Retention Rate', 'Total Sessions', 'Total Empty Sessions', 'Total Customers',
                  'Total Paid', 'New', 'Converted', 'Retained']:
            if c in d:
                d[c] = pd.to_numeric(d[c].astype(str).str.replace('%', '', regex=False), errors='coerce')
        lab_ = getattr(X, 'pr_label', '') or lab
        p = [para(f'The payroll file rates every trainer on conversion and retention for {lab_}. '
                  f'Conversion is recorded between {d["Conversion Rate"].min():.0f}% and {d["Conversion Rate"].max():.0f}%; '
                  f'retention between {d["Retention Rate"].min():.0f}% and {d["Retention Rate"].max():.0f}%. '
                  f'{int((d["Total Empty Sessions"] > 0).sum())} trainers carry at least one empty class in the same file.'),
             para('Two cautions the studio should state out loud when it uses these columns. They are averages over a cycle, '
                  'not a month, so a trainer who joined or left mid-cycle is rated on a fraction of their work. And they '
                  'count what the CRM attributes, which for a studio where most sales arrive at the desk is a small and '
                  'unrepresentative share of what actually happens.')]
        b = [hbars([(clean(r.get('Teacher Name', '')), float(pd.to_numeric(r.get('Conversion Rate'), errors='coerce') or 0), A1)
                    for _, r in d.iterrows()][:14],
                   'Conversion as the studio rates it, by trainer', unit='%',
                   note='The payroll file\u2019s own column, for the cycle it covers. Nothing here has been recomputed from attendance.'),
             T(['Trainer', 'Sessions', 'Empty', 'Customers', 'Paid', 'Converted', 'Conversion %', 'Retained', 'Retention %'],
               [[clean(r.get('Teacher Name', '')), _n(r.get('Total Sessions', 0)), _n(r.get('Total Empty Sessions', 0)),
                 _n(r.get('Total Customers', 0)), R(r.get('Total Paid', 0)), _n(r.get('Converted', 0)),
                 _f(r.get('Conversion Rate', np.nan)), _n(r.get('Retained', 0)), _f(r.get('Retention Rate', np.nan))]
                for _, r in d.iterrows()], 'num')]
        try:
            m = d.merge(t.reset_index().rename(columns={'_trainer': 'Teacher Name'}), on='Teacher Name', how='inner')
            if len(m) >= 4:
                r = np.corrcoef(m['Conversion Rate'].fillna(0), m['fill'].fillna(0))[0, 1]
                b.append(para(f'Where the scorecard and the ledger overlap ({len(m)} trainers), the correlation between the '
                              f'studio\’s conversion rating and the utilisation a trainer actually delivered is '
                              f'<strong>{r:+.2f}</strong>. A coefficient near zero is not an insult to the trainers; it is a '
                              f'warning about the metric.'))
        except Exception:
            pass
        return sec('The studio\’s own measure', 'Conversion and retention as the payroll file records them', p, b)

    def pay():
        if pr is None or not len(pr):
            return ''
        d = pr.copy()
        d['paid'] = pd.to_numeric(d['Total Paid'].astype(str).str.replace(r'[^0-9.]', '', regex=False), errors='coerce')
        d['sess'] = pd.to_numeric(d['Total Sessions'].astype(str), errors='coerce')
        d['cust'] = pd.to_numeric(d['Total Customers'].astype(str), errors='coerce')
        d = d[d['sess'].fillna(0) > 0]
        if not len(d):
            return ''
        d['per_sess'] = d['paid'] / d['sess']
        d['per_att'] = d['paid'] / d['cust'].replace(0, np.nan)
        p = [para(f'Across {len(d)} trainers the studio paid {R(d["paid"].sum())} for {d["sess"].sum():,.0f} sessions and '
                  f'{d["cust"].sum():,.0f} customers &mdash; {R(d["per_sess"].median())} a class at the median and '
                  f'{R(d["per_att"].median())} per customer. Per-session pay is a flat rate; cost per attendance is not, '
                  f'and it ranges {d["per_att"].min():,.0f} to {d["per_att"].max():,.0f}.'),
             para('This is the sentence to put in front of any pay discussion: the studio does not pay for rooms, it pays for '
                  'hours, and the margin per attendance is what decides whether an hour was worth having. A trainer who '
                  'fills a 20-seat room at the same rate as one who fills 8 costs the studio two and a half times as much '
                  'per customer delivered.')]
        b = [tab(d.reset_index()[['Teacher Name', 'sess', 'cust', 'paid', 'per_sess', 'per_att']],
                 ['Trainer', 'Sessions', 'Customers', 'Paid out', 'Per session', 'Per customer'],
                 ['w', 'n', 'n', 'm', 'm', 'm'], 'num'),
             hbars([(clean(i_), float(v_), (B1 if float(v_) > float(d['per_att'].median()) else A1))
                    for i_, v_ in d.sort_values('per_att', ascending=False)[['Teacher Name', 'per_att']].dropna().head(14).itertuples(index=False)],
                   'What the studio pays for one customer, by trainer', unit='₹',
                   note='Accent bars are at or below the studio median; the second colour marks the expensive half of the roster.')]
        return sec('What the studio pays for a session', 'Payroll against attendance', p, b)

    def first_class():
        tr = X.nw.get('trainer')
        if tr is None or not len(tr):
            return ''
        p = [para(f'First classes are not distributed at random. {clean(tr["first_classes"].idxmax())} taught the most of them '
                  f'({int(tr["first_classes"].max())}); {clean(tr["conv_pct"].idxmax())} converts them best at '
                  f'{tr["conv_pct"].max():.0f}%. If the studio does not choose who teaches a first class, the timetable '
                  f'chooses by default, and it chooses whoever is rostered at 07:00.'),
             para(f'The arithmetic is worth putting on one line: moving every first class to the trainers in the top '
                  f'conversion quartile, holding volume constant, is worth roughly '
                  f'{abs(float(tr["conv_pct"].quantile(.75) - tr["conv_pct"].median())):.0f} percentage points of conversion '
                  f'on {int(tr["first_classes"].sum()):,} first classes a year, before any marketing spend changes.')]
        fc_cols = ['Trainer Name', 'first_classes', 'converted', 'conv_pct', 'ltv']
        fc_df = tr.reset_index()
        for c in fc_cols:
            if c not in fc_df.columns:
                fc_df[c] = np.nan
        fc_df = fc_df[fc_cols].copy()
        fc_df['Trainer Name'] = fc_df['Trainer Name'].apply(clean)

        fc_ev_cols = ['Trainer Name', 'first_classes', 'converted', 'conv_pct', 'visits']
        fc_ev = tr.sort_values('first_classes', ascending=False).reset_index()
        for c in fc_ev_cols:
            if c not in fc_ev.columns:
                fc_ev[c] = np.nan
        fc_ev = fc_ev[fc_ev_cols].copy()
        fc_ev['Trainer Name'] = fc_ev['Trainer Name'].apply(clean)

        b = [tab(fc_df, ['Trainer', 'First classes taught', 'Converted', 'Conversion %', 'Mean LTV of their converts'],
                 ['w', 'n', 'n', 'p', 'm']),
             frame_ev('Evidence &mdash; who taught the first class, and what became of it',
                      fc_ev,
                      ['Trainer', 'First classes', 'Converted', 'Conversion %', 'Mean visits after'],
                      ['w', 'n', 'n', 'p', 'f1'],
                      blurb='Trainers with at least ten recorded first classes. Newcomers on a 2-for-1 intro pack are counted as converted only when the membership followed.')]
        return sec('Whose first class becomes a member', 'The single highest-leverage slot in the timetable', p, b)

    def individual():
        lines_ = []
        for name, r in t.sort_values('att', ascending=False).iterrows():
            try:
                bits = [f'{int(r["sessions"])} classes', f'{int(r["att"])} attendances',
                        f'{r["fill"]:.0f}% of the seats offered']
                if pd.notna(r.get('rpc')):
                    bits.append(f'{R(r["rpc"])} a class')
                if pd.notna(r.get('rph')):
                    bits.append(f'{R(r["rph"])} per body in the room')
                if r.get('empty', 0) and int(r['empty']) > 0:
                    bits.append(f'{int(r["empty"])} class{"" if int(r["empty"]) == 1 else "es"} to an empty room')
                if pd.notna(r.get('lc_rate')):
                    bits.append(f'{r["lc_rate"]:.1f}% of the bookings on this name were late-cancelled')
                if pd.notna(r.get('sessions_p')) and r['sessions_p'] > 0:
                    d = (r['sessions'] - r['sessions_p']) / r['sessions_p'] * 100
                    bits.append(f'{d:+.0f}% on {mon.lower()} last year')
                fmts = clean(r.get('fmtlist', '') or '')[:74]
                lines_.append(f'<h3>{clean(name)}</h3><p>' + '; '.join(bits) + f'. Taught across {int(r.get("fmts", 0))} '
                              f'formats ({fmts}), working {r.get("hours", "the whole day")}, on '
                              f'{int(r.get("days", 0))} days of the week.</p>')
            except Exception:
                continue
        if not lines_:
            return ''
        p = [para('The roster read one name at a time, because a table of fourteen rows is not the same as fourteen '
                  'sentences, and the differences between these people are the only thing in this chapter a studio can '
                  'actually act on. Each entry is measured the same way: what was scheduled, what arrived, what it earned, '
                  'and what happened to the bookings on that name.')]
        b = [''.join(lines_)]
        return sec('The roster, name by name', f'Every trainer who taught a class in {lab}', p, b)

    def causes():
        items = [('part', 'It is the slot, not the trainer',
                  f'The utilisation spread is {ratio(t["fill"].max(), t["fill"].min())} times, but revenue per attendee '
                  f'spreads only {ratio(t["rph"].dropna().max(), t["rph"].dropna().min())} times. Most of the headline '
                  f'difference is capacity and hour.',
                  'Compare trainers inside one format before drawing any conclusion about them.'),
                 ('yes', 'Volume is not quality',
                  f'{clean(t["sessions"].idxmax())} taught the most classes ({int(t["sessions"].max())}); '
                  f'{clean(t["rph"].idxmax())} earns the most per person in the room ({R(t["rph"].max())}).',
                  'Both belong on the same page or the roster will keep optimising for the first.'),
                 ('no', 'Ratings predict attendance',
                  'Where the payroll scorecard and the ledger overlap, the conversion rating and the delivered utilisation '
                  'tell separate stories.', 'Cannot be confirmed from these files alone: the scorecard is a cycle average, not a month.'),
                 ('part', 'New trainers are worse',
                  f'{int((t.get("sessions_p", pd.Series(dtype=float)).isna()).sum())} trainers teaching this month were not '
                  f'teaching in {yrp(M)}. Their utilisation sits inside the same band as the rest.',
                  'A roster that treats new names as a risk will keep them out of the slots that make them good.')]
        return sec('What else could explain it', 'Reading a trainer table honestly', [para('Every conclusion in this chapter is a claim about a person, so each of them has to survive an alternative explanation.')], [hyp(items)])

    body = run([start, scorecard, controlled, individual, yoy, week, clients, own_measure, pay, first_class, causes])
    defs = [('Trainer', 'the Trainer column of the sessions export, trimmed and matched case-insensitively to the payroll file.'),
            ('Utilisation', 'check-ins against the capacity configured for that class, not against who booked it.'),
            ('Revenue', 'the Revenue column on the session row: the value of classes delivered, not cash taken.'),
            ('First class', 'a member\’s first recorded visit at this studio in the member file, attributed to the trainer named against that visit.'),
            ('Payroll figures', 'the total paid for the cycle the file reports, with per-session and per-attendance rates derived from it.')]
    caut = [('A trainer\’s utilisation is a function of the slots they were given. Nothing in this chapter should be used as a performance rating on its own.'),
            ('The payroll export is reported by cycle, not by calendar month; where it does not cover the review month the latest cycle on file is used and labelled as such.'),
            ('Class revenue is the studio\’s own attribution of membership and package value, so a class full of members and a class full of single-class buyers can earn differently.'),
            ('Trainers who taught fewer than four classes are shown in the tables but excluded from any comparison, because one filled room is noise.')]
    body += appendix(M, X, 'instructor')
    body += method(M, defs, caut)
    kpis = [kpi('Trainers', _n(len(t)), f'{int(t["sessions"].sum())} classes'),
            kpi('Utilisation spread', f'{ratio(t["fill"].max(), t["fill"].min())}×', f'{t["fill"].min():.0f}% to {t["fill"].max():.0f}%', 'neg'),
            kpi('Revenue per attendee', R(float(t['rev'].sum() / max(t['att'].sum(), 1))), 'flat, whatever the room size'),
            kpi('Empty classes', _n(t['empty'].sum()), f'{float(t["empty"].sum() / max(t["sessions"].sum(), 1)) * 100:.1f}% of all classes', 'neg')]
    facts = [f'{len(t)} trainers taught {int(t["sessions"].sum())} classes and filled {t["att"].sum():,.0f} seats for {R(t["rev"].sum())} in {lab}.',
             f'Utilisation spread {ratio(t["fill"].max(), t["fill"].min())} times, but revenue per attendee only {ratio(t["rph"].dropna().max(), t["rph"].dropna().min())} times - most of the gap is the slot.',
             f'{t["empty"].sum():.0f} classes ran to nobody; {float(t["lc"].sum() / max(t["book"].sum(), 1)) * 100:.1f}% of their booked seats were late-cancelled.']
    ch = dict(id='instructor', n=3, title='Instructor Performance', body=body, kpis=kpis, facts=facts,
              subtitle=f'{len(t)} trainers, {ratio(t["fill"].max(), t["fill"].min())} times utilisation spread')
    ch['recs_extra'] = recs_instructor(M, X)
    return ch


def recs_instructor(M, X):
    t = X.tr
    out = []
    try:
        w = t['fill'].idxmin()
        out.append((f'Give {clean(w)} the slots that already work', 'Studio Manager',
                    f'{clean(w)} fills {t.loc[w, "fill"]:.1f}% of {int(t.loc[w, "sessions"])} classes, the lowest on the '
                    f'roster, at {R(t.loc[w, "rph"])} of revenue per attendee.',
                    'Re-timing rather than removing is the change: the same hands in a better hour usually closes half the gap without a single class being cut.'))
    except Exception:
        pass
    try:
        b = t['rph'].idxmax()
        out.append(('Pay for attendance, not for the size of the room', 'Studio Manager + Finance',
                    f'{clean(b)} delivers {R(t.loc[b, "rph"])} of class revenue per attendee against a roster average of '
                    f'{R(float(t["rev"].sum() / max(t["att"].sum(), 1)))}. Cost per attendance, not per class, is what decides '
                    f'whether an hour was worth having.',
                    'A rate anchored to attendance aligns the trainer, the timetable and the P&L on the same number and ends the incentive to fill a big room badly.'))
    except Exception:
        pass
    try:
        tr = X.nw.get('trainer')
        if tr is not None and len(tr) > 3:
            out.append(('Assign first classes deliberately, by conversion', 'Programming + Sales',
                        f'Conversion from a first class ranges from {tr["conv_pct"].min():.0f}% to {tr["conv_pct"].max():.0f}% '
                        f'across {int(tr["first_classes"].sum()):,} recorded first classes.',
                        'This is the cheapest conversion growth available: no new leads, no price change, only a decision about who stands in front of a newcomer.'))
    except Exception:
        pass
    try:
        pr = X.prscore
        if pr is not None and len(pr):
            out.append(('Stop separating trainer assessment from the ledger', 'Studio Manager',
                        'The payroll scorecard rates trainers on conversion and retention over a cycle; this chapter measures '
                        'what they actually delivered, class by class. The two currently do not inform each other.',
                        'One page a month that shows both, side by side, turns an opinion about a trainer into an argument with evidence.'))
    except Exception:
        pass
    try:
        e = t[t['empty'] > 0]
        if len(e):
            out.append(('Review the slots nobody attended, with the trainer in the room', 'Programming',
                        f'{int(t["empty"].sum())} classes ran to nobody, and {len(e)} trainers carry at least one of them.',
                        'An empty class is usually an hour rather than a person; the review should decide which one it found before anyone is reassigned.'))
    except Exception:
        pass
    return out
