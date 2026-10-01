import os, re
import pandas as pd, requests, streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="RetailPulse", page_icon="📊", layout="wide")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")

if DB_URL.startswith("sqlite") and not os.path.exists("retail.db"):   # first boot on cloud
    import generate_data, pipeline  # noqa: F401
    pipeline.run()
engine = create_engine(DB_URL)


@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)


sales = q("""SELECT f.*, p.category, p.product_name, c.region
             FROM fact_sales f JOIN dim_product p USING(product_id)
             JOIN dim_customer c USING(customer_id)""")

st.title("📊 RetailPulse — Retail Sales Analytics")
st.caption("Raw CSV → cleaning & validation → star-schema SQL DB → analytics views → dashboard")

# ---- filters
with st.sidebar:
    st.header("Filters")
    cats = st.multiselect("Category", sorted(sales.category.unique()), default=sorted(sales.category.unique()))
    regs = st.multiselect("Region", sorted(sales.region.unique()), default=sorted(sales.region.unique()))
    lo, hi = sales.order_date.min(), sales.order_date.max()
    d1, d2 = st.date_input("Date range", (pd.to_datetime(lo), pd.to_datetime(hi)))
f = sales[sales.category.isin(cats) & sales.region.isin(regs)
          & (pd.to_datetime(sales.order_date) >= pd.to_datetime(d1))
          & (pd.to_datetime(sales.order_date) <= pd.to_datetime(d2))]

# ---- KPIs
orders = f.order_id.nunique()
k = st.columns(4)
k[0].metric("Revenue", f"₹{f.revenue.sum():,.0f}")
k[1].metric("Orders", f"{orders:,}")
k[2].metric("Customers", f"{f.customer_id.nunique():,}")
k[3].metric("Avg order value", f"₹{(f.revenue.sum() / max(orders, 1)):,.0f}")

t0, t1, t2, t3, t4 = st.tabs(["Insights", "Sales", "Customers (RFM)", "Ask your data (GenAI)", "Pipeline health"])

with t0:
    st.subheader("Business questions this answers")
    mon = q("SELECT * FROM v_monthly_revenue")
    cat = q("SELECT * FROM v_category_performance").sort_values("revenue", ascending=False)
    rfm_all = q("SELECT * FROM v_customer_rfm")
    mon["yr"], mon["mo"] = mon.order_month.str[:4], mon.order_month.str[5:]
    yoy = mon.groupby("yr").revenue.sum()
    peak = mon[mon.mo.isin(["11", "12"])].revenue.mean() / mon[~mon.mo.isin(["11", "12"])].revenue.mean()
    champ = rfm_all[rfm_all.segment == "Champions"]
    reg = sales.groupby("region").revenue.sum().sort_values(ascending=False)
    st.markdown(f"""
1. **Where does revenue come from?** **{cat.iloc[0].category}** drives **{cat.iloc[0].revenue_share_pct}%** of revenue, so the business depends heavily on one category.
2. **Are we growing?** Revenue moved from ₹{yoy.iloc[0]:,.0f} ({yoy.index[0]}) to ₹{yoy.iloc[-1]:,.0f} ({yoy.index[-1]}), a change of **{(yoy.iloc[-1] / yoy.iloc[0] - 1) * 100:+.1f}%**.
3. **Is there seasonality?** Nov–Dec months average **{peak:.2f}x** the revenue of other months, so plan inventory and campaigns ahead of Q4.
4. **Which customers matter most?** **Champions** are {len(champ) / len(rfm_all) * 100:.0f}% of customers but **{champ.monetary.sum() / rfm_all.monetary.sum() * 100:.0f}%** of revenue, so prioritise retention for them and win-back for "At risk".
5. **Which region leads?** **{reg.index[0]}** at ₹{reg.iloc[0]:,.0f}; weakest is **{reg.index[-1]}**.
""")
    st.caption("Insights are computed live from the SQL views. Underlying data is synthetic.")

with t1:
    a, b = st.columns(2)
    a.subheader("Monthly revenue")
    a.line_chart(f.groupby("order_month").revenue.sum())
    b.subheader("Revenue by category")
    b.bar_chart(f.groupby("category").revenue.sum())
    a, b = st.columns(2)
    a.subheader("Revenue by region")
    a.bar_chart(f.groupby("region").revenue.sum())
    b.subheader("Top 10 products")
    b.dataframe(f.groupby(["product_name", "category"]).revenue.sum()
                 .nlargest(10).round(0).reset_index(), hide_index=True)

with t2:
    rfm = q("SELECT * FROM v_customer_rfm")
    rep = q("SELECT repeat_rate_pct FROM v_repeat_customers").iat[0, 0]
    st.metric("Repeat-customer rate", f"{rep}%")
    seg = rfm.groupby("segment").agg(customers=("customer_id", "count"),
                                      revenue=("monetary", "sum")).round(0)
    a, b = st.columns(2)
    a.subheader("Customers per segment"); a.bar_chart(seg.customers)
    b.subheader("Revenue per segment");   b.bar_chart(seg.revenue)
    st.caption("Segments from NTILE-based RFM scoring in SQL (see sql/analytics.sql).")
    st.dataframe(rfm.sort_values("monetary", ascending=False).head(20), hide_index=True)

SCHEMA = """Tables: fact_sales(order_id, order_date TEXT 'YYYY-MM-DD', order_month TEXT 'YYYY-MM', order_day INT,
customer_id, product_id, quantity, unit_price, discount, revenue),
dim_customer(customer_id, region, city), dim_product(product_id, product_name, category).
Views: v_monthly_revenue, v_category_performance, v_customer_rfm(customer_id, recency_days, frequency, monetary, segment), v_repeat_customers."""


def safe_select(sql):
    s = sql.strip().rstrip(";")
    if ";" in s or not re.match(r"(?is)^\s*(select|with)\b", s):
        return None
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", s):
        return None
    return s


with t3:
    st.write("Ask a question in plain English; an LLM writes the SQL, which is validated (read-only) and run.")
    try:
        key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = os.getenv("GEMINI_API_KEY", "")
    question = st.text_input("e.g. Which region had the highest revenue in Q4 2025?")
    if question:
        if not key:
            st.info("Set GEMINI_API_KEY (env var or Streamlit secret) to enable this tab.")
        else:
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            prompt = (f"You write one SQLite SELECT query. {SCHEMA}\nReturn ONLY the SQL, no markdown.\n"
                      f"Question: {question}")
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  params={"key": key}, timeout=30,
                                  json={"contents": [{"parts": [{"text": prompt}]}]})
                sql = r.json()["candidates"][0]["content"]["parts"][0]["text"].replace("```sql", "").replace("```", "").strip()
                ok = safe_select(sql)
                st.code(sql, language="sql")
                if ok:
                    st.dataframe(pd.read_sql(ok, engine), hide_index=True)
                else:
                    st.error("Blocked: only a single read-only SELECT is allowed.")
            except Exception as e:
                st.error(f"LLM call failed: {e}")

with t4:
    st.subheader("Pipeline run log")
    st.dataframe(q("SELECT * FROM pipeline_runs ORDER BY run_at DESC"), hide_index=True)
    st.caption("Every run records rows in, duplicates removed, invalid rows dropped and runtime.")
