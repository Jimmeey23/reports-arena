import pandas as pd, numpy as np
pd.set_option('display.width', 320); pd.set_option('display.max_columns', 70)

M = pd.read_csv('/home/user/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
_mv = M['Month Year'].astype(str)
M['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M.loc[M['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M['cohort'].isna()], format='%B-%Y', errors='coerce')

print('=' * 118)
print('VERIFY 1 — is "Source" filled in only for converted members? (data-artifact check)')
print('=' * 118)
h = M[(M['cohort'] >= '2025-01-01') & (M['cohort'] < '2026-10-01') & (M['First Visit Location'] == 'Supreme HQ, Bandra')].copy()
h['conv'] = h['Conversion Status'].eq('Converted')
h['has_src'] = h['Source'].notna()
ct = pd.crosstab(h['conv'], h['has_src'])
print(ct.to_string())
print()
print(f'  Of converters, {h[h["conv"]]["has_src"].mean()*100:.1f}% have a source recorded')
print(f'  Of non-converters, {h[~h["conv"]]["has_src"].mean()*100:.1f}% have a source recorded')
print()
print('  >> Bucket by entry type — is the gap explained by channel, or by conversion?')
t = h.groupby('Is New').agg(n=('Member Id', 'size'), conv=('conv', 'mean'), src=('has_src', 'mean')).round(3)
t['conv'] = (t['conv'] * 100).round(1); t['src'] = (t['src'] * 100).round(1)
print(t.to_string())
print()
print('  >> Within NON-converters only, what share by entry type have a source?')
nc = h[~h['conv']]
print(nc.groupby('Is New').agg(n=('Member Id', 'size'), src=('has_src', 'mean')).assign(src=lambda d: (d['src']*100).round(1)).to_string())

print()
print('=' * 118)
print('VERIFY 2 — did ANY Reshma-trained Sept-26 client ever return? (check against raw ledger)')
print('=' * 118)
C = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False)
C['dt'] = pd.to_datetime(C['Date (IST)'], errors='coerce')
C['checked'] = C['Checked In'].astype(str).str.upper().eq('TRUE')
sep = M[(M['cohort'] == pd.Timestamp('2026-09-01')) & (M['First Visit Location'] == 'Supreme HQ, Bandra')].copy()
res_ids = set(sep[sep['Trainer Name'] == 'Reshma Sharma']['Member Id'])
oth_ids = set(sep[sep['Trainer Name'] != 'Reshma Sharma']['Member Id'])
bandra_in = C[C['checked'] & (C['Location'] == 'Supreme HQ, Bandra')]
print(f'  Reshma-trained Sept-26 clients: {len(res_ids)}')
for mid in sorted(res_ids)[:40]:
    v = bandra_in[bandra_in['Member ID'] == mid]
    if len(v) > 1:
        print(f'   !! member {mid} has {len(v)} Bandra check-ins')
print(f'  Reshma group — total Bandra check-ins: {bandra_in[bandra_in["Member ID"].isin(res_ids)].shape[0]} across {len(res_ids)} members')
print(f'  Other group   — total Bandra check-ins: {bandra_in[bandra_in["Member ID"].isin(oth_ids)].shape[0]} across {len(oth_ids)} members')
print()
rs = bandra_in[bandra_in['Member ID'].isin(res_ids)]
print('  Reshma group check-in counts per member:')
print(rs.groupby('Member ID').size().value_counts().sort_index().to_string())
print()
print('  Other group check-in counts per member:')
print(bandra_in[bandra_in['Member ID'].isin(oth_ids)].groupby('Member ID').size().value_counts().sort_index().to_string())
print()
print('  ANY location (network) check-ins for the Reshma group:')
allnet = C[C['checked'] & C['Member ID'].isin(res_ids)]
print(f'   {allnet.shape[0]} check-ins across {len(res_ids)} members, at: {allnet["Location"].value_counts().to_dict()}')
print(f'   members with >=2 network check-ins: {(allnet.groupby("Member ID").size()>=2).sum()} of {len(res_ids)}')

print()
print('=' * 118)
print('VERIFY 3 — the 2-for-1 "second visit" distortion, restated')
print('=' * 118)
sep_ids = set(sep['Member Id'])
led = C[C['Member ID'].isin(sep_ids)].sort_values(['Member ID', 'dt'])
g = led[led['checked']].groupby('Member ID')
second = []
for mid, gg in g:
    gg = gg.sort_values('dt')
    if len(gg) >= 2:
        second.append({'mid': mid, 'visit2_product': gg.iloc[1]['Cleaned Product'],
                       'visit2_cat': gg.iloc[1]['Cleaned Category'], 'visit2_date': gg.iloc[1]['dt'],
                       'visit2_paid': gg.iloc[1]['Paid'], 'n': len(gg)})
s2 = pd.DataFrame(second)
print(f'  Sept-26 cohort members with 2+ attended visits: {len(s2)}')
print(s2['visit2_product'].value_counts().head(12).to_string())
print()
paid = s2['visit2_paid'].astype(str).str.upper().eq('TRUE') | s2['visit2_product'].astype(str).str.contains('2 For 1|Newcomer', case=False, na=False)
print(f'  of which the 2nd visit was a pre-paid intro-pack redemption: {paid.sum()}')
print(f'  genuine paid-or-new 2nd visits: {(~paid).sum()}')

print()
print('=' * 118)
print('VERIFY 4 — the elephant: Sept-26 trainer concentration and the whole-month effect')
print('=' * 118)
sep['conv'] = sep['Conversion Status'].eq('Converted')
sep['v'] = pd.to_numeric(sep['No of Visits'], errors='coerce')
print(f'  143 clients, 12 converted ({sep["conv"].mean()*100:.1f}%)')
nr = sep[sep['Trainer Name'] != 'Reshma Sharma']
print(f'  Excluding Reshma\'s 33: {len(nr)} clients, {nr["conv"].sum()} converted ({nr["conv"].mean()*100:.1f}%)')
print(f'  Reshma\'s 33: 0 converted')
print(f'  If Reshma had converted at the rest-of-studio rate ({nr["conv"].mean()*100:.1f}%), she would have produced {33*nr["conv"].mean():.1f} converters')
print(f'  That would lift the month to {sep["conv"].sum()+33*nr["conv"].mean():.0f} conversions = {(sep["conv"].sum()+33*nr["conv"].mean())/143*100:.1f}%')
print()
r = sep[sep['Trainer Name'] == 'Reshma Sharma']
print(f'  Reshma group: {(r["v"]>1).mean()*100:.1f}% returned for any further visit (avg {r["v"].mean():.2f} visits)')
print(f'  Other group : {(nr["v"]>1).mean()*100:.1f}% returned for any further visit (avg {nr["v"].mean():.2f} visits)')
print()
print('  Her intake by entry type vs the rest:')
print(pd.concat([r['Is New'].value_counts().rename('reshma'),
                 nr['Is New'].value_counts().rename('others')], axis=1).fillna(0).astype(int).to_string())
print()
print('  Her intake by day of week:')
print(pd.concat([r['First Visit Day'].value_counts().rename('reshma'),
                 nr['First Visit Day'].value_counts().rename('others')], axis=1).fillna(0).astype(int).to_string())
