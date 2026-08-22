# Harbinger — Complete Project Research Record
## Final Year B.E. Computer Science Engineering Project

**Author:** Iyyappan
**Email:** iyyappan200509@gmail.com
**Repository:** https://github.com/Iyyappan-15/Harbinger
**Last Updated:** 2026-08-22
**PostgreSQL Version:** 18
**Database:** harbinger_dev | Schema: harbinger_lab

---

## 1. Project Title

**Harbinger: Discovering Selectivity-Drift Thresholds for Harmful PostgreSQL Query Performance Regressions**

---

## 2. Project Abstract (Draft — For Report)

Modern relational database systems, including PostgreSQL, rely on internal cost-based query planners that select execution strategies based on table statistics. As real-world data distributions change over time — a phenomenon called selectivity drift — a growing proportion of rows may match a query predicate. This can cause silent performance regressions: the query slows significantly, yet the visible execution plan type remains unchanged, making the regression invisible to standard monitoring tools.

This project introduces Harbinger, an automated experimentation and threshold-detection framework for PostgreSQL. Harbinger systematically varies the selectivity of a predicate query across controlled data states, collects five warm-cache execution time samples per state, and uses the median runtime to identify the precise selectivity percentage at which a query crosses a defined harmful regression threshold (>= 2x baseline slowdown). The outcome is both a measured fragility threshold specific to the tested query and table, and a reusable open-source tool that can apply the same methodology to any PostgreSQL table and query.

**Keywords:** PostgreSQL, query performance, selectivity drift, index scan, execution plan, regression detection, database observability

---

## 3. Problem Statement

### 3.1 Background

PostgreSQL chooses between execution strategies (Index Scan, Sequential Scan, Bitmap Heap Scan, etc.) based on row count estimates computed from table statistics. These statistics are updated by the ANALYZE command and stored in pg_statistic. When table data changes significantly between ANALYZE runs — or when ANALYZE runs but the data distribution has drifted — the planner's cost estimates can become inaccurate.

### 3.2 Core Problem

A predicate such as `WHERE status = 'pending'` may initially match 5% of rows, making an Index Scan optimal. Over months of production use, the proportion of pending rows may grow to 30% or 50%. At high selectivity, a Sequential Scan is typically faster than an Index Scan, but PostgreSQL may retain the Index Scan if its statistics are stale or if its cost constants underestimate the true I/O cost. The result is a regression that:

- Is not surfaced by execution plan monitoring (plan type is unchanged)
- Is not surfaced by error logging (the query succeeds)
- Grows gradually, making it difficult to attribute to a specific change
- Affects production databases silently over weeks or months

### 3.3 Research Gap

No existing tool automatically measures the exact selectivity threshold at which a specific PostgreSQL query transitions from acceptable to harmful performance under warm-cache conditions using a reproducible, median-based measurement protocol.

---

## 4. Research Objectives

1. Demonstrate through controlled experiments that selectivity drift can cause harmful regressions without a visible plan-type change.
2. Identify the selectivity fragility threshold for a representative benchmark query.
3. Build and validate an automated tool (Harbinger) that applies this measurement methodology to any user-specified PostgreSQL query and table.
4. Provide reproducible, evidence-backed experimental data suitable for academic publication.

---

## 5. Project Worth Assessment

### 5.1 Academic Value

| Criterion | Assessment |
|---|---|
| Original research question | YES — no existing tool solves this specific problem |
| Real industry system (PostgreSQL) | YES — used by millions of companies worldwide |
| Measurable, quantitative outcomes | YES — timing data, thresholds, regression ratios |
| Practical engineering deliverable | YES — open-source automated tool |
| Differentiated from typical BE projects | STRONGLY YES — not a web app clone |
| Suitable for final year B.E. project | YES — appropriate scope and depth |

### 5.2 Publication Potential

| Venue | Realistic? | Requirements |
|---|---|---|
| IEEE / Springer conference paper | YES | Full sweep + literature review + automated tool |
| arXiv preprint | YES (easiest) | Same content, no peer gatekeeping |
| Academic journal | Harder | Broader experiments across query types + versions |

**Key publishable finding:** A harmful runtime regression can occur in PostgreSQL without any visible change in the top-level execution plan type. This is a verifiable, reproducible, and practically significant observation.

---

## 6. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL 18 | Core system under study |
| Experiment runner | Python 3.11+ | Automated benchmark orchestration |
| DB connector | psycopg2 | Python-to-PostgreSQL connection |
| Data analysis | pandas, numpy | Median calculation, result aggregation |
| Visualization | matplotlib, seaborn | Threshold graphs, slowdown charts |
| Evidence logging | Markdown (.md) | Living research record |
| Version control | Git + GitHub | Full project history |
| Reporting | Markdown → Word/PDF | Final paper and report |

**No cloud, no frontend, no complex infrastructure required.** The entire project runs locally on PostgreSQL + Python.

---

## 7. Methodology

### 7.1 Measurement Protocol

- **Warm cache:** Each query is run without clearing the PostgreSQL buffer cache, simulating real production conditions.
- **Five runs per state:** To account for natural timing variation, five consecutive executions are recorded.
- **Median as the reported metric:** The median of five runs is used as the representative runtime, eliminating outlier influence.
- **VACUUM (ANALYZE) after each data state change:** Statistics are always refreshed before measurement begins.

### 7.2 Regression Definition

A data state is classified as a **harmful regression** if:

```
median_runtime(drifted_state) / median_runtime(baseline) >= 2.0
```

### 7.3 Selectivity Sweep Plan

| State | Pending Rows | Selectivity | Status |
|---|---|---|---|
| Baseline | 5,000 | 5% | Measured (1 sample — 5-run formal pending) |
| Drifted | 10,000 | 10% | Pending |
| Drifted | 15,000 | 15% | Pending |
| Drifted | 20,000 | 20% | Pending |
| Drifted | 25,000 | 25% | In progress |
| Drifted | 30,000 | 30% | Pending |
| Drifted | 40,000 | 40% | Pending |
| Drifted | 50,000 | 50% | DONE — 5-run median complete |

---

## 8. Experimental Results

### 8.1 Environment

- **Machine:** Local development machine (Windows, PostgreSQL running locally)
- **PostgreSQL version:** 18
- **Database:** harbinger_dev
- **Schema:** harbinger_lab
- **Table:** harbinger_lab.orders
- **Total rows:** 100,000
- **Index:** idx_orders_status ON orders(status)
- **EXPLAIN mode:** EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)

### 8.2 Test Query

```sql
SELECT
    order_id,
    customer_id,
    order_amount
FROM harbinger_lab.orders
WHERE status = 'pending';
```

### 8.3 Baseline — 5% Selectivity (5,000 Pending Rows)

| Measurement | Value |
|---|---|
| Pending rows | 5,000 of 100,000 |
| Selectivity | 5% |
| Execution plan | Index Scan using idx_orders_status |
| Execution time | 2.193 ms |
| Sample count | 1 (preliminary — formal 5-run collection pending) |
| Buffers | shared hit = 125 |

> **Note:** This is a single timing sample used for preliminary comparison only. The formal Harbinger methodology requires five runs and uses the median. The 5% state will be re-measured with five runs when the automated tool is complete.

### 8.4 Drifted State — 50% Selectivity (50,000 Pending Rows)

**Data transformation:** 45,000 rows updated from status='completed' to status='pending', followed by VACUUM (ANALYZE).

| Run | Execution Time (ms) |
|---|---|
| 1 | 13.560 |
| 2 | 17.881 |
| 3 | 12.578 |
| 4 | 9.701 |
| 5 | 11.001 |

**Sorted:** 9.701, 11.001, 12.578, 13.560, 17.881

| Metric | Value |
|---|---|
| Median runtime | **12.578 ms** |
| Mean runtime | 12.944 ms |
| Execution plan | Index Scan using idx_orders_status (unchanged) |
| Matching rows | 50,000 |
| Buffers | shared hit = 1,250 |

### 8.5 Comparison — All Measured States vs Baseline

| Selectivity | Pending Rows | Median Runtime | Slowdown vs 5% | Regression (>=2x)? | Plan |
|---|---|---|---|---|---|
| 5% (Baseline) | 5,000 | 2.193 ms* | 1.00x | NO | Index Scan |
| 25% | 25,000 | **6.417 ms** | **2.93x** | **YES** | Index Scan |
| 50% | 50,000 | **12.578 ms** | **5.73x** | **YES** | Index Scan |

*Single preliminary sample — formal 5-run baseline pending.

### 8.5a Detailed 25% Selectivity Results

| Run | Execution Time (ms) |
|---|---|
| 1 | 5.089 |
| 2 | 6.115 |
| 3 | 9.414 |
| 4 | 6.417 |
| 5 | 9.545 |

Sorted: 5.089, 6.115, 6.417, 9.414, 9.545
**Median: 6.417 ms | Mean: 7.316 ms | Buffers: shared hit=827**

### 8.6 Key Finding from E-001 So Far

A 10x increase in selectivity (5% → 50%) caused a **5.73x slowdown** while PostgreSQL retained the same execution plan type (Index Scan). This confirms the core Harbinger hypothesis: **harmful regressions can be invisible to plan-monitoring tools.**

### 8.7 Evidence Screenshots

| File | Description |
|---|---|
| e001-baseline-5-percent-plan.png | EXPLAIN ANALYZE output at 5% selectivity baseline |
| e001-50-percent-update.png | UPDATE statement setting 50% pending rows |
| e001-50-percent-count.png | Row count verification at 50% state |
| e001-50-percent-run-1.png | Timing run 1 at 50% (13.560 ms) |
| e001-50-percent-run-2.png | Timing run 2 at 50% (17.881 ms) |
| e001-50-percent-run-3.png | Timing run 3 at 50% (12.578 ms) |
| e001-50-percent-run-4.png | Timing run 4 at 50% (9.701 ms) |
| e001-50-percent-run-5.png | Timing run 5 at 50% (11.001 ms) |

---

## 9. Project Roadmap

### Phase 1 — Complete Selectivity Sweep (Current)
- [ ] Measure 25% selectivity (5 runs, median)
- [ ] Measure 10%, 15%, 20% selectivity (5 runs each)
- [ ] Collect formal 5-run baseline at 5%
- [ ] Plot threshold curve (selectivity % vs median runtime)
- [ ] Identify exact fragility threshold

### Phase 2 — Automation Tool (Harbinger)
- [ ] Python script: db_connector.py (psycopg2 connection)
- [ ] Python script: experiment_runner.py (runs 5 queries, records times)
- [ ] Python script: data_state_manager.py (applies/restores each selectivity state)
- [ ] Python script: result_analyzer.py (calculates median, flags regressions)
- [ ] Python script: report_generator.py (produces CSV + chart)

### Phase 3 — Extended Experiments
- [ ] E-002: JOIN query across two tables
- [ ] E-003: Range predicate (WHERE order_amount > X)
- [ ] E-004: Composite index scenario

### Phase 4 — Paper and Report
- [ ] Literature review (PostgreSQL query planning papers)
- [ ] Draft paper sections
- [ ] Final result tables and graphs
- [ ] Submit to conference or arXiv

---

## 10. Limitations and Integrity Notes

1. The 5% baseline uses a single timing sample — it must be replaced with a 5-run median before any formal result is stated.
2. All measurements are on a local machine under warm-cache conditions. Cold-cache and server-environment results may differ.
3. The current experiment uses a single query pattern (equality predicate on a single indexed column). Generalization requires more query types.
4. PostgreSQL's planner behaviour may differ across versions; results are specific to PostgreSQL 18.
5. The preliminary 5.73x slowdown figure must not be cited as a final result until the 5% baseline is formally re-measured.

---

## 11. Report-Ready Abstract Paragraph (Use Verbatim or Adapt)

"In an initial controlled PostgreSQL feasibility experiment using a 100,000-row table with a B-tree index on the status column, increasing the predicate selectivity of status = 'pending' from 5% to 50% increased the median observed warm-cache execution time from a preliminary 2.193 ms baseline to 12.578 ms at the drifted state — a 5.73x slowdown. Notably, PostgreSQL retained an Index Scan at both data states, demonstrating that a severe runtime regression may occur without any visible change in the top-level execution plan type. This motivates the Harbinger framework, which automates the detection of such selectivity-drift regression thresholds."

---

## 12. Version History of This Document

| Date | Version | Changes |
|---|---|---|
| 2026-08-22 | 1.0 | Initial creation — E-001 partial results, project analysis, roadmap |

