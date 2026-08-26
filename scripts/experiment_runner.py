# ============================================================
# Harbinger — experiment_runner.py
# Runs the EXPLAIN ANALYZE benchmark query N times,
# extracts the Execution Time and parses the Plan Structure.
# ============================================================

import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import EXPLAIN_QUERY, PREDICATE_VAL, RUNS_PER_STATE
from scripts.db_connector import get_connection


def clean_plan_line(line: str) -> str:
    """Remove cost, rows, width, and actual timing/loop details from plan lines."""
    # Remove cost parameters e.g., (cost=0.29..352.87 rows=5193 width=18)
    line = re.sub(r'\(cost=.*?\)', '', line)
    # Remove actual metrics e.g., (actual rows=5000.00 loops=1)
    line = re.sub(r'\(actual.*?\)', '', line)
    return line.rstrip()


def extract_plan_structure(plan_rows: list) -> str:
    """
    Filter out timing and buffer lines, and clean cost details to get
    a normalized representation of the execution plan structure.
    """
    cleaned_lines = []
    for row in plan_rows:
        line = row[0]
        # Ignore runtime, planning, and buffer noise to avoid false transition alerts
        if any(keyword in line for keyword in ["Planning:", "Planning Time:", "Execution Time:", "Buffers:", "Trigger"]):
            continue
        cleaned = clean_plan_line(line)
        if cleaned.strip():
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def run_single(conn) -> tuple:
    """
    Execute the EXPLAIN ANALYZE query once.
    Returns: (execution_time_ms, cleaned_plan_structure_str)
    """
    with conn.cursor() as cur:
        cur.execute(EXPLAIN_QUERY, {"val": PREDICATE_VAL})
        plan_rows = cur.fetchall()

    exec_time = None
    for row in plan_rows:
        line = row[0]
        match = re.search(r"Execution Time:\s*([\d.]+)\s*ms", line)
        if match:
            exec_time = float(match.group(1))
            break

    if exec_time is None:
        raise ValueError("Could not find 'Execution Time' in EXPLAIN ANALYZE output.")

    plan_structure = extract_plan_structure(plan_rows)
    return exec_time, plan_structure


def run_benchmark(n_runs: int = RUNS_PER_STATE, verbose: bool = True) -> tuple:
    """
    Run the benchmark query n_runs times.
    Returns: (list_of_execution_times, cleaned_plan_structure_of_last_run)
    """
    if verbose:
        print(f"\n[RUN]   Running benchmark {n_runs} times (warm cache)...")

    conn = get_connection()
    times = []
    plan_structure = ""
    try:
        for i in range(1, n_runs + 1):
            exec_time, current_plan = run_single(conn)
            times.append(exec_time)
            plan_structure = current_plan   # Keep the latest plan structure
            if verbose:
                print(f"         Run {i}: {exec_time:.3f} ms")
    finally:
        conn.close()

    return times, plan_structure


if __name__ == "__main__":
    times, plan = run_benchmark(verbose=True)
    print(f"\n  All times: {[round(t,3) for t in times]}")
    print(f"  Sorted:    {sorted([round(t,3) for t in times])}")
    print("\nCleaned Plan Structure:")
    print(plan)
