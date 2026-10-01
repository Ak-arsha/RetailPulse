"""
ETL Pipeline Engine with Pandera Data Quality Validation,
Quarantine DLQ Routing, and Row-Count Reconciliation Assertions.
"""
import os
import time
import pandas as pd
from sqlalchemy import text
from db.schema import get_engine, init_db
from db.scd2 import process_scd2_customers
from validation.schemas import validate_retail_data

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")

RAW_RETAIL = "data/raw_orders.csv"
RAW_SAAS = "data/raw_saas.csv"
RAW_HEALTHCARE = "data/raw_healthcare.csv"
RAW_HITECH = "data/raw_hitech.csv"


def extract(path):
    """Read raw data from S3 if RAW_S3_URI is set, else local CSV."""
    uri = os.getenv("RAW_S3_URI")
    return pd.read_csv(uri if uri else path)


def transform_retail_with_reconciliation(df):
    """
    Transforms raw retail data and enforces strict Row-Count Reconciliation Assertion:
    raw_rows == clean_rows + quarantine_rows + duplicate_rows
    """
    raw_rows = len(df)
    clean_df, quarantine_df, duplicates_count = validate_retail_data(df)

    # Transform clean DataFrame
    for c in ("category", "region", "city", "product_name"):
        clean_df[c] = clean_df[c].astype("string").str.strip().str.title()
    clean_df["region"] = clean_df["region"].fillna("Unknown")

    clean_df["order_date"] = pd.to_datetime(clean_df["order_date"])
    clean_df["revenue"] = (clean_df["quantity"] * clean_df["unit_price"] * (1 - clean_df["discount"])).round(2)
    clean_df["order_month"] = clean_df["order_date"].dt.strftime("%Y-%m")
    clean_df["order_day"] = (clean_df["order_date"] - pd.Timestamp("2000-01-01")).dt.days
    clean_df["order_date"] = clean_df["order_date"].dt.strftime("%Y-%m-%d")
    clean_df["created_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    clean_rows = len(clean_df)
    quarantine_rows = len(quarantine_df)

    # ==========================================================
    # ROW-COUNT RECONCILIATION CHECK ASSERTION
    # ==========================================================
    reconciled_total = clean_rows + quarantine_rows + duplicates_count
    assert raw_rows == reconciled_total, (
        f"Row-Count Reconciliation Failed! Raw ({raw_rows}) != "
        f"Clean ({clean_rows}) + Quarantine ({quarantine_rows}) + Duplicates ({duplicates_count})"
    )

    report = {
        "raw_rows": raw_rows,
        "clean_rows": clean_rows,
        "quarantine_rows": quarantine_rows,
        "duplicates_removed": duplicates_count,
        "reconciled": True
    }

    return clean_df, quarantine_df, report


def transform_saas(df):
    df = df.drop_duplicates().copy()
    df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
    df = df.dropna(subset=["join_date", "customer_id"]).copy()
    df = df[df["mrr"] >= 0].copy()
    df["join_date"] = df["join_date"].dt.strftime("%Y-%m-%d")
    df["churned"] = df["churned"].astype(int)
    df["created_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return df


def transform_healthcare(df):
    df = df.drop_duplicates().copy()
    df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")
    df = df.dropna(subset=["claim_date", "claim_id"]).copy()
    df = df[df["claim_amount"] >= 0].copy()
    df["claim_date"] = df["claim_date"].dt.strftime("%Y-%m-%d")
    df["readmitted"] = df["readmitted"].astype(int)
    df["created_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return df


def transform_hitech(df):
    df = df.drop_duplicates().copy()
    df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
    df = df.dropna(subset=["log_date", "log_id"]).copy()
    df = df[df["latency_ms"] >= 0].copy()
    df["log_date"] = df["log_date"].dt.strftime("%Y-%m-%d")
    df["created_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    return df


def load(df_retail, df_quarantine, df_saas, df_hc, df_hitech, engine):
    dim_customer_scd2 = process_scd2_customers(df_retail)

    dim_product = (df_retail.groupby("product_id")
                   .agg(product_name=("product_name", "first"),
                        category=("category", "first")).reset_index())

    fact_retail = df_retail[["order_id", "order_date", "order_month", "order_day", "customer_id",
                             "product_id", "quantity", "unit_price", "discount", "revenue", "created_at"]]

    with engine.begin() as con:
        dim_customer_scd2.to_sql("dim_customer", con, if_exists="replace", index=False)
        dim_product.to_sql("dim_product", con, if_exists="replace", index=False)
        fact_retail.to_sql("fact_sales", con, if_exists="replace", index=False)
        df_saas.to_sql("fact_saas_subscriptions", con, if_exists="replace", index=False)
        df_hc.to_sql("fact_healthcare_claims", con, if_exists="replace", index=False)
        df_hitech.to_sql("fact_hitech_telemetry", con, if_exists="replace", index=False)

        if len(df_quarantine) > 0:
            df_quarantine.to_sql("quarantine_records", con, if_exists="append", index=False)

        for stmt in open("sql/analytics.sql").read().split(";"):
            if stmt.strip():
                con.execute(text(stmt))


def run():
    t0 = time.time()
    engine = get_engine(DB_URL)
    init_db(engine)

    df_ret_raw = extract(RAW_RETAIL)
    df_ret_clean, df_quarantine, report = transform_retail_with_reconciliation(df_ret_raw)

    df_saas_clean = transform_saas(extract(RAW_SAAS))
    df_hc_clean = transform_healthcare(extract(RAW_HEALTHCARE))
    df_ht_clean = transform_hitech(extract(RAW_HITECH))

    load(df_ret_clean, df_quarantine, df_saas_clean, df_hc_clean, df_ht_clean, engine)

    report["seconds"] = round(time.time() - t0, 2)
    report["run_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    pd.DataFrame([report]).to_sql("pipeline_runs", engine, if_exists="append", index=False)

    print("Pipeline OK (Reconciled 100%):", report)
    return report


if __name__ == "__main__":
    run()
