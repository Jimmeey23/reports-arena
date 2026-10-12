"""Metric reconciliation for the report engine, pinned to the atlas metric
dictionary (Jimmeey23/atlas, METRICS.md) and its September 2026 control
totals (docs/metric-reconciliation.md).

Run from the studio-app directory:

    python tests/metrics_reconciliation_test.py

The checks reproduce the atlas formulas on the engine's normalised frames:
  * sessions, attendance, seats and weighted fill
  * successful non-voided cash collection, payment VAT, collected net and
    item-level discounts with the discount/(revenue+discount) rate
  * the explicit newcomer population and its trial conversion
  * the per-studio Metrics object and the atlas rate definitions it carries
"""
from __future__ import annotations
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np
import pandas as pd

from engine.data import Dataset, discover
from engine.metrics import Metrics

UPLOADS = os.path.join(os.path.dirname(HERE), 'data', 'uploaded')

SEP_A, SEP_B = pd.Timestamp('2026-09-01'), pd.Timestamp('2026-10-01')

# Atlas September 2026 control totals, all studios.
CONTROL = dict(
    sessions=860,
    attendance=4653,
    seats=10925,
    fill=42.6,
    cash=5954184.9,
    vat=284261.0,
    net=5669924.0,
    item_discount=520468.8,
    discount_rate=8.0,
    newcomers=387,
)

FAILS = []


def check(name, got, want, tol=None):
    if tol is None:
        ok = got == want
    else:
        ok = abs(float(got) - float(want)) <= tol
    line = f'{"ok  " if ok else "FAIL"} {name}: got {got}, want {want}' + (f' (+/- {tol})' if tol else '')
    print(line)
    if not ok:
        FAILS.append(name)


def main():
    paths = discover(UPLOADS)
    D = Dataset(paths, log=lambda *a: None)

    # ------------------------------------------------------------ sessions
    X = D.sessions
    sep = X[(X['_dt'] >= SEP_A) & (X['_dt'] < SEP_B)]
    att = float(sep['CheckedIn'].sum()); seats = float(sep['Capacity'].sum())
    check('september sessions', len(sep), CONTROL['sessions'])
    check('september attendance', int(att), CONTROL['attendance'])
    check('september seats offered', int(seats), CONTROL['seats'])
    check('september weighted fill %', round(att / seats * 100, 1), CONTROL['fill'])
    # atlas no-show definition on the month
    noshow = float((sep['Booked'] - sep['CheckedIn'] - sep['LateCancelled']).sum())
    book = float(sep['Booked'].sum())
    assert noshow >= 0 and noshow <= book, 'no-shows must sit between zero and the booked book'

    # --------------------------------------------------------------- sales
    S = D.sales
    ok = S[(S['_dt'] >= SEP_A) & (S['_dt'] < SEP_B) & (S['ok'])]
    cash = float(ok['val'].sum()); vat = float(ok['vat'].sum())
    disc = float(ok['disc'].sum())
    check('september cash collected', round(cash, 1), CONTROL['cash'], tol=0.5)
    check('september payment VAT', round(vat, 1), CONTROL['vat'], tol=0.5)
    check('september collected net of VAT', round(cash - vat, 1), CONTROL['net'], tol=0.5)
    check('net column matches cash minus VAT', round(float(ok['net'].sum()), 1), round(cash - vat, 1), tol=0.5)
    check('september item-level discount', round(disc, 1), CONTROL['item_discount'], tol=0.5)
    check('september discount rate %', round(disc / (cash + disc) * 100, 1), CONTROL['discount_rate'], tol=0.05)
    check('transactions are distinct sales', int(ok['Sale ID'].nunique()) < len(ok), True)

    # ------------------------------------------------------------- newcomers
    N = D.new
    nn = N[(N['_dt'] >= SEP_A) & (N['_dt'] < SEP_B) & (N['is_new'] == True)]
    check('september newcomers', len(nn), CONTROL['newcomers'])
    conv = int(nn['Conversion Status'].astype(str).str.strip().eq('Converted').sum())
    check('converted newcomers within range (moves as statuses update)', 38 <= conv <= 60, True)

    # ----------------------------------------- per-studio Metrics object
    M = Metrics(D, 'Supreme HQ, Bandra', 2026, 9)
    F = M.sales[2026]
    check('bandra transactions are distinct sales', F['txn'] <= F['lines'], True)
    check('bandra discount rate sane (was ~28% with sale-level discounts)',
          F['depth'] < 15.0, True)
    check('bandra aov * txn ~= cash', round(F['aov'] * F['txn'] / F['cash'], 3), 1.0, tol=0.02)
    room = M.room[2026]
    check('bandra show-up rate = attended/booked', round(room['conv'], 3),
          round(room['att'] / room['book'] * 100, 3), tol=0.001)
    check('bandra late-cancel rate = late/booked', round(room['lc_rate'], 3),
          round(room['lc'] / room['book'] * 100, 3), tol=0.001)
    check('bandra no-show rate = (booked-att-late)/booked', round(room['noshow_rate'], 3),
          round((room['book'] - room['att'] - room['lc']) / room['book'] * 100, 3), tol=0.001)

    # lapsed ledger: serial-encoded Amount Paid must recover as money
    L = D.lapsed
    serial = L['Amount Paid'].dropna()
    check('lapsed amounts recovered (no absurd serial values left)',
          bool(((serial >= 0) & (serial < 5_000_000)).all()), True)
    check('lapsed amounts include the serial-recovered range (thousands of rupees)',
          bool((serial > 100000).any()), True)
    check('churn rate is churned over the whole ledger',
          round(M.led['churn_rate'], 1),
          round(L[L['_loc'] == 'Supreme HQ, Bandra']['Churned Date_d'].notna().mean() * 100, 1), tol=0.1)

    # newcomer cohort measures exist and are proportions
    nc = M.newcohort()
    if nc:
        check('cohort conversion rate is a percentage', 0 <= nc['conversion_rate'] <= 100, True)

    print()
    if FAILS:
        print(f'{len(FAILS)} reconciliation checks failed: {", ".join(FAILS)}')
        return 1
    print('all reconciliation checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
