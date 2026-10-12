"""Round-5 mining pass, part 3: payroll cost (fixed), sales deep cuts, first-visit slots."""
import pandas as pd, numpy as np
import d1_data as D
pd.set_option('display.width', 215); pd.set_option('display.max_columns', 70)
U = '/home/user/reports-arena/uploads/'; B = D.BANDRA
def num(s): return pd.to_numeric(pd.Series(s).astype(str).str.replace(r'[,\s₹]', '', regex=True), errors='coerce')
def hdr(t): print('\n' + '=' * 104 + f'\n{t}\n' + '=' * 104)
def blk(t, f):
    hdr(t)
    try: f()
    except Exception as e:
        import traceback; print('  FAILED:', type(e).__name__, e); traceback.print_exc(limit=2)

SB = D.SB.copy()
s26 = SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')]
s25 = SB[(SB['dt'] >= '2025-09-01') & (SB['dt'] < '2025-10-01')]
print('Sept-26 txns', len(s26), 'Sept-25', len(s25))

# ---------------------------------------------------------------- 13
def f13():
    P = pd.read_csv(U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
    P = P[P['Location'] == B].copy(); P['dt'] = pd.to_datetime(P['Month Year'], errors='coerce')
    for c in [c for c in P.columns if 'Paid' in c or 'Sessions' in c or 'Customers' in c or c in ('Converted','Retained','New')]:
        P[c] = num(P[c])
    pa = P[P['dt'] == '2026-08-01'].copy()
    print(f"Aug-2026 total pay ₹{pa['Total Paid'].sum():,.0f} on {pa['Total Sessions'].sum():.0f} sessions "
          f"= ₹{pa['Total Paid'].sum()/pa['Total Sessions'].sum():,.0f}/session | "
          f"empty sessions paid {pa['Total Empty Sessions'].sum():.0f} "
          f"({pa['Total Empty Sessions'].sum()/pa['Total Sessions'].sum()*100:.1f}%)")
    pa['pay_per_sess'] = (pa['Total Paid']/pa['Total Sessions']).round(0)
    print(pa[['Teacher Name','Total Sessions','Total Empty Sessions','Total Customers','Total Paid','pay_per_sess']]
          .sort_values('Total Paid', ascending=False).to_string(index=False))
    print('\nDiscipline pay split (Aug-2026):')
    for d in ['Cycle','Strength','Barre']:
        s = pa[d+' Sessions'].sum()
        if s: print(f"  {d:9} sessions {s:>5.0f}  paid ₹{pa[d+' Paid'].sum():>10,.0f}  per session ₹{pa[d+' Paid'].sum()/s:>8,.0f}")
    print('\nPayroll by month (Bandra):')
    t = P.groupby('dt').agg(teachers=('Teacher Name','nunique'), sessions=('Total Sessions','sum'),
                            paid=('Total Paid','sum'), customers=('Total Customers','sum'),
                            new=('New','sum'), conv=('Converted','sum'), ret=('Retained','sum'))
    t['pay_per_cust'] = (t['paid']/t['customers'].replace(0, np.nan)).round(0)
    t['pay_per_sess'] = (t['paid']/t['sessions']).round(0)
    t['conv_rate'] = (t['conv']/t['new']*100).round(1)
    t['ret_rate'] = (t['ret']/t['new']*100).round(1)
    print(t.round(0).to_string())
blk('13. PAYROLL COST RATIOS (corrected)', f13)

# ---------------------------------------------------------------- 14
def f14():
    print('PAYMENT METHOD (Sept-26 vs Sept-25):')
    a = s26.groupby('Payment Method')['val'].agg(['size','sum'])
    b = s25.groupby('Payment Method')['val'].agg(['size','sum'])
    j = a.join(b, lsuffix='_26', rsuffix='_25', how='outer').fillna(0)
    j['share_26'] = (j['sum_26']/j['sum_26'].sum()*100).round(1)
    j['avg_26'] = (j['sum_26']/j['size_26'].replace(0, np.nan)).round(0)
    print(j.round(0).to_string())
    print('\nDISCOUNT CODE usage (Sept-26):')
    g = s26.groupby('Discount Code').agg(n=('val','size'), rev=('val','sum'), disc=('disc','sum'))
    g['depth'] = (g['disc']/(g['rev']+g['disc'])*100).round(1)
    print(g.sort_values('rev', ascending=False).head(12).round(0).to_string())
    print('\nSOLD BY: volume, ticket, discount depth (Sept-26):')
    g = s26.groupby('Sold By').agg(n=('val','size'), rev=('val','sum'), disc=('disc','sum'))
    g['avg_sale'] = (g['rev']/g['n']).round(0)
    g['depth'] = (g['disc']/(g['rev']+g['disc'])*100).round(1)
    print(g.sort_values('rev', ascending=False).round(0).to_string())
    print('\nCategory cross-sell: how many distinct Cleoned Category did each Sept-26 buyer take?')
    cb = s26.groupby('Member ID')['Cleaned Category'].nunique()
    print(cb.value_counts().sort_index().to_string())
    print(f"  buyers {len(cb)} | single-category {(cb==1).sum()} ({(cb==1).mean()*100:.0f}%) | 2+ {(cb>=2).sum()}")
    sp = s26.groupby('Member ID')['val'].sum().sort_values(ascending=False)
    print(f"\nSpend concentration Sept-26: top 10 buyers = {sp.nlargest(10).sum()/sp.sum()*100:.1f}% of cash;"
          f" top 20 = {sp.nlargest(20).sum()/sp.sum()*100:.1f}%; bottom 50% = {sp.nsmallest(int(len(sp)/2)).sum()/sp.sum()*100:.1f}%")
    print('  top 8 buyers:', [f'{int(k)}:₹{v:,.0f}' for k, v in sp.nlargest(8).items()])
blk('14. SALES METHODS, CODES, SELLERS, CONCENTRATION', f14)

# ---------------------------------------------------------------- 15
def f15():
    """What a September-2025 buyer did over the following 12 months, by the product they first bought."""
    first = SB.sort_values('dt').groupby('Member ID').agg(fd=('dt','min'), fp=('Cleaned Product','first'))
    later = SB.groupby('Member ID').agg(nd=('dt','max'), n=('Sale ID','nunique'), v=('val','sum'))
    f = first.join(later, how='inner')
    f['obs'] = (f['nd'] - f['fd']).dt.days
    f = f[(f['fd'] >= '2025-01-01') & (f['fd'] < '2025-10-01') & (f['obs'] >= 300)]
    g = f.groupby('fp').agg(members=('n','size'), repurchase_pct=('n', lambda x: (x > 1).mean()*100),
                            avg_txns=('n','mean'), lifetime=('v','mean')).round(1)
    print('First product bought (Jan-Sep 2025 cohort, 12 months of observation):')
    print(g[g['members'] >= 3].sort_values('repurchase_pct', ascending=False).to_string())
    print('\nSame, by first CATEGORY:')
    firstc = SB.sort_values('dt').groupby('Member ID').agg(fd=('dt','min'), fc=('Cleaned Category','first'))
    fc = firstc.join(later, how='inner'); fc['obs'] = (fc['nd'] - fc['fd']).dt.days
    fc = fc[(fc['fd'] >= '2025-01-01') & (fc['fd'] < '2025-10-01') & (fc['obs'] >= 300)]
    print(fc.groupby('fc').agg(members=('n','size'), repurchase_pct=('n', lambda x: (x > 1).mean()*100),
                               avg_txns=('n','mean'), lifetime=('v','mean')).round(1).sort_values('repurchase_pct', ascending=False).to_string())
    print('\nNew vs returning cash split, Sept-26:')
    print(f"  first-ever Bandra purchase this month: ₹{(s26[s26['firstp']=='2026-09']['val'].sum() if 'firstp' in s26 else 0):,.0f}")
blk('15. FIRST-PRODUCT RETENTION COHORT', f15)

# ---------------------------------------------------------------- 16
def f16():
    """First-visit slot quality: which day/hour/source brings in people who come back."""
    CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False, usecols=[
        'Member ID','Location','Date (IST)','Checked In','Cleaned Class','Teacher Name','Time','Day of Week',
        'Is New','First Name'])
    CK = CK[CK['Location'] == B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
    CK = CK[CK['dt'].notna() & (CK['Checked In'] == True)].copy().sort_values(['Member ID','dt'])
    CK['vn'] = CK.groupby('Member ID').cumcount() + 1
    foot = CK[CK['vn'] == 1].copy()
    foot['hr'] = pd.to_numeric(foot['Time'].astype(str).str[:2], errors='coerce')
    depth = CK.groupby('Member ID').size().rename('visits')
    tot = CK.groupby('Member ID')['dt'].agg(['min','max'])
    tot['span'] = (tot['max']-tot['min']).dt.days
    foot = foot.join(depth, on='Member ID'); foot = foot.join(tot[['span']], on='Member ID')
    f = foot[foot['dt'] >= '2025-01-01']
    print(f'Members whose FIRST ever Bandra class was from Jan-2025 (n={len(f)}):')
    def sl(df, col, lab):
        g = df.groupby(col).agg(members=('visits','size'), avg_visits=('visits','mean'),
                                reach3=('visits', lambda x:(x>=3).mean()*100),
                                reach6=('visits', lambda x:(x>=6).mean()*100))
        g = g[g['members'] >= 12].round(1).sort_values('reach3', ascending=False)
        print(f'\n  by {lab}:'); print(g.to_string())
    sl(f, 'Day of Week', 'day of first class')
    f['band'] = pd.cut(f['hr'], [0,9,12,17,24], labels=['early <9','late morning 9-12','afternoon 12-17','evening 17+'])
    sl(f, 'band', 'time of first class')
    sl(f, 'Is New', 'entry type')
    sl(f, 'Cleaned Class', 'format of first class')
    sl(f, 'Teacher Name', 'first-class trainer')
blk('16. FIRST-VISIT SLOT / FORMAT / TRAINER -> DEPTH', f16)

# ---------------------------------------------------------------- 17
def f17():
    X = pd.read_csv(U + 'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
    X = X[X['Location'] == B].copy(); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
    for c in ['Capacity','CheckedIn','LateCancelled','Booked','Complimentary','Revenue','Memberships','Packages','IntroOffers','SingleClasses']:
        X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0)
    X['cap'] = X['Capacity']/X['Classes'].clip(lower=1)
    x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')]
    print('Complimentary seats in Sept-26:', x26['Complimentary'].sum(), 'of', x26['CheckedIn'].sum(), 'attended',
          f"({x26['Complimentary'].sum()/x26['CheckedIn'].sum()*100:.1f}%)")
    g = x26.groupby('Class').agg(sessions=('SessionID','size'), att=('CheckedIn','sum'), comp=('Complimentary','sum'))
    g['comp_share'] = (g['comp']/g['att'].replace(0, np.nan)*100).round(1)
    print(g.sort_values('comp', ascending=False).to_string())
    print('\nHosted / externally-branded sessions:')
    H = x26[x26['SessionName'].str.contains('X \\||Hosted|Sweat|Pickle|Peakst8|KRC|Fest|Ladies|Community', case=False, na=False)]
    print(f"  {len(H)} sessions, {H['CheckedIn'].sum()} attended, {H['cap'].sum():.0f} seats, "
          f"₹{H['Revenue'].sum():,.0f} revenue, comp seats {H['Complimentary'].sum()}")
    print(H[['Date','Day','Time','SessionName','Trainer','cap','CheckedIn','Revenue','Complimentary']].to_string(index=False))
    print('\nIntro-offer and single-class load by format (Sept-26):')
    p = x26.groupby('Class').agg(sessions=('SessionID','size'), intro=('IntroOffers','sum'),
                                 single=('SingleClasses','sum'), memb=('Memberships','sum'),
                                 pkg=('Packages','sum'), att=('CheckedIn','sum'))
    for c in ['intro','single','memb','pkg']:
        p[c+'_%'] = (p[c]/p['att'].replace(0, np.nan)*100).round(1)
    print(p.sort_values('att', ascending=False).to_string())
blk('17. COMPLIMENTARY SEATS, HOSTED SESSIONS, PAYMENT LOAD BY FORMAT', f17)
