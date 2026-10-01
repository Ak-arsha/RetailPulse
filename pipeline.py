"""ETL: extract multi-domain raw CSVs -> clean/validate -> load star schema -> build SQL analytics views.
Supports local SQLite or cloud Postgres/Supabase/AWS RDS via DATABASE_URL."""
import os
import time
import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")

RAW_RETAIL = "data/raw_orders.csv"
RAW_SAAS = "data/raw_saas.csv"
RAW_HEALTHCARE = "data/raw_healthcare.csv"
RAW_HITECH = "data/raw_hitech.csv"


def extract(path):
    """Read raw data from S3 if RAW_S3_URI is set, else local CSV."""
    uri = os.getenv("RAW_S3_URI")
    return pd.read_csv(uri if uri else path)


def transform_retail(df):
    df = df.copy()
    r = {"raw_rows": len(df)}
    df = df.drop_duplicates().copy()
    r["duplicates_removed"] = r["raw_rows"] - len(df)

    for c in ("category", "region", "city", "product_name"):
        df[c] = df[c].astype("string").str.strip().str.title()
    r["null_region_filled"] = int(df["region"].isna().sum())
    df["region"] = df["region"].fillna("Unknown")

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["order_date", "customer_id", "product_id", "order_id"]).copy()
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)].copy()
    r["invalid_rows_dropped"] = before - len(df)

    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    df["order_month"] = df["order_date"].dt.strftime("%Y-%m")
    df["order_day"] = (df["order_date"] - pd.Timestamp("2000-01-01")).dt.days
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

    assert df[["order_id", "customer_id", "product_id"]].notna().all().all(), "null keys in retail"
    assert (df["revenue"] >= 0).all(), "negative revenue in retail"
    r["clean_rows"] = len(df)
    return df, r


def transform_saas(df):
    df = df.drop_duplicates().copy()
    df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
    df = df.dropna(subset=["join_date", "customer_id"]).copy()
    df = df[df["mrr"] >= 0].copy()
    df["join_date"] = df["join_date"].dt.strftime("%Y-%m-%d")
    df["churned"] = df["churned"].astype(int)
    return df


def transform_healthcare(df):
    df = df.drop_duplicates().copy()
    df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")
    df = df.dropna(subset=["claim_date", "claim_id"]).copy()
    df = df[df["claim_amount"] >= 0].copy()
    df["claim_date"] = df["claim_date"].dt.strftime("%Y-%m-%d")
    df["readmitted"] = df["readmitted"].astype(int)
    return df


def transform_hitech(df):
    df = df.drop_duplicates().copy()
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    df = df.dropna(subset=["log_date", "log_id"]).copy()
    df = df[df["latency_ms"] >= 0].copy()
    df["log_date"] = df["log_date"].dt.strftime("%Y-%m-%d")
    return df


def load(df_retail, df_saas, df_hc, df_hitech, engine):
    dim_customer = (df_retail.groupby("customer_id")
                    .agg(region=("region", lambda s: s.mode().iat[0]),
                         city=("city", lambda s: s.mode().iat[0])).reset_index())
    dim_product = (df_retail.groupby("product_id")
                   .agg(product_name=("product_name", "first"),
                        category=("category", "first")).reset_index())
    fact_retail = df_retail[["order_id", "order_date", "order_month", "order_day", "customer_id",
                             "product_id", "quantity", "unit_price", "discount", "revenue"]]

    with engine.begin() as con:
        for name, t in (("dim_customer", dim_customer),
                        ("dim_product", dim_product),
                        ("fact_sales", fact_retail),
                        ("fact_saas_subscriptions", df_saas),
                        ("fact_healthcare_claims", df_hc),
                        ("fact_hitech_telemetry", df_hitech)):
            t.to_sql(name, con, if_exists="replace", index=False)

        for stmt in open("sql/analytics.sql").read().split(";"):
            if stmt.strip():
                con.execute(text(stmt))


def run():
    t0 = time.time()
    engine = create_engine(DB_URL)

    df_ret_raw = extract(RAW_RETAIL)
    df_ret_clean, report = transform_retail(df_ret_raw)

    df_saas_raw = extract(RAW_SAAS)
    df_saas_clean = transform_saas(df_saas_raw)

    df_hc_raw = extract(RAW_HEALTHCARE)
    df_hc_clean = transform_healthcare(df_hc_raw)

    df_ht_raw = extract(RAW_HITECH)
    df_ht_clean = transform_hitech(df_ht_raw)

    load(df_ret_clean, df_saas_clean, df_hc_clean, df_ht_clean, engine)

    report["seconds"] = round(time.time() - t0, 2)
    report["run_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    pd.DataFrame([report]).to_sql("pipeline_runs", engine, if_exists="append", index=False)

    print("Pipeline OK:", report)
    return report


if __name__ == "__main__":
    run()
