"""Round-5 mining pass, part 2: slots, no-shows, capacity, payroll cost, sales."""
import pandas as pd, numpy as np
import d1_data as D
pd.set_option('display.width', 215); pd.set_option('display.max_columns', 70)
U = '/home/user/uploads/'; B = 'Supreme HQ, Bandra'
def hdr(t): print('\n' + '=' * 104 + f'\n{t}\n' + '=' * 104)
def blk(t, f):
    hdr(t)
    try: f()
    except Exception as e:
        import traceback; print('  FAILED:', type(e).__name__, e); traceback.print_exc(limit=2)

X = pd.read_csv(U + 'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
X = X[X['Location'] == B].copy()
X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
for c in ['Capacity','CheckedIn','LateCancelled','Booked','NonPaid','Revenue','Complimentary','Memberships','Packages','IntroOffers','SingleClasses']:
    X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0)
X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
X['fill'] = X['CheckedIn'] / X['cap'].replace(0, np.nan)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()
x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')].copy()
print('x26', len(x26), 'x25', len(x25))

# ---------------------------------------------------------------- 8
def f8():
    print(f"{'':22} {'Sept-25':>10} {'Sept-26':>10} {'change':>10}")
    rows = [('Sessions', len(x25), len(x26)), ('Capacity on the board', x25['cap'].sum(), x26['cap'].sum()),
            ('Attended', x25['CheckedIn'].sum(), x26['CheckedIn'].sum()),
            ('Booked', x25['Booked'].sum(), x26['Booked'].sum()),
            ('Late cancelled', x25['LateCancelled'].sum(), x26['LateCancelled'].sum()),
            ('No-show (booked-att)', x25['Booked'].sum()-x25['CheckedIn'].sum(), x26['Booked'].sum()-x26['CheckedIn'].sum()),
            ('Complimentary seats', x25['Complimentary'].sum(), x26['Complimentary'].sum()),
            ('Non-paid seats', x25['NonPaid'].sum(), x26['NonPaid'].sum()),
            ('Booked per session', x25['Booked'].mean(), x26['Booked'].mean())]
    for lab, a, b in rows:
        ch = f'{(b/a-1)*100:+.1f}%' if a else '—'
        print(f'{lab:22} {a:>10,.1f} {b:>10,.1f} {ch:>10}')
    print('\nFill = attended / capacity. Occupancy of the booked book:')
    print(f"  Sept-25 booked/board {x25['Booked'].sum()/x25['cap'].sum()*100:.1f}% -> Sept-26 {x26['Booked'].sum()/x26['cap'].sum()*100:.1f}%")
    print(f"  of seats booked, attended rate: Sept-25 {x25['CheckedIn'].sum()/x25['Booked'].sum()*100:.1f}% -> Sept-26 {x26['CheckedIn'].sum()/x26['Booked'].sum()*100:.1f}%")
    print(f"  revenue per booked seat: Sept-25 {x25['Revenue'].sum()/x25['Booked'].sum():,.0f} -> Sept-26 {x26['Revenue'].sum()/x26['Booked'].sum():,.0f}")
    print(f"  revenue per capacity seat: Sept-25 {x25['Revenue'].sum()/x25['cap'].sum():,.0f} -> Sept-26 {x26['Revenue'].sum()/x26['cap'].sum():,.0f}")
blk('8. BOOKING BOOK, NO-SHOWS, COMPLIMENTARY SEATS', f8)

# ---------------------------------------------------------------- 9
def f9():
    d = x26[x26['cap'] >= 4].copy()
    d['cband'] = pd.cut(d['cap'], [0, 9, 11, 13, 100], labels=['<=9', '10-11', '12-13', '14+'])
    t = d.groupby('cband', observed=True).agg(sessions=('SessionID','size'), cap=('cap','mean'),
        att=('CheckedIn','mean'), fill=('fill','mean'), rev=('Revenue','sum'))
    t['fill'] = (t['fill']*100).round(1); t['cap'] = t['cap'].round(1); t['att'] = t['att'].round(2)
    t['rev_per_session'] = (t['rev']/t['sessions']).round(0)
    print('Room size vs how full it ran (Sept-2026):'); print(t.to_string())
    print('\nSame cut for Sept-2025:')
    d5 = x25[x25['cap'] >= 4].copy(); d5['cband'] = pd.cut(d5['cap'], [0,9,11,13,100], labels=['<=9','10-11','12-13','14+'])
    t5 = d5.groupby('cband', observed=True).agg(sessions=('SessionID','size'), fill=('fill','mean'), att=('CheckedIn','mean'))
    t5['fill'] = (t5['fill']*100).round(1); print(t5.round(2).to_string())
blk('9. ROOM SIZE vs FILL', f9)

# ---------------------------------------------------------------- 10
def f10():
    """Same slot, different trainer: the controlled comparison."""
    k = ['Day', 'Time', 'Class']
    g = x26.groupby(k).agg(sessions=('SessionID','size'), trainers=('Trainer','nunique'),
                           att=('CheckedIn','sum'), cap=('cap','sum'))
    g = g[(g['trainers'] >= 2) & (g['sessions'] >= 2)]
    print(f'Slots taught by 2+ trainers in Sept-2026: {len(g)}')
    rows = []
    for key, r in g.iterrows():
        sub = x26[(x26['Day'] == key[0]) & (x26['Time'] == key[1]) & (x26['Class'] == key[2])]
        per = sub.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','mean'),
                                         cap=('cap','mean'), rev=('Revenue','mean'))
        per['fill'] = per['att']/per['cap']*100
        if len(per) >= 2:
            lo, hi = per['fill'].min(), per['fill'].max()
            rows.append(dict(slot=f'{key[0][:3]} {key[1]}', fmt=key[2].replace('Studio ',''),
                             n_trainers=len(per), lo=round(lo,1), hi=round(hi,1), spread=round(hi-lo,1),
                             best=per['fill'].idxmax(), worst=per['fill'].idxmin(),
                             sessions=int(per['n'].sum())))
    t = pd.DataFrame(rows).sort_values('spread', ascending=False)
    print(t.head(24).to_string(index=False))
    if len(t):
        print(f"\nMedian within-slot spread {t['spread'].median():.1f} pts | mean {t['spread'].mean():.1f} | "
              f"slots where spread > 30 pts: {(t['spread']>30).sum()} of {len(t)}")
        # weighted: compare to overall trainer spread
        print('\nTrainer-level overall spread for reference (fill %):')
        tt = x26.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','sum'), cap=('cap','sum'))
        tt['fill'] = (tt['att']/tt['cap']*100).round(1); tt = tt[tt['n'] >= 5].sort_values('fill', ascending=False)
        print(tt.to_string())
blk('10. SAME SLOT, DIFFERENT TRAINER — CONTROLLED COMPARISON', f10)

# ---------------------------------------------------------------- 11
def f11():
    print('Revenue per attended head vs trainer pay: who covers their own cost?')
    print('Payroll is Aug-2026 (last available); sessions from Sept-2026 for comparability of ratios only.')
    P = pd.read_csv(U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
    P = P[P['Location'] == B].copy(); P['dt'] = pd.to_datetime(P['Month Year'], errors='coerce')
    pa = P[P['dt'] == '2026-08-01'].copy()
    for c in ['Total Sessions','Total Empty Sessions','Total Non-Empty Sessions','Total Customers','Total Paid',
              'Cycle Paid','Strength Paid','Barre Paid','Cycle Sessions','Strength Sessions','Barre Sessions']:
        pa[c] = pd.to_numeric(pa[c], errors='coerce').fillna(0)
    pa['pay_per_sess'] = pa['Total Paid']/pa['Total Sessions'].replace(0, np.nan)
    pa['cust_per_sess'] = pa['Total Customers']/pa['Total Sessions'].replace(0, np.nan)
    print(pa[['Teacher Name','Total Sessions','Total Empty Sessions','Total Customers','Total Paid',
              'pay_per_sess','cust_per_sess']].sort_values('Total Paid', ascending=False).round(0).to_string(index=False))
    print(f"\nTotal paid Aug-2026: ₹{pa['Total Paid'].sum():,.0f} on {pa['Total Sessions'].sum():.0f} sessions "
          f"= ₹{pa['Total Paid'].sum()/pa['Total Sessions'].sum():,.0f} per session")
    print(f"Empty sessions paid for: {pa['Total Empty Sessions'].sum():.0f} "
          f"({pa['Total Empty Sessions'].sum()/pa['Total Sessions'].sum()*100:.1f}% of sessions)")
    print('\nDiscipline pay split (Aug-2026):')
    for d in ['Cycle','Strength','Barre']:
        print(f"  {d:9} sessions {pa[d+' Sessions'].sum():>5.0f}  paid ₹{pa[d+' Paid'].sum():>9,.0f}  "
              f"per session ₹{pa[d+' Paid'].sum()/max(pa[d+' Sessions'].sum(),1):>7,.0f}")
    print('\nPayroll trend (Bandra, all months available):')
    t = P.groupby('dt').agg(teachers=('Teacher Name','nunique'), sessions=('Total Sessions','sum'),
                            paid=('Total Paid','sum'), customers=('Total Customers','sum'))
    t['pay_per_cust'] = (t['paid']/t['customers'].replace(0, np.nan)).round(0)
    t['pay_per_sess'] = (t['paid']/t['sessions']).round(0)
    print(t.round(0).to_string())
blk('11. PAYROLL COST RATIOS', f11)

# ---------------------------------------------------------------- 12
def f12():
    S = pd.read_csv(U + 'Sales - Raw - Sales (23).csv', low_memory=False)
    Sb = S[S['Calculated Location'] == B].copy()
    Sb['dt'] = pd.to_datetime(Sb['Payment Date'], errors='coerce', dayfirst=True)
    num = ['Payment Value','Discount Value In Currency','Sale Total Discount Value','Sale Item Quantity']
    for c in num: Sb[c] = pd.to_numeric(Sb[c].astype(str).str.replace(r'[,\s]','',regex=True), errors='coerce')
    s26 = Sb[(Sb['dt'] >= '2026-09-01') & (Sb['dt'] < '2026-10-01')]
    s25 = Sb[(Sb['dt'] >= '2025-09-01') & (Sb['dt'] < '2025-10-01')]
    print('PAYMENT METHOD (Sept-26 vs Sept-25):')
    a = s26.groupby('Payment Method')['Payment Value'].agg(['size','sum'])
    b = s25.groupby('Payment Method')['Payment Value'].agg(['size','sum'])
    j = a.join(b, lsuffix='_26', rsuffix='_25', how='outer').fillna(0)
    j['share_26'] = (j['sum_26']/j['sum_26'].sum()*100).round(1)
    print(j.round(0).to_string())
    print('\nPURCHASE TYPE:'); print(pd.crosstab(s26['Purchase Type'], s26['Cleaned Category'], values=s26['Payment Value'], aggfunc='sum').fillna(0).round(0).to_string())
    print('\nDISCOUNT CODE:'); print(s26.groupby('Discount Code').agg(n=('Payment Value','size'), rev=('Payment Value','sum'), disc=('Discount Value In Currency','sum')).sort_values('rev', ascending=False).head(12).round(0).to_string())
    print('\nSALE ITEM QUANTITY:'); print(s26['Sale Item Quantity'].value_counts().head(8).to_string())
    print('\nSOLD BY × discount behaviour (Sept-26):')
    g = s26.groupby('Sold By').agg(n=('Payment Value','size'), rev=('Payment Value','sum'),
                                   disc=('Discount Value In Currency','sum'))
    g['disc_depth'] = (g['disc']/(g['rev']+g['disc'])*100).round(1)
    g['avg_sale'] = (g['rev']/g['n']).round(0)
    print(g.sort_values('rev', ascending=False).round(0).to_string())
    print('\nFIRST-EVER PRODUCT -> 12-month repeat behaviour (cohort Jan-2025 to Sep-2025):')
    first = Sb.sort_values('dt').groupby('Member ID').agg(fd=('dt','min'), fp=('Cleaned Product','first'), fv=('Payment Value','first'))
    later = Sb.groupby('Member ID').agg(nd=('dt','max'), npurch=('Sale ID','nunique'), nval=('Payment Value','sum'))
    f = first.join(later, how='inner')
    f = f[(f['fd'] >= '2025-01-01') & (f['fd'] < '2025-10-01') & (f['nd']-f['fd']).dt.days >= 300]
    g = f.groupby('fp').agg(members=('npurch','size'), repeat_pct=('npurch', lambda x:(x>1).mean()*100),
                            avg_purch=('npurch','mean'), avg_value=('nval','mean'))
    print(g[g['members'] >= 3].sort_values('repeat_pct', ascending=False).round(1).to_string())
blk('12. SALES: METHODS, CODES, SELLERS, FIRST-PRODUCT RETENTION', f12)
