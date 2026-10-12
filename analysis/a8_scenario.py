import pandas as pd, numpy as np
from prep import load
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 80)
df = load()
BANDRA = 'Supreme HQ, Bandra'
SNAP = pd.Timestamp('2026-10-11')

nn = df[~df['is_import']].copy()
b = nn[nn['First Visit Location'] == BANDRA].copy()
b['obs'] = (SNAP - b['fvd']).dt.days

print('=' * 110)
print('1. YTD PICTURE — Bandra & network, Jan-Sep')
print('=' * 110)
for yr in [2024, 2025, 2026]:
    g = b[(b['fvd'] >= f'{yr}-01-01') & (b['fvd'] < f'{yr}-10-01')]
    gn = nn[(nn['fvd'] >= f'{yr}-01-01') & (nn['fvd'] < f'{yr}-10-01')]
    print(f'  {yr} Jan-Sep | BANDRA: clients={len(g):5d}  conv={g["converted"].sum():4d} ({g["converted"].mean()*100:5.1f}%)  '
          f'2nd={g["days_2nd"].notna().sum():4d} ({g["days_2nd"].notna().mean()*100:5.1f}%)  rev=Rs {g["revenue"].sum():>12,.0f}  ARPU=Rs {g["revenue"].mean():>8,.0f}')
    print(f'  {"":10s}| NETWORK: clients={len(gn):5d}  conv={gn["converted"].sum():4d} ({gn["converted"].mean()*100:5.1f}%)  rev=Rs {gn["revenue"].sum():>12,.0f}')
print()
print('  >> Bandra 2026 YTD new-client LTV is down %.0f%% vs 2025 and %.0f%% vs 2024' % (
    (b[(b['fvd']>="2026-01-01")&(b['fvd']<"2026-10-01")]['revenue'].sum()/b[(b['fvd']>="2025-01-01")&(b['fvd']<"2025-10-01")]['revenue'].sum()-1)*100,
    (b[(b['fvd']>="2026-01-01")&(b['fvd']<"2026-10-01")]['revenue'].sum()/b[(b['fvd']>="2024-01-01")&(b['fvd']<"2024-10-01")]['revenue'].sum()-1)*100))

print()
print('=' * 110)
print('2. SCENARIO MODEL — Sept-2026 Bandra cohort (n=143, days 1-13 matched basis for rates)')
print('=' * 110)
# matched basis: days 1-13 (n=70). Rates from trailing-11m baseline.
matched = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01') & (b['fvd'].dt.day <= 13)]
print(f'The Sept 1-13 sub-cohort (n={len(matched)}) is fully matured (>=28 days observed).')
base_conv, base_2nd, base_arpu = 0.1925, 0.3775, 5507
act_conv, act_2nd, act_arpu = matched['converted'].mean(), matched['days_2nd'].notna().mean(), matched['revenue'].mean()
print(f'   conversion   actual {act_conv*100:5.1f}%  vs baseline {base_conv*100:5.1f}%  -> {int(act_conv*len(matched))} vs {base_conv*len(matched):.0f} converters (gap {base_conv*len(matched)-act_conv*len(matched):.0f})')
print(f'   2nd visit    actual {act_2nd*100:5.1f}%  vs baseline {base_2nd*100:5.1f}%  -> {int(act_2nd*len(matched))} vs {base_2nd*len(matched):.0f} 2nd visits (gap {base_2nd*len(matched)-act_2nd*len(matched):.0f})')
print(f'   ARPU         actual Rs {act_arpu:,.0f} vs baseline Rs {base_arpu:,.0f}')
print()
gap_conv_13 = base_conv*len(matched) - act_conv*len(matched)
print(f'   VALUE GAP on the matured Sept 1-13 sub-cohort alone: Rs {gap_conv_13*17363:,.0f} (using Rs 17,363 revenue/converter)')
print()
print('FORECAST — once the full 143-client Sept cohort matures (at 69% of lifetime conversions realized ~30d):')
proj_conv = 143 * 0.125   # strict 30-day rate as most conservative
base_proj  = 143 * 0.1925
print(f'   projected converters (actual trajectory) : ~{proj_conv:.0f}')
print(f'   converters if baseline rate 19.25% held  : ~{base_proj:.0f}')
print(f'   revenue if baseline ARPU (Rs 5,507) held : Rs {143*base_arpu:,.0f}')
print(f'   revenue now booked                       : Rs {b[b["cohort"]==pd.Timestamp("2026-09-01")]["revenue"].sum():,.0f}')
print(f'   >> TOTAL VALUE SHORTFALL, Sept cohort    : Rs {143*base_arpu - b[b["cohort"]==pd.Timestamp("2026-09-01")]["revenue"].sum():,.0f}')

print()
print('RECOVERY SCENARIOS (Sept cohort, next 90 days):')
for lbl, uplift in [('Conservative: lift 2nd-visit to 20%', 0.20), ('Base: lift to 30%', 0.30), ('Stretch: lift to 37.8% (trailing norm)', 0.3775)]:
    n2 = 143 * uplift; cur2 = 143 * 0.129
    add_conv = (n2 - cur2) * 0.619
    print(f'   {lbl:42s} -> +{n2-cur2:4.0f} 2nd visits -> +{add_conv:4.0f} converters -> +Rs {add_conv*17363:>10,.0f}')

print()
print('=' * 110)
print('3. HOSTED/PARTNER EVENT PROGRAMME — full P&L view (network-wide)')
print('=' * 110)
h = nn[nn['First Visit Entity Name'].str.contains('Hosted| X | x |Sweat|Pickle|Peakst8|KRC|Run Club|Unfiltered|SPRINT', case=False, na=False)].copy()
print(f'All hosted/partner-event first visits in dataset: {len(h)}')
print(f'   converted {h["converted"].sum()} ({h["converted"].mean()*100:.1f}%) | LTV/client Rs {h["revenue"].mean():,.0f} | total LTV Rs {h["revenue"].sum():,.0f}')
print()
hg = h.groupby(h['cohort'].dt.to_period('M')).agg(clients=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
                                                   second=('days_2nd', lambda s: s.notna().sum()))
hg['conv_%']=(hg['conv']/hg['clients']*100).round(1); hg['2nd_%']=(hg['second']/hg['clients']*100).round(1)
hg['ltv/client']=(hg['rev']/hg['clients']).round(0)
print(hg.loc['2025-09':'2026-10'].to_string())
print()
print('Top partner programmes by volume (all time):')
hp = h.groupby('First Visit Entity Name').agg(clients=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'))
hp['conv_%']=(hp['conv']/hp['clients']*100).round(1)
hp['ltv/client']=(hp['rev']/hp['clients']).round(0)
hp['total_LTV']=hp['rev'].round(0)
print(hp.sort_values('clients',ascending=False).head(12).to_string())

print()
print('=' * 110)
print('4. BANDRA HOME-LOCATION BASE HEALTH (all clients whose home studio is Bandra)')
print('=' * 110)
bh = df[df['bandra_home'] & (~df['is_import'])].drop_duplicates('Member Id')
print(f'Total unique Bandra-home clients: {len(bh)}')
print()
print('Lifecycle status:', bh['Lifecycle Status'].value_counts().to_dict())
print()
act = bh[bh['Lifecycle Status']=='Active']
risk = bh[bh['Lifecycle Status']=='At Risk']
print(f'Active base: {len(act)} | At Risk: {len(risk)} | Lapsed: {(bh["Lifecycle Status"]=="Lapsed").sum()} | Churned: {(bh["Lifecycle Status"]=="Churned").sum()}')
print(f'Retention funnel: {len(act)/(len(bh))*100:.1f}% active, {(len(act)+len(risk))/len(bh)*100:.1f}% active+at-risk')
print()
print(f'Historical LTV of Bandra-home base: Rs {bh["revenue"].sum():,.0f}')
print(f'  Active   : Rs {act["revenue"].sum():,.0f}  (avg Rs {act["revenue"].mean():,.0f}/member)')
print(f'  At Risk  : Rs {risk["revenue"].sum():,.0f}  (avg Rs {risk["revenue"].mean():,.0f}/member)')
print(f'  >> At-risk revenue exposure: Rs {risk["revenue"].mean()*len(risk):,.0f} of prior LTV; these members historically worth Rs {risk["revenue"].mean():,.0f} each')
print()
print('At-risk members — recency:', risk['days_since'].describe().round(0).to_dict())
print()
print('Late-cancel behaviour of ACTIVE base (capacity leakage):')
print(f'   mean late-cancel rate: {act["latecancel"].mean()*100:.1f}%   median {act["latecancel"].median()*100:.1f}%')
print(f'   members with >20% late-cancel rate: {(act["latecancel"]>0.2).sum()} ({(act["latecancel"]>0.2).mean()*100:.1f}% of active base)')
print(f'   members with >50% late-cancel rate: {(act["latecancel"]>0.5).sum()}')

print()
print('=' * 110)
print('5. REVENUE CONCENTRATION — Bandra-home base')
print('=' * 110)
v = bh['revenue'].sort_values(ascending=False)
tot = v.sum()
for pct in [0.01, 0.05, 0.10, 0.20]:
    k = int(len(v)*pct)
    print(f'   top {pct*100:4.0f}% of clients ({k:4d}) = {v.head(k).sum()/tot*100:5.1f}% of LTV')
print(f'   bottom 50% of clients = {v.tail(int(len(v)*0.5)).sum()/tot*100:.1f}% of LTV')
print(f'   clients with zero LTV: {(v==0).sum()} ({(v==0).mean()*100:.1f}%)')
print()
print('Avg purchase value distribution (post-trial), Bandra-home converted:')
conv_bh = bh[bh['converted'] & (bh['avg_pv']>0)]
print(conv_bh['avg_pv'].describe(percentiles=[.25,.5,.75,.9]).round(0).to_string())
print()
print('Purchase count distribution (Bandra-home converted):')
print(conv_bh['Purchase Count Post Trial'].value_counts().sort_index().head(15).to_dict())

print()
print('=' * 110)
print('6. FIRST-CLASS TRAINER EFFECT — statistical validation (Bandra, all-time, trainers with n>=40)')
print('=' * 110)
bt = b[b['Trainer Name'].notna()]
tt = bt.groupby('Trainer Name').agg(n=('Member Id','count'), conv=('converted','sum'), rev=('revenue','sum'),
                                     second=('days_2nd', lambda s: s.notna().sum()))
tt = tt[tt['n']>=40]
tt['conv_%']=(tt['conv']/tt['n']*100).round(1)
tt['2nd_%']=(tt['second']/tt['n']*100).round(1)
tt['ltv/client']=(tt['rev']/tt['n']).round(0)
tt['total_LTV']=tt['rev'].round(0)
overall = bt['converted'].mean()*100
print(f'Overall Bandra conversion (all cohorts, trainer logged): {overall:.1f}%')
print(tt.sort_values('ltv/client', ascending=False).to_string())
print()
top = tt.sort_values('ltv/client',ascending=False)
lo, hi = top['ltv/client'].iloc[-1], top['ltv/client'].iloc[0]
print(f'   >> Trainer spread in LTV/client: Rs {lo:,.0f} to Rs {hi:,.0f} = {hi/lo:.1f}x')
print(f'   >> If the bottom 5 trainers (by LTV/client) performed at studio median, additional LTV = Rs {(top["ltv/client"].median()-top["ltv/client"].tail(5).mean())*top["n"].tail(5).sum():,.0f}')
