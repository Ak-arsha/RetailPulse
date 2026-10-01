import pandas as pd
from pipeline import transform


def raw():
    return pd.DataFrame({
        "order_id": ["O1", "O1", "O2", "O3", "O4"],
        "order_date": ["2025-01-05", "2025-01-05", "bad-date", "2025-02-10", "2025-03-01"],
        "customer_id": ["C1", "C1", "C2", "C3", "C4"],
        "region": ["north", "north", "South", None, "East "],
        "city": ["delhi", "delhi", "chennai", "pune", "patna"],
        "product_id": ["P1", "P1", "P2", "P3", "P4"],
        "product_name": ["a", "a", "b", "c", "d"],
        "category": [" electronics ", " electronics ", "HOME", "Home", "Fashion"],
        "quantity": [2, 2, 1, -1, 3],
        "unit_price": [100.0, 100.0, 50.0, 20.0, 10.0],
        "discount": [0.1, 0.1, 0.0, 0.0, 0.0],
    })


def test_dedupe_and_invalid_rows_dropped():
    df, r = transform(raw())
    assert r["duplicates_removed"] == 1
    assert r["invalid_rows_dropped"] == 2          # bad date + negative quantity
    assert set(df.order_id) == {"O1", "O4"}


def test_standardisation_and_revenue():
    df, _ = transform(raw())
    assert df[df.order_id == "O1"].category.iat[0] == "Electronics"
    assert df[df.order_id == "O1"].revenue.iat[0] == 180.0   # 2 * 100 * 0.9
    assert (df.region.isin(["North", "East", "Unknown"])).all()
