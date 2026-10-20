from extract import extract
from transform import transform
from validate import validate, validate_db
from load import get_connection, create_tables, load

URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_Africa_by_revenue"


def main():
    clean = transform(extract(URL))

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
    main()