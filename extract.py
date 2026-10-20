import requests
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def extract(url, must_have=("Revenue",)):
    """Fetch the page and return the matching table as raw text (no cleaning)."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for table in soup.find_all("table", class_="wikitable"):
        cols = [th.get_text(strip=True) for th in table.find("tr").find_all("th")]
        if all(any(word.lower() in c.lower() for c in cols) for word in must_have):
            rows = []
            for tr in table.find_all("tr")[1:]:
                cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                if len(cells) == len(cols):
                    rows.append(cells)
            return pd.DataFrame(rows, columns=cols)

    raise ValueError(f"No table found with columns containing {must_have}")