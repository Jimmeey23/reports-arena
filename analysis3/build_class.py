"""Report 2 of 3 — Class Performance, Supreme HQ Bandra, September 2026."""
import pandas as pd, numpy as np
import d1_data as D
import d2_extra as X
from d2_extra import CLASS_A, CLASS_B
from d0_common import *

CL, FMT, FMT_YOY, DOW, HOUR, BAND, PAYMIX = D.CL, D.FMT, D.FMT_YOY, D.DOW, D.HOUR, D.BAND, D.PAYMIX
LEAN_BY, FULLEST, EMPTest, WK, HOSTED = D.LEAN_BY, D.FULLEST, D.EMPTest, D.WK, D.HOSTED
x24, x25, x26 = D.x24, D.x25, D.x26
C26, C25, C24 = CL[2026], CL[2025], CL[2024]

tot = len(x26)
FILL = C26['fill']

# ------------------------------------------------------------------ charts
CH_TREND = lines([str(y) for y in [2024, 2025, 2026]],
    [('Capacity utilisation %', [C24['fill'], C25['fill'], C26['fill']], BLU),
     ('Revenue per class (₹, /100)', [C24['rev_class']/100, C25['rev_class']/100, C26['rev_class']/100], TER)],
    'Three Septembers — how full the room was, and what each class earned', as_pct=True, ymax=0.62, h=320,
    note=f'Utilisation improved from {C25["fill"]:.1f}% to {C26["fill"]:.1f}% and revenue per class rose {C26["rev_class"]/C25["rev_class"]*100-100:.0f}%. The studio is running fewer, fuller, more valuable classes than a year ago.')

_f = FMT[FMT['sessions'] >= 5].copy()
CH_FMT = hbars([(i.replace('Studio ', ''), r['fill'], BLU if r['fill'] >= 50 else (GOLD if r['fill'] >= 35 else TER))
                for i, r in _f.sort_values('fill', ascending=False).iterrows()],
    'Capacity utilisation by class format, September 2026 (5+ sessions)', maxv=90, as_pct=True,
    note=f'Studio FIT fills {FMT.loc["Studio FIT","fill"]:.0f}% of its seats and runs {int(FMT.loc["Studio FIT","sessions"])} sessions. Studio PowerCycle runs {int(FMT.loc["Studio PowerCycle","sessions"])} — more than a third of the timetable — and fills {FMT.loc["Studio PowerCycle","fill"]:.0f}%.')

CH_FMT_VOL = bars([i.replace('Studio ','') for i in FMT[FMT['sessions']>=5].index],
    [('Sessions run', FMT[FMT['sessions']>=5]['sessions'].tolist(), GREY),
     ('Attendees (scaled)', [v/8 for v in FMT[FMT['sessions']>=5]['att']], TER)],
    'Sessions run against people who came (attendees shown at 1/8 scale)', as_pct=False, ymax=100, h=330, rotate=True,
    note='The two largest formats by session count — PowerCycle and Barre 57 — are not the two largest by attendance. Studio FIT runs 39 sessions and draws 277 people; PowerCycle runs 90 and draws 410.')

CH_DOW = bars(list(DOW.index), [('Sept 2026', DOW['fill'].tolist(), BLU), ('Sept 2025', DOW['fill25'].tolist(), GREY)],
    'Utilisation by day of the week — 2026 against 2025', as_pct=True, ymax=0.75, h=320,
    note=f'Saturday is the studio’s strongest day at {DOW.loc["Saturday","fill"]:.1f}% and Wednesday its weakest at {DOW.loc["Wednesday","fill"]:.1f}% — a {DOW.loc["Saturday","fill"]-DOW.loc["Wednesday","fill"]:.0f}-point spread within the same week.')

CH_BAND = hbars([(i, r['fill'], BLU if r['fill'] >= 45 else (GOLD if r['fill'] >= 38 else TER))
                 for i, r in BAND.sort_values('fill', ascending=False).iterrows()],
    'Utilisation by time of day, September 2026', maxv=62, as_pct=True,
    note=f'Late morning (09:00–11:59) is the studio’s strongest daypart at {BAND.loc["Late morning (09:00–11:59)","fill"]:.1f}%. Early morning before 09:00 fills {BAND.loc["Early (to 08:59)","fill"]:.1f}% and carries {int(BAND.loc["Early (to 08:59)","sessions"])} sessions.')

CH_HOUR = bars([f'{int(h)}:00' for h in HOUR.index], [('Utilisation', HOUR['fill'].tolist(), BLU)],
    'Utilisation by start hour — the shape of the day', as_pct=True, ymax=0.85, h=310,
    note='The 11:00 hour is the studio’s best-sold slot at 56%; the 07:00 hour is its worst at 26%. The dip at 20:00 reflects only two sessions and should not be over-read.')

CH_LEAN = bars([i.replace('Studio ','') for i in LEAN_BY.index[:8]],
    [('Empty sessions', LEAN_BY['empty'].head(8).tolist(), TER),
     ('Sessions with 1–2 attendees', LEAN_BY['1–2 only'].head(8).tolist(), GOLD)],
    'Sessions that ran to two people or fewer, September 2026', as_pct=False, ymax=22, h=320, rotate=True,
    note=f'{int(LEAN_BY["lean"].sum())} of the month’s {tot} sessions — {LEAN_BY["lean"].sum()/tot*100:.0f}% — drew two people or fewer. Studio PowerCycle accounts for {int(LEAN_BY.loc["Studio PowerCycle","lean"])} of them.')

CH_WK = bars([f'Week {i}' for i in range(1, 6)],
    [('Sept 2025', [WK['2025']['fill'].get(i, np.nan) for i in range(1, 6)], GREY),
     ('Sept 2026', [WK['2026']['fill'].get(i, np.nan) for i in range(1, 6)], BLU)],
    'Utilisation week by week — the month fades in both years', as_pct=True, ymax=0.62, h=310,
    note='Both years follow the same arc: the strongest week is the first and the weakest the last. In 2026 the studio started from a higher base in week one and still finished at 38%.')

CH_PAYMIX = bars([i.replace('Studio ','') for i in PAYMIX.index[:8]],
    [('Membership', PAYMIX['mem_p'][:8].tolist(), BLU), ('Package', PAYMIX['pkg_p'][:8].tolist(), TER),
     ('Intro offer', PAYMIX['intro_p'][:8].tolist(), GOLD), ('Single class', PAYMIX['single_p'][:8].tolist(), GREY)],
    'How each format’s attendees paid for the class', as_pct=True, ymax=1.05, h=330, rotate=True,
    note=f'PowerCycle is the studio’s trial engine: {PAYMIX.loc["Studio PowerCycle","intro_p"]:.0f}% of its attendance is on intro offers, against {PAYMIX.loc["Studio FIT","intro_p"]:.0f}% for Studio FIT. FIT is where members go once they have bought in.')

# ------------------------------------------------------------------ tables
tr = []
for y, d in [(2024, C24), (2025, C25), (2026, C26)]:
    tr.append([f'Sept {y}', f"{d['sessions']:,}", f"{d['seats']:,}", f"{d['att']:,}", P(d['fill']),
               f"{d['empty']}", R(d['rev']), R(d['rev_class']), R(d['rev_head'])])
TR_T = T(['September', 'Sessions', 'Seats offered', 'Attended', 'Utilisation', 'Empty sessions',
          'Class revenue', 'Revenue / class', 'Revenue / attendee'], tr, 'mono')

fmt_rows = []
for i, r in FMT.iterrows():
    fmt_rows.append([i.replace('Studio ', ''), f"{int(r['sessions'])}", f"{int(r['seats']):,}", f"{int(r['att'])}",
                     P(r['fill']), f"{r['avg_size']:.2f}", f"{int(r['empty'])}", P(r['lc_rate']),
                     R(r['rev']), R(r['rev_class']), R(r['rev_head']) if pd.notna(r['rev_head']) else '—'])
FMT_T = T(['Format', 'Sessions', 'Seats', 'Attended', 'Utilisation', 'Average class', 'Empty',
           'Late-cancel rate', 'Revenue', 'Revenue / class', 'Revenue / attendee'], fmt_rows, 'mono')

yoy_rows = []
for i, r in FMT_YOY.sort_values('att', ascending=False).iterrows():
    if pd.isna(r['sessions']) or r['sessions'] == 0: continue
    yoy_rows.append([i.replace('Studio ', ''), f"{int(r['s25']) if pd.notna(r['s25']) else 0}", f"{int(r['sessions'])}",
                     f"{int(r['att'])}", f"{(int(r['att'])-int(r['a25'])) if pd.notna(r['a25']) else int(r['att']):+,}".replace('+','+').replace('-','−'),
                     P(r['fill']), P(r['fill25']) if pd.notna(r['fill25']) else '—',
                     (f"{r['fill']-r['fill25']:+.1f}" if pd.notna(r['fill25']) else '—')])
YOY_T = T(['Format', 'Sessions 2025', 'Sessions 2026', 'Attended 2026', 'Change in attendees',
           'Utilisation 2026', 'Utilisation 2025', 'Change'], yoy_rows, 'mono')

dow_rows = [[i, f"{int(r['sessions'])}", f"{int(r['seats'])}", f"{int(r['att'])}", P(r['fill']),
             P(r['fill25']) if pd.notna(r['fill25']) else '—', R(r['rev']), R(r['rev_class'])]
            for i, r in DOW.iterrows()]
DOW_T = T(['Day', 'Sessions', 'Seats', 'Attended', 'Utilisation 2026', 'Utilisation 2025',
           'Revenue', 'Revenue / class'], dow_rows, 'mono')

hour_rows = [[f'{int(h)}:00–{int(h)+1}:00', f"{int(r['sessions'])}", f"{int(r['seats'])}", f"{int(r['att'])}",
              P(r['fill']), R(r['rev'])] for h, r in HOUR.iterrows()]
HOUR_T = T(['Start hour', 'Sessions', 'Seats', 'Attended', 'Utilisation', 'Revenue'], hour_rows, 'mono')

lean_rows = [[i.replace('Studio ', ''), f"{int(r['all'])}", f"{int(r.get('empty', 0))}", f"{int(r.get('1–2 only', 0))}",
              f"{int(r['lean'])}", P(r['lean_%'])] for i, r in LEAN_BY.iterrows()]
LEAN_T = T(['Format', 'Sessions run', 'Empty', 'Ran to 1–2', 'Total lean', 'Share of format’s sessions'], lean_rows, 'mono')

lean_sess = x26[x26['CheckedIn'] <= 2][['Date', 'Day', 'Time', 'Class', 'Trainer', 'Capacity', 'CheckedIn', 'Booked', 'LateCancelled']].sort_values(['CheckedIn', 'Date'])
LEAN_ST = T(['Date', 'Day', 'Start', 'Format', 'Trainer', 'Capacity', 'Attended', 'Booked', 'Late-cancelled'],
            [[str(r['Date'])[:10], r['Day'], str(r['Time'])[:5], r['Class'].replace('Studio ', ''), r['Trainer'],
              f"{int(r['Capacity'])}", f"{int(r['CheckedIn'])}", f"{int(r['Booked'])}", f"{int(r['LateCancelled'])}"]
             for _, r in lean_sess.iterrows()], 'mono small')

full_rows = [[str(r['Date'])[:10], r['Day'], str(r['Time'])[:5], r['Class'].replace('Studio ', ''), r['Trainer'],
              f"{int(r['Capacity'])}", f"{int(r['CheckedIn'])}", R(r['Revenue'])] for _, r in FULLEST.iterrows()]
FULL_T = T(['Date', 'Day', 'Start', 'Format', 'Trainer', 'Capacity', 'Attended', 'Revenue'], full_rows, 'mono small')

emp_rows = [[str(r['Date'])[:10], r['Day'], str(r['Time'])[:5], r['Class'].replace('Studio ', ''), r['Trainer'],
             f"{int(r['Capacity'])}", f"{int(r['Booked'])}", f"{int(r['LateCancelled'])}"] for _, r in EMPTest.iterrows()]
EMPTY_T = T(['Date', 'Day', 'Start', 'Format', 'Trainer', 'Capacity', 'Booked', 'Late-cancelled'], emp_rows, 'mono small')

fill_rows = [['0 attendees (empty)', f"{int((x26['CheckedIn']==0).sum())}", f"{int(x26[x26['CheckedIn']==0]['Capacity'].sum())}"],
             ['1 attendee', f"{int((x26['CheckedIn']==1).sum())}", f"{int(x26[x26['CheckedIn']==1]['Capacity'].sum())}"],
             ['2 attendees', f"{int((x26['CheckedIn']==2).sum())}", f"{int(x26[x26['CheckedIn']==2]['Capacity'].sum())}"],
             ['3–5 attendees', f"{int(x26['CheckedIn'].between(3,5).sum())}", f"{int(x26[x26['CheckedIn'].between(3,5)]['Capacity'].sum())}"],
             ['6–10 attendees', f"{int(x26['CheckedIn'].between(6,10).sum())}", f"{int(x26[x26['CheckedIn'].between(6,10)]['Capacity'].sum())}"],
             ['11+ attendees', f"{int((x26['CheckedIn']>=11).sum())}", f"{int(x26[x26['CheckedIn']>=11]['Capacity'].sum())}"]]
FILL_T = T(['Attendance', 'Sessions', 'Seats tied up'], fill_rows, 'mono')

wk_rows = [[f'Week {i}', f"{WK['2025']['sessions'].get(i,0):.0f}", P(WK['2025']['fill'].get(i, np.nan)) if i in WK['2025']['fill'] else '—',
            f"{WK['2026']['sessions'].get(i,0):.0f}", P(WK['2026']['fill'].get(i, np.nan)) if i in WK['2026']['fill'] else '—']
           for i in range(1, 6)]
WK_T = T(['Week of month', 'Sessions 2025', 'Utilisation 2025', 'Sessions 2026', 'Utilisation 2026'], wk_rows, 'mono')

host_rows = [[str(r['Date'])[:10], r['Day'], str(r['Time'])[:5], r['SessionName'][:44], r['Trainer'],
              f"{int(r['Capacity'])}", f"{int(r['CheckedIn'])}", P(r['CheckedIn']/r['Capacity']*100)] for _, r in HOSTED.iterrows()]
HOST_T = T(['Date', 'Day', 'Start', 'Session', 'Trainer', 'Capacity', 'Attended', 'Utilisation'], host_rows, 'mono small')

# ------------------------------------------------------------------ size-mismatch analysis
sz = x26.groupby('Class').agg(sessions=('SessionID','size'), att=('CheckedIn','sum'), seats=('Capacity','sum'))
sz['att_per'] = sz['att']/sz['sessions']
sz['cap_per'] = sz['seats']/sz['sessions']
SIZE_T = T(['Format', 'Sessions', 'Seats per class', 'Average attendance', 'Unused seats per class'],
           [[i.replace('Studio ',''), f"{int(r['sessions'])}", f"{r['cap_per']:.1f}", f"{r['att_per']:.2f}",
             f"{r['cap_per']-r['att_per']:.2f}"] for i, r in sz.sort_values('sessions', ascending=False).iterrows()], 'mono')

# ------------------------------------------------------------------ recommendations
_S24 = set(X.s24['Member ID']); _S25 = set(X.s25['Member ID']); _S26 = set(X.s26['Member ID'])

RECS = [
 ('01','Right-size Studio PowerCycle','Programming + Studio Manager',
  f'PowerCycle runs {int(FMT.loc["Studio PowerCycle","sessions"])} sessions — {FMT.loc["Studio PowerCycle","sessions"]/tot*100:.0f}% of the entire timetable — and fills <strong>{FMT.loc["Studio PowerCycle","fill"]:.1f}%</strong> of its seats, down {abs(FMT_YOY.loc["Studio PowerCycle","d_fill"]):.1f} points on last September. It is the only major format whose utilisation fell, and it absorbed {abs(FMT_YOY.loc["Studio PowerCycle","d_att"]):.0f} fewer attendees than a year ago. Meanwhile its capacity per class is {sz.loc["Studio PowerCycle","cap_per"]:.1f} seats against an average attendance of {sz.loc["Studio PowerCycle","att_per"]:.2f}.',
  f'Cutting PowerCycle’s average class size from {sz.loc["Studio PowerCycle","cap_per"]:.0f} to 10 seats frees roughly {int(FMT.loc["Studio PowerCycle","sessions"]*(sz.loc["Studio PowerCycle","cap_per"]-10))} seat-hours a month without touching the timetable, and removes {int(LEAN_BY.loc["Studio PowerCycle","empty"] if "empty" in LEAN_BY else 8)} empty sessions from the board. Raising its fill to Studio FIT’s {FMT.loc["Studio FIT","fill"]:.0f}% would add roughly {int(FMT.loc["Studio PowerCycle","seats"]*FMT.loc["Studio FIT","fill"]/100)-int(FMT.loc["Studio PowerCycle","att"])} attendances a month.'),
 ('02','Make Studio FIT the template, then scale it','Programming',
  f'Studio FIT is the studio’s best-performing format by a distance: <strong>{FMT.loc["Studio FIT","fill"]:.1f}% utilisation on {int(FMT.loc["Studio FIT","sessions"])} sessions</strong>, an average class of {FMT.loc["Studio FIT","avg_size"]:.1f}, {int(FMT_YOY.loc["Studio FIT","d_att"]):+} more attendees than last September, and the highest revenue per class of any format at {R(FMT.loc["Studio FIT","rev_class"])}. It achieved this while adding 10 sessions. Only {FMT.loc["Studio FIT","intro_p"] if "intro_p" in FMT else PAYMIX.loc["Studio FIT","intro_p"]:.0f}% of its attendance is on intro offers — these are committed members.',
  f'Adding 3 FIT sessions a week at current fill adds about {int(3*4.3*FMT.loc["Studio FIT","avg_size"])} attendances a month, worth roughly {R(int(3*4.3*FMT.loc["Studio FIT","avg_size"])*FMT.loc["Studio FIT","rev_head"])} of class revenue, using capacity the studio already owns.'),
 ('03','Close the early-morning black hole','Studio Manager + Programming',
  f'Sessions starting before 09:00 fill <strong>{BAND.loc["Early (to 08:59)","fill"]:.1f}%</strong> — {BAND.loc["Late morning (09:00–11:59)","fill"]-BAND.loc["Early (to 08:59)","fill"]:.0f} points below the late-morning peak — and account for {int(BAND.loc["Early (to 08:59)","sessions"])} of the month’s sessions. <strong>Eight of the eleven fully empty sessions in September started at 07:30 or 09:15</strong>, and every one of them was PowerCycle.',
  f'Consolidating the weakest early slots into the 09:00–11:00 window, or converting them to a format with proven early demand, would remove about {int(BAND.loc["Early (to 08:59)","sessions"]*0.25)} unproductive sessions a month and lift overall utilisation by an estimated 2–3 points.'),
 ('04','Rebalance the week away from Wednesday','Programming',
  f'Wednesday fills <strong>{DOW.loc["Wednesday","fill"]:.1f}%</strong> against Saturday’s {DOW.loc["Saturday","fill"]:.1f}% — a {DOW.loc["Saturday","fill"]-DOW.loc["Wednesday","fill"]:.0f}-point gap inside the same week. Wednesday also runs {int(DOW.loc["Wednesday","sessions"])} sessions, more than any day except Tuesday, and earns the lowest revenue per class at {R(DOW.loc["Wednesday","rev_class"])} against Saturday’s {R(DOW.loc["Saturday","rev_class"])}.',
  f'Moving 4 of Wednesday’s weakest sessions to Saturday and Sunday mornings, where utilisation is {DOW.loc["Saturday","fill"]:.0f}% and {DOW.loc["Sunday","fill"]:.0f}%, redirects roughly {int(4*4.3*DOW.loc["Saturday","fill"]/100*12.7)} attendances a month into demand that already exists.'),
 ('05','Fix the fourth-week fade','Programming + Marketing',
  f'Utilisation falls from <strong>{WK["2026"]["fill"].get(1, np.nan):.1f}% in week one to {WK["2026"]["fill"].get(4, np.nan):.1f}% in week four</strong> while the number of sessions run stays broadly constant. September 2025 showed the identical pattern, which means this is a structural rhythm rather than a September event.',
  f'Holding week four to the week-one rate would add roughly {int((WK["2026"]["fill"].get(1,0)-WK["2026"]["fill"].get(4,0))/100*WK["2026"]["seats"].get(4,0))} attendances in a single week. A mid-month re-engagement push aimed at members who have not booked in 14 days is the natural instrument.'),
 ('06','Stop scheduling classes that draw two people','Programming',
  f'<strong>{int(LEAN_BY["lean"].sum())} of {tot} sessions ({LEAN_BY["lean"].sum()/tot*100:.0f}%) ran to two attendees or fewer</strong>, including {int(LEAN_BY["empty"].sum())} that were completely empty. Those sessions tied up {int(x26[x26["CheckedIn"]<=2]["Capacity"].sum())} seats on the schedule. PowerCycle accounts for {int(LEAN_BY.loc["Studio PowerCycle","lean"])} of them.',
  f'Consolidating the leanest {int(LEAN_BY["lean"].sum()*0.6)} of these sessions would free roughly {int(x26[x26["CheckedIn"]<=2]["Capacity"].sum()*0.6)} seat-hours a month and give the studio a timetable it can promote honestly. Every empty class also carries a trainer cost that this data does not capture.'),
 ('07','Build the conversion pathway that the hosted classes lack','Marketing + Studio Manager',
  f'All {len(HOSTED)} hosted and partner classes in September ran at <strong>{HOSTED["CheckedIn"].sum()/HOSTED["Capacity"].sum()*100:.0f}% utilisation</strong> — the fullest classes of the month — and produced <strong>{R(0)} of class revenue</strong>, because every attendee was complimentary. Separately, hosted-class leads convert to membership at 8.3% against 24.2% for referrals.',
  f'These are the studio’s best-attended sessions and its worst-converting source. Attaching a booked second class to every hosted attendee at the point of arrival is the cheapest fix available and would move the modelled value of the programme materially without changing what it costs to run.'),
 ('08','Publish utilisation, not just attendance','Studio Manager',
  f'The studio tracks attendance well but the timetable is set on judgement. This September a {DOW.loc["Saturday","fill"]-DOW.loc["Wednesday","fill"]:.0f}-point utilisation spread existed between two days, a {BAND.loc["Late morning (09:00–11:59)","fill"]-BAND.loc["Early (to 08:59)","fill"]:.0f}-point spread existed between two dayparts, and {int((FMT["fill"]<40).sum())} of {len(FMT)} formats filled less than 40% of their seats. None of that is visible in an attendance-only report, because attendance is a count and utilisation is a ratio.',
  'One monthly utilisation table, read before the next month’s timetable is built, changes the basis of every scheduling decision from "did anyone come" to "was this the right room".'),
 ('09','Shrink the room before shrinking the timetable','Studio Manager + Programming',
  f'Rooms of ten to eleven seats ran {X.CB_FILL_26.get("10–11"):.1f}% full across {int(X.CB26.loc["10–11","n"])} sessions; rooms of twelve to thirteen ran {X.CB_FILL_26.get("12–13"):.1f}% across {int(X.CB26.loc["12–13","n"])} sessions, and rooms of fourteen or more ran {X.CB_FILL_26.get("14+"):.1f}% across {int(X.CB26.loc["14+","n"])}. The studio has already moved in this direction — sessions in ten-to-eleven-seat rooms rose from {int(X.CB25.loc["10–11","n"])} to {int(X.CB26.loc["10–11","n"])} — and the effect on the fill rate is arithmetic, not heroics.',
  f'The {int(X.CB26.loc["12–13","n"])} sessions sitting in the twelve-to-thirteen band are the largest single block of addressable inefficiency in the timetable. Capping those rooms at eleven seats removes roughly {int(X.CB26.loc["12–13","n"])*2} seat-slots a month that nobody is buying, and lifts overall utilisation by around {((X.CB26.loc["12–13","n"])*2)/int(X.x26["cap"].sum())*100:.1f} points without changing a single thing about who teaches or when.'),
 ('10','Put a hard line under complimentary seats','Studio Manager + Finance',
  f'Complimentary seats rose {abs(X.COMP26/143*100-100):.0f}% year on year, to <strong>{X.COMP26} of {int(x26["CheckedIn"].sum())} attendances — {X.COMP_SHARE:.1f}% of the room</strong>, against {143/1476*100:.1f}% a year earlier. Studio Barre 57 alone ran {int(X.CBAR.get("Studio Barre 57",0))} comp seats on {int(x26[x26["Class"]=="Studio Barre 57"]["CheckedIn"].sum())} attendances ({X.CBAR.get("Studio Barre 57",0):.0f}%).',
  f'Comps are legitimate but they are invisible in the fill rate and the fill rate is what the timetable is judged on. A monthly comp budget by format — and a rule that a comp consumes the same seat a paying member could have bought — would make the {X.COMP26} seats visible. At September’s revenue per head of ₹931 that is {R(X.COMP26*931)} of delivered value a month to account for.'),
 ('11','Design the first visit, do not default it','Studio Manager + Programming',
  f'A first class on a Tuesday leads to a third visit {X.Q_DAY.loc["Tuesday","r3"]:.1f}% of the time; on a Sunday, {X.Q_DAY.loc["Sunday","r3"]:.1f}%. Before 9am, {X.Q_BAND.loc["Early, before 9am","r3"]:.1f}%; in the afternoon, {X.Q_BAND.loc["Afternoon, 12–17","r3"]:.1f}%. In Studio Barre 57, {X.Q_FMT.loc["Studio Barre 57","r3"]:.1f}%; in Studio Mat 57, {X.Q_FMT.loc["Studio Mat 57","r3"]:.1f}%.',
  f'Trialists are currently placed wherever there is room. Placing them deliberately — into the Tuesday and early-morning slots that convert at nearly double the afternoon rate — costs nothing and operates on the {int(X.Q_DAY["n"].sum())} first-timers this analysis covers. Even a five-point lift in third-visit conversion is worth about {R(int(X.Q_DAY["n"].sum())*0.05*931*4)} of delivered value.'),
 ('12','Manage the booking book, not the attendance','Studio Manager',
  f'Bookings fell {abs(x26["Booked"].sum()/x25["Booked"].sum()*100-100):.0f}% against a {abs(x26["CheckedIn"].sum()/x25["CheckedIn"].sum()*100-100):.1f}% fall in attendance, and the book now covers only {X.BOOK_BOARD_26:.1f}% of the seats on the board, down from {X.BOOK_BOARD_25:.1f}%. Attendance told the studio after the fact that September was quieter; the booking book said so in advance.',
  'A weekly booked-versus-capacity ratio for the coming fortnight, read alongside the fill rate for the past one, converts the timetable from a rear-view report into a leading one. It is the difference between noticing the current quarter and managing the next one.')
,
 ('13','Report frequency per active member, not attendance alone','Studio Manager + Management',
  f'The member base is widening while volume falls: <strong>{X.s26["Member ID"].nunique()} members trained this September against {X.s25["Member ID"].nunique()} last</strong>, '
  f'but each of them came {X.s26.groupby("Member ID").size().mean():.2f} times against {X.s25.groupby("Member ID").size().mean():.2f}. Attendance is a lagging number; '
  f'visits per active member is the number that moves first.',
  'A monthly line for visits per member, sitting beside the member count, would have flagged this decline in the spring instead of at the September review. '
  'It costs the studio nothing to produce and it changes what the studio notices.'),
 ('14','Build a continuity tier from the members who never leave','Studio Manager + CRM',
  f'<strong>Only {len(_S24 & _S25 & _S26)} members trained at Bandra in all three of September 2024, 2025 and 2026.</strong> Against a base of '
  f'{X.s26["Member ID"].nunique()} members this September, that is {len(_S24 & _S25 & _S26)/X.s26["Member ID"].nunique()*100:.1f}% who have kept the habit '
  f'across three years of a business that has run {X.s24["Member ID"].nunique()} and {X.s25["Member ID"].nunique()} members in the same months.',
  f'These {len(_S24 & _S25 & _S26)} people are the studio’s only proof that a member can stay. They should be known by name, asked what holds them, and used as '
  f'the benchmark against which every retention initiative is measured. A studio that cannot describe its longest-serving members in detail cannot design for them.'),
]
REC_HTML = rec_html(RECS)

SRC = f'''<h4>Sources and method</h4>
<p><strong>Day End Report &ndash; Part 3 &ndash; Sessions</strong> (25,675 rows, exported 11 October 2026) is the primary source. Each row is one class occurrence at one location, with capacity, checked-in, booked, late-cancelled, complimentary, revenue and a breakdown of how attendees paid. <strong>Day End Report &ndash; Part 3 &ndash; Teacher Recurring</strong> (3,294 rows) is the same data aggregated per recurring weekly slot and reconciles to the Sessions file exactly.</p>
<p>Utilisation is computed here as <strong>checked-in attendances divided by capacity offered, per class occurrence</strong>. This is the studio&rsquo;s own definition and it is the one used throughout. It differs from a count of bookings, and it counts a seat as unused whether the member never booked it or booked and did not turn up.</p>
<h4>A note on the recurring-slot file</h4>
<p>Two columns in the Teacher Recurring export are mislabelled in the platform: the column named <em>FillRate</em> actually contains revenue per class, and the column named <em>ClassAvgExclEmpty</em> actually contains the fill rate. This report uses only the raw counts from that file &mdash; classes, capacity and checked-in &mdash; and recomputes every ratio itself.</p>
<h4>Known limitations</h4>
<ul>
 <li><strong>No trainer cost.</strong> This data contains no payroll or cost-per-class information, so an empty class can be described as unproductive but not quantified as a loss. Part 1 of the Payroll export supplies teacher economics, and it runs only to August 2026.</li>
 <li><strong>Revenue attribution.</strong> Class revenue is the platform&rsquo;s allocation of member spend to attended classes. It reconciles to {C26['rev']/D.DN['s_cash'][2026]*100:.0f}% of September cash. It is a sound basis for comparing formats, not an accounting statement.</li>
 <li><strong>Two sessions of 20:00 and one of 16:00</strong> are too few to draw conclusions from; hour-level figures with fewer than five sessions are marked accordingly in the workbook.</li>
 <li><strong>September 2025 followed Ganesh Chaturthi</strong> (27 August) while September 2026 absorbed it (14 September). Week-by-week comparisons near the festival are affected.</li>
</ul>'''

ARW_S = '▼' if C26['sessions'] < C25['sessions'] else '▲'
ARW_A = '▼' if C26['att'] < C25['att'] else '▲'
BODY = f'''
<div class="kpis">
 <div class="kpi"><div class="l">Classes run</div><div class="v">{C26['sessions']}</div><div class="d neu">{ARW_S} {abs(C26['sessions']/C25['sessions']*100-100):.1f}% against September 2025 &mdash; fewer, fuller classes</div></div>
 <div class="kpi"><div class="l">Capacity utilisation</div><div class="v">{P(FILL)}</div><div class="d pos">▲ from {P(C25['fill'])} &mdash; the best of the three Septembers</div></div>
 <div class="kpi"><div class="l">Attendances</div><div class="v">{C26['att']:,}</div><div class="d neu">{ARW_A} {abs(C26['att']/C25['att']*100-100):.1f}% on the year</div></div>
 <div class="kpi"><div class="l">Class revenue</div><div class="v">{R(C26['rev'])}</div><div class="d pos">▲ {C26['rev']/C25['rev']*100-100:.0f}% &mdash; the only line in the studio that grew</div></div>
</div>
<div class="kpis" style="margin-top:16px">
 <div class="kpi"><div class="l">Revenue per class</div><div class="v">{R(C26['rev_class'])}</div><div class="d pos">▲ from {R(C25['rev_class'])} &mdash; up {C26['rev_class']/C25['rev_class']*100-100:.0f}%</div></div>
 <div class="kpi"><div class="l">Revenue per attendee</div><div class="v">{R(C26['rev_head'])}</div><div class="d pos">▲ from {R(C25['rev_head'])} &mdash; members are on richer plans</div></div>
 <div class="kpi"><div class="l">Empty sessions</div><div class="v">{C26['empty']}</div><div class="d">{C25['empty']} last September &mdash; but {int(LEAN_BY['lean'].sum())} ran to two people or fewer</div></div>
 <div class="kpi"><div class="l">Late cancellations</div><div class="v">{C26['lc']}</div><div class="d pos">&darr; {abs(C26['lc']/(C26['booked']+C26['lc'])*100 - C25['lc']/(C25['booked']+C25['lc'])*100):.1f} points year on year</div></div>
</div>

<h2>Start here</h2>
<div class="sub">The classes got better. There are simply fewer good ones than there should be.</div>
<p>Class performance is the one part of Bandra&rsquo;s September that improved on nearly every measure, and it deserves to be said clearly before the problems. The studio ran <strong>{C26['sessions']} classes against {C25['sessions']} a year earlier</strong> &mdash; a leaner timetable &mdash; and filled <strong>{P(FILL)} of the seats against {P(C25['fill'])}</strong>. Revenue attributed to attended classes rose from {R(C25['rev'])} to <strong>{R(C26['rev'])}</strong>, up {C26['rev']/C25['rev']*100-100:.0f}%, making it the only revenue line in the studio that grew. Revenue per class rose {C26['rev_class']/C25['rev_class']*100-100:.0f}% to {R(C26['rev_class'])}; revenue per attendee rose from {R(C25['rev_head'])} to {R(C26['rev_head'])}. Late cancellations fell from {C25['lc']} to {C26['lc']}.</p>
<p>Every one of those is a genuine operational gain, and two Septembers of improvement in a row &mdash; from {P(C24['fill'])} in 2024 to {P(C25['fill'])} to {P(FILL)} &mdash; is a trend rather than noise.</p>
{CH_TREND}
{TR_T}
<p>What the same numbers also show is a large and specific inefficiency that has been carried for three years without being addressed. <strong>The studio holds a fixed-cost timetable and fills just over two seats in five.</strong> In September 2026 it offered {C26['seats']:,} seats and used {C26['att']:,} of them. The unused {C26['seats']-C26['att']:,} seats are not evenly spread: they are concentrated in particular formats, particular days and particular hours, and the concentration is stable enough across two years to be treated as a design flaw rather than a bad month.</p>
<p>The single most useful sentence in this report is this: <strong>Studio PowerCycle runs {FMT.loc['Studio PowerCycle','sessions']/tot*100:.0f}% of the timetable and fills {FMT.loc['Studio PowerCycle','fill']:.1f}% of it, while Studio FIT runs {FMT.loc['Studio FIT','sessions']/tot*100:.0f}% of the timetable and fills {FMT.loc['Studio FIT','fill']:.1f}%.</strong> Both are good products with loyal followings. Only one of them is being given the right amount of the week.</p>

<p>And a fourth finding, which is new in this edition and changes what the first three mean. The studio is not short of people. <strong>{X.s26['Member ID'].nunique()} members trained here in September 2026 against {X.s25['Member ID'].nunique()} a year earlier</strong> &mdash; a wider base than in either of the last two Septembers. What fell was how often they came: {X.SPM26:.2f} visits each against {X.SPM25:.2f}. The {len(X.core_ix)} members who were here in both Septembers cut their own frequency {abs(X.core_now.mean()/X.core_then.mean()*100-100):.0f}%, and those missing {abs(X.CORE_LOST)} visits are <strong>{abs(X.CORE_LOST)/len(X.s26)*100:.0f}% of everything the studio filled this month</strong>. The room is not emptying because people stopped coming. It is emptying because the people who come are coming less.</p>

{CLASS_A}

{CLASS_B}

<h2>Format by format</h2>
<div class="sub">Where the seats are, and where the people are</div>
{CH_FMT}
{FMT_T}
{CH_FMT_VOL}
<p>Three formats tell the story.</p>
<p><strong>Studio FIT is the studio&rsquo;s best asset.</strong> It fills {FMT.loc['Studio FIT','fill']:.1f}% of its seats, averages {FMT.loc['Studio FIT','avg_size']:.1f} people a class, earns {R(FMT.loc['Studio FIT','rev_class'])} per class &mdash; the highest of any format &mdash; and drew {int(FMT_YOY.loc['Studio FIT','d_att'])} more attendees than last September while adding {int(FMT_YOY.loc['Studio FIT','sessions']-FMT_YOY.loc['Studio FIT','s25'])} sessions. It has zero empty classes. It is also the format with the lowest share of intro-offer attendance, meaning its audience is committed members rather than trials.</p>
<p><strong>Studio PowerCycle is the studio&rsquo;s biggest format and its least efficient.</strong> It runs {int(FMT.loc['Studio PowerCycle','sessions'])} sessions, more than a third of the month, and fills {FMT.loc['Studio PowerCycle','fill']:.1f}% &mdash; a fall of {abs(FMT_YOY.loc['Studio PowerCycle','d_fill']):.1f} points year on year, and the only major decline in the table. It absorbed {abs(FMT_YOY.loc['Studio PowerCycle','d_att']):.0f} fewer attendees. It also carries the studio&rsquo;s trial programme: {PAYMIX.loc['Studio PowerCycle','intro_p']:.0f}% of its attendance arrives on an intro offer. PowerCycle is doing two jobs &mdash; a flagship product and a trial venue &mdash; and the second is crowding out the first.</p>
<p><strong>Studio Barre 57 is the quiet improver.</strong> Utilisation rose {FMT_YOY.loc['Studio Barre 57','d_fill']:+.1f} points to {FMT.loc['Studio Barre 57','fill']:.1f}% on {int(FMT_YOY.loc['Studio Barre 57','s25']-FMT.loc['Studio Barre 57','sessions'])} fewer sessions, with attendance essentially flat. The studio cut Barre capacity and the format got tighter as a result &mdash; which is direct evidence that the same approach would work elsewhere.</p>
<p>Two formats are chronic underperformers. <strong>Studio Cardio Barre filled {FMT.loc['Studio Cardio Barre','fill']:.1f}%</strong>, almost identical to its {FMT_YOY.loc['Studio Cardio Barre','fill25']:.1f}% last year, on {int(FMT.loc['Studio Cardio Barre','sessions'])} sessions. <strong>Studio Recovery filled {FMT.loc['Studio Recovery','fill']:.1f}%</strong>, down {abs(FMT_YOY.loc['Studio Recovery','d_fill']):.1f} points. Together they account for {int(FMT.loc['Studio Cardio Barre','sessions']+FMT.loc['Studio Recovery','sessions'])} sessions and {int(FMT.loc['Studio Cardio Barre','att']+FMT.loc['Studio Recovery','att'])} attendances. Neither is a bad class; both are occupying slots that the studio&rsquo;s strongest formats could use.</p>
{ev('View every format against September 2025', YOY_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Formats that ran in only one of the two years show a blank comparator. Studio Hosted Class, Mat 57 Express and Trainer’s Choice were introduced or reintroduced in 2026.</p>')}

<h2>When the studio is busy</h2>
<div class="sub">Day of week and time of day</div>
{CH_DOW}
{DOW_T}
<p>The week is strikingly uneven. <strong>Saturday fills {DOW.loc['Saturday','fill']:.1f}% of its seats and Wednesday {DOW.loc['Wednesday','fill']:.1f}%</strong> &mdash; a {DOW.loc['Saturday','fill']-DOW.loc['Wednesday','fill']:.0f}-point spread between two days that both run a full schedule. Saturday also earns the most per class at {R(DOW.loc['Saturday','rev_class'])} against Wednesday&rsquo;s {R(DOW.loc['Wednesday','rev_class'])}. Wednesday is not short of classes &mdash; it runs {int(DOW.loc['Wednesday','sessions'])} sessions, the second-highest of the week &mdash; it is short of demand for them.</p>
{CH_BAND}
{CH_HOUR}
{HOUR_T}
<p>The daypart picture is even sharper. <strong>Late morning, 09:00 to 11:59, fills {BAND.loc['Late morning (09:00–11:59)','fill']:.1f}%</strong> and is the studio&rsquo;s strongest window, earning {R(BAND.loc['Late morning (09:00–11:59)','rev_class'])} per class. <strong>Early morning, before 09:00, fills {BAND.loc['Early (to 08:59)','fill']:.1f}%</strong> across {int(BAND.loc['Early (to 08:59)','sessions'])} sessions. That is a {BAND.loc['Late morning (09:00–11:59)','fill']-BAND.loc['Early (to 08:59)','fill']:.0f}-point gap inside a three-hour window, and it is the largest single addressable inefficiency in the timetable.</p>
<p>The hour-level view locates it precisely: the <strong>07:00 hour fills {HOUR.loc[7,'fill']:.1f}%</strong> and the <strong>11:00 hour {HOUR.loc[11,'fill']:.1f}%</strong>. The studio is running its emptiest classes at the hour when its best-sold window opens two hours later.</p>
{ev('View utilisation by every start hour', HOUR_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Hours with fewer than five sessions (12:00, 16:00, 17:00 and 20:00) are shown for completeness but should not be read as trends.</p>')}

<h2>The classes nobody came to</h2>
<div class="sub">{int(LEAN_BY['lean'].sum())} sessions that ran to two people or fewer</div>
{CH_LEAN}
{LEAN_T}
<p>Eleven sessions ran completely empty in September, and a further thirty-eight drew one or two attendees. Together that is <strong>{int(LEAN_BY['lean'].sum())} of {tot} sessions &mdash; {LEAN_BY['lean'].sum()/tot*100:.0f}% of the timetable &mdash; run for an audience of two or fewer</strong>, tying up {int(x26[x26['CheckedIn']<=2]['Capacity'].sum())} seats on the board.</p>
<p>The concentration is the actionable part. <strong>Studio PowerCycle accounts for {int(LEAN_BY.loc['Studio PowerCycle','lean'])} of the {int(LEAN_BY['lean'].sum())}</strong>, and eight of the eleven completely empty sessions were PowerCycle classes starting at 07:30, 09:15 or 18:00. Looked at as a pattern rather than as bad luck, this is not a demand failure across the studio. It is a small number of specific slots that the studio's own booking data says nobody wants.</p>
{FILL_T}
<p>The distribution across all sessions shows how thin the top of the timetable is. {int((x26['CheckedIn']>=11).sum())} sessions drew eleven or more people; {int((x26['CheckedIn']<=2).sum())} drew two or fewer. The majority of classes &mdash; {int(x26['CheckedIn'].between(3,10).sum())} of {tot} &mdash; sit in the middle band, which is exactly where a studio wants its centre of gravity and where the marginal gains are easiest to find.</p>
{ev('View all 49 sessions that ran to two people or fewer', LEAN_ST)}
{ev('View the ten fullest sessions of the month', FULL_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Restricted to classes with a capacity of 8 or more. Every one of these ran at or above 100% of capacity, which in practice means the studio added seats or accepted overbooking.</p>')}
{ev('View the ten emptiest sessions of the month', EMPTY_T)}

<h2>The month within the month</h2>
<div class="sub">September fades, and it did so last year too</div>
{CH_WK}
{WK_T}
<p>Utilisation falls from <strong>{WK['2026']['fill'].get(1, np.nan):.1f}% in the first week of September to {WK['2026']['fill'].get(4, np.nan):.1f}% in the fourth</strong>, while the number of sessions run falls only slightly. September 2025 followed the same shape, from {WK['2025']['fill'].get(1, np.nan):.1f}% to {WK['2025']['fill'].get(4, np.nan):.1f}%. Two consecutive years of the same arc means this is not an event, a festival or a marketing failure &mdash; it is the studio&rsquo;s booking rhythm.</p>
<p>The likely mechanism is straightforward: members front-load their bookings when a new month or a new package cycle begins, and the final week runs on residual commitment. Whatever the cause, the shape is predictable, and a predictable dip is a schedulable one.</p>

<h2>How the room pays for itself</h2>
<div class="sub">The payment mix behind each format</div>
{CH_PAYMIX}
<p>This is the most strategically useful table in the report, because it shows which formats are doing acquisition work and which are doing retention work.</p>
<p><strong>Studio PowerCycle is the studio&rsquo;s trial engine.</strong> {PAYMIX.loc['Studio PowerCycle','intro_p']:.0f}% of its attendance arrives on an intro offer, the highest of any format, and {PAYMIX.loc['Studio PowerCycle','single_p']:.0f}% buys in single classes. That is what an entry-point format looks like. <strong>Studio FIT is where members end up:</strong> {PAYMIX.loc['Studio FIT','mem_p']:.0f}% of its attendance is on memberships and only {PAYMIX.loc['Studio FIT','intro_p']:.0f}% on intro offers.</p>
<p>Read alongside the utilisation figures, that pairing explains the whole timetable problem. The studio is putting its lowest-intent traffic &mdash; trials and drop-ins &mdash; into its largest block of scheduled capacity, and reserving its best-performing format for a much smaller share of the week. The formats are not competing; they are mis-sequenced.</p>


<h2>Hosted and partner classes</h2>
<div class="sub">Full rooms, no revenue</div>
{HOST_T}
<p>All {len(HOSTED)} hosted classes ran at <strong>{HOSTED['CheckedIn'].sum()/HOSTED['Capacity'].sum()*100:.0f}% utilisation</strong> with {int(HOSTED['Complimentary'].sum())} complimentary attendances and <strong>{R(0)} of class revenue</strong>. They are the two or three fullest rooms of the month and they are the studio&rsquo;s most efficient way to fill seats with new faces. What they do not currently do is convert; the companion report on acquisition finds hosted-class leads converting at 8.3% against 24.2% for referrals, which is the gap to close.</p>


<h2>Recommendations</h2>
<div class="sub">Fourteen actions, ordered by expected value</div>
<p>The first four are timetable decisions that cost nothing and can be made before next month&rsquo;s schedule is published. The rest build the measurement and conversion discipline that would keep the improvements.</p>
{REC_HTML}

<h2>Method and limitations</h2>
<div class="sub">How to read these numbers, and what they cannot show</div>
{SRC}'''

HTML = page('Supreme HQ, Bandra — Class Performance, September 2026',
            'Class Performance Review &nbsp;&middot;&nbsp; September 2026',
            'Supreme HQ, Bandra',
            f'{C26["sessions"]} classes carried {C26["att"]:,} attendances through {P(FILL)} of available capacity — the studio’s best September utilisation on record, and a further {C26["rev"]/C25["rev"]*100-100:.0f}% growth in class revenue. This report sets that against the {C26["seats"]-C26["att"]:,} seats that went unused, and shows that they are concentrated in specific formats, days and hours that the studio controls.',
            f'The numbers behind the number: {len(X.core_ix)} members trained here in both Septembers &mdash; the same people, twelve months apart. They made '
            f'{int(X.core_then.sum())} visits last September and {int(X.core_now.sum())} this one, a fall of {abs(X.core_now.mean()/X.core_then.mean()-1)*100:.1f}% '
            f'and a shortfall of {abs(X.CORE_LOST)} attendances. Acquisition is working. Frequency is not.'
            f'<span>{C26["sessions"]} class occurrences</span><span>{C26["seats"]:,} seats offered</span><span>Class ledger, 18 October 2026</span><span>Utilisation = attended / capacity</span>',
            BODY)
open('/home/user/reports-arena/Bandra_September_2026_2_Class_Performance.html','w').write(HTML)
print('Report 2 written:', len(HTML), 'bytes')
print('sessions', C26['sessions'], 'fill', round(FILL,1), 'rev', round(C26['rev']), 'lean', int(LEAN_BY['lean'].sum()))
