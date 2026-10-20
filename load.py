import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = "companies.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")   # SQLite ignores foreign keys unless you ask
    return conn


def create_tables(conn):
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()

def load(conn, df):
    """Write the clean table into SQLite. Safe to run repeatedly."""
    loaded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with conn:  # one transaction: all or nothing
        for name in df["industry"].unique():
            conn.execute("INSERT OR IGNORE INTO industries (name) VALUES (?)", (name,))
        for name in df["country"].unique():
            conn.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (name,))

        industry_ids = dict(conn.execute("SELECT name, industry_id FROM industries"))
        country_ids = dict(conn.execute("SELECT name, country_id FROM countries"))

        for row in df.itertuples(index=False):
            conn.execute(
                """
                INSERT INTO companies (name, industry_id, country_id, is_subsidiary)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    industry_id   = excluded.industry_id,
                    country_id    = excluded.country_id,
                    is_subsidiary = excluded.is_subsidiary
                """,
                (row.company, industry_ids[row.industry],
                 country_ids[row.country], int(row.is_subsidiary)),
            )
            company_id = conn.execute(
                "SELECT company_id FROM companies WHERE name = ?", (row.company,)
            ).fetchone()[0]

            conn.execute(
                """
                INSERT INTO revenue (company_id, rank, revenue_bn, loaded_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(company_id) DO UPDATE SET
                    rank       = excluded.rank,
                    revenue_bn = excluded.revenue_bn,
                    loaded_at  = excluded.loaded_at
                """,
                (company_id, int(row.rank), float(row.revenue_bn), loaded_at),
            )

        # delete anything that is no longer in the source table
        names = df["company"].tolist()
        marks = ",".join("?" * len(names))

        conn.execute(
            f"""DELETE FROM revenue WHERE company_id IN
                (SELECT company_id FROM companies WHERE name NOT IN ({marks}))""",
            names,
        )
        conn.execute(f"DELETE FROM companies WHERE name NOT IN ({marks})", names)

        # tidy up industries and countries that no company uses any more
        conn.execute("DELETE FROM industries WHERE industry_id NOT IN (SELECT industry_id FROM companies)")
        conn.execute("DELETE FROM countries WHERE country_id NOT IN (SELECT country_id FROM companies)")