"""Design system, chart primitives and table helpers shared by every generated chapter.

Design language: white ground, one deep-teal accent and one muted clay accent,
nothing else. Everything else is ink, grey and hairline.
"""
import pandas as pd, numpy as np

# ---------------------------------------------------------------- palette
INK  = '#12161A'      # near-black
MUT  = '#6B7280'      # secondary text
LINE = '#E7E5E2'      # hairline
SOFT = '#F7F7F6'      # faintest fill

A1 = '#0F4C5C'        # accent 1 — deep teal (primary)
A2 = '#3F7F8C'        # accent 1, mid
A3 = '#A6C4C9'        # accent 1, pale
B1 = '#BE7048'        # accent 2 — muted clay (secondary / negative)
B2 = '#E2C3AC'        # accent 2, pale
N1 = '#8C939A'        # neutral grey
N2 = '#D3D7DA'        # neutral, light

# compatibility aliases used by the build scripts
TER, SAGE, BLU, GOLD, GREY, PLUM, RED = A1, A2, A3, B1, N2, B1, B1

# ---------------------------------------------------------------- formatting
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

def R(x, plus=False):
    if x is None or (isinstance(x, float) and np.isnan(x)): return '\u2014'
    if x < 0: return f'\u2212\u20b9{_grp(x)}'
    return f'{("+" if plus else "")}\u20b9{_grp(x)}'
def Rs(x):
    if x is None or (isinstance(x, float) and np.isnan(x)): return '\u2014'
    return ('+' if x >= 0 else '\u2212') + '\u20b9' + _grp(x)
def P(x, d=1):
    if x is None or (isinstance(x, float) and np.isnan(x)): return '\u2014'
    return f'{x:.{d}f}%'
def N(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)): return '\u2014'
    return f'{x:,.{d}f}'
def UP(v, good=None):
    """arrow + coloured change string"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return '<span class="t-neu">flat</span>'
    ar = '\u25b2' if v > 0 else ('\u25bc' if v < 0 else '\u2014')
    cls = 't-neu'
    if v != 0:
        good = (v > 0) if good is None else good
        cls = 't-pos' if good else 't-neg'
    return f'<span class="{cls}">{ar} {abs(v):,.1f}%</span>'

# ---------------------------------------------------------------- atoms
def T(head, rows, cls=''):
    return (f'<table class="{cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) +
            '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) +
            '</tbody></table>')

def ev(summary, body):
    return f'<details class="ev"><summary><span class="evi"></span>{summary}</summary><div class="evb">{body}</div></details>'

def note(t):
    return f'<div class="cnote">{t}</div>' if t else ''

def _fig(title, svg, n):
    return f'<figure class="chart"><figcaption>{title}</figcaption>{svg}{note(n)}</figure>'

_FONT = 'font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif'

def _legend(series, h, pl):
    o, lx = [], pl
    for nm, _, col in series:
        o.append(f'<rect x="{lx}" y="{h-26}" width="8" height="8" fill="{col}" rx="2"/>')
        o.append(f'<text x="{lx+13}" y="{h-18}" font-size="10.5" fill="{MUT}">{nm}</text>')
        lx += 15 + len(nm) * 6.2
    return o

def _ticks(mx, pt, ih, pl, iw, as_pct, fmt=None):
    o = []
    for i in range(5):
        y = pt+ih-ih*i/4
        o.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{pl+iw}" y2="{y:.1f}" stroke="{LINE}"/>')
        val = mx*i/4
        if fmt:
            vl = fmt(val)
        elif as_pct:
            vl = f'{val:.0f}%' if mx > 1.5 else f'{val*100:.0f}%'
        else:
            vl = f'{val:,.0f}' if val >= 1 else f'{val:.1f}'
        o.append(f'<text x="{pl-9}" y="{y+4:.1f}" text-anchor="end" font-size="10" fill="{MUT}">{vl}</text>')
    return o

def bars(labels, series, title, w=1000, h=300, ymax=None, as_pct=False, note='', hline=None, rotate=False):
    pl, pr, pt, pb = 62, 20, 26, 74
    iw, ih = w-pl-pr, h-pt-pb
    allv = [v for _, vs, _ in series for v in vs if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or (max(allv)*1.22 if allv else 1)
    ng, ns = len(labels), len(series); slot = iw/ng; bw = min(slot*0.66/ns, 44)
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    o += _ticks(mx, pt, ih, pl, iw, as_pct)
    if hline is not None:
        y = pt+ih-ih*hline/mx
        o.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{pl+iw}" y2="{y:.1f}" stroke="{B1}" stroke-width="1.3" stroke-dasharray="5 4"/>')
        hl_txt = f'{hline:.0f}%' if hline > 1.5 else f'{hline*100:.0f}%'
        o.append(f'<text x="{pl+iw-2}" y="{y-6:.1f}" text-anchor="end" font-size="10" fill="{B1}">target {hl_txt}</text>')
    for gi, lab in enumerate(labels):
        x0 = pl+gi*slot
        for si, (nm, vs, col) in enumerate(series):
            v = vs[gi]
            if v is None or (isinstance(v, float) and np.isnan(v)): continue
            bh = max(ih*v/mx, 1.5); x = x0+slot*0.17+si*bw+(slot*0.66-ns*bw)/2; y = pt+ih-bh
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
            if ng <= 20:
                vl = (f'{v:.0f}%' if v > 1.5 else f'{v*100:.0f}%') if as_pct else f'{v:,.0f}'
                o.append(f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="9" fill="{MUT}">{vl}</text>')
        anch = 'end' if rotate else 'middle'
        tr = f' transform="rotate(-38 {x0+slot/2:.1f} {pt+ih+16:.1f})"' if rotate else ''
        o.append(f'<text x="{x0+slot/2:.1f}" y="{pt+ih+17:.1f}" text-anchor="{anch}" font-size="10" fill="{MUT}"{tr}>{lab}</text>')
    o += _legend(series, h, pl)
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def stacked(labels, series, title, w=1000, h=310, pct=False, note=''):
    """series = [(name, values, colour)] stacked bottom-up"""
    pl, pr, pt, pb = 62, 20, 26, 74
    iw, ih = w-pl-pr, h-pt-pb
    tot = [sum(s[1][i] for s in series) for i in range(len(labels))]
    mx = (max(tot) if pct else max(tot)) * 1.2
    ng = len(labels); slot = iw/ng; bw = min(slot*0.5, 62)
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    o += _ticks(mx, pt, ih, pl, iw, False)
    for gi, lab in enumerate(labels):
        x = pl+gi*slot+(slot-bw)/2; acc = 0
        for nm, vs, col in series:
            v = vs[gi] or 0
            bh = ih*v/mx; y = pt+ih-bh-acc; acc += bh
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="1.5"/>')
        o.append(f'<text x="{x+bw/2:.1f}" y="{pt+ih+17:.1f}" text-anchor="middle" font-size="10" fill="{MUT}">{lab}</text>')
    o += _legend(series, h, pl)
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def lines(labels, series, title, w=1000, h=320, as_pct=True, ymax=None, note='', label_last=False):
    pl, pr, pt, pb = 62, 26, 26, 74
    iw, ih = w-pl-pr, h-pt-pb
    allv = [v for _, vs, _ in series for v in vs if v is not None and not (isinstance(v, float) and np.isnan(v))]
    mx = ymax or max(allv)*1.22
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    o += _ticks(mx, pt, ih, pl, iw, as_pct)
    step = iw/max(len(labels)-1, 1)
    for nm, vs, col in series:
        pts = [(pl+i*step, pt+ih-ih*v/mx) for i, v in enumerate(vs) if v is not None and not (isinstance(v, float) and np.isnan(v))]
        d = ' '.join(('M' if i == 0 else 'L')+f'{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#fff" stroke="{col}" stroke-width="1.8"/>')
        if label_last and pts:
            x, y = pts[-1]; last = [v for v in vs if v is not None and not (isinstance(v, float) and np.isnan(v))][-1]
            last_txt = (f"{last:.1f}%" if last > 1.5 else f"{last*100:.1f}%") if as_pct else f"{last:,.0f}"
            o.append(f'<text x="{x+7:.1f}" y="{y+4:.1f}" font-size="11" font-weight="600" fill="{col}">'
                     f'{last_txt}</text>')
    for i, lab in enumerate(labels):
        o.append(f'<text x="{pl+i*step:.1f}" y="{pt+ih+17:.1f}" text-anchor="middle" font-size="10" fill="{MUT}">{lab}</text>')
    o += _legend(series, h, pl)
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def hbars(items, title, w=1000, unit='\u20b9', as_pct=False, maxv=None, note='', pl=210):
    row_h = 29; pr, pt, pb = 92, 24, 30
    h = pt+pb+row_h*len(items); iw = w-pl-pr
    mx = maxv or max([abs(v) for _, v, _ in items] or [1])
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    for i, (lab, v, col) in enumerate(items):
        y = pt+i*row_h
        bl = max(iw*abs(v)/mx, 1.5)
        o.append(f'<rect x="{pl}" y="{y+4:.1f}" width="{bl:.1f}" height="{row_h-13}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{pl-10}" y="{y+row_h/2+4:.1f}" text-anchor="end" font-size="11.5" fill="{INK}">{lab}</text>')
        if as_pct:
            vl = f'{v:.1f}%' if abs(v) > 1.5 else f'{v*100:.1f}%'
        else:
            vl = f'{unit}{v:,.0f}' if abs(v) >= 1 else f'{v:.2f}'
        o.append(f'<text x="{pl+bl+8:.1f}" y="{y+row_h/2+4:.1f}" font-size="11" fill="{MUT}">{vl}</text>')
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def diverging(items, title, w=1000, maxv=None, note=''):
    row_h = 28; pl, pr, pt, pb = 214, 100, 24, 30
    h = pt+pb+row_h*len(items)
    cw = w-pl-pr; mid = pl+cw*0.42
    mx = maxv or max([abs(v) for _, v in items] or [1])
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    o.append(f'<line x1="{mid:.1f}" y1="{pt-8}" x2="{mid:.1f}" y2="{pt+row_h*len(items)-4}" stroke="{LINE}"/>')
    for i, (lab, v) in enumerate(items):
        y = pt+i*row_h; bl = cw*0.55*abs(v)/mx
        if v >= 0:
            o.append(f'<rect x="{mid:.1f}" y="{y+4:.1f}" width="{bl:.1f}" height="{row_h-12}" fill="{A1}" rx="2"/>'); tx = mid+bl+8
        else:
            o.append(f'<rect x="{mid-bl:.1f}" y="{y+4:.1f}" width="{bl:.1f}" height="{row_h-12}" fill="{B1}" rx="2"/>'); tx = mid-bl-8
        o.append(f'<text x="{pl-10}" y="{y+row_h/2+4:.1f}" text-anchor="end" font-size="11.5" fill="{INK}">{lab}</text>')
        lbl = ('+' if v >= 0 else '\u2212')+f'\u20b9{_grp(v)}'
        o.append(f'<text x="{tx:.1f}" y="{y+row_h/2+4:.1f}" text-anchor="{"start" if v >= 0 else "end"}" font-size="11" fill="{MUT}">{lbl}</text>')
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def funnel(items, title, w=1000, note=''):
    """items = [(label, value, sublabel)] — descending bars"""
    row_h = 52; pl, pr, pt, pb = 200, 150, 20, 26
    h = pt+pb+row_h*len(items); iw = w-pl-pr
    mx = max([v for _, v, _ in items] or [1])
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    for i, (lab, v, sub) in enumerate(items):
        y = pt+i*row_h; bl = max(iw*v/mx, 2)
        col = A1 if i == 0 else (A2 if i < 3 else A3)
        o.append(f'<rect x="{pl}" y="{y+6:.1f}" width="{bl:.1f}" height="{row_h-22}" fill="{col}" rx="2"/>')
        o.append(f'<text x="{pl-12}" y="{y+row_h/2-1:.1f}" text-anchor="end" font-size="12" fill="{INK}">{lab}</text>')
        o.append(f'<text x="{pl-12}" y="{y+row_h/2+14:.1f}" text-anchor="end" font-size="10" fill="{MUT}">{sub}</text>')
        o.append(f'<text x="{pl+bl+10:.1f}" y="{y+row_h/2+4:.1f}" font-size="12" font-weight="600" fill="{INK}">{v:,.0f}</text>')
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

def dumbbell(items, title, w=1000, unit='%', note='', lo_lab='before', hi_lab='after'):
    """items = [(label, lo, hi)]"""
    row_h = 34; pl, pr, pt, pb = 210, 96, 34, 34
    h = pt+pb+row_h*len(items); iw = w-pl-pr
    mx = max([max(a, b) for _, a, b in items] or [1])*1.18
    o = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="height:auto;{_FONT}">']
    o.append(f'<rect x="{pl}" y="{pt-22}" width="8" height="8" fill="{B1}" rx="2"/>'
             f'<text x="{pl+13}" y="{pt-15}" font-size="10.5" fill="{MUT}">{lo_lab}</text>')
    o.append(f'<rect x="{pl+130}" y="{pt-22}" width="8" height="8" fill="{A1}" rx="2"/>'
             f'<text x="{pl+143}" y="{pt-15}" font-size="10.5" fill="{MUT}">{hi_lab}</text>')
    for i, (lab, a, b) in enumerate(items):
        y = pt+i*row_h; xa = pl+iw*a/mx; xb = pl+iw*b/mx
        o.append(f'<line x1="{xa:.1f}" y1="{y+10:.1f}" x2="{xb:.1f}" y2="{y+10:.1f}" stroke="{N2}" stroke-width="2"/>')
        o.append(f'<circle cx="{xa:.1f}" cy="{y+10:.1f}" r="5" fill="{B1}"/>')
        o.append(f'<circle cx="{xb:.1f}" cy="{y+10:.1f}" r="5" fill="{A1}"/>')
        o.append(f'<text x="{pl-10}" y="{y+14:.1f}" text-anchor="end" font-size="11.5" fill="{INK}">{lab}</text>')
        o.append(f'<text x="{max(xa,xb)+11:.1f}" y="{y+14:.1f}" font-size="11" fill="{MUT}">'
                 f'{a:.1f}{unit} \u2192 {b:.1f}{unit}</text>')
    o.append('</svg>')
    return _fig(title, ''.join(o), note)

# ---------------------------------------------------------------- stylesheet
CSS = f'''
 *{{box-sizing:border-box}}
 :root{{--ink:{INK};--mut:{MUT};--line:{LINE};--soft:{SOFT};
   --a1:{A1};--a2:{A2};--a3:{A3};--b1:{B1};--b2:{B2};--n1:{N1};--n2:{N2}}}
 html{{-webkit-text-size-adjust:100%}}
 body{{margin:0;background:#fff;color:var(--ink);
   font:16px/1.68 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
   -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}}
 .wrap{{max-width:1060px;margin:0 auto;padding:0 30px 120px}}
 header{{background:#fff;border-bottom:1px solid var(--line);padding:64px 0 46px;margin-bottom:56px}}
 header .inner{{max-width:1060px;margin:0 auto;padding:0 30px}}
 .kick{{font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--a1);font-weight:600;
   display:flex;align-items:center;gap:12px;margin-bottom:24px}}
 .kick:before{{content:"";width:26px;height:1.5px;background:var(--a1);display:block}}
 h1{{font-family:Georgia,"Iowan Old Style","Times New Roman",serif;font-size:48px;line-height:1.08;
   margin:0 0 22px;font-weight:400;letter-spacing:-.018em;max-width:24ch}}
 header .lede{{color:#3C4450;margin:0;max-width:76ch;font-size:17px;line-height:1.65}}
 header .meta{{margin-top:32px;padding-top:20px;border-top:1px solid var(--line);display:flex;
   gap:30px;flex-wrap:wrap;font-size:12.5px;color:var(--mut);letter-spacing:.01em}}
 .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin:0 0 40px;
   border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
 .kpi{{padding:24px 22px 24px 0}}
 .kpi+.kpi{{border-left:1px solid var(--line);padding-left:22px}}
 .kpi .l{{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--mut);margin-bottom:12px;font-weight:600}}
 .kpi .v{{font-family:Georgia,serif;font-size:31px;font-weight:400;line-height:1;letter-spacing:-.025em}}
 .kpi .d{{font-size:12.5px;color:var(--mut);margin-top:10px;line-height:1.5}}
 .t-pos{{color:var(--a1);font-weight:600}} .t-neu{{color:var(--mut);font-weight:600}} .t-neg{{color:var(--b1);font-weight:600}}
 .pos{{color:var(--a1);font-weight:600}} .neu{{color:var(--mut);font-weight:600}} .neg{{color:var(--b1);font-weight:600}}
 h2{{font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--a1);font-weight:700;
   margin:82px 0 10px;display:flex;align-items:center;gap:12px}}
 h2:before{{content:"";width:22px;height:1.5px;background:var(--a1);display:block;flex:0 0 22px}}
 .sub{{font-family:Georgia,serif;font-size:29px;font-weight:400;letter-spacing:-.02em;margin:0 0 24px;
   line-height:1.24;max-width:34ch}}
 h3{{font-size:18px;margin:0 0 8px;font-weight:650;letter-spacing:-.012em}}
 h4{{font-size:14.5px;margin:28px 0 10px;font-weight:650}}
 p{{margin:0 0 17px}}
 strong,b{{font-weight:650}}
 .chart{{background:#fff;border:1px solid var(--line);border-radius:4px;padding:24px 26px 12px;margin:0 0 22px}}
 .chart figcaption{{font-size:14.5px;font-weight:650;margin-bottom:16px;letter-spacing:-.008em;line-height:1.4}}
 .cnote{{font-size:12.5px;color:var(--mut);line-height:1.6;margin:8px 0 6px;padding-top:13px;border-top:1px solid var(--line)}}
 table{{width:100%;border-collapse:collapse;background:#fff;font-size:13.5px;margin:0 0 14px;
   border-top:1px solid var(--ink);border-bottom:1px solid var(--line)}}
 th{{text-align:left;padding:11px 12px;font-size:10px;text-transform:uppercase;letter-spacing:.1em;
   color:var(--mut);font-weight:700;border-bottom:1px solid var(--line);white-space:nowrap}}
 td{{padding:10px 12px;border-bottom:1px solid var(--soft);vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 table.small{{font-size:12.5px}} table.small td{{padding:7px 10px}} table.small th{{padding:8px 10px}}
 .num td,.num th{{font-variant-numeric:tabular-nums}}
 .call{{border:1px solid var(--line);border-left:2.5px solid var(--a1);border-radius:3px;background:#fff;
   padding:22px 26px;margin:0 0 24px}}
 .call.b{{border-left-color:var(--b1)}} .call.n{{border-left-color:var(--n1)}}
 .call p:last-child{{margin-bottom:0}} .call h4{{margin-top:0}}
 .stat{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0;background:#fff;
   border-top:1px solid var(--ink);border-bottom:1px solid var(--line);padding:22px 0;margin:0 0 24px}}
 .stat>div{{padding:0 20px;border-left:1px solid var(--line)}}
 .stat>div:first-child{{border-left:none;padding-left:0}}
 .stat .v{{font-family:Georgia,serif;font-size:27px;line-height:1;letter-spacing:-.025em}}
 .stat .l{{font-size:10.5px;text-transform:uppercase;letter-spacing:.11em;color:var(--mut);margin-top:10px;
   line-height:1.45;font-weight:600}}
 details.ev{{border:1px solid var(--line);border-radius:3px;background:#fff;margin:0 0 20px;overflow:hidden}}
 details.ev summary{{cursor:pointer;list-style:none;padding:15px 22px;font-size:13.5px;font-weight:600;
   color:var(--a1);display:flex;align-items:center;gap:11px;user-select:none;letter-spacing:.005em}}
 details.ev summary::-webkit-details-marker{{display:none}}
 details.ev .evi{{width:13px;height:13px;flex:0 0 13px;border-radius:2px;border:1.4px solid currentColor;position:relative;transition:.18s}}
 details.ev .evi:after{{content:"";position:absolute;left:3.4px;top:3px;width:4.6px;height:4.6px;border-right:1.4px solid currentColor;
   border-bottom:1.4px solid currentColor;transform:rotate(45deg);transition:.18s}}
 details.ev[open] .evi:after{{transform:rotate(225deg);top:4.4px}}
 details.ev summary:hover{{background:var(--SOFT)}}
 .evb{{padding:6px 22px 22px;border-top:1px solid var(--line);background:#fff}}
 .evb table{{margin-top:16px}}
 .hyp{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0;margin:0 0 26px;
   border-top:1px solid var(--ink);border-bottom:1px solid var(--line)}}
 .hcard{{padding:22px;border-left:1px solid var(--line)}}
 .hcard:first-child{{border-left:none;padding-left:0}}
 .hcard .tag{{display:inline-block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;padding:4px 9px;
   border-radius:2px;font-weight:700;margin-bottom:13px;border:1px solid}}
 .tag.no{{background:#FBF1EC;color:#9A5533;border-color:#F0DACE}}
 .tag.yes{{background:#EDF4F5;color:var(--a1);border-color:#CFE1E4}}
 .tag.part{{background:#F7F7F6;color:#59606A;border-color:#E3E3E1}}
 .hcard h3{{font-size:16px;margin-bottom:9px}}
 .hcard p{{font-size:14px;margin:0;color:#3A4049;line-height:1.62}}
 .hcard .verdict{{font-size:12.5px;color:var(--mut);margin-top:13px;padding-top:12px;border-top:1px solid var(--line)}}
 .rec{{display:flex;gap:22px;border-top:1px solid var(--line);padding:26px 0 4px;margin-bottom:0}}
 .rec:first-of-type{{border-top:1px solid var(--ink)}}
 .rn{{flex:0 0 34px;height:34px;border-radius:50%;background:var(--a1);color:#fff;display:flex;
   align-items:center;justify-content:center;font-family:Georgia,serif;font-size:14px}}
 .rb{{flex:1;min-width:0}} .ro{{font-size:12px;color:var(--mut);margin-bottom:16px;letter-spacing:.02em;
   text-transform:uppercase;font-weight:600}}
 .rec p{{font-size:14.5px;margin:0 0 13px;color:#2C323A;line-height:1.64}}
 .rec .imp{{margin-bottom:14px;color:#20505C}}
 .lbl{{display:block;font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--mut);
   font-weight:700;margin-bottom:4px}}
 ul{{margin:0 0 18px;padding-left:20px}} li{{margin-bottom:9px}}
 hr{{border:none;border-top:1px solid var(--line);margin:34px 0}}
 .toc{{border-top:1px solid var(--ink);border-bottom:1px solid var(--line);padding:22px 0 24px;margin:0 0 8px;
   display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:2px 34px}}
 .toc .tocl{{grid-column:1/-1;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--mut);
   font-weight:700;margin-bottom:12px}}
 .toc a{{display:flex;gap:11px;padding:5px 0;font-size:13.5px;color:#2C323A;text-decoration:none;
   border-bottom:1px solid transparent;line-height:1.35;transition:.15s}}
 .toc a:hover{{color:var(--a1)}}
 .toc a span{{font-variant-numeric:tabular-nums;color:var(--a3);font-size:11px;padding-top:2px;
   min-width:16px;font-weight:600}}
 .toc a:hover span{{color:var(--a1)}}
 footer{{margin-top:78px;padding-top:24px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mut);line-height:1.75}}
 @media(max-width:880px){{
   .kpis{{grid-template-columns:repeat(2,1fr)}}
   .kpi{{padding:20px 16px 20px 0}} .kpi+.kpi{{padding-left:16px}}
   h1{{font-size:33px}} .sub{{font-size:22px}} .hyp{{grid-template-columns:1fr}}
   .hcard{{border-left:none;padding-left:0;border-top:1px solid var(--line)}}
   .hcard:first-child{{border-top:none}}
   .stat{{grid-template-columns:repeat(2,1fr);gap:18px 0}}
   .stat>div:nth-child(odd){{border-left:none;padding-left:0}}
   header{{padding:44px 0 34px}} header .inner{{padding:0 22px}} .wrap{{padding:0 22px 80px}}
 }}
'''

def _toc(body):
    """Give every h2 an id and build a compact contents list."""
    import re as _re
    seen, items = {}, []

    def slug(t):
        s = _re.sub(r'&[a-zA-Z#0-9]+;', '', t)
        s = _re.sub(r'[^a-zA-Z0-9 ]', '', s).strip().lower().replace(' ', '-')
        n = seen.get(s, 0); seen[s] = n + 1
        return s if n == 0 else f'{s}-{n}'

    def repl(m):
        attr, txt = m.group(1), m.group(2)
        plain = _re.sub(r'<[^>]+>', '', txt).strip()
        if not plain:
            return m.group(0)
        i = slug(plain)
        items.append((i, plain))
        return f'<h2 id="{i}"{attr}>{txt}</h2>'

    body = _re.sub(r'<h2([^>]*)>(.*?)</h2>', repl, body, flags=_re.S)
    if not items:
        return body, ''
    li = ''.join(f'<a href="#{i}"><span>{k+1:02d}</span>{t}</a>' for k, (i, t) in enumerate(items))
    toc = f'<nav class="toc"><div class="tocl">Contents</div>{li}</nav>'
    return body, toc


def page(title, kick, h1, lede, meta, body, foot=None):
    foot = foot or ('Supreme HQ, Bandra &middot; September 2026 &middot; prepared 18 October 2026<br/>'
                    'Revenue figures are gross value as recorded at snapshot, not contribution margin.')
    body, toc = _toc(body)
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<style>{CSS}</style></head><body>
<header><div class="inner">
 <div class="kick">{kick}</div>
 <h1>{h1}</h1>
 <p class="lede">{lede}</p>
 <div class="meta">{meta}</div>
</div></header>
<div class="wrap">
{toc}
{body}
<footer>{foot}</footer>
</div></body></html>'''

def rec_html(recs):
    return ''.join(f'''<div class="rec">
 <div class="rn">{r[0]}</div>
 <div class="rb">
  <h3>{r[1]}</h3><div class="ro">{r[2]}</div>
  <p><span class="lbl">Reasoning</span>{r[3]}</p>
  <p class="imp"><span class="lbl">Expected impact</span>{r[4]}</p>
 </div></div>''' for r in recs)
