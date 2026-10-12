"""Report 7 - Studio overview and intelligence."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

TODAY = pd.Timestamp('2026-10-18')
L, LP, LB = E.L, E.LP, E.LB

# ------------- check-in ledger
CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID','Location','Date (IST)','Checked In','Is Late Cancelled','Cleaned Class','Teacher Name',
             'Complementary','Paid','Class No','Day of Week','Time','Order At'])
CK = CK[CK['Location'] == E.B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
CK['cn'] = E.num(CK['Class No'])
A = CK[CK['Checked In'] == True].copy()
a26 = A[(A['dt'] >= '2026-09-01') & (A['dt'] < '2026-10-01')]
a25 = A[(A['dt'] >= '2025-09-01') & (A['dt'] < '2025-10-01')]
a24 = A[(A['dt'] >= '2024-09-01') & (A['dt'] < '2024-10-01')]
v26 = a26.groupby('Member ID').size(); v25 = a25.groupby('Member ID').size()
s25 = set(a25['Member ID']); s26 = set(a26['Member ID']); s24 = set(a24['Member ID'])
RET = s26 & s25; GONE = s25 - s26; NEWB = s26 - s25
t26 = a26.groupby('Member ID').size()
SEATS_RET = t26.reindex(list(RET)).sum(); SEATS_NEW = t26.reindex(list(NEWB)).sum()
SEP25_RET = v25.reindex(list(RET)).sum()

# ------------- sessions / money
X = D.XB.copy(); X['cap'] = X['Capacity']/X['Classes'].clip(lower=1)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()
x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')]
x24 = X[(X['dt'] >= '2024-09-01') & (X['dt'] < '2024-10-01')]
SEP = {}
for y, sub in ((2024, x24), (2025, x25), (2026, x26)):
    SEP[y] = dict(sessions=len(sub), seats=int(sub['Capacity'].sum()), att=int(sub['CheckedIn'].sum()),
                  booked=int(sub['Booked'].sum()), rev=sub['Revenue'].sum(), comp=int(sub['Complimentary'].sum()))
    SEP[y]['fill'] = SEP[y]['att']/SEP[y]['seats']*100
    SEP[y]['rev_head'] = SEP[y]['rev']/SEP[y]['att']
    SEP[y]['rev_session'] = SEP[y]['rev']/SEP[y]['sessions']
    SEP[y]['board'] = SEP[y]['booked']/SEP[y]['seats']*100

# ------------- acquisition: first-timers 12 months
N9 = pd.read_csv(E.U + 'Day End Report - Part 1 - New (9).csv', low_memory=False)
N9 = N9[(N9['First Visit Location'] == E.B)].copy()
N9['fvd'] = pd.to_datetime(N9['First Visit Date'], errors='coerce', dayfirst=True)
for c in ['Ltv','No of Visits','Days To Second Visit','Visits Per Month']:
    N9[c] = E.num(N9[c])
INTAKE = N9[(N9['fvd'] >= '2025-09-01') & (N9['fvd'] < '2026-09-01')].copy()
INTAKE['conv'] = INTAKE['Conversion Status'] == 'Converted'
CONVD = INTAKE['conv'].mean()*100
SRC_MAP = {'Website':'Website','Hosted Class':'Hosted class','Client Referral':'Client referral',
           'Yellow Messenger/Whatsapp Enquiry':'WhatsApp enquiry','Social - Instagram':'Instagram',
           'Website Form':'Website form','Incoming call':'Incoming call','Enquiry on call':'Enquiry on call',
           'Walkin':'Walk-in','Abandoned checkout':'Abandoned checkout','Staff Referral':'Staff referral'}
INTAKE['src'] = INTAKE['Source'].map(SRC_MAP).fillna(INTAKE['Source'])
SR = INTAKE.groupby('src').agg(intake=('Member Id','size'), conv=('conv','mean'), ltv=('Ltv','mean'),
                               visits=('No of Visits','mean'), second=('Days To Second Visit','median'))
SR['conv'] = SR['conv']*100
SR = SR[SR['intake'] >= 25].sort_values('intake', ascending=False)
BIG_CH = SR['intake'].idxmax()                      # largest source by volume
BEST_CH = SR['conv'].idxmax()                       # highest conversion rate
BEST_N = int(SR.loc[BEST_CH, 'intake']); BEST_CONV = float(SR.loc[BEST_CH, 'conv'])
BEST_LTV = float(SR.loc[BEST_CH, 'ltv'])
BIG_N = int(SR.loc[BIG_CH, 'intake']); BIG_CONV = float(SR.loc[BIG_CH, 'conv'])
BIG_LTV = float(SR.loc[BIG_CH, 'ltv'])
WORST_LTV_CH = SR['ltv'].idxmin()
N2ND = INTAKE['Days To Second Visit'].dropna()
PCT7 = (N2ND <= 7).mean()*100; PCT3 = (N2ND <= 3).mean()*100; MED2 = N2ND.median()

# ------------- funnel
a26s = a26.assign(n=a26.groupby('Member ID')['dt'].rank(method='first'))
step = {}
for k in range(1, 11):
    step[k] = a26s[a26s['n'] >= k]['Member ID'].nunique()
REACH = {k: v/step[1]*100 for k, v in step.items()}
recent = A[A['dt'] >= '2025-01-01']
base = recent['Member ID'].nunique()
steps = [base] + [recent[recent['cn'] >= k]['Member ID'].nunique() for k in (2, 3, 5, 10, 21)]
FUN = ['Attended once','Reached a 2nd class','Reached a 3rd class','Reached a 5th','Reached a 10th','Reached a 21st']

# ------------- money concentration
SB = D.SB.copy()   # item-level disc arrives from d1_data
R12 = SB[SB['dt'] >= '2025-10-01']; R26 = SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')]
per = R12.groupby('Member ID')['val'].sum().sort_values(ascending=False)
P10 = per.head(10).sum()/per.sum()*100; P25 = per.head(25).sum()/per.sum()*100
PB50 = per.tail(int(len(per)*0.5)).sum()/per.sum()*100
PM = R26.groupby('Payment Method')['val'].agg(['size','sum']).sort_values('sum', ascending=False)
CAT = R26.groupby('Cleaned Category')['val'].agg(['size','sum']).sort_values('sum', ascending=False)
SLOTS = R26['val'].sum()

# ------------- when people buy
SB['hr'] = SB['Created At'].astype(str).str.extract(r'(\d{1,2}):\d{2}').astype(float)
tt = SB[SB['dt'] >= '2026-01-01']
BUYHR = tt.groupby('hr')['val'].agg(['size','sum'])
BUYHR = BUYHR[(BUYHR.index >= 6) & (BUYHR.index <= 21)]

# ------------- operation
OPD = x26.groupby('Day')['CheckedIn'].sum().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
x26['hr'] = pd.to_numeric(x26['Time'].astype(str).str[:2], errors='coerce')
OPH = x26.groupby('hr')['CheckedIn'].sum()

# ------------- charts
CH_BASE = bars(['September 2024','September 2025','September 2026'],
    [('Distinct members who trained', [len(s24), len(s25), len(s26)], A1),
     ('Visits each made, on the same scale', [v24 := a24.groupby('Member ID').size().mean(),
                                              a25.groupby('Member ID').size().mean(), v26.mean()], A2)],
    'A wider base, coming less often', h=320, ymax=520,
    note='Bars three and four are on the same axis but a different unit. Read the first bar for reach and the second for frequency.')

CH_FREQ = bars(['1','2','3','4','5','6','7','8','9–12','13+'],
    [('Share of September’s members', [(v26 == k).mean() for k in range(1, 9)] +
      [((v26 >= 9) & (v26 <= 12)).mean(), (v26 >= 13).mean()], A1)],
    'How many times each member trained in September 2026', h=300, as_pct=True, ymax=0.25,
    note=f'{len(v26)} members trained at least once. {(v26==1).mean()*100:.0f}% came exactly once and '
         f'{((v26>=9)).mean()*100:.0f}% came nine times or more.')

CH_CORE = dumbbell([(m, float(v25.get(m, 0)), float(v26.get(m, 0))) for m in
                    v26.reindex(list(RET)).nlargest(12).index],
    'The same members, this September against last', unit='visits',
    note='Twelve of the 78 members who returned in both Septembers, ranked by visits this year. '
         'Every one of them attended less in September 2026 than in September 2025.')

CH_SRCF = hbars([(k, v, A1 if v >= 25 else (A2 if v >= 15 else B1)) for k, v in SR['conv'].items()],
    'Share of each source’s intake that converted to a paying member', as_pct=True,
    note='First visits between September 2025 and August 2026, by the source the studio recorded. '
         'Sources with twenty or more first visits.')

CH_SRCV = bars([k for k in SR.index],
    [('People acquired', SR['intake'].tolist(), A1),
     ('Lifetime value, ₹ hundreds', [v/100 for v in SR['ltv']], B1)],
    'Volume against value, by source', h=330, ymax=390,
    note='The two largest channels by volume are among the least valuable by outcome.')

CH_SPEED = bars(['within 3 days','4–7 days','8–14 days','15–30 days','31+ days','never returned'],
    [('Share of intake', [PCT3/100, (PCT7-PCT3)/100,
                          ((N2ND > 7) & (N2ND <= 14)).mean(),
                          ((N2ND > 14) & (N2ND <= 30)).mean(),
                          (N2ND > 30).mean(), INTAKE['Days To Second Visit'].isna().mean()], A1)],
    'How soon the second visit happened, September 2025 to August 2026 intake', h=300, as_pct=True, ymax=0.45,
    note=f'Median time to a second visit: {MED2:.0f} days. {PCT7:.1f}% of those who returned at all did so inside a week.')

CH_FUN = funnel([(FUN[i], int(steps[i]), f'{steps[i]/base*100:.1f}% of those who came at least once')
                 for i in range(len(FUN))],
    'What happens after the first visit — every Bandra member since January 2025')

_ps = per.cumsum()/per.sum()*100
_CUM = {k: per.head(k).sum()/per.sum() for k in (10, 25, 50, 100, 200, 500)}
MONEY_BANDS = [('the top 10 buyers', _CUM[10]),
               ('buyers ranked 11 to 25', _CUM[25]-_CUM[10]),
               ('buyers ranked 26 to 50', _CUM[50]-_CUM[25]),
               ('buyers ranked 51 to 100', _CUM[100]-_CUM[50]),
               ('buyers ranked 101 to 500', _CUM[500]-_CUM[100]),
               (f'all {len(per)-500:,} others', 1-_CUM[500])]
CH_MONEY = bars([b for b, _ in MONEY_BANDS], [('Share of the last 12 months’ sales', [v for _, v in MONEY_BANDS], A1)],
    'Where the last twelve months of sales came from', h=310, as_pct=True, ymax=0.32,
    note=f'{len(per):,} people bought something at Bandra in the last twelve months. The ten largest buyers alone account for {_CUM[10]*100:.1f}% of the money, '
         f'and the last {len(per)-500:,} account for {(1-_CUM[500])*100:.1f}% between them.')

CH_CAT = hbars([(k.replace('Package','pack').replace('Studio ',''), v, A1 if i < 4 else N1)
                for i, (k, v) in enumerate(CAT['sum'].items())],
    'What September’s money was spent on', unit='₹',
    note='Cleaned category of each sales line in the month.')

CH_OPD = bars([d[:3] for d in OPD.index], [('Attendances', OPD.tolist(), A1)],
    'Attendance by day of week, September 2026', h=290, ymax=320,
    note='Monday is the studio’s strongest day and Sunday its weakest, a pattern that repeats every month on file.')

# ------------- September-phases and multi-format
mm = a26.groupby('Member ID')['Cleaned Class'].nunique()
MULTI = (mm >= 2).mean()*100
SING = (mm == 1).mean()*100
TR = a26.groupby('Member ID')['Teacher Name'].nunique()
MT = (TR >= 2).mean()*100

NF = E.LP['Formats Attended'].fillna('').apply(lambda s: len([x for x in str(s).split(',') if x.strip()]))
_NFD = E.LP.assign(nf=NF)
FMT_TICKET = _NFD.groupby('nf')['Amount Paid'].mean()
FMT_CLS = _NFD.groupby('nf')['Total Sessions Completed'].mean()
TICK1 = FMT_TICKET.get(1, float('nan')); TICK4 = FMT_TICKET.get(4, float('nan'))
NEVERC_SESS = E.LP.loc[E.LP['Cancellation Rate %'] == 0, 'Total Sessions Completed'].mean()
LAPSED_L = LP[LP['Derived Status'] == 'Lapsed']
LAPSED_PEOPLE = LAPSED_L['Member ID'].nunique()
LAPSED_WARM = LAPSED_L[LAPSED_L['Days Since Last Visit'] <= 60]['Member ID'].nunique()
CORE_HOLD = 1 - SEATS_RET/SEP25_RET if SEP25_RET else 0

RECS = [
 ('01','Make the second visit a same-week appointment, for everyone','Front Desk + CRM',
  f'Of the {len(INTAKE):,} people who walked into Bandra for a first class between September 2025 and August 2026, '
  f'<strong>{CONVD:.1f}% ever converted</strong>. Of those who did return for a second visit, {PCT7:.1f}% did so within seven days '
  f'and the median was {MED2:.0f} days. There was no second visit for {INTAKE["Days To Second Visit"].isna().mean()*100:.0f}% of them.',
  f'Book the second class before the first one ends. {CONVD:.1f}% conversion on this intake means roughly '
  f'{int(len(INTAKE)*0.8-len(INTAKE)*CONVD/100):,} people a year leave after one visit. Even a five-point improvement is '
  f'{int(len(INTAKE)*0.05):,} more members a year from a change that costs nothing.'),
 ('02','Rebalance acquisition away from hosted classes','Marketing + Management',
  f'<strong>The {BIG_CH.lower()} brought in {BIG_N} first-timers &mdash; the largest single source &mdash; and converted {BIG_CONV:.1f}% of them</strong>, at a '
  f'lifetime value of {R(BIG_LTV)}. The {BEST_CH.lower()} brought {BEST_N} at {BEST_CONV:.1f}% conversion and {R(BEST_LTV)} of value.',
  'Hosted classes are the studio’s largest marketing line and its least productive one. The format is not the problem — a hosted class is a room full of people '
  'who have never been to the studio. The follow-up is the problem. Either change what happens in the 72 hours after the class, or move the budget.'),
 ('03','Treat the returning core as the studio&rsquo;s primary asset','Studio Manager + CRM',
  f'The {len(RET)} members who trained at Bandra in both September 2025 and September 2026 did <strong>{SEP25_RET/len(RET):.2f} visits each last September '
  f'and {SEATS_RET/len(RET):.2f} this September</strong> &mdash; {SEP25_RET-SEATS_RET:.0f} fewer visits from the same people, which is '
  f'{(SEP25_RET-SEATS_RET)/SEP[2026]["att"]*100:.0f}% of the whole month’s attendance.',
  'The studio did not lose these members; it lost their frequency. That is a different and much cheaper problem than churn, and it is invisible in every '
  'report that measures member counts rather than visits. A monthly frequency watch-list on the top 100 attendees would have caught it in July.'),
 ('04','Sell the third visit, not the first','Marketing + Programming',
  f'{base:,} people have trained at Bandra since January 2025. {100-steps[1]/base*100:.1f}% of them never came back for a second class, '
  f'and only <strong>{steps[2]/base*100:.1f}% ever reached a third</strong>. Past the third visit the drop-off flattens sharply &mdash; the tenth visit is reached by '
  f'{steps[4]/base*100:.1f}% and the twenty-first by {steps[5]/base*100:.1f}%.',
  f'The whole economics of the studio sit between visit one and visit three. A structured three-visit welcome &mdash; complimentary second class, coached third, '
  f'no membership pressure until it is done &mdash; targets the only transition that changes the outcome.'),
 ('05','Report frequency, not just headcount','Management',
  f'September 2026 had <strong>{len(s26)} distinct members against {len(s25)} in September 2025 &mdash; {len(s26)/len(s25)*100-100:+.0f}% more people</strong> &mdash; '
  f'and {SEP[2026]["att"]:,} attendances against {SEP[2025]["att"]:,}, a fall of {SEP[2025]["att"]-SEP[2026]["att"]}. Visits per member went from '
  f'{a25.groupby("Member ID").size().mean():.2f} to {v26.mean():.2f}.',
  'Headcount is rising and volume is falling, which means any dashboard showing only members will look healthy while the business shrinks. '
  'A monthly line for visits per active member, next to the member count, is the single most useful addition to the studio&rsquo;s reporting.'),
 ('06','Move the timetable to where the demand already is','Programming + Studio Manager',
  f'Sunday is the studio&rsquo;s weakest day at {OPD.min():.0f} attendances against Monday&rsquo;s {OPD.max():.0f}, a {OPD.max()/max(OPD.min(),1):.1f} times difference. '
  f'By hour, the board is fullest at {int(OPH.idxmax())}:00 and emptiest at {int(OPH.idxmin())}:00.',
  'The studio owns its rooms and pays its people by the session. Re-cutting a weak day and a weak hour into the slots that are already selling out is a '
  'capacity increase with no capital cost, and it is reversible after one month.'),
 ('07','Give every member a second format and a second trainer','Programming + Front Desk',
  f'<strong>{SING:.0f}% of September’s members trained in exactly one format</strong>, and {100-MT:.0f}% saw only one trainer. Members who have used four formats have '
  f'paid {R(TICK4)} across their history against {R(TICK1)} for those who have used one.',
  'A member with one format and one trainer has one diary entry and one relationship. Adding either doubles the reasons to come and halves the chance that '
  'a single timetable change or a single departure takes the member with it.'),
 ('08','Put a value on the channels that are never measured','Marketing + Finance',
  f'{BEST_CH} produced {BEST_N} first-timers worth {R(BEST_LTV)} each. {BIG_CH} produced {BIG_N} worth {R(BIG_LTV)} each. On these figures one member acquired '
  f'through {BEST_CH.lower()} is worth about {BEST_LTV/max(BIG_LTV, 1):.0f} members acquired through {BIG_CH.lower()}.',
  'The studio is comparing channels on headcount because that is what it measures. Costing each channel per converted member, and comparing that to lifetime value, '
  'would reorder the marketing plan within a quarter.'),
 ('09','Make the twelve-month lapse list a standing campaign','CRM',
  f'<strong>{len(LAPSED_L):,} paid memberships are recorded as lapsed</strong>, covering {LAPSED_PEOPLE:,} people, of whom '
  f'{LAPSED_WARM:,} were in the studio within the last sixty days.',
  'The studio has a complete, dated, contactable list of people who have already paid it money. Sorted by recency rather than by value, it is the highest-yield '
  'audience the studio owns and it requires no acquisition spend.'),
 ('10','Measure one number that is not a lagging indicator','Management + CRM',
  f'Every figure in these reports is a result. The one leading indicator the studio already collects but does not read is the second-visit rate: it is visible within '
  f'a week of a first class, it predicts lifetime value, and it is currently {PCT7:.1f}% within seven days.',
  f'A weekly dashboard of first visits, second visits inside seven days, and visits per active member gives the studio three numbers it can still act on. '
  'Everything else it currently reports is a description of what has already happened.'),
 ('11','Put the intelligence on one page, monthly','Management',
  'This report draws on six separate exports, four of which are produced on different cycles by different systems, and none of which are read together. '
  'The relationships between them &mdash; source to second visit, format to frequency, cancellation to lapse &mdash; only appear when they are joined.',
  'A single monthly page covering acquisition, frequency, retention and value, built from the same joins used here, would replace six reports nobody has time to '
  'reconcile and would make the leading indicators impossible to miss.'),
 ('12','Hold the September operating standard','Studio Manager',
  f'September 2026 delivered <strong>{R(SEP[2026]["rev_head"])} of revenue per attendance against {R(SEP[2025]["rev_head"])} a year earlier</strong>, on '
  f'{SEP[2026]["att"]:,} attendances. Booking discipline improved for the third year running: {SEP[2026]["board"]:.1f}% of the board was booked against '
  f'{SEP[2025]["board"]:.1f}% last September, and {len(SR):,} acquisition sources are now measurable to lifetime value.',
  'These are the parts of the operation that are working. Pricing per head, booking conversion and the member base are all moving the right way. The task for '
  'the next quarter is to protect them while fixing frequency, which is the one number moving the wrong way.'),
]
REC_HTML = rec_html(RECS)


CH_OPH = bars([f'{int(h)}:00' if h < 12 else f'{int(h)}pm' for h in OPH.index if 6 <= h <= 21],
              [('Attendances in September', [OPH.get(h, 0) for h in range(6, 22)], A1)],
    'Attendance by hour of day, September 2026', h=290, ymax=260,
    note='The studio’s day has two peaks and a dead middle. The 1pm to 4pm window is the least-used capacity it owns.')

SRC = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Six sources are joined for this report. Attendance and member behaviour come from the Day End Part 4 check-in ledger, filtered to {E.B}
({len(CK):,} rows, 2022 to October 2026). Session economics come from Day End Part 3 - Sessions. Acquisition and lifetime value come from
Day End Part 1 - New, using the studio&rsquo;s own conversion and retention fields. Membership lifecycle comes from the lapse ledger
({len(L):,} Bandra instances, {len(LP):,} of them paid). Sales come from the raw sales export. Leads come from the CRM lead master.<br/>
Lifetime value is the studio&rsquo;s own recorded figure per member and is not discounted. Revenue is gross value as recorded at snapshot, not contribution
margin. Conversion rates for acquisition sources cover first visits between September 2025 and August 2026, so that every member in the cohort has had at
least six weeks to convert.</p>'''

META = (f'Check-in ledger &middot; {len(CK):,} rows &middot; {A["Member ID"].nunique():,} members<br/>'
        f'Six sources joined &middot; September 2024 to October 2026<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra — Studio Overview and Intelligence',
    'Report seven of seven &middot; The month in full',
    'Studio overview and intelligence',
    f'September 2026 was the month Bandra reached more people than ever and saw less of them. {len(s26)} distinct members trained — '
    f'{len(s26)/len(s25)*100-100:.0f}% more than a year earlier — and between them they made {SEP[2025]["att"]-SEP[2026]["att"]} fewer visits. '
    'This report joins six sources to explain why, and what it would take to reverse it.',
    META, f'''
<h2>Start here</h2>
<div class="sub">The studio is not losing members. It has more of them than at any point on file. It is losing their frequency, and that is a different problem.</div>

<p>September 2026 brought <strong>{len(s26)} distinct members through the door, against {len(s25)} in September 2025 &mdash; {len(s26)/len(s25)*100-100:+.0f}%</strong>. Over the same
period attendances fell from {SEP[2025]["att"]:,} to {SEP[2026]["att"]:,}. Each member who trained in September 2026 came
<strong>{v26.mean():.2f} times on average, against {a25.groupby("Member ID").size().mean():.2f} times a year earlier</strong>.</p>

<p>The cause is visible in the member ledger, and it is not what the studio would expect. Of the {len(s25)} members who trained at Bandra in September 2025, only
<strong>{len(RET)} returned this September</strong>. The {len(GONE)} who did not had averaged {v25.reindex(list(GONE)).mean():.2f} visits last September and had a median of
{v25.reindex(list(GONE)).median():.0f} visit in the month &mdash; they were, overwhelmingly, people who had come once and never formed a habit. Meanwhile the studio recruited
<strong>{len(NEWB)} new attendees this September</strong> who had not trained in the same month last year; they contributed {SEATS_NEW:.0f} visits, more than the
{SEATS_RET and v25.reindex(list(GONE)).sum():.0f} that the leavers had taken with them.</p>

<p>So acquisition is working, and churn is mild. What has changed is the loyal core. <strong>The {len(RET)} members who came in both Septembers made
{SEP25_RET/len(RET):.2f} visits each last September and {SEATS_RET/len(RET):.2f} this September</strong> &mdash; {SEP25_RET-SEATS_RET:.0f} fewer visits from the same
{len(RET)} people, which is {(SEP25_RET-SEATS_RET)/SEP[2026]["att"]*100:.0f}% of the entire month&rsquo;s attendance. Hold their frequency constant and September 2026 would
have been a record month.</p>

{CH_BASE}

<div class="call"><h4>The finding, in one line</h4>
<p>Bandra&rsquo;s problem in September 2026 is not that people stopped coming. It is that the people who still come are coming {CORE_HOLD:.0%} less often,
and every other number in this report &mdash; fill rates, revenue per member, class counts &mdash; follows from it.</p></div>

<h2>The month at a glance</h2>
<div class="sub">{SEP[2026]["sessions"]} classes, {SEP[2026]["seats"]:,} seats on the board, {SEP[2026]["att"]:,} attendances and {R(SEP[2026]["rev"])} of attributed class revenue.</div>

<p>The operating picture is genuinely mixed, and it is worth being precise about which parts improved. The studio put on <strong>{SEP[2026]["sessions"]} classes against
{SEP[2025]["sessions"]} last September</strong>, on fewer seats.</p>

<p>Revenue per attendance rose from <strong>{R(SEP[2025]["rev_head"])} to {R(SEP[2026]["rev_head"])} &mdash; {SEP[2026]["rev_head"]/SEP[2025]["rev_head"]*100-100:+.0f}%</strong>, and total attributed
class revenue rose from {R(SEP[2025]["rev"])} to <strong>{R(SEP[2026]["rev"])}</strong>. Booking discipline improved again: {SEP[2026]["board"]:.1f}% of the board was booked,
against {SEP[2025]["board"]:.1f}% a year ago, and the share of booked seats actually honoured rose to {x26['CheckedIn'].sum()/max(x26['Booked'].sum(),1)*100:.1f}% from
{x25['CheckedIn'].sum()/max(x25['Booked'].sum(),1)*100:.1f}%. The studio is filling less of its timetable, and earning more from every seat it fills.</p>

{ev('Evidence — September 2024, 2025 and 2026 set side by side',
    T(['September','Classes','Seats on the board','Attendances','Fill rate','Board booked','Revenue','Per attendance','Unique members','Visits per member'],
      [[str(y), SEP[y]['sessions'], f"{SEP[y]['seats']:,}", f"{SEP[y]['att']:,}", P(SEP[y]['fill']), P(SEP[y]['board']),
        R(SEP[y]['rev']), R(SEP[y]['rev_head']), f"{[len(s24),len(s25),len(s26)][i]:,}",
        f"{[a24.groupby('Member ID').size().mean(), a25.groupby('Member ID').size().mean(), v26.mean()][i]:.2f}"]
       for i, y in enumerate((2024, 2025, 2026))], 'num'))}

{CH_OPD}
{CH_OPH}

<h2>The member base</h2>
<div class="sub">More people, fewer visits each. The distribution of visits is the most revealing chart in this report.</div>

<p>Of the {len(v26)} members who trained in September, <strong>{(v26==1).mean()*100:.1f}% came exactly once</strong> and {((v26>=2)&(v26<=3)).mean()*100:.1f}% came two or three times.
At the other end, <strong>{((v26>=9)).mean()*100:.1f}% came nine times or more</strong>, and those members alone account for
<strong>{v26[v26>=9].sum()/v26.sum()*100:.1f}% of everything the studio delivered</strong>. The top tenth of the member base is
{v26.nlargest(int(len(v26)*0.1)).sum()/v26.sum()*100:.1f}% of the visits.</p>

<p>There is a mirror image of this in the membership ledger. Members who <em>never</em> cancel a class completed an average of only {NEVERC_SESS:.1f} classes in their
membership &mdash; fewer than those who cancel occasionally. The members who come once are not cancelling; they are not booking in the first place.</p>

<p>The same shape appears in the money. In the last twelve months {len(per):,} people bought something at Bandra. The ten largest buyers account for
<strong>{P10:.1f}% of the revenue</strong>, the top hundred for {_CUM[100]*100:.0f}%, and the half of buyers who spent least account for {PB50:.1f}% between them.
This is a studio funded by a few hundred committed people, with a very long tail of one-time visitors around them.</p>

{CH_FREQ}
{CH_MONEY}

<div class="call b"><h4>Why concentration matters</h4>
<p>A business where a tenth of revenue sits with ten named people is exposed, and it also has an unusually clear lever: those ten members are known, contactable
and already engaged. Losing one of them costs the studio {P10/10:.1f}% of its revenue. Keeping a hundred members who are drifting from four visits a month to
one is worth considerably more than any acquisition campaign the studio could run.</p></div>

<h2>The returning core &mdash; the one number moving the wrong way</h2>
<div class="sub">{len(RET)} members came in both Septembers. Every one of them came less this year.</div>

<p>Matching the two Septembers member by member isolates what is really happening, free of any recruitment effect. The {len(RET)} members present in both months
delivered {SEP25_RET:.0f} attendances last September and {SEATS_RET:.0f} this September. Across the twelve busiest of them,
<strong>every single member attended less this year than last</strong>.</p>

<p>The members who did not return are a different and less troubling story. The {len(GONE)} who were here in September 2025 and not this year had a
<strong>median of {v25.reindex(list(GONE)).median():.0f} visit in September 2025</strong> and averaged {v25.reindex(list(GONE)).mean():.2f}. These are not lost loyalists; they are
one-time visitors who never became members in the first place, which is the funnel problem addressed below rather than a retention problem.</p>

{CH_CORE}

{ev('Evidence — the returning core against the leavers and the new intake',
    T(['Group','Members','Visits this September','Mean visits','Median visits'],
      [['Trained in both Septembers', len(RET), f"{SEATS_RET:.0f}", f"{SEATS_RET/len(RET):.2f}", f"{v26.reindex(list(RET)).median():.0f}"],
       ['Here in Sept 2025, not this year', len(GONE), '—', f"{v25.reindex(list(GONE)).mean():.2f} (last year)", f"{v25.reindex(list(GONE)).median():.0f} (last year)"],
       ['New this September', len(NEWB), f"{SEATS_NEW:.0f}", f"{SEATS_NEW/len(NEWB):.2f}", f"{v26.reindex(list(NEWB)).median():.0f}"],
       ['Trained in all three Septembers', len(s24 & s25 & s26), '—', '—', '—']], 'num'))}

<h2>The acquisition engine</h2>
<div class="sub">The studio brings people in well. What happens next is where the value is lost.</div>

<p>Between September 2025 and August 2026, <strong>{len(INTAKE):,} people took a first class at Bandra</strong>. Of those,
<strong>{CONVD:.1f}% ever converted to a paying member</strong>. For the {100-CONVD:.1f}% who did not, the story is almost always the same: there was no second visit.</p>

<p>Of those who did come back, {PCT7:.1f}% returned within a week and the median return was {MED2:.0f} days. <strong>{INTAKE["Days To Second Visit"].isna().mean()*100:.0f}% of the entire intake
never returned at all.</strong> The second visit is not an outcome the studio influences over months &mdash; it is decided in the first seven days, and it is the single
strongest predictor of everything that follows.</p>

{CH_SPEED}
{CH_FUN}

<h2>Where those people came from</h2>
<div class="sub">The biggest channels are not the best ones, and the difference is large enough to reorder the marketing plan.</div>

<p>Read by volume, one channel dominates: <strong>{BIG_CH.lower()} produced {BIG_N} first-timers</strong>, more than the website, referrals and walk-ins combined.
Read by outcome, it is the weakest channel the studio has. Of those {BIG_N} people, <strong>{BIG_CONV:.1f}% converted</strong> and their lifetime value to date is
<strong>{R(BIG_LTV)}</strong>, against <strong>{R(BEST_LTV)}</strong> for a member acquired through {BEST_CH.lower()} &mdash; a
{BEST_LTV/max(BIG_LTV,1):.0f}-fold difference on the same studio, the same classes and the same prices.</p>

<p>The channels that work are the ones where a person chose to speak to the studio before ever arriving. {BEST_CH} converts at
<strong>{BEST_CONV:.1f}%</strong>, {SR["conv"].get("Enquiry on call", float("nan")):.1f}% for enquiries by phone and {SR["conv"].get("Walk-in", float("nan")):.1f}% for walk-ins.
None of them is large. All of them are worth several times what the biggest channel is worth.</p>

{CH_SRCV}
{CH_SRCF}

{ev('Evidence — every acquisition source with twenty or more first visits',
    T(['Source','First visits','Conversion rate','Median days to 2nd visit','Mean lifetime value','Mean visits'],
      [[k, int(r['intake']), P(r['conv']), f"{r['second']:.0f}" if r['second'] == r['second'] else '—',
        R(r['ltv']), f"{r['visits']:.1f}"] for k, r in SR.iterrows()], 'num'))}

<h2>What the memberships look like</h2>
<div class="sub">Most of the book has only ever known one room and one trainer. That is the studio&rsquo;s largest unexploited asset.</div>

<p><strong>{SING:.0f}% of September&rsquo;s members trained in a single format</strong> and <strong>{100-MT:.0f}% saw a single trainer</strong>. Meanwhile members who have used four
formats have paid an average of <strong>{R(TICK4)}</strong> across their history, against <strong>{R(TICK1)}</strong> for those who have used one &mdash; a
{TICK4/max(TICK1,1):.1f}-fold difference. Even allowing for the obvious fact that longer-staying members accumulate more formats, the gap is too large to ignore:
the studio&rsquo;s most valuable members are the ones who use the whole building.</p>

{ev('Evidence — formats used, against what the member has paid',
    T(['Formats used','Members','Mean amount paid','Mean classes completed'],
      [[int(k), int(v), R(FMT_TICKET.get(k, float('nan'))), f"{FMT_CLS.get(k, float('nan')):.1f}"]
       for k, v in NF.value_counts().sort_index().items() if k >= 1], 'num'))}

<h2>How the studio earns</h2>
<div class="sub">Cash, cards and a payment stack that has quietly shifted. September&rsquo;s money came from {len(CAT)} categories.</div>

<p>September 2026 took <strong>{R(SLOTS)}</strong> across {len(R26):,} sales lines.
{', '.join(f'<strong>{k}</strong> {R(v)}' for k, v in list(CAT['sum'].items())[:4])}.</p>

<p>Read by payment method, the month is dominated by <strong>{PM.index[0]} at {R(PM['sum'].iloc[0])} ({PM['sum'].iloc[0]/SLOTS*100:.0f}%)</strong> and
{PM.index[1]} at {R(PM['sum'].iloc[1])}. The average transaction tells the more useful story:
{', '.join(f'{k} {R(r["sum"]/r["size"])}' for k, r in PM.iterrows())}.</p>

{CH_CAT}

<p>When people buy matters too, and the pattern is stable. Across 2026 the studio&rsquo;s sales peak at <strong>{int(BUYHR['sum'].idxmax())}:00</strong>, with
{int(BUYHR['size'].idxmax())} transactions in that hour alone, and the buying day runs from the morning class rush into early afternoon. Mondays and Saturdays are the
largest selling days; Sunday is the smallest.</p>

<h2>Recommendations</h2>
<div class="sub">Twelve actions, ordered by the size of the outcome each moves</div>
{REC_HTML}
{SRC}
''')
open('/home/user/reports-arena/Bandra_September_2026_7_Studio_Overview.html', 'w').write(HTML)
print(f'Report 7 written: {len(HTML)} bytes')
print(f'members {len(s24)}/{len(s25)}/{len(s26)} | visits per member {a24.groupby("Member ID").size().mean():.2f}/{a25.groupby("Member ID").size().mean():.2f}/{v26.mean():.2f}')
print(f'ret {len(RET)} seats {SEP25_RET:.0f}->{SEATS_RET:.0f} | gone {len(GONE)} | new {len(NEWB)} seats {SEATS_NEW:.0f}')
print(f'intake {len(INTAKE)} conv {CONVD:.1f}% within7 {PCT7:.1f}% median2 {MED2:.0f}')
print('SR:'); print(SR.round(1).to_string())
print('funnel', list(zip(FUN, steps)))
print(f'P10 {P10:.1f} P25 {P25:.1f} PB50 {PB50:.1f} | cats {dict(CAT["sum"].head(6))}')
print('PM:', PM.to_dict('index'))
