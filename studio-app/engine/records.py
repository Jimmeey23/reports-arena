"""Freeze the same studio/period populations used by report metrics."""
import json
import pandas as pd

# Rows embedded directly into each report page. The complete, uncapped file is
# written next to the report (records.json) and fetched by the drill-down
# explorer on demand, so the page stays loadable without losing any rows.
LIMIT = 5000

def snapshot(M, limit=LIMIT):
    datasets = {}
    for key, attribute in [('sessions','sessions'),('sales','sales'),('checkins','checkins'),('lapsed','lapsed'),('leads','leads'),('new','new')]:
        frame = getattr(M.D, attribute, None)
        if frame is None or '_loc' not in frame:
            continue
        frame = frame[frame['_loc']==M.studio].copy()
        ledger = key in ('lapsed','leads')
        if not ledger and '_dt' in frame:
            frame = M._sl(frame,M.y)
        if key=='checkins' and 'Checked In' in frame:
            frame = frame[frame['Checked In']==True]
        if key=='lapsed' and 'Purchase Date_d' in frame:
            ends=[c for c in ('Churned Date_d','End Date_d') if c in frame]
            ended=frame[ends].min(axis=1) if ends else pd.Series(pd.NaT,index=frame.index)
            life=(ended-frame['Purchase Date_d']).dt.days
            observed=life.where(life>=0).fillna((pd.Timestamp.today().normalize()-frame['Purchase Date_d']).dt.days)
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
                       'source':next((s.name for s in M.D.sources if s.kind==('newmembers' if key=='new' else key)),key)}
    return {'studio':M.studio,'period':M.label,'datasets':datasets}

def embed(value):
    return '<script type="application/json" id="p57-source-records">'+json.dumps(value,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')+'</script>'
