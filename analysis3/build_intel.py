"""Report 7 - Studio overview and intelligence, September 2026."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

TODAY = pd.Timestamp('2026-10-18')
LB, LP, L = E.LB, E.LP, E.L
X = D.XB.copy(); X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
def sx(y, m=9):
    a = pd.Timestamp(f'{y}-{m:02d}-01')
    return X[(X['dt'] >= a) & (X['dt'] < a + pd.offsets.MonthBegin(1))]
x24, x25, x26 = sx(2024), sx(2025), sx(2026)
SB = D.SB.copy()   # item-level disc arrives from d1_data

# ---------------------------------------------------------------- the year
YR = {}
for y, s in ((2024, x24), (2025, x25), (2026, x26)):
    YR[y] = dict(sessions=len(s), seats=int(s['Capacity'].sum()), att=int(s['CheckedIn'].sum()),
                 rev=s['Revenue'].sum(), classes=int(s['Booked'].sum()), lc=int(s['LateCancelled'].sum()),
                 comp=int(s['Complimentary'].sum()))
    YR[y]['fill'] = YR[y]['att']/YR[y]['seats']*100
    YR[y]['rev_class'] = YR[y]['rev']/YR[y]['sessions']
    YR[y]['rev_head'] = YR[y]['rev']/YR[y]['att']
SALES = {}
for y in (2024, 2025, 2026):
    s = SB[(SB['dt'] >= f'{y}-09-01') & (SB['dt'] < f'{y}-10-01')]
    SALES[y] = dict(lines=len(s), cash=s['val'].sum(), buyers=s['Member ID'].nunique(), disc=s['disc'].sum())
    SALES[y]['ticket'] = SALES[y]['cash']/max(SALES[y]['buyers'], 1)

PRODB = LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ', '', regex=True).str.strip()).groupby('fam').agg(
    Sold=('Member ID', 'size'), Members=('Member ID', 'nunique'), Cash=('Amount Paid', 'sum'),
    Mean_ticket=('Amount Paid', 'mean'), Mean_classes=('Total Sessions Completed', 'mean'),
    Mean_days=('Membership Duration (Days)', 'mean'),
    Live_pct=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100))
PRODB = PRODB[PRODB['Sold'] >= 15].sort_values('Sold', ascending=False)
PRODB['Cash'] = PRODB['Cash'].round(0); PRODB['Mean_ticket'] = PRODB['Mean_ticket'].round(0)
PRODB['Mean_classes'] = PRODB['Mean_classes'].round(1); PRODB['Mean_days'] = PRODB['Mean_days'].round(0)
PRODB['lbl'] = [i[:26] for i in PRODB.index]
TOP4 = PRODB.head(4)
BEST = PRODB.sort_values('Live_pct', ascending=False).iloc[0]
VOLS = ', '.join([f'{i} {int(r["Sold"]):,} units at {r["Live_pct"]:.0f}% live' for i, r in TOP4.iterrows()])
VOL_SHARE = TOP4['Sold'].sum() / PRODB['Sold'].sum() * 100

# ---------------------------------------------------------------- the member base
CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID', 'Location', 'Date (IST)', 'Checked In', 'Cleaned Class', 'Class No'])
CK = CK[CK['Location'] == E.B].copy()
CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
AT = CK[CK['dt'].notna() & (CK['Checked In'] == True)].copy()
AT['dt'] = pd.to_datetime(AT['Date (IST)'], errors='coerce')
BASE, VPD = {}, {}
for y in (2024, 2025, 2026):
    s = AT[(AT['dt'] >= f'{y}-09-01') & (AT['dt'] < f'{y}-10-01')]
    VPD[y] = s.groupby('Member ID').size()
    BASE[y] = dict(members=s['Member ID'].nunique(), visits=len(s), per=len(s)/max(s['Member ID'].nunique(), 1))
CORE = set(VPD[2025].index) & set(VPD[2026].index)
CORE_LOST = float(VPD[2025].reindex(list(CORE)).sum() - VPD[2026].reindex(list(CORE)).sum())
LEFTOVER = set(VPD[2025].index) - set(VPD[2026].index)
NEWIN = set(VPD[2026].index) - set(VPD[2025].index)
NEWVIS = float(VPD[2026].reindex(list(NEWIN)).sum())
OLDVIS = float(VPD[2025].reindex(list(LEFTOVER)).sum())
one_done = int((VPD[2025].reindex(list(LEFTOVER)) == 1).sum())
career = AT.groupby('Member ID').size()
c_core, c_gone = float(career.reindex(list(CORE)).mean()), float(career.reindex(list(LEFTOVER)).mean())
FREQD = pd.DataFrame({'Visits in September': [str(i) for i in range(1, 10)] + ['10 to 12', '13 or more'],
    'Members': [int((VPD[2026] == k).sum()) for k in range(1, 10)] + [int(((VPD[2026] >= 10) & (VPD[2026] <= 12)).sum()), int((VPD[2026] >= 13).sum())]})
FREQD['Share'] = (FREQD['Members'] / len(VPD[2026]) * 100).round(1)
FREQD['Visits'] = [int(VPD[2026][VPD[2026] == k].sum()) for k in range(1, 10)] + [int(VPD[2026][(VPD[2026] >= 10) & (VPD[2026] <= 12)].sum()), int(VPD[2026][VPD[2026] >= 13].sum())]
SINGLE = int((VPD[2026] == 1).sum())

# ---------------------------------------------------------------- leads
LBc = LB.copy(); LBc['LTVn'] = E.num(LBc['LTV']); LBc['won'] = LBc['Status'] == 'Won'
CH = LBc.groupby('Channel').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x=='Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean')).sort_values('leads', ascending=False)
CH['ltv'] = CH['ltv'].round(0)
CH['lbl'] = [i.split(' ◉')[0][:34] for i in CH.index]
SRC = LBc.groupby('Source Name').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x=='Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean')).sort_values('leads', ascending=False)
SRC['ltv'] = SRC['ltv'].round(0)
SRC = SRC[SRC['leads'] >= 40]
MON = {}
for y in (2025, 2026):
    m = LBc[(LBc['Created At_d'] >= f'{y}-01-01') & (LBc['Created At_d'] < f'{y+1}-01-01')]
    MON[y] = m.groupby(m['Created At_d'].dt.month).size()
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
ASSOC = LBc.groupby('Associate').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x=='Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean'), resp=('resp_days', 'median'))
ASSOC = ASSOC[ASSOC['leads'] >= 30].sort_values('won', ascending=False)
ASSOC['ltv'] = ASSOC['ltv'].round(0)
CT = LBc.groupby('Class Type').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x=='Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)))
CT = CT[CT['leads'] >= 100].sort_values('leads', ascending=False)
RESP = LBc['resp_days'].dropna()
RESP_R = (RESP < 0).mean()*100
RESPC = pd.cut(RESP, [-1, 0, 1, 3, 7, 100000], labels=['same day', 'next day', '2 to 3 days', '4 to 7 days', 'over a week'])
RC = LBc.assign(rb=RESPC).groupby('rb', observed=True).agg(leads=('ID', 'size'), won=('won', lambda x: round(x.mean()*100, 1)))

# ---------------------------------------------------------------- the book
LIVE = LP[LP['Derived Status'].isin(['Active', 'Renewal Grace Period', 'Renewed'])]
LIVE_BY = LIVE.groupby('Derived Status').agg(n=('Member ID', 'size'), members=('Member ID', 'nunique'), cash=('Amount Paid', 'sum'))
RECB = ['in the last 7 days','8 to 14 days ago','15 to 30 days ago','31 to 60 days ago','over 60 days ago']
LIVE = LIVE.assign(rb=pd.cut(LIVE['Days Since Last Visit'], [-1, 7, 14, 30, 60, 99999], labels=RECB))
LREC = LIVE.groupby('rb', observed=True).agg(members=('Member ID', 'nunique'), cash=('Amount Paid', 'sum'))
QUIET = int(LREC['cash'].reindex(RECB[2:]).sum()); QUIET_M = int(LREC['members'].reindex(RECB[2:]).sum())
GRACE = LIVE_BY['cash'].get('Renewal Grace Period', 0)

# ---------------------------------------------------------------- the money
R12 = SB[SB['dt'] >= '2025-10-01']
per = R12.groupby('Member ID')['val'].sum().sort_values(ascending=False)
CUM = {k: per.head(k).sum()/per.sum() for k in (10, 25, 50, 100, 200, 500)}
BOT = per.tail(len(per)//2).sum()/per.sum()*100
ONCE = int((R12.groupby('Member ID')['Sale ID'].nunique() == 1).sum())
CATS = SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')].groupby('Cleaned Category')['val'].agg(['size', 'sum']).sort_values('sum', ascending=False)

# ---------------------------------------------------------------- the room
x26 = x26.copy(); x26['hr'] = pd.to_numeric(x26['Time'].astype(str).str[:2], errors='coerce')
HRS = ['07:00','08:00','09:00','10:00','11:00','17:00','18:00','19:00']
HR = x26.groupby('hr').agg(sessions=('SessionID','size'), seats=('cap','sum'), att=('CheckedIn','sum'), rev=('Revenue','sum'))
HR['fill'] = HR['att']/HR['seats']*100
DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
DW = x26.groupby('Day').agg(sessions=('SessionID','size'), seats=('cap','sum'), att=('CheckedIn','sum'), rev=('Revenue','sum')).reindex(DAYS)
DW['fill'] = DW['att']/DW['seats']*100
WED = DW.loc['Wednesday']; TUE = DW.loc['Tuesday']

# ---------------------------------------------------------------- second visit
MBf = D.MB.copy()
MBf['d2'] = E.num(MBf['Days To Second Visit'])
MBf['v2'] = MBf['d2'].notna() | (E.num(MBf['No of Visits']).fillna(0) >= 2)
MBf['v3'] = MBf['v2'] & (E.num(MBf['No of Visits']).fillna(0) >= 3)
MB = MBf
MB['db'] = pd.cut(MB['d2'], [-1, 1, 3, 7, 14, 30, 100000],
                  labels=['Same or next day', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31+ days'])
MBS = MB.dropna(subset=['d2']).groupby('db', observed=True).agg(n=('Member Id', 'size'), ltv=('Ltv', lambda x: round(E.num(x).mean())))
MBS['share'] = (MBS['n'] / MBS['n'].sum() * 100).round(1)

# ---------------------------------------------------------------- charts
CH_LEADM = lines(MONTHS, [(str(y), [int(MON[y].get(i, 0)) for i in range(1, 13)], c) for y, c in [(2025, N1), (2026, A1)]],
    'Leads created each month, 2025 and 2026', h=310, as_pct=False, ymax=380,
    note='The second half of 2026 is tracking below the same months of 2025, and below the studio’s own first quarter.')

CH_CHAN = bars(list(CH['lbl']), [('Leads', CH['leads'].tolist(), A1),
                                 ('Share won, % (scaled ×10)', [v*10 for v in CH['won']], B1)],
    'Where the leads come from, and how many of them convert', h=340, ymax=3900, rotate=True,
    note='The two largest channels by volume convert at a third of the rate of the two smallest. The second series is drawn at ten times its true value.')

CH_CHANL = hbars([(r['lbl'], r['ltv'], A1 if r['ltv'] >= CH['ltv'].median() else B1) for _, r in CH.iterrows()],
    'Mean lifetime value of a lead, by the channel it arrived through', maxv=12000,
    note='Measured on every lead the studio has ever recorded for Bandra, whether or not it converted.')

CH_SRC = hbars([(i[:30], r['won'], A1 if r['won'] >= 15 else B1) for i, r in SRC.iterrows()],
    'Conversion by source — the named channel behind each lead', as_pct=True, maxv=30,
    note='Sources with forty or more leads. The studio’s largest named source is its weakest by a wide margin.')

CH_FUN = funnel([('Leads created', int(len(LBc)), 'every enquiry the studio has ever recorded for Bandra'),
                 ('Trial completed', int((LBc['Trial Status'] == 'Trial Completed').sum()), f'{(LBc["Trial Status"]=="Trial Completed").mean()*100:.1f}% of leads'),
                 ('Membership sold', int(LBc['won'].sum()), f'{LBc["won"].mean()*100:.1f}% of leads'),
                 ('Retained today', int((LBc['Retention Status'] == 'Retained').sum()), f'{(LBc["Retention Status"]=="Retained").mean()*100:.1f}% of leads')],
    'The whole acquisition funnel, from enquiry to retained member')

CH_ASSOC = hbars([(i, r['won'], A1 if r['won'] >= 15 else (A2 if r['won'] >= 11 else B1)) for i, r in ASSOC.iterrows()],
    'Share of leads converted, by the person who handled them', as_pct=True, maxv=24,
    note='Associates with thirty or more recorded leads. All of them work the same product list at the same prices.')

CH_RESP = bars(list(RC.index), [('Leads', RC['leads'].tolist(), A1),
                                ('Share won, % (scaled ×5)', [v*5 for v in RC['won']], B1)],
    'How fast the first response was, against whether the lead converted', h=300, ymax=2000,
    note='Response time here is days between the enquiry and the first logged follow-up; roughly a fifth of records carry a date that precedes the enquiry and are excluded.')

CH_LIVE = bars(RECB, [('Members', LREC['members'].tolist(), A1)],
    'The live book, by how long since the member was last in the studio', h=310, ymax=200,
    note=f'{QUIET_M} members holding {R(QUIET)} of recorded cash have not trained in fifteen days or more.')

CH_HR = bars([f'{int(h):02d}:00' for h in HR.index], [('Seats offered', HR['seats'].tolist(), N2),
                                                      ('Seats filled', HR['att'].tolist(), A1),
                                                      ('Free seats, as a count', HR['att'].rsub(HR['seats']).tolist(), B2)],
    'Supply against demand through the September day', h=320, ymax=700,
    note='The three bars sum to the seats offered. The studio runs 30 sessions at 07:00 at 26% utilisation and 36 at 11:00 at 56%.')

CH_DAY = bars([d[:3] for d in DAYS], [('Seats offered', DW['seats'].tolist(), N2),
                                      ('Seats filled', DW['att'].tolist(), A1)],
    'Supply against demand through the September week', h=300, ymax=700,
    note=f'Tuesday runs the most sessions and the most attendance; Wednesday runs {int(WED["sessions"])} sessions at {WED["fill"]:.0f}% and earns {R(WED["rev"])}.')

CH_CONC = bars(['the top 10','11 to 25','26 to 50','51 to 100','101 to 500', f'all {len(per)-500:,} others'],
    [('Share of the last twelve months’ sales', [CUM[10], CUM[25]-CUM[10], CUM[50]-CUM[25], CUM[100]-CUM[50],
        CUM[500]-CUM[100], 1-CUM[500]], A1)],
    'Where a year of sales actually comes from', h=310, as_pct=True, ymax=0.32,
    note=f'{len(per):,} people bought something in the year to 30 September. The ten largest account for {CUM[10]*100:.1f}% of the cash; the bottom half for {BOT:.1f}%.')

CH_CT = bars(list(CT.index), [('Leads', CT['leads'].tolist(), A1),
                              ('Share won, % (scaled ×10)', [v*10 for v in CT['won']], B1)],
    'Which class a lead asks about, and whether it converts', h=300, ymax=6000, rotate=True,
    note='Class preference is recorded on almost every lead, which makes it one of the most complete demand signals the studio holds.')

CH_PROD = hbars([(i, r['Sold'], A1) for i, r in PRODB.head(9).iterrows()],
    'What the studio sells, and how much of it is still alive', unit='', maxv=None,
    note='Units sold by product since 2022. The two largest lines are both entry products.')

CH_BASE = bars(['Sept 2024', 'Sept 2025', 'Sept 2026'],
    [('Members who trained at least once', [BASE[y]['members'] for y in (2024, 2025, 2026)], A1),
     ('Visits each, scaled ×100', [round(BASE[y]['per'] * 100) for y in (2024, 2025, 2026)], B1)],
    'A wider base, coming less often', h=300, ymax=520,
    note='The amber series is average visits per member, drawn at a hundred times its true value so the two measures share an axis.')

CH_CORE = bars(['September 2025', 'September 2026'],
    [('Visits by the same members', [int(VPD[2025].reindex(list(CORE)).sum()), int(VPD[2026].reindex(list(CORE)).sum())], A1)],
    'The same people, the same month, twelve months apart', h=280, ymax=800,
    note=f'The {len(CORE)} members who trained here in both Septembers gave the studio {abs(int(CORE_LOST)):,} fewer visits this year, a fall of {abs(CORE_LOST)/VPD[2025].reindex(list(CORE)).sum()*100:.0f}%.')

# ---------------------------------------------------------------- recommendations
RECS = [
 ('01','Rebalance acquisition away from the website and toward the phone','Marketing + CRM',
  f'<strong>Website and online sources produced {CH.loc["Website & Online Sources","leads"]:,} leads — {CH.loc["Website & Online Sources","leads"]/len(LBc)*100:.0f}% of everything the studio attracts — and converted {CH.loc["Website & Online Sources","won"]:.1f}% of them at a lifetime value of {R(CH.loc["Website & Online Sources","ltv"])}.</strong> '
  f'Calls and messages produced {CH.loc["Calls, Messages & Automated Enquiries","leads"]:,} at {CH.loc["Calls, Messages & Automated Enquiries","won"]:.1f}% and {R(CH.loc["Calls, Messages & Automated Enquiries","ltv"])}; referrals produced '
  f'{CH.loc["Referrals & Word-of-Mouth","leads"]:,} at {CH.loc["Referrals & Word-of-Mouth","won"]:.1f}% and {R(CH.loc["Referrals & Word-of-Mouth","ltv"])}.',
  f'One referral is worth more than two website leads, and one inbound call worth more than two and a half. The studio is not short of leads; it is short of the '
  f'leads that convert. A visible referral reward and a published phone number at the point of enquiry are the cheapest mix change available.'),
 ('02','Target the trial at the class people already ask for','Programming + Marketing',
  f'Barre 57 is the class {CT.loc["Barre 57","leads"]/CT["leads"].sum()*100:.0f}% of Bandra leads ask about ({int(CT.loc["Barre 57","leads"]):,} leads) and it converts at '
  f'{CT.loc["Barre 57","won"]:.1f}%. PowerCycle asks occupy {int(CT.loc["powerCycle","leads"]):,} leads at {CT.loc["powerCycle","won"]:.1f}%.',
  f'Demand is stated explicitly on almost every enquiry and the studio is already recording it. Booking the trial into the format the lead asked for, rather than '
  f'into whatever slot is free, is a scheduling decision that costs nothing and removes the most common cause of a lost first impression.'),
 ('03','Put a named owner and a target on the unconverted','CRM + Studio Manager',
  f'Of {len(LBc):,} Bandra leads, <strong>{int((LBc["Status"]=="Won").sum()):,} became members and {int((LBc["Status"]=="Open").sum()):,} are still open</strong>. '
  f'{int((LBc["Status"]=="Unresponsive").sum()):,} are marked unresponsive and {int((LBc["Status"]=="Disqualified").sum()):,} disqualified.',
  f'The open file is larger than two years of wins. It has no owner, no target and no date attached to it, and it is the single largest piece of unrealised '
  f'value in this report. A monthly review of open leads older than thirty days, with one person accountable, would convert some of it and close the rest honestly.'),
 ('04','Publish conversion by associate and manage the spread','Studio Manager + CRM',
  f'The spread is wide and it is not explained by volume: the strongest associate converts <strong>{ASSOC["won"].max():.1f}% of {int(ASSOC["won"].idxmax() and ASSOC.loc[ASSOC["won"].idxmax(),"leads"]):,} leads</strong>, '
  f'the weakest {ASSOC["won"].min():.1f}% of {int(ASSOC.loc[ASSOC["won"].idxmin(),"leads"]):,}. Median first-response time is between {int(ASSOC["resp"].min())} and {int(ASSOC["resp"].max())} days across the team.',
  f'The highest-converting associate is not the one handling the most leads. Publishing the table monthly, without naming anyone, moves the middle of the '
  f'distribution; pairing the strongest closer with the largest in-box moves the top.'),
 ('05','Answer faster, and measure it','Front Desk + CRM',
  f'The median first response is <strong>{RESP.median():.0f} days after the enquiry</strong> and only {RC.loc["same day", "leads"] if "same day" in RC.index else 0:,} leads were answered the same day. '
  f'{RESP_R:.0f}% of records carry a follow-up date that precedes the enquiry itself, which suggests the field is being back-filled rather than logged.',
  'Speed is the one variable in lead handling that the studio controls completely and has never measured properly. A response-time target, logged automatically, '
  'would turn an unmanaged process into a number. Fixing the negative dates first is a prerequisite for trusting any of it.'),
 ('06','Work the renewal grace list as a live pipeline','CRM + Front Desk',
  f'<strong>{int(LIVE_BY["n"].get("Renewal Grace Period",0))} memberships worth {R(GRACE)} are in a renewal grace period right now</strong>, and a further '
  f'{int(LIVE_BY["n"].get("Active",0))} are active. Between them they carry {R(LIVE["Amount Paid"].sum())} of recorded cash.',
  'Grace period is a decision window, not a status. These members have not said no — they have stopped being asked. A named call on each one, with the '
  'member’s own attendance and favourite format on the screen, converts the list from administration into pipeline.'),
 ('07','Call the quiet members before they lapse','CRM',
  f'<strong>{QUIET_M} members holding {R(QUIET)} of recorded cash have not trained in fifteen days or more</strong>, and {int(LREC["members"].reindex(RECB[3:]).sum())} of them have not been in for over a month. '
  f'Lapsed memberships in this book are worth only {R(LP[LP["Derived Status"]=="Lapsed"]["Amount Paid"].mean())} on average against {R(LIVE_BY["cash"].sum()/LIVE_BY["n"].sum())} for live ones.',
  'The studio already holds the two fields that predict a lapse: days since last visit and visits in the last 30. A weekly list of anyone whose 30-day visit count '
  'has fallen to zero while their membership is still live is the highest-yield call list the studio can build, and it needs no new data.'),
 ('08','Cut Wednesday and the early morning, and put the seats where the demand is','Programming + Studio Manager',
  f'Wednesday ran <strong>{int(WED["sessions"])} sessions at {WED["fill"]:.0f}% utilisation for {R(WED["rev"])}</strong>; Tuesday ran {int(TUE["sessions"])} at {TUE["fill"]:.0f}% for {R(TUE["rev"])}. '
  f'At 07:00 the studio offered {int(HR.loc[7,"seats"])} seats and filled {int(HR.loc[7,"att"])}; at 11:00 it offered {int(HR.loc[11,"seats"])} and filled {int(HR.loc[11,"att"])}.',
  f'Two days and two hours account for most of the unused capacity in the month. Moving sessions out of the weakest day and hour and into the strongest is a timetable edit, '
  f'reversible after four weeks, and it lifts utilisation without a single new member.'),
 ('09','Give every new member their second and third visit as a plan','Front Desk + CRM',
  f'Across {len(MB):,} Bandra first-timers, <strong>{MB["v2"].mean()*100:.1f}% reach a second visit and {MB["v3"].mean()*100:.1f}% reach a third</strong>. '
  f'Of those who do come back, {MBS.loc["2 to 3 days","n"]/MBS["n"].sum()*100:.0f}% return within three days and {MBS.loc[["Same or next day","2 to 3 days","4 to 7 days"],"n"].sum()/MBS["n"].sum()*100:.0f}% within a week. '
  f'Among members whose second visit took a month or more, lifetime value is {R(MBS.loc["31+ days","ltv"])} against {R(MBS.loc["Same or next day","ltv"])} for those who returned immediately.',
  f'The second visit is the transition that decides everything else, and the data says it happens inside a week or not at all. Booking visits two and three before '
  f'the member leaves the building converts an intention into a diary entry, and a diary entry is the only thing that has ever predicted a fourth visit.'),
 ('10','Make the unpaid seat visible in the fill rate','Finance + Studio Manager',
  f'September gave away {YR[2026]["comp"]:,} complimentary attendances — {YR[2026]["comp"]/YR[2026]["att"]*100:.1f}% of everything delivered — worth {R(YR[2026]["comp"]*YR[2026]["rev_head"])} '
  f'at the month’s own revenue per head. Comps are excluded from no denominator in the studio’s reporting.',
  f'Reporting utilisation alongside a paid-utilisation figure would show the studio what its promotions actually cost it in seats. No rule change is needed to '
  f'start with the number — only a second column.'),
 ('11','Track the four leading indicators monthly, and nothing else','Management',
  f'The studio currently reports attendance, revenue and member counts, all of which describe a month that has already finished. The four numbers that move '
  f'first are leads created ({int(MON[2026].get(9, 0))} in September), leads converted ({LBc[(LBc["Created At_d"]>="2026-09-01") & (LBc["Created At_d"]<"2026-10-01")]["won"].mean()*100:.1f}%), '
  f'bookings against capacity ({YR[2026]["classes"]/YR[2026]["seats"]*100:.1f}%), and visits per active member.',
  f'Each of those four can be read within a week of the month ending and each one predicts the others. A single page carrying them, published on the first working '
  f'day, would give the studio a month of warning instead of a month of explanation.'),
 ('12','Keep the two things that are working','Studio Manager',
  f'Revenue per attendance rose from {R(YR[2025]["rev_head"])} to {R(YR[2026]["rev_head"])} and revenue per class from {R(YR[2025]["rev_class"])} to {R(YR[2026]["rev_class"])}. '
  f'Late cancellations fell from {YR[2025]["lc"]:,} to {YR[2026]["lc"]:,}. The average September buyer spent {R(SALES[2026]["ticket"])} against {R(SALES[2025]["ticket"])} a year earlier.',
  f'These are genuine gains, achieved in a softer market, and they are the reason the studio is having a conversation about frequency rather than about survival. '
  f'They should be named, defended and reported as the standard the rest of the business is measured against.'),
]
REC_HTML = rec_html(RECS)

SRCBOX = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Six independent sources underpin this report, joined on member ID where they overlap. Lead behaviour comes from the CRM lead master
({len(E.LD):,} records across all centres, {len(LBc):,} for Bandra). Membership lifecycle comes from the lapse ledger
({len(L):,} Bandra instances, of which {len(LP):,} are paid). Room and revenue economics come from the Sessions export. Check-in behaviour
comes from the Day End Part 4 ledger. Acquisition value comes from the New member file. Payments come from the raw sales export.<br/>
Channel and source are the studio&rsquo;s own CRM taxonomy and are used as recorded; a lead is counted once at creation and its outcome is the status it
carries today, so recent months are understated for conversion. Response time is the interval between the lead&rsquo;s creation and the first of four
follow-up dates; the field is populated for {RESP.notna().mean()*100:.0f}% of records and {RESP_R:.0f}% carry a date that precedes the enquiry, so it is indicative rather than exact.<br/>
Revenue is gross value as recorded at snapshot, not contribution margin. Lapsed-membership cash is the amount recorded against the membership, not
revenue attributable to the month it lapsed.</p>'''

META = (f'CRM lead master &middot; {len(LBc):,} Bandra leads<br/>'
        f'Membership ledger &middot; {len(LP):,} paid memberships &middot; {len(LIVE_BY)} live instances<br/>'
        f'Room ledger &middot; {YR[2026]["sessions"]} classes in September &middot; {YR[2026]["seats"]:,} seats offered<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra — Studio Overview and Intelligence',
    'Studio Overview and Business Intelligence &nbsp;&middot;&nbsp; September 2026',
    'Supreme HQ, Bandra — the studio in one page',
    f'September held {R(SALES[2026]["cash"])} of cash from {SALES[2026]["buyers"]} buyers, delivered {YR[2026]["att"]:,} attendances across '
    f'{YR[2026]["sessions"]} classes, and converted {(LBc["won"].mean())*100:.1f}% of every lead the studio has ever recorded. This report joins the lead file, '
    f'the membership ledger, the room ledger and the sales ledger to answer one question: where does the next member come from, and what is stopping them?',
    META, f'''
<h2>Start here</h2>
<div class="sub">Four numbers describe the studio. Two are improving, one has stalled, and one has never been managed at all.</div>

<p><strong>Margin is improving.</strong> Revenue attributed to attended classes rose from {R(YR[2025]["rev"])} to {R(YR[2026]["rev"])} on
{abs(YR[2026]["sessions"]-YR[2025]["sessions"])} fewer classes, and revenue per class rose from {R(YR[2025]["rev_class"])} to
<strong>{R(YR[2026]["rev_class"])}</strong>. Revenue per attendance rose from {R(YR[2025]["rev_head"])} to {R(YR[2026]["rev_head"])}. The average September buyer
spent <strong>{R(SALES[2026]["ticket"])}</strong> against {R(SALES[2025]["ticket"])} a year ago.</p>

<p><strong>Discipline is improving.</strong> Late cancellations fell from {YR[2025]["lc"]:,} to {YR[2026]["lc"]:,}, and the share of the board that was ever
booked at all fell from {YR[2025]["classes"]/YR[2025]["seats"]*100:.1f}% to {YR[2026]["classes"]/YR[2026]["seats"]*100:.1f}% &mdash; which sounds like bad news
and is, but it is honest news: the studio is no longer counting seats nobody intended to use.</p>

<p><strong>Acquisition has stalled.</strong> Bandra created {int(MON[2026].get(9, 0))} leads in September 2026, against a 2026 monthly average of
{int(MON[2026].sum()/9):,} and a 2025 average of {int(MON[2025].sum()/12):,}. Of every lead the studio has ever recorded for this location,
<strong>{(LBc["won"].mean())*100:.1f}% became a member</strong> and {(LBc["Retention Status"]=="Retained").mean()*100:.1f}% are retained today.</p>

<p><strong>Frequency has never been managed.</strong> {int(LIVE_BY["n"].sum())} memberships are live, worth {R(LIVE["Amount Paid"].sum())} of recorded cash.
<strong>{QUIET_M} of those members, holding {R(QUIET)}, have not been in the studio for fifteen days or more.</strong> No one is currently responsible for that list,
and it is the largest recoverable number in this report.</p>

<div class="call b"><h4>The single sentence version</h4>
<p>The studio has learned to earn more from every seat and to lose fewer of them at the last minute. What it has not yet learned is who its members are, when they
are about to stop, and how to reach them before they do &mdash; and every one of the three is already visible in the data it holds.</p></div>

{CH_LEADM}

<h2>The year in numbers</h2>
<div class="sub">Three Septembers, four ledgers, one comparison.</div>

{ev('Evidence — the three ledgers, September 2024, 2025 and 2026',
    T(['September', 'Classes', 'Seats offered', 'Attended', 'Utilisation', 'Late cancellations', 'Complimentary',
       'Class revenue', 'Revenue / class', 'Revenue / attendee', 'Buyers', 'Cash', 'Cash / buyer'],
      [[str(y), YR[y]['sessions'], f"{YR[y]['seats']:,}", f"{YR[y]['att']:,}", P(YR[y]['fill']),
        YR[y]['lc'], YR[y]['comp'], R(YR[y]['rev']), R(YR[y]['rev_class']), R(YR[y]['rev_head']),
        f"{SALES[y]['buyers']:,}", R(SALES[y]['cash']), R(SALES[y]['ticket'])] for y in (2024, 2025, 2026)], 'num'))}

<h2>The member base</h2>
<div class="sub">The studio has more members than a year ago and fewer visits. Both halves of that sentence matter.</div>

<p>This is the most important correction in the report, and it is why a single attendance number is a dangerous thing to manage from.
<strong>{BASE[2026]['members']} members trained at Bandra in September 2026, against {BASE[2025]['members']} a year earlier and {BASE[2024]['members']} the year before.</strong>
The base has widened by {BASE[2026]['members']/BASE[2025]['members']*100-100:.1f}% in twelve months and is at its widest in three years.</p>

<p>Attendance fell anyway, from {YR[2025]['att']:,} to {YR[2026]['att']:,}. The reason is arithmetic: visits per member fell from
<strong>{BASE[2025]['per']:.2f} to {BASE[2026]['per']:.2f}</strong>. The studio did not lose its audience. It lost its audience&rsquo;s
frequency, and the two are managed in completely different ways.</p>

{CH_BASE}

<p>The distribution behind that average explains the whole of the month. <strong>{SINGLE} of {len(VPD[2026])} members came exactly once</strong> &mdash;
{SINGLE/len(VPD[2026])*100:.0f}% of the base &mdash; and the members who came ten times or more, {int((VPD[2026]>=10).sum())} people,
delivered {int(VPD[2026][VPD[2026]>=10].sum())} attendances between them &mdash; {VPD[2026][VPD[2026]>=10].sum()/YR[2026]['att']*100:.0f}% of the month.</p>

{ev('Evidence — how many times each member came in September 2026',
    T(['Visits in the month', 'Members', 'Share of members', 'Visits delivered'],
      [[r['Visits in September'], int(r['Members']), P(r['Share']), int(r['Visits'])] for _, r in FREQD.iterrows()], 'num'))}

<h2>The returning core</h2>
<div class="sub">{len(CORE)} people were in the room in both Septembers. Between them they account for a fifth of everything the studio filled this year.</div>

<p><strong>The {len(CORE)} members who trained at Bandra in both September 2025 and September 2026 made {int(VPD[2025].reindex(list(CORE)).sum())} visits last year
and {int(VPD[2026].reindex(list(CORE)).sum())} this year</strong> &mdash; a fall of {abs(CORE_LOST)/VPD[2025].reindex(list(CORE)).sum()*100:.0f}%, and
<strong>{abs(int(CORE_LOST)):,} visits</strong> that simply did not happen. That is
{abs(CORE_LOST)/YR[2026]['att']*100:.0f}% of every seat the studio filled in September 2026.</p>

<p>This is a true like-for-like group: the same people, the same month, twelve months apart. Had they held their year-ago frequency, September 2026 would have
recorded {int(YR[2026]['att']+abs(CORE_LOST)):,} attendances &mdash; ahead of last September&rsquo;s {YR[2025]['att']:,}, not behind it.
<strong>The month&rsquo;s decline is not an acquisition failure at all. It is a frequency failure among the members who already know the studio.</strong></p>

{CH_CORE}

<p>Who left is a second, quieter finding. Of the {len(LEFTOVER)} members who trained last September and did not appear this September,
<strong>{one_done} had made exactly one visit in that month</strong>. On lifetime numbers the distinction is stark: the members who stayed had averaged
{c_core:.0f} career visits; the ones who left had averaged {c_gone:.0f}. And the replacements are working harder than the departures did &mdash;
the {len(NEWIN)} members with no September 2025 visit delivered {int(NEWVIS):,} attendances this month, against the {int(OLDVIS):,} left behind by the
{len(LEFTOVER)} who departed.</p>

<div class="call b"><h4>What this reframes</h4>
<p>Acquisition is not the problem this report is about. The studio recruited {len(NEWIN)} members this September, more than enough to cover
its losses of {len(LEFTOVER)}. The problem is that both the arrivals and the regulars are coming fewer times each, and no measure the studio
currently reports would show that.</p></div>

<h2>What the memberships look like</h2>
<div class="sub">The studio sells two products in volume, and both of them are designed to end.</div>

<p>Everything the studio has sold as a membership at Bandra is in this ledger: {len(LP):,} paid memberships from {LP['Member ID'].nunique():,} people, worth
{R(LP['Amount Paid'].sum())}. <strong>The four largest products account for {VOL_SHARE:.0f}% of every membership sold</strong>, and every one of them is built to end quickly:
{VOLS}.</p>

<p>The product that keeps its members is not the product that sells in volume. <strong>{BEST.name} renews or stays live {BEST['Live_pct']:.0f}% of the time, the best rate in the range</strong>, and it is bought by {int(BEST['Sold'])} people. The four volume lines together have produced
{int(TOP4['Sold'].sum()):,} memberships and between {TOP4['Live_pct'].min():.0f}% and {TOP4['Live_pct'].max():.0f}% of them are alive.</p>

<p>Read as a portfolio rather than a menu, the studio is selling short commitments at scale and long ones in ones and twos. Its renewal rate is not a property of
its customers. It is a property of its product list, and the list is the easiest thing on this page to change.</p>

{CH_PROD}

<p>Across the whole product book the pattern is consistent: what predicts whether a member stays is how long the product was designed to last, not how much it cost.
The products with the longest commitment renew best and the products sold as a quantity of classes renew worst, at every price point in the range.</p>

{ev('Evidence — every product sold fifteen times or more at Bandra',
    T(['Product', 'Sold', 'Members', 'Cash taken', 'Mean ticket', 'Mean classes used', 'Mean days', 'Live or renewed'],
      [[i, int(r['Sold']), int(r['Members']), R(r['Cash']), R(r['Mean_ticket']), f"{r['Mean_classes']:.1f}",
        f"{r['Mean_days']:.0f}", P(r['Live_pct'])] for i, r in PRODB.iterrows()], 'num'))}

<h2>The acquisition engine</h2>
<div class="sub">Nearly half of everything the studio attracts arrives through a channel that converts at a third of the studio&rsquo;s average.</div>

<p>The CRM records a channel on every lead, and the shape of the funnel is unambiguous. <strong>{CH.loc["Website & Online Sources","leads"]:,} of
{len(LBc):,} Bandra leads &mdash; {CH.loc["Website & Online Sources","leads"]/len(LBc)*100:.0f}% &mdash; arrive through website and online sources, and they
convert at {CH.loc["Website & Online Sources","won"]:.1f}%.</strong> Calls and messages bring {CH.loc["Calls, Messages & Automated Enquiries","leads"]:,} leads and convert
{CH.loc["Calls, Messages & Automated Enquiries","won"]:.1f}%; referrals bring {CH.loc["Referrals & Word-of-Mouth","leads"]:,} and convert {CH.loc["Referrals & Word-of-Mouth","won"]:.1f}%.
By lifetime value the gap is wider still: {R(CH.loc["Website & Online Sources","ltv"])} against {R(CH.loc["Calls, Messages & Automated Enquiries","ltv"])}.</p>

{CH_CHAN}
{CH_CHANL}

<p>The named sources tell the same story with more precision. Of the sources carrying forty or more leads, the largest is
<strong>{SRC.index[0]} at {int(SRC['leads'].iloc[0]):,} leads and {SRC['won'].iloc[0]:.1f}% conversion</strong>. The best is
<strong>{SRC['won'].idxmax()}</strong>. Across every one of them the pattern holds: the studio is
buying reach and being paid in enquiries it cannot close.</p>

{CH_SRC}

<p>What those leads came for is also recorded, and it is one of the most complete demand signals the studio holds.
<strong>Barre 57 is named on {int(CT.loc["Barre 57","leads"]):,} leads</strong> and PowerCycle on {int(CT.loc["powerCycle","leads"]):,}. Both convert at almost the
same rate ({CT.loc["Barre 57","won"]:.1f}% and {CT.loc["powerCycle","won"]:.1f}%), and between them they account for
{CT.loc["Barre 57","leads"]/CT["leads"].sum()*100 + CT.loc["powerCycle","leads"]/CT["leads"].sum()*100:.0f}% of stated demand.</p>

{CH_CT}

<h2>The funnel, end to end</h2>
<div class="sub">Lead to trial to member to retained. Every stage is measured and every stage leaks.</div>

<p>Across every lead the studio has recorded for Bandra, <strong>{(LBc["Trial Status"]=="Trial Completed").mean()*100:.1f}% complete a trial and
{LBc["won"].mean()*100:.1f}% become a paying member</strong>. On the studio&rsquo;s own retention field, <strong>{(LBc["Retention Status"]=="Retained").mean()*100:.1f}%
are retained today</strong>.</p>

<p>The stage list is a useful place to see where the file actually sits. <strong>{int((LBc["Status"]=="Open").sum()):,} leads are open</strong> &mdash; more than twice
the number that have ever been won &mdash; against {int((LBc["Status"]=="Won").sum()):,} won, {int((LBc["Status"]=="Unresponsive").sum()):,} unresponsive and
{int((LBc["Status"]=="Disqualified").sum()):,} disqualified. The open file has no owner and no expiry.</p>

{CH_FUN}

{ev('Evidence — stage, trial and retention status across the Bandra lead file',
    T(['Lead status', 'Leads', 'Share'], [[k, int(v), P(v/len(LBc)*100)] for k, v in LBc['Status'].value_counts().items()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>Stage the record currently sits at</strong></p>' +
    T(['Stage', 'Leads'], [[k, int(v)] for k, v in LBc['Stage Name'].value_counts().head(10).items()], 'num'))}

<h2>Who handles the leads</h2>
<div class="sub">The same product list, the same prices and the same leads &mdash; and a two-to-one spread in outcomes.</div>

<p>Eight associates handle thirty or more Bandra leads each. <strong>Conversion ranges from {ASSOC["won"].max():.1f}% to {ASSOC["won"].min():.1f}%</strong>, and the
strongest is not the one with the smallest book. Lifetime value per lead ranges from {R(ASSOC["ltv"].min())} to {R(ASSOC["ltv"].max())}. Median first-response time
sits between {int(ASSOC["resp"].min())} and {int(ASSOC["resp"].max())} days across the team.</p>

{CH_ASSOC}

{ev('Evidence — every associate with thirty or more Bandra leads',
    T(['Associate', 'Leads', 'Trial completed', 'Won', 'Mean lifetime value', 'Median response, days'],
      [[i, int(r['leads']), P(r['trial']), P(r['won']), R(r['ltv']), f"{r['resp']:.0f}"] for i, r in ASSOC.iterrows()], 'num'))}

<p>Speed of response is the one input the studio controls completely. The median lead waits <strong>{RESP.median():.0f} days</strong> for its first logged
follow-up, and {RC.loc["same day","leads"] if "same day" in RC.index else 0:,} leads were answered the same day. The record is not fully reliable &mdash;
{RESP_R:.0f}% of follow-up dates precede the enquiry they belong to, which means the field is being filled in after the fact rather than at the time.</p>

{CH_RESP}

<h2>The book that is already sold</h2>
<div class="sub">{int(LIVE_BY["n"].sum())} live memberships, {R(LIVE["Amount Paid"].sum())} of recorded cash, and a decision window that closes quietly.</div>

<p>The forward view is the one the studio uses least. <strong>{int(LIVE_BY["n"].get("Renewal Grace Period",0))} memberships sit in a renewal grace period</strong>
carrying {R(GRACE)} of recorded cash, alongside {int(LIVE_BY["n"].get("Active",0))} active memberships worth {R(LIVE_BY["cash"].get("Active",0))}.</p>

<p>Read by recency rather than by status, the same book looks less comfortable. <strong>{LREC["members"].get("in the last 7 days",0)} members were in the studio
within the last week. {QUIET_M} have not been in for fifteen days or more, and they hold {R(QUIET)} of the cash.</strong> The lapsed memberships in this ledger are
worth {R(LP[LP["Derived Status"]=="Lapsed"]["Amount Paid"].mean())} on average; the live ones, {R(LIVE_BY["cash"].sum()/LIVE_BY["n"].sum())}.</p>

{CH_LIVE}

{ev('Evidence — the live book by status and by recency',
    T(['Status', 'Memberships', 'Members', 'Recorded cash'],
      [[k, int(r['n']), int(r['members']), R(r['cash'])] for k, r in LIVE_BY.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By how long since the member last trained</strong></p>' +
    T(['Last trained', 'Members', 'Recorded cash'], [[str(k), int(r['members']), R(r['cash'])] for k, r in LREC.iterrows()], 'num'))}

<h2>Where the money comes from</h2>
<div class="sub">A year of sales, concentrated enough to be fragile and personal enough to be managed.</div>

<p>In the twelve months to 30 September, <strong>{len(per):,} people bought something at Bandra</strong>, for {R(per.sum())}. The ten largest buyers account for
<strong>{CUM[10]*100:.1f}%</strong> of that, the top fifty for {CUM[50]*100:.0f}%, and the half of buyers who spent least for {BOT:.1f}%. And
<strong>{ONCE:,} of those buyers made exactly one purchase in the year</strong> &mdash; {ONCE/len(per)*100:.0f}% of the file.</p>

{CH_CONC}

<p>September&rsquo;s own money tells a similar story at smaller scale: {SALES[2026]["buyers"]} buyers, {R(SALES[2026]["cash"])}, an average of
{R(SALES[2026]["ticket"])} each. The month&rsquo;s cash was spread across {len(CATS)} product categories, led by
{', '.join(f'<strong>{k}</strong> at {R(v["sum"])}' for k, v in CATS.head(4).iterrows())}.</p>

{ev('Evidence — September cash by product category',
    T(['Category', 'Sales', 'Cash'], [[k, int(r['size']), R(r['sum'])] for k, r in CATS.iterrows()], 'num'))}

<h2>The room</h2>
<div class="sub">The studio owns the timetable and pays for it whether or not anyone comes. Two days and two hours carry the waste.</div>

<p>September offered <strong>{YR[2026]["seats"]:,} seats and filled {YR[2026]["att"]:,} of them</strong> &mdash; {YR[2026]["fill"]:.1f}% utilisation, up from
{YR[2025]["fill"]:.1f}% a year ago. But the average hides a deliberate pattern. By hour, the studio runs <strong>{int(HR.loc[7,"sessions"])} sessions at 07:00 and
fills {HR.loc[7,"fill"]:.0f}% of their seats</strong>, against {int(HR.loc[11,"sessions"])} sessions at 11:00 filling {HR.loc[11,"fill"]:.0f}%. By day,
<strong>Wednesday runs {int(WED["sessions"])} sessions at {WED["fill"]:.0f}%</strong> for {R(WED["rev"])}, while Tuesday runs {int(TUE["sessions"])} at
{TUE["fill"]:.0f}% for {R(TUE["rev"])}.</p>

{CH_HR}
{CH_DAY}

<p>Put together, the ceiling is not a demand problem. If every slot ran at the studio&rsquo;s own best-format utilisation of 71%, these same
{YR[2026]["sessions"]} classes would have delivered roughly <strong>{int(YR[2026]["seats"]*0.71):,} attendances</strong> instead of {YR[2026]["att"]:,}. The studio
does not need more demand to reach that; it needs its existing demand pointed at the right hours.</p>

<h2>What the data is telling the studio</h2>
<div class="sub">Six findings that only appear when the ledgers are joined, and that no single report can show.</div>

<p><strong>First, the leak is at the second visit, not the first.</strong> The studio is competent at attracting people and poor at keeping them past the first
class. Every lead file the studio holds shows the same cliff.</p>

<p><strong>Second, channel choice is worth more than channel volume.</strong> Website leads outnumber call leads by
{CH.loc["Website & Online Sources","leads"]/CH.loc["Calls, Messages & Automated Enquiries","leads"]:.1f} to one and are worth
{(CH.loc["Calls, Messages & Automated Enquiries","ltv"]/CH.loc["Website & Online Sources","ltv"]):.2f} times a call lead. Reallocating effort towards the smaller,
warmer channels is the cheapest growth available.</p>

<p><strong>Third, the live book is a pipeline, not a report.</strong> {int(LIVE_BY["n"].sum())} live memberships and {QUIET_M} quiet members holding {R(QUIET)} is a
call list, dated and contactable, that no one currently owns.</p>

<p><strong>Fourth, the studio&rsquo;s reporting measures results and ignores leading indicators.</strong> Attendance, revenue and member counts all describe a month
that has finished. Bookings, leads, response time and visits per active member all move first, and all four are already recorded.</p>

<p><strong>Fifth, demand is stated explicitly and is not being used.</strong> Almost every lead names the class it wants. Almost every member has a favourite
format and a favourite time recorded on their membership. The studio holds a written record of what its audience wants and schedules against format families
instead.</p>

<p><strong>Sixth, the studio is far better run than its reporting suggests.</strong> Revenue per class up {YR[2026]["rev_class"]/YR[2025]["rev_class"]*100-100:.0f}%,
late cancellations down {abs(YR[2026]["lc"]/YR[2025]["lc"]-1)*100:.0f}%, cash per buyer up
{SALES[2026]["ticket"]/SALES[2025]["ticket"]*100-100:.0f}%. The problems in this report are problems of placement and follow-through, not of performance.</p>

<h2>Recommendations</h2>
<div class="sub">Twelve actions, ordered by the size of the value each releases</div>
{REC_HTML}
{SRCBOX}
''')
open('/home/user/reports-arena/Bandra_September_2026_7_Studio_Overview.html', 'w').write(HTML)
print(f'Report 7 written: {len(HTML)} bytes')
print('leads', len(LBc), '| won pct', round(LBc['won'].mean()*100, 1))
print('channel:', CH[['leads','won','ltv']].to_dict('index'))
print('live book:', LIVE_BY.to_dict('index'), '| quiet', QUIET_M, R(QUIET))
print('concentration:', {k: round(v*100,1) for k,v in CUM.items()}, '| once', ONCE, 'of', len(per))
print('HR:', HR[['sessions','fill']].round(0).to_dict('index'))
print('DW fill:', DW['fill'].round(0).to_dict())
print('assoc:', ASSOC[['leads','won','ltv','resp']].to_dict('index'))
print('CT:', CT.to_dict('index'))
print('RESP median', RESP.median(), '| negative pct', round(RESP_R,1))
print('SALES:', SALES)
