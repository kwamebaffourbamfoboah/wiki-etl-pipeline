import logging
from unittest.mock import MagicMock, patch

import pytest

from extract import extract

FAKE_HTML = """
<table class="wikitable">
  <tr><th>Rank</th><th>Company</th><th>Revenue (US$ billions)</th></tr>
  <tr><td>1</td><td>Alpha</td><td>10.5</td></tr>
  <tr><td>2</td><td>Beta</td></tr>
  <tr><td>3</td><td>Gamma</td><td>7.2</td></tr>
  <tr></tr>
</table>
"""


def run_extract(html, **kwargs):
    """Run extract() against fake HTML instead of the internet."""
    fake_response = MagicMock()
    fake_response.text = html
    fake_response.raise_for_status = lambda: None
    with patch("extract.requests.get", return_value=fake_response):
        return extract("http://fake.url", **kwargs)


def test_malformed_row_is_dropped_and_warned_about(caplog):
    with caplog.at_level(logging.WARNING):
        df = run_extract(FAKE_HTML)
    assert list(df["Company"]) == ["Alpha", "Gamma"]
    assert "Beta" in caplog.text


def test_empty_row_is_ignored_without_a_warning(caplog):
    with caplog.at_level(logging.WARNING):
        run_extract(FAKE_HTML)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1      # only the Beta row, not the empty one


def test_missing_table_raises_a_clear_error():
    with pytest.raises(ValueError, match="No table found"):
        run_extract("<html><body><p>No tables here</p></body></html>")


def test_table_is_chosen_by_its_columns():
    html = """
    <table class="wikitable">
      <tr><th>Name</th><th>Profit</th></tr>
      <tr><td>Delta</td><td>1</td></tr>
    </table>
    """ + FAKE_HTML
    df = run_extract(html, must_have=("Revenue",))
    assert "Revenue (US$ billions)" in df.columns