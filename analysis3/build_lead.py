"""Report 8 - Lead performance and insights, Bandra."""
import pandas as pd, numpy as np
import e1_data as E
from d0_common import (R, Rs, P, N, T, ev, bars, lines, hbars, diverging, stacked, funnel, dumbbell,
                       page, rec_html, A1, A2, A3, B1, B2, N1, N2, INK, MUT)

TODAY = pd.Timestamp('2026-10-18')
LD = E.LD.copy()
LB = LD[LD['Bandra']].copy()
LB['won'] = LB['Status'] == 'Won'
LB['conv'] = LB['Conversion Status'] == 'Converted'
LB['LTVn'] = E.num(LB['LTV']); LB['Visitn'] = E.num(LB['Visits'])
LB['span'] = (LB['Converted To Customer At_d'] - LB['Created At_d']).dt.days
N_L = len(LB)
WON = int(LB['won'].sum())
TRIAL = int((LB['Trial Status'] == 'Trial Completed').sum())
RETAIN = int((LB['Retention Status'] == 'Retained').sum())
OPEN = int((LB['Status'] == 'Open').sum())
UNRESP = int((LB['Status'] == 'Unresponsive').sum())
LOST = int((LB['Status'] == 'Lost').sum())
DQ = int((LB['Status'] == 'Disqualified').sum())
TRIAL_WON = LB[LB['Trial Status'] == 'Trial Completed']['won'].mean()*100
NOTRIAL_WON = LB[LB['Trial Status'] == 'Not Tried']['won'].mean()*100
NOTRIAL_N = int((LB['Trial Status'] == 'Not Tried').sum())

# ------------------------------------------------------------ channel
CH = LB.groupby('Channel').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x == 'Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean'), vis=('Visitn', 'mean')).sort_values('leads', ascending=False)
CH['ltv'] = CH['ltv'].round(0); CH['vis'] = CH['vis'].round(1)
_CHN = {'Website & Online Sources': 'Website & online', 'Direct & Walk-in ◉ Leads': 'Direct & walk-in',
        'Referrals & Word-of-Mouth': 'Referrals & word of mouth', 'Calls, Messages & Automated Enquiries': 'Calls & messages',
        'Social Media & Influencer Marketing': 'Social & influencer', 'Miscellaneous & Other': 'Miscellaneous'}
CH['lbl'] = [_CHN.get(i, i) for i in CH.index]
WEB = CH.loc['Website & Online Sources']; CALL = CH.loc['Calls, Messages & Automated Enquiries']
WEB = CH.loc['Website & Online Sources']; CALL = CH.loc['Calls, Messages & Automated Enquiries']
REF = CH.loc['Referrals & Word-of-Mouth']; DIR = CH.loc['Direct & Walk-in ◉ Leads'] if 'Direct & Walk-in ◉ Leads' in CH.index else CH.iloc[1]

# ------------------------------------------------------------ named source
SRC = LB.groupby('Source Name').agg(leads=('ID', 'size'),
        trial=('Trial Status', lambda x: round((x == 'Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean'), vis=('Visitn', 'mean')).sort_values('leads', ascending=False)
SRC['ltv'] = SRC['ltv'].round(0); SRC['vis'] = SRC['vis'].round(1)
SRC = SRC[SRC['leads'] >= 40]
BIG_S = SRC.index[0]; BEST_S = SRC['won'].idxmax(); WORST_S = SRC['won'].idxmin()
BEST_LTV_S = SRC['ltv'].idxmax(); WORST_LTV_S = SRC['ltv'].idxmin()

# ------------------------------------------------------------ conversion span
w = LB[LB['won'] & LB['span'].notna() & (LB['span'] >= 0)].copy()
w['b'] = pd.cut(w['span'], [-1, 0, 1, 2, 3, 7, 14, 30, 90, 100000],
                labels=['the same day', 'the next day', 'two days', 'three days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 to 90 days', '91 days or more'])
SPAN = w.groupby('b', observed=True).agg(n=('ID', 'size'), ltv=('LTVn', 'mean'))
SPAN['ltv'] = SPAN['ltv'].round(0)
SPAN['share'] = (SPAN['n'] / SPAN['n'].sum() * 100).round(1)
SAME_DAY = int(SPAN.loc['the same day', 'n']); SAME_SHARE = SPAN.loc['the same day', 'share']
MED_SPAN = w['span'].median(); FAST_LTV = SPAN.loc['the same day', 'ltv']

# ------------------------------------------------------------ associates
ASSOC = LB.groupby('Associate').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x == 'Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1)), ltv=('LTVn', 'mean'), resp=('resp_days', 'median')).sort_values('won', ascending=False)
ASSOC = ASSOC[ASSOC['leads'] >= 30]
ASSOC['ltv'] = ASSOC['ltv'].round(0)
TOP_A = ASSOC.index[0]; LOW_A = ASSOC.index[-1]

# ------------------------------------------------------------ what leads ask for
CT = LB.groupby('Class Type').agg(leads=('ID', 'size'), trial=('Trial Status', lambda x: round((x == 'Trial Completed').mean()*100, 1)),
        won=('won', lambda x: round(x.mean()*100, 1))).sort_values('leads', ascending=False)
CT = CT[(CT['leads'] >= 100) & (~CT.index.isin(['-', 'nan']))]
_CTN = {'Barre 57': 'Barre 57', 'powerCycle': 'PowerCycle', 'PowerCycle': 'PowerCycle',
        'MAT': 'Mat 57', 'FIT': 'Studio FIT'}
CT['lbl'] = [_CTN.get(str(i), str(i).title()) for i in CT.index]
_PC = CT[CT.index.str.lower().str.contains('cycle')].iloc[0]
_PCL = CT[CT.index.str.lower().str.contains('cycle')].index[0]

# ------------------------------------------------------------ the open file
OP = LB[LB['Status'] == 'Open'].copy()
OP['age'] = (TODAY - OP['Created At_d']).dt.days
AGEB = ['0 to 14 days', '15 to 30 days', '31 to 60 days', '61 to 180 days', 'over 180 days']
OP['ab'] = pd.cut(OP['age'], [-1, 14, 30, 60, 180, 99999], labels=AGEB)
AGE = OP.groupby('ab', observed=True).size().reindex(AGEB).fillna(0)
AGE_WON = OP.groupby('ab', observed=True)['won'].sum().reindex(AGEB).fillna(0) if 'won' in OP else None
FRESH = int(AGE.loc['0 to 14 days'] + AGE.loc['15 to 30 days'])
STALE = int(AGE.loc['over 180 days'])
STUCK = OP[OP['Stage Name'].str.contains('Pricing', na=False)]
MEAN_AGE = OP['age'].mean()

# ------------------------------------------------------------ flow through 2026
M26 = LB[LB['Created At_d'] >= '2026-01-01']
FLOW = M26.groupby(M26['Created At_d'].dt.month).agg(
    leads=('ID', 'size'), trial=('Trial Status', lambda x: (x == 'Trial Completed').mean()*100),
    won=('won', lambda x: x.mean()*100), ltv=('LTVn', 'mean'))
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
FLOW = FLOW.reindex(range(1, len(FLOW)+1))
M25 = LB[(LB['Created At_d'] >= '2025-01-01') & (LB['Created At_d'] < '2026-01-01')]
FLOWN = M25.groupby(M25['Created At_d'].dt.month).size()
TRIAL_UP = FLOW['trial'].iloc[-2] - FLOW['trial'].iloc[0]
WON_DN = FLOW['won'].iloc[-2] - FLOW['won'].iloc[0]

# ------------------------------------------------------------ trial gate
TG = pd.DataFrame({'Trial Completed': ['Yes', 'No'],
                   'Leads': [TRIAL, NOTRIAL_N],
                   'Won_pct': [TRIAL_WON, NOTRIAL_WON],
                   'Mean_lifetime_value': [LB[LB['Trial Status'] == 'Trial Completed']['LTVn'].mean(),
                                           LB[LB['Trial Status'] == 'Not Tried']['LTVn'].mean()]})
TG['Mean_lifetime_value'] = TG['Mean_lifetime_value'].round(0)

# ------------------------------------------------------------ charts
CH_FUN = funnel([('Leads created', N_L, 'every enquiry the studio has recorded for Bandra'),
                 ('Trial completed', TRIAL, f'{TRIAL/N_L*100:.1f}% of leads'),
                 ('Membership sold', WON, f'{WON/N_L*100:.1f}% of leads, {WON/TRIAL*100:.1f}% of trials'),
                 ('Retained today', RETAIN, f'{RETAIN/N_L*100:.1f}% of leads')],
    'The whole acquisition funnel, enquiry to retained member')

CH_TG = bars(['Trial completed', 'Never took a trial'], [
    ('Leads', [TRIAL, NOTRIAL_N], A1),
    ('Share won, % (scaled ×5)', [TRIAL_WON*5, NOTRIAL_WON*5], B1)],
    'The trial is the gate, and almost nothing passes without it', h=300, ymax=4300,
    note=f'{TRIAL:,} leads completed a trial and {WON} of them bought. Of the {NOTRIAL_N:,} who never did, '
         f'{int(LB[LB["Trial Status"]=="Not Tried"]["won"].sum())} ever bought anything.')

CH_CH = bars(CH['lbl'].tolist(), [('Leads', CH['leads'].tolist(), A1),
                                  ('Share won, % (scaled ×10)', [v*10 for v in CH['won']], B1)],
    'The channels the studio uses, against the rate at which they convert', h=330, ymax=3900, rotate=True,
    note='The two largest channels by volume convert at roughly a third of the rate of the two smallest. The second series is drawn ten times its true size.')

CH_CHL = hbars([(r['lbl'], r['ltv'], A1 if r['ltv'] >= CH['ltv'].median() else B1) for _, r in CH.iterrows()],
    'Mean lifetime value of a lead, by the channel it arrived through', maxv=12000,
    note='Every lead the studio has ever recorded for Bandra, whether or not it converted.')

CH_SRC = bars(SRC.index.tolist(), [('Leads', SRC['leads'].tolist(), A1),
                                   ('Share won, % (scaled ×10)', [v*10 for v in SRC['won']], B1)],
    'The named source behind each lead, and how many become members', h=350, ymax=3600, rotate=True,
    note='Sources carrying forty or more Bandra leads. Trial completion is shown alongside in the evidence table.')

CH_SPAN = bars(list(SPAN.index), [('Wins', SPAN['n'].tolist(), A1)],
    'How long a lead took to become a member', h=320, ymax=660, rotate=True,
    note=f'{SAME_SHARE:.0f}% of every membership the studio sells is sold on the day of the enquiry. The median lead buys on the day it enquires.')

CH_SPANL = bars(list(SPAN.index), [('Mean lifetime value', SPAN['ltv'].tolist(), A2)],
    'What a win is worth, by how long it took', h=300, ymax=74000, rotate=True, as_pct=False,
    note='Same-day wins are the studio’s fastest business, and not its smallest. The long tail of patient leads is worth slightly more per head — but there are very few of them.')

CH_AS = bars(ASSOC.index.tolist(), [('Leads', ASSOC['leads'].tolist(), N2),
                                    ('Share won, % (scaled ×10)', [v*10 for v in ASSOC['won']], A1)],
    'Who handles the leads, and how many of them close', h=330, ymax=2700, rotate=True,
    note='Associates with thirty or more recorded Bandra leads. All of them work the same list at the same prices.')

CH_CT = bars(CT['lbl'].tolist(), [('Leads', CT['leads'].tolist(), A1),
                                  ('Share won, % (scaled ×10)', [v*10 for v in CT['won']], B1)],
    'The class a lead asks about, and whether it converts', h=300, ymax=6000,
    note='Class preference is recorded on almost every enquiry, which makes it the most complete statement of demand the studio holds.')

CH_AGE = hbars([(i, float(v), A1 if i != 'over 180 days' else B1) for i, v in AGE.items()],
    'The open file, by how long each lead has been sitting', unit='', maxv=None,
    note=f'Mean age of an open Bandra lead: {MEAN_AGE:.0f} days. {STALE:,} of them are more than six months old.')

CH_FLOW = lines(MONTHS[:len(FLOW)], [
    ('Trial completion, %', FLOW['trial'].round(1).tolist(), A1),
    ('Membership sold, %', FLOW['won'].round(1).tolist(), B1)],
    'How the 2026 lead cohort has behaved, month by month', h=330, as_pct=True, ymax=80,
    note='Read left to right, trial completion has risen sharply and conversion has not followed it.')

CH_FLOWN = lines(MONTHS[:12], [
    ('2025', [int(FLOWN.get(i, 0)) for i in range(1, 13)], N1),
    ('2026', [int(FLOW['leads'].get(i, 0)) if i in FLOW.index else 0 for i in range(1, 13)], A1)],
    'Leads created each month, 2025 against 2026', h=320, as_pct=False, ymax=380,
    note='The 2026 line is running below 2025 from March onwards, and September was the weakest month of the year.')

# ------------------------------------------------------------ recommendations
RECS = [
 ('01','Nothing matters more than the trial — treat it as the only target','Studio Manager + CRM',
  f'<strong>{TRIAL:,} of {N_L:,} Bandra leads completed a trial and {WON} of them became members. Of the {NOTRIAL_N:,} who never took a trial, {int(LB[LB["Trial Status"]=="Not Tried"]["won"].sum())} ever bought anything.</strong> '
  f'A completed trial converts at {TRIAL_WON:.1f}%; a lead without one converts at {NOTRIAL_WON:.2f}%. Mean lifetime value is {R(TG["Mean_lifetime_value"].iloc[0])} against {R(TG["Mean_lifetime_value"].iloc[1])}.',
  f'Every hour spent on a lead who has not booked a class is worth a fraction of the same hour spent getting that class booked. The studio’s single operational target should be the number of trials booked this week, '
  f'and every other lead metric should be read as a consequence of it.'),
 ('02','Answer on the day, because the sale is made on the day','Front Desk + CRM',
  f'<strong>{SAME_SHARE:.0f}% of every membership Bandra sells is sold the same day the enquiry arrives — {SAME_DAY} of {int(SPAN["n"].sum())} wins.</strong> The median wait from enquiry to purchase is {MED_SPAN:.0f} days. '
  f'Wins that took a month or more are {SPAN.loc[["31 to 90 days","91 days or more"],"n"].sum()/int(SPAN["n"].sum())*100:.0f}% of the volume and are worth {R(SPAN.loc[["31 to 90 days","91 days or more"],"ltv"].mean())} on average.',
  f'This is the most decisive number in the file. The studio is not running a nurture funnel; it is running a same-day counter. Response time is therefore not a service standard — it is the conversion rate, '
  f'delayed. A same-day callback on every new enquiry is the highest-yield process change available and it costs nothing.'),
 ('03','Fix the first-response date, then set a target against it','CRM + Front Desk',
  f'Median first response is {ASSOC["resp"].min():.0f} to {ASSOC["resp"].max():.0f} days across the team, and roughly a fifth of the records carry a follow-up date that precedes the enquiry itself — '
  f'the field is being back-filled rather than logged at the time.',
  f'A metric that can be written after the fact is not a metric. Until the first-response field is captured automatically, the studio cannot tell a two-hour call-back from a two-day one, and every '
  f'conversation about lead handling rests on recollection rather than record.'),
 ('04','Move the acquisition mix towards calls, referrals and walk-ins','Marketing',
  f'Website and online sources produce <strong>{WEB["leads"]:,} leads — {WEB["leads"]/N_L*100:.0f}% of everything Bandra attracts</strong> — at {WEB["won"]:.1f}% conversion and {R(WEB["ltv"])} of lifetime value. '
  f'Calls and messages produce {CALL["leads"]:,} at {CALL["won"]:.1f}% and {R(CALL["ltv"])}; referrals produce {REF["leads"]:,} at {REF["won"]:.1f}% and {R(REF["ltv"])}.',
  f'A referral lead is worth {CALL["ltv"]/WEB["ltv"]:.1f} times a website lead and converts {CALL["won"]/WEB["won"]:.1f} times as often. The studio does not need more leads; it needs the leads that already '
  f'know someone. A visible referral reward, published at the point of enquiry, is the cheapest mix change in this report.'),
 ('05','Decide what hosted classes are for','Programming + Marketing',
  f'Hosted classes generate <strong>{SRC.loc[BIG_S,"leads"] if BIG_S in SRC.index else 0:,} leads, and {SRC.loc[BIG_S,"trial"] if BIG_S in SRC.index else 0:.0f}% of them complete a trial — the highest trial rate of any source in the file</strong>. '
  f'But only {SRC.loc[BIG_S,"won"] if BIG_S in SRC.index else 0:.1f}% become members, at {R(SRC.loc[BIG_S,"ltv"]) if BIG_S in SRC.index else ""} of lifetime value.',
  f'Hosted classes are an excellent trial machine and a poor acquisition channel. Either the studio accepts them as community marketing and stops counting them as a growth channel, or it changes what '
  f'happens at the end of a hosted class — a booked next class rather than a card left on a table.'),
 ('06','Publish conversion by associate and manage the range','Studio Manager',
  f'Conversion ranges from <strong>{ASSOC["won"].min():.1f}% for {LOW_A} to {ASSOC["won"].max():.1f}% for {TOP_A}</strong> on the same product list at the same prices. Mean lifetime value per lead ranges from '
  f'{R(ASSOC["ltv"].min())} to {R(ASSOC["ltv"].max())}.',
  f'The strongest closer is not necessarily the one holding the biggest book, which is exactly why the range is worth publishing. A monthly table, without names attached, moves the middle of the '
  f'distribution; pairing the top performer with the largest in-box moves the top.'),
 ('07','Close the open file honestly','CRM',
  f'<strong>{OPEN:,} Bandra leads are still marked open and their mean age is {MEAN_AGE:.0f} days.</strong> {STALE:,} of them are more than six months old, and {len(STUCK):,} are sitting at the same stage — '
  f'pricing and schedule shared, decision never recorded.',
  f'An open lead that is two years old is not a pipeline; it is a missing status. A single afternoon of honest disposition — contactable, interested, or closed — would turn {OPEN:,} rows into a '
  f'short, real list and make every conversion figure the studio reports trustworthy again.'),
 ('08','Work the fresh open leads and stop counting the rest','CRM + Front Desk',
  f'Only {FRESH} open leads are less than thirty days old. Those are the ones the studio can still win, and they are a list one person could clear in a week.',
  f'Separating the file into a live queue and an archive is a five-minute change with a disproportionate payoff: it makes the daily follow-up task finite, and a finite task gets done. The archive should '
  f'still be contacted at renewal season, but it should not sit in the working list.'),
 ('09','Target the trial at the class people already name','Programming + Marketing',
  f'Barre 57 is named on <strong>{int(CT.loc["Barre 57","leads"]):,} leads</strong> and PowerCycle on {int(_PC["leads"]):,}. '
  f'Between them they account for {CT["leads"].sum()/N_L*100:.0f}% of all leads with a recorded preference.',
  f'The studio records what each lead wants and then books the trial into whatever slot is free. Matching the first class to the stated preference is a scheduling decision, not a marketing spend, and it '
  f'removes the commonest reason a first impression fails.'),
 ('10','Stop buying outdoor acquisition until it can be measured','Marketing',
  f'Outdoor classes produce <strong>{SRC.loc[WORST_S,"leads"] if WORST_S in SRC.index else 0:,} leads at {SRC.loc[WORST_S,"trial"] if WORST_S in SRC.index else 0:.0f}% trial completion, '
  f'{SRC.loc[WORST_S,"won"] if WORST_S in SRC.index else 0:.1f}% conversion and {R(SRC.loc[WORST_S,"ltv"]) if WORST_S in SRC.index else ""} of lifetime value</strong> — the weakest result in the file on every measure.',
  f'Every channel in this report should be held to the same two numbers: what it costs and what a lead from it is worth over a lifetime. Outdoor is currently the only line where those two are not '
  f'compared, and on the evidence it is the first budget the studio should question.'),
 ('11','Give the small, high-value sources more room','Marketing',
  f'Incoming calls produce {SRC.loc["Incoming call","leads"] if "Incoming call" in SRC.index else 0:,} leads at <strong>{SRC.loc["Incoming call","won"] if "Incoming call" in SRC.index else 0:.1f}% conversion and '
  f'{R(SRC.loc["Incoming call","ltv"]) if "Incoming call" in SRC.index else ""} of lifetime value</strong>. Influencer sign-ups produce {SRC.loc["Influencer Sign-up","leads"] if "Influencer Sign-up" in SRC.index else 0:,} leads at '
  f'{SRC.loc["Influencer Sign-up","won"] if "Influencer Sign-up" in SRC.index else 0:.1f}% and {R(SRC.loc["Influencer Sign-up","ltv"]) if "Influencer Sign-up" in SRC.index else ""}.',
  f'Neither is a volume channel and neither needs to be. Both return more per lead than anything the studio spends against at scale, and both are currently incidental rather than funded. A published '
  f'phone number and two more influencer partnerships are cheap experiments with a proven tail.'),
 ('12','Report leads weekly, not annually','Management',
  f'The studio’s lead reporting is retrospective. A weekly page carrying four numbers — leads created, trials booked, trials completed and memberships sold — would have shown the September '
  f'weakness in its first week rather than in this report.',
  f'Leads are the earliest signal the studio has: they move a full quarter before attendance does. A short weekly discipline on those four numbers turns this report from an explanation into an '
  f'early warning, and it needs no new system — only a standing appointment to read it.'),
]
REC_HTML = rec_html(RECS)

SRCBOX = f'''<h4>Sources and method</h4>
<p style="font-size:13.5px;color:#6B7280;line-height:1.7">
The CRM lead master holds {len(LD):,} records across all centres, of which {N_L:,} belong to Bandra and are used throughout. A lead is counted once, at creation, and its outcome is the
status the record carries at snapshot; recent cohorts are therefore understated for conversion and overstated for open. Channel, source, associate and class preference are the studio&rsquo;s own
fields, used as recorded.<br/>
Response time is the interval between the lead&rsquo;s creation and the first of four follow-up dates. The four comment fields are populated on every record but are largely administrative
placeholders, so contact quality cannot be measured from this file at all.<br/>
Lifetime value is the value the CRM carries against the lead, not an independently reconstructed figure; it is used for ranking channels against each other, which is the only comparison it
supports. Cash figures are as recorded at snapshot on 18 October 2026 and are not contribution margin.</p>'''

META = (f'CRM lead master &middot; {N_L:,} Bandra leads &middot; all time on file<br/>'
        f'{WON:,} memberships sold &middot; {RETAIN:,} retained &middot; {OPEN:,} still open<br/>'
        f'September 2026 intake &middot; {int(FLOW["leads"].get(9, 0))} leads &middot; September 2025 &middot; {int(FLOWN.get(9, 0))}<br/>Snapshot 18 October 2026')

HTML = page('Supreme HQ, Bandra — Lead Performance and Insights',
    'Lead Performance and Insights &nbsp;&middot;&nbsp; September 2026',
    'Supreme HQ, Bandra — where the members come from',
    f'{N_L:,} people have enquired at Bandra since the studio began recording leads. {WON:,} became members, {RETAIN:,} are still members today, and {OPEN:,} are still marked open. '
    f'This report reads the whole file to answer three questions: which channels produce members rather than enquiries, how fast a lead has to be handled to convert, and what the studio '
    f'is currently doing with the {OPEN:,} people who have not said no.',
    META, f'''
<h2>Start here</h2>
<div class="sub">The studio has a volume problem in its largest channel and a follow-through problem everywhere else. The trial is the gate, and the same day is the deadline.</div>

<p>Read the whole file and three things stand out above everything else.</p>

<p><strong>First, the trial decides everything.</strong> {TRIAL:,} of {N_L:,} leads completed a trial; {WON} of them bought. Of the {NOTRIAL_N:,} who never took a trial,
<strong>{int(LB[LB["Trial Status"]=="Not Tried"]["won"].sum())} ever bought anything</strong>. The trial is not a step in the funnel — it is the funnel.</p>

<p><strong>Second, the sale happens the day the enquiry arrives.</strong> <strong>{SAME_SHARE:.0f}% of every membership Bandra sells is sold on the same day</strong>,
and the median lead buys on the day it enquires. Everything after that is a small, slow tail.</p>

<p><strong>Third, the studio&rsquo;s biggest channel is its weakest.</strong> Website and online sources deliver {WEB["leads"]:,} leads — {WEB["leads"]/N_L*100:.0f}% of the file —
and convert {WEB["won"]:.1f}% of them at {R(WEB["ltv"])} of lifetime value. Calls, messages and referrals together deliver {CALL["leads"]+REF["leads"]:,} leads and convert
{(CALL["won"]*CALL["leads"]+REF["won"]*REF["leads"])/(CALL["leads"]+REF["leads"]):.1f}% of them at {R((CALL["ltv"]*CALL["leads"]+REF["ltv"]*REF["leads"])/(CALL["leads"]+REF["leads"]))}.</p>

<div class="call b"><h4>The single sentence version</h4>
<p>This is not a studio that cannot attract people. It is a studio that attracts {N_L:,} of them, converts the ones who walk in or ring up, and then leaves
{OPEN:,} of the rest sitting in a file whose average entry is {MEAN_AGE:.0f} days old.</p></div>

{CH_FUN}

<h2>The trial is the gate</h2>
<div class="sub">A lead who has taken a class converts at {(TRIAL_WON/NOTRIAL_WON):.0f} times the rate of a lead who has not. Nothing else in the file is close.</div>

<p>{TRIAL:,} leads completed a trial and <strong>{TRIAL_WON:.1f}% of them became members</strong>. Of the {NOTRIAL_N:,} who did not,
<strong>{NOTRIAL_WON:.2f}% converted</strong> — {int(LB[LB["Trial Status"]=="Not Tried"]["won"].sum())} people out of {NOTRIAL_N:,}. Mean lifetime value is
{R(TG["Mean_lifetime_value"].iloc[0])} against {R(TG["Mean_lifetime_value"].iloc[1])} — effectively nothing.</p>

{CH_TG}

<p>This single fact reorganises everything else in this report. Cost per lead, source quality and channel mix all matter, but they matter because they change how many trials get booked.
A channel that produces a hundred leads and twenty trials is worth more than one that produces three hundred leads and twenty trials, and the studio currently reports only the first number.</p>

{ev('Evidence — every lead, by whether a trial was ever completed',
    T(['Trial completed', 'Leads', 'Share of file', 'Ever won', 'Share won', 'Retained today', 'Mean lifetime value'],
      [['Yes', TRIAL, P(TRIAL/N_L*100), WON, P(TRIAL_WON), int(LB[LB['Trial Status']=='Trial Completed']['Retention Status'].eq('Retained').sum()),
        R(TG['Mean_lifetime_value'].iloc[0])],
       ['No', NOTRIAL_N, P(NOTRIAL_N/N_L*100), int(LB[LB['Trial Status']=='Not Tried']['won'].sum()), P(NOTRIAL_WON),
        int(LB[LB['Trial Status']=='Not Tried']['Retention Status'].eq('Retained').sum()), R(TG['Mean_lifetime_value'].iloc[1])]], 'num'))}

<h2>Speed decides it</h2>
<div class="sub">{SAME_SHARE:.0f}% of wins happen on day zero. The studio is a same-day counter with an unmeasured response time.</div>

<p>Of the {int(SPAN["n"].sum())} Bandra leads that converted and carry a usable date pair, <strong>{SAME_DAY} — {SAME_SHARE:.0f}% — bought on the same day they enquired</strong>.
The next day accounts for {SPAN.loc["the next day","share"]:.1f}%, and the whole of the first week for {SPAN.loc[["the same day","the next day","two days","three days","4 to 7 days"],"share"].sum():.1f}%.
The median lead buys on the day it enquires.</p>

{CH_SPAN}

<p>The tail is small but instructive. The {int(SPAN.loc[["31 to 90 days","91 days or more"],"n"].sum())} wins that took a month or longer are worth
{R(SPAN.loc[["31 to 90 days","91 days or more"],"ltv"].mean())} on average, against {R(FAST_LTV)} for same-day wins. Patience is rewarded, but only {SPAN.loc[["31 to 90 days","91 days or more"],"share"].sum():.1f}%
of the studio&rsquo;s business comes that way. The practical conclusion is not that slow leads are valuable; it is that a lead who has not converted within the first week is almost certainly gone.</p>

{CH_SPANL}

<div class="call"><h4>What this means for the front desk</h4>
<p>Every enquiry that arrives and is answered the next morning has already lost most of its value. The studio&rsquo;s conversion rate is therefore a description of how fast it answers,
not of how persuasive it is — and unlike persuasion, answering speed is entirely within its control.</p></div>

<h2>Where the leads come from</h2>
<div class="sub">Volume and value sit in different channels, and the gap between them is the studio&rsquo;s largest untapped gain.</div>

<p>Bandra records six channels. <strong>{WEB["lbl"]} is dominant at {WEB["leads"]:,} leads — {WEB["leads"]/N_L*100:.0f}% of the file</strong> — and converts at
{WEB["won"]:.1f}%. {CALL["lbl"]} brings {CALL["leads"]:,} leads at {CALL["won"]:.1f}%, and {REF["lbl"]} brings {REF["leads"]:,} at {REF["won"]:.1f}%.</p>

{CH_CH}
{CH_CHL}

<p>The named sources inside those channels sharpen the picture further. <strong>{BIG_S} is the largest source in the file at {int(SRC.loc[BIG_S,"leads"]):,} leads and the weakest of the major
sources at {SRC.loc[BIG_S,"won"]:.1f}%.</strong> {BEST_S} is the strongest at {SRC.loc[BEST_S,"won"]:.1f}% on {int(SRC.loc[BEST_S,"leads"])} leads, and {BEST_LTV_S} carries the highest lifetime value at {R(SRC.loc[BEST_LTV_S,"ltv"])}.
{WORST_S} is the weakest line in the file on every measure — {int(SRC.loc[WORST_S,"leads"])} leads, {SRC.loc[WORST_S,"trial"]:.0f}% trial completion, {SRC.loc[WORST_S,"won"]:.1f}% conversion and {R(SRC.loc[WORST_S,"ltv"])} of value.</p>

{CH_SRC}

{ev('Evidence — every source with forty or more Bandra leads',
    T(['Source', 'Leads', 'Trial completed', 'Won', 'Mean lifetime value', 'Mean visits'],
      [[i, int(r['leads']), P(r['trial']), P(r['won']), R(r['ltv']), f"{r['vis']:.1f}"] for i, r in SRC.iterrows()], 'num'))}

<h2>What leads ask for</h2>
<div class="sub">The studio records the class every lead wants. It is the most complete demand signal they hold, and it is not used.</div>

<p>Class preference is recorded on almost every Bandra lead. <strong>Barre 57 is named on {int(CT.loc["Barre 57","leads"]):,} leads</strong>, PowerCycle on
{int(_PC['leads']):,} — between them {CT["leads"].sum()/N_L*100:.0f}% of the entire file. They convert at almost identical rates
({CT.loc["Barre 57","won"]:.1f}% and {_PC["won"]:.1f}%).</p>

{CH_CT}

<p>Because the preference is stated at the point of enquiry, it is the cheapest personalisation the studio could act on: the trial should be booked into the class the lead asked for,
at the time they asked for it, wherever that is achievable. That is a scheduling decision rather than a marketing spend.</p>

<h2>Who handles the leads</h2>
<div class="sub">Eight associates, one product list, one price list — and a two-to-one spread in outcomes.</div>

<p>Across associates holding thirty or more Bandra leads, conversion runs from <strong>{ASSOC["won"].min():.1f}% to {ASSOC["won"].max():.1f}%</strong> and mean lifetime value per lead
from {R(ASSOC["ltv"].min())} to {R(ASSOC["ltv"].max())}. The strongest performer does not hold the smallest book, and the largest book does not produce the best result.</p>

{CH_AS}

{ev('Evidence — every associate with thirty or more Bandra leads',
    T(['Associate', 'Leads', 'Trial completed', 'Won', 'Mean lifetime value', 'Median response, days'],
      [[i, int(r['leads']), P(r['trial']), P(r['won']), R(r['ltv']), f"{r['resp']:.0f}"] for i, r in ASSOC.iterrows()], 'num'))}

<h2>The file the studio is not working</h2>
<div class="sub">{OPEN:,} open leads. A mean age of {MEAN_AGE:.0f} days. {STALE:,} of them more than six months old.</div>

<p>The open file is larger than every membership the studio has ever sold at Bandra. It is also, on the evidence of its own timestamps, almost entirely historical:
<strong>{FRESH} of the {OPEN:,} open leads are less than thirty days old</strong>, and <strong>{STALE:,} have been open for more than six months</strong>.
{len(STUCK):,} sit at the same stage — pricing and schedule shared, no decision ever recorded.</p>

{CH_AGE}

<p>That is not a pipeline. It is a filing cabinet, and it is distorting every conversion figure the studio reports, because a lead that was quietly lost two years ago is still
counted as in play. The honest disposition of this file is the least glamorous and most valuable piece of work on this page: it costs a week and it makes every subsequent
number trustworthy.</p>

{ev('Evidence — the open file, by age and by the stage it is stuck at',
    T(['Age of the lead', 'Open leads', 'Share of the open file'], [[i, int(v), P(v/OPEN*100)] for i, v in AGE.items()], 'num') +
    '<p style="font-size:13.5px;color:#6B7280;margin-top:16px"><strong>Where the open file is stuck</strong></p>' +
    T(['Stage', 'Leads'], [[i, int(v)] for i, v in OP['Stage Name'].value_counts().head(8).items()], 'num'))}

<h2>Lead flow through 2026</h2>
<div class="sub">Trial completion has risen sharply this year. Conversion has not followed it, and the volume is falling.</div>

<p>Read as a cohort — every lead grouped by the month it arrived — the 2026 file shows a studio getting better at the middle of its funnel and no better at the end of it.
<strong>Trial completion has moved from {FLOW["trial"].iloc[0]:.1f}% in January to {FLOW["trial"].iloc[-2]:.1f}% in September</strong>,
a rise of {TRIAL_UP:.0f} points. <strong>Conversion has moved from {FLOW["won"].iloc[0]:.1f}% to {FLOW["won"].iloc[-2]:.1f}%</strong>,
down {abs(WON_DN):.0f} points.</p>

{CH_FLOW}

<p>Volume tells the second half of the story. Bandra created <strong>{int(FLOW["leads"].get(9, 0))} leads in September</strong> against {int(FLOWN.get(9, 0))} in the same month last year,
and the 2026 line has run below 2025 from March onwards.</p>

{CH_FLOWN}

<p>Put together: fewer people are enquiring, more of those who do are getting into a class, and the same proportion are buying. The studio has fixed the part of the funnel it can see
and is losing the part it cannot — the top.</p>

{ev('Evidence — the 2026 lead cohort, month by month',
    T(['Month', 'Leads created', 'Trial completed', 'Won', 'Still open', 'Mean lifetime value'],
      [[MONTHS[i-1], int(r['leads']), P(r['trial']), P(r['won']),
        P(M26[M26['Created At_d'].dt.month == i]['Status'].eq('Open').mean()*100), R(r['ltv'])] for i, r in FLOW.iterrows()], 'num'))}

<h2>Recommendations</h2>
<div class="sub">Twelve actions, ordered by the value each releases</div>
{REC_HTML}
{SRCBOX}
''')
open('/home/user/reports-arena/Bandra_September_2026_8_Lead_Performance.html', 'w').write(HTML)
print(f'Report 8 written: {len(HTML)} bytes')
print('leads', N_L, 'won', WON, 'trial', TRIAL, 'retained', RETAIN, 'open', OPEN)
print('trial gate:', round(TRIAL_WON,1), 'vs', round(NOTRIAL_WON,2), '| not-tried wins', int(LB[LB['Trial Status']=='Not Tried']['won'].sum()))
print('span:', dict(SPAN[['n','ltv','share']].to_dict('index')))
print('channel:', CH[['leads','trial','won','ltv']].to_dict('index'))
print('source:', SRC[['leads','trial','won','ltv']].to_dict('index'))
print('assoc:', ASSOC[['leads','won','ltv']].to_dict('index'))
print('age:', AGE.to_dict(), '| stuck', len(STUCK), '| mean age', round(MEAN_AGE))
print('flow:', FLOW.round(1).to_dict('index'))
print('ct:', CT.to_dict('index'))
