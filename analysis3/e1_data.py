"""Data layer for the four new reports: lapse/churn ledger, leads, and shared helpers."""
import pandas as pd, numpy as np
import d1_data as D

U = '/home/user/uploads/'
B = 'Supreme HQ, Bandra'

def dparse(s):
    s = s.astype(str).str.strip().replace({'nan': None, 'NaT': None, '': None})
    out = pd.Series(pd.NaT, index=s.index, dtype='datetime64[ns]')
    iso = s.str.match(r'^\d{4}-\d{2}-\d{2}', na=False)
    out[iso] = pd.to_datetime(s[iso].str.replace(',', '', regex=False), errors='coerce')
    sl = (~iso) & s.notna()
    out[sl] = pd.to_datetime(s[sl], errors='coerce', dayfirst=True)
    return out

def num(s):
    return pd.to_numeric(pd.Series(s).astype(str).str.replace(r'[,\s\u20b9%]', '', regex=True), errors='coerce')

# ------------------------------------------------------------------ lapse ledger
_RAW = pd.read_csv(U + 'Lapsed New - Lapsed (20).csv', low_memory=False)
L_ALL = _RAW.copy()
for c in ['Amount Paid', 'Original Amount (Before Discount)', 'Discount Value']:
    L_ALL[c] = num(L_ALL[c])
for c in ['Sessions Used %','Total Sessions Completed','Remaining Sessions','Total Cancellations','Late Cancellations',
          'No Shows','Cancellation Rate %','Lapse Gap (Days)','Avg Days Between Visits','Visits in First Half',
          'Visits in Second Half','Attendance Decline Rate %','Visits in Last 30 Days','Days Since Last Visit',
          'Membership Duration (Days)','Revenue Per Session','Membership Freeze Count','Average Sessions Per Month',
          'No Show Rate %','Attendance Rate %','Days Active','Days Frozen','Early Cancellations']:
    L_ALL[c] = num(L_ALL[c])
for c in ['Purchase Date','Start Date','End Date','Churned Date','Most Recent Visit Date','First Visit Date']:
    L_ALL[c + '_d'] = dparse(L_ALL[c])

COMP = r'Staff|Complimentary|Open Barre|Copper \+ Cloves Credit|Referrer|Free'
L_ALL['is_comp'] = L_ALL['Membership Name'].str.contains(COMP, case=False, na=False)
L_ALL['is_paid'] = (~L_ALL['is_comp']) & (L_ALL['Amount Paid'] > 0)
L = L_ALL[L_ALL['Primary Location'] == B].copy()
LP = L[L['is_paid']].copy()                       # paid Bandra memberships
LS = L[L['is_comp']].copy()                       # comp / free entries
print(f'lapse ledger: {len(L_ALL):,} rows all locations | Bandra {len(L):,} | paid {len(LP):,} | comp {len(LS):,}')
print(f'  distinct Bandra members in ledger: {L["Member ID"].nunique():,} | paid only: {LP["Member ID"].nunique():,}')
PAID_YEAR = LP['Purchase Date_d'].dt.year.value_counts().sort_index().to_dict()
print('  paid memberships bought at Bandra by year:', {int(k): int(v) for k, v in PAID_YEAR.items()})

# ------------------------------------------------------------------ leads
LD = pd.read_csv(U + '\u2756 PM - Leads \u2756 - \u25c9 Leads (31).csv', low_memory=False)
for c in ['Created At', 'Converted To Customer At', 'Follow Up 1 Date', 'Follow Up 2 Date', 'Follow Up 3 Date', 'Follow Up 4 Date']:
    LD[c + '_d'] = pd.to_datetime(LD[c], errors='coerce')
LD['Purchases Made'] = num(LD['Purchases Made']); LD['LTV'] = num(LD['LTV']); LD['Visits'] = num(LD['Visits'])
LD['Bandra'] = LD['Center'].astype(str).str.contains('Bandra', case=False, na=False)
LD['n_followup'] = LD[['Follow Up 1 Date', 'Follow Up 2 Date', 'Follow Up 3 Date', 'Follow Up 4 Date']].notna().sum(axis=1)
LD['resp_days'] = (LD['Follow Up 1 Date_d'] - LD['Created At_d']).dt.days
LB = LD[LD['Bandra']].copy()
print(f'leads: {len(LD):,} total | Bandra {len(LB):,} | bandra won {int((LB["Status"]=="Won").sum()):,}'
      f' | bandra converted {int((LD["Bandra"] & (LD["Conversion Status"]=="Converted")).sum()):,}')
