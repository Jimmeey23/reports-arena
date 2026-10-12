"""Append three further recommendations to reports 4, 5 and 6."""
import re

def splice(path, anchor_block, new_block, new_recs, tail_anchor="\n]\nREC_HTML = rec_html(RECS)"):
    s = open(path).read()
    assert anchor_block in s, f'anchor missing in {path}'
    s = s.replace(anchor_block, anchor_block + new_block, 1)
    assert tail_anchor in s, f'tail missing in {path}'
    s = s.replace(tail_anchor, ',\n' + new_recs + tail_anchor, 1)
    # the previous entry already ends with a comma -> clean the double comma
    s = '\n'.join(l for l in s.split('\n') if l.strip() != ',,')
    s = s.replace(',,\n', ',\n')
    open(path, 'w').write(s)
    print('patched', path)


# ==================================================================== report 4
BLOCK4 = '''
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

'''

RECS4 = """ ('10','Sell the first month as a programme, not a class count','Sales + Front Desk',
  f'Across {int(FIRSTP["people"].sum()):,} Bandra first-timers with a recorded first purchase, the product they started on predicts almost the whole of their lifetime value. '
  f'A member whose first purchase was a 1 Month Unlimited is worth <strong>{R(FIRSTP.loc["Studio 1 Month Unlimited","ltv"])}</strong> on average; one whose first purchase was a single class is worth '
  f'{R(FIRSTP.loc["Studio Single Class","ltv"])}. Same studio, same period, same marketing \\u2014 a {FIRSTP.loc["Studio 1 Month Unlimited","ltv"]/FIRSTP.loc["Studio Single Class","ltv"]:.1f}-fold difference decided at the point of sale.',
  f'The studio\\u2019s entry offer is the cheapest thing it can say yes to, and the cheapest thing is producing the least valuable members. Selling the first month as a timed programme with a '
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
  f'The studio has one band where intervention is cheap and one where it is expensive, and the report it reads monthly is weighted towards the second. Moving the same effort one stage earlier \\u2014 '
  f'from the members who have already gone to the members whose visits have just slipped \\u2014 multiplies the yield of every retention hour the team spends.'),
"""

# ==================================================================== report 5
BLOCK5 = '''
# ---------------------------------------------------------------- depth of the format set
_FS = x26.groupby('Class').agg(sessions=('SessionID', 'size'), seats=('cap', 'sum'), att=('CheckedIn', 'sum'),
                               book=('Booked', 'sum'), rev=('Revenue', 'sum'))
_FS['fill'] = _FS['att'] / _FS['seats'] * 100
_FS['rpc'] = _FS['rev'] / _FS['sessions']
_FS['lbl'] = [str(i).replace('Studio ', '')[:22] for i in _FS.index]
_FS = _FS.sort_values('att', ascending=False)
THIN = _FS[_FS['sessions'] < 12]
FAM = _FS[_FS['lbl'].str.contains('PowerCycle', na=False)]
EXPRESS = _FS[_FS['lbl'].isin(['PowerCycle X', 'Cardio Barre X', 'Cardio Barre Express', 'Barre 57 X'])]

'''

RECS5 = """ ('10','Judge a format on twelve sessions or not at all','Programming',
  f'<strong>{len(THIN)} of the {len(_FS)} formats Bandra ran in September appeared fewer than twelve times</strong> \\u2014 between them {int(THIN["sessions"].sum())} sessions out of {int(_FS["sessions"].sum())}. '
  f'The express formats ran {int(EXPRESS["sessions"].sum())} sessions in the month between them, filling {EXPRESS["fill"].min():.0f}% to {EXPRESS["fill"].max():.0f}%.',
  f'A format that runs six times a month cannot be judged on fill rate, and it cannot be judged on revenue either. Either give a new format a real commitment \\u2014 a fixed weekly slot for '
  f'a full quarter \\u2014 or stop reporting on it. The studio is currently making programming decisions about formats it has barely tested.'),
 ('11','Let the length of a class decide, not the family it belongs to','Programming + Studio Manager',
  f'Inside the same format family the results separate sharply. PowerCycle X fills <strong>{_FS.loc["Studio PowerCycle X","fill"]:.0f}%</strong> across {int(_FS.loc["Studio PowerCycle X","sessions"])} sessions; '
  f'Cardio Barre X fills {_FS.loc["Studio Cardio Barre X","fill"]:.0f}% across {int(_FS.loc["Studio Cardio Barre X","sessions"])}. One is a premium express product, the other is an afternoon of empty seats.',
  f'The studio\\u2019s own timetable already contains the answer to its utilisation problem, in miniature: a short, specific, well-named class sells, and an unspecified short version of a long class does not. '
  f'Every express format should be rebuilt to the PowerCycle X template \\u2014 its own name, its own benefit, its own slot \\u2014 before any of them is withdrawn.'),
 ('12','Put revenue per class next to fill rate in every programming review','Studio Manager + Finance',
  f'Across September the correlation between a format\\u2019s fill rate and its revenue per class is almost total \\u2014 FIT fills {_FS.loc["Studio FIT","fill"]:.0f}% and earns '
  f'<strong>{R(_FS.loc["Studio FIT","rpc"])} a class</strong>; PowerCycle fills {_FS.loc["Studio PowerCycle","fill"]:.0f}% and earns {R(_FS.loc["Studio PowerCycle","rpc"])}. '
  f'The two columns rank the formats the same way.',
  f'Fill rate flatters formats with small rooms and penalises formats that were given the big ones, so any review that reads fill alone will keep making the same mistake. Revenue per class '
  f'is the number that survives the comparison, and pairing it with the studio\\u2019s cost per session turns a programming debate into an arithmetic one.'),
"""

# ==================================================================== report 6
BLOCK6 = '''
# ---------------------------------------------------------------- discount timing and coaching
_MB6 = D.MB.copy()
_MB6['Ltv_n'] = E.num(_MB6['Ltv'])
DT = {}
for _p in ['Studio 12 Class Package', 'Studio 1 Month Unlimited']:
    _sub = E.SB[E.SB['Cleaned Product'] == _p].copy()
    _f = _sub.groupby('Member ID').agg(fd=('dt', 'min'), dsc=('Discount Value In Currency',
                                  lambda x: (E.num(x).fillna(0) > 0).any()), v=('val', 'sum'), n=('Sale ID', 'nunique'))
    _f['obs'] = (TODAY - _f['fd']).dt.days
    _f = _f[_f['obs'] >= 180]
    DT[_p] = _f.groupby('dsc').agg(n=('n', 'size'), rpt=('n', lambda x: (x > 1).mean() * 100), ltv=('v', 'mean'))
TRAIN_LC = x26.groupby('Trainer').agg(book=('Booked', 'sum'), lc=('LateCancelled', 'sum'))
TRAIN_LC['rate'] = TRAIN_LC['lc'] / TRAIN_LC['book'].replace(0, np.nan) * 100
TRAIN_LC = TRAIN_LC[TRAIN_LC['book'] >= 100].sort_values('rate', ascending=False)
GDEEP = float(E.SB[E.SB['dt'].dt.year == 2026]['Discount Value In Currency'].apply(E.num).fillna(0).sum())
GN = E.SB[E.SB['dt'].dt.year == 2026]
GDEEP = float((GDEEP / (GN['val'].sum() + GDEEP)) * 100)
GTOT = float(LP['Amount Paid'].sum()) if 'Amount Paid' in LP else 0.0

'''

RECS6 = """ ('10','Never discount the first month \\u2014 discount the second','Marketing + Finance',
  f'On the 12 Class Package, first-buyers who paid full price repeat at {DT["Studio 12 Class Package"].loc[False,"rpt"]:.1f}% and are worth '
  f'{R(DT["Studio 12 Class Package"].loc[False,"ltv"])}. First-buyers who were discounted repeat at {DT["Studio 12 Class Package"].loc[True,"rpt"]:.1f}% and are worth '
  f'{R(DT["Studio 12 Class Package"].loc[True,"ltv"])}. The same pattern holds on the 1 Month Unlimited \\u2014 {DT["Studio 1 Month Unlimited"].loc[False,"rpt"]:.1f}% against '
  f'{DT["Studio 1 Month Unlimited"].loc[True,"rpt"]:.1f}% repeat, at {R(DT["Studio 1 Month Unlimited"].loc[False,"ltv"])} against {R(DT["Studio 1 Month Unlimited"].loc[True,"ltv"])}.',
  f'The offer is not the problem; its timing is. A discount on the first purchase lowers the value of the members the studio attracts at the exact moment it is trying to establish a habit at full '
  f'commitment. Moving the same money to the first renewal \\u2014 a retention offer rather than an acquisition offer \\u2014 rewards the behaviour the studio actually wants and stops setting the '
  f'price expectation at the beginning of the relationship.'),
 ('11','Publish late-cancellation rate by trainer as a coaching number','Studio Manager',
  f'Across trainers with a hundred or more September bookings the late-cancellation rate runs from <strong>{TRAIN_LC["rate"].min():.1f}% to {TRAIN_LC["rate"].max():.1f}%</strong> \\u2014 a four-fold spread on the same booking policy. '
  f'{TRAIN_LC.index[0]} runs {TRAIN_LC["rate"].iloc[0]:.1f}% and {TRAIN_LC.index[-1]} {TRAIN_LC["rate"].iloc[-1]:.1f}%.',
  f'A released seat is a member deciding, at short notice, that the hour no longer fits. When the rate is high for one trainer and low for another teaching the same policy, the difference is usually the '
  f'slot rather than the person. Read as a coaching number rather than a compliance one, it is the earliest signal the studio has that a slot is drifting out of its members\\u2019 lives.'),
 ('12','Show the member what the discount was worth','Marketing + Front Desk',
  f'The studio gave away <strong>{R(GN["Discount Value In Currency"].apply(E.num).fillna(0).sum())} in 2026 alone</strong>, at an average depth of {GDEEP:.1f}% of gross. Across the years on file the figure is '
  f'{R(E.SB["Discount Value In Currency"].apply(E.num).fillna(0).sum())}.',
  f'A discount that arrives silently as a lower price is read as the price. A discount that arrives as a line on the receipt, with a value against it, is read as a favour \\u2014 and favours are repaid. '
  f'Showing the saving costs nothing, changes no policy, and is the only part of the discount programme the member ever sees.'),
"""

splice('/home/user/analysis3/build_lapse.py', 'import e1_data as E\n', 'import d1_data as D\n' + BLOCK4, RECS4)
splice('/home/user/analysis3/build_format.py', "x26 = X[(X['dt'] >= '2026-09-01') & (X['dt'] < '2026-10-01')].copy()\n",
       BLOCK5, RECS5)
splice('/home/user/analysis3/build_cancel.py', "x24 = X[(X['dt'] >= '2024-09-01') & (X['dt'] < '2024-10-01')].copy()\n",
       BLOCK6, RECS6)
