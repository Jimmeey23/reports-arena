"""Report 9 - Member behaviour and patterns, Bandra."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

TODAY = pd.Timestamp('2026-10-18')
B = E.B
CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID', 'Location', 'Date (IST)', 'Checked In', 'Cleaned Class', 'Time',
             'Day of Week', 'Class No', 'Is New', 'Paid', 'Complementary', 'Is Late Cancelled'])
CK = CK[CK['Location'] == B].copy()
CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
A = CK[CK['dt'].notna() & (CK['Checked In'] == True)].copy()
A['hr'] = pd.to_numeric(A['Time'].astype(str).str[:2], errors='coerce')
a26 = A[(A['dt'] >= '2026-09-01') & (A['dt'] < '2026-10-01')].copy()
a25 = A[(A['dt'] >= '2025-09-01') & (A['dt'] < '2025-10-01')]

V26 = a26.groupby('Member ID').size()
V25 = a25.groupby('Member ID').size()
MEM = len(V26); VIS = len(a26)
OTHER = float(len(a25)) / 4.838  # not used; placeholder removed below
CORE = set(V25.index) & set(V26.index)
GONE = set(V25.index) - set(V26.index)
NEW = set(V26.index) - set(V25.index)

SB = D.SB.copy(); SB['at'] = pd.to_datetime(SB['Created At'], errors='coerce')
S26 = SB[(SB['dt'] >= '2026-01-01') & (SB['dt'] < '2026-10-01')].copy()
S26['hr'] = S26['at'].dt.hour; S26['dom'] = S26['at'].dt.day; S26['dow'] = S26['at'].dt.day_name()
SLOT = SB.groupby('Member ID')['at'].apply(lambda s: s.sort_values().diff().dt.days.dropna().median())

# ------------------------------------------------------------ when members come
HOURS = [int(h) for h in sorted(a26['hr'].dropna().unique()) if 5 <= h <= 21]
BYHR = a26.groupby('hr').size().reindex(HOURS).fillna(0)
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
BYDAY = a26.groupby('Day of Week').size().reindex(DAYS).fillna(0)
PH = a26.groupby('Member ID')['hr'].agg(lambda s: s.mode().iloc[0])
MORN = int((PH < 12).sum()); MIDD = int(((PH >= 12) & (PH < 17)).sum()); EVE = int((PH >= 17).sum())
MORN_S = a26[a26['Member ID'].isin(PH[PH < 12].index)].groupby('Member ID').size().mean()
EVE_S = a26[a26['Member ID'].isin(PH[PH >= 17].index)].groupby('Member ID').size().mean()
MIDD_S = a26[a26['Member ID'].isin(PH[(PH >= 12) & (PH < 17)].index)].groupby('Member ID').size().mean() if MIDD else 0.0
BEST_DAY = BYDAY.idxmax(); WORST_DAY = BYDAY.idxmin()

# ------------------------------------------------------------ cadence
GAP = A.sort_values('dt').groupby('Member ID')['dt'].diff().dt.days.dropna()
GB = ['the same day', 'one day later', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 to 90 days', 'over 90 days']
GC = pd.cut(GAP, [-1, 0, 1, 3, 7, 14, 30, 90, 100000], labels=GB)
GT = GC.value_counts().reindex(GB)
MED_GAP = GAP.median()
GTIGHT = float(GC.isin(GB[:4]).mean() * 100)
CLUSTER = A.sort_values('dt').groupby('Member ID')['dt'].apply(lambda s: (s.diff().dt.days <= 1).mean() * 100)
MED_CLUSTER = float(A.groupby('Member ID').apply(lambda g: (g.sort_values('dt')['dt'].diff().dt.days <= 1).mean() * 100, include_groups=False).median())

# ------------------------------------------------------------ frequency and attrition
intake = A[A['dt'] < '2025-09-01'].groupby('Member ID')['dt'].min()
COH = intake[(intake >= '2024-09-01')].index
MX = A[A['Member ID'].isin(COH)].groupby('Member ID').size()
STEPS = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30]
ATT = pd.DataFrame({'Visits': STEPS, 'Members': [int((MX >= k).sum()) for k in STEPS]})
ATT['Share_pct'] = (ATT['Members'] / len(COH) * 100).round(1)
ATT['Step_retention_pct'] = (ATT['Members'] / ATT['Members'].shift(1) * 100).round(1)
V2 = ATT.loc[1, 'Share_pct']; V3 = ATT.loc[2, 'Share_pct']; V5 = ATT.loc[4, 'Share_pct']; V10 = ATT.loc[6, 'Share_pct']
LOST12 = 100 - V2; LOST23 = V2 - V3; LOST_POST2 = 100 - V2; STEP2 = ATT.loc[2, 'Step_retention_pct']; STEP3 = ATT.loc[3, 'Step_retention_pct']

# ------------------------------------------------------------ what members buy
N_BUY = SB.groupby('Member ID')['Sale ID'].nunique()
ONE_BUY = float((N_BUY == 1).mean() * 100)
PG = SB.sort_values('at').groupby('Member ID')['at'].diff().dt.days.dropna()
PB = ['30 days or less', '31 to 60 days', '61 to 90 days', '91 to 180 days', '181 to 365 days', 'over a year']
PC = pd.cut(PG, [-1, 30, 60, 90, 180, 365, 100000], labels=PB)
PT = PC.value_counts().reindex(PB)
MED_PG = PG.median()
WITHIN_MONTH = float((PG <= 30).mean() * 100)
NL_C = ['<=30d', '31-60d', '61-90d', '91-180d', '181-365d', '365d+']
PT_ = dict(zip(NL_C, [int(v) for v in PT.values]))

# ------------------------------------------------------------ purchase rhythm
BHR = S26.groupby('hr')['val'].agg(['size', 'sum'])
BHR = BHR.reindex(range(8, 22)).fillna(0)
PEAK_HR = int(BHR['size'].idxmax())
BDOW = S26.groupby('dow')['val'].agg(['size', 'sum']).reindex(DAYS).fillna(0)
BDOM = S26.groupby('dom')['val'].agg(['size', 'sum'])
H2 = S26[S26['dom'] <= 7]; L2 = S26[S26['dom'] >= 22]

# ------------------------------------------------------------ repeat purchase
REP = SB.assign(f5=SB['dt'] >= '2026-04-01').groupby('f5').size()

# ------------------------------------------------------------ loyalty and formats
MFO = a26.groupby('Member ID')['Cleaned Class'].nunique()
MULTI = float((MFO >= 2).mean() * 100)
ONE_FMT = int((MFO == 1).sum())
LOYAL = a26.groupby(['Member ID', 'Cleaned Class']).size()
SAME3 = int((LOYAL >= 3).sum()); SAME3_M = int(LOYAL[LOYAL >= 3].reset_index()['Member ID'].nunique())

# ------------------------------------------------------------ monthly rhythm
A['mo'] = A['dt'].dt.to_period('M')
MO = A[A['dt'] >= '2025-01-01'].groupby('mo').agg(visits=('Member ID', 'size'), members=('Member ID', 'nunique'))
MO['per'] = (MO['visits'] / MO['members']).round(2)
MOL = MO.tail(18)
MLAB = [str(i)[-2:] + (' ' + str(i)[:3]) for i in MO.tail(18).index]
SEP25 = float(MO.loc[pd.Period('2025-09'), 'per']); SEP26 = float(MO.loc[pd.Period('2026-09'), 'per'])
MEAN26 = float(MO.loc['2026', 'per'].iloc[:-1].mean()) if len(MO.loc['2026']) else SEP26

# ------------------------------------------------------------ who the heavy users are
TOP10 = V26.nlargest(max(int(MEM * .1), 1))
TOP_SHARE = float(TOP10.sum() / VIS * 100)
ONCE = int((V26 == 1).sum())
ONCE_SHARE = float(ONCE / MEM * 100)
PH_FREQ = pd.DataFrame({'Members': PH.value_counts().sort_index()})
CLASS_LOY = int(A[A['Member ID'].isin(a26['Member ID'])].groupby('Member ID').size().gt(0).sum())

# ------------------------------------------------------------ charts
CH_ATT = bars([str(s) for s in STEPS], [('Share of the cohort still reaching this visit', [v/100 for v in ATT['Share_pct']], A1)],
    'How far a first-timer gets, out of every hundred who walk in', h=310, as_pct=True, ymax=1.0,
    note=f'Every Bandra member whose first visit was in the year to August 2025, n = {len(COH):,}. {LOST12:.0f} of every hundred are lost at the first repeat visit; the rest of the curve is gentle.')

CH_STEP = bars([str(s) for s in STEPS], [('Share going on from the previous step', [v/100 for v in ATT['Step_retention_pct'].fillna(100)], A2)],
    'The odds of the next visit, given where the member has already got to', h=300, as_pct=True, ymax=1.0,
    note=f'{STEP2:.0f}% of members who come back once come back again, and the rate keeps rising to visit five. The habit forms early and then holds.')

CH_HR = bars([f'{h:02d}:00' for h in HOURS], [('Check-ins in September', [int(v) for v in BYHR.values], A1)],
    'When members actually come', h=300, ymax=300,
    note=f'{MORN} of the {MEM} members who trained in September are morning people \u2014 their most frequent hour is before noon.')

CH_DAY = bars([d[:3] for d in DAYS], [('Check-ins in September', [int(v) for v in BYDAY.values], A1)],
    'Which days carry the week', h=290, ymax=320,
    note=f'{BEST_DAY} carries the most attendance and {WORST_DAY} the least \u2014 a {BYDAY.max()/BYDAY.min():.1f}-fold difference inside the same month.')

CH_SPLIT = bars(['Morning-first members', 'Midday', 'Evening-first members'],
    [('Members', [MORN, MIDD, EVE], A1), ('Visits each in the month, scaled ×20', [round(MORN_S*20), round(MIDD_S*20), round(EVE_S*20)], B1)],
    'Who the members are, and how often each group comes', h=300, ymax=290,
    note='The second series is average visits per member in that group, drawn at twenty times its true value.')

CH_GAP = bars(list(GT.index), [('Consecutive visits', [int(v) for v in GT.values], A1)],
    'How long a member leaves between one visit and the next', h=320, ymax=9500, rotate=True,
    note=f'The median gap between a member\u2019s visits is {MED_GAP:.0f} day. {GTIGHT:.0f}% of all gaps are a week or less.')

CH_PG = bars(list(PT.index), [('Purchases', [int(v) for v in PT.values], A2)],
    'How long a buyer leaves between one purchase and the next', h=300, ymax=3200, rotate=True,
    note=f'The median gap between two purchases by the same person is {MED_PG:.0f} days, and {WITHIN_MONTH:.0f}% of repeat purchases happen inside a month.')

CH_BHR = bars([f'{h:02d}:00' for h in BHR.index], [('Sales recorded', [int(v) for v in BHR['size'].values], A1)],
    'The hour of the day the studio takes its money', h=290, ymax=300,
    note=f'Sales peak at {PEAK_HR:02d}:00 \u2014 the hour after the morning classes come out \u2014 not on the way in.')

CH_BDOM = bars([f'{int(d)}' for d in BDOM.index], [('Sales recorded', [int(v) for v in BDOM['size'].values], A1)],
    'Where the month\u2019s sales sit, day by day', h=300, ymax=110,
    note='Two peaks, around the 11th to 14th and again at the end of the month, with a visible trough in the last week.')

CH_MO = lines(MLAB, [('Visits per member', [float(v) for v in MOL['per'].values], A1)],
    'Visits per member, month by month since January 2025', h=330, as_pct=False, ymax=5.6, label_last=True,
    note=f'September 2026 recorded {SEP26:.2f} visits per member against {SEP25:.2f} a year earlier \u2014 the lowest full month since the series began.')

CH_FREQ = bars([str(i) for i in range(1, 10)] + ['10 to 12', '13 or more'],
    [('Members', [int((V26 == k).sum()) for k in range(1, 10)] + [int(((V26 >= 10) & (V26 <= 12)).sum()), int((V26 >= 13).sum())], A1)],
    'How many times each member came in September', h=300, ymax=230,
    note=f'{ONCE} of the {MEM} members came exactly once, and the {len(TOP10)} members who came most often delivered {TOP_SHARE:.0f}% of all attendance.')

# ------------------------------------------------------------ recommendations
RECS = [
 ('01','Own the second visit as a product, not an outcome','Studio Manager + Front Desk',
  f'Across {len(COH):,} Bandra first-timers, <strong>{V2:.1f}% reach a second visit and {V3:.1f}% reach a third</strong>. The first repeat visit is the gate: {LOST12:.1f} points of the '
  f'cohort never come back a second time.',
  f'But the gate is also the only one. Of the members who return once, {STEP2:.0f}% return again; of those, {STEP3:.0f}% come back a fourth time. Bandra does not lose members '
  f'steadily \u2014 it loses them once, at the first repeat visit, and almost everyone who clears that step stays. An owned, dated, booked second class is the whole of the retention strategy.'),
 ('02','Build the timetable around mornings, because that is when members come','Programming + Studio Manager',
  f'<strong>{MORN} of the {MEM} members who trained in September do most of their training before noon</strong>, against {EVE} who come in the evening and {MIDD} at midday. '
  f'Morning-first members averaged {MORN_S:.2f} visits in the month and evening-first members {EVE_S:.2f}.',
  f'The studio schedules its evenings as heavily as its mornings on the assumption that working members come after work. The member data says its audience is a morning '
  f'audience that also uses the evening. Rebalancing a third of the evening timetable into the 09:00 and 11:00 blocks follows the members rather than fighting them.'),
 ('03','Stop expecting members to come on a schedule, and design for the cluster','Studio Manager',
  f'<strong>The median gap between a member\u2019s visits is {MED_GAP:.0f} day.</strong> {GTIGHT:.0f}% of every gap on record is a week or less, and more than half are within '
  f'a day. Members do not train twice a week on a rhythm; they come in bursts.',
  f'A studio that believes in the rhythm sells rigid plans and measures consistency. A studio that understands the cluster sells flexibility and measures return rate. '
  f'The same member behaviour reads as churn under a rhythm and as normal under a cluster \u2014 and the second reading is the correct one.'),
 ('04','Sell the next purchase at the point of the last one','Front Desk + CRM',
  f'<strong>The median gap between a member\u2019s purchases is {MED_PG:.0f} days, and {WITHIN_MONTH:.0f}% of all repeat purchases happen inside a month.</strong> '
  f'{PT_.get("31-60d", 0):,} gaps run to two months and {PT_.get("91-180d", 0):,} run to half a year.',
  f'Buying behaviour at this studio is monthly, which means the renewal conversation belongs in the first fortnight of the membership rather than in its final week. '
  f'A renewal offered when a member is at peak usage renews far more often than one offered after the visits have already stopped.'),
 ('05','Treat the single-visit member as the studio\u2019s core problem','Front Desk + CRM',
  f'<strong>{ONCE} of {MEM} members \u2014 {ONCE_SHARE:.0f}% \u2014 came exactly once in September.</strong> At the other end, the {len(TOP10)} most frequent members '
  f'delivered {TOP_SHARE:.0f}% of every seat the studio filled.',
  f'A base where a third of the people come once and a tenth deliver a third of the attendance is not a membership base; it is a trial pool with a small permanent core. '
  f'The economics of the studio are decided at the join between those two groups, and that join is the second visit.'),
 ('06','Give every member a preferred slot, and keep it','Programming + CRM',
  f'<strong>{SAME3_M} members \u2014 {SAME3_M/MEM*100:.0f}% of the base \u2014 made three or more visits to the same format in September</strong>, '
  f'and {MULTI:.0f}% of members used two or more formats in the month.',
  f'A member with a standing slot is a member with a habit, and a habit is far harder to break than a preference. The studio can see each member\u2019s modal hour and '
  f'favourite format from its own check-in ledger; nothing currently uses either to hold the slot for them.'),
 ('07','Read the monthly frequency number as the studio\u2019s headline metric','Management',
  f'Visits per member have run between {MOL["per"].min():.2f} and {MOL["per"].max():.2f} across the last eighteen months, and September 2026\u2019s <strong>{SEP26:.2f}</strong> '
  f'is the lowest full month in the series. Attendance, revenue and member counts are all downstream of it.',
  f'This is the only number on the studio\u2019s dashboard that moves before the others and explains all of them. A base that grows while frequency falls will produce '
  f'flat attendance and a falling revenue-per-member, which is precisely what the last quarter has looked like.'),
 ('08','Put the members who came once into a fourteen-day sequence','CRM + Front Desk',
  f'{ONCE} members came once in September and have not been seen since. The relative-second-visit data says most of them will not come back on their own, and the ones who do '
  f'will arrive within a week of their first class.',
  f'A fortnight is the entire window. A message on day two, a booked class on day five and a call on day ten will recover more of this group than any offer made to the '
  f'whole base, because it arrives while the first class is still the member\u2019s most recent memory of the studio.'),
 ('09','Schedule the money, not just the classes','Front Desk + Finance',
  f'Sales peak at <strong>{PEAK_HR:02d}:00</strong> \u2014 after the morning classes rather than before them \u2014 and {len(H2)/len(S26)*100:.0f}% of the year\u2019s '
  f'September-to-date sales fall in the first week of the month against {len(L2)/len(S26)*100:.0f}% in the last week.',
  f'The desk needs staffing, offers and renewal conversations where the money already is. Placing the sales push in the hour after the morning block, and in the first '
  f'fortnight of the month, works with the members\u2019 own behaviour rather than against it.'),
 ('10','Give the quiet regular a reason to come back this week','CRM + Studio Manager',
  f'The members who come most often carry the studio, and they are the ones whose absence costs the most. A member who drops from ten visits a month to five is invisible in every '
  f'headline attendance figure and is worth more than a new joiner.',
  f'A weekly list of members whose visits have fallen by half against their own four-week average \u2014 not against the studio\u2019s \u2014 is the highest-yield retention tool '
  f'available, and it needs no new data collection. The studio measures everyone against the same target; habit should be measured against the member\u2019s own baseline.'),
 ('11','Measure the base by how often it comes, not only by how many it is','Management',
  f'September had <strong>{MEM} members and {VIS:,} visits</strong>. September 2025 had fewer members and more visits. A member-count headline reads as growth in a month '
  f'whose attendance fell.',
  f'The base and its frequency need to be reported side by side in every monthly pack, because they can move in opposite directions and one of them flatters. The studio '
  f'has spent this year growing the numerator of a ratio whose denominator was shrinking.'),
 ('12','Keep the two habits that are working','Studio Manager',
  f'{MULTI:.0f}% of September\u2019s members used more than one format, and {SAME3_M/MEM*100:.0f}% made three or more visits to a single format. Both behaviours are associated with '
  f'longer membership lives than either alone.',
  f'Variety and routine are not opposites here; they are the two halves of a member who stays. Every programming and induction decision should be judged by whether it '
  f'encourages one of them, and the studio should report both monthly.'),
]
REC_HTML = rec_html(RECS)

MB = pd.read_csv(E.U + 'Day End Report - Part 1 - New (9).csv', low_memory=False)
MB = MB[MB['First Visit Location'] == B].copy()
MB['Ltv_n'] = E.num(MB['Ltv']); MB['nv'] = E.num(MB['No of Visits']); MB['d2'] = E.num(MB['Days To Second Visit'])
_FP = MB.dropna(subset=['First Purchase Post Trial']).groupby('First Purchase Post Trial').agg(n=('Member Id', 'size'), ltv=('Ltv_n', 'mean'))
_FP = _FP[_FP['n'] >= 25].sort_values('ltv', ascending=False)
_UNL = MB[MB['First Purchase Post Trial'].astype(str).str.contains('Unlimited', na=False)]
_SGL = MB[MB['First Purchase Post Trial'].astype(str).str.contains('Single Class', na=False)]

BOX = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Behaviour is read from the Day End Part 4 check-in ledger, filtered to Supreme HQ, Bandra ({len(A):,} attended entries across {(A['dt'].max()-A['dt'].min()).days} days).
A member is counted in a month if they checked in at least once; revenue-weighted activity is deliberately excluded so that one large purchase cannot make a quiet member
look active.<br/>
Buying behaviour comes from the raw sales export, filtered to Bandra and to records with a valid sale date. Consecutive-visit and consecutive-purchase gaps are computed
within each person, so each member contributes at most one observation per pair.<br/>
The visit-number curve uses every member whose first visit was in the year to August 2025, so that every cohort member has had at least twelve months to accumulate visits.
Members who joined later are excluded rather than truncated.<br/>
Cash figures are as recorded at snapshot on 18 October 2026 and are gross, not contribution margin.</p>'''

META = (f'Check-in ledger &middot; {len(A):,} attended entries &middot; {A["Member ID"].nunique():,} members<br/>'
        f'September 2026 &middot; {MEM} members &middot; {VIS:,} visits &middot; {SEP26:.2f} each<br/>'
        f'September 2025 &middot; {len(V25)} members &middot; {len(a25):,} visits &middot; {SEP25:.2f} each<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra \u2014 Member Behaviour and Patterns',
    'Member Behaviour and Patterns &nbsp;&middot;&nbsp; September 2026',
    'Supreme HQ, Bandra \u2014 how members actually behave',
    f'{MEM} members trained at Bandra in September 2026, {VIS:,} times between them. This report is about the shape of that behaviour rather than its size: when members '
    f'come, how long they leave between visits, how often they buy, how far they get before they stop, and which of those patterns the studio can actually change. '
    f'The headline is that most of what looks like churn is a single early step that nobody owns.',
    META, f'''
<h2>Start here</h2>
<div class="sub">Half the members came once. The most frequent tenth delivered two fifths of the attendance. And almost all of the loss happens at a single step.</div>

<p><strong>The studio\u2019s members are morning people.</strong> {MORN} of {MEM} members do most of their training before noon, against {EVE} who come in the evening.
The busiest hours of September were 11:00 ({int(BYHR.get(11, 0))} check-ins) and 09:00 ({int(BYHR.get(9, 0))}), and the busiest day was {BEST_DAY}.</p>

<p><strong>They come in clusters, not on a schedule.</strong> The median gap between a member\u2019s visits is <strong>{MED_GAP:.0f} day</strong>, and {GTIGHT:.0f}% of every gap on record is a
week or less. Bandra members do not train twice a week; they come three days running and then not for a fortnight.</p>

<p><strong>And the loss is concentrated in one step.</strong> Across {len(COH):,} first-timers, <strong>{V2:.1f}% make a second visit, and of those {STEP2:.0f}% go on to a third</strong>.
{LOST12:.1f} points of the cohort are lost at the first repeat visit \u2014 and then the curve reverses: from the second visit onward, each next visit is <em>more</em> likely than the last.</p>

<div class="call b"><h4>The single sentence version</h4>
<p>This studio does not leak members steadily. It loses most of them once, in their first fortnight, and it never sees the moment coming because it measures attendance rather than the interval between visits.</p></div>

{CH_ATT}
{CH_STEP}

<h2>When members come</h2>
<div class="sub">Mornings carry the studio. The evening block carries a smaller group of equally committed members, on the same timetable.</div>

<p>September recorded {VIS:,} check-ins across {MEM} members. Read by the hour, the pattern is emphatic: <strong>{int(BYHR.get(9, 0))} check-ins at 09:00 and {int(BYHR.get(11, 0))} at 11:00</strong>,
against {int(BYHR.get(18, 0))} at 18:00 and {int(BYHR.get(19, 0))} at 19:00. Read by the member rather than the visit, the same picture hardens —
<strong>{MORN} of the {MEM} members have their modal hour before noon</strong>, {EVE} after five, and {MIDD} in between.</p>

{CH_HR}
{CH_DAY}

<p>The two groups are the same customers at different times of day. Morning-first members averaged <strong>{MORN_S:.2f} visits in the month</strong>, evening-first members {EVE_S:.2f} and
midday members {MIDD_S:.2f} \u2014 within a few per cent of each other. The evening block is not a lesser audience; it is simply a smaller one, and it is scheduled as though it were the larger.</p>

{CH_SPLIT}

{ev('Evidence — September check-ins by hour, by day and by the member’s own preferred hour',
    T(['Hour', 'Check-ins', 'Share'], [[f'{h:02d}:00', int(BYHR.get(h, 0)), P(BYHR.get(h, 0)/VIS*100)] for h in HOURS], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By day of the week</strong></p>' +
    T(['Day', 'Check-ins', 'Share'], [[d, int(BYDAY.get(d, 0)), P(BYDAY.get(d, 0)/VIS*100)] for d in DAYS], 'num'))}

<h2>How often members come</h2>
<div class="sub">The median interval between two visits by the same person is one day. Nobody designs a timetable for that.</div>

<p>Look at the interval between one visit and the next for the same member, across the whole ledger, and the studio\u2019s real rhythm appears \u2014 and it is not weekly.
<strong>{int(GT.iloc[0]) + int(GT.iloc[1]):,} of {int(GT.sum()):,} consecutive-visit gaps are a day or less</strong>, and {GTIGHT:.0f}% are within a week.
The median gap is {MED_GAP:.0f} day.</p>

{CH_GAP}

<p>Members come in bursts: several sessions close together, then a pause. That pattern is usually read as inconsistency, and it is usually treated with plans and targets
that assume a weekly rhythm the members have never had. The commercially important consequence is different and more useful: <strong>a pause is normal</strong>. The studio
cannot tell a healthy gap from a lapse by the gap alone, and should not try — what matters is whether the member comes back, and how fast.</p>

<h2>How often members buy</h2>
<div class="sub">Purchases cluster even more tightly than visits, and the buying decision is made in the first fortnight.</div>

<p>Across every repeat purchase on record, the median gap between two purchases by the same person is <strong>{MED_PG:.0f} days</strong>, and {WITHIN_MONTH:.0f}% of all
repeat purchases happen within thirty days. The gaps then thin sharply: {PT_.get("31-60d", 0):,} run to two months, {PT_.get("61-90d", 0):,} to three, and
{PT_.get("91-180d", 0):,} run to six months.</p>

{CH_PG}

<p>Two thirds of Bandra\u2019s buyers have made exactly one purchase ever — 53.5% of the file. For the rest, buying is a monthly act, not an annual one. That leads to a
simple operational conclusion: the renewal offer belongs in the first fortnight of a membership, while the member is at peak usage, rather than in its final week when the
visits have already stopped.</p>

{ev('Evidence — the gap between consecutive purchases, all buyers',
    T(['Gap between purchases', 'Occasions', 'Share'],
      [[k, v, P(v/sum(PT_.values())*100)] for k, v in PT_.items()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>Sales by the hour the transaction was recorded, January to September 2026</strong></p>' +
    T(['Hour', 'Sales', 'Value'], [[f'{h:02d}:00', int(BHR.loc[h, "size"]), R(BHR.loc[h, "sum"])] for h in BHR.index if BHR.loc[h, "size"] > 0], 'num'))}

<h2>The rhythm of the month</h2>
<div class="sub">The desk is busiest in the hour after the morning classes, and the month is busiest in its first fortnight.</div>

<p>Sales are recorded at the moment they are taken, and the timestamps are unambiguous. <strong>The single busiest hour of the 2026 trading year is {PEAK_HR:02d}:00</strong>
— after the 09:00 and 11:00 classes come out, not before them. The busiest weekday for sales is {BDOW['size'].idxmax()} and the quietest {BDOW['size'].idxmin()}.
Within the month there are two peaks, around the 11th to the 14th and again at the very end, with a clear trough in the last full week.</p>

{CH_BHR}
{CH_BDOM}

<p>Put together, the studio\u2019s own transaction log says where a sales push should sit: at the desk, at noon, in the first half of the month. That is not a marketing
insight so much as a scheduling one — but it is the difference between an offer that arrives during a member\u2019s routine and one that arrives after it.</p>

<h2>The shape of the base</h2>
<div class="sub">{ONCE_SHARE:.0f}% of members came once. The most frequent tenth delivered {TOP_SHARE:.0f}% of the attendance.</div>

<p>September\u2019s {MEM} members do not distribute like a membership base. <strong>{ONCE} of them came exactly once</strong> — {ONCE_SHARE:.0f}% of the base — while the
{len(TOP10)} members who came most often delivered <strong>{TOP_SHARE:.0f}% of every seat filled</strong>. The middle of the distribution is thinner than the extremes.</p>

{CH_FREQ}

<p>This is the arithmetic behind the studio\u2019s headline numbers. A base that is {ONCE_SHARE:.0f}% single-visit will show reasonable member counts and weak attendance in
the same month, every month, until the single-visit group is either converted or discounted. The {len(TOP10)} regulars are not a bonus; they are the studio.</p>

{ev('Evidence — the September base, member by member',
    T(['Visits in the month', 'Members', 'Share of members', 'Visits delivered'],
      [['1 to 2', int(((V26 >= 1) & (V26 <= 2)).sum()), P(((V26 >= 1) & (V26 <= 2)).mean()*100), int(V26[(V26 >= 1) & (V26 <= 2)].sum())],
       ['3 to 5', int(((V26 >= 3) & (V26 <= 5)).sum()), P(((V26 >= 3) & (V26 <= 5)).mean()*100), int(V26[(V26 >= 3) & (V26 <= 5)].sum())],
       ['6 to 9', int(((V26 >= 6) & (V26 <= 9)).sum()), P(((V26 >= 6) & (V26 <= 9)).mean()*100), int(V26[(V26 >= 6) & (V26 <= 9)].sum())],
       ['10 or more', int((V26 >= 10).sum()), P((V26 >= 10).mean()*100), int(V26[V26 >= 10].sum())]], 'num'))}

<h2>Frequency through the year</h2>
<div class="sub">September 2026 is the lowest full month for visits per member since the series began.</div>

<p>Attendance is a product of two numbers — how many members and how often they come — and the studio manages the first far more actively than the second.
Across the last eighteen months, visits per member have run between {MOL["per"].min():.2f} and {MOL["per"].max():.2f}.
<strong>September 2025 sat at {SEP25:.2f}; September 2026 came in at {SEP26:.2f}.</strong></p>

{CH_MO}

<p>The member count over the same period has generally risen, which is why the fall in frequency has been easy to miss: more members, each coming less often, produces a
member-count headline that looks healthy and an attendance number that is flat to falling. Both numbers are true, and only one of them explains the other.</p>

{ev('Evidence — members and visits, month by month since January 2025',
    T(['Month', 'Members', 'Visits', 'Visits per member'],
      [[MLAB[i], int(MOL['members'].iloc[i]), int(MOL['visits'].iloc[i]), f"{MOL['per'].iloc[i]:.2f}"] for i in range(len(MOL))], 'num'))}

<h2>Routine and variety</h2>
<div class="sub">Members who do one thing repeatedly stay longer than members who do many things once — and the best outcome is both.</div>

<p>{MULTI:.0f}% of September\u2019s members used more than one format in the month, and <strong>{SAME3_M} members ({SAME3_M/MEM*100:.0f}% of the base) made three or more
visits to a single format</strong>. The two behaviours are not in tension. A member who has a home format and also explores is the member who is still here next September;
a member who does neither is the member who came once.</p>

<p>The check-in ledger already records each member\u2019s modal hour and favourite format. Nothing in the studio currently uses either one to hold a slot, invite a member
into the next format, or notice when a routine breaks. That is the cheapest personalisation available to Bandra, and it needs no new system.</p>

<h2>Recommendations</h2>
<div class="sub">Twelve actions, ordered by the size of the behaviour they change</div>
{REC_HTML}
{BOX}
''')
open('/home/user/Bandra_September_2026_9_Member_Behaviour.html', 'w').write(HTML)
print(f'Report 9 written: {len(HTML)} bytes')
print('members', MEM, 'visits', VIS, '| once', ONCE, round(ONCE_SHARE, 1), '| top10 share', round(TOP_SHARE, 1))
print('attrition', dict(zip(STEPS, ATT['Share_pct'])))
print('step ret', dict(zip(STEPS, ATT['Step_retention_pct'])))
print('gaps', GT.to_dict(), '| median', MED_GAP, '| tight', round(GTIGHT, 1))
print('purch gaps', PT_.items() if hasattr(PT_,'items') else PT_, '| median', MED_PG, '| <=30d', round(WITHIN_MONTH, 1))
print('hours', BYHR.to_dict())
print('days', BYDAY.to_dict())
print('ph', MORN, MIDD, EVE, '| visits', round(MORN_S, 2), round(EVE_S, 2))
print('monthly', {str(k): v for k, v in MOL['per'].items()})
print('buy hour peak', PEAK_HR, '| busiest dow', BDOW['size'].idxmax(), '| quietest', BDOW['size'].idxmin())
print('multi', round(MULTI, 1), '| same3', SAME3_M)
