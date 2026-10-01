# DataPulse — Enterprise Multi-Industry Data Solutions & Analytics Engine

> **Built for Data Solutions Associate Intern Candidates**  
> Designed to match 100% of the job description requirements for Fortune 100 client solutions across **Hi-Tech**, **Healthcare**, **Retail**, and **SaaS**.

Live Demo: [DataPulse Streamlit App](https://share.streamlit.io/Ak-arsha/retailpulse/main/app.py) | Repository: [Ak-arsha/retailpulse](https://github.com/Ak-arsha/retailpulse)

---

## 🎯 How This Repository Fits the Job Description

| Job Description Requirement | Implementation in this Repository | Relevant File / Module |
|---|---|---|
| **Translate client business challenges into data solutions** | Built 4 Fortune 100 industry solutions answering core client business metrics | [`app.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/app.py) |
| **Data Analytics Pipelines & Data Quality** | Data cleaning, standardisation, null handling, duplicate removal, fail-fast validation gates | [`pipeline.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/pipeline.py) |
| **Star Schema Data Warehousing & SQL** | Star schema DB (Fact & Dimension tables) with CTEs, Window Functions (`NTILE`, `LAG`, `ROW_NUMBER`) | [`sql/analytics.sql`](file:///c:/Users/Akarsha/Downloads/retailpulse/sql/analytics.sql) |
| **Analytics Dashboards & Visualization** | Streamlit multi-domain interactive dashboard (KPI metrics, time series, RFM matrix, bar charts) | [`app.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/app.py) |
| **Generative AI & Foundation Models** | Gemini model (`gemini-2.5-flash`) Text-to-SQL engine with read-only query security validation | [`app.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/app.py) |
| **Modern Cloud Platforms (AWS)** | Docker containerization, S3 raw landing zone (`RAW_S3_URI`), Postgres/RDS via `DATABASE_URL`, AWS EC2 deploy script | [`deploy/aws_ec2.sh`](file:///c:/Users/Akarsha/Downloads/retailpulse/deploy/aws_ec2.sh) |
| **Big Data Engineering (PySpark / Scala / Java)** | PySpark reference pipeline demonstrating distributed windowing, deduplication, and Delta Lake Parquet partitioning | [`pipeline_spark_reference.py`](file:///c:/Users/Akarsha/Downloads/retailpulse/pipeline_spark_reference.py) |
| **Agile Ceremonies & Quality Assurance** | Automated pytest suite + GitHub Actions CI workflow executed on every push/PR | [`.github/workflows/ci.yml`](file:///c:/Users/Akarsha/Downloads/retailpulse/.github/workflows/ci.yml) |

---

## 🏗️ Architecture

```text
Raw Datasets (S3 / Local CSV drops: Retail, SaaS, Healthcare, Hi-Tech)
                          │
                          ▼
            pipeline.py (Automated Ingestion & Data Engineering)
            Dedupe · Standardise · Fix Dates · Filter Anomalies · Validation Gates
                          │
                          ▼
        SQL Warehouse (SQLite locally / PostgreSQL / AWS RDS)
        Fact & Dim Tables: fact_sales · fact_saas_subscriptions · fact_healthcare_claims · fact_hitech_telemetry
                          │
                          ▼   sql/analytics.sql (CTEs, Window Functions, NTILE RFM, SLA Rollups)
  v_monthly_revenue · v_category_performance · v_customer_rfm · v_saas_metrics · v_healthcare_sla · v_hitech_telemetry
                          │
                          ▼
      app.py (Streamlit Dashboard + Gemini GenAI Text-to-SQL + Pipeline Quality Logs)
```

---

## 📊 Fortune 100 Multi-Industry Solutions

1. **Retail Analytics Vertical**: Answers revenue concentration, Q4 seasonality (Nov–Dec revenue spikes), YoY growth trajectory, and customer RFM segmentation (Champions vs. At-Risk).
2. **SaaS Subscriptions Vertical**: Analyzes Monthly Recurring Revenue (MRR), Annual Run Rate (ARR), tier distribution (Starter, Professional, Enterprise), and subscriber churn rates.
3. **Healthcare SLA & Claims Vertical**: Ingests patient claim processing telemetry, tracks SLA compliance (<24 hr response times), average claim amounts, and hospital readmission rates.
4. **Hi-Tech Cloud Telemetry Vertical**: Evaluates microservice response latencies (ms), infrastructure compute costs ($), error rates, and system stability across cloud endpoints.

---

## 🤖 Generative AI Text-to-SQL Engine

The **Ask Your Data (GenAI)** tab integrates Google Gemini (`gemini-2.5-flash`) to allow non-technical business stakeholders to query the SQL database in plain English:

- **Prompt Engineering**: Provides schema context and table definitions dynamically to the foundation model.
- **Security & Safety Gate**: Validates LLM SQL output before execution using `safe_select()` to ensure only single `SELECT`/`WITH` read-only statements execute, blocking `DROP`, `UPDATE`, or `DELETE` operations.

---

## 🚀 Quickstart & Local Execution

```bash
# 1. Install dependencies
pip install -r requirements.txt pytest

# 2. Run test suite
python -m pytest -v

# 3. Generate multi-domain datasets and run ETL pipeline
python generate_data.py && python pipeline.py

# 4. Launch Streamlit interactive dashboard
streamlit run app.py
```

---

## ☁️ AWS Cloud Deployment

### Option 1: Streamlit Community Cloud (Fastest & Free)
1. Push code to GitHub repository `Ak-arsha/retailpulse`.
2. Navigate to [share.streamlit.io](https://share.streamlit.io), connect your repository, and set main file to `app.py`.
3. In **Advanced Settings -> Secrets**, add: `GEMINI_API_KEY = "your-api-key"`.

### Option 2: AWS EC2 Instance Deployment
1. Launch an Ubuntu EC2 instance on AWS (allow inbound TCP ports **22** and **8501** in Security Group).
2. SSH into your instance and run:
   ```bash
   curl -sL https://raw.githubusercontent.com/Ak-arsha/retailpulse/main/deploy/aws_ec2.sh | bash
   ```
3. Access the live dashboard at `http://<EC2-PUBLIC-IP>:8501`.

---

## 📝 Resume Entry (Tailored for Placement Applications)

**Data Solutions Associate Intern Project — Enterprise Multi-Industry Analytics Platform**  
*Python, SQL, PySpark, Pandas, SQLAlchemy, Streamlit, Docker, AWS EC2, Gemini API, GitHub Actions*
- Architected an automated ETL data engineering pipeline ingesting 25K+ multi-domain raw records across Retail, SaaS, Healthcare, and Hi-Tech verticals with automated data quality validation gates and execution logging.
- Modeled a Star Schema SQL Warehouse utilizing CTEs and SQL Window Functions (`NTILE`, `LAG`, `ROW_NUMBER`) to power live dashboards answering critical business metrics (ARR, SLA compliance, P95 latency, RFM segmentation).
- Integrated Google Gemini foundation models for a secure, read-only Text-to-SQL query assistant, enforcing strict safety blocklists against unsafe database mutations.
- Deployed microservice architecture using Docker on AWS EC2 with continuous integration (CI) via GitHub Actions.

---

## 📚 Technical Interview Study Guide

1. **Why use a Star Schema over a flat single table?**  
   *Star schemas isolate dimensions from transactional facts, improving SQL query performance, reducing data redundancy, simplifying aggregations, and enabling modular data updates.*
2. **How does `NTILE(4)` work in customer RFM segmentation?**  
   *`NTILE(4)` divides ordered rows into 4 equal quartiles (1 to 4) based on Recency, Frequency, and Monetary metrics, allowing rule-based classification into Champions, Active, At-Risk, or Dormant segments.*
3. **How do you make LLM-generated SQL queries safe in production?**  
   *Enforce strict Regex parsing for `SELECT`/`WITH` statements only, disallow multiple query statements (`;`), block mutation keywords (`DROP`, `DELETE`, `UPDATE`), and run queries under a read-only database user role.*
4. **How would you scale this pipeline to petabyte scale in production?**  
   *Transition from pandas to PySpark / AWS EMR, leverage Delta Lake on AWS S3 with parquet partitioning, orchestrate workflows using Apache Airflow, and query via AWS Redshift or Snowflake.*
