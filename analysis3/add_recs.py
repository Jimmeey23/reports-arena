"""Add two more recommendations to the class and instructor reports, using round-5 findings."""
import re

CLASS_ADD = """ ('13','Report frequency per active member, not attendance alone','Studio Manager + Management',
  f'The member base is widening while volume falls: <strong>{X.s26["Member ID"].nunique()} members trained this September against {X.s25["Member ID"].nunique()} last</strong>, '
  f'but each of them came {X.s26.groupby("Member ID").size().mean():.2f} times against {X.s25.groupby("Member ID").size().mean():.2f}. Attendance is a lagging number; '
  f'visits per active member is the number that moves first.',
  'A monthly line for visits per member, sitting beside the member count, would have flagged this decline in the spring instead of at the September review. '
  'It costs the studio nothing to produce and it changes what the studio notices.'),
 ('14','Turn the free seat into a named referral','Marketing + Front Desk',
  f'September gave away <strong>{COMP26} complimentary seats &mdash; {COMP_SHARE:.0f}% of all attendance</strong>, worth {R(COMP26*(C26["rev"]/C26["att"]))} at the '
  f'studio\\u2019s own revenue per head. The film sessions and partner classes alone account for {int(CBAR.get("Studio Hosted Class", 0))}% of their own attendance in free seats.',
  f'A comp is the studio\\u2019s most expensive form of marketing and its least measured. Asking every comp guest for one thing &mdash; a named referral, or a booked second '
  f'visit &mdash; converts an unbilled seat into a lead and makes the spend accountable for the first time.'),
"""

TEACH_ADD = """ ('13','Judge trainers on the client journey, not only the session','Head of Training + CRM',
  f'One in four of September\\u2019s classes drew two people or fewer, and the trainers who hold those slots show it in their utilisation whatever they do. '
  f'The measure that separates them is what happens next: <strong>{Q_TR["r3"].max():.0f}% of one trainer\\u2019s first-time visitors reach a third visit, against '
  f'{Q_TR["r3"].min():.0f}% of another\\u2019s</strong>.',
  'Utilisation measures who walked into the room and is largely decided by the timetable. The share of a trainer\\u2019s first-timers who come back a second and third '
  'time measures what the trainer did once they were there, and it is the only trainer metric in this report that predicts the studio\\u2019s economics.'),
 ('14','Rotate one matched slot a month as a live test','Head of Training + Programming',
  f'Across the matched slots the median gap is {X.MED_SPREAD:.0f} points and {X.BIG} of {X.N_SLOT} separate by more than thirty. The rest of the spread is the slot. '
  f'Nobody currently knows which is which, because the timetable is rebuilt by programme rather than by comparison.',
  'Taking the single widest matched slot each month and deliberately swapping the two trainers settles the question in four weeks, at no cost, with the studio\\u2019s '
  'own data. Repeating it through the year turns a one-off analysis into a staffing principle.'),
"""


def add(fn, block, sub_old, sub_new):
    s = open(fn).read()
    assert block.split('(')[1][0] == "'"
    tail = '\n]\nREC_HTML = rec_html(RECS)'
    assert tail in s, fn
    s = s.replace(tail, ',\n' + block.rstrip() + tail, 1)
    assert sub_old in s, (fn, sub_old)
    s = s.replace(sub_old, sub_new, 1)
    open(fn, 'w').write(s)
    print('added to', fn)


add('/home/user/analysis3/build_class.py', CLASS_ADD, 'Fourteen actions, ordered by expected value',
    'Fourteen actions, ordered by expected value')
add('/home/user/analysis3/build_teacher.py', TEACH_ADD, 'Fourteen actions, ordered by expected value',
    'Fourteen actions, ordered by expected value')
print('done')
