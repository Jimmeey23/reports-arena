"""Frozen chapter KPI history and accessible month-on-month tables."""
import calendar
import json
import re
from html import escape, unescape
from pathlib import Path
from .metrics import Metrics

# Full typed metric catalogue per chapter, taken from the same Metrics object as
# the report's headline numbers. Each entry: (label, unit).
CATALOGUE = {
    'cash': ('Sales revenue', '₹'), 'transactions': ('Transactions', ''),
    'buyers': ('Buyers', ''), 'aov': ('Average order value', '₹'),
    'ticket': ('Average buyer', '₹'), 'discount_rate': ('Discount rate', '%'),
    'sessions': ('Classes taught', ''), 'seats': ('Seats offered', ''),
    'attendances': ('Attendances', ''), 'fill': ('Utilisation', '%'),
    'show_up': ('Show-up rate', '%'), 'late_cancel_rate': ('Late-cancellation rate', '%'),
    'no_show_rate': ('No-show rate', '%'), 'avg_class_size': ('Average class size', ''),
    'rev_per_session': ('Revenue per class', '₹'), 'rev_per_attendee': ('Revenue per attendee', '₹'),
    'revenue_class': ('Class-attributed revenue', '₹'), 'memberships': ('Memberships purchased', ''),
    'median_life': ('Median observed days', 'days'), 'leads': ('Leads', ''),
    'lead_win': ('Lead win rate', '%'),
}
CHAPTER_METRICS = {
    'sales': ['cash', 'transactions', 'buyers', 'aov', 'ticket', 'discount_rate'],
    'class': ['sessions', 'seats', 'attendances', 'fill', 'show_up', 'late_cancel_rate', 'no_show_rate',
              'avg_class_size', 'rev_per_session', 'rev_per_attendee', 'revenue_class'],
    'instructor': ['sessions', 'attendances', 'fill', 'avg_class_size', 'rev_per_session', 'rev_per_attendee'],
    'format': ['sessions', 'seats', 'attendances', 'fill', 'avg_class_size', 'rev_per_session'],
    'cancels': ['late_cancel_rate', 'no_show_rate', 'show_up', 'discount_rate'],
    'overview': ['cash', 'transactions', 'buyers', 'sessions', 'attendances', 'fill', 'rev_per_session'],
    'behaviour': ['attendances', 'show_up', 'avg_class_size'],
    'lapse': ['memberships', 'median_life'],
    'leads': ['leads', 'lead_win'],
}
# Headline KPI labels that already show a catalogue metric under another name.
ALIASES = {
    'cash': {'cash', 'cash taken', 'revenue'}, 'sessions': {'classes', 'classes run', 'sessions'},
    'ticket': {'average buyer', 'average buyer spend'}, 'aov': {'average sale', 'average ticket'},
    'fill': {'capacity utilisation', 'fill rate'}, 'attendances': {'attendance', 'visits'},
    'memberships': {'memberships purchased in report month', 'bought in report month'},
    'median_life': {'median membership life'}, 'leads': {'leads in report month'},
    'lead_win': {'won', 'win rate'}, 'avg_class_size': {'class size'},
    'rev_per_session': {'revenue per session'}, 'show_up': {'show-up'},
}
# Labels where a fall is the good direction (drives MoM colouring).
LOWER_IS_BETTER = re.compile(r'discount|late|no-show|cancel|empty|emptiest|churn|lapsed|came exactly once|expiring|never attended', re.I)


def indian(n):
    """Indian digit grouping (12,34,567) to match chapter KPI strings."""
    sign, n = ('-' if n < 0 else ''), abs(int(round(n)))
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ','.join([head[max(0, i - 2):i] for i in range(len(head), 0, -2)][::-1])
        s = head + ',' + tail
    return sign + s


def render(value, unit):
    if unit == '₹':
        return '₹' + indian(value)
    if unit == '%':
        return f'{value:.1f}%'
    if unit == 'days':
        return f'{value:g} days'
    return indian(value) if float(value).is_integer() else f'{value:,.2f}'


def catalogue(metric, cid):
    """Typed catalogue values for one chapter and month: {metric id: (label, value)}."""
    try:
        from ai.metrics_pack import from_metrics
        values = {m['id']: m['value'] for m in from_metrics(metric, [])['metrics']}
    except Exception:
        return {}
    out = {}
    for mid in CHAPTER_METRICS.get(cid, []):
        value = values.get(mid)
        if isinstance(value, (int, float)) and value == value:
            label, unit = CATALOGUE[mid]
            out[mid] = (label, render(float(value), unit))
    return out


def periods(year, month):
    end = year * 12 + month - 1
    return [(n // 12, n % 12 + 1) for n in range(end - 11, end + 1)]


def key(label):
    label = unescape(re.sub('<[^>]+>', '', str(label)))
    for name in list(calendar.month_name)[1:]:
        label = re.sub(r'\b' + name + r'\b', 'report month', label, flags=re.I)
    label = re.sub(r'\b(selected|this) month\b', 'report month', label, flags=re.I)
    return label.strip()


def valid(value):
    """Keep only values carrying a figure; placeholders such as '·×' are missing."""
    return value not in (None, '', 'nan') and re.search(r'\d', str(value)) is not None


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
                values = {key(k['label']): str(k['value']) for k in (row or {}).get('kpis', [])
                          if valid(k.get('value'))}
                # Headline KPIs first, then the rest of the chapter's metric catalogue.
                shown = {existing.lower() for existing in values}
                for mid, (label, value) in catalogue(metric, cid).items():
                    if not shown & ({label.lower()} | ALIASES.get(mid, set())):
                        values[label] = value
                if values:
                    result['chapters'][cid]['months'][stamp] = values
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
                        if valid(k.get('value'))}
        except (ValueError, KeyError, TypeError, OSError):
            continue
    return out


def number(value):
    value = unescape(str(value)).strip().replace('−', '-')
    match = re.fullmatch(r'([+-]?)(₹)?\s*([+-]?[\d,]+(?:\.\d+)?)\s*(%|pp|pts?|days?|×|x|visits?|min)?', value, re.I)
    if not match:
        return None
    unit = (match[2] or match[4] or '').lower()
    unit = {'pts': 'pp', 'pt': 'pp', 'day': 'days', 'x': '×', 'visit': '', 'visits': ''}.get(unit, unit)
    number = float(match[3].replace(',', ''))
    return (-number if match[1] == '-' else number), unit


def change(value, previous):
    a, b = number(value), number(previous)
    if not a or not b or a[1] != b[1]:
        return ''
    delta = a[0] - b[0]
    if a[1] in ('%', 'pp'):
        return f'{delta:+.1f} pp MoM'
    if b[0] == 0:
        return f'{delta:+,.2f} absolute · % change unavailable'
    return f'{delta / abs(b[0]) * 100:+.1f}% MoM'


def clean(months):
    """Normalise saved month values: shared labels, figures only."""
    out = {}
    for stamp, values in months.items():
        row = {}
        for label, value in values.items():
            if valid(value):
                row.setdefault(key(label), value)
        if row:
            out[stamp] = row
    return out


def chapter_stamps(months):
    """Contiguous calendar months from the chapter's first to last captured month."""
    present = sorted(months)
    if not present:
        return []
    first = int(present[0][:4])*12 + int(present[0][5:])-1
    last = int(present[-1][:4])*12 + int(present[-1][5:])-1
    return [f'{n//12}-{n%12+1:02d}' for n in range(first, last+1)]


def atlas_payload(title, months, stamps, labels, cid):
    definitions = {}
    ids = []
    for label in labels:
        mid = cid + ':' + label
        ids.append(mid)
        units = [number(values[label])[1] for values in months.values()
                 if label in values and number(values[label]) is not None]
        unit = max(set(units), key=units.count) if units else ''
        definitions[mid] = dict(label=label, unit=unit, higherIsBetter=not LOWER_IS_BETTER.search(label),
                                description='Calculated monthly KPI from uploaded exports; independent of report dates.')
    history = []
    for stamp in stamps:
        row = dict(month=stamp)
        for label in labels:
            value = months.get(stamp, {}).get(label)
            numeric = number(value) if value is not None else None
            unit = definitions[cid + ':' + label]['unit']
            # A value whose unit differs from the row's unit is shown as text, never compared.
            row[cid + ':' + label] = (numeric[0] if numeric and numeric[1] == unit
                                      else unescape(value) if value is not None else None)
        history.append(row)
    payload = json.dumps(dict(title=title, ids=ids, definitions=definitions, history=history), ensure_ascii=False)
    return ('<div class="p57-atlas-monthly"></div><script type="application/json" '
            'class="p57-atlas-monthly-data">' + payload.replace('<', '\\u003c') + '</script>')


def table(data, cid):
    ch = data['chapters'][cid]
    months = clean(ch['months'])
    stamps = chapter_stamps(months)
    ps = [(int(stamp[:4]), int(stamp[5:])) for stamp in stamps]
    labels = list(dict.fromkeys(label for stamp in reversed(stamps) for label in months.get(stamp, {})))
    header = '<th scope="col">Performance measure</th>' + ''.join(
        f'<th scope="col">{calendar.month_abbr[m]} \'{str(y)[2:]}</th>' for y, m in reversed(ps))
    body = ''
    for label in labels:
        body += '<tr><th scope="row">' + escape(label) + '</th>'
        for i in range(len(stamps) - 1, -1, -1):
            stamp = stamps[i]
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
    count = len(stamps)
    # Structure mirrors Atlas ContinuousReport: a disclosure holding the deck register.
    return (f'<details class="p57-monthly cr-disclosure" data-date-independent="true" data-chapter="{escape(cid)}">'
            '<summary>Month-by-month comparison register<span>Explore evidence</span></summary>'
            '<section class="register deck-register" data-index="MoM"><div class="register-head"><div class="register-title">'
            f'<span class="index">MoM</span><strong class="register-name">Month by month</strong><p>{count} month{"s" if count != 1 else ""} frozen at report build · {escape(ch["title"])}</p>'
            '</div></div>'
            f'<p class="p57-mom-note">{escape(data["provenance"])} Changes compare consecutive calendar months. '
            'Percentage metrics show percentage-point changes. Lead and membership outcomes reflect export status, '
            'not reconstructed historical month-end status.</p><div class="p57-mom-scroll table-scroll mom monthly-table compact" tabindex="0" '
            f'role="region" aria-label="{escape(ch["title"])} monthly metrics"><table>'
            f'<thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'
            + atlas_payload(ch['title'], months, stamps, labels, cid) + '</section></details>')


def inject(html, directory=None, data=None, chapter=None):
    # Remove previously injected blocks before refreshing available history.
    # A chapter page's existing block names its chapter; reuse it when none is given.
    previous = re.findall(r'<details class="p57-monthly[^"]*"[^>]*data-chapter="([^"]+)"', html)
    if chapter is None and len(set(previous)) == 1:
        chapter = unescape(previous[0])
    html = re.sub(r'<details class="p57-monthly[^"]*".*?</details>', '', html, flags=re.S)
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
