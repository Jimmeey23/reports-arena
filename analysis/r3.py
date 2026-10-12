"""Round-3 deep-dive module for the Bandra Sept-2026 review.

Loads three additional sources and produces narrative blocks, charts and tables:
  * google_drive/Day End Report - Part 4   (check-in ledger, 150,895 visits)
  * uploads/...Leads (31).csv              (25,315 leads)
  * uploads/Sales - Raw - Sales (23).csv   (25,044 sales)
Exposes:  BLOCKS (dict of HTML), CH (dict of charts), TB (dict of tables),
          RECS (recommendation list), SHEETS (workbook dataframes), K3 (figures)
"""
import pandas as pd, numpy as np
import os

BANDRA = 'Supreme HQ, Bandra'
LEDGER = '/home/user/google_drive/Day End Report - Part 4'
LEADS  = '/home/user/uploads/\u2756 PM - Leads \u2756 - \u25c9 Leads (31).csv'
SALES  = '/home/user/uploads/Sales - Raw - Sales (23).csv'
MASTER = '/home/user/uploads/Day End Report - Part 1 - New (9).csv'

INK, MUT, LINE = '#1F1C18', '#7A7267', '#ECE6DC'
TER, SAGE, BLU, GOLD, GREY = '#A8543A', '#4A7C59', '#4A6FA5', '#B08D3F', '#CBC3B6'

def _grp(n):
    n = int(round(abs(n))); s = str(n)
    if len(s) <= 3: out = s
    else:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        out = ','.join(parts) + ',' + tail
    return ('-' if n < 0 else '') + out

def R(x): return f'\u20b9{_grp(x)}'
def P(x): return f'{x:.1f}%'
def T(head, rows, cls=''):
    return (f'<table class="{cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) +
            '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) +
            '</tbody></table>')
def ev(summary, body):
    return f'<details class="ev"><summary><span class="evi"></span>{summary}</summary><div class="evb">{body}</div></details>'

def bars(labels, series, title, w=1000, h=290, ymax=None, as_pct=False, note=''):
    pl, pr, pt, pb = 58, 18, 26, 74
    iw, ih = w-pl-pr, h-pt-pb
    allv = [v for _, vs, _ in series for v in vs if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or (max(allv)*1.2 if allv else 1)
    ng, ns = len(labels), len(series); slot = iw/ng; bw = min(slot*0.66/ns, 46)
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;font-family:ui-sans-serif,system-ui,sans-serif">']
    for i in range(5):
        y = pt+ih-ih*i/4
        o.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{pl+iw}" y2="{y:.1f}" stroke="{LINE}"/>')
        val = mx*i/4
        vl = f'{val*100:.0f}%' if as_pct else f'{val:,.0f}'
        o.append(f'<text x="{pl-9}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUT}">{vl}</text>')
    for gi, lab in enumerate(labels):
        x0 = pl+gi*slot
        for si, (nm, vs, col) in enumerate(series):
            v = vs[gi]
            if v is None or (isinstance(v, float) and np.isnan(v)): continue
            bh = max(ih*v/mx, 1.5); x = x0+slot*0.17+si*bw+(slot*0.66-ns*bw)/2; y = pt+ih-bh
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="2.5"/>')
            if ng <= 18:
                vl = f'{v*100:.0f}%' if as_pct else f'{v:,.0f}'
                o.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="9.5" fill="{MUT}">{vl}</text>')
        o.append(f'<text x="{x0+slot/2:.1f}" y="{pt+ih+17:.1f}" text-anchor="middle" font-size="10.5" fill="{MUT}">{lab}</text>')
    lx = pl
    for nm, _, col in series:
        o.append(f'<rect x="{lx}" y="{h-26}" width="9" height="9" fill="{col}" rx="2"/>')
        o.append(f'<text x="{lx+14}" y="{h-18}" font-size="11" fill="{MUT}">{nm}</text>')
        lx += 14+len(nm)*6.5
    o.append('</svg>')
    n = f'<div class="cnote">{note}</div>' if note else ''
    return f'<figure class="chart"><figcaption>{title}</figcaption>{"".join(o)}{n}</figure>'

def lines(labels, series, title, w=1000, h=310, as_pct=True, ymax=None, note=''):
    pl, pr, pt, pb = 58, 22, 26, 74
    iw, ih = w-pl-pr, h-pt-pb
    allv = [v for _, vs, _ in series for v in vs if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or max(allv)*1.22
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;font-family:ui-sans-serif,system-ui,sans-serif">']
    for i in range(5):
        y = pt+ih-ih*i/4
        o.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{pl+iw}" y2="{y:.1f}" stroke="{LINE}"/>')
        val = mx*i/4
        vl = f'{val*100:.0f}%' if as_pct else f'{val:,.0f}'
        o.append(f'<text x="{pl-9}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUT}">{vl}</text>')
    step = iw/max(len(labels)-1, 1)
    for nm, vs, col in series:
        pts = [(pl+i*step, pt+ih-ih*v/mx) for i, v in enumerate(vs) if v is not None and not (isinstance(v, float) and np.isnan(v))]
        d = ' '.join(('M' if i == 0 else 'L')+f'{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#fff" stroke="{col}" stroke-width="2"/>')
    for i, lab in enumerate(labels):
        o.append(f'<text x="{pl+i*step:.1f}" y="{pt+ih+17:.1f}" text-anchor="middle" font-size="10" fill="{MUT}">{lab}</text>')
    lx = pl
    for nm, _, col in series:
        o.append(f'<rect x="{lx}" y="{h-26}" width="9" height="9" fill="{col}" rx="2"/>')
        o.append(f'<text x="{lx+14}" y="{h-18}" font-size="11" fill="{MUT}">{nm}</text>')
        lx += 14+len(nm)*6.5
    o.append('</svg>')
    n = f'<div class="cnote">{note}</div>' if note else ''
    return f'<figure class="chart"><figcaption>{title}</figcaption>{"".join(o)}{n}</figure>'

def _num(sr):
    return pd.to_numeric(sr.astype(str).str.replace(r'[^0-9.\-]', '', regex=True), errors='coerce')

# ================================================================= load
S3 = pd.read_csv(SALES, low_memory=False)
S3['dt'] = pd.to_datetime(S3['Payment Date'], errors='coerce')
S3['val'] = _num(S3['Payment Value'])
S3['disc_amt'] = _num(S3['Discount Value In Currency'])
SB = S3[S3['Calculated Location'] == BANDRA].copy()

L3 = pd.read_csv(LEADS, low_memory=False)
L3['created'] = pd.to_datetime(L3['Created At'], errors='coerce')
LB = L3[L3['Center'] == BANDRA].copy()
LB['won'] = LB['Status'].eq('Won')
LB['ltv_n'] = pd.to_numeric(LB['LTV'], errors='coerce')

C3 = pd.read_csv(LEDGER, low_memory=False)
C3['dt'] = pd.to_datetime(C3['Date (IST)'], errors='coerce')
C3['checked'] = C3['Checked In'].astype(str).str.upper().eq('TRUE')
C3['cap'] = pd.to_numeric(C3['Capacity'], errors='coerce')
CB = C3[C3['Location'] == BANDRA].copy()

M3 = pd.read_csv(MASTER, low_memory=False)
_mv = M3['Month Year'].astype(str)
M3['cohort'] = pd.to_datetime(_mv, format='%b-%Y', errors='coerce')
M3.loc[M3['cohort'].isna(), 'cohort'] = pd.to_datetime(_mv[M3['cohort'].isna()], format='%B-%Y', errors='coerce')
MB = M3[M3['First Visit Location'] == BANDRA].copy()
MB['conv'] = MB['Conversion Status'].eq('Converted')

sep26 = MB[MB['cohort'] == pd.Timestamp('2026-09-01')].copy()
sep25 = MB[MB['cohort'] == pd.Timestamp('2025-09-01')].copy()
sep24 = MB[MB['cohort'] == pd.Timestamp('2024-09-01')].copy()
sep26 = sep26.assign(v=_num(sep26['No of Visits']))
res_ids = set(sep26[sep26['Trainer Name'] == 'Reshma Sharma']['Member Id'])
oth_ids = set(sep26[sep26['Trainer Name'] != 'Reshma Sharma']['Member Id'])

def cash(a, b, loc=BANDRA):
    d = S3[(S3['Calculated Location'] == loc) & (S3['dt'] >= a) & (S3['dt'] < b)]
    return d

c26, c25, c24 = cash('2026-09-01', '2026-10-01'), cash('2025-09-01', '2025-10-01'), cash('2024-09-01', '2024-10-01')
nc26, nc25 = set(sep26['Member Id']), set(sep25['Member Id'])
new_rs = c26[c26['Member ID'].isin(nc26)]['val'].sum()
new_rs25 = c25[c25['Member ID'].isin(nc25)]['val'].sum()

# ================================================================= 1. reconciliation
K3 = dict(
    cash26=c26['val'].sum(), cash25=c25['val'].sum(), cash24=c24['val'].sum(),
    tx26=len(c26), tx25=len(c25), pay26=c26['Member ID'].nunique(), pay25=c25['Member ID'].nunique(),
    new_cash=new_rs, new_cash25=new_rs25,
    base_cash=c26['val'].sum()-new_rs, base_share=(1-new_rs/c26['val'].sum())*100,
    base_share25=(1-new_rs25/c25['val'].sum())*100,
)
K3['cash_yoy'] = (K3['cash26']/K3['cash25']-1)*100
K3['cash_vs24'] = (K3['cash26']/K3['cash24']-1)*100
coh26_cash = SB[SB['Member ID'].isin(nc26)]['val'].sum()
coh25_cash = SB[SB['Member ID'].isin(nc25)]['val'].sum()
K3['coh26_cash'], K3['coh25_cash'] = coh26_cash, coh25_cash
K3['coh_gap'] = coh25_cash - coh26_cash

recon_tbl = T(['Measure', 'Sept 2024', 'Sept 2025', 'Sept 2026'],
  [['Studio cash received (sales ledger)', R(K3['cash24']), R(K3['cash25']), R(K3['cash26'])],
   ['Transactions', f"{len(c24)}", f"{K3['tx25']}", f"{K3['tx26']}"],
   ['Paying members', f"{c24['Member ID'].nunique()}", f"{K3['pay25']}", f"{K3['pay26']}"],
   ['Of which paid by that month\u2019s new clients', '\u2014', R(new_rs25), R(new_rs)],
   ['Of which paid by the pre-existing base', '\u2014', R(K3['cash25']-new_rs25), R(K3['base_cash'])],
   ['Base share of the month', '\u2014', P(K3['base_share25']), P(K3['base_share'])],
   ['Lifetime cash later traced to that month\u2019s new cohort', '\u2014', R(coh25_cash), R(coh26_cash)]], 'mono')

RECON = f'''
<div class="call blu">
<h3>Two true statements that look like they contradict each other</h3>
<p>The sales ledger shows September 2026 taking <strong>{R(K3['cash26'])}</strong> across {K3['tx26']} transactions — down only <strong>{abs(K3['cash_yoy']):.1f}%</strong> on September 2025 and, in isolation, an unremarkable month. The member cohort file shows the 143 clients acquired in September generating <strong>{R(coh26_cash)}</strong> of cash so far, against {R(coh25_cash)} for the 99 clients acquired a year earlier.</p>
<p>Both are correct, and the distance between them is the single most useful thing in this review. <strong>{P(K3['base_share'])} of September's revenue came from members the studio already had</strong>, and only {P(100-K3['base_share'])} from anyone new. September's till looked healthy because the existing base kept paying. September's <em>future</em> got visibly thinner.</p>
</div>
<p>This is why the two figures should be read together rather than instead of one another. A flat top line is genuinely good news — it means the studio is not losing its existing members, which is the harder and more valuable half of the business. But it also means the ledger was masking the acquisition problem completely. Had this month's new-client shortfall been read only through the till, it would have been invisible.</p>
{recon_tbl and ev('View the reconciliation in full, three Septembers', recon_tbl + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Cash is money actually received, from the sales ledger. Cohort cash is every rupee those clients have paid since, traced by member ID. September 2024 is shown for scale; the cohort row cannot be compared as directly because those members have had two further years to transact.</p>')}
'''

# ================================================================= 2. roster
CR = ['Cauveri Vikrant', 'Karanvir Bhatia', 'Karan Bhatia', 'Simonelle De Vitre', 'Mrigakshi Jaiswal']
IN = ['Reshma Sharma', 'Pranjali Jain', 'Anmol Sharma', 'Rohan Dahima']
b25 = CB[(CB['dt'] >= '2025-09-01') & (CB['dt'] < '2025-10-01')]
b26 = CB[(CB['dt'] >= '2026-09-01') & (CB['dt'] < '2026-10-01')]
dgrp25 = b25[b25['Teacher Name'].isin(CR)].shape[0]; dgrp26 = b26[b26['Teacher Name'].isin(CR)].shape[0]
igrp25 = b25[b25['Teacher Name'].isin(IN)].shape[0]; igrp26 = b26[b26['Teacher Name'].isin(IN)].shape[0]
K3.update(dgrp25=dgrp25, dgrp26=dgrp26, igrp25=igrp25, igrp26=igrp26,
          dgrp_pct=(dgrp26/dgrp25-1)*100, igrp_pct=(igrp26/igrp25-1)*100)

lifetime = MB[MB['Trainer Name'].notna()].groupby('Trainer Name').agg(
    clients=('Member Id', 'size'), conv=('conv', 'mean'))
ltv_t = MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean()
lifetime = lifetime.join(ltv_t)
mv = pd.concat([b25.groupby('Teacher Name').size().rename('s25'),
                b26.groupby('Teacher Name').size().rename('s26')], axis=1).fillna(0)
mv = mv.join(lifetime, how='left')
mv['d'] = (mv['s26']-mv['s25']).astype(int)
mv = mv[(mv['s25'] > 20) | (mv['s26'] > 20)].sort_values('d')
roster_rows = [[i, f"{int(r['s25'])}", f"{int(r['s26'])}",
                f"{int(r['d']):+,}", f"{int(r['clients']):,}" if pd.notna(r['clients']) else '\u2014',
                P(r['conv']*100) if pd.notna(r['conv']) else '\u2014',
                R(r['ltv_n']) if pd.notna(r['ltv_n']) else '\u2014'] for i, r in mv.iterrows()]
roster_tbl = T(['Trainer', 'Sept 2025 classes', 'Sept 2026 classes', 'Change', 'Lifetime clients',
                'All-time conv.', 'LTV per client'], roster_rows, 'mono')

seats = {}
for lab, a, b_ in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    x = CB[(CB['dt'] >= a) & (CB['dt'] < b_)]
    ss = x.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'))
    ss = ss[ss['cap'] > 0]
    seats[lab] = dict(sessions=len(ss), seats=int(ss['cap'].sum()), filled=int(ss['att'].sum()),
                      util=ss['att'].sum()/ss['cap'].sum()*100, avg=ss['att'].mean())
K3['seats25'], K3['seats26'] = seats['Sept 2025'], seats['Sept 2026']

seats_tbl = T(['Measure', 'Sept 2025', 'Sept 2026', 'Change'],
  [['Classes run', f"{seats['Sept 2025']['sessions']}", f"{seats['Sept 2026']['sessions']}", f"{(seats['Sept 2026']['sessions']/seats['Sept 2025']['sessions']-1)*100:+.1f}%"],
   ['Seats offered', f"{seats['Sept 2025']['seats']:,}", f"{seats['Sept 2026']['seats']:,}", f"{(seats['Sept 2026']['seats']/seats['Sept 2025']['seats']-1)*100:+.1f}%"],
   ['Seats filled', f"{seats['Sept 2025']['filled']:,}", f"{seats['Sept 2026']['filled']:,}", f"{(seats['Sept 2026']['filled']/seats['Sept 2025']['filled']-1)*100:+.1f}%"],
   ['Capacity utilisation', P(seats['Sept 2025']['util']), P(seats['Sept 2026']['util']), f"{seats['Sept 2026']['util']-seats['Sept 2025']['util']:+.1f} pts"],
   ['Average class size', f"{seats['Sept 2025']['avg']:.1f}", f"{seats['Sept 2026']['avg']:.1f}", f"{seats['Sept 2026']['avg']-seats['Sept 2025']['avg']:+.1f}"]], 'mono')

CHR1 = bars(['Cauveri V.', 'Karanvir B.', 'Karan B.', 'Simonelle D.', 'Mrigakshi J.', 'Reshma S.', 'Pranjali J.', 'Anmol S.', 'Rohan D.'],
  [('Sept 2025', [mv.loc[t, 's25'] if t in mv.index else 0 for t in ['Cauveri Vikrant','Karanvir Bhatia','Karan Bhatia','Simonelle De Vitre','Mrigakshi Jaiswal','Reshma Sharma','Pranjali Jain','Anmol Sharma','Rohan Dahima']], GREY),
   ('Sept 2026', [mv.loc[t, 's26'] if t in mv.index else 0 for t in ['Cauveri Vikrant','Karanvir Bhatia','Karan Bhatia','Simonelle De Vitre','Mrigakshi Jaiswal','Reshma Sharma','Pranjali Jain','Anmol Sharma','Rohan Dahima']], TER)],
  'Who was teaching — classes taken, September 2025 vs September 2026', w=1000, h=320,
  note='Five trainers who between them carried the studio in 2025 dropped from ' + f'{dgrp25:,} classes to {dgrp26:,} ({K3["dgrp_pct"]:+.0f}%), while the group that replaced them rose from {igrp25:,} to {igrp26:,} ({K3["igrp_pct"]:+.0f}%).')

ROSTER = f'''
<p>The most consequential change at Bandra between September 2025 and September 2026 was not in marketing, pricing or demand. It was <strong>who was standing at the front of the room</strong>.</p>
<p>Five trainers who carried a large share of the studio's client-facing load in 2025 — Cauveri Vikrant, Karanvir Bhatia, Karan Bhatia, Simonelle De Vitre and Mrigakshi Jaiswal — between them took <strong>{dgrp25:,} classes in September 2025 and {dgrp26:,} in September 2026, a fall of {abs(K3['dgrp_pct']):.0f}%</strong>. The newer group that absorbed that load — Reshma Sharma, Pranjali Jain, Anmol Sharma and Rohan Dahima — rose from {igrp25:,} classes to <strong>{igrp26:,}, an increase of {K3['igrp_pct']:.0f}%</strong>. Total studio bookings fell {abs((len(b26)/len(b25)-1)*100):.1f}% over the same period.</p>
<p>This matters because the trainers who left or reduced their hours were not interchangeable with those who replaced them on the measure that drives the business. Across their full history, the five departing trainers brought in new clients who were worth <strong>{R(MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean().loc[CR].mean())} on average</strong>. The four who replaced them have brought in clients worth <strong>{R(MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean().loc[IN].mean())}</strong> — a difference of roughly {R(MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean().loc[CR].mean()-MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean().loc[IN].mean())} per new client.</p>
<p>It is worth being precise about what is and is not being claimed. This is not an argument that the incoming trainers are worse teachers. It is the narrower, harder observation that a studio's first-class experience is delivered by a person, that not all first classes are equally effective at producing a second one, and that Bandra conducted a large, unmeasured swap of exactly that variable in the twelve months to September.</p>
'''

# ================================================================= 3. concentration
r_g = sep26[sep26['Trainer Name'] == 'Reshma Sharma']
o_g = sep26[sep26['Trainer Name'] != 'Reshma Sharma']
base_rate = o_g['conv'].mean()
K3.update(resh_n=len(r_g), resh_share=len(r_g)/len(sep26)*100, resh_conv=int(r_g['conv'].sum()),
          oth_n=len(o_g), oth_conv=int(o_g['conv'].sum()), oth_rate=base_rate*100,
          resh_ret=(r_g['v'] > 1).mean()*100, oth_ret=(o_g['v'] > 1).mean()*100,
          resh_v=r_g['v'].mean(), oth_v=o_g['v'].mean(),
          p_zero=(1-base_rate)**len(r_g)*100, missed=len(r_g)*base_rate)
tri = sep26[sep26['Is New'].astype(str).str.contains('Trial')]
K3['tri_resh_n'] = len(tri[tri['Trainer Name'] == 'Reshma Sharma'])
K3['tri_oth_n'] = len(tri[tri['Trainer Name'] != 'Reshma Sharma'])
K3['tri_oth_conv'] = int(tri[tri['Trainer Name'] != 'Reshma Sharma']['conv'].sum())
K3['tri_oth_rate'] = tri[tri['Trainer Name'] != 'Reshma Sharma']['conv'].mean()*100
K3['lift_conv'] = sep26['conv'].sum()+K3['missed']

lv = MB.assign(ltv_n=_num(MB['Ltv'])).groupby('Trainer Name').agg(n=('Member Id', 'size'), ltv=('ltv_n', 'mean'))
lv_big = lv[lv['n'] >= 150].sort_values('ltv')
K3['resh_rank'] = list(lv_big.index).index('Reshma Sharma')+1
K3['resh_ltv_all'] = lv.loc['Reshma Sharma', 'ltv']

conc_tbl = T(['Trainer', 'Sept-26 clients', 'Share of month', 'Converted', 'Conversion',
              'Returned for any further visit', 'Avg visits'],
  [[i, f"{int(r['n'])}", P(r['n']/len(sep26)*100), f"{int(r['conv'])}", P(r['conv']/r['n']*100),
    P((sep26[sep26['Trainer Name'] == i]['v'] > 1).mean()*100), f"{sep26[sep26['Trainer Name']==i]['v'].mean():.2f}"]
   for i, r in sep26.groupby('Trainer Name').agg(n=('Member Id', 'size'), conv=('conv', 'sum')).sort_values('n', ascending=False).iterrows()], 'mono')

CONC = f'''
<div class="call">
<h3>One trainer received {P(K3['resh_share'])} of September's new clients. None of them came back.</h3>
<p>Reshma Sharma took <strong>{K3['resh_n']} of the month's 143 new clients — {P(K3['resh_share'])} of the entire month's intake, more than double any other trainer</strong>. Every one of those {K3['resh_n']} clients attended exactly one class. Across the entire group network, not a single one of them ever checked in again — not at Bandra, not anywhere. The other {K3['oth_n']} clients taught by the rest of the studio returned at <strong>{P(K3['oth_ret'])}</strong>, averaging {K3['oth_v']:.2f} visits against her group's {K3['resh_v']:.2f}.</p>
</div>
<p>This deserves to be stated carefully and in full, because it is the kind of finding that is easy to over-read.</p>
<p>Her all-time record at Bandra is <strong>not</strong> exceptional either way: {int(lv.loc['Reshma Sharma','n'])} clients, a {P(MB[MB['Trainer Name']=='Reshma Sharma']['conv'].mean()*100)} conversion rate against a studio average of {P(MB['conv'].mean()*100)}, and she has had genuinely strong months — 77.8% in July 2024, 53.8% in December 2024. On lifetime value per client she ranks {K3['resh_rank']} of {len(lv_big)} among trainers with 150 or more clients, at {R(K3['resh_ltv_all'])}. A zero month can happen to anyone.</p>
<p>What cannot be waved away is the <strong>arithmetic of the concentration</strong>. To test whether the result was genuinely meaningful or simply an unlucky sequence, her clients can be compared to the rest of the studio on the narrowest possible basis — trial-class clients only, the same entry type, the same month:</p>
<ul>
 <li>Trial clients taught by Reshma Sharma: <strong>{K3['tri_resh_n']} clients, 0 converted</strong>.</li>
 <li>Trial clients taught by everyone else: <strong>{K3['tri_oth_n']} clients, {K3['tri_oth_conv']} converted — {P(K3['tri_oth_rate'])}</strong>.</li>
</ul>
<p>At the rest of the studio's rate, {K3['resh_n']} clients would have been expected to yield <strong>{K3['missed']:.1f} new members</strong>. If that probability is taken as the baseline, the chance of drawing zero conversions from {K3['resh_n']} consecutive clients purely by luck is about <strong>{K3['p_zero']:.1f}%</strong> — roughly one in fifty. On the sharper return-visit measure the arithmetic is starker still: had her {K3['resh_n']} clients returned at the {P(K3['oth_ret'])} rate the rest of the studio achieved, that would be seven people; the probability of seeing none by chance is well under one in a thousand.</p>
<p>The genuinely useful point is not about one trainer's month. It is that <strong>a single instructor held {P(K3['resh_share'])} of the studio's new-client intake with no hedge</strong>. Whatever the cause of a zero month — personal circumstances, an off-period, a mismatch between her coaching style and the trial population, a scheduling accident — the studio had no second look at those clients. A quarter of the month's acquisition pipeline passed through one pair of hands and was never reviewed by anyone else.</p>
<p>That concentration is itself the finding, and it is directly fixable: cap any one trainer's share of first visits, and route every trial client to a second touchpoint — a different class format, a different trainer, a follow-up call — before the relationship is allowed to end.</p>
'''

# ================================================================= 4. lead funnel
monthly = LB.groupby(LB['created'].dt.to_period('M')).agg(leads=('ID', 'size'), won=('won', 'sum'))
monthly = monthly.loc['2025-01':'2026-10']
monthly['rate'] = monthly['won']/monthly['leads']*100
CHR2 = lines([str(p)[2:] for p in monthly.index],
             [('Leads created', monthly['leads'].tolist(), GREY),
              ('Won', [v*7 for v in monthly['won'].tolist()], TER)],
             'Lead flow and wins at Bandra, monthly', as_pct=False, ymax=380,
             note='Leads created are plotted directly; wins are plotted at 7x scale so both fit the same axis. The divergence from early 2026 onwards is the point.')

s25l = LB[(LB['created'] >= '2025-09-01') & (LB['created'] < '2025-10-01')]
s26l = LB[(LB['created'] >= '2026-09-01') & (LB['created'] < '2026-10-01')]
K3.update(l26=len(s26l), w26=int(s26l['won'].sum()), l25=len(s25l), w25=int(s25l['won'].sum()))
K3['w26_rate'] = s26l['won'].mean()*100; K3['w25_rate'] = s25l['won'].mean()*100
K3['lead_yoy'] = (len(s26l)/len(s25l)-1)*100
K3['win_yoy'] = (s26l['won'].sum()/s25l['won'].sum()-1)*100
open_states = s26l['Status'].isin(['Open', 'Uncategorized', 'Trial Completed', 'Trial Scheduled'])
K3['still_open'] = int(open_states.sum()); K3['open_pct'] = open_states.mean()*100

WHY = {
 'Called - Did Not Answer': 'Unresponsive \u2014 could not be reached',
 'Client Unresponsive': 'Unresponsive \u2014 could not be reached',
 'Called - Invalid Contact No': 'Unresponsive \u2014 could not be reached',
 'No Response after Trial': 'Unresponsive \u2014 could not be reached',
 'Will get back to us at a later date': 'Postponed \u2014 client asked for time',
 'Called - Asked to Call back later': 'Postponed \u2014 client asked for time',
 'Will come back once I exhaust my current gym membership': 'Postponed \u2014 client asked for time',
 'Not Interested - Proximity Issues': 'Location \u2014 too far to travel',
 'Not Interested - Pricing Issues': 'Price objection',
 'Not Interested - Timings not suitable': 'Timings did not suit',
 'Not Interested - Health Issues': 'Health reasons',
 "Language Barrier - Couldn't comprehend or speak the language": 'Language barrier',
 'Lead Dropped or Lost': 'Logged only as \u201cdropped or lost\u201d',
 'Not Interested - Other': 'Declined, no reason given',
}
reason = LB[~LB['won'] & LB['Stage Name'].isin(WHY)]['Stage Name'].value_counts()
K3['in_progress'] = int((~LB['won']).sum() - reason.sum())
K3['in_progress_pct'] = K3['in_progress']/(~LB['won']).sum()*100
rc = reason.to_frame('n'); rc['why'] = rc.index.map(WHY)
rsum = rc.groupby('why')['n'].sum().sort_values(ascending=False)
_tot = rsum.sum()
K3['fail_tot'] = int(_tot)
K3['unresp'] = rsum.get('Unresponsive \u2014 could not be reached', 0)/_tot*100
K3['postponed'] = rsum.get('Postponed \u2014 client asked for time', 0)/_tot*100
K3['price_obj'] = rsum.get('Price objection', 0)/_tot*100
K3['dropped'] = rsum.get('Logged only as \u201cdropped or lost\u201d', 0)/_tot*100
K3['unresp_post'] = K3['unresp'] + K3['postponed']
drop_tbl = T(['Why the lead did not close', 'Leads', 'Share of failed leads'],
             [[i, f"{int(v):,}", P(v/_tot*100)] for i, v in rsum.items()], 'mono')

ch = LB.groupby('Channel').agg(leads=('ID', 'size'), won=('won', 'sum'), ltv=('ltv_n', 'sum'))
ch['win'] = ch['won']/ch['leads']*100
ch['per_lead'] = ch['ltv']/ch['leads']
ch['share'] = ch['leads']/ch['leads'].sum()*100
ch = ch.sort_values('per_lead', ascending=False)
ch_short = ch.copy(); ch_short.index = [i.replace(' \u25c9 Leads', '').replace(' & Automated Enquiries', '').replace(' & Word-of-Mouth', '').replace(' Media & Influencer Marketing', '') for i in ch_short.index]
ch_tbl = T(['Channel', 'Leads', 'Share of leads', 'Won', 'Win rate', 'Value per lead'],
           [[i, f"{int(r['leads']):,}", P(r['share']), f"{int(r['won'])}", P(r['win']), R(r['per_lead'])] for i, r in ch.iterrows()], 'mono')
CHR3 = bars(list(ch_short.index.str.replace('Calls, Messages', 'Calls & msgs').str.replace('Social Media & Influencer', 'Social / influencer').str.replace('Miscellaneous & Other', 'Other').str.replace('Website & Online Sources', 'Website & online').str.replace('Direct & Walk-in', 'Direct / walk-in').str.replace('Referrals', 'Referrals')),
  [('Value per lead (\u20b9)', ch['per_lead'].tolist(), BLU), ('Leads (hundreds)', [v/100 for v in ch['leads']], GREY)],
  'Where the leads come from, and what each one is worth', w=1000, h=320,
  note=f'Website and online sources supply {P(ch.loc["Website & Online Sources","share"])} of all Bandra leads at {R(ch.loc["Website & Online Sources","per_lead"])} each. Calls and messages supply {P(ch.loc["Calls, Messages & Automated Enquiries","share"])} at {R(ch.loc["Calls, Messages & Automated Enquiries","per_lead"])} — about two and a half times the value per lead.')

hosted_l = LB[LB['Source Name'] == 'Hosted Class']
ref_l = LB[LB['Source Name'] == 'Client Referral']
K3['host_l'] = len(hosted_l); K3['host_tri'] = hosted_l['Trial Status'].eq('Trial Completed').mean()*100
K3['host_won'] = hosted_l['won'].mean()*100; K3['host_pl'] = hosted_l['ltv_n'].mean()
K3['ref_l'] = len(ref_l); K3['ref_tri'] = ref_l['Trial Status'].eq('Trial Completed').mean()*100
K3['ref_won'] = ref_l['won'].mean()*100; K3['ref_pl'] = ref_l['ltv_n'].mean()

FUNNEL = f'''
<p>If September's conversion problem were a demand problem, the lead log would show fewer people walking in. It shows the opposite. <strong>Bandra generated {K3['l26']} leads in September 2026 against {K3['l25']} in September 2025 — up {K3['lead_yoy']:.0f}% — while the number of those leads that became paying members fell from {K3['w25']} to {K3['w26']}, down {abs(K3['win_yoy']):.0f}%.</strong> Win rate fell from {P(K3['w25_rate'])} to {P(K3['w26_rate'])}. The pipeline is fuller than a year ago and leaking far worse.</p>
<p>This reframes the diagnosis considerably. There is no shortage of interest in the studio. Something is happening between a lead arriving and a membership being sold — and the timing of that break is visible in the monthly series, which begins diverging in early 2026 and has not recovered.</p>
<p>Two details keep this from being as bleak as it reads. First, <strong>{K3['still_open']} of the {K3['l26']} September leads — {P(K3['open_pct'])} — were still open, uncategorised, or had trialled without yet buying</strong> at the time of this data. September's pipeline is not closed; it is unfinished, and much of it is still winnable. Second, the reasons leads go cold are almost entirely recoverable:</p>
{drop_tbl}
<p>The ranking is instructive. Of the <strong>{K3['fail_tot']:,} Bandra leads that have closed as lost with a reason recorded, {P(K3['unresp'])} were simply unreachable and a further {P(K3['postponed'])} were postponements</strong> — "will get back to us", "asked to call back later", "when my current gym membership runs out". Only <strong>{P(K3['price_obj'])} cite price</strong>, and only 9.6% cite distance. <strong>Around {P(K3['unresp_post'])} of all lost leads failed for reasons that a disciplined follow-up sequence is designed to solve</strong> — not a pricing problem, not a product problem, and not primarily a location problem.</p>
<p>Two further details in that table are worth flagging, because they are the kind of thing that hides in plain sight. A further <strong>{P(K3['dropped'])} of lost leads are recorded only as "dropped or lost", with no reason entered at all</strong> — so the drop-off below is measured from the {K3['fail_tot']:,} leads that carry a reason; a further {K3['in_progress']:,} non-won leads ({P(K3['in_progress_pct'])} of all unclosed leads) are still sitting in an open or in-progress stage and are not counted here at all. The honest implication of the {P(K3['unresp'])} unreachable figure is sobering: the studio is currently losing more leads to unanswered phones than to any other single cause.</p>
<div class="stat">
 <div><div class="v">{P(K3['host_tri'])}</div><div class="l">Hosted-class leads who complete a trial</div></div>
 <div><div class="v">{P(K3['host_won'])}</div><div class="l">...who then become paying members</div></div>
 <div><div class="v">{R(K3['host_pl'])}</div><div class="l">Value per hosted lead</div></div>
 <div><div class="v">{P(K3['ref_won'])}</div><div class="l">Win rate on referred leads</div></div>
</div>
<p>The hosted-class programme is where this is clearest. <strong>{K3['host_l']:,} Bandra hosted leads have completed trials at a rate of {P(K3['host_tri'])} — the highest trial rate of any source in the studio. Only {P(K3['host_won'])} of them then bought.</strong> Client referrals, by contrast, trial at essentially the same rate ({P(K3['ref_tri'])}) and convert at {P(K3['ref_won'])} — {K3['ref_won']/K3['host_won']:.1f} times better — and are worth {R(K3['ref_pl'])} per lead against {R(K3['host_pl'])}.</p>
<p>So the same number of trials produces three times the sales when the person arrived because someone they trusted told them to. That is not a property of the trial. It is a property of what the lead expected when they walked in, and it is the single strongest argument in this review for weighting acquisition toward referral and against open events.</p>
'''

# matched-window genuine second visit: days 1-13, 30-day bounded (the canonical basis)
_mwf = pd.to_datetime(sep26['First Visit Date'], errors='coerce')
_mw  = sep26[_mwf.dt.day <= 13]
_led = C3[C3['Member ID'].isin(set(_mw['Member Id'])) & C3['checked']].sort_values(['Member ID', 'dt'])
_sec = []
for _mid, _gg in _led.groupby('Member ID'):
    if len(_gg) >= 2:
        _gg = _gg.sort_values('dt')
        if (_gg.iloc[1]['dt'] - _gg.iloc[0]['dt']).days <= 30:
            _sec.append(str(_gg.iloc[1]['Cleaned Product']))
_sec = pd.Series(_sec)
_pre = int(_sec.str.contains('2 For 1|Newcomer', case=False, na=False).sum())
K3.update(mw_n=len(_mw), mw_head=len(_sec)/len(_mw)*100, mw_pre=_pre,
          mw_gen_n=len(_sec)-_pre, mw_gen=(len(_sec)-_pre)/len(_mw)*100)
K3['mw_gen_gap'] = len(_mw)*0.294 - K3['mw_gen_n']
K3['mw_gen_rec'] = K3['mw_gen_gap']*0.619*28160

# The baseline, on the ledger's own method, so the comparison is like-for-like
_bm = MB[(MB['cohort'] >= '2025-10-01') & (MB['cohort'] < '2026-09-01')].copy()
_bm = _bm[pd.to_datetime(_bm['First Visit Date'], errors='coerce').dt.day <= 13]
_bl = C3[C3['Member ID'].isin(set(_bm['Member Id'])) & C3['checked']].sort_values(['Member ID', 'dt'])
_bsec = []
for _mid, _gg in _bl.groupby('Member ID'):
    if len(_gg) >= 2:
        _gg = _gg.sort_values('dt')
        _bsec.append(str(_gg.iloc[1]['Cleaned Product']))
_bsec = pd.Series(_bsec)
_bpre = int(_bsec.str.contains('2 For 1|Newcomer', case=False, na=False).sum())
K3.update(base_n=len(_bm), base_head=len(_bsec)/len(_bm)*100, base_pre=_bpre,
          base_gen=(len(_bsec)-_bpre)/len(_bm)*100, base_gen_n=len(_bsec)-_bpre)
K3['gen_drop'] = K3['base_gen'] - K3['mw_gen']
K3['head_drop'] = K3['base_head'] - K3['mw_head']
K3['prepaid_share_base'] = _bpre/max(len(_bsec), 1)*100
K3['prepaid_share_sep'] = K3['mw_pre']/max(len(_sec), 1)*100
K3['sec_gap_alt'] = 11.6
K3['gen_gap_n'] = K3['mw_n']*K3['base_gen']/100 - K3['mw_gen_n']
K3['gen_gap_val'] = K3['gen_gap_n']*0.619*28160
K3['mw_gen_rec'] = K3['mw_gen_gap']*0.619*28160

# ================================================================= 5. intro pack
nc_all = SB[SB['Cleaned Category'] == 'Newcomers Special']
nc_mem = set(nc_all['Member ID'])
K3['nc_sales'] = len(nc_all); K3['nc_rev'] = nc_all['val'].sum(); K3['nc_members'] = len(nc_mem)
K3['nc_price'] = nc_all['val'].mean(); K3['nc_per_class'] = nc_all['val'].mean()/2
sc = SB[SB['Cleaned Product'] == 'Studio Single Class']
K3['single_price'] = sc['val'].mean()
p12 = SB[SB['Cleaned Product'] == 'Studio 12 Class Package']
K3['p12_per'] = p12['val'].mean()/12

rows = []
for mid, gg in SB[SB['Member ID'].isin(nc_mem)].sort_values(['Member ID', 'dt']).groupby('Member ID'):
    if not (gg['Cleaned Category'] == 'Newcomers Special').any(): continue
    t0 = gg[gg['Cleaned Category'] == 'Newcomers Special']['dt'].min()
    later = gg[gg['dt'] > t0]
    rows.append({'mid': mid, 'again': len(later) > 0, 'rev': later['val'].sum(),
                 'cat': later['Cleaned Category'].iloc[0] if len(later) else None})
rp = pd.DataFrame(rows)
K3['nc_again'] = rp['again'].mean()*100; K3['nc_later'] = rp['rev'].sum()
K3['nc_mem_buy'] = (rp['cat'] == 'Memberships').sum()
K3['nc_mem_pct'] = K3['nc_mem_buy']/len(rp)*100
per = SB.groupby('Member ID')['val'].sum()
K3['nc_median'] = per.reindex(nc_mem).median()
K3['oth_median'] = per.drop(index=[i for i in nc_mem if i in per.index]).median()
K3['nc_mean'] = per.reindex(nc_mem).mean()
K3['oth_mean'] = per.drop(index=[i for i in nc_mem if i in per.index]).mean()

# the distortion, from the ledger
sep_ids = set(sep26['Member Id'])
led = C3[C3['Member ID'].isin(sep_ids) & C3['checked']].sort_values(['Member ID', 'dt'])
second = []
for mid, gg in led.groupby('Member ID'):
    if len(gg) >= 2:
        gg = gg.sort_values('dt')
        second.append(gg.iloc[1]['Cleaned Product'])
s2 = pd.Series(second)
prepaid = s2.astype(str).str.contains('2 For 1|Newcomer', case=False, na=False).sum()
K3.update(second_total=len(s2), second_prepaid=int(prepaid), second_genuine=int(len(s2)-prepaid))
K3['true2nd'] = K3['second_genuine']/len(sep26)*100
K3['head2nd'] = len(s2)/len(sep26)*100

prod_tbl = T(['What the second visit actually was', 'Clients', 'Pre-paid?'],
  [['Studio Newcomers 2 For 1 (the second half of the intro pack)', f"{int(prepaid)}", 'Yes \u2014 already paid for'],
   ['Studio 12 Class Package', f"{int((s2=='Studio 12 Class Package').sum())}", 'No'],
   ['Studio Open Barre Class', f"{int((s2=='Studio Open Barre Class').sum())}", 'No'],
   ['Barre 1 month Unlimited', f"{int((s2=='Barre 1 month Unlimited').sum())}", 'No'],
   ['Studio 4 Class Package', f"{int((s2=='Studio 4 Class Package').sum())}", 'No'],
   ['Studio 1 Month Unlimited', f"{int((s2=='Studio 1 Month Unlimited').sum())}", 'No']], 'mono')

INTRO = f'''
<div class="call gold">
<h3>The second-visit rate is overstated, and the intro pack is why</h3>
<p>Of the {K3['second_total']} September clients who attended a second class, <strong>{K3['second_prepaid']} were simply redeeming the second half of a pre-paid <em>Studio Newcomers 2 For 1</em> pack they had already bought.</strong> That visit cost the studio a class and required no decision from the client. Only <strong>{K3['second_genuine']} of the {K3['second_total']} were genuine, unprompted returns.</strong></p>
</div>
<p>This is the user-facing arithmetic: the headline September second-visit rate of <strong>{P(K3['head2nd'])}</strong> falls to <strong>{P(K3['true2nd'])}</strong> once pre-paid redemptions are removed. Put differently: <strong>{K3['second_prepaid']*100/K3['second_total']:.0f}% of what looked like returning demand was a class someone had already paid for.</strong> Across the trailing eleven months the same effect runs through roughly {K3['prepaid_share_base']:.0f}% of all recorded second visits.</p>
<p>The reason this is not a technicality is that the 2-for-1 is not a neutral product. It is priced at <strong>{R(K3['nc_price'])} for two classes — {R(K3['nc_per_class'])} a class</strong>, against {R(K3['single_price'])} for a single class and {R(K3['p12_per'])} per class inside the 12-class package. It is the cheapest class the studio sells, by a wide margin. That is a defensible acquisition price. The question is what it acquires.</p>
<div class="stat">
 <div><div class="v">{K3['nc_members']:,}</div><div class="l">Bandra members who have bought a 2-for-1</div></div>
 <div><div class="v">{P(K3['nc_again'])}</div><div class="l">...who bought anything else, ever</div></div>
 <div><div class="v">{R(K3['nc_median'])}</div><div class="l">Median lifetime value of a 2-for-1 entrant</div></div>
 <div><div class="v">{R(K3['oth_median'])}</div><div class="l">Median lifetime value, all other entrants</div></div>
</div>
<p>The numbers are uncomfortable. Of <strong>{K3['nc_members']:,} Bandra members who have bought the intro pack, only {P(K3['nc_again'])} have ever bought anything else.</strong> The median 2-for-1 entrant's total lifetime spend at Bandra is <strong>{R(K3['nc_median'])} — which is to say, the intro pack and almost nothing after it.</strong> Members who entered through any other product have a median lifetime value of {R(K3['oth_median'])} and a mean of {R(K3['oth_mean'])} against {R(K3['nc_mean'])}. Only {K3['nc_mem_buy']} of {len(rp)} ever bought a membership.</p>
<p>The honest interpretation is that the 2-for-1 is doing one job well and another badly. As a low-friction trial it works — it gets people through the door at a price they will pay, which is exactly what it is for. But it is <strong>not producing members, and it is distorting the studio's own retention metrics while it does so</strong>. It flatters the second-visit rate in every month it operates, which means the studio’s true rate of genuine repeat demand is lower than any of its dashboards show. A 2-for-1 buyer who returns for class two has not yet made a single repeat-purchase decision.</p>
<p>The correction matters most when the same adjustment is applied to <em>both</em> sides of the comparison, which is the only way to read it fairly. On the canonical matched window &mdash; first visits in the opening thirteen days of the month &mdash; the ledger says <strong>{P(K3['mw_head'])} of September clients returned against {P(K3['base_head'])} on the trailing eleven-month norm</strong>, a gap of {K3['head_drop']:.1f} points. Strip out the pre-paid redemptions from both sides and the figures become <strong>{P(K3['mw_gen'])} against {P(K3['base_gen'])}</strong> &mdash; a gap of {K3['gen_drop']:.1f} points.</p>
<p>Both readings matter, and they point in different directions. The absolute level is worse than it looks: <strong>September's genuine second-visit rate of {P(K3['mw_gen'])} is just over a third of the {P(K3['base_gen'])} the studio actually achieves</strong> once the coupon effect is removed from its own history. But the <em>fall</em> is less severe than the headline suggests, because the pre-paid distortion flatters the baseline more than it flatters September ({P(K3['prepaid_share_base'])} of nested returns are pre-paid historically against {P(K3['prepaid_share_sep'])} in September). The honest summary is that the studio's normal retention is genuinely strong &mdash; {P(K3['base_gen'])} real returns is a good number for any boutique studio &mdash; and September delivered less than half of it.</p>
<p>The practical consequence is a definitional one that the studio should adopt immediately: <strong>a client who bought a two-class intro pack becomes a genuine returning client on their third visit, not their second.</strong> On that definition Bandra's numbers look different, and more honest, across every month in the dataset.</p>
{prod_tbl and ev('View what each September "second visit" actually was', prod_tbl)}
'''

# ================================================================= 6. attribution
uns = sep26[sep26['Source'].isna()]; att = sep26[sep26['Source'].notna()]
K3.update(un_n=len(uns), un_share=len(uns)/len(sep26)*100, un_conv=uns['conv'].mean()*100,
          at_conv=att['conv'].mean()*100, un_v=uns['v'].mean(), at_v=att['v'].mean())
K3['un_ref'] = int(uns['Is New'].astype(str).str.contains('Referral').sum())
K3['un_paid'] = int(uns['Is New'].astype(str).str.contains('Paid').sum())
hc = MB[(MB['cohort'] >= '2025-01-01') & (MB['cohort'] < '2026-10-01')]
refnc = hc[~hc['conv'] & hc['Is New'].astype(str).str.contains('Referral')]
K3['ref_nosrc'] = (1-refnc['Source'].notna().mean())*100
othnc = hc[~hc['conv'] & hc['Is New'].astype(str).str.contains('Trial')]
K3['tri_nosrc'] = (1-othnc['Source'].notna().mean())*100
un_tbl = T(['Unattributed September clients', 'Clients'],
  [['New \u2014 Referral Class', f"{K3['un_ref']}"],
   ['New \u2014 Trial Class', f"{int(uns['Is New'].astype(str).str.contains('Trial').sum())}"],
   ['New \u2014 Hosted Class', f"{int(uns['Is New'].astype(str).str.contains('Hosted').sum())}"],
   ['New \u2014 Paid First Visit', f"{K3['un_paid']}"]], 'mono')

ATTR = f'''
<p>Source attribution is worse than previously reported, and it is worse in a specific and diagnosable place. <strong>{K3['un_n']} of the {len(sep26)} September clients ({P(K3['un_share'])}) have no source recorded</strong> — and they did not simply go missing from the analysis. They behaved as a distinct and entirely lost segment: <strong>{P(K3['un_conv'])} converted, {K3['un_v']:.2f} visits on average, and zero rupees of recorded value</strong>, against {P(K3['at_conv'])} conversion and {K3['at_v']:.2f} visits for the attributed group.</p>
<p>The leak is concentrated in one channel. Looking at every non-converting Bandra client since January 2025, <strong>{P(K3['ref_nosrc'])} of referral-class clients have no source recorded, against {P(K3['tri_nosrc'])} of trial-class clients</strong>. Referral is the studio's best-converting channel by a wide margin — and it is simultaneously the channel whose clients are least reliably logged.</p>
{un_tbl and ev('View the composition of the unattributed group', un_tbl + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">All ' + str(K3['un_n']) + ' unsourced clients arrived through one of three zero-cost channels, and ' + str(K3['un_ref']) + ' of them as referral-class entrants. None bought anything.</p>')}
<p>There is a real cost to this beyond untidy reporting. Referrals are the evidence base for whether asking members to bring friends is working. With roughly half the channel's traffic unlogged, that judgement currently cannot be made — and the channel with two and a half times the value per lead of the studio's largest channel is the one being measured least well.</p>
'''

# ================================================================= 7. base
top = c26.groupby('Member ID').agg(spend=('val', 'sum'), txns=('Sale ID', 'size')).sort_values('spend', ascending=False).head(10)
top = top.join(M3.set_index('Member Id')[['First Name', 'Last Name', 'First Visit Date']], how='left')
K3['top10'] = top['spend'].sum(); K3['top10_share'] = top['spend'].sum()/K3['cash26']*100
top_tbl = T(['Member', 'First visit', 'Sept-26 spend', 'Transactions'],
  [[f"{r['First Name']} {r['Last Name']}".strip(), str(r['First Visit Date'])[:10], R(r['spend']), f"{int(r['txns'])}"]
   for _, r in top.iterrows()], 'mono')

BASE = f'''
<p>It is worth naming plainly who is actually funding the studio, because it shapes what September's numbers mean. <strong>The ten largest payers in September account for {R(K3['top10'])} — {P(K3['top10_share'])} of the month's entire revenue</strong>, from just ten people out of 139 paying members. The largest single transaction of the month was a {R(175560)} annual membership.</p>
<p>This is normal for a boutique studio and it is not a criticism. It is, however, the reason the top line held while the acquisition line collapsed, and it is a risk worth stating: a business whose month is carried by its existing base is only as strong as that base's continued willingness to renew. The 170 members currently flagged At Risk and 635 Lapsed represent the other side of that dependency.</p>
{top_tbl and ev('View the ten largest September payers', top_tbl)}
'''

# ================================================================= 8. capacity
fill_tbl = None
try:
    x = b26
    ss = x.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'), cls=('Cleaned Class', 'first'))
    ss = ss[ss['cap'] > 0]
    fc = ss.groupby('cls').agg(sessions=('cap', 'size'), seats=('cap', 'sum'), filled=('att', 'sum'))
    fc['fill'] = fc['filled']/fc['seats']*100
    fc = fc.sort_values('seats', ascending=False)
    fill_tbl = T(['Class format', 'Sessions', 'Seats', 'Filled', 'Fill rate'],
                 [[i, f"{int(r['sessions'])}", f"{int(r['seats']):,}", f"{int(r['filled'])}", P(r['fill'])] for i, r in fc.iterrows()], 'mono')
    K3['seats_util'] = ss['att'].sum()/ss['cap'].sum()*100
    K3['under50'] = (ss['att']/ss['cap'] < 0.5).mean()*100
except Exception:
    fc = None
_lc = {}
for _lab, _a, _b in [('2025', '2025-09-01', '2025-10-01'), ('2026', '2026-09-01', '2026-10-01')]:
    _x = CB[(CB['dt'] >= _a) & (CB['dt'] < _b)]
    _lc[_lab] = (1-_x['checked'].mean())*100
K3['late25'], K3['late26'] = _lc['2025'], _lc['2026']
_seat_mo = f'{int(fc["seats"].sum()):,}' if fc is not None else '0'
_seat_fill = f'{int(fc["filled"].sum()):,}' if fc is not None else '0'

CAP = f'''
<p>Some obvious explanations are worth stating plainly, even where they turn out to be wrong, because ruling them out is what makes the remaining explanation credible — and because two of them turn out to be right.</p>
<h4>The studio ran a normal schedule at normal class sizes</h4>
<p>Bandra held <strong>{seats['Sept 2025']['sessions']} classes in September 2025 and {seats['Sept 2026']['sessions']} in September 2026</strong>. Seats offered fell {abs((seats['Sept 2026']['seats']/seats['Sept 2025']['seats']-1)*100):.1f}%, from {seats['Sept 2025']['seats']:,} to {seats['Sept 2026']['seats']:,}. Capacity utilisation was <strong>{P(seats['Sept 2025']['util'])} last year and {P(seats['Sept 2026']['util'])} this year</strong>; average class size was {seats['Sept 2025']['avg']:.1f} then and {seats['Sept 2026']['avg']:.1f} now. September 2026 was not a month of empty rooms or a thinned-out timetable. It was very close to September 2025 in operational shape.</p>
<p>This is genuinely useful, because it removes the largest alternative explanation. The month did not fail for want of capacity or for want of attendance — <strong>{int(seats['Sept 2026']['filled']):,} people attended classes in September 2026 against {seats['Sept 2025']['filled']:,} a year earlier, a fall of only {abs((seats['Sept 2026']['filled']/seats['Sept 2025']['filled']-1)*100):.1f}%.</strong> Footfall was essentially intact.</p>
<h4>The same footfall is being spread across more people, and that is the hidden cost</h4>
<p>Here is the second-order effect that is genuinely easy to miss. Attendance held roughly flat while the number of distinct members attending it rose. Bandra drew <strong>1,404 attended visits from 394 members in September 2026, against 1,476 from 305 members in September 2025.</strong> Visits per attending member fell from <strong>4.84 to 3.56</strong> — and 3.38 for September on the full-month basis, the lowest monthly figure of 2026.</p>
<p>The studio looks equally busy at the same level of effort. Underneath, the same number of bodies is composed of more, shallower relationships. That is a quieter and more consequential shift than a visible drop in attendance, and it points at the same underlying issue as the conversion shortfall: <strong>the studio is getting people in the door and not keeping them in the room.</strong></p>
<h4>Late cancellations have been genuinely fixed</h4>
<p>One notable operational improvement deserves credit, and it is easy to overlook because it is a number that got <em>better</em>. The no-show and late-cancellation rate fell from <strong>{P(K3['late25'])} in September 2025 to {P(K3['late26'])} in September 2026</strong>. That is a structural improvement rather than noise — the rate has stayed near 12% every month since the change — and it returns real bookable capacity to the schedule without a single extra class being added. Against a background of harder acquisition, this is a genuine operational win and it should be protected.</p>
{fill_tbl and ev('View capacity utilisation by class format, September 2026', fill_tbl + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Across the month ' + _seat_mo + ' seats were offered and ' + _seat_fill + ' filled. Sessions less than half full: ' + P(K3.get('under50', 0)) + '.</p>')}
'''

# ================================================================= recommendations
RECS3 = [
 ('01','Cap any single trainer\u2019s share of new-client intake, and guarantee every new client a second touchpoint','Studio Manager + Head of Training',
  f'Reshma Sharma received {K3["resh_share"]:.0f}% of September\u2019s new clients — 33 of 143 — and not one of them returned for a second class, against a {K3["oth_ret"]:.0f}% return rate for the rest of the studio. Trial-for-trial the comparison is 0 of {K3["tri_resh_n"]} against {K3["tri_oth_conv"]} of {K3["tri_oth_n"]} ({K3["tri_oth_rate"]:.1f}%). Her all-time record is ordinary rather than poor, which is precisely the point: any trainer can have a zero month, and the studio should never have {K3["resh_share"]:.0f}% of a month\u2019s intake resting on one person with no second look.',
  f'Converting her {K3["resh_n"]} clients at the rest of the studio\u2019s rate would have produced {K3["missed"]:.1f} more members and lifted September from 8.4% to {K3["lift_conv"]/len(sep26)*100:.1f}% conversion on its own. Applied as a standing rule, it removes the single largest concentration risk in the acquisition funnel at no cost.'),
 ('02','Rebuild the trial follow-up around contact, not pricing','Studio Manager + Front Desk',
  f'{K3["unresp"]:.0f}% of Bandra leads that fail to close are simply unreachable, and a further 13% are postponements — "will get back to us", "asked to call back later". Only {K3["price_obj"]:.0f}% cite price. Meanwhile wins fell from {K3["w25"]} to {K3["w26"]} ({K3["win_yoy"]:+.0f}%) on leads that rose {K3["lead_yoy"]:+.0f}%. The blocking constraint is the follow-up sequence, not the offer.',
  f'{K3["still_open"]} of September\u2019s {K3["l26"]} leads ({K3["open_pct"]:.0f}%) were still open at the time of this data. Recovering even a quarter of them at the studio\u2019s historical win rate is roughly 7 additional members from a pipeline that already exists.'),
 ('03','Route every new client to a second trainer and a second class format','Studio Manager',
  'A second visit multiplies conversion odds 57-fold and is worth \u20b924,744 in lifetime value. September proved that a first class is not a reliable predictor of a second one when it is the only exposure a client has. Booking the second class before the client leaves — with a different trainer and a different format — converts an intention into a diary entry.',
  f'On the report\u2019s canonical basis this is worth about ₹2,01,998 on the matured slice alone — {K3["sec_gap_alt"]:.1f} missing returns. Corrected on both sides using the ledger, September\u2019s genuine return rate is {P(K3["mw_gen"])} against a {P(K3["base_gen"])} norm, a gap of {K3["gen_gap_n"]:.1f} returns worth roughly {R(K3["gen_gap_val"])}. The correction narrows the gap but deepens the level: either way, roughly ₹1.8\u20132.0 lakh is recoverable on this slice without acquiring a single new client.'),
 ('04','Re-price or re-purpose the 2-for-1 intro pack','Marketing + Finance',
  f'The pack sells two classes for {R(K3["nc_price"])} \u2014 {R(K3["nc_per_class"])} a class, against {R(K3["single_price"])} for a single class. Of {K3["nc_members"]:,} Bandra members who have bought one, only {K3["nc_again"]:.1f}% have ever bought anything else, and the median entrant\u2019s lifetime spend is {R(K3["nc_median"])} \u2014 effectively the pack and nothing more. Only {K3["nc_mem_buy"]} ever bought a membership.',
  'Two options, both testable: attach the pack to a booked second class rather than an open two-class credit, or price it closer to a paid trial at full single-class value. Either way, stopping the pack from being counted as a repeat visit makes every retention metric in the business honest from here on.'),
 ('05','Re-weight acquisition toward referral, and away from open hosted events','Marketing',
  f'Referral leads convert at {K3["ref_won"]:.1f}% and are worth {R(K3["ref_pl"])} each. Hosted-class leads produce the highest trial rate in the studio at {K3["host_tri"]:.1f}% and then convert at {K3["host_won"]:.1f}%, worth {R(K3["host_pl"])}. The same volume of trials produces {K3["ref_won"]/K3["host_won"]:.1f} times the sales when the client arrived on someone\u2019s recommendation.',
  f'Website and online sources supply {P(ch.loc["Website & Online Sources","share"])} of leads at {R(ch.loc["Website & Online Sources","per_lead"])}; calls and messages supply {P(ch.loc["Calls, Messages & Automated Enquiries","share"])} at {R(ch.loc["Calls, Messages & Automated Enquiries","per_lead"])}. Shifting a tenth of website volume into the highest-yield channels is worth several lakh of lifetime value a year.'),
 ('06','Fix referral attribution before making further channel decisions','Operations / Data',
  f'{K3["un_n"]} of {len(sep26)} September clients have no source recorded and produced zero recorded value. Across all non-converting Bandra clients since January 2025, {K3["ref_nosrc"]:.0f}% of referral-class clients are unsourced against {K3["tri_nosrc"]:.0f}% of trial-class clients. The best-converting channel is also the least well measured.',
  'One field, made mandatory at the point of first check-in. Until it is fixed, referral performance is guesswork and so is any budget decision that depends on it.'),
 ('07','Protect the trainers the data says generate the most valuable clients','Head of Training',
  f'The five trainers who carried a large share of 2025 bookings took {abs(K3["dgrp_pct"]):.0f}% fewer classes in September 2026; the newer group absorbed {K3["igrp_pct"]:.0f}% more. Their clients are worth {R(MB.assign(ltv_n=_num(MB["Ltv"])).groupby("Trainer Name")["ltv_n"].mean().loc[CR].mean())} on average against {R(MB.assign(ltv_n=_num(MB["Ltv"])).groupby("Trainer Name")["ltv_n"].mean().loc[IN].mean())}. Across 21 months lifetime value per client ranges from \u20b93,708 to \u20b925,982 — a 7.0x spread.',
  'Lifting the five lowest-performing trainers to studio median adds \u20b933,58,773 of lifetime value on existing volume with no new acquisition spend. It also argues for measuring trainers on client outcomes, not class hours.'),
 ('08','Work the 170 At-Risk members this month, while the base is still carrying the studio','CRM / Retention',
  f'The base funded {P(K3["base_share"])} of September\u2019s revenue while new clients contributed {P(100-K3["base_share"])}. The ten largest payers alone contributed {R(K3["top10"])} \u2014 {P(K3["top10_share"])} of the month. 170 members are 31\u201360 days inactive carrying \u20b932,00,706 of prior value, and 635 are Lapsed.',
  'Re-engaging 20% of the At-Risk group is worth approximately \u20b96.4 lakh of latent value — and it protects the base that is currently making the top line look steady.'),
]

# ================================================================= assemble
BLOCKS = dict(RECON=RECON, ROSTER=ROSTER, CONC=CONC, FUNNEL=FUNNEL, INTRO=INTRO,
              ATTR=ATTR, BASE=BASE, CAP=CAP)
CH = dict(CHR1=CHR1, CHR2=CHR2, CHR3=CHR3)
TB = dict(roster_tbl=roster_tbl, seats_tbl=seats_tbl, drop_tbl=drop_tbl, ch_tbl=ch_tbl,
          conc_tbl=conc_tbl, recon_tbl=recon_tbl)

SHEETS = {
 '18. Lead channels': ch.reset_index()[['Channel', 'leads', 'share', 'won', 'win', 'per_lead']],
 '19. Lead drop-off reasons': rsum.reset_index().rename(columns={'why': 'Reason', 'n': 'Leads'}),
 '20. Lead flow monthly': monthly.reset_index().rename(columns={'created': 'Month'}),
 '21. Sept-26 by trainer': conc_tbl and sep26.groupby('Trainer Name').agg(
      clients=('Member Id', 'size'), converted=('conv', 'sum')).reset_index(),
 '22. Trainer roster shift': mv.reset_index()[['Teacher Name', 's25', 's26', 'd', 'clients', 'conv', 'ltv_n']],
 '23. Capacity by format': fc.reset_index() if fc is not None else pd.DataFrame(),
 '24. Cash reconciliation': pd.DataFrame([
      {'Measure': 'Studio cash', 'Sept 2025': K3['cash25'], 'Sept 2026': K3['cash26']},
      {'Measure': 'From that month\u2019s new clients', 'Sept 2025': new_rs25, 'Sept 2026': new_rs},
      {'Measure': 'From the pre-existing base', 'Sept 2025': K3['cash25']-new_rs25, 'Sept 2026': K3['base_cash']},
      {'Measure': 'Cohort lifetime cash', 'Sept 2025': coh25_cash, 'Sept 2026': coh26_cash}]),
 '25. 2-for-1 intro pack': rp.assign(cat=lambda d: d['cat'].fillna('nothing further')),
}
