"""Single data layer for the three companion reports.
Sources (all Supreme HQ, Bandra):
  S  Sales - Raw - Sales (23)                 cash received
  X  Day End Report - Part 3 - Sessions (19)  class occurrences
  R  Day End Report - Part 3 - Teacher Recurring (7)  recurring-slot aggregates
  P  Day End Report - Part 1 - Payroll (4)    teacher scorecard (to Aug-2026)
  M  Day End Report - Part 1 - New (9)        member cohorts (client outcomes by teacher)
"""
import re
import pandas as pd, numpy as np

BANDRA = 'Supreme HQ, Bandra'
U = '/home/user/reports-arena/uploads/'

# Numbers in these exports can arrive as Sheets serial dates ("1903-11-17,
# 12:00:00" = 1417.5 days after 1899-12-30). Recover them the same way the
# atlas normaliser does, instead of dropping them as NaN.
_SERIAL = re.compile(r'^(1[89]\d\d|190\d)-(\d\d)-(\d\d), (\d\d):(\d\d):(\d\d)$')

def _num(sr):
    st = sr.astype(str).str.strip()
    serial = st.str.match(_SERIAL, na=False)
    out = pd.to_numeric(st.str.replace(r'[₹,\s]', '', regex=True).replace({'nan': None, '-': ''}), errors='coerce')
    if serial.any():
        ts = pd.to_datetime(st[serial].str.replace(',', '', regex=False), errors='coerce')
        out = out.copy()
        out.loc[serial] = ((ts - pd.Timestamp('1899-12-30')).dt.total_seconds() / 86400).round(2)
    return out

def _is_new(v):
    t = str(v).strip()
    if not t or t.lower() in ('nan', '-', 'none'): return None
    if re.match(r'^not\b', t, re.I): return False
    if re.search(r'\bnew\b', t, re.I): return True
    if re.match(r'^(existing|returning|repeat|staff|family)', t, re.I): return False
    return None

S = pd.read_csv(U+'Sales - Raw - Sales (23).csv', low_memory=False)
# Cash belongs to payment dates; collected cash counts successful, non-voided
# payments only. Net of VAT is payment value minus payment VAT on the same
# lines. Discounts are the item-level figure (unit discount x quantity),
# because sale-level discount values repeat on every item row.
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = _num(S['Payment Value'])
S['vat'] = _num(S['Payment VAT']).fillna(0)
S['net'] = S['val'] - S['vat']
S['disc'] = (_num(S['Sale Item Unit Discount Value']) * _num(S['Sale Item Quantity'])).fillna(0)
S['gross'] = S['val'] + S['disc']
S['ok'] = S['Payment Status'].astype(str).str.strip().str.lower().eq('succeeded') & \
          ~S['Sec. Is Voided'].astype(str).str.strip().str.lower().eq('true')
S = S[S['ok']].copy()
SB = S[S['Calculated Location'] == BANDRA].copy()

X = pd.read_csv(U+'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
X['hr'] = pd.to_datetime(X['Time'], format='%H:%M:%S', errors='coerce').dt.hour
for c in ['Capacity', 'CheckedIn', 'LateCancelled', 'Booked', 'NonPaid', 'Complimentary',
          'Memberships', 'Packages', 'IntroOffers', 'SingleClasses', 'Revenue']:
    X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0)
XB = X[X['Location'] == BANDRA].copy()
XB['fill'] = np.where(XB['Capacity'] > 0, XB['CheckedIn']/XB['Capacity']*100, np.nan)

R = pd.read_csv(U+'Day End Report - Part 3 - Teacher Recurring (7).csv', low_memory=False)
R['dt'] = pd.to_datetime(R['Date'], errors='coerce')
RB = R[R['Location'] == BANDRA].copy()

P = pd.read_csv(U+'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
P['dt'] = pd.to_datetime(P['Month Year'], format='%b-%Y', errors='coerce')
P.loc[P['dt'].isna(), 'dt'] = pd.to_datetime(P['Month Year'][P['dt'].isna()], format='%B-%Y', errors='coerce')
PB = P[P['Location'] == BANDRA].copy()
PB['paid'] = _num(PB['Total Paid'])
PB['conv'] = _num(PB['Conversion Rate'].astype(str).str.replace('%', '', regex=True))
PB['ret'] = _num(PB['Retention Rate'].astype(str).str.replace('%', '', regex=True))

M = pd.read_csv(U+'Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')
# Explicit newcomer flag: the file also carries imports and existing-member
# first-visit rows, which must not dilute acquisition measures (atlas rule).
M['is_new'] = M['Is New'].map(_is_new)
MB = M[(M['First Visit Location'] == BANDRA) & (M['is_new'] == True)].copy()
MB['conv'] = MB['Conversion Status'].astype(str).str.strip().eq('Converted')
MB['ltv_n'] = _num(MB['Ltv'])
MB['v'] = _num(MB['No of Visits'])
MB['fpv'] = _num(MB['First Purchase Value']) if 'First Purchase Value' in MB.columns else np.nan
MB['visits_post'] = _num(MB['Visits Post Trial']) if 'Visits Post Trial' in MB.columns else np.nan

# ---------------------------------------------------------------- windows
def win(df, col, y, m):
    a = pd.Timestamp(f'{y}-{m:02d}-01')
    b = a + pd.offsets.MonthBegin(1)
    return df[(df[col] >= a) & (df[col] < b)].copy()

s24, s25, s26 = win(SB, 'dt', 2024, 9), win(SB, 'dt', 2025, 9), win(SB, 'dt', 2026, 9)
x24, x25, x26 = win(XB, 'dt', 2024, 9), win(XB, 'dt', 2025, 9), win(XB, 'dt', 2026, 9)

# ------------------------------------------------------------------ SALES
DN = {}
DN['s_cash'] = {y: d['val'].sum() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
# Transactions are distinct sales, not item rows.
DN['s_txn'] = {y: d['Sale ID'].nunique() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_lines'] = {y: len(d) for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_mem'] = {y: d['Member ID'].nunique() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_avg'] = {y: (DN['s_cash'][y]/max(DN['s_txn'][y], 1)) for y in DN['s_cash']}
DN['s_per_buyer'] = {y: (DN['s_cash'][y]/max(DN['s_mem'][y], 1)) for y in DN['s_cash']}
DN['s_med'] = {y: d['val'].median() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_disc'] = {y: d['disc'].sum() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_vat'] = {y: d['vat'].sum() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
DN['s_net'] = {y: d['net'].sum() for y, d in [(2024, s24), (2025, s25), (2026, s26)]}
# Discount rate: discount as a share of discount plus collected revenue.
DN['s_depth'] = {y: (DN['s_disc'][y]/(DN['s_cash'][y]+DN['s_disc'][y])*100
                     if (DN['s_cash'][y]+DN['s_disc'][y]) else 0) for y in DN['s_cash']}

CAT_ORDER = ['Memberships', 'Class Packages', 'Sessions/Single Classes', 'Newcomers Special',
             'Retail', 'Privates', 'Money Credits']
cat26 = s26.groupby('Cleaned Category').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
cat25 = s25.groupby('Cleaned Category').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
cat24 = s24.groupby('Cleaned Category').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
CATS = pd.concat([cat24.add_suffix('_24'), cat25.add_suffix('_25'), cat26.add_suffix('_26')], axis=1).fillna(0)
CATS = CATS.reindex([c for c in CAT_ORDER if c in CATS.index])

prod26 = s26.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
prod25 = s25.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
PRODS = prod26.join(prod25, lsuffix='_26', rsuffix='_25', how='outer').fillna(0)
PRODS['d'] = PRODS['rev_26'] - PRODS['rev_25']
PRODS['avg_26'] = PRODS['rev_26']/PRODS['n_26'].replace(0, np.nan)
PRODS = PRODS.sort_values('rev_26', ascending=False)
# top movers only (material)
MOVERS = PRODS[(PRODS['rev_26'].abs() >= 10000) | (PRODS['rev_25'].abs() >= 10000)].copy()
MOVERS = MOVERS.reindex(MOVERS['d'].abs().sort_values(ascending=False).index)

NCLS = {'Studio Single Class': 1, 'Studio Newcomers 2 For 1': 2, 'Studio 4 Class Package': 4,
        'Studio 8 Class Package': 8, 'Studio 10 Class Package': 10, 'Studio 12 Class Package': 12,
        'Studio 20 Single Class Package': 20, 'Studio 10 Single Class Package': 10}
PPC = []
for p, n in NCLS.items():
    d = s26[s26['Cleaned Product'] == p]
    if len(d): PPC.append((p, len(d), d['val'].mean(), d['val'].mean()/n))
PPC = pd.DataFrame(PPC, columns=['product', 'n', 'avg_price', 'per_class']).sort_values('per_class')

sold26 = s26.groupby('Sold By').agg(n=('Sale ID', 'size'), rev=('val', 'sum')).sort_values('rev', ascending=False)
sold25 = s25.groupby('Sold By').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
SOLD = sold26.join(sold25, lsuffix='_26', rsuffix='_25', how='outer').fillna(0)
SOLD['avg_26'] = SOLD['rev_26']/SOLD['n_26'].replace(0, np.nan)
# year-to-date for each seller, Sep-26 vs Jan-Sep-26
sold_ytd = win(SB[(SB['dt'] >= '2026-01-01') & (SB['dt'] < '2026-10-01')], 'dt', 2026, 9)
sold_ytd = SB[(SB['dt'] >= '2026-01-01') & (SB['dt'] < '2026-10-01')].groupby('Sold By').agg(
    n=('Sale ID', 'size'), rev=('val', 'sum'))

first = SB.groupby('Member ID')['dt'].min().dt.to_period('M')
s26f = s26.assign(firstp=s26['Member ID'].map(first))
NEWREV = s26f[s26f['firstp'] == '2026-09']['val'].sum()
EXREV = s26f[s26f['firstp'] != '2026-09']['val'].sum()

BINS = [0, 2000, 5000, 10000, 20000, 50000, 10**9]
LABS = ['under ₹2k', '₹2–5k', '₹5–10k', '₹10–20k', '₹20–50k', '₹50k+']
s26b = s26.assign(band=pd.cut(s26['val'], bins=BINS, labels=LABS))
BANDS = s26b.groupby('band', observed=True).agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
BANDS['pct'] = BANDS['rev']/BANDS['rev'].sum()*100

MONTHS = SB[(SB['dt'] >= '2025-01-01') & (SB['dt'] < '2026-10-01')]
CATTR = MONTHS.groupby([MONTHS['dt'].dt.to_period('M'), 'Cleaned Category'])['val'].sum().unstack(fill_value=0)
CATTR = CATTR.reindex(columns=[c for c in CAT_ORDER if c in CATTR.columns]).fillna(0)

RET26 = s26[s26['Cleaned Category'] == 'Retail']
PMETH26 = s26.groupby('Payment Method').agg(n=('Sale ID', 'size'), rev=('val', 'sum')).sort_values('rev', ascending=False)
PTYPE26 = s26.groupby('Purchase Type').agg(n=('Sale ID', 'size'), rev=('val', 'sum')).sort_values('rev', ascending=False)

# ------------------------------------------------------------------ CLASSES
CL = {}
for y, d in [(2024, x24), (2025, x25), (2026, x26)]:
    CL[y] = dict(sessions=len(d), seats=int(d['Capacity'].sum()), att=int(d['CheckedIn'].sum()),
                 empty=int((d['CheckedIn'] == 0).sum()), rev=d['Revenue'].sum(),
                 lc=int(d['LateCancelled'].sum()), booked=int(d['Booked'].sum()))
    CL[y]['fill'] = CL[y]['att']/CL[y]['seats']*100
    CL[y]['rev_class'] = CL[y]['rev']/CL[y]['sessions']
    CL[y]['rev_head'] = CL[y]['rev']/max(CL[y]['att'], 1)

FMT = x26.groupby('Class').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                               att=('CheckedIn', 'sum'), lc=('LateCancelled', 'sum'),
                               booked=('Booked', 'sum'), rev=('Revenue', 'sum'),
                               nonpaid=('NonPaid', 'sum'), comp=('Complimentary', 'sum'))
FMT['fill'] = FMT['att']/FMT['seats']*100
FMT['avg_size'] = FMT['att']/FMT['sessions']
FMT['rev_class'] = FMT['rev']/FMT['sessions']
FMT['rev_head'] = FMT['rev']/FMT['att'].replace(0, np.nan)
FMT['empty'] = x26.groupby('Class')['CheckedIn'].apply(lambda s: int((s == 0).sum()))
# Late-cancel rate is late cancellations over the booked book (a released
# seat was itself a booking; it must not be added to the denominator again).
FMT['lc_rate'] = FMT['lc']/FMT['booked'].replace(0, np.nan)*100
FMT['show'] = FMT['att']/FMT['booked'].replace(0, np.nan)*100
FMT = FMT.sort_values('rev', ascending=False)
_a25 = x25.groupby('Class').agg(s25=('SessionID', 'size'), cap25=('Capacity', 'sum'),
                                a25=('CheckedIn', 'sum'), r25=('Revenue', 'sum'))
FMT_YOY = FMT[['sessions', 'seats', 'att', 'fill', 'rev', 'rev_class']].join(_a25, how='outer')
FMT_YOY['fill25'] = np.where(FMT_YOY['s25'].fillna(0) > 0,
                             FMT_YOY['a25']/FMT_YOY['cap25'].replace(0, np.nan)*100, np.nan)
FMT_YOY['d_fill'] = FMT_YOY['fill'] - FMT_YOY['fill25']
FMT_YOY['d_att'] = FMT_YOY['att'] - FMT_YOY['a25']

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DOW = x26.groupby('Day').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                             att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
DOW['fill'] = DOW['att']/DOW['seats']*100
DOW['rev_class'] = DOW['rev']/DOW['sessions']
DOW = DOW.reindex(DAYS)
DOW25 = x25.groupby('Day').agg(att=('CheckedIn', 'sum'), seats=('Capacity', 'sum'))
DOW['fill25'] = x25.groupby('Day').apply(lambda d: d['CheckedIn'].sum()/d['Capacity'].sum()*100).reindex(DAYS)

HOUR = x26.groupby('hr').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                             att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
HOUR['fill'] = HOUR['att']/HOUR['seats']*100

def band(h):
    if pd.isna(h): return 'Unknown'
    if h < 9: return 'Early (to 08:59)'
    if h < 12: return 'Late morning (09:00–11:59)'
    if h < 16: return 'Midday (12:00–15:59)'
    if h < 18: return 'Afternoon (16:00–17:59)'
    if h < 21: return 'Evening (18:00–20:59)'
    return 'Late (21:00+)'
x26b = x26.assign(band=x26['hr'].apply(band))
BAND = x26b.groupby('band').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                                att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
BAND['fill'] = BAND['att']/BAND['seats']*100
BAND['rev_class'] = BAND['rev']/BAND['sessions']
BAND = BAND.sort_values('fill', ascending=False)

PAYMIX = x26.groupby('Class').agg(mem=('Memberships', 'sum'), pkg=('Packages', 'sum'),
                                  intro=('IntroOffers', 'sum'), single=('SingleClasses', 'sum'))
PAYMIX['total'] = PAYMIX.sum(axis=1)
for c in ['mem', 'pkg', 'intro', 'single']:
    PAYMIX[c+'_p'] = PAYMIX[c]/PAYMIX['total'].replace(0, np.nan)*100
PAYMIX = PAYMIX[PAYMIX['total'] > 0].sort_values('total', ascending=False)

EMPTY = x26[x26['CheckedIn'] == 0].copy().sort_values('Date')
NEAR = x26[(x26['CheckedIn'] > 0) & (x26['CheckedIn'] <= 2)].copy()
LEAN = pd.concat([EMPTY.assign(kind='empty'), NEAR.assign(kind='1–2 only')])
LEAN_BY = LEAN.groupby(['Class', 'kind']).size().unstack(fill_value=0)
ALLFMT = x26.groupby('Class').size().rename('all')
LEAN_BY = LEAN_BY.join(ALLFMT)
LEAN_BY['share'] = (LEAN_BY.sum(axis=1)-LEAN_BY.get('all', 0))/LEAN_BY['all']*100 if 'all' in LEAN_BY else np.nan
LEAN_BY['lean'] = LEAN_BY.get('empty', 0)+LEAN_BY.get('1–2 only', 0)
LEAN_BY['lean_%'] = LEAN_BY['lean']/LEAN_BY['all']*100
LEAN_BY = LEAN_BY.sort_values('lean', ascending=False)

FULLEST = x26[x26['Capacity'] >= 8].nlargest(10, 'fill')[['Date', 'Day', 'Time', 'Class', 'Trainer', 'Capacity', 'CheckedIn', 'Booked', 'Revenue']]
EMPTest = x26[x26['Capacity'] >= 8].nsmallest(10, 'fill')[['Date', 'Day', 'Time', 'Class', 'Trainer', 'Capacity', 'CheckedIn', 'Booked', 'LateCancelled', 'Revenue']]

WK = {}
for lab, d in [('2025', x25), ('2026', x26)]:
    dd = d.assign(wk=((d['dt'].dt.day-1)//7)+1)
    w = dd.groupby('wk').agg(sessions=('SessionID', 'size'), att=('CheckedIn', 'sum'),
                             seats=('Capacity', 'sum'), rev=('Revenue', 'sum'))
    w['fill'] = w['att']/w['seats']*100
    WK[lab] = w

HOSTED = x26[x26['SessionName'].str.contains('X |x |Hosted|Sweat|Pickle|Peakst8|KRC|Fest|Ladies', case=False, na=False)]

# ------------------------------------------------------------------ TEACHERS
TCH = x26.groupby('Trainer').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                                 att=('CheckedIn', 'sum'), booked=('Booked', 'sum'),
                                 lc=('LateCancelled', 'sum'), rev=('Revenue', 'sum'),
                                 formats=('Class', 'nunique'), slots=('Time', 'nunique'))
TCH['fill'] = TCH['att']/TCH['seats']*100
TCH['avg_class'] = TCH['att']/TCH['sessions']
TCH['rev_class'] = TCH['rev']/TCH['sessions']
TCH['rev_head'] = TCH['rev']/TCH['att'].replace(0, np.nan)
TCH['lc_rate'] = TCH['lc']/TCH['booked'].replace(0, np.nan)*100
TCH['show'] = TCH['att']/TCH['booked'].replace(0, np.nan)*100
TCH['share_sessions'] = TCH['sessions']/len(x26)*100
TCH['share_att'] = TCH['att']/int(x26['CheckedIn'].sum())*100
t25 = x25.groupby('Trainer').agg(s25=('SessionID', 'size'), a25=('CheckedIn', 'sum'), r25=('Revenue', 'sum'))
TCH = TCH.join(t25, how='outer').fillna(0)
TCH['d_sessions'] = TCH['sessions']-TCH['s25']
TCH['d_att'] = TCH['att']-TCH['a25']
TCH = TCH.sort_values('rev', ascending=False)

TF = x26.groupby(['Trainer', 'Class']).agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                                           att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
TF['fill'] = TF['att']/TF['seats']*100

TSLOT = x26.groupby(['Trainer', 'Day', 'Time']).agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'),
                                                    att=('CheckedIn', 'sum'), rev=('Revenue', 'sum')).reset_index()
TSLOT['fill'] = TSLOT['att']/TSLOT['seats'].replace(0, np.nan)*100
TSLOT['rev_class'] = TSLOT['rev']/TSLOT['sessions']

# client outcomes by first-class teacher (cohort file)
CLI = MB[MB['Trainer Name'].notna()].groupby('Trainer Name').agg(
    clients=('Member Id', 'size'), conv=('conv', 'sum'), ltv=('ltv_n', 'mean'), visits=('v', 'mean'))
CLI['conv_%'] = CLI['conv']/CLI['clients']*100
CLI_SEP = MB[MB['cohort'] == '2026-09-01'].groupby('Trainer Name').agg(
    clients=('Member Id', 'size'), conv=('conv', 'sum'), visits=('v', 'mean')).sort_values('clients', ascending=False)
CLI_SEP['conv_%'] = CLI_SEP['conv']/CLI_SEP['clients']*100

# recurring slots
ACT = RB[RB['dt'] >= '2026-10-01'].copy()
ACT['_cap_per'] = ACT['Capacity']/ACT['Classes'].replace(0, np.nan)
ACT['_fill'] = ACT['CheckedIn']/ACT['Capacity'].replace(0, np.nan)*100
ACT_SLOTS = ACT.groupby('Trainer').agg(slots=('SessionID', 'size'), classes=('Classes', 'sum'),
                                       seats=('Capacity', 'sum'), att=('CheckedIn', 'sum'),
                                       rev=('Revenue', 'sum')).sort_values('slots', ascending=False)
ACT_SLOTS['fill'] = ACT_SLOTS['att']/ACT_SLOTS['seats']*100

# payroll (through Aug-2026)
PAY = PB[PB['dt'] == '2026-08-01'].copy().sort_values('Total Paid', ascending=False)
PAY_HIST = PB.groupby('Teacher Name').agg(months=('dt', 'nunique'), sessions=('Total Sessions', 'sum'),
                                          paid=('paid', 'sum'), conv=('conv', 'mean'), ret=('ret', 'mean'),
                                          new=('New', 'sum'), convd=('Converted', 'sum'), retd=('Retained', 'sum'))
PAY_HIST['conv_calc'] = PAY_HIST['convd']/PAY_HIST['new'].replace(0, np.nan)*100
PAY_TREND = PB.groupby('dt').agg(teachers=('Teacher Name', 'nunique'), sessions=('Total Sessions', 'sum'),
                                 paid=('paid', 'sum'), new=('New', 'sum'), convd=('Converted', 'sum'),
                                 retd=('Retained', 'sum'))
PAY_TREND['conv_calc'] = PAY_TREND['convd']/PAY_TREND['new'].replace(0, np.nan)*100

if __name__ == '__main__':
    print('s26 cash', DN['s_cash'], '\nclass', CL, '\ntop trainers\n', TCH.head(6).to_string())
    print('\nPRODS\n', PRODS.head(8).to_string())
    print('\nACT_SLOTS\n', ACT_SLOTS.to_string())
    print('\nPAY\n', PAY[['Teacher Name','Total Sessions','Total Customers','paid','Converted','conv','Retained','ret','New']].to_string())
