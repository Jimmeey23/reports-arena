import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')

b = df[(df['First Visit Location'] == BANDRA) & (~df['is_import'])].copy()
b['obs_days'] = (SNAP - b['fvd']).dt.days

# ---- STRICT apples-to-apples: every cohort restricted to first visits on days 1-11 of the month
#      => every member has >=30 days of observation as of the 11-Oct-2026 snapshot
print('=' * 110)
print('STRICT EQUAL-WINDOW ANALYSIS — Bandra cohorts, first visits restricted to day 1-11 of each month')
print('(guarantees >=30 observed days for every member, so Sept-2026 is fully comparable)')
print('=' * 110)
rows = []
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    g = g[g['fvd'].dt.day <= 11]
    if len(g) < 8: continue
    rows.append({
        'cohort': str(per), 'n': len(g),
        'conv30d_%': round((g['converted'] & (g['conv_span'] <= 30)).mean() * 100, 1),
        '2nd_visit_30d_%': round((g['days_2nd'] <= 30).mean() * 100, 1),
        'avg_visits': round(g['No of Visits'].mean(), 2),
        'retained_%': round((g['Retention Status'] == 'Retained').mean() * 100, 1),
        'late_cancel_%': round(g['latecancel'].mean() * 100, 1),
    })
eq = pd.DataFrame(rows)
print(eq.to_string(index=False))

print()
recent = eq[eq['cohort'] >= '2025-09']
print('--- trailing-12-month (Oct-25 .. Sep-26) baseline vs Sep-26 ---')
base = eq[(eq['cohort'] >= '2025-10') & (eq['cohort'] <= '2026-08')]
sep = eq[eq['cohort'] == '2026-09'].iloc[0]
for col in ['conv30d_%', '2nd_visit_30d_%', 'avg_visits', 'retained_%', 'late_cancel_%']:
    m, s = base[col].mean(), sep[col]
    print(f'   {col:18s} trailing-12m avg = {m:6.2f} | Sep-26 = {s:6.2f} | delta = {s-m:+6.2f}')

print()
print('Sep-26 percentile rank vs all cohorts since 2024:')
for col in ['conv30d_%', '2nd_visit_30d_%', 'avg_visits', 'retained_%', 'late_cancel_%']:
    pct = (eq[col] <= sep[col]).mean() * 100
    print(f'   {col:18s} Sep-26 sits at the {pct:4.0f}th percentile of {len(eq)} cohorts')

# ---- NETWORK BENCHMARK on the same strict basis
print()
print('=' * 110)
print('NETWORK (all studios) on the same strict day-1-11 basis')
print('=' * 110)
nn = df[~df['is_import']].copy()
rows = []
for per, g in nn.groupby(nn['cohort'].dt.to_period('M')):
    g = g[g['fvd'].dt.day <= 11]
    if len(g) < 10: continue
    rows.append({'cohort': str(per), 'n': len(g),
                 'conv30d_%': round((g['converted'] & (g['conv_span'] <= 30)).mean()*100, 1),
                 '2nd_visit_30d_%': round((g['days_2nd'] <= 30).mean()*100, 1)})
neq = pd.DataFrame(rows)
print(neq.tail(15).to_string(index=False))

# ---- Bandra share of network
print()
print('=' * 110)
print('BANDRA SHARE OF NETWORK ACQUISITION')
print('=' * 110)
tot = nn.groupby(nn['cohort'].dt.to_period('M')).size()
bd = nn[nn['First Visit Location'] == BANDRA].groupby(nn['cohort'].dt.to_period('M')).size()
share = (bd / tot * 100).round(1)
z = pd.DataFrame({'network_new': tot, 'bandra_new': bd, 'bandra_share_%': share}).loc['2025-09':'2026-09']
print(z.to_string())

# ---- VOLUME vs QUALITY quadrant
print()
print('=' * 110)
print('VOLUME vs QUALITY — Bandra: is rising volume diluting quality?')
print('=' * 110)
rows = []
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if len(g) < 15: continue
    g = g.copy()
    rows.append({'cohort': str(per), 'vol': len(g),
                 'pct_2nd': round((g['days_2nd'].notna()).mean()*100, 1),
                 'conv_rate': round(g['converted'].mean()*100, 1),
                 'arpu': round(g['revenue'].mean(), 0),
                 'rev_total': int(g['revenue'].sum())})
q = pd.DataFrame(rows)
q['vol_rank'] = q['vol'].rank(ascending=False).astype(int)
print(q.tail(20).to_string(index=False))
print()
print('Correlation (Bandra cohorts since 2024, n=%d): volume vs conversion rate = %.3f | volume vs ARPU = %.3f'
      % (len(q), q['vol'].corr(q['conv_rate']), q['vol'].corr(q['arpu'])))
