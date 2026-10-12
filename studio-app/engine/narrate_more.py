"""A second pass of recommendations, one per table in the chapter.

The first pass in narrate.py states the four or five actions that follow from
the headline figures. This pass walks the evidence tables underneath - the
hour grid, the duration bands, the cancellation bands, the source table - and
turns each of them into an action a named person can take. Every line is
guarded, so a chapter built from a partial upload simply carries fewer.
"""
from __future__ import annotations
from .design import R


def _clean(label):
    return str(label).replace('Studio ', '')


def extra(M, cid, R_, add, cap=11):
    y = M.y
    lab = M.label
    F = M.room.get(y, {})

    def room():
        return cap - len(R_)

    # ── sales ────────────────────────────────────────────────────────────────
    if cid == 'sales' and room() > 0:
        try:
            h = M.sale_hours
            top, low = h['size'].idxmax(), h['size'].idxmin()
            add('Put a second pair of hands on the counter at the peak hour',
                'Front Desk',
                f'{int(top):02d}:00 took {int(h["size"].max())} transactions, {int(low):02d}:00 took {int(h["size"].min())}.',
                'The counter is the only place where a faster response converts directly into a larger ticket. Staffing should follow the hour grid, not the shift rota.')
        except Exception:
            pass
        try:
            c = M.cats
            add('Give the top two categories a bundle price',
                'Sales + Marketing',
                f'{str(c.index[0])} and {str(c.index[1])} together produced {R(c["sum"].iloc[0] + c["sum"].iloc[1])}, {(c["sum"].iloc[0] + c["sum"].iloc[1]) / M.sales[y]["cash"] * 100:.0f}% of the month, across {int(c["size"].iloc[0] + c["size"].iloc[1])} transactions.',
                'Two categories that are usually bought together can be priced together. It raises the average ticket without touching list prices.')
        except Exception:
            pass
        try:
            d = M.disc_year[y]
            add('Cap the depth and keep the spread',
                'Finance + Management',
                f'{M.sales[y]["spread"]:.0f}% of transactions carried a discount at {d["depth"]:.1f}% average depth, on {R(d["disc"])} of gross value.',
                'Spread is a policy decision and depth is a margin decision. Publishing an approved depth band converts an open negotiation into a rule the desk can apply.')
        except Exception:
            pass
        try:
            per_day = M.sales[y]['txn'] / max(M.days['sessions'].count() * 0 + 30, 1)
            add('Set a daily transaction target, not just a monthly one',
                'Studio Manager',
                f'{M.sales[y]["txn"]:,} transactions across the month is {per_day:.1f} a day, against {M.sales[y]["buyers"]:,} buyers.',
                'A daily number is visible while the month can still be changed. Monthly totals only ever arrive as news.')
        except Exception:
            pass
        try:
            s1 = M.sales.get(y - 1)
            if s1:
                add('Separate new-member cash from renewal cash in every report',
                    'Finance + CRM',
                    f'Cash per buyer was {R(M.sales[y]["ticket"])} this month against {R(s1["ticket"])} a year earlier, on {M.sales[y]["buyers"]:,} buyers against {s1["buyers"]:,}.',
                    'The two lines are managed by different teams, respond to different offers and carry different costs. One number cannot steer both.')
        except Exception:
            pass
        try:
            src = M.people
            add('Track the buyer, not the transaction, month on month',
                'Management',
                f'{M.sales[y]["buyers"]:,} people bought this month. Transaction counts rise easily when the same small group buys more often.',
                'A studio can lose a third of its buyers and still print a flat revenue line for a quarter. Only the buyer count warns you.')
        except Exception:
            pass

    # ── class ────────────────────────────────────────────────────────────────
    if cid == 'class' and room() > 0:
        try:
            d = M.days
            add('Rebuild the weakest weekday before adding any class',
                'Programming + Studio Manager',
                f'{d["fill"].idxmin()} filled {d["fill"].min():.1f}% across {int(d.loc[d["fill"].idxmin(), "sessions"])} classes while {d["fill"].idxmax()} filled {d["fill"].max():.1f}%.',
                'Shifting a class from the weakest day to the strongest costs nothing and lifts the room without touching the timetable size.')
        except Exception:
            pass
        try:
            h = M.hours.dropna()
            low = h.nsmallest(1, 'fill').index[0]
            add('Test a smaller room in the emptiest hours',
                'Studio Manager',
                f'{int(low):02d}:00 ran {int(h.loc[low, "sessions"])} classes at {h.loc[low, "fill"]:.0f}% fill, while the studio average was {F.get("fill", 0):.1f}%.',
                'Capacity is only wasted relative to demand. A short class in a small room can fill without changing who books it.')
        except Exception:
            pass
        try:
            add('Check the seat count against the book, class by class',
                'Programming',
                f'{F.get("seats", 0):,.0f} seats were offered for {F.get("att", 0):,.0f} attendances, so {F.get("seats", 0) - F.get("att", 0):,.0f} seats went unsold.',
                'Half the capacity problem is created by the room a class is put in. The seat count is editable and it costs nothing to change.')
        except Exception:
            pass
        try:
            s = M._sl(M.D.sessions, y)
            add('Decide the fate of every class that ran to nobody',
                'Programming',
                f'{int((s["CheckedIn"] == 0).sum())} classes had no attendees at all against {int((s["CheckedIn"] <= 2).sum())} with two or fewer.',
                'These are individual decisions, not a category. A one-page list with a keep, move or drop box next to each one clears the question in a single meeting.')
        except Exception:
            pass
        try:
            add('Publish capacity, bookings and show rate for the coming week',
                'Studio Manager',
                f'Utilisation for the month closed at {F.get("fill", 0):.1f}%.',
                'Seats sold three days ahead is a leading measure and it is available before the class runs. Show rate at the door is a lagging one.')
        except Exception:
            pass
        try:
            add('Keep one deliberate experiment slot in the timetable',
                'Programming',
                f'{len(M.formats)} formats ran this month, of which {len(M.formats) - len(getattr(M, "formats_main", M.formats))} appeared fewer than three times.',
                'New formats need a defended slot and a review date, or they quietly become nobody’s format and are judged on a handful of classes.')
        except Exception:
            pass

    # ── instructor ───────────────────────────────────────────────────────────
    if cid == 'instructor' and room() > 0:
        try:
            t = M.trainers
            add('Pair the strongest filler with the weakest slot before cutting it',
                'Programming + Studio Manager',
                f'{t["fill"].idxmax()} fills {t["fill"].max():.1f}% and {t["fill"].idxmin()} fills {t["fill"].min():.1f}% on the same timetable.',
                'Trialling the best performer in the weakest slot separates a demand problem from a coaching one, and it costs four weeks.')
        except Exception:
            pass
        try:
            t = M.trainers
            add('Give every regular a named trainer',
                'Studio Manager + CRM',
                f'{len(t)} trainers taught {t["sessions"].sum():,.0f} classes for {t["att"].sum():,.0f} attendances.',
                'The trainer relationship is the most durable retention asset a studio has. It has to be visible in the roster to be managed.')
        except Exception:
            pass
        try:
            t = M.trainers
            add('Review late-cancellation rate in the coaching conversation',
                'Studio Manager',
                f'Rates run from {t["lc_rate"].dropna().min():.1f}% to {t["lc_rate"].dropna().max():.1f}% on one policy.',
                'A rate that high is usually a slot that has slipped out of the members’ week. The fix is a timetable edit, not a reminder.')
        except Exception:
            pass
        try:
            add('Cost the roster per attendance, not per class',
                'Management + Finance',
                f'Revenue per attendance was {R(F.get("rph", 0))} across the month.',
                'Payroll per attendance is the only teaching cost that sits on the same basis as the revenue it supports.')
        except Exception:
            pass
        try:
            f = getattr(M, 'formats_main', M.formats)
            s_ = M._sl(M.D.sessions, y)
            sub = s_[s_['_cls'] == f.index[0]]
            add('Watch how many trainers share one format',
                'Programming',
                f'{_clean(f.index[0])} holds {sub["CheckedIn"].sum() / max(s_["CheckedIn"].sum(), 1) * 100:.0f}% of all attendances and is taught by {sub["_trainer"].nunique()} different trainers.',
                'Too many hands on one format flattens the standard and hides who is filling the room. The trainer list for each format belongs on the programming page.')
        except Exception:
            pass
        try:
            t = M.trainers
            add('Give the marginal slot to whoever already filled theirs',
                'Studio Manager',
                f'The utilisation spread is {t["fill"].max() / max(t["fill"].min(), 0.1):.1f} times.',
                'The next hour added should go to evidence rather than to the rota order. It is the cheapest capacity decision in the month.')
        except Exception:
            pass

    # ── lapse ────────────────────────────────────────────────────────────────
    if cid == 'lapse' and room() > 0:
        try:
            d = M.dur
            add('Make the mid-length products the default recommendation',
                'Sales + Marketing',
                f'Memberships of 31 to 60 days carry {R(d.loc[d["Membership Duration (Days)"] == "31 to 60 days", "ticket"].iloc[0])} of average cash against {R(d.loc[d["Membership Duration (Days)"] == "2 to 7 days", "ticket"].iloc[0])} for a week-long product.',
                'The short products are the ones that leave. What a member buys first predicts how long they stay far better than how much they liked the trial.')
        except Exception:
            pass
        try:
            d = M.dur
            tiny = d[d['Membership Duration (Days)'].isin(['same day', '2 to 7 days'])]
            add('Convert the single-class buyers before the week is out',
                'Front Desk + CRM',
                f'{int(tiny["n"].sum()):,} memberships lasted a week or less and used {tiny["cls"].mean():.2f} classes each.',
                'This is the largest, cheapest and most time-sensitive group in the ledger. A call on day three is worth more than any win-back offer in month three.')
        except Exception:
            pass
        try:
            s = M.status_mix
            add('Work the not-activated and grace-period files monthly',
                'CRM + Front Desk',
                f'{int(s.get("Not Activated", 0)):,} memberships never activated and {int(s.get("Renewal Grace Period", 0)):,} sit inside the grace window.',
                'Both are dated, small and contactable. A monthly standing list keeps this number from building up into a churn statistic.')
        except Exception:
            pass
        try:
            if hasattr(M, 'unused_low'):
                add('Offer the unspent classes back as visits, not as credit',
                    'CRM',
                    f'{M.unused_low:,} memberships used a quarter or less of what they paid for, leaving {M.unused_left:,.0f} classes unspent.',
                    'Undelivered classes are already paid for. Converting them into visits rebuilds the habit; converting them into credit only postpones the decision to leave.')
        except Exception:
            pass
        try:
            add('Price a three-month product deliberately',
                'Sales + Management',
                f'The median membership life is {int(getattr(M, "median_life", 0))} days.',
                'If the median life is inside the second month, a three-month product sets a different expectation and gives the studio two renewal conversations instead of one.')
        except Exception:
            pass
        try:
            add('Read churn by joining month, not only by product',
                'CRM',
                f'{M.led["rows"]:,} memberships sit in the ledger, {M.led["paid"]:,} of them paid.',
                'Members who joined in the same month behave similarly. Cohort lines show whether retention is improving or whether the mix is merely changing.')
        except Exception:
            pass

    # ── format ───────────────────────────────────────────────────────────────
    if cid == 'format' and room() > 0:
        try:
            f = getattr(M, 'formats_main', M.formats)
            add('Rebalance the block that carries most of the timetable',
                'Programming + Studio Manager',
                f'{_clean(f.index[0])} holds {f["share_sessions"].iloc[0]:.0f}% of all classes at {f["fill"].iloc[0]:.1f}% fill.',
                'A single format holding a third of the week makes the studio’s utilisation a property of that format rather than of the timetable.')
        except Exception:
            pass
        try:
            f = M.formats
            add('Move express formats into the peak hours',
                'Programming',
                f'{_clean(f["rpc"].idxmax())} earns the most per class at {R(f["rpc"].max())} while the shortest formats run mostly off-peak.',
                'The peak hour is the scarcest slot in the week and a short class is the cheapest way to use part of it.')
        except Exception:
            pass
        try:
            add('Match the format to the room it is given',
                'Studio Manager',
                f'Rooms fill from {M.rooms["fill"].min():.1f}% to {M.rooms["fill"].max():.1f}%, a gap driven by capacity rather than by demand.',
                'Several formats can be run in more than one room. Moving the emptier ones into the smaller room raises utilisation without new members.')
        except Exception:
            pass
        try:
            b = M.beh
            add('Sell the second format to the single-format faithful',
                'Marketing + Front Desk',
                f'{b.get("multi", 0):.0f}% of members used more than one format and {b.get("same3_members", 0)} made three or more visits in a single one.',
                'Members who hold two formats attend more often and lapse less. The list of people to approach is already in the check-in ledger.')
        except Exception:
            pass
        try:
            add('Retire or re-launch the formats under a real trial size',
                'Programming',
                f'{len(M.formats)} formats appear in the month, and the smallest ones ran only a handful of classes.',
                'A format judged on five classes tells you nothing. Commit to a twelve-class trial or take it off the timetable and stop reporting it.')
        except Exception:
            pass
        try:
            add('Watch the show rate of every format, not only the fill',
                'Studio Manager',
                f'The month closed at {F.get("fill", 0):.1f}% utilisation across {F.get("sessions", 0)} classes.',
                'Formats that fill on paper but empty at the door behave differently from formats that convert bookings into attendance.')
        except Exception:
            pass

    # ── cancels ──────────────────────────────────────────────────────────────
    if cid == 'cancels' and room() > 0:
        try:
            b = M.cancel_bands
            heavy = b[b['b'] == 'over 50%']
            never = b[b['b'] == 'never cancels']
            add('Ask the members who never cancel for something',
                'CRM + Marketing',
                f'{int(never["n"].iloc[0]):,} members cancelled nothing this year and hold {never["live"].iloc[0]:.1f} live classes each.',
                'This is the most committed list in the database and it is currently used for nothing. Reviews, referrals and price tests all start here.')
        except Exception:
            pass
        try:
            add('Handle the heaviest cancellers as a scheduling problem',
                'Studio Manager + CRM',
                f'{int(heavy["n"].iloc[0]):,} members cancelled more than half their bookings and late-cancel {heavy["late"].iloc[0]:.1f}% of the time.',
                'That pattern describes a week that no longer fits. A short conversation about times is cheaper than a discount and more likely to hold them.')
        except Exception:
            pass
        try:
            lc = M.lc_dow
            add('Check the timetable on the days that release most seats',
                'Programming',
                f'{lc.idxmax()} released {int(lc.max())} seats late, {lc.idxmin()} released {int(lc.min())}.',
                'Late releases cluster on particular days and hours. That is a timetable signal, not a member behaviour problem.')
        except Exception:
            pass
        try:
            h = M.lc_hour
            add('Send the reminder four hours out, not twenty-four',
                'CRM + Front Desk',
                f'Late releases peak at {int(h.idxmax()):02d}:00 with {int(h.max())} seats.',
                'A reminder timed before the usual cancellation hour catches the booking rather than the loss.')
        except Exception:
            pass
        try:
            c = M.lc_year[y]
            add('Re-price the seat that was released',
                'Finance',
                f'{c["lc"]:,.0f} seats were released late out of {c.get("book", 0):,.0f} booked.',
                'A seat released hours before the class is worth little to the studio and a great deal to the member on the waitlist. Automated backfill converts the loss into an attendance.')
        except Exception:
            pass
        try:
            add('Discount the quiet hour, not the product',
                'Marketing + Finance',
                f'{M.lc_year[y]["lc"]:,.0f} late releases against an average board occupancy of {M.lc_year[y].get("book", 0) / max(F.get("seats", 1), 1) * 100:.1f}%.',
                'Fill is bought with terms, not with price. An off-peak pass protects the peak price while it lifts the hours that need it.')
        except Exception:
            pass

    # ── overview ─────────────────────────────────────────────────────────────
    if cid == 'overview' and room() > 0:
        try:
            p = M.people.get(y, {}); p1 = M.people.get(y - 1, {})
            add('Report visits per member as the studio’s headline number',
                'Management',
                f'{p.get("members", 0)} members made {p.get("visits", 0):,} visits, {p.get("per", 0):.2f} each, against {p1.get("per", 0):.2f} a year earlier.',
                'It moves before revenue, before member counts and before payroll. Every other number on the page is downstream of it.')
        except Exception:
            pass
        try:
            pl = M.led
            add('Put paying members and visiting members on the same page',
                'Management + CRM',
                f'{pl["paid"]:,} paid memberships are on the ledger and {M.people.get(y, {}).get("members", 0)} members visited this month.',
                'The gap between the two is the studio’s contactable pipeline. It should be worked as a list rather than reported as a ratio.')
        except Exception:
            pass
        try:
            add('Set next month’s capacity plan from utilisation and not from last year’s revenue',
                'Studio Manager',
                f'Utilisation was {F.get("fill", 0):.1f}% on {F.get("sessions", 0)} classes and {F.get("seats", 0):,.0f} seats.',
                'Seats and hours are what the studio actually sells. Revenue follows the rooms, and the rooms are set a month ahead.')
        except Exception:
            pass
        try:
            add('Protect the hours that already work',
                'Programming',
                f'{M.days["fill"].idxmax()} fills {M.days["fill"].max():.1f}% and {M.hours["fill"].idxmax():.0f}:00 fills {M.hours["fill"].max():.1f}%.',
                'Growth decisions are easy when the strongest blocks are named. It also stops a good slot being traded away for a quiet one.')
        except Exception:
            pass
        try:
            add('Give the team one page a month and four numbers on it',
                'Management',
                'Leads, trials, bookings against capacity and visits per member all move before revenue does.',
                'Each can be read within a week of the month ending. A single page is more likely to be acted on than a full review.')
        except Exception:
            pass

    # ── leads ────────────────────────────────────────────────────────────────
    if cid == 'leads' and room() > 0:
        try:
            s = M.lead_src
            ref = s[s.index.astype(str).str.contains('Referral', case=False)]
            web = s[s.index.astype(str).str.contains('Website', case=False)]
            if len(ref) and len(web):
                add('Move a share of acquisition spend towards referrals',
                    'Marketing',
                    f'Referrals convert {ref["won"].iloc[0]:.1f}% of their leads at {R(ref["ltv"].iloc[0])} of lifetime value; the website converts {web["won"].iloc[0]:.1f}% at {R(web["ltv"].iloc[0])}.',
                    'The cheapest mix change available is asking members who already refer well to do it more often. It needs a process, not a budget.')
        except Exception:
            pass
        try:
            s = M.lead_src
            big = s['leads'].idxmax()
            add('Put a named owner on the largest source',
                'Front Desk + CRM',
                f'{str(big)[:38]} supplies {int(s["leads"].max()):,} leads and converts {s.loc[big, "won"]:.1f}%, the weakest rate of any large channel.',
                'The largest pool is not the best one. Improving the biggest channel by two points is worth more than opening a new one.')
        except Exception:
            pass
        try:
            if hasattr(M, 'lead_assoc'):
                a = M.lead_assoc
                add('Score associates on trials booked, not on leads held',
                    'Studio Manager',
                    f'Associate conversion runs from {a["won"].min():.1f}% to {a["won"].max():.1f}% on comparable lead volumes.',
                    'Trials are the step the studio controls. Leads are demand; trials are work.')
        except Exception:
            pass
        try:
            if hasattr(M, 'open_stage'):
                st = M.open_stage
                add('Work the open file from the freshest stage backwards',
                    'CRM',
                    f'{int(st.get("Shared Pricing & Schedule Details", 0)):,} leads sit at the pricing stage and {int(st.get("Sent Introductory message", 0)):,} at first contact.',
                    'Pricing-stage leads have already shown interest and need a decision, not a reminder sequence. They are the highest-yield calls on the list.')
        except Exception:
            pass
        try:
            if hasattr(M, 'lead_class'):
                c = M.lead_class
                add('Match the enquiry to the class the lead asked about',
                    'Front Desk',
                    f'{c["won"].idxmax()} converts {c["won"].max():.1f}% against {c["won"].min():.1f}% for the next best group.',
                    'Where a lead names a class, the trial booking should be that class. It is the cheapest personalisation available and it needs no system.')
        except Exception:
            pass
        try:
            if hasattr(M, 'trial_gate'):
                add('Make the trial the only acquisition target',
                    'Studio Manager + CRM',
                    f'Trial-takers convert at {M.trial_gate.loc["Trial Completed", "won_pct"]:.1f}% and the rest at {M.trial_gate.loc["Not Tried", "won_pct"]:.2f}%.',
                    'Every hour spent on a lead that has not booked a class is worth a fraction of the same hour spent getting that class booked.')
        except Exception:
            pass

    # ── behaviour ────────────────────────────────────────────────────────────
    if cid == 'behaviour' and room() > 0:
        try:
            b = M.beh
            add('Treat bursts as normal and plan for gaps instead',
                'Studio Manager + Programming',
                f'{b.get("gap_week", 0):.0f}% of the gaps between one visit and the next are a week or less and the median gap is {b.get("gap_med", 0):.0f} day.',
                'Members train in bursts rather than on a fixed rhythm. Plans and nudges should be built around the return after a gap, not around a perfect week.')
        except Exception:
            pass
        try:
            b = M.beh
            add('Recruit the top tenth as ambassadors',
                'Marketing + Studio Manager',
                f'{b.get("top_n", 0)} members produced {b.get("top_share", 0):.0f}% of this month’s attendance.',
                'The members who already behave the way the studio wants are the best source of referrals and the most credible voices in a testimonial.')
        except Exception:
            pass
        try:
            d = b['days']
            add('Ask why the weakest day is weak before adding a class to it',
                'Programming',
                f'{d.idxmin()} drew {int(d.min())} visits against {int(d.max())} on {d.idxmax()}.',
                'A quiet day is sometimes a demand fact and sometimes a timetable fact. The answer decides whether the fix is a class or a campaign.')
        except Exception:
            pass
        try:
            add('Give the once-only members a dated plan, not a reminder',
                'Front Desk + CRM',
                f'{int(b.get("once", 0))} members came exactly once this month, {b.get("once_share", 0):.0f}% of everyone who visited.',
                'The second visit is the transition that decides a membership. A booked time, a named trainer and a follow-up call is the whole intervention.')
        except Exception:
            pass
        try:
            add('Watch frequency by monthly cohort, not by average',
                'Management',
                'Averages hide a book that has split into a small frequent core and a long tail of occasional visitors.',
                'The two groups need different work: one needs more capacity, the other needs a habit. A single average number cannot tell them apart.')
        except Exception:
            pass
        try:
            add('Read the check-in ledger as the studio’s most honest dataset',
                'Management + CRM',
                f'{M.people.get(y, {}).get("visits", 0):,} visits are recorded for this month alone.',
                'Every booking, cancellation and purchase decision eventually shows up here. It is the only table that describes behaviour rather than intent.')
        except Exception:
            pass
    return R_
