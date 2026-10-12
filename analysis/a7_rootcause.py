import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')
nn = df[~df['is_import']].copy()
b = nn[nn['First Visit Location'] == BANDRA].copy()
b['obs'] = (SNAP - b['fvd']).dt.days

# ---------- MATCHED WINDOW: day 1-13 of month, >=30 days observed ----------
print('=' * 110)
print('1. MATCHED WINDOW (first visits on days 1-13, all with >=28 days observed) — Bandra')
print('=' * 110)
rows = []
for yr, mo in [(2025,7),(2025,8),(2025,9),(2025,10),(2025,11),(2025,12),(2026,1),(2026,2),(2026,3),
               (2026,4),(2026,5),(2026,6),(2026,7),(2026,8),(2026,9)]:
    s = pd.Timestamp(yr, mo, 1); e = pd.Timestamp(yr + (mo == 12), (mo % 12) + 1, 1)
    g = b[(b['fvd'] >= s) & (b['fvd'] < e) & (b['fvd'].dt.day <= 13)]
    if len(g) < 10: continue
    rows.append({'cohort': f'{yr}-{mo:02d}', 'n': len(g),
                 'conv_%': round(g['converted'].mean()*100, 1),
                 '2nd_%': round(g['days_2nd'].notna().mean()*100, 1),
                 'visits': round(g['No of Visits'].mean(), 2),
                 'arpu': int(g['revenue'].mean()),
                 'rev': int(g['revenue'].sum())})
m = pd.DataFrame(rows)
print(m.to_string(index=False))
print()
base = m[(m['cohort'] >= '2025-10') & (m['cohort'] <= '2026-08')]
sep = m[m['cohort'] == '2026-09'].iloc[0]
print('Trailing-11m baseline vs Sep-26 (matched window):')
for c in ['n','conv_%','2nd_%','visits','arpu']:
    print(f'   {c:8s} base={base[c].mean():8.2f}   Sep26={sep[c]:8.2f}   delta={sep[c]-base[c].mean():+8.2f}')

# ---------- FREE TRIAL MICRO-ANALYSIS ----------
print()
print('=' * 110)
print('2. FREE-TRIAL FUNNEL: what broke inside the trial class?')
print('=' * 110)
ft = b[b['Is New'] == 'New - Trial Class'].copy()
rows = []
for per, g in ft.groupby(ft['cohort'].dt.to_period('M')):
    if len(g) < 12: continue
    rows.append({'cohort': str(per), 'n': len(g), 'conv_%': round(g['converted'].mean()*100,1),
                 '2nd_%': round(g['days_2nd'].notna().mean()*100,1),
                 'avg_visits': round(g['No of Visits'].mean(),2),
                 'late_cancel_%': round(g['latecancel'].mean()*100,1),
                 'arpu': int(g['revenue'].mean())})
print(pd.DataFrame(rows).tail(14).to_string(index=False))

print()
print('Free-trial Sept-2026 breakdown by trainer:')
sft = ft[ft['cohort'] == pd.Timestamp('2026-09-01')]
tt = sft.groupby(sft['Trainer Name'].fillna('(none)')).agg(n=('Member Id','count'), conv=('converted','sum'),
        second=('days_2nd', lambda x: x.notna().sum()), rev=('revenue','sum'))
tt['2nd_%'] = (tt['second']/tt['n']*100).round(1); tt['arpu']=(tt['rev']/tt['n']).round(0)
print(tt.sort_values('n',ascending=False).to_string())

print()
print('Free-trial Sept-2026 by day of week:')
dd = sft.groupby('First Visit Day').agg(n=('Member Id','count'), conv=('converted','sum'),
        second=('days_2nd', lambda x: x.notna().sum()))
dd['2nd_%'] = (dd['second']/dd['n']*100).round(1)
print(dd.sort_values('n',ascending=False).to_string())

# ---------- RESHMA SHARMA ----------
print()
print('=' * 110)
print('3. RESHMA SHARMA — is the Sept anomaly new?')
print('=' * 110)
rs = b[b['Trainer Name'] == 'Reshma Sharma'].copy()
rg = rs.groupby(rs['cohort'].dt.to_period('M')).agg(n=('Member Id','count'), conv=('converted','sum'),
        second=('days_2nd', lambda x: x.notna().sum()), rev=('revenue','sum'))
rg['conv_%']=(rg['conv']/rg['n']*100).round(1); rg['2nd_%']=(rg['second']/rg['n']*100).round(1)
rg['arpu']=(rg['rev']/rg['n']).round(0)
print('All months with >=5 clients:')
print(rg[rg['n']>=5].tail(20).to_string())
print()
print('All-time Reshma (n=%d): conv%%=%.1f  second%%=%.1f  arpu=Rs %,.0f'.replace(',.0f','.0f') % (
    len(rs), rs['converted'].mean()*100, rs['days_2nd'].notna().mean()*100, rs['revenue'].mean()))
print()
sep_rs = rs[rs['cohort'] == pd.Timestamp('2026-09-01')]
print('Sept-2026 Reshma (n=%d):' % len(sep_rs))
print('  entity:', sep_rs['First Visit Entity Name'].value_counts().to_dict())
print('  day:', sep_rs['First Visit Day'].value_counts().to_dict())
print('  slot:', sep_rs['First Visit Time Slot'].value_counts().to_dict())
print('  Is New:', sep_rs['Is New'].value_counts().to_dict())
print('  Source:', sep_rs['Source'].fillna('(unattr)').value_counts().to_dict())
print('  Membership Used:', sep_rs['Membership Used'].fillna('(none)').value_counts().head(6).to_dict())
print('  avg No of Visits: %.2f | conv=%d | 2nd=%d' % (sep_rs['No of Visits'].mean(), sep_rs['converted'].sum(), sep_rs['days_2nd'].notna().sum()))

print()
print('Compare: Reshma Sept-2025 (if any) and Aug-2026:')
for per in ['2025-09','2026-07','2026-08','2026-09']:
    g = rs[rs['cohort'].dt.to_period('M').astype(str) == per]
    if len(g): print(f'   {per}: n={len(g):3d} conv={g["converted"].sum():2d} 2nd={g["days_2nd"].notna().sum():2d} visits={g["No of Visits"].mean():.2f} rev=Rs {g["revenue"].sum():,.0f}')

# ---------- CLASS FORMAT MIX ----------
print()
print('=' * 110)
print('4. FORMAT MIX SHIFT at Bandra (share of first visits by class family)')
print('=' * 110)
def fam(s):
    s = str(s).strip()
    if 'Hosted' in s: return 'Hosted/Partner event'
    if s.startswith('powerCycle'): return 'powerCycle'
    if 'Barre' in s: return 'Barre 57'
    if 'Mat 57' in s: return 'Mat 57'
    if 'FIT' in s: return 'Studio FIT'
    return 'Other'
b['fam'] = b['First Visit Entity Name'].apply(fam)
rows=[]
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if len(g) < 20: continue
    sh = g['fam'].value_counts(normalize=True)*100
    rows.append({'cohort': str(per), 'n': len(g),
                 'Barre%': round(sh.get('Barre 57',0),1), 'Hosted%': round(sh.get('Hosted/Partner event',0),1),
                 'powerCycle%': round(sh.get('powerCycle',0),1), 'Mat57%': round(sh.get('Mat 57',0),1),
                 'FIT%': round(sh.get('Studio FIT',0),1)})
print(pd.DataFrame(rows).tail(14).to_string(index=False))
print()
print('Conversion rate by format family, Bandra, historical vs Sep-26:')
for lbl, d in [('Oct25-Aug26', b[(b['cohort']>='2025-10-01')&(b['cohort']<='2026-08-31')]), ('Sep-26', b[b['cohort']==pd.Timestamp('2026-09-01')])]:
    t = d.groupby('fam').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
    t['conv_%']=(t['conv']/t['n']*100).round(1); t['arpu']=(t['rev']/t['n']).round(0)
    print(f'--- {lbl} ---'); print(t.sort_values('n',ascending=False).to_string()); print()
