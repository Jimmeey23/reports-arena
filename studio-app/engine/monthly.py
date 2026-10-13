"""Frozen chapter KPI history and accessible month-on-month tables."""
import calendar
import json
import re
from html import escape, unescape
from pathlib import Path
from .metrics import Metrics


def periods(year, month):
    end = year * 12 + month - 1
    return [(n // 12, n % 12 + 1) for n in range(end - 11, end + 1)]


def key(label):
    label = unescape(re.sub('<[^>]+>', '', str(label)))
    for name in list(calendar.month_name)[1:]:
        label = re.sub(r'\b' + name + r'\b', 'report month', label, flags=re.I)
    return label.strip()


def available_periods(D, studio):
    """Read the full source population, independently of report dates."""
    stamps = set()
    for name in ('sales', 'sessions', 'checkins', 'leads', 'lapsed'):
        frame = getattr(D, name, None)
        if frame is None or '_loc' not in frame:
            continue
        frame = frame[frame['_loc'] == studio]
        date = 'Purchase Date_d' if name == 'lapsed' and 'Purchase Date_d' in frame else '_dt'
        if date in frame:
            stamps.update(frame[date].dropna().dt.strftime('%Y-%m').tolist())
    if not stamps:
        return []
    start, end = min(stamps), max(stamps)
    first = int(start[:4])*12 + int(start[5:])-1
    last = int(end[:4])*12 + int(end[5:])-1
    return [(n//12,n%12+1) for n in range(first,last+1)]


def capture(D, studio, year, month, chapters, builders, fallbacks, log):
    all_periods = available_periods(D, studio)
    result = dict(studio=studio, year=year, month=month, scope_version=3, date_independent=True,
                  periods=[f'{y}-{m:02d}' for y,m in all_periods],
                  provenance='All available months from the uploaded source exports, independently of report date filters. The latest month may be partial.', chapters={})
    for ch in chapters:
        result['chapters'][ch['id']] = dict(title=ch['title'], slug=ch.get('slug', ''), months={})
    for y, m in all_periods:
        stamp = f'{y}-{m:02d}'
        log(f'  all-month metrics: {studio} · {stamp}')
        try:
            metric = Metrics(D, studio, y, m)
        except Exception as exc:
            log(f'  monthly metrics {stamp} unavailable: {exc}')
            continue
        for ch in chapters:
            cid = ch['id']
            try:
                required = {'sales': ['sales'], 'class': ['sessions'], 'instructor': ['sessions'],
                            'format': ['sessions'], 'cancels': ['sessions'], 'behaviour': ['checkins'],
                            'leads': ['leads'], 'lapse': ['lapsed'],
                            'overview': ['sales', 'sessions', 'checkins']}[cid]
                available = False
                for source in required:
                    frame = getattr(metric.D, source, None)
                    if frame is not None and '_loc' in frame and '_dt' in frame:
                        available |= not metric._sl(frame, y).empty
                if not available:
                    continue
                row = builders[cid](metric)
                if row is None:
                    row = fallbacks[cid](metric)
                if row:
                    result['chapters'][cid]['months'][stamp] = {
                        key(k['label']): str(k['value']) for k in row.get('kpis', [])
                        if k.get('value') not in (None, '', 'nan')}
            except Exception as exc:
                log(f'  monthly metrics {cid} {stamp} unavailable: {exc}')
    return result


def saved_history(directory):
    directory = Path(directory)
    current = json.loads((directory / 'manifest.json').read_text())
    out = dict(studio=current['studio'], year=current['year'], month=current['month'],
               provenance='Saved reports for this studio only. Missing months require reports generated from the original exports.',
               chapters={ch['id']: dict(title=ch['title'], slug=ch.get('slug', ''), months={})
                         for ch in current['chapters']})
    # Use the same latest saved snapshot per month for every report view.
    # Neither the selected report period nor its date filter affects history.
    paths = sorted(directory.parent.glob('*/manifest.json'))
    for path in paths:
        try:
            mf = json.loads(path.read_text())
            stamp = f'{mf["year"]}-{mf["month"]:02d}'
            if mf['studio'] != out['studio']:
                continue
            for ch in mf['chapters']:
                if ch['id'] in out['chapters']:
                    out['chapters'][ch['id']]['months'][stamp] = {
                        key(k['label']): str(k['value']) for k in ch.get('kpis', [])
                        if k.get('value') not in (None, '', 'nan')}
        except (ValueError, KeyError, TypeError, OSError):
            continue
    return out


def number(value):
    value = unescape(str(value)).strip()
    match = re.fullmatch(r'(₹)?([+-]?[\d,]+(?:\.\d+)?)(%| days?|×)?', value)
    if not match:
        return None
    return float(match[2].replace(',', '')), (match[1] or match[3] or '').strip()


def change(value, previous):
    a, b = number(value), number(previous)
    if not a or not b or a[1] != b[1]:
        return ''
    delta = a[0] - b[0]
    if a[1] == '%':
        return f'{delta:+.1f} pp MoM'
    if b[0] == 0:
        return f'{delta:+,.2f} absolute · % change unavailable'
    return f'{delta / abs(b[0]) * 100:+.1f}% MoM'


def atlas_payload(data, cid, stamps, labels):
    ch = data['chapters'][cid]
    definitions = {}
    ids = []
    for label in labels:
        mid = cid + ':' + label
        ids.append(mid)
        sample = next((number(values[label]) for values in ch['months'].values()
                       if label in values and number(values[label]) is not None), None)
        definitions[mid] = dict(label=label, unit=sample[1] if sample else '',
                                description='Calculated monthly KPI from uploaded exports; independent of report dates.')
    history = []
    for stamp in stamps:
        row = dict(month=stamp)
        for label in labels:
            value = ch['months'].get(stamp, {}).get(label)
            numeric = number(value) if value is not None else None
            row[cid + ':' + label] = numeric[0] if numeric else unescape(value) if value is not None else None
        history.append(row)
    payload = json.dumps(dict(title=ch['title'], ids=ids, definitions=definitions, history=history), ensure_ascii=False)
    return ('<div class="p57-atlas-monthly"></div><script type="application/json" '
            'class="p57-atlas-monthly-data">' + payload.replace('<', '\\u003c') + '</script>')


def table(data, cid):
    ch = data['chapters'][cid]
    stamps = data.get('periods') or sorted({stamp for ch in data['chapters'].values() for stamp in ch['months']})
    if stamps:
        first = int(stamps[0][:4])*12 + int(stamps[0][5:])-1
        last = int(stamps[-1][:4])*12 + int(stamps[-1][5:])-1
        stamps = [f'{n//12}-{n%12+1:02d}' for n in range(first,last+1)]
    ps = [(int(stamp[:4]), int(stamp[5:])) for stamp in stamps]
    months = ch['months']
    labels = list(dict.fromkeys(label for stamp in reversed(stamps) for label in months.get(stamp, {})))
    header = '<th scope="col">Metric</th>' + ''.join(
        f'<th scope="col">{calendar.month_abbr[m]} {y}</th>' for y, m in ps)
    body = ''
    for label in labels:
        body += '<tr><th scope="row">' + escape(label) + '</th>'
        for i, stamp in enumerate(stamps):
            value = months.get(stamp, {}).get(label)
            previous = months.get(stamps[i-1], {}).get(label) if i else None
            delta = change(value, previous) if value is not None and previous is not None else ''
            body += '<td>' + (escape(unescape(value)) if value is not None else '<span class="p57-mom-missing">Unavailable</span>')
            if delta:
                body += '<small>' + escape(delta) + '</small>'
            body += '</td>'
        body += '</tr>'
    if not labels:
        body = f'<tr><td colspan="{len(stamps)+1}">No saved metrics are available for this chapter.</td></tr>'
    return (f'<details class="p57-monthly" data-date-independent="true" data-chapter="{escape(cid)}"><summary>Month-on-month metrics</summary>'
            f'<p>{escape(data["provenance"])} Changes compare consecutive calendar months. '
            'Percentage metrics show percentage-point changes. Lead and membership outcomes reflect export status, '
            'not reconstructed historical month-end status.</p><div class="p57-mom-scroll" tabindex="0" '
            f'role="region" aria-label="{escape(ch["title"])} monthly metrics"><table>'
            f'<caption>{escape(ch["title"])} · {escape(data["studio"])} · monthly performance</caption>'
            f'<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>' + atlas_payload(data, cid, stamps, labels) + '</details>')


def inject(html, directory=None, data=None, chapter=None):
    # Remove previously injected blocks before refreshing available history.
    html = re.sub(r'<details class="p57-monthly".*?</details>', '', html, flags=re.S)
    if data is None and directory:
        try:
            path = Path(directory) / 'monthly.json'
            data = json.loads(path.read_text()) if path.is_file() else saved_history(directory)
        except (ValueError, KeyError, TypeError, OSError):
            return html
    if not data:
        return html
    combined = False
    for cid, ch in data['chapters'].items():
        slug = ch.get('slug') or re.sub('[^a-z0-9]+', '-', ch['title'].lower()).strip('-')[:60]
        marker = f'<section id="{slug}">'
        if marker in html:
            combined = True
            html = html.replace(marker, marker + table(data, cid), 1)
    if not combined:
        cid = chapter or (Path(directory).stem if directory else None)
        if cid not in data['chapters']:
            title = re.search('<title>(.*?)</title>', html, re.S)
            cid = next((k for k, ch in data['chapters'].items() if title and ch['title'] in unescape(title[1])), None)
        if cid:
            html = html.replace('<div class="wrap">', '<div class="wrap">' + table(data, cid), 1)
    return html
