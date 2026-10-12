"""Report 3 of 3 — Instructor Performance, Supreme HQ Bandra, September 2026."""
import pandas as pd, numpy as np
import d1_data as D
import d2_extra as X
from d2_extra import TEACH_A, TEACH_B
from d0_common import *

TCH, TF, TSLOT, CLI, CLI_SEP = D.TCH, D.TF, D.TSLOT, D.CLI, D.CLI_SEP
ACT, ACT_SLOTS, PAY, PAY_HIST, PAY_TREND = D.ACT, D.ACT_SLOTS, D.PAY, D.PAY_HIST, D.PAY_TREND
x26, x25 = D.x26, D.x25
C26, C25 = D.CL[2026], D.CL[2025]

TR = TCH[TCH['sessions'] > 0].copy()
KN = len(TR)
ATT = int(x26['CheckedIn'].sum())
SESS = len(x26)

# top-3 concentration
T3 = TR.nlargest(3, 'sessions')
T3_SHARE = T3['sessions'].sum()/SESS*100

# ------------------------------------------------------------------ charts
CH_REV = hbars([(i, r['rev'], BLU if r['rev'] >= 120000 else GOLD) for i, r in TR.sort_values('rev', ascending=False).iterrows()],
    'Revenue attributed to each trainer\u2019s classes, September 2026', maxv=215000,
    note=f'The top three trainers \u2014 Vivaran Dhasmana, Atulan Purohit and Reshma Sharma \u2014 account for {R(TR.nlargest(3,"rev")["rev"].sum())}, or {TR.nlargest(3,"rev")["rev"].sum()/C26["rev"]*100:.0f}% of the month\u2019s class revenue.')

CH_FILL = hbars([(i, r['fill'], BLU if r['fill'] >= 50 else (GOLD if r['fill'] >= 38 else TER))
                 for i, r in TR.sort_values('fill', ascending=False).iterrows()],
    'Capacity utilisation by trainer \u2014 who fills their room', maxv=72, as_pct=True,
    note=f'From {TR["fill"].max():.0f}% to {TR["fill"].min():.0f}% \u2014 the strongest trainer fills {TR["fill"].max()/TR["fill"].min():.1f} times as many seats as the weakest. Utilisation is the cleanest single measure of whether a trainer is being given the right slots.')

CH_SESS = bars([i for i in TR.sort_values('sessions', ascending=False).index[:10]],
    [('Sessions run', TR.sort_values('sessions', ascending=False)['sessions'].head(10).tolist(), GREY),
     ('Attendees (1/5 scale)', [v/5 for v in TR.sort_values('sessions', ascending=False)['att'].head(10)], TER)],
    'Sessions run against attendance drawn \u2014 the top ten trainers', as_pct=False, ymax=60, h=330, rotate=True,
    note='Vivaran Dhasmana teaches the most sessions but does not draw the most people. Atulan Purohit teaches 27 sessions and draws 205 attendees \u2014 the same as Vivaran draws from 39.')

CH_YOY = diverging([(i, r['d_att']) for i, r in TR.sort_values('d_att').iterrows() if not pd.isna(r['d_att'])],
    'Change in attendance drawn per trainer, September 2026 against September 2025', maxv=140,
    note='Attendance moved by more than 100 people in both directions between two trainers. This is not a studio-wide drift; it is a redistribution.')

CH_REVHEAD = hbars([(i, r['rev_head'], BLU if r['rev_head'] >= 1000 else GOLD)
                    for i, r in TR[TR['att'] > 0].sort_values('rev_head', ascending=False).iterrows()],
    'Revenue per attendee by trainer \u2014 who teaches the members on richer plans', maxv=1150,
    note='A narrow spread, from \u20b9798 to \u20b91,073. Unlike utilisation, revenue-per-head is fairly even, which means differences in trainer revenue come almost entirely from how many people they teach, not from who they teach.')

CH_PAYROLL = lines([str(p)[2:] for p in PAY_TREND.index[-12:]],
    [('New clients seen', PAY_TREND['new'].tail(12).tolist(), GREY),
     ('Converted to membership (x10)', [v*10 for v in PAY_TREND['convd'].tail(12)], TER)],
    'New clients seen and converted per month, all Bandra trainers combined', as_pct=False, ymax=160,
    note='Payroll data runs to August 2026 and is not available for September. Conversions are shown at 10x scale. The divergence from mid-2026 is the pattern the September member data also shows.')

CH_SLOTS = hbars([(i, r['slots'], BLU) for i, r in ACT_SLOTS.iterrows()],
    'Recurring weekly slots held by each trainer (currently active)', maxv=15, unit='',
    note=f'{int(ACT_SLOTS["slots"].sum())} active recurring slots across {len(ACT_SLOTS)} trainers. Vivaran Dhasmana holds {int(ACT_SLOTS["slots"].max())}, one in every seven of the studio\u2019s recurring timetable.')

CH_CLIENTS = hbars([(i, r['conv_%'], BLU if r['conv_%'] >= 22 else GOLD)
                    for i, r in CLI[CLI['clients'] >= 40].sort_values('conv_%', ascending=False).iterrows()],
    'Lifetime conversion rate of the clients each trainer taught first (40+ clients)', maxv=32, as_pct=True,
    note='This is the outcome measure, and it is the only one in this report that links a trainer to what happens to a client after the first class. It ranges from 18.8% to 30.0%.')

# ------------------------------------------------------------------ tables
main_rows = []
for i, r in TR.iterrows():
    main_rows.append([i, f"{int(r['sessions'])}", f"{int(r['att'])}", f"{r['avg_class']:.2f}", P(r['fill']),
                      P(r['lc_rate']), f"{int(r['formats'])}", R(r['rev']), R(r['rev_class']),
                      R(r['rev_head']) if pd.notna(r['rev_head']) else '\u2014'])
MAIN_T = T(['Trainer', 'Sessions', 'Attendees', 'Avg class', 'Utilisation', 'Late-cancel rate',
            'Formats', 'Revenue', 'Revenue / class', 'Revenue / attendee'], main_rows, 'mono')

yoy_rows = []
for i, r in TR.sort_values('d_att').iterrows():
    if pd.isna(r['d_att']): continue
    yoy_rows.append([i, f"{int(r['s25'])}", f"{int(r['sessions'])}", f"{int(r['d_sessions']):+}".replace('-', '\u2212'),
                     f"{int(r['a25'])}", f"{int(r['att'])}", f"{int(r['d_att']):+}".replace('-', '\u2212'),
                     R(r['r25']), R(r['rev']), Rs(r['rev']-r['r25'])])
YOY_T = T(['Trainer', 'Sessions 2025', 'Sessions 2026', 'Change', 'Attendees 2025', 'Attendees 2026',
           'Change', 'Revenue 2025', 'Revenue 2026', 'Change'], yoy_rows, 'mono')

fmt_rows = [[i, j.replace('Studio ', ''), f"{int(r['sessions'])}", f"{int(r['seats'])}", f"{int(r['att'])}",
             P(r['fill']), R(r['rev']), R(r['rev']/r['sessions'])]
            for (i, j), r in TF.sort_values(['Trainer', 'rev'], ascending=[True, False]).iterrows()]
FMT_T = T(['Trainer', 'Format', 'Sessions', 'Seats', 'Attended', 'Utilisation', 'Revenue', 'Revenue / class'], fmt_rows, 'mono small')

slot_rows = [[i, r['Day'], str(r['Time'])[:5], f"{int(r['sessions'])}", f"{int(r['seats'])}", f"{int(r['att'])}",
              P(r['fill']), R(r['rev']), R(r['rev_class'])]
             for i, r in TSLOT[(TSLOT['sessions'] >= 2)].sort_values('fill', ascending=False).iterrows()]
SLOT_T = T(['Trainer', 'Day', 'Start', 'Sessions', 'Seats', 'Attended', 'Utilisation', 'Revenue', 'Revenue / class'], slot_rows, 'mono small')

dead_rows = [[i, r['Day'], str(r['Time'])[:5], f"{int(r['sessions'])}", f"{int(r['seats'])}", f"{int(r['att'])}",
              P(r['fill']), R(r['rev'])] for i, r in TSLOT[(TSLOT['sessions'] >= 2) & (TSLOT['fill'] < 20)].sort_values('fill').iterrows()]
DEAD_T = T(['Trainer', 'Day', 'Start', 'Sessions', 'Seats', 'Attended', 'Utilisation', 'Revenue'], dead_rows, 'mono small')

cli_rows = [[i, f"{int(r['clients'])}", f"{int(r['conv'])}", P(r['conv_%']), R(r['ltv']), f"{r['visits']:.2f}"]
            for i, r in CLI[CLI['clients'] >= 40].sort_values('conv_%', ascending=False).iterrows()]
CLI_T = T(['Trainer', 'Lifetime first-timers taught', 'Converted', 'Conversion rate', 'Value per client', 'Avg visits'], cli_rows, 'mono')

sep_rows = [[i, f"{int(r['clients'])}", P(r['clients']/143*100), f"{int(r['conv'])}", P(r['conv_%']), f"{r['visits']:.2f}"]
            for i, r in CLI_SEP.iterrows()]
SEP_T = T(['Trainer', 'September clients', 'Share of month', 'Converted', 'Conversion', 'Avg visits'], sep_rows, 'mono')

pay_rows = [[i, f"{int(r['Total Sessions'])}", f"{int(r['Total Customers'])}", R(r['paid']), f"{int(r['New'])}",
             f"{int(r['Converted'])}", P(r['conv']), f"{int(r['Retained'])}", P(r['ret'])]
            for i, r in PAY.iterrows()]
PAY_T = T(['Trainer', 'Sessions', 'Customers', 'Revenue paid', 'New clients', 'Converted', 'Conversion',
           'Retained', 'Retention'], pay_rows, 'mono')

payh = PAY_HIST.sort_values('convd', ascending=False)
payh_rows = [[i, f"{int(r['months'])}", f"{int(r['sessions'])}", f"{int(r['new'])}", f"{int(r['convd'])}",
              P(r['conv_calc']) if pd.notna(r['conv_calc']) else '\u2014', f"{int(r['retd'])}"]
             for i, r in payh.iterrows()]
PAYH_T = T(['Trainer', 'Months on record', 'Sessions taught', 'New clients seen', 'Converted', 'Conversion rate',
            'Retained'], payh_rows, 'mono')

slot_hold = pd.concat([ACT_SLOTS[['slots', 'classes']], TR[['sessions', 'att', 'fill']].rename(
    columns={'sessions': 'sep_sessions', 'att': 'sep_att', 'fill': 'sep_fill'})], axis=1)
slot_hold = slot_hold.sort_values('slots', ascending=False)
HOLD_T = T(['Trainer', 'Active recurring slots', 'Classes taught on those slots (lifetime)',
            'September sessions', 'September attendees', 'September utilisation'],
           [[i, f"{int(r['slots'])}", f"{int(r['classes'])}",
             f"{int(r['sep_sessions'])}" if pd.notna(r['sep_sessions']) else '\u2014',
             f"{int(r['sep_att'])}" if pd.notna(r['sep_att']) else '\u2014',
             P(r['sep_fill']) if pd.notna(r['sep_fill']) else '\u2014'] for i, r in slot_hold.iterrows()], 'mono')

# ------------------------------------------------------------------ recommendations
RECS = [
 ('01','Give Atulan Purohit and Rohan Dahima more of the week','Studio Manager + Head of Training',
  f'Atulan Purohit drew <strong>{int(TR.loc["Atulan Purohit","d_att"]):+} more attendees</strong> than last September from only {int(TR.loc["Atulan Purohit","d_sessions"]):+} more sessions, at <strong>{TR.loc["Atulan Purohit","fill"]:.1f}% utilisation</strong> \u2014 the highest of any trainer above 20 sessions. Rohan Dahima filled <strong>{TR.loc["Rohan Dahima","fill"]:.1f}%</strong> on {int(TR.loc["Rohan Dahima","sessions"])} sessions, second-highest. Both also sit in the top half on lifetime client conversion ({CLI.loc["Atulan Purohit","conv_%"]:.1f}% and {CLI.loc["Rohan Dahima","conv_%"]:.1f}%).',
  f'Both are currently under-used relative to their fill. Moving 6 of the studio\u2019s weakest slots to these two, and holding them to their current {TR.loc["Atulan Purohit","fill"]:.0f}% and {TR.loc["Rohan Dahima","fill"]:.0f}% utilisation, adds roughly {int(6*4.3*(TR.loc["Atulan Purohit","fill"]+TR.loc["Rohan Dahima","fill"])/200)} attendances a month against the slots they replace.'),
 ('02','Review the slots no one attends, whoever is teaching them','Studio Manager',
  f'<strong>{len(TSLOT[(TSLOT["sessions"]>=2) & (TSLOT["fill"]<20)])} recurring slots ran at under 20% utilisation</strong> in September across {TSLOT[(TSLOT["sessions"]>=2) & (TSLOT["fill"]<20)]["Trainer"].nunique()} trainers. The three worst \u2014 Anmol Sharma\u2019s Thursday 18:00 ({P(TSLOT.set_index(["Trainer","Day","Time"]).loc[("Anmol Sharma","Thursday","18:00:00"),"fill"])}), Mrigakshi Jaiswal\u2019s Wednesday 19:30 ({P(TSLOT.set_index(["Trainer","Day","Time"]).loc[("Mrigakshi Jaiswal","Wednesday","19:30:00"),"fill"])}) and Vivaran Dhasmana\u2019s Wednesday 07:30 ({P(TSLOT.set_index(["Trainer","Day","Time"]).loc[("Vivaran Dhasmana","Wednesday","07:30:00"),"fill"])}) \u2014 drew a combined {int(TSLOT.set_index(["Trainer","Day","Time"]).loc[("Anmol Sharma","Thursday","18:00:00"),"att"] + TSLOT.set_index(["Trainer","Day","Time"]).loc[("Mrigakshi Jaiswal","Wednesday","19:30:00"),"att"] + TSLOT.set_index(["Trainer","Day","Time"]).loc[("Vivaran Dhasmana","Wednesday","07:30:00"),"att"])} people from 18 scheduled classes.',
  f'Clearing or rescheduling these slots frees about {int(TSLOT[(TSLOT["sessions"]>=2) & (TSLOT["fill"]<20)]["seats"].sum()*0.5)} seat-hours a month and removes the single largest source of the studio\u2019s {int((x26["CheckedIn"]<=2).sum())} lean sessions. It also protects the trainers holding them, because a dead slot reads as a performance problem when it is a scheduling one.'),
 ('03','Separate trainer assessment from slot assessment','Head of Training',
  f'The spread across trainers looks alarming \u2014 {TR["fill"].max():.0f}% utilisation at the top against {TR["fill"].min():.0f}% at the bottom. But revenue per attendee is nearly flat across the whole group, from {R(TR["rev_head"].min())} to {R(TR["rev_head"].max())}. <strong>Trainers are not teaching different-value audiences; they are being handed differently-sized rooms at differently attractive times.</strong> Anmol Sharma is the clearest example: {P(CLI_SEP.loc["Anmol Sharma","conv_%"] if "Anmol Sharma" in CLI_SEP.index else np.nan)} conversion on September clients and the best client follow-through in the studio, while holding four 07:30 Monday slots that filled 11.5%.',
  'One rule: judge a trainer on utilisation of the slots they hold, not their raw fill rate. Applied for one quarter, it separates coaching problems from scheduling problems and stops the studio losing good instructors over dead hours.'),
 ('04','Stop the September concentration from repeating','Studio Manager',
  f'Reshma Sharma received <strong>{CLI_SEP["clients"].max()} of September\u2019s 143 new clients \u2014 {CLI_SEP["clients"].max()/143*100:.0f}% of the month\u2019s intake</strong>, more than double any other trainer, and none of them returned for a second class. Across the studio, the top three trainers by session volume taught {T3["sessions"].sum()} of {SESS} classes ({T3_SHARE:.0f}%).',
  'Cap any trainer\u2019s share of first-time clients at 15%, and route every new client to a second trainer and a second format. The concentration finding is set out in full in the September performance review; this recommendation is the standing rule that prevents it recurring.'),
 ('05','Put trainer-level conversion into the monthly review','Head of Training + CRM',
  f'Payroll records show Bandra&rsquo;s combined new-client conversion falling from <strong>{PAY_TREND.loc["2025-09-01","conv_calc"]:.1f}% in September 2025 to {PAY_TREND.loc["2026-08-01","conv_calc"]:.1f}% in August 2026</strong> \u2014 the last month for which payroll data exists. Within the same table individual trainers range from {PAY["conv"].min():.0f}% to {PAY["conv"].max():.0f}%. Pranjali Jain converted {PAY.set_index("Teacher Name").loc["Pranjali Jain","conv"]:.1f}% of new clients with {PAY.set_index("Teacher Name").loc["Pranjali Jain","ret"]:.1f}% retention in August; three trainers converted none.',
  'A single monthly table of trainers by new clients seen, converted and retained would have surfaced both the studio-level decline and the individual spread several months earlier. It costs nothing to produce from data the studio already holds.'),
 ('06','Give the newer trainers a defined client-handover role','Head of Training',
  f'Four trainers who barely taught in September 2025 now hold meaningful volume \u2014 Reshma Sharma ({int(TR.loc["Reshma Sharma","sessions"])} sessions), Pranjali Jain ({int(TR.loc["Pranjali Jain","sessions"])}), Anmol Sharma ({int(TR.loc["Anmol Sharma","sessions"])}) and Rohan Dahima ({int(TR.loc["Rohan Dahima","sessions"])}). Between them they drew {int(TR.loc[["Reshma Sharma","Pranjali Jain","Anmol Sharma","Rohan Dahima"],"att"].sum())} attendances. Their lifetime client conversion rates ({CLI.loc["Pranjali Jain","conv_%"]:.1f}% for Pranjali, {CLI.loc["Anmol Sharma","conv_%"]:.1f}% for Anmol) sit below the studio\u2019s established trainers.',
  f'A structured pairing \u2014 every new client taught by a developing trainer gets one follow-up class with an experienced one \u2014 costs no acquisition spend and directly addresses the second-visit gap that the main review values at roughly \u20b92 lakh a month.'),
 ('07','Rebuild the recurring timetable around 98 slots, not 14 trainers','Programming + Studio Manager',
  f'The studio currently runs <strong>{int(ACT_SLOTS["slots"].sum())} active recurring weekly slots</strong> across {len(ACT_SLOTS)} trainers. Vivaran Dhasmana holds {int(ACT_SLOTS["slots"].max())} of them and Anisha Shah holds 4. Lifetime fill on those slots ranges from {ACT_SLOTS["fill"].min():.0f}% to {ACT_SLOTS["fill"].max():.0f}%. Anisha Shah&rsquo;s 4 slots fill {ACT_SLOTS.set_index(ACT_SLOTS.index).loc["Anisha Shah","fill"]:.0f}% on aggregate; Anmol Sharma&rsquo;s 8 fill {ACT_SLOTS.loc["Anmol Sharma","fill"]:.0f}%.',
  'The recurring timetable is the studio\u2019s product, and it should be reviewed slot by slot each quarter with utilisation as the criterion \u2014 not reassigned wholesale when a trainer joins or leaves. That is the difference between a schedule and an inheritance.'),
 ('08','Protect the trainers who fill their rooms','Studio Manager',
  f'{TR["fill"].max() and TR.nlargest(3,"fill").index.tolist()[0]} fills {TR["fill"].max():.0f}% and {TR.nlargest(3,"fill").index.tolist()[1]} {TR.nlargest(3,"fill")["fill"].iloc[1]:.0f}%. Five trainers who carried a large share of 2025 classes took {abs(D.TCH.loc[["Cauveri Vikrant","Karanvir Bhatia","Karan Bhatia","Simonelle De Vitre","Mrigakshi Jaiswal"],"sessions"].sum()/D.TCH.loc[["Cauveri Vikrant","Karanvir Bhatia","Karan Bhatia","Simonelle De Vitre","Mrigakshi Jaiswal"],"s25"].sum()*100-100):.0f}% fewer classes this September, and their lifetime clients were worth ₹8,701 each against ₹6,617 for the group that replaced them.',
  'Retention of proven instructors is cheaper than recruitment. A quarterly retention conversation anchored on each trainer\u2019s utilisation and client-conversion numbers gives the studio something concrete to manage, and gives the trainer something concrete to be recognised for.'),
 ('09','Align per-session pay with the room, not the day','Finance + Head of Training',
  f'In August the studio paid {R(X.PAY_SESS)} per session across {int(X.PA["Total Sessions"].sum())} sessions. Split by discipline, Cycle sessions cost {R(X.CYCLE_RATE)} each and Barre sessions {R(X.BARRE_RATE)}. PowerCycle runs 35% of the timetable at a 35% fill rate, while Studio FIT fills 71% \u2014 so the highest per-session pay is attached to the emptiest product, and individual rates across the payroll span {R(X.RATE_MIN)} to {R(X.RATE_MAX)} with no relationship to utilisation.',
  f'A modest re-weighting \u2014 holding the pay envelope constant but tying part of it to each session\u2019s fill against its format benchmark \u2014 makes the studio\u2019s biggest controllable cost respond to its biggest controllable problem, without cutting anyone\u2019s rate.'),
 ('10','Give the first class to the trainers who convert it','Head of Training + Studio Manager',
  f'Across {int(X.Q_TR["n"].sum())} first-time visitors since January 2025, the share who reached a third visit ranges from {X.Q_TR["r3"].min():.1f}% to {X.Q_TR["r3"].max():.1f}% by who taught the first class. The top of that range is approached by trainers who each took {int(X.Q_TR.iloc[0]["n"])} and {int(X.Q_TR.iloc[1]["n"])} first classes, while others took {int(X.Q_TR.iloc[-1]["n"])} and {int(X.Q_TR.iloc[-2]["n"])}. The assignment is currently a by-product of the rota.',
  f'If the bottom-half trainers moved to the group median, the studio would gain roughly {int(X.Q_TR["n"].sum()*(X.Q_TR["r3"].median()-X.Q_TR["r3"].min())/100)} additional members reaching a third visit a year \u2014 which, at the studio\u2019s own first-to-third conversion economics, is the single highest-value reallocation available that costs nothing.'),
 ('11','Publish the shared-slot table every month','Head of Training',
  f'Twenty-four slots were taught by two or more trainers in September. The median gap between the best and worst trainer within the same slot was {X.MED_SPREAD:.1f} points, and six slots showed more than 30 points. In the remaining slots the gap was small enough that the trainer is not the variable.',
  'One table a month, naming the trainer on each side of every shared slot, ends the argument about whether utilisation differences are the trainer or the timetable. It also gives the studio a fair way to move slots: on evidence, in the same class, at the same hour.'),
 ('12','Match the premium formats to the rooms they deserve','Programming + Studio Manager',
  f'PowerCycle is the studio\u2019s most expensive format to run ({R(X.CYCLE_RATE)} per session in August against {R(X.BARRE_RATE)} for Barre) and its least occupied ({X.PC_FILL:.1f}%). The same product fills {X.PCE_FILL:.1f}% in its express form and 52.6% at Cardio Barre Express. This is not a demand problem for the format; it is a demand problem for the slot and the room it sits in.',
  f'Rebuilding PowerCycle at express length and eleven-seat rooms \u2014 the configuration where every other Cycling variant fills \u2014 addresses the two largest cost lines in the report at once: the most expensive sessions to run and the emptiest rooms in the studio.')
,
 ('13','Judge trainers on the client journey, not only the session','Head of Training + CRM',
  f'One in four of September\u2019s classes drew two people or fewer, and the trainers who hold those slots show it in their utilisation whatever they do. '
  f'The measure that separates them is what happens next: <strong>{X.Q_TR["r3"].max():.0f}% of one trainer\u2019s first-time visitors reach a third visit, against '
  f'{X.Q_TR["r3"].min():.0f}% of another\u2019s</strong>.',
  'Utilisation measures who walked into the room and is largely decided by the timetable. The share of a trainer\u2019s first-timers who come back a second and third '
  'time measures what the trainer did once they were there, and it is the only trainer metric in this report that predicts the studio\u2019s economics.'),
 ('14','Rotate one matched slot a month as a live test','Head of Training + Programming',
  f'Across the matched slots the median gap is {X.MED_SPREAD:.0f} points and {X.BIG} of {X.N_SLOT} separate by more than thirty. The rest of the spread is the slot. '
  f'Nobody currently knows which is which, because the timetable is rebuilt by programme rather than by comparison.',
  'Taking the single widest matched slot each month and deliberately swapping the two trainers settles the question in four weeks, at no cost, with the studio\u2019s '
  'own data. Repeating it through the year turns a one-off analysis into a staffing principle.'),
]
REC_HTML = rec_html(RECS)

SRC = f'''<h4>Sources and method</h4>
<p>Four exports, all at a snapshot of 11 October 2026. <strong>Day End Report &ndash; Part 3 &ndash; Sessions</strong> (25,675 class occurrences) is the operational record: who taught, which format, at what hour, to how many people. <strong>Day End Report &ndash; Part 3 &ndash; Teacher Recurring</strong> (3,294 rows) aggregates the same data per recurring weekly slot and reconciles to the Sessions file exactly. <strong>Day End Report &ndash; Part 1 &ndash; Payroll</strong> (1,120 rows) gives the studio&rsquo;s own per-trainer monthly conversion and retention record. <strong>Day End Report &ndash; Part 1 &ndash; New</strong> (21,171 member records) supplies the client-outcome view: what happened to the members each trainer taught first.</p>
<h4>The three lenses, and why all three are needed</h4>
<p>An instructor can be read three ways and the three readings disagree often enough to matter. <strong>Operationally</strong> &mdash; how many classes, how full, how much revenue. <strong>Commercially</strong> &mdash; the studio&rsquo;s own payroll conversion and retention record per trainer. <strong>By client outcome</strong> &mdash; what the members a trainer taught first went on to be worth. This report shows all three side by side, because a trainer can fill a room and still produce clients who never return, and a trainer can hold dead slots and still be the best developer of new members in the studio.</p>
<h4>Known limitations</h4>
<ul>
 <li><strong>Payroll stops in August 2026.</strong> No September payroll record exists, so the studio&rsquo;s own conversion and retention numbers cannot be shown for the month under review. Where payroll figures appear they are labelled with their month.</li>
 <li><strong>Small samples.</strong> Several trainers taught under 10 sessions in September and three taught fewer than five. Their percentages are shown for completeness but should not be read as performance signals; the workbook flags sample sizes.</li>
 <li><strong>Attribution is not causation.</strong> "First-class trainer" is the instructor who took a client&rsquo;s very first visit, and it is the only trainer link the data supports. Clients choose classes as well as trainers, so the relationship is measurable but not causal.</li>
 <li><strong>No trainer cost.</strong> This data contains no pay rates or cost per class, so revenue is gross and no margin per trainer can be calculated.</li>
 <li><strong>The recurring-slot fill rates</strong> in the final table are lifetime figures across each slot&rsquo;s full history, not September-only, and are labelled as such.</li>
</ul>'''

BODY = f'''
<div class="kpis">
 <div class="kpi"><div class="l">Trainers teaching</div><div class="v">{KN}</div><div class="d">across {SESS} classes and {int(TR["formats"].sum())} trainer-format combinations</div></div>
 <div class="kpi"><div class="l">Top trainer by revenue</div><div class="v">{TR['rev'].max() and R(TR['rev'].max())}</div><div class="d">Vivaran Dhasmana, on {int(TR.loc['Vivaran Dhasmana','sessions'])} sessions</div></div>
 <div class="kpi"><div class="l">Utilisation spread</div><div class="v">{TR['fill'].max()/TR['fill'].min():.1f}&times;</div><div class="d neu">{TR['fill'].max():.0f}% at the top against {TR['fill'].min():.0f}% at the bottom</div></div>
 <div class="kpi"><div class="l">Revenue per attendee</div><div class="v">{R(TR['rev_head'].min())}&ndash;{R(TR['rev_head'].max())}</div><div class="d pos">a narrow band &mdash; the audience is similar everywhere</div></div>
</div>
<div class="kpis" style="margin-top:16px">
 <div class="kpi"><div class="l">Top 3 concentration</div><div class="v">{P(T3_SHARE)}</div><div class="d neu">of all classes taught by three trainers</div></div>
 <div class="kpi"><div class="l">Active recurring slots</div><div class="v">{int(ACT_SLOTS['slots'].sum())}</div><div class="d">held by {len(ACT_SLOTS)} trainers &mdash; the studio&rsquo;s actual product</div></div>
 <div class="kpi"><div class="l">Slots under 20% full</div><div class="v">{len(TSLOT[(TSLOT['sessions']>=2) & (TSLOT['fill']<20)])}</div><div class="d neg">across {TSLOT[(TSLOT['sessions']>=2) & (TSLOT['fill']<20)]['Trainer'].nunique()} trainers &mdash; a scheduling problem, not a teaching one</div></div>
 <div class="kpi"><div class="l">Bandra conversion, Aug-26</div><div class="v">{P(PAY_TREND.loc['2026-08-01','conv_calc'])}</div><div class="d neg">&darr; from {P(PAY_TREND.loc['2025-09-01','conv_calc'])} in Sept 2025 &mdash; last available payroll month</div></div>
</div>

<h2>Start here</h2>
<div class="sub">Fourteen people, one timetable, and three different ways to read them</div>
<p>In September 2026, <strong>{KN} trainers taught {SESS} classes</strong> to {ATT:,} attendances and generated {R(C26['rev'])} of class-attributed revenue &mdash; {C26['rev']/C25['rev']*100-100:.0f}% more than the same month a year earlier. That headline is genuinely strong, and it is worth stating before anything else: on the studio&rsquo;s most important operational measure, this group of trainers improved the business.</p>
<p>Underneath the aggregate, the individual spread is wide and, more usefully, it is <strong>explainable</strong>. Utilisation ranges from {TR['fill'].max():.0f}% to {TR['fill'].min():.0f}%. Revenue per trainer ranges from {R(TR['rev'].min())} to {R(TR['rev'].max())}. Lifetimes client conversion ranges from {CLI[CLI['clients']>=40]['conv_%'].min():.1f}% to {CLI[CLI['clients']>=40]['conv_%'].max():.1f}%.</p>
<p>But the most important finding in this report is a negative one, and it changes how the other numbers should be read. <strong>Revenue per attendee is nearly flat across the entire group.</strong> Every trainer in the studio is teaching an audience worth roughly the same per head &mdash; from {R(TR['rev_head'].min())} to {R(TR['rev_head'].max())}, a spread of only {TR['rev_head'].max()/TR['rev_head'].min()*100-100:.0f}%. That means the large differences in trainer revenue are not about who the trainer is teaching or what the members are worth. They are about <strong>how many people are in the room</strong> &mdash; and how many people are in the room is a function of which slots the studio gave them.</p>
<div class="call blu">
<h3>The honest headline is about the timetable, not the people</h3>
<p>When utilisation varies {TR['fill'].max()/TR['fill'].min():.1f}x but revenue per attendee varies only {TR['rev_head'].max()/TR['rev_head'].min()*100-100:.0f}%, the variance is mostly in the assignment of slots. Trainers who hold Saturday mornings and 11:00 weekday slots fill their rooms; trainers who hold 07:30 Mondays and 18:00 Thursdays do not. <strong>The studio is currently measuring its trainers with a number that is substantially determined by its own scheduling decisions.</strong></p>
<p>That is the single most actionable finding in this report, and the cheapest to act on: assess trainers on how well they fill <em>the slots they hold</em>, and separately assess whether those slots should exist at all.</p>
<p>Two things complicate that clean story, and this edition adds both. <strong>First, the trainer is not irrelevant.</strong> In the
{X.N_SLOT} slots taught by more than one trainer this September &mdash; the only fair test the data allows &mdash; the median gap between the best and
worst trainer teaching the same class at the same hour was <strong>{X.MED_SPREAD:.1f} percentage points</strong>. Slot assignment explains most of the
variance, not all of it. <strong>Second, the studio is paying for the emptiest room.</strong> In August it paid {R(X.PAY_SESS)} per session, but
{R(X.CYCLE_RATE)} for a Cycle session against {R(X.BARRE_RATE)} for a Barre session &mdash; so the format that runs 35% of the timetable at a 35% fill rate is
also the most expensive one to run.</p>
</div>

<h2>The scorecard</h2>
<div class="sub">September 2026, all fourteen trainers</div>
{CH_REV}
{MAIN_T}
<p>Vivaran Dhasmana taught the most classes ({int(TR.loc['Vivaran Dhasmana','sessions'])}) and generated the most revenue ({R(TR.loc['Vivaran Dhasmana','rev'])}), but at {TR.loc['Vivaran Dhasmana','fill']:.1f}% utilisation he is filling fewer than two seats in five. Atulan Purohit taught {int(TR.loc['Atulan Purohit','sessions'])} sessions &mdash; barely two thirds as many &mdash; drew the same {int(TR.loc['Atulan Purohit','att'])} attendees, and generated {R(TR.loc['Atulan Purohit','rev'])} at <strong>{TR.loc['Atulan Purohit','fill']:.1f}% utilisation, the best of any trainer with more than 20 sessions</strong>.</p>
<p>Measured per class, Atulan Purohit earned {R(TR.loc['Atulan Purohit','rev_class'])} and Rohan Dahima {R(TR.loc['Rohan Dahima','rev_class'])}, against Vivaran Dhasmana&rsquo;s {R(TR.loc['Vivaran Dhasmana','rev_class'])} and Karanvir Bhatia&rsquo;s {R(TR.loc['Karanvir Bhatia','rev_class'])}. That is a {TR.loc[['Atulan Purohit','Rohan Dahima'],'rev_class'].mean()/TR.loc[['Karanvir Bhatia','Vivaran Dhasmana'],'rev_class'].mean():.2f}x difference in what an hour of the same studio&rsquo;s time produces, before any consideration of cost.</p>
{CH_FILL}
{CH_SESS}
<p>The pattern is consistent and it repeats across the table: <strong>the trainers with the fewest sessions are often the ones filling them best.</strong> That is not coincidence &mdash; it usually means a trainer has been given a small number of good slots, while the highest-volume trainers carry the marginal ones. It is worth being explicit that this is a compliment to nobody and a criticism of nobody. It is what a timetable looks like when slots are allocated by seniority or availability rather than by demand.</p>
{ev('View every trainer-format combination for September', FMT_T)}
{ev('View the September trading against September 2025, trainer by trainer', YOY_T)}

{TEACH_A}

<h2>What changed in a year</h2>
<div class="sub">A redistribution, not a decline</div>
{CH_YOY}
<p>The year-on-year table is where the September story becomes concrete. Attendance moved by more than 100 people in both directions between individual trainers, while the studio total fell only {abs(C26['att']/C25['att']*100-100):.1f}%. <strong>Students did not leave the studio. They moved between its trainers.</strong></p>
<p>On the rising side, <strong>Atulan Purohit drew {int(TR.loc['Atulan Purohit','d_att']):+} attendees</strong> on {int(TR.loc['Atulan Purohit','d_sessions']):+} sessions, and <strong>Pranjali Jain {int(TR.loc['Pranjali Jain','d_att']):+}</strong> on {int(TR.loc['Pranjali Jain','d_sessions']):+} sessions. Rohan Dahima added {int(TR.loc['Rohan Dahima','d_att']):+} on {int(TR.loc['Rohan Dahima','d_sessions']):+}. On the falling side, <strong>Karanvir Bhatia lost {abs(int(TR.loc['Karanvir Bhatia','d_att']))} attendees</strong> and Reshma Sharma lost {abs(int(TR.loc['Reshma Sharma','d_att']))} despite teaching {int(TR.loc['Reshma Sharma','d_sessions']):+} more sessions.</p>
<div class="call gold">
<h3>Reshma Sharma&rsquo;s September, read next to her year</h3>
<p>She taught {int(TR.loc['Reshma Sharma','sessions'])} sessions against 4 in September 2025 &mdash; the largest increase in teaching load of anyone in the studio &mdash; and received {CLI_SEP['clients'].max()} of the month&rsquo;s {143} new clients. Her classes filled {TR.loc['Reshma Sharma','fill']:.1f}% of capacity and her late-cancellation rate was {TR.loc['Reshma Sharma','lc_rate']:.1f}%, the lowest of any trainer above 20 sessions. Her lifetime clients convert at {CLI.loc['Reshma Sharma','conv_%']:.1f}%, against a studio average of {CLI['conv_%'].mean():.1f}%.</p>
<p>None of that contradicts the finding in the main September review that not one of her {CLI_SEP['clients'].max()} September clients returned. Both are true: she absorbed the largest load increase in the studio, held one of the biggest intakes of the year, and that intake converted at zero. The concentration &mdash; {CLI_SEP['clients'].max()/143*100:.0f}% of a month&rsquo;s acquisition through one pair of hands with no second look &mdash; is the studio&rsquo;s problem to fix, not hers to carry.</p>
</div>


<h2>Where the week actually goes</h2>
<div class="sub">Recurring slots, and the ones nobody attends</div>
{CH_SLOTS}
{HOLD_T}
<p>The recurring timetable &mdash; <strong>{int(ACT_SLOTS['slots'].sum())} weekly slots</strong> &mdash; is the studio&rsquo;s real product. It is more stable than any monthly figure and it determines what members can book. It is also unevenly distributed: Vivaran Dhasmana holds {int(ACT_SLOTS['slots'].max())}, Anisha Shah {int(ACT_SLOTS.loc['Anisha Shah','slots'])}.</p>
{DEAD_T}
<p>{len(TSLOT[(TSLOT['sessions']>=2) & (TSLOT['fill']<20)])} recurring slots ran at under 20% utilisation in September. The three worst &mdash; Anmol Sharma&rsquo;s Thursday 18:00, Mrigakshi Jaiswal&rsquo;s Wednesday 19:30 and Vivaran Dhasmana&rsquo;s Wednesday 07:30 &mdash; drew a combined {int(TSLOT.set_index(['Trainer','Day','Time']).loc[('Anmol Sharma','Thursday','18:00:00'),'att'] + TSLOT.set_index(['Trainer','Day','Time']).loc[('Mrigakshi Jaiswal','Wednesday','19:30:00'),'att'] + TSLOT.set_index(['Trainer','Day','Time']).loc[('Vivaran Dhasmana','Wednesday','07:30:00'),'att'])} people from 18 scheduled classes.</p>
<p>This matters for how the studio manages people. A trainer holding three dead slots will show a poor utilisation number no matter how well they teach, and a trainer holding three Saturday mornings will show a good one. Until the slots are separated from the trainer in the reporting, the numbers will keep telling the studio about its schedule while appearing to tell it about its staff.</p>
<div class="call">
<h3>Anmol Sharma is the counter-example that proves the point</h3>
<p>He shows {P(TR.loc['Anmol Sharma','fill'])} utilisation &mdash; among the lowest in the studio. He also placed <strong>6 of 14 September clients into a second class</strong>, the best client follow-through of any trainer in the month, and his clients averaged <strong>{CLI_SEP.loc['Anmol Sharma','visits']:.1f} visits</strong> against a studio average of {CLI_SEP['visits'].mean():.2f}. His four Monday 07:30 slots filled 11.5%. His Thursday 18:00 slot filled 3.8%.</p>
<p>He is, on the evidence, an unusually effective developer of new members who has been given a set of hours nobody wants to attend. Any performance system that ranked trainers by utilisation alone would have identified him as the problem. That is the failure mode this report exists to prevent.</p>
</div>
{ev('View every recurring slot that ran two or more times, ranked by utilisation', SLOT_T)}

<h2>What happens to the clients</h2>
<div class="sub">The outcome measure &mdash; and the one that matters most</div>
{CH_CLIENTS}
{CLI_T}
<p>This is the measure with the longest horizon and the greatest commercial weight, because the second visit is what converts a trial into a member. Across trainers with at least 40 first-time clients, conversion ranges from <strong>{CLI[CLI['clients']>=40]['conv_%'].min():.1f}% to {CLI[CLI['clients']>=40]['conv_%'].max():.1f}%</strong> and value per client from {R(CLI[CLI['clients']>=40]['ltv'].min())} to {R(CLI[CLI['clients']>=40]['ltv'].max())} &mdash; a {CLI[CLI['clients']>=40]['ltv'].max()/CLI[CLI['clients']>=40]['ltv'].min():.1f}x spread on identical class hours.</p>
<p>The top of this table is where the studio&rsquo;s best developer of new members sits: <strong>Karan Bhatia at {CLI.loc['Karan Bhatia','conv_%']:.1f}% conversion and {R(CLI.loc['Karan Bhatia','ltv'])} per client on {int(CLI.loc['Karan Bhatia','clients'])} first-time clients</strong>, and <strong>Atulan Purohit at {CLI.loc['Atulan Purohit','conv_%']:.1f}% with the highest client value in the group at {R(CLI.loc['Atulan Purohit','ltv'])}</strong>. Note that Karan Bhatia taught only {int(TR.loc['Karan Bhatia','sessions'])} classes in September, down from {int(TR.loc['Karan Bhatia','s25'])} a year earlier &mdash; the studio&rsquo;s strongest converter of new clients has had his teaching load cut by {abs(TR.loc['Karan Bhatia','d_sessions']/TR.loc['Karan Bhatia','s25']*100):.0f}%.</p>
<div class="stat">
 <div><div class="v">{CLI.loc['Karan Bhatia','conv_%']:.1f}%</div><div class="l">Conversion, Karan Bhatia &mdash; highest in the studio</div></div>
 <div><div class="v">{R(CLI.loc['Atulan Purohit','ltv'])}</div><div class="l">Value per client, Atulan Purohit</div></div>
 <div><div class="v">{CLI_SEP['clients'].max()}</div><div class="l">September clients taught by one trainer</div></div>
 <div><div class="v">{P(CLI_SEP[CLI_SEP['conv']==0].shape[0]/len(CLI_SEP)*100)}</div><div class="l">Of September trainers converted nobody</div></div>
</div>
{SEP_T}
{ev('View lifetime client outcomes for every trainer with 20 or more first-time clients', CLI_T)}

<h2>The studio&rsquo;s own measure</h2>
<div class="sub">Payroll conversion and retention &mdash; through August 2026</div>
<p>The payroll export carries the studio&rsquo;s own per-trainer record: clients seen, converted and retained. It is the most direct trainer-accountability data the studio holds. It also <strong>stops at August 2026</strong>, so there is no September figure against which to hold this month&rsquo;s cohort. The last available month is shown below.</p>
{PAY_T}
<p>In August 2026 the pattern was highly uneven. <strong>Pranjali Jain converted {PAY.set_index('Teacher Name').loc['Pranjali Jain','conv']:.1f}% of new clients and retained {PAY.set_index('Teacher Name').loc['Pranjali Jain','ret']:.1f}%</strong> &mdash; the best combined result in the studio. Mrigakshi Jaiswal and Anisha Shah each converted 50% on small samples. At the other end, <strong>Karan Bhatia, Simonelle De Vitre and Richard D&rsquo;Costa converted none of their new clients</strong>, on 9, 2 and 3 new clients respectively. Vivaran Dhasmana saw the most new clients ({int(PAY.set_index('Teacher Name').loc['Vivaran Dhasmana','New'])}) and converted {PAY.set_index('Teacher Name').loc['Vivaran Dhasmana','conv']:.1f}% of them.</p>
{CH_PAYROLL}
{PAYH_T}
<p>Across the whole payroll record, Bandra&rsquo;s combined conversion of new clients has fallen from <strong>{PAY_TREND.loc['2025-09-01','conv_calc']:.1f}% in September 2025 to {PAY_TREND.loc['2026-08-01','conv_calc']:.1f}% in August 2026</strong>, while the number of new clients seen rose from {int(PAY_TREND.loc['2025-09-01','new'])} to {int(PAY_TREND.loc['2026-08-01','new'])}. More new faces, fewer conversions &mdash; the same pattern the lead register and the member cohort file both show from their own directions.</p>
{ev('View each trainer\u2019s full payroll record at Bandra', PAYH_T + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Conversion rate is recomputed here from raw counts of new clients and conversions, because the platform\u2019s own monthly rate is computed on a subset and averages differently. Months on record indicates how many monthly payroll rows exist for that trainer at Bandra.</p>')}

{TEACH_B}


<h2>Recommendations</h2>
<div class="sub">Fourteen actions, ordered by expected value</div>
<p>The first two are scheduling decisions that require no spend and can be taken before next month&rsquo;s timetable is published. The rest change how trainers are measured, supported and retained.</p>
{REC_HTML}

<h2>Method and limitations</h2>
<div class="sub">How to read these numbers, and what they cannot show</div>
{SRC}'''

HTML = page('Supreme HQ, Bandra \u2014 Instructor Performance, September 2026',
            'Instructor Performance Review &nbsp;&middot;&nbsp; September 2026',
            'Supreme HQ, Bandra',
            f'{KN} trainers taught {SESS} classes to {ATT:,} attendances in September and generated {C26["rev"]/C25["rev"]*100-100:.0f}% more class revenue than a year earlier. Utilisation across them ranges {TR["fill"].max()/TR["fill"].min():.1f}-fold \u2014 but revenue per attendee varies by only {TR["rev_head"].max()/TR["rev_head"].min()*100-100:.0f}%, which says the spread is mostly in the slots trainers were given, not in the trainers themselves.',
            f'Held against the slot it was given, the picture changes: inside the same day, hour and format, the trainer still moved the room by a median of '
            f'{X.MED_SPREAD:.0f} points, and in {X.BIG} of {X.N_SLOT} slots the spread exceeded 30. That is a real effect &mdash; and in '
            f'{int((X.SLOTS["spread"] <= 10).sum())} slots it disappears entirely.',
            f'<span>{KN} trainers</span><span>{int(ACT_SLOTS["slots"].sum())} recurring slots</span><span>Class, recurring, payroll and member data</span><span>Snapshot 18 October 2026</span>',
            BODY)
open('/home/user/Bandra_September_2026_3_Instructor_Performance.html','w').write(HTML)
print('Report 3 written:', len(HTML), 'bytes')
print('trainers', KN, '| spread', round(TR['fill'].max()/TR['fill'].min(),2), '| revhead spread', round(TR['rev_head'].max()/TR['rev_head'].min()*100-100,1))
