"""Apply the supplied September review to the existing frozen Bandra reports.
Preserves evidence rows, chapter identities and source snapshots; backs up revisions.
"""
from pathlib import Path
import sys,json,re,shutil,hashlib
from datetime import datetime
from html import escape
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.editorial import TITLES,clean_body,methodology
from engine.reader import enhance_report
DOC=(ROOT/'editorial/bandra-september-2026-review.md').read_text()
TARGETS=['20261011-232828-eb72','20261011-173500-demo']

def fragment(text):
    paragraphs=[]
    for block in text.strip().split('\n\n'):
        block=block.strip()
        if not block:continue
        if block.startswith('#'):
            paragraphs.append('<h3>'+escape(block.lstrip('#').strip())+'</h3>');continue
        if block.startswith('Priority ') and '\n' not in block:
            paragraphs.append('<h3>'+escape(block)+'</h3>');continue
        t=escape(block).replace('\n',' ')
        t=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',t)
        paragraphs.append('<p>'+t+'</p>')
    return ''.join(paragraphs)

def excerpt(start,end,offset=0):
    return DOC.split(start,1)[1].split(end,1)[0].strip()

STARTS={'sales':'## Sales Performance','class':'## Class Performance','instructor':'## Instructor Performance','lapse':'## Membership Health, Retention and Lapse','format':'## Format Performance\n','cancels':'## Revenue and Capacity Leakage','overview':'## Studio Overview and Business Intelligence','leads':'## Lead Performance and Acquisition Health','behaviour':'## Member Behaviour and Engagement'}
ENDS={'sales':'### Replace these specific','class':'### Replace the subsection','instructor':'### Replace "The controlled','lapse':'### Replace "The two','format':'### Replace the following','cancels':'### Replace the late','overview':'### Replace "What the data','leads':'### Rewrite "The file','behaviour':'### Replace "How often'}
INTRO={c:excerpt(STARTS[c],ENDS[c]) for c in STARTS}
INTRO['sales']=INTRO['sales'].replace('across 213 transactions','across 196 distinct transactions (213 sale lines)')
INTRO['class']=INTRO['class'].replace('A further 1,889 available seats were never booked.','There were 1,689 places without a recorded booking and 1,889 unoccupied places in total.').replace('199 were recorded as late cancellations.','199 were recorded as late cancellations; one booking was neither attended nor recorded as late-cancelled.')
INTRO['cancels']=INTRO['cancels'].replace('₹1.64 lakh','₹1.45 lakh').replace('₹1,63,709','₹1,45,209')
INTRO['lapse']='''Membership expiry is visible. Customer disengagement requires a separate attendance and purchasing assessment.

The frozen September purchase cohort contains 325 membership records, including 121 paid purchases. Product status and usage reflect the uploaded export, rather than reconstructed September month-end outcomes. The median observed follow-up is eight days through month-end, not a completed membership lifetime.

A product reaching its end date does not establish customer churn. Review subsequent purchases, latest attendance, entitlement validity and the interval since expiry before identifying customer inactivity.

Distinguish members approaching expiry with healthy attendance, members with valid entitlements and declining engagement, and customers whose products ended without a subsequent recorded purchase. Each group requires a different response.

**Retention priority:** Identify declining engagement while members still have valid reasons to return. The review’s broader historical counts and unused-credit totals cannot be verified from this frozen monthly cohort; retained historical reference tables must not be quoted as September findings.'''
INTRO['leads']='''Trial progression is a useful intermediate acquisition milestone; subsequent purchasing and engagement remain the commercial outcomes.

September’s frozen cohort contains 189 enquiries, 103 recorded trials and 12 recorded conversions at export. The recorded conversion rate is 6.3%. More recent enquiries have had less time to progress, so compare cohorts over a consistent observation window.

The original historical lead export is unavailable. The review’s lifetime counts, open-pipeline totals and historical 26.1% versus 2.2% conversion comparison cannot be independently verified from the saved September population and are excluded from performance conclusions.

**Acquisition priority:** Review trial scheduling, completion and follow-up ownership within the available cohort, qualify open opportunities and track trial-to-purchase progression without treating trial completion as the final acquisition goal.'''
INTRO['overview']=INTRO['overview'].replace('Meanwhile, the studio received 189 new leads, against a historical lead database containing 2,120 records still marked open.','The studio received 189 September leads. Historical open-pipeline volume cannot be verified from the available frozen lead population.')
INTRO['behaviour']=re.sub(r'The historical visiting ledger.*?\n\n','',INTRO['behaviour'],flags=re.S)

HEADS={
 'Which products drove sales':'Revenue Mix: Which Products Sustained September?', 'Package length and purchased access':'Are Customers Committing to Less?', 'What each session credit earns':'Product Pricing: Value, Commitment and Purchase Behaviour', 'When sales picked up':'Revenue Timing: When Did Customers Buy?', 'Basket size and repeat buyers':'Transaction Value and Repeat Purchasing','The team behind the sales':'Sales Contribution by Associate','Discounting':'Discount Dependency and Revenue Protection','Who drove the sales':'Customer Concentration: Who Sustains Revenue?','First purchases and later activity':'First Purchase Behaviour and Long-Term Customer Value',
 'Capacity and attendance':'Capacity Is Available, but Demand Is Unevenly Distributed','Sessions with no attendance':'Underperforming Classes: Where Capacity Is Being Lost', 'Comparable sessions':'Like-for-Like Performance: Separating Instructor Impact from Schedule Impact','The scorecard':'Attendance and Utilisation by Instructor','Member attendance by instructor':'Post-Class Engagement and Conversion','Newcomer conversion by instructor':'First-Class Conversion by Instructor',
 'Purchases with and without recorded attendance':'Product Completion Is Not the Same as Customer Churn','Recorded changes in attendance':'Declining Visit Frequency Is an Earlier Retention Signal','Unused access and recent attendance':'Unused Credits: An Opportunity to Rebuild Engagement',
 'Format scorecard':'Format Performance Scorecard','Format reach and repeat visits':'Customer Reach vs Repeat Engagement','Members using more than one format':'Does Cross-Format Participation Increase Engagement?','Attendance and value by format':'Single-Format Loyalty vs Multi-Format Participation','When each format is used':'Demand Patterns by Format and Time Slot','Complimentary attendance by format':'Complimentary Attendance and Promotional Allocation',
 'Decisions supported by this month':'What September Establishes—and What Still Needs Investigation','Open leads and follow-up needs':'Pipeline Hygiene: Which Open Leads Are Actionable?','How often members come':'The Average Member Does Not Represent the Typical Member','Regulars are visiting less often':'Returning Members and Visit Frequency','The returning core':'The Returning Core: 252 Fewer Visits from the Same 78 People','Visits across the month':'Attendance Across Comparable Reporting Weeks',
 'The key takeaway':'What the numbers reveal','What to do with these findings':'Commercial implication','Recommendations':'Recommended response'}

COPY={}
def add(cid,heading,start,end):COPY[cid,heading]=excerpt(start,end)
add('sales','Which products drove sales','Revenue Mix\n','Are Customers Committing to Less?\n')
add('sales','Package length and purchased access','Are Customers Committing to Less?\n','Customer Concentration\n')
add('sales','Who drove the sales','Customer Concentration\n','Replace the existing Sales chapter conclusion')
add('class','Capacity and attendance','New heading: Capacity Is Available, but Demand Is Unevenly Distributed','### Replace "The free seats"')
add('class','Sessions with no attendance','New heading: Underperforming Classes: Where Capacity Is Being Lost','### Replace the chapter conclusion')
add('instructor','Comparable sessions','New heading: Like-for-Like Performance: Separating Instructor Impact from Schedule Impact','### Improve all 14')
add('lapse','Purchases with and without recorded attendance','New heading: Product Completion Is Not the Same as Customer Churn','### Replace "The decline')
COPY['lapse','Recorded changes in attendance']='Review recent attendance against each member’s established pattern, using comparable observation windows and sufficient visits. A declining frequency can prompt an earlier conversation about member-reported scheduling or service barriers; it does not establish why attendance changed. The historical percentages in the review require a broader validated cohort before publication.'
COPY['lapse','Unused access and recent attendance']='Unused credits represent outstanding service entitlements, not automatically incremental revenue. Prioritise members with valid remaining credits, low utilisation and a widening gap since their last attendance. Validate redemption eligibility and the cohort before reporting a total unused-credit opportunity.'
add('format','Members using more than one format','### Rewrite the multi-format insight','## Chapter 06')
add('cancels','Released capacity, not booked losses','### Replace the late-cancellation opportunity statement','### Rewrite the discounting conclusion')
add('cancels','Where discounts were recorded','### Rewrite the discounting conclusion','## Chapter 07')
COPY['cancels','Where discounts were recorded']=COPY['cancels','Where discounts were recorded'].replace('₹1.64 lakh','₹1.45 lakh')
COPY['overview','Decisions supported by this month']='Customer reach increased, visit frequency weakened and 57.4% of available capacity remained unoccupied. These findings are supported by the saved attendance and session records. Weather, festivals, instructor quality and internal process gaps remain unestablished explanations; they require additional evidence. Historical trial conversion and open-pipeline claims cannot be verified from the frozen September lead snapshot.'
COPY['leads','Open leads and follow-up needs']='Recorded pipeline volume is not the same as an actionable sales opportunity. Segment the available open enquiries by recency, trial status and recorded follow-up, then confirm intent with the prospect. The review’s 2,120 lifetime open leads and 1,664 older-than-a-year records require the missing historical export before publication.'
COPY['leads','Who handles the leads']='Compare associates using the same cohort, lead source, allocation period and conversion observation window. Review response time, trial scheduling, trial completion, purchasing conversion and recorded follow-up separately. Historical associate rankings from the review cannot be validated from the available September snapshot.'
add('behaviour','How often members come','New heading: The Average Member Does Not Represent the Typical Member','### Replace "The returning core"')
CORE=excerpt('### The Returning Core: 252 Fewer Visits from the Same 78 People','### Replace "The rhythm')
COPY['behaviour','One-time visitors and regular attendance']=CORE
add('behaviour','Visits across the month','### Replace "The rhythm of the month"','### Replace the chapter\'s closing paragraph')
CONCLUSIONS={
 'sales':excerpt('Replace the existing Sales chapter conclusion with:','## Chapter 02'),
 'class':excerpt('### Replace the chapter conclusion','## Chapter 03'),
 'instructor':'Instructor attendance outcomes reflect both contribution and timetable conditions. Review comparable formats and time slots before changing allocation or attributing differences to teaching quality. Keep compensation analysis separate from class-attributed revenue.',
 'lapse':'Identify declining engagement before expiry, validate remaining entitlements and distinguish product completion from customer inactivity. Use confirmed attendance and repurchase evidence to select the appropriate follow-up.',
 'format':'Strengthen proven recurring formats, investigate weaker slots and test cross-format recommendations with a comparable group. Assess partnership events against their own acquisition and community objectives.',
 'cancels':'Manage released capacity and pricing discipline separately. Track actual seat recovery and subsequent purchasing outcomes rather than converting illustrative opportunity values into realised revenue.',
 'overview':excerpt('End the chapter with:','## Chapter 08'),
 'leads':'Completed trials are a primary intermediate conversion milestone, alongside subsequent purchase and sustained engagement. Use consistent observation windows and verify pipeline status before treating recorded open leads as active opportunities.',
 'behaviour':excerpt('### Replace the chapter\'s closing paragraph','# 5. Completely redesign')}

EXEC=excerpt('## Executive Summary','### Management conclusion')
# Historical trial figures are supplied commentary, not independently verified evidence.
EXEC=re.sub(r'\*\*05.*', '**05 | Trial progression needs a consistent conversion window.**\n\nSeptember recorded 12 conversions from 189 enquiries and 103 recorded trials at export. Assess trial completion, follow-up and purchasing over comparable cohort windows. Historical trial conversion rates in the review are unavailable for independent verification.',EXEC,flags=re.S)
ACTIONS=excerpt('Priority 01 —','## 6. Add a measurable October Scorecard')
ACTIONS='Priority 01 — '+ACTIONS
ACTIONS=ACTIONS.replace('Historical conversion stands at 26.1% among completed-trial leads, versus 2.2% among leads without a completed trial.','September recorded 189 enquiries, 103 trials and 12 conversions at export; historical trial-status conversion rates are unavailable for independent verification.').replace('145 paid memberships with usage data had utilised no more than one-quarter of their entitlement.','The September purchase cohort contains 325 membership records, including 121 paid purchases; engagement risk requires validation of usage, product validity and last attendance.')
SCORE='''<h2 id="october-scorecard">October Scorecard</h2><p>These are proposed management goals, not forecasts or approved budgets. The historical trial conversion baseline in the review cannot be verified from the available source snapshot.</p><table class="num"><thead><tr><th>Performance indicator</th><th>September baseline</th><th>Proposed October target</th></tr></thead><tbody>'''+''.join('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>' for row in [
 ('Active attendees','394','Monitor alongside frequency'),('Average visits per attendee','3.56','4.00'),('Studio utilisation','42.6%','47.0%'),('Classes with 0–2 attendees','49','35 or fewer'),('Late-cancellation rate','12.4%','Below 10%'),('One-visit share','52%','Below 45%'),('Total attendance','1,404','1,550'),('Trial-to-purchase conversion','Historical baseline unavailable','Set on a comparable mature cohort'),('Sales revenue','₹15.29L','Set against approved sales budget')])+ '</tbody></table>'+fragment(excerpt('### Add this paragraph below the scorecard','# 7. Improve'))
VERDICT=excerpt('# The September Verdict','## 11. My recommended implementation order')
METHOD=methodology('September 1–30, 2026',2026)


def insert_html(after,text):
    for n in list(BeautifulSoup(text,'html.parser').contents):after.insert_after(n);after=n

def siblings(h):
    result=[]
    for n in h.next_siblings:
        if getattr(n,'name',None)=='h2':break
        if getattr(n,'name',None):result.append(n)
    return result

def replace_narrative(h,text):
    for n in siblings(h):
        if n.name=='p' or ('call' in n.get('class',[]) and not n.find(['table','svg'])):n.decompose()
    insert_html(h,fragment(text))

def evidence_digest(s):
    # Existing tables only; newly authored scorecard is checked separately.
    return [hashlib.sha256(str(t).encode()).hexdigest() for t in s.select('table')]


def correct_chapter(s,cid,container,mf):
    headings=list(container.find_all('h2',recursive=False))
    for h in headings:
        old=h.get_text(' ',strip=True)
        if old in ('Recommendations','Recommended response'):
            for n in siblings(h):n.decompose()
            h.string='Recommended response'
            insert_html(h,'<p>'+escape(CONCLUSIONS[cid])+'</p><p>Use the consolidated October Action Plan to assign ownership and measure progress.</p>')
        elif old in ('The key takeaway','What the numbers reveal'):
            replace_narrative(h,INTRO[cid]);h.string='What the numbers reveal'
        elif old in ('What to do with these findings','Commercial implication'):
            replace_narrative(h,CONCLUSIONS[cid]);h.string='Commercial implication'
        elif (cid,old) in COPY:replace_narrative(h,COPY[cid,old])
        if old in HEADS:h.string=HEADS[old]
    # The old intro callout duplicated the first section.
    for call in list(container.find_all('div',class_='call',recursive=False)):
        if call.find('h4') and call.h4.get_text() in ('In short','Performance verdict'):call.decompose()
    insert_html(container.find('h2'),'<p class="p57-performance-verdict"><strong>Performance verdict:</strong> '+escape(mf['subtitle'])+'</p>')
    # Retain the monthly cohort, rather than silently substituting supplied lifetime totals.
    insert_html(headings[-1],METHOD)
    if cid=='instructor':
        table=container.find('table');rows={r.find('td').get_text(' ',strip=True):[c.get_text(' ',strip=True) for c in r.find_all('td')] for r in table.select('tbody tr') if r.find('td')}
        for h in container.select('h3'):
            row=rows.get(h.get_text(' ',strip=True))
            if not row or len(row)<8:continue
            for old in list(h.next_siblings):
                if getattr(old,'name',None) in ('h2','h3'):break
                if getattr(old,'name',None)=='p':old.decompose()
            insert_html(h,fragment(f'**Contribution:** {row[1]} Studio Sessions, {row[2]} attendances and {row[5]} delivered class revenue; {row[6]} per session and {row[7]} per attendee.\n\n**Performance interpretation:** Recorded utilisation was {row[4]}. Assigned formats, capacity and time slots affect this outcome; it is not an isolated measure of teaching effectiveness.\n\n**Recommended focus:** Compare recurring sessions within the same format and time window, retain the sample size, and review weaker slots before changing teaching volume.'))
    for a in s.select('a[href^="#"]'):
        target=s.find(id=a['href'][1:])
        if target and target.name=='h2':
            span=a.find('span');prefix=str(span) if span else '';a.clear()
            for n in list(BeautifulSoup(prefix+escape(target.get_text(' ',strip=True)),'html.parser').contents):a.append(n)
    # Remove only invalid narrative; never rewrite source table values.
    for p in list(container.select('p,.cnote,.sub')):
        if p.find_parent('table') or p.find(['table','svg']):continue
        txt=p.get_text(' ',strip=True)
        if re.search(r'^\d+ classes;.*attendances;|₹3\.(65|74) crore|5,929|30th out of 29|₹10,264 to ₹10,264|·-fold|\b1 days\b|Working 07 to 19|one or two runs ·',txt):p.decompose()
    if cid=='instructor':
        for p in container.select('p,.cnote'):
            if re.search(r'payroll|compensation|payout',p.get_text(),re.I) and '₹13' in p.get_text():p.string='Delivered class revenue is not instructor compensation. A cost comparison requires a separately reconciled payroll dataset.'


def main():
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');backup=ROOT/'backups'/('bandra-editorial-'+stamp);backup.mkdir(parents=True)
    for rid in TARGETS:
        d=ROOT/'runs'/rid
        if json.loads((d/'manifest.json').read_text()).get('editorial_version')=='bandra-review-v1':
            print('Already corrected',rid);continue
        shutil.copytree(d,backup/rid);mf=json.loads((d/'manifest.json').read_text());byid={c['id']:c for c in mf['chapters']}
        for cid,c in byid.items():
            c['title']=TITLES[cid];c['subtitle']=re.search(r'### Recommended (?:chapter )?headline\n\n(.*?)\n',DOC.split('## Chapter '+f'{c["n"]:02d}',1)[-1]).group(1) if cid!='cancels' else 'Protect booked attendance and maintain pricing discipline.'
            c['summary']=BeautifulSoup(fragment(INTRO[cid]),'html.parser').get_text(' ',strip=True)
            c['narration']=c['summary'];c['summary_ai']='';c['recs_extra']=[];c['recs']=[];c['facts']=[c['summary']];c['editorial_version']='bandra-review-v1'
        report=BeautifulSoup((d/'report.html').read_text(),'html.parser')
        for name in [c+'.html' for c in byid]+['report.html']:
            s=report if name=='report.html' else BeautifulSoup((d/name).read_text(),'html.parser')
            before=evidence_digest(s)
            if name=='report.html':
                for cid,c in byid.items():
                    section=s.find(id=c['slug']);correct_chapter(s,cid,section,c);section.find('h2').string=f'Chapter {c["n"]:02d}  {c["title"]}';section.select_one('.sub').string=c['subtitle']
                overview=s.find(id=byid['overview']['slug']);first=s.select_one('.wrap>section');first.insert_before(overview.extract())
                s.select_one('body>header h1').string='September 2026 | Studio Performance Review'
                s.select_one('body>header .lede').string='A larger audience. A weaker attendance habit. September’s opportunity is to turn wider reach into more consistent visits and purchasing continuity.'
                old=s.select_one('.p57-executive-summary');old.clear();old.append(BeautifulSoup('<h2 id="executive-summary">Executive Summary</h2>'+fragment(EXEC)+'<h3>Management conclusion</h3>'+fragment(excerpt('### Management conclusion','# 4. Chapter-by-chapter')),'html.parser'))
                kpis='<div class="kpis">'+''.join(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div><div class="d">{dt}</div><p>{note}</p></div>' for l,v,dt,note in [('Sales revenue','₹15.29L','↓ 2.3% YoY','Fewer buyers, higher spend per buyer.'),('Active attendees','394','↑ 29.2% YoY','A wider audience, but less frequent visits.'),('Attendance','1,404','↓ 4.9% YoY','Fewer visits despite more attendees.'),('Studio utilisation','42.6%','↑ 0.8 percentage points YoY','More than half of available capacity remains unused.')])+'</div>'
                old.insert_before(BeautifulSoup(kpis,'html.parser'))
                old.insert_before(BeautifulSoup('<p>September welcomed 394 attendees, compared with 305 in September 2025. Average visits per attendee declined from 4.84 to 3.56. Sales reached ₹15.29 lakh while 259 Studio Sessions operated at 42.6% utilisation. The management question is how to turn a larger audience into more frequent visits and stronger purchasing continuity.</p>','html.parser'))
                for a in s.select('.toc a[href]'):
                    c=next((c for c in byid.values() if a['href']=='#'+c['slug']),None)
                    if c:a.string=c['title']
                wrap=s.select_one('.wrap');wrap.append(BeautifulSoup('<section id="october-action-plan"><h2>October Action Plan</h2>'+fragment(ACTIONS)+'</section><section id="october-targets">'+SCORE+'</section><section id="september-verdict"><h2>The September Verdict</h2>'+fragment(VERDICT)+'</section>','html.parser'))
                issues='<details class="ev"><summary>Review reconciliation and source limits</summary><p>The supplied content review guides the narrative. Reconciled frozen sources control reported actuals: 196 distinct Sale IDs across 213 sale lines; ₹1,45,209 successful-sale item discounts; 1,689 unbooked places and 1,889 unoccupied places. Historical lead totals and conversion rates in the review are unverified because the original historical lead export is unavailable. Broader historical membership and visit-gap claims are not substituted for the frozen monthly cohort. Retained archival evidence retains its original scope and qualification.</p></details>'
                s.find(id='october-action-plan').insert_before(BeautifulSoup(issues,'html.parser'))
            else:
                cid=name[:-5];c=byid[cid];correct_chapter(s,cid,s.select_one('.wrap'),c);s.select_one('body>header h1').string=c['title'];s.select_one('body>header .lede').string=c['subtitle']
            # Clear private generated cues containing obsolete language, keep authored notes in workspace.
            notes={h['id']:['Lead with: '+h.get_text(' ',strip=True),'Discuss the adjacent source-backed finding and proposed response.'] for h in s.select('h2[id]')}
            for payload in s.select('#p57-generated-speaker-notes'):payload.string=json.dumps(notes,ensure_ascii=False).replace('<','\\u003c')
            after=evidence_digest(s)
            if name=='report.html':
                # Moving the scorecard changes table order; all original evidence stays byte-identical.
                assert sorted(before)==sorted(after[:-1]),'Evidence changed in '+name
            else:assert before==after,'Evidence changed in '+name
            (d/name).write_text(enhance_report(str(s),report_dir=d))
            if name!='report.html':
                byid[cid]['sections']=[dict(n=i+1,id=h['id'],title=h.get_text(' ',strip=True),slug=h['id']) for i,h in enumerate(s.select('.wrap h2[id]'))];byid[cid]['speaker_notes']=notes
        mf['chapters']=sorted(mf['chapters'],key=lambda c:c['id']!='overview')
        mf['editorial_version']='bandra-review-v1';mf['editorial_reviewed_at']=stamp;mf['editorial_source']='editorial/bandra-september-2026-review.md';mf['editorial_limits']=['Historical review figures excluded where not source-verifiable.','Distinct transactions, discounts and unbooked seats use reconciled frozen definitions.']
        (d/'manifest.json').write_text(json.dumps(mf,indent=1,ensure_ascii=False))
        pack=json.loads((d/'metrics.json').read_text())
        for c in pack['chapters']:
            c.update({key:byid[c['id']][key] for key in ('title','summary','facts')});c['recs']=[]
        (d/'metrics.json').write_text(json.dumps(pack,ensure_ascii=False,indent=1))
        print('Corrected',rid,'backup',backup/rid)
    print('Existing evidence tables preserved exactly; source snapshots unchanged.')
if __name__=='__main__':main()
