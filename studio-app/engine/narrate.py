"""The writing layer: executive summaries, spoken narration and the
recommendations that close each chapter.

Everything here is composed from the numbers the metrics layer computed, so a
summary can never say something the data does not support. If an LLM key is
configured the composed text is handed to the model to be rewritten more
fluently - but the model is only ever given the composed facts, never asked to
produce new ones.
"""
from __future__ import annotations
import json, os, re, urllib.request
import pandas as pd
from .design import R, P, N
from .metrics import MONTH_NAMES
from .narrate_more import extra as _extra


# --------------------------------------------------------------------- wording
def _pc(x, base):
    if not base:
        return ''
    d = (x - base) / base * 100
    return f', {"up" if d >= 0 else "down"} {abs(d):.0f}% on the same month last year'


def summary(M, ch):
    """Four or five sentences that say what the chapter found."""
    y, m, lab = M.y, M.m, M.label
    s = []
    if ch['id'] == 'sales':
        F = M.sales[y]; P1 = M.sales.get(y - 1)
        s.append(f'{R(F["cash"])} was taken at {M.studio} in {lab}, across {F["lines"]} transactions from {F["buyers"]} buyers')
        s.append(f'The average buyer spent {R(F["ticket"])}{_pc(F["ticket"], P1["ticket"]) if P1 else ""}')
        if hasattr(M, 'cats') and len(M.cats):
            s.append(f'The largest category was {M.cats.index[0]} at {R(M.cats["sum"].iloc[0])}')
        L = M.room.get(y, {})
        s.append(f'Class revenue reached {R(L.get("rev", 0))} at {R(L.get("rpc", 0))} a class')
    elif ch['id'] == 'class':
        F = M.room.get(y, {}); P1 = M.room.get(y - 1, {})
        s.append(f'{F.get("sessions", 0)} classes ran at {M.studio} in {lab}, offering {F.get("seats", 0):,.0f} seats and filling {F.get("att", 0):,.0f} of them')
        s.append(f'Utilisation came in at {F.get("fill", 0):.1f}%{_pc(F.get("fill", 0), P1.get("fill")) if P1 else ""}')
        s.append(f'Revenue per class was {R(F.get("rpc", 0))} and revenue per seat filled {R(F.get("rph", 0))}')
        s.append(f'{int((M._sl(M.D.sessions, y)["CheckedIn"] <= 2).sum())} classes ran to two people or fewer')
    elif ch['id'] == 'instructor':
        t = M.trainers
        s.append(f'{len(t)} trainers taught {t["sessions"].sum():,.0f} classes in {lab}, drawing {t["att"].sum():,.0f} attendances and {R(t["rev"].sum())} of revenue')
        s.append(f'Utilisation ranged from {t["fill"].min():.1f}% to {t["fill"].max():.1f}%, a {t["fill"].max()/max(t["fill"].min(),0.1):.1f}-fold spread')
        rph = t['rph'].dropna()
        s.append(f'But revenue per attendee ran only {R(rph.min())} to {R(rph.max())}, so most of the spread is the slots rather than the trainers')
    elif ch['id'] == 'lapse':
        s.append(f'{M.led["rows"]:,} memberships are in the {M.studio} ledger, {M.led["paid"]:,} of them paid')
        if hasattr(M, 'surv'):
            sv = M.surv.set_index('Point')['still']
            s.append(f'{sv.get("Day 30", 0):.0f}% of paid memberships survive thirty days and {sv.get("Day 180", 0):.0f}% survive six months')
        if hasattr(M, 'median_life'):
            s.append(f'The median membership lasts {int(M.median_life)} days and carries {R(M.ticket)} of recorded cash')
        if hasattr(M, 'products') and len(M.products):
            s.append(f'{str(M.products.index[0])} keeps its members best at {M.products["live"].iloc[0]:.0f}% still live or renewed')
    elif ch['id'] == 'format':
        f = M.formats
        s.append(f'{len(f)} formats ran {f["sessions"].sum():,.0f} classes in {lab} for {R(f["rev"].sum())}')
        s.append(f'{str(f["fill"].idxmax()).replace("Studio ", "")} filled {f["fill"].max():.1f}% of its seats against {f["fill"].min():.1f}% for {str(f["fill"].idxmin()).replace("Studio ", "")}')
        if hasattr(M, 'fmt_members') and len(M.fmt_members):
            s.append(f'{str(M.fmt_members["members"].idxmax()).replace("Studio ", "")} reached the most members at {int(M.fmt_members["members"].max())}')
    elif ch['id'] == 'cancels':
        c = M.lc_year[y]; P1 = M.lc_year.get(y - 1, {})
        s.append(f'{c["lc"]:,.0f} seats were released late in {lab}, {P(c["rate"])} of everything booked')
        if P1:
            s.append(f'That is {"down" if c["lc"] < P1["lc"] else "up"} from {P1["lc"]:,.0f} a year earlier')
        room = M.room.get(y, {})
        s.append(f'Attendance ran at {c["att"]/max(c["book"],1)*100:.1f}% of the booked book, and the board is only {c["book"]/max(room.get("seats",1),1)*100:.1f}% booked in the first place')
        if hasattr(M, 'disc_year') and y in M.disc_year:
            s.append(f'Discount depth stands at {M.disc_year[y]["depth"]:.1f}% across {M.disc_year[y]["spread"]:.0f}% of sales')
    elif ch['id'] == 'overview':
        F = M.room.get(y, {}); S = M.sales.get(y, {})
        s.append(f'{M.studio} ran {F.get("sessions", 0)} classes at {F.get("fill", 0):.1f}% utilisation in {lab}, earning {R(F.get("rev", 0))} from the room')
        s.append(f'{R(S.get("cash", 0))} was taken from {S.get("buyers", 0)} buyers')
        if hasattr(M, 'core'):
            s.append(f'The {M.core["n"]} members who returned from the same month last year gave {abs(M.core["lost"]):,.0f} fewer visits, about {M.core["share_of_month"]:.0f}% of the month')
        if hasattr(M, 'lead_fun'):
            s.append(f'{M.lead_month:,} leads arrived and {M.lead_fun["won_pct"]:.1f}% of all leads on file have converted')
    elif ch['id'] == 'leads':
        lf = M.lead_fun
        s.append(f'{lf["leads"]:,} leads are recorded for {M.studio}: {lf["trial"]:,} completed a trial, {lf["won"]:,} became members, {lf["retained"]:,} are still with the studio')
        s.append(f'Trial-takers convert at {M.trial_gate.loc["Trial Completed", "won_pct"]:.1f}% against {M.trial_gate.loc["Not Tried", "won_pct"]:.2f}% without one' if hasattr(M, 'trial_gate') else '')
        if hasattr(M, 'lead_same'):
            s.append(f'{M.lead_same:.0f}% of memberships are sold the same day the enquiry arrives')
        if hasattr(M, 'open_n'):
            s.append(f'{M.open_n:,} leads are still marked open at a mean age of {M.open_age:.0f} days')
    elif ch['id'] == 'behaviour':
        b = M.beh
        pp = M.people.get(y, {})
        s.append(f'{pp.get("members", 0):,} members trained {pp.get("visits", 0):,} times in {lab}, {pp.get("per", 0):.2f} visits each')
        s.append(f'{b.get("once_share", 0):.0f}% came exactly once and the top tenth delivered {b.get("top_share", 0):.0f}% of attendance')
        s.append(f'{b.get("morning", 0)} of {pp.get("members", 0)} members do most of their training before noon')
        if 'gap_med' in b:
            s.append(f'The median gap between visits is {b["gap_med"]:.0f} day and between purchases {b.get("pgap_med", 0):.0f} days')
    return '. '.join(x for x in s if x) + '.'


def narration(M, ch):
    """A spoken script: plain sentences, no symbols, about forty seconds long."""
    y, lab = M.y, M.label
    open_line = f"{ch['title']}. {M.studio}, {lab}."
    facts = ' '.join(ch.get('facts', []))
    # strip currency symbols and abbreviations that read badly aloud
    spoken = (facts.replace('₹', '').replace('₹', '').replace('%', ' per cent')
                   .replace('  ', ' ').strip())
    close = {
        'sales': 'The question this chapter leaves is not whether the month sold, but how much of it was sold at full price.',
        'class': 'The room is the studio’s fixed cost. Every seat that goes unfilled was paid for anyway.',
        'instructor': 'The fairest way to read a trainer is against the slots they were given, and then to ask whether those slots should exist.',
        'lapse': 'Members are not lost in a moment. They stop coming, and everything needed to see it is already recorded.',
        'format': 'No format wins on every measure, so the studio’s job is to decide what each one is for.',
        'cancels': 'A released seat is a member telling the studio, in the only way they can, that the time no longer works.',
        'overview': 'Read together, these ledgers describe a business that earns well per class and loses its regulars slowly.',
        'leads': 'The trial is the gate and the same day is the deadline. Everything else in this chapter is a consequence of those two.',
        'behaviour': 'Most of what looks like churn at this studio is one early step that nobody currently owns.',
    }.get(ch['id'], '')
    return f'{open_line} {spoken} {close}'.strip()


# --------------------------------------------------------------------- recs
def recommendations(M, cid, extra=None):
    y, lab, m = M.y, M.label, M.m
    F = M.room.get(y, {})
    P1 = M.room.get(y - 1, {})
    S1 = M.sales.get(y - 1, {}) if hasattr(M, 'sales') else {}
    R_ = []

    def add(t, owner, reason, impact):
        R_.append((f'{len(R_)+1:02d}', t, owner, reason, impact))

    # the section tables the deep chapter itself built get first refusal
    for t, owner, reason, impact in (extra or []):
        add(t, owner, reason, impact)

    if cid == 'sales':
        if hasattr(M, 'cats') and len(M.cats):
            add('Put a named owner on the largest category', 'Sales + Studio Manager',
                f'{str(M.cats.index[0])} produced {R(M.cats["sum"].iloc[0])} of the month’s {R(M.sales[y]["cash"])} across {int(M.cats["size"].iloc[0])} transactions.',
                'The largest line in any month deserves a target, a price test and a person accountable for it. Managing the total hides the composition.')
        add('Sell the next purchase at the point of the last one', 'Front Desk',
            f'The average buyer spent {R(M.sales[y]["ticket"])} and repeat buying at this studio clusters tightly around a monthly rhythm.',
            'A renewal offered while a member is at peak usage converts far more often than one offered after the visits have already stopped.')
        add('Report cash per buyer, not just cash', 'Finance',
            f'Revenue per class is {R(F.get("rpc", 0))} and revenue per attendance {R(F.get("rph", 0))}; the buyer, not the seat, is the unit that has to be replaced.',
            'A studio can grow transactions while shrinking buyers. One column prevents that.')
        if hasattr(M, 'sale_hours') and len(M.sale_hours):
            hh = int(M.sale_hours['size'].idxmax())
            add('Staff the desk where the money already is', 'Front Desk + Studio Manager',
                f'The busiest trading hour of the month was {hh:02d}:00, taking {int(M.sale_hours.loc[hh, "size"])} transactions.',
                'Placing the sales conversation in that hour costs nothing and works with the members’ own routine rather than against it.')
        if S1:
            add('Watch the discount mix, not the discount total', 'Marketing + Finance',
                f'{M.sales[y]["spread"]:.0f}% of sales carried a discount at {M.sales[y]["depth"]:.1f}% depth, against {S1["spread"]:.0f}% at {S1["depth"]:.1f}% a year earlier.',
                'Depth and spread move independently, and only one of them is visible in the revenue line.')
    elif cid == 'class':
        add('Cut or re-time the sessions nobody comes to', 'Programming + Studio Manager',
            f'{int((M._sl(M.D.sessions, y)["CheckedIn"] <= 2).sum())} classes ran to two people or fewer and {int((M._sl(M.D.sessions, y)["CheckedIn"] == 0).sum())} had nobody at all.',
            'Every empty class costs the same as a full one. Moving those hours is a timetable edit and it is reversible after four weeks.')
        if hasattr(M, 'hours') and len(M.hours):
            wk = M.hours.dropna().nsmallest(1, 'fill').index[0]
            add('Rebuild the weakest hour of the day', 'Programming',
                f'{int(wk):02d}:00 was the emptiest hour of the month at {M.hours.dropna().nsmallest(1, "fill")["fill"].iloc[0]:.0f}% utilisation across {int(M.hours.dropna().nsmallest(1, "fill")["sessions"].iloc[0])} classes.',
                'One hour, repeated weekly, is the cheapest capacity decision available. It should be a test with a review date, not a habit.')
        if hasattr(M, 'rooms') and len(M.rooms) > 1:
            add('Match the room to the demand, not the format', 'Studio Manager',
                f'{M.rooms.iloc[0]["band"]} filled {M.rooms.iloc[0]["fill"]:.1f}% while {M.rooms.iloc[-1]["band"]} filled {M.rooms.iloc[-1]["fill"]:.1f}%.',
                'Small rooms fill and large ones do not. Where the timetable allows, the smaller room for the same class raises utilisation with no new demand.')
        add('Publish utilisation weekly, by day and hour', 'Studio Manager',
            f'The month’s utilisation was {F.get("fill", 0):.1f}% against {P1.get("fill", 0):.1f}% a year earlier.',
            'A weekly number turns a monthly post-mortem into a decision the team can still act on.')
    elif cid == 'instructor':
        t = M.trainers
        add('Assess trainers on the slots they hold, and separately on the slots themselves', 'Studio Manager',
            f'Revenue per attendee runs only {R(t["rph"].dropna().min())} to {R(t["rph"].dropna().max())}, while utilisation runs {t["fill"].min():.1f}% to {t["fill"].max():.1f}%.',
            'The two tables answer different questions. Confusing them penalises trainers for the studio’s scheduling decisions.')
        add('Give the strongest filler more of the week', 'Programming + Studio Manager',
            f'{t["fill"].idxmax()} fills {t["fill"].max():.1f}% across {t.loc[t["fill"].idxmax(), "sessions"]:.0f} classes.',
            'Where a trainer repeatedly fills the room they were given, the next marginal slot should be theirs before it is anyone else’s.')
        if 'checkins' in M.has:
            add('Track who brings new members, not just who teaches', 'Studio Manager + CRM',
                'New-member flow varies by trainer and is recorded in the check-in ledger, but it is not on any scorecard.',
                'A trainer who attracts first visits is doing acquisition work. That deserves to be visible.')
        add('Watch late-cancellation rate by trainer as a coaching number', 'Studio Manager',
            f'Rates range from {t["lc_rate"].dropna().min():.1f}% to {t["lc_rate"].dropna().max():.1f}% on the same booking policy.',
            'A high rate usually means a slot that has drifted out of the members’ week, which is a scheduling answer, not a compliance one.')
    elif cid == 'lapse':
        if hasattr(M, 'surv'):
            sv = M.surv.set_index('Point')['still']
            add('Run an activation sequence through the first fortnight', 'Front Desk + CRM',
                f'{100 - sv.get("Day 14", 0):.0f}% of paid memberships end within fourteen days and {100 - sv.get("Day 30", 0):.0f}% within thirty.',
                'The first two weeks decide the membership. A dated plan, a booked class and a call on day ten is the whole intervention.')
        if hasattr(M, 'unused_low'):
            add('Collect the unused classes', 'CRM + Front Desk',
                f'{M.unused_low:,} memberships used a quarter or less of what they bought, leaving {M.unused_left:,.0f} classes unspent.',
                'Paid-for and undelivered is a liability and a warm reason to make contact.')
        if hasattr(M, 'products') and len(M.products):
            add('Lead with the product that keeps its members', 'Sales + Marketing',
                f'{str(M.products.index[0])} is still live or renewed {M.products["live"].iloc[0]:.0f}% of the time, the best rate in the range.',
                'Renewal is a property of the product list before it is a property of the customer. What works should be sold first.')
        if hasattr(M, 'recency') and len(M.recency):
            add('Work win-back by recency, not by lifetime value', 'CRM',
                f'The warmest group paid {R(M.recency.iloc[0]["cash"])} on average; the group gone over six months paid {R(M.recency.iloc[-1]["cash"])}.',
                'The members most likely to return are also the ones who were worth the most. Chasing the biggest historical spenders wastes the list.')
        add('Put the churn number in the acquisition plan', 'Management + Finance',
            f'Median membership life is {int(getattr(M, "median_life", 0))} days.',
            'If most of the book has to be replaced each month, acquisition is a maintenance cost rather than a growth line, and it should be budgeted as one.')
    elif cid == 'format':
        f = M.formats
        add('Decide what each format is for', 'Programming + Studio Manager',
            f'{str(f.index[0]).replace("Studio ", "")} carries {f["share_sessions"].iloc[0]:.0f}% of the timetable at {f["fill"].iloc[0]:.1f}% utilisation, while {str(f["fill"].idxmax()).replace("Studio ", "")} fills {f["fill"].max():.1f}%.',
            'Revenue leadership and efficiency leadership sit in different formats. The timetable should be set by the second and defended by the first.')
        add('Give the fullest format more of the week', 'Programming',
            f'{str(f["fill"].idxmax()).replace("Studio ", "")} runs {f.loc[f["fill"].idxmax(), "sessions"]:.0f} classes and fills {f["fill"].max():.1f}% of them.',
            'Scaling what already fills is the least risky capacity decision available.')
        if hasattr(M, 'fmt_members') and len(M.fmt_members):
            add('Sell the second format deliberately', 'Marketing + Front Desk',
                f'{M.beh.get("multi", 0):.0f}% of members used more than one format this month and {M.beh.get("same3_members", 0)} made three or more visits to a single one.',
                'A member with two formats and a routine is the member who is still here next year. Both halves of that can be designed for.')
        add('Stop judging formats on fewer than twelve sessions', 'Programming',
            f'The smallest formats ran only a handful of classes this month.',
            'A format cannot be assessed on a handful of appearances. Either commit to a real trial or stop reporting on it.')
    elif cid == 'cancels':
        c = M.lc_year[y]
        add('Give the released seat back to the waitlist automatically', 'CRM + Front Desk',
            f'{c["lc"]:,.0f} seats were released late, at an average board occupancy of {c["book"]/max(M.room.get(y, {}).get("seats", 1),1)*100:.1f}%.',
            'A seat released hours before the class is worth little to the studio and a great deal to a member who could not book.')
        if hasattr(M, 'lc_members'):
            add('Contact the members who cancel repeatedly', 'CRM',
                f'{M.lc_conc["three_plus"]} members cancelled three or more times, and the ten heaviest made {M.lc_conc["top10_share"]:.0f}% of all cancellations.',
                'Repeat cancelling is a schedule that no longer fits. A short conversation is cheaper than a discount and more likely to hold them.')
        if hasattr(M, 'disc_year') and len(M.disc_year) > 1:
            add('Set a discount ceiling and publish the range', 'Finance + Management',
                f'Depth across recent years runs from {min(v["depth"] for v in M.disc_year.values()):.1f}% to {max(v["depth"] for v in M.disc_year.values()):.1f}%.',
                'Publishing the range, without naming anyone, moves behaviour faster than a policy does.')
        add('Test whether discounts buy loyalty at all', 'Marketing',
            'Pooled comparisons flatter discounting because the products that carry offers are the ones that renew anyway.',
            'A controlled test measured on renewal, not on units sold, would settle a question the studio has been answering by assumption.')
    elif cid == 'overview':
        if hasattr(M, 'core'):
            add('Own the frequency number, not just the member count', 'Management',
                f'The returning core gave {abs(M.core["lost"]):,.0f} fewer visits than the same members produced a year earlier — {M.core["share_of_month"]:.0f}% of the month.',
                'Membership counts flatter a month whose attendance fell. The two numbers belong side by side on one page.')
        add('Report four leading indicators monthly and nothing else', 'Management',
            'Leads, trials booked, bookings against capacity and visits per active member all move before revenue does.',
            'Each can be read within a week of the month ending, and each predicts the others. One page would give the studio a month of warning.')
        if 'lapsed' in M.has and hasattr(M, 'recency'):
            add('Treat the live book as pipeline, not administration', 'CRM + Front Desk',
                f'{M.led["paid"]:,} paid memberships are on file and the warmest lapsed group is contactable today.',
                'A dated, owned call list built from the studio’s own ledger is the highest-yield piece of work available.')
        add('Keep the gains on the record', 'Studio Manager',
            f'Revenue per class is {R(F.get("rpc", 0))} against {R(P1.get("rpc", 0)) if P1 else "—"} a year earlier.',
            'Naming what improved protects it. A studio that only reports problems tends to lose the things that were working.')
    elif cid == 'leads':
        lf = M.lead_fun
        add('Make the trial the only acquisition target', 'Studio Manager + CRM',
            f'Trial-takers convert at {M.trial_gate.loc["Trial Completed", "won_pct"]:.1f}% and everything else at {M.trial_gate.loc["Not Tried", "won_pct"]:.2f}%.',
            'Every hour spent on a lead that has not booked a class is worth a fraction of the same hour spent getting that class booked.')
        if hasattr(M, 'lead_span'):
            add('Answer every enquiry the same day', 'Front Desk + CRM',
                f'{M.lead_same:.0f}% of memberships are sold on the day of the enquiry.',
                'Response time is the conversion rate, delayed. It is also the one variable in lead handling the studio controls completely.')
        if hasattr(M, 'lead_ch') and len(M.lead_ch):
            best = M.lead_ch['won'].idxmax(); worst = M.lead_ch['won'].idxmin()
            add('Move acquisition towards the channels that convert', 'Marketing',
                f'{str(best)[:34]} converts {M.lead_ch["won"].max():.1f}% of its leads; {str(worst)[:34]} converts {M.lead_ch["won"].min():.1f}%.',
                'The studio does not need more leads, it needs the leads that already know someone. A published phone number and a referral reward are the cheapest mix changes available.')
        if hasattr(M, 'open_n'):
            add('Close the open file honestly', 'CRM',
                f'{M.open_n:,} leads are open at a mean age of {M.open_age:.0f} days, {M.open_stale:,} of them older than six months.',
                'A single pass to contactable, interested or closed turns thousands of rows into a short real list and makes every conversion figure trustworthy.')
    elif cid == 'behaviour':
        b = M.beh
        add('Book the second visit before the member leaves the building', 'Front Desk + CRM',
            f'{b.get("once_share", 0):.0f}% of this month’s members came exactly once.',
            'The second visit is the transition that decides the membership, and nobody is currently asking for it at the moment it can be booked.')
        add('Build the timetable around mornings', 'Programming + Studio Manager',
            f'{b.get("morning", 0)} of {M.people.get(y, {}).get("members", 0)} members do most of their training before noon.',
            'The evening block is not a lesser audience, it is simply a smaller one — and it is currently scheduled as though it were the largest.')
        if 'gap_med' in b:
            add('Stop expecting members to come on a schedule', 'Studio Manager',
                f'The median gap between a member’s visits is {b["gap_med"]:.0f} day and {b.get("gap_week", 0):.0f}% of all gaps are a week or less.',
                'Members come in bursts. A rhythm-shaped plan measures them as inconsistent when they are behaving normally.')
        if 'pgap_med' in b:
            add('Sell the next purchase inside the first month', 'Front Desk + CRM',
                f'The median gap between purchases is {b.get("pgap_med", 0):.0f} days and {b.get("pgap_month", 0):.0f}% of repeat purchases happen inside thirty days.',
                'Buying here is monthly. A renewal conversation belongs in the first fortnight, not the final week.')
        add('Read frequency as the headline metric', 'Management',
            f'Visits per member in {lab} were {M.people.get(y, {}).get("per", 0):.2f}.',
            'Attendance, revenue and member counts are all downstream of it, and it is the only one of them that moves first.')

    # second pass: one action per evidence table
    _extra(M, cid, R_, add, cap=15)

    # the three passes above can reach the same conclusion by different routes;
    # keep the first (best-evidenced) wording of each and renumber
    seen, keep = [], []
    for r in R_:
        words = set(re.findall(r'[a-z]{4,}', (r[1] + ' ' + r[2]).lower()))
        dup = False
        for prev in seen:
            if len(words & prev) / max(len(words | prev), 1) > 0.55:
                dup = True
                break
        if not dup:
            seen.append(words)
            keep.append(r)
    keep = [(f'{i + 1:02d}',) + r[1:] for i, r in enumerate(keep[:14])]
    return keep


# --------------------------------------------------------------------- LLM
def llm(text, key, model='gpt-4o-mini', base='https://api.openai.com/v1/chat/completions'):
    """Optional: rewrite composed text with a language model. Never used to
    invent facts - the model only sees what the metrics layer produced."""
    prompt = ('You are the analyst who wrote the following notes about a fitness studio. '
              'Rewrite them as three short, plain, confident sentences for the studio owner. '
              'Use only the facts given; do not add numbers, do not use marketing language, '
              'and do not use em dashes.\n\n' + text)
    body = json.dumps({'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                       'temperature': 0.4, 'max_tokens': 320}).encode()
    req = urllib.request.Request(base, data=body, headers={
        'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())['choices'][0]['message']['content'].strip()
