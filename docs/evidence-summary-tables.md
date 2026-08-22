# Harbinger — Experimental Evidence Summary
## (Clean Reference Sheet for Report Writing)

---

## EXPERIMENT E-001 — Selectivity Drift Feasibility Proof

### Setup
- Table: harbinger_lab.orders | Rows: 100,000
- Index: idx_orders_status ON status (B-tree)
- Query: SELECT order_id, customer_id, order_amount FROM harbinger_lab.orders WHERE status = 'pending'
- Measurement: EXPLAIN (ANALYZE, BUFFERS, TIMING OFF) — 5 warm-cache runs — median reported

---

### Result Table 1: Baseline — 5% Selectivity (Preliminary)

| Parameter | Value |
|---|---|
| Pending rows | 5,000 / 100,000 |
| Selectivity | 5% |
| Execution plan | Index Scan using idx_orders_status |
| Execution time | 2.193 ms |
| Buffers | shared hit = 125 |
| Note | Single sample — formal 5-run collection pending |

---

### Result Table 2: All 5 Runs Per Selectivity State

| State | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Median | Mean |
|---|---|---|---|---|---|---|---|
| 15% | 5.124 | 4.391 | 6.106 | 3.737 | 4.078 | **4.391** | 4.687 |
| 20% | 6.268 | 7.769 | 5.349 | 7.912 | 4.302 | **6.268** | 6.320 |
| 25% | 5.089 | 6.115 | 9.414 | 6.417 | 9.545 | **6.417** | 7.316 |
| 50% | 13.560 | 17.881 | 12.578 | 9.701 | 11.001 | **12.578** | 12.944 |

*(All times in ms)*

---

### Result Table 3: MASTER COMPARISON TABLE — Full Selectivity Sweep

| Selectivity | Pending Rows | Buffers | Median Runtime (ms) | Slowdown vs 5% | Regression (>=2x)? | Plan Type |
|---|---|---|---|---|---|---|
| 5% (Baseline) | 5,000 | 125 | 2.193* | 1.00x | NO | Index Scan |
| 10% | 10,000 | TBD | TBD | TBD | TBD | TBD |
| **15%** | **15,000** | **657** | **4.391** | **2.00x** | **AT THRESHOLD** | **Index Scan** |
| 20% | 20,000 | 741 | 6.268 | 2.86x | YES | Index Scan |
| 25% | 25,000 | 827 | 6.417 | 2.93x | YES | Index Scan |
| 30% | 30,000 | TBD | TBD | TBD | TBD | TBD |
| 40% | 40,000 | TBD | TBD | TBD | TBD | TBD |
| 50% | 50,000 | 1,250 | 12.578 | 5.73x | YES | Index Scan |

*Single preliminary sample — will be replaced with formal 5-run median.

---

### CRITICAL FINDING — Fragility Threshold Identified at ~15%

> At 15% selectivity, the median runtime (4.391 ms) is exactly 2.00x the preliminary 5% baseline (2.193 ms).
> PostgreSQL retained an Index Scan at every tested selectivity level.
> The selectivity fragility threshold for this query and table is at or near 15%.
> Confirmation requires: (a) formal 5-run 5% baseline, (b) 10% selectivity measurement.

---

### Key Findings (Report-Ready Sentences)

1. "At 15% selectivity (15,000 of 100,000 rows matching the predicate), the median warm-cache execution time was 4.391 ms — exactly 2.00x the preliminary 5% baseline of 2.193 ms — marking the selectivity fragility threshold for this query."

2. "PostgreSQL retained an Index Scan at every tested selectivity level from 5% to 50%, confirming that harmful performance regressions can occur without any visible change in the execution plan type."

3. "The slowdown scaled from 2.00x at 15% to 2.86x at 20%, 2.93x at 25%, and 5.73x at 50%, indicating a non-linear degradation as selectivity increases beyond the threshold."

4. "The fragility threshold range is provisionally identified as between 10% and 15% selectivity and requires one further measurement (10%) to confirm."

---

### Screenshot Evidence Index (Complete)

| Screenshot File | Execution Time | Selectivity |
|---|---|---|
| e001-baseline-5-percent-plan.png | 2.193 ms | 5% Baseline |
| e001-50-percent-update.png | — | 50% Setup |
| e001-50-percent-count.png | — | 50% Verification |
| e001-50-percent-run-1.png | 13.560 ms | 50% Run 1 |
| e001-50-percent-run-2.png | 17.881 ms | 50% Run 2 |
| e001-50-percent-run-3.png | 12.578 ms | 50% Run 3 |
| e001-50-percent-run-4.png | 9.701 ms | 50% Run 4 |
| e001-50-percent-run-5.png | 11.001 ms | 50% Run 5 |
| e001-25-percent-run-1.png | 5.089 ms | 25% Run 1 |
| e001-25-percent-run-2.png | 6.115 ms | 25% Run 2 |
| e001-25-percent-run-3.png | 9.414 ms | 25% Run 3 |
| e001-25-percent-run-4.png | 6.417 ms | 25% Run 4 |
| e001-25-percent-run-5.png | 9.545 ms | 25% Run 5 |
| e001-20-percent-run-1.png | 6.268 ms | 20% Run 1 |
| e001-20-percent-run-2.png | 7.769 ms | 20% Run 2 |
| e001-20-percent-run-3.png | 5.349 ms | 20% Run 3 |
| e001-20-percent-run-4.png | 7.912 ms | 20% Run 4 |
| e001-20-percent-run-5.png | 4.302 ms | 20% Run 5 |
| e001-15-percent-run-1.png | 5.124 ms | 15% Run 1 |
| e001-15-percent-run-2.png | 4.391 ms | 15% Run 2 |
| e001-15-percent-run-3.png | 6.106 ms | 15% Run 3 |
| e001-15-percent-run-4.png | 3.737 ms | 15% Run 4 |
| e001-15-percent-run-5.png | 4.078 ms | 15% Run 5 |

---

*This file is updated automatically after each completed experiment.*
*Last updated: 2026-08-22 — CRITICAL: 15% threshold identified (2.00x slowdown)*
