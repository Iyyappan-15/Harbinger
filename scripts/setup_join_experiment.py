# ============================================================
# Harbinger — setup_join_experiment.py
# Migrates database schema for Phase 4: E-002 JOIN Query.
# Creates harbinger_lab.customers and seeds 10,000 records.
# ============================================================

import sys
import os
import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.db_connector import get_connection

def setup_migration():
    print("[MIGRATION] Setting up Phase 4 -- E-002 JOIN Query Experiment...")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Create table schema
            print("            Recreating harbinger_lab.customers table...")
            cur.execute("""
                DROP TABLE IF EXISTS harbinger_lab.customers CASCADE;
                CREATE TABLE harbinger_lab.customers (
                    customer_id INTEGER PRIMARY KEY,
                    customer_name VARCHAR(100) NOT NULL,
                    customer_tier VARCHAR(20) NOT NULL
                );
            """)

            # 2. Populate customer data (10,000 entries matching orders range)
            print("            Generating 10,000 distinct customer rows...")
            customers = []
            for i in range(1, 10001):
                tier = "Gold" if i % 3 == 0 else "Silver" if i % 3 == 1 else "Bronze"
                customers.append((i, f"Customer_#{i}", tier))
            
            # Efficient batch insert
            execute_values(
                cur,
                "INSERT INTO harbinger_lab.customers (customer_id, customer_name, customer_tier) VALUES %s",
                customers
            )
            print(f"            Successfully seeded {len(customers):,} rows into harbinger_lab.customers.")

            # 3. Create foreign-key helper index on orders table if not present
            print("            Creating helper index on orders(customer_id) for joins...")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON harbinger_lab.orders(customer_id);")

            # 4. Refresh stats
            print("            Refreshing database planner stats...")
            cur.execute("VACUUM (ANALYZE) harbinger_lab.customers;")
            cur.execute("VACUUM (ANALYZE) harbinger_lab.orders;")

        print("[OK]        Migration complete. E-002 database schema is ready.")
    except Exception as e:
        print(f"[ERROR]     Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    setup_migration()
