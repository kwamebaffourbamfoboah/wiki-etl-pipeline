from pathlib import Path

import pandas as pd
import pytest

from raw_store import load_raw
from transform import transform

SAMPLE = Path(__file__).parent / "data" / "africa_companies_sample.csv"


@pytest.fixture
def raw():
    """A fresh copy of the saved raw table for each test."""
    return load_raw(SAMPLE)


def test_transform_keeps_all_rows(raw):
    clean = transform(raw)
    assert len(clean) == 100


def test_transform_column_names_and_types(raw):
    clean = transform(raw)
    assert list(clean.columns) == [
        "rank", "company", "industry", "revenue_bn", "country", "is_subsidiary",
    ]
    assert pd.api.types.is_integer_dtype(clean["rank"])
    assert pd.api.types.is_float_dtype(clean["revenue_bn"])


def test_transform_merges_duplicate_industry_labels(raw):
    clean = transform(raw)
    assert "Chemistry" not in set(clean["industry"])
    assert "Chemicals" in set(clean["industry"])


def test_transform_flags_eight_subsidiaries(raw):
    clean = transform(raw)
    assert clean["is_subsidiary"].sum() == 8


def test_tied_rank_gives_clear_error(raw):
    raw.loc[2, "Rank"] = "=3"
    with pytest.raises(ValueError, match="not a plain whole number"):
        transform(raw)