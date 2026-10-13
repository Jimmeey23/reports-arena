# Bandra September 2026 — supplied-file reconciliation

Reconciled on **13 October 2026**. Both saved Bandra September reviews were updated; the Kemps Corner review was not changed. The nine reference HTML chapters, the supplied Performance Review and three supporting XLSX workbooks in the repository are the supplied-file basis for this revision. Original reference files are unchanged, with SHA-256 receipts in `bandra-source-reconciliation.json`.

## Content added or restored

The ten saved chapters now use the reference chapter content rather than retaining a second, conflicting generated version. Source recommendations appear once per chapter. The old executive/action-plan copies and incompatible CSV-derived month registers are no longer repeated above or below them.

| Chapter | Source information now included |
|---|---|
| Sales | Full product/distinct-sale/quantity/net/VAT register; twelve visible monthly sales scorecards; six observed upgrades across five transitions; annual/private purchase trackers; payment-method definitions; first-purchase versus first-visit attribution. |
| Class | Room-size and timetable comparisons; lean and empty sessions; first-class circumstances and later visits; hosted/partner classes; workbook-defined maturity slice, gap decomposition, intake drivers, correlations and festival phases. |
| Instructor | Recurring-slot commitments; matched-slot comparisons; roster change; historical first-timer outcomes; August payroll scorecard and the limits on September inference. |
| Membership health | Historical duration, survival, product renewal, credit use and recency populations; distinct member-level engagement segments from the base-health workbook. These are not relabelled as September churn. |
| Format | Format reach, repeat participation, cross-format behaviour, timing and complimentary allocation. |
| Cancellations/discounts | Historical discount depth, seller/product/code detail, cancellation concentration and the distinction between released-seat opportunity value and booked losses. |
| Overview | Historical business/room/member/lead registers plus rolling twelve-month and calendar-year-to-date acquisition windows with their actual maturity denominators. |
| Leads | Historical trial gate, source and associate detail, follow-up stages, open-file age and monthly cohorts; workbook-recorded drop-off reasons. |
| Behaviour | Attendance timing, frequency distribution, purchase intervals, monthly rhythm and routine/variety. |
| Performance Review | The supplied comprehensive review: September picture, equal-observation acquisition analysis, root causes, pipeline and intro-pack findings, opportunities, recommendations and limitations. Identical evidence already shown in earlier chapters is cross-linked, not appended again. |

Ten supplementary workbook sheets are placed with the relevant chapters. Their cells retain the workbook's exact values and precision; blank cells remain `n/a`. Other workbook sheets support the already-present source tables/charts rather than being appended a second time. Identical detailed tables and charts are replaced by links to their single evidence location; headline metrics may still recur where needed to understand a chapter.

## Requested chapter sequence

1. Studio Overview
2. Sales & Revenue
3. Class Performance
4. Instructor Performance
5. Membership Health / Lapsed & Churned
6. Format Comparisons
7. Cancellations & Discounts
8. Lead Performance
9. Member Behaviour
10. Performance Review

Both saved reports, their contents navigation, standalone chapter numbering and manifest/library lists follow this sequence. Source reconciliation is idempotent and does not append a second Performance Review on subsequent runs. General generation uses the same presentation policy when chapters are available.

## Discrepancies resolved

| Item | Conflicting presentation | Resolution / authoritative basis |
|---|---|---|
| September sales | Saved report: 196 transactions; reference breakdown also contains 213 payment rows. | **195 distinct sales, 210 units, 213 contributing payment rows**, per the explicitly reconciled sales reference / Atlas extract. Grouped counts can overlap. |
| Average order value | Averages based on other denominators. | **₹7,843**, the reference-rounded collections / 195 distinct sales. ₹11,003 remains spend per buyer, not AOV. |
| Discounts | Saved sales card said “9% of gross.” | **8.7% of pre-discount list value**: discount / (collections + discount). ₹1,45,209 is unchanged. 31 distinct discounted sales and 36 discounted payment lines are different populations. |
| Trial-completed wins | HTML said 1,006 wins among 3,493 trial-completed leads, but quoted a 26.1% rate. | Detailed workbook `46 The trial gate`: **911 / 3,493 = 26.08%**. Another 95 wins without a trial produce the unchanged **1,006 overall wins**. Both narrative and subgroup table are corrected. |
| One-visit attendance scenario | Sales recommendation used 98 one-visit attendees. | Workbook `06 Member frequency Sep-26`: **205** one-visit attendees among 394, or **52.0%**. The revised scenario uses 205 visits and approximately ₹1,90,757 of attributed activity value, not promised collections. |
| Single-purchase buyers | Sales recommendation claimed 103 single-purchase members, despite 139 buyers and 41 repeat buyers. | **98** single-purchase buyers, by the reference's own arithmetic. The source-median hypothetical is ₹1,90,316 and explicitly illustrative. |
| Newly acquired contribution | 19.6% versus 12.5%. | Both retained with distinct cohort labels: **first purchase** at Bandra versus **first visit** in September. First-visit cash is ₹1,91,530; neither measure overwrites the other. |
| Membership/lead populations | Older report restricted conclusions to frozen September rows because historical sources were unavailable. | The supplied historical reference/workbook populations are now shown as historical, alongside their printed scope. Snapshot status is not asserted to be a historical month-end status. |
| Sales-to-attendance ratio | 85% described as purchased credits consumed / liabilities released. | The two ledgers are distinct. Their same-month ratio cannot establish unused credits, consumption, deferred liabilities or profit. |
| Snapshot and maturation | Some sources say 18 October 2026; some workbook results claim completed 30-day windows. | Explicit caveat: these are supplied reference results, **not independently verified as of 13 October**. The entire September cohort, and even all of September 1–13, is not fully 30-day mature today. |

## Preservation and verification

- No new raw exports are substituted. Original CSVs and all reference files are untouched.
- Legacy embedded frozen CSV snapshots are archived locally as `records-before-source-reconciliation.json` beside each run. They are not exposed as drill-down evidence for a different supplied-source population. These rebuildable/private records stay ignored by Git.
- The report library's summaries, section navigation and source provenance are updated. AI manifest fallback and generated metric packs agree on 195 distinct sales and ₹7,843 AOV, even if `metrics.json` is absent on deployment.
- Private workspace databases are not edited. This is a replacement of report content; existing user-authored presentation overrides are not independently reconciled.
- Reconciliation regression tests check both runs, unique anchors, resolved evidence links, duplicate-table removal, exact supplementary workbook cells, unchanged source hashes and corrected report/AI figures. Existing AI and editorial tests also pass.

Reproduce with:

```sh
.venv/bin/python studio-app/analysis/reconcile_bandra_sources.py
.venv/bin/python -m unittest discover -s studio-app/tests -p 'bandra_source_reconciliation_test.py' -v
```

Local report files are updated. No production deployment or push was performed.
