import os
import hashlib
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

st.set_page_config(page_title="DataPulse — Enterprise Multi-Industry Platform", page_icon="⚡", layout="wide")

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")
engine = create_engine(DB_URL)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)


# Auto-initialize DB on first boot
if DB_URL.startswith("sqlite") and not os.path.exists("retail.db"):
    import db.schema
    db.schema.init_db(engine)
    import generate_data
    import pipeline
    pipeline.run()

# ==========================================================
# AUTHENTICATION & SESSION MANAGEMENT
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None

if not st.session_state["authenticated"]:
    st.markdown("""
        <style>
        .login-card {
            max-width: 420px;
            margin: 40px auto;
            padding: 30px;
            border-radius: 12px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 1px solid #334155;
            color: #f8fafc;
            text-align: center;
        }
        .login-footer {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("⚡ DataPulse")
        st.subheader("Enterprise Authentication")
        st.caption("Sign in to access Multi-Industry Solutions & GenAI Analytics")

        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In 🔐", use_container_width=True)

            if submit_login:
                uname = username_input.strip()
                pwd_hash = hash_password(password_input.strip())
                try:
                    user_df = q(f"SELECT username, role, is_active FROM users WHERE username = '{uname}' AND hashed_password = '{pwd_hash}'")
                    if len(user_df) > 0 and user_df.iat[0, 2] == 1:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_df.iat[0, 0]
                        st.session_state["user_role"] = user_df.iat[0, 1]
                        st.success(f"Welcome {user_df.iat[0, 0]} ({user_df.iat[0, 1]} role)")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception as e:
                    # Fallback check for demo
                    if uname in ["admin", "analyst", "viewer"] and password_input in ["admin123", "analyst123", "viewer123"]:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = uname
                        st.session_state["user_role"] = uname.capitalize()
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        st.info("💡 **Demo Credentials**:\n- **Admin**: `admin` / `admin123`\n- **Analyst**: `analyst` / `analyst123`\n- **Viewer**: `viewer` / `viewer123`")
        st.markdown("<div class='login-footer'>🔒 <i>Unauthorized access is monitored and logged.</i></div>", unsafe_allow_html=True)
    st.stop()


# ==========================================================
# LOGGED IN DASHBOARD UI
# ==========================================================
user_role = st.session_state["user_role"]
username = st.session_state["username"]

st.sidebar.markdown(f"👤 **User**: `{username}` | 🔑 **Role**: `{user_role}`")
if st.sidebar.button("Logout 🚪"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.rerun()

st.sidebar.divider()

st.title("⚡ DataPulse — Enterprise Multi-Industry Platform")
st.caption("Data Engineering, Pandera DLQ, dbt Modeling, Dagster Orchestration, FastAPI & GenAI Solutions")

domain = st.sidebar.radio(
    "Select Client Domain Vertical",
    ["Retail Analytics", "SaaS Subscriptions", "Healthcare SLA & Claims", "Hi-Tech Cloud Telemetry"],
    index=0
)

st.sidebar.divider()

# ==========================================================
# 1. RETAIL DOMAIN
# ==========================================================
if domain == "Retail Analytics":
    sales = q("""SELECT f.*, p.category, p.product_name, c.region
                 FROM fact_sales f JOIN dim_product p USING(product_id)
                 JOIN dim_customer c USING(customer_id)""")

    with st.sidebar:
        st.header("Retail Filters")
        cats = st.multiselect("Category", sorted(sales.category.unique()), default=sorted(sales.category.unique()))
        regs = st.multiselect("Region", sorted(sales.region.unique()), default=sorted(sales.region.unique()))
        lo_date = pd.to_datetime(sales.order_date.min()).date()
        hi_date = pd.to_datetime(sales.order_date.max()).date()
        date_res = st.date_input("Date range", (lo_date, hi_date))
        if isinstance(date_res, (tuple, list)):
            if len(date_res) == 2:
                d1, d2 = date_res
            elif len(date_res) == 1:
                d1 = d2 = date_res[0]
            else:
                d1, d2 = lo_date, hi_date
        else:
            d1 = d2 = date_res

    order_dates = pd.to_datetime(sales.order_date).dt.date
    f = sales[sales.category.isin(cats) & sales.region.isin(regs) & (order_dates >= d1) & (order_dates <= d2)]

    orders = f.order_id.nunique()
    k = st.columns(4)
    k[0].metric("Total Revenue", f"₹{f.revenue.sum():,.0f}")
    k[1].metric("Orders Processed", f"{orders:,}")
    k[2].metric("Active Customers", f"{f.customer_id.nunique():,}")
    k[3].metric("Avg Order Value", f"₹{(f.revenue.sum() / max(orders, 1)):,.0f}")

    t0, t1, t2 = st.tabs(["Business Insights", "Sales Performance (Plotly)", "Customer RFM Matrix"])

    with t0:
        st.subheader("Fortune 100 Client Business Insights")
        mon = q("SELECT * FROM v_monthly_revenue")
        cat = q("SELECT * FROM v_category_performance").sort_values("revenue", ascending=False)
        rfm_all = q("SELECT * FROM v_customer_rfm")
        mon["yr"], mon["mo"] = mon.order_month.str[:4], mon.order_month.str[5:]
        yoy = mon.groupby("yr").revenue.sum()
        peak = mon[mon.mo.isin(["11", "12"])].revenue.mean() / mon[~mon.mo.isin(["11", "12"])].revenue.mean()
        champ = rfm_all[rfm_all.segment == "Champions"]

        st.markdown(f"""
1. **Revenue Drivers**: **{cat.iloc[0].category}** generates **{cat.iloc[0].revenue_share_pct}%** of revenue.
2. **YoY Growth**: Revenue moved from ₹{yoy.iloc[0]:,.0f} ({yoy.index[0]}) to ₹{yoy.iloc[-1]:,.0f} ({yoy.index[-1]}), demonstrating **{(yoy.iloc[-1] / yoy.iloc[0] - 1) * 100:+.1f}%** growth.
3. **Q4 Seasonality**: Nov–Dec demand spikes **{peak:.2f}x** over baseline months.
4. **Customer Value**: **Champions** account for {len(champ) / len(rfm_all) * 100:.0f}% of customers but generate **{champ.monetary.sum() / rfm_all.monetary.sum() * 100:.0f}%** of revenue.
""")

    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Monthly Revenue Trend")
            df_mon = f.groupby("order_month").revenue.sum().reset_index()
            fig_mon = px.line(df_mon, x="order_month", y="revenue", title="Monthly Revenue Trend (₹)", markers=True)
            st.plotly_chart(fig_mon, use_container_width=True)
        with col2:
            st.subheader("Revenue by Category")
            df_cat = f.groupby("category").revenue.sum().reset_index()
            fig_cat = px.bar(df_cat, x="category", y="revenue", color="category", title="Category Sales Breakdown (₹)")
            st.plotly_chart(fig_cat, use_container_width=True)

    with t2:
        rfm = q("SELECT * FROM v_customer_rfm")
        rep = q("SELECT repeat_rate_pct FROM v_repeat_customers").iat[0, 0]
        st.metric("Repeat Customer Rate", f"{rep}%")
        fig_rfm = px.scatter(rfm, x="recency_days", y="monetary", color="segment", size="frequency",
                             hover_data=["customer_id"], title="Customer RFM Segmentation Matrix")
        st.plotly_chart(fig_rfm, use_container_width=True)


# ==========================================================
# 2. SAAS DOMAIN
# ==========================================================
elif domain == "SaaS Subscriptions":
    st.header("SaaS Subscription Analytics")
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
        fig_saas1 = px.bar(metrics, x="tier", y="total_mrr", color="tier", title="MRR by Plan Tier ($)")
        st.plotly_chart(fig_saas1, use_container_width=True)
    with col2:
        fig_saas2 = px.pie(metrics, values="total_customers", names="tier", title="Subscriber Tier Distribution")
        st.plotly_chart(fig_saas2, use_container_width=True)


# ==========================================================
# 3. HEALTHCARE DOMAIN (SERVER-ENFORCED PII MASKING)
# ==========================================================
elif domain == "Healthcare SLA & Claims":
    st.header("Healthcare Claim SLA & Patient Analytics")

    # Viewer Role PII Masking Enforcement: Toggle is hidden for Viewer role
    if user_role == "Viewer":
        mask_pii = True
        st.info("🔒 Server-Enforced PII Masking: Patient identities are masked for Viewer role.")
    else:
        mask_pii = st.sidebar.checkbox("Mask Sensitive Patient PII", value=True)

    hc_raw = q("SELECT * FROM fact_healthcare_claims")
    hc_sla = q("SELECT * FROM v_healthcare_sla")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Claims Ingested", f"{len(hc_raw):,}")
    c2.metric("Avg Claim Value", f"${hc_raw.claim_amount.mean():,.2f}")
    c3.metric("Avg Processing Hours", f"{hc_raw.processing_hours.mean():.1f} hrs")
    c4.metric("Overall SLA Breach Rate", f"{(hc_raw[hc_raw.processing_hours > 24].shape[0] / len(hc_raw) * 100):.1f}%")

    fig_hc = px.bar(hc_sla, x="claim_type", y="sla_breach_pct", color="claim_type", title="SLA Breach Rate (%) (>24 Hours)")
    st.plotly_chart(fig_hc, use_container_width=True)

    if mask_pii:
        hc_display = hc_raw.copy()
        hc_display["patient_id"] = "PAT_REDACTED_" + hc_display["patient_id"].astype(str).str[-3:]
        st.subheader("Patient Claims (PII Masked)")
        st.dataframe(hc_display.head(20), hide_index=True)
    else:
        st.subheader("Patient Claims (Unmasked Raw View)")
        st.dataframe(hc_raw.head(20), hide_index=True)


# ==========================================================
# 4. HI-TECH TELEMETRY
# ==========================================================
elif domain == "Hi-Tech Cloud Telemetry":
    st.header("Hi-Tech Microservice Telemetry & Infrastructure")
    ht = q("SELECT * FROM v_hitech_telemetry")
    ht_raw = q("SELECT * FROM fact_hitech_telemetry")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Microservice Logs Ingested", f"{len(ht_raw):,}")
    c2.metric("Avg API Latency", f"{ht_raw.latency_ms.mean():.2f} ms")
    c3.metric("Total Infra Compute Cost", f"${ht_raw.compute_cost.sum():,.2f}")
    c4.metric("Total System Errors", f"{ht_raw.error_count.sum():,}")

    fig_ht = px.bar(ht, x="service_name", y="avg_latency_ms", color="service_name", title="Microservice API Response Latency (ms)")
    st.plotly_chart(fig_ht, use_container_width=True)


# ==========================================================
# DATA OPS SCORECARD, RECONCILIATION & GENAI TABS
# ==========================================================
st.divider()

# RBAC Controls for Footer Tabs
if user_role == "Viewer":
    st.info("ℹ️ Login as Analyst or Admin to access GenAI Text-to-SQL Assistant & Data Quality Audit Scorecard.")
else:
    t_genai, t_ops = st.tabs(["🤖 Ask Your Data (GenAI Assistant)", "⚙️ Data Ops & Row-Count Reconciliation"])

    with t_genai:
        st.subheader("Generative AI Query Engine (Google Gemini)")
        st.write("Convert business questions into validated SQL queries executed securely against the database.")
        user_q = st.text_input("Enter business question (e.g. Which region had the highest revenue?)")
        if user_q:
            try:
                from genai.engine import generate_and_validate_sql
                res = generate_and_validate_sql(user_q, engine)
                if res["status"] == "success":
                    st.code(res["sql"], language="sql")
                    st.dataframe(pd.DataFrame(res["data"]), hide_index=True)
                elif res["status"] == "warning":
                    st.info(res["message"])
                else:
                    st.error(res["message"])
            except Exception as e:
                st.error(f"GenAI execution error: {e}")

    with t_ops:
        st.subheader("Row-Count Reconciliation & Pipeline Accounting")
        runs = q("SELECT * FROM pipeline_runs ORDER BY run_at DESC LIMIT 5")
        st.dataframe(runs, hide_index=True)

        if user_role == "Admin":
            if st.button("Trigger Manual Pipeline Run 🚀"):
                import pipeline
                r = pipeline.run()
                st.success(f"Pipeline executed successfully! Reconciled: {r['reconciled']}")
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Quarantine Dead-Letter Queue (DLQ)")
            try:
                quarantine = q("SELECT * FROM quarantine_records ORDER BY quarantined_at DESC LIMIT 10")
                st.dataframe(quarantine, hide_index=True)
            except Exception:
                st.info("No quarantine records logged.")
        with col2:
            st.subheader("GenAI Query Audit Log")
            try:
                audit = q("SELECT * FROM genai_query_audit ORDER BY queried_at DESC LIMIT 10")
                st.dataframe(audit, hide_index=True)
            except Exception:
                st.info("No GenAI audit logs recorded yet.")
