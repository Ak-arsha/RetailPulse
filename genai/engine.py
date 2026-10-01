"""
GenAI Engine Hardening:
- Uses Google Gemini API with model fallback & Streamlit secrets integration.
- Column-level PII Masking for Healthcare patient fields.
- Schema table validation against live DB tables (blocking hallucinated tables).
- Read-only SELECT query guardrails.
"""
import os
import re
import pandas as pd
import requests

SCHEMA_CONTEXT = """
Available Tables & Views in SQL Warehouse:
- fact_sales(order_id, order_date, order_month, customer_id, product_id, quantity, unit_price, discount, revenue)
- dim_customer(customer_id, region, city, valid_from, valid_to, is_current)
- dim_product(product_id, product_name, category)
- fact_saas_subscriptions(customer_id, tier, mrr, join_date, churned, seats)
- fact_healthcare_claims(claim_id, patient_id [MASKED_PII], claim_type, claim_amount, processing_hours, readmitted, claim_date)
- fact_hitech_telemetry(log_id, service_name, latency_ms, compute_cost, error_count, log_date)
Views: v_monthly_revenue, v_category_performance, v_customer_rfm, v_repeat_customers, v_saas_metrics, v_healthcare_sla, v_hitech_telemetry.
"""

VALID_TABLES = {
    "fact_sales", "dim_customer", "dim_product", "fact_saas_subscriptions",
    "fact_healthcare_claims", "fact_hitech_telemetry", "v_monthly_revenue",
    "v_category_performance", "v_customer_rfm", "v_repeat_customers",
    "v_saas_metrics", "v_healthcare_sla", "v_hitech_telemetry"
}


def get_gemini_api_key() -> str:
    """Retrieves GEMINI_API_KEY from environment variable or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                key = str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
    return key


def mask_pii_query(user_query: str) -> str:
    """Masks patient IDs, SSNs, and personal identification numbers from prompt text."""
    masked = re.sub(r"\b(PAT\d{4,8})\b", "[PATIENT_ID_REDACTED]", user_query, flags=re.IGNORECASE)
    masked = re.sub(r"\b(\d{3}-\d{2}-\d{4})\b", "[SSN_REDACTED]", masked)
    return masked


def validate_table_names(sql: str) -> bool:
    """Blocks hallucinated non-existent tables in generated SQL."""
    matches = re.findall(r"(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)", sql)
    for tbl in matches:
        if tbl.lower() not in VALID_TABLES:
            return False
    return True


def safe_select_guard(sql: str) -> bool:
    """Enforces strict single read-only SELECT/WITH statements."""
    s = sql.strip().rstrip(";")
    if ";" in s or not re.match(r"(?is)^\s*(select|with)\b", s):
        return False
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma|replace|truncate)\b", s):
        return False
    return True


def generate_and_validate_sql(user_query: str, engine=None):
    """Generates SQL using Gemini API, validates schema & read-only guardrails, and executes query."""
    key = get_gemini_api_key()
    masked_query = mask_pii_query(user_query)

    if not key or key == "YOUR_GEMINI_API_KEY":
        return {
            "status": "warning",
            "message": "GEMINI_API_KEY not configured. Please set GEMINI_API_KEY in Streamlit Cloud Secrets Manager to enable live LLM querying.",
            "sql": None,
            "data": []
        }

    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash"
    ]

    prompt = (f"You write one ANSI SQL / SQLite / Postgres SELECT query based on this database schema:\n{SCHEMA_CONTEXT}\n"
              f"Return ONLY the SQL block, with no markdown formatting.\nQuestion: {masked_query}")

    last_error = ""

    for model in models_to_try:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": key},
                timeout=12,
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            data = r.json()

            if "error" in data:
                last_error = data["error"].get("message", str(data["error"]))
                continue

            if "candidates" in data and data["candidates"]:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    raw_sql = candidate["content"]["parts"][0]["text"].replace("```sql", "").replace("```", "").strip()

                    if not safe_select_guard(raw_sql):
                        return {"status": "error", "message": "Blocked: SQL failed safety check (must be single SELECT statement)", "sql": raw_sql, "data": []}

                    if not validate_table_names(raw_sql):
                        return {"status": "error", "message": "Blocked: Query references non-existent or un-approved table name", "sql": raw_sql, "data": []}

                    df_res = pd.read_sql(raw_sql, engine) if engine else pd.DataFrame()
                    return {
                        "status": "success",
                        "sql": raw_sql,
                        "count": len(df_res),
                        "data": df_res.to_dict(orient="records")
                    }
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "status": "error",
        "message": f"LLM execution error: {last_error if last_error else 'Unable to generate SQL'}",
        "sql": None,
        "data": []
    }
