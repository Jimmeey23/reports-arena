import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 70)

C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
Bs = C[C['Location'] == 'Supreme HQ, Bandra'].copy()
Bs['ym'] = Bs['dt'].dt.to_period('M')

S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = pd.to_numeric(S['Payment Value'].astype(str).str.replace(r'[,\s]', '', regex=True), errors='coerce')
SB = S[S['Calculated Location'] == 'Supreme HQ, Bandra'].copy()

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')

print('=' * 118)
print('A. TEACHING ROSTER — when did teachers leave / arrive? (classes taught per month at Bandra)')
print('=' * 118)
piv = Bs.groupby(['ym', 'Teacher Name']).size().unstack(fill_value=0)
piv = piv.loc['2025-06':'2026-10']
cols = piv.sum().sort_values(ascending=False).head(16).index
print(piv[cols].to_string())

print()
print('=' * 118)
print('B. THE DEPARTED — what did the teachers who left actually contribute?')
print('=' * 118)
sep25 = Bs[(Bs['dt'] >= '2025-09-01') & (Bs['dt'] < '2025-10-01')]
sep26 = Bs[(Bs['dt'] >= '2026-09-01') & (Bs['dt'] < '2026-10-01')]
a = sep25.groupby('Teacher Name').agg(sep25_bookings=('Member ID', 'size'), sep25_att=('checked', 'sum'))
b_ = sep26.groupby('Teacher Name').agg(sep26_bookings=('Member ID', 'size'), sep26_att=('checked', 'sum'))
j = a.join(b_, how='outer').fillna(0)
j['change'] = j['sep26_bookings'] - j['sep25_bookings']
j['pct'] = (j['change'] / j['sep25_bookings'].replace(0, np.nan) * 100).round(0)
# attach lifetime LTV-per-client as first-class teacher
lt = M[M['First Visit Location'] == 'Supreme HQ, Bandra']
lt['ltv_n'] = pd.to_numeric(lt['Ltv'].astype(str).str.replace(r'[^0-9]', '', regex=True), errors='coerce')
tt = lt[lt['Trainer Name'].notna()].groupby('Trainer Name').agg(clients=('Member Id', 'size'), ltv_per=('ltv_n', 'mean')).round(0)
j = j.join(tt, how='left')
print(j.sort_values('sep25_bookings', ascending=False).head(20).to_string())

print()
print('=' * 118)
print('C. COHORT CASH — validating the member file against the actual ledger')
print('=' * 118)
for lbl, start, end, coh in [('Sept 2025 cohort', '2025-09-01', '2025-10-01', pd.Timestamp('2025-09-01')),
                             ('Sept 2026 cohort', '2026-09-01', '2026-10-01', pd.Timestamp('2026-09-01'))]:
    ids = set(M[(M['cohort'] == coh) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]['Member Id'])
    cash = SB[SB['Member ID'].isin(ids)]
    mfile = M[(M['cohort'] == coh) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]
    mfile_ltv = pd.to_numeric(mfile['Ltv'].astype(str).str.replace(r'[^0-9]', '', regex=True), errors='coerce').sum()
    print(f'  {lbl} (n={len(ids)}):')
    print(f'    member-file lifetime value        : Rs {mfile_ltv:>12,.0f}')
    print(f'    actual cash recorded in ledger    : Rs {cash["val"].sum():>12,.0f}  ({len(cash)} transactions)')
    print(f'    avg per client (ledger)           : Rs {cash["val"].sum()/max(len(ids),1):>12,.0f}')
    print()

print('=' * 118)
print('D. BASE REVENUE DEPENDENCE — who actually pays for the studio')
print('=' * 118)
for lbl, d, cutoff in [('Sept 2025', S[(S['dt'] >= '2025-09-01') & (S['dt'] < '2025-10-01') & (S['Calculated Location'] == 'Supreme HQ, Bandra')], pd.Timestamp('2025-09-01')),
                       ('Sept 2026', SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')], pd.Timestamp('2026-09-01'))]:
    thismo = set(M[M['cohort'] == cutoff]['Member Id'])
    newc = d[d['Member ID'].isin(thismo)]
    print(f'  {lbl}: total Rs {d["val"].sum():>11,.0f} | new clients that month Rs {newc["val"].sum():>10,.0f} ({newc["val"].sum()/d["val"].sum()*100:4.1f}%)'
          f' | pre-existing base Rs {d["val"].sum()-newc["val"].sum():>11,.0f} ({(d["val"].sum()-newc["val"].sum())/d["val"].sum()*100:4.1f}%)')

print()
print('=' * 118)
print('E. 2-FOR-1 vs OTHER ENTRY PATHS — is the intro pack a good deal for the studio?')
print('=' * 118)
# compare members by how they entered: what they paid later
nc_members = set(SB[SB['Cleaned Category'] == 'Newcomers Special']['Member ID'])
paid_first = set()
for mid, gg in SB[SB['Cleaned Category'] != 'Newcomers Special'].groupby('Member ID'):
    if mid not in nc_members:
        paid_first.add(mid)
def lifetime(ids):
    d = SB[SB['Member ID'].isin(ids)]
    per = d.groupby('Member ID')['val'].sum()
    return per.mean(), per.median(), len(per)
print(f'  Entry via Newcomers 2-for-1 (n={len(nc_members)}):      avg lifetime Rs {lifetime(nc_members)[0]:>9,.0f} | median Rs {lifetime(nc_members)[1]:>9,.0f}')
print(f'  Entry via any other product (n={len(paid_first)}):      avg lifetime Rs {lifetime(paid_first)[0]:>9,.0f} | median Rs {lifetime(paid_first)[1]:>9,.0f}')

print()
print('=' * 118)
print('F. SEPT-2026 LEADS — still-open pipeline (accurate)')
print('=' * 118)
L = pd.read_csv('/home/user/uploads/❖ PM - Leads ❖ - ◉ Leads (31).csv', low_memory=False)
L['created'] = pd.to_datetime(L['Created At'], errors='coerce')
LB = L[L['Center'] == 'Supreme HQ, Bandra'].copy()
LB['won'] = LB['Status'].eq('Won')
s26 = LB[(LB['created'] >= '2026-09-01') & (LB['created'] < '2026-10-01')]
open_states = s26['Status'].isin(['Open', 'Uncategorized', 'Trial Completed', 'Trial Scheduled'])
print(f'  Leads created Sept-2026: {len(s26)}')
print(f'  Won: {s26["won"].sum()} ({s26["won"].mean()*100:.1f}%)')
print(f'  Still in pipeline (open/trialed not yet sold): {open_states.sum()} ({open_states.mean()*100:.0f}%)')
print(f'  Lost/unresponsive/disqualified: {(~open_states & ~s26["won"]).sum()}')
print()
print('  Sept-2026 lead sources:')
print(s26['Source Name'].value_counts().head(10).to_string())
print()
print('  Sept-2026 leads by channel with outcome:')
t = s26.groupby('Channel').agg(leads=('ID', 'size'), won=('won', 'sum'), trialed=('Trial Status', lambda x: x.eq('Trial Completed').sum()))
t['win_%'] = (t['won'] / t['leads'] * 100).round(1)
print(t.to_string())
