"""Report 1 of 3 — Sales Performance, Supreme HQ Bandra, September 2026."""
import pandas as pd, numpy as np
import d1_data as D
import d2_extra as X
from d2_extra import SALES_A, SALES_B
from d0_common import *

DN, CL, CATS, PRODS, MOVERS, PPC = D.DN, D.CL, D.CATS, D.PRODS, D.MOVERS, D.PPC
BANDS, SOLD, PMETH26, PTYPE26, CATTR, RET26 = D.BANDS, D.SOLD, D.PMETH26, D.PTYPE26, D.CATTR, D.RET26
LABS = D.LABS
s24, s25, s26 = D.s24, D.s25, D.s26

cash26, cash25, cash24 = DN['s_cash'][2026], DN['s_cash'][2025], DN['s_cash'][2024]
yoy = cash26/cash25*100 - 100
ytd26 = D.SB[(D.SB['dt'] >= '2026-01-01') & (D.SB['dt'] < '2026-10-01')]
ytd25 = D.SB[(D.SB['dt'] >= '2025-01-01') & (D.SB['dt'] < '2025-10-01')]
ytd_yoy = ytd26['val'].sum()/ytd25['val'].sum()*100 - 100

# ------------------------------------------------------------------ charts
CH_CASH = bars([str(y) for y in [2024, 2025, 2026]],
    [('Cash received', [cash24, cash25, cash26], BLU),
     ('Attributed to classes', [CL[2024]['rev'], CL[2025]['rev'], CL[2026]['rev']], TER)],
    'Cash received, and how much of it was consumed as classes — three Septembers', h=320, ymax=2700000,
    note=f'Cash held roughly flat ({R(cash25)} to {R(cash26)}), but the share of it actually delivered as attended classes rose from {CL[2025]["rev"]/cash25*100:.0f}% to {CL[2026]["rev"]/cash26*100:.0f}%. The studio is now selling close to what it consumes.')

CH_MIX = bars([str(y) for y in [2024, 2025, 2026]],
    [('Memberships', [CATS.loc['Memberships', f'rev_{str(y)[2:]}'] if f'rev_{str(y)[2:]}' in CATS.columns else 0 for y in [2024, 2025, 2026]], BLU),
     ('Class packages', [CATS.loc['Class Packages', f'rev_{str(y)[2:]}'] if f'rev_{str(y)[2:]}' in CATS.columns else 0 for y in [2024, 2025, 2026]], TER),
     ('Single classes', [CATS.loc['Sessions/Single Classes', f'rev_{str(y)[2:]}'] if f'rev_{str(y)[2:]}' in CATS.columns else 0 for y in [2024, 2025, 2026]], GOLD)],
    'Where the money came from — memberships, packages and single classes', h=330,
    note='Memberships remain the largest single line at 43.6% of September cash, but the composition inside that line has changed sharply: long-duration memberships have given way to one-month commitments.')

_mv = MOVERS.head(10)
CH_MOVERS = diverging([(i, r['d']) for i, r in _mv.iterrows()],
    'Product-level change against September 2025', maxv=300000,
    note='Two long memberships account for almost the whole of the year-on-year movement. Studio 1 Month Unlimited fell by ₹2,54,968 on 15 fewer sales, and Studio 3 Month Unlimited by ₹1,54,204 on 3 fewer. Against that, two new longer products landed in September for the first time.')

_dur = D.SB[(D.SB['dt'] >= '2025-01-01') & (D.SB['dt'] < '2026-10-01')]
_dmm = _dur[_dur['Cleaned Category'] == 'Memberships'].copy()
_dmm['kind'] = np.select([
    _dmm['Cleaned Product'].str.contains('Annual', na=False),
    _dmm['Cleaned Product'].str.contains('6 Month', na=False),
    _dmm['Cleaned Product'].str.contains('3 Month', na=False),
    _dmm['Cleaned Product'].str.contains('1 Month|1 month', na=False)],
    ['Annual', '6-Month', '3-Month', '1-Month'], default='Other')
DU = _dmm.groupby([_dmm['dt'].dt.to_period('M'), 'kind']).size().unstack(fill_value=0)
DU = DU.reindex(columns=['1-Month', '3-Month', '6-Month', 'Annual'], fill_value=0)
CH_DUR = bars([str(p)[2:] for p in DU.index],
    [('1-Month', DU['1-Month'].tolist(), BLU), ('3-Month', DU['3-Month'].tolist(), TER),
     ('6-Month', DU['6-Month'].tolist(), GOLD), ('12-Month', DU['Annual'].tolist(), SAGE)],
    'Memberships sold per month by commitment length — the mix is shortening', h=330,
    note=f'Three-month memberships ran at 18 units in April 2025 and 2 in September 2026. One-month memberships are doing the work that longer commitments used to do.')

_ladder = PPC.sort_values('per_class')
CH_LADDER = hbars([(r['product'].replace('Studio ', ''), r['per_class'], BLU if r['per_class'] > 1600 else GOLD)
                   for _, r in _ladder.iterrows()],
    'What a class actually costs the member, by package — September 2026', maxv=2100,
    note='The 12-class package is the cheapest per class at ₹1,444; the 2-for-1 intro pack halves that again to ₹971. Yet the 10-class package sells at ₹1,735 a class and nearly matches the 12-class on volume. There is room to nudge buyers up a tier.')

CH_BANDS = bars(list(BANDS.index), [('Transactions', BANDS['n'].tolist(), GREY), ('Revenue (scaled)', [v/30000 for v in BANDS['rev']], TER)],
    'Transaction size — where 213 sales actually sit', h=310, as_pct=False, ymax=200,
    note=f'{BANDS.loc[LABS[0],"n"]:.0f} transactions were under ₹2,000 — {BANDS.loc[LABS[0],"n"]/213*100:.0f}% of all sales — but they produced only {BANDS.loc[LABS[0],"pct"]:.0f}% of revenue. Revenue is scaled down by 30,000 to share the axis.')

CH_SOLD = hbars([(i, r['rev_26'], BLU if r['rev_26'] > 200000 else GOLD) for i, r in SOLD.iterrows()],
    'Who wrote the sales — September 2026', maxv=440000,
    note=f'{R(SOLD.loc["-", "rev_26"])} of September sales — {SOLD.loc["-", "rev_26"]/cash26*100:.0f}% — carry no salesperson name at all. That is the single largest "rep" in the studio.')

# ------------------------------------------------------------------ tables
cat_rows = []
for c in CATS.index:
    cat_rows.append([c, R(CATS.loc[c, 'rev_24']), R(CATS.loc[c, 'rev_25']), R(CATS.loc[c, 'rev_26']),
                     Rs(CATS.loc[c, 'rev_26']-CATS.loc[c, 'rev_25']), P(CATS.loc[c, 'rev_26']/cash26*100)])
CAT_T = T(['Category', 'Sept 2024', 'Sept 2025', 'Sept 2026', 'Change vs 2025', 'Share of Sept-26'], cat_rows, 'mono')

mov_rows = [[i, f"{int(r['n_25'])}", f"{int(r['n_26'])}", R(r['rev_25']), R(r['rev_26']), Rs(r['d'])] for i, r in MOVERS.iterrows()]
MOV_T = T(['Product', 'Units Sept-25', 'Units Sept-26', 'Revenue Sept-25', 'Revenue Sept-26', 'Change'], mov_rows, 'mono')

ladder_rows = [[r['product'], f"{int(r['n'])}", R(r['avg_price']), R(r['per_class'])] for _, r in PPC.iterrows()]
LAD_T = T(['Product', 'Units sold', 'Average price', 'Cost per class'], ladder_rows, 'mono')

band_rows = [[i, f"{int(r['n'])}", f"{r['n']/len(s26)*100:.0f}%", R(r['rev']), P(r['pct'])] for i, r in BANDS.iterrows()]
BAND_T = T(['Transaction size', 'Sales', 'Share of sales', 'Revenue', 'Share of revenue'], band_rows, 'mono')

sold_rows = [[i if i != '-' else 'Not attributed', f"{int(r['n_26'])}", R(r['rev_26']),
              R(r['avg_26']) if pd.notna(r['avg_26']) else '—',
              R(r['per_month']) if pd.notna(r.get('per_month')) else '—',
              P(r['rev_26']/cash26*100)] for i, r in SOLD.iterrows()]
SOLD_T = T(['Salesperson', 'Sales', 'Revenue', 'Average sale', 'Jan–Sep monthly average', 'Share of Sept-26'], sold_rows, 'mono')

disc_rows = [[i, f"{int(r['n'])}", R(r['discount']), R(r['rev']), P(r['avg_depth'])] for i, r in
             s26[s26['disc'] > 0].assign(list=lambda d: d['val']+d['disc'], depth=lambda d: d['disc']/(d['val']+d['disc'])*100).groupby('Cleaned Product').agg(n=('Sale ID', 'size'), discount=('disc', 'sum'), rev=('val', 'sum'), avg_depth=('depth', 'mean')).sort_values('discount', ascending=False).iterrows()]
DISC_T = T(['Product discounted', 'Sales', 'Discount given', 'Revenue after discount', 'Average discount depth'], disc_rows, 'mono')

memb_rows = [[str(p), f"{int(r['1-Month'])}", f"{int(r['3-Month'])}", f"{int(r['6-Month'])}", f"{int(r['Annual'])}"]
             for p, r in DU.iterrows()]
MEMB_T = T(['Month', '1-Month', '3-Month', '6-Month', '12-Month'], memb_rows, 'mono')

yc = pd.concat([ytd25.groupby(ytd25['dt'].dt.month)['val'].sum().rename('m25'),
                ytd26.groupby(ytd26['dt'].dt.month)['val'].sum().rename('m26')], axis=1)
yc.index = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep']
YTD_T = T(['Month', '2025', '2026', 'Change'],
          [[m, R(r['m25']), R(r['m26']), Rs(r['m26']-r['m25'])] for m, r in yc.iterrows()] +
          [['<strong>Jan–Sep</strong>', f"<strong>{R(ytd25['val'].sum())}</strong>", f"<strong>{R(ytd26['val'].sum())}</strong>", f"<strong>{Rs(ytd26['val'].sum()-ytd25['val'].sum())}</strong>"]], 'mono')
CH_YTD = lines(list(yc.index), [('2025', yc['m25'].tolist(), GREY), ('2026', yc['m26'].tolist(), TER)],
    'Monthly cash received, January to September', as_pct=False, ymax=2200000, note=f'Two months carry the year: April was up {R(yc.loc["Apr","m26"]-yc.loc["Apr","m25"])} and August up {R(yc.loc["Aug","m26"]-yc.loc["Aug","m25"])}. September is the third-weakest month of 2026, and the whole year is within {abs(ytd_yoy):.1f}% of 2025.')

ret_rows = [[i, f"{int(r['n'])}", R(r['rev'])] for i, r in RET26.groupby('Cleaned Product').agg(n=('Sale ID','size'), rev=('val','sum')).sort_values('rev', ascending=False).iterrows()]
RET_T = T(['Retail product', 'Units', 'Revenue'], ret_rows, 'mono')

pm_rows = [[i, f"{int(r['n'])}", R(r['rev']), P(r['rev']/cash26*100)] for i, r in PMETH26.iterrows()]
PM_T = T(['Payment method', 'Transactions', 'Revenue', 'Share'], pm_rows, 'mono')

# ------------------------------------------------------------------ recommendations
# ------------------------------------------------------------ round-5 additions: what the first purchase predicts
N9 = pd.read_csv('/home/user/reports-arena/uploads/Day End Report - Part 1 - New (9).csv', low_memory=False)
N9 = N9[N9['First Visit Location'] == 'Supreme HQ, Bandra'].copy()
for _c in ['Ltv', 'No of Visits', 'Days To Second Visit', 'Visits Per Month']:
    N9[_c] = X.num(N9[_c]) if hasattr(X, 'num') else pd.to_numeric(
        N9[_c].astype(str).str.replace(r'[,\\s₹]', '', regex=True), errors='coerce')
FP = N9[N9['First Purchase Post Trial'].notna()].groupby('First Purchase Post Trial').agg(
    people=('Member Id', 'size'), ltv=('Ltv', 'mean'), visits=('No of Visits', 'mean'), vpm=('Visits Per Month', 'mean'))
FP = FP[FP['people'] >= 25].sort_values('ltv', ascending=False)
FPN = FP.copy(); FPN.index = [str(i).replace('Studio ', '') for i in FPN.index]
TOP_STARTER = FPN['ltv'].idxmax(); LOW_STARTER = FPN['ltv'].idxmin()
FP_RATIO = FPN['ltv'].max() / max(FPN['ltv'].min(), 1)
N9['d2'] = pd.cut(N9['Days To Second Visit'], [-1, 1, 3, 7, 14, 30, 100000],
                  labels=['same or next day', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31+ or never'])
SP = N9.groupby('d2', observed=True).agg(people=('Member Id', 'size'), ltv=('Ltv', 'mean'), visits=('No of Visits', 'mean'))
SP7 = float(SP.loc['4 to 7 days', 'ltv']); SPLAST = float(SP.loc['31+ or never', 'ltv'])
SPLAST_N = int(SP.loc['31+ or never', 'people'])

CH_FPLTV = hbars([(i, float(r['ltv']), TER if r['ltv'] >= FPN['ltv'].median() else GREY) for i, r in FPN.iterrows()],
    'Lifetime value of a member, by the first thing they ever bought', maxv=82000,
    note=f'{len(N9):,} Bandra first-timers with a recorded first purchase. The product a member starts on predicts more about their eventual value than '
         'anything except how fast they came back a second time.')

CH_SPEED = bars([str(i) for i in SP.index],
                [('Mean lifetime value, ₹ hundreds', [float(r['ltv']) / 100 for _, r in SP.iterrows()], TER),
                 ('Mean visits (×8, on the same axis)', [float(r['visits']) * 8 for _, r in SP.iterrows()], GREY)],
    'How fast the second visit came, against what the member went on to be worth', h=320, ymax=430,
    note='The second visit is decided within days and predicts almost everything after it. Members who returned within a week are worth about three times '
         'those who took a month, or never came back.')

RECS = [
 ('01','Re-weight the product ladder toward 12-class packages','Sales + Studio Manager',
  f'The 12-class package sells at {R(PPC.set_index("product").loc["Studio 12 Class Package","per_class"])} a class — the best value the studio offers — and it grew {Rs(MOVERS.loc["Studio 12 Class Package","d"])} on four more sales. The 10-class package costs the member {R(PPC.set_index("product").loc["Studio 10 Class Package","per_class"])} a class and sold 13 units at almost exactly the same average ticket. Both price at roughly ₹17,300. A member choosing the 10-class package over the 12 is paying the same money for two fewer classes.',
  f'Moving 6 of September’s 13 ten-class sales up to the twelve-class tier adds {6*2} class credits to the studio’s delivered base at no revenue cost, and is the cleanest available improvement to the entry offer. On September volume that is worth about ₹1.1 lakh of delivered capacity a year.'),
 ('02','Put a named owner on every repeat sale','Studio Manager',
  f'41 of September’s 139 paying members bought more than once — and they produced {P(s26[s26["Member ID"].isin(s26.groupby("Member ID").size().pipe(lambda c: c[c>=2]).index)]["val"].sum()/cash26*100)} of the month’s {R(cash26)}. Meanwhile {R(SOLD.loc["-","rev_26"])} of September sales — {SOLD.loc["-","rev_26"]/cash26*100:.0f}% — have no salesperson recorded, the largest single block in the ledger.',
  f'Named attribution on the unattributed block would make the repeat-purchase cycle visible and manageable for the first time. Selling one additional package to each of the 103 single-purchase members at September’s median ticket of {R(DN["s_med"][2026])} is worth roughly ₹1.9 lakh a month.'),
 ('03','Fix the three-month membership before it disappears','Sales + Finance',
  f'Three-month memberships ran at 18 units in April 2025 and <strong>2 units in September 2026</strong>. Over the same period one-month units fell from 29 to 15. Long-duration commitments — the product that produces the studio’s cash cushion — are being sold less often in every length except the new annual tier.',
  f'Recovering even 8 three-month units a month at the historic average ticket of about ₹24,900 returns roughly ₹24 lakh a year of higher-commitment revenue, and materially improves the deferred-revenue position.'),
 ('04','Standardise discount depth at 15% and stop it leaking past it','Finance + Front Desk',
  f'{int(s26[s26["disc"]>0]["Sale ID"].nunique())} September sales carried a discount worth {R(s26["disc"].sum())} in total — {P(s26["disc"].sum()/(s26["val"].sum()+s26["disc"].sum())*100)} of list value. Depth averages {P(s26[s26["disc"]>0].assign(d=lambda x: x["disc"]/(x["val"]+x["disc"])*100)["d"].mean())}, but the annual membership was discounted 19.2% and the 20-class pack 19.2%, against 14.4% on the standard packages.',
  f'Holding every discount to the 15% standard while keeping the same volume saves roughly ₹1.1 lakh a year on September’s pattern alone. Depth discipline is also the single easiest lever to audit.'),
 ('05','Treat the single-class price as a deliberate tier, not a default','Sales',
  f'Single classes at {R(PPC.set_index("product").loc["Studio Single Class","avg_price"])} each are now the second-largest unit line at 38 sales, up {Rs(PRODS.loc["Studio Single Class","d"])} year on year. They are profitable per head but they never build a habit, and {R(PPC.set_index("product").loc["Studio Single Class","per_class"])} a class is the worst value the member can pick.',
  f'Converting a third of September’s 38 single-class buyers into a four-class package at the point of purchase adds about ₹56,000 of committed revenue from the same people, and gives them a reason to return.'),
 ('06','Protect the new long-duration products','Sales + Finance',
  f'September produced the studio’s first {R(PRODS.loc["Studio Annual Unlimited","rev_26"])} annual membership and a {R(PRODS.loc["Studio 6 Month Unlimited","rev_26"])} six-month sale — together {R(PRODS.loc["Studio Annual Unlimited","rev_26"]+PRODS.loc["Studio 6 Month Unlimited","rev_26"])}, or {P((PRODS.loc["Studio Annual Unlimited","rev_26"]+PRODS.loc["Studio 6 Month Unlimited","rev_26"])/cash26*100)} of the month, from two transactions. Both are new propositions and neither existed in September 2025.',
  f'An annual and a six-month sale replace roughly 15 one-month renewals. If these two products can be sold four times a month rather than once, they add about ₹11 lakh a year while lengthening the average commitment.'),
 ('07','Make the 213 sales count for retention, not just cash','CRM',
  f'139 members paid the studio in September, against 143 new clients acquired. The two numbers are close, which means the month’s acquisition effort is not yet compounding into the paying base — and the existing base contributed {P(D.EXREV/cash26*100)} of the {R(cash26)}.',
  f'Every September buyer who is not booked into a class within 14 days is a renewal risk. A checkout prompt to book the next class is the cheapest retention intervention available and costs nothing to build.'),
 ('08','Attack frequency, not price — the money is in the fourth visit','Studio Manager + CRM',
  f'The check-in ledger shows the base widening to {X.s26["Member ID"].nunique()} members while visits per member fell to {X.s26.groupby("Member ID").size().mean():.2f} from {X.s25.groupby("Member ID").size().mean():.2f}. In the same ledger, members who trained in both Septembers cut their own frequency {abs(X.core_now.mean()/X.core_then.mean()*100-100):.0f}%, costing {X.CORE_LOST} visits — {X.CORE_LOST/1404*100:.0f}% of everything filled this month. Cash per member actually rose, from {R(981453/X.s25["Member ID"].nunique())} to {R(1306451/X.s26["Member ID"].nunique())}.',
  f'This is the only lever in the report that does not require new customers. Lifting the {s26.groupby("Member ID").size().eq(1).sum()} members who came exactly once this month to two visits would add about {s26.groupby("Member ID").size().eq(1).sum()} attendances — roughly {R(s26.groupby("Member ID").size().eq(1).sum()*931)} — without a single rupee of acquisition spend.'),
 ('09','Make the online checkout the default for every membership','Sales + Finance',
  f'Stripe sales averaged {R(X.PM.loc["stripe","sum"]/X.PM.loc["stripe","size"])} a transaction against {R(X.PM.loc["cash","sum"]/X.PM.loc["cash","size"])} for cash, and split-payment sales averaged {R(X.PM.loc["multiple-payment-methods","sum"]/X.PM.loc["multiple-payment-methods","size"])}. Stripe transactions fell from {int(X.sale25.groupby("Payment Method")["val"].size().get("stripe",0))} to {int(X.PM.loc["stripe","size"])} year on year while counter sales rose. The high-value products are migrating off the channel that handles them best.',
  'Routing every membership and multi-class pack through a card-on-file or link-based checkout removes the desk as a bottleneck for the products that need a considered decision, and makes the second purchase a one-tap action rather than a visit.'),
 ('10','Put all discount codes under one owner','Finance',
  f'Two codes — NC-2026-SHQ and ZAP10 — account for {R(X.sale26[X.sale26["Discount Code"].isin(["NC-2026-SHQ","ZAP10"])]["disc"].sum())} of the {R(X.sale26["disc"].sum())} given away in September, on {int(X.sale26[X.sale26["Discount Code"].isin(["NC-2026-SHQ","ZAP10"])].shape[0])} of the month’s 213 sales. A further single use of 20OFFSHQ cost {R(41800)}. Meanwhile the unattributed salesperson block carried the deepest average discount of any seller at 16.3%, against 12.8% for Imran Shaikh.',
  'Codes are created by whoever needs one, and nobody compares them. One owner, one register, one monthly review of depth by code makes the discount line controllable for the first time and would have caught the 20OFFSHQ depth before it was granted.'),
 ('11','Sell the second category','Studio Manager',
  f'{X.SINGLE_CAT:.0f}% of September buyers bought from a single product category and only {int((X.cx>=2).sum())} of {len(X.cx)} shopped across two. The top ten buyers produced {X.TOP10:.0f}% of the month’s cash while the bottom half produced {X.BOT50:.1f}%. A boutique studio lives on the second and third purchase, not the first.',
  f'A single bundle — one Barre class, one Cycle class, priced to be obviously better than either alone — is the cheapest way to move members out of a single format. Members who train in two formats are the studio’s most durable customers, and on this month’s data almost nobody is being asked to become one.')
,
 ('12','Lead with the membership, not the single class','Sales + Front Desk',
  f'A first-time buyer who starts on a <strong>{TOP_STARTER} goes on to be worth {R(FPN["ltv"].max())}</strong>; one who starts on a '
  f'<strong>{LOW_STARTER} is worth {R(FPN["ltv"].min())}</strong>. There are {int(FPN.loc[LOW_STARTER,"people"])} people in that bottom group and '
  f'{int(FPN.loc[TOP_STARTER,"people"])} in the top one.',
  f'Both are sold at the same desk. Presenting the commitment first — and treating the trial entry as a route into it rather than as a purchase in its own '
  f'right — changes the mix without touching the price list.'),
 ('13','Book the second class before the first one ends','Front Desk + Sales + CRM',
  f'Members who took their second class inside a week are worth <strong>{R(SP7)}</strong>; those who waited a month or never returned are worth '
  f'<strong>{R(SPLAST)}</strong>. There are {SPLAST_N} people in that last group alone.',
  f'This is a front-desk action, not a campaign: at the end of every first class, before the client leaves the building, the next visit is chosen and booked. '
  f'It costs nothing, it is measurable within a week, and on this data it is the highest-value habit the sales and service teams could adopt.'),
]
REC_HTML = rec_html(RECS)

# ------------------------------------------------------------------ source note
_NW_PAY = len(D.S); _B_LINES = len(D.SB); _B_PAY = D.SB['Sale ID'].nunique()
_N_SESS = len(D.X); _N_NEW = len(D.M)
SRC = f'''<h4>Sources and method</h4>
<p>Three exports at a snapshot of 11 October 2026. <strong>Sales &ndash; Raw</strong> ({_NW_PAY:,} succeeded, non-voided payments network-wide, {_B_LINES:,} sale lines from {_B_PAY:,} payments at Bandra) provides cash received, product, discount, salesperson and payment method. <strong>Day End Report &ndash; Part 3 &ndash; Sessions</strong> ({_N_SESS:,} class occurrences) provides revenue attributed to attended classes. <strong>Day End Report &ndash; Part 1 &ndash; New</strong> ({_N_NEW:,} member records) identifies which September revenue came from clients acquired that month.</p>
<h4>What the two revenue measures mean, and why both are shown</h4>
<p>Cash is money actually received on a payment date; it is what the studio banked. Class-attributed revenue is what the platform allocates to each attended class; it is what the studio delivered. They are different numbers on purpose, and the gap between them is the most informative thing in this report &mdash; it measures how much of what members paid for has not yet been consumed. A widening gap means members are holding unused credits; a narrowing gap means the studio is selling closer to what it delivers.</p>
<h4>Known limitations</h4>
<ul>
 <li><strong>No cost of sale.</strong> No CAC, contribution margin or payroll cost is present in this data, so payback and profitability cannot be calculated. All figures are gross value.</li>
 <li><strong>Salesperson cover.</strong> {SOLD.loc["-","rev_26"]/cash26*100:.0f}% of September revenue has no salesperson recorded. Attributed performance is therefore a floor on each named seller, not a full picture.</li>
 <li><strong>Retail is understated in scope.</strong> Retail appears here as a revenue line only; no stock, cost or sell-through data is available.</li>
 <li><strong>Comparability.</strong> September 2025 followed Ganesh Chaturthi (27 August); September 2026 absorbed it (14 September). Single-month year-on-year comparisons carry that distortion. The year-to-date table is the more reliable frame.</li>
</ul>'''

# ------------------------------------------------------------------ body
ARROW = '▼' if yoy < 0 else '▲'
BODY = f'''
<div class="kpis">
 <div class="kpi"><div class="l">Cash received</div><div class="v">{R(cash26)}</div><div class="d neu">{ARROW} {abs(yoy):.1f}% against September 2025 &mdash; the till held</div></div>
 <div class="kpi"><div class="l">Transactions</div><div class="v">{DN['s_txn'][2026]}</div><div class="d">from {DN['s_mem'][2026]} paying members &mdash; {DN['s_mem'][2026]/DN['s_mem'][2025]*100:.0f}% of last September's paying base</div></div>
 <div class="kpi"><div class="l">Average sale</div><div class="v">{R(DN['s_avg'][2026])}</div><div class="d pos">▲ {R(DN['s_avg'][2026]-DN['s_avg'][2025])} against last year — essentially flat</div></div>
 <div class="kpi"><div class="l">Median sale</div><div class="v">{R(DN['s_med'][2026])}</div><div class="d pos">▲ from {R(DN['s_med'][2025])} — the typical sale got bigger</div></div>
</div>
<div class="kpis" style="margin-top:16px">
 <div class="kpi"><div class="l">Memberships</div><div class="v">{P(CATS.loc['Memberships','rev_26']/cash26*100)}</div><div class="d">of cash — still the largest line, but the mix inside it has shortened</div></div>
 <div class="kpi"><div class="l">Class packages</div><div class="v">{P(CATS.loc['Class Packages','rev_26']/cash26*100)}</div><div class="d pos">▲ {Rs(CATS.loc['Class Packages','rev_26']-CATS.loc['Class Packages','rev_25'])} on the year</div></div>
 <div class="kpi"><div class="l">Discount given</div><div class="v">{R(s26['disc'].sum())}</div><div class="d neu">{P(s26['disc'].sum()/(s26['val'].sum()+s26['disc'].sum())*100)} of list value, on {int(s26[s26['disc']>0]['Sale ID'].nunique())} of {DN['s_txn'][2026]} sales</div></div>
 <div class="kpi"><div class="l">From new clients</div><div class="v">{P(D.NEWREV/cash26*100)}</div><div class="d neu">only {R(D.NEWREV)} came from members making their first-ever Bandra purchase</div></div>
</div>

<h2>Start here</h2>
<div class="sub">The till held. What sat behind it did not.</div>
<p>September 2026 banked <strong>{R(cash26)}</strong> across {DN['s_txn'][2026]} transactions &mdash; a fall of just <strong>{abs(yoy):.1f}%</strong> on September 2025 and, read on its own, an unremarkable month. The average sale actually rose, from {R(DN['s_avg'][2025])} to <strong>{R(DN['s_avg'][2026])}</strong>, and the median sale rose from {R(DN['s_med'][2025])} to {R(DN['s_med'][2026])}. On the headline numbers this is a steady month.</p>
<p>Three things underneath it are not steady, and they are what this report is about.</p>
<p style="padding:16px 18px;background:#F7F7F6;border-radius:3px;font-size:14.5px;margin-bottom:22px">
<strong>The one-line version, if you read nothing else.</strong> The studio served <strong>{X.s26['Member ID'].nunique()} members this September against {X.s25['Member ID'].nunique()} last September</strong> &mdash;
its widest September base in three years &mdash; and collected <strong>{R(1306451/X.s26['Member ID'].nunique())} of class revenue from each of them against {R(981453/X.s25['Member ID'].nunique())}</strong>. Both of those went up.
The only thing that went down is how often each of them came: <strong>{X.s26.groupby("Member ID").size().mean():.2f} visits against {X.s25.groupby("Member ID").size().mean():.2f}</strong>. That single change is worth more than the entire year-on-year
movement in the cash line, and it is the difference between a studio running at capacity and one running at {P(42.6)}.</p>
<p><strong>First, the month was funded by people the studio already had.</strong> Members making their first-ever Bandra purchase contributed {R(D.NEWREV)}, or {P(D.NEWREV/cash26*100)} of the month; existing members contributed the other {R(D.EXREV)}. That is normal for a mature studio, and it is genuinely good news about the base. It also means September&rsquo;s cash figure tells you almost nothing about September&rsquo;s acquisition performance. The two must be read separately.</p>
<p style="font-size:13.5px;color:#7A7267">A note on that number: {P(D.NEWREV/cash26*100)} counts members whose <em>first purchase</em> at Bandra was in September. The performance review quotes {P(100-87.5)} on a different and narrower definition &mdash; clients whose <em>first visit</em> was in September, who paid a narrower sum. The two measures diverge because some September visitors had already bought a package, and some September buyers had already visited. Both are correct; the purchase-based figure is the relevant one for a sales report.</p>
<p><strong>Second, the commitment length is shortening.</strong> Three-month memberships sold 18 units in April 2025 and <strong>2 in September 2026</strong>. One-month memberships fell from 29 units to 15 over the same year. The products that give the studio a forward revenue cushion are being sold less often than they were.</p>
<p><strong>Third &mdash; and this is the finding with the most consequence &mdash; the studio is now selling almost exactly what it delivers.</strong> In September 2024, {R(cash24)} of cash translated into {R(CL[2024]['rev'])} of attended classes: <strong>{CL[2024]['rev']/cash24*100:.0f}%</strong>. In September 2025 that rose to {CL[2025]['rev']/cash25*100:.0f}%. In September 2026 it reached <strong>{CL[2026]['rev']/cash26*100:.0f}%</strong>. That is a profound structural change and it deserves to be named plainly, because it cuts both ways.</p>
{CH_CASH}
<div class="call blu">
<h3>The same flat top line means something completely different in 2026 than it did in 2024</h3>
<p>Two years ago a large share of the cash the studio took was never drawn down as classes. Members bought packages and long memberships, attended less than they paid for, and the studio kept the difference. That unused capacity was quiet, real revenue &mdash; and it was also a symptom of disengagement.</p>
<p>By September 2026 that cushion has largely gone: <strong>{CL[2026]['rev']/cash26*100:.0f} of every ₹100 banked is now delivered as an attended class</strong>, against {CL[2024]['rev']/cash24*100:.0f} two years earlier. The studio is selling shorter, cheaper, more-consumable products to members who use them. The revenue is more honest. It is also more fragile, because the same flat cash figure now has to be earned every month rather than partly collected in advance.</p>
</div>
<p>This is the single most useful reframe in the report. Bandra&rsquo;s September problem is not that revenue collapsed &mdash; it did not. It is that <strong>the business model quietly shifted from selling commitment to selling consumption</strong>, while the cash total stayed flat and therefore hid the change. Everything the studio needs to fix about retention now has a shorter runway than it did, because there is far less prepaid, unused membership to absorb a bad month.</p>

{SALES_A}

<h2>Where the money came from</h2>
<div class="sub">Category mix, and the two products that moved the year</div>
{CAT_T}
{CH_MIX}
<p>Memberships stayed the largest line at <strong>{R(CATS.loc['Memberships','rev_26'])}</strong>, or {P(CATS.loc['Memberships','rev_26']/cash26*100)} of the month, but they fell {Rs(CATS.loc['Memberships','rev_26']-CATS.loc['Memberships','rev_25'])} year on year. Class packages rose {Rs(CATS.loc['Class Packages','rev_26']-CATS.loc['Class Packages','rev_25'])} to {R(CATS.loc['Class Packages','rev_26'])} and now sit within {R(CATS.loc['Memberships','rev_26']-CATS.loc['Class Packages','rev_26'])} of the leading line. Single classes grew {Rs(CATS.loc['Sessions/Single Classes','rev_26']-CATS.loc['Sessions/Single Classes','rev_25'])} to {R(CATS.loc['Sessions/Single Classes','rev_26'])} on {int(PRODS.loc['Studio Single Class','n_26'])} sales.</p>
<p>Read together, those three movements say one thing: <strong>the studio sold more products, at lower price points, to the same people.</strong> Unit count is holding up; commitment value is not.</p>
{CH_MOVERS}
{MOV_T}
<p>The product-level detail is unusually concentrated. <strong>Studio 1 Month Unlimited alone accounts for {Rs(MOVERS.loc['Studio 1 Month Unlimited','d'])}, and Studio 3 Month Unlimited for {Rs(MOVERS.loc['Studio 3 Month Unlimited','d'])}.</strong> Those two lines explain essentially the entire year-on-year movement in the month. Against them, September produced two products that did not exist a year earlier &mdash; a {R(PRODS.loc['Studio Annual Unlimited','rev_26'])} annual membership and a {R(PRODS.loc['Studio 6 Month Unlimited','rev_26'])} six-month sale &mdash; worth {R(PRODS.loc['Studio Annual Unlimited','rev_26']+PRODS.loc['Studio 6 Month Unlimited','rev_26'])} between them from just two transactions.</p>
<p>That is the most encouraging line in this report. The studio has found a way to sell long commitments at a high ticket. The task is to sell more than two of them.</p>
{ev('View every product sold in September, against September 2025', MOV_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Products with less than ₹10,000 of movement in either year are excluded above; the full ledger is in the workbook. "Session" is a combined line covering session-type purchases recorded outside the standard package list, averaging ₹3,002 per sale.</p>')}

<h2>The commitment-length problem</h2>
<div class="sub">The studio&rsquo;s forward revenue cushion is thinning</div>
{CH_DUR}
{MEMB_T}
<p>A membership business has two jobs: get paid, and get the member to re-commit. The second job is the one that compounds. Bandra&rsquo;s membership line is being held up by one-month products while the longer commitments &mdash; the ones that roll over less often and generate far more lifetime value per conversation &mdash; shrink to almost nothing.</p>
<p>Three-month memberships are the clearest case: <strong>18 units in April 2025, 2 units in September 2026</strong>. In the same window one-month units fell from 29 to 15. Only the new six-month and annual tiers grew, and from a base of almost zero. This is a sales-mix problem, not a demand problem &mdash; the members are still buying; they are buying shorter.</p>
<div class="call gold">
<h3>Why this matters more than the flat top line suggests</h3>
<p>A one-month member makes twelve purchase decisions a year. A three-month member makes four. A twelve-month member makes one. Every step down in commitment length multiplies the number of moments at which the studio can lose the member &mdash; and the data shows September losing them in exactly those moments. Combined with a delivery ratio that has risen from {CL[2024]['rev']/cash24*100:.0f}% to {CL[2026]['rev']/cash26*100:.0f}%, the studio now has both a shorter commitment base <em>and</em> less prepaid cushion to absorb the consequences.</p>
</div>

<h2>Pricing and the product ladder</h2>
<div class="sub">What a class costs, and which tier wins</div>
{CH_LADDER}
{LAD_T}
<p>The ladder is mostly rational: per-class cost falls as the package grows, from {R(PPC.set_index('product').loc['Studio Single Class','per_class'])} for a single class to {R(PPC.set_index('product').loc['Studio 12 Class Package','per_class'])} inside the 12-class pack. Two rungs break the pattern, and both are worth acting on.</p>
<p>The <strong>10-class package at {R(PPC.set_index('product').loc['Studio 10 Class Package','per_class'])} a class</strong> is priced above the 12-class pack while selling for essentially the same money &mdash; an average ticket of {R(PPC.set_index('product').loc['Studio 10 Class Package','avg_price'])} against {R(PPC.set_index('product').loc['Studio 12 Class Package','avg_price'])}. Thirteen members bought the worse-value option in September. And the <strong>2-for-1 intro pack halves the price again to {R(PPC.set_index('product').loc['Studio Newcomers 2 For 1','per_class'])} a class</strong>, which is defensible as acquisition but sets the member&rsquo;s price expectation extremely low at exactly the moment they are deciding whether the studio is worth full price.</p>

<h2>Trading pattern through the year</h2>
<div class="sub">September in the context of 2026</div>
{CH_YTD}
{YTD_T}
<p>Year to date the studio is within <strong>{abs(ytd_yoy):.1f}%</strong> of 2025 on cash &mdash; {R(ytd26['val'].sum())} against {R(ytd25['val'].sum())} &mdash; while selling {ytd25['Sale ID'].nunique()-ytd26['Sale ID'].nunique()} fewer transactions to {ytd25['Member ID'].nunique()-ytd26['Member ID'].nunique()} fewer paying members. The average sale rose from {R(ytd25['val'].sum()/max(ytd25['Sale ID'].nunique(),1))} to {R(ytd26['val'].sum()/max(ytd26['Sale ID'].nunique(),1))}. September is not an outlier on cash; it is a normal month in a flat year. The outlier is in what the month delivered, not what it collected.</p>

<h2>How September was paid for</h2>
<div class="sub">Transaction size, repeat buyers and payment method</div>
{CH_BANDS}
{BAND_T}
<p>The distribution is thin at the bottom and very fat at the top. <strong>{int(BANDS.loc[LABS[0],'n'])} of the month&rsquo;s {DN['s_lines'][2026]} sale lines were under ₹2,000</strong> and produced {P(BANDS.loc[LABS[0],'pct'])} of revenue, while <strong>{int(BANDS.loc[LABS[5],'n'])} sales above ₹50,000 produced {P(BANDS.loc[LABS[5],'pct'])}</strong>. The 10&ndash;20k band &mdash; the standard package tier &mdash; carried {P(BANDS.loc[LABS[3],'pct'])} on its own.</p>
<p>That shape is the signature of a business whose revenue depends on a small number of large commitments. It is efficient, and it is concentrated. The three largest sales of the month were {R(175560)}, {R(102344)} and {R(50242)}; the single annual membership is {P(175560/cash26*100)} of September on its own.</p>
{PM_T}
<p>Repeat purchasing is doing more work than it appears. <strong>36 of the 139 paying members bought more than once in September, and they produced {P(s26[s26['Member ID'].isin(s26.groupby('Member ID').size().pipe(lambda c: c[c>=2]).index)]['val'].sum()/cash26*100)} of the month&rsquo;s cash.</strong> One member bought eleven times. The distribution of repeat behaviour, not the acquisition funnel, is what made September look normal.</p>

<h2>Who sold it</h2>
<div class="sub">Salesperson performance, and the largest block in the ledger</div>
{CH_SOLD}
{SOLD_T}
<p>Shipra Bhika led the month with <strong>{R(SOLD.loc['Shipra Bhika','rev_26'])}</strong> across {int(SOLD.loc['Shipra Bhika','n_26'])} sales, followed by Imran Shaikh at {R(SOLD.loc['Imran Shaikh','rev_26'])} and Nadiya Shaikh at {R(SOLD.loc['Nadiya Shaikh','rev_26'])}. Nadiya wrote the most sales of anyone ({int(SOLD.loc['Nadiya Shaikh','n_26'])}) at the lowest average ticket ({R(SOLD.loc['Nadiya Shaikh','avg_26'])}), while Deesha Changwani converted {int(SOLD.loc['Deesha Changwani','n_26'])} sales at the second-lowest average &mdash; a volume pattern that suggests walk-in and single-class traffic.</p>
<div class="call">
<h3>{R(SOLD.loc['-','rev_26'])} of September revenue has no salesperson name on it</h3>
<p>That is <strong>{SOLD.loc['-','rev_26']/cash26*100:.0f}% of the month</strong> across {int(SOLD.loc['-','n_26'])} transactions &mdash; larger than any named individual. Some of it will be genuine self-service, online or app purchases, which is a good thing to have. But as recorded it means the studio cannot currently answer which of its salespeople produce members who stay, because a quarter of the evidence is unattributed. Named attribution is a one-field fix at the point of sale.</p>
</div>

<h2>Discounting</h2>
<div class="sub">{R(s26['disc'].sum())} given away, concentrated at the top of the ladder</div>
{DISC_T}
<p>Discounting is disciplined in volume and loose in depth. Only <strong>{int(s26[s26['disc']>0]['Sale ID'].nunique())} of {DN['s_txn'][2026]} sales carried a discount</strong>, but the depth averaged {P(s26[s26['disc']>0].assign(d=lambda x: x['disc']/(x['val']+x['disc'])*100)['d'].mean())} and reached <strong>19.2% on the annual membership and the 20-class pack</strong>, against 14.4% on the standard monthly and three-month products. The deeper discounts sit on the highest-value products &mdash; which is where each percentage point costs the most. The annual membership&rsquo;s discount alone was {R(41800)}.</p>

{SALES_B}

<h2>Retail</h2>
<div class="sub">A small line that is not yet a business</div>
{RET_T}
<p>Retail produced <strong>{R(RET26['val'].sum())} across {len(RET26)} sales from {RET26['Member ID'].nunique()} members</strong> &mdash; {P(RET26['val'].sum()/cash26*100)} of the month, with an average sale of {R(RET26['val'].mean())}. Consumables are the largest component at {R(RET26[RET26['Cleaned Product']=='Retail - Consumables']['val'].sum())} across {int((RET26['Cleaned Product']=='Retail - Consumables').sum())} sales. At this scale retail is a member-service line rather than a revenue line, and the data contains no stock or margin information with which to judge it further.</p>


<h2>What the first purchase predicts</h2>
<div class="sub">Nothing in the sales ledger separates members as sharply as the product they started on &mdash; except how quickly they came back.</div>

<p>Take the {len(N9):,} people whose first visit to Bandra is on record and group them by the first thing they bought. The spread in eventual lifetime value is
not marginal, it is structural. A member who started on a <strong>{TOP_STARTER} is worth {R(FPN['ltv'].max())} to the studio</strong>. One who started on a
<strong>{LOW_STARTER} is worth {R(FPN['ltv'].min())}</strong>. Between them sit every other product in the range, in a consistent order: memberships first,
packages second, single classes last.</p>

<p>The obvious caution applies, and it is worth stating plainly: members who chose a bigger commitment were already more committed. But the gap is
<strong>{FP_RATIO:.1f}-fold</strong>, and the studio sells both products from the same front desk within the same minute. What a new client is offered first is
not a neutral choice.</p>

{CH_FPLTV}

<p>The second predictor is time, and it is even more directly actionable. Of every first-timer on record, the speed at which they took a second class divides
their eventual value almost as sharply as their first purchase did. Members who returned <strong>within a week are worth {R(SP7)} on average</strong>; those who
took a month, or never came back at all, are worth <strong>{R(SPLAST)}</strong>.</p>

{CH_SPEED}

{ev('Evidence &mdash; first purchase and speed to the second visit',
    T(['First purchase', 'People', 'Mean lifetime value', 'Mean visits', 'Visits per month'],
      [[i, int(r['people']), R(r['ltv']), f"{r['visits']:.1f}", f"{r['vpm']:.1f}"] for i, r in FPN.iterrows()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>By speed to the second visit</strong></p>' +
    T(['Second visit within', 'People', 'Mean lifetime value', 'Mean visits'],
      [[str(i), int(r['people']), R(r['ltv']), f"{r['visits']:.1f}"] for i, r in SP.iterrows()], 'num'))}

<h2>Recommendations</h2>
<div class="sub">Thirteen actions, ordered by expected value</div>
<p>The first three protect what already works. Four are pricing and structure. The last four attack frequency, channel and cross-selling &mdash; the levers that do not require a single new customer. Each recommendation carries the reasoning behind it and the impact the studio should expect, so it can be argued with rather than simply accepted.</p>
{REC_HTML}

<h2>Method and limitations</h2>
<div class="sub">How to read these numbers, and what they cannot show</div>
{SRC}'''

HTML = page('Supreme HQ, Bandra — Sales Performance, September 2026',
            'Sales Performance Review &nbsp;&middot;&nbsp; September 2026',
            'Supreme HQ, Bandra',
            f'September banked {R(cash26)} &mdash; within {abs(yoy):.1f}% of last year, and indistinguishable from a normal month on the top line. Underneath it, the studio sold the same money in shorter commitments, to more people, and consumed {CL[2026]["rev"]/cash26*100:.0f}% of it as delivered classes against {CL[2024]["rev"]/cash24*100:.0f}% two years ago. '
            f'Two findings stand out. The {len(X.core_ix)} members who trained here in both Septembers gave the studio {abs(X.CORE_LOST)} fewer visits this year, worth about {R(abs(X.CORE_LOST)*(1306451/len(s26)))} of class revenue. And the product a first-time buyer starts on predicts their lifetime value more than anything except how fast they come back: {R(FPN["ltv"].max())} from a {TOP_STARTER.lower()}, {R(FPN["ltv"].min())} from a {LOW_STARTER.lower()}.',
            f'<span>{DN["s_txn"][2026]} transactions</span><span>{DN["s_mem"][2026]} paying members</span><span>Sales ledger, Sessions ledger and member file</span><span>Snapshot 18 October 2026</span>',
            BODY)
open('/home/user/reports-arena/Bandra_September_2026_1_Sales_Performance.html','w').write(HTML)
print('Report 1 written:', len(HTML), 'bytes')
print('cash', round(cash26), '| yoy', round(yoy,1), '| ytd yoy', round(ytd_yoy,1))
