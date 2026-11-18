import logging
import sqlite3
from pathlib import Path

from history import snapshot
from load import create_tables, load
from raw_store import load_raw
from transform import transform

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SAMPLE = Path("tests") / "data" / "africa_companies_sample.csv"
DEMO_DB = Path("demo.db")

DEMO_DB.unlink(missing_ok=True)          # start from an empty demo database
conn = sqlite3.connect(DEMO_DB)
conn.execute("PRAGMA foreign_keys = ON")
create_tables(conn)

# run 1: the data as it was in the saved snapshot
clean = transform(load_raw(SAMPLE))
load(conn, clean)
snapshot(conn, clean, "demo: original data")

# run 2: pretend Wikipedia changed - two revenues updated, one company dropped
changed = clean[clean["company"] != "Dangote Cement Nigeria"].copy()
changed.loc[changed["company"] == "Sonatrach", "revenue_bn"] = 80.0
changed.loc[changed["company"] == "Eskom", "revenue_bn"] = 15.2
load(conn, changed)
snapshot(conn, changed, "demo: changed data")

print("\nRuns recorded:")
for row in conn.execute("SELECT run_id, row_count FROM runs ORDER BY run_id"):
    print("  run", row[0], "-", row[1], "companies")

print("\nCompanies whose revenue changed between run 1 and run 2:")
changed_rows = conn.execute("""
    SELECT a.company, a.revenue_bn, b.revenue_bn, ROUND(b.revenue_bn - a.revenue_bn, 3)
    FROM revenue_history a
    JOIN revenue_history b ON b.company = a.company
    WHERE a.run_id = 1 AND b.run_id = 2 AND a.revenue_bn != b.revenue_bn
    ORDER BY a.company
""").fetchall()
for company, old, new, diff in changed_rows:
    print(f"  {company}: {old} -> {new} ({diff:+})")

print("\nCompanies in run 1 that are missing from run 2:")
missing = conn.execute("""
    SELECT a.company
    FROM revenue_history a
    LEFT JOIN revenue_history b ON b.company = a.company AND b.run_id = 2
    WHERE a.run_id = 1 AND b.company IS NULL
""").fetchall()
for (company,) in missing:
    print(" ", company)

print("\nStill in the live companies table?",
      conn.execute("SELECT COUNT(*) FROM companies WHERE name = 'Dangote Cement Nigeria'")
      .fetchone()[0] == 1)
conn.close()