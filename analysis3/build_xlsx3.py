"""Companion workbook for the seven Bandra September-2026 reports."""
import pandas as pd, numpy as np, sys
sys.path.insert(0, '/home/user/reports-arena/analysis3')
import e1_data as E
import d1_data as D
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

TODAY = pd.Timestamp('2026-10-18')
OUT = '/home/user/reports-arena/Bandra_September_2026_Reports_4-9_Data.xlsx'
SHEETS = []

def add(name, df, note=''):
    SHEETS.append((name[:31], df, note))

# ---------------------------------------------------------------- shared loads
X = D.XB.copy(); X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
def septx(y, m=9):
    s = X[(X['dt'] >= f'{y}-{m:02d}-01') & (X['dt'] < (pd.Timestamp(f'{y}-{m:02d}-01') + pd.offsets.MonthBegin(1)))]
    return s
x24, x25, x26 = septx(2024), septx(2025), septx(2026)

CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID', 'Location', 'Date (IST)', 'Checked In', 'Is Late Cancelled', 'Cleaned Class',
             'Teacher Name', 'Complementary', 'Paid', 'Class No'])
CK = CK[CK['Location'] == E.B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
CK['cn'] = E.num(CK['Class No'])
A = CK[CK['Checked In'] == True].copy()
a24 = A[(A['dt'] >= '2024-09-01') & (A['dt'] < '2024-10-01')]
a25 = A[(A['dt'] >= '2025-09-01') & (A['dt'] < '2025-10-01')]
a26 = A[(A['dt'] >= '2026-09-01') & (A['dt'] < '2026-10-01')]
v26 = a26.groupby('Member ID').size(); v25 = a25.groupby('Member ID').size()
S25, S26, S24 = set(a25['Member ID']), set(a26['Member ID']), set(a24['Member ID'])

SB = D.SB.copy()
SB['disc'] = SB['disc']  # item-level, from d1_data
SB['gross'] = SB['val'] + SB['disc']; SB['has_disc'] = SB['disc'] > 0; SB['yr'] = SB['dt'].dt.year
R12 = SB[SB['dt'] >= '2025-10-01']; R26 = SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')]

N9 = pd.read_csv(E.U + 'Day End Report - Part 1 - New (9).csv', low_memory=False)
N9 = N9[N9['First Visit Location'] == E.B].copy()
N9['fvd'] = pd.to_datetime(N9['First Visit Date'], errors='coerce', dayfirst=False)
for c in ['Ltv', 'No of Visits', 'Days To Second Visit', 'Visits Per Month']:
    N9[c] = E.num(N9[c])
INTAKE = N9[(N9['fvd'] >= '2025-09-01') & (N9['fvd'] < '2026-09-01') &
            N9['Is New'].astype(str).str.startswith('New')].copy()
INTAKE['conv'] = INTAKE['Conversion Status'] == 'Converted'
SRC_MAP = {'Website': 'Website', 'Hosted Class': 'Hosted class', 'Client Referral': 'Client referral',
           'Yellow Messenger/Whatsapp Enquiry': 'WhatsApp enquiry', 'Social - Instagram': 'Instagram',
           'Website Form': 'Website form', 'Incoming call': 'Incoming call', 'Enquiry on call': 'Enquiry on call',
           'Walkin': 'Walk-in', 'Abandoned checkout': 'Abandoned checkout', 'Staff Referral': 'Staff referral'}
INTAKE['src'] = INTAKE['Source'].map(SRC_MAP).fillna(INTAKE['Source'])

# ================================================================ 1 three Septembers
rows = []
for y, s in ((2024, x24), (2025, x25), (2026, x26)):
    rows.append(dict(September=y, Classes=len(s), Seats=int(s['Capacity'].sum()), Attended=int(s['CheckedIn'].sum()),
                     Fill_pct=round(s['CheckedIn'].sum() / s['Capacity'].sum() * 100, 1),
                     Booked=int(s['Booked'].sum()), Board_booked_pct=round(s['Booked'].sum() / s['Capacity'].sum() * 100, 1),
                     Late_cancellations=int(s['LateCancelled'].sum()),
                     Complimentary=int(s['Complimentary'].sum()),
                     Revenue=round(s['Revenue'].sum()),
                     Revenue_per_class=round(s['Revenue'].sum() / len(s)),
                     Revenue_per_head=round(s['Revenue'].sum() / s['CheckedIn'].sum()),
                     Unique_members=A[(A['dt'] >= f'{y}-09-01') & (A['dt'] < f'{y}-10-01')]['Member ID'].nunique()))
    rows[-1]['Visits_per_member'] = round(
        A[(A['dt'] >= f'{y}-09-01') & (A['dt'] < f'{y}-10-01')].groupby('Member ID').size().mean(), 2)
add('01 Three Septembers', pd.DataFrame(rows), 'Class ledger, Sessions file, filtered to Supreme HQ Bandra.')

# ================================================================ 2 format matrix
def fmtmat(s):
    g = s.groupby('Class').agg(Classes=('SessionID', 'size'), Seats=('Capacity', 'sum'), Attended=('CheckedIn', 'sum'),
        Booked=('Booked', 'sum'), Late_cancellations=('LateCancelled', 'sum'), Complimentary=('Complimentary', 'sum'),
        Revenue=('Revenue', 'sum'), Intro_offers=('IntroOffers', 'sum'), Memberships=('Memberships', 'sum'),
        Packages=('Packages', 'sum'), Single_classes=('SingleClasses', 'sum'))
    g['Fill_pct'] = (g['Attended'] / g['Seats'] * 100).round(1)
    g['Attended_per_class'] = (g['Attended'] / g['Classes']).round(2)
    g['Revenue_per_class'] = (g['Revenue'] / g['Classes']).round(0)
    g['Revenue_per_head'] = (g['Revenue'] / g['Attended'].replace(0, np.nan)).round(0)
    g['Cancel_rate_pct'] = (g['Late_cancellations'] / g['Booked'].replace(0, np.nan) * 100).round(1)
    g['Comp_share_pct'] = (g['Complimentary'] / g['Attended'].replace(0, np.nan) * 100).round(1)
    return g.sort_values('Attended', ascending=False).reset_index()
add('02 Format matrix Sep-26', fmtmat(x26), 'Sessions file, September 2026.')
add('03 Format matrix Sep-25', fmtmat(x25), 'Sessions file, September 2025.')

# ================================================================ 3 members per format
MB = []
for cls, s in a26.groupby('Cleaned Class'):
    vc = s.groupby('Member ID').size()
    MB.append(dict(Format=cls.replace('Studio ', ''), Members=len(vc), Attendances=len(s),
                   Visits_per_member=round(len(s) / max(len(vc), 1), 2), Came_4_plus_pct=round((vc >= 4).mean() * 100, 1),
                   Came_once_pct=round((vc == 1).mean() * 100, 1), Regulars=int((vc >= 4).sum())))
add('04 Members per format Sep-26', pd.DataFrame(MB).sort_values('Members', ascending=False), 'Check-in ledger, attended entries.')

# ================================================================ 4 the member core
CORE = pd.DataFrame([
    dict(Group='Trained in both Septembers', Members=len(S26 & S25), Visits_this_September=float(v26.reindex(list(S26 & S25)).sum()),
         Mean_visits=round(v26.reindex(list(S26 & S25)).mean(), 2), Median_visits=float(v26.reindex(list(S26 & S25)).median()),
         Visits_September_2025=float(v25.reindex(list(S26 & S25)).sum()), Mean_visits_2025=round(v25.reindex(list(S26 & S25)).mean(), 2)),
    dict(Group='Here in Sept 2025, not this year', Members=len(S25 - S26), Visits_this_September=np.nan, Mean_visits=np.nan,
         Median_visits=np.nan, Visits_September_2025=float(v25.reindex(list(S25 - S26)).sum()),
         Mean_visits_2025=round(v25.reindex(list(S25 - S26)).mean(), 2)),
    dict(Group='New this September', Members=len(S26 - S25), Visits_this_September=float(v26.reindex(list(S26 - S25)).sum()),
         Mean_visits=round(v26.reindex(list(S26 - S25)).mean(), 2), Median_visits=float(v26.reindex(list(S26 - S25)).median()),
         Visits_September_2025=np.nan, Mean_visits_2025=np.nan)])
add('05 Core vs new members', CORE, 'Matched member by member between September 2025 and September 2026.')

FREQ = pd.DataFrame({'Visits in September': list(range(1, 10)) + ['10 to 12', '13 or more'],
                     'Members': [int((v26 == k).sum()) for k in range(1, 10)] +
                                [int(((v26 >= 10) & (v26 <= 12)).sum()), int((v26 >= 13).sum())]})
FREQ['Share_pct'] = (FREQ['Members'] / v26.sum() * 100).round(1)
FREQ['Attendances'] = [int((v26[v26 == k]).sum()) for k in range(1, 10)] + \
                      [int(v26[(v26 >= 10) & (v26 <= 12)].sum()), int(v26[v26 >= 13].sum())]
add('06 Member frequency Sep-26', FREQ, f'{len(v26)} members trained at least once in September 2026.')

rows = []
for m in v26.reindex(list(S26 & S25)).nlargest(20).index:
    rows.append(dict(Member=m, Visits_September_2026=int(v26.get(m, 0)), Visits_September_2025=int(v25.get(m, 0)),
                     Change=int(v26.get(m, 0) - v25.get(m, 0))))
add('07 The returning core, top 20', pd.DataFrame(rows), 'The 78 members who trained in both Septembers, ranked by visits this year.')

# ================================================================ 5 booking book and rooms
BK = pd.DataFrame([dict(September=y, Seats=int(s['Capacity'].sum()), Booked=int(s['Booked'].sum()),
                        Board_booked_pct=round(s['Booked'].sum() / s['Capacity'].sum() * 100, 1),
                        Attended=int(s['CheckedIn'].sum()), Attended_of_booked_pct=round(s['CheckedIn'].sum() / max(s['Booked'].sum(), 1) * 100, 1),
                        Late_cancellations=int(s['LateCancelled'].sum()),
                        Revenue_per_booked_seat=round(s['Revenue'].sum() / max(s['Booked'].sum(), 1)))
                   for y, s in ((2024, x24), (2025, x25), (2026, x26))])
add('08 Booking book', BK, 'Booked seats against seats on the board, and what was honoured.')

_x = x26.copy(); _x['capr'] = _x['Capacity'] / _x['Classes'].clip(lower=1)
_x['band'] = pd.cut(_x['capr'], [0, 11, 13, 40], labels=['10 to 11 seats', '12 to 13 seats', '14 or more seats'])
RB = _x.groupby('band', observed=True).agg(Classes=('SessionID', 'size'), Seats=('capr', 'mean'),
                                           Attended=('CheckedIn', 'mean'), Revenue=('Revenue', 'mean')).reset_index()
RB['Fill_pct'] = (RB['Attended'] / RB['Seats'] * 100).round(1)
RB['Revenue_per_class'] = RB['Revenue'].round(0)
add('09 Room size Sep-26', RB, 'Sessions grouped by the number of seats the room holds.')

CC = x26.groupby('Class').agg(Attended=('CheckedIn', 'sum'), Complimentary=('Complimentary', 'sum')).reset_index()
CC['Comp_share_pct'] = (CC['Complimentary'] / CC['Attended'].replace(0, np.nan) * 100).round(1)
add('10 Complimentary seats', CC.sort_values('Comp_share_pct', ascending=False), 'September 2026, by format.')

# ================================================================ 6 acquisition
SR = INTAKE.groupby('src').agg(First_visits=('Member Id', 'size'), Conversion_pct=('conv', lambda x: round(x.mean() * 100, 1)),
                               Median_days_to_2nd_visit=('Days To Second Visit', 'median'), Mean_lifetime_value=('Ltv', 'mean'),
                               Mean_visits=('No of Visits', 'mean'), Mean_visits_per_month=('Visits Per Month', 'mean'))
SR['Mean_lifetime_value'] = SR['Mean_lifetime_value'].round(0)
add('11 Acquisition sources', SR[SR['First_visits'] >= 20].sort_values('First_visits', ascending=False).reset_index(),
    'First visits September 2025 to August 2026, by the source the studio recorded.')

FP = N9[N9['First Purchase Post Trial'].notna()].groupby('First Purchase Post Trial').agg(
    People=('Member Id', 'size'), Mean_lifetime_value=('Ltv', 'mean'), Mean_visits=('No of Visits', 'mean'),
    Mean_visits_per_month=('Visits Per Month', 'mean'))
FP = FP[FP['People'] >= 25].sort_values('Mean_lifetime_value', ascending=False)
FP['Mean_lifetime_value'] = FP['Mean_lifetime_value'].round(0)
FP['Mean_visits'] = FP['Mean_visits'].round(1)
FP['Mean_visits_per_month'] = FP['Mean_visits_per_month'].round(1)
add('12 First purchase to LTV', FP.reset_index(), 'Every Bandra first-timer with a recorded first purchase.')

N9['d2'] = pd.cut(N9['Days To Second Visit'], [-1, 1, 3, 7, 14, 30, 100000],
                  labels=['Same or next day', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31+ or never'])
SP = N9.groupby('d2', observed=True).agg(People=('Member Id', 'size'), Mean_lifetime_value=('Ltv', 'mean'),
                                         Mean_visits=('No of Visits', 'mean')).reset_index()
SP['Mean_lifetime_value'] = SP['Mean_lifetime_value'].round(0); SP['Mean_visits'] = SP['Mean_visits'].round(1)
add('13 Speed to second visit', SP, 'The strongest single predictor of lifetime value in the member file.')

recent = A[A['dt'] >= '2025-01-01']
base = recent['Member ID'].nunique()
FUN = pd.DataFrame({'Stage': ['Attended once', 'Reached a 2nd class', 'Reached a 3rd class', 'Reached a 5th',
                              'Reached a 10th', 'Reached a 21st'],
                    'Members': [base] + [recent[recent['cn'] >= k]['Member ID'].nunique() for k in (2, 3, 5, 10, 21)]})
FUN['Share_of_intake_pct'] = (FUN['Members'] / base * 100).round(1)
FUN['Step_conversion_pct'] = (FUN['Members'] / FUN['Members'].shift(1) * 100).round(1)
add('14 Visit funnel', FUN, 'Every member who has trained at Bandra since January 2025.')

# ================================================================ 7 concentration, payment, timing
per = R12.groupby('Member ID')['val'].sum().sort_values(ascending=False)
CONC = pd.DataFrame({'Band': ['the top 10 buyers', 'buyers 11 to 25', 'buyers 26 to 50', 'buyers 51 to 100',
                              'buyers 101 to 500', f'all {len(per)-500} others'],
                     'Share_of_sales_pct': [round(per.head(10).sum() / per.sum() * 100, 1),
                                            round((per.head(25).sum() - per.head(10).sum()) / per.sum() * 100, 1),
                                            round((per.head(50).sum() - per.head(25).sum()) / per.sum() * 100, 1),
                                            round((per.head(100).sum() - per.head(50).sum()) / per.sum() * 100, 1),
                                            round((per.head(500).sum() - per.head(100).sum()) / per.sum() * 100, 1),
                                            round((per.sum() - per.head(500).sum()) / per.sum() * 100, 1)]})
add('15 Buyer concentration', CONC, f'{len(per):,} people bought something in the twelve months to 30 September 2026.')

PM = R26.groupby('Payment Method')['val'].agg(['size', 'sum']).reset_index()
PM.columns = ['Payment Method', 'Sales', 'Value']
PM['Value'] = PM['Value'].round(0); PM['Average_transaction'] = (PM['Value'] / PM['Sales']).round(0)
PM['Share_pct'] = (PM['Value'] / PM['Value'].sum() * 100).round(1)
add('16 Payment method Sep-26', PM.sort_values('Value', ascending=False), 'Raw sales export, September 2026.')

# ================================================================ 8 cancellations
LC = CK[CK['Is Late Cancelled'] == True]
rows = []
for y in (2024, 2025, 2026):
    s = CK[(CK['Is Late Cancelled'] == True) & (CK['dt'] >= f'{y}-01-01') & (CK['dt'] < f'{y+1}-01-01')]
    a = CK[(CK['Checked In'] == True) & (CK['dt'] >= f'{y}-01-01') & (CK['dt'] < f'{y+1}-01-01')]
    rows.append(dict(Year=y, Late_cancellations=len(s), Attendances=len(a),
                     Per_100_attendances=round(len(s) / max(len(a), 1) * 100, 1)))
add('17 Late cancellations by year', pd.DataFrame(rows), 'Check-in ledger, Bandra.')

lc26 = CK[(CK['Is Late Cancelled'] == True) & (CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')]
LCM = lc26.groupby('Member ID').size().sort_values(ascending=False)
top10 = LCM.nlargest(10).sum() / LCM.sum() * 100
CONC2 = pd.DataFrame({'Measure': ['Members who cancelled', 'Total cancellations', 'Median per member',
                                  'Members with 3 or more', 'Top 10 members share of cancellations'],
                      'Value': [len(LCM), int(LCM.sum()), float(LCM.median()), int((LCM >= 3).sum()), round(top10, 1)]})
add('18 Cancellation concentration', CONC2, 'September 2026.')

LCF = lc26.groupby('Cleaned Class').size().sort_values(ascending=False)
ATT = a26.groupby('Cleaned Class').size()
LCFMT = pd.DataFrame({'Format': [k.replace('Studio ', '') for k in LCF.index],
                      'Late_cancellations': LCF.values,
                      'Attendance': [int(ATT.get(k, 0)) for k in LCF.index],
                      'Per_100_attended': [round(LCF[k] / max(ATT.get(k, 1), 1) * 100, 1) for k in LCF.index]})
add('19 Cancellations by format', LCFMT, 'September 2026.')

_lch = CK[(CK['Is Late Cancelled'] == True) & (CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')].copy()
_lch['Weekday'] = _lch['dt'].dt.day_name()
LCH = _lch.groupby('Weekday').size().reset_index(name='Late_cancellations').rename(columns={'Weekday': 'Day of week'})
LCH['Day of week'] = pd.Categorical(LCH['Day of week'],
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], ordered=True)
LCH = LCH.sort_values('Day of week')
add('20 Cancellations by day', LCH, 'September 2026.')

# ================================================================ 9 discounts
DG = SB.groupby('yr').agg(Sales=('Sale ID', 'nunique'), Gross=('gross', 'sum'), Discount=('disc', 'sum'),
                          Discounted_sales=('has_disc', 'sum')).reset_index()
DG.columns = ['Year', 'Sales', 'Gross', 'Discount', 'Discounted_sales']
DG['Depth_pct'] = (DG['Discount'] / DG['Gross'] * 100).round(2)
DG['Spread_pct'] = (DG['Discounted_sales'] / DG['Sales'] * 100).round(1)
DG['Gross'] = DG['Gross'].round(0); DG['Discount'] = DG['Discount'].round(0)
add('21 Discount by year', DG, 'Raw sales export, all months on file.')

D26 = SB[SB['yr'] == 2026]
DP = D26.groupby('Cleaned Product').agg(Sales=('Sale ID', 'nunique'), Gross=('gross', 'sum'), Discount=('disc', 'sum'),
                                        Discounted_sales=('has_disc', 'sum')).reset_index()
DP['Depth_pct'] = (DP['Discount'] / DP['Gross'] * 100).round(1)
DP['Spread_pct'] = (DP['Discounted_sales'] / DP['Sales'] * 100).round(1)
DP['Gross'] = DP['Gross'].round(0); DP['Discount'] = DP['Discount'].round(0)
add('22 Discount by product', DP[DP['Sales'] >= 15].sort_values('Depth_pct', ascending=False),
    'Sales with fifteen or more transactions in 2026.')

DS = D26.groupby('Sold By').agg(Sales=('Sale ID', 'nunique'), Gross=('gross', 'sum'), Discount=('disc', 'sum'),
                                Discounted_sales=('has_disc', 'sum')).reset_index()
DS['Depth_pct'] = (DS['Discount'] / DS['Gross'] * 100).round(1)
DS['Spread_pct'] = (DS['Discounted_sales'] / DS['Sales'] * 100).round(1)
DS['Gross'] = DS['Gross'].round(0); DS['Discount'] = DS['Discount'].round(0)
add('23 Discount by seller', DS[DS['Sales'] >= 20].sort_values('Depth_pct', ascending=False),
    'Sellers with twenty or more recorded sales in 2026.')

later = SB.groupby('Member ID').agg(n=('Sale ID', 'nunique'), v=('val', 'sum'))
def eff(frame):
    f = frame.sort_values('dt').groupby('Member ID').agg(fd=('dt', 'min'), fdisc=('has_disc', 'first')).join(later)
    f['obs'] = (TODAY - f['fd']).dt.days
    f = f[f['obs'] >= 180]
    return f.groupby('fdisc').agg(Buyers=('n', 'size'), Repeat_pct=('n', lambda x: round((x > 1).mean() * 100, 1)),
                                  Mean_transactions=('n', 'mean'), Lifetime_value=('v', 'mean'))
EFF = []
e = eff(SB).reset_index()
for _, r in e.iterrows():
    EFF.append(dict(First_purchase='All products', Discounted='Yes' if r['fdisc'] else 'No', Buyers=int(r['Buyers']),
                    Repeat_pct=r['Repeat_pct'], Mean_transactions=round(r['Mean_transactions'], 2),
                    Lifetime_value=round(r['Lifetime_value'])))
for k in ['Studio Newcomers 2 For 1', 'Studio 12 Class Package', 'Studio 1 Month Unlimited', 'Studio 4 Class Package']:
    try:
        e = eff(SB[SB['Cleaned Product'] == k]).reset_index()
        for _, r in e.iterrows():
            EFF.append(dict(First_purchase=k.replace('Studio ', ''), Discounted='Yes' if r['fdisc'] else 'No',
                            Buyers=int(r['Buyers']), Repeat_pct=r['Repeat_pct'],
                            Mean_transactions=round(r['Mean_transactions'], 2), Lifetime_value=round(r['Lifetime_value'])))
    except Exception:
        pass
add('24 Discount effectiveness', pd.DataFrame(EFF),
    'Pooled, then controlled for the product bought first. Buyers whose first purchase is at least 180 days old.')

# ================================================================ 10 the membership book
L, LP = E.L, E.LP
d = LP[LP['Purchase Date_d'].notna() & (LP['Purchase Date_d'] >= '2024-01-01')].copy()
T = TODAY
d['ended'] = d[['Churned Date_d', 'End Date_d']].min(axis=1)
d['life'] = (d['ended'] - d['Purchase Date_d']).dt.days
d['life'] = d['life'].where(d['life'] >= 0)
d['cens'] = (T - d['Purchase Date_d']).dt.days
d['obs'] = d['life'].fillna(d['cens'])
n = len(d)
SURV = pd.DataFrame({'Point': ['Day 7', 'Day 14', 'Day 30', 'Day 45', 'Day 60', 'Day 90', 'Day 120', 'Day 180', 'One year'],
                     'Still_in_force_pct': [round(((d['obs'] > k) | d['life'].isna()).sum() / n * 100, 1)
                                            for k in (7, 14, 30, 45, 60, 90, 120, 180, 365)]})
SURV['Ended_pct'] = (100 - SURV['Still_in_force_pct']).round(1)
SURV['Paid_memberships_observed'] = n
add('25 Membership survival', SURV, 'Paid Bandra memberships bought since January 2024, n = %d.' % n)

DUR = LP[LP['Membership Duration (Days)'].notna() & (LP['Membership Duration (Days)'] >= 0)].copy()
DUR['band'] = pd.cut(DUR['Membership Duration (Days)'], [-1, 1, 7, 30, 60, 90, 180, 400, 99999],
                     labels=['Same day', '2 to 7 days', '8 to 30 days', '31 to 60 days', '61 to 90 days',
                             '91 to 180 days', '181 to 365 days', 'Over a year'])
DB = DUR.groupby('band', observed=True).agg(Memberships=('Member ID', 'size'), Members=('Member ID', 'nunique'),
                                            Mean_price_paid=('Amount Paid', 'mean'),
                                            Mean_classes_completed=('Total Sessions Completed', 'mean')).reset_index()
DB['Mean_price_paid'] = DB['Mean_price_paid'].round(0); DB['Mean_classes_completed'] = DB['Mean_classes_completed'].round(1)
add('26 Membership duration bands', DB, 'How long paid Bandra memberships actually lasted.')

PR = LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ', '', regex=True).str.strip())
PRD = PR.groupby('fam').agg(Sold=('Member ID', 'size'), Members=('Member ID', 'nunique'),
                            Cash_taken=('Amount Paid', 'sum'), Mean_ticket=('Amount Paid', 'mean'),
                            Mean_classes=('Total Sessions Completed', 'mean'),
                            Mean_days=('Membership Duration (Days)', 'mean'),
                            Renewed_or_live_pct=('Derived Status', lambda x: round(x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100, 1)),
                            Lapsed_pct=('Derived Status', lambda x: round((x == 'Lapsed').mean() * 100, 1))).reset_index()
PRD['Cash_taken'] = PRD['Cash_taken'].round(0); PRD['Mean_ticket'] = PRD['Mean_ticket'].round(0)
PRD['Mean_classes'] = PRD['Mean_classes'].round(1); PRD['Mean_days'] = PRD['Mean_days'].round(0)
add('27 Product renewal', PRD[PRD['Sold'] >= 15].sort_values('Renewed_or_live_pct', ascending=False),
    'Paid Bandra memberships, products with fifteen or more sold.')

uc = LP[LP['Sessions Used %'].notna()].copy()
uc['band'] = pd.cut(uc['Sessions Used %'], [-1, 10, 25, 50, 75, 99, 100.1],
                    labels=['Used 10% or less', '11 to 25%', '26 to 50%', '51 to 75%', '76 to 99%', 'Used 100%'])
UC = uc.groupby('band', observed=True).agg(Memberships=('Member ID', 'size'),
                                           Mean_price_paid=('Amount Paid', 'mean'),
                                           Mean_classes_used=('Total Sessions Completed', 'mean'),
                                           Mean_classes_remaining=('Remaining Sessions', 'mean')).reset_index()
for c in ['Mean_price_paid', 'Mean_classes_used', 'Mean_classes_remaining']:
    UC[c] = UC[c].round(1)
add('28 Unused credit', UC, 'Package and credit products only; %d memberships, %d classes unused in total.'
    % (len(uc), int(uc['Remaining Sessions'].sum())))

rc = LP[LP['Days Since Last Visit'].notna()].copy()
rc['band'] = pd.cut(rc['Days Since Last Visit'], [-1, 30, 60, 90, 180, 365, 99999],
                    labels=['0 to 30 days', '31 to 60 days', '61 to 90 days', '91 to 180 days',
                            '181 to 365 days', 'Over a year'])
RC = rc.groupby('band', observed=True).agg(Members=('Member ID', 'nunique'), Memberships=('Member ID', 'size'),
                                           Mean_price_paid=('Amount Paid', 'mean'),
                                           Mean_classes_completed=('Total Sessions Completed', 'mean')).reset_index()
RC['Mean_price_paid'] = RC['Mean_price_paid'].round(0); RC['Mean_classes_completed'] = RC['Mean_classes_completed'].round(1)
add('29 Winnability by recency', RC, 'Paid Bandra memberships, by how long since the member last trained.')

CB = LP.copy()
CB['band'] = pd.cut(CB['Cancellation Rate %'], [-1, 0, 10, 25, 50, 1000],
                    labels=['Never cancels', 'Cancels up to 10%', '11 to 25%', '26 to 50%', 'Over 50%'])
CBT = CB.groupby('band', observed=True).agg(Memberships=('Member ID', 'size'),
                                            Mean_classes=('Total Sessions Completed', 'mean'),
                                            Mean_late_cancellations=('Late Cancellations', 'mean'),
                                            Mean_no_shows=('No Shows', 'mean'),
                                            Live_or_renewed_pct=('Derived Status', lambda x: round(x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100, 1))).reset_index()
for c in ['Mean_classes', 'Mean_late_cancellations', 'Mean_no_shows']:
    CBT[c] = CBT[c].round(1)
add('30 Cancellation bands', CBT, 'Paid Bandra memberships, by how often the member released a booked seat late.')

# ================================================================ 11 leads
LB = E.LB.copy(); LB['LTVn'] = E.num(LB['LTV']); LB['won'] = LB['Status'] == 'Won'
LS = LB.groupby('Source Name').agg(
    Leads=('ID', 'size'),
    Trial_completed_pct=('Trial Status', lambda x: round((x == 'Trial Completed').mean() * 100, 1)),
    Won_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1)),
    Converted_pct=('Conversion Status', lambda x: round((x == 'Converted').mean() * 100, 1)),
    Mean_lifetime_value=('LTVn', 'mean'),
    Mean_visits=('Visits', lambda x: round(E.num(x).mean(), 1))).reset_index()
LS['Mean_lifetime_value'] = LS['Mean_lifetime_value'].round(0)
LS['Source'] = LS['Source Name']
LS = LS[LS['Leads'] >= 20].drop(columns=['Source Name']).sort_values('Leads', ascending=False)
add('31 Lead sources', LS, 'Bandra CRM leads, all time on file.')

_c = [f'Follow Up Comments ({i})' for i in (1, 2, 3, 4)]
for _col in _c:
    LB[_col + '_clean'] = LB[_col].astype(str).str.strip().replace({'nan': '', '-': '', 'None': ''})
LB['n_comment'] = (LB[[c + '_clean' for c in _c]] != '').sum(axis=1)
FU = LB.groupby('n_comment').agg(
    Leads=('ID', 'size'),
    Won_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1)),
    Converted_pct=('Conversion Status', lambda x: round((x == 'Converted').mean() * 100, 1)),
    Mean_lifetime_value=('LTVn', 'mean')).reset_index()
FU.columns = ['Logged_contacts', 'Leads', 'Won_pct', 'Converted_pct', 'Mean_lifetime_value']
FU['Mean_lifetime_value'] = FU['Mean_lifetime_value'].round(0)
add('32 Follow-up contact', FU,
    'Bandra leads by how many of the four follow-up comment fields were actually filled in. The record shows what contact was logged, not what was attempted.')

# ================================================================ 12 trainers and teaching
TCH = x26.groupby('Trainer').agg(Sessions=('SessionID', 'size'), Attendees=('CheckedIn', 'sum'),
                                 Seats=('Capacity', 'sum'), Booked=('Booked', 'sum'),
                                 Late_cancellations=('LateCancelled', 'sum'), Revenue=('Revenue', 'sum')).reset_index()
TCH['Avg_class'] = (TCH['Attendees'] / TCH['Sessions']).round(2)
TCH['Fill_pct'] = (TCH['Attendees'] / TCH['Seats'] * 100).round(1)
TCH['Revenue_per_class'] = (TCH['Revenue'] / TCH['Sessions']).round(0)
TCH['Revenue_per_attendee'] = (TCH['Revenue'] / TCH['Attendees'].replace(0, np.nan)).round(0)
add('33 Trainer scorecard', TCH.sort_values('Revenue', ascending=False), 'Sessions file, September 2026.')

_S = D.XB[D.XB['dt'] >= '2026-01-01'].copy()
_S['slot'] = _S['Class'].astype(str) + ' | ' + _S['Day'].astype(str) + ' | ' + _S['Time'].astype(str)
rows = []
for slot, g in _S.groupby('slot'):
    if g['Trainer'].nunique() < 2:
        continue
    t = g.groupby('Trainer').agg(n=('SessionID', 'size'), att=('CheckedIn', 'mean')).query('n >= 3')
    if len(t) < 2:
        continue
    t = t.sort_values('att', ascending=False)
    rows.append(dict(Slot=slot, Trainers_compared=len(t), Best=t.index[0], Best_attendance=round(float(t['att'].iloc[0]), 1),
                     Weakest=t.index[-1], Weakest_attendance=round(float(t['att'].iloc[-1]), 1),
                     Gap=round(float(t['att'].iloc[0] - t['att'].iloc[-1]), 1),
                     Gap_pct=round(float((t['att'].iloc[0] - t['att'].iloc[-1]) / max(t['att'].iloc[-1], .01) * 100), 1)))
add('34 Matched slots', pd.DataFrame(rows).sort_values('Gap', ascending=False),
    'Slots in 2026 taught by two or more trainers, each at least three times.')

PAY = pd.read_csv(E.U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
PAY = PAY[PAY['Location'] == E.B].copy()
for c in ['Total Sessions', 'Total Empty Sessions', 'Total Customers', 'Total Paid', 'New', 'Converted', 'Retained',
          'Cycle Sessions', 'Cycle Paid', 'Strength Sessions', 'Strength Paid', 'Barre Sessions', 'Barre Paid']:
    PAY[c] = E.num(PAY[c])
PAY['mo'] = PAY['Month Year'].astype(str)
MO = PAY.groupby('mo').agg(Sessions=('Total Sessions', 'sum'), Empty_sessions=('Total Empty Sessions', 'sum'),
                           Customers=('Total Customers', 'sum'), Paid=('Total Paid', 'sum'),
                           New=('New', 'sum'), Converted=('Converted', 'sum'), Retained=('Retained', 'sum')).reset_index()
MO['Empty_pct'] = (MO['Empty_sessions'] / MO['Sessions'] * 100).round(1)
MO['Paid_per_customer'] = (MO['Paid'] / MO['Customers']).round(0)
add('35 Teaching month by month', MO, 'Part 1 Payroll, Bandra. Empty sessions are classes nobody attended.')

DSUM = PAY[['Cycle Sessions', 'Cycle Paid', 'Strength Sessions', 'Strength Paid', 'Barre Sessions', 'Barre Paid']].sum()
DSUM = pd.DataFrame([dict(Discipline='Cycle', Sessions=int(DSUM['Cycle Sessions']), Paid=round(DSUM['Cycle Paid']),
                          Paid_per_session=round(DSUM['Cycle Paid'] / max(DSUM['Cycle Sessions'], 1))),
                     dict(Discipline='Strength', Sessions=int(DSUM['Strength Sessions']), Paid=round(DSUM['Strength Paid']),
                          Paid_per_session=round(DSUM['Strength Paid'] / max(DSUM['Strength Sessions'], 1))),
                     dict(Discipline='Barre', Sessions=int(DSUM['Barre Sessions']), Paid=round(DSUM['Barre Paid']),
                          Paid_per_session=round(DSUM['Barre Paid'] / max(DSUM['Barre Sessions'], 1)))])
add('36 Teaching by discipline', DSUM, 'Payroll file, all months on file.')


# ---------------------------------------------------------------- extra round-6 views
CKm = CK[CK['Checked In'] == True].copy()
MBASE = []
for _y in (2024, 2025, 2026):
    _s = CKm[(CKm['dt'] >= f'{_y}-09-01') & (CKm['dt'] < f'{_y}-10-01')]
    _v = _s.groupby('Member ID').size()
    MBASE.append(dict(September=_y, Members=len(_v), Attendances=len(_s),
                      Visits_per_member=round(len(_s) / max(len(_v), 1), 2),
                      Came_once=int((_v == 1).sum()), Came_ten_or_more=int((_v >= 10).sum()),
                      Visits_from_top_decile=int(_v.nlargest(max(int(len(_v) * .1), 1)).sum())))
add('37 The member base', pd.DataFrame(MBASE), 'Unique members who checked in at Bandra in each September, from the Part 4 ledger.')

_mfall = CKm.groupby('Member ID')['Cleaned Class'].nunique()
_inv = E.LP.groupby('Member ID')['Amount Paid'].sum()
_mfl = pd.DataFrame({'Formats ever used': _mfall})
_mfl['Recorded spend on memberships'] = _mfl.index.map(_inv).fillna(0)
MF = _mfl.groupby('Formats ever used').agg(Members=('Recorded spend on memberships', 'size'),
        Mean_recorded_spend=('Recorded spend on memberships', 'mean')).reset_index()
MF['Mean_recorded_spend'] = MF['Mean_recorded_spend'].round(0)
add('38 Multi-format ladder', MF[MF['Members'] >= 25].head(14),
    'Bandra members, by how many different formats they have ever attended. Spend is recorded membership payments, not all sales.')

# every member's own frequency in September 2026, for the class report
_v = CKm[(CKm['dt'] >= '2026-09-01') & (CKm['dt'] < '2026-10-01')].groupby('Member ID').size()
FR = _v.value_counts().sort_index().rename_axis('Visits in September 2026').reset_index(name='Members')
FR['Share_pct'] = (FR['Members'] / FR['Members'].sum() * 100).round(1)
add('40 Member frequency 2026', FR, 'How many times each of the 394 members who trained in September 2026 came.')

CHS = LB.groupby('Channel').agg(Leads=('ID', 'size'),
        Trial_completed_pct=('Trial Status', lambda x: round((x == 'Trial Completed').mean() * 100, 1)),
        Won_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1)),
        Mean_lifetime_value=('LTVn', 'mean')).reset_index()
CHS['Channel'] = CHS['Channel'].str.replace(' ◉ Leads', '', regex=False)
CHS['Mean_lifetime_value'] = CHS['Mean_lifetime_value'].round(0)
add('39 Lead channels', CHS.sort_values('Leads', ascending=False), 'Bandra CRM leads grouped by the channel taxonomy the studio uses.')


PRODB = LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ', '', regex=True).str.strip()).groupby('fam').agg(
    Sold=('Member ID', 'size'), Members=('Member ID', 'nunique'), Cash=('Amount Paid', 'sum'),
    Mean_ticket=('Amount Paid', 'mean'), Mean_classes=('Total Sessions Completed', 'mean'),
    Mean_days=('Membership Duration (Days)', 'mean'),
    Live_or_renewed_pct=('Derived Status', lambda x: round(x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100, 1)),
    Lapsed_pct=('Derived Status', lambda x: round((x == 'Lapsed').mean() * 100, 1)))
PRODB = PRODB[PRODB['Sold'] >= 15].sort_values('Sold', ascending=False).reset_index()
for c in ['Cash', 'Mean_ticket']:
    PRODB[c] = PRODB[c].round(0)
for c in ['Mean_classes', 'Mean_days']:
    PRODB[c] = PRODB[c].round(1)
add('41 Product book', PRODB, 'Paid Bandra memberships, products with fifteen or more sold.')

ASSOC = LB.groupby('Associate').agg(Leads=('ID', 'size'),
        Trial_pct=('Trial Status', lambda x: round((x == 'Trial Completed').mean() * 100, 1)),
        Won_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1)),
        Mean_lifetime_value=('LTVn', 'mean'), Median_response_days=('resp_days', 'median'))
ASSOC = ASSOC[ASSOC['Leads'] >= 30].sort_values('Won_pct', ascending=False).reset_index()
ASSOC['Mean_lifetime_value'] = ASSOC['Mean_lifetime_value'].round(0)
add('42 Lead handling', ASSOC, 'Bandra associates with thirty or more recorded leads.')

_L26 = LB[LB['Created At_d'] >= '2026-01-01']
LM = _L26.groupby(_L26['Created At_d'].dt.to_period('M')).agg(Leads=('ID', 'size'),
        Won=('Status', lambda x: int((x == 'Won').sum())),
        Converted_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1))).reset_index()
LM['Created At_d'] = LM['Created At_d'].astype(str)
add('43 Lead flow 2026', LM, 'Bandra leads created each month of 2026 and how many had converted at snapshot.')

CHS2 = LB.groupby('Channel').agg(Leads=('ID', 'size'),
        Trial_completed_pct=('Trial Status', lambda x: round((x == 'Trial Completed').mean() * 100, 1)),
        Won_pct=('Status', lambda x: round((x == 'Won').mean() * 100, 1)),
        Mean_lifetime_value=('LTVn', 'mean')).reset_index()
CHS2['Channel'] = CHS2['Channel'].str.replace(' ◉ Leads', '', regex=False)
CHS2['Mean_lifetime_value'] = CHS2['Mean_lifetime_value'].round(0)
add('44 Lead channels', CHS2.sort_values('Leads', ascending=False), 'Bandra leads by channel taxonomy.')


# ================================================================ reports 8 and 9
_L = LB.copy(); _L['LTVn'] = E.num(_L['LTV']); _L['won'] = _L['Status'] == 'Won'
_L['span'] = (_L['Converted To Customer At_d'] - _L['Created At_d']).dt.days
add('45 Lead funnel', pd.DataFrame([
    dict(Stage='Leads created', Count=len(_L), Share_pct=100.0),
    dict(Stage='Trial completed', Count=int((_L['Trial Status'] == 'Trial Completed').sum()),
         Share_pct=round((_L['Trial Status'] == 'Trial Completed').mean() * 100, 1)),
    dict(Stage='Membership sold', Count=int(_L['won'].sum()), Share_pct=round(_L['won'].mean() * 100, 1)),
    dict(Stage='Retained today', Count=int((_L['Retention Status'] == 'Retained').sum()),
         Share_pct=round((_L['Retention Status'] == 'Retained').mean() * 100, 1))]),
    'Every Bandra lead ever recorded, by how far it got. All time on file.')

TG = _L.groupby('Trial Status').agg(Leads=('ID', 'size'), Won=('won', 'sum'),
        Won_pct=('won', lambda x: round(x.mean() * 100, 2)),
        Mean_lifetime_value=('LTVn', lambda x: round(x.mean())),
        Retained_today=('Retention Status', lambda x: int((x == 'Retained').sum()))).reset_index()
add('46 The trial gate', TG, 'Split by whether the lead ever completed a trial class.')

_w = _L[_L['won'] & _L['span'].notna() & (_L['span'] >= 0)].copy()
_wb = pd.cut(_w['span'], [-1, 0, 1, 2, 3, 7, 14, 30, 90, 100000],
             labels=['Same day', 'Next day', 'Two days', 'Three days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 to 90 days', '91 days or more'])
SPANG = _w.assign(Gap=_wb).groupby('Gap', observed=True).agg(Wins=('ID', 'size'), Mean_lifetime_value=('LTVn', 'mean')).reset_index()
SPANG['Mean_lifetime_value'] = SPANG['Mean_lifetime_value'].round(0)
SPANG['Share_pct'] = (SPANG['Wins'] / SPANG['Wins'].sum() * 100).round(1)
add('47 Enquiry to purchase', SPANG, 'Won Bandra leads with a usable date pair, by how long the decision took.')

_OP = LB[LB['Status'] == 'Open'].copy(); _OP['age'] = (pd.Timestamp('2026-10-18') - _OP['Created At_d']).dt.days
_OB = pd.cut(_OP['age'], [-1, 14, 30, 60, 180, 99999], labels=['0 to 14 days', '15 to 30 days', '31 to 60 days', '61 to 180 days', 'over 180 days'])
OPG = _OP.assign(Age=_OB).groupby('Age', observed=True).size().reset_index(name='Open_leads')
add('48 The open file', OPG, f'{len(_OP):,} open Bandra leads, mean age {_OP["age"].mean():.0f} days.')

_L26 = LB[LB['Created At_d'] >= '2026-01-01']
FL2 = _L26.groupby(_L26['Created At_d'].dt.to_period('M')).agg(
        Leads=('ID', 'size'), Trial_completed_pct=('Trial Status', lambda x: round((x == 'Trial Completed').mean() * 100, 1)),
        Won_pct=('won', lambda x: round(x.mean() * 100, 1)),
        Open_pct=('Status', lambda x: round((x == 'Open').mean() * 100, 1)),
        Mean_lifetime_value=('LTVn', 'mean')).reset_index()
FL2['Created At_d'] = FL2['Created At_d'].astype(str)
FL2['Mean_lifetime_value'] = FL2['Mean_lifetime_value'].round(0)
add('49 2026 lead cohorts', FL2, 'Bandra leads grouped by the month they arrived, so each is read like its peers.')

_CKm = CK[CK['Checked In'] == True].copy()
_V26 = _CKm[(_CKm['dt'] >= '2026-09-01') & (_CKm['dt'] < '2026-10-01')].groupby('Member ID').size()
FREQ2 = _V26.value_counts().sort_index().rename_axis('Visits in the month').reset_index(name='Members')
FREQ2['Share_pct'] = (FREQ2['Members'] / FREQ2['Members'].sum() * 100).round(1)
add('50 Member frequency', FREQ2, 'The 394 members who trained at Bandra in September 2026, by how many times each came.')

_G = CKm.sort_values('dt').groupby('Member ID')['dt'].diff().dt.days.dropna()
GB2 = ['the same day', 'one day later', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 to 90 days', 'over 90 days']
GC2 = pd.cut(_G, [-1, 0, 1, 3, 7, 14, 30, 90, 100000], labels=GB2)
add('51 Gap between visits', GC2.value_counts().reindex(GB2).rename_axis('Gap').reset_index(name='Occasions'),
    f'Every consecutive-visit gap in the Bandra ledger. Median {_G.median():.0f} day.')

_SBm = D.SB.copy(); _SBm['at'] = pd.to_datetime(_SBm['Created At'], errors='coerce')
_PG = _SBm.sort_values('at').groupby('Member ID')['at'].diff().dt.days.dropna()
PB2 = ['30 days or less', '31 to 60 days', '61 to 90 days', '91 to 180 days', '181 to 365 days', 'over a year']
add('52 Gap between purchases', pd.cut(_PG, [-1, 30, 60, 90, 180, 365, 100000], labels=PB2).value_counts().reindex(PB2)
    .rename_axis('Gap').reset_index(name='Occasions'), f'Every repeat purchase on record. Median {_PG.median():.0f} days.')

_S26 = _SBm[(_SBm['dt'] >= '2026-01-01') & (_SBm['dt'] < '2026-10-01')].copy()
_S26['hr'] = _S26['at'].dt.hour
BH = _S26.groupby('hr').agg(Sales=('val', 'size'), Value=('val', 'sum')).reset_index()
BH['Value'] = BH['Value'].round(0)
add('53 Sales by hour', BH, 'When the studio takes its money, January to September 2026.')

_S26['dom'] = _S26['at'].dt.day
BD = _S26.groupby('dom').agg(Sales=('val', 'size'), Value=('val', 'sum')).reset_index()
BD['Value'] = BD['Value'].round(0)
add('54 Sales by day of month', BD, 'Where the month’s selling sits, January to September 2026.')

_intake = _CKm[_CKm['dt'] < '2025-09-01'].groupby('Member ID')['dt'].min()
_COH = _intake[_intake >= '2024-09-01'].index
_MX = _CKm[_CKm['Member ID'].isin(_COH)].groupby('Member ID').size()
STEPS2 = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30]
AT2 = pd.DataFrame({'Visits reached': STEPS2, 'Members': [int((_MX >= k).sum()) for k in STEPS2]})
AT2['Share_of_cohort_pct'] = (AT2['Members'] / len(_COH) * 100).round(1)
AT2['Step_retention_pct'] = (AT2['Members'] / AT2['Members'].shift(1) * 100).round(1)
add('55 Visit number curve', AT2, f'Every Bandra member whose first visit was in the year to August 2025, n = {len(_COH):,}.')

_MO = _CKm[_CKm['dt'] >= '2025-01-01'].copy(); _MO['mo'] = _MO['dt'].dt.to_period('M')
MOG = _MO.groupby('mo').agg(Members=('Member ID', 'nunique'), Visits=('Member ID', 'size')).reset_index()
MOG['Visits_per_member'] = (MOG['Visits'] / MOG['Members']).round(2)
MOG['mo'] = MOG['mo'].astype(str)
add('56 Frequency by month', MOG, 'Visits per active member, every month since January 2025.')

# rebuild the README to cover every sheet
README = pd.DataFrame({'Sheet': [s[0] for s in SHEETS], 'What it contains': [s[2] if s[2] else '' for s in SHEETS]})
README = pd.concat([pd.DataFrame({'Sheet': ['README'], 'What it contains': [
    'Companion data for the Supreme HQ Bandra September 2026 reports 4 to 9. Every table behind every chart, ready to sort, '
    'filter and reconcile. Sources: the Day End Part 4 check-in ledger, the Sessions, Payroll and New-member exports, the raw '
    'sales export, the membership lapse ledger and the CRM lead master. Snapshot 18 October 2026. Revenue is gross value as '
    'recorded, not contribution margin.']}), README], ignore_index=True)

# ================================================================ write
with pd.ExcelWriter(OUT, engine='openpyxl') as xl:
    README.to_excel(xl, sheet_name='README', index=False)
    for name, df, _ in SHEETS:
        df.to_excel(xl, sheet_name=name, index=False)

    wb = xl.book
    head_fill = PatternFill('solid', fgColor='0F4C5C')
    head_font = Font(color='FFFFFF', bold=True, size=10.5)
    thin = Side(style='thin', color='E7E5E2')
    for ws in wb.worksheets:
        ws.freeze_panes = 'A2'
        for cell in ws[1]:
            cell.fill = head_fill; cell.font = head_font
            cell.alignment = Alignment(horizontal='left', vertical='center')
        ws.row_dimensions[1].height = 22
        for col in ws.columns:
            letter = get_column_letter(col[0].column)
            width = max((len(str(c.value)) for c in col[:400] if c.value is not None), default=10)
            ws.column_dimensions[letter].width = min(max(width + 3, 11), 52)
        ws.sheet_view.showGridLines = False

print(f'Workbook written: {OUT}')
import os
print(f'  {os.path.getsize(OUT):,} bytes | {len(SHEETS)} data sheets + README')
for n, df, _ in SHEETS:
    print(f'  {n:<32} {len(df):>5} rows x {len(df.columns)} cols')
