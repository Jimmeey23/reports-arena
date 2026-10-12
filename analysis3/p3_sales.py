import pandas as pd, numpy as np
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)

S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = pd.to_numeric(S['Payment Value'].astype(str).str.replace(r'[^0-9.\-]', '', regex=True), errors='coerce')
S['disc'] = pd.to_numeric(S['Discount Value In Currency'].astype(str).str.replace(r'[^0-9.\-]', '', regex=True), errors='coerce').fillna(0)
sb = S[S['Calculated Location'] == 'Supreme HQ, Bandra'].copy()
s26 = sb[(sb['dt'] >= '2026-09-01') & (sb['dt'] < '2026-10-01')]
s25 = sb[(sb['dt'] >= '2025-09-01') & (sb['dt'] < '2025-10-01')]
s24 = sb[(sb['dt'] >= '2024-09-01') & (sb['dt'] < '2024-10-01')]

print('=' * 110); print('A. ALL COLUMNS'); print('=' * 110)
for c in S.columns:
    print('  ', c, '|', S[c].dtype, '|', str(S[c].dropna().iloc[0])[:60] if S[c].notna().any() else 'ALL NULL')

print()
print('=' * 110); print('B. SEPTEMBER, THREE YEARS'); print('=' * 110)
rows = []
for y, d in [(2024, s24), (2025, s25), (2026, s26)]:
    rows.append(dict(year=y, txns=len(d), gross=d['val'].sum(), discounts=d['disc'].sum(),
                     net=d['val'].sum(), members=d['Member ID'].nunique(),
                     avg_txn=d['val'].mean(), median_txn=d['val'].median()))
print(pd.DataFrame(rows).round(0).to_string())

print()
print('=' * 110); print('C. PAYMENT METHOD / SOLD BY / PURCHASE TYPE, Sep-2026'); print('=' * 110)
for c in ['Payment Method', 'Purchase Type', 'Sold By', 'Sec. Membership']:
    if c in s26.columns:
        print(f'--- {c} ---')
        print(s26.groupby(c).agg(txns=('Sale ID', 'size'), revenue=('val', 'sum')).sort_values('revenue', ascending=False).head(12).to_string())
        print()

print('=' * 110); print('D. PRODUCT MIX — Sep-2026 vs Sep-2025'); print('=' * 110)
p26 = s26.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
p25 = s25.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), rev=('val', 'sum'))
j = p26.join(p25, lsuffix='_26', rsuffix='_25', how='outer').fillna(0)
j['d_rev'] = j['rev_26'] - j['rev_25']
j['avg_26'] = (j['rev_26'] / j['n_26'].replace(0, np.nan)).round(0)
print(j.sort_values('rev_26', ascending=False).round(0).to_string())

print()
print('=' * 110); print('E. DISCOUNTS, Sep-2026 detail'); print('=' * 110)
d26 = s26[s26['disc'] > 0]
print(f'  transactions with a discount: {len(d26)} of {len(s26)} ({len(d26)/len(s26)*100:.0f}%)')
print(f'  total discount given: Rs {s26["disc"].sum():,.0f}')
if len(d26):
    print(d26.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), discount=('disc', 'sum'), rev=('val', 'sum')).to_string())

print()
print('=' * 110); print('F. WHO PAID — new vs existing, Sep-2026'); print('=' * 110)
first = sb.groupby('Member ID')['dt'].min().dt.to_period('M')
s26m = s26.assign(first_period=s26['Member ID'].map(first))
print(s26m.groupby(s26m['first_period'] == '2026-09').agg(txns=('Sale ID', 'size'), rev=('val', 'sum'),
      members=('Member ID', 'nunique')).to_string())
print()
print('  Sept-26 sales by whether it is the member\'s first-ever Bandra purchase:')
print(f'   new-member purchases: {s26m[s26m["first_period"]=="2026-09"]["val"].sum():,.0f}')
print(f'   existing-member purchases: {s26m[s26m["first_period"]!="2026-09"]["val"].sum():,.0f}')

print()
print('=' * 110); print('G. TRANSACTION SIZE DISTRIBUTION, Sep-2026'); print('=' * 110)
bins = [0, 2000, 5000, 10000, 20000, 50000, 10**9]
labs = ['<2k', '2-5k', '5-10k', '10-20k', '20-50k', '50k+']
s26b = s26.assign(band=pd.cut(s26['val'], bins=bins, labels=labs))
print(s26b.groupby('band', observed=True).agg(n=('Sale ID', 'size'), rev=('val', 'sum')).assign(
      pct=lambda d: (d['rev']/d['rev'].sum()*100).round(1)).to_string())

print()
print('=' * 110); print('H. RETAIL, Sep-2026'); print('=' * 110)
r = s26[s26['Cleaned Category'] == 'Retail']
print(r.groupby('Cleaned Product').agg(n=('Sale ID', 'size'), rev=('val', 'sum')).sort_values('rev', ascending=False).to_string())
print(f'  retail total Rs {r["val"].sum():,.0f} across {len(r)} txns, {r["Member ID"].nunique()} members')

print()
print('=' * 110); print('I. PRICE PER CLASS BY PACKAGE SIZE, Sep-2026'); print('=' * 110)
for prod, n_cls in [('Studio Single Class', 1), ('Studio Newcomers 2 For 1', 2), ('Studio 4 Class Package', 4),
                    ('Studio 8 Class Package', 8), ('Studio 10 Class Package', 10), ('Studio 12 Class Package', 12),
                    ('Studio 20 Single Class Package', 20)]:
    d = s26[s26['Cleaned Product'] == prod]
    if len(d):
        print(f'  {prod:34s} n={len(d):3d} avg Rs {d["val"].mean():>9,.0f} per-class Rs {d["val"].mean()/n_cls:>8,.0f}')

print()
print('=' * 110); print('J. MEMBERSHIP vs PACKAGE vs SINGLE — trend by month (Bandra)'); print('=' * 110)
sb2 = sb[(sb['dt'] >= '2025-01-01') & (sb['dt'] < '2026-10-01')]
t = sb2.groupby([sb2['dt'].dt.to_period('M'), 'Cleaned Category'])['val'].sum().unstack(fill_value=0)
print(t.round(0).to_string())
