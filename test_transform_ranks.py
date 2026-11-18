import pandas as pd

from transform import transform

COLUMNS = ["Rank", "Company", "Industry", "Revenue(US$ billions)", "Headquarters"]


def make_raw(ranks):
    """Build a small raw table with the given rank values."""
    rows = [
        [rank, f"Company {i}", "Retail", "5.0", "Ghana"]
        for i, rank in enumerate(ranks, start=1)
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


# 1. normal ranks should work
clean = transform(make_raw(["1", "2", "3"]))
print("normal ranks:", clean["rank"].tolist())

# 2. a tied rank should stop with a clear message
try:
    transform(make_raw(["1", "2", "=3"]))
    print("tied rank: MISSED (no error was raised)")
except ValueError as e:
    print("tied rank: CAUGHT")
    print("   ", e)