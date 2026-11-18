import sqlite3
from pathlib import Path

import pytest

from load import create_tables, load
from raw_store import load_raw
from transform import transform
from validate import validate_db

SAMPLE = Path(__file__).parent / "data" / "africa_companies_sample.csv"


@pytest.fixture
def clean():
    return transform(load_raw(SAMPLE))


@pytest.fixture
def db(clean):
    """A fresh in-memory database with the sample data loaded."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    load(conn, clean)
    yield conn
    conn.close()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_load_creates_expected_row_counts(db):
    assert count(db, "industries") == 20
    assert count(db, "countries") == 14
    assert count(db, "companies") == 100
    assert count(db, "revenue") == 100


def test_loading_twice_creates_no_duplicates(db, clean):
    load(db, clean)
    assert count(db, "industries") == 20
    assert count(db, "countries") == 14
    assert count(db, "companies") == 100
    assert count(db, "revenue") == 100


def test_healthy_database_passes_all_checks(db, clean):
    assert validate_db(db, expected_rows=len(clean)) == []


def test_missing_revenue_row_is_caught(db, clean):
    db.execute("DELETE FROM revenue WHERE company_id = 1")
    problems = validate_db(db, expected_rows=len(clean))
    assert any("no revenue row" in p for p in problems)


def test_stale_row_is_caught(db, clean):
    db.execute(
        "UPDATE revenue SET loaded_at = '2000-01-01T00:00:00+00:00' WHERE company_id = 2"
    )
    problems = validate_db(db, expected_rows=len(clean))
    assert any("Stale rows" in p for p in problems)


def test_broken_foreign_key_is_caught(db, clean):
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("UPDATE companies SET industry_id = 9999 WHERE company_id = 3")
    problems = validate_db(db, expected_rows=len(clean))
    assert any("Foreign key" in p for p in problems)


def test_company_removed_from_source_is_deleted(db, clean):
    smaller = clean[clean["company"] != "Sonatrach"].copy()
    load(db, smaller)
    assert db.execute(
        "SELECT COUNT(*) FROM companies WHERE name = 'Sonatrach'"
    ).fetchone()[0] == 0
    assert count(db, "companies") == len(smaller)
    assert count(db, "revenue") == len(smaller)


def test_country_with_no_companies_is_removed(db, clean):
    smaller = clean[clean["country"] != "Algeria"].copy()
    load(db, smaller)
    assert db.execute(
        "SELECT COUNT(*) FROM countries WHERE name = 'Algeria'"
    ).fetchone()[0] == 0
    assert count(db, "countries") == 13