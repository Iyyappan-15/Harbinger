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

### Result Table 1: Baseline — 5% Selectivity

| Parameter | Value |
|---|---|
| Pending rows | 5,000 / 100,000 |
| Selectivity | 5% |
| Execution plan | Index Scan using idx_orders_status |
| Execution time | 2.193 ms |
| Note | Single sample — formal 5-run collection pending |

---

### Result Table 2: Drifted State — 20% Selectivity — All 5 Runs

| Run | Execution Time (ms) |
|---|---|
| Run 1 | 6.268 |
| Run 2 | 7.769 |
| Run 3 | 5.349 |
| Run 4 | 7.912 |
| Run 5 | 4.302 |
| **Sorted** | 4.302, 5.349, 6.268, 7.769, 7.912 |
| **Median** | **6.268** |
| **Mean** | **6.320** |

---

### Result Table 3: Drifted State — 25% Selectivity — All 5 Runs

| Run | Execution Time (ms) |
|---|---|
| Run 1 | 5.089 |
| Run 2 | 6.115 |
| Run 3 | 9.414 |
| Run 4 | 6.417 |
| Run 5 | 9.545 |
| **Sorted** | 5.089, 6.115, 6.417, 9.414, 9.545 |
| **Median** | **6.417** |
| **Mean** | **7.316** |

---

### Result Table 4: Drifted State — 50% Selectivity — All 5 Runs

| Run | Execution Time (ms) |
|---|---|
| Run 1 | 13.560 |
| Run 2 | 17.881 |
| Run 3 | 12.578 |
| Run 4 | 9.701 |
| Run 5 | 11.001 |
| **Sorted** | 9.701, 11.001, 12.578, 13.560, 17.881 |
| **Median** | **12.578** |
| **Mean** | **12.944** |

---

### Result Table 5: Full Selectivity Sweep — Master Comparison Table (Ongoing)

| Selectivity | Pending Rows | Buffers | Median Runtime (ms) | Slowdown vs 5% | Regression (>=2x)? | Plan Type |
|---|---|---|---|---|---|---|
| 5% (Baseline) | 5,000 | 125 | 2.193* | 1.00x | NO | Index Scan |
| 10% | 10,000 | TBD | TBD | TBD | TBD | TBD |
| 15% | 15,000 | TBD | TBD | TBD | TBD | TBD |
| 20% | 20,000 | 741 | **6.268** | **2.86x** | **YES** | Index Scan |
| 25% | 25,000 | 827 | **6.417** | **2.93x** | **YES** | Index Scan |
| 30% | 30,000 | TBD | TBD | TBD | TBD | TBD |
| 40% | 40,000 | TBD | TBD | TBD | TBD | TBD |
| 50% | 50,000 | 1,250 | **12.578** | **5.73x** | **YES** | Index Scan |

*Single preliminary sample — will be replaced with formal 5-run median.

---

### Key Findings (Report-Ready Sentences)

1. "PostgreSQL retained an Index Scan across all tested selectivity levels. A harmful regression (>=2x slowdown) occurred at every drifted state tested — 20%, 25%, and 50%."

2. "At 20% selectivity, the median runtime was 6.268 ms — a 2.86x slowdown vs the 2.193 ms baseline — despite no plan change."

3. "At 25% selectivity, median runtime was 6.417 ms — a 2.93x slowdown. At 50%, median runtime was 12.578 ms — a 5.73x slowdown."

4. "The selectivity fragility threshold lies between 5% and 20%. States 10% and 15% are being tested to identify the exact crossing point."

---

### Screenshot Evidence Index

| Screenshot File | What It Shows | Selectivity |
|---|---|---|
| e001-baseline-5-percent-plan.png | EXPLAIN ANALYZE — Index Scan, 2.193 ms, 5,000 rows | 5% Baseline |
| e001-50-percent-update.png | UPDATE changing 45,000 rows to pending | 50% Setup |
| e001-50-percent-count.png | Row count verification at 50% | 50% |
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

---

*This file is updated automatically after each completed experiment.*
*Last updated: 2026-08-22 — Added 20% selectivity results*
