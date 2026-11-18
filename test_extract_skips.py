import logging
from unittest.mock import patch, MagicMock

from extract import extract

# switch logging on so we can see the messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

FAKE_HTML = """
<table class="wikitable">
  <tr><th>Rank</th><th>Company</th><th>Revenue (US$ billions)</th></tr>
  <tr><td>1</td><td>Alpha</td><td>10.5</td></tr>
  <tr><td>2</td><td>Beta</td></tr>
  <tr><td>3</td><td>Gamma</td><td>7.2</td></tr>
  <tr></tr>
</table>
"""

fake_response = MagicMock()
fake_response.text = FAKE_HTML
fake_response.raise_for_status = lambda: None

# replace the real internet request with our fake page
with patch("extract.requests.get", return_value=fake_response):
    df = extract("http://fake.url")

print(df)