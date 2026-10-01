"""Database Schema Definitions & Engine Factory supporting PostgreSQL & SQLite fallback."""
import os
from sqlalchemy import (create_engine, MetaData, Table, Column, String, Integer,
                        Float, DateTime, Boolean, text, Index)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///retail.db")


def get_engine(url=DB_URL):
    """Factory creating SQLAlchemy engine for PostgreSQL or SQLite."""
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_size=10, max_overflow=20)


def init_db(engine=None):
    """Initializes tables, constraints, indexes, quarantine DLQ, and audit logs."""
    if engine is None:
        engine = get_engine()

    meta = MetaData()

    # Fact Sales (Retail)
    fact_sales = Table(
        'fact_sales', meta,
        Column('order_id', String(50), primary_key=True),
        Column('order_date', String(20), index=True),
        Column('order_month', String(10), index=True),
        Column('order_day', Integer),
        Column('customer_id', String(50), index=True),
        Column('product_id', String(50), index=True),
        Column('quantity', Integer),
        Column('unit_price', Float),
        Column('discount', Float),
        Column('revenue', Float),
        Column('created_at', String(30))
    )

    # Dim Customer
    dim_customer = Table(
        'dim_customer', meta,
        Column('customer_id', String(50), primary_key=True),
        Column('region', String(50)),
        Column('city', String(50)),
        Column('valid_from', String(30)),
        Column('valid_to', String(30)),
        Column('is_current', Integer)
    )

    # Dim Product
    dim_product = Table(
        'dim_product', meta,
        Column('product_id', String(50), primary_key=True),
        Column('product_name', String(100)),
        Column('category', String(50), index=True)
    )

    # Fact SaaS
    fact_saas = Table(
        'fact_saas_subscriptions', meta,
        Column('customer_id', String(50), primary_key=True),
        Column('tier', String(50), index=True),
        Column('mrr', Float),
        Column('join_date', String(20)),
        Column('churned', Integer),
        Column('seats', Integer),
        Column('created_at', String(30))
    )

    # Fact Healthcare
    fact_healthcare = Table(
        'fact_healthcare_claims', meta,
        Column('claim_id', String(50), primary_key=True),
        Column('patient_id', String(50), index=True),
        Column('claim_type', String(50), index=True),
        Column('claim_amount', Float),
        Column('processing_hours', Float),
        Column('readmitted', Integer),
        Column('claim_date', String(20)),
        Column('created_at', String(30))
    )

    # Fact Hi-Tech
    fact_hitech = Table(
        'fact_hitech_telemetry', meta,
        Column('log_id', String(50), primary_key=True),
        Column('service_name', String(50), index=True),
        Column('latency_ms', Float),
        Column('compute_cost', Float),
        Column('error_count', Integer),
        Column('log_date', String(20)),
        Column('created_at', String(30))
    )

    # Quarantine Dead-Letter Queue (DLQ) Table
    quarantine = Table(
        'quarantine_records', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('dataset_name', String(50), index=True),
        Column('record_id', String(50)),
        Column('raw_payload', String(1000)),
        Column('rejection_reason', String(250)),
        Column('quarantined_at', String(30))
    )

    # GenAI Query Audit Table
    genai_audit = Table(
        'genai_query_audit', meta,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_query', String(500)),
        Column('generated_sql', String(1000)),
        Column('execution_status', String(20)),
        Column('execution_time_ms', Float),
        Column('queried_at', String(30))
    )

    meta.create_all(engine)
    print(f"[Database Schema] Initialized tables and constraints on engine: {engine.url}")
    return meta


if __name__ == "__main__":
    init_db()
