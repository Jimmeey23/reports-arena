"""Member tables rendered directly from a run's frozen evidence, never guessed."""
import json
import re
from html import escape
from pathlib import Path


def load(runs, rid, pack):
    path = Path(runs, rid, 'records.json')
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError):
        return {}
    if data.get('studio') != pack.get('studio') or data.get('period') != pack.get('period'):
        return {}
    tables = data.get('member_tables')
    if tables is not None:
        return tables
    # Legacy snapshots contain current-month attended check-ins, but cannot
    # identify which people also attended in the previous September.
    dataset = data.get('datasets', {}).get('checkins', {})
    if dataset.get('truncated') or len(dataset.get('rows', [])) != dataset.get('total'):
        return {}
    members = {}
    for row in dataset.get('rows', []):
        mid = row.get('Member ID')
        if mid is None or row.get('Checked In') is not True:
            continue
        name = ' '.join(str(row.get(c)) for c in ('First Name', 'Last Name') if row.get(c))
        item = members.setdefault(str(mid), dict(member_id=str(mid), name=name or 'Name unavailable', visits=0))
        item['visits'] += 1
    return dict(all=list(members.values()), period=pack.get('period'))


def member_table(instruction, current_html, evidence, context=''):
    q = (instruction or '').lower()
    if not ('table' in q and re.search(r'members?|people', q) and re.search(r'visits?|attendance', q)):
        return None
    selected = re.sub('<[^>]+>', ' ', current_html or '').lower()
    scope = q + ' ' + selected + ' ' + context.lower()
    core = bool(re.search(r'returning|both (?:months|septembers)|same[ -](?:people|members)|last (?:year|september)', scope))
    once = bool(re.search(r'(?:one|single|once|exactly 1) visit|came (?:exactly )?once', scope))
    rows = evidence.get('returning_core' if core else 'all')
    if rows is None:
        return dict(error='This saved report does not contain the member-level evidence for that cohort. Regenerate the report from the original exports to capture the names and visits; no members have been guessed.')
    if once and not core:
        rows = [r for r in rows if r['visits'] == 1]
    count = re.search(r'\b(\d+)\s+members?\b', q)
    if not count:
        count = re.search(r'\b(\d+)\s+(?:returning\s+)?members?\b', selected)
    if count and int(count[1]) != len(rows):
        return dict(error=f'The saved evidence identifies {len(rows)} members in this cohort, rather than {count[1]}. Select the cohort section or specify its attendance filter so the correct members can be listed.')
    rows = sorted(rows, key=lambda r: (-r['visits'], r['name'], r['member_id']))
    title = 'Returning community members' if core else 'Community members and visits'
    header = '<th scope="col">Community member</th><th scope="col">Member ID</th>'
    if core:
        header += f'<th scope="col">{escape(str(evidence.get("previous_year")))} visits</th>'
    header += '<th scope="col">Report-period visits</th>'
    body = ''
    for r in rows:
        cells = [r['name'], r['member_id']] + ([r['previous_visits']] if core else []) + [r['visits']]
        body += '<tr>' + ''.join('<td>'+escape(str(c))+'</td>' for c in cells) + '</tr>'
    html = (f'<div class="table-wrap"><table><caption>{title} · {escape(str(evidence.get("period", "")))} · '
            f'{len(rows)} members · attended check-ins</caption><thead><tr>{header}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')
    return dict(html=html, mode='deterministic', tokens=0, cached=False)
