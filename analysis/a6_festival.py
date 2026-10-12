import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')
nn = df[~df['is_import']].copy()
b = nn[nn['First Visit Location'] == BANDRA].copy()

print('=' * 110)
print('FESTIVAL HYPOTHESIS — Ganeshotsav 2026 ran 14-25 Sep (visarjan Fri 25 Sep, procession route = Bandra)')
print('=' * 110)

sep = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01')].copy()
sep['phase'] = np.where(sep['fvd'] < '2026-09-14', 'A. Pre-festival (Sep 1-13)',
                np.where(sep['fvd'] <= '2026-09-25', 'B. Ganeshotsav (Sep 14-25)', 'C. Post-visarjan (Sep 26-30)'))
print('BANDRA Sept-2026 cohort by festival phase:')
t = sep.groupby('phase').agg(clients=('Member Id','count'), conv=('converted','sum'),
                             second=('days_2nd', lambda s: s.notna().sum()), rev=('revenue','sum'))
t['conv_%'] = (t['conv']/t['clients']*100).round(1)
t['second_%'] = (t['second']/t['clients']*100).round(1)
t['arpu'] = (t['rev']/t['clients']).round(0)
print(t.to_string())

print()
print('Daily first-visit volume — Bandra, Sep 1-30 2026:')
daily = sep.groupby(sep['fvd'].dt.date).agg(n=('Member Id','count'), conv=('converted','sum'))
for d, r in daily.iterrows():
    dow = pd.Timestamp(d).day_name()[:3]
    bar = '#' * int(r['n'])
    mark = '  <-- GANESH CHATURTHI' if str(d) == '2026-09-14' else ('  <-- VISARJAN' if str(d)=='2026-09-25' else '')
    print(f'   {d} {dow}  n={int(r["n"]):3d}  {bar}{mark}')

print()
print('=' * 110)
print('COMPARISON: same phase structure, prior Septembers (Bandra)')
print('=' * 110)
for yr in [2024, 2025, 2026]:
    x = b[(b['fvd'] >= f'{yr}-09-01') & (b['fvd'] < f'{yr}-10-01')]
    if len(x) < 20: continue
    x = x.copy()
    x['phase'] = np.where(x['fvd'].dt.day <= 13, 'pre (1-13)', np.where(x['fvd'].dt.day <= 25, 'festival (14-25)', 'post (26-30)'))
    t = x.groupby('phase').agg(clients=('Member Id','count'), conv=('converted','sum'), second=('days_2nd', lambda s: s.notna().sum()))
    t['conv_%'] = (t['conv']/t['clients']*100).round(1)
    t['second_%'] = (t['second']/t['clients']*100).round(1)
    print(f'--- Sept {yr} (n={len(x)}) ---'); print(t.to_string())
    print(f'    total Sept volume: {len(x)}')
    print()

print('Note: Ganesh Chaturthi dates -> 2024: Sep 7 | 2025: Aug 27 | 2026: Sep 14')
print('=> Sept-2025 was a POST-festival month (clean); Sept-2026 was a festival month. Direct YoY comparison is invalid.')

print()
print('=' * 110)
print('NETWORK-WIDE: does the festival explain the Sept engagement collapse?')
print('=' * 110)
nn2 = nn[(nn['fvd'] >= '2026-09-01') & (nn['fvd'] < '2026-10-01')].copy()
nn2['phase'] = np.where(nn2['fvd'].dt.day <= 13, 'pre (1-13)', np.where(nn2['fvd'].dt.day <= 25, 'festival (14-25)', 'post (26-30)'))
t = nn2.groupby('phase').agg(clients=('Member Id','count'), conv=('converted','sum'), second=('days_2nd', lambda s: s.notna().sum()),
                             visits=('No of Visits','mean'))
t['conv_%'] = (t['conv']/t['clients']*100).round(1)
t['second_%'] = (t['second']/t['clients']*100).round(1)
t['visits'] = t['visits'].round(2)
print(t.to_string())

print()
print('Daily network volume, Sept 2026 (all studios):')
dn = nn2.groupby(nn2['fvd'].dt.date).size()
print('   ' + '  '.join(f'{d.day}:{v}' for d, v in dn.items()))

print()
print('=' * 110)
print('AUGUST vs SEPTEMBER at Bandra — did volume shift rather than disappear?')
print('=' * 110)
for lbl, s, e in [('Aug-2026', '2026-08-01','2026-09-01'), ('Sep-2026','2026-09-01','2026-10-01')]:
    x = b[(b['fvd'] >= s) & (b['fvd'] < e)]
    print(f'   {lbl}: clients={len(x)}  conv={x["converted"].sum()} ({x["converted"].mean()*100:.1f}%)  2nd-visit={x["days_2nd"].notna().sum()} ({x["days_2nd"].notna().mean()*100:.1f}%)  rev=Rs {x["revenue"].sum():,.0f}')
