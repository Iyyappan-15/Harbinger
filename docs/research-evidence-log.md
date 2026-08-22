# Harbinger Research Evidence Log

This file is the running evidence record for the Harbinger project. It preserves verified experiments, decisions, measurements, limitations, and report-ready findings as they occur.

## Project metadata

- Project: Harbinger - Discovering Selectivity-Drift Thresholds for Harmful PostgreSQL Query Performance Regressions
- Database: PostgreSQL 18
- Database: `harbinger_dev`
- Experiment schema: `harbinger_lab`
- Primary test table: `harbinger_lab.orders`
- Measurement policy for the MVP: warm cache, five executions per final data state, median runtime as the reported runtime.

## Experiment E-001 - Initial selectivity-drift feasibility proof

### Purpose

Verify that a controlled increase in the percentage of rows matching a PostgreSQL predicate can produce a measurable runtime regression, and observe whether the execution plan changes.

### Test query

```sql
SELECT
    order_id,
    customer_id,
    order_amount
FROM harbinger_lab.orders
WHERE status = 'pending';
```

### Table and index

- Table: `harbinger_lab.orders`
- Index: `idx_orders_status` on `status`
- Total rows: 100,000
- PostgreSQL plan capture: `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)`

### Baseline data state

- Pending orders: 5,000 of 100,000
- Selectivity: 5%
- Observed plan: Index Scan using `idx_orders_status`
- Observed execution time: 2.193 ms
- Observed actual rows: 5,000

### Drifted data state

- Pending orders: 50,000 of 100,000
- Selectivity: 50%
- Data transformation: 45,000 rows changed from `completed` to `pending`, followed by `VACUUM (ANALYZE)`.
- Observed plan: Index Scan using `idx_orders_status`
- Observed actual rows: 50,000

### Runtime samples at 50% selectivity

| Run | Execution time (ms) |
|---:|---:|
| 1 | 13.560 |
| 2 | 17.881 |
| 3 | 12.578 |
| 4 | 9.701 |
| 5 | 11.001 |

- Median runtime: 12.578 ms
- Mean runtime: 12.944 ms
- Preliminary slowdown relative to the single recorded 5% baseline: approximately 5.73x
- Absolute increase relative to that baseline: 10.385 ms

### Evidence-based finding

At 50% selectivity, the test query was substantially slower than at 5% selectivity even though PostgreSQL retained the same visible top-level plan type (Index Scan). This supports the Harbinger methodology: a harmful regression must be defined using measured runtime, while execution-plan changes are explanatory evidence rather than a mandatory condition.

### Current interpretation

- The 50% data state is a preliminary harmful state under the proposed 2x slowdown rule.
- This is not yet the final fragility threshold because intermediate drift levels have not yet been evaluated.
- The 5% state has only one recorded timing sample. Before any formal result is reported, Harbinger must collect five timing samples at both the baseline and each tested drift state, then use the median.
- The controlled update approach is appropriate for this feasibility proof. The final automated experiment must recreate or restore each data state reproducibly to avoid unintended interaction between sequential test states.

### Report-ready wording (draft)

"In an initial controlled PostgreSQL feasibility experiment with 100,000 rows, increasing the predicate selectivity of `status = 'pending'` from 5% to 50% increased the median observed execution time from a preliminary 2.193 ms baseline measurement to 12.578 ms at the drifted state. PostgreSQL retained an Index Scan, demonstrating that a harmful runtime regression may occur without a visible top-level plan-type transition. Formal evaluation will repeat all data states five times and report median values."

### Supporting screenshots

- `e001-baseline-5-percent-plan.png`
- `e001-50-percent-count.png`
- `e001-50-percent-update.png`
- `e001-50-percent-run-1.png`
- `e001-50-percent-run-2.png`
- `e001-50-percent-run-3.png`
- `e001-50-percent-run-4.png`
- `e001-50-percent-run-5.png`

---

## Experiment E-001 continued — 25% selectivity data state

### Data state

- Pending orders: 25,000 of 100,000
- Selectivity: 25%
- Data transformation: 25,000 rows changed from `pending` back to `completed`, followed by `VACUUM (ANALYZE)`.
- Observed plan: Index Scan using `idx_orders_status`
- Observed actual rows: 25,000
- Buffers: shared hit = 827
- Verified count: completed = 75,000 (75%), pending = 25,000 (25%)

### Runtime samples at 25% selectivity

| Run | Execution time (ms) |
|---:|---:|
| 1 | 5.089 |
| 2 | 6.115 |
| 3 | 9.414 |
| 4 | 6.417 |
| 5 | 9.545 |

Sorted: 5.089, 6.115, 6.417, 9.414, 9.545

- **Median runtime: 6.417 ms**
- Mean runtime: 7.316 ms
- Slowdown vs preliminary 5% baseline (2.193 ms): **2.93x**
- Regression threshold (>= 2x): **EXCEEDED**
- Plan type changed vs baseline: **NO** — Index Scan retained

### Evidence-based finding at 25%

At 25% selectivity, the query is already 2.93x slower than the 5% baseline — exceeding the 2x harmful regression threshold — while PostgreSQL still uses an Index Scan. The fragility threshold lies somewhere between 5% and 25% and must be narrowed by testing 10%, 15%, and 20%.

### Supporting screenshots

- `e001-25-percent-run-1.png` — 5.089 ms
- `e001-25-percent-run-2.png` — 6.115 ms
- `e001-25-percent-run-3.png` — 9.414 ms
- `e001-25-percent-run-4.png` — 6.417 ms
- `e001-25-percent-run-5.png` — 9.545 ms

---

## Cumulative results so far (E-001)

| Selectivity | Pending Rows | Median Runtime | Slowdown vs 5% | Regression? | Plan |
|---:|---:|---:|---:|---|---|
| 5% (baseline) | 5,000 | 2.193 ms* | 1.00x | NO | Index Scan |
| 25% | 25,000 | **6.417 ms** | **2.93x** | **YES** | Index Scan |
| 50% | 50,000 | **12.578 ms** | **5.73x** | **YES** | Index Scan |

*Single preliminary sample — formal 5-run baseline pending.

**Next states to test:** 10%, 15%, 20% (to find exact threshold crossing point)


---

## Experiment E-001 continued — 20% selectivity data state

### Data state

- Pending orders: 20,000 of 100,000
- Selectivity: 20%
- Data transformation: 5,000 rows changed from `pending` back to `completed` (from 25% state), followed by `VACUUM (ANALYZE)`.
- Observed plan: Index Scan using `idx_orders_status`
- Observed actual rows: 20,000
- Buffers: shared hit = 741
- Verified count: completed = 80,000 (80%), pending = 20,000 (20%)

### Runtime samples at 20% selectivity

| Run | Execution time (ms) |
|---:|---:|
| 1 | 6.268 |
| 2 | 7.769 |
| 3 | 5.349 |
| 4 | 7.912 |
| 5 | 4.302 |

Sorted: 4.302, 5.349, 6.268, 7.769, 7.912

- **Median runtime: 6.268 ms**
- Mean runtime: 6.320 ms
- Slowdown vs preliminary 5% baseline (2.193 ms): **2.86x**
- Regression threshold (>= 2x): **EXCEEDED**
- Plan type changed vs baseline: **NO** — Index Scan retained

### Evidence-based finding at 20%

At 20% selectivity, the query is already 2.86x slower than the 5% baseline — exceeding the 2x harmful regression threshold — while PostgreSQL still uses an Index Scan. The fragility threshold lies between 5% and 20%. Next: test 15% and 10%.

### Supporting screenshots

- `e001-20-percent-run-1.png` — 6.268 ms
- `e001-20-percent-run-2.png` — 7.769 ms
- `e001-20-percent-run-3.png` — 5.349 ms
- `e001-20-percent-run-4.png` — 7.912 ms
- `e001-20-percent-run-5.png` — 4.302 ms



---

## Experiment E-001 continued — 15% selectivity data state

### Data state

- Pending orders: 15,000 of 100,000
- Selectivity: 15%
- Data transformation: 5,000 rows changed from `pending` back to `completed` (from 20% state), followed by `VACUUM (ANALYZE)`.
- Observed plan: Index Scan using `idx_orders_status`
- Observed actual rows: 15,000
- Buffers: shared hit = 657
- Verified count: completed = 85,000 (85%), pending = 15,000 (15%)

### Runtime samples at 15% selectivity

| Run | Execution time (ms) |
|---:|---:|
| 1 | 5.124 |
| 2 | 4.391 |
| 3 | 6.106 |
| 4 | 3.737 |
| 5 | 4.078 |

Sorted: 3.737, 4.078, 4.391, 5.124, 6.106

- **Median runtime: 4.391 ms**
- Mean runtime: 4.687 ms
- Slowdown vs preliminary 5% baseline (2.193 ms): **2.00x**
- Regression threshold (>= 2x): **EXACTLY AT THRESHOLD**
- Plan type changed vs baseline: **NO** — Index Scan retained

### CRITICAL Evidence-based finding at 15%

At 15% selectivity, the median runtime (4.391 ms) is exactly 2.00x the preliminary 5% baseline (2.193 ms). This is the most significant measurement of E-001: the selectivity fragility threshold is at or very near 15%. Any selectivity above 15% produces a confirmed harmful regression.

This finding must be validated formally by:
1. Collecting a proper 5-run baseline at 5% to replace the single-sample 2.193 ms measurement.
2. Testing 10% selectivity to confirm it falls below the 2x threshold.
3. If 10% is below 2x, the threshold range is confirmed as 10%-15%.

### Supporting screenshots

- `e001-15-percent-run-1.png` — 5.124 ms
- `e001-15-percent-run-2.png` — 4.391 ms
- `e001-15-percent-run-3.png` — 6.106 ms
- `e001-15-percent-run-4.png` — 3.737 ms
- `e001-15-percent-run-5.png` — 4.078 ms

