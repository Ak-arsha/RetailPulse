# RetailPulse — Retail Sales Analytics Pipeline

**Client brief (simulated):** a retail client has messy raw order exports and no single source of truth. They want to know where revenue comes from, whether it is growing, how seasonal it is, and which customers to retain. RetailPulse turns the raw data into a validated SQL warehouse, a dashboard, and a plain-English query interface.

**Flow:** raw CSV / S3 → cleaning & validation → star-schema SQL DB → analytics views → dashboard + GenAI text-to-SQL

> Data is **synthetic** (`generate_data.py` injects duplicates, nulls, bad dates, negative quantities, inconsistent casing) to simulate a client data drop. The pipeline works with any CSV with the same columns.

## Architecture
```
raw_orders.csv (local or s3://...)  ──►  pipeline.py: extract → transform → validate → load
                                            dedupe · standardise · fix dates · drop invalid · derive revenue
                                            ▼
                      SQL warehouse (SQLite locally / Postgres e.g. AWS RDS via DATABASE_URL)
                      fact_sales · dim_customer · dim_product · pipeline_runs
                                            ▼   sql/analytics.sql (CTEs, window functions, NTILE RFM)
          v_monthly_revenue · v_category_performance · v_customer_rfm · v_repeat_customers
                                            ▼
            app.py: Streamlit dashboard (Insights · Sales · RFM · GenAI · Pipeline health)
```

## How it maps to the Data Solutions Associate role
| Role requirement | Where in this repo |
|---|---|
| Translate client business challenges into data solutions | Client brief + **Insights** tab (5 business questions answered from SQL) |
| Data pipelines | `pipeline.py` (ETL, validation gates, run logging, S3 source) |
| Analytics dashboards | `app.py` (Streamlit) |
| SQL | `sql/analytics.sql`, star schema |
| Cloud platforms (AWS) | `deploy/aws_ec2.sh`, S3 input (`RAW_S3_URI`), Postgres/RDS via `DATABASE_URL`, Dockerfile |
| Generative AI | Gemini text-to-SQL tab with read-only guard |
| Agile / quality | `tests/` (pytest) + GitHub Actions CI on every push |

## Run locally
```bash
pip install -r requirements.txt
python generate_data.py && python pipeline.py
pytest -q
streamlit run app.py          # optional: export GEMINI_API_KEY=...
```

## Deploy
**Option 1 — Streamlit Community Cloud (fastest, free, ~10 min):** push to GitHub → share.streamlit.io → New app → repo `Ak-arsha/retailpulse`, file `app.py` → Advanced settings → Secrets: `GEMINI_API_KEY="..."`. The DB builds itself on first boot.

**Option 2 — AWS EC2 (use this if you want to say "deployed on AWS"):**
1. EC2 → Launch instance → Ubuntu, small free-tier-eligible type, create a key pair.
2. Security group: allow inbound TCP **22** (your IP) and **8501**.
3. `ssh -i key.pem ubuntu@<public-ip>` then run `curl -sL https://raw.githubusercontent.com/Ak-arsha/retailpulse/main/deploy/aws_ec2.sh | bash`
4. Open `http://<public-ip>:8501`.
5. Set a **billing alarm** and **stop/terminate** the instance when you're done to avoid charges.

**Optional AWS extras (only claim if you do them):** upload the CSV to an S3 bucket and run with `RAW_S3_URI=s3://bucket/raw_orders.csv` (`pip install s3fs`, AWS creds configured); create an RDS Postgres and set `DATABASE_URL=postgresql+psycopg2://user:pass@host/db`.

## Resume entry (edit to match what you really deploy)
**RetailPulse – Retail Analytics Pipeline & Dashboard** (Live | GitHub)
*Python, SQL, Pandas, SQLAlchemy, Streamlit, Docker, AWS EC2, Gemini API, GitHub Actions*
- Built an ETL pipeline that cleans and validates 18K+ raw order records (dedupe, null handling, schema checks) into a star-schema SQL warehouse, with run-level data-quality logging and pytest + CI.
- Wrote SQL views (CTEs, window functions, NTILE RFM) powering a dashboard that answers client questions on revenue concentration, growth, seasonality and customer retention; deployed with Docker on AWS EC2.
- Added a Gemini-powered text-to-SQL assistant with read-only query validation for non-technical users.

## Study guide
1. Why a star schema instead of one flat table?
2. How does `NTILE` work and how were segments defined?
3. What validation runs before load, and why fail loudly?
4. Why precompute `order_month`/`order_day`? (SQL portability)
5. How do you make LLM-generated SQL safe? (SELECT-only, single statement, blocklist; in prod a read-only DB user)
6. How would you scale it? (incremental loads, Airflow/Cloud Scheduler, partitioning, Redshift/BigQuery)
7. What would you monitor in production? (row counts, null rates, freshness, run failures)
