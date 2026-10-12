"""Data layer for the four new reports: lapse/churn ledger, leads, and shared helpers."""
import pandas as pd, numpy as np
import d1_data as D

U = '/home/user/reports-arena/uploads/'
B = 'Supreme HQ, Bandra'

def dparse(s):
    s = s.astype(str).str.strip().replace({'nan': None, 'NaT': None, '': None})
    out = pd.Series(pd.NaT, index=s.index, dtype='datetime64[ns]')
    iso = s.str.match(r'^\d{4}-\d{2}-\d{2}', na=False)
    out[iso] = pd.to_datetime(s[iso].str.replace(',', '', regex=False), errors='coerce')
    sl = (~iso) & s.notna()
    out[sl] = pd.to_datetime(s[sl], errors='coerce', dayfirst=True)
    return out

import re as _re
_SERIAL = _re.compile(r'^(1[89]\d\d|190\d)-(\d\d)-(\d\d), (\d\d):(\d\d):(\d\d)$')

def num(s):
    """Numeric parse that also recovers Sheets serial-date cells (a value of
    1417.5 stored as "1903-11-17, 12:00:00"), as the atlas normaliser does."""
    st = pd.Series(s).astype(str).str.strip()
    serial = st.str.match(_SERIAL, na=False)
    out = pd.to_numeric(st.str.replace(r'[,\s₹%]', '', regex=True).replace({'nan': None, '-': ''}), errors='coerce')
    if serial.any():
        ts = pd.to_datetime(st[serial].str.replace(',', '', regex=False), errors='coerce')
        out = out.copy()
        out.loc[serial] = ((ts - pd.Timestamp('1899-12-30')).dt.total_seconds() / 86400).round(2)
    return out

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
LD = pd.read_csv(U + '❖ PM - Leads ❖ - ◉ Leads (31).csv', low_memory=False)
for c in ['Created At', 'Converted To Customer At', 'Follow Up 1 Date', 'Follow Up 2 Date', 'Follow Up 3 Date', 'Follow Up 4 Date']:
    LD[c + '_d'] = pd.to_datetime(LD[c], errors='coerce')
LD['Purchases Made'] = num(LD['Purchases Made']); LD['LTV'] = num(LD['LTV']); LD['Visits'] = num(LD['Visits'])
LD['Bandra'] = LD['Center'].astype(str).str.contains('Bandra', case=False, na=False)
LD['n_followup'] = LD[['Follow Up 1 Date', 'Follow Up 2 Date', 'Follow Up 3 Date', 'Follow Up 4 Date']].notna().sum(axis=1)
# A follow-up dated before the enquiry is a recording error: excluded from
# response-time measures rather than read as an instant reply (atlas rule).
LD['resp_days'] = (LD['Follow Up 1 Date_d'] - LD['Created At_d']).dt.days
LD.loc[LD['resp_days'] < 0, 'resp_days'] = np.nan
LB = LD[LD['Bandra']].copy()
print(f'leads: {len(LD):,} total | Bandra {len(LB):,} | bandra won {int((LB["Status"]=="Won").sum()):,}'
      f' | bandra converted {int((LD["Bandra"] & (LD["Conversion Status"]=="Converted")).sum()):,}')
