import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

COLUMNS = ["company", "industry", "country", "is_subsidiary", "rank", "revenue_bn"]


def data_hash(df):
    """A fingerprint of the clean data. Same data always gives the same hash."""
    ordered = df[COLUMNS].sort_values("company").reset_index(drop=True)
    text = ordered.to_csv(index=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot(conn, df, source_url):
    """Record this run in the history tables, unless nothing changed since the last run.

    Returns the new run_id, or None if the data was unchanged.
    """
    new_hash = data_hash(df)

    with conn:  # one transaction: the run and all its rows are saved together or not at all
        latest = conn.execute(
            "SELECT data_hash FROM runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()
        if latest and latest[0] == new_hash:
            logger.info("Data unchanged since the last run - no new history snapshot")
            return None

        run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cursor = conn.execute(
            "INSERT INTO runs (run_at, source_url, data_hash, row_count) VALUES (?, ?, ?, ?)",
            (run_at, source_url, new_hash, len(df)),
        )
        run_id = cursor.lastrowid

        rows = [
            (run_id, r.company, r.industry, r.country,
             int(r.is_subsidiary), int(r.rank), float(r.revenue_bn))
            for r in df.itertuples(index=False)
        ]
        conn.executemany(
            """
            INSERT INTO revenue_history
                (run_id, company, industry, country, is_subsidiary, rank, revenue_bn)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    logger.info("Saved history snapshot: run %d, %d rows", run_id, len(df))
    return run_id