import pandas as pd, numpy as np
pd.set_option('display.width', 290); pd.set_option('display.max_columns', 70)

L = pd.read_csv('/home/user/uploads/❖ PM - Leads ❖ - ◉ Leads (31).csv', low_memory=False)
L['created'] = pd.to_datetime(L['Created At'], errors='coerce')
L['conv_at'] = pd.to_datetime(L['Converted To Customer At'], errors='coerce')
L['ltv_n'] = pd.to_numeric(L['LTV'], errors='coerce')
L['visits_n'] = pd.to_numeric(L['Visits'], errors='coerce')
L['purch_n'] = pd.to_numeric(L['Purchases Made'], errors='coerce')

print('LEADS total:', len(L), '| created range:', L['created'].min(), '->', L['created'].max())
print()
print('=' * 118)
print('A. BANDRA LEADS — volume and outcome by SOURCE')
print('=' * 118)
B = L[L['Center'] == 'Supreme HQ, Bandra'].copy()
print(f'Bandra leads: {len(B)}  ({len(B)/len(L)*100:.0f}% of network)')
print()
B['won'] = B['Status'].eq('Won')
B['trialed'] = B['Trial Status'].eq('Trial Completed')
src = B.groupby('Source Name').agg(leads=('ID', 'size'), won=('won', 'sum'),
                                   trialed=('trialed', 'sum'), ltv=('ltv_n', 'sum'))
src['win_%'] = (src['won'] / src['leads'] * 100).round(1)
src['trial_%'] = (src['trialed'] / src['leads'] * 100).round(1)
src['ltv_per_lead'] = (src['ltv'] / src['leads']).round(0)
src = src.sort_values('leads', ascending=False)
print(src.head(22).to_string())
print()
print('=' * 118)
print('B. BANDRA LEADS BY CHANNEL (rolled up)')
print('=' * 118)
ch = B.groupby('Channel').agg(leads=('ID', 'size'), won=('won', 'sum'), trialed=('trialed', 'sum'),
                              ltv=('ltv_n', 'sum'), visits=('visits_n', 'sum'))
ch['win_%'] = (ch['won'] / ch['leads'] * 100).round(1)
ch['trial_%'] = (ch['trialed'] / ch['leads'] * 100).round(1)
ch['ltv_per_lead'] = (ch['ltv'] / ch['leads']).round(0)
ch['ltv_per_win'] = (ch['ltv'] / ch['won'].replace(0, np.nan)).round(0)
print(ch.sort_values('leads', ascending=False).to_string())

print()
print('=' * 118)
print('C. WHY LEADS FAIL — the drop-off reasons, Bandra')
print('=' * 118)
print(B['Stage Name'].value_counts().head(24).to_string())
print()
lost = B[B['Status'].isin(['Lost', 'Unresponsive', 'Disqualified'])]
print(f'Bandra leads that did not convert: {len(lost)} of {len(B)} ({len(lost)/len(B)*100:.0f}%)')
print()
print('--- Named reasons (non-converting leads) ---')
reasons = lost['Stage Name'].value_counts().head(16)
print(reasons.to_string())
print()
base = len(lost)
named = {'Proximity/too far': ['Proximity'], 'Unresponsive/no contact': ['Unresponsive', 'No Response', 'Did Not Answer', 'did not answer'],
         'Pricing objection': ['Pricing'], 'Timing/postponed': ['later date', 'out of town', 'traveling'], 'Other/not interested': ['Other']}
tot = 0
for k, keys in named.items():
    m = lost['Stage Name'].str.contains('|'.join(keys), case=False, na=False)
    print(f'   {k:30s} {m.sum():5d}  ({m.sum()/base*100:5.1f}%)')
    tot += m.sum()
print(f'   {"UNCLASSIFIED":30s} {base-tot:5d}  ({(base-tot)/base*100:5.1f}%)')

print()
print('=' * 118)
print('D. LEAD FLOW — market demand signal. Leads created per month, Bandra')
print('=' * 118)
B['ym'] = B['created'].dt.to_period('M')
flow = B.groupby('ym').agg(leads=('ID', 'size'), won=('won', 'sum'))
flow['win_%'] = (flow['won'] / flow['leads'] * 100).round(1)
print(flow.loc['2025-01':'2026-10'].to_string())

print()
print('=' * 118)
print('E. THE ATTRIBUTION GAP — can leads data recover the 28.7% unattributed?')
print('=' * 118)
M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')
sep = M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]
print(f'Sept-26 Bandra cohort: {len(sep)} | source recorded: {sep["Source"].notna().sum()} | blank: {sep["Source"].isna().sum()}')
lead_ids = set(pd.to_numeric(B['Member ID'], errors='coerce').dropna().astype('int64'))
sep_matched = sep[sep['Member Id'].isin(lead_ids)]
print(f'Of the 143, matched to a Bandra lead record: {len(sep_matched)}')
unattr = sep[sep['Source'].isna()]
unattr_matched = unattr[unattr['Member Id'].isin(lead_ids)]
print(f'Of the {len(unattr)} unattributed, recoverable from leads data: {len(unattr_matched)}')
if len(unattr_matched):
    lm = B[B['Member ID'].astype(str).isin(unattr_matched['Member Id'].astype(str))]
    print('   their lead sources:', lm['Source Name'].value_counts().head(10).to_dict())

print()
print('=' * 118)
print('F. SEPT-2026 BANDRA LEADS specifically — the month under review')
print('=' * 118)
s26 = B[(B['created'] >= '2026-09-01') & (B['created'] < '2026-10-01')]
print(f'Leads created in Sept 2026 for Bandra: {len(s26)}')
print('Status:', s26['Status'].value_counts().to_dict())
print()
print('Source mix of September leads vs the prior 11 months:')
prev = B[(B['created'] >= '2025-10-01') & (B['created'] < '2026-09-01')]
a = s26['Source Name'].value_counts(normalize=True).mul(100).round(1)
b_ = prev['Source Name'].value_counts(normalize=True).mul(100).round(1)
cmp_ = pd.DataFrame({'Sep-26 %': a, 'prior 11mo %': b_}).fillna(0)
print(cmp_.sort_values('Sep-26 %', ascending=False).head(14).to_string())
print()
print('Trial outcome of September leads vs prior:')
for lbl, d in [('Sep-26', s26), ('prior 11mo', prev)]:
    print(f'  {lbl}: trialed={d["Trial Status"].eq("Trial Completed").sum()} of {len(d)} '
          f'({d["Trial Status"].eq("Trial Completed").mean()*100:.1f}%) | won={d["Status"].eq("Won").sum()} ({d["Status"].eq("Won").mean()*100:.1f}%)')
