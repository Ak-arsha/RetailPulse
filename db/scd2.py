"""Slowly Changing Dimension Type 2 (SCD2) Implementation."""
import pandas as pd


def process_scd2_customers(new_df, existing_dim_df=None):
    """
    Processes SCD Type 2 tracking for customer dimension changes.
    Columns: customer_id, region, city, valid_from, valid_to, is_current
    """
    now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    current_customers = (new_df.groupby("customer_id")
                         .agg(region=("region", lambda s: s.mode().iat[0]),
                              city=("city", lambda s: s.mode().iat[0]))
                         .reset_index())

    current_customers["valid_from"] = now_str
    current_customers["valid_to"] = "9999-12-31 23:59:59"
    current_customers["is_current"] = 1

    if existing_dim_df is None or len(existing_dim_df) == 0:
        return current_customers

    # Merge and compare changes
    merged = current_customers.merge(existing_dim_df[existing_dim_df["is_current"] == 1],
                                     on="customer_id", suffixes=("", "_old"), how="left")

    changed_mask = (merged["region"] != merged["region_old"]) | (merged["city"] != merged["city_old"])
    changed_cust_ids = merged[changed_mask]["customer_id"].tolist()

    if changed_cust_ids:
        # Expire old records
        existing_dim_df.loc[existing_dim_df["customer_id"].isin(changed_cust_ids) &
                            (existing_dim_df["is_current"] == 1), "valid_to"] = now_str
        existing_dim_df.loc[existing_dim_df["customer_id"].isin(changed_cust_ids) &
                            (existing_dim_df["is_current"] == 1), "is_current"] = 0

    combined = pd.concat([existing_dim_df, current_customers], ignore_index=True)
    return combined.drop_duplicates(subset=["customer_id", "valid_from"])
