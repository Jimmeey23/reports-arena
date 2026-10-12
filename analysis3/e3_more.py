"""Mining pass for reports 2-4: survival, formats, cancellations, discounts, leads."""
import pandas as pd, numpy as np, e1_data as E
pd.set_option('display.width', 230); pd.set_option('display.max_columns', 70)
L, LP, LS = E.L, E.LP, E.LS
LD, LB = E.LD, E.LB
def hdr(t): print('\n' + '='*104 + f'\n{t}\n' + '='*104)
def blk(t, f):
    hdr(t)
    try: f()
    except Exception as e:
        import traceback; print('FAILED', type(e).__name__, e); traceback.print_exc(limit=2)

# ------------------------------------------------------------------ A survival
def fA():
    d = LP[LP['Purchase Date_d'].notna()].copy()
    d = d[d['Purchase Date_d'] >= '2024-01-01']
    d['churn'] = d['Churned Date_d']
    d['ended'] = d[['Churned Date_d', 'End Date_d']].min(axis=1)
    d['life'] = (d['ended'] - d['Purchase Date_d']).dt.days
    d['life'] = d['life'].where(d['life'] >= 0)
    # where no end date exists, censored at days since purchase
    d['cens'] = (pd.Timestamp('2026-10-18') - d['Purchase Date_d']).dt.days
    d['obs'] = d['life'].fillna(d['cens'])
    print('Cohort survival: membership still in force N days after purchase (paid Bandra, bought 2024+)')
    print(f"{'days':>6} {'at risk':>9} {'ended by then':>14} {'surviving':>10}")
    for n in [7, 14, 30, 45, 60, 90, 120, 180, 270, 365]:
        risk = d[d['obs'] >= n]
        if not len(risk): continue
        surv = ((d['obs'] > n) | d['life'].isna()).sum() / len(d) * 100
        print(f'{n:>6} {len(risk):>9,} {int(d["life"].le(n).sum()):>14,} {surv:>9.1f}%')
    print('\nMedian days-to-end by purchase year:')
    print(d.groupby(d['Purchase Date_d'].dt.year)['obs'].median().to_string())
blk('A. MEMBERSHIP SURVIVAL CURVE', fA)

# ------------------------------------------------------------------ B not activated
def fB():
    n = L[L['Derived Status'] == 'Not Activated']
    print(f'Not Activated: {len(n):,} Bandra memberships, {n["Member ID"].nunique():,} members')
    print(f'  cash taken: ₹{n["Amount Paid"].sum():,.0f} | mean ticket ₹{n["Amount Paid"].mean():,.0f}')
    print(f'  mean days between purchase and membership end: {n["Membership Duration (Days)"].mean():.1f}')
    print('  by product:'); print(n['Membership Name'].value_counts().head(8).to_string())
    print('  by purchase year:'); print(n['Purchase Date_d'].dt.year.value_counts().sort_index().to_string())
    print(f'\n  of these, how many had ALSO paid for something else at Bandra? '
          f'{n["Member ID"].isin(LP["Member ID"]).mean()*100:.1f}%')
blk('B. BOUGHT AND NEVER CAME', fB)

# ------------------------------------------------------------------ C formats
def fC():
    import d1_data as D
    X = pd.read_csv(E.U + 'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
    X = X[X['Location'] == E.B].copy(); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
    for c in ['Capacity','CheckedIn','LateCancelled','Booked','Complimentary','Revenue','Memberships','Packages','IntroOffers','SingleClasses','Classes']:
        X[c] = E.num(X[c]).fillna(0)
    X['cap'] = X['Capacity']/X['Classes'].clip(lower=1)
    x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')]
    x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')]
    CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False,
                     usecols=['Member ID','Location','Date (IST)','Checked In','Cleaned Class','Duration (Minutes)','Teacher Name'])
    CK = CK[(CK['Location'] == E.B) & (CK['Checked In'] == True)].copy()
    CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
    CK['dur'] = E.num(CK['Duration (Minutes)']).replace(0, np.nan)
    c26 = CK[(CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')]
    print('Duration data available for Sept-26 attendances:', int(c26['dur'].notna().sum()), 'of', len(c26))
    print('Duration by format (minutes):')
    print(c26.groupby('Cleaned Class')['dur'].agg(['size','median','mean']).round(0).to_string())
    g = x26.groupby('Class').agg(sessions=('SessionID','size'), seats=('Capacity','sum'), att=('CheckedIn','sum'),
        booked=('Booked','sum'), lc=('LateCancelled','sum'), comp=('Complimentary','sum'), rev=('Revenue','sum'),
        intro=('IntroOffers','sum'), single=('SingleClasses','sum'), memb=('Memberships','sum'), pkg=('Packages','sum'))
    g['fill'] = (g['att']/g['seats']*100).round(1)
    g['rev_class'] = (g['rev']/g['sessions']).round(0)
    g['rev_head'] = (g['rev']/g['att'].replace(0,np.nan)).round(0)
    g['cancel_rate'] = (g['lc']/g['booked'].replace(0,np.nan)*100).round(1)
    g['sub_rate'] = ((g['booked']-g['att'])/g['booked'].replace(0,np.nan)*100).round(1)
    print('\nFORMAT MATRIX, September 2026:')
    print(g.sort_values('att', ascending=False).to_string())
    print('\nMEMBERS per format (unique, Sept-2026) and their repeat inside the month:')
    rows=[]
    for cls, s in c26.groupby('Cleaned Class'):
        vc = s.groupby('Member ID').size()
        rows.append(dict(fmt=cls.replace('Studio ',''), members=len(vc), visits=len(s),
                         per_member=round(len(s)/max(len(vc),1),2),
                         regulars= int((vc>=4).sum()), regular_pct=round((vc>=4).mean()*100,1)))
    print(pd.DataFrame(rows).sort_values('members', ascending=False).to_string(index=False))
blk('C. FORMAT MATRIX', fC)

# ------------------------------------------------------------------ D format & lapse
def fD():
    d = LP[LP['Favorite Format'].notna() & LP['Days Since Last Visit'].notna()].copy()
    d['fav'] = d['Favorite Format'].str.replace('Studio ','').str.title().str.replace('Powercycle','PowerCycle')
    g = d.groupby('fav').agg(members=('Member ID','nunique'), ticket=('Amount Paid','mean'),
        sessions=('Total Sessions Completed','mean'), since=('Days Since Last Visit','mean'),
        lifetime=('Membership Duration (Days)','mean'))
    print('Behaviour by the format a member used most:')
    print(g[g['members']>=40].round(1).sort_values('members', ascending=False).to_string())
    print('\nMulti-format vs single-format members (Formats Attended is a text list):')
    d2 = LP.copy()
    d2['nf'] = d2['Formats Attended'].fillna('').apply(lambda s: 0 if not s else len([x for x in str(s).split(',') if x.strip()]))
    print(d2.groupby('nf').agg(members=('Member ID','nunique'), ticket=('Amount Paid','mean'),
        sessions=('Total Sessions Completed','mean'), lifetime=('Membership Duration (Days)','mean'),
        last30=('Visits in Last 30 Days','mean'), since=('Days Since Last Visit','mean')).round(1).head(8).to_string())
blk('D. FORMAT PREFERENCE AND BEHAVIOUR', fD)

# ------------------------------------------------------------------ E cancellations
def fE():
    CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False,
        usecols=['Member ID','Location','Date (IST)','Checked In','Is Late Cancelled','Cleaned Class','Time','Day of Week','Teacher Name'])
    CK = CK[CK['Location'] == E.B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
    LC = CK[CK['Is Late Cancelled'] == True]
    print('Late cancellations in the live ledger (all time, Bandra):', len(LC))
    for y in (2024, 2025, 2026):
        s = LC[(LC['dt'] >= f'{y}-01-01') & (LC['dt'] < f'{y+1}-01-01')]
        a = CK[(CK['Checked In'] == True) & (CK['dt'] >= f'{y}-01-01') & (CK['dt'] < f'{y+1}-01-01')]
        print(f'  {y}: {len(s):>6,} late cancellations against {len(a):>6,} attendances = {len(s)/max(len(a),1)*100:.1f}% of the book')
    print('\n2026 by month:')
    print(LC[LC['dt']>='2026-01-01'].groupby(LC['dt'].dt.to_period('M')).size().to_string())
    s = LC[(LC['dt'] >= '2026-09-01') & (LC['dt'] < '2026-10-01')]
    a = CK[(CK['Checked In'] == True) & (CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')]
    print(f'\nSeptember 2026: {len(s)} late cancellations against {len(a)} attendances')
    print('by format:'); print(s['Cleaned Class'].value_counts().head(10).to_string())
    print('\nby day:'); print(s['Day of Week'].value_counts().to_string())
    print('\nby hour of the cancelled class:')
    s = s.assign(hr=pd.to_numeric(s['Time'].astype(str).str[:2], errors='coerce'))
    print(s['hr'].value_counts().sort_index().to_string())
    print('\nwho cancels: concentration among Sept-26 late cancellers')
    vc = s.groupby('Member ID').size()
    print(f'  {vc.sum()} cancellations from {len(vc)} members | median {vc.median():.0f} | mean {vc.mean():.2f} | max {vc.max()}')
    print(f'  top 10 members account for {vc.nlargest(10).sum()/vc.sum()*100:.1f}% of September cancellations')
    print(f'  members with 3+ cancellations: {int((vc>=3).sum())} = {(vc>=3).sum()/len(vc)*100:.1f}% of cancellers')
    print('\nLate-cancel rate by trainer (Sept-26, sessions with >=10 bookings):')
    import d1_data as D
    X = D.XB.copy(); x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')]
    t = x26.groupby('Trainer').agg(sessions=('SessionID','size'), booked=('Booked','sum'), lc=('LateCancelled','sum'), att=('CheckedIn','sum'))
    t['lc_rate'] = (t['lc']/t['booked'].replace(0,np.nan)*100).round(1)
    print(t[t['booked']>=60].sort_values('lc_rate', ascending=False).round(1).to_string())
blk('E. LATE CANCELLATIONS', fE)

# ------------------------------------------------------------------ F discounts
def fF():
    import d1_data as D
    SB = D.SB.copy()
    SB['disc'] = E.num(SB['Discount Value In Currency']).fillna(0)
    SB['gross'] = SB['val'] + SB['disc']
    SB['has_disc'] = SB['disc'] > 0
    SB['yr'] = SB['dt'].dt.year; SB['mo'] = SB['dt'].dt.to_period('M')
    print('Discount taken at Bandra, all months on file:')
    t = SB.groupby('yr').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'),
                             discount_sales=('has_disc','sum'))
    t['depth'] = (t['disc']/t['gross']*100).round(2)
    t['pct_sales_discounted'] = (t['discount_sales']/t['sales']*100).round(1)
    print(t.round(0).to_string())
    print('\nBy month, 2026:')
    t2 = SB[SB['yr']==2026].groupby('mo').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('has_disc','sum'))
    t2['depth'] = (t2['disc']/t2['gross']*100).round(2); t2['pct'] = (t2['n']/t2['sales']*100).round(1)
    print(t2.round(0).to_string())
    print('\nDISCOUNT EFFECTIVENESS: do discounted buyers come back?')
    first = SB.sort_values('dt').groupby('Member ID').agg(fd=('dt','min'), fdisc=('has_disc','first'))
    later = SB.groupby('Member ID').agg(nd=('dt','max'), n=('Sale ID','nunique'), v=('val','sum'))
    f = first.join(later)
    f = f[f['fd'] < '2026-09-01']
    f['obs'] = (pd.Timestamp('2026-10-18') - f['fd']).dt.days
    f = f[f['obs'] >= 180]
    t3 = f.groupby('fdisc').agg(buyers=('n','size'), repurchase_pct=('n', lambda x:(x>1).mean()*100),
                                txns=('n','mean'), lifetime=('v','mean'))
    print(t3.round(1).to_string())
    print('\nSAME, controlling for the product bought first:')
    for k in ['Studio Newcomers 2 For 1','Studio 1 Month Unlimited','Studio 12 Class Package','Session']:
        s = SB.sort_values('dt')
        s = s[s['Cleaned Product'] == k]
        if len(s) < 30: continue
        ff = s.groupby('Member ID').agg(fd=('dt','min'), fdisc=('has_disc','first')).join(later)
        ff['obs'] = (pd.Timestamp('2026-10-18') - ff['fd']).dt.days
        ff = ff[ff['obs'] >= 180]
        if len(ff) < 20: continue
        print(f'  {k}: n={len(ff)}, repeat rate discounted {ff[ff["fdisc"]]["n"].gt(1).mean()*100:.1f}% '
              f'vs full price {ff[~ff["fdisc"]]["n"].gt(1).mean()*100:.1f}% | '
              f'LTV ₹{ff[ff["fdisc"]]["v"].mean():,.0f} vs ₹{ff[~ff["fdisc"]]["v"].mean():,.0f}')
blk('F. DISCOUNTS AND WHETHER THEY WORK', fF)

# ------------------------------------------------------------------ G leads
def fG():
    print('BANDRA SALES FUNNEL (all leads on file)')
    print(f'  leads {len(LB):,}')
    print('  by status:'); print(LB['Status'].value_counts().head(10).to_string())
    print(f"\n  trial completed {int((LB['Trial Status']=='Trial Completed').sum()):,} "
          f"({(LB['Trial Status']=='Trial Completed').mean()*100:.1f}%)")
    print(f"  converted {int((LB['Conversion Status']=='Converted').sum()):,} "
          f"({(LB['Conversion Status']=='Converted').mean()*100:.1f}%)")
    print(f"  retained {int((LB['Retention Status']=='Retained').sum()):,} "
          f"({(LB['Retention Status']=='Retained').mean()*100:.1f}%)")
    print('\nFOLLOW-UP CADENCE vs OUTCOME')
    g = LB.groupby('n_followup').agg(leads=('ID','size'),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100),
        ltv=('LTV','mean'), visits=('Visits','mean'))
    print(g.round(2).to_string())
    print('\n  Same, on leads created in the last 12 months only:')
    r = LB[LB['Created At_d'] >= '2025-10-01']
    print(r.groupby('n_followup').agg(leads=('ID','size'),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100), ltv=('LTV','mean')).round(2).to_string())
    print('\nSOURCE ECONOMICS, Bandra:')
    g = LB.groupby('Source Name').agg(leads=('ID','size'),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100),
        ltv=('LTV','mean'), visits=('Visits','mean'))
    print(g[g['leads']>=25].round(1).sort_values('won', ascending=False).to_string())
    print('\nASSOCIATE PERFORMANCE (leads handled):')
    g = LB.groupby('Associate').agg(leads=('ID','size'),
        followed=('n_followup', lambda x:(x>0).mean()*100),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100), ltv=('LTV','mean'))
    print(g[g['leads']>=60].round(1).sort_values('leads', ascending=False).to_string())
    print('\nRESPONSE SPEED: days from lead creation to first follow-up')
    d = LB[LB['Follow Up 1 Date_d'].notna()].copy()
    d['gap'] = (d['Follow Up 1 Date_d'] - d['Created At_d']).dt.days
    d = d[d['gap'] >= 0]
    print(f'  n={len(d):,} | median {d["gap"].median():.0f} days | mean {d["gap"].mean():.1f}')
    d['b'] = pd.cut(d['gap'], [-1,0,1,3,7,999], labels=['same day','next day','2–3 days','4–7 days','over a week'])
    print(d.groupby('b', observed=True).agg(leads=('ID','size'),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100), ltv=('LTV','mean')).round(2).to_string())
    print('\nLEAD VOLUME AND OUTCOME BY YEAR (Bandra):')
    print(LB.groupby(LB['Created At_d'].dt.year).agg(leads=('ID','size'),
        trial=('Trial Status', lambda x:(x=='Trial Completed').mean()*100),
        won=('Status', lambda x:(x=='Won').mean()*100), ltv=('LTV','mean')).round(1).to_string())
blk('G. LEADS INTELLIGENCE', fG)
