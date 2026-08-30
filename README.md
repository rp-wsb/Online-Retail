# Online Retail — ETL Pipeline & Power BI Dashboard

An end-to-end data pipeline that transforms raw e-commerce transaction data into a
dimensional data warehouse and an interactive Power BI dashboard — built as a hands-on
exploration of the full BI workflow: **Extract → Transform → Load → Model → Visualize**.

## Overview

This project takes a year of transaction data from a UK-based online retailer and turns
it into a queryable star schema and a multi-page sales dashboard. The focus isn't just
on producing charts, but on the data engineering steps that make those charts trustworthy:
cleaning inconsistent source data, enforcing referential integrity, and documenting the
trade-offs made along the way.

## Architecture

```
CSV (raw transactions)
        │
        ▼
  ┌─────────────┐
  │   extract   │  pandas.read_csv
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │  transform  │  cleaning, normalization, star-schema reshaping
  └─────────────┘
        │
        ▼
  ┌─────────────┐
  │    load     │  SQLAlchemy → SQLite
  └─────────────┘
        │
        ▼
  sql/warehouse.db (star schema)
        │
        ▼
  Power BI (DAX measures, relationships, multi-page dashboard)
```

## Tech Stack

| Layer | Tools |
|---|---|
| Extraction & Transformation | Python, pandas |
| Loading | SQLAlchemy, SQLite |
| Data Modeling | SQL (star schema: 1 fact table, 3 dimensions) |
| Visualization | Power BI (Power Query, DAX) |

## Data Source

[Online Retail Dataset](https://www.kaggle.com/datasets/ulrikthygepedersen/online-retail-dataset)
(Kaggle, originally from the UCI Machine Learning Repository) — ~540,000 transactions from
a UK-based non-store online retailer, December 2010 to December 2011.

## Data Model (Star Schema)

```
                 ┌──────────────────┐
                 │   dim_date       │
                 └─────────┬────────┘
                           │
┌─────────────────┐        │        ┌─────────────────┐
│  dim_product    ├────────┼────────┤  dim_customer   │
└────────┬────────┘        │        └────────┬────────┘
         │                 │                 │
         └──────────►┌─────┴───────┐◄────────┘
                     │ fact_sales  │
                     └─────────────┘
```

- **fact_sales** — one row per order line: quantity, unit price, revenue, cancellation flag
- **dim_date** — calendar attributes (year, quarter, month, weekday) for time-based analysis
- **dim_product** — deduplicated product catalog
- **dim_customer** — customer-to-country mapping, including a resolved `UNKNOWN` entry
  for guest checkouts

Full definition: [`sql/schema.sql`](sql/schema.sql)

## Data Quality — What Was Actually Fixed

Raw transactional data is never clean. These are the concrete issues found and resolved
in the ETL step, rather than being pushed downstream into the dashboard:

- **Inconsistent product keys**: ~110 product codes existed as case/whitespace variants
  of each other (e.g. `85099b` vs `85099B`), which silently broke the product dimension's
  uniqueness and caused a many-to-many relationship in the data model. Fixed by normalizing
  `StockCode` (trim + uppercase) before deduplication.
- **Orphaned fact rows (guest orders)**: a large share of transactions have no `CustomerID`.
  Rather than leaving a `NULL` foreign key (which breaks relationship constraints and
  shows up as a misleading blank category in every visual), these rows are mapped to an
  explicit `UNKNOWN` member in `dim_customer` — a standard dimensional-modeling pattern for
  preserving referential integrity.
- **Invalid price rows**: line items with `UnitPrice <= 0` (adjustments, samples) are
  excluded, while genuine cancellations (negative quantity, `InvoiceNo` starting with `C`)
  are kept and explicitly flagged rather than deleted, so gross and net figures can both
  be reported.

## Dashboard

Two pages so far, more planned (see below):

**Sales Overview** — KPI cards (Total Orders, Total Revenue, Net Revenue, Average Order
Value), a date-range and country slicer, and a combo chart tracking orders vs. revenue
by month.

**Top Products** — ranked bar chart and detail table of best-selling products by revenue,
plus a country breakdown showing revenue concentration.


**Planned**: a Customers & Countries page (geographic breakdown, top customers) and a
Data Quality & Returns page (cancellation rate over time) — see [Extending](#possible-extensions).

## Key Insights

- The United Kingdom accounts for roughly **84% of total revenue** — the business is
  overwhelmingly domestic despite operating internationally.
- Revenue climbs steadily from September and peaks in **November**, consistent with
  pre-Christmas retail seasonality, then drops in December as the order window closes.
- The top revenue driver isn't a single "hero product" — postage/shipping charges and a
  handful of home-decor items (cake stands, tea lights, bunting) make up the top of the list,
  suggesting a long-tail catalog rather than a few dominant SKUs.

## Project Structure

```
├── data/               raw CSV (not committed — see .gitignore)
├── sql/
│   └── schema.sql      star schema DDL
├── etl/
│   ├── etl.py           extract → transform → load pipeline
│   └── requirements.txt
├── dashboard/           Power BI screenshots
├── warehouse.db         generated SQLite database (created by etl.py)
└── README.md

```

## Setup & Run

```bash
pip install -r etl/requirements.txt
# place the raw CSV at data/online_retail.csv (see Data Source above)
python etl/etl.py
```

This produces `warehouse.db`, ready to be connected to Power BI (or any SQL client)
for analysis.

## Possible Extensions

- Customer segmentation (RFM analysis: recency, frequency, monetary value)
- Automated scheduled refresh via a proper Postgres warehouse instead of SQLite
- A returns/cancellation-rate page, using the `is_cancellation` flag already modeled
- Unit tests for the transform step (e.g. asserting no duplicate `stock_code` after
  normalization)

## Data License

The dataset is provided under Kaggle's terms via the original UCI Machine Learning
Repository listing. Raw data is not included in this repository — see Setup & Run above.
