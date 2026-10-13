"""Shared management-report language and evidence rules."""
from pathlib import Path
import re,json
from bs4 import BeautifulSoup

POLICY = Path(__file__).resolve().parents[1] / 'editorial' / 'language-standard.txt'
def instructions():
    return POLICY.read_text()

TITLES = dict(sales='Sales & Revenue Health', **{'class':'Class Demand & Capacity Utilisation'},
 instructor='Instructor Contribution & Effectiveness', lapse='Membership Health, Retention & Lapse',
 format='Format Performance & Programming Strategy', cancels='Revenue & Capacity Leakage',
 overview='Studio Management Scorecard', leads='Lead Funnel & Acquisition Health',
 behaviour='Member Engagement & Attendance Behaviour')
REPLACEMENTS = {
 'The room is bigger than the demand':'Available Capacity and Attendance Demand',
 'Nobody was lost. Nothing was converted':'Customer Reach and Returning-Member Attendance',
 'The two ways to lose a member':'Product Completion Is Not the Same as Customer Churn',
 'The decline that comes first':'Declining Visit Frequency Is an Earlier Retention Signal',
 'The controlled test':'Like-for-Like Performance: Instructor and Schedule Effects',
 'The league table':'Format Performance Scorecard',
 'The multi-format multiplier':'Cross-Format Participation and Engagement',
 'The file the studio is not working':'Pipeline Hygiene and Actionable Leads',
 'per body in the room':'revenue per attendee',
 'The lowest on the roster':'Lowest recorded utilisation among the instructors assessed',
 'Whose first class becomes a member':'First-Class Conversion by Instructor',
 'Make the trial the only acquisition target':'Make completed trials the primary intermediate conversion milestone',
 'In short':'Performance verdict', 'Start here':'What the numbers reveal',
 'The key takeaway':'What the numbers reveal', 'Executive interpretation':'Commercial implication',
 'What to do with these findings':'Commercial implication',
 'Expected impact':'Success measure', 'Expected Impact':'Success measure',
}
REPLACEMENTS.update(json.loads((POLICY.parent / 'phrase-replacements.json').read_text()))
INVALID = re.compile(r'(?:\bnan\b|\binf\b|·(?:-fold|\s*days|\s*%|\s*at)|additional attendances a month|5,929 additional|₹3\.(?:65|74) crore|85% of what was collected|cost(?:s| the studio)? nothing|Nobody is currently asking|Nothing recovers that money|The studio has no alert|Both are used to decide who gets)', re.I)

def clean_body(body):
    soup=BeautifulSoup(body,'html.parser')
    for node in list(soup.find_all(string=True)):
        if node.parent.name in ('script','style') or node.find_parent(['table','svg']): continue
        text=str(node)
        for old,new in REPLACEMENTS.items(): text=text.replace(old,new)
        text=re.sub(r'the club has met, and lost, [\d,]+ people', 'Historical membership records show product expiry; customer-level churn requires separate identification',text,flags=re.I)
        text=text.replace('1 days','1 day')
        node.replace_with(text)
    # A missing calculation cannot support a narrative sentence. Evidence rows stay intact.
    for p in list(soup.select('p,.cnote,.sub')):
        if p.find(['table','svg','details']) or p.find_parent('table'):continue
        if INVALID.search(p.get_text(' ',strip=True)):p.decompose()
    for p in list(soup.select('p,.cnote,.sub')):
        text=p.get_text(' ',strip=True)
        ranking=re.search(r'(\d+)(?:st|nd|rd|th) out of (\d+)',text)
        span=re.search(r'from (₹[\d,]+) to (₹[\d,]+)',text)
        if (ranking and int(ranking[1])>int(ranking[2])) or (span and span[1]==span[2]):p.decompose()
    for box in list(soup.select('.call,.rec')):
        if not box.get_text(strip=True):box.decompose()
    return str(soup)

def methodology(label,year):
    return f'''<details class="ev p57-methodology"><summary>Reading the Numbers</summary>
<p><strong>Reporting period:</strong> {label}, unless a historical or comparison period is explicitly identified. <strong>Comparison basis:</strong> the same calendar month in {year-1} for year-on-year movements.</p>
<p><strong>Sales revenue:</strong> successful, non-voided transactions attributed to payment date. Distinct transactions are Sale IDs; sale lines are product rows. <strong>Delivered class revenue:</strong> revenue attributed to attended sessions in the class export, a separate measure from sales revenue.</p>
<p><strong>Attendance:</strong> checked-in places, not bookings. <strong>Active attendee:</strong> a distinct individual with at least one attendance. <strong>Utilisation:</strong> total attended places divided by available capacity; rate changes are percentage points.</p>
<p><strong>Memberships:</strong> product expiry, duration, export-state status, attendance continuity and customer-level churn are different measures. Confirm subsequent purchases and attendance before describing customer loss. Usage fields reflect the export, not reconstructed historical month-end outcomes.</p>
<p><strong>Interpretation:</strong> historical findings retain their own period and cohort. Associations do not establish causes. Released seats and unused credits are not automatically lost or additional cash revenue. Proposed targets and hypothetical scenarios are separate from realised performance.</p></details>'''

def apply(M,ch):
    ch['title']=TITLES.get(ch['id'],ch['title'])
    ch['body']=clean_body(ch.get('body',''))+methodology(M.label,M.y)
    for key in ('summary','subtitle','narration'):
        if ch.get(key):ch[key]=BeautifulSoup(clean_body('<p>'+ch[key]+'</p>'),'html.parser').get_text(' ',strip=True)
    # Proposed responses must be measured, not described as guaranteed uplift.
    cleaned=[]
    for rec in ch.get('recs',[]):
        values=list(rec)
        for i in (1,3):
            values[i]=BeautifulSoup(clean_body('<p>'+str(values[i])+'</p>'),'html.parser').get_text(' ',strip=True)
        if not values[1] or not values[3]:continue
        values[4]='Proposed test: compare the same eligible cohort and metric before and after the change. Track attendance, purchasing or conversion as relevant; no uplift or cost saving is assumed.'
        cleaned.append(tuple(values))
    ch['recs']=cleaned
    ch['editorial_version']='management-language-v1'
