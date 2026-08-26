# ============================================================
# Harbinger — db_connector.py
# Manages PostgreSQL connections
# ============================================================

import psycopg2
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.db_config import DB_CONFIG


def get_connection():
    """Return a live psycopg2 connection to the harbinger database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True   # Required for VACUUM to run outside transaction
        return conn
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Cannot connect to PostgreSQL: {e}")
        print("  Check that PostgreSQL is running and DB_CONFIG in config/db_config.py is correct.")
        sys.exit(1)


def test_connection():
    """Quick connection test — prints PostgreSQL version if successful."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"[OK] Connected: {version[:60]}")
    conn.close()


if __name__ == "__main__":
    test_connection()
