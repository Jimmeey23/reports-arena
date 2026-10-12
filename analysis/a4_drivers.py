import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')
b = df[(df['First Visit Location'] == BANDRA) & (~df['is_import'])].copy()
b['obs_days'] = (SNAP - b['fvd']).dt.days
bx = b[b['cohort'] == pd.Timestamp('2026-09-01')].copy()

print('=' * 110)
print('A. WHAT DOES A SECOND VISIT WORTH? (Bandra, all cohorts n=%d)' % len(b))
print('=' * 110)
b['had2'] = b['days_2nd'].notna()
g = b.groupby('had2').agg(n=('Member Id','count'), conv=('converted','sum'),
                          ltv_mean=('revenue','mean'), ltv_median=('revenue','median'),
                          ltv_sum=('revenue','sum'), visits=('No of Visits','mean'))
g['conv_%'] = (g['conv']/g['n']*100).round(1)
print(g.round(0).to_string())
delta = g.loc[True,'ltv_mean'] - g.loc[False,'ltv_mean']
print(f'\n   >> Incremental lifetime value of getting a 2nd visit = Rs {delta:,.0f} per member')
print(f'   >> 2nd-visit members are {(g.loc[True,"conv_%"]/g.loc[False,"conv_%"]):.0f}x more likely to convert')

print()
print('=' * 110)
print('B. OPPORTUNITY SIZING — Sep-2026 Bandra cohort (n=143)')
print('=' * 110)
n = len(bx)
actual_2nd = bx['days_2nd'].notna().sum()
trailing_2nd = 0.306   # trailing-12m strict equal-window 2nd-visit-30d rate
expected_2nd = round(n * trailing_2nd)
gap_members = expected_2nd - actual_2nd
conv_of_2nd = 0.619    # share of 2nd-visit members who convert (all-cohort)
incr_conv = round(gap_members * conv_of_2nd)
horizon_ltv = 17363    # avg revenue per converter, Bandra Sep-26
print(f'   Cohort size                              : {n}')
print(f'   Actual members with a 2nd visit          : {actual_2nd}  ({actual_2nd/n*100:.1f}%)')
print(f'   Expected at trailing-12m norm (30.6%)    : {expected_2nd}')
print(f'   MISSING 2nd VISITS                       : {gap_members}')
print(f'   Likely incremental converters            : {incr_conv}  (at 61.9% 2nd-visit->conversion)')
print(f'   Expected 30-day revenue recovered        : Rs {incr_conv*horizon_ltv:,.0f}')
print(f'   Annualised (x12 cohorts)                 : Rs {incr_conv*horizon_ltv*12:,.0f}')
print(f'   Using full-lifetime LTV of a 2nd visitor : Rs {gap_members*(g.loc[True,"ltv_mean"]-g.loc[False,"ltv_mean"]):,.0f}  (12-mo horizon)')

print()
print('=' * 110)
print('C. SEPT-2026 COHORT — SEGMENTED BY ENTRY ROUTE')
print('=' * 110)
bx['channel'] = np.select(
    [bx['Is New'].eq('New - Trial Class'),
     bx['Is New'].eq('New - Hosted Class'),
     bx['Is New'].eq('New - Referral Class'),
     bx['Is New'].eq('New - Paid First Visit')],
    ['1. Free Trial Class', '2. Hosted Class', '3. Referral (free)', '4. Paid First Visit'],
    default='5. Other')
bsx = b[b['cohort'] == pd.Timestamp('2026-09-01')].copy()
bsx['channel'] = np.select(
    [bsx['Is New'].eq('New - Trial Class'),
     bsx['Is New'].eq('New - Hosted Class'),
     bsx['Is New'].eq('New - Referral Class'),
     bsx['Is New'].eq('New - Paid First Visit')],
    ['1. Free Trial Class', '2. Hosted Class', '3. Referral (free)', '4. Paid First Visit'],
    default='5. Other')
t = bx.groupby('channel').agg(n=('Member Id','count'), conv=('converted','sum'),
                              rev=('revenue','sum'), second=('days_2nd', lambda s: s.notna().sum()))
t['conv_%'] = (t['conv']/t['n']*100).round(1)
t['second_%'] = (t['second']/t['n']*100).round(1)
t['arpu'] = (t['rev']/t['n']).round(0)
print(t.sort_index().to_string())

print()
print('SAME SEGMENTATION, HISTORICAL BENCHMARK (Bandra, cohorts Oct-25..Aug-26, >=30 obs days):')
hist = b[(b['cohort'] >= '2025-10-01') & (b['cohort'] <= '2026-08-31') & (b['obs_days'] >= 30)].copy()
hist['channel'] = np.select(
    [hist['Is New'].eq('New - Trial Class'),
     hist['Is New'].eq('New - Hosted Class'),
     hist['Is New'].eq('New - Referral Class'),
     hist['Is New'].eq('New - Paid First Visit')],
    ['1. Free Trial Class', '2. Hosted Class', '3. Referral (free)', '4. Paid First Visit'],
    default='5. Other')
h = hist.groupby('channel').agg(n=('Member Id','count'), conv=('converted','sum'),
                                rev=('revenue','sum'), second=('days_2nd', lambda s: (s<=30).sum()))
h['conv_%'] = (h['conv']/h['n']*100).round(1)
h['second30_%'] = (h['second']/h['n']*100).round(1)
h['arpu'] = (h['rev']/h['n']).round(0)
print(h.sort_index().to_string())

print()
print('=' * 110)
print('D. TRAINER DEEP DIVE — Sept 2026 Bandra first-class trainer')
print('=' * 110)
tr = bx.groupby(bx['Trainer Name'].fillna('(unassigned)')).agg(
    n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
    second=('days_2nd', lambda s: s.notna().sum()),
    ret=('Retention Status', lambda s: (s=='Retained').sum()))
tr['conv_%']=(tr['conv']/tr['n']*100).round(1)
tr['second_%']=(tr['second']/tr['n']*100).round(1)
tr['arpu']=(tr['rev']/tr['n']).round(0)
tr['ret_%']=(tr['ret']/tr['n']*100).round(1)
print(tr.sort_values('n', ascending=False).to_string())
print()
print('Historical trainer benchmark (Bandra, Oct-25..Aug-26, >=30 obs):')
htr = hist.groupby(hist['Trainer Name'].fillna('(unassigned)')).agg(
    n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
    second=('days_2nd', lambda s: (s<=30).sum()))
htr['conv_%']=(htr['conv']/htr['n']*100).round(1)
htr['second30_%']=(htr['second']/htr['n']*100).round(1)
htr['arpu']=(htr['rev']/htr['n']).round(0)
print(htr[htr['n']>=8].sort_values('conv_%', ascending=False).to_string())

print()
print('=' * 110)
print('E. WHAT CLASS IS THE FIRST VISIT? (Sept-26 Bandra)')
print('=' * 110)
ce = bx.groupby('First Visit Entity Name').agg(n=('Member Id','count'), conv=('converted','sum'),
        rev=('revenue','sum'), second=('days_2nd', lambda s: s.notna().sum()))
ce['conv_%']=(ce['conv']/ce['n']*100).round(1)
ce['second_%']=(ce['second']/ce['n']*100).round(1)
ce['arpu']=(ce['rev']/ce['n']).round(0)
print(ce.sort_values('n', ascending=False).to_string())

print()
print('=' * 110)
print('F. DAY-OF-WEEK & TIME SLOT (Sept-26 Bandra)')
print('=' * 110)
for col in ['First Visit Day','First Visit Time Slot']:
    t = bx.groupby(col).agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
                            second=('days_2nd', lambda s: s.notna().sum()))
    t['conv_%']=(t['conv']/t['n']*100).round(1)
    t['second_%']=(t['second']/t['n']*100).round(1)
    t['arpu']=(t['rev']/t['n']).round(0)
    print(f'--- {col} ---'); print(t.sort_values('n',ascending=False).to_string()); print()

print()
print('Historical benchmark by day-of-week (Bandra Oct-25..Aug-26, >=30obs):')
hd = hist.groupby('First Visit Day').agg(n=('Member Id','count'), conv=('converted','sum'))
hd['conv_%']=(hd['conv']/hd['n']*100).round(1)
print(hd.sort_values('conv_%',ascending=False).to_string())
