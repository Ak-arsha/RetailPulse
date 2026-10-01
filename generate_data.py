"""Generate synthetic multi-domain datasets (Retail, SaaS, Healthcare, Hi-Tech)
with realistic data-quality anomalies to simulate Fortune 100 raw client data drops."""
import os
import numpy as np
import pandas as pd

os.makedirs("data", exist_ok=True)
rng = np.random.default_rng(42)

# ==========================================
# 1. RETAIL DOMAIN
# ==========================================
CATS = {"Electronics": (40, 900), "Home": (10, 250), "Fashion": (8, 150),
        "Grocery": (1, 30), "Beauty": (4, 90)}
REGIONS = {"North": ["Delhi", "Gurugram", "Lucknow"], "South": ["Chennai", "Bengaluru", "Hyderabad"],
           "East": ["Kolkata", "Patna"], "West": ["Mumbai", "Pune", "Ahmedabad"]}

products = []
for i in range(120):
    cat = list(CATS)[i % 5]
    lo, hi = CATS[cat]
    products.append((f"P{i:03d}", f"{cat} Item {i:03d}", cat, round(float(rng.uniform(lo, hi)), 2)))

customers = []
for i in range(1500):
    reg = rng.choice(list(REGIONS), p=[.3, .3, .15, .25])
    customers.append((f"C{i:04d}", reg, rng.choice(REGIONS[reg])))

days = pd.date_range("2024-01-01", "2025-12-31")
w = np.array([1.8 if d.month in (11, 12) else 1.0 for d in days]) * np.linspace(1, 1.4, len(days))
w /= w.sum()
cust_w = rng.pareto(2.0, len(customers)) + 1
cust_w /= cust_w.sum()

rows_retail = []
for oid in range(9000):
    c = customers[rng.choice(len(customers), p=cust_w)]
    d = days[rng.choice(len(days), p=w)]
    for _ in range(rng.integers(1, 4)):
        p = products[rng.integers(0, len(products))]
        rows_retail.append([f"O{oid:05d}", d.strftime("%Y-%m-%d"), c[0], c[1], c[2],
                            p[0], p[1], p[2], int(rng.integers(1, 6)), p[3],
                            float(rng.choice([0, 0, 0, .05, .10, .20]))])

df_retail = pd.DataFrame(rows_retail, columns=["order_id", "order_date", "customer_id", "region", "city",
                                        "product_id", "product_name", "category", "quantity",
                                        "unit_price", "discount"])
n_ret = len(df_retail)
df_retail.loc[rng.choice(n_ret, int(.015 * n_ret), replace=False), "region"] = None
df_retail.loc[rng.choice(n_ret, int(.01 * n_ret), replace=False), "quantity"] = -1
df_retail.loc[rng.choice(n_ret, int(.01 * n_ret), replace=False), "order_date"] = "not available"
idx_ret = rng.choice(n_ret, int(.2 * n_ret), replace=False)
df_retail.loc[idx_ret, "category"] = df_retail.loc[idx_ret, "category"].str.upper()
idx_ret2 = rng.choice(n_ret, int(.1 * n_ret), replace=False)
df_retail.loc[idx_ret2, "category"] = " " + df_retail.loc[idx_ret2, "category"] + " "
df_retail = pd.concat([df_retail, df_retail.sample(int(.02 * n_ret), random_state=1)]).sample(frac=1, random_state=2)
df_retail.to_csv("data/raw_orders.csv", index=False)
print(f"[Retail] Wrote data/raw_orders.csv ({len(df_retail):,} rows)")

# ==========================================
# 2. SAAS DOMAIN (Subscription Analytics)
# ==========================================
saas_tiers = ["Starter", "Professional", "Enterprise"]
rows_saas = []
for sid in range(1200):
    cust_id = f"SAAS_C{sid:04d}"
    tier = rng.choice(saas_tiers, p=[0.5, 0.35, 0.15])
    base_mrr = 99.0 if tier == "Starter" else (499.0 if tier == "Professional" else 2499.0)
    join_date = days[rng.choice(len(days))]
    churned = bool(rng.choice([True, False], p=[0.12, 0.88]))
    seats = int(rng.integers(5, 200) if tier == "Enterprise" else rng.integers(1, 15))
    rows_saas.append([cust_id, tier, base_mrr, join_date.strftime("%Y-%m-%d"), churned, seats])

df_saas = pd.DataFrame(rows_saas, columns=["customer_id", "tier", "mrr", "join_date", "churned", "seats"])
# Inject data-quality noise
n_s = len(df_saas)
df_saas.loc[rng.choice(n_s, int(0.01 * n_s), replace=False), "mrr"] = -50.0
df_saas.loc[rng.choice(n_s, int(0.015 * n_s), replace=False), "join_date"] = "invalid_date"
df_saas = pd.concat([df_saas, df_saas.sample(int(0.02 * n_s), random_state=42)]).sample(frac=1, random_state=3)
df_saas.to_csv("data/raw_saas.csv", index=False)
print(f"[SaaS] Wrote data/raw_saas.csv ({len(df_saas):,} rows)")

# ==========================================
# 3. HEALTHCARE DOMAIN (Claims & SLA Analytics)
# ==========================================
claims_types = ["Inpatient", "Outpatient", "Emergency", "Pharmacy"]
rows_hc = []
for cid in range(2500):
    claim_id = f"CLM{cid:05d}"
    patient_id = f"PAT{rng.integers(1000, 9999)}"
    ctype = rng.choice(claims_types)
    claim_amount = round(float(rng.uniform(150, 12000)), 2)
    proc_hours = round(float(rng.uniform(2.0, 72.0)), 1)
    readmitted = bool(rng.choice([True, False], p=[0.15, 0.85]))
    claim_date = days[rng.choice(len(days))]
    rows_hc.append([claim_id, patient_id, ctype, claim_amount, proc_hours, readmitted, claim_date.strftime("%Y-%m-%d")])

df_hc = pd.DataFrame(rows_hc, columns=["claim_id", "patient_id", "claim_type", "claim_amount", "processing_hours", "readmitted", "claim_date"])
n_h = len(df_hc)
df_hc.loc[rng.choice(n_h, int(0.01 * n_h), replace=False), "claim_amount"] = -100.0
df_hc = pd.concat([df_hc, df_hc.sample(int(0.015 * n_h), random_state=99)]).sample(frac=1, random_state=4)
df_hc.to_csv("data/raw_healthcare.csv", index=False)
print(f"[Healthcare] Wrote data/raw_healthcare.csv ({len(df_hc):,} rows)")

# ==========================================
# 4. HI-TECH DOMAIN (Cloud Telemetry & Infrastructure)
# ==========================================
services = ["AuthService", "PaymentGateway", "DataIngestor", "ModelInferenceAPI", "SearchEngine"]
rows_hitech = []
for tid in range(3000):
    log_id = f"LOG{tid:06d}"
    svc = rng.choice(services)
    latency_ms = round(float(rng.exponential(scale=120.0) + 15.0), 2)
    compute_cost = round(float(rng.uniform(0.01, 2.50)), 4)
    error_count = int(rng.choice([0, 0, 0, 0, 1, 2, 5], p=[0.8, 0.1, 0.05, 0.02, 0.01, 0.01, 0.01]))
    log_date = days[rng.choice(len(days))]
    rows_hitech.append([log_id, svc, latency_ms, compute_cost, error_count, log_date.strftime("%Y-%m-%d")])

df_hitech = pd.DataFrame(rows_hitech, columns=["log_id", "service_name", "latency_ms", "compute_cost", "error_count", "log_date"])
n_ht = len(df_hitech)
df_hitech.loc[rng.choice(n_ht, int(0.01 * n_ht), replace=False), "latency_ms"] = -10.0
df_hitech = pd.concat([df_hitech, df_hitech.sample(int(0.02 * n_ht), random_state=12)]).sample(frac=1, random_state=5)
df_hitech.to_csv("data/raw_hitech.csv", index=False)
print(f"[Hi-Tech] Wrote data/raw_hitech.csv ({len(df_hitech):,} rows)")
