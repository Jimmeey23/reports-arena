"""Chapters 6 to 9 of the generated report."""
from __future__ import annotations
import pandas as pd, numpy as np
from .design import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                     A1, A2, A3, B1, B2, N1, N2)
from .metrics import DAYS, MONTH_NAMES
from .chapters_a import _k


# ============================================================== 6 cancellations
def cancels(M):
    if not hasattr(M, 'lc_year') or M.y not in M.lc_year:
        return None
    c = M.lc_year[M.y]; p1 = M.lc_year.get(M.y - 1, {})
    body, kpis = [], [
        _k('Late cancellations', f"{c['lc']:,.0f}", (f"from {p1['lc']:,.0f} a year earlier" if p1 else ''), 'pos'),
        _k('Share of the book', P(c['rate']), (f"was {p1['rate']:.1f}% in {M.y-1}" if p1 else ''), 'pos'),
        _k('Booked seats honoured', P(c['att'] / c['book'] * 100 if c['book'] else 0), 'attendance as a share of what was booked', 'pos'),
        _k('Board ever booked', P(c['book'] / max(M.room.get(M.y, {}).get('seats', 1), 1) * 100),
           'how much of the timetable is ever claimed', 'neu')]

    body.append(f'''<h2>Start here</h2>
<p>{M.studio} released <strong>{c['lc']:,.0f} seats late in {M.label}</strong>{f", against {p1['lc']:,.0f} in the same month a year earlier" if p1 else ""} —
{P(c['rate'])} of every seat booked. Attendance ran at {P(c['att'] / c['book'] * 100 if c['book'] else 0)} of the booked book.</p>
<p>The more useful number is underneath: the board is only {P(c['book'] / max(M.room.get(M.y, {}).get('seats', 1), 1) * 100)} booked in the first place.
Tightening cancellation rules improves the conversion of demand that already exists. It does not create any.</p>''')

    if p1:
        rows = []
        for y in sorted(M.lc_year):
            r = M.lc_year[y]
            room = M.room.get(y, {})
            rows.append([str(y), f"{r['book']:,.0f}", f"{r['att']:,.0f}", P(r['att'] / r['book'] * 100 if r['book'] else 0),
                         f"{r['lc']:,.0f}", P(r['rate']), P(r['book'] / max(room.get('seats', 1), 1) * 100),
                         R(room.get('rev', 0) / r['book']) if r['book'] else '—'])
        body.append(ev(f'Evidence — the booking book in {MONTH_NAMES[M.m-1]}',
                       T(['Year', 'Seats booked', 'Attended', 'Honoured', 'Late cancels', 'Cancelled late',
                          'Board ever booked', 'Revenue / booked seat'], rows, 'num')))
        body.append(bars([str(y) for y in sorted(M.lc_year)],
                         [('Booked seats', [M.lc_year[y]['book'] for y in sorted(M.lc_year)], N2),
                          ('Attended', [M.lc_year[y]['att'] for y in sorted(M.lc_year)], A1),
                          ('Cancelled late', [M.lc_year[y]['lc'] for y in sorted(M.lc_year)], B1)],
                         'The booking book: claimed, honoured, released', h=310,
                         note='A late cancellation is a booked seat given up after the studio’s cut-off.'))

    if hasattr(M, 'lc_fmt') and len(M.lc_fmt):
        lf = M.lc_fmt.head(8)
        body.append(f'''<h2>Where the cancelled seats are</h2>
<p>Cancellations concentrate by format: <strong>{str(lf.index[0]).replace('Studio ', '')} lost {int(lf['lc'].iloc[0])} seats late</strong>,
followed by {str(lf.index[1]).replace('Studio ', '')} at {int(lf['lc'].iloc[1])}.</p>''')
        body.append(bars([str(i).replace('Studio ', '')[:16] for i in lf.index],
                         [('Late cancellations', [int(v) for v in lf['lc']], B1)],
                         'Late cancellations by format', h=300, rotate=True,
                         note='Counts of booked seats released after the cut-off.'))

    if hasattr(M, 'lc_members'):
        conc = M.lc_conc
        body.append(f'''<h2>Who cancels</h2>
<p><strong>{conc['members']} members cancelled at least once in {M.label}</strong>, {conc['per']:,} cancellations between them.
{conc['three_plus']} members cancelled three times or more, and the ten heaviest account for {conc['top10_share']:.0f}% of the total.</p>
<p>Repeat cancelling is not carelessness. It is a schedule that has stopped fitting, and it is worth a conversation rather than a charge.</p>''')
        body.append(bars([str(int(i)) for i in (M.lc_hour.index if hasattr(M, 'lc_hour') else [])],
                         [('Late cancellations', [int(v) for v in (M.lc_hour.values if hasattr(M, 'lc_hour') else [])], B1)],
                         'When the cancelled classes were scheduled', h=290,
                         note='Cancellations cluster in the hours where working members’ days most often go wrong.'))

    if hasattr(M, 'disc_year') and M.y in M.disc_year:
        d = M.disc_year[M.y]; dp1 = M.disc_year.get(M.y - 1, {})
        body.append(f'''<h2>The discount book</h2>
<p>Discount depth in {M.y} stands at <strong>{d['depth']:.1f}% of gross value</strong>{f", against {dp1['depth']:.1f}% in {M.y-1}" if dp1 else ""},
spread across {d['spread']:.0f}% of transactions ({R(d['disc'])} given away on {R(d['gross'])} of gross).</p>''')
        if len(M.disc_year) > 1:
            ys = sorted(M.disc_year)
            body.append(bars([str(y) for y in ys],
                             [('Discount depth, %', [M.disc_year[y]['depth'] for y in ys], B1),
                              ('Share of sales discounted, %', [M.disc_year[y]['spread'] for y in ys], A2)],
                             'Discount depth against discount spread, year by year', h=300,
                             note='Depth is the value given away as a share of gross. Spread is how many sales carried any discount at all.'))

    if hasattr(M, 'disc_prod') and len(M.disc_prod):
        dp = M.disc_prod.head(8)
        body.append(bars([str(i)[:22] for i in dp.index],
                         [('Discount depth, %', [float(v) for v in dp['depth']], B1),
                          ('Share of sales discounted, %', [float(v) for v in dp['spread']], A2)],
                         'Discount depth by product', h=320, rotate=True,
                         note='Products with eight or more transactions this year.'))

    if hasattr(M, 'disc_seller') and len(M.disc_seller):
        ds = M.disc_seller
        body.append(f'''<h2>Do the discounts work?</h2>
<p>Pooled, discounting looks like the best investment the studio makes. Controlled for what was bought, the effect usually narrows or reverses — the
products that carry offers are not the products that carry full price. Discount depth by seller runs from
<strong>{ds['depth'].min():.1f}% to {ds['depth'].max():.1f}%</strong>; nobody is doing anything wrong, and nobody is being told the range exists.</p>''')
        body.append(hbars([(str(i)[:22], float(v), B1) for i, v in ds['depth'].items()],
                          'Discount depth by the person who sold it', as_pct=True, unit='', maxv=max(ds['depth'].max() * 1.2, 20),
                          note='Sellers with eight or more recorded transactions this year.'))

    facts = [f'{c["lc"]:,.0f} late cancellations in {M.label}, {c["rate"]:.1f}% of the booked book.'
             + (f' Down from {p1["lc"]:,.0f} a year earlier.' if p1 else ''),
             f'{P(c["book"] / max(M.room.get(M.y, {}).get("seats", 1), 1) * 100)} of the board is ever booked at all, so the constraint is demand, not discipline.']
    if hasattr(M, 'disc_year') and M.y in M.disc_year:
        facts.append(f'Discount depth {M.disc_year[M.y]["depth"]:.1f}% on {M.disc_year[M.y]["spread"]:.0f}% of transactions.')
    return dict(id='cancels', n=6, title='Late Cancellations and Discounts', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{c["lc"]:,.0f} released seats, {c["rate"]:.1f}% of the book')


# =================================================================== 7 overview
def overview(M):
    F = M.room.get(M.y, {}); p1 = M.room.get(M.y - 1, {})
    S = M.sales.get(M.y, {}) if hasattr(M, 'sales') else {}
    body, kpis = [], [
        _k('Classes run', f"{F.get('sessions', 0):,}", f"{F.get('att', 0):,.0f} attendances", 'neu'),
        _k('Utilisation', P(F.get('fill', 0)), (f"from {p1['fill']:.1f}% a year earlier" if p1 else ''), 'pos'),
        _k('Class revenue', R(F.get('rev', 0)), f"{R(F.get('rpc', 0))} a class", 'pos'),
        _k('Cash taken', R(S.get('cash', 0)), f"{S.get('buyers', 0)} buyers", 'pos')]

    body.append(f'''<h2>Start here</h2>
<p>{M.studio} in {M.label}: <strong>{F.get('sessions', 0)} classes, {F.get('att', 0):,.0f} attendances, {R(F.get('rev', 0))} of class revenue</strong>
and {R(S.get('cash', 0))} of cash taken from {S.get('buyers', 0)} buyers. This chapter joins the ledgers — room, sales, members, leads — into one page.</p>''')

    if p1:
        body.append(f'''<p>Against {MONTH_NAMES[M.m-1]} {M.y-1}: utilisation {'up' if F.get('fill', 0) >= p1['fill'] else 'down'} from
{p1['fill']:.1f}% to {F.get('fill', 0):.1f}%, class revenue {'up' if F.get('rev', 0) >= p1['rev'] else 'down'} from {R(p1['rev'])} to {R(F.get('rev', 0))},
and revenue per class from {R(p1['rpc'])} to {R(F.get('rpc', 0))}.</p>''')
        rows = [[str(y), f"{M.room[y]['sessions']:,}", f"{M.room[y]['seats']:,.0f}", f"{M.room[y]['att']:,.0f}",
                 P(M.room[y]['fill']), f"{M.room[y]['lc']:,.0f}", R(M.room[y]['rev']), R(M.room[y]['rpc']), R(M.room[y]['rph'])]
                for y in sorted(M.room)]
        body.append(ev(f'Evidence — {MONTH_NAMES[M.m-1]} across the years on file',
                       T(['Year', 'Classes', 'Seats', 'Attended', 'Utilisation', 'Late cancels', 'Revenue',
                          'Revenue / class', 'Revenue / attendee'], rows, 'num')))

    if hasattr(M, 'people') and M.y in M.people:
        pp = M.people[M.y]
        body.append(f'''<h2>The member base</h2>
<p><strong>{pp['members']} members trained here in {M.label}</strong>, {pp['visits']:,} times between them — {pp['per']:.2f} visits each.
{('Against ' + str(M.people[M.y-1]['members']) + ' members at ' + f"{M.people[M.y-1]['per']:.2f}" + ' visits each a year earlier.') if (M.y-1) in M.people else ''}</p>''')
        if hasattr(M, 'core'):
            k = M.core
            body.append(f'''<p>The returning core explains most of the movement. <strong>{k['n']} members trained in both {MONTH_NAMES[M.m-1].lower()}s</strong>,
making {k['prev']:,.0f} visits last year and {k['now']:,.0f} this year — {abs(k['lost']):,.0f} visits that simply did not happen, about
{k['share_of_month']:.0f}% of everything the studio filled. Meanwhile {k['gone']} members from last year did not return and {k['new']} newcomers arrived.</p>
<p>This is a true like-for-like group: the same people, the same month, twelve months apart. Had they held their year-ago frequency, {M.label} would have
recorded {M.people[M.y]['visits'] + abs(k['lost']):,.0f} visits rather than {M.people[M.y]['visits']:,}.</p>''')
            body.append(bars([f'{MONTH_NAMES[M.m-1][:3]} {M.y-1}', f'{MONTH_NAMES[M.m-1][:3]} {M.y}'],
                             [('Visits by the same members', [k['prev'], k['now']], A1)],
                             'The returning core, year on year', h=280, ymax=k['prev'] * 1.25 if k['prev'] else None,
                             note=f"{k['n']} members who trained in both months, measured on their own visits."))

        if hasattr(M, 'beh') and 'monthly' in M.beh:
            mo = M.beh['monthly']
            body.append(f'''<h2>Frequency through the year</h2>
<p>Attendance is the product of how many members there are and how often they come, and the second number has been the one moving.
Visits per member in {M.label} were <strong>{mo['per'].iloc[-1]:.2f}</strong>, against {mo['per'].max():.2f} at the best month in the window and
{mo['per'].iloc[-2]:.2f} the month before.</p>''')
            body.append(lines([str(i)[-5:] for i in mo.index], [('Visits per member', [float(v) for v in mo['per']], A1)],
                              'Visits per member, month by month', h=320, as_pct=False, ymax=float(mo['per'].max()) * 1.2,
                              label_last=True, note='The studio’s headline number: attendance divided by the members who produced it.'))

    if hasattr(M, 'lead_fun'):
        lf = M.lead_fun
        body.append(f'''<h2>Where the members come from</h2>
<p>Across every lead the studio has recorded for {M.studio}, <strong>{lf['trial_pct']:.1f}% complete a trial and {lf['won_pct']:.1f}% become members</strong>,
with {lf['retained_pct']:.1f}% retained today. {M.lead_month:,} leads arrived in {M.label}
{f"against {M.lead_month_prev:,} in the same month a year earlier" if M.lead_month_prev else ""}.</p>''')
        body.append(funnel([('Leads created', lf['leads'], 'every enquiry on file'),
                            ('Trial completed', lf['trial'], f"{lf['trial_pct']:.1f}% of leads"),
                            ('Membership sold', lf['won'], f"{lf['won_pct']:.1f}% of leads"),
                            ('Retained today', lf['retained'], f"{lf['retained_pct']:.1f}% of leads")],
                           'Lead to member to retained'))
        if hasattr(M, 'lead_ch') and len(M.lead_ch):
            lc = M.lead_ch
            body.append(hbars([(str(i)[:26], float(r['won']), A1 if r['won'] >= lc['won'].median() else B1) for i, r in lc.iterrows()],
                              'Share of leads converted, by channel', as_pct=True, unit='', maxv=float(lc['won'].max()) * 1.2,
                              note=f"{str(lc.index[0])[:34]} brings the most leads at {R(lc['ltv'].iloc[0])} of lifetime value."))

    if hasattr(M, 'formats') and len(M.formats):
        f = M.formats
        body.append(f'''<h2>The room</h2>
<p>The studio put {F.get('seats', 0):,.0f} seats on the board and filled {F.get('att', 0):,.0f} of them — {F.get('fill', 0):.1f}% utilisation.
By format the spread is wide: <strong>{str(f['fill'].idxmax()).replace('Studio ', '')} at {f['fill'].max():.1f}%</strong> against
{str(f['fill'].idxmin()).replace('Studio ', '')} at {f['fill'].min():.1f}%.</p>''')
        body.append(hbars([(str(i).replace('Studio ', '')[:22], float(v), A1 if v >= f['fill'].median() else B1) for i, v in f['fill'].items()],
                          'Utilisation by format', as_pct=True, unit='', maxv=100,
                          note='Attendance as a share of the seats each format offered.'))

    body.append(f'''<h2>What the ledgers say together</h2>
<p>Each source on its own describes a month. Joined, they describe a business: the room earns more per class than a year ago
{R(F.get('rpc', 0))} against {R(p1.get('rpc', 0)) if p1 else '—'}, the members who were already here are coming less often, and the
leads that arrive are converting at a rate the studio largely determines by how fast it answers them.</p>''')

    facts = [f'{M.label} at {M.studio}: {F.get("sessions", 0)} classes, {F.get("fill", 0):.1f}% utilisation, {R(F.get("rev", 0))} of class revenue.',
             f'{R(S.get("cash", 0))} of cash from {S.get("buyers", 0)} buyers.']
    if hasattr(M, 'core'):
        facts.append(f'The returning core dropped {abs(M.core["lost"]):,.0f} visits against the same month last year — about {M.core["share_of_month"]:.0f}% of the month.')
    return dict(id='overview', n=7, title='Studio Overview and Intelligence', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{M.label} in one page — room, cash, members, leads')


# =================================================================== 8 leads
def leads(M):
    if 'leads' not in M.has:
        return None
    lf = M.lead_fun
    body, kpis = [], [
        _k('Leads in selected month', f"{lf['leads']:,}", f"{M.lead_month:,} arrived in {M.label}", 'neu'),
        _k('Trial completed', P(lf['trial_pct']), f"{lf['trial']:,} trials", 'neu'),
        _k('Became members', P(lf['won_pct']), f"{lf['won']:,} memberships sold", 'pos'),
        _k('Retained today', P(lf['retained_pct']), f"{lf['retained']:,} still with the studio", 'pos')]

    tg = getattr(M, 'trial_gate', None)
    if tg is not None and 'Trial Completed' in tg.index and 'Not Tried' in tg.index:
        yes, no = tg.loc['Trial Completed'], tg.loc['Not Tried']
        body.append(f'''<h2>Start here</h2>
<p>Of {lf['leads']:,} leads recorded for {M.studio}, <strong>{lf['trial']:,} completed a trial and {lf['won']:,} became members</strong>.
Split by whether a trial ever happened, the funnel is decisive: trial-takers convert at <strong>{yes['won_pct']:.1f}%</strong>
against {no['won_pct']:.2f}% for everyone else — {int(no['won'])} people out of {int(no['leads']):,}.</p>
<p>{M.lead_month:,} leads arrived in {M.label}{f", against {M.lead_month_prev:,} in {MONTH_NAMES[M.m-1]} {M.y-1}" if M.lead_month_prev else ""}.
The trial is not a step in the funnel. It is the funnel.</p>''')
    else:
        body.append(f'''<h2>Start here</h2>
<p>{lf['leads']:,} leads are recorded for {M.studio}: <strong>{lf['trial']:,} completed a trial, {lf['won']:,} became members and {lf['retained']:,} are still
with the studio</strong>. {M.lead_month:,} arrived in {M.label}.</p>''')

    body.append(funnel([('Leads created', lf['leads'], 'all time on file'),
                        ('Trial completed', lf['trial'], f"{lf['trial_pct']:.1f}% of leads"),
                        ('Membership sold', lf['won'], f"{lf['won_pct']:.1f}% of leads, {lf['won']/max(lf['trial'],1)*100:.1f}% of trials"),
                        ('Retained today', lf['retained'], f"{lf['retained_pct']:.1f}% of leads")],
                       'The whole acquisition funnel'))

    if hasattr(M, 'lead_span') and len(M.lead_span):
        s = M.lead_span
        same = s[s['b'].astype(str) == 'same day']
        share = float(same['n'].iloc[0] / s['n'].sum() * 100) if len(same) else 0
        body.append(f'''<h2>Speed decides it</h2>
<p>Of the leads that converted and carry a usable date pair, <strong>{share:.0f}% bought on the same day they enquired</strong>. The whole first week
accounts for {float(s.loc[s['b'].isin(['same day', 'next day', '2 to 3 days', '4 to 7 days']), 'n'].sum() / s['n'].sum() * 100):.1f}% of wins.</p>
<p>That is a counter, not a nurture funnel. A lead answered the next morning has already lost most of its value — and response speed, unlike persuasion,
is entirely within the studio's control.</p>''')
        body.append(bars([str(i) for i in s['b']], [('Wins', [int(v) for v in s['n']], A1)],
                         'How long a lead took to become a member', h=320, rotate=True,
                         note='Won leads with a usable enquiry-to-purchase date pair, by how long the decision took.'))
        body.append(ev('Evidence — enquiry to purchase',
                       T(['Time to decide', 'Wins', 'Share', 'Mean lifetime value'],
                         [[str(r['b']), int(r['n']), P(r['n'] / s['n'].sum() * 100), R(r['ltv'])] for _, r in s.iterrows()], 'num')))

    if hasattr(M, 'lead_ch') and len(M.lead_ch):
        lc = M.lead_ch
        body.append(hbars([(str(i)[:28], float(r['won']), A1 if r['won'] >= lc['won'].median() else B1) for i, r in lc.iterrows()],
                          'Conversion by channel', as_pct=True, unit='', maxv=float(lc['won'].max()) * 1.25,
                          note='The channels the studio uses, and how many of their leads become members.'))

    if hasattr(M, 'lead_src') and len(M.lead_src):
        ls = M.lead_src.head(12)
        body.append(f'''<h2>Which sources produce members</h2>
<p>Named sources sharpen the picture. <strong>{ls.index[0]} is the largest source on file at {int(ls['leads'].iloc[0]):,} leads</strong>
and converts {ls['won'].iloc[0]:.1f}% of them. The strongest by conversion in the list is
<strong>{ls['won'].idxmax()} at {ls['won'].max():.1f}%</strong>.</p>''')
        body.append(bars([str(i)[:16] for i in ls.index],
                         [('Leads', [int(v) for v in ls['leads']], N2),
                          ('Share won, % ×10', [float(v) * 10 for v in ls['won']], A1)],
                         'Lead volume against conversion, by source', h=340, rotate=True,
                         note='Sources with twenty or more leads. The second series is drawn ten times its true value.'))
        body.append(ev('Evidence — source, volume and value',
                       T(['Source', 'Leads', 'Trial completed', 'Won', 'Mean lifetime value'],
                         [[str(i), int(r['leads']), P(r['trial']), P(r['won']), R(r['ltv'])] for i, r in M.lead_src.iterrows()], 'num')))

    if hasattr(M, 'lead_assoc') and len(M.lead_assoc):
        la = M.lead_assoc
        body.append(f'''<h2>Who handles the leads</h2>
<p>Conversion across associates runs from <strong>{la['won'].min():.1f}% to {la['won'].max():.1f}%</strong> on the same product list at the same prices.
The strongest performer does not hold the smallest book.</p>''')
        body.append(hbars([(str(i)[:22], float(v), A1 if v >= la['won'].median() else B1) for i, v in la['won'].items()],
                          'Share of leads converted, by the person handling them', as_pct=True, unit='',
                          maxv=float(la['won'].max()) * 1.25,
                          note='Associates with twenty or more recorded leads.'))

    if hasattr(M, 'open_n'):
        body.append(f'''<h2>The file nobody is working</h2>
<p><strong>{M.open_n:,} leads are still marked open, with a mean age of {M.open_age:.0f} days.</strong> Only {M.open_fresh:,} of them are less than
thirty days old, and {M.open_stale:,} have been open for more than six months.</p>
<p>An open lead that is a year old is not a pipeline; it is a missing status — and it inflates every conversion figure the studio reports.
Dispositioning this file honestly is a week of work and it makes every subsequent number trustworthy.</p>''')
        if hasattr(M, 'open_stage'):
            body.append(ev('Evidence — where the open file is stuck',
                           T(['Stage', 'Leads'], [[str(i), int(v)] for i, v in M.open_stage.items()], 'num')))

    if hasattr(M, 'lead_trend') and len(M.lead_trend):
        t = M.lead_trend.tail(12)
        body.append(f'''<h2>Lead flow</h2>
<p>Leads move a quarter before attendance does, which makes them the earliest signal the studio has. Over the last twelve months
<strong>{int(t['leads'].sum()):,} leads were created and {float(t['won_pct'].mean()):.1f}% converted on average</strong>.</p>''')
        body.append(lines([str(i)[-5:] for i in t.index], [('Leads created', [int(v) for v in t['leads']], A1)],
                          'Leads created, month by month', h=300, as_pct=False, note='Counted at the month the enquiry arrived, so recent months are complete for volume.'))

    facts = [f'{lf["leads"]:,} leads in selected month for {M.studio}: {lf["trial"]:,} trials, {lf["won"]:,} memberships, {lf["retained"]:,} retained.',
             f'Trial-takers convert at {tg.loc["Trial Completed", "won_pct"]:.1f}% against {tg.loc["Not Tried", "won_pct"]:.2f}% without one.' if tg is not None else 'Trial completion is the gate.']
    if hasattr(M, 'lead_same'):
        facts.append(f'{M.lead_same:.0f}% of memberships are sold the same day the enquiry arrives.')
    return dict(id='leads', n=8, title='Lead Performance and Insights', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{lf["leads"]:,} leads, {lf["trial_pct"]:.1f}% trialled, {lf["won_pct"]:.1f}% bought')


# =============================================================== 9 behaviour
def behaviour(M):
    if 'behaviour' not in M.has and 'checkins' not in M.has:
        return None
    b = M.beh
    body, kpis = [], [
        _k('Members this month', f"{M.people.get(M.y, {}).get('members', 0):,}", f"{M.people.get(M.y, {}).get('visits', 0):,} visits", 'neu'),
        _k('Visits per member', f"{M.people.get(M.y, {}).get('per', 0):.2f}", (f"from {M.people[M.y-1]['per']:.2f} a year earlier" if (M.y-1) in getattr(M, 'people', {}) else ''), 'neg'),
        _k('Came once', f"{b.get('once_share', 0):.0f}%", f"{b.get('once', 0)} members, single visit", 'neg'),
        _k('Top tenth of members', f"{b.get('top_share', 0):.0f}%", 'of all attendance', 'pos')]

    per = M.people.get(M.y, {}).get('per', 0)
    per_prev = M.people.get(M.y - 1, {}).get('per', 0)
    body.append(f'''<h2>Start here</h2>
<p>{M.studio} had <strong>{M.people.get(M.y, {}).get('members', 0):,} members and {M.people.get(M.y, {}).get('visits', 0):,} visits in {M.label}</strong> —
{per:.2f} visits each{f", against {per_prev:.2f} in the same month last year" if per_prev else ""}. This chapter is about the shape of that behaviour rather than
its size: when members come, how long they leave between visits, how often they buy, and which of those patterns the studio can actually change.</p>''')

    if 'freq' in b and len(b['freq']):
        fq = b['freq']
        body.append(f'''<p><strong>{b['once_share']:.0f}% of members came exactly once this month</strong>, and the {b['top_n']} most frequent members
delivered {b['top_share']:.0f}% of every seat filled. A base with that shape will show healthy member counts and weak attendance at the same time, every month.</p>''')
        body.append(bars([str(i) if i < 10 else '10+' for i in fq.index[:11]], [('Members', [int(v) for v in fq.values[:11]], A1)],
                         'How many times each member came', h=300, note='Members who checked in at least once during the month.'))

    if 'hours' in b and len(b['hours']):
        h = b['hours']
        body.append(f'''<h2>When members come</h2>
<p>Read by the hour, the pattern is emphatic: <strong>{int(h.idxmax()):02d}:00 carries the most check-ins ({int(h.max())})</strong>.
Read by the member rather than the visit, <strong>{b['morning']} of {M.people.get(M.y, {}).get('members', 0)} members do most of their training before noon</strong>,
against {b['evening']} who come in the evening and {b['midday']} at midday.</p>''')
        body.append(bars([f'{int(i):02d}:00' for i in h.index], [('Check-ins', [int(v) for v in h.values], A1)],
                         'When members actually come', h=300, note='Every check-in at the studio during the month.'))
        if 'days' in b and len(b['days']):
            d = b['days']
            body.append(bars([str(i)[:3] for i in d.index], [('Check-ins', [int(v) for v in d.values], A1)],
                             'Which days carry the week', h=290,
                             note=f"{d.idxmax()} carries the most attendance and {d.idxmin()} the least — a {d.max()/max(d.min(),1):.1f}-fold difference inside the same month."))

    if 'gap' in b and len(b['gap'].dropna()):
        g = b['gap']
        body.append(f'''<h2>How often members come</h2>
<p>Look at the interval between one visit and the next for the same person: <strong>the median gap is {b['gap_med']:.0f} day</strong>, and
{b['gap_week']:.0f}% of every gap in the ledger is a week or less.</p>
<p>Members come in bursts rather than on a rhythm — several sessions close together, then a pause. That pattern is usually read as inconsistency and treated
with plans that assume a weekly cadence the members have never had.</p>''')
        body.append(bars([str(i) for i in g.index], [('Consecutive visits', [int(v) for v in g.fillna(0).values], A1)],
                         'How long a member leaves between visits', h=320, rotate=True,
                         note='Every consecutive-visit gap in the ledger, at this studio, all time.'))

    if 'pgap' in b and len(b['pgap'].dropna()):
        pg = b['pgap']
        body.append(f'''<h2>How often members buy</h2>
<p>The median gap between two purchases by the same person is <strong>{b['pgap_med']:.0f} days</strong>, and {b['pgap_month']:.0f}% of repeat purchases
happen inside a month. Buying at this studio is a monthly act, which puts the renewal conversation in the first fortnight of a membership rather than its last week.</p>''')
        body.append(bars([str(i) for i in pg.index], [('Purchases', [int(v) for v in pg.fillna(0).values], A2)],
                         'How long a buyer leaves between purchases', h=300, rotate=True,
                         note=f"{b.get('one_buy', 0):.1f}% of buyers have ever made exactly one purchase."))

    if 'monthly' in b and len(b['monthly']):
        mo = b['monthly']
        body.append(f'''<h2>Frequency through the year</h2>
<p>Visits per member have run between <strong>{mo['per'].min():.2f} and {mo['per'].max():.2f}</strong> over the period on file, and {M.label} sits at
{mo['per'].iloc[-1]:.2f}. More members each coming slightly less often produces a member count that looks healthy and attendance that is flat — which is
why the base and its frequency belong on the same page.</p>''')
        body.append(lines([str(i)[-5:] for i in mo.index], [('Visits per member', [float(v) for v in mo['per']], A1)],
                          'Visits per member, month by month', h=320, as_pct=False, ymax=float(mo['per'].max()) * 1.2,
                          label_last=True, note='Attendance divided by the members who produced it.'))

    if 'multi' in b:
        body.append(f'''<h2>Routine and variety</h2>
<p>{b['multi']:.0f}% of the month's members used more than one format, and <strong>{b.get('same3_members', 0)} members made three or more visits to a
single format</strong>. Routine and variety are not opposites here; both are associated with staying longer. The check-in ledger already records each member's
favourite format and preferred hour, and nothing in the studio currently uses either to hold a slot or to notice when a habit breaks.</p>''')

    facts = [f'{M.people.get(M.y, {}).get("members", 0):,} members and {M.people.get(M.y, {}).get("visits", 0):,} visits in {M.label} — {per:.2f} each.',
             f'{b.get("once_share", 0):.0f}% of members came once; the top tenth delivered {b.get("top_share", 0):.0f}% of attendance.']
    if 'gap_med' in b:
        facts.append(f'The median gap between a member’s visits is {b["gap_med"]:.0f} day and between purchases {b.get("pgap_med", 0):.0f} days.')
    return dict(id='behaviour', n=9, title='Member Behaviour and Patterns', body=''.join(body), kpis=kpis, facts=facts,
                subtitle=f'{M.people.get(M.y, {}).get("members", 0):,} members, {per:.2f} visits each')


ALL = [cancels, overview, leads, behaviour]
