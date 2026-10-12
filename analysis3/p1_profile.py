import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)

P = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
R = pd.read_csv('/home/user/uploads/Day End Report - Part 3 - Teacher Recurring (7).csv', low_memory=False)
X = pd.read_csv('/home/user/uploads/Day End Report - Part 3 - Sessions (19).csv', low_memory=False)

print('=' * 110); print('PAYROLL'); print('=' * 110)
P['dt'] = pd.to_datetime(P['Month Year'], format='%b-%Y', errors='coerce')
P.loc[P['dt'].isna(), 'dt'] = pd.to_datetime(P['Month Year'][P['dt'].isna()], format='%B-%Y', errors='coerce')
print('date range:', P['dt'].min(), '->', P['dt'].max())
print('locations:', P['Location'].value_counts().to_dict())
print('unique teachers:', P['Teacher Name'].nunique())
print()
B = P[P['Location'] == 'Supreme HQ, Bandra']
print('BANDRA rows:', len(B), '| teachers:', B['Teacher Name'].nunique(), '| months:', B['dt'].nunique())
print('  Bandra Sep-2026 rows:', len(B[B['dt'] == '2026-09-01']), '| Sep-2025:', len(B[B['dt'] == '2025-09-01']), '| Sep-2024:', len(B[B['dt'] == '2024-09-01']))
print()
print('Bandra Sep-2026:')
print(B[B['dt'] == '2026-09-01'][['Teacher Name', 'Cycle Sessions', 'Strength Sessions', 'Barre Sessions',
      'Total Sessions', 'Total Customers', 'Total Paid', 'Converted', 'Conversion Rate',
      'Retained', 'Retention Rate', 'New']].to_string())
print()
print('is (Teacher, Location, Month) unique?', not P.duplicated(['Teacher ID', 'Location', 'Month Year']).any())

print()
print('=' * 110); print('TEACHER RECURRING'); print('=' * 110)
R['dt'] = pd.to_datetime(R['Date'], errors='coerce')
print('date range:', R['dt'].min(), '->', R['dt'].max())
print('locations:', R['Location'].value_counts().to_dict())
print('unique Trainer:', R['Trainer'].nunique(), '| unique SessionID:', R['SessionID'].nunique())
print('grain check — duplicated(SessionID, Date, Time):', R.duplicated(['SessionID', 'Date', 'Time']).sum())
print('grain check — duplicated(SessionID, Date):', R.duplicated(['SessionID', 'Date']).sum())
print('grain check — duplicated(SessionID):', R.duplicated(['SessionID']).sum())
print()
RB = R[R['Location'] == 'Supreme HQ, Bandra']
print('Bandra rows:', len(RB))
print('Bandra Sep-2026:', len(RB[(RB['dt'] >= '2026-09-01') & (RB['dt'] < '2026-10-01')]))
print()
print(RB[(RB['dt'] >= '2026-09-01') & (RB['dt'] < '2026-10-01')].head(8)[
  ['Trainer', 'SessionName', 'Date', 'Day', 'Time', 'Capacity', 'CheckedIn', 'Booked', 'Revenue',
   'Classes', 'TotalSessions', 'FillRate', 'ClassAvgInclEmpty']].to_string())

print()
print('=' * 110); print('SESSIONS'); print('=' * 110)
X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
print('date range:', X['dt'].min(), '->', X['dt'].max())
print('locations:', X['Location'].value_counts().to_dict())
print('unique Trainer:', X['Trainer'].nunique(), '| unique SessionID:', X['SessionID'].nunique())
print('grain check — duplicated(SessionID, Date, Time):', X.duplicated(['SessionID', 'Date', 'Time']).sum())
print('grain check — duplicated(SessionID, Date):', X.duplicated(['SessionID', 'Date']).sum())
print('grain check — duplicated(SessionID):', X.duplicated(['SessionID']).sum())
print()
XB = X[X['Location'] == 'Supreme HQ, Bandra']
print('Bandra rows:', len(XB))
for lab, a, b_ in [('Sep 2024', '2024-09-01', '2024-10-01'), ('Sep 2025', '2025-09-01', '2025-10-01'), ('Sep 2026', '2026-09-01', '2026-10-01')]:
    x = XB[(XB['dt'] >= a) & (XB['dt'] < b_)]
    print(f'  {lab}: rows={len(x)} sessions={x["SessionID"].nunique()} checkedIn={int(x["CheckedIn"].sum())} revenue={x["Revenue"].sum():,.0f}')
print()
print('Bandra Sep-2026 sample rows:')
print(XB[(XB['dt'] >= '2026-09-01') & (XB['dt'] < '2026-10-01')].head(10)[
  ['Trainer', 'SessionName', 'Date', 'Day', 'Time', 'Capacity', 'CheckedIn', 'LateCancelled', 'Booked',
   'Revenue', 'Classes', 'Memberships', 'Packages', 'IntroOffers', 'SingleClasses', 'Class']].to_string())

print()
print('=' * 110); print('ARE Sessions(19) and the earlier Part 3 export the same?'); print('=' * 110)
old = pd.read_csv('/home/user/google_drive/Day End Report - Part 3', low_memory=False)
print('old rows', len(old), '| new rows', len(X))
print('old cols', [c for c in old.columns if c not in X.columns])
print('new-only cols', [c for c in X.columns if c not in old.columns])
print('old date range', pd.to_datetime(old['Date'], errors='coerce').min(), '->', pd.to_datetime(old['Date'], errors='coerce').max())
