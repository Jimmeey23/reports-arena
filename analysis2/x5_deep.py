import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 70)

C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
C['cap'] = pd.to_numeric(C['Capacity'], errors='coerce')
Bs = C[C['Location'] == 'Supreme HQ, Bandra'].copy()

print('=' * 118)
print('FILL RATE — computed per session (correct method)')
print('=' * 118)
def fill(d):
    s = d.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'))
    s = s[s['cap'] > 0]
    return s
for lbl, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    s = fill(Bs[(Bs['dt'] >= a) & (Bs['dt'] < b_)])
    s['f'] = s['att'] / s['cap'] * 100
    print(f'  {lbl}: {len(s)} sessions | median fill {s["f"].median():.0f}% | mean {s["f"].mean():.0f}% | '
          f'under 50%: {(s["f"]<50).sum()} ({(s["f"]<50).mean()*100:.0f}%) | over 90%: {(s["f"]>90).sum()} ({(s["f"]>90).mean()*100:.0f}%)')
print()
x = Bs[(Bs['dt'] >= '2026-09-01') & (Bs['dt'] < '2026-10-01')]
s = fill(x); s = s.join(x.groupby('Session ID')['Cleaned Class'].first())
byc = s.groupby('Cleaned Class').agg(sessions=('cap', 'size'), seats=('cap', 'sum'), attended=('att', 'sum'))
byc['fill_%'] = (byc['attended'] / byc['seats'] * 100).round(0)
print('  By class format, Sept 2026:')
print(byc.sort_values('seats', ascending=False).to_string())
print()
print('  Seats actually used vs offered across the month:')
print(f'   seats offered: {int(s["cap"].sum()):,} | seats filled: {int(s["att"].sum()):,} | utilisation: {s["att"].sum()/s["cap"].sum()*100:.1f}%')

print()
print('=' * 118)
print('TEACHER-LEVEL CHANGE — who lost/gained classes')
print('=' * 118)
for lbl, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    t = Bs[(Bs['dt'] >= a) & (Bs['dt'] < b_)]
    print(f'--- {lbl} ---')
    print(t.groupby('Teacher Name').agg(bookings=('Member ID', 'size'), attended=('checked', 'sum')).sort_values('bookings', ascending=False).head(12).to_string())
    print()

print('=' * 118)
print('2-FOR-1 ECONOMICS vs SINGLE CLASS')
print('=' * 118)
S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = pd.to_numeric(S['Payment Value'].astype(str).str.replace(r'[,\s]', '', regex=True), errors='coerce')
SB = S[S['Calculated Location'] == 'Supreme HQ, Bandra']
for p in ['Studio Newcomers 2 For 1', 'Studio Single Class', 'Studio 4 Class Package', 'Studio 12 Class Package',
          'Studio 1 Month Unlimited', 'Studio 10 Class Package', 'Studio 20 Single Class Package']:
    d = SB[SB['Cleaned Product'] == p]
    if not len(d): continue
    classes = {'Studio Newcomers 2 For 1': 2, 'Studio Single Class': 1, 'Studio 4 Class Package': 4,
               'Studio 12 Class Package': 12, 'Studio 1 Month Unlimited': None, 'Studio 10 Class Package': 10,
               'Studio 20 Single Class Package': 20}.get(p)
    per = f'Rs {d["val"].mean()/classes:,.0f}' if classes else '—'
    print(f'  {p:34s} n={len(d):5d}  avg price Rs {d["val"].mean():>9,.0f}  per-class {per:>10s}')

print()
print('=' * 118)
print('DOES THE 2-FOR-1 LEAD TO A MEMBERSHIP? (Bandra)')
print('=' * 118)
nc_members = set(SB[SB['Cleaned Category'] == 'Newcomers Special']['Member ID'])
after = SB[SB['Member ID'].isin(nc_members)].sort_values(['Member ID', 'dt'])
rows = []
for mid, gg in after.groupby('Member ID'):
    nc_rows = gg[gg['Cleaned Category'] == 'Newcomers Special']
    if not len(nc_rows): continue
    t0 = nc_rows['dt'].min()
    later = gg[gg['dt'] > t0]
    rows.append({'mid': mid, 'bought_again': len(later) > 0, 'later_rev': later['val'].sum(),
                 'later_cat': later['Cleaned Category'].iloc[0] if len(later) else None})
r = pd.DataFrame(rows)
print(f'  Members who ever bought a Bandra Newcomers 2-for-1: {len(r)}')
print(f'  Bought anything afterwards: {r["bought_again"].sum()} ({r["bought_again"].mean()*100:.1f}%)')
print(f'  Revenue after the intro pack: Rs {r["later_rev"].sum():,.0f} (avg Rs {r["later_rev"].mean():,.0f}/member)')
print()
print('  What they buy next:')
print(r['later_cat'].value_counts().to_string())
print()
allb = SB.groupby('Member ID').agg(txns=('Sale ID', 'size'), rev=('val', 'sum'))
print(f'  BANDRA comparison — all buyers: avg lifetime Rs {allb["rev"].mean():,.0f}, avg txns {allb["txns"].mean():.2f}')

print()
print('=' * 118)
print('LEAD SOURCE QUALITY — the channels ranked by economics (Bandra, lifetime)')
print('=' * 118)
L = pd.read_csv('/home/user/uploads/❖ PM - Leads ❖ - ◉ Leads (31).csv', low_memory=False)
L['ltv_n'] = pd.to_numeric(L['LTV'], errors='coerce')
LB = L[L['Center'] == 'Supreme HQ, Bandra'].copy()
LB['won'] = LB['Status'].eq('Won')
ch = LB.groupby('Channel').agg(leads=('ID', 'size'), won=('won', 'sum'), ltv=('ltv_n', 'sum'))
ch['win_%'] = (ch['won'] / ch['leads'] * 100).round(1)
ch['ltv_per_lead'] = (ch['ltv'] / ch['leads']).round(0)
ch['share_%'] = (ch['leads'] / ch['leads'].sum() * 100).round(1)
ch = ch.sort_values('ltv_per_lead', ascending=False)
print(ch.to_string())
print()
best = ch.index[0]; worst = ch.iloc[-1]
print(f'  >> Best channel: {ch.index[0]} at Rs {ch["ltv_per_lead"].iloc[0]:,.0f} per lead')
print(f'  >> Volume is concentrated in: {ch["share_%"].idxmax()} ({ch["share_%"].max():.0f}% of leads) at Rs {ch.loc[ch["share_%"].idxmax(),"ltv_per_lead"]:,.0f} per lead')

print()
print('=' * 118)
print('HOSTED CLASS LEADS — trials galore, sales rare')
print('=' * 118)
h = LB[LB['Source Name'] == 'Hosted Class']
print(f'  Bandra hosted-class leads: {len(h)}')
print(f'    trialed: {h["Trial Status"].eq("Trial Completed").sum()} ({h["Trial Status"].eq("Trial Completed").mean()*100:.1f}%)')
print(f'    won    : {h["won"].sum()} ({h["won"].mean()*100:.1f}%)')
print(f'    avg LTV per lead: Rs {h["ltv_n"].mean():,.0f}')
print()
print('  Compare client referral:')
rf = LB[LB['Source Name'] == 'Client Referral']
print(f'    referral leads {len(rf)} | trialed {rf["Trial Status"].eq("Trial Completed").mean()*100:.1f}% | won {rf["won"].mean()*100:.1f}% | LTV/lead Rs {rf["ltv_n"].mean():,.0f}')

print()
print('=' * 118)
print('SEPT-2026 BANDRA LEADS — pipeline still open')
print('=' * 118)
L['created'] = pd.to_datetime(L['Created At'], errors='coerce')
s26 = LB[(LB['created'] >= '2026-09-01') & (LB['created'] < '2026-10-01')]
print(f'  Leads created Sept-2026: {len(s26)}')
print(f'  Still open/uncategorised: {s26["Status"].isin(["Open","Uncategorized","Trial Completed","Trial Scheduled"]).sum()} '
      f'({s26["Status"].isin(["Open","Uncategorized","Trial Completed","Trial Scheduled"]).mean()*100:.0f}%)')
print(f'  Won so far: {s26["won"].sum()} ({s26["won"].mean()*100:.1f}%)')
print()
print('  Lead->trial->win timing (Bandra, all leads with both dates):')
L2 = LB.dropna(subset=['created', 'conv_at']) if 'conv_at' in LB else None
LB['conv_at'] = pd.to_datetime(LB['Converted To Customer At'], errors='coerce')
t = LB.dropna(subset=['created', 'conv_at'])
print(f'   leads with a conversion date: {len(t)} | median days created->converted: {(t["conv_at"]-t["created"]).dt.days.median():.0f}')
