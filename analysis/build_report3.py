"""Builds the redesigned Supreme HQ Bandra Sept-2026 review:
   constructive tone, year-in-context framing, causal root-cause section,
   and collapsible evidence panels. Also writes the Excel workbook."""
import pandas as pd, numpy as np
from prep import load

# ---------------------------------------------------------------- data
df = load()
SNAP = pd.Timestamp('2026-10-11'); BANDRA = 'Supreme HQ, Bandra'
nn = df[~df['is_import']].copy()
for _d in (nn,):
    _d['obs'] = (SNAP - _d['fvd']).dt.days
b = nn[nn['First Visit Location'] == BANDRA].copy()
b['fam'] = np.select(
 [b['First Visit Entity Name'].str.contains('Hosted| X | x |Sweat|Pickle|Peakst8|KRC|Run Club|Unfiltered|SPRINT', case=False, na=False),
  b['First Visit Entity Name'].str.startswith('powerCycle', na=False),
  b['First Visit Entity Name'].str.contains('Barre', na=False),
  b['First Visit Entity Name'].str.contains('Mat 57', na=False),
  b['First Visit Entity Name'].str.contains('FIT', na=False)],
 ['Hosted / partner','powerCycle','Barre 57','Mat 57','Studio FIT'], default='Other')
b['hosted'] = b['fam'].eq('Hosted / partner')

sep   = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01')]
aug   = b[(b['fvd'] >= '2026-08-01') & (b['fvd'] < '2026-09-01')]
sep25 = b[(b['fvd'] >= '2025-09-01') & (b['fvd'] < '2025-10-01')]
hist  = b[(b['fvd'] >= '2025-10-01') & (b['fvd'] < '2026-09-01')]
mw    = sep[sep['fvd'].dt.day <= 13]                     # fully matured matched window n=70
sep1213 = sep[(sep['fvd'] >= '2026-09-12') & (sep['fvd'] < '2026-09-14')]

# ---------------------------------------------------------------- CANONICAL CALC
# Primary comparison = matched window (first visits on days 1-13 of the month) with
# 30-DAY BOUNDED outcomes, so every member and every baseline has a fair, equal window.
base_mw = b[(b['fvd'] >= '2025-10-01') & (b['fvd'] < '2026-09-01')]
base_mw = base_mw[base_mw['fvd'].dt.day <= 13]
base_conv = (base_mw['converted'] & (base_mw['conv_span'] <= 30)).mean()*100
base_2nd  = (base_mw['days_2nd'] <= 30).mean()*100
base_rev  = base_mw['revenue'].mean()
base_vis  = base_mw['No of Visits'].mean()
bc, bs = base_conv/100, base_2nd/100

mw_c30 = (mw['converted'] & (mw['conv_span'] <= 30)).sum()
mw_s30 = (mw['days_2nd'] <= 30).sum()
conv_gap = len(mw)*bc - mw_c30
sec_gap  = len(mw)*bs - mw_s30

sep1213_ = mw[mw['fvd'].dt.day >= 12]
sep1_11_  = mw[mw['fvd'].dt.day <= 11]
ev_c30 = (sep1213_['converted'] & (sep1213_['conv_span'] <= 30)).sum()
ev_s30 = (sep1213_['days_2nd'] <= 30).sum()
ev_conv_gap = len(sep1213_)*bc - ev_c30
ev_sec_gap  = len(sep1213_)*bs - ev_s30

# value of the shortfall
cb = base_mw[base_mw['converted'] & (base_mw['conv_span'] <= 30)]
LTV_CONV   = cb['revenue'].mean()          # baseline lifetime value per converter
FIRST_CONV = cb['first_pv'].mean()         # baseline first-purchase value per converter
full_gap   = conv_gap * len(sep) / len(mw) # scale the matured-slice gap to the whole cohort
proj_ltv   = full_gap * LTV_CONV
near_term  = full_gap * FIRST_CONV
recover_2nd = sec_gap * 0.619 * LTV_CONV   # 2nd-visit gap -> converters -> value (matured slice)

K = dict(
  n=len(sep), conv=sep['converted'].sum(), conv_pct=sep['converted'].mean()*100,
  rev=sep['revenue'].sum(), arpu=sep['revenue'].mean(),
  second=sep['days_2nd'].notna().sum(), second_pct=sep['days_2nd'].notna().mean()*100,
  visits=sep['No of Visits'].mean(),
  mw_n=len(mw), mw_conv=len(mw) and mw_c30, mw_conv_pct=mw_c30/len(mw)*100,
  mw_second=mw_s30, mw_second_pct=mw_s30/len(mw)*100,
  base_conv=base_conv, base_second=base_2nd, base_rev=base_rev, base_vis=base_vis,
  base_mw_n=len(base_mw), conv_gap=conv_gap, sec_gap=sec_gap,
  ev_conv_share=ev_conv_gap/conv_gap*100, ev_sec_share=ev_sec_gap/sec_gap*100,
  full_gap=full_gap, proj_ltv=proj_ltv, near_term=near_term, recover_2nd=recover_2nd,
  base_vol=117.8,
)
K['shortfall'] = proj_ltv
K['ev_conv_gap_val'] = ev_conv_gap * LTV_CONV

# ---------------------------------------------------------------- ROUND 3
import sys as _sys; _sys.path.insert(0, '/home/user/analysis')
from r3 import BLOCKS as R3, CH as R3CH, TB as R3TB, RECS3, SHEETS as R3SHEETS, K3
import r3 as _r3
_lvm = _r3.MB.assign(ltv_n=_r3._num(_r3.MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean()
lv_dep = _lvm.loc[_r3.CR].mean(); lv_new = _lvm.loc[_r3.IN].mean()
seats = {}
for _lab, _a, _b in [('Sept 2025', '2025-09-01', '2025-10-01'), ('Sept 2026', '2026-09-01', '2026-10-01')]:
    _x = _r3.CB[(_r3.CB['dt'] >= _a) & (_r3.CB['dt'] < _b)]
    _ss = _x.groupby('Session ID').agg(cap=('cap', 'first'), att=('checked', 'sum'))
    _ss = _ss[_ss['cap'] > 0]
    seats[_lab] = dict(sessions=len(_ss), seats=int(_ss['cap'].sum()), filled=int(_ss['att'].sum()),
                       util=_ss['att'].sum()/_ss['cap'].sum()*100, avg=_ss['att'].mean())

# ---------------------------------------------------------------- year-in-context tables
def ttm(start, end):
    g = b[(b['fvd'] >= start) & (b['fvd'] < end)]
    e = g[g['obs'] >= 30]
    c90 = g[g['converted'] & (g['conv_span'] <= 90)]
    e90 = g[g['obs'] >= 90]
    return dict(clients=len(g),
                conv30=(e['converted'] & (e['conv_span'] <= 30)).mean()*100,
                second30=(e['days_2nd'] <= 30).mean()*100,
                rev90=c90['first_pv'].sum()/max(len(e90), 1))
TTM = {lbl: ttm(s, e) for lbl, s, e in [
    ('Oct 2023 – Sep 2024','2023-10-01','2024-10-01'),
    ('Oct 2024 – Sep 2025','2024-10-01','2025-10-01'),
    ('Oct 2025 – Sep 2026','2025-10-01','2026-10-01')]}

JANSEP = {}
for yr in [2024, 2025, 2026]:
    g = b[(b['fvd'] >= f'{yr}-01-01') & (b['fvd'] < f'{yr}-10-01')]
    e = g[g['obs'] >= 90]; c90 = e[e['converted'] & (e['conv_span'] <= 90)]
    JANSEP[yr] = dict(clients=len(g), conv90=(len(c90)/len(e)*100) if len(e) else np.nan,
                      n90=len(e), c90=len(c90), second=e['days_2nd'].notna().mean()*100,
                      revnew=c90['first_pv'].sum()/max(len(e), 1), pkg=c90['first_pv'].median())

# monthly YoY
mo_rows = []
for mo in range(1, 10):
    r = {'m': pd.Timestamp(2026, mo, 1).strftime('%b')}
    for yr in [2025, 2026]:
        s = pd.Timestamp(yr, mo, 1); e = s + pd.offsets.MonthBegin(1)
        g = b[(b['fvd'] >= s) & (b['fvd'] < e)]; e30 = g[g['obs'] >= 30]
        r[f'n{yr}'] = len(g)
        r[f'c{yr}'] = (e30['converted'] & (e30['conv_span'] <= 30)).mean()*100 if len(e30) >= 8 else np.nan
        r[f's{yr}'] = (e30['days_2nd'] <= 30).mean()*100 if len(e30) >= 8 else np.nan
    mo_rows.append(r)
MO = pd.DataFrame(mo_rows)

SEPS = {}
for yr in [2024, 2025, 2026]:
    g = b[(b['fvd'] >= f'{yr}-09-01') & (b['fvd'] < f'{yr}-10-01')]; e = g[g['obs'] >= 30]
    SEPS[yr] = dict(n=len(g), conv30=(e['converted'] & (e['conv_span'] <= 30)).mean()*100,
                    second30=(e['days_2nd'] <= 30).mean()*100, arpu=g['revenue'].mean(),
                    rev=g['revenue'].sum())

# driver table across months
drv = []
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    if str(per) < '2025-01': continue
    e = g[g['obs'] >= 30]
    if len(e) < 20: continue
    drv.append(dict(cohort=str(per), n=len(g), conv30=(e['converted'] & (e['conv_span'] <= 30)).mean()*100,
                    second30=(e['days_2nd'] <= 30).mean()*100, hosted=g['hosted'].mean()*100,
                    free=g['Payment Method'].eq('free').mean()*100,
                    weekend=g['First Visit Day'].isin(['Saturday', 'Sunday']).mean()*100,
                    arpu=e['revenue'].mean()))
DR = pd.DataFrame(drv)
CORR = {c: (DR[c].corr(DR['conv30']), DR[c].corr(DR['second30']), DR[c].corr(DR['arpu']))
        for c in ['n', 'hosted', 'free', 'weekend']}

# channels
CH = {'New - Trial Class':'Free trial class','New - Hosted Class':'Hosted class','New - Referral Class':'Referral (complimentary)','New - Paid First Visit':'Paid first visit'}
sep_c = sep.copy(); hist_c = hist.copy()
for d in (sep_c, hist_c): d['channel'] = d['Is New'].map(CH).fillna('Other')
chs = sep_c.groupby('channel').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
chh = hist_c.groupby('channel').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))

# trainers
def tr(d, mn=1):
    t = d[d['Trainer Name'].notna()].groupby('Trainer Name').agg(n=('Member Id','size'), conv=('converted','sum'),
            sec=('days_2nd', lambda s: s.notna().sum()), rev=('revenue','sum'))
    t['conv_p'] = t['conv']/t['n']*100; t['sec_p'] = t['sec']/t['n']*100; t['ltv'] = t['rev']/t['n']
    return t[t['n'] >= mn]
TSEP, THIST, TALL = tr(sep), tr(hist, 8), tr(b, 40)

# formats
FSEP = sep.groupby('fam').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
FSEP['conv_p'] = FSEP['conv']/FSEP['n']*100; FSEP['arpu'] = FSEP['rev']/FSEP['n']
FHIST = hist.groupby('fam').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
FHIST['conv_p'] = FHIST['conv']/FHIST['n']*100; FHIST['arpu'] = FHIST['rev']/FHIST['n']

# hosted programme
h = nn[nn['First Visit Entity Name'].str.contains('Hosted| X | x |Sweat|Pickle|Peakst8|KRC|Run Club|Unfiltered|SPRINT', case=False, na=False)].copy()
HM = h.groupby(h['cohort'].dt.to_period('M')).agg(clients=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum')).loc['2025-09':'2026-10']
HP = h.groupby('First Visit Entity Name').agg(clients=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
HP['conv_p'] = HP['conv']/HP['clients']*100; HP['ltv'] = HP['rev']/HP['clients']
HOSTED = dict(n=len(h), conv=h['converted'].sum(), conv_p=h['converted'].mean()*100, ltv=h['revenue'].mean(), rev=h['revenue'].sum())

# festival phases
ph = []
for yr in [2024, 2025, 2026]:
    x = b[(b['fvd'] >= f'{yr}-09-01') & (b['fvd'] < f'{yr}-10-01')]
    if len(x) < 20: continue
    for lab, lo, hi in [('1–13', 1, 13), ('14–25', 14, 25), ('26–30', 26, 30)]:
        g = x[(x['fvd'].dt.day >= lo) & (x['fvd'].dt.day <= hi)]
        if not len(g): continue
        ph.append(dict(year=yr, phase=lab, n=len(g), conv=g['converted'].mean()*100, second=g['days_2nd'].notna().mean()*100))

# base
bh = df[df['bandra_home'] & (~df['is_import'])].drop_duplicates('Member Id')
risk = bh[bh['Lifecycle Status'] == 'At Risk']
LIFE = bh['Lifecycle Status'].value_counts()

# ---------------------------------------------------------------- charts
INK, MUT, LINE = '#1F1C18', '#7A7267', '#ECE6DC'
TER, SAGE, BLU, GOLD, GREY = '#A8543A', '#4A7C59', '#4A6FA5', '#B08D3F', '#CBC3B6'

def esc(s): return str(s)

def bars(labels, series, title, w=1000, h=290, ymax=None, as_pct=False, legend=True, note=''):
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
        o.append(f'<text x="{pl-9}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUT}">{(f"{val*100:.0f}%" if as_pct else f"{val:,.0f}")}</text>')
    for gi, lab in enumerate(labels):
        x0 = pl+gi*slot
        for si, (nm, vs, col) in enumerate(series):
            v = vs[gi]
            if v is None or (isinstance(v, float) and np.isnan(v)): continue
            bh = max(ih*v/mx, 1.5); x = x0+slot*0.17+si*bw+(slot*0.66-ns*bw)/2; y = pt+ih-bh
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="2.5"/>')
            if ng <= 17:
                vl = f'{v*100:.0f}%' if as_pct else f'{v:,.0f}'
                o.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="9.5" fill="{MUT}">{vl}</text>')
        o.append(f'<text x="{x0+slot/2:.1f}" y="{pt+ih+17:.1f}" text-anchor="middle" font-size="10.5" fill="{MUT}">{lab}</text>')
    if legend:
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
        o.append(f'<text x="{pl-9}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUT}">{(f"{val*100:.0f}%" if as_pct else f"{val:,.0f}")}</text>')
    step = iw/max(len(labels)-1, 1)
    for nm, vs, col in series:
        pts = [(pl+i*step, pt+ih-ih*v/mx) for i, v in enumerate(vs) if v is not None and not (isinstance(v, float) and np.isnan(v))]
        d = ' '.join(f'{"M" if i==0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
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

mon = b.groupby(b['cohort'].dt.to_period('M')).agg(n=('Member Id','size'), conv=('converted','sum')).loc['2025-09':'2026-09']
CH1 = bars([str(p)[2:] for p in mon.index], [('New clients', list(mon['n']), GREY), ('Converted', list(mon['conv']), TER)],
           'Monthly intake and conversions at Bandra', note='Volume has climbed steadily since May 2026. Conversions have not kept pace — the gap is what this report investigates.')
CH2 = lines([f'{r.m}', ''] if False else MO['m'].tolist(),
            [('2025', MO['c2025'].tolist(), GREY), ('2026', MO['c2026'].tolist(), TER)],
            '30-day conversion rate, 2026 vs 2025 — same months', ymax=0.30,
            note='Calculated on the equal-observation basis (30-day window). 2026 tracked 2025 closely through April; the divergence opens from May and is widest in September.')
CH3 = bars(['Sept 2024','Sept 2025','Sept 2026'], [('Clients', [SEPS[y]['n'] for y in [2024,2025,2026]], GREY)],
           'September intake across three years — volume recovered, quality did not', ymax=190,
           note='2026 brought the highest September volume of the three (143 vs 99 in 2025) while conversion and second-visit rates fell.')
CH4 = bars(['1–13', '14–25', '26–30'],
           [('Sept 2024', [next(p['conv'] for p in ph if p['year']==2024 and p['phase']=='1–13'), next(p['conv'] for p in ph if p['year']==2024 and p['phase']=='14–25'), next(p['conv'] for p in ph if p['year']==2024 and p['phase']=='26–30')], GREY),
            ('Sept 2025', [next(p['conv'] for p in ph if p['year']==2025 and p['phase']=='1–13'), next(p['conv'] for p in ph if p['year']==2025 and p['phase']=='14–25'), next(p['conv'] for p in ph if p['year']==2025 and p['phase']=='26–30')], BLU),
            ('Sept 2026', [next(p['conv'] for p in ph if p['year']==2026 and p['phase']=='1–13'), next(p['conv'] for p in ph if p['year']==2026 and p['phase']=='14–25'), next(p['conv'] for p in ph if p['year']==2026 and p['phase']=='26–30')], TER)],
           'September split by Ganeshotsav phase — the festival explains less than it appears to', as_pct=True, ymax=0.62,
           note='Ganesh Chaturthi was 14 Sep 2026. If the festival were the cause, the pre-festival phase should outperform. In 2026 all three phases were weak.')
CH5 = bars(['No 2nd visit','Had 2nd visit'],
           [('Lifetime value per client', [b[~b['days_2nd'].notna()]['revenue'].mean(), b[b['days_2nd'].notna()]['revenue'].mean()], BLU)],
           'The second visit is the single largest value lever', ymax=31000,
           note='Clients who returned converted at 61.9%; those who did not, at 1.1%. Difference in lifetime value: ₹24,744 per person.')
CH6 = bars(['Anmol S.','Pranjali J.','Mrigakshi J.','Atulan P.','Rohan D.'],
           [('Sept-26 2nd-visit %', [42.9, 33.3, 16.7, 14.3, 15.8], SAGE),
            ('Sept-26 conv %', [7.1, 33.3, 16.7, 14.3, 10.5], TER)],
           'Best second-visit performance in September (trainers with 6+ new clients)', as_pct=True, ymax=0.55,
           note='Anmol Sharma placed 6 of 14 new clients into a second class — the strongest follow-through in the studio this month.')
CH7 = lines([str(p)[2:] for p in HM.index],
            [('Clients', HM['clients'].tolist(), GREY), ('Converted', HM['conv'].tolist(), TER)],
            'Hosted / partner programme — people brought in vs people who converted', as_pct=False, ymax=150,
            note='The programme reliably produces volume. Conversion has drifted down from ~7-9% to under 1%. This is an engineering gap, not a demand problem.')
CH8 = bars(list(TALL.sort_values('ltv', ascending=False).index.str.replace(r'\s+', ' ', regex=True).str.slice(0, 11)),
           [('Lifetime value per client', TALL.sort_values('ltv', ascending=False)['ltv'].tolist(), BLU)],
           'Lifetime value per client by first-class trainer (all-time, 40+ clients)',
           w=1000, h=320, note='A 7.0x spread between the highest and lowest — the clearest untapped lever in the studio, requiring no new acquisition spend.')

# ---------------------------------------------------------------- tables
def T(head, rows, cls=''):
    return (f'<table class="{cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) +
            '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) +
            '</tbody></table>')

def ev(summary, body):
    return f'<details class="ev"><summary><span class="evi"></span>{summary}</summary><div class="evb">{body}</div></details>'

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

# year table
yr_rows = []
for lbl, d in TTM.items():
    yr_rows.append([lbl, f"{d['clients']:,}", P(d['conv30']), P(d['second30']), R(d['rev90'])])
TTM_T = T(['Twelve months to 30 Sep','New clients','30-day conversion','30-day 2nd visit','Revenue per new client (90-day)'], yr_rows, 'mono')

js_rows = [[str(y), f"{JANSEP[y]['clients']:,}", f"{JANSEP[y]['n90']:,}", P(JANSEP[y]['conv90']), P(JANSEP[y]['second']), R(JANSEP[y]['revnew']), R(JANSEP[y]['pkg'])] for y in [2024,2025,2026]]
JS_T = T(['Jan–Sep','New clients','Matured cohort','90-day conversion','2nd-visit rate','Revenue / new client','Median first package'], js_rows, 'mono')

mo_t = T(['Month','2025 clients','2026 clients','2025 conv.','2026 conv.','2025 2nd visit','2026 2nd visit'],
         [[r['m'], f"{int(r['n2025'])}", f"{int(r['n2026'])}", P(r['c2025']), P(r['c2026']), P(r['s2025']), P(r['s2026'])] for r in MO.to_dict('records')], 'mono')

sep_t = T(['September','New clients','30-day conversion','30-day 2nd visit','Revenue','Revenue / client'],
          [[str(y), SEPS[y]['n'], P(SEPS[y]['conv30']), P(SEPS[y]['second30']), R(SEPS[y]['rev']), R(SEPS[y]['arpu'])] for y in [2024,2025,2026]], 'mono')

sc_t = T(['Metric','Sep 2026','Aug 2026','Sep 2025','Trailing 12-mo'],
  [['New clients', len(sep), len(aug), len(sep25), '117.8 / month'],
   ['Conversions', f"{K['conv']} ({P(K['conv_pct'])})", f"{aug['converted'].sum()} ({P(aug['converted'].mean()*100)})", f"{sep25['converted'].sum()} ({P(sep25['converted'].mean()*100)})", '—'],
   ['30-day 2nd-visit rate', P(K['mw_second_pct']), '—', '27.3%', P(K['base_second'])],
   ['Revenue booked', R(K['rev']), R(aug['revenue'].sum()), R(sep25['revenue'].sum()), '—'],
   ['Revenue per client', R(K['arpu']), R(aug['revenue'].mean()), R(sep25['revenue'].mean()), R(5507)],
   ['Visits per client', f"{K['visits']:.2f}", f"{aug['No of Visits'].mean():.2f}", f"{sep25['No of Visits'].mean():.2f}", '—'],
   ['Share of network intake', '36.6%', '35.3%', '27.7%', '—']], 'mono')

drv_t = T(['Month','Clients','30-day conv.','30-day 2nd visit','Hosted share','Free share','Weekend share','Revenue / client'],
  [[r['cohort'], r['n'], P(r['conv30']), P(r['second30']), P(r['hosted']), P(r['free']), P(r['weekend']), R(r['arpu'])] for r in DR.to_dict('records')], 'mono')

corr_t = T(['Intake characteristic','vs 30-day conversion','vs 30-day 2nd visit','vs revenue/client'],
  [['Monthly volume', f"{CORR['n'][0]:+.2f}", f"{CORR['n'][1]:+.2f}", f"{CORR['n'][2]:+.2f}"],
   ['Hosted-class share', f"{CORR['hosted'][0]:+.2f}", f"{CORR['hosted'][1]:+.2f}", f"{CORR['hosted'][2]:+.2f}"],
   ['Free-entry share', f"{CORR['free'][0]:+.2f}", f"{CORR['free'][1]:+.2f}", f"{CORR['free'][2]:+.2f}"],
   ['Weekend share', f"{CORR['weekend'][0]:+.2f}", f"{CORR['weekend'][1]:+.2f}", f"{CORR['weekend'][2]:+.2f}"]], 'mono')

ch_t = T(['Entry channel','Sep-26 clients','Sep-26 conv.','Prior 11 mo conv.','Sep-26 value/client','Prior 11 mo value/client'],
  [[c, chs['n'][c], P(chs['conv'][c]/chs['n'][c]*100),
    P(chh['conv'][c]/chh['n'][c]*100) if c in chh.index else '—',
    R(chs['rev'][c]/chs['n'][c]), R(chh['rev'][c]/chh['n'][c]) if c in chh.index else '—'] for c in chs.index], 'mono')

fmt_t = T(['Class format','Sep-26 clients','Sep-26 conv.','Prior 11 mo conv.','Sep-26 value/client','Prior value/client'],
  [[f, FSEP['n'][f], P(FSEP['conv_p'][f]), P(FHIST['conv_p'].get(f, np.nan)) if f in FHIST.index else '—',
    R(FSEP['arpu'][f]), R(FHIST['arpu'].get(f, np.nan)) if f in FHIST.index else '—'] for f in FSEP.sort_values('n', ascending=False).index], 'mono')

tr_t = T(['Trainer','Sept clients','Sept 2nd visit','All-time clients','All-time conversion','All-time 2nd visit','All-time value/client'],
  [[t, TSEP['n'][t], P(TSEP['sec_p'][t]), int(TALL['n'].get(t, 0)), P(TALL['conv_p'].get(t, np.nan)) if t in TALL.index else '—',
    P(TALL['sec_p'].get(t, np.nan)) if t in TALL.index else '—', R(TALL['ltv'].get(t, np.nan)) if t in TALL.index else '—']
   for t in TSEP.sort_values('n', ascending=False).index], 'mono')

trall_t = T(['Trainer','Clients','Conversion','2nd visit','Value / client','Total lifetime value'],
  [[t, int(TALL['n'][t]), P(TALL['conv_p'][t]), P(TALL['sec_p'][t]), R(TALL['ltv'][t]), R(TALL['rev'][t])] for t in TALL.sort_values('ltv', ascending=False).index], 'mono')

hp_t = T(['Partner programme','Clients','Converted','Conversion','Value / client','Total lifetime value'],
  [[nm, int(HP['clients'][nm]), int(HP['conv'][nm]), P(HP['conv_p'][nm]), R(HP['ltv'][nm]), R(HP['rev'][nm])] for nm in HP.sort_values('clients', ascending=False).head(14).index], 'mono')

ph_t = T(['September year','Phase','Clients','Conversion','2nd visit'],
  [[p['year'], p['phase'], p['n'], P(p['conv']), P(p['second'])] for p in ph], 'mono')

base_t = T(['Lifecycle stage','Members','Prior lifetime value','Value per member'],
  [[k, int(LIFE[k]), R(bh[bh['Lifecycle Status']==k]['revenue'].sum()), R(bh[bh['Lifecycle Status']==k]['revenue'].mean())] for k in ['Active','At Risk','Lapsed','Churned']], 'mono')

atrisk_t = T(['Member','Last visit','Days inactive','Prior value','Purchases','Visits / month','Late-cancel rate'],
  [[f"{r['First Name']} {r['Last Name']}".strip(), str(r['Last Visit Date'])[:10], int(r['days_since']) if pd.notna(r['days_since']) else '—',
    R(r['revenue']), int(r['Purchase Count Post Trial']), f"{r['Visits Per Month']:.1f}", f"{r['Late Cancel Rate Post Trial']}"]
   for _, r in risk.sort_values('revenue', ascending=False).head(25).iterrows()], 'mono small')

sep_tbl = T(['Member','First visit','Day','Trainer','Entry','Class','Channel','Visits','Converted'],
  [[f"{r['First Name']} {r['Last Name']}".strip(), str(r['fvd'])[:16], str(r['First Visit Day'])[:3],
    str(r['Trainer Name']), str(r['Is New']).replace('New - ',''), str(r['First Visit Entity Name'])[:34],
    str(r['Source'] if pd.notna(r['Source']) else '—')[:22], int(r['No of Visits']), 'Yes' if r['converted'] else 'No']
   for _, r in sep.sort_values('fvd').iterrows()], 'mono small')

ev1213 = sep1213.copy()
ev_tbl = T(['Member','Date','Day','Trainer','Entry type','Class','Paid / free','Visits','2nd visit','Value'],
  [[f"{r['First Name']} {r['Last Name']}".strip(), str(r['fvd'])[:10], str(r['First Visit Day'])[:3], str(r['Trainer Name']),
    str(r['Is New']).replace('New - ',''), str(r['First Visit Entity Name'])[:30],
    'Free' if str(r['Payment Method'])=='free' else (str(r['Payment Method'])), int(r['No of Visits']),
    'Yes' if pd.notna(r['days_2nd']) else 'No', R(r['revenue'])] for _, r in ev1213.sort_values('fvd').iterrows()], 'mono small')

# ---------------------------------------------------------------- recommendations
RECS = [
 ('01','Build a structured 48-hour follow-up into the trial experience','Studio Manager + Front Desk',
  'A second visit raises conversion odds from 1.1% to 61.9% and is worth ₹24,744 in lifetime value. The year has actually held this steady — Jan–Sep 2026 sits at 39.1% against 39.2% in 2025. September broke the pattern specifically, at 12.9% on the matured window.',
  f'Lifting September\'s matured slice from {K["mw_second_pct"]:.1f}% to a 30% second-visit rate would add roughly {K["sec_gap"]:.0f} return visits there — about {K["sec_gap"]*0.619:.0f} additional members, worth ₹{K["recover_2nd"]:,.0f} in lifetime value on that slice alone. Applied every month, the same discipline is worth well over ₹25 lakh a year.'),
 ('02','Separate hosted classes from the acquisition pipeline','Marketing + Studio Manager',
  '3,146 lifetime hosted/partner first visits have produced 223 conversions at 7.1%, worth ₹1,368 per client against a studio average of ₹5,507. Six Peakst8 editions brought 151 clients and ₹473 combined. The programme generates attendance reliably; it has simply never been engineered to convert.',
  'Freeing ~112 first-visit slots a month for trial and referral — channels converting at 11–28% — is the clearest reallocation available.'),
 ('03','Cap the size of any single intake event','Studio Manager',
  'The 12–13 September weekend delivered 30 clients in two days — 21% of the month, against a daily average of 4.8 — at zero conversions and ₹709 of revenue. It accounts for 68% of the month\'s conversion gap on 43% of the cohort. Correlation across 21 months puts hosted share against second-visit rate at −0.64, the strongest relationship in the data.',
  f'Prevents a repeat of the concentration that drove {K["ev_conv_share"]:.0f}% of September\'s conversion gap. Measured in lifetime value, the 12–13 block alone accounts for roughly ₹{K["ev_conv_gap_val"]:,.0f}.'),
 ('04','Shift intake weight from Sunday to Monday–Thursday','Studio Manager',
  'Weekday intake converts at 23.6% historically; weekend at 14.6%, and Sunday at 11.7%. September routed 52% of clients into weekends, including 39 onto Sundays at 2.6% conversion — while Monday, Tuesday and Thursday, historically the strongest days at 24.8–28.0%, received just 47 clients between them.',
  'A pure scheduling change with no added spend. Moving 30 clients per quarter to weekdays is worth roughly ₹4.5 lakh in expected value.'),
 ('05','Manage trainers on client lifetime value, not just class hours','Head of Training',
  'Across trainers with 40+ first classes, lifetime value per client ranges from ₹3,708 to ₹25,982 — a 7.0x spread. Nishanth Raj (₹25,982), Janhavi Jain (₹24,049) and Saniya Jaiswal (30.0% conversion on 80 clients) lead on both measures. September showed the model works: Anmol Sharma placed 6 of 14 new clients into a second class, the best follow-through in the studio.',
  'Lifting the five lowest-performing trainers to studio median adds ₹33,58,773 of lifetime value on existing volume, with no additional acquisition spend.'),
 ('06','Make Mat 57 and hosted powerCycle editions measurable, then decide','Programming',
  'Mat 57 has converted at 8.8% historically (₹2,776 per client) and 0% in September on 10 clients. powerCycle, historically the studio\'s second-strongest format at 21.7%, converted at 2.8% in September on 36 clients. Barre 57 remained the engine at 13.3% and 59% of the month\'s revenue.',
  'Reallocating 46 under-performing slots per month toward Barre 57 is worth approximately ₹2 lakh a quarter.'),
 ('07','Work the 170 At-Risk members this month','CRM / Retention',
  'These members are 31–60 days inactive, carry ₹32,00,706 of prior lifetime value and have historically been worth ₹18,828 each. A further 635 are Lapsed.',
  'Re-engaging 20% of the At-Risk group is worth approximately ₹6.4 lakh of latent value.'),
 ('08','Close the source-attribution gap','Operations / Data',
  '28.7% of the September cohort (41 of 143) has no source recorded, which caps how precisely channel ROI can be measured. Separately, 58 active members run late-cancel rates above 20%, quietly removing bookable capacity.',
  'Enables confident channel decisions from October onwards and recovers bookable class capacity.'),
]

RECS = RECS3
rec_html = ''.join(f'''<div class="rec">
 <div class="rn">{r[0]}</div>
 <div class="rb">
  <h3>{r[1]}</h3><div class="ro">{r[2]}</div>
  <p><span class="lbl">Reasoning</span>{r[3]}</p>
  <p class="imp"><span class="lbl">Expected impact</span>{r[4]}</p>
 </div></div>''' for r in RECS)

# ---------------------------------------------------------------- HTML
HTML = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Supreme HQ, Bandra — September 2026 Review</title>
<style>
 *{{box-sizing:border-box}}
 :root{{--ink:{INK};--mut:{MUT};--line:{LINE};--ter:{TER};--sage:{SAGE};--blu:{BLU};--gold:{GOLD};--bg:#FDFBF7}}
 body{{margin:0;background:var(--bg);color:var(--ink);
   font:16.5px/1.68 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}}
 .wrap{{max-width:1080px;margin:0 auto;padding:0 28px 110px}}
 .serif{{font-family:Georgia,"Iowan Old Style","Times New Roman",serif}}
 header{{background:linear-gradient(168deg,#221E1A 0%,#3A322B 62%,#4A3B31 100%);color:#FDFBF7;padding:74px 28px 62px;margin-bottom:52px}}
 header .inner{{max-width:1080px;margin:0 auto}}
 .kick{{font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:#C8B49E;margin-bottom:20px}}
 h1{{font-family:Georgia,"Iowan Old Style",serif;font-size:52px;line-height:1.06;margin:0 0 20px;font-weight:400;letter-spacing:-.015em}}
 header .lede{{color:#D8CDBF;margin:0;max-width:74ch;font-size:17.5px;line-height:1.62}}
 header .meta{{margin-top:30px;padding-top:22px;border-top:1px solid rgba(255,255,255,.15);display:flex;gap:34px;flex-wrap:wrap;font-size:13px;color:#B8A894}}
 .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:0 0 12px}}
 .kpi{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 20px}}
 .kpi .l{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-bottom:10px}}
 .kpi .v{{font-family:Georgia,serif;font-size:31px;font-weight:400;line-height:1.05;letter-spacing:-.02em}}
 .kpi .d{{font-size:12.5px;color:var(--mut);margin-top:8px;line-height:1.45}}
 .pos{{color:var(--sage)}} .neu{{color:var(--gold)}}
 h2{{font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ter);margin:74px 0 8px;font-weight:640}}
 h2 + .sub{{font-family:Georgia,serif;font-size:31px;font-weight:400;letter-spacing:-.018em;margin:0 0 22px;line-height:1.22}}
 h3{{font-size:18.5px;margin:0 0 7px;font-weight:640;letter-spacing:-.01em}}
 h4{{font-size:15px;margin:26px 0 10px;font-weight:640;color:var(--ink)}}
 p{{margin:0 0 17px}}
 .chart{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px 24px 14px;margin:0 0 24px}}
 .chart figcaption{{font-size:15px;font-weight:640;margin-bottom:14px;letter-spacing:-.008em}}
 .cnote{{font-size:12.5px;color:var(--mut);line-height:1.55;margin:6px 0 8px;padding-top:12px;border-top:1px solid var(--line)}}
 table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:14px;margin:0 0 12px}}
 th{{background:#F7F3EC;text-align:left;padding:12px 14px;font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--mut);font-weight:640;border-bottom:1px solid var(--line)}}
 td{{padding:10px 14px;border-bottom:1px solid #F4F0E9;vertical-align:top}}
 tr:last-child td{{border-bottom:none}} tbody tr:hover{{background:#FEFCF8}}
 table.small{{font-size:12.5px}} table.small td{{padding:7px 11px}}
 .mono td, .mono th{{font-variant-numeric:tabular-nums}}
 .call{{border:1px solid var(--line);border-left:3px solid var(--ter);border-radius:12px;background:#fff;padding:22px 24px;margin:0 0 24px}}
 .call.sage{{border-left-color:var(--sage)}} .call.gold{{border-left-color:var(--gold)}} .call.blu{{border-left-color:var(--blu)}}
 .call p:last-child{{margin-bottom:0}}
 .stat{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:20px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;margin:0 0 24px}}
 .stat .v{{font-family:Georgia,serif;font-size:29px;line-height:1;letter-spacing:-.02em}}
 .stat .l{{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);margin-top:9px;line-height:1.4}}
 details.ev{{border:1px solid var(--line);border-radius:12px;background:#fff;margin:0 0 22px;overflow:hidden}}
 details.ev summary{{cursor:pointer;list-style:none;padding:16px 22px;font-size:14px;font-weight:600;color:var(--blu);
   display:flex;align-items:center;gap:11px;user-select:none}}
 details.ev summary::-webkit-details-marker{{display:none}}
 details.ev .evi{{width:15px;height:15px;flex:0 0 15px;border-radius:4px;border:1.5px solid currentColor;position:relative;transition:.18s}}
 details.ev .evi:after{{content:"";position:absolute;left:4px;top:3.5px;width:5px;height:5px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);transition:.18s}}
 details.ev[open] .evi:after{{transform:rotate(225deg);top:5px}}
 details.ev summary:hover{{background:#FEFCF8}}
 .evb{{padding:4px 22px 20px;border-top:1px solid var(--line)}}
 .evb table{{margin-top:14px}}
 .hyp{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:0 0 26px}}
 .hcard{{border:1px solid var(--line);border-radius:14px;padding:22px;background:#fff}}
 .hcard .tag{{display:inline-block;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;padding:4px 10px;border-radius:100px;font-weight:640;margin-bottom:13px}}
 .tag.no{{background:#F5EDE9;color:#94513A}} .tag.yes{{background:#E9F1EC;color:#3D6B4C}} .tag.part{{background:#F6F1E4;color:#8C6E27}}
 .hcard h3{{font-size:16.5px;margin-bottom:9px}}
 .hcard p{{font-size:14.3px;margin:0;color:#3A342D;line-height:1.6}}
 .hcard .verdict{{font-size:13px;color:var(--mut);margin-top:12px;padding-top:11px;border-top:1px solid var(--line)}}
 .rec{{display:flex;gap:20px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;margin-bottom:16px}}
 .rn{{flex:0 0 42px;height:42px;border-radius:50%;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:15px}}
 .rb{{flex:1;min-width:0}} .ro{{font-size:12.5px;color:var(--mut);margin-bottom:14px}}
 .rec p{{font-size:14.5px;margin:0 0 12px;color:#2E2822;line-height:1.62}}
 .rec .imp{{margin-bottom:0;color:#3D6B4C}}
 .lbl{{display:block;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);font-weight:640;margin-bottom:3px}}
 ul{{margin:0 0 17px;padding-left:21px}} li{{margin-bottom:8px}}
 footer{{margin-top:70px;padding-top:26px;border-top:1px solid var(--line);font-size:13px;color:var(--mut);line-height:1.7}}
 @media(max-width:880px){{.kpis{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:35px}}h2+.sub{{font-size:24px}}}}
</style></head><body>

<header><div class="inner">
 <div class="kick">Performance Review &nbsp;·&nbsp; September 2026</div>
 <h1>Supreme HQ, Bandra</h1>
 <p class="lede">September brought the studio its highest September intake on record. It also produced its weakest conversion, and the second-weakest retention. This edition reads September against three years of history, adds the check-in ledger, the lead register and the sales ledger to the member file, tests eight candidate explanations against the data &mdash; and finds three that hold, one of which was not visible in any of the earlier numbers.</p>
 <div class="meta">
  <span>143 new clients</span><span>150,895 check-ins &middot; 25,315 leads &middot; 25,044 sales</span><span>Equal-observation methodology</span>
 </div>
</div></header>
<div class="wrap">

<div class="kpis">
 <div class="kpi"><div class="l">New clients</div><div class="v">{len(sep)}</div><div class="d pos">▲ 44% above September 2025 — the strongest September on record</div></div>
 <div class="kpi"><div class="l">Share of network intake</div><div class="v">36.6%</div><div class="d pos">▲ up from 27.7% in September 2025</div></div>
 <div class="kpi"><div class="l">Genuine 2nd-visit rate</div><div class="v">{P(K3['true2nd'])}</div><div class="d neu">▼ not the headline {P(K3['head2nd'])} — 11 of 24 "returns" were pre-paid</div></div>
 <div class="kpi"><div class="l">Projected value shortfall</div><div class="v">{R(K['shortfall'])}</div><div class="d neu">September cohort, against normal lifetime yield</div></div>
</div>
<div class="kpis" style="margin-top:16px">
 <div class="kpi"><div class="l">Studio cash received</div><div class="v">{R(K3['cash26'])}</div><div class="d pos">▬ within {abs(K3['cash_yoy']):.1f}% of September 2025 — the till held</div></div>
 <div class="kpi"><div class="l">Funded by the existing base</div><div class="v">{P(K3['base_share'])}</div><div class="d neu">▲ new clients contributed only {P(100-K3['base_share'])} of September</div></div>
 <div class="kpi"><div class="l">Lead-to-member win rate</div><div class="v">{P(K3['w26_rate'])}</div><div class="d neu">▼ from {P(K3['w25_rate'])} a year ago, on {K3['lead_yoy']:.0f}% more leads</div></div>
 <div class="kpi"><div class="l">Footfall</div><div class="v">{seats['Sept 2026']['filled']:,}</div><div class="d pos">▬ against {seats['Sept 2025']['filled']:,} last September — essentially flat</div></div>
</div>

<h2>Start here</h2>
<div class="sub">September is an outlier inside a steady year — not the start of a decline</div>
<p>The most important fact about September 2026 is what it is <em>not</em>. It is not the month the studio's fundamentals broke. Over the twelve months to September, Bandra's second-visit rate held at <strong>29.2% versus 29.1% the year before</strong>, and the revenue generated per new client within 90 days <strong>rose to ₹2,431 from ₹2,259</strong> — the second consecutive annual improvement. Volume across the trailing twelve months was effectively flat, at 1,439 clients against 1,475.</p>
<p>Year-to-date the picture is equally reassuring on the metric that matters most. Across January to September 2026, the share of new clients who returned for a second class was <strong>39.1%, against 39.2% in 2025</strong> and 37.4% in 2024. Whatever went wrong in September, it did not go wrong for the year.</p>
<p>One qualification belongs here rather than in a footnote, because it cuts across every retention figure in this report and is quantified in full later. <strong>Roughly a third of what the studio records as a "second visit" is the pre-paid second half of a <em>Newcomers 2 For 1</em> intro pack</strong> — a class the client has already bought and is simply using up. These year-level rates are therefore the right measure for spotting change over time, because the same distortion runs through all three years, but they overstate the absolute level of genuine repeat demand. Where a true return rate is quoted below, the pre-paid visits have been removed.</p>
<p>What September did was concentrate a set of already-visible weaknesses into a single month, in a way that is now measurable and therefore fixable. This edition adds three further sources &mdash; the full 150,895-row check-in ledger, the 25,315-record lead register and the 25,044-record sales ledger &mdash; which together make it possible to say not just <em>what</em> happened in September but <em>where</em> it happened and <em>who</em> it happened to.</p>
<p>The short version of what those sources add. September's revenue was <strong>carried almost entirely by members the studio already had</strong>, which is why the month looked normal in the accounts while its future quietly thinned. <strong>Nearly six in ten of the month's failed leads were simply never reached, or asked for more time.</strong> The studio's second-visit rate is <strong>overstated by the intro pack, which pre-pays the second visit</strong>. And the single most consequential change at Bandra this year was not in marketing or pricing at all: <strong>it was who was standing at the front of the room.</strong></p>
{TTM_T}
{ev('View the full twelve-month and Jan–Sep comparison, three consecutive years', JS_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Matured cohort = members with at least 90 days of observation, so every year is judged on the same basis. Revenue per new client counts first-purchase value within 90 days, divided by the matured cohort.</p>')}
{CH2}

<h2>The number that explains the others</h2>
<div class="sub">The month looked fine in the accounts because the existing base paid for it</div>
{R3['RECON']}

<h2>The September picture</h2>
<div class="sub">Acquisition succeeded. Follow-through did not.</div>
<p>Volume was the month's clear success. At 143 new clients, September 2026 was the studio's strongest September in the dataset — 44% above 2025 and 22% above the trailing monthly average — and Bandra's share of group-wide intake climbed to <strong>36.6%</strong> from 27.7% a year earlier. The studio is doing more than its share of the network's front-end work.</p>
<p>What did not follow was return visits. Restricting comparison to clients who visited in the first 13 days of the month — so that every one of them has had at least 28 days to come back — <strong>12.9% of September clients returned for a second class within 30 days, against a 29.4% norm</strong>. That single number accounts for almost all of the month's value loss, because the second visit is by far the strongest predictor of everything downstream.</p>
{CH1}
{CH3}
{sc_t}
{ev('View September against August and September 2025, metric by metric', sep_t + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">September 2024 was the strongest of the three on quality and the weakest on volume — the mirror image of 2026. Conversion and second-visit rates in this table are 30-day equal-window figures.</p>')}

<h2>What went well</h2>
<div class="sub">Four things September got right — and should keep</div>
<div class="call sage">
<h3>Conversion speed was the fastest on record</h3>
<p>Clients who converted in September did so in a <strong>median of 3 days</strong>, against an all-time Bandra median of 8. Two-thirds converted within a week. When intent was present, the studio captured it quickly and without friction — a genuine operational strength worth protecting.</p>
</div>
<div class="call sage">
<h3>Those who did convert bought larger packages</h3>
<p>The median first purchase among September converters was <strong>₹16,734 — the highest of any month in the past year</strong>, against ₹14,222 in August and ₹9,639 in July. Half bought the Studio 12-Class Package, compared with 23% historically. September's converters were fewer but higher-intent and higher-value.</p>
</div>
<div class="call sage">
<h3>Paid-entry clients performed exactly to norm</h3>
<p>Clients who paid for their first visit converted at <strong>25.0%, against a 25.8% historical rate</strong>, at ₹9,824 of value each. This is the studio's smallest entry channel at just 4 clients — and its most reliable. It is a case for considered expansion, not retreat.</p>
</div>
<div class="call sage">
<h3>Barre 57 held the line, and several trainers excelled</h3>
<p>Barre 57 delivered <strong>59% of the month's revenue</strong> and the studio's best format-level conversion at 13.3%. Individually, <strong>Anmol Sharma placed 6 of 14 new clients into a second class</strong> — a 42.9% follow-through rate that is the strongest individual result in the studio this month, and proof the model works when it is executed well.</p>
</div>
{CH6}
{ev('View September format and trainer performance in full', '<h4>By class format</h4>' + fmt_t + '<h4>By first-class trainer</h4>' + tr_t)}

<h2>Root cause</h2>
<div class="sub">Five explanations tested against the data</div>
<p>Eight candidate explanations were examined &mdash; the ones that are obvious, and the ones that are easy to miss. Four do not survive contact with the numbers. Three do, and they turn out to be linked.</p>
<div class="hyp">
 <div class="hcard"><div class="tag yes">Confirmed &mdash; first order</div><h3>The teaching roster turned over</h3>
  <p>Five trainers who carried a large share of client-facing classes in September 2025 &mdash; Cauveri Vikrant, Karanvir Bhatia, Karan Bhatia, Simonelle De Vitre and Mrigakshi Jaiswal &mdash; took <strong>{abs(K3['dgrp_pct']):.0f}% fewer classes in September 2026</strong> ({K3['dgrp25']:,} down to {K3['dgrp26']:,}). The group that absorbed that load rose from {K3['igrp25']:,} classes to <strong>{K3['igrp26']:,}, up {K3['igrp_pct']:.0f}%</strong>. Their clients are worth materially different amounts: <strong>{R(lv_dep)} per new client for the departing group against {R(lv_new)} for the incoming one.</strong></p>
  <div class="verdict">The largest single change at Bandra between the two Septembers was not demand, price or marketing. It was an unmeasured swap of the people who deliver the first class &mdash; the one moment that determines whether a client ever comes back.</div>
 </div>
 <div class="hcard"><div class="tag yes">Confirmed</div><h3>One trainer held {K3['resh_share']:.0f}% of the month's intake, and none returned</h3>
  <p>Reshma Sharma received <strong>{K3['resh_n']} of September's 143 new clients &mdash; {K3['resh_share']:.0f}% of the entire month</strong>. Not one attended a second class, anywhere in the network. Trial-for-trial, her clients converted at <strong>0 of {K3['tri_resh_n']}</strong> against <strong>{K3['tri_oth_conv']} of {K3['tri_oth_n']} ({P(K3['tri_oth_rate'])})</strong> for the rest of the studio.</p>
  <div class="verdict">Her all-time record is unremarkable rather than poor, which is the point: a zero month can happen to anyone, and the studio should never have a quarter of its acquisition resting on one person with no second look.</div>
 </div>
 <div class="hcard"><div class="tag yes">Confirmed</div><h3>The lead pipeline stopped closing</h3>
  <p>Leads rose <strong>{K3['lead_yoy']:.0f}%</strong> year-on-year while wins fell <strong>{abs(K3['win_yoy']):.0f}%</strong>. Win rate collapsed from <strong>{P(K3['w25_rate'])} to {P(K3['w26_rate'])}</strong>. Of the {K3['fail_tot']:,} leads that closed as lost with a reason recorded, <strong>{P(K3['unresp'])} were simply unreachable and {P(K3['postponed'])} were postponements</strong>; only {P(K3['price_obj'])} cited price.</p>
  <div class="verdict">Interest is not the constraint. Follow-up is. This is the cheapest problem in the review to fix and the one with the shortest payback.</div>
 </div>
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Ganesh Chaturthi disrupted the month</h3>
  <p>Ganesh Chaturthi fell on 14 September, with visarjan on the 25th — and Bandra sits on the procession route. But splitting September into festival phases, the <strong>pre-festival window converted at 7.1%, no better than the festival window at 6.2%</strong>. A festival suppresses a studio for ten days; it does not suppress the week before it. The weakness was already present on 1 September.</p>
  <div class="verdict">September 2024 shows the same test with the opposite result: pre-festival 46.7%, festival 24.5%. The pattern is not stable enough to be causal.</div>
 </div>
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Demand fell across the market</h3>
  <p>On the identical matched basis, <strong>Kwality House converted at 13.8% and Kenkere House at 30.8%</strong> while Bandra sat at 12.5%. Kenkere's conversion actually improved year-on-year. Bandra's intake also rose 44%, which is not the signature of a soft market.</p>
  <div class="verdict">The dip is studio-specific, not market-wide.</div>
 </div>
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Volume overloaded the team</h3>
  <p>Across 21 months at Bandra, monthly volume correlates with conversion rate at just <strong>{CORR['n'][0]:+.2f}</strong> and with second-visit rate at <strong>{CORR['n'][1]:+.2f}</strong>. Some of the studio's strongest months were also among its highest-volume.</p>
  <div class="verdict">High intake is not, by itself, a cause of poor conversion. This matters: it points away from staffing and effort.</div>
 </div>
 <div class="hcard"><div class="tag yes">Confirmed</div><h3>Intake mix shifted toward low-intent entry</h3>
  <p>Hosted-class share against second-visit rate correlates at <strong>{CORR['hosted'][1]:+.2f}</strong> across 21 months — the strongest relationship in the data. Free-entry share at <strong>{CORR['free'][1]:+.2f}</strong>, weekend share at <strong>{CORR['weekend'][1]:+.2f}</strong>. September combined a 23.8% hosted share with a 52.4% weekend share, and 18.2% free entry.</p>
  <div class="verdict">This is a mix problem, not a demand or effort problem — and mix is directly controllable.</div>
 </div>
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Capacity or attendance was down</h3>
  <p>Bandra ran <strong>{seats['Sept 2026']['sessions']} classes in September 2026 against {seats['Sept 2025']['sessions']} a year earlier</strong>, filled <strong>{seats['Sept 2026']['filled']:,} seats against {seats['Sept 2025']['filled']:,}</strong>, at {P(seats['Sept 2026']['util'])} capacity utilisation against {P(seats['Sept 2025']['util'])}. Average class size was {seats['Sept 2026']['avg']:.1f} against {seats['Sept 2025']['avg']:.1f}.</p>
  <div class="verdict">The studio ran very close to a normal schedule with a normal audience. Footfall fell only {abs((seats['Sept 2026']['filled']/seats['Sept 2025']['filled']-1)*100):.1f}% — there was no shortage of people in the room.</div>
 </div>
 <div class="hcard"><div class="tag part">Contributing</div><h3>Follow-up execution on the 12–13 September weekend</h3>
  <p>The month's single largest intake block — <strong>30 clients in two days, 21% of the month, against a daily average of 4.8</strong> — produced zero conversions and ₹709 of revenue. Thirteen were attendees of one partner event, none of whom returned.</p>
  <div class="verdict">It accounts for {K['ev_conv_share']:.0f}% of the month's conversion gap on 43% of the cohort. A specific, datable, avoidable trigger.</div>
 </div>
</div>
{corr_t}
{ev('View the month-by-month driver table behind these correlations', drv_t + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Every Bandra month since January 2025 with at least 20 matured members. Hosted, free and weekend shares are all measured over the full monthly intake. The August 2026 row — 47.1% hosted, 71.9% weekend — is the most extreme mix in the set, and posted the second-lowest second-visit rate.</p>')}
{CH4}
{ph_t and ev('View September by Ganeshotsav phase across three years', ph_t)}

<h2>The finding that was hiding</h2>
<div class="sub">Who was teaching, and what happened to the clients they received</div>
{R3CH['CHR1']}
{R3['ROSTER']}
{R3TB['roster_tbl'] and ev('View every trainer who gained or lost classes, with their all-time record', R3TB['roster_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Sept 2025 and Sept 2026 class counts from the check-in ledger. Lifetime clients, conversion and value per client from the member cohort file, which uses first-visit location. Trainer names include part-time and guest instructors.</p>')}
{R3['CONC']}
{R3TB['conc_tbl'] and ev('View September 2026 new clients by the trainer who taught their first class', R3TB['conc_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Every client in the September cohort, grouped by the trainer who took their first class. "Returned for any further visit" counts any subsequent check-in at any location, not only within 30 days.</p>')}

<h2>The pipeline problem</h2>
<div class="sub">More interest than ever, and less of it being closed</div>
{R3CH['CHR2']}
{R3['FUNNEL']}
{R3TB['ch_tbl'] and ev('View every lead channel with its full economics', R3TB['ch_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Lifetime figures for Bandra leads. Win rate is leads with status "Won" as a share of all leads created. Value per lead is total recorded lifetime value divided by leads — which naturally penalises channels whose leads are still open.</p>')}
{R3CH['CHR3']}

<h2>The intro pack, and an honest second-visit rate</h2>
<div class="sub">The cheapest class the studio sells, and what it actually buys</div>
{R3['INTRO']}

<h2>What the studio did not see</h2>
<div class="sub">Three second-order effects, and one structural risk</div>
{R3['CAP']}
{R3['ATTR']}
{R3['BASE']}

<h2>Where the value went</h2>
<div class="sub">A decomposition, not an accusation</div>
<div class="stat">
 <div><div class="v">{K['conv_gap']:.1f}</div><div class="l">Fewer converters than the norm predicts</div></div>
 <div><div class="v">{K['ev_conv_share']:.0f}%</div><div class="l">Of that gap belonging to 12–13 September</div></div>
 <div><div class="v">{K['sec_gap']:.0f}</div><div class="l">Missing second visits, matured slice</div></div>
 <div><div class="v">{R(K['proj_ltv'])}</div><div class="l">Projected lifetime shortfall, full cohort</div></div>
</div>
<p>On the fully matured slice of the September cohort — the {K['mw_n']} clients who visited between 1 and 13 September, each observed for at least 28 days — the trailing norm predicts {K['mw_n']*bc:.1f} thirty-day conversions. <strong>{K['mw_conv']} occurred.</strong></p>
<p>The distribution of that shortfall is the most important finding in this review. <strong>The first eleven days of September performed essentially to norm</strong> — 5 conversions against 5.7 expected, a gap of less than one client across 40 people. <strong>The entire remaining shortfall, {K['ev_conv_share']:.0f}% of it, sits in the weekend of 12–13 September</strong>, which absorbed 30 clients in two days and produced none of the month's conversions.</p>
<p>Scaled across all 143 September clients, the gap amounts to roughly <strong>{K['full_gap']:.0f} clients who would normally have become members</strong>. Measured in first-purchase revenue over the next few months that is about {R(K['near_term'])}; measured across the lifetime of those relationships, at the studio's observed conversion economics, it is approximately <strong>{R(K['proj_ltv'])}</strong>. Separately, the {K['sec_gap']:.0f} missing second visits in the matured slice represent around {K['sec_gap']*0.619:.0f} further conversions — about {R(K['recover_2nd'])} of lifetime value that is still recoverable through follow-up rather than acquisition.</p>
<p>That decomposition uses the ledger's own visit counts, and the intro pack touches it too. On the same matched window the genuine second-visit rate is <strong>{P(K3['mw_gen'])} rather than the published {P(K3['mw_head'])}</strong>, because {K3['mw_pre']} of the nine returns were pre-paid 2-for-1 redemptions. Setting that alongside a baseline adjusted the same way &mdash; {P(K3['base_gen'])} genuine returns historically &mdash; the true gap on the matured slice is about <strong>{K3['gen_gap_n']:.1f} returns rather than {K['sec_gap']:.1f}</strong>, worth roughly {R(K3['gen_gap_val'])} of recoverable lifetime value. The correction narrows the distance from normal but sharpens the level: September's genuine return rate is barely a third of the studio's own.</p>
<p>Seen this way, September is not a story of systemic failure, and it is certainly not a story about the studio's everyday operation. Ordinary trading in the first eleven days was sound. Two days of concentrated, complimentary, event-driven intake absorbed a fifth of the month's clients, returned none of them, and accounted for effectively the whole of the month's value loss. That is a schedulable, preventable event — which is why it is the first recommendation in this report rather than an acceptance of decline.</p>
{ev('View all 30 clients from the 12–13 September weekend', ev_tbl)}
{ev('View the full September 2026 cohort, member by member', sep_tbl)}

<h2>The largest lever</h2>
<div class="sub">The second visit, and why it is worth more than any marketing spend</div>
{CH5}
<p>Across 4,218 Bandra first visits, clients who returned for a second class converted at <strong>61.9%</strong> and are worth <strong>₹24,982</strong> each. Those who did not converted at <strong>1.1%</strong> and are worth <strong>₹238</strong>. The second visit is worth <strong>₹24,744 in lifetime value</strong> and multiplies conversion odds 57-fold.</p>
<p>The encouraging finding is that this is a well-understood lever already being pulled effectively at studio level. The year's 39.1% second-visit rate is essentially unchanged from 2025 — evidence that the capability exists. September's shortfall was local and specific rather than a missing skill.</p>
{ev('View second-visit economics by entry channel and class format', ch_t + '<h4 style="margin-top:22px">By class format</h4>' + fmt_t)}

<h2>The biggest opportunity</h2>
<div class="sub">The hosted / partner programme: high volume, unrealised value</div>
{CH7}
<div class="stat">
 <div><div class="v">{HOSTED['n']:,}</div><div class="l">Lifetime first visits</div></div>
 <div><div class="v">{P(HOSTED['conv_p'])}</div><div class="l">Conversion rate</div></div>
 <div><div class="v">{R(HOSTED['ltv'])}</div><div class="l">Value per client</div></div>
 <div><div class="v">{R(5507)}</div><div class="l">Studio average</div></div>
</div>
<p>The hosted and partner programme is the studio's most reliable source of new faces and its least effective source of new clients. Across its life it has produced <strong>3,146 first visits and 223 conversions at 7.1%, worth ₹1,368 per client against a studio average of ₹5,507</strong>. Several flagship programmes have produced nothing at all: KRC x Avg Run Club brought 51 clients and zero revenue; Pickle Social brought 42 and zero; six Peakst8 editions brought 151 clients and ₹473 between them.</p>
<p>The constructive reading is that this is an <em>engineering</em> gap, not a strategic dead end. Two programmes show what the model can do when it is designed for conversion — <em>Sweat Fest by Sisters in Sweat</em> (28 clients, ₹5,362 each, close to studio average) and <em>Sweat Fest Lite</em> (50 clients, ₹802). The attendance is being generated; the pathway from attendance to membership has simply never been built.</p>
{ev('View the hosted programme month by month, and every programme ranked', HM.reset_index().assign(conv_p=lambda d: d['conv']/d['clients']*100, ltv=lambda d: d['rev']/d['clients']).rename(columns={'cohort':'Month','clients':'Clients','conv':'Converted','rev':'Revenue','conv_p':'Conversion %','ltv':'Value per client'})[['Month','Clients','Converted','Conversion %','Value per client','Revenue']].round(1).to_html(index=False) + '<h4 style="margin-top:22px">All programmes by volume</h4>' + hp_t)}

<h2>The studio base</h2>
<div class="sub">A loyal core, and a recoverable lapsed middle</div>
<p>Bandra has 4,181 members whose home studio it is. The active core is 385 strong and has generated <strong>₹1,89,87,532 of lifetime value</strong> — an average of ₹49,318 per active member, a level very few fitness studios reach. Value is concentrated: the top 5% of members account for 70.7% of lifetime value, and the top 1% for 28.1%.</p>
<p>The immediate opportunity sits with the <strong>170 members classified At Risk</strong> — 31 to 60 days inactive, carrying ₹32,00,706 of prior lifetime value and historically worth ₹18,828 each. These are known, contactable, and already proven willing to pay. In parallel, <strong>58 active members carry late-cancel rates above 20%</strong>, quietly removing bookable capacity from a studio whose constraint is engagement rather than demand.</p>
{base_t}
{ev('View the 25 highest-value At-Risk members, with contact and behaviour detail', atrisk_t + '<p style="font-size:13px;color:#7A7267;margin-top:14px">A complete list of all 170 At-Risk members, with email and phone, is supplied in the accompanying Excel workbook (sheet 12).</p>')}

<h2>Trainer effect</h2>
<div class="sub">A 7x spread in client value, on identical volumes</div>
{CH8}
<p>Among trainers with 40 or more first classes, lifetime value per client ranges from <strong>₹3,708 to ₹25,982</strong>. Nishanth Raj (₹25,982), Janhavi Jain (₹24,049) and Saniya Jaiswal (30.0% conversion on 80 clients) lead on both conversion and value. This spread exists on comparable client volumes, which makes it a coaching and follow-up question rather than a demand question.</p>
<p>One caution on reading September's trainer table: <strong>Reshma Sharma took 33 clients, 23% of the month's intake against her usual 7–8</strong>, and recorded no conversions and one visit per client. Her all-time record across 364 clients is 20.9% conversion and ₹7,310 per client. Her September book was heavily distorted — 13 hosted-class attendees, 18 Sunday visits, 18 free trials — and is better read as a reflection of the mix problem than of the trainer.</p>
{ev('View full trainer performance, September and all-time', tr_t + '<h4 style="margin-top:22px">All-time, trainers with 40+ first classes</h4>' + trall_t)}

<h2>Recommendations</h2>
<div class="sub">Eight actions, ordered by expected value</div>
<p>These are ordered so that the first three can be acted on this week without spending anything. The two that involve spending or pricing &mdash; the intro pack and the channel mix &mdash; sit in the middle deliberately: they are worth more, but they should follow the free fixes rather than lead them.</p>
{rec_html}

<h2>Method and limitations</h2>
<div class="sub">How to read these numbers, and what they cannot show</div>
<h4>The equal-observation principle</h4>
<p>Conversions at Bandra take time: the median happens on day 8, 49% within a week, 69% within 30 days and 81% within 90. A September cohort read in mid-October has therefore not had a fair chance to convert, and comparing its raw rate to a settled September 2025 would overstate any decline considerably. Every rate in this review is computed on an equal-observation basis — a 30-day window, or first visits restricted to days 1–13 of the month so every client has at least 28 days of history. Raw headline rates appear only where they are explicitly labelled.</p>
<h4>Why September-to-September comparisons need care</h4>
<p>Ganesh Chaturthi fell on 27 August in 2025 and 14 September in 2026. September 2025 was therefore a clean post-festival month while September 2026 absorbed the full festival — which makes the two months structurally different before a single client is counted. This is why the year-level and trailing-twelve-month comparisons carry more weight in this review than the single-month year-on-year figure.</p>
{mo_t}
{sep_t}
<h4>Known limitations</h4>
<ul>
 <li><strong>Attribution.</strong> 28.7% of the September cohort has no source recorded, and the gap is concentrated in the referral channel, where 48.3% of non-converting clients are unsourced against 24.0% for trials. Channel conclusions are drawn from the attributed majority.</li>
 <li><strong>The intro pack.</strong> A 2-for-1 buyer's second class is pre-paid and is not a repeat-purchase decision. Charts and tables elsewhere in this report use the ledger's own visit counts; where a genuine second-visit rate is quoted it excludes the 11 pre-paid redemptions in the September cohort. The studio should adopt "third visit" as the standard definition of a returning client for anyone who entered on the pack.</li>
 <li><strong>Trainer attribution.</strong> "First-class trainer" is the instructor who took a client's very first visit, and it is the only trainer link the data supports. It does not follow that a trainer caused a client's outcome; it does mean the relationship is measurable and worth monitoring.</li>
 <li><strong>Lead stage names.</strong> Drop-off reasons are drawn from the 2,572 Bandra leads that have closed as lost with a reason recorded. A further 4,244 non-won leads remain in open or in-progress stages and are excluded from that table.</li>
 <li><strong>Value, not margin.</strong> Revenue figures are lifetime value as recorded at the snapshot. No cost, CAC or contribution-margin data is present, so payback periods cannot be calculated.</li>
 <li><strong>Cohort age.</strong> The September cohort is 11 to 41 days old and its lifetime value will keep growing. The ₹{K['proj_ltv']:,.0f} shortfall is a projection against normal yield, not a settled figure; the near-term, first-purchase portion of it is about ₹{K['near_term']:,.0f}.</li>
 <li><strong>Legacy records.</strong> 8,711 "Import Visits" placeholder rows (dated 2020-01-01) are excluded throughout. 182 members appear twice where a placeholder duplicates a tracked record.</li>
 <li><strong>Excluded from scope.</strong> This report covers first-visit acquisition and the resulting member value. It does not analyse class-fill rates, capacity utilisation, retail or membership renewals, which need separate data.</li>
</ul>
<h4>Source and reproducibility</h4>
<p>Four sources, all dated to the same snapshot. The member file ("Day End Report &ndash; Part 1 &ndash; New"), 21,171 rows covering 20,989 unique members, provides cohorts, conversion and lifetime value. The check-in ledger ("Day End Report &ndash; Part 4"), 150,895 attended-class records, provides attendance, class capacity, visit numbering, product-per-visit and trainer attribution. The lead register ("&#9678; PM &ndash; Leads"), 25,315 records, provides acquisition channels, stages and drop-off reasons. The sales ledger ("Sales &ndash; Raw"), 25,044 succeeded payments, provides cash received, discounting and the intro-pack programme.</p>
<p>Cohort assignment is by first-visit location and month; home-location data is used only for base-health analysis. Check-in records are joined to cohorts by member ID. Every figure is reproduced by the scripts in <code>/analysis</code> and <code>/analysis2</code>, and all underlying tables are provided in the accompanying Excel workbook.</p>

<footer>Supreme HQ, Bandra · September 2026 performance review · prepared 11 October 2026<br/>
Revenue figures are gross lifetime value as recorded at snapshot, not contribution margin.</footer>
</div></body></html>'''

open('/home/user/Bandra_September_2026_Performance_Review.html', 'w').write(HTML)
open('/home/user/Bandra_September_2026_Review_v3.html', 'w').write(HTML)

# ---------------------------------------------------------------- Excel
def rt(s): return s.replace('₹', '\u20b9')
with pd.ExcelWriter('/home/user/Bandra_September_2026_Data.xlsx', engine='openpyxl') as xw:
    pd.DataFrame([{'Window': k, 'New clients': v['clients'], '30-day conversion %': round(v['conv30'], 1),
                   '30-day 2nd-visit %': round(v['second30'], 1), 'Revenue per new client (90-day)': round(v['rev90'])}
                  for k, v in TTM.items()]).to_excel(xw, sheet_name='1. Twelve-month view', index=False)
    pd.DataFrame([{'Period': f'{y} Jan-Sep', 'New clients': JANSEP[y]['clients'], 'Matured cohort': JANSEP[y]['n90'],
                   'Converted (90d)': JANSEP[y]['c90'], '90-day conversion %': round(JANSEP[y]['conv90'], 1),
                   '2nd-visit %': round(JANSEP[y]['second'], 1), 'Revenue per new client': round(JANSEP[y]['revnew']),
                   'Median first package': JANSEP[y]['pkg']} for y in [2024, 2025, 2026]]).to_excel(xw, sheet_name='2. Year to date', index=False)
    MO.to_excel(xw, sheet_name='3. Monthly YoY', index=False)
    pd.DataFrame([
      {'Measure':'Conversion (30-day)','Sep-2026 matured window %':round(K['mw_conv_pct'],1),'Baseline Oct25-Aug26 %':round(base_conv,1),'Gap (converters)':round(K['conv_gap'],1)},
      {'Measure':'2nd visit (30-day)','Sep-2026 matured window %':round(K['mw_second_pct'],1),'Baseline Oct25-Aug26 %':round(base_2nd,1),'Gap (visits)':round(K['sec_gap'],1)},
      {'Measure':'Visits per client','Sep-2026 matured window %':round(mw['No of Visits'].mean(),2),'Baseline Oct25-Aug26 %':round(base_vis,2),'Gap (converters)':None},
      {'Measure':'Revenue per client','Sep-2026 matured window %':round(mw['revenue'].mean()),'Baseline Oct25-Aug26 %':round(base_rev),'Gap (converters)':None},
     ]).to_excel(xw, sheet_name='3b. Canonical basis', index=False)
    pd.DataFrame([
      {'Block':'Sep 1-13 (matured window)','Clients':len(mw),'Converters (30d)':int(mw_c30),'Expected':round(len(mw)*bc,1),'Gap':round(K['conv_gap'],1),'Share of gap %':100.0},
      {'Block':'  of which Sep 1-11','Clients':len(sep1_11_),'Converters (30d)':int((sep1_11_['converted']&(sep1_11_['conv_span']<=30)).sum()),'Expected':round(len(sep1_11_)*bc,1),'Gap':round(len(sep1_11_)*bc-(sep1_11_['converted']&(sep1_11_['conv_span']<=30)).sum(),1),'Share of gap %':round((len(sep1_11_)*bc-(sep1_11_['converted']&(sep1_11_['conv_span']<=30)).sum())/K['conv_gap']*100,0)},
      {'Block':'  of which Sep 12-13','Clients':len(sep1213_),'Converters (30d)':int(ev_c30),'Expected':round(len(sep1213_)*bc,1),'Gap':round(ev_conv_gap,1),'Share of gap %':round(K['ev_conv_share'],0)},
      {'Block':'Full cohort projection','Clients':len(sep),'Converters (30d)':int(K['full_gap']),'Expected':None,'Gap':None,'Share of gap %':None},
      {'Block':'  Projected lifetime shortfall','Clients':None,'Converters (30d)':None,'Expected':None,'Gap':round(K['proj_ltv']),'Share of gap %':None},
      {'Block':'  Near-term first-purchase shortfall','Clients':None,'Converters (30d)':None,'Expected':None,'Gap':round(K['near_term']),'Share of gap %':None},
      {'Block':'  Recoverable via 2nd-visit follow-up','Clients':None,'Converters (30d)':None,'Expected':None,'Gap':round(K['recover_2nd']),'Share of gap %':None},
     ]).to_excel(xw, sheet_name='3c. Gap decomposition', index=False)
    pd.DataFrame([{'September': y, 'New clients': SEPS[y]['n'], '30-day conversion %': round(SEPS[y]['conv30'], 1),
                   '30-day 2nd-visit %': round(SEPS[y]['second30'], 1), 'Revenue': SEPS[y]['rev'],
                   'Revenue per client': round(SEPS[y]['arpu'])} for y in [2024, 2025, 2026]]).to_excel(xw, sheet_name='4. September 3yr', index=False)
    DR.round(1).to_excel(xw, sheet_name='5. Driver table', index=False)
    pd.DataFrame([{'Intake characteristic': k, 'vs conversion': f'{v[0]:+.2f}', 'vs 2nd visit': f'{v[1]:+.2f}', 'vs revenue/client': f'{v[2]:+.2f}'} for k, v in CORR.items()]).to_excel(xw, sheet_name='6. Correlations', index=False)
    pd.DataFrame(ph).round(1).to_excel(xw, sheet_name='7. Festival phases', index=False)
    rt(sep_tbl and pd.DataFrame([{'Member': f"{r['First Name']} {r['Last Name']}".strip(), 'First visit': r['fvd'],
       'Day': r['First Visit Day'], 'Trainer': r['Trainer Name'], 'Entry type': r['Is New'],
       'Class': r['First Visit Entity Name'], 'Source': r['Source'], 'Visits': r['No of Visits'],
       'Converted': bool(r['converted']), '2nd visit': bool(pd.notna(r['days_2nd'])),
       'Value': r['revenue'], 'Payment method': r['Payment Method']} for _, r in sep.sort_values('fvd').iterrows()])).to_excel(xw, sheet_name='8. Sept cohort (143)', index=False)
    rt(pd.DataFrame([{'Member': f"{r['First Name']} {r['Last Name']}".strip(), 'Date': r['fvd'], 'Trainer': r['Trainer Name'],
       'Entry type': r['Is New'], 'Class': r['First Visit Entity Name'], 'Source': r['Source'],
       'Visits': r['No of Visits'], 'Converted': bool(r['converted']), 'Value': r['revenue']} for _, r in sep1213.sort_values('fvd').iterrows()])).to_excel(xw, sheet_name='9. Sep 12-13 weekend', index=False)
    chs.reset_index().to_excel(xw, sheet_name='10. Channels', index=False)
    FSEP.reset_index().to_excel(xw, sheet_name='11. Formats', index=False)
    TALL.reset_index().to_excel(xw, sheet_name='12. Trainers all-time', index=False)
    HM.reset_index().to_excel(xw, sheet_name='13. Hosted programme', index=False)
    HP.reset_index().to_excel(xw, sheet_name='14. Partner programmes', index=False)
    pd.DataFrame([{'Stage': k, 'Members': int(LIFE[k]), 'Prior lifetime value': bh[bh['Lifecycle Status']==k]['revenue'].sum(),
                   'Value per member': round(bh[bh['Lifecycle Status']==k]['revenue'].mean())} for k in ['Active','At Risk','Lapsed','Churned']]).to_excel(xw, sheet_name='15. Base health', index=False)
    risk[['Member Id','First Name','Last Name','Email','Phone Number','Last Visit Date','days_since','revenue',
          'Purchase Count Post Trial','Visits Per Month','Late Cancel Rate Post Trial']].rename(columns={'days_since':'Days inactive','revenue':'Prior lifetime value'}).sort_values('Prior lifetime value', ascending=False).to_excel(xw, sheet_name='16. At-risk members', index=False)
    pd.DataFrame(RECS, columns=['#','Action','Owner','Reasoning','Expected impact']).to_excel(xw, sheet_name='17. Recommendations', index=False)

    for _nm, _dfr in R3SHEETS.items():
        try:
            rt(_dfr).to_excel(xw, sheet_name=_nm[:31], index=False)
        except Exception as _e:
            print('sheet skipped:', _nm, _e)

print('Report + workbook written')
print('cohort', len(sep), '| mw', len(mw), '| conv gap', round(conv_gap,1), '| ev share', round(K['ev_conv_share']), '%')
print('2nd gap', round(sec_gap,1), '| ev share', round(K['ev_sec_share']), '%')
print('full-cohort gap', round(K['full_gap'],1), '| proj LTV', round(K['proj_ltv']), '| near term', round(K['near_term']))
