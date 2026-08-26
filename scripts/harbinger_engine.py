# ============================================================
# Harbinger — harbinger_engine.py
# The core orchestrator that conducts selectivity sweeps,
# parses thresholds, and outputs query fragility reports.
# ============================================================

import sys
import os
import json
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import (
    SELECTIVITY_LEVELS, RUNS_PER_STATE, REGRESSION_THRESHOLD,
    TARGET_TABLE, BENCHMARK_QUERY
)
from scripts.data_state_manager import set_selectivity, verify_state
from scripts.experiment_runner import run_benchmark
from scripts.result_analyzer import analyze_state, classify_risk


def run_full_sweep(regression_threshold: float = REGRESSION_THRESHOLD, verbose: bool = True, selectivity_levels: list = None, runs_per_state: int = None) -> dict:
    """
    Orchestrates the entire selectivity sweep:
      1. Records initial state so we can restore it later.
      2. Starts from baseline (lowest selectivity in SELECTIVITY_LEVELS).
      3. Gathers formal 5-run median baseline runtime & baseline plan.
      4. Iterates through all subsequent selectivity levels.
      5. Identifies FT_runtime (Performance Threshold) and PTT (Plan Transition Threshold).
      6. Restores the database back to its initial state.
      7. Returns sweep results and discovered thresholds.
    """
    if verbose:
        print("=" * 60)
        print("HARBINGER AUTOMATED DUAL-THRESHOLD SWEEP ENGINE")
        print("=" * 60)
    
    # 1. Capture initial data state to restore later
    if verbose:
        print("[INIT] Capturing current data state to restore after sweep...")
    initial_counts = verify_state(verbose=False)
    initial_pending = initial_counts.get("pending", 5000)
    initial_pct = round(initial_pending / 100000.0 * 100.0, 1)
    if verbose:
        print(f"       Initial state: {initial_pct}% selectivity ({initial_pending:,} pending rows)")

    levels_to_sweep = selectivity_levels if selectivity_levels is not None else SELECTIVITY_LEVELS
    runs_count = runs_per_state if runs_per_state is not None else RUNS_PER_STATE

    # Sort selectivity levels to sweep systematically
    sweep_levels = sorted(levels_to_sweep)
    baseline_level = sweep_levels[0]
    drift_levels = sweep_levels[1:]
    
    sweep_results = []
    
    # 2. Establish Baseline (lowest level)
    if verbose:
        print(f"\n[SWEEP] Establishing baseline at {baseline_level}% selectivity...")
    
    set_selectivity(baseline_level, verbose=verbose)
    baseline_times, baseline_plan = run_benchmark(n_runs=runs_count, verbose=verbose)
    
    # Analyze baseline against itself to setup tracking structures
    baseline_analysis = analyze_state(
        times=baseline_times,
        plan_structure=baseline_plan,
        baseline_median=None, # It is the baseline
        baseline_plan=None,
        regression_threshold=regression_threshold
    )
    baseline_median = baseline_analysis["median"]
    
    # Store baseline result
    baseline_entry = {
        "selectivity_pct": baseline_level,
        "median_ms": baseline_median,
        "slowdown": 1.00,
        "is_perf_regression": False,
        "is_plan_transition": False,
        "plan_structure": baseline_plan,
        "all_times": baseline_times
    }
    sweep_results.append(baseline_entry)
    
    ft_runtime = None
    ptt = None
    
    # 3. Sweep drifted states
    for level in drift_levels:
        if verbose:
            print(f"\n[SWEEP] Advancing to {level}% selectivity...")
            
        set_selectivity(level, verbose=verbose)
        times, plan = run_benchmark(n_runs=runs_count, verbose=verbose)
        
        analysis = analyze_state(
            times=times,
            plan_structure=plan,
            baseline_median=baseline_median,
            baseline_plan=baseline_plan,
            regression_threshold=regression_threshold
        )
        
        entry = {
            "selectivity_pct": level,
            "median_ms": analysis["median"],
            "slowdown": analysis["slowdown"],
            "is_perf_regression": analysis["is_perf_regression"],
            "is_plan_transition": analysis["is_plan_transition"],
            "plan_structure": plan,
            "all_times": times
        }
        sweep_results.append(entry)
        
        # Track first performance regression threshold
        if analysis["is_perf_regression"] and ft_runtime is None:
            ft_runtime = level
            if verbose:
                print(f"       >>> PERFORMANCE REGRESSION DETECTED AT {level}% (FT_runtime = {level}%)")
                
        # Track first plan transition threshold
        if analysis["is_plan_transition"] and ptt is None:
            ptt = level
            if verbose:
                print(f"       >>> PLAN TRANSITION DETECTED AT {level}% (PTT = {level}%)")

    # 4. Restore initial state
    if verbose:
        print(f"\n[RESTORE] Restoring database back to initial state ({initial_pct}% selectivity)...")
    set_selectivity(initial_pct, verbose=verbose)
    
    # 5. Build Summary
    risk = classify_risk(ft_runtime)
    
    summary = {
        "target_table": TARGET_TABLE,
        "benchmark_query": BENCHMARK_QUERY.strip(),
        "baseline_median_ms": baseline_median,
        "ft_runtime": ft_runtime,
        "ptt": ptt,
        "risk_classification": risk,
        "results": sweep_results
    }
    
    if verbose:
        print_final_summary_report(summary)
        
    return summary


def print_final_summary_report(summary: dict):
    """Prints a beautiful markdown-friendly terminal summary report."""
    print("\n" + "=" * 60)
    print("HARBINGER QUERY FRAGILITY REPORT")
    print("=" * 60)
    print(f"Target Table: {summary['target_table']}")
    print(f"Baseline Median: {summary['baseline_median_ms']:.3f} ms")
    print("-" * 60)
    
    print("PERFORMANCE FRAGILITY")
    if summary["ft_runtime"] is not None:
        print(f"  FT_runtime:   {summary['ft_runtime']}% selectivity")
        print(f"  Risk Status:  {summary['risk_classification']}")
    else:
        print("  FT_runtime:   None (No performance regression detected)")
        print(f"  Risk Status:  Low Risk")
        
    print("\nPLAN TRANSITION FRAGILITY")
    if summary["ptt"] is not None:
        print(f"  PTT:          {summary['ptt']}% selectivity")
    else:
        print("  PTT:          None (Execution plan remained stable)")
        
    print("\nKEY FINDING:")
    ft = summary["ft_runtime"]
    pt = summary["ptt"]
    
    if ft is not None and pt is not None:
        if ft < pt:
            print(f"  Performance degradation occurs BEFORE execution plan transition.")
            print(f"  FT_runtime = {ft}%  <  PTT = {pt}%")
        elif ft > pt:
            print(f"  Execution plan transition occurs BEFORE performance degradation.")
            print(f"  PTT = {pt}%  <  FT_runtime = {ft}%")
        else:
            print(f"  Performance degradation and plan transition occur simultaneously at {ft}%.")
    elif ft is not None and pt is None:
        print(f"  Performance degradation occurs WITHOUT any execution plan transition (Case B).")
        print(f"  FT_runtime = {ft}% | PTT = None")
    elif ft is None and pt is not None:
        print(f"  Execution plan transition occurs WITHOUT performance regression (Case C).")
        print(f"  PTT = {pt}% | FT_runtime = None")
    else:
        print("  No fragility detected within the tested drift range (Case D).")
        
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_full_sweep(verbose=True)
