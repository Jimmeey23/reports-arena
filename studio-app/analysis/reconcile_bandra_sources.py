"""Reconcile saved September Bandra chapters with the supplied reference files.

Run from the repository: .venv/bin/python studio-app/analysis/reconcile_bandra_sources.py
Only the two existing Bandra September runs are changed; source files are immutable.
HTML references govern chapter content; workbook rows govern conflicting breakdowns;
the explicitly reconciled sales reference governs distinct-sale counting.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
import sys
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
import openpyxl

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP))
from engine.reader import enhance_report
from ai.metrics_pack import from_manifest, dump
from engine.chapter_order import CHAPTER_ORDER, chapter_number, ordered

FILES = {
    'sales': '1_Sales_Performance', 'class': '2_Class_Performance',
    'instructor': '3_Instructor_Performance', 'lapse': '4_Lapsed_Churned',
    'format': '5_Format_Comparisons', 'cancels': '6_Cancellations_Discounts',
    'overview': '7_Studio_Overview', 'leads': '8_Lead_Performance',
    'behaviour': '9_Member_Behaviour', 'review': 'Performance_Review',
}
FILES = {cid: FILES[cid] for cid in CHAPTER_ORDER}
TARGETS = ('20261011-232828-eb72', '20261011-173500-demo')
# These supplementary populations are absent from the nine narrative references.
# Other workbook sheets support their existing tables and are not appended again.
SUPPLEMENTS = {
    'overview': ['1. Twelve-month view', '2. Year to date'],
    'class': ['3b. Canonical basis', '3c. Gap decomposition', '5. Driver table',
              '6. Correlations', '7. Festival phases'],
    'lapse': ['15. Base health'],
    'leads': ['19. Lead drop-off reasons'],
    'sales': ['24. Cash reconciliation'],
}
NOTICE = (
    'Reconciled against the nine supplied Bandra chapter files, the Performance Review, and three workbooks on '
    '13 October 2026. September metrics and historical/export-wide populations are '
    'labelled separately. The sales reference specifies 195 distinct sales, 210 units '
    'and 213 payment rows; these counts are not interchangeable. Workbook breakdowns '
    'take precedence over conflicting prose. Source files retain their printed precision. '
    'Some reference files label their snapshot 18 October 2026, after this reconciliation '
    'date; those snapshot-dependent outcomes are reproduced as supplied, not independently '
    'verified as of today. Historical associations and illustrative revenue scenarios '
    'are not causal findings or forecasts. Product expiry is not customer churn. '
    'Collections and class-attributed revenue are different ledgers, not a measure '
    'of consumed purchases or deferred liabilities.'
)


def soup(text):
    return BeautifulSoup(text, 'html.parser')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def money(value):
    n = str(round(value))
    if len(n) <= 3:
        return '₹' + n
    lead = n[:-3]
    groups = []
    while lead:
        groups.insert(0, lead[-2:])
        lead = lead[:-2]
    return '₹' + ','.join(groups) + ',' + n[-3:]


def table(rows):
    def cell(v):
        if v is None:
            return 'n/a'
        return str(v)
    return ('<div class="source-table"><table class="num"><thead><tr>' +
            ''.join('<th>' + escape(cell(v)) + '</th>' for v in rows[0]) +
            '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(
                '<td>' + escape(cell(v)) + '</td>' for v in row) + '</tr>'
                for row in rows[1:]) + '</tbody></table></div>')


def workbook_note(name):
    if name in ('3b. Canonical basis', '3c. Gap decomposition'):
        return ('Source-defined matured slice: September 1–13, 70 clients; not the full '
                '143-client September cohort. The source labels this a 30-day window. '
                'On 13 October the entire slice has not completed 30 days; retain these '
                'as supplied reference-window results, not independently verified current '
                'outcomes. Expected counts and currency shortfalls are modelled scenarios, '
                'not realised revenue. Indented subgroups overlap their parent.')
    if name in ('5. Driver table', '6. Correlations', '7. Festival phases'):
        return ('Historical source-defined newcomer cohorts. Observation windows vary; '
                'recent cohorts are immature. Correlations and festival phase differences '
                'do not establish causation. Percent fields retain source units; arpu is '
                'source-recorded revenue per client, not a mature lifetime value.')
    if name == '1. Twelve-month view':
        return ('Rolling October–September acquisition windows, not calendar year totals. '
                '30-day progression and 90-day revenue are different observation windows.')
    if name == '2. Year to date':
        return ('Calendar January–September acquisition cohorts. The 2026 matured cohort '
                'contains 687 of 1,077 newcomers; do not compare its 90-day outcome with '
                'the full September export-snapshot conversion rate.')
    if name == '15. Base health':
        return ('Historical member-level engagement segments, not membership-instance '
                'expiry counts. Prior lifetime value is historical spend, not recoverable '
                'cash. The workbook’s 170 at-risk members differ from the expiry ledger’s '
                '137 recently inactive members because their populations differ.')
    if name == '19. Lead drop-off reasons':
        return ('Historical recorded reasons; not September-only losses. Reason counts '
                'describe the reason register and must not be added to lead-status counts.')
    return ('First-visit acquisition basis: ₹1,91,530 / ₹15,29,410.18 = 12.5%. '
            'The 19.6% figure elsewhere uses first purchase at Bandra, a different cohort. '
            'Cohort lifetime cash is not September collections; do not sum these rows.')


def correct_source(fragment, cid):
    """Narrow corrections where the supplied detailed workbook resolves source conflicts."""
    if cid == 'leads':
        for node in fragment.find_all(string=True):
            value = str(node).replace('1006 of them', '911 of them')
            value = value.replace('1,006 of them', '911 of them')
            if value != str(node):
                node.replace_with(value)
        for t in fragment.find_all('table'):
            if 'Trial completed' in t.get_text() and 'Ever won' in t.get_text():
                for row in t.select('tbody tr'):
                    cells = row.find_all('td')
                    if cells and cells[0].get_text(strip=True) == 'Yes':
                        cells[3].string = '911'
    if cid == 'sales':
        for p in fragment.select('p'):
            text = p.get_text(' ', strip=True)
            if 'Lifting the 98 members who came exactly once' in text:
                p.clear()
                p.append('Illustrative scenario: the frequency workbook records 205 members '
                         'with one September visit (52.0% of 394 attendees). One additional '
                         'visit each would add 205 attendances; at the observed average '
                         'attributed yield this is about ₹1,90,757 of activity value, not '
                         'booked revenue, profit or guaranteed incremental collections.')
            if '103 single-purchase members' in text:
                p.clear()
                p.append('The source records 41 repeat buyers among 139 buyers, leaving '
                         '98 single-purchase buyers, not 103. A further purchase from each '
                         'at the source median ₹1,942 would illustrate ₹1,90,316 of '
                         'collections, not a forecast or a validated offer price.')
            if 'Depth averages 12.8%' in text:
                for node in p.find_all(string=True):
                    node.replace_with(str(node).replace('Depth averages 12.8%',
                        'The aggregate weighted rate is 8.7% of pre-discount list value'))
        # Correct, rather than repeat, source text that treats ledger ratios as credit usage.
        for node in fragment.find_all(string=True):
            value = str(node).replace('how much of it was consumed as classes',
                                      'class-attributed revenue (separate ledger)')
            value = value.replace('consumed 85% of it as delivered classes',
                                  'recorded class-attributed revenue equal to 85% of collections')
            if value != str(node):
                node.replace_with(value)
    # Recommendations remain source scenarios, but do not imply guaranteed uplift.
    for x in fragment.select('.imp .lbl'):
        if x.get_text(strip=True) == 'Expected impact':
            x.string = 'Illustrative impact'
    return fragment


def source_chapters():
    workbook = openpyxl.load_workbook(ROOT / 'Bandra_September_2026_Data.xlsx', data_only=True)
    chapters = {}
    for cid, basename in FILES.items():
        path = ROOT / ('Bandra_September_2026_' + basename + '.html')
        source = soup(path.read_text())
        fragment = soup('<div></div>').div
        for node in source.select_one('.wrap').children:
            if getattr(node, 'name', None) and node.name not in ('nav', 'footer', 'script', 'style'):
                fragment.append(copy.copy(node))
        correct_source(fragment, cid)
        for name in SUPPLEMENTS.get(cid, []):
            block = soup('<section class="source-supplement"><h2>' + escape(name) +
                         '</h2><p class="source-citation">Bandra_September_2026_Data.xlsx · ' +
                         escape(name) + '</p><p>' + escape(workbook_note(name)) + '</p>' +
                         table(list(workbook[name].values)) + '</section>').section
            recommendations = next((h for h in fragment.select('h2')
                                    if h.get_text(strip=True) == 'Recommendations'), None)
            if recommendations:
                recommendations.insert_before(block)
            else:
                fragment.append(block)
        # Keep header-specific historical scope available inside the combined chapter.
        scope = source.select_one('header .meta')
        fragment.insert(0, soup('<p class="source-citation">Reference: ' + escape(path.name) +
                               '. Printed scope: ' + escape(scope.get_text(' ', strip=True) if scope else '') + '</p>').p)
        # Namespaced IDs avoid cross-chapter collisions while preserving chart links.
        old_ids = {}
        for node in fragment.select('[id]'):
            old = node['id']
            old_ids[old] = cid + '-source-' + old
            node['id'] = old_ids[old]
        for a in fragment.select('a[href^="#"]'):
            if a['href'][1:] in old_ids:
                a['href'] = '#' + old_ids[a['href'][1:]]
        sections = []
        for i, heading in enumerate(fragment.select('h2'), 1):
            heading['id'] = f'sec-{cid}-{i}'
            sections.append(dict(n=i, id=heading['id'], title=heading.get_text(' ', strip=True)))
        chapters[cid] = dict(fragment=fragment, sections=sections,
                             source=path.name, sha256=digest(path))
    return chapters


def deduplicate(chapters):
    """Store every identical evidence table once, replacing repeats with links.

    Cross-chapter KPI summaries remain, but detailed duplicate rows do not.
    Standalone chapters link to the owner in the combined report.
    """
    seen = {}
    references = []
    for cid in FILES:
        fragment = chapters[cid]['fragment']
        for t in list(fragment.select('table, figure.chart')):
            if t.name == 'table':
                signature = ('table', tuple(tuple(c.get_text(' ', strip=True) for c in row.find_all(['th', 'td']))
                                           for row in t.find_all('tr')))
            else:
                # Captions may differ even when the plotted data is identical.
                signature = ('chart', str(t.find('svg')))
            if signature not in seen:
                anchor = f'{cid}-evidence-{len(seen) + 1}'
                t['id'] = anchor
                seen[signature] = (cid, anchor)
                continue
            owner, anchor = seen[signature]
            link = soup(f'<p class="source-cross-reference">This evidence is presented once: '
                        f'<a href="report.html#{anchor}">{escape(owner.title())} chapter — '
                        'source evidence</a>.</p>').p
            parent = t.find_parent('details')
            # Do not remove sibling tables inside the same evidence disclosure.
            if t.name == 'table' and parent and len(parent.find_all('table')) == 1:
                parent.replace_with(link)
            else:
                t.replace_with(link)
            references.append(dict(chapter=cid, owner=owner, anchor=anchor, kind=signature[0]))
    return references


def navigation(sections):
    return soup('<nav class="toc"><div class="tocl">Contents</div>' + ''.join(
        f'<a href="#{x["id"]}"><span>{i:02}</span>{escape(x["title"])}</a>'
        for i, x in enumerate(sections, 1)) + '</nav>').nav


def shell(path):
    doc = soup(path.read_text())
    # Legacy monthly registers and frozen CSV previews use a conflicting population.
    # Do not expose them as evidence for the imported reference tables.
    frozen = doc.select_one('#p57-source-records')
    archive = path.parent / 'records-before-source-reconciliation.json'
    if frozen and not archive.exists():
        archive.write_text(frozen.get_text())
    for node in doc.find_all('script'):
        if node.get('id') not in ('p57-saved-workspace', 'p57-structural-edits'):
            node.decompose()
    for node in doc.select('#p57-reader-assets, #p57-monthly-style'):
        node.decompose()
    doc.select_one('.wrap').clear()
    if not doc.select_one('#bandra-source-style'):
        style = doc.new_tag('style', id='bandra-source-style')
        style.string = ('.source-table{overflow-x:auto;margin:20px 0}.source-table table{min-width:720px}'
                        '.source-citation{font-size:12px;color:#7a7267}'
                        '.source-reconciliation{padding:20px;border-left:4px solid #a88647;background:#faf5e9;font-size:13px}'
                        '.source-cross-reference{padding:12px;background:#f3efe8}'
                        '.source-supplement{margin:28px 0}.source-table th{white-space:normal}')
        doc.head.append(style)
    return doc


def kpis(fragment):
    out = []
    for k in fragment.select('.kpi'):
        def text(selector):
            x = k.select_one(selector)
            return x.get_text(' ', strip=True) if x else ''
        out.append(dict(label=text('.l'), value=text('.v'), detail=text('.d'), tone='neu'))
    return out


def update_run(directory, chapters, receipt):
    mf = directory / 'manifest.json'
    manifest = json.loads(mf.read_text())
    if manifest.get('studio') != 'Supreme HQ, Bandra' or (manifest.get('year'), manifest.get('month')) != (2026, 9):
        raise ValueError('Only Bandra September 2026 can be reconciled')
    # Requested presentation: Overview first; supplied Performance Review last.
    if not any(ch['id'] == 'review' for ch in manifest['chapters']):
        manifest['chapters'].append(dict(id='review', title='Performance Review',
                                         slug='performance-review', kpis=[], facts=[], recs=[]))
    manifest['chapters'] = ordered(manifest['chapters'])
    for ch in manifest['chapters']:
        ch['n'] = chapter_number(ch['id'])
    combined = shell(directory / 'report.html')
    wrap = combined.select_one('.wrap')
    navitems = []
    for ch in manifest['chapters']:
        cid = ch['id']
        src = chapters[cid]
        fragment = copy.copy(src['fragment'])
        single_path = directory / (cid + '.html')
        single = shell(single_path if single_path.exists() else ROOT / src['source'])
        single.select_one('header h1').string = ch['title']
        kick = single.select_one('header .kick')
        if kick:
            kick.string = f"Chapter {ch['n']:02} · September 2026"
        single_wrap = single.select_one('.wrap')
        single_wrap.append(navigation(src['sections']))
        single_wrap.append(soup('<p class="source-reconciliation">' + escape(NOTICE) + '</p>').p)
        for node in list(fragment.children):
            single_wrap.append(copy.copy(node))
        lede = single.select_one('header .lede')
        if lede:
            lede.string = 'Source-reconciled September 2026 chapter, including separately labelled historical reference populations.'
        meta = single.select_one('header .meta')
        if meta:
            meta.string = 'Reconciled 13 October 2026 · ' + src['source']
        (directory / (cid + '.html')).write_text(enhance_report(str(single)))
        section = soup(f'<section id="{escape(ch["slug"])}"><h2 id="chapter-{cid}">'
                       f'Chapter {ch["n"]:02} · {escape(ch["title"])}</h2></section>').section
        for node in list(src['fragment'].children):
            section.append(copy.copy(node))
        for link in section.select('.source-cross-reference a'):
            link['href'] = link['href'].replace('report.html#', '#')
        wrap.append(section)
        navitems.append(dict(id=ch['slug'], title=ch['title']))
        ch['sections'] = src['sections']
        ch['subtitle'] = 'Source-reconciled September chapter; historical populations are separately labelled.'
        ch['depth'] = len(str(src['fragment']))
        ch['kpis'] = kpis(src['fragment'])
        paragraphs = [p.get_text(' ', strip=True) for p in src['fragment'].select('p')
                      if not p.get('class')]
        ch['summary'] = paragraphs[0] if paragraphs else ''
        ch['facts'] = paragraphs[:4]
        ch['narration'] = ch['summary']
        # Old generated prose/notes/action arrays carry obsolete populations.
        for key in ('summary_ai', 'recs', 'recs_extra', 'speaker_notes'):
            ch[key] = [] if key != 'summary_ai' else ''
        ch['source_reference'] = src['source']
        ch['source_sha256'] = src['sha256']
        ch['editorial_version'] = 'bandra-source-reconciliation-v1'
    wrap.insert(0, soup('<p class="source-reconciliation">' + escape(NOTICE) + '</p>').p)
    wrap.insert(0, navigation(navitems))
    wrap.append(soup('<footer>Supreme HQ, Bandra · September 2026 · Reconciled 13 October 2026. '
                     'Source figures retain printed precision; historical scopes are labelled in each chapter.</footer>').footer)
    lede = combined.select_one('header .lede')
    if lede:
        lede.string = 'Ten source-reconciled chapters, with Studio Overview first and Performance Review last. Detailed evidence is shown once, with links where chapters share the same table.'
    meta = combined.select_one('header .meta')
    if meta:
        meta.string = 'Supreme HQ, Bandra · September 2026 · Reconciled 13 October 2026'
    (directory / 'report.html').write_text(enhance_report(str(combined)))
    manifest['source_reconciliation'] = receipt
    manifest['sources'] = list(dict.fromkeys(manifest.get('sources', []) + receipt['sources']))
    manifest['warnings'] = list(dict.fromkeys(manifest.get('warnings', []) + [NOTICE]))
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    # Ensure the report library and AI cannot continue answering from the old count.
    pack = from_manifest(manifest)
    pack['source_reconciliation'] = receipt
    dump(pack, directory / 'metrics.json')


def main():
    chapters = source_chapters()
    references = deduplicate(chapters)
    sources = [c['source'] for c in chapters.values()] + [p.name for p in sorted(ROOT.glob('Bandra*.xlsx'))]
    receipt = dict(version=2, chapter_order=list(CHAPTER_ORDER), date='2026-10-13', sources=sources,
                   metric_overrides=[dict(id='transactions', value=195, unit='count', chapter='sales', detail='Distinct sales; 213 payment rows; 210 units'),
                                     dict(id='aov', value=7843, unit='INR', chapter='sales', detail='Gross collections / 195 distinct sales; source rounded')],
                   sha256={name: digest(ROOT / name) for name in sources},
                   supplements=SUPPLEMENTS, duplicate_evidence_replaced=references,
                   precedence='Reconciled sales reference for sales counts; workbook detailed rows over conflicting prose; chapter HTML for other narrative and historical scope.',
                   limitations=NOTICE)
    for target in TARGETS:
        directory = APP / 'runs' / target
        if directory.exists():
            update_run(directory, chapters, receipt)
            print('Updated', target)
    (APP / 'analysis' / 'bandra-source-reconciliation.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
