"""Refine report narrative and private default cues without changing evidence rows."""
import re,json,math
from html import escape
from bs4 import BeautifulSoup
from engine.design import R

HEADLINES={
 'Start here':'The key takeaway', 'The base is narrowing':'Member count and visit frequency',
 'The base is widening':'Member count and visit frequency','The loyal core halved its frequency':'Regulars are visiting less often',
 'Where the money came from':'Which products drove sales','The commitment-length problem':'Package length and purchased access',
 'Pricing and the product ladder':'What each session credit earns','Trading pattern through the month':'When sales picked up',
 'How the month was paid for':'Basket size and repeat buyers','Who sold it':'The team behind the sales',
 'How the money arrived':'How members paid','Who the money came from':'Who drove the sales',
 'What the first purchase predicts':'First purchases and later activity','What else could explain it':'Other explanations to check',
 'Nobody was lost. Nothing was converted':'Attendance changed with the timetable','What the booking book says':'Bookings, attendance and no-shows',
 'The room is bigger than the demand':'Capacity and attendance','The free seats':'Complimentary attendance',
 'Who a first class brings in':'Newcomers and conversion','When the studio is busy':'The hours members attend',
 'The classes nobody came to':'Sessions with no attendance','The month within the month':'Attendance across the month',
 'How the room pays for itself':'Delivered session revenue','Hosted and partner classes':'Signature partnership experiences',
 'The controlled test':'Comparable sessions','The roster, name by name':'Instructor session patterns',
 'Where the week actually goes':'Sessions by day and time','What happens to the clients':'Member attendance by instructor',
 'The studio\\’s own measure':'Recorded instructor scores','What the studio pays for a session':'Recorded instructor payouts',
 'Whose first class becomes a member':'Newcomer conversion by instructor','The shape of the churn book':'Purchase-cohort status and observation time',
 'The two ways to lose a member':'Purchases with and without recorded attendance','The decline that comes first':'Recorded changes in attendance',
 'Who is winnable':'Unused access and recent attendance','What the lost book cost':'Amounts on memberships marked lapsed',
 'The league table':'Format scorecard','Reach against regularity':'Format reach and repeat visits',
 'The multi-format multiplier':'Members using more than one format','What a devotee is worth':'Attendance and value by format',
 'Where the free seats sit':'Complimentary attendance by format','What a released seat costs':'Released capacity, not booked losses',
 'What cancelling actually predicts':'Cancellation patterns and member activity','The discount book':'Where discounts were recorded',
 'Do discounts work?':'Discounts and subsequent activity','What the memberships look like':'September purchase-cohort status',
 'The acquisition engine':'Newcomers and lead progression','Where the money comes from':'Sales mix',
 'The book that is already sold':'Purchased access and expiry dates','What the data is telling the studio':'Decisions supported by this month',
 'The trial is the gate':'Trials and recorded wins','Speed decides it':'Response times and recorded wins',
 'The follow-up book':'Recorded follow-up activity','Where the leads come from':'Lead sources and outcomes',
 'What leads ask for':'Prospects’ stated interests','The file the studio is not working':'Open leads and follow-up needs',
 'The rhythm of the month':'Visits across the month','The shape of the base':'One-time visitors and regular attendance',
 'Routine and variety':'Preferred times and format variety','What the intro pack does to the numbers':'Newcomer visits after the first session',
 'The underlying tables':'Supporting tables','Executive interpretation':'What to do with these findings',
 'The year in numbers':'Same-month comparisons across years','The month inside the ledger':'Purchase and expiry dates',
}
TOPICS={
 'sales':'Review buyer count, average spend and product mix together before changing pricing.',
 'class':'Review recurring low-attendance sessions by hour and format before changing capacity.',
 'instructor':'Compare similar formats and time slots, and keep session sample sizes visible.',
 'lapse':'Use the dated purchase cohort for follow-up; verify each membership’s current status before contact.',
 'format':'Compare attendance, utilisation and delivered revenue together before changing the format mix.',
 'cancels':'Review release timing and backfill evidence before changing the cancellation policy.',
 'overview':'Track sales, attended visits and repeat attendance separately; give each action a measurable outcome.',
 'leads':'Review open enquiries and missing follow-up records; ask prospects to state their barriers.',
 'behaviour':'Use repeat attendance to identify follow-up needs; ask members about their stated barriers.',
}
CAUTIONS={
 'sales':'Sales revenue is payment receipts. Delivered session revenue describes attended activity; the two totals are not a purchase-usage reconciliation.',
 'class':'Utilisation is total attendances divided by total capacity. It is not the average of individual session percentages.',
 'instructor':'Assigned slots and formats differ. Rankings alone do not establish an instructor effect.',
 'lapse':'Statuses and usage are export-state fields. Observed days through September 30 are not completed membership lifetime; checkpoints without mature purchases are unavailable.',
 'format':'A member may attend several formats; distinct member counts across formats are not additive.',
 'cancels':'Released seats valued at average session revenue are an illustrative opportunity value, not a booked loss.',
 'overview':'Different ledgers measure different activity. Avoid adding sales and delivered session revenue.',
 'leads':'Lead calculations use the report’s complete September snapshot. The original lead CSV and historical month-end outcomes were unavailable for independent verification.',
 'behaviour':'One visit is not confirmed churn. Spend is recorded check-in revenue; preference is observed attendance, not a stated intention.',
}


def chapter_copy(cid,M):
 y=M.y;S=M.sales[y];F=M.room[y];P=M.people[y];L=getattr(M,'lead_fun',{});C=M.core
 p=M.sales.get(y-1,{});dy=(S['cash']/p['cash']-1)*100 if p.get('cash') else None
 def growth(v):return f'{abs(v):.1f}% {"higher" if v>=0 else "lower"}'
 if cid=='sales':return (f'Sales were {growth(dy)} than last September' if dy is not None else 'Sales revenue and buyer activity',f"Sales revenue was {R(S['cash'])} from {S['txn']} distinct sales and {S['buyers']} buyers. Average spend per buyer was {R(S['ticket'])}; recorded item discounts were {S['depth']:.1f}% of sales revenue plus discounts.")
 if cid=='class':return ('Fewer sessions, a higher share of seats filled',f"{F['sessions']} sessions delivered {F['att']:,.0f} attendances across {F['seats']:,.0f} available seats. Utilisation was {F['fill']:.1f}%; average attendance was {F['classavg']:.2f} per session.")
 if cid=='instructor':return ('Read instructor results alongside their slots',f"{len(M.trainers)} instructors delivered the month’s {F['sessions']} sessions. Review recorded attendance, capacity and delivered revenue by instructor, then compare like-for-like hours and formats.")
 if cid=='lapse':return ('Recent purchases need time before retention can be judged',f"{M.led['rows']} memberships were purchased in September, including {M.led['paid']} paid purchases with {R(M.led['cash'])} recorded. The median observed follow-up was {M.median_life:.0f} days through month-end, not a completed lifetime. Thirty-day and longer checkpoints are unavailable for this purchase cohort.")
 if cid=='format':return ('Compare each format on reach, utilisation and revenue',f"{len(M.formats)} formats account for {F['att']:,.0f} attendances and {R(F['rev'])} of delivered revenue. Review each format’s offered seats and session count alongside its attendance.")
 if cid=='cancels':return ('Released seats are capacity to recover',f"{F['lc']:,.0f} late-cancelled seats were recorded against {F['book']:,.0f} bookings: a {F['lc_rate']:.1f}% release rate. {F['noshow']:,.0f} booked seat was neither attended nor late-cancelled. Released capacity is not automatically lost revenue.")
 if cid=='overview':return ('Read sales, seats and regular visits together',f"Sales revenue was {R(S['cash'])}; delivered session revenue was {R(F['rev'])}. {P['members']} community members attended {P['visits']:,} times. The {C['n']} members present in both Septembers made {C['now']:,.0f} visits, compared with {C['prev']:,.0f} last year.")
 if cid=='leads':return ('Trials and follow-ups show where prospects progress',f"{L.get('leads',0)} September enquiries are recorded; {L.get('trial',0)} have a completed trial and {L.get('won',0)} are marked Won. The recorded win rate is {L.get('won_pct',0):.1f}% of all September enquiries. These are snapshot outcomes, not verified September-end statuses.")
 return ('Repeat visits tell the fuller attendance story',f"{P['members']} community members made {P['visits']:,} attended visits, averaging {P['per']:.2f} each. The same {C['n']} returning members made {abs(C['lost']):,.0f} {"fewer" if C['lost']>=0 else "more"} visits than last September ({abs(C['drop_pct']):.1f}%).")


def table_fact(table):
 if table is None:return ''
 headers=[c.get_text(' ',strip=True) for c in table.select('thead th')]
 rows=table.select('tbody tr')
 if not headers or not rows:return ''
 result=[]
 for row in rows[:2]:
  cells=[c.get_text(' ',strip=True) for c in row.find_all('td',recursive=False)]
  if len(cells)!=len(headers) or not cells:continue
  numeric=[(h,c) for h,c in zip(headers[1:],cells[1:]) if re.search(r'\d',c) and c not in ('nan','—','·')]
  if numeric:result.append(cells[0]+': '+', '.join(h.lower()+' '+c for h,c in numeric[:3]))
 return '; '.join(result)+'.' if result else ''


def refine_body(body,cid,M):
 soup=BeautifulSoup(body,'html.parser');notes={};headline,summary=chapter_copy(cid,M)
 headings=list(soup.find_all('h2',recursive=False))
 for h in headings:
  old=h.get_text(' ',strip=True);h.string=HEADLINES.get(old,old)
  siblings=[]
  for n in h.next_siblings:
   if getattr(n,'name',None)=='h2':break
   siblings.append(n)
  elements=[n for n in siblings if getattr(n,'name',None)]
  if old in ('The underlying tables','Method and limitations'):continue
  for el in elements:
   if 'hyp' in el.get('class',[]):el.decompose()
  if old=='What else could explain it':
   text='The available records show associations, not causes. Member-reported reasons, promotion attribution and waitlist or release timing are needed to test explanations.'
  elif old in ('Start here','Executive interpretation'):
   text=summary
  elif cid=='lapse':
   text=table_fact(next((el if el.name=='table' else el.find('table') for el in elements if el.name=='table' or el.name=='details'),None)) or f"This section describes September’s {M.led['rows']} purchases as recorded in the export."
   if 'surv' in old.lower() or old=='The shape of the churn book':text=f"Only the 7- and 14-day checkpoints have eligible September purchases. Thirty-day, six-month and one-year checkpoints are unavailable. The median observed follow-up is {M.median_life:.0f} days through month-end."
  elif old in ('Member count and visit frequency','The member base'):
   pp=M.people.get(M.y-1,{});text=f"{M.people[M.y]['members']} distinct community members attended this September, compared with {pp.get('members','unavailable')} last September. Visits per member were {M.people[M.y]['per']:.2f}, compared with {pp.get('per',0):.2f}."
  elif old in ('The loyal core halved its frequency','The returning core'):
   c=M.core;text=f"The same {c['n']} members made {c['prev']:,.0f} visits last September and {c['now']:,.0f} this September: {abs(c['drop_pct']):.1f}% {"fewer" if c['lost']>=0 else "more"}. This is a same-member comparison, not a churn rate."
  else:
   tables=[el for el in elements if el.name=='table'];text=table_fact(tables[0] if tables else None)
   if not text:
    candidates=[]
    for el in elements:
     if el.name=='p':
      sentence=re.split(r'(?<=[.!?])\s+',el.get_text(' ',strip=True))[0]
      if re.search(r'\d',sentence) and not re.search(r'costs? nothing|will |would |worth |predict|decides|caus|every gym|winnable|surviv|lasts |Day 30|after a year|two years|No of Visits|every name',sentence,re.I):candidates.append(sentence)
    text=candidates[0] if candidates else f"Review the recorded {h.get_text().lower()} below, with each measure’s population and reporting period in view."
  # Retain all quantitative charts, tables and evidence disclosures. Replace
  # unsupported narrative rather than treating rhetorical conclusions as data.
  for el in elements:
   if el.attrs is None:continue
   if el.name=='p' or 'sub' in el.get('class',[]) or 'call' in el.get('class',[]):el.decompose()
  p=soup.new_tag('p');p['class']='p57-section-takeaway';p.string=text;h.insert_after(p)
  if old in ('Start here','Executive interpretation','What else could explain it'):
   q=soup.new_tag('p');q['class']='p57-section-decision';q.string=TOPICS[cid];p.insert_after(q)
   c=soup.new_tag('p');c['class']='p57-section-caveat';c.string=CAUTIONS[cid];q.insert_after(c)
  # Store by numbered heading identity, assigned later by build._sections.
  notes[old]=[f'Lead with: {h.get_text()}',f'Quote: {text}',f'Ask: {TOPICS[cid]}',f'Keep in mind: {CAUTIONS[cid]}']
 for el in soup.find_all(string=re.compile(r'Median life|Lifetime|whole-year figures|full calendar year|Days7|Cash taken')):
  text=str(el).replace('Median life','Median observed days').replace('whole-year figures','same-month comparisons').replace('full calendar year','same calendar month in each year').replace('Cash taken','Sales revenue')
  if 'end date minus purchase date' in text:text='Observed days: elapsed time from purchase to a recorded end within the month, otherwise to September 30. This is right-censored follow-up, not completed lifetime.'
  el.replace_with(text)
 return str(soup),notes


def recommendations(cid):
 return [(1,TOPICS[cid].rstrip('.'),{'sales':'Sales + Finance','class':'Studio Management','instructor':'Instructor Leadership','lapse':'Client Success','format':'Studio Management','cancels':'Studio Operations','overview':'Studio Management','leads':'Sales + Client Success','behaviour':'Client Success'}[cid],CAUTIONS[cid],'Review the same eligible population and metric definition next month. No uplift is assumed.')]
