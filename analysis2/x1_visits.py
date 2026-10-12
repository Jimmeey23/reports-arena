import pandas as pd, numpy as np
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 60)

C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
C['late'] = C['Is Late Cancelled'].astype(str).str.upper().eq('TRUE')
B = C[C['Location'] == 'Supreme HQ, Bandra'].copy()
B['ym'] = B['dt'].dt.to_period('M')

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')

print('=' * 118)
print('A. BANDRA FOOTFALL — attendance volume, unique members, and frequency')
print('=' * 118)
g = B.groupby('ym').agg(bookings=('Member ID', 'size'), attended=('checked', 'sum'),
                        late_cancels=('late', 'sum'), members=('Member ID', 'nunique'))
g = g.loc['2025-01':'2026-10']
g['visits_per_member'] = (g['attended'] / g['members']).round(2)
g['late_cancel_%'] = (g['late_cancels'] / g['bookings'] * 100).round(1)
print(g.to_string())

print()
print('--- September, three years ---')
for yr in [2024, 2025, 2026]:
    x = B[(B['dt'] >= f'{yr}-09-01') & (B['dt'] < f'{yr}-10-01')]
    a = x[x['checked']]
    print(f'  Sept {yr}: bookings={len(x):5d}  attended={len(a):5d}  unique members={a["Member ID"].nunique():4d}  '
          f'visits/member={len(a)/max(a["Member ID"].nunique(),1):.2f}  late cancels={int(x["late"].sum()):4d} ({x["late"].mean()*100:.1f}%)')

print()
print('=' * 118)
print('B. CLASS-LEVEL ENGAGEMENT — is the studio getting quieter per member?')
print('=' * 118)
for lbl, s, e in [('2025 Jan-Sep', '2025-01-01', '2025-10-01'), ('2026 Jan-Sep', '2026-01-01', '2026-10-01')]:
    x = B[(B['dt'] >= s) & (B['dt'] < e)]
    a = x[x['checked']]
    per_member = a.groupby('Member ID').size()
    print(f'  {lbl}: attended={len(a):6d} members={a["Member ID"].nunique():5d} '
          f'visits/member={per_member.mean():.2f} median={per_member.median():.0f} '
          f'| 1-visit members={100*(per_member==1).mean():.1f}%')
    # retention-of-visitors: how many returned within the period
print()
print('  Member visit-frequency distribution:')
for lbl, s, e in [('2025 Jan-Sep', '2025-01-01', '2025-10-01'), ('2026 Jan-Sep', '2026-01-01', '2026-10-01')]:
    x = B[(B['dt'] >= s) & (B['dt'] < e)]
    a = x[x['checked']].groupby('Member ID').size()
    print(f'   {lbl}: ' + ' | '.join(f'{k}-visit: {(a==k).sum()}' for k in [1, 2, 3]) +
          f' | 10+: {(a>=10).sum()}')

print()
print('=' * 118)
print('C. THE 2-FOR-1 DISTORTION — how much of "2nd visit" is actually a pre-paid redemption')
print('=' * 118)
sep_ids = set(M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]['Member Id'])
def return_profile(ids, label):
    sb = B[B['Member ID'].isin(ids)].sort_values(['Member ID', 'dt'])
    rows = []
    for mid, gg in sb.groupby('Member ID'):
        att = gg[gg['checked']]
        if len(att) == 0: continue
        rows.append({'mid': mid, 'n': len(att),
                     'c2': att.iloc[1]['Cleaned Product'] if len(att) > 1 else None,
                     'c3': att.iloc[2]['Cleaned Product'] if len(att) > 2 else None})
    d = pd.DataFrame(rows)
    if d.empty: return None
    two = d[d['n'] >= 2]
    prepaid = two['c2'].str.contains('2 For 1|Newcomers', case=False, na=False).sum()
    print(f'  {label}: cohort={len(ids)} attended={len(d)}')
    print(f'     reached a 2nd class        : {len(two):3d}  ({len(two)/len(ids)*100:5.1f}% of cohort)')
    print(f'       of which pre-paid 2-for-1: {prepaid:3d}')
    print(f'       of which genuine return  : {len(two)-prepaid:3d}  ({(len(two)-prepaid)/len(ids)*100:5.1f}% of cohort)')
    print(f'     reached a 3rd class        : {(d["n"]>=3).sum():3d}  ({(d["n"]>=3).sum()/len(ids)*100:5.1f}% of cohort)')
    return d

dsep = return_profile(sep_ids, 'Sept 2026 Bandra cohort')
print()
for lbl, mo in [('Aug 2026', '2026-08-01'), ('Jul 2026', '2026-07-01'), ('Sept 2025', '2025-09-01')]:
    ids = set(M[(M['cohort'] == pd.Timestamp(mo)) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]['Member Id'])
    return_profile(ids, f'{lbl} Bandra cohort')
    print()

print('=' * 118)
print('D. NEWCOMERS 2 FOR 1 — programme economics')
print('=' * 118)
nc = B[B['Cleaned Product'].str.contains('2 For 1', na=False)]
print(f'Bandra lifetime records on Newcomers 2 For 1: {len(nc)}  unique members: {nc["Member ID"].nunique()}')
print('By month (last 14):')
print(nc.groupby('ym').size().loc['2025-09':'2026-10'].to_string())
print()
# do 2-for-1 users convert?
ncm = M[M['Memberships Bought Post Trial'].astype(str).str.contains('2 For 1', na=False)]
print(f'Members in master file who bought Newcomers 2 For 1 at any point: {len(ncm)}')
print(f'  converted: {ncm["Conversion Status"].eq("Converted").sum()} ({ncm["Conversion Status"].eq("Converted").mean()*100:.1f}%)')
print(f'  retained : {ncm["Retention Status"].eq("Retained").sum()} ({ncm["Retention Status"].eq("Retained").mean()*100:.1f}%)')
print(f'  avg lifetime value: Rs {pd.to_numeric(ncm["Ltv"].astype(str).str.replace(r"[^0-9]","",regex=True),errors="coerce").mean():,.0f}')
print()
allm = M[M['First Visit Location'] == 'Supreme HQ, Bandra']
print(f'BANDRA benchmark: converted {allm["Conversion Status"].eq("Converted").mean()*100:.1f}%, retained {allm["Retention Status"].eq("Retained").mean()*100:.1f}%')
2
