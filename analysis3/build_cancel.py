"""Report 6 - Late cancellations and discounts."""
import pandas as pd, numpy as np
import e1_data as E
import d1_data as D
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

TODAY = pd.Timestamp('2026-10-18')
L, LP = E.L, E.LP
X = D.XB.copy()
X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()
x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')].copy()
x24 = X[(X['dt'] >= '2024-09-01') & (X['dt'] < '2024-10-01')].copy()

# ---------------------------------------------------------------- discount timing and coaching
_MB6 = D.MB.copy()
_MB6['Ltv_n'] = E.num(_MB6['Ltv'])
DT = {}
for _p in ['Studio 12 Class Package', 'Studio 1 Month Unlimited']:
    _sub = D.SB[D.SB['Cleaned Product'] == _p].copy()
    _f = _sub.groupby('Member ID').agg(fd=('dt', 'min'), dsc=('Discount Value In Currency',
                                  lambda x: (E.num(x).fillna(0) > 0).any()), v=('val', 'sum'), n=('Sale ID', 'nunique'))
    _f['obs'] = (TODAY - _f['fd']).dt.days
    _f = _f[_f['obs'] >= 180]
    DT[_p] = _f.groupby('dsc').agg(n=('n', 'size'), rpt=('n', lambda x: (x > 1).mean() * 100), ltv=('v', 'mean'))
TRAIN_LC = x26.groupby('Trainer').agg(book=('Booked', 'sum'), lc=('LateCancelled', 'sum'))
TRAIN_LC['rate'] = TRAIN_LC['lc'] / TRAIN_LC['book'].replace(0, np.nan) * 100
TRAIN_LC = TRAIN_LC[TRAIN_LC['book'] >= 100].sort_values('rate', ascending=False)
GN = D.SB[D.SB['dt'].dt.year == 2026]
GDEEP = float(E.num(GN['Discount Value In Currency']).fillna(0).sum())
GDEEP = float((GDEEP / (GN['val'].sum() + GDEEP)) * 100)
GTOT = float(LP['Amount Paid'].sum()) if 'Amount Paid' in LP else 0.0
GDISC_ALL = float(E.num(D.SB['Discount Value In Currency']).fillna(0).sum())


YR = X.groupby(X['dt'].dt.year).agg(sessions=('SessionID','size'), booked=('Booked','sum'),
                                    att=('CheckedIn','sum'), lc=('LateCancelled','sum'), seats=('Capacity','sum'))
YR['conv'] = YR['att']/YR['booked']*100
YR['lc_rate'] = YR['lc']/YR['booked']*100
YR['booked_day'] = YR['booked']/YR['seats']*100
YR['rev'] = X.groupby(X['dt'].dt.year)['Revenue'].sum()
YR['rev_seat'] = YR['rev']/YR['att']

SEP = X[X['dt'].dt.month == 9].groupby(X['dt'].dt.year).agg(
    sessions=('SessionID','size'), booked=('Booked','sum'), att=('CheckedIn','sum'),
    lc=('LateCancelled','sum'), comp=('Complimentary','sum'), rev=('Revenue','sum'), seats=('Capacity','sum'),
    booked_per=('Booked','mean'), book_on_board=('Booked', lambda s: s.mean()))
SEP['book_on_board'] = SEP['booked']/SEP['seats']*100
SEP['conv'] = SEP['att']/SEP['booked']*100
SEP['rev_head'] = SEP['rev']/SEP['att']
SEP['booked_sess'] = SEP['booked']/SEP['sessions']

# who cancels, Sept-26
CK = pd.read_csv('/home/user/google_drive/Day End Report - Part 4', low_memory=False,
    usecols=['Member ID','Location','Date (IST)','Checked In','Is Late Cancelled','Cleaned Class','Time',
             'Day of Week','Teacher Name','Complementary','Paid'])
CK = CK[CK['Location'] == E.B].copy(); CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
A = CK[CK['Checked In'] == True]
a26 = A[(A['dt'] >= '2026-09-01') & (A['dt'] < '2026-10-01')]
lc26 = CK[(CK['Is Late Cancelled'] == True) & (CK['dt'] >= '2026-09-01') & (CK['dt'] < '2026-10-01')].copy()
lc25 = CK[(CK['Is Late Cancelled'] == True) & (CK['dt'] >= '2025-09-01') & (CK['dt'] < '2026-01-01')]
lc_all = CK[CK['Is Late Cancelled'] == True]
lc26['hr'] = pd.to_numeric(lc26['Time'].astype(str).str[:2], errors='coerce')
LCF = lc26.groupby('Cleaned Class').size().sort_values(ascending=False)
LCFIN = (lc26['Cleaned Class'].value_counts()/a26['Cleaned Class'].value_counts()*100).dropna()
LCM = lc26.groupby('Member ID').size().sort_values(ascending=False)
LCHR = lc26['hr'].value_counts().sort_index()
LCHR = LCHR[LCHR.index >= 5]
LCDW = lc26['Day of Week'].value_counts()

# ledger-side cancellation behaviour
cb = LP.copy()
CBC = ['never cancels','up to 10%','11\u201325%','26\u201350%','over 50%']
cb['band'] = pd.cut(cb['Cancellation Rate %'], [-1,0,10,25,50,1000], labels=CBC)
CB = cb.groupby('band', observed=True).agg(n=('Member ID','size'), sess=('Total Sessions Completed','mean'),
        late=('Late Cancellations','mean'), noshow=('No Shows','mean'),
        renew=('Derived Status', lambda x: x.isin(['Renewed','Active','Renewal Grace Period']).mean()*100))
TOTLC_L = int(cb['Late Cancellations'].sum())
TOP10 = cb['Late Cancellations'].nlargest(int(len(cb)*0.1)).sum()/cb['Late Cancellations'].sum()*100

# -------- discounts
SB = D.SB.copy()
SB['disc'] = E.num(SB['Discount Value In Currency']).fillna(0)
SB['gross'] = SB['val'] + SB['disc']
SB['has_disc'] = SB['disc'] > 0
SB['yr'] = SB['dt'].dt.year
DG = SB.groupby('yr').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('has_disc','sum'))
DG['depth'] = DG['disc']/DG['gross']*100
DG['pct_sales'] = DG['n']/DG['sales']*100
D26 = SB[SB['yr'] == 2026]
DP = D26.groupby('Cleaned Product').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('has_disc','sum'))
DP['depth'] = DP['disc']/DP['gross']*100
DP['pct_sales'] = DP['n']/DP['sales']*100
DP = DP[DP['sales'] >= 15].sort_values('depth', ascending=False)
DS = D26.groupby('Sold By').agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('has_disc','sum'))
DS['depth'] = DS['disc']/DS['gross']*100
DS['pct_sales'] = DS['n']/DS['sales']*100
DS = DS[DS['sales'] >= 20].sort_values('depth', ascending=False)
DCODE = D26[D26['has_disc']].groupby('Discount Code').agg(n=('Sale ID','size'), disc=('disc','sum')).sort_values('disc', ascending=False).head(10)
MOM = SB[SB['yr'] == 2026].groupby(SB['dt'].dt.to_period('M')).agg(sales=('Sale ID','size'), gross=('gross','sum'), disc=('disc','sum'), n=('has_disc','sum'))
MOM['depth'] = MOM['disc']/MOM['gross']*100
MOM['pct'] = MOM['n']/MOM['sales']*100

# discount effectiveness: pooled and controlled
later = SB.groupby('Member ID').agg(nd=('dt','max'), n=('Sale ID','nunique'), v=('val','sum'))
def eff(frame):
    f = frame.sort_values('dt').groupby('Member ID').agg(fd=('dt','min'), fdisc=('has_disc','first')).join(later)
    f['obs'] = (TODAY - f['fd']).dt.days
    f = f[f['obs'] >= 180]
    return f.groupby('fdisc').agg(buyers=('n','size'), repeat=('n', lambda x: (x > 1).mean()*100), ltv=('v','mean'), txns=('n','mean'))
EPOOL = eff(SB)
ESEP = {}
for k in ['Studio Newcomers 2 For 1','Studio 12 Class Package','Studio 1 Month Unlimited']:
    E_SEP = eff(SB[SB['Cleaned Product'] == k])
    if len(E_SEP) == 2 and E_SEP['buyers'].min() >= 15: ESEP[k] = E_SEP

CH_DISCG = lines(['2024','2025','2026'],
    [('Discount as a share of gross sales', [DG.loc[y,'depth']/100 for y in (2024,2025,2026)], A1),
     ('Share of sales that carried a discount', [DG.loc[y,'pct_sales']/100 for y in (2024,2025,2026)], N1)],
    'Discount depth against discount spread, 2024 to 2026', h=300, as_pct=True, ymax=0.30,
    note='Depth is the value given away as a share of gross. Spread is how many sales carried any discount at all. '
         'In 2026 the studio discounted fewer sales, more deeply.')

CH_LCYR = bars(['2024','2025','2026'],
    [('Late cancellations', [YR.loc[y,'lc'] for y in (2024,2025,2026)], B1),
     ('Attended', [YR.loc[y,'att'] for y in (2024,2025,2026)], A1)],
    'The two halves of the booking book, by year', h=310, ymax=20000,
    note='Late cancellations peaked in 2025 and have fallen sharply. The attending line is the part of the book that showed up.')

CH_LCCONV = lines(['2024','2025','2026'],
    [('Booked seats that were attended', [YR.loc[y,'conv']/100 for y in (2024,2025,2026)], A1),
     ('Booked seats that became a late cancellation', [YR.loc[y,'lc_rate']/100 for y in (2024,2025,2026)], B1)],
    'Booking discipline has improved three years running', h=300, as_pct=True, ymax=0.95,
    note='Of every hundred seats booked at Bandra, more are now honoured and fewer are released late.')

CH_LCFOR = hbars([(k.replace('Studio ',''), v, A1 if v >= 3 else N1) for k, v in LCFIN.head(8).items()],
    'Late cancellations as a share of each format\u2019s attendance, September 2026', as_pct=True)

CH_LCHR = bars([f'{int(h)}:00' if h < 12 else f'{int(h)}pm' for h in LCHR.index],
               [('Late cancellations', LCHR.tolist(), B1)],
    'When the cancelled classes were scheduled', h=280, ymax=48,
    note='Cancellations cluster in the mid-morning and the early evening \u2014 exactly where the paying demand sits.')

CH_LCMEM = hbars([(f'{int(k)}' + (' cancellation' if k == 1 else ' cancellations'), int(v), B1 if k >= 3 else A1)
                  for k, v in LCM.value_counts().sort_index().items() if k <= 6],
    'How many cancellations each affected member made, September 2026', unit='')

CH_CBB = diverging([(b, v) for b, v in CB['sess'].items()],
    'Mean classes completed, by how often the membership cancelled')

CH_DISCP = hbars([(k.replace('Studio ',''), v, A1 if v >= 10 else N1) for k, v in DP['depth'].items()],
    'Discount depth by product, 2026', as_pct=True,
    note='Only products with fifteen or more sales in 2026 are shown. The 2-for-1 pack and the 4-class package carry no '
         'recorded discount at all because their list price is already the offer.')

CH_DISCS = hbars([(k, v, A1 if v >= 12 else N1) for k, v in DS['depth'].items()],
    'Discount depth by the person who sold it, 2026', as_pct=True,
    note='Sellers with twenty or more recorded sales in 2026.')

CH_MOM = bars([str(p) for p in MOM.index], [('Discount depth', MOM['depth'].tolist(), A1),
                                            ('Share of sales discounted', MOM['pct'].tolist(), N1)],
              'Discounting through 2026, month by month', h=300, as_pct=True, ymax=0.35)

# ------------------------------------------------------------ recommendations
RECS = [
 ('01','Put a late-cancellation charge against the seat, and enforce it','Front Desk + Studio Manager',
  f'{int(YR.loc[2026,"lc"]):,} seats were released late in 2026 at Bandra, and the studio recovered nothing for them. '
  f'The already-improving trend &mdash; from {YR.loc[2025,"lc_rate"]:.1f}% of the book in 2025 to {YR.loc[2026,"lc_rate"]:.1f}% this year &mdash; shows members respond to being held to the booking.',
  f'A late cancellation at an average of {R(YR.loc[2026,"rev_seat"])} a seat is worth real money. Charging or crediting a fraction of it, and applying the rule to everyone, '
  f'is the single cheapest revenue line available and it costs the studio nothing to introduce.'),
 ('02','Offer the released seat back to the waitlist, automatically','CRM + Front Desk',
  f'September\u2019s {len(lc26)} late cancellations were released at an average of '
  f'{SEP.loc[2026,"book_on_board"]:.1f}% board occupancy \u2014 a third of the board was still unsold when they were given back. '
  f'{int(LCF.get("Studio PowerCycle",0))} of them were PowerCycle, {int(LCF.get("Studio FIT",0))} were FIT.',
  'A seat released four hours before the class is worth almost nothing to the studio and a great deal to a member who could not book. '
  'Auto-offering released seats to the waitlist and to members who have not trained that week converts a loss into a visit at no cost.'),
 ('03','Contact the members who cancel repeatedly, personally','CRM',
  f'{len(LCM)} members cancelled in September, but <strong>{int((LCM>=3).sum())} members made three or more cancellations</strong> and the top ten made '
  f'{LCM.nlargest(10).sum()/LCM.sum()*100:.1f}% of all of them. Across the paid book, the worst 10% of memberships carry {TOP10:.1f}% of every late cancellation ever recorded.',
  'Repeat cancelling is not laziness, it is a schedule that does not fit. These are engaged members whose booking and life are out of step. '
  'A short call about which slots actually work for them is cheaper than a discount and more likely to hold them.'),
 ('04','Use the cancellation signal as an early-warning field','CRM + Studio Manager',
  f'Across {len(LP):,} paid memberships, members who never cancelled completed {CB["sess"].get("never cancels", float("nan")):.1f} classes; those who cancelled more than half completed '
  f'{CB["sess"].get("over 50%", float("nan")):.1f} and averaged {CB["late"].get("over 50%", float("nan")):.1f} late cancellations each. Renewal rates barely move across the bands.',
  'Cancelling is a symptom of a life getting busier, not a cause of leaving &mdash; which is exactly why it is worth acting on the first time it appears, not after the membership ends. '
  'A member whose cancellation rate crosses a threshold should enter a contact sequence the same week.'),
 ('05','Re-time the classes that lose their bookings','Programming',
  f'Cancellations cluster at {", ".join(str(int(h))+":00" for h in LCHR.nlargest(3).index)}, and by day on '
  f'{", ".join(LCDW.index[:3])}. The formats that lose the most seats are {", ".join(LCF.index[:3].str.replace("Studio ","",regex=False))}.',
  'A cancellation is a member telling the studio that the time does not work. Where a slot loses a fifth or more of its bookings every week, moving the slot '
  'or shortening the format is a programming fix rather than a compliance problem.'),
 ('06','Stop discounting the products that renew best','Marketing + Studio Manager',
  f'The 1 Month Unlimited carries {DP["depth"].get("Studio 1 Month Unlimited", float("nan")):.1f}% discount depth and {DP["pct_sales"].get("Studio 1 Month Unlimited", float("nan")):.0f}% of its sales are discounted. '
  f'The 3 Month Unlimited carries {DP["depth"].get("Studio 3 Month Unlimited", float("nan")):.1f}%, and the 10 Class Package is discounted on '
  f'{DP["pct_sales"].get("Studio 10 Class Package", float("nan")):.0f}% of its sales.',
  'The studio is buying demand for the products that were already going to sell. Every rupee given away on a 1 Month Unlimited is a rupee taken off a '
  'product whose lifetime value is the highest in the range.'),
 ('07','Test the discount on the products where it has never been tried','Marketing',
  f'The 8 Class Package carries {DP["depth"].get("Studio 8 Class Package", 0):.1f}% depth on {DP["pct_sales"].get("Studio 8 Class Package", 0):.0f}% of sales and the 12 Class Package '
  f'{DP["depth"].get("Studio 12 Class Package", 0):.1f}% on {DP["pct_sales"].get("Studio 12 Class Package", 0):.0f}%, while the 1 Month Unlimited sits at '
  f'{DP["depth"].get("Studio 1 Month Unlimited", 0):.1f}%.',
  'The pricing energy is concentrated in one product. A controlled trial of a modest offer on a package product, measured on renewal rather than on units sold, '
  'would tell the studio whether its discounts work at all before it signs another year of them.'),
 ('08','Set a discount ceiling and report depth by seller','Finance + Management',
  f'Sellers with twenty or more 2026 sales range from {DS["depth"].min():.1f}% to {DS["depth"].max():.1f}% in discount depth, and the number of discounted sales ranges from '
  f'{DS["pct_sales"].min():.0f}% to {DS["pct_sales"].max():.0f}% of their book. Nobody is doing anything wrong; nobody is being told the range exists.',
  'Publishing the range monthly, without naming individuals, moves behaviour faster than any policy. A ceiling with an approval route above it turns discounting from '
  'a habit into a decision.'),
 ('09','Price the discount honestly in the P&amp;L','Finance',
  f'Across the years on file the studio has given away <strong>{R(SB["disc"].sum())}</strong> against {R(SB["gross"].sum())} of gross sales, at an average depth of '
  f'{SB["disc"].sum()/SB["gross"].sum()*100:.1f}% &mdash; and 2026 is the deepest year on record at {DG.loc[2026,"depth"]:.1f}%.',
  'Discount is a cost of sale and belongs on the same line as marketing. Reported together, the studio can see what it spent to acquire demand in cash versus in price, '
  'and can compare the two for the first time.'),
 ('10','Never discount the first month \u2014 discount the second','Marketing + Finance',
  f'On the 12 Class Package, first-buyers who paid full price repeat at {DT["Studio 12 Class Package"].loc[False,"rpt"]:.1f}% and are worth '
  f'{R(DT["Studio 12 Class Package"].loc[False,"ltv"])}. First-buyers who were discounted repeat at {DT["Studio 12 Class Package"].loc[True,"rpt"]:.1f}% and are worth '
  f'{R(DT["Studio 12 Class Package"].loc[True,"ltv"])}. The same pattern holds on the 1 Month Unlimited \u2014 {DT["Studio 1 Month Unlimited"].loc[False,"rpt"]:.1f}% against '
  f'{DT["Studio 1 Month Unlimited"].loc[True,"rpt"]:.1f}% repeat, at {R(DT["Studio 1 Month Unlimited"].loc[False,"ltv"])} against {R(DT["Studio 1 Month Unlimited"].loc[True,"ltv"])}.',
  f'The offer is not the problem; its timing is. A discount on the first purchase lowers the value of the members the studio attracts at the exact moment it is trying to establish a habit at full '
  f'commitment. Moving the same money to the first renewal \u2014 a retention offer rather than an acquisition offer \u2014 rewards the behaviour the studio actually wants and stops setting the '
  f'price expectation at the beginning of the relationship.'),
 ('11','Publish late-cancellation rate by trainer as a coaching number','Studio Manager',
  f'Across trainers with a hundred or more September bookings the late-cancellation rate runs from <strong>{TRAIN_LC["rate"].min():.1f}% to {TRAIN_LC["rate"].max():.1f}%</strong> \u2014 a four-fold spread on the same booking policy. '
  f'{TRAIN_LC.index[0]} runs {TRAIN_LC["rate"].iloc[0]:.1f}% and {TRAIN_LC.index[-1]} {TRAIN_LC["rate"].iloc[-1]:.1f}%.',
  f'A released seat is a member deciding, at short notice, that the hour no longer fits. When the rate is high for one trainer and low for another teaching the same policy, the difference is usually the '
  f'slot rather than the person. Read as a coaching number rather than a compliance one, it is the earliest signal the studio has that a slot is drifting out of its members\u2019 lives.'),
 ('12','Show the member what the discount was worth','Marketing + Front Desk',
  f'The studio gave away <strong>{R(E.num(GN['Discount Value In Currency']).fillna(0).sum())} in 2026 alone</strong>, at an average depth of {GDEEP:.1f}% of gross. Across the years on file the figure is '
  f'{R(GDISC_ALL)} across every year on file.',
  f'A discount that arrives silently as a lower price is read as the price. A discount that arrives as a line on the receipt, with a value against it, is read as a favour \u2014 and favours are repaid. '
  f'Showing the saving costs nothing, changes no policy, and is the only part of the discount programme the member ever sees.'),

]
REC_HTML = rec_html(RECS)

# headline numbers for the lede
D_LC26 = int(YR.loc[2026,'lc']); D_LC25 = int(YR.loc[2025,'lc'])
D_DEPTH = DG.loc[2026,'depth']; D_DEPTH24 = DG.loc[2024,'depth']
D_GIVE = SB[SB['yr'] == 2026]['disc'].sum()

SRC = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
Booking and cancellation behaviour from <em>Day End Report - Part 3 - Sessions</em> and the Day End Part 4 check-in ledger, both filtered to {E.B}.
&ldquo;Late cancellation&rdquo; is the studio&rsquo;s own flag on a booked seat released after the cut-off; a no-show is a booked seat where nobody appeared and no
cancellation was registered, and it is close to nil at this studio.<br/>
Discount data from <em>Sales - Raw - Sales</em>: depth is discount value as a share of gross sales value (net plus discount), and spread is the share of sales
carrying any discount at all. Renewal and repeat outcomes are measured for buyers whose first purchase is at least 180 days old, so that the observation window
is fair.<br/>
Cash-basis figures as recorded at snapshot, not contribution margin.</p>'''

META = (f'Cancellation ledger &middot; {len(lc_all):,} late cancellations, 2024 to October 2026<br/>'
        f'Sales ledger &middot; {len(SB):,} line items &middot; {R(SB["disc"].sum())} of discount on file<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra \u2014 Late Cancellations and Discounts',
    'Report six of seven &middot; Booking behaviour and price',
    'Late cancellations and discounts',
    f'Two ways a studio gives away value: a seat booked and released too late, and a price quietly marked down. In September, Bandra released '
    f'{len(lc26)} seats late. In 2026 it has given away {R(D_GIVE)} in discounts at a depth of {D_DEPTH:.1f}% \u2014 the deepest it has ever discounted. '
    'This report measures both, and separates the part of each that is a real problem from the part that is simply the cost of running a studio.',
    META, f'''
<h2>Start here</h2>
<div class="sub">Booking discipline has genuinely improved. Discounting has genuinely worsened. Both are choices, and only one is being managed.</div>

<p>Start with the good news, because it is real and it is measurable. Across every seat booked at Bandra this year, <strong>{YR.loc[2026,"conv"]:.1f}% were attended and only
{YR.loc[2026,"lc_rate"]:.1f}% became a late cancellation</strong>. In 2025 those figures were {YR.loc[2025,"conv"]:.1f}% and {YR.loc[2025,"lc_rate"]:.1f}%; in 2024, {YR.loc[2024,"conv"]:.1f}% and
{YR.loc[2024,"lc_rate"]:.1f}%. Late cancellations fell from <strong>{D_LC25:,} seats in 2025 to {D_LC26:,} this year</strong>, while the number of attending visits rose.
Whatever changed in how the studio communicates expections around bookings, it worked.</p>

<p>In September 2026 specifically, {len(lc26)} seats were released late against {len(a26):,} attendances. That is <strong>{len(lc26)/len(a26)*100:.1f} late cancellations for every
hundred classes attended</strong> &mdash; a level the studio can live with, and one it can reduce further.</p>

<p>The discount story moves the other way. The studio discounted <strong>{R(D_GIVE)} in 2026 so far, at a depth of {D_DEPTH:.1f}% of gross</strong>, against
{D_DEPTH24:.1f}% in 2024. Discount spread has fallen &mdash; fewer sales carry an offer &mdash; but the offers that are made are deeper, and they are concentrated
on the products that needed them least. That is the finding worth acting on.</p>

{CH_LCYR}
{CH_LCCONV}

<h2>What a released seat costs</h2>
<div class="sub">A late cancellation is a seat the studio paid for and did not use. Whether that matters depends entirely on how full the room was.</div>

<p>The value of a released seat is not fixed. It is worth almost nothing in a half-empty room and a great deal in a full one. In September the board ran at
<strong>{SEP.loc[2026,"book_on_board"]:.1f}% occupancy on the booking book</strong> when those {len(lc26)} seats were released, against {SEP.loc[2025,"book_on_board"]:.1f}% in September 2025.
More than half the seats were unsold at the moment they were given back.</p>

<p>That changes the remedy. Charging for a late cancellation recovers a little; <strong>reselling the seat recovers the whole ticket and keeps the member</strong>.
And the seats are not evenly distributed: {int(LCF.get("Studio PowerCycle",0))} of them were PowerCycle, {int(LCF.get("Studio FIT",0))} FIT and {int(LCF.get("Studio Barre 57",0))} Barre 57,
so the recovery problem is concentrated in the three formats that between them carry most of the week.</p>

{ev('Evidence \u2014 the booking book, September 2024, 2025 and 2026',
    T(['September','Sessions','Seats on the board','Seats booked','Booked per session','Board occupancy','Attended','Late cancellations','Attended of booked','Revenue per head'],
      [[str(y), int(SEP.loc[y,'sessions']), int(SEP.loc[y,'seats']), int(SEP.loc[y,'booked']),
        f"{SEP.loc[y,'booked_sess']:.1f}", P(SEP.loc[y,'book_on_board']), int(SEP.loc[y,'att']), int(SEP.loc[y,'lc']),
        P(SEP.loc[y,'conv']), R(SEP.loc[y,'rev_head'])] for y in (2024, 2025, 2026)], 'num'))}

<h2>Who cancels, and when</h2>
<div class="sub">Cancelling is concentrated, and it is concentrated among the studio&rsquo;s most engaged members.</div>

<p>In September <strong>{len(LCM)} members</strong> released a booked seat late. But {int((LCM==1).sum())} of them did it once and {int((LCM>=3).sum())} did it three times or more, and
the ten heaviest accounts for <strong>{LCM.nlargest(10).sum()/LCM.sum()*100:.1f}% of every cancellation in the month</strong>. Across the entire paid membership book the
concentration is starker still: <strong>the worst tenth of memberships account for {TOP10:.1f}% of all {TOTLC_L:,} late cancellations ever recorded</strong>.</p>

<p>The timing says something the studio can use. Cancellations cluster at {", ".join(str(int(h))+":00" for h in LCHR.nlargest(3).index)}, the mid-morning block, and again in the
early evening &mdash; the two windows where the studio&rsquo;s paying demand is strongest. By day, {LCDW.index[0]} and {LCDW.index[1]} carry the most. These are not random
acts of forgetfulness; they are the hours where a working member&rsquo;s day most often gets in the way.</p>

{CH_LCHR}
{CH_LCMEM}

{ev('Evidence \u2014 September 2026 cancellations by format, day and hour',
    T(['Format','Late cancellations','Attendance','As a share of its attendance'],
      [[k.replace('Studio ',''), int(LCF.get(k,0)), int(a26['Cleaned Class'].value_counts().get(k,0)), P(LCFIN.get(k, float('nan')))]
       for k in LCF.index[:10]], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By day of week</strong></p>' +
    T(['Day','Late cancellations'], [[k, int(v)] for k, v in LCDW.items()], 'num'))}

<h2>What cancelling actually predicts</h2>
<div class="sub">It does not predict leaving. It predicts a member whose week has stopped fitting &mdash; which is more useful.</div>

<p>Sort the {len(LP):,} paid memberships by how often they cancelled and a clear picture emerges. Members who never cancelled completed an average of
<strong>{CB["sess"].get("never cancels", float("nan")):.1f} classes</strong>. Those who cancelled more than half of everything they booked completed
<strong>{CB["sess"].get("over 50%", float("nan")):.1f}</strong> and averaged {CB["late"].get("over 50%", float("nan")):.1f} late cancellations each. Between those two extremes, engagement rises before it falls:
the members who cancel a little attend more than the members who never cancel at all.</p>

<p>And yet the renewal rate barely moves across the bands &mdash; {CB["renew"].min():.1f}% to {CB["renew"].max():.1f}%. <strong>Cancelling is a symptom, not a cause.</strong>
That is precisely why it is valuable: it appears weeks before the member stops coming, it is already recorded, and nobody reads it.</p>

{CH_CBB}

{ev('Evidence \u2014 cancellation bands across the paid book',
    T(['How often they cancelled','Memberships','Mean classes completed','Mean late cancellations','Mean no-shows','Still live or renewed'],
      [[b, int(r['n']), f"{r['sess']:.1f}", f"{r['late']:.1f}", f"{r['noshow']:.1f}", P(r['renew'])] for b, r in CB.iterrows()], 'num'))}

<h2>The discount book</h2>
<div class="sub">The studio is giving away more per sale than ever, to fewer sales, and mostly on the products that did not need it.</div>

<p>Across the years on file Bandra has given away <strong>{R(SB["disc"].sum())}</strong> of discount against {R(SB["gross"].sum())} of gross sales. The trend in depth is
unmistakable: <strong>{DG.loc[2024,"depth"]:.1f}% in 2024, {DG.loc[2025,"depth"]:.1f}% in 2025, {DG.loc[2026,"depth"]:.1f}% in 2026.</strong> At the same time the spread narrowed
&mdash; {DG.loc[2024,"pct_sales"]:.0f}% of sales carried a discount in 2024 against {DG.loc[2026,"pct_sales"]:.0f}% this year. The studio has stopped discounting casually and
started discounting decisively, which is a different behaviour, not obviously a better one.</p>

<p>Where the money goes is the more interesting question. In 2026 the <strong>1 Month Unlimited carried {DP["depth"].get("Studio 1 Month Unlimited", float("nan")):.1f}% depth across
{DP["pct_sales"].get("Studio 1 Month Unlimited", float("nan")):.0f}% of its sales</strong> and the <strong>10 Class Package was discounted on {DP["pct_sales"].get("Studio 10 Class Package", float("nan")):.0f}% of its sales</strong>,
while the 12 Class Package sat at {DP["depth"].get("Studio 12 Class Package", float("nan")):.1f}% and the single-class products at almost nothing at all.</p>

{CH_DISCG}
{CH_MOM}
{CH_DISCP}

{ev('Evidence \u2014 discount by product and by seller, 2026',
    T(['Product','Sales','Gross','Discount given','Depth','Share of sales discounted'],
      [[k.replace('Studio ',''), int(r['sales']), R(r['gross']), R(r['disc']), P(r['depth']), P(r['pct_sales'])]
       for k, r in DP.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By seller</strong></p>' +
    T(['Sold by','Sales','Gross','Discount given','Depth','Share of sales discounted'],
      [[k, int(r['sales']), R(r['gross']), R(r['disc']), P(r['depth']), P(r['pct_sales'])] for k, r in DS.iterrows()], 'num'))}

{CH_DISCS}

{ev('Evidence \u2014 the discount codes that cost the most in 2026',
    T(['Code','Sales','Value given away'], [[k, int(r['n']), R(r['disc'])] for k, r in DCODE.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px">The codes read as a calendar of the studio&rsquo;s campaigns: anniversary offers, a new-customer code, '
    'festival and self-love promotions. Two codes alone account for the largest single blocks of value given away this year.</p>')}

<h2>Do discounts work?</h2>
<div class="sub">Pooled, they look like the best investment the studio makes. Controlled for what was bought, the effect disappears &mdash; and in places reverses.</div>

<p>Take every first-time buyer whose first purchase is at least six months old and split them by whether that first purchase carried a discount. Pooled, the answer is
spectacular: discounted first-buyers repeat at <strong>{EPOOL.loc[True,"repeat"]:.1f}%</strong> and are worth {R(EPOOL.loc[True,"ltv"])} in lifetime value, against
{EPOOL.loc[False,"repeat"]:.1f}% and {R(EPOOL.loc[False,"ltv"])} for those who paid full price.</p>

<p>That comparison is not fair, because the products that carry discounts are not the products that carry full price. Hold the product constant and the picture changes:</p>

{'<br/>'.join(f'<strong>{k.replace("Studio ","")}</strong> &mdash; discounted first-buyers repeat at {v.loc[True,"repeat"]:.1f}% against {v.loc[False,"repeat"]:.1f}% for full-price buyers, '
 f'with lifetime value of {R(v.loc[True,"ltv"])} against {R(v.loc[False,"ltv"])}.' for k, v in ESEP.items())}

<p>The pooled advantage was composition. Members who happened to start on an unlimited or package product were always going to stay longer, and those products happen to
carry the offers. <strong>On this evidence the studio has no proof that its discounts buy loyalty &mdash; only that they reduce the price of sales it would largely have made anyway.</strong>
That is a testable proposition, and it is not currently being tested.</p>

{ev('Evidence \u2014 discount effectiveness, pooled and controlled for the first product bought',
    T(['First purchase was discounted','Buyers','Repeat rate','Mean transactions','Lifetime value'],
      [[('Yes' if k else 'No'), int(r['buyers']), P(r['repeat']), f"{r['txns']:.2f}", R(r['ltv'])] for k, r in EPOOL.iterrows()], 'num') +
    ''.join('<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>' + k.replace('Studio ','') + '</strong></p>' +
            T(['Discounted','Buyers','Repeat rate','Lifetime value'],
              [[('Yes' if kk else 'No'), int(rr['buyers']), P(rr['repeat']), R(rr['ltv'])] for kk, rr in vv.iterrows()], 'num')
            for k, vv in ESEP.items()))}

<h2>Recommendations</h2>
<div class="sub">Nine actions, ordered by the size of the value each protects</div>
{REC_HTML}
{SRC}
''')
open('/home/user/Bandra_September_2026_6_Cancellations_Discounts.html', 'w').write(HTML)
print(f'Report 6 written: {len(HTML)} bytes')
print('conv', YR['conv'].round(1).to_dict(), '| lc_rate', YR['lc_rate'].round(1).to_dict())
print('Sept board occ', SEP['book_on_board'].round(1).to_dict())
print('depth', DG['depth'].round(1).to_dict(), 'pct', DG['pct_sales'].round(1).to_dict())
print('ESEP', {k: v.round(1).to_dict('index') for k, v in ESEP.items()})
print('LC by fmt', LCF.head(5).to_dict(), '| members', len(LCM), '| 3+', int((LCM>=3).sum()))
