from pathlib import Path
import pandas as pd

from sqlalchemy import create_engine

RAW_PATH = Path("data/online_retail.csv")
DB_PATH = "sqlite:///warehouse.db"

#extract
def extract(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="ISO-8859-1")
    print(f"Extrahiert: {len(df):,} Zeilen")
    return df

#transform

def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["InvoiceNo", "StockCode", "InvoiceDate"]).copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["CustomerID"] = df["CustomerID"].astype("Int64").astype("string")
    df["is_cancellation"] = df["InvoiceNo"].astype(str).str.startswith("C")
    df = df[(df["UnitPrice"] > 0) | (df["is_cancellation"])]
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()

    df = df[(df["UnitPrice"] > 0) | (df["is_cancellation"])]

    unique_dates = pd.to_datetime(df["InvoiceDate"].dt.date.drop_duplicates().sort_values())
    dim_date = pd.DataFrame({"full_date": unique_dates})
    dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["weekday_name"] = dim_date["full_date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["full_date"].dt.weekday >= 5

    dim_date = dim_date[[
        "date_key", "full_date", "year", "quarter", "month",
        "month_name", "day", "weekday_name", "is_weekend",
    ]]

    dim_product = (
        df[["StockCode", "Description"]]
        .drop_duplicates(subset="StockCode")
        .rename(columns={"StockCode": "stock_code", "Description": "description"})
    )

    dim_customer = (
        df.dropna(subset=["CustomerID"])[["CustomerID", "Country"]]
        .drop_duplicates(subset="CustomerID")
        .rename(columns={"CustomerID": "customer_id", "Country": "country"})
    )

    fact_sales = df.copy()
    fact_sales["date_key"] = fact_sales["InvoiceDate"].dt.strftime("%Y%m%d").astype(int)
    fact_sales["revenue"] = fact_sales["Quantity"] * fact_sales["UnitPrice"]
    fact_sales = fact_sales.rename(columns={
        "InvoiceNo": "invoice_no", "StockCode": "stock_code",
        "CustomerID": "customer_id", "Quantity": "quantity", "UnitPrice": "unit_price",
    })[["invoice_no", "stock_code", "customer_id", "date_key",
        "quantity", "unit_price", "revenue", "is_cancellation"]]

    return {"dim_date": dim_date, "dim_product": dim_product,
            "dim_customer": dim_customer, "fact_sales": fact_sales}


#load

def load(tables: dict[str, pd.DataFrame], db_path: str) -> None:
    engine = create_engine(db_path)
    for name, table in tables.items():
        table.to_sql(name, engine, if_exists="replace", index=False)
        print(f"Geladen: {name} ({len(table):,} Zeilen)")

if __name__ == "__main__":
    raw_df = extract(RAW_PATH)
    star_schema_tables = transform(raw_df)
    load(star_schema_tables, DB_PATH)


