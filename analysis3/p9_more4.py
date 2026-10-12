"""Round-5 mining, part 4: decomposition of September seats, cohorts, ARPU."""
import pandas as pd, numpy as np, d1_data as D
pd.set_option('display.width', 210); pd.set_option('display.max_columns', 60)
B = D.BANDRA
def hdr(t): print('\n' + '=' * 104 + f'\n{t}\n' + '=' * 104)
def blk(t, f):
    hdr(t)
    try: f()
    except Exception as e:
        import traceback; print('FAILED', type(e).__name__, e); traceback.print_exc(limit=2)

CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False, usecols=[
    'Member ID','Location','Date (IST)','Checked In','Cleaned Class','Teacher Name','Time','Day of Week','Is New'])
CK = CK[(CK['Location'] == B)].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
CK = CK[CK['dt'].notna() & (CK['Checked In'] == True)].copy()
AT = CK
def sept(y): return AT[(AT['dt'] >= f'{y}-09-01') & (AT['dt'] < f'{y}-10-01')]

# ---------------------------------------------------------------- 18
def f18():
    s26, s25 = sept(2026), sept(2025)
    m26 = set(s26['Member ID']); m25 = set(s25['Member ID'])
    # every Sept-26 seat attributed to a cohort
    mem26 = s26.groupby('Member ID').size()
    ret = mem26[mem26.index.isin(m25)]; new = mem26[~mem26.index.isin(m25)]
    print('DECOMPOSITION OF SEPTEMBER-2026 SEATS')
    print(f"  total seats {int(mem26.sum()):,} from {len(mem26)} members")
    print(f"  returning faces (also here in Sept-25): {len(ret):>4} members -> {int(ret.sum()):>5,} seats "
          f"({ret.sum()/mem26.sum()*100:.1f}%) | {ret.mean():.2f} visits each")
    print(f"  everything else (absent Sept-25):       {len(new):>4} members -> {int(new.sum()):>5,} seats "
          f"({new.sum()/mem26.sum()*100:.1f}%) | {new.mean():.2f} visits each")
    old = mem26[mem26.index.isin(m25)]
    prev = s25.groupby('Member ID').size()
    print('\n  For the 78 who did return, their own September volume:')
    print(f"    Sept-25: {int(prev[prev.index.isin(m25 & m26)].sum()):,} seats ({prev[prev.index.isin(m25&m26)].mean():.2f} each)")
    print(f"    Sept-26: {int(mem26[mem26.index.isin(m25 & m26)].sum()):,} seats ({mem26[mem26.index.isin(m25&m26)].mean():.2f} each)")
    gone = prev[prev.index.isin(m25 - m26)]
    print(f"\n  The {len(gone)} who left after Sept-25 were worth {int(gone.sum()):,} seats "
          f"({gone.mean():.2f} each). At the same rate that is {int(gone.sum()):,} seats of lost volume.")
    print(f"  The {len(new)} who replaced them delivered {int(new.sum()):,} — "
          f"a shortfall of {int(gone.sum()-new.sum()):,} seats, or {(gone.sum()-new.sum())/gone.sum()*100:.0f}%.")
    print('\n  Same decomposition for Sept-25 vs Sept-24:')
    s24 = sept(2024); m24 = set(s24['Member ID'])
    p25 = s25.groupby('Member ID').size(); p24 = s24.groupby('Member ID').size()
    r = p25[p25.index.isin(m24)]; n = p25[~p25.index.isin(m24)]
    print(f"    returning {len(r)} members -> {int(r.sum()):,} seats | absent-Sept-24 {len(n)} members -> {int(n.sum()):,} seats")
blk('18. WHERE SEPTEMBER-2026 SEATS ACTUALLY CAME FROM', f18)

# ---------------------------------------------------------------- 19
def f19():
    """Sept-25 leavers: were they good members or marginal ones?"""
    s25, s26 = sept(2025), sept(2026)
    m25 = set(s25['Member ID']); m26 = set(s26['Member ID'])
    v25 = s25.groupby('Member ID').size()
    stay = v25[v25.index.isin(m25 & m26)]; gone = v25[v25.index.isin(m25 - m26)]
    alltime = AT.groupby('Member ID').size()
    last = AT.groupby('Member ID')['dt'].max()
    print(f"Sept-25 stayers (n={len(stay)}): Sept-25 visits mean {stay.mean():.2f}, median {stay.median():.0f}")
    print(f"Sept-25 leavers (n={len(gone)}): Sept-25 visits mean {gone.mean():.2f}, median {gone.median():.0f}")
    print('\n  All-time depth of each group:')
    for lab, idx in [('stayers', stay.index), ('leavers', gone.index)]:
        a = alltime[alltime.index.isin(idx)]
        print(f"    {lab:8} n {len(a):>4} | lifetime visits mean {a.mean():.1f} median {a.median():.0f} | "
              f"{a.gt(20).mean()*100:.1f}% ever reached 21+ visits")
    print('\n  Last Bandra visit of the leavers (i.e. when they actually stopped):')
    lv = last[last.index.isin(gone.index)]
    print(lv.dt.to_period('M').value_counts().sort_index().to_string())
    print(f"\n  Of the {len(gone)} Sept-25 members who skipped Sept-26, "
          f"{(lv < '2026-09-01').sum()} had already stopped before September 2026; "
          f"{(lv >= '2026-09-01').sum()} simply did not come this month.")
blk('19. WHO LEFT AFTER SEPT-25', f19)

# ---------------------------------------------------------------- 20
def f20():
    """Days to second visit + conversion speed from the member file."""
    M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
    Mb = M[M['First Visit Location'] == B].copy()
    for c in ['Days To Second Visit','Ltv','No of Visits','Ltv Post Trial','Conversion Span (Days)','Visits Per Month']:
        Mb[c] = pd.to_numeric(Mb[c].astype(str).str.replace(r'[,\s₹]','',regex=True), errors='coerce')
    Mb['fvd'] = pd.to_datetime(Mb['First Visit Date'], errors='coerce', dayfirst=True)
    print('Columns of interest, non-null counts:', {c: int(Mb[c].notna().sum()) for c in
          ['Days To Second Visit','Conversion Span (Days)','Ltv','No of Visits','Visits Per Month']})
    d = Mb[(Mb['fvd'] >= '2025-09-01') & (Mb['fvd'] < '2026-09-01')]
    print(f'\nBandra first visits Sep-2025 to Aug-2026: {len(d)}')
    print('  Conversion Speed Bucket:'); print(d['Conversion Speed Bucket'].value_counts().to_string())
    print('\n  Days To Second Visit distribution:')
    ds = d['Days To Second Visit'].dropna()
    if len(ds):
        print(f"    n={len(ds)} | median {ds.median():.0f} | mean {ds.mean():.1f}")
        for lo, hi, lab in [(0,1,'0-1 day'),(2,3,'2-3 days'),(4,7,'4-7 days'),(8,14,'8-14 days'),(15,30,'15-30 days'),(31,999,'31+ days')]:
            print(f"      {lab:>10}: {(ds.between(lo,hi)).sum():>5} ({(ds.between(lo,hi)).mean()*100:>5.1f}%)")
    print('\n  Sept-2026 intake only:')
    q = Mb[(Mb['fvd'] >= '2026-09-01') & (Mb['fvd'] < '2026-10-01')]
    print(f"    first visits {len(q)} | with a 2nd visit {q['Days To Second Visit'].notna().sum()} "
          f"| conversion status: {q['Conversion Status'].value_counts().to_dict()}")
    print(f"    converted so far {q['Converted'].sum() if 'Converted' in q else 'n/a'}")
    print('\n  Retention Status x Conversion Status (Sep-2025-Aug-2026 intake):')
    print(pd.crosstab(d['Conversion Status'], d['Retention Status']).to_string())
    print('\n  Source (lead origin) performance, Sep-2025 to Aug-2026 intake:')
    g = d.groupby('Source').agg(n=('Ltv','size'), conv=('Conversion Status', lambda x: (x=='Converted').mean()*100),
                                ltv=('Ltv','mean'), visits=('No of Visits','mean'))
    print(g[g['n'] >= 10].round(2).sort_values('conv', ascending=False).to_string())
blk('20. CONVERSION SPEED AND LEAD SOURCE (member file)', f20)

# ---------------------------------------------------------------- 21
def f21():
    rows = []
    for y in range(2024, 2027):
        for m in range(1, 13):
            a = AT[(AT['dt'] >= f'{y}-{m:02d}-01') & (AT['dt'] < pd.Timestamp(f'{y}-{m:02d}-01') + pd.offsets.MonthBegin(1))]
            if len(a) < 20: continue
            rows.append(dict(mon=f'{y}-{m:02d}', members=a['Member ID'].nunique(), seats=len(a)))
    t = pd.DataFrame(rows)
    X = pd.read_csv('/home/user/uploads/Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
    X = X[X['Location'] == B].copy(); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
    X['Revenue'] = pd.to_numeric(X['Revenue'].astype(str).str.replace(',',''), errors='coerce').fillna(0)
    r = X.groupby(X['dt'].dt.to_period('M'))['Revenue'].sum().reset_index()
    r.columns = ['mon','rev']; r['mon'] = r['mon'].astype(str)
    t = t.merge(r, on='mon', how='left').fillna(0)
    t['rev_per_member'] = (t['rev']/t['members']).round(0)
    t['seats_per_member'] = (t['seats']/t['members']).round(2)
    print('Monthly active members, seats, class revenue, revenue PER MEMBER:')
    print(t.to_string(index=False))
blk('21. REVENUE PER ACTIVE MEMBER BY MONTH', f21)
