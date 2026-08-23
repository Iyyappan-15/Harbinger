# Harbinger — Experimental Evidence Summary
## E-001 FINAL VALIDATED RESULTS — All States, Formal 5-Run Median Baseline

**Last updated: 2026-08-23 — E-001 100% COMPLETE**

---

## FORMAL BASELINE — 5% Selectivity (5-Run Median)

| Run | Execution Time (ms) |
|---|---|
| Run 1 | 2.528 |
| Run 2 | 2.882 |
| Run 3 | 2.527 |
| Run 4 | 1.347 |
| Run 5 | 1.735 |
| **Sorted** | 1.347, 1.735, 2.527, 2.528, 2.882 |
| **Formal Median** | **2.527 ms** |
| ~~Preliminary (1 sample)~~ | ~~2.193 ms~~ — retired |

---

## MASTER RESULT TABLE — E-001 Complete (All 5-Run Medians, Formal Baseline)

| Selectivity | Pending Rows | Buffers | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Median (ms) | Slowdown | Regression? | Plan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **5% (Baseline)** | 5,000 | 486 | 2.528 | 2.882 | 2.527 | 1.347 | 1.735 | **2.527** | **1.00x** | NO ✅ | Index Scan |
| 10% | 10,000 | 571 | 2.591 | 4.513 | 3.397 | 2.153 | 3.584 | **3.397** | **1.34x** | NO ✅ | Index Scan |
| 15% | 15,000 | 657 | 5.124 | 4.391 | 6.106 | 3.737 | 4.078 | **4.391** | **1.74x** | NO ✅ | Index Scan |
| **20%** | **20,000** | **741** | **6.268** | **7.769** | **5.349** | **7.912** | **4.302** | **6.268** | **2.48x** | **YES ❌** | **Index Scan** |
| 25% | 25,000 | 827 | 5.089 | 6.115 | 9.414 | 6.417 | 9.545 | **6.417** | **2.54x** | YES ❌ | Index Scan |
| 50% | 50,000 | 1,250 | 13.560 | 17.881 | 12.578 | 9.701 | 11.001 | **12.578** | **4.98x** | YES ❌ | Index Scan |

---

## CONFIRMED FRAGILITY THRESHOLD: 15% → 20% Selectivity

| State | Median | Slowdown | Safe? |
|---|---|---|---|
| 15% | 4.391 ms | 1.74x | ✅ SAFE — below 2x |
| **20%** | **6.268 ms** | **2.48x** | **❌ FIRST REGRESSION** |

> The selectivity fragility threshold for this query is confirmed between **15% and 20% selectivity**.
> PostgreSQL retained an Index Scan at every tested level — regressions are invisible to plan monitoring.

---

## SORTED VALUES PER STATE

| Selectivity | Sorted Values (ms) | Median |
|---|---|---|
| 5% (Baseline) | 1.347, 1.735, **2.527**, 2.528, 2.882 | 2.527 |
| 10% | 2.153, 2.591, **3.397**, 3.584, 4.513 | 3.397 |
| 15% | 3.737, 4.078, **4.391**, 5.124, 6.106 | 4.391 |
| 20% | 4.302, 5.349, **6.268**, 7.769, 7.912 | 6.268 |
| 25% | 5.089, 6.115, **6.417**, 9.414, 9.545 | 6.417 |
| 50% | 9.701, 11.001, **12.578**, 13.560, 17.881 | 12.578 |

---

## FINAL REPORT-READY FINDINGS

**Finding 1 — Threshold:**
"The selectivity fragility threshold for the benchmark query lies between 15% and 20% selectivity. At 15% (15,000 rows), the median runtime was 4.391 ms (1.74x baseline — safe). At 20% (20,000 rows), it was 6.268 ms (2.48x baseline — first harmful regression). PostgreSQL retained an Index Scan at every tested level."

**Finding 2 — Plan Invisibility:**
"An Index Scan was retained from 5% to 50% selectivity. At 50%, the slowdown was 4.98x — yet the execution plan showed no change. Plan-type monitoring would have reported safe at every level."

**Finding 3 — Baseline Methodology Matters:**
"A preliminary single-sample baseline of 2.193 ms suggested the threshold was at 15% (2.00x). The formal 5-run median baseline of 2.527 ms revised this to the 15%–20% range (1.74x at 15%, 2.48x at 20%). This confirms that single-sample baselines produce misleading results and validates the Harbinger 5-run median protocol."

**Finding 4 — Non-Linear Degradation:**
"Slowdown scaled non-linearly: 1.34x (10%), 1.74x (15%), 2.48x (20%), 2.54x (25%), 4.98x (50%). The steepest jump was between 15% and 20% — a 0.74x increase in slowdown for a 5% increase in selectivity — marking the transition zone."

**Finding 5 — Buffer Correlation:**
"Shared buffer hits: 486 (5%), 571 (10%), 657 (15%), 741 (20%), 827 (25%), 1,250 (50%). Proportional I/O growth confirms the regression is real, not measurement noise."

---

## COMPLETE SCREENSHOT EVIDENCE INDEX (33 Files)

| File | Time | State |
|---|---|---|
| e001-baseline-5-percent-plan.png | 2.193 ms (preliminary) | 5% Preliminary |
| e001-baseline-5pct-formal-run-1.png | 2.528 ms | 5% Formal Run 1 |
| e001-baseline-5pct-formal-run-2.png | 2.882 ms | 5% Formal Run 2 |
| e001-baseline-5pct-formal-run-3.png | 2.527 ms | 5% Formal Run 3 |
| e001-baseline-5pct-formal-run-4.png | 1.347 ms | 5% Formal Run 4 |
| e001-baseline-5pct-formal-run-5.png | 1.735 ms | 5% Formal Run 5 |
| e001-10-percent-run-1.png | 2.591 ms | 10% Run 1 |
| e001-10-percent-run-2.png | 4.513 ms | 10% Run 2 |
| e001-10-percent-run-3.png | 3.397 ms | 10% Run 3 |
| e001-10-percent-run-4.png | 2.153 ms | 10% Run 4 |
| e001-10-percent-run-5.png | 3.584 ms | 10% Run 5 |
| e001-15-percent-run-1.png | 5.124 ms | 15% Run 1 |
| e001-15-percent-run-2.png | 4.391 ms | 15% Run 2 |
| e001-15-percent-run-3.png | 6.106 ms | 15% Run 3 |
| e001-15-percent-run-4.png | 3.737 ms | 15% Run 4 |
| e001-15-percent-run-5.png | 4.078 ms | 15% Run 5 |
| e001-20-percent-run-1.png | 6.268 ms | 20% Run 1 |
| e001-20-percent-run-2.png | 7.769 ms | 20% Run 2 |
| e001-20-percent-run-3.png | 5.349 ms | 20% Run 3 |
| e001-20-percent-run-4.png | 7.912 ms | 20% Run 4 |
| e001-20-percent-run-5.png | 4.302 ms | 20% Run 5 |
| e001-25-percent-run-1.png | 5.089 ms | 25% Run 1 |
| e001-25-percent-run-2.png | 6.115 ms | 25% Run 2 |
| e001-25-percent-run-3.png | 9.414 ms | 25% Run 3 |
| e001-25-percent-run-4.png | 6.417 ms | 25% Run 4 |
| e001-25-percent-run-5.png | 9.545 ms | 25% Run 5 |
| e001-50-percent-run-1.png | 13.560 ms | 50% Run 1 |
| e001-50-percent-run-2.png | 17.881 ms | 50% Run 2 |
| e001-50-percent-run-3.png | 12.578 ms | 50% Run 3 |
| e001-50-percent-run-4.png | 9.701 ms | 50% Run 4 |
| e001-50-percent-run-5.png | 11.001 ms | 50% Run 5 |
| e001-50-percent-count.png | — | 50% count verify |
| e001-50-percent-update.png | — | 50% setup |

---
*E-001 COMPLETE — 2026-08-23 | All 6 states measured with formal 5-run medians*
