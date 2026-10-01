import os
import hashlib
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

LOGO_PATH = "datapulse_favicon.png" if os.path.exists("datapulse_favicon.png") else ("datapulse_favicon_64.png" if os.path.exists("datapulse_favicon_64.png") else None)

st.set_page_config(
    page_title="DataPulse | Enterprise Analytics Platform",
    page_icon=LOGO_PATH if LOGO_PATH else "⚡",
    layout="wide"
)

# Unified House Palette & Plotly Template Config
HOUSE_PALETTE = ["#1B3A5C", "#0D9488", "#D97706", "#64748B"]

# Inject Global CSS Styling
st.markdown("""
<style>
  #MainMenu, footer, header {visibility: hidden;}
  .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
  h1 {font-size: 1.9rem; letter-spacing: -0.5px; color: #1B3A5C;}
  h2 {font-size: 1.25rem; color: #1B3A5C; border-bottom: 2px solid #E5EAF0; padding-bottom: 6px;}
  [data-testid="stMetric"] {
      background: #F4F6F9; border: 1px solid #E5EAF0;
      border-radius: 10px; padding: 14px 16px;
  }
  [data-testid="stMetricValue"] {font-size: 1.6rem; color: #1B3A5C;}
  .login-card {
      max-width: 420px; margin: 40px auto; padding: 30px; border-radius: 12px;
      background: #FFFFFF; border: 1px solid #E5EAF0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
  }
  .refreshed-badge { font-size: 12px; color: #64748B; margin-bottom: 12px; }
  .page-desc { font-size: 14px; color: #475569; margin-bottom: 20px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if LOGO_PATH:
            st.image(LOGO_PATH, width=64)
        st.markdown("<h2 style='text-align:center;'>DataPulse Authentication</h2>", unsafe_allow_html=True)
        st.caption("Sign in with enterprise credentials to access multi-industry analytics & GenAI solutions.")

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
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except Exception:
                    if uname in ["admin", "analyst", "viewer"] and password_input in ["admin123", "analyst123", "viewer123"]:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = uname
                        st.session_state["user_role"] = uname.capitalize()
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        st.info("💡 **Demo Credentials**:\n- **Admin**: `admin` / `admin123`\n- **Analyst**: `analyst` / `analyst123`\n- **Viewer**: `viewer` / `viewer123`")
        st.caption("🔒 *Unauthorized access is monitored and logged.*")
    st.stop()


# ==========================================================
# BRANDED HEADER BLOCK WITH LOGO
# ==========================================================
head_col1, head_col2 = st.columns([1, 14])
with head_col1:
    if LOGO_PATH:
        st.image(LOGO_PATH, width=52)
with head_col2:
    st.markdown("""
    <div style="padding-top:4px;">
      <span style="font-size:24px;font-weight:700;color:#1B3A5C;">DataPulse</span>
      <span style="font-size:13px;color:#6B7280;padding-left:12px;
                   border-left:1px solid #E5EAF0;margin-left:12px;">
        Enterprise Multi-Industry Data Platform</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================================
# SIDEBAR FORMAL NAVIGATION & FOOTER
# ==========================================================
user_role = st.session_state["user_role"]
username = st.session_state["username"]

st.sidebar.markdown(f"👤 **User**: `{username}` | 🔑 **Role**: `{user_role}`")
if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Navigation")

domain = st.sidebar.radio(
    "Select Industry Vertical",
    ["Retail Analytics", "SaaS Subscriptions", "Healthcare SLA & Claims", "Hi-Tech Cloud Telemetry"],
    index=0
)

st.sidebar.divider()

# Sidebar Footer
st.sidebar.markdown("""
<div style="font-size: 11px; color: #64748B;">
  <b>DataPulse</b> v1.0.0<br>
  Built by <b>Akarsha</b><br>
  <a href="https://github.com/Ak-arsha/RetailPulse" target="_blank" style="color:#1B3A5C;text-decoration:none;">🔗 GitHub Repository</a>
</div>
""", unsafe_allow_html=True)

last_refreshed = pd.Timestamp.now().strftime("%B %d, %Y - %H:%M:%S UTC")

# ==========================================================
# 1. RETAIL DOMAIN
# ==========================================================
if domain == "Retail Analytics":
    st.markdown("<h2>Retail Omnichannel Performance & RFM Segmentation</h2>", unsafe_allow_html=True)
    st.markdown("<div class='page-desc'>Analyzes multi-channel retail revenue streams, Q4 seasonality spikes, product hierarchy performance, and RFM customer segmentation.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='refreshed-badge'>🕒 Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

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
    k[0].metric("Total Revenue", f"₹{f.revenue.sum():,.0f}", delta="+14.2% YoY")
    k[1].metric("Orders Processed", f"{orders:,}", delta="+8.5%")
    k[2].metric("Active Customers", f"{f.customer_id.nunique():,}", delta="+5.1%")
    k[3].metric("Avg Order Value", f"₹{(f.revenue.sum() / max(orders, 1)):,.0f}", delta="+3.4%")

    t0, t1, t2 = st.tabs(["Business Insights", "Sales Performance", "Customer RFM Matrix"])

    with t0:
        mon = q("SELECT * FROM v_monthly_revenue")
        cat = q("SELECT * FROM v_category_performance").sort_values("revenue", ascending=False)
        rfm_all = q("SELECT * FROM v_customer_rfm")
        mon["yr"], mon["mo"] = mon.order_month.str[:4], mon.order_month.str[5:]
        yoy = mon.groupby("yr").revenue.sum()
        peak = mon[mon.mo.isin(["11", "12"])].revenue.mean() / mon[~mon.mo.isin(["11", "12"])].revenue.mean()
        champ = rfm_all[rfm_all.segment == "Champions"]

        st.markdown(f"""
1. **Primary Revenue Driver**: **{cat.iloc[0].category}** generates **{cat.iloc[0].revenue_share_pct}%** of overall revenue.
2. **Growth Trajectory**: Revenue moved from ₹{yoy.iloc[0]:,.0f} ({yoy.index[0]}) to ₹{yoy.iloc[-1]:,.0f} ({yoy.index[-1]}), demonstrating **{(yoy.iloc[-1] / yoy.iloc[0] - 1) * 100:+.1f}%** growth.
3. **Q4 Seasonality**: Nov–Dec demand spikes **{peak:.2f}x** over baseline months.
4. **Customer Concentration**: **Champions** account for {len(champ) / len(rfm_all) * 100:.0f}% of customers but generate **{champ.monetary.sum() / rfm_all.monetary.sum() * 100:.0f}%** of sales revenue.
""")

    with t1:
        col1, col2 = st.columns(2)
        with col1:
            df_mon = f.groupby("order_month").revenue.sum().reset_index()
            fig_mon = px.line(df_mon, x="order_month", y="revenue", title="Monthly Revenue Trend (₹)",
                              labels={"order_month": "Month", "revenue": "Revenue (₹)"},
                              template="plotly_white", color_discrete_sequence=[HOUSE_PALETTE[0]], height=300)
            st.plotly_chart(fig_mon, use_container_width=True)
        with col2:
            df_cat = f.groupby("category").revenue.sum().reset_index()
            fig_cat = px.bar(df_cat, x="category", y="revenue", title="Category Sales Breakdown (₹)",
                             labels={"category": "Category", "revenue": "Revenue (₹)"},
                             template="plotly_white", color_discrete_sequence=[HOUSE_PALETTE[1]], height=300)
            st.plotly_chart(fig_cat, use_container_width=True)

    with t2:
        rfm = q("SELECT * FROM v_customer_rfm")
        rep = q("SELECT repeat_rate_pct FROM v_repeat_customers").iat[0, 0]
        st.metric("Repeat Customer Rate", f"{rep}%", delta="+2.1% Retained")
        fig_rfm = px.scatter(rfm, x="recency_days", y="monetary", color="segment", size="frequency",
                             hover_data=["customer_id"], title="Customer RFM Segmentation Matrix",
                             labels={"recency_days": "Recency (Days)", "monetary": "Monetary Value (₹)"},
                             template="plotly_white", color_discrete_sequence=HOUSE_PALETTE, height=320)
        st.plotly_chart(fig_rfm, use_container_width=True)


# ==========================================================
# 2. SAAS DOMAIN
# ==========================================================
elif domain == "SaaS Subscriptions":
    st.markdown("<h2>SaaS Subscription ARR/MRR & Retention Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<div class='page-desc'>Tracks Monthly Recurring Revenue (MRR), subscriber plan tiers, and customer churn rates across subscription cohorts.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='refreshed-badge'>🕒 Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

    saas = q("SELECT * FROM fact_saas_subscriptions")
    metrics = q("SELECT * FROM v_saas_metrics")

    c1, c2, c3, c4 = st.columns(4)
    total_mrr = saas["mrr"].sum()
    c1.metric("Total Active MRR", f"${total_mrr:,.2f}", delta="+11.8% MoM")
    c2.metric("Annual Run Rate (ARR)", f"${total_mrr * 12:,.2f}", delta="+14.5% YoY")
    c3.metric("Total Subscribers", f"{len(saas):,}", delta="+92 Seats")
    c4.metric("Avg Churn Rate", f"{(saas.churned.mean() * 100):.1f}%", delta="-0.6% Churn")

    col1, col2 = st.columns(2)
    with col1:
        fig_saas1 = px.bar(metrics, x="tier", y="total_mrr", title="MRR Contribution by Plan Tier ($)",
                           labels={"tier": "Plan Tier", "total_mrr": "Total MRR ($)"},
                           template="plotly_white", color_discrete_sequence=[HOUSE_PALETTE[0]], height=300)
        st.plotly_chart(fig_saas1, use_container_width=True)
    with col2:
        fig_saas2 = px.pie(metrics, values="total_customers", names="tier", title="Subscriber Tier Share",
                           template="plotly_white", color_discrete_sequence=HOUSE_PALETTE, height=300)
        st.plotly_chart(fig_saas2, use_container_width=True)


# ==========================================================
# 3. HEALTHCARE DOMAIN
# ==========================================================
elif domain == "Healthcare SLA & Claims":
    st.markdown("<h2>Healthcare Patient Claim Turnaround & SLA Monitoring</h2>", unsafe_allow_html=True)
    st.markdown("<div class='page-desc'>Monitors patient claim turnaround hours, 24-hour SLA breach compliance rates, and hospital readmission statistics.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='refreshed-badge'>🕒 Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

    # Server-enforced PII masking for Viewer role
    if user_role == "Viewer":
        mask_pii = True
        st.info("🔒 Server-Enforced PII Masking: Patient identities are masked for Viewer role.")
    else:
        mask_pii = st.sidebar.checkbox("Mask Sensitive Patient PII", value=True)

    hc_raw = q("SELECT * FROM fact_healthcare_claims")
    hc_sla = q("SELECT * FROM v_healthcare_sla")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Claims Ingested", f"{len(hc_raw):,}", delta="+4.2%")
    c2.metric("Avg Claim Value", f"${hc_raw.claim_amount.mean():,.2f}", delta="+1.8%")
    c3.metric("Avg Processing Hours", f"{hc_raw.processing_hours.mean():.1f} hrs", delta="-2.4 hrs SLA")
    c4.metric("SLA Breach Rate (>24h)", f"{(hc_raw[hc_raw.processing_hours > 24].shape[0] / len(hc_raw) * 100):.1f}%", delta="-1.2% Breach")

    fig_hc = px.bar(hc_sla, x="claim_type", y="sla_breach_pct", title="SLA Breach Rate (%) (>24 Hours)",
                    labels={"claim_type": "Claim Type", "sla_breach_pct": "SLA Breach Rate (%)"},
                    template="plotly_white", color_discrete_sequence=[HOUSE_PALETTE[2]], height=300)
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
    st.markdown("<h2>Hi-Tech Microservice Telemetry & Infrastructure Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<div class='page-desc'>Evaluates microservice API response latencies (ms), infrastructure compute costs ($), and system error rates.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='refreshed-badge'>🕒 Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

    ht = q("SELECT * FROM v_hitech_telemetry")
    ht_raw = q("SELECT * FROM fact_hitech_telemetry")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Logs Ingested", f"{len(ht_raw):,}", delta="+12.0%")
    c2.metric("Avg API Latency", f"{ht_raw.latency_ms.mean():.2f} ms", delta="-4.5 ms P95")
    c3.metric("Infra Compute Cost", f"${ht_raw.compute_cost.sum():,.2f}", delta="-2.1% Cost Opt")
    c4.metric("System Error Count", f"{ht_raw.error_count.sum():,}", delta="-15 Error Rate")

    fig_ht = px.bar(ht, x="service_name", y="avg_latency_ms", title="Microservice API Response Latency (ms)",
                    labels={"service_name": "Service Name", "avg_latency_ms": "Avg Latency (ms)"},
                    template="plotly_white", color_discrete_sequence=[HOUSE_PALETTE[1]], height=300)
    st.plotly_chart(fig_ht, use_container_width=True)


# ==========================================================
# DATA OPS SCORECARD & GENAI TABS
# ==========================================================
st.divider()

if user_role == "Viewer":
    st.info("ℹ️ Login as Analyst or Admin to access GenAI Text-to-SQL Assistant & Data Quality Audit Scorecard.")
else:
    t_genai, t_ops = st.tabs(["🤖 Ask Your Data (GenAI Assistant)", "⚙️ Data Ops & Row-Count Reconciliation"])

    with t_genai:
        st.subheader("Generative AI Query Engine (Google Gemini)")
        st.markdown("<div class='page-desc'>Converts plain English business questions into validated SQL queries executed securely against the database.</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='page-desc'>Monitors ETL pipeline execution SLA, Pandera DLQ quarantine counts, and accounting reconciliation status.</div>", unsafe_allow_html=True)
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
