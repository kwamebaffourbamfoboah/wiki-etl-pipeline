import argparse

from extract import extract
from transform import transform
from validate import validate, validate_db
from load import get_connection, create_tables, load
from raw_store import save_raw, load_raw

URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_Africa_by_revenue"


def main(raw_file=None):
    if raw_file:
        raw = load_raw(raw_file)            # no internet needed
    else:
        raw = extract(URL)
        save_raw(raw, "africa_companies")
    clean = transform(raw)

    errors, warnings = validate(clean)
    for w in warnings:
        print("WARNING:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        raise SystemExit("Validation failed - nothing was loaded.")

    conn = get_connection()
    try:
        create_tables(conn)
        load(conn, clean)

        problems = validate_db(conn, expected_rows=len(clean))
        if problems:
            for p in problems:
                print("DB ERROR:", p)
            raise SystemExit("Database checks failed.")
        print("Database checks passed")

        for table in ["industries", "countries", "companies", "revenue"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(table, n)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wikipedia company revenue pipeline")
    parser.add_argument(
        "--raw-file",
        help="Run from a saved raw CSV instead of scraping Wikipedia",
    )
    args = parser.parse_args()
    main(args.raw_file)