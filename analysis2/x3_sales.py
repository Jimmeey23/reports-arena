import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 70)

S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
def _n(col):
    return pd.to_numeric(S[col].astype(str).str.replace(r'[,\s]', '', regex=True), errors='coerce')
S['val'] = _n('Payment Value')
S['disc_amt'] = _n('Discount Value In Currency')
S['ym'] = S['dt'].dt.to_period('M')
B = S[S['Calculated Location'] == 'Supreme HQ, Bandra'].copy()

print('=' * 118)
print('A. BANDRA REVENUE LEDGER — monthly, all categories')
print('=' * 118)
g = B.groupby('ym').agg(txns=('Sale ID', 'size'), revenue=('val', 'sum'), members=('Member ID', 'nunique'))
g = g.loc['2025-01':'2026-10']
g['avg_txn'] = (g['revenue'] / g['txns']).round(0)
print(g.round(0).to_string())
print()
print('--- September, three years (Bandra) ---')
for yr in [2024, 2025, 2026]:
    x = B[(B['dt'] >= f'{yr}-09-01') & (B['dt'] < f'{yr}-10-01')]
    print(f'  Sept {yr}: txns={len(x):5d}  revenue=Rs {x["val"].sum():>12,.0f}  members={x["Member ID"].nunique():4d}  avg txn=Rs {x["val"].mean():>8,.0f}')

print()
print('=' * 118)
print('B. WHAT SEPTEMBER 2026 SOLD (Bandra) — category and product mix')
print('=' * 118)
s26 = B[(B['dt'] >= '2026-09-01') & (B['dt'] < '2026-10-01')]
cat = s26.groupby('Cleaned Category').agg(txns=('Sale ID', 'size'), revenue=('val', 'sum'))
cat['rev_%'] = (cat['revenue'] / cat['revenue'].sum() * 100).round(1)
cat['avg'] = (cat['revenue'] / cat['txns']).round(0)
print(cat.sort_values('revenue', ascending=False).to_string())
print()
print('Top products by revenue, Sept 2026:')
pr = s26.groupby('Cleaned Product').agg(txns=('Sale ID', 'size'), revenue=('val', 'sum'))
pr['avg'] = (pr['revenue'] / pr['txns']).round(0)
print(pr.sort_values('revenue', ascending=False).head(18).to_string())

print()
print('=' * 118)
print('C. NEWCOMERS 2 FOR 1 — the intro pack, by the numbers')
print('=' * 118)
nc = S[S['Cleaned Category'] == 'Newcomers Special']
print(f'Network lifetime: {len(nc)} sales, Rs {nc["val"].sum():,.0f}, avg Rs {nc["val"].mean():,.0f}')
ncb = nc[nc['Calculated Location'] == 'Supreme HQ, Bandra']
print(f'Bandra lifetime: {len(ncb)} sales, Rs {ncb["val"].sum():,.0f}')
ncb_m = ncb.groupby('ym').agg(sales=('Sale ID', 'size'), revenue=('val', 'sum'), members=('Member ID', 'nunique')).loc['2025-09':'2026-10']
print()
print('Bandra 2-for-1 monthly:')
print(ncb_m.round(0).to_string())
print()
print('Sept-2026 Bandra 2-for-1 sales:', len(ncb[ncb['ym'] == '2026-09']), '| revenue Rs', round(ncb[ncb['ym'] == '2026-09']['val'].sum()))
print()
print('Discounted?')
for lbl, d in [('Network', nc), ('Bandra', ncb)]:
    disc = d['disc_amt'].fillna(0)
    print(f'  {lbl}: avg discount Rs {disc.mean():,.0f} | % of txns with discount: {(disc>0).mean()*100:.1f}% | avg price Rs {d["val"].mean():,.0f}')

print()
print('=' * 118)
print('D. DISCOUNTING — how much is being given away at Bandra?')
print('=' * 118)
B['disc'] = B['disc_amt'].fillna(0)
dm = B.groupby('ym').agg(revenue=('val', 'sum'), discounts=('disc', 'sum'), txns=('Sale ID', 'size'))
dm = dm.loc['2025-09':'2026-10']
dm['disc_%_of_rev'] = (dm['discounts'] / (dm['revenue'] + dm['discounts']) * 100).round(1)
print(dm.round(0).to_string())
print()
print('Sept-2026 by category:')
d26 = s26.assign(disc=s26['disc_amt'].fillna(0))
print(d26.groupby('Cleaned Category').agg(txns=('Sale ID', 'size'), revenue=('val', 'sum'), discount=('disc', 'sum')).round(0).to_string())

print()
print('=' * 118)
print('E. WHO IS BUYING — first-time vs repeat buyers in Sept 2026')
print('=' * 118)
first_txn = B.groupby('Member ID')['dt'].min().dt.to_period('M')
s26m = s26.assign(is_first=s26['Member ID'].map(first_txn) == '2026-09')
print('Sept-26 Bandra transactions:', len(s26m))
print('  by buyers whose FIRST ever Bandra purchase was in Sept-26:', s26m['is_first'].sum(),
      f'(Rs {s26m[s26m["is_first"]]["val"].sum():,.0f})')
print('  by existing members:', (~s26m['is_first']).sum(), f'(Rs {s26m[~s26m["is_first"]]["val"].sum():,.0f})')

print()
print('=' * 118)
print('F. INTRO-OFFER TO MEMBERSHIP CONVERSION — the money question')
print('=' * 118)
# members who bought a Newcomers pack, then what did they buy next?
nc_members = set(ncb['Member ID'])
after = B[B['Member ID'].isin(nc_members)].sort_values(['Member ID', 'dt'])
rows = []
for mid, gg in after.groupby('Member ID'):
    if not (gg['Cleaned Category'] == 'Newcomers Special').any(): continue
    nc_rows = gg[gg['Cleaned Category'] == 'Newcomers Special']
    t0 = nc_rows['dt'].min()
    later = gg[(gg['dt'] > t0) & (gg['Cleaned Category'] != 'Newcomers Special')]
    rows.append({'mid': mid, 'bought_again': len(later) > 0,
                 'later_rev': later['val'].sum(),
                 'later_cat': later['Cleaned Category'].iloc[0] if len(later) else None})
r = pd.DataFrame(rows)
print(f'Bandra members who ever bought a Newcomers 2-for-1: {len(r)}')
print(f'  bought anything afterwards: {r["bought_again"].sum()} ({r["bought_again"].mean()*100:.1f}%)')
print(f'  revenue generated after the intro pack: Rs {r["later_rev"].sum():,.0f} (avg Rs {r["later_rev"].mean():,.0f} per member)')
print()
print('  what they bought next:')
print(r['later_cat'].value_counts().to_string())
