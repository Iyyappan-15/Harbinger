# ============================================================
# Harbinger — harbinger_cli.py
# Command-line interface for the Harbinger dual-threshold engine.
#
# Usage:
#   python -m cli.harbinger_cli run
#   python -m cli.harbinger_cli run --threshold 1.5
#   python -m cli.harbinger_cli run --levels 5 10 20 50 --save
#   python -m cli.harbinger_cli connect
#   python -m cli.harbinger_cli status
# ============================================================

import argparse
import sys
import os
import csv
import json
import statistics
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import (
    SELECTIVITY_LEVELS, RUNS_PER_STATE, REGRESSION_THRESHOLD,
    TARGET_TABLE, PREDICATE_VAL
)
from scripts.db_connector import get_connection, test_connection
from scripts.data_state_manager import verify_state
from scripts.result_analyzer import classify_risk


# ─── Helpers ────────────────────────────────────────────────

def print_banner():
    print()
    print("=" * 60)
    print("  HARBINGER  —  Dual-Threshold Fragility Engine")
    print("  PostgreSQL Query Performance & Plan Fragility")
    print("=" * 60)
    print()


def save_csv(summary: dict, output_path: str):
    """Write the per-state sweep results to a CSV file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'selectivity_pct', 'median_ms', 'slowdown',
            'is_perf_regression', 'is_plan_transition', 'runs'
        ])
        for row in summary['results']:
            writer.writerow([
                row['selectivity_pct'],
                row['median_ms'],
                row['slowdown'],
                row['is_perf_regression'],
                row['is_plan_transition'],
                json.dumps(row['all_times'])
            ])
    print(f"\n[SAVED] CSV -> {output_path}")


def save_json(summary: dict, output_path: str):
    """Write the full summary to a JSON file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    # Strip plan structure from JSON to keep it readable
    clean = {k: v for k, v in summary.items() if k != 'results'}
    clean['results'] = []
    for row in summary['results']:
        clean_row = {k: v for k, v in row.items() if k != 'plan_structure'}
        clean['results'].append(clean_row)
    clean['generated_at'] = datetime.now().isoformat()
    with open(output_path, 'w') as f:
        json.dump(clean, f, indent=2)
    print(f"[SAVED] JSON -> {output_path}")


# ─── Commands ───────────────────────────────────────────────

def cmd_connect(args):
    """Test database connection and exit."""
    print_banner()
    print("[CMD] Testing database connection...")
    test_connection()


def cmd_status(args):
    """Show current table row distribution."""
    print_banner()
    print(f"[CMD] Current data distribution in {TARGET_TABLE}:\n")
    counts = verify_state(verbose=True)
    total  = sum(counts.values())
    pending = counts.get(PREDICATE_VAL, 0)
    print(f"\n  Total rows : {total:,}")
    print(f"  Selectivity: {pending / total * 100:.1f}%  ({pending:,} rows match '{PREDICATE_VAL}')")


def cmd_run(args):
    """Run the full dual-threshold selectivity sweep."""
    print_banner()

    # Override config values from CLI flags if provided
    threshold = args.threshold
    levels    = sorted(args.levels) if args.levels else sorted(SELECTIVITY_LEVELS)
    runs      = args.runs

    print(f"  Regression threshold : {threshold}×")
    print(f"  Selectivity levels   : {levels}")
    print(f"  Runs per state       : {runs}")
    print(f"  Target table         : {TARGET_TABLE}")
    print()

    # Dynamically patch config for this run
    import config.db_config as cfg
    original_levels    = cfg.SELECTIVITY_LEVELS
    original_runs      = cfg.RUNS_PER_STATE
    original_threshold = cfg.REGRESSION_THRESHOLD

    cfg.SELECTIVITY_LEVELS   = levels
    cfg.RUNS_PER_STATE       = runs
    cfg.REGRESSION_THRESHOLD = threshold

    from scripts.harbinger_engine import run_full_sweep
    summary = run_full_sweep(regression_threshold=threshold, verbose=True)

    # Restore config
    cfg.SELECTIVITY_LEVELS   = original_levels
    cfg.RUNS_PER_STATE       = original_runs
    cfg.REGRESSION_THRESHOLD = original_threshold

    # Save outputs if requested
    if args.save or args.out_csv or args.out_json:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path  = args.out_csv  or f"results/sweep_{ts}.csv"
        json_path = args.out_json or f"results/sweep_{ts}.json"
        save_csv(summary, csv_path)
        save_json(summary, json_path)

    return summary


# ─── Argument Parser ────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog='harbinger',
        description='Harbinger — PostgreSQL Query Fragility Detection (Dual-Threshold Engine)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.harbinger_cli connect
  python -m cli.harbinger_cli status
  python -m cli.harbinger_cli run
  python -m cli.harbinger_cli run --threshold 1.5
  python -m cli.harbinger_cli run --levels 5 10 20 50
  python -m cli.harbinger_cli run --save
  python -m cli.harbinger_cli run --threshold 2.0 --levels 5 10 15 20 25 50 --save
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # ── connect ──────────────────────────────────────────────
    subparsers.add_parser(
        'connect',
        help='Test the database connection and exit'
    )

    # ── status ───────────────────────────────────────────────
    subparsers.add_parser(
        'status',
        help='Show current row distribution in the target table'
    )

    # ── run ──────────────────────────────────────────────────
    run_parser = subparsers.add_parser(
        'run',
        help='Run the full dual-threshold selectivity sweep'
    )
    run_parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=REGRESSION_THRESHOLD,
        help=f'Slowdown multiplier to classify as regression (default: {REGRESSION_THRESHOLD})'
    )
    run_parser.add_argument(
        '--levels', '-l',
        type=int,
        nargs='+',
        default=None,
        help=f'Selectivity levels to sweep in %% (default: {SELECTIVITY_LEVELS})'
    )
    run_parser.add_argument(
        '--runs', '-r',
        type=int,
        default=RUNS_PER_STATE,
        help=f'Number of timing runs per state (default: {RUNS_PER_STATE})'
    )
    run_parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='Auto-save results to results/ as CSV + JSON with timestamp'
    )
    run_parser.add_argument(
        '--out-csv',
        type=str,
        default=None,
        help='Custom path for CSV output (implies --save)'
    )
    run_parser.add_argument(
        '--out-json',
        type=str,
        default=None,
        help='Custom path for JSON output (implies --save)'
    )

    return parser


# ─── Entry Point ────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.command == 'connect':
        cmd_connect(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'run':
        cmd_run(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
