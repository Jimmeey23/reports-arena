import pandas as pd, numpy as np, json
from prep import load

pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 60)
df = load()
SEP26 = pd.Timestamp('2026-09-01')
SEP25 = pd.Timestamp('2025-09-01')
BANDRA = 'Supreme HQ, Bandra'

out = {}

# ---------------------------------------------------------------- 1. NETWORK + BANDRA ACQUISITION TREND
bandra = df[df['bandra_fv']].copy()
net = df[~df['is_import']].copy()

def cohort_counts(d, studio_col, studio):
    x = d[d[studio_col] == studio] if studio else d
    g = x.groupby(x['cohort'].dt.to_period('M')).agg(
        new_clients=('Member Id', 'count'),
        converted=('converted', 'sum'),
        revenue=('revenue', 'sum'),
    )
    g['conv_rate'] = (g['converted'] / g['new_clients'] * 100).round(1)
    return g

print('=' * 90)
print('1. MONTHLY NEW-CLIENT ACQUISITION — SUPREME HQ BANDRA (first-visit location)')
print('=' * 90)
bt = cohort_counts(df, 'First Visit Location', BANDRA)
print(bt.loc['2025-09':'2026-10'])

print()
print('Network totals (all studios, non-import) by month, 2026:')
nt = cohort_counts(df, None, None)
print(nt.loc['2026-01':'2026-10'])

print()
print('Sept-2026 vs Sept-2025 vs Aug-2026, by studio:')
for st in [BANDRA, 'Kwality House, Kemps Corner', 'Kenkere House', 'Pop-up', 'Plash Pilates']:
    a = cohort_counts(df, 'First Visit Location', st)
    def get(t):
        return int(a.loc[t, 'new_clients']) if t in a.index else 0
    print(f'  {st:32s} Sep25={get("2025-09"):4d}  Aug26={get("2026-08"):4d}  Sep26={get("2026-09"):4d}')

# ---------------------------------------------------------------- 2. SEPT-26 BANDRA COHORT DEEP DIVE
print()
print('=' * 90)
print('2. SEPT-2026 BANDRA COHORT — CONVERSION FUNNEL & ECONOMICS')
print('=' * 90)

def cohort_profile(d, studio, month):
    x = d[(d['First Visit Location'] == studio) & (d['cohort'] == month)].copy()
    n = len(x)
    conv = x['converted'].sum()
    paid = (x['Purchase Count Post Trial'] > 0).sum()
    rev = x['revenue'].sum()
    prof = dict(
        n=n, converted=int(conv), conv_rate=round(conv/n*100, 1) if n else 0,
        paid_first_visit=(x['Is New'] == 'New - Paid First Visit').sum(),
        bought=int(paid), rev=rev, arpu=round(rev/n, 0) if n else 0,
        rev_per_converter=round(rev/conv, 0) if conv else 0,
        avg_first_pv=round(x.loc[x['first_pv'] > 0, 'first_pv'].mean(), 0) if (x['first_pv'] > 0).any() else 0,
        median_conv_span=x['conv_span'].median(),
        avg_conv_span=x['conv_span'].mean(),
        avg_days_2nd=x['days_2nd'].mean(),
        pct_2nd_visit=(x['days_2nd'].notna()).mean() * 100,
        avg_visits=x['No of Visits'].mean(),
        avg_visits_pt=x['Visits Post Trial'].mean(),
        retained=(x['Retention Status'] == 'Retained').sum(),
        ret_rate=round((x['Retention Status'] == 'Retained').mean() * 100, 1),
        late_cancel=x['latecancel'].mean() * 100,
    )
    return x, prof

bx, bp = cohort_profile(df, BANDRA, SEP26)
print('SEPT-2026 @ BANDRA:')
for k, v in bp.items():
    print(f'   {k:22s} {v}')

print()
print('--- comparison cohorts (same studio & month structure) ---')
rows = []
for studio, month, lbl in [
    (BANDRA, SEP26, 'Bandra Sep-26'),
    (BANDRA, pd.Timestamp('2026-08-01'), 'Bandra Aug-26'),
    (BANDRA, pd.Timestamp('2026-07-01'), 'Bandra Jul-26'),
    (BANDRA, SEP25, 'Bandra Sep-25'),
    ('Kwality House, Kemps Corner', SEP26, 'Kemps Sep-26'),
    ('Kenkere House', SEP26, 'Kenkere Sep-26'),
]:
    _, p = cohort_profile(df, studio, month)
    p['label'] = lbl
    rows.append(p)
cmp = pd.DataFrame(rows).set_index('label')
print(cmp[['n', 'converted', 'conv_rate', 'rev', 'arpu', 'rev_per_converter', 'avg_first_pv',
           'median_conv_span', 'avg_days_2nd', 'pct_2nd_visit', 'avg_visits', 'ret_rate']].round(1).to_string())

bx.to_csv('/home/user/analysis/bandra_sep26_cohort.csv', index=False)

# ---------------------------------------------------------------- 3. CONVERSION SPEED + FUNNEL STAGES
print()
print('=' * 90)
print('3. CONVERSION SPEED & FUNNEL — BANDRA SEP-26 (n=%d)' % bp['n'])
print('=' * 90)
print('Conversion Speed Bucket:')
cs = bx['Conversion Speed Bucket'].value_counts()
print((cs.to_frame('n').assign(pct=(cs/len(bx)*100).round(1))).to_string())
print()
print('Conversion span distribution (converters only, days):')
print(bx.loc[bx['converted'], 'conv_span'].describe().round(1).to_string())
print()
print('Source of new clients (Bandra Sep-26):')
src = bx['Source'].fillna('(unattributed)').value_counts()
sdf = src.to_frame('clients')
sdf['conv'] = bx.groupby(bx['Source'].fillna('(unattributed)'))['converted'].sum()
sdf['conv_rate'] = (sdf['conv'] / sdf['clients'] * 100).round(1)
sdf['revenue'] = bx.groupby(bx['Source'].fillna('(unattributed)'))['revenue'].sum()
sdf['arpu'] = (sdf['revenue'] / sdf['clients']).round(0)
print(sdf.to_string())
print()
print('Is New (entry type):')
e = bx.groupby('Is New').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
e['conv_rate'] = (e['conv']/e['n']*100).round(1); e['arpu']=(e['rev']/e['n']).round(0)
print(e.sort_values('n', ascending=False).to_string())
print()
print('Time slot / day of week:')
for col in ['First Visit Time Slot','First Visit Day']:
    t = bx.groupby(col).agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
    t['conv_rate']=(t['conv']/t['n']*100).round(1); t['arpu']=(t['rev']/t['n']).round(0)
    print(f'--- {col} ---'); print(t.sort_values('n',ascending=False).to_string()); print()
print('Trainer (first class) — Bandra Sep-26:')
tr = bx.groupby(bx['Trainer Name'].fillna('(none/unassigned)')).agg(
    n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
    ret=('Retention Status', lambda s:(s=='Retained').sum()))
tr['conv_rate']=(tr['conv']/tr['n']*100).round(1)
tr['arpu']=(tr['rev']/tr['n']).round(0)
tr['ret_rate']=(tr['ret']/tr['n']*100).round(1)
print(tr.sort_values('n',ascending=False).to_string())
print()
print('First-visit class entity (which class/product):')
ce = bx.groupby('First Visit Entity Name').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
ce['conv_rate']=(ce['conv']/ce['n']*100).round(1); ce['arpu']=(ce['rev']/ce['n']).round(0)
print(ce.sort_values('n',ascending=False).to_string())
print()
print('Payment method on first visit:')
pm = bx.groupby('Payment Method').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
pm['conv_rate']=(pm['conv']/pm['n']*100).round(1); pm['arpu']=(pm['rev']/pm['n']).round(0)
print(pm.sort_values('n',ascending=False).to_string())
