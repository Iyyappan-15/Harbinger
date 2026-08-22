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

### Result Table 2: Drifted State — 50% Selectivity — All 5 Runs

| Run | Execution Time (ms) |
|---|---|
| Run 1 | 13.560 |
| Run 2 | 17.881 |
| Run 3 | 12.578 |
| Run 4 | 9.701 |
| Run 5 | 11.001 |
| **Median** | **12.578** |
| **Mean** | **12.944** |

---

### Result Table 3: Comparison — Baseline vs 50% Drifted

| Metric | Baseline (5%) | Drifted (50%) | Change |
|---|---|---|---|
| Selectivity | 5% | 50% | +45 percentage points |
| Median runtime | 2.193 ms | 12.578 ms | +10.385 ms |
| Slowdown ratio | 1.0x | **5.73x** | EXCEEDS 2x threshold |
| Execution plan | Index Scan | Index Scan | NO CHANGE |
| Matching rows | 5,000 | 50,000 | 10x more rows |

---

### Result Table 4: 25% Selectivity — (IN PROGRESS)

| Run | Execution Time (ms) |
|---|---|
| Run 1 | TBD |
| Run 2 | TBD |
| Run 3 | TBD |
| Run 4 | TBD |
| Run 5 | TBD |
| **Median** | **TBD** |

---

### Result Table 5: Full Selectivity Sweep — Summary (Ongoing)

| Selectivity | Pending Rows | Median Runtime (ms) | Slowdown vs Baseline | Regression? | Plan Type |
|---|---|---|---|---|---|
| 5% (Baseline) | 5,000 | 2.193* | 1.00x | NO | Index Scan |
| 10% | 10,000 | TBD | TBD | TBD | TBD |
| 15% | 15,000 | TBD | TBD | TBD | TBD |
| 20% | 20,000 | TBD | TBD | TBD | TBD |
| 25% | 25,000 | TBD | TBD | TBD | TBD |
| 30% | 30,000 | TBD | TBD | TBD | TBD |
| 40% | 40,000 | TBD | TBD | TBD | TBD |
| 50% | 50,000 | **12.578** | **5.73x** | **YES** | Index Scan |

*Single preliminary sample — will be replaced with 5-run median.

---

### Key Finding (Report-Ready Sentence)

PostgreSQL retained an Index Scan from 5% to 50% selectivity, yet median execution time increased by 5.73x (2.193 ms to 12.578 ms). A harmful regression occurred with NO visible plan change.

---

### Screenshot Evidence Index

| Screenshot File | What It Shows | Selectivity State |
|---|---|---|
| e001-baseline-5-percent-plan.png | EXPLAIN ANALYZE — Index Scan, 2.193 ms, 5,000 rows | 5% Baseline |
| e001-50-percent-update.png | UPDATE command changing 45,000 rows to pending | 50% Setup |
| e001-50-percent-count.png | Row count: completed=50,000, pending=50,000 | 50% Verification |
| e001-50-percent-run-1.png | Timing run 1: 13.560 ms | 50% |
| e001-50-percent-run-2.png | Timing run 2: 17.881 ms | 50% |
| e001-50-percent-run-3.png | Timing run 3: 12.578 ms | 50% |
| e001-50-percent-run-4.png | Timing run 4: 9.701 ms | 50% |
| e001-50-percent-run-5.png | Timing run 5: 11.001 ms | 50% |

---

*This file is updated automatically after each completed experiment.*
*Last updated: 2026-08-22*
