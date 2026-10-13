"""Turns a Dataset plus a studio and a month into nine chapters of HTML."""
from __future__ import annotations
import os, re, json, time
from pathlib import Path
import pandas as pd
from .design import page, rec_html, T, ev, R, P, A1, B1, now_ist
from .metrics import Metrics, MONTH_NAMES
from .reader import enhance_report
from .records import snapshot, embed
from . import chapters_a as CA, chapters_b as CB
from . import chapters_deep as CD1, chapters_deep2 as CD2, chapters_deep3 as CD3, chapters_deep4 as CD4
from . import narrate as NR
from .insights import executive
from .editorial import apply as apply_editorial

# the deep builders write the report at full length; the short ones are the
# fallback for a chapter whose sources are too thin for the deep version
DEEP = {
    'sales': CD1.sales, 'class': CD2.classperf, 'instructor': CD2.instructor,
    'lapse': CD3.lapse, 'format': CD3.formatcmp, 'cancels': CD4.cancels,
    'overview': CD4.overview, 'leads': CD4.leads, 'behaviour': CD4.behaviour,
}
SHALLOW = {
    'sales': CA.sales, 'class': CA.classperf, 'instructor': CA.instructor,
    'lapse': CA.lapse, 'format': CA.formatcmp, 'cancels': CB.cancels,
    'overview': CB.overview, 'leads': CB.leads, 'behaviour': CB.behaviour,
}
BUILDERS = dict(SHALLOW)


def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60]


def _sections(cid, body):
    """Give every <h2> inside a chapter a stable anchor id and return the list of
    sections so the sidebar can show the chapter's sub-topics as sub-headers."""
    if not body:
        return body, []
    pattern = re.compile(r'<h2>(.*?)</h2>', re.S)
    sections = []

    def _rep(m):
        idx = len(sections) + 1
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        anchor = f'sec-{cid}-{idx}'
        sections.append({'n': idx, 'id': anchor, 'title': title, 'slug': _slug(title)})
        return f'<h2 id="{anchor}">{m.group(1)}</h2>'

    new_body = pattern.sub(_rep, body)
    return new_body, sections


def build(D, studio, year, month, outdir, log=print, use_llm=None,
          chapters=None, period_label=None, editorial=None):
    """Returns {'chapters': [...], 'dir': outdir, 'html': combined_path}."""
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    M = Metrics(D, studio, year, month, log=log)
    label = period_label or M.label
    frozen_records = snapshot(M)
    # The complete, uncapped population for every source. The report pages embed
    # only a capped preview (they must stay loadable); the drill-down explorer
    # fetches this file on demand so no row past the preview cap is ever hidden.
    try:
        full_records = snapshot(M, limit=None)
        Path(outdir, 'records.json').write_text(json.dumps(full_records, ensure_ascii=False, allow_nan=False))
    except Exception as e:
        log(f'  full records skipped: {e}')
    out = []
    for cid, fn in BUILDERS.items():
        if chapters and cid not in chapters:
            continue
        ch = None
        try:
            ch = DEEP[cid](M)
            if ch is not None:
                ch['depth'] = len(ch.get('body', ''))
        except Exception as e:
            log(f'  chapter {cid}: the full form was not possible ({type(e).__name__}: {e}); '
                f'fell back to the short form')
            ch = None
        if ch is None:
            try:
                ch = fn(M)
            except Exception as e:
                log(f'  chapter {cid} failed: {e}')
                ch = dict(id=cid, n=0, title=cid.title(), subtitle='could not be built',
                          body='<p>This chapter needs a source that was not in this upload, so it has been left out '
                               'rather than estimated.</p>', kpis=[], facts=[], recs_extra=[])
        if ch is None:
            log(f'  chapter {cid} skipped (missing source)')
            continue
        if cid in ('leads', 'lapse'):
            scope = ('Enquiries created' if cid == 'leads' else 'Memberships purchased') + f' in {M.label}. Status, trial, retention and lifetime fields reflect the uploaded export; historical month-end outcomes cannot be reconstructed from a current-state export.'
            ch['body'] = '<p class="p57-period-scope">' + scope + '</p>' + ch.get('body', '')
        interpretation = executive(M, ch)
        ch['body'] = ch.get('body', '') + interpretation
        ch['narrative_version'] = 2
        ch['summary'] = NR.summary(M, ch)
        ch['narration'] = NR.narration(M, ch)
        ch['recs'] = NR.recommendations(M, cid, ch.get('recs_extra'))
        apply_editorial(M, ch)
        ch['body'], ch['sections'] = _sections(cid, ch.get('body', ''))
        if editorial:
            editorial(M, ch)
        ch['slug'] = _slug(ch['title'])
        ch['html'] = enhance_report(_chapter_page(M, ch, label).replace('</head>',embed(frozen_records)+'</head>',1))
        ch['kpis'] = [k for k in ch.get('kpis', []) if k.get('value') not in (None, '', 'nan')]
        out.append(ch)

    # optional rewrite of the summaries through a language model
    if use_llm:
        key, model = use_llm
        for ch in out:
            try:
                ch['summary_ai'] = NR.llm(ch['summary'], key, model)
            except Exception as e:
                ch['summary_ai'] = ''
                log(f'  llm summary failed: {e}')

    from .monthly import capture, inject
    monthly = capture(D, studio, year, month, out, DEEP, SHALLOW, log)
    Path(outdir, 'monthly.json').write_text(json.dumps(monthly, ensure_ascii=False))
    for ch in out:
        ch['html'] = inject(ch['html'], data=monthly, chapter=ch['id'])
    combined = inject(_combined(M, out, label), data=monthly).replace('</head>',embed(frozen_records)+'</head>',1)
    cpath = os.path.join(outdir, 'report.html')
    Path(cpath).write_text(enhance_report(combined))
    for ch in out:
        Path(outdir, ch['id'] + '.html').write_text(ch['html'])
    # Compact metric snapshot powering the in-report AI assistant: every
    # headline figure plus definitions, grounded in the Metrics object.
    try:
        from ai import metrics_pack
        metrics_pack.dump(metrics_pack.from_metrics(M, out), os.path.join(outdir, 'metrics.json'))
    except Exception as e:
        log(f'  metrics pack skipped: {e}')
    meta = dict(scope_version=2, studio=studio, year=year, month=month, label=label, built=now_ist().strftime('%d %B %Y, %H:%M IST'),
                seconds=round(time.time() - t0, 1), chapters=[{k: v for k, v in ch.items() if k not in ('html', 'body')} for ch in out],
                sources=[s.name for s in D.sources], warnings=D.warnings)
    Path(outdir, 'manifest.json').write_text(json.dumps(meta, indent=1, default=str))
    log(f'  {len(out)} chapters built in {meta["seconds"]}s')
    return dict(chapters=out, dir=outdir, manifest=meta, metrics=M)


# --------------------------------------------------------------------- pages
def _chapter_page(M, ch, label):
    kpi_html = ''
    if ch.get('kpis'):
        kpi_html = '<div class="kpis">' + ''.join(
            f'''<div class="kpi"><div class="l">{k['label']}</div><div class="v">{k['value']}</div>
            <div class="d {k.get('tone','neu')}">{k.get('detail','')}</div></div>''' for k in ch['kpis']) + '</div>'
    sum_html = (f'''<div class="call"><h4>Performance verdict</h4><p>{ch['summary']}</p></div>''' if ch.get('summary') else '')
    rec_html_block = ''
    if ch.get('recs'):
        recs = [(r[0], r[1], r[2], r[3], r[4]) for r in ch['recs']]
        rec_html_block = (f'''<h2>Recommended response</h2>
<div class="sub">{len(recs)} proposed actions with owners and success measures</div>'''
                          + rec_html(recs))
    body = kpi_html + sum_html + ch['body'] + rec_html_block
    meta = (f"{M.studio} &middot; {label} &middot; chapter {ch.get('n', 0)} of 9<br/>"
            f"Snapshot {now_ist():%d %B %Y} &middot; generated from {len(M.D.sources)} uploaded exports")
    return page(f'{M.studio} \u2014 {ch["title"]}', f'Chapter {ch.get("n", 0):02d} &nbsp; {label}',
                ch['title'], ch.get('subtitle') or '', meta, body)


def _combined(M, chapters, label):
    chapters = sorted(chapters, key=lambda c: c['id'] != 'overview')
    toc = '<div class="toc"><ol>' + ''.join(
        f'<li><a href="#{c["slug"]}">{c["title"]}</a> <span class="tp">{c.get("subtitle","")}</span></li>'
        for c in chapters) + '</ol></div>'
    parts = []
    for c in chapters:
        kpi = ('<div class="kpis">' + ''.join(
            f'''<div class="kpi"><div class="l">{k['label']}</div><div class="v">{k['value']}</div>
            <div class="d {k.get('tone','neu')}">{k.get('detail','')}</div></div>''' for k in c['kpis']) + '</div>') if c.get('kpis') else ''
        recs = rec_html([(r[0], r[1], r[2], r[3], r[4]) for r in c['recs']]) if c.get('recs') else ''
        parts.append(f'''<section id="{c['slug']}">
<h2>Chapter {c.get('n', 0):02d} &nbsp; {c['title']}</h2>
<div class="sub">{c.get('subtitle','')}</div>
{kpi}
<div class="call"><h4>Performance verdict</h4><p>{c.get('summary','')}</p></div>
{c['body']}
<h2>Recommended response</h2><div class="sub">{len(c.get('recs', []))} actions for this chapter</div>{recs}
</section>''')
    meta = (f"{M.studio} &middot; {label}<br/>{len(chapters)} chapters &middot; generated {now_ist():%d %B %Y}<br/>"
            f"Snapshot {now_ist():%d %B %Y}")
    lede = (f'Every chapter of the {label} review for {M.studio}, generated from the exports on file. '
            f'Each chapter opens with a summary, presents the evidence, and closes with the actions the numbers support.')
    S = M.sales.get(M.y, {}); F = M.room.get(M.y, {}); C = getattr(M,'core',{})
    executive = ''
    if S and F:
        executive = '<div class="p57-executive-summary" aria-label="Executive summary"><h2 id="executive-summary">Executive Summary</h2><ul>'
        executive += f'<li><strong>{R(S["cash"])}</strong> in sales revenue from {S["txn"]} distinct sales and {S["buyers"]} buyers.</li>'
        executive += f'<li><strong>{F["fill"]:.1f}% utilisation</strong>: {F["att"]:,.0f} attendances across {F["sessions"]} sessions. Delivered session revenue was {R(F["rev"])}.</li>'
        if C: executive += f'<li>The same <strong>{C["n"]} returning members</strong> made {abs(C["lost"]):,.0f} {"fewer" if C["lost"]>=0 else "more"} visits than {MONTH_NAMES[M.m-1]} {M.y-1} ({abs(C["drop_pct"]):.1f}%).</li>'
        executive += '</ul></div>'
    return page(f'{M.studio} \u2014 {label} Performance Review', f'{M.studio} &nbsp; {label}',
                'Performance Review', lede, meta, executive + toc + ''.join(parts))
