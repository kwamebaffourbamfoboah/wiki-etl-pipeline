import sqlite3

conn = sqlite3.connect("companies.db")
total = conn.execute("""
    SELECT ROUND(SUM(r.revenue_bn), 1)
    FROM revenue r
    JOIN companies c ON c.company_id = r.company_id
    WHERE c.is_subsidiary = 1
""").fetchone()[0]
print("Subsidiary revenue (US$ bn):", total)
conn.close()