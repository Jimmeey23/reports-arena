import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 70)

X = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
R = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 3 - Teacher Recurring (7).csv', low_memory=False)
P = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)

X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
R['dt'] = pd.to_datetime(R['Date'], errors='coerce')
P['dt'] = pd.to_datetime(P['Month Year'], format='%b-%Y', errors='coerce')
P.loc[P['dt'].isna(), 'dt'] = pd.to_datetime(P['Month Year'][P['dt'].isna()], format='%B-%Y', errors='coerce')

print('=' * 110); print('PAYROLL — what months does it actually cover, per location?'); print('=' * 110)
print(P.groupby('Location')['dt'].agg(['min', 'max', 'nunique', 'size']).to_string())
print()
print('Bandra payroll — last 8 months present:')
B = P[P['Location'] == 'Supreme HQ, Bandra']
print(B.groupby('dt').agg(teachers=('Teacher Name', 'nunique'), sessions=('Total Sessions', 'sum')).tail(8).to_string())
print()
print('>> CONFIRMED: payroll ends Aug-2026. No Sept-2026 rows.')

print()
print('=' * 110); print('TEACHER RECURRING — what is a row?'); print('=' * 110)
rb = R[R['Location'] == 'Supreme HQ, Bandra'].copy()
print('Bandra rows:', len(rb), '| unique SessionID:', rb['SessionID'].nunique())
print('Rows per (Trainer, Time, Day):')
print(rb.groupby(['Trainer', 'Day', 'Time']).size().describe())
print()
print('Sample: does one row = one recurring weekly slot?')
smp = rb[(rb['dt'] >= '2026-09-01') & (rb['dt'] < '2026-10-01')].sort_values(['Trainer', 'Time'])
print(smp[['Trainer', 'SessionName', 'Day', 'Time', 'Classes', 'Capacity', 'CheckedIn', 'Booked',
           'Revenue', 'FillRate', 'ClassAvgInclEmpty', 'ClassAvgExclEmpty', 'WeightedAverage']].head(20).to_string())
print()
print('Recompute fill rate = CheckedIn / Capacity where Capacity>0 (rows in Sep-26):')
t = smp.copy(); t['cap_per'] = t['Capacity'] / t['Classes'].replace(0, np.nan)
print(t[['Trainer','Time','Classes','Capacity','CheckedIn','cap_per','FillRate']].head(12).to_string())

print()
print('=' * 110); print('SESSIONS — the clean class-occurrence book'); print('=' * 110)
xb = X[X['Location'] == 'Supreme HQ, Bandra'].copy()
x26 = xb[(xb['dt'] >= '2026-09-01') & (xb['dt'] < '2026-10-01')]
x25 = xb[(xb['dt'] >= '2025-09-01') & (xb['dt'] < '2025-10-01')]
x24 = xb[(xb['dt'] >= '2024-09-01') & (xb['dt'] < '2024-10-01')]
print(f"Sep-2026: {len(x26)} class occurrences | checked-in {int(x26['CheckedIn'].sum())} | revenue Rs {x26['Revenue'].sum():,.0f}")
print(f"Sep-2025: {len(x25)} | {int(x25['CheckedIn'].sum())} | Rs {x25['Revenue'].sum():,.0f}")
print(f"Sep-2024: {len(x24)} | {int(x24['CheckedIn'].sum())} | Rs {x24['Revenue'].sum():,.0f}")
print()
print('revenue per checked-in:')
for lab, d in [('2024', x24), ('2025', x25), ('2026', x26)]:
    print(f'  Sep-{lab}: Rs {d["Revenue"].sum()/max(d["CheckedIn"].sum(),1):,.0f}')
print()
print('Class mix, Sep-2026:')
print(x26.groupby('Class').agg(sessions=('SessionID', 'size'), cap=('Capacity', 'sum'),
      checked=('CheckedIn', 'sum'), revenue=('Revenue', 'sum')).sort_values('revenue', ascending=False).to_string())
print()
print('Empty sessions (0 checked in):')
for lab, d in [('Sep-2024', x24), ('Sep-2025', x25), ('Sep-2026', x26)]:
    e = (d['CheckedIn'] == 0).sum()
    print(f'  {lab}: {e} of {len(d)} sessions ({e/len(d)*100:.0f}%)')
print()
print('By time of day, Sep-2026:')
x26 = x26.copy(); x26['hr'] = pd.to_datetime(x26['Time'], format='%H:%M:%S', errors='coerce').dt.hour
print(x26.groupby('hr').agg(sessions=('SessionID','size'), cap=('Capacity','sum'), checked=('CheckedIn','sum'),
      revenue=('Revenue','sum')).assign(fill=lambda d: (d['checked']/d['cap']*100).round(0)).to_string())
print()
print('By day of week, Sep-2026:')
print(x26.groupby('Day').agg(sessions=('SessionID','size'), cap=('Capacity','sum'), checked=('CheckedIn','sum'),
      revenue=('Revenue','sum')).assign(fill=lambda d: (d['checked']/d['cap']*100).round(0)).to_string())

print()
print('=' * 110); print('SALES — Bandra September, three years'); print('=' * 110)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = pd.to_numeric(S['Payment Value'].astype(str).str.replace(r'[^0-9.\-]', '', regex=True), errors='coerce')
sb = S[S['Calculated Location'] == 'Supreme HQ, Bandra']
print('Bandra sales columns:', [c for c in S.columns])
print()
for y in [2024, 2025, 2026]:
    d = sb[(sb['dt'] >= f'{y}-09-01') & (sb['dt'] < f'{y}-10-01')]
    print(f'  Sep-{y}: {len(d)} txns | Rs {d["val"].sum():,.0f} | {d["Member ID"].nunique()} paying members')
