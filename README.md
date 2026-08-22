# Harbinger

> **Discovering Selectivity-Drift Thresholds for Harmful PostgreSQL Query Performance Regressions**

## What is Harbinger?

Harbinger is a research tool and automated experimentation framework that identifies the exact point at which a growing percentage of matching rows causes a PostgreSQL query to cross from acceptable performance into a harmful regression — even when the query execution plan does not visibly change.

## Research Problem

PostgreSQL's query planner uses statistics (via ANALYZE) to choose between Index Scans and Sequential Scans. As data distribution changes over time (selectivity drift), the planner may retain an Index Scan even when a Sequential Scan would be faster, or vice versa. This causes silent performance regressions that are difficult to detect in production.

## Core Question

> At what selectivity percentage does a predicate query on a real PostgreSQL table cross the harmful regression threshold, and can this threshold be measured automatically and reliably?

## Methodology

- Controlled experiments on a 100,000-row PostgreSQL table
- Five warm-cache execution time samples per data state
- Median runtime as the reported metric
- Defined regression threshold: >= 2x slowdown from baseline
- Systematic sweep across selectivity levels: 5%, 10%, 15%, 20%, 25%, 30%, 40%, 50%

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 18 |
| Experiment runner | Python 3 |
| Data analysis | pandas, matplotlib |
| Evidence logging | Markdown |
| Version control | Git + GitHub |
| Reporting | LaTeX / Word |

## Project Structure

\\\
harbinger/
├── config/          # Database connection config
├── data/            # Seed data and SQL setup scripts
├── docs/            # Research evidence log and screenshots
│   └── evidence/    # Screenshot evidence per experiment
├── results/         # Experiment result CSVs and plots
├── scripts/         # Automation scripts (experiment runner)
└── tests/           # Validation and sanity tests
\\\

## Current Status

| Experiment | State | Result |
|---|---|---|
| E-001 Baseline (5%) | Done (1 sample — formal 5-run pending) | 2.193 ms |
| E-001 Drifted (50%) | Done (5-run median) | 12.578 ms — 5.73x slowdown |
| E-001 Drifted (25%) | In progress | TBD |

## Author

Iyyappan — Final Year B.E. Computer Science Engineering Project
