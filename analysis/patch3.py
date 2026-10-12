import re, shutil

src = '/home/user/analysis/build_report2.py'
dst = '/home/user/analysis/build_report3.py'
s = open(src).read()
n0 = len(s)

def sub(old, new, count=1):
    global s
    assert old in s, 'ANCHOR NOT FOUND: ' + old[:90]
    s = s.replace(old, new, count)

# ---------------------------------------------------------------- 1. import the round-3 module
sub("K['ev_conv_gap_val'] = ev_conv_gap * LTV_CONV\n",
    "K['ev_conv_gap_val'] = ev_conv_gap * LTV_CONV\n\n"
    "# ---------------------------------------------------------------- ROUND 3\n"
    "import sys as _sys; _sys.path.insert(0, '/home/user/analysis')\n"
    "from r3 import BLOCKS as R3, CH as R3CH, TB as R3TB, RECS3, SHEETS as R3SHEETS, K3\n")

# ---------------------------------------------------------------- 2. header
sub('''<p class="lede">September brought the studio its highest September intake on record. It also produced the month's weakest conversion. This review reads September inside the year it belongs to, tests the obvious explanations against the data, and identifies where the value actually went.</p>
 <div class="meta">
  <span>143 new clients</span><span>Member-level CRM snapshot, 11 Oct 2026</span><span>Equal-observation methodology</span>
 </div>''',
'''<p class="lede">September brought the studio its highest September intake on record. It also produced its weakest conversion, and the second-weakest retention. This edition reads September against three years of history, adds the check-in ledger, the lead register and the sales ledger to the member file, tests eight candidate explanations against the data &mdash; and finds three that hold, one of which was not visible in any of the earlier numbers.</p>
 <div class="meta">
  <span>143 new clients</span><span>150,895 check-ins &middot; 25,315 leads &middot; 25,044 sales</span><span>Equal-observation methodology</span>
 </div>''')

# ---------------------------------------------------------------- 3. KPIs
sub('''<div class="kpis">
 <div class="kpi"><div class="l">New clients</div><div class="v">{len(sep)}</div><div class="d pos">▲ 44% above September 2025 — the strongest September on record</div></div>
 <div class="kpi"><div class="l">Share of network intake</div><div class="v">36.6%</div><div class="d pos">▲ up from 27.7% in September 2025</div></div>
 <div class="kpi"><div class="l">30-day 2nd-visit rate</div><div class="v">{P(K['mw_second_pct'])}</div><div class="d neu">▼ against a {P(K['base_second'])} trailing norm — the month's central issue</div></div>
 <div class="kpi"><div class="l">Projected value shortfall</div><div class="v">{R(K['shortfall'])}</div><div class="d neu">September cohort, against normal lifetime yield</div></div>
</div>''',
'''<div class="kpis">
 <div class="kpi"><div class="l">New clients</div><div class="v">{len(sep)}</div><div class="d pos">▲ 44% above September 2025 — the strongest September on record</div></div>
 <div class="kpi"><div class="l">Share of network intake</div><div class="v">36.6%</div><div class="d pos">▲ up from 27.7% in September 2025</div></div>
 <div class="kpi"><div class="l">Genuine 2nd-visit rate</div><div class="v">{P(K3['true2nd'])}</div><div class="d neu">▼ not the headline {P(K3['head2nd'])} — 11 of 24 "returns" were pre-paid</div></div>
 <div class="kpi"><div class="l">Projected value shortfall</div><div class="v">{R(K['shortfall'])}</div><div class="d neu">September cohort, against normal lifetime yield</div></div>
</div>
<div class="kpis" style="margin-top:16px">
 <div class="kpi"><div class="l">Studio cash received</div><div class="v">{R(K3['cash26'])}</div><div class="d pos">▬ within {abs(K3['cash_yoy']):.1f}% of September 2025 — the till held</div></div>
 <div class="kpi"><div class="l">Funded by the existing base</div><div class="v">{P(K3['base_share'])}</div><div class="d neu">▲ new clients contributed only {P(100-K3['base_share'])} of September</div></div>
 <div class="kpi"><div class="l">Lead-to-member win rate</div><div class="v">{P(K3['w26_rate'])}</div><div class="d neu">▼ from {P(K3['w25_rate'])} a year ago, on {K3['lead_yoy']:.0f}% more leads</div></div>
 <div class="kpi"><div class="l">Footfall</div><div class="v">{seats['Sept 2026']['filled']:,}</div><div class="d pos">▬ against {seats['Sept 2025']['filled']:,} last September — essentially flat</div></div>
</div>''')

# ---------------------------------------------------------------- 4. Start-here prose
sub('''<p>What September did was concentrate a set of already-visible weaknesses into a single month, in a way that is now measurable and therefore fixable.</p>''',
'''<p>What September did was concentrate a set of already-visible weaknesses into a single month, in a way that is now measurable and therefore fixable. This edition adds three further sources &mdash; the full 150,895-row check-in ledger, the 25,315-record lead register and the 25,044-record sales ledger &mdash; which together make it possible to say not just <em>what</em> happened in September but <em>where</em> it happened and <em>who</em> it happened to.</p>
<p>The short version of what those sources add. September's revenue was <strong>carried almost entirely by members the studio already had</strong>, which is why the month looked normal in the accounts while its future quietly thinned. <strong>Two thirds of the month's failed leads were simply never reached or asked for more time.</strong> The studio's second-visit rate is <strong>overstated by the intro pack, which pre-pays the second visit</strong>. And the single most consequential change at Bandra this year was not in marketing or pricing at all: <strong>it was who was standing at the front of the room.</strong></p>''')

# ---------------------------------------------------------------- 5. new reconciliation section
sub('''{CH2}

<h2>The September picture</h2>''',
'''{CH2}

<h2>The number that explains the others</h2>
<div class="sub">The month looked fine in the accounts because the existing base paid for it</div>
{R3['RECON']}

<h2>The September picture</h2>''')

# ---------------------------------------------------------------- 6. root-cause intro + new cards
sub('''<p>Several plausible explanations were examined. Four do not survive contact with the numbers. One does.</p>
<div class="hyp">
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Ganesh Chaturthi disrupted the month</h3>''',
'''<p>Eight candidate explanations were examined &mdash; the ones that are obvious, and the ones that are easy to miss. Four do not survive contact with the numbers. Three do, and they turn out to be linked.</p>
<div class="hyp">
 <div class="hcard"><div class="tag yes">Confirmed &mdash; first order</div><h3>The teaching roster turned over</h3>
  <p>Five trainers who carried a large share of client-facing classes in September 2025 &mdash; Cauveri Vikrant, Karanvir Bhatia, Karan Bhatia, Simonelle De Vitre and Mrigakshi Jaiswal &mdash; took <strong>{K3['dgrp_pct']:.0f}% fewer classes in September 2026</strong> ({K3['dgrp25']:,} down to {K3['dgrp26']:,}). The group that absorbed that load rose from {K3['igrp25']:,} classes to <strong>{K3['igrp26']:,}, up {K3['igrp_pct']:.0f}%</strong>. Their clients are worth materially different amounts: <strong>{R(lv_dep)} per new client for the departing group against {R(lv_new)} for the incoming one.</strong></p>
  <div class="verdict">The largest single change at Bandra between the two Septembers was not demand, price or marketing. It was an unmeasured swap of the people who deliver the first class &mdash; the one moment that determines whether a client ever comes back.</div>
 </div>
 <div class="hcard"><div class="tag yes">Confirmed</div><h3>One trainer held {K3['resh_share']:.0f}% of the month's intake, and none returned</h3>
  <p>Reshma Sharma received <strong>{K3['resh_n']} of September's 143 new clients &mdash; {K3['resh_share']:.0f}% of the entire month</strong>. Not one attended a second class, anywhere in the network. Trial-for-trial, her clients converted at <strong>0 of {K3['tri_resh_n']}</strong> against <strong>{K3['tri_oth_conv']} of {K3['tri_oth_n']} ({P(K3['tri_oth_rate'])})</strong> for the rest of the studio.</p>
  <div class="verdict">Her all-time record is unremarkable rather than poor, which is the point: a zero month can happen to anyone, and the studio should never have a quarter of its acquisition resting on one person with no second look.</div>
 </div>
 <div class="hcard"><div class="tag yes">Confirmed</div><h3>The lead pipeline stopped closing</h3>
  <p>Leads rose <strong>{K3['lead_yoy']:.0f}%</strong> year-on-year while wins fell <strong>{abs(K3['win_yoy']):.0f}%</strong>. Win rate collapsed from <strong>{P(K3['w25_rate'])} to {P(K3['w26_rate'])}</strong>. Of the {K3['fail_tot']:,} leads that closed as lost with a reason recorded, <strong>{P(K3['unresp'])} were simply unreachable and {P(K3['postponed'])} were postponements</strong>; only {P(K3['price_obj'])} cited price.</p>
  <div class="verdict">Interest is not the constraint. Follow-up is. This is the cheapest problem in the review to fix and the one with the shortest payback.</div>
 </div>
 <div class="hcard"><div class="tag no">Ruled out</div><h3>Ganesh Chaturthi disrupted the month</h3>''')

sub('''<div class="hcard"><div class="tag part">Contributing</div><h3>Follow-up execution on the 12–13 September weekend</h3>''',
'''<div class="hcard"><div class="tag no">Ruled out</div><h3>Capacity or attendance was down</h3>
  <p>Bandra ran <strong>{seats['Sept 2026']['sessions']} classes in September 2026 against {seats['Sept 2025']['sessions']} a year earlier</strong>, filled <strong>{seats['Sept 2026']['filled']:,} seats against {seats['Sept 2025']['filled']:,}</strong>, at {P(seats['Sept 2026']['util'])} capacity utilisation against {P(seats['Sept 2025']['util'])}. Average class size was {seats['Sept 2026']['avg']:.1f} against {seats['Sept 2025']['avg']:.1f}.</p>
  <div class="verdict">The studio ran very close to a normal schedule with a normal audience. Footfall fell only {abs((seats['Sept 2026']['filled']/seats['Sept 2025']['filled']-1)*100):.1f}% — there was no shortage of people in the room.</div>
 </div>
 <div class="hcard"><div class="tag part">Contributing</div><h3>Follow-up execution on the 12–13 September weekend</h3>''')

# ---------------------------------------------------------------- 7. new sections after root cause
sub('''{corr_t}
{ev('View the month-by-month driver table behind these correlations',''',
'''{corr_t}
{ev('View the month-by-month driver table behind these correlations',''')

sub('''{CH4}
{ph_t and ev('View September by Ganeshotsav phase across three years', ph_t)}''',
'''{CH4}
{ph_t and ev('View September by Ganeshotsav phase across three years', ph_t)}

<h2>The finding that was hiding</h2>
<div class="sub">Who was teaching, and what happened to the clients they received</div>
{R3CH['CHR1']}
{R3['ROSTER']}
{R3TB['roster_tbl'] and ev('View every trainer who gained or lost classes, with their all-time record', R3TB['roster_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Sept 2025 and Sept 2026 class counts from the check-in ledger. Lifetime clients, conversion and value per client from the member cohort file, which uses first-visit location. Trainer names include part-time and guest instructors.</p>')}
{R3['CONC']}
{R3TB['conc_tbl'] and ev('View September 2026 new clients by the trainer who taught their first class', R3TB['conc_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Every client in the September cohort, grouped by the trainer who took their first class. "Returned for any further visit" counts any subsequent check-in at any location, not only within 30 days.</p>')}

<h2>The pipeline problem</h2>
<div class="sub">More interest than ever, and less of it being closed</div>
{R3CH['CHR2']}
{R3['FUNNEL']}
{R3TB['ch_tbl'] and ev('View every lead channel with its full economics', R3TB['ch_tbl'] + '<p style="font-size:13.5px;color:#7A7267;margin-top:14px">Lifetime figures for Bandra leads. Win rate is leads with status "Won" as a share of all leads created. Value per lead is total recorded lifetime value divided by leads — which naturally penalises channels whose leads are still open.</p>')}
{R3CH['CHR3']}

<h2>The intro pack, and an honest second-visit rate</h2>
<div class="sub">The cheapest class the studio sells, and what it actually buys</div>
{R3['INTRO']}

<h2>What the studio did not see</h2>
<div class="sub">Three second-order effects, and one structural risk</div>
{R3['CAP']}
{R3['ATTR']}
{R3['BASE']}''')

# ---------------------------------------------------------------- 8. recommendations
sub("rec_html = ''.join(f'''<div class=\"rec\">",
    "RECS = RECS3\nrec_html = ''.join(f'''<div class=\"rec\">")
sub('''<h2>Recommendations</h2>
<div class="sub">Eight actions, ordered by expected value</div>''',
'''<h2>Recommendations</h2>
<div class="sub">Eight actions, ordered by expected value</div>
<p>These are ordered so that the first three can be acted on this week without spending anything. The two that involve spending or pricing &mdash; the intro pack and the channel mix &mdash; sit in the middle deliberately: they are worth more, but they should follow the free fixes rather than lead them.</p>''')

# ---------------------------------------------------------------- 9. method section update
sub('''<li><strong>Attribution.</strong> 28.7% of the September cohort has no source recorded. Channel conclusions are drawn from the 72% that is attributed.</li>''',
'''<li><strong>Attribution.</strong> 28.7% of the September cohort has no source recorded, and the gap is concentrated in the referral channel, where 48.3% of non-converting clients are unsourced against 24.0% for trials. Channel conclusions are drawn from the attributed majority.</li>
 <li><strong>The intro pack.</strong> A 2-for-1 buyer's second class is pre-paid and is not a repeat-purchase decision. Charts and tables elsewhere in this report use the ledger's own visit counts; where a genuine second-visit rate is quoted it excludes the 11 pre-paid redemptions in the September cohort. The studio should adopt "third visit" as the standard definition of a returning client for anyone who entered on the pack.</li>
 <li><strong>Trainer attribution.</strong> "First-class trainer" is the instructor who took a client's very first visit, and it is the only trainer link the data supports. It does not follow that a trainer caused a client's outcome; it does mean the relationship is measurable and worth monitoring.</li>
 <li><strong>Lead stage names.</strong> Drop-off reasons are drawn from the 2,572 Bandra leads that have closed as lost with a reason recorded. A further 4,244 non-won leads remain in open or in-progress stages and are excluded from that table.</li>''')

sub('''<p>Member-level CRM export ("Day End Report – Part 1 – New"), 21,171 rows covering 20,989 unique members, snapshot dated 11 October 2026. Cohort assignment is by first-visit location and month; home-location data is used only for base-health analysis. Every figure is reproduced by the scripts in <code>/analysis</code>, and all underlying tables are provided in the accompanying Excel workbook.</p>''',
'''<p>Four sources, all dated to the same snapshot. The member file ("Day End Report &ndash; Part 1 &ndash; New"), 21,171 rows covering 20,989 unique members, provides cohorts, conversion and lifetime value. The check-in ledger ("Day End Report &ndash; Part 4"), 150,895 attended-class records, provides attendance, class capacity, visit numbering, product-per-visit and trainer attribution. The lead register ("&#9678; PM &ndash; Leads"), 25,315 records, provides acquisition channels, stages and drop-off reasons. The sales ledger ("Sales &ndash; Raw"), 25,044 succeeded payments, provides cash received, discounting and the intro-pack programme.</p>
<p>Cohort assignment is by first-visit location and month; home-location data is used only for base-health analysis. Check-in records are joined to cohorts by member ID. Every figure is reproduced by the scripts in <code>/analysis</code> and <code>/analysis2</code>, and all underlying tables are provided in the accompanying Excel workbook.</p>''')

# ---------------------------------------------------------------- 10. workbook additions
sub("""print('Report + workbook written')""",
"""    for _nm, _dfr in R3SHEETS.items():
        try:
            rt(_dfr).to_excel(xw, sheet_name=_nm[:31], index=False)
        except Exception as _e:
            print('sheet skipped:', _nm, _e)

print('Report + workbook written')""")

# pre-compute the two roster value means used in the new hypothesis card
sub("from r3 import BLOCKS as R3, CH as R3CH, TB as R3TB, RECS3, SHEETS as R3SHEETS, K3",
"""from r3 import BLOCKS as R3, CH as R3CH, TB as R3TB, RECS3, SHEETS as R3SHEETS, K3
import r3 as _r3
_lvm = _r3.MB.assign(ltv_n=_r3._num(_r3.MB['Ltv'])).groupby('Trainer Name')['ltv_n'].mean()
lv_dep = _lvm.loc[_r3.CR].mean(); lv_new = _lvm.loc[_r3.IN].mean()""")

open(dst, 'w').write(s)
print('wrote', dst)
print('grew from', n0, 'to', len(s), 'bytes')
