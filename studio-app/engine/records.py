"""Freeze the same studio/period populations used by report metrics."""
import json
import pandas as pd

# Rows embedded directly into each report page. The complete, uncapped file is
# written next to the report (records.json) and fetched by the drill-down
# explorer on demand, so the page stays loadable without losing any rows.
LIMIT = 5000

def member_tables(M):
    """Freeze member-level attendance, including the exact returning cohort."""
    def aggregate(frame):
        result = {}
        if frame is None or 'Member ID' not in frame:
            return result
        for row in frame.to_dict('records'):
            mid = row.get('Member ID')
            if pd.isna(mid):
                continue
            key = str(mid)
            name = ' '.join(str(row.get(c)) for c in ('First Name', 'Last Name')
                            if pd.notna(row.get(c)) and str(row.get(c)).strip())
            item = result.setdefault(key, dict(member_id=key, name=name or 'Name unavailable', visits=0))
            item['visits'] += 1
        return result
    current = aggregate(M._ck(M.y))
    previous = aggregate(M._ck(M.y - 1))
    core = [dict(current[k], previous_visits=previous[k]['visits'])
            for k in current.keys() & previous.keys()]
    order = lambda rows: sorted(rows, key=lambda r: (-r['visits'], r['name'], r['member_id']))
    return dict(all=order(list(current.values())), returning_core=order(core),
                previous_year=M.y - 1, year=M.y, period=M.label)

def snapshot(M, limit=LIMIT):
    datasets = {}
    for key, attribute in [('sessions','sessions'),('sales','sales'),('checkins','checkins'),('lapsed','lapsed'),('leads','leads'),('new','new'),('membership_churn','lapsed')]:
        frame = getattr(M.source_D if key == 'membership_churn' else M.D, attribute, None)
        if frame is not None and key == 'membership_churn':
            frame = frame.copy()
            if 'Churned Date_d' not in frame: continue
            frame['_dt'] = frame['Churned Date_d']
        if frame is None or '_loc' not in frame:
            continue
        frame = frame[frame['_loc']==M.studio].copy()
        ledger = False
        if not ledger and '_dt' in frame:
            frame = M._sl(frame,M.y)
        if key=='checkins' and 'Checked In' in frame:
            frame = frame[frame['Checked In']==True]
        if key=='lapsed' and 'Purchase Date_d' in frame:
            ends=[c for c in ('Churned Date_d','End Date_d') if c in frame]
            ended=frame[ends].min(axis=1) if ends else pd.Series(pd.NaT,index=frame.index)
            ended=ended.where(ended<=M.as_of)
            life=(ended-frame['Purchase Date_d']).dt.days
            observed=life.where(life>=0).fillna((M.as_of-frame['Purchase Date_d']).dt.days)
            paid=frame['Amount Paid'].fillna(0)>0 if 'Amount Paid' in frame else ~frame['Membership Name'].astype(str).str.contains('Complimentary|Staff',case=False,na=False)
            frame['Observed life days']=observed.where(paid & frame['Purchase Date_d'].notna())
        # Identifiers support distinct-member calculations, while contact details
        # and raw transport fields are excluded from the saved explorer.
        columns=[c for c in frame if not any(t in str(c).lower() for t in ('email','phone','token','uniqueid'))]
        view = frame[columns] if limit is None else frame[columns].head(limit)
        rows=json.loads(view.to_json(orient='records',date_format='iso'))
        datasets[key]={'rows':rows,'total':len(frame),'truncated':limit is not None and len(frame)>limit,
                       'complete':limit is None,
                       'scope':'Studio-wide ledger snapshot' if ledger else 'Selected studio and report month',
                       'source':next((s.name for s in M.D.sources if s.kind==('newmembers' if key=='new' else 'lapsed' if key=='membership_churn' else key)),key)}
    return {'studio':M.studio,'period':M.label,'datasets':datasets,
            'member_tables':member_tables(M)}

def embed(value):
    return '<script type="application/json" id="p57-source-records">'+json.dumps(value,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')+'</script>'
