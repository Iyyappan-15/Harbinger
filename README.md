# Harbinger

> **Predicting PostgreSQL Query Performance and Plan Fragility Under Future Data Drift**

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Phase-3%20Complete-brightgreen)]()

---

## What is Harbinger?

Harbinger is an automated database query fragility detection framework. It simulates future data distribution changes (selectivity drift) on a PostgreSQL table and independently discovers two critical thresholds:

| Threshold | Symbol | Meaning |
|---|---|---|
| Performance Fragility Threshold | **FT_runtime** | The selectivity % where runtime exceeds 2× baseline |
| Plan Transition Threshold | **PTT** | The selectivity % where PostgreSQL changes execution plan |

> **Key finding from E-001:** Performance degradation occurred at **15%** selectivity (`FT_runtime`), while the execution plan did not change until **50%** (`PTT`). This proves that plan-type monitoring alone misses the most critical regressions.

---

## The Problem

PostgreSQL chooses between Index Scans and Sequential Scans based on table statistics. As data distribution drifts over time (e.g. more orders become `pending`), queries silently degrade:

```
5% selectivity  → Plan: Index Scan → Runtime: 0.9 ms
15% selectivity → Plan: Index Scan → Runtime: 2.4 ms  ← 2.7x SLOWER (invisible to monitors)
50% selectivity → Plan: CHANGED   → Runtime: 13.5 ms  ← 15x SLOWER
```

No existing tool detects `FT_runtime < PTT` automatically.

---

## How It Works

```
SQL Query + PostgreSQL Table
            │
            ▼
    Drift Simulator (controls selectivity)
            │
            ▼
    ┌───────────────────────┐
    │  Dual-Threshold Engine │
    │  ├── FT_runtime search │
    │  └── PTT search        │
    └───────────┬───────────┘
                │
                ▼
      Risk Classification
    (Critical / High / Medium / Low)
                │
                ▼
         Report Output
         (terminal + CSV)
```

**Measurement Protocol:** 5 warm-cache runs per selectivity state → median runtime → compared to formal 5-run baseline.

---

## Validated Results — E-001 Automated Sweep

> **Baseline (5% selectivity):** 0.892 ms (5-run median)

| Selectivity | Median (ms) | Slowdown | FT_runtime Crossed? | Plan Stable? |
|---|---|---|---|---|
| 5% (Baseline) | 0.892 | 1.00× | — | ✅ Index Scan |
| 10% | 1.678 | 1.88× | No | ✅ Index Scan |
| **15%** | **2.427** | **2.72×** | **✅ YES — FT_runtime = 15%** | ✅ Index Scan |
| 20% | 3.487 | 3.91× | Yes | ✅ Index Scan |
| 25% | 4.461 | 5.00× | Yes | ✅ Index Scan |
| **50%** | **13.530** | **15.17×** | Yes | **❌ PTT = 50% (plan changed!)** |

**Risk Classification:** 🔴 **Critical** (FT_runtime < 20%)

**Case Type:** **A** — Performance degrades (15%) *before* the planner changes strategy (50%).

---

## Project Structure

```text
harbinger/
├── config/
│   ├── db_config.py          # Real connection config (gitignored — never pushed)
│   └── db_config.example.py  # Safe template — copy and fill in your password
│
├── data/                     # Seed SQL scripts to recreate the test table
│
├── docs/
│   ├── research-evidence-log.md      # Full running evidence log with all runs
│   ├── evidence-summary-tables.md    # Clean copy-paste tables for reports
│   ├── harbinger-full-project-report.md
│   └── evidence/                     # 33 screenshot PNG files (pgAdmin EXPLAIN output)
│
├── results/                  # Generated CSVs, charts, and JSON reports (gitignored)
│
├── scripts/
│   ├── db_connector.py        # PostgreSQL connection manager
│   ├── data_state_manager.py  # Controlled selectivity changes + VACUUM ANALYZE
│   ├── experiment_runner.py   # 5-run EXPLAIN ANALYZE timing + plan structure parser
│   ├── result_analyzer.py     # Median, slowdown ratio, PTT comparison, risk bands
│   └── harbinger_engine.py    # Core orchestrator — runs the full sweep
│
├── tests/                    # Sanity and validation tests (Phase 4)
├── requirements.txt
└── README.md
```

---

## Quick Start

**1. Clone the repository:**
```bash
git clone https://github.com/Iyyappan-15/Harbinger.git
cd harbinger
```

**2. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**3. Configure your database:**
```bash
cp config/db_config.example.py config/db_config.py
# Edit config/db_config.py with your PostgreSQL credentials
```

**4. Start the FastAPI backend:**
```bash
uvicorn scripts.api_server:app --reload --port 8000
```

**5. Start the React Frontend:**
```bash
cd frontend
npm install
npm run dev -- --port 3000
```
Open `http://localhost:3000` to access the full interactive dashboard.


---

## Tech Stack

| Layer | Technology | Version | Role |
|---|---|---|---|
| Database | PostgreSQL | 18 | System under study |
| Language | Python | 3.14 | Automation engine |
| API Server | FastAPI | 0.110+ | REST API Layer |
| Frontend | React + Vite | 19 / 6 | Single Page App |
| Component UI | Material-UI (MUI) | 6.x | Dark Mode Components & Grid |
| Interactive Charts | Recharts | 2.x | D3 SVG plots with threshold overlays |
| DB Driver | psycopg2-binary | 2.9+ | Python ↔ PostgreSQL |
| Data | pandas | 3.x | Median execution calculation |
| Version Control | Git + GitHub | — | Configuration & history tracking |

---

## Risk Classification

| FT_runtime | Risk Level | Meaning |
|---|---|---|
| < 20% | 🔴 Critical | Regression near normal operating range |
| 20%–40% | 🟠 High | Regression likely within weeks |
| 40%–70% | 🟡 Medium | Time available for preventive action |
| > 70% | 🟢 Low | Unlikely to be reached in production |

---

## Roadmap

- [x] Phase 1 — PostgreSQL test environment setup
- [x] Phase 2 — Manual proof-of-concept (E-001, 6 selectivity levels, 33 screenshots)
- [x] Phase 3 — Python automation engine (dual-threshold sweep)
- [ ] Phase 4 — E-002 JOIN query experiment (trigger PTT with multi-table join)
- [x] Phase 5 — CLI application
- [x] Phase 6 — Streamlit dashboard (internal validation)
- [x] Phase 7 — React + Vite Dashboard & FastAPI Backend (presentation UI)
- [ ] Phase 8 — GitHub PR integration
- [ ] Phase 9 — Final research report and paper

---

## Author

**Iyyappan** — Final Year B.E. Computer Science Engineering
`iyyappan200509@gmail.com`
