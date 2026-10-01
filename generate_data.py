"""Generate a messy, realistic retail orders CSV (synthetic) to simulate a raw client data drop."""
import numpy as np, pandas as pd

rng = np.random.default_rng(42)
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

rows = []
for oid in range(9000):
    c = customers[rng.choice(len(customers), p=cust_w)]
    d = days[rng.choice(len(days), p=w)]
    for _ in range(rng.integers(1, 4)):
        p = products[rng.integers(0, len(products))]
        rows.append([f"O{oid:05d}", d.strftime("%Y-%m-%d"), c[0], c[1], c[2],
                     p[0], p[1], p[2], int(rng.integers(1, 6)), p[3],
                     float(rng.choice([0, 0, 0, .05, .10, .20]))])

df = pd.DataFrame(rows, columns=["order_id", "order_date", "customer_id", "region", "city",
                                 "product_id", "product_name", "category", "quantity",
                                 "unit_price", "discount"])
n = len(df)
# --- inject realistic data-quality problems ---
df.loc[rng.choice(n, int(.015 * n), replace=False), "region"] = None
df.loc[rng.choice(n, int(.01 * n), replace=False), "quantity"] = -1
df.loc[rng.choice(n, int(.01 * n), replace=False), "order_date"] = "not available"
idx = rng.choice(n, int(.2 * n), replace=False)
df.loc[idx, "category"] = df.loc[idx, "category"].str.upper()
idx = rng.choice(n, int(.1 * n), replace=False)
df.loc[idx, "category"] = " " + df.loc[idx, "category"] + " "
df = pd.concat([df, df.sample(int(.02 * n), random_state=1)]).sample(frac=1, random_state=2)
df.to_csv("data/raw_orders.csv", index=False)
print(f"Wrote data/raw_orders.csv with {len(df):,} rows")
