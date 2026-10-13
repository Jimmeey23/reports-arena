from pathlib import Path
from bs4 import BeautifulSoup
import re, html
p=Path('Bandra_September_2026_1_Sales_Performance.html')
raw=p.read_text(); cut=raw.index('<style id="p57-reader-assets">'); content,assets=raw[:cut],raw[cut:]
# Correct overlapping source metrics without touching reader scripts or cohort counts.
content=content.replace('196 transactions','195 distinct transactions').replace('₹7,803','₹7,843').replace('31 of 196 sales','31 distinct sales out of 195').replace('₹15,45,660 of class revenue','₹2,34,491 of illustrative class revenue opportunity')
content=content.replace('Snapshot 18 October 2026','Reconciled 13 October 2026').replace('prepared 18 October 2026','reconciled 13 October 2026')
content=content.replace('▲ −₹100 against last year — essentially flat','▼ ₹60 against the HTML’s prior-year ₹7,903; prior-year definition unverified')
content=content.replace('The average sale actually rose, from ₹7,903 to <strong>₹7,843</strong>, and the median sale rose from ₹1,770 to ₹1,942.','Average order value is <strong>₹7,843</strong> (gross collections / 195 distinct sales). The HTML’s prior-year average is ₹7,903; its median comparison is retained as HTML-only evidence, not verified by the PDF.')
content=content.replace('on 38 sales.','on 73 distinct sales (37 Session and 36 Studio Single Class).')
content=content.replace('Thirteen members bought the worse-value option in September.','Eight distinct sales from eight buyers accounted for 13 units of the 10-class package in September.')
content=content.replace('Two months carry the year: April was up −₹1,05,150 and August up −₹7,76,420. September is the third-weakest month of 2026, and the whole year is within 1.8% of 2025.','April fell ₹1,05,150 and August fell ₹7,76,420 year on year. September is the fifth-lowest gross-collection month of January–September 2026; year-to-date collections are down 1.8%.')
content=content.replace('Transaction size — where 213 sales actually sit','Payment-line size — where 213 contributing rows sit').replace('149 transactions were under ₹2,000 — 70% of all sales','149 payment lines were under ₹2,000 — 70% of contributing rows').replace('3 sales above ₹50,000','3 payment lines above ₹50,000').replace('₹50,242','₹50,243')
content=content.replace('That is the single largest "rep" in the studio.','Shipra Bhika’s ₹4,26,757 exceeds the unattributed block.').replace('larger than any named individual.','below Shipra Bhika’s ₹4,26,757.').replace('across 30 transactions','across 30 payment lines')
content=content.replace('the depth averaged 12.8%','the overall weighted discount rate is 8.7%').replace('Single classes at ₹1,943 each are now the second-largest unit line at 38 sales','Studio Single Class averages ₹2,050 per distinct sale across 36 sales')
content=content.replace('₹1,943','₹2,050').replace('₹1,942</td><td>₹971','₹2,023</td><td>₹1,012').replace('₹971','₹1,012')
content=content.replace('more than anything except how fast they come back','in the historical HTML cohorts; this association does not establish causation')
# The same-month ledger ratio cannot measure unused credits or recognised liabilities.
content=content.replace('it measures how much of what members paid for has not yet been consumed. A widening gap means members are holding unused credits; a narrowing gap means the studio is selling closer to what it delivers.','the same-month ratio compares two different ledgers. It does not measure unused credits, deferred revenue or prepaid liabilities: purchases and attendance can belong to different periods and cohorts.')
s=BeautifulSoup(content,'html.parser'); wrap=s.select_one('.wrap')
def parse(x): return BeautifulSoup(x,'html.parser')
def table(headers,rows):
 return '<div class="source-table"><table class="num"><thead><tr>'+''.join('<th>'+html.escape(str(v))+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def money(v):
 from decimal import Decimal
 n=str(int(round(float(v)))); return '₹'+(n if len(n)<=3 else ','.join([n[:-3][max(0,i-2):i] for i in range(len(n[:-3]),0,-2)][::-1])+','+n[-3:])
def insert_before(id,markup): s.find(id=id).insert_before(parse(markup))
def block(id,title,body): return f'<h2 id="{id}">{title}</h2>'+body
note='''<div class="call" id="source-reconciliation"><h3>Shared-file source of truth</h3><p>Scope: Supreme HQ, Bandra, 1–30 September 2026. The supplied Atlas PDF (pages 1–9) governs overlapping sales metrics; the supplied HTML retains historical, attendance, cohort and salesperson detail absent from the PDF. Where they conflict, the PDF’s explicit distinct-sale and quantity definitions take precedence. No new source data has been substituted.</p><p><strong>195 distinct sales · 210 units · 213 contributing payment rows · 139 unique buyers.</strong> Counts by product/category can overlap; never sum grouped distinct-sale or buyer counts to obtain the overall population. PDF lakh labels remain rounded where no exact value is supplied. HTML-only evidence is identified below.</p></div>'''
s.select_one('.kpis').insert_before(parse(note))
# Replace median headline with source-backed buyer value.
k=s.select('.kpis')[0].select('.kpi'); k[1].select_one('.v').string='195'; k[2].select_one('.l').string='Average order value'; k[3].select_one('.l').string='Revenue per buyer'; k[3].select_one('.v').string='₹11,003'; k[3].select_one('.d').string='Gross collections / 139 unique buyers'
insert_before('start-here','<div class="kpis">'+''.join(f'<div class="kpi"><div class="l">{a}</div><div class="v">{b}</div><div class="d">{c}</div></div>' for a,b,c in [('Net of VAT','₹14,56,626','PDF page 1'),('VAT','₹72,784','Gross less net of VAT'),('Units sold','210','Quantity; not transaction count'),('Deferred balance','₹2,712','PDF-reported balance; not inferred from attendance')])+'</div>')
# Label old grouped line-count tables precisely.
for t in s.find_all('table'):
 heads=[x.get_text() for x in t.select('th')]
 if heads and heads[0] in ['Transaction size','Salesperson','Code']:
  for th in t.select('th'):
   th.string=th.get_text().replace('Transaction size','Payment-line size').replace('Share of sales','Share of payment lines').replace('Average sale','Average payment line').replace('Sales','Payment lines') if th.get_text()!='Salesperson' else 'Salesperson'
 if heads and heads[0]=='Product discounted':
  for row in t.select('tbody tr'):
   if row.select_one('td').get_text()=='Studio 10 Class Package': row.select('td')[1].string='8'
 if heads and heads[0]=='Product' and 'Cost per class' in heads:
  rows=t.select('tbody tr'); rows[0].select('td')[1].string='24'; rows[-1].select('td')[1].string='36'; rows[-1].select('td')[2].string='₹2,050'
# Payment totals: PDF amounts that are rounded remain rounded; exact HTML gross shown with provenance.
for t in s.find_all('table'):
 if t.select_one('th') and t.select_one('th').get_text()=='Payment method':
  t.replace_with(parse(table(['Payment method','Distinct sales','Units','Gross (HTML exact)','Net of VAT (PDF)','VAT','AOV (PDF)','Discount','Payment rows'],[
   ['custom',140,148,'₹8,92,920','₹8.5L','₹42,394','₹6,378','₹63,356',151],['stripe',28,28,'₹3,58,952','₹3.4L','₹17,093','₹12,820','₹57,716',28],['multiple-payment-methods',12,13,'₹1,77,162','₹1.7L','₹8,520','₹14,763','₹17,545',13],['cash',15,21,'₹1,00,377','₹95,601','₹4,777','₹6,692','₹6,591',21]])))
# Replace duplicated payment narrative and outdated code claims.
h=s.find(id='how-the-money-arrived'); sub=h.find_next_sibling('div'); sub.string='Payment methods and discounts, with distinct-sale denominators.'
ps=[]; n=sub.find_next_sibling()
while n and n.name!='h2':
 if n.name=='p': ps.append(n)
 n=n.find_next_sibling()
ps[0].replace_with(parse('<p>Custom accounts for 140 distinct sales and 151 payment rows. Stripe has 28 distinct sales; split payments have 12 and cash has 15. Split payments have the highest average order value at ₹14,763, followed by Stripe at ₹12,820, cash at ₹6,692 and custom at ₹6,378 (PDF page 9). Payment-method labels alone do not establish online, desk or self-service attribution.</p>'))
ps[1].replace_with(parse('<p>Three named codes appear in the supplied register: NC-2026-SHQ, ZAP10 and 20OFFSHQ. NC-2026-SHQ contributes ₹61,129 of discounts and ZAP10 ₹34,880; together ₹96,009. The annual sale’s 20OFFSHQ discount is ₹41,800. A further ₹7,400 discount has no code. Code names do not establish acquisition or retention intent (PDF page 6).</p>'))
for text in s.find_all(string=True):
 if text.parent.name in ['script','style']: continue
 replacements={'custom · 151 sales':'custom · 140 sales','multiple-payment-methods · 13 sales':'split payments · 12 sales','cash · 21 sales':'cash · 15 sales','151 sales worth ₹8,92,920':'140 distinct sales worth ₹8,92,920','Average ticket: Stripe ₹12,820, split payments ₹13,628, custom ₹5,913, cash ₹4,780.':'Average order value: Stripe ₹12,820, split payments ₹14,763, custom ₹6,378, cash ₹6,692.'}
 v=str(text)
 for a,b in replacements.items(): v=v.replace(a,b)
 if v!=str(text): text.replace_with(v)
# Full product register; exact printed values, including source rounding differences.
products=[('Studio 12 Class Package',15,15,259875,247500,12375),('Studio 20 Single Class Package',1,1,31080,29600,1480),('Studio 10 Class Package',8,13,225548,214725,10823),('Studio 8 Class Package',4,4,52460,49960,2500),('Studio 4 Class Package',6,6,41055,39100,1955),('Barre 1 month Unlimited',3,3,44915,42776,2139),('Studio 1 Month Unlimited',12,12,230722,219735,10987),('Barre 3 Month Unlimited',1,1,50243,47850,2393),('Studio 6 Month Unlimited',1,1,102344,97470,4874),('Studio Annual Unlimited',1,1,175560,167200,8360),('Studio Shared 2 Week Unlimited',1,1,13650,13000,650),('Studio 3 Month Unlimited',1,1,49177,46835,2342),('Money Credits',3,3,2712,2712,0),('Studio Newcomers 2 For 1',24,24,48562,46250,2313),('Studio Private Class',1,1,5250,5000,250),('Retail - Other Retail',12,13,2080,1981,99),('Retail - Apparel',2,3,4099,3904,195),('Retail - Consumables',31,34,5175,4929,246),('Session',37,37,111090,105800,5290),('Studio Single Class',36,36,73815,70300,3515)]
insert_before('the-commitmentlength-problem',block('source-performance-register','Source performance register', '<p>PDF pages 2 and 9. Gross, net and VAT retain the source’s independently rounded values. Session gross ₹1,11,090 is derived from category gross ₹1,84,905 less Studio Single Class ₹73,815. Product sales overlap: retail categories illustrate why group counts cannot be added.</p>'+table(['Product','Distinct sales','Units','Gross','Net of VAT','VAT'],[[a,b,c,money(d),money(e),money(f)] for a,b,c,d,e,f in products])+ '<p class="cnote">Full scope total: 195 distinct sales, 210 units, ₹15,29,410 gross, ₹14,56,626 net of VAT and ₹72,784 VAT. Category gross values displayed in the source sum to ₹15,29,410.</p>'))
# Discount denominator footnote.
insert_before('how-the-money-arrived','<div class="call"><p>PDF page 6 reports <strong>36 discounted payment lines</strong>; the HTML reports <strong>31 distinct discounted sales</strong> (15.9% of 195). These are different populations. Discounts are available on 210 of 213 payment lines; the remaining three stay unavailable. Weighted rate = discounts / (gross collections + discounts). Product discount values in the HTML total ₹1,45,209; the PDF displays the total rounded as ₹1.5L.</p></div>')
# Upgrade and member registers.
upgrade=[['Studio 6 Month Unlimited','Studio Annual Unlimited',1,1,'₹1,75,560','₹1,67,200','₹41,800','19.2%'],['Studio 1 Month Unlimited','Barre 3 Month Unlimited',1,1,'₹50,243','₹47,850','₹0','0.0%'],['Studio 4 Class Package','Studio 10 Class Package',2,2,'₹34,965','₹33,300','₹3,700','9.6%'],['Studio 12 Class Package','Studio 20 Single Class Package',1,1,'₹31,080','₹29,600','₹7,400','19.2%'],['Studio 2 Week Unlimited','Studio 1 Month Unlimited',1,1,'₹20,239','₹19,275','₹0','0.0%']]
insert_before('recommendations',block('membership-upgrades','Observed membership upgrades','<p>Six observed upgrade sales by six community members across five transitions (PDF page 7). Upgrades compare the preceding paid purchase of the same type with a longer unlimited plan or larger class package; same-day changes are excluded. The count follows the first payment date of the upgrade, using earlier purchase history.</p>'+table(['Previous plan','Purchased product','Sales','Members','Gross','Net of VAT','Discount','Rate'],upgrade)+'<p>Summing the printed transition amounts gives ₹3,12,087 gross and ₹2,97,225 net of VAT; PDF headline totals are rounded to ₹3.1L and ₹3.0L. Discounts total ₹52,900; weighted rate 14.5%.</p>')+block('annual-private-trackers','Annual and private member purchases',table(['Community member','Purchase month','Product','Sales','Members','Gross','Net of VAT','Discount','Rate'],[['Prachi Ghadge','2026-09','Studio Annual Unlimited',1,1,'₹1,75,560','₹1,67,200','₹41,800','19.2%'],['sonam singh','2026-09','Studio Private Class',1,1,'₹5,250','₹5,000','₹0','0.0%']])+'<p class="cnote">PDF pages 7–8. Annual and private purchases follow payment dates and the active studio scope. The annual purchase is also an upgrade; these registers overlap and must not be added to total sales.</p>'))
# Add PDF monthly complete printed window, retaining lakh precision.
monthly=[('Sept 26',195,210,'₹15.3L','₹14.6L','₹72,784','₹7,843','₹1.5L','8.7%',139),('Aug 26',225,242,'₹22.8L','₹21.7L','₹1.1L','₹10,136','₹1.8L','7.5%',166),('Jul 26',226,261,'₹18.9L','₹18.0L','₹90,687','₹8,360','₹1.8L','8.5%',168),('Jun 26',179,196,'₹14.4L','₹13.7L','₹69,062','₹8,030','₹1.4L','9.1%',136),('May 26',189,211,'₹15.0L','₹14.3L','₹72,132','₹7,946','₹1.4L','8.7%',140),('Apr 26',232,270,'₹27.4L','₹26.1L','₹1.3L','₹11,831','₹6.0L','17.9%',172),('Mar 26',182,192,'₹11.3L','₹10.7L','₹53,722','₹6,193','₹98,370','8.0%',151),('Feb 26',188,199,'₹15.4L','₹14.7L','₹73,950','₹8,189','₹2.3L','13.1%',140),('Jan 26',196,206,'₹20.0L','₹19.1L','₹96,487','₹10,222','₹2.2L','9.8%',166),('Dec 25',172,186,'₹14.4L','₹13.7L','₹67,618','₹8,384','₹1.5L','9.2%',124),('Nov 25',204,226,'₹13.2L','₹12.6L','₹62,758','₹6,462','₹78,334','5.6%',157),('Oct 25',170,201,'₹10.2L','₹9.7L','₹49,249','₹6,000','₹42,978','4.0%',125)]
insert_before('how-september-was-paid-for',block('monthly-source-scorecard','Month-by-month source scorecard','<p>PDF page 5 exposes 12 of its 14 completed months. Only the visible months are reproduced. September versus August: transactions −13.3%, buyers −16.3%, AOV −22.6%; gross collections −32.9% using exact HTML totals. Discount rate rises 1.2 percentage points. Historical lakh values retain PDF precision.</p>'+table(['Month','Sales','Units','Gross','Net of VAT','VAT','AOV','Discount','Rate','Buyers'],monthly)))
# Repair source-only claims, distinguish historical detail, preserve reader.
insert_before('method-and-limitations','<div class="call"><h3>Evidence boundaries and source differences</h3><p>Median sale, first-purchase cohorts, lifetime value, attendance, frequency, repeat buyers, salesperson figures and historical year-on-year/YTD comparisons are retained from the supplied HTML; the PDF does not independently verify them. Salesperson and transaction-size counts in that HTML are payment-line counts (213 total), not distinct sales. The PDF contains no expanded salesperson scorecard and no daily chart values readable from the printed charts; these are not fabricated.</p><p>No failed or voided groups appear in the PDF’s active scope (page 9). This describes the filtered register, not a verified zero across all attempted payments. The PDF’s “membership liabilities” panel lists sales measures, not outstanding unused credits or recognised deferred-revenue liabilities.</p><p>The HTML’s 252-visit illustration equals about ₹2,34,491 at its unrounded observed attendance yield; it is an opportunity scenario, not booked or recoverable revenue. Likewise, the same-month 85% session-to-collections ratio cannot establish that 85% of September purchases were consumed.</p></div>')
for h in s.find_all('h2'):
 # BeautifulSoup resolves duplicated source attributes; anchors now unique.
 if not h.get('id'): h['id']=re.sub(r'[^a-z0-9]+','-',h.get_text().lower()).strip('-')
nav=s.select_one('.toc'); nav.clear(); nav.append(parse('<div class="tocl">Contents</div>'))
for i,h in enumerate(s.find_all('h2'),1): nav.append(parse(f'<a href="#{h["id"]}"><span>{i:02}</span>{html.escape(h.get_text())}</a>'))
# Rescale clipped monthly revenue chart with the actual maximum.
for f in s.select('figure.chart'):
 if f.select_one('figcaption') and f.select_one('figcaption').get_text()=='Monthly cash received, January to September':
  svg=f.find('svg')
  for node in svg.find_all(['path','circle']):
   if node.name=='path': node['d']=re.sub(r'([ML])([\d.]+),(-?[\d.]+)',lambda m:f'{m[1]}{m[2]},{246-(246-float(m[3]))*2200000/3400000:.1f}',node['d'])
   else: node['cy']=f'{246-(246-float(node["cy"]))*2200000/3400000:.1f}'
  labels=['0','8,50,000','17,00,000','25,50,000','34,00,000']
  for node,label in zip([x for x in svg.find_all('text') if x.get('x')=='53'],labels): node.string=label
# Add responsive scrolling for wide evidence tables.
p.write_text(str(s)+'<style>.source-table{overflow-x:auto;margin:0 0 22px}.source-table table{min-width:820px}.source-table th{white-space:normal}.source-table td{font-variant-numeric:tabular-nums}</style>'+assets)
print('Updated',p)
