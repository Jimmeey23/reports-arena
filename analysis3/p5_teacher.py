import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)

R = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 3 - Teacher Recurring (7).csv', low_memory=False)
X = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
P = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
R['dt'] = pd.to_datetime(R['Date'], errors='coerce'); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
P['dt'] = pd.to_datetime(P['Month Year'], format='%b-%Y', errors='coerce')

rb = R[R['Location'] == 'Supreme HQ, Bandra'].copy()
xb = X[X['Location'] == 'Supreme HQ, Bandra'].copy()

print('=' * 110); print('A. RECURRING FILE — what does Date mean?'); print('=' * 110)
print('Bandra rows', len(rb))
print('Date distribution (top 10):'); print(rb['dt'].value_counts().head(10).to_string())
print('min/max:', rb['dt'].min(), rb['dt'].max())
print('Trainers in Bandra recurring:', sorted(rb['Trainer'].unique()))

print()
print('=' * 110); print('B. DECODE THE COLUMNS — test on one trainer/slot'); print('=' * 110)
t = rb[(rb['Trainer'] == 'Anmol Sharma') & (rb['Day'] == 'Monday') & (rb['Time'] == '07:30:00')]
print(t[['SessionName','Classes','Capacity','CheckedIn','Booked','Revenue','FillRate','ClassAvgInclEmpty','ClassAvgExclEmpty']].to_string())
print()
print('Try: FillRate = Revenue/Classes ->', 21521.94/12)
print('Try: ClassAvgExclEmpty = CheckedIn/Capacity ->', 17/156)
print('Try: ClassAvgInclEmpty = ? Booked/Classes ->', 17/12, '| CheckedIn/Classes ->', 17/12)
print('>> FillRate is mislabelled (it is revenue per class). ClassAvgExclEmpty is the true fill rate.')

print()
print('=' * 110); print('C. RECOMPUTE RECURRING SLOTS MYSELF from Sessions(19)'); print('=' * 110)
# find the window that reproduces the recurring file: try trailing 90 days
for days, label in [(60, 'last 60d'), (90, 'last 90d'), (120, 'last 120d'), (182, 'last 182d')]:
    cut = xb['dt'].max() - pd.Timedelta(days=days)
    w = xb[xb['dt'] >= cut]
    mine = w.groupby(['Trainer', 'Day', 'Time']).size().rename('mine')
    theirs = rb.set_index(['Trainer', 'Day', 'Time'])['Classes']
    j = pd.concat([mine, theirs], axis=1).dropna()
    if len(j):
        match = (j['mine'] == j['Classes']).mean()
        print(f'  {label}: overlapping slots {len(j)} | exact match {match*100:.0f}% | mean diff {(j["mine"]-j["Classes"]).abs().mean():.2f}')

print()
print('=' * 110); print('D. BANDRA SEP-2026 TRAINER SCORECARD (from Sessions)'); print('=' * 110)
x26 = xb[(xb['dt'] >= '2026-09-01') & (xb['dt'] < '2026-10-01')].copy()
x25 = xb[(xb['dt'] >= '2025-09-01') & (xb['dt'] < '2025-10-01')].copy()
g = x26.groupby('Trainer').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), attended=('CheckedIn','sum'),
                               booked=('Booked','sum'), lc=('LateCancelled','sum'), rev=('Revenue','sum'),
                               formats=('Class','nunique'), slots=('Time','nunique'))
g['fill_%'] = (g['attended']/g['seats']*100).round(1)
g['avg_class'] = (g['attended']/g['sessions']).round(2)
g['rev_per_class'] = (g['rev']/g['sessions']).round(0)
g['rev_per_head'] = (g['rev']/g['attended'].replace(0,np.nan)).round(0)
g['lc_%'] = (g['lc']/(g['booked']+g['lc'])*100).round(1)
g = g.sort_values('rev', ascending=False)
print(g.to_string())

print()
print('=' * 110); print('E. TRAINER × FORMAT, Sep-2026'); print('=' * 110)
tf = x26.groupby(['Trainer','Class']).agg(sessions=('SessionID','size'), seats=('Capacity','sum'),
                                          attended=('CheckedIn','sum'), rev=('Revenue','sum'))
tf['fill_%'] = (tf['attended']/tf['seats']*100).round(0)
print(tf.sort_values(['Trainer','rev'], ascending=[True, False]).to_string())

print()
print('=' * 110); print('F. SESSION VOLUME + FILL BY TRAINER, three Septembers'); print('=' * 110)
for lab, d in [('Sep-2025', x25), ('Sep-2026', x26)]:
    t = d.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','sum'), seats=('Capacity','sum'), rev=('Revenue','sum'))
    t['fill_%'] = (t['att']['sum'] and 0) or 0
    t['fill_%'] = (t['att']/t['seats']*100).round(0)
    print(f'--- {lab} ---')
    print(t.sort_values('n', ascending=False).to_string())
    print()

print('=' * 110); print('G. PAYROLL — Bandra teacher economics (through Aug-2026)'); print('=' * 110)
pb = P[P['Location'] == 'Supreme HQ, Bandra'].copy()
print('columns available:', [c for c in P.columns if 'Paid' in c or 'Rate' in c or 'Conversion' in c or 'Retention' in c])
p26 = pb[pb['dt'] == '2026-08-01']
print()
print('Bandra Aug-2026 payroll:')
print(p26[['Teacher Name','Total Sessions','Total Customers','Total Paid','Converted','Conversion Rate','Retained','Retention Rate','New']].to_string())
print()
print('Sessions by band over time:')
print(pb.groupby('dt')['Total Sessions'].sum().tail(14).to_string())
