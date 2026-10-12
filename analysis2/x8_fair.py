import pandas as pd, numpy as np
from math import comb
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 70)

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')
s = M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')].copy()
s['conv'] = s['Conversion Status'].eq('Converted')
s['entry'] = s['Is New'].astype(str)

print('=' * 118)
print('FAIRNESS TEST 1 — compare like with like: conversion by entry type x teacher')
print('=' * 118)
tri = s[s['entry'].str.contains('Trial')]
r = tri[tri['Trainer Name'] == 'Reshma Sharma']; o = tri[tri['Trainer Name'] != 'Reshma Sharma']
print(f'  TRIAL-class clients: Reshma {len(r)} clients, {r["conv"].sum()} converted ({r["conv"].mean()*100:.1f}%)')
print(f'  TRIAL-class clients: everyone else {len(o)} clients, {o["conv"].sum()} converted ({o["conv"].mean()*100:.1f}%)')
print()
print('  By trainer (trial clients only):')
tt = tri.groupby('Trainer Name').agg(clients=('Member Id', 'size'), conv=('conv', 'sum'))
tt['conv_%'] = (tt['conv'] / tt['clients'] * 100).round(1)
print(tt.sort_values('clients', ascending=False).to_string())

print()
print('=' * 118)
print('FAIRNESS TEST 2 — is 0 of 33 a real signal or luck?')
print('=' * 118)
base = s[s['Trainer Name'] != 'Reshma Sharma']['conv'].mean()
n = 33
p0 = (1 - base) ** n
print(f'  Studio conversion rate excluding Reshma: {base*100:.1f}%')
print(f'  Probability of 0 conversions in {n} clients purely by chance: {p0*100:.1f}%')
print(f'  Expected conversions in 33 clients at that rate: {base*n:.1f}')
print()
# all-time, is her LTV low?
lt = M[M['First Visit Location'] == 'Supreme HQ, Bandra'].copy()
lt['ltv_n'] = pd.to_numeric(lt['Ltv'].astype(str).str.replace(r'[^0-9]', '', regex=True), errors='coerce')
big = lt[lt['Trainer Name'].notna()].groupby('Trainer Name').agg(n=('Member Id', 'size'), ltv=('ltv_n', 'mean'))
big = big[big['n'] >= 150].sort_values('ltv')
print('  All-time LTV per client, trainers with 150+ clients:')
print(big.round(0).to_string())
print()
print(f'  Reshma sits at rank {list(big.index).index("Reshma Sharma")+1} of {len(big)} on lifetime value per client.')

print()
print('=' * 118)
print('FAIRNESS TEST 3 — month-by-month, her conversion vs the studio')
print('=' * 118)
mo = M[M['First Visit Location'] == 'Supreme HQ, Bandra'].copy()
mo['conv'] = mo['Conversion Status'].eq('Converted')
res = []
for ym, g in mo.groupby(mo['cohort'].dt.to_period('M')):
    gg = g[g['Trainer Name'] == 'Reshma Sharma']
    oo = g[g['Trainer Name'] != 'Reshma Sharma']
    if len(gg) < 4: continue
    res.append({'month': str(ym), 'reshma_n': len(gg), 'reshma_conv_%': round(gg['conv'].mean()*100, 1),
                'studio_conv_%': round(oo['conv'].mean()*100, 1) if len(oo) else np.nan})
rd = pd.DataFrame(res)
rd['gap'] = (rd['reshma_conv_%'] - rd['studio_conv_%']).round(1)
print(rd.set_index('month').to_string())

print()
print('=' * 118)
print('FAIRNESS TEST 4 — Sept-26 vintage: is EVERY new trainer weak, or just one?')
print('=' * 118)
print('  Clients each trainer received in Sept-26 and how many they converted:')
g = s.groupby('Trainer Name').agg(n=('Member Id', 'size'), conv=('conv', 'sum'))
g['conv_%'] = (g['conv'] / g['n'] * 100).round(1)
g['share_of_month_%'] = (g['n'] / len(s) * 100).round(1)
print(g.sort_values('n', ascending=False).to_string())

print()
print('=' * 118)
print('FAIRNESS TEST 5 — did the STARTERS she taught get a fair shot? visit depth')
print('=' * 118)
s['v'] = pd.to_numeric(s['No of Visits'], errors='coerce')
print(f'  Reshma-trained clients: avg visits {s[s["Trainer Name"]=="Reshma Sharma"]["v"].mean():.2f}, '
      f'% who came back at all {(s[s["Trainer Name"]=="Reshma Sharma"]["v"]>1).mean()*100:.1f}%')
print(f'  All other clients     : avg visits {s[s["Trainer Name"]!="Reshma Sharma"]["v"].mean():.2f}, '
      f'% who came back at all {(s[s["Trainer Name"]!="Reshma Sharma"]["v"]>1).mean()*100:.1f}%')

print()
print('=' * 118)
print('SEATS OFFERED — true counts (per session, not per booking row)')
print('=' * 118)
C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
C['cap'] = pd.to_numeric(C['Capacity'], errors='coerce')
Bs = C[C['Location'] == 'Supreme HQ, Bandra']
for lbl, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    x = Bs[(Bs['dt'] >= a) & (Bs['dt'] < b_)]
    ss = x.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'), booked=('Member ID', 'size'))
    ss = ss[ss['cap'] > 0]
    print(f'  {lbl}: {len(ss)} sessions | seats offered {int(ss["cap"].sum()):,} | seats filled {int(ss["att"].sum()):,} | '
          f'utilisation {ss["att"].sum()/ss["cap"].sum()*100:.1f}% | avg class size {ss["att"].mean():.1f} of {ss["cap"].mean():.1f}')

print()
print('=' * 118)
print('YEAR CONTEXT — same roster check across the whole year')
print('=' * 118)
for per, lab in [(('2024-09-01', '2024-10-01'), 'Sept 2024'), (('2025-09-01', '2025-10-01'), 'Sept 2025'), (('2026-09-01', '2026-10-01'), 'Sept 2026')]:
    x = Bs[(Bs['dt'] >= per[0]) & (Bs['dt'] < per[1])]
    ss = x.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'), booked=('Member ID', 'size'))
    ss = ss[ss['cap'] > 0]
    if not len(ss): continue
    print(f'  {lab}: {len(ss)} sessions | seats {int(ss["cap"].sum()):,} | filled {int(ss["att"].sum()):,} | util {ss["att"].sum()/ss["cap"].sum()*100:.1f}%')
