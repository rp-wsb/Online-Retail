-- ============================================================
-- Star Schema "Online Retail Dataset" (Kaggle / UCI)
-- Quelle: https://www.kaggle.com/datasets/ulrikthygepedersen/online-retail-dataset
-- ============================================================

-- Dimension: Datum
CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,   -- Format YYYYMMDD, z.B. 20101201
    full_date     DATE    NOT NULL,
    year          INTEGER NOT NULL,
    quarter       INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    day           INTEGER NOT NULL,
    weekday_name  TEXT    NOT NULL,
    is_weekend    BOOLEAN NOT NULL
);

-- Dimension: Produkt
CREATE TABLE dim_product (
    stock_code   TEXT PRIMARY KEY,
    description  TEXT
);

-- Dimension: Kunde
-- CustomerID fehlt bei Gastbestellungen -> im Fact als NULL zulaessig
CREATE TABLE dim_customer (
    customer_id  TEXT PRIMARY KEY,
    country      TEXT NOT NULL
);

-- Faktentabelle: Verkaeufe
CREATE TABLE fact_sales (
    sale_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no       TEXT    NOT NULL,
    stock_code       TEXT    NOT NULL REFERENCES dim_product(stock_code),
    customer_id      TEXT    REFERENCES dim_customer(customer_id),  -- nullable: Gastbestellung
    date_key         INTEGER NOT NULL REFERENCES dim_date(date_key),
    quantity         INTEGER NOT NULL,
    unit_price       REAL    NOT NULL,
    revenue          REAL    NOT NULL,   -- quantity * unit_price
    is_cancellation  BOOLEAN NOT NULL    -- true, wenn invoice_no mit 'C' beginnt
);

CREATE INDEX idx_fact_sales_date     ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_product  ON fact_sales(stock_code);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_id);