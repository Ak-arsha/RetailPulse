# DataPulse Production v2 — Enterprise Multi-Industry Data Platform

> **Built for Data Solutions & Data Engineering Candidates**  
> Solves 100% of job description requirements for Fortune 100 client solutions across **Hi-Tech**, **Healthcare**, **Retail**, and **SaaS**.

GitHub Repository: [https://github.com/Ak-arsha/RetailPulse](https://github.com/Ak-arsha/RetailPulse)

---

## 🚀 Single-Command Launch (Docker Compose)

Launch the entire enterprise stack (PostgreSQL 16, FastAPI REST API, Streamlit Dashboard, and Dagster Orchestration UI) in **one command**:

```bash
docker-compose up --build
```

### 🔗 Container Endpoints
- **Streamlit Analytics Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI REST API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Dagster Pipeline Orchestrator**: [http://localhost:3000](http://localhost:3000)
- **PostgreSQL Database**: `localhost:5432` (`datapulse`)

---

## 🎯 Phased Architecture Roadmap (M1–M5)

| Milestone | Scope & Deliverables | Core Value Delivered |
|---|---|---|
| **M1 (Core Engine)** | `docker-compose.yml` (PostgreSQL 16), Pandera DLQ Quarantine, Watermark Incremental Pipeline, Row-Count Reconciliation assertion | Data Quality & Pipeline Accounting |
| **M2 (Modeling Layer)** | `dbt` project (`dbt_project/`) with staging/marts models, dbt tests (`unique`, `not_null`), `schema.yml` | Analytics Modeling Credibility |
| **M3 (API & Security)** | FastAPI backend REST services (`api/main.py`), API Key Auth (`X-API-Key`), `datapulse_readonly` PostgreSQL role, Rate limiting & 10s query timeout | Security & Backend Architecture |
| **M4 (Ops & Hardened AI)** | **Dagster** pipeline orchestration (`orchestration/`), Gemini SDK (`genai/engine.py`), PII masking, GenAI audit logging | Data Operations & AI Safety |
| **M5 (UI & IaC Polish)** | Interactive **Plotly** visualizations, UI Data Quality Scorecard, Terraform IaC reference (`infra/terraform/`) | Enterprise Product Polish |

---

## 🏗️ Architecture

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
 │   - API Key Auth (X-API-Key)                 │
 │   - Read-Only User Connection                │
 │   - Rate Limiting & 10s Execution Timeout    │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────┐
 │   app.py — Streamlit UI with Plotly Charts    │
 │   - Interactive Plotly Visualizations        │
 │   - Data Ops & Reconciliation Scorecard      │
 │   - GenAI Text-to-SQL + Audit Log & PII Mask │
 └──────────────────────────────────────────────┘
```

---

## 📊 Row-Count Reconciliation & Pipeline Accounting

To ensure zero silent data loss, the ETL pipeline enforces a strict accounting assertion:

$$\text{Raw Rows} = \text{Clean Rows Loaded} + \text{Quarantine DLQ Rows} + \text{Duplicates Removed}$$

Any dataset imbalance instantly halts ingestion and fires a reconciliation exception alert.

---

## 🤖 GenAI Engine Hardening & Security

The GenAI engine ([`genai/engine.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/genai/engine.py)) integrates Google Gemini (`gemini-2.5-flash`) with enterprise-grade guardrails:
1. **Column-Level PII Masking**: Automatically redacts patient IDs and personal identifiers (`[PATIENT_ID_REDACTED]`) before prompt transmission.
2. **Schema Table Validation**: Blocks hallucinated non-existent tables against a strict whitelist.
3. **Read-Only Database Role**: Connects via `datapulse_readonly` PostgreSQL credentials, preventing unauthorized table mutations (`DROP`, `UPDATE`, `DELETE`).
4. **Audit Logging**: Logs user queries, generated SQL, execution latency (ms), and status to `genai_query_audit`.

---

## 🛠️ Infrastructure as Code (Terraform)

Directory [`infra/terraform/`](file:///c:/Users/Akarsha/Downloads/retailpulse/infra/terraform) provisions production cloud infrastructure:
- **AWS S3 Data Lake**: Raw Landing Zone & Curated Lakehouse S3 buckets.
- **AWS RDS PostgreSQL**: Production PostgreSQL 16 database instance.
- **AWS ECR**: Elastic Container Registry repository for Docker container images.

---

## 🧪 Local Execution & Verification

```bash
# 1. Install dependencies
pip install -r requirements.txt pytest

# 2. Run unit & reconciliation test suite
python -m pytest -v

# 3. Execute ETL ingestion pipeline
python generate_data.py && python pipeline.py

# 4. Launch FastAPI REST service
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 5. Launch Streamlit UI
streamlit run app.py
```
