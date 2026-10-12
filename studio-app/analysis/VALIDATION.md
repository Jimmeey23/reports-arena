# September 2026 report review

Both Bandra and Kemps Corner reports were refined in place, including older saved copies. Original source snapshots, section links and private user edits were preserved. Each report includes its validation receipt and data limitations.

| Control | Bandra | Kemps Corner |
|---|---:|---:|
| Sales revenue | ₹15,29,410.18 | ₹32,06,430.87 |
| Distinct sales | 196 | 233 |
| Buyers | 139 | 179 |
| Attended visits | 1,404 | 2,090 |
| Offered seats | 3,293 | 4,606 |
| Weighted utilisation | 42.64% | 45.38% |
| Delivered session revenue | ₹13,06,451.49 | ₹19,01,972.95 |
| Explicit newcomers | 143 | 118 |
| Newcomer conversions | 12 | 14 |

Independent controls read original CSV values using Decimal and datetime, outside the engine's formula helpers. Session and check-in attendance counts and monetary amounts reconcile exactly. Duplicate identity and missing required numeric-field checks pass. The rebuilt reports pass 34 metric checks each, plus source-integrity controls.

Corrections include monetary Paid values previously coerced to booleans, distinct-sale transaction bands, total purchased credits for per-credit prices, ten buyer deciles, September-inclusive year-to-date totals, month-specific newcomer cohorts and eligibility-aware retention checkpoints. Percent charts retain percentage units even below 1%.

September purchase cohorts cannot support 30-day or longer retention checkpoints. Lead arithmetic was checked against complete saved September populations; the original lead CSV and historical month-end lead outcomes were unavailable. Ledger status and conversion fields represent export snapshots rather than verified historical month-end states. Sales and delivered session revenue measure different activity and must not be added or treated as a purchase-usage reconciliation. Instructor comparisons do not establish causation.

Validation: metric reconciliation, six period-scope tests, deletion API regression, presenter and speaker-note tests, and DOM checks against both populated final reports pass. DOM checks cover unique anchors, generated notes, private-note preservation and cleaned copy. Visual browser review was unavailable. Local reports are updated; the Railway deployment has not been deployed with these changes.
