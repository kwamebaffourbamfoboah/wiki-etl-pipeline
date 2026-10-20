from extract import extract
from transform import transform
from validate import validate

URL = "https://en.wikipedia.org/wiki/List_of_largest_companies_in_Africa_by_revenue"
good = transform(extract(URL))


def run(label, df):
    errors, _ = validate(df)
    print(f"{label}: {'CAUGHT' if errors else 'MISSED'}")
    for e in errors:
        print("   ", e)


# 1. rows missing
run("30 rows deleted", good.iloc[:70].copy())

# 2. missing value
bad = good.copy()
bad.loc[5, "revenue_bn"] = None
run("missing revenue", bad)

# 3. duplicate company
bad =  good.copy()
bad.loc[10, "company"] = bad.loc[11, "company"]
run("duplicate company", bad)

# 4. negative revenue
bad = good.copy()
bad.loc[3, "revenue_bn"] = -5
run("negative revenue", bad)

# 5. empty text
bad = good.copy()
bad.loc[7, "industry"] = ""
run("empty industry", bad)

# 6. wrong units (millions instead of billions)
bad = good.copy()
bad.loc[2, "revenue_bn"] = 12989
run("revenue in millions", bad)