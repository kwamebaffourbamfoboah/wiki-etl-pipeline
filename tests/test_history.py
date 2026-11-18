import sqlite3
from pathlib import Path

import pytest

from history import data_hash, snapshot
from load import create_tables, load
from raw_store import load_raw
from transform import transform

SAMPLE = Path(__file__).parent / "data" / "africa_companies_sample.csv"


@pytest.fixture
def clean():
    return transform(load_raw(SAMPLE))


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    yield conn
    conn.close()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def sonatrach_revenue(conn, run_id):
    return conn.execute(
        "SELECT revenue_bn FROM revenue_history WHERE run_id = ? AND company = 'Sonatrach'",
        (run_id,),
    ).fetchone()[0]


def test_first_run_creates_a_snapshot(db, clean):
    assert snapshot(db, clean, "test") == 1
    assert count(db, "runs") == 1
    assert count(db, "revenue_history") == 100


def test_same_data_twice_creates_one_snapshot(db, clean):
    snapshot(db, clean, "test")
    assert snapshot(db, clean, "test") is None
    assert count(db, "runs") == 1
    assert count(db, "revenue_history") == 100


def test_row_order_does_not_change_the_hash(clean):
    shuffled = clean.sample(frac=1, random_state=1)
    assert data_hash(shuffled) == data_hash(clean)


def test_changed_data_creates_a_second_snapshot_and_keeps_the_old_values(db, clean):
    snapshot(db, clean, "test")
    changed = clean.copy()
    idx = changed.index[changed["company"] == "Sonatrach"][0]
    changed.loc[idx, "revenue_bn"] = 80.0

    assert snapshot(db, changed, "test") == 2
    assert count(db, "runs") == 2
    assert count(db, "revenue_history") == 200
    assert sonatrach_revenue(db, 1) == 77.013
    assert sonatrach_revenue(db, 2) == 80.0


def test_going_back_to_earlier_data_is_still_recorded(db, clean):
    changed = clean.copy()
    idx = changed.index[changed["company"] == "Sonatrach"][0]
    changed.loc[idx, "revenue_bn"] = 80.0

    snapshot(db, clean, "test")
    snapshot(db, changed, "test")
    assert snapshot(db, clean, "test") == 3
    assert count(db, "runs") == 3


def test_history_keeps_companies_removed_from_source(db, clean):
    load(db, clean)
    snapshot(db, clean, "test")

    smaller = clean[clean["company"] != "Sonatrach"].copy()
    load(db, smaller)
    snapshot(db, smaller, "test")

    in_companies = db.execute(
        "SELECT COUNT(*) FROM companies WHERE name = 'Sonatrach'"
    ).fetchone()[0]
    in_history = db.execute(
        "SELECT COUNT(*) FROM revenue_history WHERE company = 'Sonatrach'"
    ).fetchone()[0]
    assert in_companies == 0     # deleted from the live tables
    assert in_history == 1       # but still in run 1 of the history