import pandas as pd

# raw column name on the Wikipedia page -> the name we use from here on
COLUMN_MAP = {
    "Rank": "rank",
    "Company": "company",
    "Industry": "industry",
    "Revenue(US$ billions)": "revenue_bn",
    "Headquarters": "country",
}

# merge duplicate industry labels (same idea as before)
INDUSTRY_MAP = {
    "Chemistry": "Chemicals",
    "Holding": "Conglomerate",
    "Airline": "Transport",
}

# entries whose revenue is already included in a larger listed company
SUBSIDIARIES = [
    "MTN Nigeria", "MTN South Africa", "Vodacom South Africa",
    "Massmart Wholesale", "Massmart Retail", "Transnet Freight Rail",
    "Dangote Cement Nigeria", "Gold Fields Ghana",
]


def transform(raw):
    """Take the raw scraped table, return a clean one."""
    missing = set(COLUMN_MAP) - set(raw.columns)
    if missing:
        raise ValueError(f"Columns missing from the scraped table: {missing}")

    df = raw.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())].copy()

    df["rank"] = df["rank"].astype(int)
    df["revenue_bn"] = pd.to_numeric(df["revenue_bn"], errors="coerce")
    for col in ["company", "industry", "country"]:
        df[col] = df[col].str.strip()

    df["industry"] = df["industry"].replace(INDUSTRY_MAP)
    df["is_subsidiary"] = df["company"].isin(SUBSIDIARIES).astype(int)
    return df