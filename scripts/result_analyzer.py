# ============================================================
# Harbinger — result_analyzer.py
# Calculates medians, slowdown ratios, detects plan transitions,
# and performs risk classification.
# ============================================================

import statistics
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import REGRESSION_THRESHOLD


def analyze_state(times: list, plan_structure: str, baseline_median: float, baseline_plan: str, regression_threshold: float = REGRESSION_THRESHOLD) -> dict:
    """
    Analyzes measurements for a single selectivity state.
    Returns:
      - all_times: List of run times (ms)
      - sorted_times: Sorted list of run times (ms)
      - median: Median execution time (ms)
      - mean: Mean execution time (ms)
      - min_time: Minimum execution time (ms)
      - max_time: Maximum execution time (ms)
      - slowdown: Slowdown ratio vs baseline
      - is_perf_regression: True if slowdown >= regression_threshold
      - is_plan_transition: True if plan_structure differs from baseline_plan
      - plan_structure: The plan structure string
    """
    sorted_times = sorted(times)
    median = statistics.median(times)
    mean = statistics.mean(times)
    
    slowdown = round(median / baseline_median, 3) if baseline_median else 1.0
    is_perf_regression = slowdown >= regression_threshold
    
    # Simple direct string comparison on normalized plan structure
    is_plan_transition = False
    if baseline_plan:
        is_plan_transition = plan_structure.strip() != baseline_plan.strip()
        
    return {
        "all_times": [round(t, 3) for t in times],
        "sorted_times": [round(t, 3) for t in sorted_times],
        "median": round(median, 3),
        "mean": round(mean, 3),
        "min_time": round(min(times), 3),
        "max_time": round(max(times), 3),
        "slowdown": slowdown,
        "is_perf_regression": is_perf_regression,
        "is_plan_transition": is_plan_transition,
        "plan_structure": plan_structure
    }


def classify_risk(ft_runtime: float) -> str:
    """
    Classifies risk based on the Performance Fragility Threshold (FT_runtime).
    Bands:
      - FT_runtime < 20%: Critical Risk
      - 20% <= FT_runtime < 40%: High Risk
      - 40% <= FT_runtime < 70%: Medium Risk
      - FT_runtime >= 70% or None: Low Risk
    """
    if ft_runtime is None:
        return "Low Risk"
    if ft_runtime < 20.0:
        return "Critical Risk"
    elif ft_runtime < 40.0:
        return "High Risk"
    elif ft_runtime < 70.0:
        return "Medium Risk"
    else:
        return "Low Risk"


def print_state_report(selectivity_pct: float, analysis: dict):
    """Prints a clear report for a single selectivity state."""
    perf_status = "REGRESSION" if analysis["is_perf_regression"] else "SAFE"
    plan_status = "TRANSITIONED" if analysis["is_plan_transition"] else "STABLE"
    
    print(f"\nSelectivity State: {selectivity_pct}%")
    print(f"  Median Runtime:   {analysis['median']:.3f} ms (Slowdown: {analysis['slowdown']:.2f}x) -> {perf_status}")
    print(f"  Plan Structure:   {plan_status}")
    if analysis["is_plan_transition"]:
        print("  [Plan changed from baseline]")


if __name__ == "__main__":
    # Quick self-test
    base_plan = "Index Scan using idx_orders_status on orders"
    drift_plan_same = "Index Scan using idx_orders_status on orders"
    drift_plan_diff = "Seq Scan on orders"
    
    print("Testing stable plan:")
    res_stable = analyze_state([4.1, 4.3, 4.2, 4.5, 4.0], drift_plan_same, 2.5, base_plan)
    print_state_report(15.0, res_stable)
    
    print("\nTesting transitioned plan:")
    res_trans = analyze_state([6.2, 7.1, 6.5, 5.8, 6.3], drift_plan_diff, 2.5, base_plan)
    print_state_report(20.0, res_trans)
