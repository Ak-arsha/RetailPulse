"""ETL: extract raw CSV -> clean/validate -> load star schema -> build SQL analytics views.
Set DATABASE_URL to point at Postgres/Supabase/Cloud SQL; defaults to local SQLite."""
import os, time
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")
RAW = "data/raw_orders.csv"


def extract(path=RAW):
    """Read raw data from an S3 landing zone if RAW_S3_URI is set (needs s3fs + AWS creds), else local CSV."""
    uri = os.getenv("RAW_S3_URI")          # e.g. s3://my-bucket/raw/raw_orders.csv
    return pd.read_csv(uri if uri else path)


def transform(df):
    r = {"raw_rows": len(df)}
    df = df.drop_duplicates()
    r["duplicates_removed"] = r["raw_rows"] - len(df)

    for c in ("category", "region", "city", "product_name"):
        df[c] = df[c].astype("string").str.strip().str.title()
    r["null_region_filled"] = int(df["region"].isna().sum())
    df["region"] = df["region"].fillna("Unknown")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["order_date", "customer_id", "product_id", "order_id"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
    r["invalid_rows_dropped"] = before - len(df)

    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    df["order_month"] = df["order_date"].dt.strftime("%Y-%m")          # portable across SQL engines
    df["order_day"] = (df["order_date"] - pd.Timestamp("2000-01-01")).dt.days
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    # validation gates: fail loudly instead of loading bad data
    assert df[["order_id", "customer_id", "product_id"]].notna().all().all(), "null keys"
    assert (df["revenue"] >= 0).all(), "negative revenue"
    r["clean_rows"] = len(df)
    return df, r


def load(df, engine):
    dim_customer = (df.groupby("customer_id")
                      .agg(region=("region", lambda s: s.mode().iat[0]),
                           city=("city", lambda s: s.mode().iat[0])).reset_index())
    dim_product = (df.groupby("product_id")
                     .agg(product_name=("product_name", "first"),
                          category=("category", "first")).reset_index())
    fact = df[["order_id", "order_date", "order_month", "order_day", "customer_id",
               "product_id", "quantity", "unit_price", "discount", "revenue"]]
    with engine.begin() as con:
        for name, t in (("dim_customer", dim_customer), ("dim_product", dim_product),
                        ("fact_sales", fact)):
            t.to_sql(name, con, if_exists="replace", index=False)
        for stmt in open("sql/analytics.sql").read().split(";"):
            if stmt.strip():
                con.execute(text(stmt))


def run():
    t0 = time.time()
    engine = create_engine(DB_URL)
    df, report = transform(extract())
    load(df, engine)
    report["seconds"] = round(time.time() - t0, 2)
    report["run_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.DataFrame([report]).to_sql("pipeline_runs", engine, if_exists="append", index=False)
    print("Pipeline OK:", report)
    return report


if __name__ == "__main__":
    run()
