from pathlib import Path

import pytest

from raw_store import load_raw
from transform import transform
from validate import validate

SAMPLE = Path(__file__).parent / "data" / "africa_companies_sample.csv"


@pytest.fixture
def clean():
    """A fresh clean table for each test."""
    return transform(load_raw(SAMPLE))


def test_clean_data_has_no_errors(clean):
    errors, _ = validate(clean)
    assert errors == []


def test_out_of_order_revenue_is_a_warning_not_an_error(clean):
    errors, warnings = validate(clean)
    assert errors == []
    assert any("Ethiopian Airlines" in w for w in warnings)
    assert any("Tiger Brands" in w for w in warnings)


def test_too_few_rows_is_caught(clean):
    errors, _ = validate(clean.iloc[:70].copy())
    assert any("Expected about 100 rows" in e for e in errors)


def test_missing_revenue_is_caught(clean):
    clean.loc[5, "revenue_bn"] = None
    errors, _ = validate(clean)
    assert any("Missing values" in e for e in errors)


def test_duplicate_company_is_caught(clean):
    clean.loc[10, "company"] = clean.loc[11, "company"]
    errors, _ = validate(clean)
    assert any("Duplicate companies" in e for e in errors)


def test_negative_revenue_is_caught(clean):
    clean.loc[3, "revenue_bn"] = -5
    errors, _ = validate(clean)
    assert any("greater than 0" in e for e in errors)


def test_empty_industry_is_caught(clean):
    clean.loc[7, "industry"] = ""
    errors, _ = validate(clean)
    assert any("Empty text in column 'industry'" in e for e in errors)


def test_revenue_in_millions_is_caught(clean):
    clean.loc[2, "revenue_bn"] = 12989
    errors, _ = validate(clean)
    assert any("millions instead of billions" in e for e in errors)