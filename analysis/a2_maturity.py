import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')

# ============================================================ MATURITY / TIME-TO-CONVERT
b = df[(df['First Visit Location'] == BANDRA) & (~df['is_import'])].copy()
b['obs_days'] = (SNAP - b['fvd']).dt.days
conv = b[b['converted']].copy()

print('=' * 95)
print('MATURITY CHECK — how long does conversion take at Bandra?  (all converted cohorts 2023-2026, n=%d)' % len(conv))
print('=' * 95)
print(conv['conv_span'].describe(percentiles=[.1,.25,.5,.6,.7,.75,.8,.9,.95]).round(1).to_string())
print()
for k in [7, 14, 30, 45, 60, 90]:
    print(f'   share of conversions that happen within {k:3d} days of first visit: {(conv["conv_span"] <= k).mean()*100:5.1f}%')

print()
print('Second-visit timing (days to 2nd visit), Bandra all cohorts:')
print(b['days_2nd'].describe(percentiles=[.25,.5,.75,.9]).round(1).to_string())
for k in [7, 14, 30, 45]:
    print(f'   share of members whose 2nd visit was within {k:3d} days: {(b["days_2nd"] <= k).mean()*100:5.1f}%  (of all members)')

# ============================================================ EQUAL-WINDOW CONVERSION RATES
print()
print('=' * 95)
print('EQUAL-OBSERVATION-WINDOW CONVERSION RATES — Bandra monthly cohorts')
print('(rate = converted within K days of first visit / cohort size, over members with >=K days observed)')
print('=' * 95)
rows = []
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if len(g) < 5: continue
    r = {'cohort': str(per), 'n': len(g)}
    for K in [30, 45, 60]:
        elig = g[g['obs_days'] >= K]
        if len(elig) >= 5:
            hit = (elig['converted'] & (elig['conv_span'] <= K)).sum()
            r[f'conv{K}'] = round(hit / len(elig) * 100, 1)
        else:
            r[f'conv{K}'] = np.nan
    rows.append(r)
eq = pd.DataFrame(rows)
print(eq.to_string(index=False))

# ============================================================ FUEL: second visit as leading indicator
print()
print('=' * 95)
print('SECOND-VISIT AS LEADING INDICATOR (Bandra, non-import, all cohorts)')
print('=' * 95)
b['had2'] = b['days_2nd'].notna()
tab = b.groupby('had2').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
                            visits=('No of Visits','mean'))
tab['conv_rate'] = (tab['conv']/tab['n']*100).round(1)
tab['arpu'] = (tab['rev']/tab['n']).round(0)
print(tab.to_string())

print()
print('Sept-2026 Bandra cohort: second-visit split')
bx = b[b['cohort'] == pd.Timestamp('2026-09-01')]
print(f'   had 2nd visit: {bx["days_2nd"].notna().sum()} of {len(bx)}  ({bx["days_2nd"].notna().mean()*100:.1f}%)')
print(f'   converted among 2nd-visit group : {bx.loc[bx["days_2nd"].notna(),"converted"].sum()}')
print(f'   converted among no-2nd-visit grp: {bx.loc[bx["days_2nd"].isna(),"converted"].sum()}')

# maturity of 2nd visits across cohorts
print()
print('2nd-visit attainment by cohort (members with >=30 days observed):')
rows=[]
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if len(g) < 5: continue
    elig = g[g['obs_days'] >= 30]
    if len(elig) < 5: continue
    rows.append({'cohort': str(per), 'n': len(elig),
                 'pct_2nd_visit': round(elig['days_2nd'].notna().mean()*100, 1),
                 'conv30': round((elig['converted'] & (elig['conv_span']<=30)).mean()*100, 1),
                 'avg_visits': round(elig['No of Visits'].mean(), 2)})
print(pd.DataFrame(rows).to_string(index=False))
