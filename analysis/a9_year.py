import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 280); pd.set_option('display.max_columns', 90)
df = load()
BANDRA = 'Supreme HQ, Bandra'; SNAP = pd.Timestamp('2026-10-11')
nn = df[~df['is_import']].copy()
b = nn[nn['First Visit Location'] == BANDRA].copy()
for _d in (b, nn): _d['obs'] = (SNAP - _d['fvd']).dt.days

print('#' * 118)
print('# 1. THE YEAR AS A WHOLE — trailing twelve months, three consecutive years (equal-observation basis)')
print('#' * 118)
def ttm(d, start, end):
    g = d[(d['fvd'] >= start) & (d['fvd'] < end)]
    e = g[g['obs'] >= 30]                      # only members with a full 30-day window observed
    return dict(
        clients=len(g),
        observed=len(e),
        conv30=round((e['converted'] & (e['conv_span'] <= 30)).mean()*100, 1) if len(e) else np.nan,
        conv_all=round(g['converted'].mean()*100, 1),
        second30=round((e['days_2nd'] <= 30).mean()*100, 1) if len(e) else np.nan,
        second_all=round(g['days_2nd'].notna().mean()*100, 1),
        arpu=round(g['revenue'].mean()),
        rev=int(g['revenue'].sum()),
        visits=round(g['No of Visits'].mean(), 2),
        rev_per_90d=round(g.loc[g['converted'] & (g['conv_span'] <= 90), 'first_pv'].sum() / max(len(g[g['obs'] >= 90]), 1)),
    )
rows = []
for lbl, s, e in [('TTM Oct23-Sep24','2023-10-01','2024-10-01'),
                  ('TTM Oct24-Sep25','2024-10-01','2025-10-01'),
                  ('TTM Oct25-Sep26','2025-10-01','2026-10-01')]:
    r = ttm(b, s, e); r['window'] = lbl; rows.append(r)
t = pd.DataFrame(rows).set_index('window')
print(t.to_string())

print()
print('--- Network for comparison ---')
rows = []
for lbl, s, e in [('TTM Oct24-Sep25','2024-10-01','2025-10-01'), ('TTM Oct25-Sep26','2025-10-01','2026-10-01')]:
    r = ttm(nn, s, e); r['window'] = lbl; rows.append(r)
print(pd.DataFrame(rows).set_index('window').to_string())

print()
print('#' * 118)
print('# 2. YEAR TO DATE — 2026 vs 2025, month by month (same months, equal observation)')
print('#' * 118)
rows = []
for mo in range(1, 10):
    r = {'month': pd.Timestamp(2026, mo, 1).strftime('%b')}
    for yr in [2025, 2026]:
        g = b[(b['fvd'] >= f'{yr}-{mo:02d}-01') & (b['fvd'] < (pd.Timestamp(yr, mo, 1) + pd.offsets.MonthEnd(1)).strftime('%Y-%m-%d'))]
        e = g[g['obs'] >= 30]
        r[f'n_{yr}'] = len(g)
        r[f'conv30_{yr}'] = round((e['converted'] & (e['conv_span'] <= 30)).mean()*100, 1) if len(e) >= 8 else np.nan
        r[f'2nd30_{yr}'] = round((e['days_2nd'] <= 30).mean()*100, 1) if len(e) >= 8 else np.nan
    rows.append(r)
ytd = pd.DataFrame(rows)
print(ytd.to_string(index=False))
print()
jn = ytd[ytd['month'].isin(['Jan','Feb','Mar','Apr','May','Jun'])]
print('Jan-Jun averages:')
for c in ['n', 'conv30', '2nd30']:
    line = []
    for yr in [2025, 2026]:
        col = c + '_' + str(yr)
        line.append(f'{col}={jn[col].mean():.1f}')
    print('   ' + '   '.join(line))

print()
print('#' * 118)
print('# 3. CONTRIBUTION ANALYSIS — how much of the September gap came from specific intake blocks')
print('#' * 118)
mw = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01') & (b['fvd'].dt.day <= 13)]
baseline = 0.1925
blocks = {
 'Sep 1-11  (n=%d)' % len(mw[mw['fvd'].dt.day <= 11]): mw[mw['fvd'].dt.day <= 11],
 'Sep 12-13 (n=%d)' % len(mw[mw['fvd'].dt.day >= 12]): mw[mw['fvd'].dt.day >= 12],
}
tot_gap = len(mw)*baseline - mw['converted'].sum()
print(f'Matched window n={len(mw)}  actual converters={mw["converted"].sum()}  expected at baseline={len(mw)*baseline:.1f}  TOTAL GAP={tot_gap:.1f}')
for k, g in blocks.items():
    gap = len(g)*baseline - g['converted'].sum()
    print(f'   {k}: expected {len(g)*baseline:.1f}, actual {g["converted"].sum()}, gap {gap:.1f}  -> {gap/tot_gap*100:.0f}% of total gap')

print()
print('--- 2nd-visit contribution ---')
tot2 = len(mw)*0.3775 - mw['days_2nd'].notna().sum()
print(f'Matched window 2nd visits: actual={mw["days_2nd"].notna().sum()}  expected={len(mw)*0.3775:.1f}  GAP={tot2:.1f}')
for k, g in blocks.items():
    gap2 = len(g)*0.3775 - g['days_2nd'].notna().sum()
    print(f'   {k}: expected {len(g)*0.3775:.1f}, actual {g["days_2nd"].notna().sum()}, gap {gap2:.1f}  -> {gap2/tot2*100:.0f}% of total gap')

print()
print('#' * 118)
print('# 4. WHAT IS WORKING — the positives, quantified')
print('#' * 118)
sep = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01')]
hist = b[(b['fvd'] >= '2025-10-01') & (b['fvd'] < '2026-09-01')]

print('a) Barre 57 remained the engine:')
for lbl, d in [('Sep-26', sep), ('prior 11m', hist)]:
    g = d[d['First Visit Entity Name'].str.contains('Barre 57', na=False)]
    print(f'   {lbl}: n={len(g)} conv={g["converted"].sum()} ({g["converted"].mean()*100:.1f}%) rev=Rs {g["revenue"].sum():,.0f} ({g["revenue"].sum()/d["revenue"].sum()*100:.0f}% of month)')

print()
print('b) Conversion speed is excellent — September converters moved FAST:')
conv_sep = sep[sep['converted']]
print(f'   median days to convert: {conv_sep["conv_span"].median():.0f} (all-time Bandra median 8)')
print(f'   within 7 days: {(conv_sep["conv_span"]<=7).mean()*100:.0f}%')

print()
print('c) Paid-entry clients are the highest-value cohort:')
for lbl, d in [('Sep-26', sep), ('prior 11m', hist)]:
    g = d[d['Is New'] == 'New - Paid First Visit']
    print(f'   {lbl}: n={len(g)} conv={g["converted"].mean()*100:.1f}% ARPU=Rs {g["revenue"].mean():,.0f}')

print()
print('d) Strong individual performances in September:')
tt = sep[sep['Trainer Name'].notna()].groupby('Trainer Name').agg(n=('Member Id','size'), conv=('converted','sum'), second=('days_2nd', lambda s: s.notna().sum()), rev=('revenue','sum'))
tt['2nd_%'] = tt['second']/tt['n']*100; tt['arpu'] = tt['rev']/tt['n']
tt = tt[(tt['n'] >= 6) & ((tt['2nd_%'] > 30) | (tt['conv'] >= 2))]
print(tt.sort_values('2nd_%', ascending=False).to_string())

print()
print('e) Network position strengthening:')
for lbl, d in [('Sep-25', b[(b['fvd']>='2025-09-01')&(b['fvd']<'2025-10-01')]), ('Sep-26', sep)]:
    tot = nn[(nn['fvd'] >= ('2025-09-01' if lbl=='Sep-25' else '2026-09-01')) & (nn['fvd'] < ('2025-10-01' if lbl=='Sep-25' else '2026-10-01'))]
    print(f'   {lbl}: Bandra {len(d)} of network {len(tot)} = {len(d)/len(tot)*100:.1f}%')

print()
print('#' * 118)
print('# 5. PRICING CHECK — did Sept converters buy smaller packages?')
print('#' * 118)
print('Median FIRST purchase value, converters by month:')
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if str(per) < '2025-10': continue
    cv = g[g['converted']]
    if len(cv) < 5: continue
    print(f'   {per}: n={len(cv):3d}  median first purchase Rs {cv["first_pv"].median():>9,.0f}   mean Rs {cv["first_pv"].mean():>9,.0f}')
print()
print('Package mix shift (Sept-26 converters vs prior 11m):')
for lbl, d in [('Sep-26', sep), ('prior 11m', hist)]:
    cv = d[d['converted']]
    pk = cv['First Purchase Post Trial'].astype(str).str.strip().value_counts(normalize=True).head(5)*100
    print(f'   --- {lbl} ---'); print(pk.round(1).to_string())
