# ============================================================
# Harbinger — data_state_manager.py
# Sets the table to an exact selectivity percentage
# and refreshes PostgreSQL statistics.
# ============================================================

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.db_config import (
    TARGET_TABLE, PREDICATE_COL, PREDICATE_VAL,
    ORDER_COL, TOTAL_ROWS
)
from scripts.db_connector import get_connection


def set_selectivity(target_pct: float, verbose: bool = True) -> int:
    """
    Set the table so that exactly target_pct % of rows have
    PREDICATE_COL = PREDICATE_VAL.

    Strategy:
      1. Set ALL rows to the non-predicate value ('completed').
      2. Set exactly target_count rows to the predicate value ('pending').
      3. Run VACUUM (ANALYZE) to refresh planner statistics.

    Returns the actual pending row count after the operation.
    """
    target_count = int(TOTAL_ROWS * target_pct / 100)
    non_pred_val = "completed"   # the other value

    if verbose:
        print(f"\n[STATE] Setting selectivity to {target_pct}% ({target_count:,} rows)...")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Step 1: Reset all rows to non-predicate value
            cur.execute(
                f"UPDATE {TARGET_TABLE} SET {PREDICATE_COL} = %s",
                (non_pred_val,)
            )
            if verbose:
                print(f"         Reset all {TOTAL_ROWS:,} rows to '{non_pred_val}'")

            # Step 2: Set exactly target_count rows to predicate value
            cur.execute(
                f"""
                UPDATE {TARGET_TABLE}
                SET {PREDICATE_COL} = %s
                WHERE {ORDER_COL} IN (
                    SELECT {ORDER_COL}
                    FROM {TARGET_TABLE}
                    ORDER BY {ORDER_COL}
                    LIMIT %s
                )
                """,
                (PREDICATE_VAL, target_count)
            )
            if verbose:
                print(f"         Set {target_count:,} rows to '{PREDICATE_VAL}'")

            # Step 3: VACUUM ANALYZE (must run with autocommit=True)
            cur.execute(f"VACUUM (ANALYZE) {TARGET_TABLE}")
            if verbose:
                print(f"         VACUUM (ANALYZE) complete")

            # Step 4: Verify actual count
            cur.execute(
                f"SELECT COUNT(*) FROM {TARGET_TABLE} WHERE {PREDICATE_COL} = %s",
                (PREDICATE_VAL,)
            )
            actual_count = cur.fetchone()[0]

        if verbose:
            print(f"[OK]    Verified: {actual_count:,} rows match '{PREDICATE_VAL}' ({actual_count/TOTAL_ROWS*100:.1f}%)")

        return actual_count

    finally:
        conn.close()


def verify_state(verbose: bool = True) -> dict:
    """Return current row distribution as a dict."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {PREDICATE_COL}, COUNT(*) as cnt
                FROM {TARGET_TABLE}
                GROUP BY {PREDICATE_COL}
                ORDER BY {PREDICATE_COL}
                """
            )
            rows = cur.fetchall()
        result = {row[0]: row[1] for row in rows}
        if verbose:
            for status, cnt in result.items():
                print(f"  {status}: {cnt:,} ({cnt/TOTAL_ROWS*100:.1f}%)")
        return result
    finally:
        conn.close()


if __name__ == "__main__":
    print("Current table state:")
    verify_state()
