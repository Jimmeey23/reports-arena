import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')

nn = df[~df['is_import']].copy()
nn['obs_days'] = (SNAP - nn['fvd']).dt.days
nn['studio'] = nn['First Visit Location'].fillna('(unknown)')

print('=' * 110)
print('1. IS THIS A BANDRA PROBLEM OR A NETWORK PROBLEM?  (strict day-1-11 window)')
print('=' * 110)
strict = nn[nn['fvd'].dt.day <= 11].copy()
rows = []
for (per, st), g in strict.groupby([strict['cohort'].dt.to_period('M'), 'studio']):
    if len(g) < 8: continue
    rows.append({'cohort': str(per), 'studio': st, 'n': len(g),
                 'conv30': round((g['converted'] & (g['conv_span'] <= 30)).mean()*100, 1),
                 'second30': round((g['days_2nd'] <= 30).mean()*100, 1),
                 'visits': round(g['No of Visits'].mean(), 2)})
sr = pd.DataFrame(rows)
for st in [BANDRA, 'Kwality House, Kemps Corner', 'Kenkere House']:
    x = sr[sr['studio'] == st].tail(13)
    print(f'--- {st} ---')
    print(x[['cohort','n','conv30','second30','visits']].to_string(index=False))
    base = sr[(sr['studio']==st) & (sr['cohort']>='2025-10') & (sr['cohort']<='2026-08')]
    cur  = sr[(sr['studio']==st) & (sr['cohort']=='2026-09')]
    if len(cur):
        print(f'    trailing-12m: conv30={base["conv30"].mean():.1f}  second30={base["second30"].mean():.1f}  visits={base["visits"].mean():.2f}')
        print(f'    Sep-26      : conv30={cur["conv30"].iloc[0]:.1f}  second30={cur["second30"].iloc[0]:.1f}  visits={cur["visits"].iloc[0]:.2f}')
    print()

print('=' * 110)
print('2. SEPTEMBER SEASONALITY — same studio, same month, prior years (strict window)')
print('=' * 110)
rows=[]
for (st, per), g in strict.groupby(['studio', strict['cohort'].dt.to_period('M')]):
    if 'Sep' not in str(per) or len(g) < 8: continue
    rows.append({'studio': st, 'month': str(per), 'n': len(g),
                 'conv30': round((g['converted'] & (g['conv_span'] <= 30)).mean()*100,1),
                 'second30': round((g['days_2nd'] <= 30).mean()*100,1)})
print(pd.DataFrame(rows).sort_values(['studio','month']).to_string(index=False))

print()
print('=' * 110)
print('3. DAY-OF-WEEK MIX SHIFT — Bandra, did Sept get an unusual intake mix?')
print('=' * 110)
b = nn[nn['studio'] == BANDRA].copy()
rows=[]
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if len(g) < 20: continue
    d = g['First Visit Day'].value_counts(normalize=True)*100
    rows.append({'cohort': str(per), 'n': len(g),
                 'Sun%': round(d.get('Sunday',0),1), 'Sat%': round(d.get('Saturday',0),1),
                 'Mon%': round(d.get('Monday',0),1), 'Tue%': round(d.get('Tuesday',0),1),
                 'Wed%': round(d.get('Wednesday',0),1), 'Thu%': round(d.get('Thursday',0),1),
                 'Fri%': round(d.get('Friday',0),1)})
mix = pd.DataFrame(rows)
print(mix.tail(14).to_string(index=False))

print()
print('=' * 110)
print('4. HOSTED / PARTNER CLASS PROGRAMME — Bandra vs Network, standalone economics')
print('=' * 110)
h = nn[nn['First Visit Entity Name'].str.contains('Hosted|X |x |Sweat|Pickle|Peakst8|KRC|Run Club', case=False, na=False)].copy()
print(f'Total hosted/partner first visits in dataset: {len(h)}')
print(f'  converted: {h["converted"].sum()}  ({h["converted"].mean()*100:.1f}%)   revenue: Rs {h["revenue"].sum():,.0f}')
print(f'  avg LTV per hosted client: Rs {h["revenue"].mean():,.0f}')
print()
hg = h.groupby(h['cohort'].dt.to_period('M')).agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
                                                    second=('days_2nd', lambda s: s.notna().sum()))
hg['conv_%']=(hg['conv']/hg['n']*100).round(1)
hg['second_%']=(hg['second']/hg['n']*100).round(1)
hg['arpu']=(hg['rev']/hg['n']).round(0)
print(hg.loc['2025-09':'2026-10'].to_string())
print()
print('Named partner programmes (all time, top 15 by volume):')
hp = h.groupby('First Visit Entity Name').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
hp['conv_%']=(hp['conv']/hp['n']*100).round(1)
hp['ltv_per_client']=(hp['rev']/hp['n']).round(0)
hp['total_ltv']=hp['rev'].round(0)
print(hp.sort_values('n',ascending=False).head(15).to_string())

print()
print('=' * 110)
print('5. RESHMA SHARMA DEEP DIVE — the zero-conversion anomaly')
print('=' * 110)
rs = b[b['Trainer Name'] == 'Reshma Sharma']
print('All-time Bandra as first trainer: n=%d, conv=%d (%.1f%%), second=%d (%.1f%%), LTV/client=Rs %,.0f'.replace(',.0f','.0f') % (
    len(rs), rs['converted'].sum(), rs['converted'].mean()*100, rs['days_2nd'].notna().sum(),
    rs['days_2nd'].notna().mean()*100, rs['revenue'].mean()))
print()
print('By cohort month (last 14 months):')
rg = rs.groupby(rs['cohort'].dt.to_period('M')).agg(n=('Member Id','count'), conv=('converted','sum'),
                                                     second=('days_2nd', lambda s: s.notna().sum()), rev=('revenue','sum'))
rg['conv_%']=(rg['conv']/rg['n']*100).round(1); rg['second_%']=(rg['second']/rg['n']*100).round(1)
rg['arpu']=(rg['rev']/rg['n']).round(0)
print(rg.tail(14).to_string())
print()
sep_rs = rs[rs['cohort'] == pd.Timestamp('2026-09-01')]
print('Sept-2026 Reshma clients — what class did they attend, what day/slot, what entry route?')
print(sep_rs.groupby(['First Visit Entity Name','First Visit Day','First Visit Time Slot']).size().to_string())
print()
print('entry route:', sep_rs['Is New'].value_counts().to_dict())
print('source:', sep_rs['Source'].fillna('(unattributed)').value_counts().to_dict())
print('membership used on first visit:', sep_rs['Membership Used'].fillna('(none)').value_counts().head(8).to_dict())

print()
print('=' * 110)
print('6. DATA QUALITY / ATTRIBUTION')
print('=' * 110)
bx = b[b['cohort'] == pd.Timestamp('2026-09-01')]
print('Sept-26 Bandra cohort source attribution:')
print('   unattributed: %d of %d (%.1f%%)' % (bx['Source'].isna().sum(), len(bx), bx['Source'].isna().mean()*100))
print('   no trainer logged: %d' % bx['Trainer Name'].isna().sum())
print('   no phone: %d' % bx['Phone Number'].isna().sum())
print('   no home location: %d' % bx['Home Location'].isna().sum())
print()
print('Network-wide unattributed (non-import): %.1f%%' % (nn['Source'].isna().mean()*100))
print('Bandra all-time unattributed: %.1f%%' % (b['Source'].isna().mean()*100))
