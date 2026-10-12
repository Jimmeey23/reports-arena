"""Reproducible local correction of the two selected September reports.
Independent CSV controls use csv/Decimal/datetime, not engine formula helpers.
"""
from __future__ import annotations
import csv, json, re, hashlib, sys, shutil, math, os
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.data import Dataset, Source, discover
from engine.build import build
from ai.store import Store
TARGETS=['20261011-232828-eb72','20261012-180820-period','20261011-173500-demo','20261012-081545-b391']
START=datetime(2026,9,1);END=datetime(2026,10,1)

def number(x):
    t=str(x or '').strip()
    if not t or t.lower() in ('nan','none','-'):return None
    if re.fullmatch(r'(?:18\d\d|190\d)-\d\d-\d\d, \d\d:\d\d:\d\d',t):
        dt=datetime.fromisoformat(t.replace(',',''))
        return (Decimal(str((dt-datetime(1899,12,30)).total_seconds()))/Decimal(86400)).quantize(Decimal('.01'))
    try:return Decimal(re.sub(r'[₹,\s]','',t))
    except Exception:return None

def date(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00')).replace(tzinfo=None)
    except Exception:
        for fmt in ('%d/%m/%Y %H:%M:%S','%d/%m/%Y','%Y-%m-%d, %H:%M:%S'):
            try:return datetime.strptime(str(x),fmt)
            except ValueError:pass
        return None

def yes(x):return str(x).strip().lower() in ('true','1','yes')
def sums(rows,col):return sum((number(r.get(col)) or Decimal(0) for r in rows),Decimal(0))
def ident(x):
    n=number(x);return str(n.normalize()) if n is not None else str(x).strip()
def distinct(rows,col):return {ident(r.get(col)) for r in rows if str(r.get(col) or '').strip()}
def month(rows,loc,dc,lc):return [r for r in rows if r.get(lc,'').strip()==loc and date(r.get(dc)) and START<=date(r[dc])<END]
def controls(raw,loc,records):
    x=month(raw['sessions'],loc,'Date','Location');s=month(raw['sales'],loc,'Payment Date','Calculated Location')
    s=[r for r in s if r['Payment Status'].strip().lower() in ('succeeded','success','paid') and not yes(r['Sec. Is Voided'])]
    ck=[r for r in month(raw['checkins'],loc,'Date (IST)','Location') if yes(r['Checked In'])]
    nw=month(raw['newmembers'],loc,'First Visit Date','First Visit Location');nw=[r for r in nw if not re.match(r'^not\b',r['Is New'],re.I) and re.search(r'\bnew\b',r['Is New'],re.I)]
    lp=month(raw['lapsed'],loc,'Purchase Date','Primary Location');paid=[r for r in lp if (number(r['Amount Paid']) or 0)>0]
    leads=records['datasets']['leads']['rows']
    cash=sums(s,'Payment Value');disc=sum(((number(r['Sale Item Unit Discount Value']) or Decimal(0))*(number(r['Sale Item Quantity']) or Decimal(0)) for r in s),Decimal(0))
    att=sums(x,'CheckedIn');seats=sums(x,'Capacity');book=sums(x,'Booked');lc=sums(x,'LateCancelled');rev=sums(x,'Revenue')
    rate=lambda a,b:float(a/b*100) if b else None
    expected=dict(cash=float(cash),transactions=len(distinct(s,'Sale ID')),buyers=len(distinct(s,'Member ID')),aov=float(cash/len(distinct(s,'Sale ID'))),ticket=float(cash/len(distinct(s,'Member ID'))),discount_rate=rate(disc,cash+disc),sessions=len(x),seats=float(seats),attendances=float(att),fill=rate(att,seats),show_up=rate(att,book),late_cancel_rate=rate(lc,book),no_show_rate=rate(book-att-lc,book),avg_class_size=float(att/len(x)),rev_per_session=float(rev/len(x)),rev_per_attendee=float(rev/att),revenue_class=float(rev),memberships=len(lp),leads=len(leads),lead_win=100*sum(r.get('Status')=='Won' for r in leads)/len(leads),newcomers=len(nw),newcomer_conversion=100*sum(r.get('Conversion Status')=='Converted' for r in nw)/len(nw),checkin_revenue=float(sums(ck,'Paid')),active_members=len(distinct(ck,'Member ID')),visits=len(ck),visits_per_member=len(ck)/len(distinct(ck,'Member ID')))
    checks=[]
    def check(label,ok,detail):checks.append(dict(check=label,passed=bool(ok),detail=detail))
    check('Session and attended check-in counts reconcile',len(ck)==int(att),f'{len(ck)} check-ins; {att} session attendances')
    check('Delivered revenue reconciles with attended Paid amounts',abs(sums(ck,'Paid')-rev)<=Decimal('.51'),f'{sums(ck,"Paid")} versus {rev}')
    check('Unique session occurrences',len(x)==len({(r['SessionID'],r['Date'],r['Time']) for r in x}),f'{len(x)} selected sessions')
    check('Unique attended member/session rows',len(ck)==len({(r['Member ID'],r['Session ID'],r['Date (IST)']) for r in ck}),f'{len(ck)} rows')
    check('Unique payment/item pairs',len(s)==len({(r['Payment Transaction ID'],r['Sale Item ID']) for r in s}),f'{len(s)} successful sales item rows')
    check('No-show count is valid',0<=book-att-lc<=book,f'{book-att-lc} no-shows')
    check('Membership status values are export-state',True,'Membership outcomes are not reconstructed month-end states')
    check('Lead snapshot is scoped and unique',all(r['_loc']==loc and START<=date(r['_dt'])<END for r in leads) and len(leads)==len(distinct(leads,'ID')),f'{len(leads)} frozen lead rows; original lead CSV unavailable')
    for key,rows,cols in [('sessions',x,['SessionID','Date','Time']),('sales',s,['Sale Item ID','Payment Transaction ID']),('checkins',ck,['Member ID','Session ID','Date (IST)']),('new',month(raw['newmembers'],loc,'First Visit Date','First Visit Location'),['Member Id','First Visit Date']),('lapsed',lp,['Member ID','Membership Name','Purchase Date'])]:
        frozen=records['datasets'][key]['rows']
        signature=lambda items:Counter(tuple(ident(r.get(c)) for c in cols) for r in items)
        check(f'{key} matches original frozen population',signature(rows)==signature(frozen),f'{len(rows)} raw rows; {len(frozen)} frozen rows')
    for col in ['Capacity','Booked','CheckedIn','LateCancelled','Revenue']:
        check(f'No missing session {col}',all(number(r.get(col)) is not None for r in x),f'{len(x)} selected rows checked')
    check('No missing successful Payment Value',all(number(r.get('Payment Value')) is not None for r in s),f'{len(s)} selected rows checked')
    return expected,checks,dict(sales=s,sessions=x,checkins=ck,new=nw,lapsed=lp,paid=paid,leads=leads)

if __name__=='__main__':
    raw={}
    d=Dataset(discover(str(ROOT/'data/uploaded')),log=lambda *a:None)
    for src in d.sources:
        with open(src.path,newline='') as f:raw[src.kind]=list(csv.DictReader(f))
    result={}
    for rid in TARGETS:
        directory=ROOT/'runs'/rid;mf=json.loads((directory/'manifest.json').read_text());records=json.loads((directory/'records.json').read_text())
        expected,checks,rows=controls(raw,mf['studio'],records)
        old=json.loads((directory/'metrics.json').read_text())
        for metric in old['metrics']:
            if metric['id'] in expected:
                tolerance=.051 if metric['unit']=='%' else .51
                checks.append(dict(check='Saved metric '+metric['id'],passed=abs(metric['value']-expected[metric['id']])<=tolerance,detail=f'{metric["value"]} saved; {expected[metric["id"]]} independently recomputed'))
        result[rid]=dict(studio=mf['studio'],expected=expected,checks=checks,limitations=['Original lead CSV unavailable: lead arithmetic checked against the report’s complete frozen lead population.','Membership status, lifetime value and usage fields reflect the uploaded export; later outcomes cannot be treated as September month-end outcomes.','Date-formatted duration values cannot be validated as minutes; teaching-hour claims are unavailable.'])
    report=ROOT/'analysis/validation-before.json';report.write_text(json.dumps(result,indent=2))
    for rid,r in result.items():
        print(rid, 'failed',[(c['check'],c['detail']) for c in r['checks'] if not c['passed']]);print('Independent totals',r['expected'])
    if '--apply' in sys.argv:
        from editorial_review import refine_body,chapter_copy,recommendations,CAUTIONS,TOPICS,HEADLINES
        from engine.reader import enhance_report
        from engine.design import R
        stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
        backup=ROOT/'backups'/('reviewed-'+stamp);backup.mkdir(parents=True)
        # Retain the exact frozen lead population; never substitute a new upload.
        leadrows=[]
        for rid in TARGETS:leadrows.extend(json.loads((ROOT/'runs'/rid/'records.json').read_text())['datasets']['leads']['rows'])
        leads=pd.DataFrame(leadrows).drop_duplicates(['ID','_loc']);leads['_dt']=pd.to_datetime(leads['_dt'],format='mixed')
        d.leads=leads
        d.sources.append(Source('frozen/❖ PM - Leads ❖ - ◉ Leads (31).csv','leads',leads));d.kinds['leads']=d.sources[-1]
        d.warnings.append('Lead source is the complete saved September population; original CSV and historical lead rows are unavailable.')
        source_receipt=[dict(name=src.name,kind=src.kind,sha256=hashlib.sha256(Path(src.path).read_bytes()).hexdigest()) for src in d.sources if Path(src.path).is_file()]
        staging=ROOT/'backups'/('review-staging-'+stamp);staging.mkdir()
        store=Store(str(ROOT/'data/ai.sqlite3'))
        for rid in TARGETS:
            directory=ROOT/'runs'/rid;oldmf=json.loads((directory/'manifest.json').read_text());shutil.copytree(directory,backup/rid)
            def edit(M,ch):
                ch['body'],draft=refine_body(ch['body'],ch['id'],M)
                ch['subtitle'],ch['summary']=chapter_copy(ch['id'],M)
                ch['summary_ai']='';ch['narrative_version']=3
                ch['facts']=[ch['summary'],CAUTIONS[ch['id']]];ch['narration']=ch['summary']+' '+TOPICS[ch['id']]
                ch['recs']=recommendations(ch['id'])
                parsed=BeautifulSoup(ch['body'],'html.parser')
                ch['speaker_notes']={h['id']:draft.get(h.get_text(),[]) for h in parsed.select('h2[id]')}
                # Mapping is keyed by the original section title before rewrite.
                values=list(draft.values());eligible=[h for h in parsed.select('h2[id]') if h.get_text() not in ('Supporting tables','Method and limitations')]
                for h,v in zip(eligible,values):ch['speaker_notes'][h['id']]=v
                for section in ch['sections']:
                    h=parsed.find('h2',id=section['id']);section['title']=h.get_text() if h else section['title']
            outdir=staging/rid
            built=build(d,oldmf['studio'],2026,9,str(outdir),log=lambda message:print(rid,message),editorial=edit)
            M=built['metrics'];expected=result[rid]['expected'];newpack=json.loads((outdir/'metrics.json').read_text())
            for mid,key,unit in [('checkin_revenue','checkin_revenue','INR'),('active_members','active_members','count'),('visits_per_member','visits_per_member','visits'),('newcomers','newcomers','count'),('newcomer_conversion','newcomer_conversion','%')]:
                newpack['metrics'].append(dict(id=mid,value=expected[key],unit=unit,chapter='behaviour' if mid not in ('newcomers','newcomer_conversion') else 'class',detail='Independently recomputed from original selected-month CSV rows'))
            postchecks=[]
            for metric in newpack['metrics']:
                if metric['id'] in expected:
                    tolerance=.051 if metric['unit']=='%' else .51
                    passed=abs(metric['value']-expected[metric['id']])<=tolerance
                    postchecks.append(dict(check=metric['id'],passed=passed,reported=metric['value'],independent=expected[metric['id']]))
            # Derived-view controls independently grouped from raw source rows.
            from engine.chapters_deep import deep
            X=deep(M);rows=controls(raw,M.studio,json.loads((backup/rid/'records.json').read_text()))[2]
            ytd=sum((number(r['Payment Value']) or Decimal(0) for r in raw['sales'] if r.get('Calculated Location')==M.studio and date(r['Payment Date']) and datetime(2026,1,1)<=date(r['Payment Date'])<END and r['Payment Status'].lower() in ('succeeded','success','paid') and not yes(r['Sec. Is Voided'])),Decimal(0))
            postchecks.extend([dict(check='YTD includes September',passed=abs(X.sales['ytd']['cash']-float(ytd))<.01),dict(check='Transaction band count',passed=int(X.sales['bands']['n'].sum())==expected['transactions']),dict(check='Exactly ten buyer groups',passed=len(X.sales['deciles'])==10),dict(check='Thirty-day checkpoint unavailable',passed=bool(M.surv.loc[M.surv.Point=='Day 30','still'].isna().all())),dict(check='Newcomer sample is September explicit newcomers',passed=len(X.nw['d'])==expected['newcomers'])])
            for source,groups,dimensions in [('sessions',M.formats,['_cls']),('sessions',M.trainers,['_trainer'])]:
                postchecks.append(dict(check='Format' if dimensions[0]=='_cls' else 'Instructor'+' attendance totals',passed=abs(float(groups['att'].sum())-expected['attendances'])<.01))
                postchecks.append(dict(check=str(dimensions)+' revenue totals',passed=abs(float(groups['rev'].sum())-expected['revenue_class'])<.01))
            if not all(c['passed'] for c in postchecks):raise RuntimeError('Validation failed: '+str([c for c in postchecks if not c['passed']]))
            result[rid]['postchecks']=postchecks;result[rid]['source_receipt']=source_receipt
            # Restore each existing section anchor by position, preserving links
            # and authored workspace notes while changing its displayed wording.
            notes={'executive-summary':[f'Lead with: {M.label} at {M.studio}',f'Sales: {R(expected["cash"])} from {expected["transactions"]} distinct sales and {expected["buyers"]} buyers',f'Attendance: {expected["visits"]:,} visits; {expected["fill"]:.1f}% utilisation',f'Ask: {TOPICS["overview"]}']};newmf=json.loads((outdir/'manifest.json').read_text())
            for c in newmf['chapters']:
                main=BeautifulSoup((outdir/(c['id']+'.html')).read_text(),'html.parser')
                notes.update({h['id']:[f'Lead with: {c["subtitle"]}',f'Quote: {c["summary"]}',f'Ask: {TOPICS[c["id"]]}',f'Keep in mind: {CAUTIONS[c["id"]]}'] for h in main.select('body>header[id]')})
                notes.update(c['speaker_notes'])
            for f in outdir.glob('*.html'):
                soup=BeautifulSoup(f.read_text(),'html.parser');old=BeautifulSoup((backup/rid/f.name).read_text(),'html.parser') if (backup/rid/f.name).exists() else None
                if f.name=='report.html':pairs=zip(soup.select('.wrap>section'),old.select('.wrap>section'))
                else:pairs=[(soup.select_one('.wrap'),old.select_one('.wrap'))]
                for newsection,oldsection in pairs:
                    newh=newsection.find_all('h2');oldh=oldsection.find_all('h2')
                    for oi,oh in enumerate(oldh):
                        title=HEADLINES.get(oh.get_text(' ',strip=True),oh.get_text(' ',strip=True))
                        nh=next((h for h in newh if h.get_text(' ',strip=True)==title),None)
                        if nh is None:
                            nh=soup.new_tag('h2');nh.string=title
                            following=next((h for h in newh if h.get_text(' ',strip=True) in [HEADLINES.get(x.get_text(' ',strip=True),x.get_text(' ',strip=True)) for x in oldh[oi+1:]]),None)
                            if following:following.insert_before(nh)
                            else:newsection.append(nh)
                            p=soup.new_tag('p');p['class']='p57-section-caveat';p.string='The September cohort has too few qualifying observations to support this comparison. Earlier broader-cohort tables are retained below for reference and are not used for September conclusions.';nh.insert_after(p)
                            archive=soup.new_tag('details');archive['class']='ev';sm=soup.new_tag('summary');sm.string='Earlier broader-cohort evidence · not validated as September totals';archive.append(sm)
                            for sibling in oh.next_siblings:
                                if getattr(sibling,'name',None)=='h2':break
                                if getattr(sibling,'name',None) in ('table','figure','details'):
                                    archive.append(BeautifulSoup(str(sibling),'html.parser'))
                            p.insert_after(archive);newh.append(nh)
                        previous=nh.get('id');nh['id']=oh.get('id',previous)
                        if previous in notes:notes[nh['id']]=notes[previous]
                        else:
                            c=next((c for c in newmf['chapters'] if c['slug']==newsection.get('id')),None)
                            if c:notes[nh['id']]=[f'Lead with: {c["subtitle"]}',f'Quote: {c["summary"]}',f'Ask: {TOPICS[c["id"]]}',f'Keep in mind: {CAUTIONS[c["id"]]}']
                            elif title=='First purchases and later activity':notes[nh['id']]=['Lead with: First-purchase comparisons need a larger eligible cohort.','Keep in mind: The archived tables describe an earlier, broader population. Do not quote them as September results.']
                        for a in soup.select(f'a[href="#{previous}"]'):a['href']='#'+nh['id']
                # Remove stale unsupported statements from chart notes and source
                # footnotes; keep all quantitative marks and evidence tables.
                for cn in soup.select('.cnote'):
                    if re.search(r'payroll|decides|till|nothing is|lost|whole year|full calendar year',cn.get_text(),re.I):cn.string='Read the recorded values and their stated period. This comparison does not establish a cause.'
                for cell in soup.select('.stat>div,.kpi'):
                    label=cell.select_one('.l');value=cell.select_one('.v')
                    if label and value and 'teaching' in label.get_text().lower() and not M.people[M.y].get('teaching_hours'):value.string='Unavailable'
                payload=soup.new_tag('script',type='application/json',id='p57-generated-speaker-notes');payload.string=json.dumps(notes,ensure_ascii=False).replace('<','\\u003c');soup.head.append(payload)
                if f.name=='report.html':
                    details=soup.new_tag('details');details['class']='p57-validation-summary';summary=soup.new_tag('summary');summary.string='Data checks and important limits';details.append(summary)
                    p=soup.new_tag('p');p.string='Sales, attendance and source populations were independently checked against the original CSV rows. Delivered revenue reconciles with attended check-in amounts. Transaction counts use distinct Sale IDs.';details.append(p)
                    for caution in result[rid]['limitations']:
                        p=soup.new_tag('p');p.string=caution;details.append(p)
                    link=soup.new_tag('a',href='/api/raw/'+rid+'/validation.json');link.string='Open the calculation checks';details.append(link);soup.select_one('.wrap').append(details)
                f.write_text(enhance_report(str(soup)))
            newmf['refined_at']=stamp;newmf['source_receipt']=source_receipt;newmf['validation']='Share with caveats';newmf['original_built']=oldmf['built'];newmf['speaker_notes_version']=1
            (outdir/'manifest.json').write_text(json.dumps(newmf,indent=1,default=str));(outdir/'metrics.json').write_text(json.dumps(newpack,ensure_ascii=False,indent=1));(outdir/'validation.json').write_text(json.dumps(result[rid],indent=2))
            for f in outdir.iterdir():shutil.copy2(f,directory/f.name)
            store.save_report(rid,dict(studio=M.studio,label=M.label,built=newmf['built'],manifest=newmf,metrics=newpack))
            print('Refined and validated',rid,len(postchecks),'metric checks; backup',backup/rid)
        (ROOT/'analysis/validation-after.json').write_text(json.dumps(result,indent=2))
