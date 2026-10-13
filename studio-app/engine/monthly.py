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


def capture(D, studio, year, month, chapters, builders, fallbacks, log):
    result = dict(studio=studio, year=year, month=month,
                  provenance='Frozen calculations from this report’s uploaded exports.', chapters={})
    for ch in chapters:
        result['chapters'][ch['id']] = dict(title=ch['title'], slug=ch['slug'], months={})
    for y, m in periods(year, month):
        stamp = f'{y}-{m:02d}'
        if (y, m) == (year, month):
            built = chapters
        else:
            try:
                metric = Metrics(D, studio, y, m)
            except Exception as exc:
                log(f'  monthly metrics {stamp} unavailable: {exc}')
                continue
            built = []
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
                        built.append(row)
                except Exception as exc:
                    log(f'  monthly metrics {cid} {stamp} unavailable: {exc}')
        for ch in built:
            result['chapters'][ch['id']]['months'][stamp] = {
                key(k['label']): str(k['value']) for k in ch.get('kpis', [])
                if k.get('value') not in (None, '', 'nan')}
    return result


def saved_history(directory):
    directory = Path(directory)
    current = json.loads((directory / 'manifest.json').read_text())
    out = dict(studio=current['studio'], year=current['year'], month=current['month'],
               provenance='Saved reports for this studio only. Missing months require reports generated from the original exports.',
               chapters={ch['id']: dict(title=ch['title'], slug=ch.get('slug', ''), months={})
                         for ch in current['chapters']})
    allowed = {f'{y}-{m:02d}' for y, m in periods(out['year'], out['month'])}
    # The selected report always wins for its own month; duplicate historical
    # months use the latest saved run, with no recalculation from newer uploads.
    paths = sorted(directory.parent.glob('*/manifest.json'))
    paths = [p for p in paths if p.parent != directory] + [directory / 'manifest.json']
    for path in paths:
        try:
            mf = json.loads(path.read_text())
            stamp = f'{mf["year"]}-{mf["month"]:02d}'
            if mf['studio'] != out['studio'] or stamp not in allowed:
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


def table(data, cid):
    ch = data['chapters'][cid]
    ps = periods(data['year'], data['month'])
    stamps = [f'{y}-{m:02d}' for y, m in ps]
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
        body = '<tr><td colspan="13">No saved metrics are available for this chapter.</td></tr>'
    return (f'<details class="p57-monthly" data-chapter="{escape(cid)}"><summary>Month-on-month metrics</summary>'
            f'<p>{escape(data["provenance"])} Changes compare consecutive calendar months. '
            'Percentage metrics show percentage-point changes. Lead and membership outcomes reflect export status, '
            'not reconstructed historical month-end status.</p><div class="p57-mom-scroll" tabindex="0" '
            f'role="region" aria-label="{escape(ch["title"])} monthly metrics"><table>'
            f'<caption>{escape(ch["title"])} · {escape(data["studio"])} · monthly performance</caption>'
            f'<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div></details>')


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
