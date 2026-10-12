"""Round-5 deep mining pass: controlled trainer comparisons, leakage, teaching economics, first-product LTV,
member-base width vs depth, monthly retention, discipline mix, payment methods, concentration."""
import pandas as pd, numpy as np, sys
sys.path.insert(0, '/home/user/analysis3')
import e1_data as E
import d1_data as D

pd.set_option('display.width', 220); pd.set_option('display.max_columns', 50)
OUT = []
def blk(h):
    OUT.append('\n' + '=' * 100 + f'\n{h}\n' + '=' * 100)
def pr(x):
    OUT.append(str(x))
def run(name, fn):
    try:
        fn()
    except Exception as e:
        OUT.append(f'!! {name} FAILED: {type(e).__name__}: {e}')

U = E.U
TODAY = pd.Timestamp('2026-10-18')
X = D.XB.copy()
X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()
S = X[X['dt'] >= '2026-01-01'].copy()
S['slot'] = S['Class'].astype(str) + ' | ' + S['Day'].astype(str) + ' | ' + S['Time'].astype(str)

# ============================================================ 1 controlled trainer comparison
def f1():
    g = S.groupby('slot').agg(n=('SessionID','size'), trainers=('Trainer','nunique'), cap=('cap','mean'))
    rows = []
    for slot, r in g[g['trainers'] >= 2].iterrows():
        sub = S[S['slot'] == slot]
        t = sub.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','mean'), rev=('Revenue','mean'), lc=('LateCancelled','mean'))
        t = t[t['n'] >= 3]
        if len(t) < 2: continue
        t = t.sort_values('att', ascending=False)
        rows.append(dict(slot=slot, n_sess=int(r['n']), trainers=len(t), best=t.index[0], best_att=t['att'].iloc[0],
                         worst=t.index[-1], worst_att=t['att'].iloc[-1], spread=t['att'].iloc[0] - t['att'].iloc[-1],
                         spread_pct=(t['att'].iloc[0] - t['att'].iloc[-1]) / max(t['att'].iloc[-1], .01) * 100, cap=r['cap']))
    SLOT = pd.DataFrame(rows).sort_values('spread', ascending=False)
    pr(f'slots compared: {len(SLOT)} | mean spread {SLOT["spread"].mean():.1f} attendees | median {SLOT["spread"].median():.1f}')
    pr(f'slots where the spread exceeds 4 attendees: {int((SLOT["spread"] > 4).sum())} = {(SLOT["spread"] > 4).mean()*100:.0f}%')
    pr(f'mean attendance of the best trainer in each slot: {SLOT["best_att"].mean():.1f} | worst: {SLOT["worst_att"].mean():.1f}')
    pr(SLOT.head(16).to_string(index=False, float_format=lambda v: f'{v:,.1f}'))
    rows2 = []
    for _, r in SLOT.iterrows():
        sub = S[S['slot'] == r['slot']]
        t = sub.groupby('Trainer')['CheckedIn'].mean()
        t = t[sub.groupby('Trainer').size() >= 3]
        m = t.mean()
        for tr, v in t.items():
            rows2.append(dict(trainer=tr, slot=r['slot'], vs_slot_mean=v - m, att=v))
    P = pd.DataFrame(rows2)
    tp = P.groupby('trainer').agg(slots=('slot','size'), avg_vs_slot=('vs_slot_mean','mean'), avg_att=('att','mean'))
    pr('\nper-trainer average premium against the mean of the identical slots:')
    pr(tp[tp['slots'] >= 4].sort_values('avg_vs_slot', ascending=False).round(1).to_string())

# ============================================================ 2 room size vs fill
def f2():
    b = [0, 10, 14, 18, 22, 40]; lb = ['<=10 seats','11-14','15-18','19-22','23+']
    X['cband'] = pd.cut(X['cap'], b, labels=lb)
    cb = X.groupby('cband', observed=True).agg(sessions=('SessionID','size'), att=('CheckedIn','mean'), cap=('cap','mean'), rev=('Revenue','mean'))
    cb['fill'] = cb['att'] / cb['cap'] * 100
    pr('ALL MONTHS ON FILE'); pr(cb.round(1).to_string())
    c26 = x26.assign(cband=pd.cut(x26['cap'], b, labels=lb))
    cb2 = c26.groupby('cband', observed=True).agg(sessions=('SessionID','size'), att=('CheckedIn','mean'), cap=('cap','mean'), rev=('Revenue','mean'))
    cb2['fill'] = cb2['att'] / cb2['cap'] * 100
    pr('\nSEPT 2026'); pr(cb2.round(1).to_string())

# ============================================================ 3 booking leakage
def f3():
    x26['noshow'] = (x26['Booked'] - x26['CheckedIn'] - x26['LateCancelled']).clip(lower=0)
    pr(f"booked {x26['Booked'].sum():,.0f} | attended {x26['CheckedIn'].sum():,.0f} | late cancelled {x26['LateCancelled'].sum():,.0f} | no-show {x26['noshow'].sum():,.0f}")
    pr(f"booked-to-attended conversion {x26['CheckedIn'].sum()/x26['Booked'].sum()*100:.1f}%")
    f = x26.groupby('Class').agg(booked=('Booked','sum'), att=('CheckedIn','sum'), lc=('LateCancelled','sum'), ns=('noshow','sum'), sess=('SessionID','size'))
    f['conv'] = f['att'] / f['booked'] * 100; f['ns_rate'] = f['ns'] / f['booked'] * 100
    pr('\nby format (5+ sessions):'); pr(f[f['sess'] >= 5].sort_values('conv', ascending=False).round(1).to_string())
    ab = X.groupby(X['dt'].dt.year).agg(booked=('Booked','sum'), att=('CheckedIn','sum'), lc=('LateCancelled','sum'))
    ab['conv'] = ab['att'] / ab['booked'] * 100; ab['lc_rate'] = ab['lc'] / ab['booked'] * 100
    pr('\nall time by year:'); pr(ab.round(1).to_string())

# ============================================================ 4 hosted classes
def f4():
    h26 = x26[x26['Class'] == 'Studio Hosted Class']; ha = X[X['Class'] == 'Studio Hosted Class']
    pr(f"Sept-26: {len(h26)} sessions | {h26['CheckedIn'].sum():,.0f} attendees | revenue Rs {h26['Revenue'].sum():,.0f} | seats put on {h26['Capacity'].sum():,.0f}")
    pr(f"all time: {len(ha)} sessions | {ha['CheckedIn'].sum():,.0f} attendees | revenue Rs {ha['Revenue'].sum():,.0f}")

# ============================================================ 5 first purchase -> LTV
def f5():
    N9 = pd.read_csv(U + 'Day End Report - Part 1 - New (9).csv', low_memory=False)
    N9 = N9[N9['First Visit Location'] == E.B].copy()
    for c in ['Ltv','No of Visits','Days To Second Visit','Visits Per Month','Visits Post Trial','Late Cancel Rate Post Trial',
              'Avg Purchase Value Post Trial','Total Purchases All Time','Days Active','First Purchase Value']:
        N9[c] = E.num(N9[c])
    pr(f'Bandra first-timers on file: {len(N9):,}')
    fp = N9[N9['First Purchase Post Trial'].notna()].groupby('First Purchase Post Trial').agg(
        people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'), days=('Days Active','mean'),
        vpm=('Visits Per Month','mean'))
    fp = fp[fp['people'] >= 25].sort_values('ltv', ascending=False)
    pr('\nby the product they first bought:'); pr(fp.round(0).to_string())
    N9['d2'] = pd.cut(N9['Days To Second Visit'], [-1, 1, 3, 7, 14, 30, 100000],
                      labels=['same/next day','2-3 days','4-7 days','8-14 days','15-30 days','31+ or never'])
    sp = N9.groupby('d2', observed=True).agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'),
                                             vpm=('Visits Per Month','mean'), retained=('Retention Status', lambda x: (x == 'Retained').mean()*100))
    pr('\nby speed to the second visit:'); pr(sp.round(0).to_string())
    sr = N9.groupby('Source').agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'), vpm=('Visits Per Month','mean'))
    pr('\nby first-visit source:'); pr(sr[sr['people'] >= 30].sort_values('ltv', ascending=False).round(0).to_string())
    ft = N9.groupby('First Visit Type').agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'), vpm=('Visits Per Month','mean'))
    pr('\nby first-visit type:'); pr(ft[ft['people'] >= 30].round(0).to_string())
    N9['lq'] = pd.qcut(N9['Ltv'].rank(method='first'), 4, labels=['bottom quartile','second','third','top quartile'])
    pr('\nlifetime-value quartile against behaviour:')
    pr(N9.groupby('lq', observed=True).agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean'),
        vpm=('Visits Per Month','mean'), late_cancel=('Late Cancel Rate Post Trial','mean'),
        payments=('Total Purchases All Time','mean'), days=('Days Active','mean')).round(1).to_string())
    pr('\nconversion speed bucket:')
    pr(N9.groupby('Conversion Speed Bucket').agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean')).round(0).to_string())
    pr('\nlifecycle status:')
    pr(N9.groupby('Lifecycle Status').agg(people=('Member Id','size'), ltv=('Ltv','mean'), visits=('No of Visits','mean')).round(0).to_string())
    return N9

# ============================================================ 6 teaching economics
def f6():
    PY_ = pd.read_csv(U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
    PY_ = PY_[PY_['Location'] == E.B].copy()
    for c in ['Total Sessions','Total Non-Empty Sessions','Total Empty Sessions','Total Customers','Total Paid','Retained','New','Converted',
              'Cycle Sessions','Cycle Paid','Strength Sessions','Strength Paid','Barre Sessions','Barre Paid']:
        PY_[c] = E.num(PY_[c])
    PY_['mo'] = PY_['Month Year'].astype(str)
    zz = PY_.groupby('mo').agg(sessions=('Total Sessions','sum'), empty=('Total Empty Sessions','sum'),
                               pay=('Total Paid','sum'), cust=('Total Customers','sum'), new=('New','sum'), ret=('Retained','sum'))
    zz['empty_pct'] = zz['empty'] / zz['sessions'] * 100
    zz['pay_per_cust'] = zz['pay'] / zz['cust']
    pr('monthly teaching payroll, Bandra:'); pr(zz.round(1).to_string())
    last = PY_[PY_['mo'] == PY_['mo'].max()]
    lm = X[(X['dt'] >= '2026-08-01') & (X['dt'] < '2026-09-01')]
    sess = lm.groupby('Trainer').agg(sessions=('SessionID','size'), att=('CheckedIn','sum'), rev=('Revenue','sum'),
                                     empty=('CheckedIn', lambda x: (x == 0).sum()))
    J = sess.join(last.set_index('Teacher Name')[['Total Paid','Total Customers','Cycle Sessions','Strength Sessions','Barre Sessions']], how='outer')
    J['pay_per_session'] = J['Total Paid'] / J['sessions']
    J['cost_per_attendee'] = J['Total Paid'] / J['att']
    J['revenue_per_attendee'] = J['rev'] / J['att']
    J['empty_share'] = J['empty'] / J['sessions'] * 100
    pr('\nper-teacher, August 2026 (last full month on file):')
    pr(J.sort_values('sessions', ascending=False).round(0).to_string())
    pr(f"\nstudio teaching pay that month: Rs {last['Total Paid'].sum():,.0f} | sessions {last['Total Sessions'].sum():,.0f} "
       f"| empty {last['Total Empty Sessions'].sum():,.0f} = {last['Total Empty Sessions'].sum()/max(last['Total Sessions'].sum(),1)*100:.1f}%")
    ds = PY_.groupby('mo').agg(cyc_s=('Cycle Sessions','sum'), cyc_p=('Cycle Paid','sum'), st_s=('Strength Sessions','sum'),
                               st_p=('Strength Paid','sum'), ba_s=('Barre Sessions','sum'), ba_p=('Barre Paid','sum'))
    pr('\ndiscipline mix and pay per session:')
    dd = pd.DataFrame({'cycle_sessions': ds['cyc_s'], 'cycle_pay_per_session': ds['cyc_p']/ds['cyc_s'],
                       'strength_sessions': ds['st_s'], 'strength_pay_per_session': ds['st_p']/ds['st_s'].replace(0, np.nan),
                       'barre_sessions': ds['ba_s'], 'barre_pay_per_session': ds['ba_p']/ds['ba_s'].replace(0, np.nan)})
    pr(dd.round(1).to_string())

# ============================================================ 7 payment method, concentration, discount
def f7():
    SB = D.SB.copy()
    SB['disc'] = E.num(SB['Discount Value In Currency']).fillna(0)
    SB['yr'] = SB['dt'].dt.year
    for y in (2025, 2026):
        s = SB[(SB['dt'] >= f'{y}-09-01') & (SB['dt'] < f'{y}-10-01')]
        t = s.groupby('Payment Method').agg(n=('Sale ID','size'), val=('val','sum')).sort_values('val', ascending=False)
        t['pct'] = t['val'] / t['val'].sum() * 100
        pr(f'\npayment method {y}:'); pr(t.round(0).to_string())
    s26 = SB[SB['yr'] == 2026].assign(gross=lambda d: d['val'] + d['disc'], hd=lambda d: d['disc'] > 0)
    sd = s26.groupby('Sold By').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('hd','sum'))
    sd['depth'] = sd['disc'] / sd['gross'] * 100; sd['pct_sales'] = sd['n'] / sd['sales'] * 100
    pr('\ndiscount depth by seller, 2026 (20+ sales):'); pr(sd[sd['sales'] >= 20].sort_values('depth', ascending=False).round(1).to_string())
    sp = s26.groupby('Cleaned Product').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('hd','sum'))
    sp['depth'] = sp['disc'] / sp['gross'] * 100; sp['pct_sales'] = sp['n'] / sp['sales'] * 100
    pr('\ndiscount depth by product, 2026 (15+ sales):'); pr(sp[sp['sales'] >= 15].sort_values('depth', ascending=False).round(1).to_string())
    pr('\ndiscount code usage, 2026:')
    dc = s26[s26['hd']].groupby('Discount Code').agg(n=('Sale ID','size'), disc=('disc','sum')).sort_values('disc', ascending=False)
    pr(dc.head(16).round(0).to_string())
    r12 = SB[SB['dt'] >= '2025-10-01']
    per = r12.groupby('Member ID')['val'].sum().sort_values(ascending=False)
    pr(f"\nbuyers in the last 12 months: {len(per):,} | total Rs {per.sum():,.0f}")
    for k in (10, 25, 50, 100, 200):
        if len(per) > k: pr(f'  top {k} buyers = {per.head(k).sum()/per.sum()*100:.1f}% of sales')
    pr(f'  one-purchase-only buyers: {int((r12.groupby("Member ID")["Sale ID"].nunique()==1).sum())} of {r12["Member ID"].nunique()}')
    pr('\nrevenue by category, Sept-26 vs Sept-25:')
    cc = SB[(SB['dt'] >= '2025-09-01') | (SB['dt'] >= '2026-09-01')].copy()
    cc = cc.assign(yr=cc['dt'].dt.year, cat=cc['Cleaned Category'])
    cc = cc[cc['dt'].dt.month == 9]
    pr(cc.pivot_table(index='cat', columns='yr', values='val', aggfunc='sum').fillna(0).round(0).to_string())
    pr('\npurchase type, Sept-26:')
    pr(SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')].groupby('Purchase Type').agg(n=('Sale ID','size'), val=('val','sum')).round(0).to_string())

# ============================================================ 9 format adjacency
def f9():
    CK = D.CK
    A26 = CK[(CK['Checked In'] == True) & (CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')]
    mm = A26.groupby('Member ID')['Cleaned Class'].apply(lambda s: sorted(set(s)))
    from collections import Counter
    cnt = Counter(); solo = Counter()
    for f in mm:
        if len(f) == 1: solo[f[0]] += 1
        for i in range(len(f)):
            for j in range(i + 1, len(f)):
                cnt[(f[i].replace('Studio ', ''), f[j].replace('Studio ', ''))] += 1
    pr('top format pairs among Sept-26 members:'); pr(pd.Series(cnt).sort_values(ascending=False).head(12).to_string())
    pr('\nmembers who came in exactly one format in Sept-26:')
    pr(pd.Series(solo).sort_values(ascending=False).head(10).to_string())

# ============================================================ 10 when people buy
def f10():
    SB = D.SB.copy()
    SB['hr'] = SB['Created At'].astype(str).str.extract(r'(\d{1,2}):\d{2}').astype(float)
    tt = SB[SB['dt'] >= '2026-01-01']
    pr(tt.groupby(tt['dt'].dt.day_name())['val'].agg(['size','sum']).reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).round(0).to_string())
    pr('\nby hour (2026):'); pr(tt.groupby(tt['hr'])['val'].agg(['size','sum']).round(0).to_string())
    pr('\nby day of month, 2026:'); pr(tt.groupby(tt['dt'].dt.day)['val'].agg(['size','sum']).round(0).to_string())

# ============================================================ 11 teacher retention economics
def f11():
    PY_ = pd.read_csv(U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
    PY_ = PY_[PY_['Location'] == E.B].copy(); PY_['mo'] = PY_['Month Year'].astype(str)
    for c in ['Converted','Conversion Rate','Retained','Retention Rate','New','Total Customers','Total Sessions','Total Empty Sessions','Total Non-Empty Sessions']:
        PY_[c] = E.num(PY_[c])
    last6 = PY_[PY_['mo'] >= sorted(PY_['mo'].unique())[-6]]
    t = last6.groupby('Teacher Name').agg(months=('mo','nunique'), sessions=('Total Sessions','mean'),
        empty=('Total Empty Sessions','mean'), cust=('Total Customers','sum'), new=('New','sum'), conv=('Converted','sum'),
        ret=('Retained','sum'))
    t['conv_rate'] = t['conv'] / t['new'].replace(0, np.nan) * 100
    t['ret_rate'] = t['ret'] / t['cust'].replace(0, np.nan) * 100
    pr('last six months on file, by teacher:')
    pr(t[t['months'] >= 3].sort_values('conv_rate', ascending=False).round(1).to_string())

for nm, fn in [('1 controlled trainer comparison', f1), ('2 room size vs fill', f2), ('3 booking leakage', f3),
               ('4 hosted classes', f4), ('5 first purchase to LTV', f5), ('6 teaching economics', f6),
               ('7 payment method / concentration / discount', f7), ('9 format adjacency', f9),
               ('10 when people buy', f10), ('11 teacher conversion', f11)]:
    OUT.append(f'\n\n##################### BLOCK {nm} #####################')
    run(nm, fn)

open('/home/user/analysis3/p6_out.txt', 'w').write('\n'.join(OUT))
print('\n'.join(OUT))
