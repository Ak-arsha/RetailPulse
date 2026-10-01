import pandas as pd
from pipeline import transform_retail, transform_saas, transform_healthcare, transform_hitech


def sample_retail_raw():
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


def test_retail_dedupe_and_invalid_rows_dropped():
    df, r = transform_retail(sample_retail_raw())
    assert r["duplicates_removed"] == 1
    assert r["invalid_rows_dropped"] == 2  # bad date + negative quantity
    assert set(df.order_id) == {"O1", "O4"}


def test_retail_standardisation_and_revenue():
    df, _ = transform_retail(sample_retail_raw())
    assert df[df.order_id == "O1"].category.iat[0] == "Electronics"
    assert df[df.order_id == "O1"].revenue.iat[0] == 180.0  # 2 * 100 * 0.9
    assert (df.region.isin(["North", "East", "Unknown"])).all()


def test_saas_transform():
    df_raw = pd.DataFrame({
        "customer_id": ["C1", "C1", "C2"],
        "tier": ["Starter", "Starter", "Enterprise"],
        "mrr": [99.0, 99.0, -10.0],
        "join_date": ["2024-01-01", "2024-01-01", "invalid_date"],
        "churned": [False, False, True],
        "seats": [5, 5, 20]
    })
    df_clean = transform_saas(df_raw)
    assert len(df_clean) == 1
    assert df_clean.customer_id.iat[0] == "C1"


def test_healthcare_transform():
    df_raw = pd.DataFrame({
        "claim_id": ["CLM1", "CLM2"],
        "patient_id": ["PAT1", "PAT2"],
        "claim_type": ["Inpatient", "Outpatient"],
        "claim_amount": [500.0, -50.0],
        "processing_hours": [12.5, 24.0],
        "readmitted": [False, True],
        "claim_date": ["2024-05-10", "2024-05-11"]
    })
    df_clean = transform_healthcare(df_raw)
    assert len(df_clean) == 1
    assert df_clean.claim_id.iat[0] == "CLM1"


def test_hitech_transform():
    df_raw = pd.DataFrame({
        "log_id": ["L1", "L2"],
        "service_name": ["AuthService", "PaymentGateway"],
        "latency_ms": [45.2, -5.0],
        "compute_cost": [0.05, 0.10],
        "error_count": [0, 1],
        "log_date": ["2024-06-01", "2024-06-02"]
    })
    df_clean = transform_hitech(df_raw)
    assert len(df_clean) == 1
    assert df_clean.log_id.iat[0] == "L1"
