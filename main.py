import argparse
import logging

from config import load_config
from extract import extract
from transform import transform
from validate import validate, validate_db
from load import get_connection, create_tables, load
from raw_store import save_raw, load_raw

logger = logging.getLogger(__name__)


def main(raw_file=None):
    config = load_config()
    if raw_file:
        logger.info("Running from saved raw file: %s", raw_file)
        raw = load_raw(raw_file)            # no internet needed
    else:
        raw = extract(config["url"])
        save_raw(raw, config["dataset_name"])
    clean = transform(raw)

    errors, warnings = validate(clean)
    for w in warnings:
        logger.warning(w)
    if errors:
        for e in errors:
            logger.error(e)
        raise SystemExit("Validation failed - nothing was loaded.")

    conn = get_connection()
    try:
        create_tables(conn)
        load(conn, clean)

        problems = validate_db(conn, expected_rows=len(clean))
        if problems:
            for p in problems:
                logger.error("Database check failed: %s", p)
            raise SystemExit("Database checks failed.")
        logger.info("Database checks passed")

        for table in ["industries", "countries", "companies", "revenue"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            logger.info("%s: %d rows", table, n)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Wikipedia company revenue pipeline")
    parser.add_argument(
        "--raw-file",
        help="Run from a saved raw CSV instead of scraping Wikipedia",
    )
    args = parser.parse_args()
    main(args.raw_file)