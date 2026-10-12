import pandas as pd, numpy as np
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 70)

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')
s = M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')].copy()
s['conv'] = s['Conversion Status'].eq('Converted')
s['v'] = pd.to_numeric(s['No of Visits'], errors='coerce')

print('=' * 118)
print('A. FIRST-VISIT TEACHER -> CLIENT OUTCOME, Sept-2026 Bandra cohort (n=143)')
print('=' * 118)
t = s.groupby('Trainer Name').agg(clients=('Member Id', 'size'), conv=('conv', 'sum'), visits=('v', 'mean'),
                                  ref=('Is New', lambda x: x.str.contains('Referral', na=False).sum()),
                                  trail=('Is New', lambda x: x.str.contains('Trial', na=False).sum()))
t['conv_%'] = (t['conv'] / t['clients'] * 100).round(1)
t['visits'] = t['visits'].round(2)
print(t.sort_values('clients', ascending=False).to_string())

print()
print('=' * 118)
print('B. THE ROSTER SHIFT — bookings by teacher, Sept-25 vs Sept-26 (Bandra)')
print('=' * 118)
C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
Bs = C[C['Location'] == 'Supreme HQ, Bandra']
sep25 = Bs[(Bs['dt'] >= '2025-09-01') & (Bs['dt'] < '2025-10-01')]
sep26 = Bs[(Bs['dt'] >= '2026-09-01') & (Bs['dt'] < '2026-10-01')]
print(f'  Sept-25: {len(sep25)} bookings, {int(sep25["checked"].sum())} attended, {sep25["Session ID"].nunique()} sessions')
print(f'  Sept-26: {len(sep26)} bookings, {int(sep26["checked"].sum())} attended, {sep26["Session ID"].nunique()} sessions')
print(f'  change : bookings {(len(sep26)/len(sep25)-1)*100:+.1f}%, attended {(sep26["checked"].sum()/sep25["checked"].sum()-1)*100:+.1f}%, sessions {(sep26["Session ID"].nunique()/sep25["Session ID"].nunique()-1)*100:+.1f}%')
print()
lt = M[M['First Visit Location'] == 'Supreme HQ, Bandra']
lt = lt.assign(ltv_n=pd.to_numeric(lt['Ltv'].astype(str).str.replace(r'[^0-9]', '', regex=True), errors='coerce'))
lt = lt.assign(conv=lt['Conversion Status'].eq('Converted'))
tt = lt.groupby('Trainer Name').agg(all_clients=('Member Id', 'size'), all_conv=('conv', 'mean'), ltv_per=('ltv_n', 'mean'))
a = sep25.groupby('Teacher Name').size().rename('sep25')
b_ = sep26.groupby('Teacher Name').size().rename('sep26')
j = pd.concat([a, b_], axis=1).fillna(0).join(tt)
j = j[(j['sep25'] > 20) | (j['sep26'] > 20)]
j['d'] = (j['sep26'] - j['sep25']).astype(int)
j['all_conv_%'] = (j['all_conv'] * 100).round(1)
j = j.sort_values('d')
print(j[['sep25', 'sep26', 'd', 'all_clients', 'all_conv_%', 'ltv_per']].to_string())

print()
print('=' * 118)
print('C. IS THE CONVERSION DECLINE FOLLOWING THE ROSTER? (monthly)')
print('=' * 118)
cols = ['Cauveri Vikrant', 'Karanvir Bhatia', 'Karan Bhatia', 'Simonelle De Vitre', 'Mrigakshi Jaiswal',
        'Vivaran Dhasmana', 'Atulan Purohit', 'Reshma Sharma', 'Pranjali Jain', 'Anmol Sharma', 'Rohan Dahima']
piv = Bs.groupby([Bs['dt'].dt.to_period('M'), 'Teacher Name']).size().unstack(fill_value=0)
piv = piv.reindex(columns=cols, fill_value=0).loc['2025-06':'2026-10']
piv['DEPARTED_grp'] = piv[['Cauveri Vikrant', 'Karanvir Bhatia', 'Karan Bhatia', 'Simonelle De Vitre', 'Mrigakshi Jaiswal']].sum(axis=1)
piv['INCOMING_grp'] = piv[['Reshma Sharma', 'Pranjali Jain', 'Anmol Sharma', 'Rohan Dahima']].sum(axis=1)
print(piv[['DEPARTED_grp', 'INCOMING_grp', 'Vivaran Dhasmana', 'Atulan Purohit']].to_string())
print()
print('  Share of all Bandra bookings held by the DEPARTED group + Vivaran vs the INCOMING group:')
for ym in ['2025-06', '2025-09', '2026-01', '2026-03', '2026-06', '2026-09']:
    tot = piv.loc[ym].sum() - piv.loc[ym, ['DEPARTED_grp', 'INCOMING_grp']].sum()
    print(f'   {ym}: departed-group {piv.loc[ym,"DEPARTED_grp"]:4d} | incoming-group {piv.loc[ym,"INCOMING_grp"]:4d} | others {tot:4d}')

print()
print('=' * 118)
print('D. COHORT OUTCOME BY THE TEACHER THEY HAD (Bandra, all-time cohort file)')
print('=' * 118)
big = tt[tt['all_clients'] >= 40].copy()
big['all_conv_%'] = (big['all_conv'] * 100).round(1)
print(big.sort_values('all_conv', ascending=False)[['all_clients', 'all_conv_%', 'ltv_per']].round(0).to_string())
