import pandas as pd, numpy as np
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 70)

S = pd.read_csv('/home/user/uploads/Sales - Raw - Sales (23).csv', low_memory=False)
S['dt'] = pd.to_datetime(S['Payment Date'], errors='coerce')
S['val'] = pd.to_numeric(S['Payment Value'].astype(str).str.replace(r'[,\s]', '', regex=True), errors='coerce')
S['disc_amt'] = pd.to_numeric(S['Discount Value In Currency'].astype(str).str.replace(r'[,\s]', '', regex=True), errors='coerce')
B = S[S['Calculated Location'] == 'Supreme HQ, Bandra'].copy()

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')

C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')

print('=' * 118)
print('A. RECONCILIATION — why the member file says -77% but the ledger says flat')
print('=' * 118)
sep = B[(B['dt'] >= '2026-09-01') & (B['dt'] < '2026-10-01')]
sep25 = B[(B['dt'] >= '2025-09-01') & (B['dt'] < '2025-10-01')]
print(f'  Sept-26 Bandra CASH through the studio ledger      : Rs {sep["val"].sum():>12,.0f}   ({len(sep)} transactions, {sep["Member ID"].nunique()} paying members)')
print(f'  Sept-25 Bandra CASH through the studio ledger      : Rs {sep25["val"].sum():>12,.0f}   ({len(sep25)} transactions, {sep25["Member ID"].nunique()} paying members)')
print(f'  YoY change in cash                                 : {(sep["val"].sum()/sep25["val"].sum()-1)*100:+.1f}%')
print()
cohort_ids = set(M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]['Member Id'])
cm = S[S['Member ID'].isin(cohort_ids)]
print(f'  Cash from the 143 Sept-26 NEW clients (all months)  : Rs {cm["val"].sum():>12,.0f}')
print(f'    of which paid in Sept-26                          : Rs {cm[cm["dt"] < "2026-10-01"]["val"].sum():>12,.0f}')
print(f'  Cash from EXISTING members in Sept-26               : Rs {sep[~sep["Member ID"].isin(cohort_ids)]["val"].sum():>12,.0f}')
print()
print('  >> The two metrics measure different things:')
print('     - The member file tracks lifetime value ATTRIBUTED TO THE NEW-CLIENT COHORT (slow to accrue).')
print('     - The sales ledger tracks ALL CASH received in the month, mostly from the existing base.')
print('     - Studio cash held flat YoY. New-client cohort value fell sharply. Both are true.')

print()
print('=' * 118)
print('B. WHO IS PAYING — the base is carrying the studio')
print('=' * 118)
for lbl, d, cutoff in [('Sept 2025', sep25, pd.Timestamp('2025-09-01')), ('Sept 2026', sep, pd.Timestamp('2026-09-01'))]:
    seen_before = set(M[M['cohort'] < cutoff]['Member Id'])
    newc = d[d['Member ID'].isin(set(M[M['cohort'] == cutoff]['Member Id']))]
    print(f'  {lbl}: total Rs {d["val"].sum():>11,.0f} | from THAT month\'s new clients: Rs {newc["val"].sum():>10,.0f} ({newc["val"].sum()/d["val"].sum()*100:4.1f}%)'
          f' | from the pre-existing base: Rs {d["val"].sum()-newc["val"].sum():>11,.0f} ({(d["val"].sum()-newc["val"].sum())/d["val"].sum()*100:4.1f}%)')
print()
print('Sept-2026 top spenders (the studio depends on these):')
top = sep.groupby('Member ID').agg(spend=('val', 'sum'), txns=('Sale ID', 'size')).sort_values('spend', ascending=False).head(12)
top = top.join(M.set_index('Member Id')[['First Name', 'Last Name', 'First Visit Date', 'Home Location']], how='left')
print(top.to_string())

print()
print('=' * 118)
print('C. EASY-TO-MISS #1 — the 41 unattributed clients: who are they?')
print('=' * 118)
s = M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')]
un = s[s['Source'].isna()]
print(f'Unattributed: {len(un)} of {len(s)}')
print('  their entry type :', un['Is New'].value_counts().to_dict())
print('  their day of week:', un['First Visit Day'].value_counts().to_dict())
print('  their time slot  :', un['First Visit Time Slot'].value_counts().to_dict())
print('  their trainer    :', un['Trainer Name'].value_counts().head(6).to_dict())
print('  payment method   :', un['Payment Method'].value_counts().to_dict())
print('  class            :', un['First Visit Entity Name'].value_counts().head(6).to_dict())
print()
print('  vs attributed cohort:')
at = s[s['Source'].notna()]
print('   attributed entry type:', at['Is New'].value_counts().to_dict())
print(f'  outcome: unattributed converted {un["Conversion Status"].eq("Converted").mean()*100:.1f}% vs attributed {at["Conversion Status"].eq("Converted").mean()*100:.1f}%')
print(f'  unattributed visits/client {un["No of Visits"].mean():.2f} vs attributed {at["No of Visits"].mean():.2f}')
print(f'  unattributed value/client Rs {pd.to_numeric(un["Ltv"].astype(str).str.replace(r"[^0-9]","",regex=True),errors="coerce").mean():,.0f} vs attributed Rs {pd.to_numeric(at["Ltv"].astype(str).str.replace(r"[^0-9]","",regex=True),errors="coerce").mean():,.0f}')

print()
print('=' * 118)
print('D. EASY-TO-MISS #2 — late cancellations and no-shows (capacity leakage)')
print('=' * 118)
Bs = C[C['Location'] == 'Supreme HQ, Bandra'].copy()
for lbl, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    x = Bs[(Bs['dt'] >= a) & (Bs['dt'] < b_)]
    print(f'  {lbl}: bookings={len(x)} attended={int(x["checked"].sum())} '
          f'no-show/late-cancel={len(x)-int(x["checked"].sum())} ({(1-x["checked"].mean())*100:.1f}%) '
          f'| capacity offered={int(pd.to_numeric(x["Capacity"],errors="coerce").fillna(0).sum())} '
          f'| fill={x["checked"].mean()*100:.1f}%')
print()
print('  >> Sept-2026 capacity utilisation by class:')
x = Bs[(Bs['dt'] >= '2026-09-01') & (Bs['dt'] < '2026-10-01')].copy()
x['cap'] = pd.to_numeric(x['Capacity'], errors='coerce')
sess = x.groupby('Session ID').agg(name=('Session Name', 'first'), cap=('cap', 'first'), booked=('Member ID', 'size'), att=('checked', 'sum'))
sess['fill_%'] = (sess['att'] / sess['cap'] * 100).round(0)
print(f'   sessions run: {len(sess)} | median fill {sess["fill_%"].median():.0f}% | mean {sess["fill_%"].mean():.0f}%')
print(f'   sessions under 50% full: {(sess["fill_%"]<50).sum()} ({(sess["fill_%"]<50).mean()*100:.0f}%)')
print(f'   sessions over 90% full : {(sess["fill_%"]>90).sum()} ({(sess["fill_%"]>90).mean()*100:.0f}%)')
print()
print('  By class name:')
byc = x.groupby('Cleaned Class').agg(sessions=('Session ID', 'nunique'), capacity=('cap', 'sum'), attended=('checked', 'sum'))
byc['fill_%'] = (byc['attended'] / byc['capacity'] * 100).round(0)
print(byc.sort_values('attended', ascending=False).head(12).to_string())

print()
print('=' * 118)
print('E. EASY-TO-MISS #3 — the Sept 12-13 event in the actual ledger')
print('=' * 118)
ev = Bs[(Bs['dt'] >= '2026-09-12') & (Bs['dt'] < '2026-09-14')]
print(f'  Sept 12-13 Bandra sessions: {ev["Session ID"].nunique()} | bookings {len(ev)} | attended {int(ev["checked"].sum())}')
print(f'  no-shows: {len(ev)-int(ev["checked"].sum())} ({(1-ev["checked"].mean())*100:.0f}%)')
print()
print('  sessions held that weekend:')
print(ev.groupby(['Session ID']).agg(name=('Session Name', 'first'), teacher=('Teacher Name', 'first'),
      cap=('Capacity', 'first'), booked=('Member ID', 'size'), att=('checked', 'sum')).to_string())
print()
print('  compare an ordinary weekend (Sept 19-20):')
ev2 = Bs[(Bs['dt'] >= '2026-09-19') & (Bs['dt'] < '2026-09-21')]
print(f'   bookings {len(ev2)} | attended {int(ev2["checked"].sum())} | no-shows {len(ev2)-int(ev2["checked"].sum())} ({(1-ev2["checked"].mean())*100:.0f}%)')

print()
print('=' * 118)
print('F. EASY-TO-MISS #4 — has the class schedule itself changed?')
print('=' * 118)
for lbl, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    x = Bs[(Bs['dt'] >= a) & (Bs['dt'] < b_)]
    print(f'  {lbl}: {x["Session ID"].nunique()} distinct sessions | classes offered by name:')
    print('    ', x['Cleaned Class'].value_counts().to_dict())
