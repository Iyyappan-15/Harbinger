# Harbinger — Experimental Evidence Summary
## (Clean Reference Sheet for Report Writing)

---

## EXPERIMENT E-001 — Selectivity Drift Feasibility Proof

### Setup
- Table: harbinger_lab.orders
- Rows: 100,000
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

### Result Table 2: Drifted State — 25% Selectivity — All 5 Runs

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

### Result Table 3: Drifted State — 50% Selectivity — All 5 Runs

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

### Result Table 4: Full Selectivity Sweep — Master Comparison Table (Ongoing)

| Selectivity | Pending Rows | Median Runtime (ms) | Slowdown vs Baseline | Regression (>=2x)? | Plan Type |
|---|---|---|---|---|---|
| 5% (Baseline) | 5,000 | 2.193* | 1.00x | NO | Index Scan |
| 10% | 10,000 | TBD | TBD | TBD | TBD |
| 15% | 15,000 | TBD | TBD | TBD | TBD |
| 20% | 20,000 | TBD | TBD | TBD | TBD |
| 25% | 25,000 | **6.417** | **2.93x** | **YES** | Index Scan |
| 30% | 30,000 | TBD | TBD | TBD | TBD |
| 40% | 40,000 | TBD | TBD | TBD | TBD |
| 50% | 50,000 | **12.578** | **5.73x** | **YES** | Index Scan |

*Single preliminary sample — will be replaced with formal 5-run median.

---

### Key Finding (Report-Ready Sentences)

1. "PostgreSQL retained an Index Scan from 5% to 50% selectivity, yet median execution time increased by 5.73x (2.193 ms to 12.578 ms). A harmful regression occurred with NO visible plan change."

2. "At 25% selectivity, the query was already 2.93x slower than the 5% baseline — exceeding the 2x harmful regression threshold — while still using an Index Scan."

3. "The selectivity fragility threshold lies between 5% and 25%. Intermediate states (10%, 15%, 20%) must be measured to identify the exact crossing point."

---

### Screenshot Evidence Index

| Screenshot File | What It Shows | Selectivity |
|---|---|---|
| e001-baseline-5-percent-plan.png | EXPLAIN ANALYZE — Index Scan, 2.193 ms, 5,000 rows | 5% Baseline |
| e001-50-percent-update.png | UPDATE changing 45,000 rows to pending | 50% Setup |
| e001-50-percent-count.png | Row count: completed=50,000 pending=50,000 | 50% Verification |
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

---

*This file is updated automatically after each completed experiment.*
*Last updated: 2026-08-22 — Added 25% selectivity results*
