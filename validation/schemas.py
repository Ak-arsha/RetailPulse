"""Pandera Data Quality Validation Engine & Quarantine Routing."""
import pandas as pd


def validate_retail_data(df):
    """
    Validates raw retail data.
    Returns: (clean_df, quarantine_df, duplicates_count)
    """
    raw_rows = len(df)

    # 1. Deduplication accounting
    df_dedup = df.drop_duplicates().copy()
    duplicates_count = raw_rows - len(df_dedup)

    quarantine_list = []
    clean_mask = pd.Series(True, index=df_dedup.index)

    # Rule 1: Key fields must not be null
    null_keys = df_dedup[["order_id", "customer_id", "product_id"]].isna().any(axis=1)
    if null_keys.any():
        for idx, row in df_dedup[null_keys].iterrows():
            quarantine_list.append({
                "dataset_name": "Retail Orders",
                "record_id": str(row.get("order_id", "UNKNOWN")),
                "raw_payload": str(row.to_dict()),
                "rejection_reason": "Null Key Fields (order_id/customer_id/product_id)",
                "quarantined_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        clean_mask &= ~null_keys

    # Rule 2: Order Date must be valid date
    dates = pd.to_datetime(df_dedup["order_date"], errors="coerce")
    bad_dates = dates.isna() & clean_mask
    if bad_dates.any():
        for idx, row in df_dedup[bad_dates].iterrows():
            quarantine_list.append({
                "dataset_name": "Retail Orders",
                "record_id": str(row.get("order_id", "UNKNOWN")),
                "raw_payload": str(row.to_dict()),
                "rejection_reason": f"Invalid Order Date format: {row.get('order_date')}",
                "quarantined_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        clean_mask &= ~bad_dates

    # Rule 3: Quantity & Price must be positive
    invalid_metrics = ((df_dedup["quantity"] <= 0) | (df_dedup["unit_price"] <= 0)) & clean_mask
    if invalid_metrics.any():
        for idx, row in df_dedup[invalid_metrics].iterrows():
            quarantine_list.append({
                "dataset_name": "Retail Orders",
                "record_id": str(row.get("order_id", "UNKNOWN")),
                "raw_payload": str(row.to_dict()),
                "rejection_reason": f"Non-positive quantity ({row.get('quantity')}) or price ({row.get('unit_price')})",
                "quarantined_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        clean_mask &= ~invalid_metrics

    clean_df = df_dedup[clean_mask].copy()
    quarantine_df = pd.DataFrame(quarantine_list)

    return clean_df, quarantine_df, duplicates_count
