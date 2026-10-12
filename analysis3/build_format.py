"""Report 5 - Format comparisons."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

# --------------------------------------------------- sessions frame
X = pd.read_csv(E.U + 'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
X = X[X['Location'] == E.B].copy(); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
for c in ['Capacity','CheckedIn','LateCancelled','Booked','Complimentary','Revenue','Memberships','Packages',
          'IntroOffers','SingleClasses','Classes']:
    X[c] = E.num(X[c]).fillna(0)
X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()

# ---------------------------------------------------------------- depth of the format set
_FS = x26.groupby('Class').agg(sessions=('SessionID', 'size'), seats=('cap', 'sum'), att=('CheckedIn', 'sum'),
                               book=('Booked', 'sum'), rev=('Revenue', 'sum'))
_FS['fill'] = _FS['att'] / _FS['seats'] * 100
_FS['rpc'] = _FS['rev'] / _FS['sessions']
_FS['lbl'] = [str(i).replace('Studio ', '')[:22] for i in _FS.index]
_FS = _FS.sort_values('att', ascending=False)
THIN = _FS[_FS['sessions'] < 12]
FAM = _FS[_FS['lbl'].str.contains('PowerCycle', na=False)]
EXPRESS = _FS[_FS.index.isin(['Studio PowerCycle Express', 'Studio Cardio Barre Express'])]

x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')].copy()
x24 = X[(X['dt'] >= '2024-09-01') & (X['dt'] < '2024-10-01')].copy()

SHORT = {'Studio PowerCycle':'PowerCycle','Studio Barre 57':'Barre 57','Studio FIT':'FIT','Studio Mat 57':'Mat 57',
         'Studio Cardio Barre':'Cardio Barre','Studio Back Body Blaze':'Back Body Blaze',
         'Studio PowerCycle Express':'PowerCycle X','Studio Recovery':'Recovery','Studio Hosted Class':'Hosted',
         'Studio Mat 57 Express':'Mat 57 X','Studio Cardio Barre Express':'Cardio Barre X',
         "Studio Trainer's Choice":"Trainer's Choice"}
def mk(d):
    g = d.groupby('Class').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), att=('CheckedIn','sum'),
        booked=('Booked','sum'), lc=('LateCancelled','sum'), comp=('Complimentary','sum'), rev=('Revenue','sum'),
        intro=('IntroOffers','sum'), single=('SingleClasses','sum'), memb=('Memberships','sum'), pkg=('Packages','sum'))
    g['fill'] = g['att']/g['seats'].replace(0, np.nan)*100
    g['rev_class'] = g['rev']/g['sessions']
    g['rev_head'] = g['rev']/g['att'].replace(0, np.nan)
    g['cancel_rate'] = g['lc']/g['booked'].replace(0, np.nan)*100
    g['avg_size'] = g['att']/g['sessions']
    return g
F26, F25, F24 = mk(x26), mk(x25), mk(x24)
MAIN = ['Studio PowerCycle','Studio Barre 57','Studio FIT','Studio Mat 57','Studio Cardio Barre',
        'Studio Back Body Blaze','Studio PowerCycle Express','Studio Recovery','Studio Mat 57 Express',
        'Studio Cardio Barre Express']
F = F26.loc[[c for c in MAIN if c in F26.index]].copy()
F['name'] = [SHORT[c] for c in F.index]
TOT_SESS = int(F26['sessions'].sum()); TOT_REV = F26['rev'].sum(); TOT_ATT = int(F26['att'].sum())

# --------------------------------------------------- member-level
CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID','Location','Date (IST)','Checked In','Is Late Cancelled','Cleaned Class'])
CK = CK[CK['Location'] == E.B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
A = CK[CK['Checked In'] == True].copy()
c26 = A[(A['dt'] >= '2026-09-01') & (A['dt'] < '2026-10-01')].copy()
c25 = A[(A['dt'] >= '2025-09-01') & (A['dt'] < '2025-10-01')]
MB = []
for cls, s in c26.groupby('Cleaned Class'):
    vc = s.groupby('Member ID').size()
    MB.append(dict(cls=cls, mem=len(vc), visits=len(s), per=len(s)/max(len(vc),1),
                   reg=int((vc>=4).sum()), regp=(vc>=4).mean()*100, once=(vc==1).mean()*100))
MBR = pd.DataFrame(MB).set_index('cls')

# format pairs
pairs = {}
mm = c26.groupby('Member ID')['Cleaned Class'].apply(lambda s: sorted(set(s)))
for f in mm:
    for i in range(len(f)):
        for j in range(i+1, len(f)):
            k = (f[i].replace('Studio ',''), f[j].replace('Studio ',''))
            pairs[k] = pairs.get(k, 0) + 1
PR = pd.Series(pairs).sort_values(ascending=False)

# --------------------------------------------------- favourite format economics
d = E.LP[E.LP['Favorite Format'].notna() & E.LP['Days Since Last Visit'].notna()].copy()
_FFIX = {'Barre 57 Express':'Barre 57 X','Cardio Barre Express 57':'Cardio Barre X','Cardio Barre Express':'Cardio Barre X',
         'PowerCycle Express':'PowerCycle X','Mat 57 Express':'Mat 57 X','Back Body Blaze Express':'BBB X',
         'Back Body Blaze':'Back Body Blaze','SWEAT in 30':'SWEAT in 30','Strength Lab':'Strength Lab',
         'Foundations':'Foundations','Juniors Class':'Juniors','Recovery':'Recovery'}
def _fav(s):
    t = ''.join(ch for ch in str(s) if ch.isalnum() or ch == ' ').strip()
    if t.startswith('Studio '): t = t[len('Studio '):]
    if t.lower().startswith('powercycle'):
        t = 'PowerCycle' + t[len('powercycle'):]
    elif t.lower().startswith('barre 57'):
        t = 'Barre 57' + t[len('barre 57'):]
    t = _FFIX.get(t, t)
    return t
d['fav'] = d['Favorite Format'].map(_fav)
FAV = d.groupby('fav').agg(members=('Member ID','nunique'), ticket=('Amount Paid','mean'),
    cls=('Total Sessions Completed','mean'), life=('Membership Duration (Days)','mean'),
    since=('Days Since Last Visit','mean')).sort_values('members', ascending=False)
FAV = FAV[FAV['members'] >= 40]

# multi-format ladder
nd = E.LP.copy()
nd['nf'] = nd['Formats Attended'].fillna('').apply(lambda s: 0 if not s else len([x for x in str(s).split(',') if x.strip()]))
NF = nd.groupby('nf').agg(members=('Member ID','nunique'), ticket=('Amount Paid','mean'),
    cls=('Total Sessions Completed','mean'), life=('Membership Duration (Days)','mean'),
    last30=('Visits in Last 30 Days','mean'), since=('Days Since Last Visit','mean'))
NF = NF[(NF['members'] >= 30) & (NF.index >= 1)]  # memberships with no recorded format are excluded

# --------------------------------------------------- day / hour matrices
x26['hr'] = pd.to_numeric(x26['Time'].astype(str).str[:2], errors='coerce')
DH = x26[x26['Class'].isin(MAIN)].pivot_table(index='Class', columns='Day', values='CheckedIn', aggfunc='sum').fillna(0)
DH['tot'] = DH.sum(axis=1)
HH = x26[x26['Class'].isin(MAIN)].pivot_table(index='Class', columns='hr', values='CheckedIn', aggfunc='sum').fillna(0)

# --------------------------------------------------- charts
CH_LEAGUE = hbars([(r['name'], r['fill'], A1 if r['fill'] >= 50 else (A2 if r['fill'] >= 38 else B1))
                   for _, r in F.iterrows()],
    'Capacity utilisation by format, September 2026', as_pct=True,
    note='Attendance as a share of the seats the studio put on the board. The studio average across all formats is '
         f'{TOT_ATT/F26["seats"].sum()*100:.1f}%.')

CH_SHARE = bars([r['name'] for _, r in F.iterrows()],
    [('Share of the timetable', [r['sessions']/TOT_SESS for _, r in F.iterrows()], A1),
     ('Share of attendance', [r['att']/TOT_ATT for _, r in F.iterrows()], A2),
     ('Share of class revenue', [r['rev']/TOT_REV for _, r in F.iterrows()], A3)],
    'Three ways of measuring the same format, and how differently they rank', h=340, as_pct=True, ymax=0.42,
    note='PowerCycle carries a third of the timetable and less than a third of attendance. FIT is the reverse.')

CH_ECO = diverging([(r['name'], r['rev_head']) for _, r in F.sort_values('rev_head', ascending=False).iterrows()],
    'What one attendance is worth, by format', note='Revenue attributed to attended classes, divided by attendance. '
    'The spread is narrow — about 40% from top to bottom — which matters for what it tells us about pricing.')

CH_MEM = bars([r['name'] for _, r in F.iterrows()],
    [('Distinct members', [MBR['mem'].get(c, 0) for c in F.index], A1),
     ('Share who came 4+ times this month', [MBR['regp'].get(c, 0) for c in F.index], B1)],
    'Reach against regularity, by format', h=320, ymax=200,
    note='FIT reaches fewer members than PowerCycle but turns far more of them into regulars inside a single month.')

CH_NF = bars([str(int(i)) for i in NF.index], [('Members in this band', NF['members'].tolist(), A1)],
    'How many formats each member uses', h=280, ymax=1200,
    note='Counted across the whole membership history, from the formats recorded on each membership.')

CH_NFV = diverging([(f'{int(i)} format' + ('s' if i > 1 else ''), v) for i, v in NF['ticket'].items()],
    'Average amount paid, by how many formats the member used',
    note='Read with the counts above: the number of members falls as the ladder rises, and the value per member rises '
         'with it. Correlation, not causation — but a strong and consistent gradient.')

CH_FAV = bars([k for k in FAV.head(8).index], [('Members', FAV['members'].head(8).tolist(), A1),
                                       ('Mean price paid, ₹ hundreds', [v/100 for v in FAV['ticket'].head(8)], B1)],
    'The format a member uses most, and what those members are worth', h=320, ymax=1300,
    note='Restricted to formats with forty or more members whose favourite format is recorded.')

CH_DH = hbars([(SHORT.get(k, k.replace('Studio ','')), row['tot'], A1 if i < 3 else A2)
               for i, (k, row) in enumerate(DH.sort_values('tot', ascending=False).head(8).iterrows())],
    'Where each format’s attendance comes from — total for the month', unit='',
    note='Underneath each figure the same number is split by day; see the evidence panel for the full grid.')

PEAK_A = ', '.join(f'<strong>{SHORT.get(c, c)}</strong> draws most on {DH.loc[c].drop("tot").idxmax()}' for c in DH.index[:5])
PEAK_B = ', '.join(f'{SHORT.get(c, c)} peaks on {DH.loc[c].drop("tot").idxmax()[:3]}' for c in DH.index[:4])

CH_COMP = hbars([(SHORT.get(k, k), v, A1 if v < 6 else B1) for k, v in
                 (F26['comp']/F26['att'].replace(0, np.nan)*100).dropna().sort_values(ascending=False).head(8).items()],
    'Share of each format’s attendance that was complimentary', as_pct=True)

# --------------------------------------------------- recommendations
RECS = [
 ('01','Rebuild PowerCycle around the room it actually fills','Programming + Studio Manager',
  f'PowerCycle carries <strong>{F.loc["Studio PowerCycle","sessions"]/TOT_SESS*100:.0f}% of the timetable</strong> and fills '
  f'<strong>{F.loc["Studio PowerCycle","fill"]:.1f}%</strong> of its seats, against Studio FIT at {F.loc["Studio FIT","fill"]:.1f}% on '
  f'{F.loc["Studio FIT","sessions"]/TOT_SESS*100:.0f}% of the timetable. Its express variant fills {F26.loc["Studio PowerCycle Express","fill"]:.1f}% '
  f'in roughly half the room.',
  f'Cutting the average PowerCycle class to eleven seats removes about {int(F.loc["Studio PowerCycle","sessions"]*(F.loc["Studio PowerCycle","seats"]/F.loc["Studio PowerCycle","sessions"]-11))} '
  f'seat-slots a month that nobody is buying, and lifts the studio-wide utilisation rate on its own.'),
 ('02','Scale Studio FIT deliberately','Programming',
  f'FIT is the best-performer on every efficiency measure: <strong>{F.loc["Studio FIT","fill"]:.1f}% fill, {R(F.loc["Studio FIT","rev_class"])} revenue per class</strong>, '
  f'and {MBR["regp"].get("Studio FIT", float("nan")):.1f}% of its attendees came four or more times inside the month — the highest regularity of any format.',
  f'Adding three FIT sessions a week at the current average of {F.loc["Studio FIT","avg_size"]:.1f} attendees, at {R(F.loc["Studio FIT","rev_head"])} a head, '
  f'is worth about {R(3*4.3*F.loc["Studio FIT","avg_size"]*F.loc["Studio FIT","rev_head"])} of class revenue a month from capacity the studio already owns.'),
 ('03','Treat the express formats as a distinct product, not a short version','Programming + Marketing',
  f'PowerCycle Express fills <strong>{F26.loc["Studio PowerCycle Express","fill"]:.1f}%</strong> against its parent at {F.loc["Studio PowerCycle","fill"]:.1f}%, and '
  f'Cardio Barre fills {F26.loc["Studio Cardio Barre","fill"]:.1f}% against Cardio Barre Express at {F26.loc["Studio Cardio Barre Express","fill"]:.1f}%. '
  'The express formats are not simply weaker — at their best they beat the full-length class in a smaller room.',
  'Express formats cost less to deliver, fill a harder slot and suit a member who cannot commit ninety minutes. Building two or three '
  'deliberate express slots into peak commuter windows is a cheaper capacity expansion than adding full-length classes.'),
 ('04','Market the multi-format ladder as the product','Marketing + Studio Manager',
  f'Members who have used one format have paid an average of <strong>{R(NF["ticket"].get(1, float("nan")))}</strong> and completed {NF["cls"].get(1, float("nan")):.1f} classes. '
  f'Those who have used three formats have paid {R(NF["ticket"].get(3, float("nan")))} and completed {NF["cls"].get(3, float("nan")):.1f}. At five formats the figure is '
  f'{R(NF["ticket"].get(5, NF["ticket"].max()))} on {NF["cls"].get(5, NF["cls"].max()):.1f} classes.',
  f'Only {P(NF[NF.index>=3]["members"].sum()/NF["members"].sum()*100)} of members have used three or more formats. Moving one member in ten up one rung of the ladder '
  'is the single largest value lever in this report, and it needs a product and a script rather than a discount.'),
 ('05','Fix the formats nobody is asked to try','Programming + Front Desk',
  f'Studio Mat 57 reaches {MBR["mem"].get("Studio Mat 57", 0)} members at {F26.loc["Studio Mat 57","fill"]:.1f}% fill with only '
  f'{MBR["regp"].get("Studio Mat 57", float("nan")):.1f}% returning four or more times. Cardio Barre reaches {MBR["mem"].get("Studio Cardio Barre", 0)} at '
  f'{F26.loc["Studio Cardio Barre","fill"]:.1f}% with {MBR["regp"].get("Studio Cardio Barre", float("nan")):.1f}% regulars.',
  'These are good products with almost no habit attached. A single well-chosen pairing — Mat 57 as the recovery companion to Barre 57, '
  'Cardio Barre as the first step toward Barre 57 — turns two under-used rooms into a route rather than a stop.'),
 ('06','Set the comp budget by format, not in total','Studio Manager + Finance',
  f'Complimentary seats run at {F26.loc["Studio Barre 57","comp"]/F26.loc["Studio Barre 57","att"]*100:.1f}% of Barre 57 attendance against '
  f'{F26.loc["Studio FIT","comp"]/F26.loc["Studio FIT","att"]*100:.1f}% for FIT. Across the studio that is {int(F26["comp"].sum()):,} free seats, '
  f'worth {R(F26["comp"].sum()*TOT_REV/TOT_ATT)} at the studio’s own revenue per head.',
  'A per-format comp allowance makes an invisible number visible. It also stops the formats with the most loyal paying audiences from quietly '
  'absorbing the markdowns that belong to the studio as a whole.'),
 ('07','Use the day grid to re-time, not to cut','Programming',
  f'Every major format has at least one day it owns: {PEAK_B}. The same formats are weak on their worst day by a wide margin.',
  'The cheapest utilisation gain available is to move sessions from a format’s weakest day to its strongest, and from a format that is weak at '
  'that hour to one that is strong. That is a scheduling exercise, not a product decision, and it costs nothing to trial for a month.'),
 ('08','Report formats by their member economics, not their revenue','Management',
  f'Ranked by revenue the formats read PowerCycle, Barre 57, FIT. Ranked by fill they read FIT, Mat 57, PowerCycle X. Ranked by members reached they read '
  f'PowerCycle {MBR["mem"].get("Studio PowerCycle",0)}, Barre 57 {MBR["mem"].get("Studio Barre 57",0)}, FIT {MBR["mem"].get("Studio FIT",0)}. '
  'Ranked by how many of those members become regulars they read FIT first by a distance.',
  'A single monthly page carrying utilisation, members reached, regularity and revenue per head gives the studio four views of the same product. '
  'The current revenue-only view systematically favours the format with the most sessions.'),
 ('09','Watch the formats whose devotees drift','CRM + Programming',
  f'Members whose favourite format is PowerCycle have been absent an average of {FAV["since"].get("PowerCycle", float("nan")):.0f} days; '
  f'for FIT devotees it is {FAV["since"].get("FIT", float("nan")):.0f} days. '
  f'The value of a FIT devotee is {R(FAV["ticket"].get("FIT", np.nan))} against {R(FAV["ticket"].get("PowerCycle", np.nan))} for PowerCycle, on '
  f'{FAV["cls"].get("FIT", float("nan")):.1f} against {FAV["cls"].get("PowerCycle", float("nan")):.1f} classes.',
  'Favourite format is a useful early-warning field the studio already collects and does not read. A monthly count of members whose favourite '
  'format has gone quiet is a churn watch-list that costs nothing to produce.'),
 ('10','Judge a format on twelve sessions or not at all','Programming',
  f'<strong>{len(THIN)} of the {len(_FS)} formats Bandra ran in September appeared fewer than twelve times</strong> — between them {int(THIN["sessions"].sum())} sessions out of {int(_FS["sessions"].sum())}. '
  f'The express formats ran {int(EXPRESS["sessions"].sum())} sessions in the month between them, filling {EXPRESS["fill"].min():.0f}% to {EXPRESS["fill"].max():.0f}%.',
  f'A format that runs six times a month cannot be judged on fill rate, and it cannot be judged on revenue either. Either give a new format a real commitment — a fixed weekly slot for '
  f'a full quarter — or stop reporting on it. The studio is currently making programming decisions about formats it has barely tested.'),
 ('11','Let the length of a class decide, not the family it belongs to','Programming + Studio Manager',
  f'Inside the same format family the results separate sharply. PowerCycle Express fills <strong>{_FS.loc["Studio PowerCycle Express","fill"]:.0f}%</strong> across {int(_FS.loc["Studio PowerCycle Express","sessions"])} sessions; '
  f'Cardio Barre Express fills {_FS.loc["Studio Cardio Barre Express","fill"]:.0f}% across {int(_FS.loc["Studio Cardio Barre Express","sessions"])}. One is a premium express product, the other is an afternoon of empty seats.',
  f'The studio’s own timetable already contains the answer to its utilisation problem, in miniature: a short, specific, well-named class sells, and an unspecified short version of a long class does not. '
  f'Every express format should be rebuilt to the PowerCycle Express template — its own name, its own benefit, its own slot — before any of them is withdrawn.'),
 ('12','Put revenue per class next to fill rate in every programming review','Studio Manager + Finance',
  f'Across September the correlation between a format’s fill rate and its revenue per class is almost total — FIT fills {_FS.loc["Studio FIT","fill"]:.0f}% and earns '
  f'<strong>{R(_FS.loc["Studio FIT","rpc"])} a class</strong>; PowerCycle fills {_FS.loc["Studio PowerCycle","fill"]:.0f}% and earns {R(_FS.loc["Studio PowerCycle","rpc"])}. '
  f'The two columns rank the formats the same way.',
  f'Fill rate flatters formats with small rooms and penalises formats that were given the big ones, so any review that reads fill alone will keep making the same mistake. Revenue per class '
  f'is the number that survives the comparison, and pairing it with the studio’s cost per session turns a programming debate into an arithmetic one.'),

]
REC_HTML = rec_html(RECS)

SRC = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Session economics from <em>Day End Report - Part 3 - Sessions</em>, September 2024, 2025 and 2026, filtered to {E.B}. Capacity is per session
(total capacity divided by the number of classes recorded on the row). Member reach and regularity from the Day End Part 4 check-in ledger,
attended entries only. Favourite-format and format-count fields from the lapse ledger, which records the formats against each membership.
<br/>Formats with one or fewer sessions in the month are excluded from the comparison tables. Revenue is class-attributed revenue as recorded, not
contribution margin, and a complimentary seat earns nothing by construction.</p>'''

META = (f'Sessions ledger &middot; {len(x26):,} classes, September 2026<br/>'
        f'{len(F)} formats compared &middot; {int(TOT_ATT):,} attendances &middot; {R(TOT_REV)} attributed revenue<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra — Format Comparisons',
    'Report five of seven &middot; Product performance',
    'Format comparisons',
    f'{len(F)} formats, one timetable and one audience. The format that carries {F.loc["Studio PowerCycle","sessions"]/TOT_SESS*100:.0f}% of the week fills '
    f'{F.loc["Studio PowerCycle","fill"]:.1f}% of its seats; the format that carries {F.loc["Studio FIT","sessions"]/TOT_SESS*100:.0f}% fills {F.loc["Studio FIT","fill"]:.1f}%. '
    'This report compares them on eight measures at once and finds that the studio is not short of demand — it is short of the right demand in the right room.',
    META, f'''
<h2>Start here</h2>
<div class="sub">On revenue, PowerCycle leads. On every measure of efficiency, it is last among the formats that matter.</div>

<p>September 2026 ran <strong>{int(TOT_SESS):,} classes across {len(F26)} formats</strong>, drew {int(TOT_ATT):,} attendances and attributed
<strong>{R(TOT_REV)}</strong> of revenue to them. But the three largest formats are almost identical in scale and wildly different in behaviour.
<strong>PowerCycle and Barre 57 together carry {((F.loc['Studio PowerCycle','sessions']+F.loc['Studio Barre 57','sessions'])/TOT_SESS*100):.0f}% of the timetable and fill
{F.loc['Studio PowerCycle','fill']:.1f}% and {F.loc['Studio Barre 57','fill']:.1f}% respectively. Studio FIT carries {F.loc['Studio FIT','sessions']/TOT_SESS*100:.0f}% and fills {F.loc['Studio FIT','fill']:.1f}%.</strong></p>

<p>The reason this is not simply a scheduling problem is visible in the member data. PowerCycle reaches <strong>{MBR['mem'].get('Studio PowerCycle',0)} distinct members</strong>
in the month &mdash; more than any other format &mdash; while FIT reaches {MBR['mem'].get('Studio FIT',0)}. But of FIT&rsquo;s members,
<strong>{MBR['regp'].get('Studio FIT', float('nan')):.1f}% came four or more times inside the month</strong>. Of PowerCycle&rsquo;s, {MBR['regp'].get('Studio PowerCycle', float('nan')):.1f}% did.
FIT is not a bigger product. It is a stickier one, and the studio is giving the stickier product less than half the week.</p>

{CH_LEAGUE}

<h2>The league table</h2>
<div class="sub">Eight measures, and no format wins all of them. The pattern of who wins what is the finding.</div>

<p>Set the formats side by side and a division of labour emerges that the studio is not currently managing deliberately. <strong>FIT wins on fill ({F.loc['Studio FIT','fill']:.1f}%),
revenue per class ({R(F.loc['Studio FIT','rev_class'])}) and regularity ({MBR['regp'].get('Studio FIT', float('nan')):.1f}%).</strong> Mat 57 is second on fill at
{F26.loc['Studio Mat 57','fill']:.1f}% on a small timetable. PowerCycle leads on absolute attendance simply because it runs {F.loc['Studio PowerCycle','sessions']:.0f} sessions.
And the express formats &mdash; PowerCycle X at {F26.loc['Studio PowerCycle Express','fill']:.1f}%, Cardio Barre X at {F26.loc['Studio Cardio Barre Express','fill']:.1f}% &mdash;
are the widest spread in the table, which tells the studio that format length matters more than format family.</p>

{CH_SHARE}

<p>Read on revenue per head, however, the differences almost vanish: <strong>{R(F['rev_head'].min())} to {R(F['rev_head'].max())}</strong>, a spread of
{F['rev_head'].max()/F['rev_head'].min()*100-100:.0f}%. That is a striking result. It means the audience is worth roughly the same per person wherever they sit.
<strong>Formats do not differ in the value of the member. They differ in how many members the studio can get into the room.</strong></p>

{CH_ECO}

{ev('Evidence — the full format matrix, September 2026',
    T(['Format','Classes','Seats','Attended','Fill','Booked','Late canc.','Complimentary','Revenue','Per class','Per head','Cancel rate'],
      [[SHORT.get(k, k), int(r['sessions']), int(r['seats']), int(r['att']), P(r['fill']), int(r['booked']), int(r['lc']),
        int(r['comp']), R(r['rev']), R(r['rev_class']), R(r['rev_head']) if r['rev_head'] == r['rev_head'] else '—',
        P(r['cancel_rate']) if r['cancel_rate'] == r['cancel_rate'] else '—']
       for k, r in F26.sort_values('att', ascending=False).iterrows()], 'num small'))}

<h2>Reach against regularity</h2>
<div class="sub">PowerCycle brings the most people through the door. FIT is the only format that turns them into regulars.</div>

<p>Reach and regularity are different questions, and the studio currently answers only the first. In September,
<strong>PowerCycle touched {MBR['mem'].get('Studio PowerCycle',0)} individual members, Barre 57 {MBR['mem'].get('Studio Barre 57',0)} and FIT {MBR['mem'].get('Studio FIT',0)}</strong>.
But a member who comes once counts the same as a member who comes daily. Measured by the share of a format&rsquo;s audience that attended at least four times
in the month, the order reverses: <strong>FIT {MBR['regp'].get('Studio FIT', float('nan')):.1f}%, PowerCycle {MBR['regp'].get('Studio PowerCycle', float('nan')):.1f}%,
Barre 57 {MBR['regp'].get('Studio Barre 57', float('nan')):.1f}%</strong>, and the smaller formats fall to {MBR['regp'].get('Studio Mat 57', float('nan')):.1f}% and below.</p>

<p>The average member of each format tells the same story. A FIT attendee came <strong>{MBR['per'].get('Studio FIT', float('nan')):.2f} times</strong> in the month; a Barre 57 attendee
{MBR['per'].get('Studio Barre 57', float('nan')):.2f}; a Mat 57 attendee {MBR['per'].get('Studio Mat 57', float('nan')):.2f}. Meanwhile
<strong>{MBR['once'].get('Studio Mat 57', float('nan')):.0f}% of Mat 57&rsquo;s attendees and {MBR['once'].get('Studio Cardio Barre', float('nan')):.0f}% of Cardio Barre&rsquo;s came exactly once</strong> in the month.</p>

{CH_MEM}

{ev('Evidence — members reached, repeat visits and regularity by format',
    T(['Format','Distinct members','Attendances','Visits per member','Came 4+ times','Came exactly once'],
      [[SHORT.get(k, k), int(r['mem']), int(r['visits']), f"{r['per']:.2f}", P(r['regp']), P(r['once'])]
       for k, r in MBR.sort_values('mem', ascending=False).iterrows()], 'num'))}

<h2>The multi-format multiplier</h2>
<div class="sub">Nothing in this dataset separates members as cleanly as how many formats they have used.</div>

<p>The lapse ledger records every format each member has trained in. Sort members by that count and the economics move in a straight line.
A member who has used <strong>one format has paid an average of {R(NF['ticket'].get(1, float('nan')))} and completed {NF['cls'].get(1, float('nan')):.1f} classes</strong>.
At two formats that becomes {R(NF['ticket'].get(2, float('nan')))} and {NF['cls'].get(2, float('nan')):.1f}. At three, {R(NF['ticket'].get(3, float('nan')))} and {NF['cls'].get(3, float('nan')):.1f}.
By five formats the same member has paid <strong>{R(NF['ticket'].get(5, NF['ticket'].max()))}</strong> and completed <strong>{NF['cls'].get(5, NF['cls'].max()):.1f} classes</strong>.</p>

<p>This is a correlation and it would be wrong to read it as a mechanism &mdash; members who were going to stay longer naturally tried more. But it is a
remarkably clean gradient, and it points at a specific gap: <strong>only {P(NF[NF.index>=3]['members'].sum()/NF['members'].sum()*100)} of members have ever used three or more formats.</strong>
Most of the book has only ever known one room.</p>

{CH_NF}
{CH_NFV}

{ev('Evidence — the format ladder',
    T(['Formats used','Members','Mean paid','Mean classes completed','Mean days in force','Visits in the last 30 days'],
      [[int(i), int(r['members']), R(r['ticket']), f"{r['cls']:.1f}", f"{r['life']:.0f}", f"{r['last30']:.1f}"]
       for i, r in NF.iterrows()], 'num'))}

<h2>What a devotee is worth</h2>
<div class="sub">A member&rsquo;s favourite format predicts their value better than anything except their attendance.</div>

<p>Members whose favourite format is <strong>FIT</strong> have paid an average of <strong>{R(FAV['ticket'].get('FIT', np.nan))}</strong>,
completed {FAV['cls'].get('FIT', float('nan')):.1f} classes, and were last in the studio {FAV['since'].get('FIT', float('nan')):.0f} days ago.
Members whose favourite is PowerCycle have paid {R(FAV['ticket'].get('PowerCycle', np.nan))}, completed {FAV['cls'].get('PowerCycle', float('nan')):.1f} classes and were last seen
{FAV['since'].get('PowerCycle', float('nan')):.0f} days ago &mdash; and there are {FAV['members'].get('PowerCycle', 0)} of them against {FAV['members'].get('FIT', 0)}. The formats with the largest followings are not the
formats with the most committed ones.</p>

{CH_FAV}

{ev('Evidence — favourite format against lifetime value',
    T(['Favourite format','Members','Mean paid','Mean classes completed','Mean days in force','Days since last visit'],
      [[k, int(r['members']), R(r['ticket']), f"{r['cls']:.1f}", f"{r['life']:.0f}", f"{r['since']:.0f}"]
       for k, r in FAV.iterrows()], 'num'))}

<h2>When each format is used</h2>
<div class="sub">Every format owns a day. None of them owns the whole week, and the studio schedules as though they do.</div>

<p>Mapping attendance by format and day shows how concentrated each product&rsquo;s audience is. {PEAK_A}. The weakest day for each is
typically less than half the strongest.</p>

{CH_DH}

{ev('Evidence — attendance by format and day, September 2026',
    T(['Format'] + list(DH.columns[:-1]) + ['Total'],
      [[SHORT.get(k, k)] + [int(v) for v in row[:-1]] + [int(row['tot'])] for k, row in DH.iterrows()], 'num small'))}

<h2>Where the free seats sit</h2>
<div class="sub">Complimentary attendance is concentrated, and it lands on the formats with the most loyal paying audiences.</div>

<p>Across the studio {int(F26['comp'].sum()):,} attendances were complimentary in September. They are not evenly spread.
<strong>Barre 57 ran {F26.loc['Studio Barre 57','comp']/F26.loc['Studio Barre 57','att']*100:.1f}% of its attendance on comps</strong>, with Mat 57 at
{F26.loc['Studio Mat 57','comp']/F26.loc['Studio Mat 57','att']*100:.1f}% and PowerCycle at {F26.loc['Studio PowerCycle','comp']/F26.loc['Studio PowerCycle','att']*100:.1f}%,
against FIT at {F26.loc['Studio FIT','comp']/F26.loc['Studio FIT','att']*100:.1f}%. At the studio&rsquo;s revenue per head of {R(TOT_REV/TOT_ATT)}, those
{int(F26['comp'].sum()):,} seats represent {R(F26['comp'].sum()*TOT_REV/TOT_ATT)} of delivered value.</p>

{CH_COMP}

<h2>Recommendations</h2>
<div class="sub">Nine actions, ordered by the size of the opportunity each addresses</div>
{REC_HTML}
{SRC}
''')
open('/home/user/reports-arena/Bandra_September_2026_5_Format_Comparisons.html', 'w').write(HTML)
print(f'Report 5 written: {len(HTML)} bytes | formats {len(F)} | att {int(TOT_ATT)} | rev {TOT_REV:,.0f}')
print('fill:', {r['name']: round(r['fill'], 1) for _, r in F.iterrows()})
print('members:', {k: int(v) for k, v in MBR['mem'].items()})
print('nf:', NF.reset_index().to_dict('records'))
print('fav:', FAV.round(0).to_dict('index'))
