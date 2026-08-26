# ============================================================
# Harbinger — Database Connection Configuration EXAMPLE
# ============================================================
# Copy this file to config/db_config.py and fill in your values.
# config/db_config.py is gitignored and will NEVER be pushed.

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "harbinger_dev",
    "user":     "postgres",
    "password": "YOUR_POSTGRES_PASSWORD_HERE",
    "options":  "-c search_path=harbinger_lab"
}

# ── Experiment settings ──────────────────────────────────────

TARGET_TABLE       = "harbinger_lab.orders"
PREDICATE_COL      = "status"
PREDICATE_VAL      = "pending"
ORDER_COL          = "order_id"
TOTAL_ROWS         = 100_000
SELECTIVITY_LEVELS = [5, 10, 15, 20, 25, 50]
RUNS_PER_STATE     = 5
REGRESSION_THRESHOLD = 2.0

BENCHMARK_QUERY = """
SELECT
    o.order_id,
    c.customer_name,
    c.customer_tier,
    o.order_amount
FROM harbinger_lab.orders o
JOIN harbinger_lab.customers c ON o.customer_id = c.customer_id
WHERE o.status = %(val)s
"""

EXPLAIN_QUERY = """
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)
SELECT
    o.order_id,
    c.customer_name,
    c.customer_tier,
    o.order_amount
FROM harbinger_lab.orders o
JOIN harbinger_lab.customers c ON o.customer_id = c.customer_id
WHERE o.status = %(val)s
"""
