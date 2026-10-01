# DataPulse — Enterprise Multi-Industry Data Platform

> **Built for Data Solutions & Data Engineering Candidates**  
> Solves 100% of job description requirements for Fortune 100 client solutions across **Hi-Tech**, **Healthcare**, **Retail**, and **SaaS**.

GitHub Repository: [https://github.com/Ak-arsha/RetailPulse](https://github.com/Ak-arsha/RetailPulse)

---

## Documentation Overview

> The DataPulse interface opens on a public landing page that presents the platform's capabilities, architecture, and industry coverage, with clear calls to action to sign in or register. Authentication is handled through a minimal, centered card layout for both sign-in and registration, featuring inline validation, password strength enforcement, uniform error messaging, and optional single sign-on. Role-based access is assigned at registration or by administrator approval, and all authentication events are recorded in the audit log.

---

## Frontend Overview & Architecture

DataPulse Dashboard is a multi-vertical analytics interface built with Streamlit and Plotly, served on top of a FastAPI REST backend. The UI provides:

- **Landing Screen**: Public entry point communicating platform capabilities, architecture flow, trusted industry verticals, and direct calls to action to Sign In or Register.
- **Sign In & Sign Up Pages**: Formal card layout supporting account authentication, registration with password policy enforcement, and role selection.
- **Vertical Switcher Across Four Industries**: Retail, SaaS, Healthcare, and Hi-Tech verticals — each domain features metric cards with delta trend indicators, compact Plotly white charts, and detail tables.
- **Interactive Plotly Visualizations**: Hover tooltips, cross-filtering, and date-range pickers instead of static images.
- **Data Ops & Quality Scorecard**: Live pipeline SLA status, last-loaded timestamps, quarantine row counts with error reasons, and GenAI query audit logs.
- **Ask Your Data (GenAI) Panel**: Natural-language Text-to-SQL with visible generated SQL, execution time, and audit trails.
- **Healthcare PII Masking**: Role-based server-enforced masking for patient claim data.

---

## Authorization & Security (RBAC)

> JWT-based authentication with bcrypt-hashed credentials, role-based access control (Administrator/Analyst/Viewer), server-enforced PII masking, and full audit logging of logins and GenAI queries.

### Role-Based Access Control (RBAC) Matrix

| Role | Access Permissions |
|---|---|
| **Administrator** | Full system access: Dashboards, GenAI queries, manual pipeline re-runs, quarantine inspection, audit logs, raw PII view toggle. |
| **Analyst** | Dashboards + GenAI queries + Data Ops Scorecard (read-only). Healthcare PII toggle available. |
| **Viewer** | Dashboards only. Healthcare PII is **always server-side masked**. GenAI panel and re-runs are disabled. |

### Demo Credentials (Local / Cloud Test):
- **Admin**: Username `admin` | Password `admin123`
- **Analyst**: Username `analyst` | Password `analyst123`
- **Viewer**: Username `viewer` | Password `viewer123`

---

## Single-Command Local Launch (Docker Compose)

Launch the entire enterprise stack (PostgreSQL 16, FastAPI REST API, Streamlit Dashboard, and Dagster Orchestration UI) in **one command**:

```bash
docker-compose up --build
```

### Container Endpoints
- **Streamlit Analytics Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI REST API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Dagster Pipeline Orchestrator**: [http://localhost:3000](http://localhost:3000)
- **PostgreSQL Database**: `localhost:5432` (`datapulse`)

---

## Architecture Flow

```text
       RAW DATA DROP (AWS S3 / Local CSVs)
 ┌──────────────────────────────────────────────┐
 │ • Retail Orders  • SaaS Subscriptions        │
 │ • Healthcare SLA • Hi-Tech Cloud Telemetry   │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────┐
 │   pipeline.py — Pandera DLQ & Accounting     │
 │   - Validates data via Pandera Schemas       │
 │   - Routes invalid records to quarantine_dlq │
 │   - Asserts: raw == clean + quarantine + dup │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────┐
 │   POSTGRESQL 16 DATABASE (Star Schema)      │
 │   - Fact & Dimension Tables                  │
 │   - Role Security: datapulse_admin (Read/Write)│
 │                    datapulse_readonly (SELECT) │
 │   - Users & Auth Table (Admin/Analyst/Viewer)│
 └──────────────────────┬───────────────────────┘
                        │
                        ▼   dbt_project/ (dbt Models & Data Tests)
 ┌──────────────────────────────────────────────┐
 │   marts/ (v_customer_rfm, v_saas_metrics...) │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────┐
 │   api/main.py — FastAPI Backend REST Service │
 │   - JWT Auth & API Key Security (X-API-Key)  │
 │   - Read-Only User Connection                │
 │   - Rate Limiting & 10s Execution Timeout    │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────┐
 │   app.py — Streamlit UI with Landing & Auth  │
 │   - Public Landing Page & Sign In / Sign Up  │
 │   - Interactive Plotly Visualizations        │
 │   - Data Ops & Reconciliation Scorecard      │
 │   - GenAI Text-to-SQL + Audit Log & PII Mask │
 └──────────────────────────────────────────────┘
```

---

## Row-Count Reconciliation & Pipeline Accounting

To ensure zero silent data loss, the ETL pipeline enforces a strict accounting assertion:

$$\text{Raw Rows} = \text{Clean Rows Loaded} + \text{Quarantine DLQ Rows} + \text{Duplicates Removed}$$

Any dataset imbalance instantly halts ingestion and fires a reconciliation exception alert.

---

## Streamlit Community Cloud Deployment

To deploy your app live on Streamlit Cloud:

1. Log into **[share.streamlit.io](https://share.streamlit.io)** with GitHub.
2. Click **New app** -> Select repository **`Ak-arsha/RetailPulse`**, branch **`main`**, main file **`app.py`**.
3. Under **Advanced Settings -> Secrets**, add:
   ```toml
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
   ```
4. Click **Deploy**!

---

## Local Execution & Verification

```bash
# 1. Install dependencies
pip install -r requirements.txt pytest

# 2. Run unit & reconciliation test suite
python -m pytest -v

# 3. Execute ETL ingestion pipeline
python generate_data.py && python pipeline.py

# 4. Launch Streamlit UI
streamlit run app.py
```
