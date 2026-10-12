"""Generates the Supreme HQ Bandra Sept-2026 performance report (self-contained HTML)
   and an Excel workbook of the underlying tables."""
import pandas as pd, numpy as np, json, html
from prep import load

df = load()
SNAP = pd.Timestamp('2026-10-11'); BANDRA = 'Supreme HQ, Bandra'
SEP26 = pd.Timestamp('2026-09-01')
nn = df[~df['is_import']].copy()
b  = nn[nn['First Visit Location'] == BANDRA].copy()
b['obs'] = (SNAP - b['fvd']).dt.days
sep = b[(b['fvd'] >= '2026-09-01') & (b['fvd'] < '2026-10-01')].copy()
sep12 = b[(b['fvd'] >= '2026-09-12') & (b['fvd'] < '2026-09-14')].copy()

# ============================ helpers ============================
INK, MUTED, LINE = '#14110F', '#6B6259', '#E6E0D8'
ACC, GOOD, WARN, BAD = '#B4472B', '#2F7D5D', '#C98A2E', '#A62F2F'

def fmt(n, pre='Rs '):
    return f'{pre}{n:,.0f}'

def bar_chart(labels, series, title='', w=980, h=300, ymax=None, colors=None, legend=None, ylab='', as_pct=False):
    """series: list of (name, values, color)"""
    pad_l, pad_r, pad_t, pad_b = 56, 20, 30, 66
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    allv = [v for _, vals, _ in series for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or (max(allv) * 1.18 if allv else 1)
    ng = len(labels); ns = len(series)
    slot = iw / ng
    bw = slot * 0.68 / ns
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:100%;height:auto;font-family:ui-sans-serif,system-ui,-apple-system,sans-serif">']
    for i in range(5):
        y = pad_t + ih - ih * i / 4
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l+iw}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1"/>')
        val = mx * i / 4
        lbl = f'{val*100:.0f}%' if as_pct else (f'{val:,.0f}')
        out.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{lbl}</text>')
    for gi, lab in enumerate(labels):
        x0 = pad_l + gi * slot
        for si, (name, vals, col) in enumerate(series):
            v = vals[gi]
            if v is None or (isinstance(v, float) and np.isnan(v)): continue
            bh = ih * v / mx
            x = x0 + slot * 0.16 + si * bw
            y = pad_t + ih - bh
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
            if ng <= 16:
                vl = f'{v*100:.0f}%' if as_pct else f'{v:,.0f}'
                out.append(f'<text x="{x+bw/2:.1f}" y="{y-4:.1f}" text-anchor="middle" font-size="9.5" fill="{MUTED}">{vl}</text>')
        out.append(f'<text x="{x0+slot/2:.1f}" y="{pad_t+ih+16:.1f}" text-anchor="middle" font-size="10.5" fill="{MUTED}">{lab}</text>')
    if legend:
        lx = pad_l
        for name, col in legend:
            out.append(f'<rect x="{lx}" y="{h-22}" width="10" height="10" fill="{col}" rx="2"/>')
            out.append(f'<text x="{lx+15}" y="{h-13}" font-size="11" fill="{MUTED}">{name}</text>')
            lx += 12 + len(name) * 6.4
    out.append('</svg>')
    return f'<div class="chart"><div class="chart-t">{title}</div>{"".join(out)}</div>'

def line_chart(labels, series, title='', w=980, h=310, as_pct=False, ymax=None, ylab=''):
    pad_l, pad_r, pad_t, pad_b = 56, 24, 30, 70
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    allv = [v for _, vals, _ in series for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or (max(allv) * 1.2 if allv else 1)
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:100%;height:auto;font-family:ui-sans-serif,system-ui,sans-serif">']
    for i in range(5):
        y = pad_t + ih - ih * i / 4
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l+iw}" y2="{y:.1f}" stroke="{LINE}"/>')
        val = mx * i / 4
        vl = f'{val*100:.0f}%' if as_pct else f'{val:,.0f}'
        out.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{vl}</text>')
    step = iw / max(len(labels) - 1, 1)
    for name, vals, col in series:
        pts = [(pad_l + i * step, pad_t + ih - ih * v / mx) for i, v in enumerate(vals) if v is not None and not (isinstance(v, float) and np.isnan(v))]
        d = ' '.join(f'{"M" if i==0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linejoin="round"/>')
        for x, y in pts:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#fff" stroke="{col}" stroke-width="2"/>')
    for i, lab in enumerate(labels):
        if len(labels) > 14 and i % 2: continue
        out.append(f'<text x="{pad_l+i*step:.1f}" y="{pad_t+ih+17:.1f}" text-anchor="middle" font-size="10" fill="{MUTED}">{lab}</text>')
    lx = pad_l
    for name, col in [(s[0], s[2]) for s in series]:
        out.append(f'<rect x="{lx}" y="{h-24}" width="10" height="10" fill="{col}" rx="2"/>')
        out.append(f'<text x="{lx+15}" y="{h-15}" font-size="11" fill="{MUTED}">{name}</text>')
        lx += 12 + len(name) * 6.6
    out.append('</svg>')
    return f'<div class="chart"><div class="chart-t">{title}</div>{"".join(out)}</div>'

# ============================ build data ============================
# 1. monthly acquisition
mon = b.groupby(b['cohort'].dt.to_period('M')).agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
mon = mon.loc['2025-09':'2026-09']
mlabels = [str(p)[2:] for p in mon.index]

# 2. matched window (days 1-13)
mw = []
for per, g in b.groupby(b['cohort'].dt.to_period('M')):
    g = g[g['fvd'].dt.day <= 13]
    if len(g) < 10 or str(per) < '2025-09': continue
    mw.append((str(per)[2:], len(g), g['converted'].mean()*100, g['days_2nd'].notna().mean()*100, g['revenue'].mean(), g['No of Visits'].mean()))
mwd = pd.DataFrame(mw, columns=['cohort','n','conv','second','arpu','visits'])

# 3. channel table (Sep-26 vs hist)
CH = {'New - Trial Class':'Free Trial Class','New - Hosted Class':'Hosted Class','New - Referral Class':'Referral (free)','New - Paid First Visit':'Paid First Visit'}
hist = b[(b['fvd'] >= '2025-10-01') & (b['fvd'] < '2026-09-01')].copy()
for d in (sep, hist):
    d['channel'] = d['Is New'].map(CH).fillna('Other')
ch_s = sep.groupby('channel').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
ch_h = hist.groupby('channel').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))

# 4. trainers
def tr_tbl(d, minn=1):
    t = d[d['Trainer Name'].notna()].groupby('Trainer Name').agg(n=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'), second=('days_2nd', lambda s: s.notna().sum()))
    t['conv_pct'] = t['conv']/t['n']*100; t['second_pct'] = t['second']/t['n']*100; t['ltv'] = t['rev']/t['n']
    return t[t['n'] >= minn]
tr_sep = tr_tbl(sep); tr_hist = tr_tbl(hist, 8); tr_all = tr_tbl(b, 40)

# 5. base
bh = df[df['bandra_home'] & (~df['is_import'])].drop_duplicates('Member Id')
risk = bh[bh['Lifecycle Status'] == 'At Risk']

# 6. hosted programme
h = nn[nn['First Visit Entity Name'].str.contains('Hosted| X | x |Sweat|Pickle|Peakst8|KRC|Run Club|Unfiltered|SPRINT', case=False, na=False)].copy()
hm = h.groupby(h['cohort'].dt.to_period('M')).agg(clients=('Member Id','size'), conv=('converted','sum'), rev=('revenue','sum'))
hm = hm.loc['2025-09':'2026-10']

# 7. festival phases
ph = []
for yr in [2024, 2025, 2026]:
    x = b[(b['fvd'] >= f'{yr}-09-01') & (b['fvd'] < f'{yr}-10-01')].copy()
    if len(x) < 20: continue
    for lab, lo, hi in [('Sep 1-13', 1, 13), ('Sep 14-25', 14, 25), ('Sep 26-30', 26, 30)]:
        g = x[(x['fvd'].dt.day >= lo) & (x['fvd'].dt.day <= hi)]
        if not len(g): continue
        ph.append({'year': yr, 'phase': lab, 'n': len(g), 'conv': g['converted'].mean()*100, 'second': g['days_2nd'].notna().mean()*100})

# ============================ SVG charts ============================
c1 = bar_chart(mlabels, [('New clients', list(mon['n']), '#C9BFB2'), ('Converted', list(mon['conv']), ACC)],
               'New clients vs conversions — Supreme HQ Bandra', legend=[('New clients', '#C9BFB2'), ('Converted', ACC)])
c2 = line_chart(mwd['cohort'].tolist(), [('Conversion rate %', mwd['conv'].tolist(), ACC), ('2nd-visit rate %', mwd['second'].tolist(), '#3F6E8C')],
                'Matched window (first visits days 1-13, all fully matured) — conversion & 2nd-visit rate', as_pct=True, ymax=60)
c3 = bar_chart(['No 2nd visit','Had 2nd visit'], [('LTV/client', [b[~b['days_2nd'].notna()]['revenue'].mean(), b[b['days_2nd'].notna()]['revenue'].mean()], '#3F6E8C'),],
               'Why the 2nd visit decides everything — lifetime value per client')
c4 = bar_chart(list(ch_s.index), [('Sep-26 conv %', list(ch_s['conv']/ch_s['n']*100), ACC), ('Prior 11-mo conv %', [ch_h['conv'].get(i,0)/ch_h['n'].get(i,1)*100 for i in ch_s.index], '#C9BFB2')],
               'Conversion rate by entry channel — Sep-26 vs prior 11 months', as_pct=True, ymax=45,
               legend=[('Sep-26', ACC), ('Prior 11 months', '#C9BFB2')])
top = tr_all.sort_values('ltv', ascending=False)
c5 = bar_chart([n if len(n) < 13 else n[:12]+'.' for n in top.index], [('LTV/client', list(top['ltv']), '#3F6E8C')],
               'First-class trainer effect — LTV per client (all-time, n>=40)', w=980, h=320)
c6 = bar_chart([str(x)[2:] for x in hm.index], [('Clients', list(hm['clients']), '#C9BFB2'), ('Converted', list(hm['conv']), ACC)],
               'Hosted / partner-class programme — volume vs conversions', legend=[('Clients brought in','#C9BFB2'),('Converted',ACC)])
lab3 = [f'{p["year"]}<br/>{p["phase"]}' for p in ph]
c7 = bar_chart(lab3, [('Conv %', [p['conv'] for p in ph], ACC), ('2nd-visit %', [p['second'] for p in ph], '#3F6E8C')],
               'September phased by Ganeshotsav — Bandra (festival was 14-25 Sep 2026)', as_pct=True, ymax=65,
               legend=[('Conversion %', ACC), ('2nd-visit %', '#3F6E8C')])

# base funnel data
lf = bh['Lifecycle Status'].value_counts()

# ============================ recommendations ============================
RECS = [
 ("1","Stop treating Hosted / partner classes as an acquisition channel",
  "Band the programme.",
  "3,146 lifetime first visits produced 223 conversions (7.1%) and Rs 1,368 LTV/client — vs Rs 5,507 studio average. Sep-26: 112 clients across the network, 1 conversion, Rs 149/client. KRC x Avg Run Club (51 clients), Pickle Social (42), six Peakst8 editions (166 clients) produced a combined Rs 473.",
  "Free up ~112 first-visit slots/month; redeploy to trial + referral where conversion is 11-28%."),
 ("2","Install a mandatory 48-hour second-visit protocol",
  "Studio manager + front desk.",
  "A 2nd visit lifts conversion 57x (1.1% -> 61.9%) and is worth Rs 24,744 in lifetime value. Sep-26 ran at 12.9% vs a 37.8% trailing norm. Recovering to 30% = +15 converters = +Rs 2.6L per cohort, ~Rs 31L a year.",
  "Rs 26-38L annualised. Highest-ROI action in this report."),
 ("3","Cap and re-sequence weekend intake",
  "Studio manager.",
  "Weekend intake converts at 14.6% vs 23.6% on weekdays. In Sep-26 the studio put 75 of 143 clients (52%) into weekends at 6.7% conversion, and 30 of those arrived on the 12-13 Sep weekend at 0% conversion.",
  "Shifting 30 clients/quarter from weekend to Mon-Thu is worth ~Rs 4.5L in expected value."),
 ("4","Manage trainers on LTV, not hours",
  "Head of Training.",
  "Trainer spread is 7.0x (Rs 3,708 to Rs 25,982 LTV/client). Nishanth Raj (42 clients), Janhavi Jain (49) and Saniya Jaiswal (80) lead on both conversion (22-30%) and value. Lifting the bottom five to studio median adds Rs 33.6L of lifetime value on existing volume.",
  "Rs 33.6L lifetime; no added acquisition spend."),
 ("5","Fix September-style mass events",
  "Marketing + studio manager.",
  "The 12-13 Sep weekend delivered 21% of the month's clients, 0 conversions and Rs 709 revenue. All 13 'Priyanka's Barre Hosted Class' attendees never returned (avg visits 1.00).",
  "Prevents a repeat of the Rs 5.8L September value shortfall."),
 ("6","Retire or re-position Mat 57 and re-examine powerCycle",
  "Programming.",
  "Mat 57 has converted at 8.8% historically (Rs 2,776 LTV) and 0% in Sep (10 clients). powerCycle fell from 21.7% to 2.8% conversion in Sep-26 on 36 clients.",
  "Reallocating 46 weak-format slots to Barre 57 (13-24% conv) is worth ~Rs 2L/quarter."),
 ("7","Work the 170 At-Risk members now",
  "CRM / retention.",
  "170 Bandra-home members sit At Risk (31-60 days inactive) with Rs 3.2L of prior LTV behind them and a historical value of Rs 18,828 each. Another 635 are Lapsed.",
  "Recovering 20% of At Risk = ~Rs 6.4L of latent value."),
 ("8","Fix source attribution and late-cancellation",
  "Ops / data.",
  "28.7% of the Sep-26 cohort has no source recorded (41 of 143), which makes channel ROI unmeasurable. Separately, 58 active members run late-cancel rates above 20%, quietly destroying capacity.",
  "Enables every future channel decision; recovers bookable capacity."),
]

# ============================ HTML ============================
def pct(x): return f'{x:.1f}%'
def rs(x): return f'&#8377;{x:,.0f}'
def rupee(x): return f'\u20b9{x:,.0f}'

sc_rows = [
 ('New clients', f"{len(sep)}", f"{len(b[(b['fvd'] >= '2026-08-01') & (b['fvd'] < '2026-09-01')])}", "99", "117.8 / mo"),
 ('Conversions (raw)', f"{sep['converted'].sum()} ({pct(sep['converted'].mean()*100)})", "21 (13.7%)", "25 (25.3%)", "—"),
 ('2nd-visit rate', pct(sep['days_2nd'].notna().mean()*100), "22.2%", "36.4%", "35.3%"),
 ('Revenue booked', rs(sep['revenue'].sum()), rs(531037), rs(916475), "—"),
 ('Revenue per client', rs(sep['revenue'].mean()), rs(3471), rs(9257), rs(5430)),
 ('Visits per client', f"{sep['No of Visits'].mean():.2f}", "3.30", "6.09", "4.78"),
 ('Network share of new clients', "36.6%", "35.3%", "27.7%", "—"),
]
mw26 = mwd[mwd['cohort'] == '26-09'].iloc[0]
mwb  = mwd[(mwd['cohort'] >= '25-10') & (mwd['cohort'] <= '26-08')]
matched_rows = [
 ('Conversion rate', pct(mw26['conv']), pct(mwb['conv'].mean()), mw26['conv']-mwb['conv'].mean()),
 ('2nd-visit rate', pct(mw26['second']), pct(mwb['second'].mean()), mw26['second']-mwb['second'].mean()),
 ('Visits per client', f"{mw26['visits']:.2f}", f"{mwb['visits'].mean():.2f}", mw26['visits']-mwb['visits'].mean()),
 ('Revenue per client', rs(mw26['arpu']), rs(mwb['arpu'].mean()), mw26['arpu']-mwb['arpu'].mean()),
]

def tbl(headers, rows, cls=''):
    th = ''.join(f'<th>{h}</th>' for h in headers)
    tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'

ch_rows = []
for c in ch_s.index:
    n_s, cv_s = ch_s['n'][c], ch_s['conv'][c]
    n_h = ch_h['n'].get(c, 0); cv_h = ch_h['conv'].get(c, 0)
    ch_rows.append([c, n_s, pct(cv_s/n_s*100) if n_s else '—', pct(cv_h/n_h*100) if n_h else '—',
                    rs(ch_s['rev'][c]/n_s) if n_s else '—', rs(ch_h['rev'][c]/n_h) if n_h else '—'])

trr = []
tse = tr_sep.sort_values('n', ascending=False)
for t in tse.index:
    n_s = tr_sep['n'][t]
    h_n = tr_hist['n'].get(t, 0)
    trr.append([t, n_s, pct(tr_sep['conv_pct'][t]) if n_s else '—', pct(tr_hist['conv_pct'].get(t, np.nan)) if h_n else '—',
                pct(tr_sep['second_pct'][t]) if n_s else '—', rs(tr_sep['ltv'][t]) if n_s else '—'])

tra = []
for t in tr_all.sort_values('ltv', ascending=False).index:
    tra.append([t, int(tr_all['n'][t]), pct(tr_all['conv_pct'][t]), pct(tr_all['second_pct'][t]), rs(tr_all['ltv'][t]), rs(tr_all['rev'][t])])

rec_html = ''.join(f'''<div class="rec">
  <div class="rec-n">{r[0]}</div>
  <div class="rec-b">
    <h3>{r[1]}</h3>
    <div class="rec-owner">Owner: {r[2]}</div>
    <p class="rec-ev"><strong>Evidence.</strong> {r[3]}</p>
    <p class="rec-im"><strong>Impact.</strong> {r[4]}</p>
  </div></div>''' for r in RECS)

HTML = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Supreme HQ Bandra — September 2026 Performance Review</title>
<style>
 *{{box-sizing:border-box}}
 body{{margin:0;background:#FBF9F6;color:{INK};font:16px/1.62 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}}
 .wrap{{max-width:1060px;margin:0 auto;padding:0 24px 96px}}
 header{{background:{INK};color:#FBF9F6;padding:56px 24px 48px;margin-bottom:44px}}
 header .inner{{max-width:1060px;margin:0 auto}}
 .kicker{{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#B9AFA3;margin-bottom:14px}}
 h1{{font-size:40px;line-height:1.12;margin:0 0 14px;font-weight:650;letter-spacing:-.02em}}
 header p{{color:#B9AFA3;margin:0;max-width:70ch;font-size:16.5px}}
 h2{{font-size:14px;letter-spacing:.14em;text-transform:uppercase;color:{ACC};margin:56px 0 6px;font-weight:650}}
 h2 + .sub{{font-size:27px;font-weight:640;letter-spacing:-.015em;margin:0 0 20px;line-height:1.2}}
 h3{{font-size:18px;margin:0 0 6px;font-weight:640}}
 p{{margin:0 0 16px}}
 .cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 8px}}
 .card{{background:#fff;border:1px solid {LINE};border-radius:12px;padding:18px}}
 .card .l{{font-size:11.5px;text-transform:uppercase;letter-spacing:.09em;color:{MUTED};margin-bottom:8px}}
 .card .v{{font-size:26px;font-weight:660;letter-spacing:-.02em;line-height:1.1}}
 .card .d{{font-size:12.5px;color:{MUTED};margin-top:6px}}
 .up{{color:{GOOD}}} .down{{color:{BAD}}}
 table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid {LINE};border-radius:12px;overflow:hidden;font-size:14.5px;margin:0 0 10px}}
 th{{background:#F4F0EA;text-align:left;padding:11px 14px;font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;color:{MUTED};font-weight:640;border-bottom:1px solid {LINE}}}
 td{{padding:10px 14px;border-bottom:1px solid #F1ECE5;vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 tbody tr:hover{{background:#FDFBF8}}
 .chart{{background:#fff;border:1px solid {LINE};border-radius:12px;padding:20px 20px 8px;margin:0 0 22px}}
 .chart-t{{font-size:14.5px;font-weight:640;margin-bottom:10px}}
 .callout{{background:#fff;border:1px solid {LINE};border-left:4px solid {ACC};border-radius:10px;padding:20px 22px;margin:0 0 22px}}
 .callout h3{{margin-bottom:8px}}
 .center{{text-align:right}} .mono{{font-variant-numeric:tabular-nums}}
 .rec{{display:flex;gap:18px;background:#fff;border:1px solid {LINE};border-radius:12px;padding:20px 22px;margin-bottom:14px}}
 .rec-n{{flex:0 0 38px;height:38px;border-radius:50%;background:{INK};color:#fff;display:flex;align-items:center;justify-content:center;font-weight:660;font-size:15px}}
 .rec-b{{flex:1;min-width:0}}
 .rec-owner{{font-size:12.5px;color:{MUTED};margin-bottom:10px}}
 .rec-ev,.rec-im{{font-size:14.5px;margin:0 0 8px;color:#2C2621}}
 .rec-im{{margin-bottom:0;color:{GOOD};font-weight:560}}
 .find{{display:grid;grid-template-columns:34px 1fr;gap:16px;margin:0 0 26px}}
 .find .no{{font-size:30px;font-weight:660;color:#DDD3C6;line-height:1}}
 .find h3{{margin-top:2px}}
 ul{{margin:0 0 16px;padding-left:20px}} li{{margin-bottom:7px}}
 .note{{font-size:13.5px;color:{MUTED};font-style:italic;margin:-4px 0 14px}}
 .band{{background:#fff;border:1px solid {LINE};border-radius:12px;padding:20px 22px;margin-bottom:22px;display:flex;gap:26px;flex-wrap:wrap}}
 .band div{{flex:1;min-width:150px}}
 .band .v{{font-size:24px;font-weight:660;letter-spacing:-.02em}}
 .band .l{{font-size:11.5px;text-transform:uppercase;letter-spacing:.09em;color:{MUTED};margin-top:5px}}
 footer{{margin-top:60px;padding-top:24px;border-top:1px solid {LINE};font-size:13px;color:{MUTED}}}
 @media(max-width:820px){{.cards{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:30px}}}}
</style></head><body>
<header><div class="inner">
  <div class="kicker">Performance Review &middot; September 2026</div>
  <h1>Supreme HQ, Bandra</h1>
  <p>September 2026 delivered the highest new-client volume of any September in the dataset — and the lowest value per client. This report separates a genuine operational failure from a reporting artefact, isolates the two weekends that caused most of it, and prices the fix.</p>
</div></header>
<div class="wrap">

<div class="cards">
  <div class="card"><div class="l">New clients</div><div class="v">143</div><div class="d up">&#9650; +44% vs Sep-25 (99) &middot; record September</div></div>
  <div class="card"><div class="l">Revenue booked</div><div class="v">{rs(sep['revenue'].sum())}</div><div class="d down">&#9660; &minus;77% vs Sep-25 &middot; &minus;61% vs Aug-26</div></div>
  <div class="card"><div class="l">2nd-visit rate</div><div class="v">{pct(sep['days_2nd'].notna().mean()*100)}</div><div class="d down">&#9660; vs 35.3% prior 11-month norm</div></div>
  <div class="card"><div class="l">Value shortfall</div><div class="v">{rs(579140)}</div><div class="d down">Sept cohort vs baseline ARPU</div></div>
</div>
<p class="note">All figures are for the September 2026 first-visit cohort at Supreme HQ, Bandra, from a snapshot dated 11 Oct 2026.</p>

<h2>Executive summary</h2>
<div class="sub">Volume went up. Everything downstream of it went down.</div>
<p>Bandra acquired <strong>143 new clients in September 2026</strong> — the strongest September on record, 44% ahead of September 2025 and 22% above the trailing 11-month monthly average. It was also the studio's <strong>weakest month for monetisation in the dataset</strong>.</p>
<p>The temptation is to read the raw numbers as collapse: conversion at 8.4% against 25.3% a year ago, revenue down 77%. <strong>That reading is substantially wrong.</strong> Two-thirds of Bandra conversions historically land within 30 days of the first visit, so a September cohort measured 11 days into October is structurally incomplete. Once September is placed on an equal-observation basis, conversion is 12.5% against a 15.2% trailing norm — a real but modest gap.</p>
<p><strong>The real problem is the second visit, and it is severe.</strong> On a fully-matured matched window (first visits 1–13 September, all clients observed 28+ days), only <strong>12.9% of clients returned for a second class against a 37.8% norm — the bottom decile of 30 cohorts.</strong> Because a second visit raises conversion odds 57-fold and is worth <strong>{rs(24744)} in lifetime value</strong>, this single failure accounts for almost all of the month's value loss.</p>
<p>Chasing the cause leads to one weekend. <strong>12–13 September brought in 30 clients — 21% of the entire month — who have produced zero conversions and {rs(709)} of revenue.</strong> Thirteen of them were attendees of a single partner event, <em>Physique 57 x Priyanka's Barre Hosted Class</em>, none of whom ever returned. The mass free-event model is the mechanism, and it is not confined to one weekend: the hosted/partner programme has run <strong>3,146 first visits for 223 conversions (7.1%) and {rs(1368)} of value per client</strong> across its life.</p>
<p>Two myths are worth retiring with the data. <strong>This was not a Ganeshotsav effect</strong> — Ganesh Chaturthi fell on 14 September 2026, but the pre-festival window converted at 7.1%, as badly as the festival window itself. And <strong>the network did not fail with Bandra</strong>: Kwality House and Kenkere House posted 13.8% and 30.8% 30-day conversion on the same matched basis. Bandra's engagement collapse (1.79 visits per client against a 5.06 norm) is the standout.</p>

<h2>Scorecard</h2>
<div class="sub">September 2026, as reported</div>
{tbl(['Metric','Sep 2026','Aug 2026','Sep 2025','Trailing norm'], sc_rows, 'mono')}
<p class="note">Trailing norm = Bandra, Oct-2025 to Aug-2026. "New clients" trailing norm is the monthly average.</p>

<h2>Method</h2>
<div class="sub">Why the headline numbers understate September — and why they matter anyway</div>
<div class="callout">
<h3>The cohort-maturity trap</h3>
<p style="margin-bottom:10px">Bandra conversions take time. Across every converted cohort, the median conversion happens on <strong>day 8</strong>; 49% land within a week, 69% within 30 days, 81% within 90 days. A September cohort read in mid-October has had barely 30–40 days for even its earliest members.</p>
<p style="margin-bottom:0">So the raw 8.4% is not comparable to 25.3% in a fully-settled September 2025. Every rate in this report is therefore recomputed on an <strong>equal-observation window</strong>: either the first 30 days, or first visits restricted to 1–13 September so every client has 28+ days of history. That is the only basis on which September can be judged — and it is the basis on which the genuinely alarming findings below survive.</p>
</div>
{c2}
<p class="note">Read on the equal-window basis, September's 30-day conversion of 12.5% is below the 15.2% norm but the 31st percentile of 30 cohorts — unremarkable. The second-visit line is the break: 12.9% against a 37.8% norm, 10th percentile.</p>

<h2>Finding 01</h2>
<div class="sub">Volume hit a record while value per client collapsed</div>
<div class="find"><div class="no">01</div><div>
{bar_chart(mlabels, [('New clients', list(mon['n']), '#C9BFB2'), ('Converted', list(mon['conv']), ACC)], 'Bandra — new clients vs conversions by cohort month', legend=[('New clients','#C9BFB2'),('Converted',ACC)])}
<p>Bandra has been absorbing more of the network's acquisition every month. Its share of all new clients across the group rose from <strong>24.6% in October 2025 to 36.6% in September 2026</strong>. Group volume is up; Bandra is carrying it.</p>
<p>But volume and quality have decoupled sharply since May 2026. Visits per new client fell from an 11-month norm of 4.78 to <strong>1.59</strong> in September. Revenue per client fell from {rs(5430)} to <strong>{rs(sep['revenue'].mean())}</strong>. Notably, volume itself is <em>not</em> the cause: across 30 cohorts the correlation between monthly volume and conversion rate is just <strong>0.13</strong>.</p>
</div></div>

<h2>Finding 02</h2>
<div class="sub">The 12–13 September weekend: 21% of the month, 0% of the value</div>
<div class="find"><div class="no">02</div><div>
<div class="band">
 <div><div class="v">30</div><div class="l">clients 12&ndash;13 Sep</div></div>
 <div><div class="v">0</div><div class="l">conversions</div></div>
 <div><div class="v">1.10</div><div class="l">visits per client</div></div>
 <div><div class="v">{rs(709)}</div><div class="l">revenue</div></div>
 <div><div class="v">93%</div><div class="l">never returned</div></div>
</div>
<p>Those two days produced the single largest intake block of the month — and {rs(709)} of revenue between them. Half the block arrived through free or hosted routes: 14 free trials, 13 hosted-class attendees, 3 referral guests. Membership used was "none" for 13 and "Studio Open Barre Class" for 12 — i.e. almost entirely complimentary access.</p>
<p>The clearest artefact is <em>Physique 57 x Priyanka's Barre Hosted Class</em>: <strong>13 attendees, none of whom returned for a second class, contributing zero revenue.</strong> A second partner event, <em>Soumya's Barre Hosted Class</em>, ran on 23 September and produced an identical outcome: 9 clients, no second visits, no revenue. Across the month the two events brought 22 people into the studio and converted none of them.</p>
</div></div>

<h2>Finding 03</h2>
<div class="sub">The second visit is the whole business — and it broke</div>
<div class="find"><div class="no">03</div><div>
{c3}
<p>Across all 4,218 Bandra first visits, clients who returned for a second class converted at <strong>61.9%</strong> and are worth <strong>{rs(24982)}</strong> each. Clients who never returned converted at <strong>1.1%</strong> and are worth <strong>{rs(238)}</strong>. The second visit is worth <strong>{rs(24744)}</strong> of lifetime value and multiplies conversion odds by <strong>57x</strong>.</p>
<p>September ran that lever at 12.9% against a 37.8% norm — roughly <strong>17 missing second visits</strong> in the matured slice of the cohort alone. Recovering to a 30% rate is worth <strong>+{rs(262813)}</strong> on this one cohort; holding the trailing norm is worth <strong>+{rs(381925)}</strong>.</p>
</div></div>

<h2>Finding 04</h2>
<div class="sub">Entry channel is the strongest predictor of outcome</div>
<div class="find"><div class="no">04</div><div>
{c4}
{tbl(['Entry channel','Sep-26 clients','Sep-26 conv.','Prior 11-mo conv.','Sep-26 rev/client','Prior rev/client'], ch_rows, 'mono')}
<p>Free trials remain the workhorse — 79 of 143 clients — but converted at <strong>11.4% in September against 27.5% over the prior 11 months</strong>. Referrals, historically the second-best channel at 17.2%, fell to <strong>2.9%</strong>. Hosted classes converted at 3.8% against a 3.6% norm, i.e. they performed to their (poor) baseline.</p>
<p>The one channel that behaved well was <strong>paid first visits</strong>: 4 clients, 25% conversion, {rs(9824)} each. It is the smallest and most under-invested channel at the studio.</p>
</div></div>

<h2>Finding 05</h2>
<div class="sub">The hosted / partner programme does not pay for itself</div>
<div class="find"><div class="no">05</div><div>
{c6}
<div class="band">
 <div><div class="v">3,146</div><div class="l">lifetime first visits</div></div>
 <div><div class="v">7.1%</div><div class="l">conversion</div></div>
 <div><div class="v">{rs(1368)}</div><div class="l">LTV per client</div></div>
 <div><div class="v">{rs(5507)}</div><div class="l">studio average</div></div>
 <div><div class="v">{rs(149)}</div><div class="l">LTV/client, Sep-26</div></div>
</div>
<p>Assessed across its full life, the hosted/partner programme has produced <strong>223 conversions from 3,146 first visits — 7.1% — at {rs(1368)} of lifetime value per head, against a studio average of {rs(5507)}.</strong> Several flagship partner programmes have produced <em>literally nothing</em>: KRC x Avg Run Club brought 51 clients and zero revenue; Pickle Social brought 42 and zero; six Peakst8 editions brought 151 clients and {rs(473)} combined.</p>
<p>It is also getting worse, not better. The programme's yield fell from {rs(2273)} per client in November 2025 to <strong>{rs(149)} in September 2026</strong>. Two programmes are the exception worth studying: <em>Sweat Fest by Sisters in Sweat</em> (28 clients, {rs(5362)} each) and <em>Sweat Fest Lite</em> (50 clients, {rs(802)} each) — both cleared the bar that the others miss.</p>
</div></div>

<h2>Finding 06</h2>
<div class="sub">Not a festival effect — and not a network effect</div>
<div class="find"><div class="no">06</div><div>
{c7}
<p>Ganesh Chaturthi 2026 fell on <strong>Monday 14 September</strong>, with visarjan on <strong>Friday 25 September</strong> — and Bandra sits on the procession route. The festival hypothesis is intuitive and it is wrong.</p>
<p>Splitting September by festival phase, the <strong>pre-festival window (1–13 Sep) converted at 7.1% — exactly as badly as the festival window itself (6.2%).</strong> A festival suppresses a studio for ten days; it does not suppress the week before it. In September 2024 the same phase analysis shows the opposite pattern: pre-festival 46.7%, festival 24.5%. The degradation was already fully in place on day one of September 2026.</p>
<p>Nor is this simply the market. On the identical matched basis, <strong>Kwality House converted at 13.8% and Kenkere House at 30.8%</strong> while Bandra sat at 12.5%. Kenkere's conversion actually <em>improved</em> year-on-year. Bandra's distinct failure is engagement: <strong>1.79 visits per new client against a 5.06 norm</strong>.</p>
<p class="note">A caution for future reporting: September-to-September comparisons are invalid for 2025 vs 2026. Ganesh Chaturthi fell on 27 August in 2025, making September 2025 a clean post-festival month, while September 2026 absorbed the full festival.</p>
</div></div>

<h2>Finding 07</h2>
<div class="sub">First-class trainer drives a 7x spread in client value</div>
<div class="find"><div class="no">07</div><div>
{c5}
<p>Among trainers with 40+ first classes, lifetime value per client ranges from <strong>{rs(3708)} to {rs(25982)} — a 7.0x spread</strong>. Nishanth Raj (42 clients, {rs(25982)}), Janhavi Jain (49, {rs(24049)}) and Saniya Jaiswal (80, 30.0% conversion, {rs(13871)}) lead on both conversion and value.</p>
<p>Because these trainers already handle large books, the arithmetic is material: <strong>lifting the five weakest trainers to the studio median would add {rs(3358773)} in lifetime value on existing volume</strong>, with no additional acquisition spend.</p>
<p>September's anomaly is instructive and should <em>not</em> be read as an individual failing. Reshma Sharma took 33 clients — 23% of the month's entire intake, against her usual 7–8 — and produced 0 conversions and 1.00 visits per client. But her all-time record is 364 clients at 20.9% conversion and {rs(7310)} per client, and her September book was distorted by event assignment: 13 hosted-class attendees, 18 on Sundays, and 18 free trials.</p>
</div></div>

<h2>Finding 08</h2>
<div class="sub">Weekend intake is being over-used and under-converts</div>
<div class="find"><div class="no">08</div><div>
{tbl(['Day','Sep-26 clients','Sep-26 conv.','Prior 11-mo conv.'], [
 ['Monday','19','15.8%','24.8%'],['Tuesday','13','15.4%','25.5%'],['Wednesday','17','5.9%','18.4%'],
 ['Thursday','15','6.7%','28.0%'],['Friday','4','0.0%','19.5%'],['Saturday','36','11.1%','16.9%'],['Sunday','39','2.6%','11.7%']], 'mono')}
<p>Weekday intake converts at <strong>23.6%</strong> historically; weekend intake at <strong>14.6%</strong>. Sunday has always been the weakest day (11.7%). In September the studio <strong>loaded 75 of 143 clients — 52% — into weekends</strong>, including 39 onto Sundays, where they converted at 2.6%. Monday, Tuesday and Thursday, historically the three strongest days at 24.8–28.0%, received just 47 clients between them.</p>
<p>The single highest-value structural change available is to move intake weight from Sunday to Monday–Thursday. That reallocation needs no new spend, only scheduling.</p>
</div></div>

<h2>Finding 09</h2>
<div class="sub">The base is thin, concentrated, and leaking</div>
<div class="find"><div class="no">09</div><div>
<div class="band">
 <div><div class="v">4,181</div><div class="l">Bandra-home clients</div></div>
 <div><div class="v">385</div><div class="l">Active (9.2%)</div></div>
 <div><div class="v">170</div><div class="l">At Risk (4.1%)</div></div>
 <div><div class="v">635</div><div class="l">Lapsed</div></div>
 <div><div class="v">2,991</div><div class="l">Churned</div></div>
</div>
<p>Only <strong>9.2% of Bandra-home members are Active</strong>; adding At Risk brings it to 13.3%. The 170 At Risk members are 31–60 days inactive, carried <strong>{rs(3200706)} of prior lifetime value</strong>, and were historically worth <strong>{rs(18828)} each</strong>. They are the cheapest recoverable revenue in the dataset.</p>
<p>Value is also extremely concentrated: the <strong>top 5% of clients account for 70.7% of lifetime value and the top 1% for 28.1%</strong>, while 73.5% of members have never generated revenue. Meanwhile <strong>58 active members carry late-cancellation rates above 20%</strong>, quietly removing bookable capacity from a studio whose problem is already engagement.</p>
</div></div>

<h2>Recommendations</h2>
<div class="sub">Eight actions, ranked by expected value</div>
{rec_html}

<h2>Appendix</h2>
<div class="sub">Method, data, and what this analysis cannot see</div>
<p><strong>Source.</strong> Member-level CRM export ("Day End Report – Part 1 – New"), 21,171 rows covering 20,989 unique members, snapshot dated 11 October 2026. Each row is a member keyed to their first-visit cohort month with lifetime aggregates.</p>
<p><strong>Cohort definition.</strong> "September 2026 Bandra" = 143 members whose <em>first visit location</em> was Supreme HQ, Bandra, with a first-visit date in September 2026. Members whose <em>home location</em> is Bandra (4,458 rows) are used only for base-health analysis.</p>
<p><strong>Maturity adjustment.</strong> Two equal-observation bases are used throughout: (a) 30-day window — conversion counted only if it occurred within 30 days of first visit, over members with ≥30 days observed; (b) matched window — first visits restricted to days 1–13 of the month so every member has ≥28 days observed. Raw rates are shown only where labelled.</p>
<p><strong>Known data limitations.</strong> The 8,711 legacy "Import Visits" placeholder rows (first visit 2020-01-01) are excluded from all cohort analysis. 182 members appear twice where a legacy placeholder duplicates a tracked record. <strong>28.7% of the September cohort has no source recorded</strong>, which caps how precisely channel ROI can be measured. Revenue is lifetime value as recorded at snapshot; no separate transaction ledger, cost, or CAC data is present, so all figures are gross value rather than margin. 360 members appear in the source with a session count but no product linkage.</p>
<p><strong>Reproducibility.</strong> Every figure in this report is generated by the scripts in <code>/analysis</code> (prep.py and a1–a8). The September cohort extract is also supplied as CSV, and all underlying tables as an Excel workbook.</p>

<footer>Supreme HQ, Bandra &middot; September 2026 performance review &middot; prepared 11 October 2026<br/>
Figures derive from a member-level CRM snapshot; revenue is gross lifetime value, not margin.</footer>
</div></body></html>'''

with open('/home/user/Bandra_September_2026_Performance_Review.html', 'w') as f:
    f.write(HTML)

# ============================ Excel workbook ============================
with pd.ExcelWriter('/home/user/Bandra_September_2026_Data.xlsx', engine='openpyxl') as xw:
    pd.DataFrame([{'Metric': r[0], 'Sep 2026': r[1], 'Aug 2026': r[2], 'Sep 2025': r[3], 'Trailing norm': r[4]} for r in sc_rows]).replace('&#8377;', '\u20b9', regex=True).to_excel(xw, '1. Scorecard', index=False)
    mon.reset_index().rename(columns={'cohort':'Month','n':'New clients','conv':'Converted','rev':'Revenue'}).to_excel(xw, '2. Monthly trend', index=False)
    mwd.to_excel(xw, '3. Matched window', index=False)
    sep.to_excel(xw, '4. Sept cohort (raw)', index=False)
    sep12.to_excel(xw, '5. Sept 12-13 weekend', index=False)
    ch_h.reset_index().to_excel(xw, '6. Channels', index=False)
    tr_all.reset_index().to_excel(xw, '7. Trainer lifetime', index=False)
    tr_sep.reset_index().to_excel(xw, '8. Trainer Sept-26', index=False)
    hm.reset_index().rename(columns={'cohort':'Month'}).to_excel(xw, '9. Hosted programme', index=False)
    pd.DataFrame(ph).to_excel(xw, '10. Festival phases', index=False)
    bh.groupby('Lifecycle Status').agg(members=('Member Id','size'), lifetime_value=('revenue','sum'), avg_value=('revenue','mean')).reset_index().to_excel(xw, '11. Base health', index=False)
    risk[['Member Id','First Name','Last Name','Email','Phone Number','Last Visit Date','days_since','revenue','Purchase Count Post Trial','Visits Per Month','Late Cancel Rate Post Trial']].sort_values('revenue', ascending=False).to_excel(xw, '12. At-risk members', index=False)
    pd.DataFrame(RECS, columns=['#','Action','Owner','Evidence','Expected impact']).to_excel(xw, '13. Recommendations', index=False)

print('HTML + XLSX written')
print('Sep cohort:', len(sep), 'revenue', sep['revenue'].sum(), 'conv', sep['converted'].sum())
print('Sep 12-13:', len(sep12), sep12['revenue'].sum())
