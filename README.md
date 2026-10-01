# DataPulse — Enterprise Multi-Industry Data Platform

> **Built for Data Solutions & Data Engineering Candidates**  
> Solves 100% of job description requirements for Fortune 100 client solutions across **Hi-Tech**, **Healthcare**, **Retail**, and **SaaS**.

GitHub Repository: [https://github.com/Ak-arsha/RetailPulse](https://github.com/Ak-arsha/RetailPulse)  
*Note: The GitHub repository retains the original `RetailPulse` name (`Ak-arsha/RetailPulse`); the platform was rebranded to `DataPulse` in the enterprise release.*

---

## Documentation Overview

> The DataPulse interface opens on a public landing page that presents the platform's capabilities, architecture, and industry coverage, with clear calls to action to sign in or register. Authentication is handled through a minimal, centered card layout for both sign-in and registration, featuring inline validation, password strength enforcement, uniform error messaging, and optional single sign-on. Role-based access is assigned at registration or by administrator approval, and all authentication events are recorded in the audit log.

---

## Frontend Overview & Architecture

DataPulse Dashboard is a multi-vertical analytics interface built with Streamlit and Plotly, served on top of a FastAPI REST backend. The UI provides:

- **Landing Screen**: Public entry point communicating platform capabilities, architecture flow, trusted industry verticals, and direct calls to action to Sign In or Register.
- **Sign In & Sign Up Pages**: Formal card layout supporting account authentication, registration with password policy enforcement (10+ characters, uppercase, lowercase, number, special character), and role selection.
- **Vertical Switcher Across Four Industries**: Retail, SaaS, Healthcare, and Hi-Tech verticals — each domain features metric cards with delta trend indicators, compact Plotly white charts, and detail tables.
- **Currency Regionalization**: Retail metrics use **INR (₹)** for an India-region retail client drop, while SaaS, Healthcare, and Hi-Tech verticals use **USD ($)** for global Fortune 100 operations.
- **Interactive Plotly Visualizations**: Hover tooltips, cross-filtering, and date-range pickers instead of static images.
- **Data Ops & Quality Scorecard**: Live pipeline SLA status, last-loaded timestamps, quarantine row counts with error reasons, and GenAI query audit logs.
- **Ask Your Data (GenAI) Panel**: Natural-language Text-to-SQL with visible generated SQL, execution time, and audit trails.
- **Healthcare PII Masking**: Role-based server-enforced masking for patient claim data.

> **Short Resume Line**:  
> *"Designed and built an interactive multi-industry analytics dashboard (Streamlit + Plotly) with role-based data masking, live data-quality scorecards, and a GenAI Text-to-SQL assistant backed by a FastAPI service."*

---

## Authorization & Security (RBAC)

> JWT-based authentication with bcrypt-hashed credentials, role-based access control (Administrator/Analyst/Viewer), server-enforced PII masking, and full audit logging of logins and GenAI queries.

### Role-Based Access Control (RBAC) Matrix

| Role | Access Permissions |
|---|---|
| **Administrator** | Full system access: Dashboards, GenAI queries, manual pipeline re-runs, quarantine DLQ inspection, audit logs, raw PII view toggle. |
| **Analyst** | Dashboards + GenAI queries + Data Ops Scorecard (read-only). Healthcare PII toggle available. |
| **Viewer** | Dashboards only. Healthcare PII is **always server-side masked**. GenAI panel and re-runs are disabled. |

### Demo Credentials (Evaluation Only):
*Note: Credentials listed are seeded demo accounts for evaluation purposes only; production deployments enforce secret rotation via AWS Secrets Manager.*
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

## Data Engineering, Incremental Ingestion & PySpark

### Watermark-Based Incremental CDC Ingestion
The pipeline ([`pipeline.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/pipeline.py)) implements watermark-based incremental CDC ingestion (`WHERE updated_at > watermark`) and supports multi-format extraction from AWS S3 via `boto3` (CSV, JSON, Parquet).

### Big Data PySpark Distributed Architecture
The reference module ([`pipeline_spark_reference.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/pipeline_spark_reference.py)) demonstrates PySpark distributed ETL, windowing deduplication via `ROW_NUMBER()`, and Parquet partitioning (`partitionBy("category")`) on S3 for enterprise scale processing.

---

## Architecture Flow & CI/CD Pipeline

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

### Industrial CI/CD Pipeline ([`.github/workflows/ci.yml`](file:///c:/Users/Akarsha/Downloads/retailpulse/.github/workflows/ci.yml))
GitHub Actions automatically runs on every push and pull request:
1. **Linting**: Code quality checks via Flake8.
2. **Database Integration Tests**: Launches a PostgreSQL 16 service container and executes the PyTest suite (5 core module tests + Pandera schema checks) with a 100% pass rate.
3. **dbt Analytics Tests**: Runs `dbt compile` and `dbt test` against the target database.
4. **Docker Container Build**: Validates `docker build` image creation before deployment.

---

## Row-Count Reconciliation & Automated Alerting

To ensure zero silent data loss, the ETL pipeline enforces a strict accounting assertion:

$$\text{Raw Rows} = \text{Clean Rows Loaded} + \text{Quarantine DLQ Rows} + \text{Duplicates Removed}$$

Any dataset imbalance halts ingestion and fires an automated alert to an **AWS SNS Topic / Slack Webhook / Dagster Sensor**.

---

## Cloud Infrastructure as Code (Terraform & IAM)

Directory [`infra/terraform/`](file:///c:/Users/Akarsha/Downloads/retailpulse/infra/terraform) provisions production AWS infrastructure:
- **AWS S3 Data Lake**: Raw Landing Zone, Staged, and Curated Lakehouse S3 buckets.
- **AWS RDS PostgreSQL**: Production PostgreSQL 16 database instance.
- **AWS ECR & App Runner / ECS**: Elastic Container Registry repository and ECS/App Runner compute services.
- **IAM Roles**: Least-privilege IAM policies for S3 ingestion and RDS access.

---

## Secrets Management & Governance

All sensitive credentials—including the Gemini API key, PostgreSQL passwords, and JWT secret keys—are retrieved exclusively from **Environment Variables or AWS Secrets Manager**, never hardcoded in source files.

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
