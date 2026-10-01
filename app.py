import os
import re
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="DataPulse — Fortune 100 Multi-Industry Solutions", page_icon="⚡", layout="wide")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")

# Auto-initialize database on first boot if missing
if DB_URL.startswith("sqlite") and not os.path.exists("retail.db"):
    import generate_data
    import pipeline
    pipeline.run()

engine = create_engine(DB_URL)


@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)


# Header
st.title("⚡ DataPulse — Enterprise Multi-Industry Data Solutions")
st.caption("Data Engineering, Analytics Dashboards & GenAI Solutions for Fortune 100 Clients (Hi-tech · Healthcare · Retail · SaaS)")

# Domain Selector
domain = st.sidebar.radio(
    "Select Client Domain Vertical",
    ["Retail Analytics", "SaaS Subscriptions", "Healthcare SLA & Claims", "Hi-Tech Cloud Telemetry"],
    index=0
)

st.sidebar.divider()

# ==========================================================
# 1. RETAIL DOMAIN DASHBOARD
# ==========================================================
if domain == "Retail Analytics":
    sales = q("""SELECT f.*, p.category, p.product_name, c.region
                 FROM fact_sales f JOIN dim_product p USING(product_id)
                 JOIN dim_customer c USING(customer_id)""")

    with st.sidebar:
        st.header("Retail Filters")
        cats = st.multiselect("Category", sorted(sales.category.unique()), default=sorted(sales.category.unique()))
        regs = st.multiselect("Region", sorted(sales.region.unique()), default=sorted(sales.region.unique()))
        lo, hi = sales.order_date.min(), sales.order_date.max()
        d1, d2 = st.date_input("Date range", (pd.to_datetime(lo), pd.to_datetime(hi)))

    f = sales[sales.category.isin(cats) & sales.region.isin(regs)
              & (pd.to_datetime(sales.order_date) >= pd.to_datetime(d1))
              & (pd.to_datetime(sales.order_date) <= pd.to_datetime(d2))]

    orders = f.order_id.nunique()
    k = st.columns(4)
    k[0].metric("Total Revenue", f"₹{f.revenue.sum():,.0f}")
    k[1].metric("Orders Processed", f"{orders:,}")
    k[2].metric("Active Customers", f"{f.customer_id.nunique():,}")
    k[3].metric("Avg Order Value", f"₹{(f.revenue.sum() / max(orders, 1)):,.0f}")

    t0, t1, t2 = st.tabs(["Business Insights", "Sales Performance", "Customer RFM Segmentation"])

    with t0:
        st.subheader("Fortune 100 Client Business Insights")
        mon = q("SELECT * FROM v_monthly_revenue")
        cat = q("SELECT * FROM v_category_performance").sort_values("revenue", ascending=False)
        rfm_all = q("SELECT * FROM v_customer_rfm")
        mon["yr"], mon["mo"] = mon.order_month.str[:4], mon.order_month.str[5:]
        yoy = mon.groupby("yr").revenue.sum()
        peak = mon[mon.mo.isin(["11", "12"])].revenue.mean() / mon[~mon.mo.isin(["11", "12"])].revenue.mean()
        champ = rfm_all[rfm_all.segment == "Champions"]
        reg = sales.groupby("region").revenue.sum().sort_values(ascending=False)

        st.markdown(f"""
1. **Revenue Drivers**: **{cat.iloc[0].category}** generates **{cat.iloc[0].revenue_share_pct}%** of overall revenue.
2. **Growth Trajectory**: Revenue shifted from ₹{yoy.iloc[0]:,.0f} ({yoy.index[0]}) to ₹{yoy.iloc[-1]:,.0f} ({yoy.index[-1]}), demonstrating **{(yoy.iloc[-1] / yoy.iloc[0] - 1) * 100:+.1f}%** YoY growth.
3. **Q4 Seasonality**: Nov–Dec demand spikes **{peak:.2f}x** over baseline months. Recommended action: pre-allocate inventory in Q3.
4. **Customer Value**: **Champions** account for {len(champ) / len(rfm_all) * 100:.0f}% of total customers but generate **{champ.monetary.sum() / rfm_all.monetary.sum() * 100:.0f}%** of total sales revenue.
5. **Regional Hierarchy**: Top performing market is **{reg.index[0]}** (₹{reg.iloc[0]:,.0f}), lowest is **{reg.index[-1]}**.
""")

    with t1:
        a, b = st.columns(2)
        a.subheader("Monthly Revenue Trend")
        a.line_chart(f.groupby("order_month").revenue.sum())
        b.subheader("Revenue by Category")
        b.bar_chart(f.groupby("category").revenue.sum())
        a, b = st.columns(2)
        a.subheader("Regional Breakdown")
        a.bar_chart(f.groupby("region").revenue.sum())
        b.subheader("Top 10 Products")
        b.dataframe(f.groupby(["product_name", "category"]).revenue.sum().nlargest(10).round(0).reset_index(), hide_index=True)

    with t2:
        rfm = q("SELECT * FROM v_customer_rfm")
        rep = q("SELECT repeat_rate_pct FROM v_repeat_customers").iat[0, 0]
        st.metric("Repeat Customer Rate", f"{rep}%")
        seg = rfm.groupby("segment").agg(customers=("customer_id", "count"), revenue=("monetary", "sum")).round(0)
        a, b = st.columns(2)
        a.subheader("Customer Distribution by Segment"); a.bar_chart(seg.customers)
        b.subheader("Revenue Contribution by Segment"); b.bar_chart(seg.revenue)
        st.dataframe(rfm.sort_values("monetary", ascending=False).head(20), hide_index=True)


# ==========================================================
# 2. SAAS DOMAIN DASHBOARD
# ==========================================================
elif domain == "SaaS Subscriptions":
    st.header("SaaS Subscription Analytics & Retention")
    saas = q("SELECT * FROM fact_saas_subscriptions")
    metrics = q("SELECT * FROM v_saas_metrics")

    c1, c2, c3, c4 = st.columns(4)
    total_mrr = saas["mrr"].sum()
    c1.metric("Total Active MRR", f"${total_mrr:,.2f}")
    c2.metric("Annual Run Rate (ARR)", f"${total_mrr * 12:,.2f}")
    c3.metric("Total Subscribers", f"{len(saas):,}")
    c4.metric("Avg Churn Rate", f"{(saas.churned.mean() * 100):.1f}%")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("MRR Distribution by Plan Tier")
        st.bar_chart(metrics.set_index("tier")["total_mrr"])
    with col2:
        st.subheader("Subscriber Count by Plan Tier")
        st.bar_chart(metrics.set_index("tier")["total_customers"])

    st.subheader("Tier Performance Breakdown")
    st.dataframe(metrics, hide_index=True)


# ==========================================================
# 3. HEALTHCARE DOMAIN DASHBOARD
# ==========================================================
elif domain == "Healthcare SLA & Claims":
    st.header("Healthcare Claim Processing & SLA Metrics")
    hc_sla = q("SELECT * FROM v_healthcare_sla")
    hc_raw = q("SELECT * FROM fact_healthcare_claims")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Claims Ingested", f"{len(hc_raw):,}")
    c2.metric("Avg Claim Value", f"${hc_raw.claim_amount.mean():,.2f}")
    c3.metric("Avg Processing Time", f"{hc_raw.processing_hours.mean():.1f} hrs")
    c4.metric("Overall SLA Breach Rate", f"{(hc_raw[hc_raw.processing_hours > 24].shape[0] / len(hc_raw) * 100):.1f}%")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Avg Processing Hours by Claim Type")
        st.bar_chart(hc_sla.set_index("claim_type")["avg_processing_hours"])
    with col2:
        st.subheader("SLA Breach Rate (%) (>24 Hours)")
        st.bar_chart(hc_sla.set_index("claim_type")["sla_breach_pct"])

    st.subheader("Claim SLA Analytics Table")
    st.dataframe(hc_sla, hide_index=True)


# ==========================================================
# 4. HI-TECH DOMAIN DASHBOARD
# ==========================================================
elif domain == "Hi-Tech Cloud Telemetry":
    st.header("Hi-Tech Cloud Telemetry & Infrastructure Performance")
    ht = q("SELECT * FROM v_hitech_telemetry")
    ht_raw = q("SELECT * FROM fact_hitech_telemetry")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Microservice Logs Ingested", f"{len(ht_raw):,}")
    c2.metric("Avg API Latency", f"{ht_raw.latency_ms.mean():.2f} ms")
    c3.metric("Total Infra Compute Cost", f"${ht_raw.compute_cost.sum():,.2f}")
    c4.metric("Total System Errors", f"{ht_raw.error_count.sum():,}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Microservice Latency (ms)")
        st.bar_chart(ht.set_index("service_name")["avg_latency_ms"])
    with col2:
        st.subheader("Total Infra Compute Cost ($)")
        st.bar_chart(ht.set_index("service_name")["total_cost_usd"])

    st.subheader("Microservice Telemetry Metrics")
    st.dataframe(ht, hide_index=True)


# ==========================================================
# COMMON FOOTER TABS: GENAI & PIPELINE HEALTH
# ==========================================================
st.divider()
t_genai, t_health = st.tabs(["🤖 Ask Your Data (GenAI Assistant)", "⚙️ Pipeline Health & Data Quality"])

SCHEMA = """Tables available in star schema SQL warehouse:
- fact_sales(order_id, order_date 'YYYY-MM-DD', order_month 'YYYY-MM', customer_id, product_id, quantity, unit_price, discount, revenue)
- dim_customer(customer_id, region, city)
- dim_product(product_id, product_name, category)
- fact_saas_subscriptions(customer_id, tier, mrr, join_date, churned, seats)
- fact_healthcare_claims(claim_id, patient_id, claim_type, claim_amount, processing_hours, readmitted, claim_date)
- fact_hitech_telemetry(log_id, service_name, latency_ms, compute_cost, error_count, log_date)
Views: v_monthly_revenue, v_category_performance, v_customer_rfm, v_repeat_customers, v_saas_metrics, v_healthcare_sla, v_hitech_telemetry."""


def safe_select(sql):
    s = sql.strip().rstrip(";")
    if ";" in s or not re.match(r"(?is)^\s*(select|with)\b", s):
        return None
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", s):
        return None
    return s


with t_genai:
    st.subheader("Generative AI Query & Business Intelligence Engine")
    st.write("Convert plain-English business requests into validated SQL queries executed live against the warehouse.")

    try:
        key = os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = os.getenv("GEMINI_API_KEY", "")

    question = st.text_input("Enter business query (e.g. Which microservice has the highest API latency?)")
    if question:
        if not key:
            st.info("💡 Set GEMINI_API_KEY environment variable or Streamlit secret to activate live LLM querying.")
        else:
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            prompt = (f"You write one SQLite SELECT query based on this database schema:\n{SCHEMA}\n"
                      f"Return ONLY the SQL block, with no markdown formatting.\nQuestion: {question}")
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
                    st.error("Blocked: Only single read-only SELECT queries are allowed.")
            except Exception as e:
                st.error(f"LLM call execution error: {e}")

with t_health:
    st.subheader("ETL Data Quality & Execution Logs")
    runs = q("SELECT * FROM pipeline_runs ORDER BY run_at DESC")
    st.dataframe(runs, hide_index=True)
    st.caption("Data Quality validation logs track row counts, null values handled, duplicates removed, and processing time.")
