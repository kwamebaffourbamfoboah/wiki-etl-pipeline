CREATE TABLE IF NOT EXISTS industries (
    industry_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS countries (
    country_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS companies (
    company_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    industry_id   INTEGER NOT NULL REFERENCES industries(industry_id),
    country_id    INTEGER NOT NULL REFERENCES countries(country_id),
    is_subsidiary INTEGER NOT NULL CHECK (is_subsidiary IN (0, 1))
);

CREATE TABLE IF NOT EXISTS revenue (
    company_id INTEGER PRIMARY KEY REFERENCES companies(company_id),
    rank       INTEGER NOT NULL,
    revenue_bn REAL NOT NULL CHECK (revenue_bn > 0),
    loaded_at  TEXT NOT NULL
);