"""Lapse & churn mining."""
import pandas as pd, numpy as np, e1_data as E
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 60)
L, LP, LS = E.L, E.LP, E.LS
def hdr(t): print('\n' + '='*104 + f'\n{t}\n' + '='*104)
def blk(t, f):
    hdr(t)
    try: f()
    except Exception as e:
        import traceback; print('FAILED', type(e).__name__, e); traceback.print_exc(limit=2)

def f1():
    print('MEMBERSHIP LIFECYCLE, Bandra, every membership instance in the ledger')
    t = L.groupby('Derived Status').agg(instances=('Member ID','size'), members=('Member ID','nunique'))
    t['pct'] = (t['instances']/len(L)*100).round(1)
    print(t.sort_values('instances', ascending=False).to_string())
    print(f'\ntotal {len(L):,} instances from {L["Member ID"].nunique():,} distinct members')
    print('\nBy product family (paid only, Bandra):')
    fam = LP['Membership Name'].str.replace(r'^Studio ','',regex=True)
    t = LP.assign(fam=fam).groupby('fam').agg(sold=('Member ID','size'), members=('Member ID','nunique'),
            cash=('Amount Paid','sum'), lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100),
            renewed=('Derived Status', lambda x:(x.isin(['Renewed','Active','Renewal Grace Period'])).mean()*100),
            sessions=('Total Sessions Completed','mean'), days=('Membership Duration (Days)','mean'))
    t['avg_ticket']=(t['cash']/t['sold']).round(0)
    print(t[t['sold']>=40].sort_values('sold', ascending=False).round(1).to_string())
blk('1. THE SHAPE OF THE LEDGER', f1)

def f2():
    """Does duration predict churn?"""
    d = LP[LP['Membership Duration (Days)'].notna() & (LP['Membership Duration (Days)']>=0)].copy()
    d['band'] = pd.cut(d['Membership Duration (Days)'], [-1,1,7,30,60,90,180,400,10000],
                       labels=['same day','2–7 days','8–30 days','31–60 days','61–90 days','91–180 days','181–365 days','> 1 year'])
    t = d.groupby('band', observed=True).agg(memberships=('Member ID','size'), avg_ticket=('Amount Paid','mean'),
            sessions=('Total Sessions Completed','mean'), last30=('Visits in Last 30 Days','mean'),
            lapse_gap=('Lapse Gap (Days)','mean'), since=('Days Since Last Visit','mean'))
    print('Membership lifetime vs behaviour (paid Bandra memberships):')
    print(t.round(1).to_string())
    print(f"\nmedian membership lifetime {d['Membership Duration (Days)'].median():.0f} days | "
          f"mean {d['Membership Duration (Days)'].mean():.0f}")
    q = d['Membership Duration (Days)'].quantile([.25,.5,.75,.9]).round(0).to_dict()
    print('quartiles:', q)
    print('\nOf paid memberships that ran 30 days or less, how many sessions were completed?')
    short = d[d['Membership Duration (Days)']<=30]
    print(f'  {len(short):,} memberships | mean sessions {short["Total Sessions Completed"].mean():.2f} '
          f'| mean ticket ₹{short["Amount Paid"].mean():,.0f}')
blk('2. DURATION AND THE LAPSE CURVE', f2)

def f3():
    """Unused credit: did they use what they paid for?"""
    d = LP[LP['Sessions Used %'].notna()].copy()
    print(f'memberships with a countable session allowance: {len(d):,}')
    d['band'] = pd.cut(d['Sessions Used %'], [-1,10,25,50,75,99,100.1],
                       labels=['used ≤10%','11–25%','26–50%','51–75%','76–99%','used 100%'])
    t = d.groupby('band', observed=True).agg(memberships=('Member ID','size'), ticket=('Amount Paid','mean'),
            remaining=('Remaining Sessions','mean'), sessions=('Total Sessions Completed','mean'),
            since=('Days Since Last Visit','mean'), lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100))
    t['unused_value'] = (t['remaining']*d.groupby('band', observed=True)['Revenue Per Session'].mean()).round(0)
    print(t.round(1).to_string())
    tot_rem = d['Remaining Sessions'].sum()
    print(f'\nunused sessions across these memberships: {tot_rem:,.0f}')
    print(f"memberships that used 25% or less of what they bought: {int((d['Sessions Used %']<=25).sum()):,} "
          f"({(d['Sessions Used %']<=25).mean()*100:.1f}%)")
    print(f"memberships that used everything: {int((d['Sessions Used %']>=100).sum()):,} ({(d['Sessions Used %']>=100).mean()*100:.1f}%)")
blk('3. DID THEY USE WHAT THEY PAID FOR', f3)

def f4():
    """The decline signal before the lapse."""
    d = LP[LP['Attendance Decline Rate %'].notna()].copy()
    print(f"memberships with a computable attendance decline: {len(d):,}")
    d['dec'] = pd.cut(d['Attendance Decline Rate %'], [-1000,-50,-20,0,20,50,1000],
                      labels=['fell >50%','fell 20–50%','flat or small fall','rose slightly','rose 20–50%','rose >50%'])
    t = d.groupby('dec', observed=True).agg(memberships=('Member ID','size'), avg_visits=('Total Sessions Completed','mean'),
            since=('Days Since Last Visit','mean'), lapse_gap=('Lapse Gap (Days)','mean'),
            lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100))
    print(t.round(1).to_string())
    print(f"\nmean decline across all: {d['Attendance Decline Rate %'].mean():.1f}% | median {d['Attendance Decline Rate %'].median():.1f}%")
    print(f"share whose second half was worse than their first half: "
          f"{(d['Visits in Second Half']<d['Visits in First Half']).mean()*100:.1f}%")
    print(f"share whose second half was half the first or worse: "
          f"{(d['Visits in Second Half']<=d['Visits in First Half']*0.5).mean()*100:.1f}%")
blk('4. THE DECLINE BEFORE THE LAPSE', f4)

def f5():
    """Who is gone, who is winnable: recency distribution."""
    d = LP[LP['Days Since Last Visit'].notna()].copy()
    d['band'] = pd.cut(d['Days Since Last Visit'], [-1,30,60,90,180,365,10000],
                       labels=['0–30 days','31–60 days','61–90 days','91–180 days','181–365 days','over a year'])
    t = d.groupby('band', observed=True).agg(members=('Member ID','nunique'), instances=('Member ID','size'),
            ticket=('Amount Paid','mean'), sessions=('Total Sessions Completed','mean'),
            formats=('Formats Attended','first'))
    print('Recency since last visit (paid Bandra memberships):')
    print(t.round(1).to_string())
    for lab, lo, hi in [('still warm (<=60 days)',0,60), ('cooling (61–180)',61,180), ('gone (>180)',181,100000)]:
        s = d[d['Days Since Last Visit'].between(lo,hi)]
        print(f'  {lab:22s}: {s["Member ID"].nunique():>4} members | mean ticket ₹{s["Amount Paid"].mean():>8,.0f} | mean sessions {s["Total Sessions Completed"].mean():.2f}')
    print('\nFavourite format of the lapsed:')
    print(LP[LP['Derived Status']=='Lapsed']['Favorite Format'].value_counts().head(12).to_string())
    print('\nFavourite time of the lapsed:')
    print(LP[LP['Derived Status']=='Lapsed']['Favorite Half of Day'].value_counts().head(8).to_string())
blk('5. RECENCY, WINNABILITY, AND WHO THEY WERE', f5)

def f6():
    """Cancellation behaviour among the lapsed."""
    d = LP.copy()
    d['crate'] = d['Cancellation Rate %']
    d['nrate'] = d['No Show Rate %']
    g = d.groupby('Derived Status').agg(n=('Member ID','size'), cancels=('Total Cancellations','mean'),
        late=('Late Cancellations','mean'), noshow=('No Shows','mean'), crate=('Cancellation Rate %','mean'),
        nrate=('No Show Rate %','mean'), sessions=('Total Sessions Completed','mean'))
    print('Cancellation behaviour by current status (paid memberships):')
    print(g.round(2).to_string())
    print('\nDoes a high cancellation rate predict lapse?')
    d['cband'] = pd.cut(d['Cancellation Rate %'], [-1,0,10,25,50,1000], labels=['never cancels','up to 10%','11–25%','26–50%','over 50%'])
    t = d.groupby('cband', observed=True).agg(memberships=('Member ID','size'), sessions=('Total Sessions Completed','mean'),
            late=('Late Cancellations','mean'), since=('Days Since Last Visit','mean'),
            lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100))
    print(t.round(1).to_string())
    tot = d['Late Cancellations'].sum()
    top = d.nlargest(int(len(d)*0.10), 'Late Cancellations')
    print(f"\ntotal late cancellations in the ledger: {tot:,.0f} across {int((d['Late Cancellations']>0).sum()):,} memberships")
    print(f"the worst 10% of memberships account for {top['Late Cancellations'].sum()/max(tot,1)*100:.1f}% of them")
blk('6. CANCELLATION BEHAVIOUR AND LAPSE', f6)

def f7():
    """The 2-for-1 and other entry products: which entry leads to a lasting relationship?"""
    fam = LP['Membership Name'].str.replace(r'^Studio ','',regex=True).str.strip()
    d = LP.assign(fam=fam)
    key = ['Newcomers 2 For 1','1 Month Unlimited Membership','3 Month Unlimited Membership','4 Class Package',
           '8 Class Package','12 Class Package','10 Single Class Pack','Extended 10 Single Class Pack',
           'Single Class','20 Single Class Package','6 Month Unlimited','Annual Unlimited']
    rows=[]
    for k in key:
        s = d[d['fam']==k]
        if len(s) < 15: continue
        rows.append(dict(product=k, sold=len(s), members=s['Member ID'].nunique(),
            ticket=s['Amount Paid'].mean(), sessions=s['Total Sessions Completed'].mean(),
            lifetime_days=s['Membership Duration (Days)'].mean(),
            last30=s['Visits in Last 30 Days'].mean(),
            lapsed=(s['Derived Status']=='Lapsed').mean()*100,
            since=s['Days Since Last Visit'].mean()))
    t = pd.DataFrame(rows).sort_values('sold', ascending=False)
    print('Product-level outcomes (paid Bandra memberships):')
    print(t.round(1).to_string(index=False))
blk('7. PRODUCT BY PRODUCT', f7)

def f8():
    """Churn by purchase year — is retention getting worse?"""
    d = LP[LP['Purchase Date_d'].notna()].copy()
    d['yr'] = d['Purchase Date_d'].dt.year
    t = d[d['yr']>=2024].groupby('yr').agg(memberships=('Member ID','size'), members=('Member ID','nunique'),
        ticket=('Amount Paid','mean'), sessions=('Total Sessions Completed','mean'),
        lifetime=('Membership Duration (Days)','mean'), last30=('Visits in Last 30 Days','mean'),
        lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100),
        renewed=('Derived Status', lambda x:(x.isin(['Renewed','Active','Renewal Grace Period','New'])).mean()*100))
    print(t.round(1).to_string())
    print('\nBy purchase quarter, 2025-2026:')
    t2 = d[d['yr']>=2025].groupby(d['Purchase Date_d'].dt.to_period('Q')).agg(
        memberships=('Member ID','size'), ticket=('Amount Paid','mean'),
        sessions=('Total Sessions Completed','mean'), since=('Days Since Last Visit','mean'),
        lapsed=('Derived Status', lambda x:(x=='Lapsed').mean()*100))
    print(t2.round(1).to_string())
blk('8. CHURN BY COHORT YEAR', f8)
