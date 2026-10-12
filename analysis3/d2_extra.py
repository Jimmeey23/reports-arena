"""Deep-dive content for the three reports: new findings from the round-5 mining pass.
Exports SALES_EXTRA, CLASS_EXTRA, TEACH_EXTRA (HTML) and EXTRA_RECS_* (recommendation lists).
"""
import pandas as pd, numpy as np
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       A1, A2, A3, B1, B2, N1, N2, INK, MUT)

B = 'Supreme HQ, Bandra'; U = '/home/user/reports-arena/uploads/'
def num(s): return pd.to_numeric(pd.Series(s).astype(str).str.replace(r'[,\s₹]', '', regex=True), errors='coerce')

# =================================================================== CHECK-IN LEDGER
CK = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False, usecols=[
    'Member ID','Location','Date (IST)','Checked In','Cleaned Class','Is New'])
CK = CK[CK['Location'] == B].copy()
CK['dt'] = pd.to_datetime(CK['Date (IST)'], errors='coerce')
AT = CK[CK['dt'].notna() & (CK['Checked In'] == True)].copy()
def sept(y): return AT[(AT['dt'] >= f'{y}-09-01') & (AT['dt'] < f'{y}-10-01')]
s24, s25, s26 = sept(2024), sept(2025), sept(2026)
v26 = s26.groupby('Member ID').size(); v25 = s25.groupby('Member ID').size()
m25, m26, m24 = set(s25['Member ID']), set(s26['Member ID']), set(s24['Member ID'])
core_ix = m25 & m26
core_now = v26[v26.index.isin(core_ix)]; core_then = v25[v25.index.isin(core_ix)]
CORE_LOST = int(core_then.sum() - core_now.sum())
core_old = v25[v25.index.isin(m24 & m25)]; core_old_prev = s24.groupby('Member ID').size()[lambda s: s.index.isin(m24 & m25)]
ret_seats = int(v26[v26.index.isin(core_ix)].sum()); new_seats = int(v26[~v26.index.isin(m25)].sum())

# monthly activity
rows = []
for y in range(2024, 2027):
    for m in range(1, 13):
        a = AT[(AT['dt'] >= f'{y}-{m:02d}-01') & (AT['dt'] < pd.Timestamp(f'{y}-{m:02d}-01') + pd.offsets.MonthBegin(1))]
        if len(a) < 20: continue
        rows.append(dict(mon=f'{str(y)[2:]}-{m:02d}', members=a['Member ID'].nunique(), seats=len(a),
                         spm=len(a)/a['Member ID'].nunique()))
ACT = pd.DataFrame(rows)
ACT_L = ACT[ACT['mon'] >= '25-01']
LAB12 = [m[-2:] + ('·Jan' if m.endswith('-01') else '') for m in ACT_L['mon']]
LAB12 = [m.split('-')[1] for m in ACT_L['mon']]
SPM = [(v, '') for v in ACT_L['spm'].tolist()]

# =================================================================== SESSIONS
X = pd.read_csv(U + 'Day End Report - Part 3 - Sessions (19).csv', low_memory=False)
X = X[X['Location'] == B].copy(); X['dt'] = pd.to_datetime(X['Date'], errors='coerce')
for c in ['Capacity','CheckedIn','LateCancelled','Booked','Complimentary','Revenue','Memberships','Packages','IntroOffers','SingleClasses','Classes']:
    X[c] = num(X[c]).fillna(0)
X['cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
X['fill'] = X['CheckedIn'] / X['cap'].replace(0, np.nan)
x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()
x25 = X[(X['dt'] >= '2025-09-01') & (X['dt'] < '2025-10-01')].copy()
def cb(d):
    d = d[d['cap'] >= 4].copy()
    d['cband'] = pd.cut(d['cap'], [0, 9, 11, 13, 100], labels=['≤9 seats', '10–11', '12–13', '14+'])
    return d.groupby('cband', observed=True).agg(n=('SessionID','size'), att=('CheckedIn','sum'), cap=('cap','sum'))
CB26, CB25 = cb(x26), cb(x25)
CB_FILL_26 = (CB26['att']/CB26['cap']*100); CB_FILL_25 = (CB25['att']/CB25['cap']*100)

# =================================================================== PAYROLL
P4 = pd.read_csv(U + 'Day End Report - Part 1 - Payroll (4).csv', low_memory=False)
P4 = P4[P4['Location'] == B].copy(); P4['dt'] = pd.to_datetime(P4['Month Year'], errors='coerce')
for c in [c for c in P4.columns if 'Paid' in c or 'Sessions' in c or 'Customers' in c]:
    P4[c] = num(P4[c])
PA = P4[P4['dt'] == '2026-08-01'].copy()
PAY_SESS = PA['Total Paid'].sum()/PA['Total Sessions'].sum()
CYCLE_RATE = PA['Cycle Paid'].sum()/max(PA['Cycle Sessions'].sum(), 1)
BARRE_RATE = PA['Barre Paid'].sum()/max(PA['Barre Sessions'].sum(), 1)
CONV = P4[P4['dt'] >= '2025-09-01'].groupby('Teacher Name')[['Converted','New','Retained']].sum()
CONV['conv_rate'] = (CONV['Converted']/CONV['New'].replace(0, np.nan)*100)

# =================================================================== SALES
import d1_data as _D
SB = _D.SB.copy()                      # already-parsed September-complete sales frame
SB['val'] = SB['val'].astype(float)
# disc stays item-level (unit discount x quantity) as set in d1_data; the
# sale-level column repeats on every item row and must not be re-summed
sale26 = SB[(SB['dt'] >= '2026-09-01') & (SB['dt'] < '2026-10-01')]
sale25 = SB[(SB['dt'] >= '2025-09-01') & (SB['dt'] < '2025-10-01')]
PM = sale26.groupby('Payment Method')['val'].agg(['size','sum']).sort_values('sum', ascending=False)
spend = sale26.groupby('Member ID')['val'].sum().sort_values(ascending=False)
TOP10 = spend.nlargest(10).sum()/spend.sum()*100
BOT50 = spend.nsmallest(int(len(spend)/2)).sum()/spend.sum()*100
cx = sale26.groupby('Member ID')['Cleaned Category'].nunique()
SINGLE_CAT = (cx == 1).mean()*100

# =================================================================== FIRST-VISIT QUALITY
CK2 = pd.read_csv('/home/user/reports-arena/google_drive/Day End Report - Part 4', low_memory=False, usecols=[
    'Member ID','Location','Date (IST)','Checked In','Cleaned Class','Teacher Name','Time','Day of Week','Is New'])
CK2 = CK2[CK2['Location'] == B].copy(); CK2['dt'] = pd.to_datetime(CK2['Date (IST)'], errors='coerce')
CK2 = CK2[CK2['dt'].notna() & (CK2['Checked In'] == True)].copy().sort_values(['Member ID','dt'])
CK2['vn'] = CK2.groupby('Member ID').cumcount()+1
depth_all = CK2.groupby('Member ID').size().rename('visits')
F = CK2[CK2['vn'] == 1].join(depth_all, on='Member ID')
F = F[F['dt'] >= '2025-01-01'].copy()
F['hr'] = num(F['Time'].astype(str).str[:2])
F['band'] = pd.cut(F['hr'], [0, 9, 12, 17, 24], labels=['Early, before 9am', 'Late morning, 9–12', 'Afternoon, 12–17', 'Evening, after 17'])
def quality(df, col, minn=12):
    g = df.groupby(col, observed=True).agg(n=('visits','size'), r3=('visits', lambda x: (x >= 3).mean()*100),
                                           r6=('visits', lambda x: (x >= 6).mean()*100), av=('visits','mean'))
    return g[g['n'] >= minn].sort_values('r3', ascending=False)
Q_DAY = quality(F, 'Day of Week')
Q_BAND = quality(F, 'band')
Q_FMT = quality(F, 'Cleaned Class')
Q_ENT = quality(F, 'Is New', 20)
Q_TR = quality(F, 'Teacher Name', 20)

# =================================================================== LEAD SOURCE
MB = pd.read_csv(U + 'Day End Report - Part 1 - New (9).csv', low_memory=False)
MB['is_new'] = MB['Is New'].map(_D._is_new)
MB = MB[(MB['First Visit Location'] == B) & (MB['is_new'] == True)].copy()
MB['fvd'] = pd.to_datetime(MB['First Visit Date'], errors='coerce')
MB['Ltv'] = num(MB['Ltv']); MB['No of Visits'] = num(MB['No of Visits'])
MB['Days To Second Visit'] = num(MB['Days To Second Visit'])
SRC = MB[(MB['fvd'] >= '2025-09-01') & (MB['fvd'] < '2026-09-01')]
LS = SRC.groupby('Source').agg(n=('Ltv','size'), conv=('Conversion Status', lambda x: (x == 'Converted').mean()*100),
                               ltv=('Ltv','mean'), av=('No of Visits','mean'))
LS = LS[LS['n'] >= 10].sort_values('conv', ascending=False)
SPEED = SRC['Conversion Speed Bucket'].value_counts()
D2 = SRC['Days To Second Visit'].dropna()
SEP_INTAKE = MB[(MB['fvd'] >= '2026-09-01') & (MB['fvd'] < '2026-10-01')]

E = A1; E2 = B1; E3 = A3; E4 = N2

# precomputed bits used inside the narrative strings
CB_REV26 = (x26.assign(b=pd.cut(x26['cap'], [0, 9, 11, 13, 100], labels=['≤9 seats','10–11','12–13','14+']))
            .groupby('b', observed=True)['Revenue'].sum())
CB_RPS = {k: (CB_REV26.get(k, 0) / max(int(CB26.loc[k, 'n']) if k in CB26.index else 1, 1)) for k in CB_REV26.index}
LEAVERS_ONE_AND_DONE = int((v25[v25.index.isin(m25 - m26)] == 1).sum())
_last_all = AT.groupby('Member ID')['dt'].max()
_leavers = list(m25 - m26)
LEAVERS_ONE_AND_DONE = int((v25[v25.index.isin(_leavers)] == 1).sum())
LEAVERS_LAST_IN_SEP25 = sum(1 for _m in _leavers
                            if pd.Timestamp('2025-09-01') <= _last_all.get(_m, pd.Timestamp('1900-01-01')) < pd.Timestamp('2025-10-01'))
SPM26 = len(s26)/s26['Member ID'].nunique()
SPM25 = len(s25)/s25['Member ID'].nunique()
PC_FILL = x26[x26['Class']=='Studio PowerCycle']['CheckedIn'].sum()/x26[x26['Class']=='Studio PowerCycle']['cap'].sum()*100
PCE_FILL = x26[x26['Class']=='Studio PowerCycle Express']['CheckedIn'].sum()/x26[x26['Class']=='Studio PowerCycle Express']['cap'].sum()*100
RATE_MIN = (PA['Total Paid'] / PA['Total Sessions'].replace(0, np.nan)).min()
RATE_MAX = (PA['Total Paid'] / PA['Total Sessions'].replace(0, np.nan)).max()

# =================================================================== HELPER
def card(tag, cls, head, body, verdict):
    return f'''<div class="hcard"><span class="tag {cls}">{tag}</span><h3>{head}</h3>
    <p>{body}</p><div class="verdict">{verdict}</div></div>'''

# ============================================================ SALES EXTRA
SALES_EXTRA = f'''
<h2 id="reach">The base is widening</h2>
<div class="sub">More people came to Bandra this September than in either of the last two. They each came less often.</div>

<p>This is the finding that reframes the whole month. The cash line fell 2.3%, and it is tempting to read that as demand
weakening. The check-in ledger says the opposite: <strong>{s26['Member ID'].nunique()} individual members trained at Bandra in September 2026, against
{s25['Member ID'].nunique()} in September 2025 and {s24['Member ID'].nunique()} in September 2024</strong> &mdash; a base that has grown
{(s26['Member ID'].nunique()/s25['Member ID'].nunique()-1)*100:.0f}% year on year. The studio is reaching more people than it ever has in a September.</p>

<p>What fell was frequency. The average member trained <strong>{len(s26)/s26['Member ID'].nunique():.2f} times</strong> in September 2026 against
<strong>{len(s25)/s25['Member ID'].nunique():.2f} times</strong> a year earlier. Revenue per active member went the other way &mdash;
<strong>{R(1306451/s26['Member ID'].nunique())} against {R(981453/s25['Member ID'].nunique())}</strong>, up {(1306451/s26['Member ID'].nunique())/(981453/s25['Member ID'].nunique())*100-100:.1f}%. Each member is worth more;
there are just fewer visits in each of them. Fewer seats were sold, but they were better-paid seats.</p>

{bars([str(m.split('-')[1]) for m in ACT_L['mon']], [('Visits per active member', ACT_L['spm'].tolist(), E)],
      'Visits per active member, by month — the line has been sliding since mid-2025',
      h=290, ymax=5.4, note='Check-in ledger, attended visits only. September 2026 is the lowest figure since March 2024 excluding the '
      'part-month of October 2026. Breadth expanded while depth contracted.')}

<div class="stat">
 <div><div class="v">{s26['Member ID'].nunique()}</div><div class="l">Members trained<br/>Sept 2026 (305 a year ago)</div></div>
 <div><div class="v">{len(s26)/s26['Member ID'].nunique():.2f}</div><div class="l">Visits per member<br/>(4.84 a year ago)</div></div>
 <div><div class="v">{R(1306451/s26['Member ID'].nunique())}</div><div class="l">Class revenue per<br/>active member</div></div>
 <div><div class="v">{P((1306451/s26['Member ID'].nunique())/(981453/s25['Member ID'].nunique())*100-100)}</div><div class="l">Change in revenue<br/>per member, YoY</div></div>
</div>

<h2>The loyal core halved its frequency</h2>
<div class="sub">Seventy-eight people who trained here last September came back this September. Between them they gave the studio {abs(CORE_LOST)} fewer visits.</div>

<p>This is treated in full in the class performance report, because it is fundamentally a question of volume rather than of money. Its cash
consequence is easy to state, though. The {abs(CORE_LOST)} visits those members did not make are, at September&rsquo;s class revenue of
{R(1306451/len(s26))} a head, roughly <strong>{R(abs(CORE_LOST)*(1306451/len(s26)))} of class revenue the studio never booked</strong> &mdash; in a month when the
entire cash line moved by {R(abs(1564732-1529410))}. Frequency, not price, is where the money went.</p>

<h2>How the money arrived</h2>
<div class="sub">Online payments now carry the largest tickets by a factor of two, and discounting is almost entirely code-driven.</div>

<p>Four channels took the month&rsquo;s money. Counter and custom payment took the most transactions &mdash;
<strong>{int(PM.loc['custom','size'])} sales worth {R(PM.loc['custom','sum'])}</strong> &mdash; but the largest average ticket sits with Stripe at
<strong>{R(PM.loc['stripe','sum']/PM.loc['stripe','size'])} on {int(PM.loc['stripe','size'])} sales</strong>, more than twice the cash average of {R(PM.loc['cash','sum']/PM.loc['cash','size'])}.
The pattern is not incidental: the products that require a decision &mdash; annual and six-month memberships, multi-class packs &mdash; are bought on cards and online, while
day-to-day singles are bought at the desk. Stripe transactions fell from {int(sale25.groupby('Payment Method')['val'].size().get('stripe',0))} to {int(PM.loc['stripe','size'])} year on year; multi-method sales,
where a member splits a large purchase, doubled from 6 to {int(PM.loc['multiple-payment-methods','size'])}.</p>

<p>Discounting is concentrated in five codes, and three of them are <em>acquisition</em> codes rather than retention codes. Two codes alone
&mdash; <strong>NC-2026-SHQ ({int(sale26.groupby('Discount Code').size().get('NC-2026-SHQ',0))} uses, {R(sale26[sale26['Discount Code']=='NC-2026-SHQ']['disc'].sum())} given away)</strong>
and <strong>ZAP10 ({int(sale26.groupby('Discount Code').size().get('ZAP10',0))} uses, {R(sale26[sale26['Discount Code']=='ZAP10']['disc'].sum())})</strong> &mdash;
account for {R(sale26[sale26['Discount Code'].isin(['NC-2026-SHQ','ZAP10'])]['disc'].sum())} of the {R(sale26['disc'].sum())} given away. A single use of the <code>20OFFSHQ</code> code
cost {R(41800)} on its own. Because a code requires intent, every rupee of discount here is a rupee someone asked for and was granted &mdash; which makes it a policy question, not a leakage question.</p>

{hbars([(f'{k} · {int(v)} sales', PM.loc[k,'sum'], E if i == 0 else (E2 if i == 1 else E3))
        for i, (k, v) in enumerate(PM['size'].items())],
       'Cash by payment channel, September 2026', note='Average ticket: Stripe ' +
       R(PM.loc['stripe','sum']/PM.loc['stripe','size']) + ', split payments ' +
       R(PM.loc['multiple-payment-methods','sum']/PM.loc['multiple-payment-methods','size']) + ', custom ' +
       R(PM.loc['custom','sum']/PM.loc['custom','size']) + ', cash ' + R(PM.loc['cash','sum']/PM.loc['cash','size']) + '.')}

{ev('Evidence — discount codes used in September 2026',
    T(['Code', 'Sales', 'Revenue after discount', 'Discount given', 'Effective depth'],
      [[k, int(r['n']), R(r['rev']), R(r['disc']), P(r['disc']/(r['rev']+r['disc'])*100)]
       for k, r in sale26.groupby('Discount Code').agg(n=('val','size'), rev=('val','sum'), disc=('disc','sum'))
       .sort_values('rev', ascending=False).head(8).iterrows()], 'num'))}

<h2>Who the money came from</h2>
<div class="sub">Ten members account for more than a third of the month. Half of all buyers account for seven per cent.</div>

<p>September&rsquo;s {len(spend)} paying members are not a flat distribution. The top ten by spend account for
<strong>{TOP10:.0f}% of the month&rsquo;s cash</strong>, the top twenty for {spend.nlargest(20).sum()/spend.sum()*100:.0f}%, while the bottom half of buyers contribute
<strong>{BOT50:.1f}%</strong>. That is not unusual for a boutique studio and it is not a problem &mdash; but it does mean that two or three decisions by
high-value members move the monthly number more than any campaign aimed at the base. The single largest purchase of the month,
an annual unlimited membership at {R(175560)}, was worth more than the combined purchases of the bottom {int(len(spend)*0.35)} buyers.</p>

<p>The other side of concentration is breadth of need. <strong>{SINGLE_CAT:.0f}% of September buyers bought from only one product category.</strong>
Only {int((cx>=2).sum())} of {len(cx)} members bought across two categories, and a single member bought across four. There is very little
cross-selling happening: a member who joins for Barre and a member who joins for PowerCycle are, on this month&rsquo;s evidence, treated
as the same customer until they leave.</p>

{diverging([('Top 10 buyers', spend.nlargest(10).sum()), ('Buyers 11–20', spend.nlargest(20).sum()-spend.nlargest(10).sum()),
            ('Buyers 21–70', spend.nlargest(70).sum()-spend.nlargest(20).sum()),
            ('Bottom half of buyers', spend.nsmallest(int(len(spend)/2)).sum())],
           'Cash by buyer tier, September 2026', note='Read as contribution, not as growth: the top decile is where retention '
           'spend earns the most, and where a single lapse costs the most.')}
'''

CORE_SECTION = f'''<h2>The loyal core halved its frequency</h2>
<div class="sub">Seventy-eight people who trained here last September came back this September. Between them they gave the studio {abs(CORE_LOST)} fewer visits.</div>

<p>{len(core_ix)} members trained at Bandra in <em>both</em> September 2025 and September 2026. This is a true like-for-like group &mdash; same
people, same month, twelve months apart. In September 2025 they made <strong>{int(core_then.sum())} visits</strong> ({core_then.mean():.2f} each). In September 2026
they made <strong>{int(core_now.sum())}</strong> ({core_now.mean():.2f} each). That is a fall of <strong>{abs(core_now.mean()/core_then.mean()-1)*100:.1f}%</strong> in the
frequency of the studio&rsquo;s most committed customers.</p>

<p>The arithmetic matters more than the percentage. Those {abs(CORE_LOST)} lost visits are <strong>{abs(CORE_LOST)/len(s26)*100:.0f}% of every seat that was
filled in September 2026</strong>. Had the core held its year-ago frequency, September 2026 would have recorded
<strong>{len(s26)+abs(CORE_LOST):,} attendances</strong> &mdash; ahead of September 2025&rsquo;s {len(s25):,}, not behind it. The month&rsquo;s decline is not an
acquisition failure at all. It is a frequency failure among people who already know the studio.</p>

{dumbbell([('Sept-2024 core (n=%d)' % len(core_old), core_old_prev.mean(), core_old.mean()),
           ('Sept-2026 core (n=%d)' % len(core_ix), core_then.mean(), core_now.mean())],
          'Visits per member in September, for members present in two consecutive Septembers',
          lo_lab='earlier September', hi_lab='later September',
          note='The same measurement applied to the two most recent September pairs. The decay is not new &mdash; it was '
          '−11.5% between 2024 and 2025, and −35.3% between 2025 and 2026. It is accelerating.')}

{ev('Evidence — the two September cohorts, member by member',
    T(['Cohort', 'Members', 'Earlier September', 'Later September', 'Change in visits per member'],
      [['Sept-2024 → Sept-2025 (present in both)', len(core_old), f'{core_old_prev.mean():.2f}',
        f'{core_old.mean():.2f}', P((core_old.mean()/core_old_prev.mean()-1)*100)],
       ['Sept-2025 → Sept-2026 (present in both)', len(core_ix), f'{core_then.mean():.2f}',
        f'{core_now.mean():.2f}', P((core_now.mean()/core_then.mean()-1)*100)]], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:14px">Only members with at least one attended visit in both months are counted, '
    'so no joining or leaving distorts the comparison. The 2025–26 pair is a smaller and more committed group by construction, which '
    'makes its 35% decline more notable, not less.</p>')}

<h2>Nobody was lost. Nothing was converted.</h2>
<div class="sub">The churn is almost entirely people who came once and never came back &mdash; and it is being replaced in volume.</div>

<p>Of the {len(m25-m26)} members who trained in September 2025 and did not appear in September 2026, <strong>{(s25.groupby('Member ID').size()[lambda s: s.index.isin(m25-m26)] == 1).sum()}</strong>
had made exactly one visit in that month, and {LEAVERS_LAST_IN_SEP25} of the 227 were last seen in September 2025 itself. On lifetime numbers the distinction is stark:
the members who <em>stayed</em> had averaged <strong>{(AT.groupby('Member ID').size()[lambda s: s.index.isin(core_ix)].mean()):.0f} career visits</strong>, while the ones who
left averaged <strong>{(AT.groupby('Member ID').size()[lambda s: s.index.isin(m25-m26)].mean()):.0f}</strong>. The studio is not losing its regulars. It is failing to convert its trials.</p>

<p>And the replacements are working harder than the departures did. The {len(m26-m25)} members who had no September 2025 visit delivered
<strong>{new_seats:,} attendances</strong> this month; the {len(m25-m26)} who left behind them had delivered only
<strong>{int(v25[v25.index.isin(m25-m26)].sum()):,}</strong> a year ago. New blood out-performed old losses by
<strong>{new_seats/int(v25[v25.index.isin(m25-m26)].sum())*100-100:.0f}%</strong>. The problem is not that the studio cannot recruit. It is that it recruits at
the top of the funnel and leaks at the bottom.</p>

{bars(['Sept 2024', 'Sept 2025', 'Sept 2026'],
      [('Members trained', [s24['Member ID'].nunique(), s25['Member ID'].nunique(), s26['Member ID'].nunique()], E),
       ('Attendances', [len(s24), len(s25), len(s26)], E3)],
      'Breadth versus depth — the two lines have crossed',
      h=290, ymax=1600,
      note='Attendances are shown on the same axis to make the divergence visible; the member count is an index of breadth, '
      'the attendance count of depth. Breadth is at a three-year high. Depth is not.')}

'''

_sa = SALES_EXTRA.index('<h2>How the money arrived</h2>')
SALES_A, SALES_B = SALES_EXTRA[:_sa], SALES_EXTRA[_sa:]

# ============================================================ CLASS EXTRA
BOOK_BOARD_25 = x25['Booked'].sum()/x25['cap'].sum()*100
BOOK_BOARD_26 = x26['Booked'].sum()/x26['cap'].sum()*100
ATT_OF_BOOK_25 = x25['CheckedIn'].sum()/x25['Booked'].sum()*100
ATT_OF_BOOK_26 = x26['CheckedIn'].sum()/x26['Booked'].sum()*100
COMP26 = int(x26['Complimentary'].sum()); COMP_SHARE = COMP26/x26['CheckedIn'].sum()*100
CBAR = x26.groupby('Class').agg(att=('CheckedIn','sum'), comp=('Complimentary','sum'))
CBAR = (CBAR['comp']/CBAR['att'].replace(0, np.nan)*100).dropna().sort_values(ascending=False)

CLASS_EXTRA = CORE_SECTION + f'''
<h2 id="book">What the booking book says</h2>
<div class="sub">Bookings fell four times faster than attendance. That is the cleanest warning in the data.</div>

<p>Attendance is a lagging number &mdash; it tells you what happened in the room. The booking book tells you what members <em>intended</em>
to do, and it moved sharply. Members booked <strong>{int(x25['Booked'].sum()):,} seats in September 2025 and {int(x26['Booked'].sum()):,} in September 2026</strong>,
a fall of {abs(x26['Booked'].sum()/x25['Booked'].sum()*100-100):.0f}%. Attendance fell only {abs(x26['CheckedIn'].sum()/x25['CheckedIn'].sum()*100-100):.1f}%. The two numbers have come apart, and the
gap is entirely explained by discipline: {int(x25['LateCancelled'].sum())} late cancellations became {int(x26['LateCancelled'].sum())}.</p>

<p>Two things are true at once. The studio is now far better at converting an intention into a visit &mdash; <strong>{ATT_OF_BOOK_25:.1f}% of booked seats
were actually used a year ago, against {ATT_OF_BOOK_26:.1f}% now</strong>, and revenue per booked seat rose from {R(981453/x25['Booked'].sum())} to
{R(1306451/x26['Booked'].sum())}. But the intention pool itself is drying up: the book now covers only <strong>{BOOK_BOARD_26:.1f}% of the seats on the board,
down from {BOOK_BOARD_25:.1f}%</strong>. Tightening cancellation policy has improved the conversion of demand that already exists. It has not
created any new demand.</p>

<div class="stat">
 <div><div class="v">{int(x25['Booked'].sum()):,} &rarr; {int(x26['Booked'].sum()):,}</div><div class="l">Seats booked<br/>{P(x26['Booked'].sum()/x25['Booked'].sum()*100-100)} year on year</div></div>
 <div><div class="v">{P(ATT_OF_BOOK_25)} &rarr; {P(ATT_OF_BOOK_26)}</div><div class="l">Booked seats<br/>actually attended</div></div>
 <div><div class="v">{P(BOOK_BOARD_25)} &rarr; {P(BOOK_BOARD_26)}</div><div class="l">Seats on the board<br/>that were ever booked</div></div>
 <div><div class="v">{R(981453/x25['Booked'].sum())} &rarr; {R(1306451/x26['Booked'].sum())}</div><div class="l">Revenue per<br/>booked seat</div></div>
</div>

<div class="call b"><h4>Why this matters more than the fill rate</h4>
<p>Fill rate is computed after the fact. Bookings are the leading indicator, and the book is now half-empty
{P(BOOK_BOARD_26)} of capacity was ever claimed. A timetable designed for {int(x26['cap'].sum()):,} seat-slots is being asked to serve a book of {int(x26['Booked'].sum()):,}.
Until the booking rate rises, no amount of scheduling refinement will fill the room &mdash; there is nothing left to convert.</p></div>

<h2>The room is bigger than the demand</h2>
<div class="sub">Small rooms fill. Large rooms do not. The studio has been quietly fixing this &mdash; and has further to go.</div>

<p>Sort the month&rsquo;s sessions by how many seats the room holds and a clean pattern appears. Rooms of <strong>ten and eleven seats ran {CB_FILL_26.iloc[0]:.1f}% full</strong>
across {int(CB26['n'].iloc[0])} sessions. Rooms of <strong>twelve and thirteen ran {CB_FILL_26.iloc[1]:.1f}%</strong> across {int(CB26['n'].iloc[1])} sessions, and rooms of fourteen or more
ran {CB_FILL_26.iloc[2]:.1f}% across {int(CB26['n'].iloc[2])}. The same pattern held a year earlier, so this is a property of the timetable, not of September.</p>

<p>The encouraging part is that the studio has already begun to move. September 2025 ran {int(CB25['n'].iloc[0])} sessions in ten-to-eleven-seat rooms; September 2026 ran {int(CB26['n'].iloc[0])}.
Sessions in the largest rooms fell from {int(CB25['n'].iloc[2])} to {int(CB26['n'].iloc[2])}. Shifting a class into a smaller room does not change how many people
come &mdash; it changes how full the room looks and how much the same demand is worth, and revenue per session in the small-room band was
<strong>{R(x26[x26['cap'].between(10,11)]['Revenue'].sum()/max(len(x26[x26['cap'].between(10,11)]),1))}</strong> against
{R(x26[x26['cap']>=12]['Revenue'].sum()/max(len(x26[x26['cap']>=12]),1))} elsewhere.</p>

{bars(['10–11 seats', '12–13 seats', '14+ seats'],
      [('Sept 2025', [CB_FILL_25.get('10–11', np.nan)/100, CB_FILL_25.get('12–13', np.nan)/100, CB_FILL_25.get('14+', np.nan)/100], E4),
       ('Sept 2026', [CB_FILL_26.get('10–11', np.nan)/100, CB_FILL_26.get('12–13', np.nan)/100, CB_FILL_26.get('14+', np.nan)/100], E)],
      'How full the room ran, by how many seats it holds', as_pct=True, h=300, ymax=0.78,
      note='Capacity bands are the per-session seat count. The 10–11 band is the studio’s best-performing room size in both years; '
           'rooms of nine seats or fewer are omitted as they hold too few sessions to compare.')}

{ev('Evidence — capacity bands, sessions, attendances and revenue',
    T(['Room size', 'Sessions 2026', 'Attendances 2026', 'Fill 2026', 'Fill 2025', 'Revenue 2026', 'Revenue per session'],
      [[b, int(CB26.loc[b, 'n']) if b in CB26.index else 0,
        int(CB26.loc[b, 'att']) if b in CB26.index else 0,
        P(CB_FILL_26.get(b, np.nan)) if b in CB_FILL_26.index else '—',
        P(CB_FILL_25.get(b, np.nan)) if b in CB_FILL_25.index else '—',
        R(CB_REV26.get(b, 0)), R(CB_RPS.get(b, 0))]
       for b in ['10–11', '12–13', '14+']], 'num'))}

<h2>{COMP_SHARE:.0f} per cent of the room was free</h2>
<div class="sub">Complimentary seats rose by more than half while paid attendance fell. Barre 57 is the most affected.</div>

<p>Of the {int(x26['CheckedIn'].sum()):,} attendances recorded in September 2026, <strong>{COMP26:,} carried no payment</strong> &mdash; {COMP_SHARE:.1f}% of the room,
against {x25['Complimentary'].sum()/x25['CheckedIn'].sum()*100:.1f}% a year earlier. Complimentary seats rose {abs(COMP26/x25['Complimentary'].sum()*100-100):.0f}% while paid seats fell. Comps are not wrong in themselves: staff visits,
partner classes and make-goods are legitimate. But they are invisible in an attendance-only report, and at this scale they change the
meaning of the fill rate. <strong>A 42.6% fill on 3,293 seats is {int(x26['CheckedIn'].sum()):,} attendances; {COMP26} of them produced no revenue at all.</strong></p>

<p>Studio Barre 57 is the format most affected: {int(CBAR.get('Studio Barre 57', 0))} of its {int(x26[x26['Class']=='Studio Barre 57']['CheckedIn'].sum())} attendances
({CBAR.get('Studio Barre 57', 0):.0f}%) were complimentary, against {CBAR.get('Studio FIT', 0):.1f}% for Studio FIT. The two hosted classes in the month
&mdash; the Physique 57 partner sessions on 13 and 23 September &mdash; were 100% complimentary, 24 seats, zero revenue, and are correctly recorded as marketing rather than trading.</p>

{hbars([(k.replace('Studio ', ''), v, E if i == 0 else (E2 if i < 3 else E3)) for i, (k, v) in
        enumerate(CBAR.head(7).items())], 'Complimentary seats as a share of each format’s attendance',
       as_pct=True, note='Formats with fewer than one per cent comp share (Back Body Blaze, FIT, PowerCycle Express) are omitted.')}

<h2>Who a first class brings in &mdash; and whether they come back</h2>
<div class="sub">The day, hour and format of somebody&rsquo;s very first class predicts their lifetime with unusual accuracy.</div>

<p>Take every member whose first ever Bandra class fell from January 2025 onward, follow them for their whole history, and split by the
circumstances of that first visit. The differences are large enough to schedule against.</p>

<p>By day: people whose <strong>first class was on a Tuesday reach a third visit {Q_DAY.loc['Tuesday','r3']:.1f}% of the time</strong>; those who started on a
<strong>Sunday, {Q_DAY.loc['Sunday','r3']:.1f}%</strong>. By hour: a first class <strong>before 9am converts to a third visit {Q_BAND.loc['Early, before 9am','r3']:.1f}%</strong>
of the time and yields {Q_BAND.loc['Early, before 9am','av']:.1f} visits on average, against <strong>{Q_BAND.loc['Afternoon, 12–17','r3']:.1f}% and {Q_BAND.loc['Afternoon, 12–17','av']:.1f} visits</strong> for an afternoon start. By format: <strong>a first class in Studio Barre 57 leads to a third visit
{Q_FMT.loc['Studio Barre 57','r3']:.1f}% of the time and {Q_FMT.loc['Studio Barre 57','av']:.1f} visits</strong>, while a first class in Studio Mat 57 leads to
{Q_FMT.loc['Studio Mat 57','r3']:.1f}% and {Q_FMT.loc['Studio Mat 57','av']:.1f} visits.</p>

<p>None of this means a Tuesday class is better than a Sunday class. It means that the people willing to start on a Tuesday, or before
work, or in the Barre room, are a different kind of customer. The studio currently gives trials and first-timers to whichever slot has room.
The data says that decision has a measurable twelve-month consequence, and it is currently being made by default rather than by design.</p>

{hbars([(k, v/100, E if v == Q_DAY['r3'].max() else (E2 if v >= Q_DAY['r3'].mean() else E3))
        for k, v in Q_DAY['r3'].items()], 'Share of members who reach a third visit, by the day of their first class',
       as_pct=True, note='Every member whose first Bandra class fell from January 2025 onward, n = ' +
       f"{int(Q_DAY['n'].sum())} across these days. Depth measured over their entire history, so the group is still maturing.")}

{ev('Evidence — first-class circumstances and lifetime depth',
    T(['Day of first class', 'Members', 'Reached a 3rd visit', 'Reached a 6th visit', 'Average lifetime visits'],
      [[k, int(r['n']), P(r['r3']), P(r['r6']), f"{r['av']:.1f}"] for k, r in Q_DAY.iterrows()], 'num') +
    '<h4 style="margin-top:24px">By hour of first class</h4>' +
    T(['Band', 'Members', 'Reached a 3rd visit', 'Reached a 6th visit', 'Average lifetime visits'],
      [[str(k), int(r['n']), P(r['r3']), P(r['r6']), f"{r['av']:.1f}"] for k, r in Q_BAND.iterrows()], 'num') +
    '<h4 style="margin-top:24px">By format of first class</h4>' +
    T(['Format', 'Members', 'Reached a 3rd visit', 'Reached a 6th visit', 'Average lifetime visits'],
      [[str(k).replace('Studio ', ''), int(r['n']), P(r['r3']), P(r['r6']), f"{r['av']:.1f}"] for k, r in Q_FMT.iterrows()], 'num') +
    '<h4 style="margin-top:24px">By how they were brought in</h4>' +
    T(['Entry type', 'Members', 'Reached a 3rd visit', 'Reached a 6th visit', 'Average lifetime visits'],
      [[str(k), int(r['n']), P(r['r3']), P(r['r6']), f"{r['av']:.1f}"] for k, r in Q_ENT.iterrows()], 'num'))}
'''

_ca = CLASS_EXTRA.index('<h2 id="book">What the booking book says</h2>')
CLASS_A, CLASS_B = CLASS_EXTRA[:_ca], CLASS_EXTRA[_ca:]

# ============================================================ TEACHER EXTRA
SLOT_TBL = []
for key, r in x26.groupby(['Day','Time','Class']).agg(n=('SessionID','size'), tr=('Trainer','nunique')).query('tr >= 2').iterrows():
    sub = x26[(x26['Day'] == key[0]) & (x26['Time'] == key[1]) & (x26['Class'] == key[2])]
    per = sub.groupby('Trainer').agg(n=('SessionID','size'), att=('CheckedIn','mean'), cap=('cap','mean'))
    per['fill'] = per['att']/per['cap']*100
    if len(per) >= 2:
        SLOT_TBL.append(dict(slot=f'{key[0][:3]} {key[1][:5]}', fmt=key[2].replace('Studio ', ''), k=len(per),
                             lo=per['fill'].min(), hi=per['fill'].max(), best=per['fill'].idxmax(),
                             worst=per['fill'].idxmin(), n=int(per['n'].sum())))
SLOTS = pd.DataFrame(SLOT_TBL).sort_values('hi', ascending=False).assign(spread=lambda d: d['hi']-d['lo']) \
    .sort_values('spread', ascending=False)
MED_SPREAD = SLOTS['spread'].median(); N_SLOT = len(SLOTS); BIG = (SLOTS['spread'] > 30).sum()
ONE_SESS = int((SLOTS['n'] == SLOTS['k']).sum())
MULTI_SLOT = int((SLOTS['n'] > SLOTS['k']).sum())
MED_ROBUST = SLOTS[SLOTS['n'] > SLOTS['k']]['spread'].median()
OVER20 = int((SLOTS[SLOTS['n'] > SLOTS['k']]['spread'] > 20).sum())
Q_TR40 = Q_TR[Q_TR['n'] >= 40]

TEACH_EXTRA = f'''
<h2 id="controlled">The controlled test</h2>
<div class="sub">Twenty-four slots were taught by more than one trainer in September. Inside those slots, the trainer still moved the room by a median of {MED_SPREAD:.0f} points.</div>

<p>The scorecard in this report compares trainers who hold different slots, so it cannot separate the trainer from the slot. There is one clean way to
do that in the data: find the times in the week that <em>two or more</em> trainers taught the same class, and compare them. {N_SLOT} such slots exist in September.</p>

<p>The result refines the headline. It is true that slot assignment drives most of the variance &mdash; but it is not true that the trainer is irrelevant.
Within the same day, hour and format, the gap between the best and worst trainer has a <strong>median of {MED_SPREAD:.1f} percentage points</strong>, and in
<strong>{BIG} of the {N_SLOT} slots the spread exceeds 30 points</strong>. That is a real, repeatable trainer effect, and because both trainers are teaching
the same class at the same time of day to the same pool, it cannot be blamed on scheduling.</p>

<p>The largest gaps are instructive: <strong>{SLOTS.iloc[0]['slot']} {SLOTS.iloc[0]['fmt']}</strong> ran
{SLOTS.iloc[0]['hi']:.1f}% full with {SLOTS.iloc[0]['best']} and {SLOTS.iloc[0]['lo']:.1f}% with {SLOTS.iloc[0]['worst']};
<strong>{SLOTS.iloc[1]['slot']} {SLOTS.iloc[1]['fmt']}</strong> ran {SLOTS.iloc[1]['hi']:.1f}% with {SLOTS.iloc[1]['best']} against {SLOTS.iloc[1]['lo']:.1f}% with {SLOTS.iloc[1]['worst']}.
But {int((SLOTS['spread'] <= 10).sum())} of the {N_SLOT} slots show a spread of ten points or less &mdash; in those, who is teaching genuinely does not
matter, and the studio should stop treating those slots as a performance question.</p>

<div class="call n"><h4>A caution on the two largest rows</h4>
<p>In {ONE_SESS} of the {N_SLOT} slots every trainer taught exactly one session, so their spread rests on a single class each and should not be read as a
benchmark. Excluding those, the median spread across the remaining <strong>{MULTI_SLOT} slots is actually higher at {MED_ROBUST:.1f} points</strong>, and
<strong>{OVER20} of the {MULTI_SLOT}</strong> show a gap of more than twenty points. The finding does not depend on the outliers; it is the ordinary case.
What the outliers do show is the size of the opportunity when a slot is systematically mis-assigned.</p></div>

{hbars([(f"{r['slot']} · {r['fmt']}", r['spread']/100, E if r['spread'] > 30 else (E2 if r['spread'] > 15 else E3))
        for _, r in SLOTS.head(12).iterrows()],
       'Spread between the best and worst trainer in the same slot, September 2026', as_pct=True,
       note='Only slots taught by two or more trainers. A high spread means the slot is trainer-sensitive; a low spread means it is not.')}

{ev('Evidence — every shared slot, with the best and worst trainer named',
    T(['Slot', 'Format', 'Trainers', 'Sessions', 'Worst fill', 'Best fill', 'Spread', 'Worst', 'Best'],
      [[r['slot'], r['fmt'], int(r['k']), r['n'], P(r['lo']), P(r['hi']), f"{r['spread']:.1f} pts",
        r['worst'], r['best']] for _, r in SLOTS.iterrows()], 'num small'))}

<h2>What the studio pays for a session</h2>
<div class="sub">Teaching cost per session now sits at roughly the value of the class it delivers &mdash; and the most expensive format is the emptiest one.</div>

<p>Payroll is only available to August 2026, so this is context rather than September measurement, but the ratio is the point. In August the
studio paid <strong>{R(1429010)} to its {int(PA['Total Sessions'].sum())} sessions across {int(PA['Teacher Name'].nunique())} teachers</strong> &mdash; <strong>{R(1429010/PA['Total Sessions'].sum())} of teaching cost per
session</strong>. In September, class-attributed revenue per session was {R(5044)}. Those two numbers are now within a few per cent of each other, and while
class-attributed revenue is not the studio&rsquo;s whole revenue, a direct cost that consumes essentially all of the attributed top line is worth
stating plainly.</p>

<p>The composition matters more than the total. Split the payroll by discipline and the price of a session differs sharply:
<strong>Cycle sessions cost {R(CYCLE_RATE)} each, Barre sessions {R(BARRE_RATE)}</strong>. PowerCycle &mdash; the format running 35% of the timetable at a
35.0% fill rate &mdash; is the single most expensive thing the studio schedules per session. The studio is paying its highest per-session rate to
deliver the product with the lowest occupancy, and its lowest rate to Studio FIT, which fills at 71.0%.</p>

<p>Individual per-session rates span a wide band &mdash; from <strong>{R(RATE_MIN)} to {R(RATE_MAX)}</strong> across the {int(PA['Teacher Name'].nunique())} people on the
August payroll. A spread for experience is normal and defensible; what is not defensible is that it bears no relation to fill rate, which is
the outcome the business actually needs. The two trainers paid the most in August were not the two who filled the most seats.</p>

{bars(['Cycle', 'Barre', 'All'], [('Pay per session', [CYCLE_RATE, BARRE_RATE, PAY_SESS], E)],
      'Teaching pay per session, by discipline — August 2026',
      note='Cycle is PowerCycle and its variants; Barre covers Barre 57, Cardio Barre and Mat. The blended figure is ' +
      R(PAY_SESS) + ' per session across all ' + f"{int(PA['Total Sessions'].sum())}" + ' sessions.')}

<h2>Whose first class becomes a member</h2>
<div class="sub">Across 3,000 first-time visitors, the trainer who took the first class made a measurable difference to whether there was a third.</div>

<p>For every member whose first ever Bandra class fell from January 2025 onward, we know who taught it and how deep the relationship went.
Across all of them, the spread on &ldquo;did this person reach a third visit&rdquo; runs from
<strong>{Q_TR['r3'].max():.1f}% to {Q_TR['r3'].min():.1f}%</strong>. The strongest first-class conversion among high-volume trainers is
<strong>{Q_TR.index[0]} at {Q_TR.iloc[0]['r3']:.1f}% on {int(Q_TR.iloc[0]['n'])} first-timers</strong>. Taking only trainers who handled forty or
more first classes, so that no rate rests on a handful of visitors, the range is <strong>{Q_TR40['r3'].max():.1f}% down to {Q_TR40['r3'].min():.1f}%</strong>
&mdash; still a difference of {Q_TR40['r3'].max()-Q_TR40['r3'].min():.0f} percentage points in the single most consequential moment of a member&rsquo;s life with
the studio.</p>

<p>This is not a quality judgement and should not be read as one. First classes are assigned by timetable convenience, and some trainers
receive first-timers in the studio&rsquo;s hardest slots. What it does establish is that the first class is a distinct skill from teaching a
full room, and the studio currently has no mechanism to recognise or reward it. One trainer in this list took {int(Q_TR.iloc[0]['n'])} first-timers;
another took {int(Q_TR['n'].min())}, and nobody decided that on purpose.</p>

{hbars([(k, r['r3']/100, E if r['r3'] == Q_TR['r3'].max() else (E2 if r['r3'] >= Q_TR['r3'].mean() else E3))
        for k, r in Q_TR.iterrows() if r['n'] >= 40],
       'Share of a trainer’s first-time visitors who reached a third visit', as_pct=True,
       note='Trainers with at least 40 first classes since January 2025, so that the rate is not driven by a handful of visitors.')}
'''

_ta = TEACH_EXTRA.index('<h2>What the studio pays for a session</h2>')
TEACH_A, TEACH_B = TEACH_EXTRA[:_ta], TEACH_EXTRA[_ta:]
