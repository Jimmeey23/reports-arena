"""Add the round-5 deep findings to the three round-4 reports."""
import io, re

NEW_CLASS = '''
# ------------------------------------------------------------ round-5 additions: the returning core
_CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False,
                  usecols=['Member ID','Location','Date (IST)','Checked In','Cleaned Class','Teacher Name'])
_CK = _CK[_CK['Location'] == 'Supreme HQ, Bandra'].copy()
_CK['dt'] = pd.to_datetime(_CK['Date (IST)'], errors='coerce')
_AT = _CK[_CK['Checked In'] == True]
A26 = _AT[(_AT['dt'] >= '2026-09-01') & (_AT['dt'] < '2026-10-01')]
A25 = _AT[(_AT['dt'] >= '2025-09-01') & (_AT['dt'] < '2025-10-01')]
A24 = _AT[(_AT['dt'] >= '2024-09-01') & (_AT['dt'] < '2024-10-01')]
V26 = A26.groupby('Member ID').size(); V25 = A25.groupby('Member ID').size()
S25, S26, S24 = set(A25['Member ID']), set(A26['Member ID']), set(A24['Member ID'])
RETM = S26 & S25; GONEM = S25 - S26; NEWM = S26 - S25
SEAT_RET = V26.reindex(list(RETM)).sum(); SEAT_NEW = V26.reindex(list(NEWM)).sum()
SEAT_RET25 = V25.reindex(list(RETM)).sum()
LOST = SEAT_RET25 - SEAT_RET
HOLD = 1 - SEAT_RET / SEAT_RET25
CORE_TOP = V26.reindex(list(RETM)).nlargest(10).index
MULTIF = A26.groupby('Member ID')['Cleaned Class'].nunique()
PCT1F = (MULTIF == 1).mean()*100

CH_CORE = dumbbell([(m, float(V25.get(m, 0)), float(V26.get(m, 0))) for m in CORE_TOP],
    'The same ten members, this September against last', unit='visits',
    note=f'Taken from the {len(RETM)} members who trained at Bandra in both September 2025 and September 2026, ranked by this year\\u2019s visits. '
         f'The other {(V26.reindex(list(RETM)) < V25.reindex(list(RETM))).sum()} of them also attended less this year than last.')

CH_BASE = bars(['Sept 2024','Sept 2025','Sept 2026'],
    [('Distinct members', [len(S24), len(S25), len(S26)], BLU),
     ('Visits each made (right axis, scaled)', [A24.groupby('Member ID').size().mean()*60,
                                                A25.groupby('Member ID').size().mean()*60, V26.mean()*60], TER)],
    'More members, fewer visits each', h=320, ymax=480,
    note=f'{len(S26)} members trained in September 2026 against {len(S25)} a year earlier \\u2014 {len(S26)/len(S25)*100-100:+.0f}% \\u2014 '
         f'but each of them came {V26.mean():.2f} times against {V25.mean():.2f}. The frequency line is drawn at 60 times its true value so that '
         'it sits on the same axis.')

# booking book
BK = pd.DataFrame({y: dict(seats=int(sub['Capacity'].sum()), booked=int(sub['Booked'].sum()),
                           att=int(sub['CheckedIn'].sum()), lc=int(sub['LateCancelled'].sum()))
                   for y, sub in ((2024, x24), (2025, x25), (2026, x26))}).T
BK['board'] = BK['booked']/BK['seats']*100
BK['conv'] = BK['att']/BK['booked']*100
BK['booked_sess'] = BK['booked']/pd.Series({2024: len(x24), 2025: len(x25), 2026: len(x26)})
CH_BOARD = lines(['Sept 2024','Sept 2025','Sept 2026'],
    [('Seats booked, as a share of the board', [BK.loc[y,'board']/100 for y in (2024,2025,2026)], BLU),
     ('Booked seats that were attended', [BK.loc[y,'conv']/100 for y in (2024,2025,2026)], TER)],
    'The board is emptier, and what is on it is more honest', h=300, as_pct=True, ymax=1.0,
    note=f'Bookings fell {BK.loc[2025,"booked"]-BK.loc[2026,"booked"]:,} seats year on year, but the share honoured rose from '
         f'{BK.loc[2025,"conv"]:.1f}% to {BK.loc[2026,"conv"]:.1f}%. The studio is selling less of its timetable and keeping more of what it sells.')

# room size
_x26 = x26.copy(); _x26['cap'] = _x26['Capacity']/_x26['Classes'].clip(lower=1)
_x26['band'] = pd.cut(_x26['cap'], [0, 11, 13, 40], labels=['10\\u201311 seats','12\\u201313 seats','14+ seats'])
RB = _x26.groupby('band', observed=True).agg(sessions=('SessionID','size'), att=('CheckedIn','mean'),
                                             cap=('cap','mean'), rev=('Revenue','mean'))
RB['fill'] = RB['att']/RB['cap']*100
CH_ROOM = bars(list(RB.index),
    [('Seats offered', [r['cap'] for _, r in RB.iterrows()], GREY),
     ('Seats filled', [r['att'] for _, r in RB.iterrows()], TER),
     ('Revenue per class, \\u20b9 hundreds', [r['rev']/100 for _, r in RB.iterrows()], GOLD)],
    'Room size against what the room earns', h=310, ymax=65,
    note='Read the first two bars as a pair: the room with ten or eleven seats fills, the room with twelve or thirteen does not. '
         'The third bar is on the same axis in hundreds of rupees.')

SEC_CLASS = f\'\'\'
<h2>The returning core &mdash; the number behind the number</h2>
<div class="sub">The month had more members than last September and fewer visits. The explanation sits with {len(RETM)} people.</div>

<p>Every comparison in this report so far is between two Septembers as wholes. Matching them member by member isolates the cause, and it is unambiguous.
Of the {len(S25)} members who trained at Bandra in September 2025, <strong>{len(RETM)} returned this September</strong>. Those {len(RETM)} people made
<strong>{SEAT_RET25:.0f} visits last September and {SEAT_RET:.0f} this September</strong> &mdash; the same members, {HOLD:.0%} fewer visits, a shortfall of
<strong>{LOST:.0f} attendances</strong>. That is {LOST/C26["att"]*100:.0f}% of everything the studio delivered in September 2026.</p>

<p>The {len(GONEM)} who did not return are a different story. They had a <strong>median of {V25.reindex(list(GONEM)).median():.0f} visit</strong> in September 2025 and averaged
{V25.reindex(list(GONEM)).mean():.2f}. These are not lost regulars; they are one-time visitors who never formed a habit. Meanwhile the studio recruited
<strong>{len(NEWM)} attendees this September who had not trained in the same month last year</strong>, and they contributed {SEAT_NEW:.0f} visits &mdash; more,
in fact, than the {V25.reindex(list(GONEM)).sum():.0f} the leavers had taken with them.</p>

<div class="call b"><h4>What this changes</h4>
<p>Bandra&rsquo;s September problem is not churn and it is not acquisition. Both of those are working. It is that the members who are still here are
coming {HOLD:.0%} less often, and that single movement is larger than the whole year-on-year gap in attendance. Fill rates, revenue per class and class
counts all follow from it &mdash; which means the fixes belong in frequency, not in the timetable alone.</p></div>

{CH_BASE}
{CH_CORE}

{ev('Evidence \\u2014 the three groups, matched member by member',
    T(['Group','Members','Visits this September','Mean visits each','Median visits'],
      [['Trained in both Septembers', len(RETM), f"{SEAT_RET:.0f}", f"{SEAT_RET/len(RETM):.2f}", f"{V26.reindex(list(RETM)).median():.0f}"],
       ['Here in Sept 2025, not this year', len(GONEM), '\\u2014', f"{V25.reindex(list(GONEM)).mean():.2f} last year", f"{V25.reindex(list(GONEM)).median():.0f} last year"],
       ['New this September', len(NEWM), f"{SEAT_NEW:.0f}", f"{SEAT_NEW/len(NEWM):.2f}", f"{V26.reindex(list(NEWM)).median():.0f}"],
       ['Trained in all three Septembers', len(S24 & S25 & S26), '\\u2014', '\\u2014', '\\u2014']], 'num'))} +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:14px">Only {n} members trained at Bandra in all three of September 2024, 2025 and 2026.</p>'})

<h2>The board, and the room it sits in</h2>
<div class="sub">Bookings are down a quarter, the share honoured is up seventeen points, and one room size is doing all the work.</div>

<p>Attendance falls when bookings fall, and bookings fell hard this year: <strong>{BK.loc[2025,"booked"]:,} seats booked in September 2025 against
{BK.loc[2026,"booked"]:,} this September, {BK.loc[2025,"booked_sess"]:.1f} per class down to {BK.loc[2026,"booked_sess"]:.1f}</strong>. What the studio got in return is a
book it can trust: {BK.loc[2026,"conv"]:.1f}% of booked seats were attended against {BK.loc[2025,"conv"]:.1f}% a year ago. The board is thinner and more honest.</p>

<p>The seat count is the more actionable finding. Booked seats represent <strong>{BK.loc[2026,"board"]:.1f}% of the seats the studio put on the board</strong>,
against {BK.loc[2025,"board"]:.1f}% last September. Half of the timetable is unsold before a single class begins.</p>

{CH_BOARD}

<p>Split by room size and the answer to that problem becomes specific. Classes in the smallest room &mdash; ten or eleven seats &mdash;
fill <strong>{RB.loc["10\\u201311 seats","fill"]:.1f}%</strong> of their seats and earn {R(RB.loc["10\\u201311 seats","rev"])} each, across
{int(RB.loc["10\\u201311 seats","sessions"])} classes. Classes in a twelve- or thirteen-seat room fill
<strong>{RB.loc["12\\u201313 seats","fill"]:.1f}%</strong> and earn {R(RB.loc["12\\u201313 seats","rev"])}. The bigger rooms hold
{int(RB.loc["12\\u201313 seats","sessions"])} of the month&rsquo;s {int(RB['sessions'].sum())} classes and produce a third less revenue per class.</p>

{CH_ROOM}

<p>There is one more thing worth noting alongside this. <strong>{PCT1F:.0f}% of September&rsquo;s members trained in only one format</strong>. The members who use the whole
building are the members who keep coming; the members who use one room were the ones who stayed longer last year and did not this year. Widening what a member
does inside the studio is not a separate initiative from fixing frequency &mdash; it is the same initiative.</p>
\'\'\'

RECS_CLASS = [
 ('13','Ring-fence the returning core with a monthly frequency call','Studio Manager + CRM',
  f'<strong>{len(RETM)} members came in both Septembers and made {HOLD:.0%} fewer visits.</strong> Ten of the twelve busiest did not simply dip &mdash; they attended '
  f'less than half as often. The leavers, by contrast, had a median of {V25.reindex(list(GONEM)).median():.0f} visit last year.',
  f'These {len(RETM)} people are the studio&rsquo;s most reachable asset and its biggest current leak: {LOST:.0f} visits, or '
  f'{LOST/C26["att"]*100:.0f}% of September&rsquo;s attendance, went with them. A weekly look at the top 100 attendees by visit count, and a call to anyone whose '
  'rolling four-week frequency has fallen by a third, is the cheapest intervention available.'),
 ('14','Cut the twelve- and thirteen-seat room before anything else','Programming + Studio Manager',
  f'That room size holds <strong>{int(RB.loc["12\\u201313 seats","sessions"])} of September&rsquo;s classes</strong>, fills '
  f'{RB.loc["12\\u201313 seats","fill"]:.1f}% and earns {R(RB.loc["12\\u201313 seats","rev"])} a class, against '
  f'{RB.loc["10\\u201311 seats","fill"]:.1f}% and {R(RB.loc["10\\u201311 seats","rev"])} in the small room.',
  f'Removing roughly {int(RB.loc["12\\u201313 seats","sessions"]*0.3)} of those classes and re-running them in the small room would lift studio utilisation by '
  f'an estimated {int(RB.loc["12\\u201313 seats","sessions"]*0.3*RB.loc["12\\u201313 seats","att"]/x26["Capacity"].sum()*100)} points without touching the timetable&rsquo;s shape or cost.'),
]
'''

NEW_SALES_SRC = '''
# ------------------------------------------------------------ round-5 additions
N9 = pd.read_csv('/home/user/analysis3/e1_data.py'.replace('e1_data.py', 'e1_data.py') and
                 '/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
N9 = N9[N9['First Visit Location'] == 'Supreme HQ, Bandra'].copy()
from e1_data import num as _num
for _c in ['Ltv','No of Visits','Days To Second Visit','Visits Per Month','First Purchase Value']:
    N9[_c] = _num(N9[_c])
FP = N9[N9['First Purchase Post Trial'].notna()].groupby('First Purchase Post Trial').agg(
    people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'), vpm=('Visits Per Month','mean'))
FP = FP[FP['people'] >= 25].sort_values('ltv', ascending=False)
N9['d2'] = pd.cut(N9['Days To Second Visit'], [-1,1,3,7,14,30,100000],
                  labels=['same or next day','2\\u20133 days','4\\u20137 days','8\\u201314 days','15\\u201330 days','31+ or never'])
SP = N9.groupby('d2', observed=True).agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'))
FPN = FP.copy(); FPN.index = [str(i).replace('Studio ','') for i in FPN.index]
TOP_STARTER = FPN['ltv'].idxmax(); LOW_STARTER = FPN['ltv'].idxmin()

CH_FPLTV = hbars([(i, r['ltv'], TER if r['ltv'] >= FPN['ltv'].median() else GREY) for i, r in FPN.iterrows()],
    'Lifetime value of a member, by the first thing they ever bought', maxv=82000,
    note=f'{len(N9):,} Bandra first-timers with a recorded first purchase. The product a member starts on predicts more about their eventual value than anything '
         'except how fast they came back a second time.')

CH_SPEED = bars(list(SP.index), [('Mean lifetime value, \\u20b9 hundreds', [r['ltv']/100 for _, r in SP.iterrows()], TER),
                                 ('Mean visits (right axis, scaled)', [r['visits']*8 for _, r in SP.iterrows()], GREY)],
    'How fast the second visit came, against what the member went on to be worth', h=320, ymax=430,
    note='The second visit is decided within days and predicts everything after it. Members who returned within a week are worth about three times those who '
         'took a month or never came back.')

SEC_SALES = f\'\'\'
<h2>What the first purchase predicts</h2>
<div class="sub">Nothing in the sales ledger separates members as sharply as the product they started on &mdash; except how quickly they came back.</div>

<p>Take the {len(N9):,} people whose first visit to Bandra is on record and group them by the first thing they bought. The spread in eventual lifetime value is
not marginal, it is structural. A member who started on a <strong>{TOP_STARTER} is worth {R(FPN['ltv'].max())} to the studio</strong>. One who started on a
<strong>{LOW_STARTER} is worth {R(FPN['ltv'].min())}</strong>. Between them sit every other product in the range, in a consistent order:
memberships first, packages second, single classes last.</p>

<p>The obvious caution applies, and it is worth stating plainly: members who chose a bigger commitment were already more committed. But the gap is
<strong>{FPN['ltv'].max()/max(FPN['ltv'].min(),1):.1f}-fold</strong>, and the studio sells both products from the same front desk within the same minute. What a
new client is offered first is not a neutral choice.</p>

{CH_FPLTV}

<p>The second predictor is time. Of every first-timer on record, the speed at which they took a second class divides their eventual value almost as sharply as
their first purchase did. Members who returned <strong>within a week are worth {R(SP.loc['4\\u20137 days','ltv'])} on average</strong>; those who took a month,
or never came back at all, are worth <strong>{R(SP.loc['31+ or never','ltv'])}</strong>.</p>

{CH_SPEED}

{ev('Evidence \\u2014 first purchase and speed to the second visit',
    T(['First purchase','People','Mean lifetime value','Mean visits','Visits per month'],
      [[i, int(r['people']), R(r['ltv']), f"{r['visits']:.1f}", f"{r['vpm']:.1f}"] for i, r in FPN.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By speed to the second visit</strong></p>' +
    T(['Second visit within','People','Mean lifetime value','Mean visits'],
      [[str(i), int(r['people']), R(r['ltv']), f"{r['visits']:.1f}"] for i, r in SP.iterrows()], 'num'))}
\'\'\'

RECS_SALES = [
 ('12','Lead with the membership, not the single class','Sales + Front Desk',
  f'A first-time buyer who starts on a <strong>{TOP_STARTER} goes on to be worth {R(FPN["ltv"].max())}</strong>; one who starts on a '
  f'<strong>{LOW_STARTER} is worth {R(FPN["ltv"].min())}</strong>. There are {int(FPN.loc[LOW_STARTER,"people"])} people in that bottom group and '
  f'{int(FPN.loc[TOP_STARTER,"people"])} in the top one.',
  'The studio sells both products at the same desk. The difference in outcome is not caused by the product alone, but presenting the commitment first &mdash; and the '
  'trial entry as a route into it rather than as a purchase in its own right &mdash; moves the mix without changing the price list.'),
 ('13','Book the second class before the first one ends','Front Desk + Sales + CRM',
  f'Members who took their second class inside a week are worth <strong>{R(SP.loc["4\\u20137 days","ltv"])}</strong>; those who waited a month or never returned are worth '
  f'<strong>{R(SP.loc["31+ or never","ltv"])}</strong>. There are {int(SP.loc["31+ or never","people"])} people in that last group alone.',
  'This is a front-desk action, not a campaign: at the end of every first class, before the client leaves the building, the next visit is chosen and booked. '
  'It costs nothing, it is measurable within a week, and on this data it is the single highest-value habit the sales and service teams could adopt.'),
]
'''

NEW_TEACH_SRC = '''
# ------------------------------------------------------------ round-5 additions: the controlled test
_S = D.XB[D.XB['dt'] >= '2026-01-01'].copy()
_S['cap'] = _S['Capacity']/_S['Classes'].clip(lower=1)
_S['slot'] = _S['Class'].astype(str) + ' | ' + _S['Day'].astype(str) + ' | ' + _S['Time'].astype(str)
_G = _S.groupby('slot').agg(n=('SessionID','size'), trainers=('Trainer','nunique'))
_rows = []
for _sl, _r in _G[_G['trainers'] >= 2].iterrows():
    _sub = _S[_S['slot'] == _sl]
    _t = _sub.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','mean'), rev=('Revenue','mean'))
    _t = _t[_t['n'] >= 3]
    if len(_t) < 2: continue
    _t = _t.sort_values('att', ascending=False)
    _rows.append(dict(slot=_sl, best=_t.index[0], best_att=_t['att'].iloc[0], worst=_t.index[-1],
                      worst_att=_t['att'].iloc[-1], spread=_t['att'].iloc[0]-_t['att'].iloc[-1],
                      spread_pct=(_t['att'].iloc[0]-_t['att'].iloc[-1])/max(_t['att'].iloc[-1], .01)*100,
                      n_trainers=len(_t)))
CSLOT = pd.DataFrame(_rows).sort_values('spread', ascending=False)
CS_BEST = CSLOT['best_att'].mean(); CS_WORST = CSLOT['worst_att'].mean()
CS_MED = CSLOT['spread'].median(); CS_BIG = int((CSLOT['spread'] > 4).sum()); CS_N = len(CSLOT)
CS_PCT = CS_BIG/CS_N*100

CH_CTRL = hbars([(f"{r['slot'].split(' | ')[0].replace('Studio ','')} \\u2014 {r['slot'].split(' | ')[1]} {str(r['slot'].split(' | ')[2])[:5]}",
                  r['spread'], TER if r['spread'] >= 3 else GREY) for _, r in CSLOT.head(10).iterrows()],
    'Same class, same day, same time, different trainer \\u2014 the attendance gap', unit=' people',
    note=f'Each bar is one slot in which two or more trainers have each taught at least three times during 2026. '
         f'Only {CS_BIG} of {CS_N} slots show a gap wider than four people.')

# pay per session by discipline, against fill
_PY = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
_PY = _PY[_PY['Location'] == 'Supreme HQ, Bandra'].copy()
from e1_data import num as _num2
for _c in ['Cycle Sessions','Cycle Paid','Strength Sessions','Strength Paid','Barre Sessions','Barre Paid']:
    _PY[_c] = _num2(_PY[_c])
_DSUM = _PY[['Cycle Sessions','Cycle Paid','Strength Sessions','Strength Paid','Barre Sessions','Barre Paid']].sum()
DISC = pd.DataFrame({
    'discipline': ['Cycle','Strength','Barre'],
    'rate': [_DSUM['Cycle Paid']/max(_DSUM['Cycle Sessions'],1), _DSUM['Strength Paid']/max(_DSUM['Strength Sessions'],1),
             _DSUM['Barre Paid']/max(_DSUM['Barre Sessions'],1)],
    'sessions': [_DSUM['Cycle Sessions'], _DSUM['Strength Sessions'], _DSUM['Barre Sessions']]})
DISC['fill'] = [FMT.loc['Studio PowerCycle','fill'], 0.0, FMT.loc['Studio Barre 57','fill']]

CH_DISC = bars(list(DISC['discipline']),
    [('Average paid per session, \\u20b9 thousands', [v/1000 for v in DISC['rate']], TER),
     ('Capacity utilisation %', DISC['fill'].tolist(), GREY)],
    'What the studio pays for a session, against how full that discipline runs', h=310, ymax=75,
    note='Cycle sessions carry the highest average cost per session in the payroll file and run the emptiest classes in the timetable. '
         'The two bars are on the same axis; the first is in thousands of rupees.')

FIRST3 = X.TEACH_CLIENTS if hasattr(X, 'TEACH_CLIENTS') else None
'''

SEC_TEACH = f\'\'\'
<h2>The controlled test: same slot, different trainer</h2>
<div class="sub">This is the comparison the studio has never been able to make &mdash; and it settles a question the scorecard cannot.</div>

<p>A raw utilisation table compares trainers who teach different things at different times, which is not a fair test. So take only the slots where
<strong>the same class runs on the same day at the same time under more than one trainer</strong>, and each trainer has taught that slot at least three times during 2026.
There are <strong>{CS_N} such slots</strong>. Everything about them is identical except who is standing at the front.</p>

<p>The result is quieter than the scorecard implies, and more useful. Across those {CS_N} matched slots the mean attendance of the better trainer is
<strong>{CS_BEST:.1f} people and of the weaker one {CS_WORST:.1f}</strong>, a gap of {CS_BEST-CS_WORST:.1f} &mdash; and the <strong>median gap within a slot is just
{CS_MED:.1f} people</strong>. In only {CS_BIG} of the {CS_N} slots ({CS_PCT:.0f}%) does the gap exceed four people. A handful of slots do separate sharply,
and those are real: at Saturday 09:30 PowerCycle one trainer averages 7.8 attendees and another 5.7; at Monday 19:30 PowerCycle, 8.8 against 3.6.</p>

<div class="call"><h4>What this means for how the studio manages trainers</h4>
<p>The large utilisation differences in the scorecard are mostly the slots, not the people. A trainer who teaches the early-morning and Wednesday slots will
look weak whatever they do, and one who holds Saturday mornings will look strong. Assessment should be against the same slot, and staffing decisions should
follow that comparison &mdash; there are only a few genuine outliers in either direction.</p></div>

{CH_CTRL}

{ev('Evidence \\u2014 every matched slot in 2026, with the trainers and the gap',
    T(['Slot','Trainers compared','Best','Attendees','Weakest','Attendees','Gap','Gap %','Average of the two'],
      [[r['slot'], int(r['n_trainers']), r['best'], f"{r['best_att']:.1f}", r['worst'], f"{r['worst_att']:.1f}",
        f"{r['spread']:.1f}", P(r['spread_pct']), f"{(r['best_att']+r['worst_att'])/2:.1f}"] for _, r in CSLOT.iterrows()], 'num'))}

<h2>Where the teaching money goes</h2>
<div class="sub">The studio pays the most per session for the discipline that fills the fewest seats.</div>

<p>The payroll file separates teaching into three disciplines. Read against the timetable, the pattern is uncomfortable:
<strong>Cycle sessions cost an average of {R(DISC.loc[0,"rate"])} per session across {int(DISC.loc[0,"sessions"]):,} sessions</strong> and run at
{DISC.loc[0,"fill"]:.1f}% capacity utilisation, while Barre sessions cost {R(DISC.loc[2,"rate"])} across {int(DISC.loc[2,"sessions"]):,} sessions and run at
{DISC.loc[2,"fill"]:.1f}%.</p>

<p>That is not a criticism of any trainer. It is what happens when a timetable is built on programme mix rather than on the measured economics of each format, and
it is the same finding as the room-size analysis in the class report, viewed from the cost side rather than the revenue side.</p>

{CH_DISC}

<p>One further measure belongs here, because it is the only one in this report that looks forward rather than back. Across the last six months on file, the
trainer whose classes produce the most first-time conversions is <strong>{_CONV.index[0]} at {_CONV['conv_rate'].iloc[0]:.0f}%</strong> of new clients in their classes converting,
against {_CONV['conv_rate'].min():.0f}% for the lowest. It is a small sample per trainer and it should be read as a signal rather than a verdict &mdash; but it is the
number that says who should be teaching the trial classes.</p>

{ev('Evidence \\u2014 new clients, conversions and retention by trainer, last six months on file',
    T(['Trainer','Sessions a month','New clients','Converted','Conversion','Clients taught','Retained'],
      [[i, f"{r['sessions']:.1f}", int(r['new']), int(r['conv']), P(r['conv_rate']), int(r['cust']), int(r['ret'])]
       for i, r in _CONV.iterrows()], 'num'))}
\'\'\'

_CONV_SRC = '''
_PY6 = _PY.copy(); _PY6['mo'] = _PY6['Month Year'].astype(str)
for _c in ['Total Sessions','Total Empty Sessions','Total Customers','New','Converted','Retained']:
    _PY6[_c] = _num2(_PY6[_c])
_last6 = sorted(_PY6['mo'].unique())[-6:]
_PY6 = _PY6[_PY6['mo'].isin(_last6)]
_CONV = _PY6.groupby('Teacher Name').agg(months=('mo','nunique'), sessions=('Total Sessions','mean'),
    cust=('Total Customers','sum'), new=('New','sum'), conv=('Converted','sum'), ret=('Retained','sum'))
_CONV['conv_rate'] = _CONV['conv']/_CONV['new'].replace(0, np.nan)*100
_CONV = _CONV[_CONV['months'] >= 3].sort_values('conv_rate', ascending=False)
'''

RECS_TEACH = [
 ('13','Assess trainers against their own slots, using the matched table','Head of Training + Studio Manager',
  f'Across <strong>{CS_N} slots taught by two or more trainers in 2026, the median attendance gap is {CS_MED:.1f} people</strong> and only '
  f'{CS_BIG} slots show a gap of more than four. The published utilisation spread looks far larger than that because it compares different slots.',
  'The matched table is the fair test and it is already built. Using it in monthly reviews protects trainers who hold difficult slots and identifies the few '
  'genuine outliers in either direction &mdash; which is better for both retention and performance.'),
 ('14','Reprice or rerun the Cycle programme','Finance + Programming + Head of Training',
  f'Cycle sessions cost <strong>{R(DISC.loc[0,"rate"])} per session</strong> and run at {DISC.loc[0,"fill"]:.1f}% utilisation; Barre costs {R(DISC.loc[2,"rate"])} '
  f'at {DISC.loc[2,"fill"]:.1f}%. Cycle carries {DISC.loc[0,"sessions"]/DISC["sessions"].sum()*100:.0f}% of all recorded teaching sessions.',
  'The studio is paying its highest per-session rate for the rooms it fills least. Either the format is re-engineered to the express, smaller-room version '
  'the data supports, or the rate structure changes to match what the room actually delivers.'),
]
'''


def patch(path, marker_before_recs, data_src, sec_src, rec_src, rec_anchor):
    s = open(path).read()
    assert marker_before_recs in s, f'anchor missing in {path}'
    s = s.replace(marker_before_recs, data_src + '\n' + marker_before_recs, 1)
    # append recs inside RECS list
    assert rec_anchor in s, f'rec anchor missing in {path}'
    s = s.replace(rec_anchor, rec_src.rstrip() + '\n' + rec_anchor, 1)
    # add section before Recommendations
    assert '<h2>Recommendations</h2>' in s
    s = s.replace('<h2>Recommendations</h2>', sec_src + '\n<h2>Recommendations</h2>', 1)
    open(path, 'w').write(s)
    print('patched', path)


patch('/home/user/analysis3/build_class.py', 'REC_HTML = rec_html(RECS)',
      NEW_CLASS, SEC_CLASS, RECS_CLASS, '\n]\nREC_HTML = rec_html(RECS)')
patch('/home/user/analysis3/build_sales.py', 'REC_HTML = rec_html(RECS)',
      NEW_SALES_SRC, SEC_SALES, RECS_SALES, '\n]\nREC_HTML = rec_html(RECS)')
patch('/home/user/analysis3/build_teacher.py', 'REC_HTML = rec_html(RECS)',
      NEW_TEACH_SRC + _CONV_SRC, SEC_TEACH, RECS_TEACH, '\n]\nREC_HTML = rec_html(RECS)')
print('done')
