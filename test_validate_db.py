import sqlite3
from extract import extract
from transform import transform
from load import create_tables, load
from validate import validate_db

URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_Africa_by_revenue"
clean = transform(extract(URL))


def fresh_db():
    """A new in-memory database with the clean data loaded."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    load(conn, clean)
    return conn


def run(label, conn):
    problems = validate_db(conn, expected_rows=len(clean))
    print(f"{label}: {'CAUGHT' if problems else 'MISSED'}")
    for p in problems:
        print("   ", p)


# 0. healthy database should have no problems
run("healthy database (should say MISSED = no problems)", fresh_db())

# 1. a company loses its revenue row
conn = fresh_db()
conn.execute("DELETE FROM revenue WHERE company_id = 1")
run("revenue row deleted", conn)

# 2. a leftover row from an older load
conn = fresh_db()
conn.execute("UPDATE revenue SET loaded_at = '2000-01-01T00:00:00+00:00' WHERE company_id = 2")
run("stale row", conn)

# 3. a broken link between tables
conn = fresh_db()
conn.execute("PRAGMA foreign_keys = OFF")
conn.execute("UPDATE companies SET industry_id = 9999 WHERE company_id = 3")
run("broken foreign key", conn)

# 4. a company disappears from the source -> it should be deleted
conn = fresh_db()
smaller = clean[clean["company"] != "Sonatrach"].copy()
load(conn, smaller)
n = conn.execute("SELECT COUNT(*) FROM companies WHERE name = 'Sonatrach'").fetchone()[0]
print("Sonatrach removed:", "YES" if n == 0 else "NO - still there")
for table in ["companies", "revenue", "industries", "countries"]:
    print(table, conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

# 5. a whole country disappears -> the country row should be tidied away
conn = fresh_db()
smaller = clean[clean["country"] != "Algeria"].copy()
load(conn, smaller)
algeria = conn.execute("SELECT COUNT(*) FROM countries WHERE name = 'Algeria'").fetchone()[0]
print("Algeria removed from countries:", "YES" if algeria == 0 else "NO - still there")
for table in ["companies", "revenue", "countries"]:
    print(table, conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])