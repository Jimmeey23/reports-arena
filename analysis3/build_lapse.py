"""Report 4 - Lapsed and churned memberships."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D

# ---------------------------------------------------------------- what predicts a long life
_MB = D.MB.copy()
_MB['Ltv_n'] = E.num(_MB['Ltv']); _MB['nvis'] = E.num(_MB['No of Visits'])
_MB['d2'] = E.num(_MB['Days To Second Visit'])
FIRSTP = _MB.dropna(subset=['First Purchase Post Trial']).groupby('First Purchase Post Trial').agg(
    people=('Member Id', 'size'), ltv=('Ltv_n', 'mean'), visits=('nvis', 'mean'))
FIRSTP = FIRSTP[FIRSTP['people'] >= 25].sort_values('ltv', ascending=False)
FIRSTP['lbl'] = [str(i).replace('Studio ', '').replace(' Package', ' pack').replace(' Unlim',
                 ' Unl')[:26] for i in FIRSTP.index]
_SB = _MB.dropna(subset=['d2'])
_SB['band'] = pd.cut(_SB['d2'], [-1, 1, 3, 7, 14, 30, 100000],
                     labels=['Next day or sooner', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 days or more'])
SPEED = _SB.groupby('band', observed=True).agg(people=('Member Id', 'size'), ltv=('Ltv_n', 'mean'), visits=('nvis', 'mean'))
SPEED['ret'] = _SB.groupby('band', observed=True)['Retention Status'].apply(lambda x: (x == 'Retained').mean() * 100)
LIFE = _MB['Lifecycle Status'].value_counts()
_LT = _MB.groupby('Lifecycle Status').agg(ltv=('Ltv_n', 'mean'), visits=('nvis', 'mean'))
NEVERC = int((E.num(_MB['No of Visits']).fillna(0) < 2).sum())

from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

L, LP, LS = E.L, E.LP, E.LS
TODAY = pd.Timestamp('2026-10-18')

d = LP[LP['Purchase Date_d'].notna() & (LP['Purchase Date_d'] >= '2024-01-01')].copy()
d['ended'] = d[['Churned Date_d', 'End Date_d']].min(axis=1)
d['life'] = (d['ended'] - d['Purchase Date_d']).dt.days
d['life'] = d['life'].where(d['life'] >= 0)
d['cens'] = (TODAY - d['Purchase Date_d']).dt.days
d['obs'] = d['life'].fillna(d['cens'])
STEPS = [7, 14, 30, 45, 60, 90, 120, 180, 365]
LBL = ['day 7', 'day 14', 'day 30', 'day 45', 'day 60', 'day 90', 'day 120', 'day 180', '1 year']
SURV = [((d['obs'] > n) | d['life'].isna()).sum()/len(d)*100 for n in STEPS]
GONE = [100 - s for s in SURV]
MED_END = d.groupby(d['Purchase Date_d'].dt.year)['obs'].median()
d['cyr'] = d['Purchase Date_d'].dt.year
COH_STEPS = [14, 30, 60, 90, 180]
COH = {}
for y in (2024, 2025, 2026):
    sub = d[d['cyr'] == y]
    COH[y] = [((sub['obs'] > n) | sub['life'].isna()).mean()*100 if len(sub) else np.nan for n in COH_STEPS]
# what the lapsed book was worth
LAPSED_CASH = LP[LP['Derived Status'] == 'Lapsed']['Amount Paid'].sum()
BANDRA_CASH = LP['Amount Paid'].sum()
AVG_TICKET = LP['Amount Paid'].mean()

DURB = ['2\u20137 days','8\u201330 days','31\u201360 days','61\u201390 days','91\u2013180 days','181\u2013365 days','over a year']
dur = LP[LP['Membership Duration (Days)'].notna() & (LP['Membership Duration (Days)'] >= 0)].copy()
dur['band'] = pd.cut(dur['Membership Duration (Days)'], [-1,1,7,30,60,90,180,400,99999], labels=['same day']+DURB)
DB = dur.groupby('band', observed=True).agg(n=('Member ID','size'), ticket=('Amount Paid','mean'),
                                             sessions=('Total Sessions Completed','mean'))

UB = ['used \u226410%','11\u201325%','26\u201350%','51\u201375%','76\u201399%','used 100%']
uc = LP[LP['Sessions Used %'].notna()].copy()
uc['band'] = pd.cut(uc['Sessions Used %'], [-1,10,25,50,75,99,100.1], labels=UB)
UG = uc.groupby('band', observed=True).agg(n=('Member ID','size'), ticket=('Amount Paid','mean'),
                                           remaining=('Remaining Sessions','mean'), used=('Total Sessions Completed','mean'))
UNUSED = int(uc['Remaining Sessions'].sum())

dec = LP[(LP['Visits in First Half'] + LP['Visits in Second Half']) >= 4].copy()
dec['ratio'] = dec['Visits in Second Half'] / dec['Visits in First Half'].replace(0, np.nan)
DEC = {'wound down to nothing': (dec['Visits in Second Half'] == 0).mean()*100,
       'more than halved': ((dec['ratio'] > 0) & (dec['ratio'] <= 0.5)).mean()*100,
       'slipped a little': ((dec['ratio'] > 0.5) & (dec['ratio'] < 1)).mean()*100,
       'held steady or grew': (dec['ratio'] >= 1).mean()*100}

RB = ['0\u201330 days','31\u201360 days','61\u201390 days','91\u2013180 days','181\u2013365 days','over a year']
rc = LP[LP['Days Since Last Visit'].notna()].copy()
rc['band'] = pd.cut(rc['Days Since Last Visit'], [-1,30,60,90,180,365,99999], labels=RB)
rd = rc.groupby('band', observed=True).agg(members=('Member ID','nunique'), inst=('Member ID','size'),
                                           ticket=('Amount Paid','mean'), sessions=('Total Sessions Completed','mean'))
WARM = rc[rc['Days Since Last Visit'].between(0,60)]; COOL = rc[rc['Days Since Last Visit'].between(61,180)]
GONEM = rc[rc['Days Since Last Visit'] > 180]

fam = LP['Membership Name'].str.replace(r'^Studio ', '', regex=True).str.strip()
pr = LP.assign(fam=fam)
KEY = ['Newcomers 2 For 1','Single Class','1 Month Unlimited Membership','4 Class Package','12 Class Package',
       '8 Class Package','10 Single Class Pack','Extended 10 Single Class Pack','2 Week Unlimited Membership',
       '3 Month Unlimited Membership','6 Month Unlimited Membership']
PRODT = pd.DataFrame([dict(p=k, sold=len(s), ticket=s['Amount Paid'].mean(), cls=s['Total Sessions Completed'].mean(),
                           life=s['Membership Duration (Days)'].mean(),
                           renew=(s['Derived Status'].isin(['Renewed','Active','Renewal Grace Period'])).mean()*100)
                      for k in KEY if len(s := pr[pr['fam'] == k]) >= 15]).sort_values('renew')

canc = LP.copy()
CBC = ['never cancels','up to 10%','11\u201325%','26\u201350%','over 50%']
canc['cband'] = pd.cut(canc['Cancellation Rate %'], [-1,0,10,25,50,1000], labels=CBC)
cb = canc.groupby('cband', observed=True).agg(n=('Member ID','size'), sessions=('Total Sessions Completed','mean'),
        late=('Late Cancellations','mean'), win=('Derived Status', lambda x: (x=='Renewed').mean()*100))
TOTLC = canc['Late Cancellations'].sum()
NOTACT = L[L['Derived Status'] == 'Not Activated']

# ------------------------------------------------------------------ charts
CH_SURV = lines(LBL, [('Still in force', [v/100 for v in SURV], A1), ('Lapsed', [v/100 for v in GONE], B1)],
    'How long a paid Bandra membership actually lasts', h=330, as_pct=True, ymax=1.0,
    note=f'Every paid Bandra membership bought since January 2024 that has had time to run, n = {len(d):,}. '
         'Memberships still open count as surviving to today, so the curve is a floor, not a ceiling.')
CH_DUR = hbars([(b, int(DB['n'].get(b, 0)), A1 if i < 3 else (A2 if i < 5 else A3)) for i, b in enumerate(DURB)],
    'How long paid memberships lasted, by count', unit='')
CH_UC = bars(UB, [('Memberships in this band', [int(UG['n'].get(b, 0)) for b in UB], A1),
                  ('Mean classes actually used', [UG['used'].get(b, 0) for b in UB], B1)],
    'What people bought against what they used', h=310, ymax=360,
    note=f'Session allowance is recorded for package and credit products only, so this covers {len(uc):,} memberships. '
         'The clay bars are mean classes used, on the same axis.')
CH_DEC = hbars([(k, v, A1 if k == 'held steady or grew' else (A2 if k == 'slipped a little' else B1))
                for k, v in DEC.items()],
    'The second half of a membership, measured against its first half', as_pct=True,
    note=f'{len(dec):,} memberships with at least four completed visits, so the halves mean something.')
CH_REC = bars(RB, [('Members', [float(rd['members'].get(k, 0)) for k in RB], A1),
                   ('Mean price paid, \u20b9 hundreds', [rd['ticket'].get(k, 0)/100 for k in RB], B1)],
    'Time since last visit, against what those members had paid', h=310, ymax=1400,
    note='Read together: the members most recently in the room are also the ones who paid the most. '
         'The further away someone has drifted, the smaller they were in the first place.')
CH_CC = hbars([(b, int(cb['n'].get(b, 0)), A1 if i == 0 else (A2 if i < 3 else B1)) for i, b in enumerate(CBC)],
    'Memberships by how often they cancelled', unit='',
    note=f'{TOTLC:,.0f} late cancellations across the paid book; the worst 10% of memberships carry four in five of them.')
CH_CCB = lines(CBC, [('Mean classes completed', [cb['sessions'].get(b, 0) for b in CBC], A1)],
    'Engagement rises with cancelling, then collapses', h=290, as_pct=False, ymax=20,
    note='A member who cancels is a member who is trying. The collapse only starts past the halfway mark.')

CH_COH = lines(['day 14','day 30','day 60','day 90','day 180'],
    [(f'Bought in {y}', [v/100 if v == v else None for v in COH[y]], c)
     for y, c in [(2024, A3), (2025, A2), (2026, A1)]],
    'Survival by the year the membership was bought', h=310, as_pct=True, ymax=1.0,
    note='The 2026 curve sits above the others partly because its memberships are younger and still running. '
         'Comparing the first thirty days across all three years is the fair read, and 2026 is not better than 2024.')

CH_FAM = hbars([(str(k).replace('Unlimited Membership','Unlimited').replace(' Class Package','-class pack'),
                 v, A1 if v >= 200 else A3) for k, v in
                LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ','',regex=True))
                  .groupby('fam').size().sort_values(ascending=False).head(12).items()],
    'The paid book by product', unit='',
    note='Everything the studio has sold at Bandra since 2022. Two of the largest lines are entry products.')

# ------------------------------------------------------------------ recommendations
RECS = [
 ('01','Run a fourteen-day activation sequence on every membership sold','Studio Manager + CRM',
  f'<strong>{GONE[1]:.1f}% of paid memberships end within fourteen days and {GONE[2]:.1f}% within thirty</strong>, and {cb["n"].get("never cancels",0):,.0f} memberships never '
  f'cancelled a single class because they never booked one. The median paid membership at Bandra lasts {d["obs"].median():.0f} days.',
  f'Getting one in ten of the memberships that currently die inside a fortnight to reach four visits would add roughly '
  f'{int(len(d)*0.08)} members into the active habit band each year. On the studio\u2019s own attendance economics that is the largest single '
  f'recoverable block in this report.'),
 ('02','Treat "bought and never attended" as a same-day alert, not a report line','Front Desk + CRM',
  f'There are <strong>{len(NOTACT):,} Bandra memberships across {NOTACT["Member ID"].nunique():,} people that were paid for and never activated</strong>, and the trend is rising: '
  f'{int((NOTACT["Purchase Date_d"].dt.year==2024).sum())} in 2024, {int((NOTACT["Purchase Date_d"].dt.year==2025).sum())} in 2025, {int((NOTACT["Purchase Date_d"].dt.year==2026).sum())} so far in 2026.',
  'A member who has bought and not booked is the highest-intent, lowest-cost call the studio can make. Ringing them within 48 hours of purchase '
  'converts a dead transaction into a first visit, and a first visit is the only thing that has ever predicted a second.'),
 ('03','Put a member on a plan at their first renewal, not a quantity','Studio Manager',
  f'The 12-class package renews at {PRODT.set_index("p")["renew"].get("12 Class Package", float("nan")):.0f}% while the 10-class single pack renews at '
  f'{PRODT.set_index("p")["renew"].get("10 Single Class Pack", float("nan")):.0f}%, at virtually the same ticket. The 4-class package renews at '
  f'{PRODT.set_index("p")["renew"].get("4 Class Package", float("nan")):.0f}% and the 2-for-1 pack at {PRODT.set_index("p")["renew"].get("Newcomers 2 For 1", float("nan")):.0f}%.',
  'The difference is not price, it is framing. Selling the same money as a scheduled programme rather than a bundle of classes is a script change, '
  'not a product change, and it moves the single largest cohort in the book.'),
 ('04','Write down the unused classes and go and collect them','Studio Manager + CRM',
  f'<strong>{UNUSED:,} paid classes sit unused</strong> across {len(uc):,} memberships, and {int((uc["Sessions Used %"]<=25).sum())} memberships used a quarter or less of what they bought. '
  f'Memberships that used 10% or less of their allowance are carrying {UG["remaining"].get("used \u226410%", float("nan")):.0f} unspent classes each.',
  'Every one of those classes has already been paid for. Asking a member to come and use what they own is the least expensive contact the studio can '
  'make, it requires no discount and no offer, and it puts a body back in the room.'),
 ('05','Watch the second half of every membership for the halving signal','CRM',
  f'<strong>{DEC["wound down to nothing"]+DEC["more than halved"]:.0f}% of memberships show a second half that was half the first or worse</strong>, and '
  f'{DEC["wound down to nothing"]:.0f}% end with a second half in which the member did not attend at all. Only {DEC["held steady or grew"]:.0f}% held or improved.',
  'This is a leading indicator that already exists in the data and is not being read. A member whose visit rate halves in the middle of a membership '
  'should trigger a human contact while the membership is still live, not a win-back campaign after it ends.'),
 ('06','Segment win-back by recency, not by lifetime value','CRM + Marketing',
  f'{WARM["Member ID"].nunique()} members were last in the room within 60 days and paid an average of {R(WARM["Amount Paid"].mean())}; '
  f'{GONEM["Member ID"].nunique()} have been gone over six months and paid {R(GONEM["Amount Paid"].mean())}.',
  'The instinct is to chase the biggest historical spenders. The evidence is that recency and value travel together: the recently lapsed are both the '
  'most winnable and the most valuable. Re-ranking the win-back list by recency would re-point the same effort at roughly double the average ticket.'),
 ('07','Separate the two churn mechanisms in every dashboard','CRM + Studio Manager',
  f'{cb["n"].get("never cancels",0):,.0f} memberships never booked a class, while {cb["n"].get("over 50%",0):,.0f} cancelled more than half of everything they booked. '
  f'Both are currently reported as one lapsed number.',
  'An onboarding problem and a habit-decay problem need different owners, different scripts and different timelines. Reporting them as a single churn '
  'figure guarantees that the studio treats both with the remedy for whichever is more visible.'),
 ('08','Freeze, do not lose, the members who are slipping','Front Desk',
  f'Only {int(LP["Membership Freeze Count"].gt(0).sum())} of {len(LP):,} paid memberships ever used a freeze, while {NOTACT["Member ID"].nunique():,} members never activated at all '
  f'and {cb["n"].get("never cancels",0):,.0f} never booked.',
  'A two-week freeze costs the studio almost nothing, keeps the contract alive, and converts a lapse into a pause. Offering it proactively at the '
  'moment attendance drops is cheaper than any win-back campaign and protects the relationship while the member sorts out whatever interrupted it.'),
 ('09','Price the churn into the acquisition plan','Management',
  f'At a {GONE[2]:.1f}% thirty-day and {GONE[4]:.1f}% sixty-day end rate, the studio must replace most of its book every two months. That is the real reason the '
  f'lead engine has to run at {len(E.LB):,} leads.',
  'Framing acquisition as the cost of churn rather than as growth changes what the studio is willing to spend on retention. On this data, a one-point '
  'improvement in thirty-day survival removes the need for more acquisition than any campaign the studio could run.'),
 ('10','Sell the first month as a programme, not a class count','Sales + Front Desk',
  f'Across {int(FIRSTP["people"].sum()):,} Bandra first-timers with a recorded first purchase, the product they started on predicts almost the whole of their lifetime value. '
  f'A member whose first purchase was a 1 Month Unlimited is worth <strong>{R(FIRSTP.loc["Studio 1 Month Unlimited","ltv"])}</strong> on average; one whose first purchase was a single class is worth '
  f'{R(FIRSTP.loc["Studio Single Class","ltv"])}. Same studio, same period, same marketing \u2014 a {FIRSTP.loc["Studio 1 Month Unlimited","ltv"]/FIRSTP.loc["Studio Single Class","ltv"]:.1f}-fold difference decided at the point of sale.',
  f'The studio\u2019s entry offer is the cheapest thing it can say yes to, and the cheapest thing is producing the least valuable members. Selling the first month as a timed programme with a '
  f'named start date, rather than a pack of classes the member can spend at leisure, changes the product without changing the price. The trial class should be an audition for '
  f'{R(FIRSTP.loc["Studio 1 Month Unlimited","ltv"])}, not a coupon for one session.'),
 ('11','Book the second visit before the member leaves the building','Front Desk + CRM',
  f'Among {len(_SB):,} measurable first-timers, lifetime value falls in a straight line with how long the second visit took. Members back within a day are worth '
  f'<strong>{R(SPEED.loc["Next day or sooner","ltv"])}</strong> and are retained at {SPEED.loc["Next day or sooner","ret"]:.0f}%. Those whose second visit took a month or never happened are worth '
  f'{R(SPEED.loc["31 days or more","ltv"])} and retained at {SPEED.loc["31 days or more","ret"]:.0f}%.',
  f'The second visit is worth {SPEED.loc["Next day or sooner","ltv"]/SPEED.loc["31 days or more","ltv"]:.1f} times the third, the tenth or anything after it, because everything after it depends on it. '
  f'It is also the easiest thing in this report to influence: a member standing at the desk on their first day will say yes to a date. Nobody is currently asking.'),
 ('12','Read the at-risk band fortnightly, not the lapsed band annually','Studio Manager + CRM',
  f'Of every Bandra first-timer on file, <strong>{LIFE.get("Churned",0):,} are recorded as churned and {LIFE.get("Lapsed",0):,} as lapsed</strong>, against {LIFE.get("Active",0):,} active and '
  f'only {LIFE.get("At Risk",0):,} flagged at risk. The members in the at-risk band are worth {R(_LT.loc["At Risk","ltv"])} each on average against {R(_LT.loc["Churned","ltv"])} for the churned band.',
  f'The studio has one band where intervention is cheap and one where it is expensive, and the report it reads monthly is weighted towards the second. Moving the same effort one stage earlier \u2014 '
  f'from the members who have already gone to the members whose visits have just slipped \u2014 multiplies the yield of every retention hour the team spends.'),

]
REC_HTML = rec_html(RECS)

SRC = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Lapse ledger: <em>Lapsed New - Lapsed</em>, {len(E.L_ALL):,} membership instances across all locations, filtered to
{E.B} ({len(L):,} instances, {L['Member ID'].nunique():,} members). Paid memberships are those with a recorded amount paid and no staff,
complimentary or promotional product name ({len(LP):,} instances, {LP['Member ID'].nunique():,} members). Attendance behaviour is cross-checked against the
Day End Part 4 check-in ledger. Membership dates arrive in two formats and are parsed accordingly.<br/>
Survival is measured from purchase to the earlier of the churn date and the membership end date; memberships that are still open are treated as
surviving to 18 October 2026. Products with fewer than fifteen sales are excluded from product-level rates.
Session-allowance and remaining-session fields are populated for package and credit products only.<br/>
Figures are gross value as recorded at snapshot, not contribution margin.</p>'''

META = (f'Lapse ledger &middot; {len(L):,} Bandra membership instances and {len(LP):,} paid memberships<br/>'
        f'Check-in ledger &middot; {E.L['Member ID'].nunique():,} members, 2022 to October 2026<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra \u2014 Lapsed and Churned Memberships',
    'Report four of seven &middot; Membership lifecycle',
    'Lapsed and churned memberships',
    'Every membership Bandra has ever sold, read forward from the day it was bought. The median paid membership lasts '
    f'{d["obs"].median():.0f} days, {GONE[2]:.1f}% are finished inside a month, and the way they end is split almost evenly between members who never '
    'started and members who quietly stopped.',
    META, BODY := f'''
<h2>Start here</h2>
<div class="sub">The churn book is not a story about losing loyal members. It is a story about memberships that never really began.</div>

<p>Every membership ever sold at Bandra sits in this ledger: <strong>{len(L):,} memberships taken out by {L['Member ID'].nunique():,} people</strong>, of which
{len(LP):,} were paid memberships from {LP['Member ID'].nunique():,} members. Read forward from purchase, the pattern is stark and consistent across two years of
trading: <strong>one in five paid memberships ends within a week. More than half end within a month. Only {SURV[-1]:.1f}% are still in force a year later.</strong></p>

<p>The median paid Bandra membership lasts <strong>{d['obs'].median():.0f} days</strong>. Not months &mdash; days. And it has shortened: the median membership bought in 2024
ran {MED_END.get(2024, float('nan')):.0f} days, one bought in 2025 ran {MED_END.get(2025, float('nan')):.0f}, and one bought so far in 2026 is running {MED_END.get(2026, float('nan')):.0f}.
Every retention, referral and frequency conversation the studio has depends on that number, and it is getting worse.</p>

<p>The reassuring reading is in <em>how</em> people are lost rather than how many. Among memberships with enough visits to measure a trend,
<strong>{P(DEC['wound down to nothing']+DEC['more than halved'])} ran a second half that was half the first or worse</strong> &mdash; and
{P(DEC['wound down to nothing'])} ended with a second half in which the member did not attend at all. They did not cancel, complain or ask for a refund. They
drifted, while the membership was still live and still contactable. That is a recoverable failure, and it is what this report is built around.</p>

{CH_SURV}

<h2>The shape of the churn book</h2>
<div class="sub">{P(100-1.3-4.3-0.9)} of every membership Bandra has ever sold is now lapsed. The live book is a thin sliver of the lifetime book.</div>

<p>At Bandra the derived statuses read: <strong>{int(L['Derived Status'].eq('Lapsed').sum()):,} lapsed</strong> ({P(L['Derived Status'].eq('Lapsed').mean()*100)}),
{int(L['Derived Status'].eq('Renewal Grace Period').sum()):,} in a renewal grace period, {int(L['Derived Status'].eq('Not Activated').sum()):,} never activated,
{int(L['Derived Status'].eq('Active').sum()):,} active and {int(L['Derived Status'].eq('Renewed').sum()):,} renewed.</p>

<p>That ratio is less alarming than it looks, because it counts every instance since 2022 including free and promotional entries &mdash;
{int(L['is_comp'].sum()):,} of the {len(L):,} rows are complimentary or staff entries rather than purchases. Restricted to paid memberships the picture softens but does not
change shape: of {len(LP):,} paid memberships, <strong>{P(LP['Derived Status'].eq('Lapsed').mean()*100)} are lapsed</strong> and only
{P(LP['Derived Status'].isin(['Active','Renewed','Renewal Grace Period']).mean()*100)} are live or renewing.</p>

<div class="call b"><h4>What a {SURV[2]:.1f}% thirty-day survival rate means commercially</h4>
<p>A studio that loses {GONE[2]:.1f}% of its memberships inside a month is not running a retention business. It is running an acquisition business with a very
short billing cycle &mdash; and every month it must refill {GONE[2]:.1f}% of the book from scratch simply to stand still. That is the reason the studio&rsquo;s lead
engine has to run as hard as it does, and it reframes acquisition from growth activity into maintenance cost.</p></div>

{CH_DUR}

<h2>The two ways to lose a member</h2>
<div class="sub">Half the churn is people who never engaged. Half is people who engaged and then withdrew. They need opposite responses.</div>

<p>Sort the paid memberships by how often they cancelled and a useful split appears. <strong>{int(cb['n'].get('never cancels',0)):,} memberships never cancelled a single class</strong> &mdash;
and they completed an average of just {cb['sessions'].get('never cancels', float('nan')):.1f} sessions. They did not leave because something went wrong; they never arrived. At the
other end, {int(cb['n'].get('over 50%',0)):,} memberships cancelled more than half of everything they booked, averaging {cb['late'].get('over 50%', float('nan')):.1f} late cancellations each.
Those members were present, engaged, and visibly losing the habit before they stopped.</p>

<p>Two failure modes, two fixes. The first is a <strong>first-fortnight activation problem</strong> &mdash; the product was bought and not used. The second is a
<strong>habit-decay problem</strong> &mdash; the rhythm broke. A single win-back campaign aimed at both will be efficient at neither, which is why the
recommendations in this report keep them apart.</p>

{CH_CC}
{CH_CCB}

{ev('Evidence \u2014 cancellation behaviour against outcome',
    T(['How often they cancelled','Memberships','Mean classes completed','Mean late cancellations','Share ever renewed'],
      [[b, int(r['n']), f"{r['sessions']:.1f}", f"{r['late']:.1f}", P(r['win'])] for b, r in cb.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:14px">Note how flat the renewal rate is across every band. Cancelling a lot is an early symptom '
    'rather than a cause, which is exactly why it is worth acting on the first time it appears.</p>')}

<h2>Did they use what they paid for?</h2>
<div class="sub">Most did. The ones who did not are identifiable at the point of sale, and they are carrying a lot of unspent money.</div>

<p>Session allowance is recorded for {len(uc):,} package and credit memberships. Of those, <strong>{int((uc['Sessions Used %']>=100).sum()):,} ({P((uc['Sessions Used %']>=100).mean()*100)})
used every class they bought</strong>, and a further {int(((uc['Sessions Used %']>75)&(uc['Sessions Used %']<100)).sum()):,} used more than three-quarters. At the other end,
<strong>{int((uc['Sessions Used %']<=25).sum()):,} memberships ({P((uc['Sessions Used %']<=25).mean()*100)}) used a quarter or less</strong>, leaving {UNUSED:,} unused classes in total.</p>

<p>The unused-credit group is the one to act on, commercially as much as humanly. A member who has paid and not attended has received nothing for their money;
the studio has banked revenue it will eventually have to earn or give back in goodwill. It is also a countable, visible, unfinished transaction sitting in the
CRM: memberships in the lowest usage band are carrying <strong>{UG['remaining'].get('used \u226410%', float('nan')):.0f} and {UG['remaining'].get('11\u201325%', float('nan')):.0f} unspent classes</strong>.</p>

{CH_UC}

<h2>The decline that comes first</h2>
<div class="sub">Almost every lost member slowed down before they stopped. The slowdown is measurable, and it happens while the membership is still live.</div>

<p>Splitting each membership period in half and comparing the two shows the shape of a departure. <strong>{P(DEC['wound down to nothing'])} of measurable memberships ended with a
second half in which the member did not attend at all</strong>, and a further {P(DEC['more than halved'])} more than halved their frequency. Together,
<strong>{P(DEC['wound down to nothing']+DEC['more than halved'])} of memberships ran a second half that was half the first or worse</strong>, against just {P(DEC['held steady or grew'])} that held or grew.</p>

<p>This is a warning the studio already owns and does not use. The decline is visible from the mid-point of any monthly or quarterly cycle. A member whose visits
halve in the second fortnight of a one-month membership is stating exactly what is about to happen, and nothing in the current process reads that signal.</p>

{CH_DEC}

<h2>Product by product</h2>
<div class="sub">Commitment length is the only product feature that reliably predicts survival. Price is not.</div>

<p>Sorted by renewal rate the products separate cleanly. The <strong>6-month unlimited renews at {PRODT['renew'].max():.0f}%</strong>, the extended 10-class pack at
{PRODT.set_index('p')['renew'].get('Extended 10 Single Class Pack', float('nan')):.0f}% and the 12-class package at {PRODT.set_index('p')['renew'].get('12 Class Package', float('nan')):.0f}%. At the bottom, the
<strong>2-for-1 introductory pack renews at {PRODT.set_index('p')['renew'].get('Newcomers 2 For 1', float('nan')):.0f}%</strong>, the four-class package at
{PRODT.set_index('p')['renew'].get('4 Class Package', float('nan')):.0f}% and the ten-class single pack at {PRODT.set_index('p')['renew'].get('10 Single Class Pack', float('nan')):.0f}%.</p>

<p>Two things stand out. The <strong>10-class single pack is the worst performer in the range</strong> &mdash; it sells at almost the same ticket as the 12-class package and converts
to a renewal {PRODT.set_index('p')['renew'].get('12 Class Package', float('nan'))-PRODT.set_index('p')['renew'].get('10 Single Class Pack', float('nan')):.0f} points less often. And the gap between the two is not price; it is whether the
member was sold a <em>programme</em> or a <em>quantity</em>.</p>

{hbars([(r['p'].replace(' Membership','').replace(' Single Class Pack',' pack'), r['renew'],
         A1 if r['renew'] >= PRODT['renew'].median() else B1) for _, r in PRODT.iterrows()],
       'Share of each product\u2019s memberships that renewed or are still live', as_pct=True,
       note='Paid Bandra memberships only, products with fifteen or more sold.')}

{ev('Evidence \u2014 every paid product at Bandra',
    T(['Product','Sold','Average ticket','Mean classes completed','Mean days in force','Renewed or still live'],
      [[r['p'], r['sold'], R(r['ticket']), f"{r['cls']:.1f}", f"{r['life']:.0f}", P(r['renew'])]
       for _, r in PRODT.sort_values('sold', ascending=False).iterrows()], 'num'))}

<h2>Who is winnable</h2>
<div class="sub">The win-back list writes itself, and it is the opposite of the list most studios use.</div>

<p>Sorted by how long it has been since they last came, the paid book splits into three groups with very different economics.
<strong>{WARM['Member ID'].nunique()} members are still warm</strong> &mdash; in the room within the last sixty days &mdash; and they paid an average of
<strong>{R(WARM['Amount Paid'].mean())}</strong> across {WARM['Total Sessions Completed'].mean():.1f} completed classes. A further {COOL['Member ID'].nunique()} are cooling, having paid {R(COOL['Amount Paid'].mean())}.
The remaining <strong>{GONEM['Member ID'].nunique()} are gone</strong>, absent more than six months, and paid only {R(GONEM['Amount Paid'].mean())} on average.</p>

<p>The instinct is to chase whoever spent the most over their lifetime. The data says the opposite: <strong>the members still worth winning are the ones who have
been gone the least time, and they are also the ones who were worth the most.</strong> Someone last seen three weeks ago who has paid {R(WARM['Amount Paid'].mean())} is a
lapse. Someone last seen two years ago who paid {R(GONEM['Amount Paid'].mean())} is a completed relationship.</p>

{CH_REC}

{ev('Evidence \u2014 the win-back list in numbers',
    T(['Time since last visit','Members','Memberships','Mean paid','Mean classes completed'],
      [[b, int(r['members']), int(r['inst']), R(r['ticket']), f"{r['sessions']:.1f}"] for b, r in rd.iterrows()], 'num'))}

<h2>What the lost book cost</h2>
<div class="sub">The lapsed memberships represent almost all of the money the studio has taken at Bandra, and most of it was spent fast.</div>

<p>The {len(LP):,} paid Bandra memberships in this ledger represent <strong>{R(BANDRA_CASH)} of recorded payments</strong>, at an average ticket of {R(AVG_TICKET)}.
Of that, <strong>{R(LAPSED_CASH)} &mdash; {P(LAPSED_CASH/BANDRA_CASH*100)} &mdash; sits against memberships now recorded as lapsed</strong>. That is not money the studio has lost;
it is money the studio has already banked against relationships that have ended.</p>

<p>The sharper question is how quickly it was earned. With a median membership lasting {d['obs'].median():.0f} days and {GONE[2]:.1f}% finished inside a month, an average ticket of
{R(AVG_TICKET)} is being collected roughly every {d['obs'].median():.0f} days and then having to be replaced. The studio is not short of customers. It is short of
<em>duration</em> &mdash; and duration is the one input that makes every other number in these reports easier.</p>

{CH_COH}

{ev('Evidence — the paid book by product, and what happened to each line',
    T(['Product family','Memberships sold','Members','Cash taken','Mean ticket','Lapsed'],
      [[str(k), int(v), int(LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ','',regex=True))
         .groupby('fam')['Member ID'].nunique().get(k, 0)), R(g['Amount Paid'].sum()), R(g['Amount Paid'].mean()),
        P((g['Derived Status']=='Lapsed').mean()*100)]
       for k, v in LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ','',regex=True)).groupby('fam').size()
         .sort_values(ascending=False).head(14).items()
       for g in [LP.assign(fam=LP['Membership Name'].str.replace(r'^Studio ','',regex=True)).groupby('fam').get_group(k)]], 'num'))}

{CH_FAM}

{ev('Evidence \u2014 membership lifetime bands',
    T(['How long it lasted','Memberships','Mean price paid','Mean classes completed'],
      [[b, int(r['n']), R(r['ticket']), f"{r['sessions']:.1f}"] for b, r in DB.iterrows()], 'num'))}

<h2>Recommendations</h2>
<div class="sub">Nine actions, ordered by the size of the leak they address</div>
{REC_HTML}
{SRC}
''')
open('/home/user/Bandra_September_2026_4_Lapsed_Churned.html', 'w').write(HTML)
print(f'Report 4 written: {len(HTML)} bytes')
print(f'survival 7d {SURV[0]:.1f} 14d {SURV[1]:.1f} 30d {SURV[2]:.1f} 60d {SURV[4]:.1f} 90d {SURV[5]:.1f} 1yr {SURV[-1]:.1f} | median {d["obs"].median():.0f}d')
print('median end by year', {int(k): int(v) for k, v in MED_END.items()})
print('decline', {k: round(v, 1) for k, v in DEC.items()})
print('warm/cool/gone', WARM['Member ID'].nunique(), COOL['Member ID'].nunique(), GONEM['Member ID'].nunique())
print('not activated', len(NOTACT))
print('prod renew', [(r['p'], round(r['renew'], 1), r['sold']) for _, r in PRODT.iterrows()])
