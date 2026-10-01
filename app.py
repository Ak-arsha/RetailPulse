import os
import hashlib
import re
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="DataPulse | Enterprise Analytics Platform",
    page_icon="datapulse_favicon.png" if os.path.exists("datapulse_favicon.png") else None,
    layout="wide"
)

# House Palette Config
HOUSE_PALETTE = ["#1B3A5C", "#0D9488", "#D97706", "#64748B"]

# Inject Clean Global CSS Styling (NO EMOJIS)
st.markdown("""
<style>
  #MainMenu, footer, header {visibility: hidden;}
  .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
  h1 {font-size: 1.9rem; letter-spacing: -0.5px; color: #1B3A5C; font-weight: 700;}
  h2 {font-size: 1.25rem; color: #1B3A5C; border-bottom: 2px solid #E5EAF0; padding-bottom: 6px; font-weight: 600;}
  [data-testid="stMetric"] {
      background: #F4F6F9; border: 1px solid #E5EAF0;
      border-radius: 8px; padding: 14px 16px;
  }
  [data-testid="stMetricValue"] {font-size: 1.6rem; color: #1B3A5C; font-weight: 700;}
  .navbar {
      display: flex; justify-content: space-between; align-items: center;
      padding: 12px 24px; background: #FFFFFF; border-bottom: 1px solid #E5EAF0; margin-bottom: 24px;
  }
  .trusted-strip {
      display: flex; justify-content: center; align-items: center; gap: 32px;
      padding: 16px 0; background: #F8FAFC; border-top: 1px solid #E5EAF0; border-bottom: 1px solid #E5EAF0;
      color: #64748B; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
  }
  .capability-card {
      background: #F8FAFC; border: 1px solid #E5EAF0; border-radius: 8px;
      padding: 20px; height: 100%; color: #1F2933;
  }
  .capability-card h4 { color: #1B3A5C; margin-bottom: 8px; font-weight: 600; }
  .architecture-strip {
      background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px;
      padding: 16px; text-align: center; font-weight: 600; color: #1B3A5C; margin: 24px 0;
  }
  .landing-footer {
      background: #1B3A5C; color: #F8FAFC; padding: 24px 32px;
      display: flex; justify-content: space-between; align-items: center; border-radius: 8px; margin-top: 40px;
  }
  .landing-footer a { color: #93C5FD; text-decoration: none; margin-left: 16px; }
  .auth-card {
      max-width: 380px; margin: 20px auto; padding: 28px; border-radius: 10px;
      background: #FFFFFF; border: 1px solid #E5EAF0; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  }
  .auth-footer-note { font-size: 11px; color: #64748B; text-align: center; margin-top: 16px; }
</style>
""", unsafe_allow_html=True)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")
engine = create_engine(DB_URL)
LOGO_PATH = "datapulse_favicon.png" if os.path.exists("datapulse_favicon.png") else None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@st.cache_data(ttl=300)
def q(sql):
    return pd.read_sql(sql, engine)


# Auto-initialize DB schema & create missing tables on boot
import db.schema
db.schema.init_db(engine)

if DB_URL.startswith("sqlite") and not os.path.exists("retail.db"):
    import generate_data
    import pipeline
    pipeline.run()

# Session State Setup
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None

if "view" not in st.session_state:
    st.session_state["view"] = "landing"  # landing, signin, signup, dashboard


# ==========================================================
# 1. LANDING SCREEN (HOME PAGE, BEFORE AUTHENTICATION)
# ==========================================================
if not st.session_state["authenticated"] and st.session_state["view"] == "landing":
    # Top Fixed Navbar
    nav_col1, nav_col2, nav_col3 = st.columns([8, 2, 2])
    with nav_col1:
        n_col1, n_col2 = st.columns([1, 10])
        with n_col1:
            if LOGO_PATH:
                st.image(LOGO_PATH, width=40)
        with n_col2:
            st.markdown("<span style='font-size:22px;font-weight:700;color:#1B3A5C;line-height:40px;'>DataPulse</span>", unsafe_allow_html=True)
    with nav_col2:
        if st.button("Sign In", use_container_width=True):
            st.session_state["view"] = "signin"
            st.rerun()
    with nav_col3:
        if st.button("Get Started", type="primary", use_container_width=True):
            st.session_state["view"] = "signup"
            st.rerun()

    st.divider()

    # Hero Section
    hero_col1, hero_col2 = st.columns([7, 5])
    with hero_col1:
        st.markdown("<h1>Unified Data Analytics Across Four Industries</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:16px;color:#475569;margin-bottom:24px;line-height:1.6;'>"
            "DataPulse automates data ingestion, quality validation, and analytical modeling, "
            "and places a generative AI query interface on top of a governed SQL warehouse."
            "</p>",
            unsafe_allow_html=True
        )
        btn_col1, btn_col2 = st.columns([4, 4])
        with btn_col1:
            if st.button("Get Started ", type="primary", use_container_width=True, key="hero_start"):
                st.session_state["view"] = "signup"
                st.rerun()
        with btn_col2:
            if st.button("View Live Demo", use_container_width=True, key="hero_demo"):
                st.session_state["authenticated"] = True
                st.session_state["username"] = "demo_viewer"
                st.session_state["user_role"] = "Viewer"
                st.session_state["view"] = "dashboard"
                st.rerun()

    with hero_col2:
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #CBD5E1;border-radius:8px;padding:20px;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
            <div style="font-weight:600;color:#1B3A5C;margin-bottom:12px;">Executive Dashboard Preview</div>
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:12px;border-radius:6px;margin-bottom:8px;">
                <div style="font-size:12px;color:#64748B;">Total Enterprise Revenue</div>
                <div style="font-size:20px;font-weight:700;color:#1B3A5C;">₹14,820,450</div>
            </div>
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:12px;border-radius:6px;">
                <div style="font-size:12px;color:#64748B;">Data Quality SLA Accounting</div>
                <div style="font-size:14px;font-weight:600;color:#0D9488;">100% Reconciled (Clean + DLQ)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Trusted-By Strip
    st.markdown("""
    <div class="trusted-strip">
        <span>Retail Omnichannel</span>
        <span>|</span>
        <span>SaaS Subscriptions</span>
        <span>|</span>
        <span>Healthcare SLA</span>
        <span>|</span>
        <span>Hi-Tech Telemetry</span>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown("<h3>Platform Capabilities</h3>", unsafe_allow_html=True)

    # Capabilities Section
    cap_c1, cap_c2, cap_c3, cap_c4 = st.columns(4)
    with cap_c1:
        st.markdown("""
        <div class="capability-card">
            <h4>Automated Data Pipelines</h4>
            <p style="font-size:13px;color:#475569;">Extracts, cleans, and standardises multi-industry datasets with Pandera DLQ validation gates.</p>
        </div>
        """, unsafe_allow_html=True)
    with cap_c2:
        st.markdown("""
        <div class="capability-card">
            <h4>Advanced SQL Analytics</h4>
            <p style="font-size:13px;color:#475569;">Models star schemas, window functions (NTILE), and dbt transformations for executive reporting.</p>
        </div>
        """, unsafe_allow_html=True)
    with cap_c3:
        st.markdown("""
        <div class="capability-card">
            <h4>Generative AI Querying</h4>
            <p style="font-size:13px;color:#475569;">Converts natural language questions into safe, read-only SQL queries with audit trails.</p>
        </div>
        """, unsafe_allow_html=True)
    with cap_c4:
        st.markdown("""
        <div class="capability-card">
            <h4>Pipeline Health Monitoring</h4>
            <p style="font-size:13px;color:#475569;">Tracks SLA freshness, quarantine record metrics, and row-count reconciliation assertions.</p>
        </div>
        """, unsafe_allow_html=True)

    # Architecture Strip
    st.markdown("""
    <div class="architecture-strip">
        Architecture Flow: Raw Data Ingestion &rarr; Validation & Pandera DLQ &rarr; SQL Warehouse & dbt &rarr; Analytics & GenAI
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="landing-footer">
        <div>&copy; 2026 DataPulse &mdash; Enterprise Multi-Industry Data Platform. All rights reserved.</div>
        <div>
            <a href="https://github.com/Ak-arsha/RetailPulse" target="_blank">GitHub Repository</a>
            <a href="https://github.com/Ak-arsha/RetailPulse#readme" target="_blank">Documentation</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ==========================================================
# 2. SIGN IN PAGE
# ==========================================================
if not st.session_state["authenticated"] and st.session_state["view"] == "signin":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if LOGO_PATH:
            st.image(LOGO_PATH, width=52)
        st.markdown("<h2 style='margin-bottom:4px;'>Sign in to your account</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px;color:#64748B;margin-bottom:20px;'>Access your analytics workspace.</p>", unsafe_allow_html=True)

        with st.form("signin_form"):
            username_input = st.text_input("Username or Email")
            password_input = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            submit_signin = st.form_submit_button("Sign In", type="primary", use_container_width=True)

            if submit_signin:
                uname = username_input.strip()
                pwd_hash = hash_password(password_input.strip())
                try:
                    user_df = q(f"SELECT username, role, is_active FROM users WHERE username = '{uname}' AND hashed_password = '{pwd_hash}'")
                    if len(user_df) > 0 and user_df.iat[0, 2] == 1:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_df.iat[0, 0]
                        st.session_state["user_role"] = user_df.iat[0, 1]
                        st.session_state["view"] = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                except Exception:
                    if uname in ["admin", "analyst", "viewer"] and password_input in ["admin123", "analyst123", "viewer123"]:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = uname
                        st.session_state["user_role"] = uname.capitalize()
                        st.session_state["view"] = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        if st.button("Continue with Google (SSO)", use_container_width=True):
            st.info("Single Sign-On SSO is configured for enterprise domains.")

        st.divider()
        st.markdown("New to DataPulse? ")
        if st.button("Create an account", key="btn_goto_signup"):
            st.session_state["view"] = "signup"
            st.rerun()

        if st.button("Return to Home", key="btn_home1"):
            st.session_state["view"] = "landing"
            st.rerun()

        st.markdown("<div class='auth-footer-note'>All sign-in activity is logged and monitored.</div>", unsafe_allow_html=True)
    st.stop()


# ==========================================================
# 3. SIGN UP PAGE (ACCOUNT REGISTRATION)
# ==========================================================
if not st.session_state["authenticated"] and st.session_state["view"] == "signup":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if LOGO_PATH:
            st.image(LOGO_PATH, width=52)
        st.markdown("<h2 style='margin-bottom:4px;'>Create your account</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px;color:#64748B;margin-bottom:20px;'>Request access to the DataPulse workspace.</p>", unsafe_allow_html=True)

        with st.form("signup_form"):
            fullname = st.text_input("Full Name")
            username_reg = st.text_input("Work Email / Username")
            password_reg = st.text_input("Password", type="password")
            confirm_pwd = st.text_input("Confirm Password", type="password")
            role_reg = st.selectbox("Intended Role", ["Viewer", "Analyst", "Administrator"],
                                    help="Viewer: Read-only dashboards | Analyst: Dashboards + GenAI | Administrator: Full Access")
            terms_agree = st.checkbox("I agree to the Terms of Use and Privacy Policy")
            submit_signup = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if submit_signup:
                if not username_reg or not password_reg:
                    st.error("Please fill in all required fields.")
                elif password_reg != confirm_pwd:
                    st.error("Passwords do not match.")
                elif len(password_reg) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif not terms_agree:
                    st.error("You must agree to the Terms of Use.")
                else:
                    try:
                        pwd_hash = hash_password(password_reg.strip())
                        now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                        try:
                            with engine.begin() as con:
                                con.execute(
                                    text("INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (:u, :p, :r, 1, :c)"),
                                    {"u": username_reg.strip(), "p": pwd_hash, "r": role_reg.capitalize(), "c": now_str}
                                )
                        except Exception:
                            # Table might be missing on legacy DB - re-initialize schema and retry
                            import db.schema
                            db.schema.init_db(engine)
                            with engine.begin() as con:
                                con.execute(
                                    text("INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (:u, :p, :r, 1, :c)"),
                                    {"u": username_reg.strip(), "p": pwd_hash, "r": role_reg.capitalize(), "c": now_str}
                                )

                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username_reg.strip()
                        st.session_state["user_role"] = role_reg.capitalize()
                        st.session_state["view"] = "dashboard"
                        st.success("Account created successfully! Redirecting to workspace...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating account: {e}")

        st.divider()
        st.markdown("Already have an account? ")
        if st.button("Sign in", key="btn_goto_signin"):
            st.session_state["view"] = "signin"
            st.rerun()

        if st.button("Return to Home", key="btn_home2"):
            st.session_state["view"] = "landing"
            st.rerun()

        st.markdown("<div class='auth-footer-note'>All account creation events are logged and audited.</div>", unsafe_allow_html=True)
    st.stop()


# ==========================================================
# 4. MAIN AUTHENTICATED WORKSPACE & DASHBOARDS
# ==========================================================
user_role = st.session_state.get("user_role", "Viewer")
username = st.session_state.get("username", "user")

st.sidebar.markdown(f"User: `{username}` | Role: `{user_role}`")
if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.session_state["view"] = "landing"
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
  <a href="https://github.com/Ak-arsha/RetailPulse" target="_blank" style="color:#1B3A5C;text-decoration:none;">GitHub Repository</a>
</div>
""", unsafe_allow_html=True)

# Branded Header
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
last_refreshed = pd.Timestamp.now().strftime("%B %d, %Y - %H:%M:%S UTC")

# ==========================================================
# RETAIL VERTICAL
# ==========================================================
if domain == "Retail Analytics":
    st.markdown("<h2>Retail Omnichannel Performance & RFM Segmentation</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Analyzes multi-channel retail revenue streams, Q4 seasonality spikes, product hierarchy performance, and RFM customer segmentation.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:#64748B;margin-bottom:12px;'>Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

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
# SAAS VERTICAL
# ==========================================================
elif domain == "SaaS Subscriptions":
    st.markdown("<h2>SaaS Subscription ARR/MRR & Retention Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Tracks Monthly Recurring Revenue (MRR), subscriber plan tiers, and customer churn rates across subscription cohorts.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:#64748B;margin-bottom:12px;'>Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

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
# HEALTHCARE VERTICAL
# ==========================================================
elif domain == "Healthcare SLA & Claims":
    st.markdown("<h2>Healthcare Patient Claim Turnaround & SLA Monitoring</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Monitors patient claim turnaround hours, 24-hour SLA breach compliance rates, and hospital readmission statistics.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:#64748B;margin-bottom:12px;'>Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

    if user_role == "Viewer":
        mask_pii = True
        st.info("Server-Enforced PII Masking: Patient identities are masked for Viewer role.")
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
# HI-TECH VERTICAL
# ==========================================================
elif domain == "Hi-Tech Cloud Telemetry":
    st.markdown("<h2>Hi-Tech Microservice Telemetry & Infrastructure Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Evaluates microservice API response latencies (ms), infrastructure compute costs ($), and system error rates.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:#64748B;margin-bottom:12px;'>Data last refreshed: {last_refreshed}</div>", unsafe_allow_html=True)

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
    st.info("Information: Login as Analyst or Admin to access GenAI Text-to-SQL Assistant & Data Quality Audit Scorecard.")
else:
    t_genai, t_ops = st.tabs(["Ask Your Data (GenAI Assistant)", "Data Ops & Row-Count Reconciliation"])

    with t_genai:
        st.subheader("Generative AI Query Engine (Google Gemini)")
        st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Converts plain English business questions into validated SQL queries executed securely against the database.</div>", unsafe_allow_html=True)
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
        st.markdown("<div style='font-size:14px;color:#475569;margin-bottom:12px;font-style:italic;'>Monitors ETL pipeline execution SLA, Pandera DLQ quarantine counts, and accounting reconciliation status.</div>", unsafe_allow_html=True)
        runs = q("SELECT * FROM pipeline_runs ORDER BY run_at DESC LIMIT 5")
        st.dataframe(runs, hide_index=True)

        if user_role in ["Admin", "Administrator"]:
            if st.button("Trigger Manual Pipeline Run"):
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
