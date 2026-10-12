import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 70)

X = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
X['hr'] = pd.to_datetime(X['Time'], format='%H:%M:%S', errors='coerce').dt.hour
xb = X[X['Location'] == 'Supreme HQ, Bandra'].copy()
x26 = xb[(xb['dt'] >= '2026-09-01') & (xb['dt'] < '2026-10-01')].copy()
x25 = xb[(xb['dt'] >= '2025-09-01') & (xb['dt'] < '2025-10-01')].copy()
x24 = xb[(xb['dt'] >= '2024-09-01') & (xb['dt'] < '2024-10-01')].copy()

print('=' * 110); print('A. THREE SEPTEMBERS — headline class metrics'); print('=' * 110)
for lab, d in [('Sep-2024', x24), ('Sep-2025', x25), ('Sep-2026', x26)]:
    cap, chk = d['Capacity'].sum(), d['CheckedIn'].sum()
    print(f'  {lab}: sessions {len(d):3d} | seats {cap:6,d} | attended {chk:5,d} | fill {chk/cap*100:5.1f}% | '
          f'empty {(d["CheckedIn"]==0).sum():3d} | revenue Rs {d["Revenue"].sum():>10,.0f} | /class Rs {d["Revenue"].sum()/len(d):>7,.0f} | /attendee Rs {d["Revenue"].sum()/max(chk,1):>6,.0f}')

print()
print('=' * 110); print('B. Sep-2026 BY FORMAT'); print('=' * 110)
f = x26.groupby('Class').agg(sessions=('SessionID', 'size'), seats=('Capacity', 'sum'), attended=('CheckedIn', 'sum'),
                             lc=('LateCancelled', 'sum'), nonpaid=('NonPaid', 'sum'), rev=('Revenue', 'sum'))
f['fill_%'] = (f['attended']/f['seats']*100).round(1)
f['avg_size'] = (f['attended']/f['sessions']).round(2)
f['rev_per_class'] = (f['rev']/f['sessions']).round(0)
f['rev_per_head'] = (f['rev']/f['attended'].replace(0, np.nan)).round(0)
f['empty'] = x26.groupby('Class')['CheckedIn'].apply(lambda s: (s == 0).sum())
print(f.sort_values('rev', ascending=False).to_string())

print()
print('=' * 110); print('C. Sep-2026 BY DAY OF WEEK'); print('=' * 110)
od = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
dy = x26.groupby('Day').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), attended=('CheckedIn','sum'), rev=('Revenue','sum'))
dy['fill_%'] = (dy['attended']/dy['seats']*100).round(1)
dy['rev_per_class'] = (dy['rev']/dy['sessions']).round(0)
print(dy.reindex(od).to_string())

print()
print('=' * 110); print('D. Sep-2026 BY START HOUR'); print('=' * 110)
hr = x26.groupby('hr').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), attended=('CheckedIn','sum'), rev=('Revenue','sum'))
hr['fill_%'] = (hr['attended']/hr['seats']*100).round(1)
hr['rev_per_class'] = (hr['rev']/hr['sessions']).round(0)
print(hr.to_string())

print()
print('=' * 110); print('E. TIME-OF-DAY BANDS'); print('=' * 110)
def band(h):
    if pd.isna(h): return 'unknown'
    if h < 9: return 'Early (before 9)'
    if h < 12: return 'Morning (9-11)'
    if h < 16: return 'Midday (12-15)'
    if h < 18: return 'Afternoon (16-17)'
    if h < 21: return 'Evening (18-20)'
    return 'Late (21+)'
x26['band'] = x26['hr'].apply(band)
bd = x26.groupby('band').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), attended=('CheckedIn','sum'), rev=('Revenue','sum'))
bd['fill_%'] = (bd['attended']/bd['seats']*100).round(1)
bd['rev_per_class'] = (bd['rev']/bd['sessions']).round(0)
print(bd.sort_values('fill_%', ascending=False).to_string())

print()
print('=' * 110); print('F. PAYMENT TYPE MIX PER CLASS, Sep-2026'); print('=' * 110)
pm = x26.groupby('Class').agg(mem=('Memberships','sum'), pkg=('Packages','sum'), intro=('IntroOffers','sum'), single=('SingleClasses','sum'))
pm['total'] = pm.sum(axis=1)
for c in ['mem','pkg','intro','single']:
    pm[c+'_%'] = (pm[c]/pm['total']*100).round(1)
print(pm.sort_values('total', ascending=False).to_string())

print()
print('=' * 110); print('G. BEST AND WORST INDIVIDUAL SESSIONS, Sep-2026 (capacity>=8)'); print('=' * 110)
xx = x26[x26['Capacity'] >= 8].copy()
xx['fill'] = xx['CheckedIn']/xx['Capacity']*100
cols = ['Date','Day','Time','Class','Trainer','Capacity','CheckedIn','Booked','LateCancelled','Revenue']
print('--- fullest ---')
print(xx.nlargest(12, 'fill')[cols].to_string())
print('--- emptiest ---')
print(xx.nsmallest(12, 'fill')[cols].to_string())

print()
print('=' * 110); print('H. EMPTY / NEAR-EMPTY SESSIONS — what did they cost?'); print('=' * 110)
emp = x26[x26['CheckedIn'] == 0]
near = x26[(x26['CheckedIn'] > 0) & (x26['CheckedIn'] <= 2)]
print(f'  fully empty: {len(emp)} sessions, {emp["Capacity"].sum()} seats, Rs {emp["Revenue"].sum():,.0f} revenue')
print(emp[['Date','Day','Time','Class','Trainer','Capacity','Booked','LateCancelled']].to_string())
print(f'  1-2 attendees: {len(near)} sessions, {near["Capacity"].sum()} seats')
print(near.groupby('Class').size().to_string())

print()
print('=' * 110); print('I. WEEKLY PATTERN, Sep-2026 vs Sep-2025'); print('=' * 110)
for lab, d in [('2025', x25), ('2026', x26)]:
    d = d.copy(); d['wk'] = ((d['dt'].dt.day - 1)//7)+1
    w = d.groupby('wk').agg(sessions=('SessionID','size'), attended=('CheckedIn','sum'), seats=('Capacity','sum'), rev=('Revenue','sum'))
    w['fill_%'] = (w['attended']/w['seats']*100).round(1)
    print(f'--- Sep-{lab} ---'); print(w.to_string())

print()
print('=' * 110); print('J. HOSTED / SPECIAL CLASSES, Sep-2026'); print('=' * 110)
h = x26[x26['SessionName'].str.contains('X |x |Hosted|Sweat|Pickle|Peakst8|KRC|Fest|Ladies', case=False, na=False)]
print(f'  {len(h)} sessions')
print(h[['Date','Day','Time','SessionName','Trainer','Capacity','CheckedIn','NonPaid','Complimentary','Revenue']].to_string())
