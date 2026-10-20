def validate(df, expected_rows=100, tolerance=5):
    """Return (errors, warnings). Errors should stop the load; warnings are just reported."""
    errors, warnings = [], []

    # --- errors: the data is not safe to load ---
    if abs(len(df) - expected_rows) > tolerance:
        errors.append(f"Expected about {expected_rows} rows, got {len(df)}")

    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        errors.append(f"Missing values: {nulls.to_dict()}")

    if df["company"].duplicated().any():
        errors.append(f"Duplicate companies: {df.loc[df['company'].duplicated(), 'company'].tolist()}")

    if df["rank"].duplicated().any():
        errors.append("Duplicate ranks")

    if (df["revenue_bn"] <= 0).any():
        errors.append("Revenue must be greater than 0")
    
    if (df["revenue_bn"] > 500).any():
        errors.append("Revenue above 500 bn - is the column in millions instead of billions?")

    for col in ["company", "industry", "country"]:
        if (df[col] == "").any():
            errors.append(f"Empty text in column '{col}'")

    # --- warnings: odd, but not necessarily wrong ---
    ordered = df.sort_values("rank")
    out_of_order = ordered[ordered["revenue_bn"] > ordered["revenue_bn"].shift(1)]
    for row in out_of_order.itertuples():
        warnings.append(
            f"{row.company} (rank {row.rank}) has more revenue than the company ranked above it"
        )

    return errors, warnings

def validate_db(conn, expected_rows):
    """Check the database after loading. Returns a list of problems."""
    problems = []

    # every company must have a revenue row
    missing = conn.execute("""
        SELECT c.name
        FROM companies c
        LEFT JOIN revenue r ON r.company_id = c.company_id
        WHERE r.company_id IS NULL
    """).fetchall()
    if missing:
        problems.append(f"Companies with no revenue row: {[m[0] for m in missing]}")

    # no broken links between tables
    broken = conn.execute("PRAGMA foreign_key_check").fetchall()
    if broken:
        problems.append(f"Foreign key violations: {len(broken)}")

    # row count should match what we just loaded
    n = conn.execute("SELECT COUNT(*) FROM revenue").fetchone()[0]
    if n != expected_rows:
        problems.append(f"revenue has {n} rows, expected {expected_rows}")

    # rows not touched by the latest load are leftovers from an earlier run
    stale = conn.execute("""
        SELECT c.name
        FROM revenue r
        JOIN companies c ON c.company_id = r.company_id
        WHERE r.loaded_at < (SELECT MAX(loaded_at) FROM revenue)
    """).fetchall()
    if stale:
        problems.append(f"Stale rows not in the latest load: {[s[0] for s in stale]}")

    return problems